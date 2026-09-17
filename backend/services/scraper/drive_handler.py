"""
Google Drive resolver and recursive folder traversal engine.
Handles:
- drive.google.com/file/d/...
- drive.google.com/open?id=...
- drive.google.com/drive/folders/...
- docs.google.com/document/d/...
- docs.google.com/presentation/d/...
- docs.google.com/spreadsheets/d/...
- Recursive nested folder traversal with folder path preservation
- Auth/permission barrier detection (ActionRequiredItem generation)
"""

import re
import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

from .models import ActionRequiredItem

logger = logging.getLogger(__name__)


class GoogleDriveItem:
    """Represents a discovered child file or folder inside Google Drive."""
    def __init__(
        self,
        item_id: str,
        name: str,
        is_folder: bool,
        folder_path: str = "",
        direct_url: Optional[str] = None,
        mime_type: Optional[str] = None,
        size: Optional[int] = None,
    ):
        self.item_id = item_id
        self.name = name
        self.is_folder = is_folder
        self.folder_path = folder_path
        self.direct_url = direct_url or f"https://drive.google.com/uc?export=download&id={item_id}"
        self.mime_type = mime_type
        self.size = size

    def __repr__(self):
        kind = "Folder" if self.is_folder else "File"
        return f"<GoogleDriveItem [{kind}] {self.name} (id={self.item_id}, mime={self.mime_type}, size={self.size}, path='{self.folder_path}')>"


