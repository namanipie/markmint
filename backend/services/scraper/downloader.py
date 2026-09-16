"""
Resilient streaming file downloader and strict PDF validator for MarkMint.
Guarantees:
- Streaming downloads (bounded memory).
- Exponential backoff retry with error recovery.
- Google Drive large-file virus scan confirmation redirect handling.
- Strict PDF verification: size > 0, %PDF- magic bytes, readable PDF structure.
- Rejection of HTML error pages saved as PDF.
- Path traversal prevention and deterministic sanitized corpus storage.
- Chunked SHA-256 calculation.
"""

import os
import re
import time
import hashlib
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs
import requests
import pdfplumber

logger = logging.getLogger(__name__)


def sanitize_filesystem_name(name: str) -> str:
    """Sanitizes strings to create safe directory or file names, preventing path traversal."""
    if not name:
        return "unnamed"
    # Remove null bytes and control chars
    clean = re.sub(r"[\x00-\x1f\x7f]", "", str(name))
    # Replace slashes, backslashes, colons, and path traversal sequences
    clean = clean.replace("..", "_").replace("/", "_").replace("\\", "_").replace(":", "_")
    clean = clean.replace("?", "_").replace("*", "_").replace('"', "_").replace("<", "_").replace(">", "_").replace("|", "_")
    clean = " ".join(clean.split()).strip()
    return clean or "unnamed"


class ValidationResult:
    """Outcome of file validation."""
    def __init__(
        self,
        is_valid: bool,
        sha256: Optional[str] = None,
        file_size: int = 0,
        failure_reason: Optional[str] = None,
    ):
        self.is_valid = is_valid
        self.sha256 = sha256
        self.file_size = file_size
        self.failure_reason = failure_reason

    def __repr__(self):
        return f"<ValidationResult valid={self.is_valid} size={self.file_size} sha256={self.sha256[:8] if self.sha256 else None}>"