class GoogleDriveHandler:
    """Comprehensive parser and recursive navigator for Google Drive files and folders."""

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    @classmethod
    def extract_file_id(cls, url: str) -> Optional[str]:
        """Extract Google Drive file ID from arbitrary Google Drive or Docs link."""
        if not url:
            return None

        # Check /file/d/{id}
        match = re.search(r"drive\.google\.com/file/d/([A-Za-z0-9_-]{25,})", url)
        if match:
            return match.group(1)

        # Check /document/d/{id} or /presentation/d/{id} or /spreadsheets/d/{id}
        doc_match = re.search(r"docs\.google\.com/(?:document|presentation|spreadsheets)/d/([A-Za-z0-9_-]{25,})", url)
        if doc_match:
            return doc_match.group(1)

        # Check open?id={id} or uc?id={id} or uc?export=download&id={id}
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if "id" in qs and qs["id"]:
            fid = qs["id"][0]
            if len(fid) >= 20:
                return fid

        return None

    @classmethod
    def extract_folder_id(cls, url: str) -> Optional[str]:
        """Extract Google Drive folder ID from URL."""
        if not url:
            return None
        match = re.search(r"drive\.google\.com/drive/(?:u/\d+/)?folders/([A-Za-z0-9_-]+)", url)
        if match:
            return match.group(1)
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if "id" in qs and "folders" in url:
            return qs["id"][0]
        return None

    @classmethod
    def is_drive_url(cls, url: str) -> bool:
        """Check if URL belongs to Google Drive / Docs."""
        if not url:
            return False
        return any(d in url for d in ["drive.google.com", "docs.google.com"])

    @classmethod
    def is_drive_folder(cls, url: str) -> bool:
        """Check if URL points to a Google Drive folder."""
        return cls.extract_folder_id(url) is not None

    @classmethod
    def get_direct_download_url(cls, url: str) -> str:
        """
        Converts any Google Drive file or Google Docs/Slides/Sheets link
        to a direct PDF download / export URL.
        """
        # Google Docs export
        if "docs.google.com/document/d/" in url:
            fid = cls.extract_file_id(url)
            return f"https://docs.google.com/document/d/{fid}/export?format=pdf"

        # Google Presentations export
        if "docs.google.com/presentation/d/" in url:
            fid = cls.extract_file_id(url)
            return f"https://docs.google.com/presentation/d/{fid}/export/pdf"

        # Google Spreadsheets export
        if "docs.google.com/spreadsheets/d/" in url:
            fid = cls.extract_file_id(url)
            return f"https://docs.google.com/spreadsheets/d/{fid}/export?format=pdf"

        # Standard Drive file
        file_id = cls.extract_file_id(url)
        if file_id:
            return f"https://drive.google.com/uc?export=download&id={file_id}"

        return url

    @classmethod
    def _parse_drive_ivd(cls, html_text: str) -> List[Dict[str, Any]]:
        """Parses Google Drive's embedded window['_DRIVE_ivd'] data structure."""
        m = re.search(r"window\['_DRIVE_ivd'\]\s*=\s*'([^']+)'", html_text)
        if not m:
            return []
        try:
            raw_str = m.group(1).replace(r'\/', '/')
            decoded_str = raw_str.encode('utf-8').decode('unicode_escape')
            data = json.loads(decoded_str)
            items = []

            def find_items(obj):
                if isinstance(obj, list):
                    if (
                        len(obj) > 3
                        and isinstance(obj[0], str)
                        and len(obj[0]) >= 20
                        and isinstance(obj[1], list)
                        and isinstance(obj[2], str)
                        and isinstance(obj[3], str)
                    ):
                        items.append({
                            'id': obj[0],
                            'parents': obj[1],
                            'name': obj[2],
                            'mime': obj[3],
                            'is_folder': (obj[3] == 'application/vnd.google-apps.folder'),
                            'size': obj[13] if len(obj) > 13 and isinstance(obj[13], int) else None,
                        })
                    else:
                        for x in obj:
                            find_items(x)

            find_items(data)
            return items
        except Exception as e:
            logger.debug("Failed to parse _DRIVE_ivd: %s", e)
            return []

    @classmethod
    def traverse_folder(
        cls,
        folder_url: str,
        current_folder_path: str = "",
        max_depth: int = 5,
        visited_folders: Optional[set] = None,
        timeout: int = 20,
    ) -> Tuple[List[GoogleDriveItem], Optional[ActionRequiredItem]]:
        """
        Recursively traverse Google Drive folder and nested subfolders.
        Uses native _DRIVE_ivd payload if available, falling back to HTML DOM parsing.
        Returns:
            (items_found, action_required_if_blocked)
        """
        if visited_folders is None:
            visited_folders = set()

        folder_id = cls.extract_folder_id(folder_url)
        if not folder_id:
            return [], None

        if folder_id in visited_folders or max_depth <= 0:
            return [], None

        visited_folders.add(folder_id)
        url = f"https://drive.google.com/drive/folders/{folder_id}"

        headers = {
            "User-Agent": cls.USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            r = requests.get(url, headers=headers, timeout=timeout)
        except Exception as e:
            action = ActionRequiredItem(
                source="Google Drive",
                url=folder_url,
                problem=f"Network error accessing folder: {str(e)}",
                what_is_needed="Check internet connection or supply public folder link",
            )
            return [], action

        # Check for authentication barrier or access denied
        if r.status_code in [401, 403, 404] or "accounts.google.com/signin" in r.text or "You need access" in r.text:
            logger.warning("Google Drive folder requires authentication: %s", folder_url)
            action = ActionRequiredItem(
                source="Google Drive",
                url=folder_url,
                problem="Authentication required / permission denied (private folder)",
                what_is_needed="Change folder sharing to 'Anyone with the link can view' or export contents",
            )
            return [], action

        found_items: List[GoogleDriveItem] = []
        subfolders_to_visit: List[Tuple[str, str]] = []  # (subfolder_id, subfolder_name)

        # Strategy 1: Attempt native _DRIVE_ivd decoding
        ivd_items = cls._parse_drive_ivd(r.text)
        if ivd_items:
            for it in ivd_items:
                if it['id'] == folder_id:
                    continue
                if it['is_folder']:
                    subfolders_to_visit.append((it['id'], it['name']))
                else:
                    found_items.append(GoogleDriveItem(
                        item_id=it['id'],
                        name=it['name'],
                        is_folder=False,
                        folder_path=current_folder_path,
                        mime_type=it['mime'],
                        size=it['size'],
                    ))
        else:
            # Strategy 2: Fallback to HTML DOM parsing
            soup = BeautifulSoup(r.text, "html.parser")
            elements = soup.find_all(attrs={"data-id": True})
            seen_ids = set()

            for el in elements:
                did = el.get("data-id")
                if not did or did == "_gd" or did in seen_ids:
                    continue
                seen_ids.add(did)

                label = el.get("aria-label") or ""
                if not label:
                    child = el.find(attrs={"aria-label": True})
                    if child:
                        label = child.get("aria-label", "")

                is_folder = (
                    "Google Drive Folder" in label
                    or "Folder" in label
                    or "/folders/" in str(el)
                )

                clean_name = label
                for suffix in [" PDF Shared", " PDF", " Shared", " Google Drive Folder"]:
                    if clean_name.endswith(suffix):
                        clean_name = clean_name[:-len(suffix)].strip()

                if not clean_name:
                    clean_name = " ".join(el.stripped_strings) or f"item_{did}"

                if is_folder:
                    subfolders_to_visit.append((did, clean_name))
                else:
                    found_items.append(GoogleDriveItem(
                        item_id=did,
                        name=clean_name,
                        is_folder=False,
                        folder_path=current_folder_path,
                    ))

        # Recursively traverse nested subfolders
        for sub_id, sub_name in subfolders_to_visit:
            nested_path = f"{current_folder_path}/{sub_name}".strip("/")
            sub_url = f"https://drive.google.com/drive/folders/{sub_id}"
            nested_items, nested_action = cls.traverse_folder(
                sub_url,
                current_folder_path=nested_path,
                max_depth=max_depth - 1,
                visited_folders=visited_folders,
                timeout=timeout,
            )
            found_items.extend(nested_items)

        return found_items, None