class ResourceDownloader:
    """Handles streaming download, retry, Drive confirm tokens, and strict PDF verification."""

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        corpus_dir: str = "corpus",
        temp_dir: str = "data/.download_cache/temp",
        max_file_size_bytes: int = 100 * 1024 * 1024,  # 100 MB
        timeout_seconds: int = 45,
    ):
        self.corpus_dir = corpus_dir
        self.temp_dir = temp_dir
        self.max_file_size_bytes = max_file_size_bytes
        self.timeout_seconds = timeout_seconds

        os.makedirs(self.corpus_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    @classmethod
    def calculate_sha256(cls, file_path: str) -> str:
        """Calculate SHA-256 hash in 64KB blocks."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def validate_pdf_file(cls, file_path: str) -> ValidationResult:
        """
        Validates downloaded file:
        1. File must exist and size > 0.
        2. Must start with '%PDF-' magic bytes.
        3. Must open cleanly via PDF parser (pdfplumber/pdfminer).
        4. Rejects HTML pages (e.g. Google Drive error/login pages).
        """
        if not os.path.exists(file_path):
            return ValidationResult(is_valid=False, failure_reason="File does not exist on disk")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return ValidationResult(is_valid=False, file_size=0, failure_reason="Downloaded file is 0 bytes (empty)")

        # Read first 1024 bytes for magic bytes check
        with open(file_path, "rb") as f:
            header = f.read(1024)

        # Check for HTML signature
        header_lower = header.lower()
        if (
            b"<!doctype html" in header_lower
            or b"<html" in header_lower
            or b"<body" in header_lower
            or b"accounts.google.com" in header_lower
        ):
            return ValidationResult(
                is_valid=False,
                file_size=file_size,
                failure_reason="File is an HTML web page disguised as a PDF (e.g. login/error page)",
            )

        # Check for %PDF- magic bytes
        if b"%PDF-" not in header[:64]:
            return ValidationResult(
                is_valid=False,
                file_size=file_size,
                failure_reason=f"Invalid PDF header: Missing '%PDF-' magic bytes (starts with: {header[:16]!r})",
            )

        # Structural integrity check with PDF parser
        try:
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                if page_count == 0:
                    return ValidationResult(
                        is_valid=False,
                        file_size=file_size,
                        failure_reason="PDF contains 0 valid pages",
                    )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                file_size=file_size,
                failure_reason=f"PDF structure is damaged or corrupt: {str(e)}",
            )

        # File is valid
        file_hash = cls.calculate_sha256(file_path)
        return ValidationResult(is_valid=True, sha256=file_hash, file_size=file_size)

    def download_to_temp(
        self,
        download_url: str,
        max_retries: int = 3,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Streams download into a temporary file. Handles Google Drive large-file scan warnings.
        Returns:
            (temp_file_path, error_message)
        """
        temp_filename = f"dl_{int(time.time()*1000)}_{hashlib.md5(download_url.encode()).hexdigest()[:10]}.tmp"
        temp_file_path = os.path.join(self.temp_dir, temp_filename)

        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "*/*",
        }

        session = requests.Session()

        for attempt in range(1, max_retries + 1):
            try:
                r = session.get(download_url, headers=headers, stream=True, timeout=self.timeout_seconds)

                if r.status_code != 200:
                    r.raise_for_status()

                # Stream to temp file
                downloaded_bytes = 0
                with open(temp_file_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=32768):
                        if chunk:
                            downloaded_bytes += len(chunk)
                            if downloaded_bytes > self.max_file_size_bytes:
                                f.close()
                                if os.path.exists(temp_file_path):
                                    os.remove(temp_file_path)
                                return None, f"File exceeded size limit of {self.max_file_size_bytes} bytes"
                            f.write(chunk)

                # Check if Google Drive returned an HTML virus scan confirmation page
                with open(temp_file_path, "rb") as f:
                    first_bytes = f.read(2048)

                if b"<!doctype html" in first_bytes.lower() or b"confirm=" in first_bytes.lower():
                    # Parse confirmation token from HTML
                    with open(temp_file_path, "r", encoding="utf-8", errors="ignore") as f:
                        html_content = f.read()

                    confirm_match = re.search(r'href="(/uc\?export=download[^"]*confirm=[^"]*)"', html_content)
                    if not confirm_match:
                        confirm_match = re.search(r'action="([^"]*)"', html_content)
                    if not confirm_match:
                        token_match = re.search(r'confirm=([0-9A-Za-z_-]+)', html_content)
                        if token_match:
                            token = token_match.group(1)
                            confirm_url = f"{download_url}&confirm={token}"
                        else:
                            confirm_url = None
                    else:
                        confirm_url = confirm_match.group(1).replace("&amp;", "&")
                        if confirm_url.startswith("/"):
                            confirm_url = f"https://drive.google.com{confirm_url}"

                    if confirm_url:
                        logger.info("Following Google Drive large-file confirmation redirect...")
                        r2 = session.get(confirm_url, headers=headers, stream=True, timeout=self.timeout_seconds)
                        if r2.status_code == 200:
                            downloaded_bytes = 0
                            with open(temp_file_path, "wb") as f:
                                for chunk in r2.iter_content(chunk_size=32768):
                                    if chunk:
                                        downloaded_bytes += len(chunk)
                                        f.write(chunk)

                return temp_file_path, None

            except Exception as e:
                logger.warning(
                    "Download attempt %d/%d failed for %s: %s",
                    attempt, max_retries, download_url, str(e)
                )
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except OSError:
                        pass

                if attempt < max_retries:
                    backoff = 2 ** attempt
                    time.sleep(backoff)
                else:
                    return None, f"Failed after {max_retries} attempts: {str(e)}"

        return None, "All retry attempts exhausted"

    def build_destination_path(
        self,
        semester: Optional[str],
        subject: Optional[str],
        classification: Optional[str],
        filename: str,
        drive_folder_path: Optional[str] = None,
    ) -> str:
        """
        Builds a sanitized deterministic filesystem path preventing path traversal:
        corpus/Semester_{sem}/{subject}/{classification}/[{drive_folder_path}/]{filename}.pdf
        """
        sem_str = f"Semester_{sanitize_filesystem_name(str(semester))}" if semester else "Semester_General"
        subj_str = sanitize_filesystem_name(subject or "General")
        class_str = sanitize_filesystem_name(classification or "OTHER")
        file_str = sanitize_filesystem_name(filename)

        if not file_str.lower().endswith(".pdf"):
            file_str += ".pdf"

        path_parts = [self.corpus_dir, sem_str, subj_str, class_str]

        if drive_folder_path:
            # Sanitize each subfolder in drive_folder_path
            folders = [sanitize_filesystem_name(p) for p in drive_folder_path.replace("\\", "/").split("/") if p.strip()]
            path_parts.extend(folders)

        path_parts.append(file_str)
        return os.path.join(*path_parts)

    def store_verified_file(
        self,
        temp_file_path: str,
        destination_path: str,
    ) -> str:
        """Moves verified file to destination path, creating parent directories safely."""
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        # If destination already exists with same content, overwrite safely
        if os.path.exists(destination_path):
            os.remove(destination_path)
        os.replace(temp_file_path, destination_path)
        return destination_path
