"""
Canonical Corpus Reorganization Script for MarkMint.

Enforces physical corpus structure:
corpus/Semester_{1..8}/<Canonical Course Name>/

Performs:
1. Moves misplaced Sem 3/4 courses out of corpus/Semester_1:
   - Advanced Programming Practice (APP) -> corpus/Semester_3/Advanced Programming Practice (APP)
   - Artificial Intelligence (AI) -> corpus/Semester_4/Artificial Intelligence (AI)
   - Advanced Calculus and Complex Analysis -> merges into corpus/Semester_2/Advanced Calculus and Complex Analysis
2. Moves misplaced Sem 3 courses out of corpus/Semester_2:
   - Microbiology -> corpus/Semester_3/Microbiology
3. Moves staging pyqs from data/s3_s4/pyqs into canonical corpus destinations:
   - COA_*.pdf -> corpus/Semester_3/Computer Organization and Architecture/PYQ/
   - DAA_*.pdf -> corpus/Semester_4/Design and Analysis of Algorithms/PYQ/
   - DBMS_*.pdf -> corpus/Semester_4/Database Management Systems/PYQ/
   - DSA_*.pdf -> corpus/Semester_3/Data Structures and Algorithms/PYQ/
   - OS_*.pdf -> corpus/Semester_3/Operating Systems/PYQ/
4. Moves higher-semester staging material from data/1 Year:
   - Control Systems -> corpus/Semester_4/Control Systems
   - Digital Electronic Principles -> corpus/Semester_3/Digital Electronic Principles
   - Electronic Devices -> corpus/Semester_3/Electronic Devices
   - COI -> corpus/Semester_3/Constitution of India
   - Hardware and troubleshoot -> corpus/Semester_3/Hardware and Troubleshooting
   - Measuring Instrument -> corpus/Semester_3/Measuring Instruments
5. Updates path references in manifests (data/manifest.json, etc.) and database (production_corpus.db).
6. Preserves SHA-256 idempotency with zero loss.
"""

import os
import shutil
import hashlib
import json
import logging
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from backend.core.database import SessionLocal
from backend.models.core import Document

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reorganize_corpus")


def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def ensure_semester_dirs(base_dir: str = "corpus"):
    for sem in range(1, 9):
        sem_dir = os.path.join(base_dir, f"Semester_{sem}")
        os.makedirs(sem_dir, exist_ok=True)
    logger.info("Ensured corpus/Semester_1 through corpus/Semester_8 exist.")


def move_directory_contents(src_dir: str, dst_dir: str, path_mapping: Dict[str, str]) -> int:
    """
    Recursively moves files from src_dir to dst_dir.
    If destination file exists with identical SHA-256, safely removes src.
    If destination file does not exist, moves and preserves SHA-256.
    Records src -> dst mapping in path_mapping.
    """
    if not os.path.exists(src_dir):
        logger.warning("Source directory does not exist: %s", src_dir)
        return 0

    os.makedirs(dst_dir, exist_ok=True)
    moved_count = 0

    for root, dirs, files in os.walk(src_dir):
        rel_root = os.path.relpath(root, src_dir)
        target_root = os.path.join(dst_dir, rel_root) if rel_root != "." else dst_dir
        os.makedirs(target_root, exist_ok=True)

        for filename in files:
            src_file = os.path.join(root, filename)
            dst_file = os.path.join(target_root, filename)

            src_hash = sha256_file(src_file)

            if os.path.exists(dst_file):
                dst_hash = sha256_file(dst_file)
                if src_hash == dst_hash:
                    logger.debug("Duplicate identical file at destination: %s", dst_file)
                    os.remove(src_file)
                else:
                    # Name collision with different content: preserve both
                    base, ext = os.path.splitext(filename)
                    alt_name = f"{base}_alt_{src_hash[:8]}{ext}"
                    dst_file = os.path.join(target_root, alt_name)
                    shutil.move(src_file, dst_file)
                    assert sha256_file(dst_file) == src_hash, "SHA-256 mismatch after move"
                    moved_count += 1
            else:
                shutil.move(src_file, dst_file)
                assert sha256_file(dst_file) == src_hash, "SHA-256 mismatch after move"
                moved_count += 1

            path_mapping[src_file] = dst_file

    # Clean up empty source directory
    try:
        shutil.rmtree(src_dir)
    except Exception as e:
        logger.warning("Could not remove empty src_dir %s: %s", src_dir, e)

    return moved_count


def update_manifests(path_mapping: Dict[str, str]):
    manifest_files = [
        "data/manifest.json",
        "data/manifests/canary_manifest.json",
        "data/manifests/first_year_manifest.json",
        "data/manifests/first_year_union_manifest.json",
    ]

    # Normalize mappings to both backslash and forward slash
    norm_mappings = {}
    for src, dst in path_mapping.items():
        src_clean = os.path.normpath(src)
        dst_clean = os.path.normpath(dst)
        norm_mappings[src_clean] = dst_clean
        norm_mappings[src_clean.replace("\\", "/")] = dst_clean.replace("\\", "/")
        norm_mappings[src_clean.replace("/", "\\")] = dst_clean.replace("/", "\\")

    for m_path in manifest_files:
        if not os.path.exists(m_path):
            continue

        try:
            with open(m_path, "r", encoding="utf-8") as f:
                content = f.read()

            modified = False
            for old_path, new_path in norm_mappings.items():
                if old_path in content:
                    content = content.replace(old_path, new_path)
                    modified = True

            # Also replace any general folder path substrings
            general_replacements = [
                ("corpus\\\\Semester_1\\\\Advanced Programming Practice (APP)", "corpus\\\\Semester_3\\\\Advanced Programming Practice (APP)"),
                ("corpus/Semester_1/Advanced Programming Practice (APP)", "corpus/Semester_3/Advanced Programming Practice (APP)"),
                ("corpus\\\\Semester_1\\\\Artificial Intelligence (AI)", "corpus\\\\Semester_4\\\\Artificial Intelligence (AI)"),
                ("corpus/Semester_1/Artificial Intelligence (AI)", "corpus/Semester_4/Artificial Intelligence (AI)"),
                ("corpus\\\\Semester_1\\\\Advanced Calculus and Complex Analysis", "corpus\\\\Semester_2\\\\Advanced Calculus and Complex Analysis"),
                ("corpus/Semester_1/Advanced Calculus and Complex Analysis", "corpus/Semester_2/Advanced Calculus and Complex Analysis"),
                ("corpus\\\\Semester_2\\\\Microbiology", "corpus\\\\Semester_3\\\\Microbiology"),
                ("corpus/Semester_2/Microbiology", "corpus/Semester_3/Microbiology"),
            ]
            for old_sub, new_sub in general_replacements:
                if old_sub in content:
                    content = content.replace(old_sub, new_sub)
                    modified = True

            if modified:
                with open(m_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info("Updated manifest paths in: %s", m_path)
        except Exception as e:
            logger.error("Error updating manifest %s: %s", m_path, e)


def update_database(path_mapping: Dict[str, str], db: Session):
    norm_mappings = {}
    for src, dst in path_mapping.items():
        norm_mappings[os.path.normpath(src)] = os.path.normpath(dst)
        norm_mappings[src.replace("\\", "/")] = dst.replace("\\", "/")
        norm_mappings[src.replace("/", "\\")] = dst.replace("/", "\\")

    docs = db.query(Document).all()
    updated = 0
    for doc in docs:
        if not doc.source:
            continue
        doc_src = os.path.normpath(doc.source)
        if doc_src in norm_mappings:
            doc.source = norm_mappings[doc_src]
            updated += 1
        elif "Semester_1" in doc.source:
            for old_sub, new_sub in [
                ("Semester_1/Advanced Programming Practice", "Semester_3/Advanced Programming Practice"),
                ("Semester_1\\Advanced Programming Practice", "Semester_3\\Advanced Programming Practice"),
                ("Semester_1/Artificial Intelligence", "Semester_4/Artificial Intelligence"),
                ("Semester_1\\Artificial Intelligence", "Semester_4\\Artificial Intelligence"),
                ("Semester_1/Advanced Calculus", "Semester_2/Advanced Calculus"),
                ("Semester_1\\Advanced Calculus", "Semester_2\\Advanced Calculus"),
            ]:
                if old_sub in doc.source:
                    doc.source = doc.source.replace(old_sub, new_sub)
                    updated += 1

    if updated > 0:
        db.commit()
        logger.info("Updated %d Document.source records in database.", updated)
    else:
        logger.info("No Document.source records required database updates.")


def main():
    logger.info("=== Starting Canonical Corpus Reorganization ===")
    ensure_semester_dirs("corpus")

    path_mapping: Dict[str, str] = {}
    total_moved = 0

    # 1. Misplaced courses in corpus/Semester_1
    sem1_moves = [
        ("corpus/Semester_1/Advanced Programming Practice (APP)", "corpus/Semester_3/Advanced Programming Practice (APP)"),
        ("corpus/Semester_1/Artificial Intelligence (AI)", "corpus/Semester_4/Artificial Intelligence (AI)"),
        ("corpus/Semester_1/Advanced Calculus and Complex Analysis", "corpus/Semester_2/Advanced Calculus and Complex Analysis"),
    ]
    for src, dst in sem1_moves:
        if os.path.exists(src):
            cnt = move_directory_contents(src, dst, path_mapping)
            logger.info("Moved %d files from '%s' -> '%s'", cnt, src, dst)
            total_moved += cnt

    # 2. Misplaced courses in corpus/Semester_2
    sem2_moves = [
        ("corpus/Semester_2/Microbiology", "corpus/Semester_3/Microbiology"),
    ]
    for src, dst in sem2_moves:
        if os.path.exists(src):
            cnt = move_directory_contents(src, dst, path_mapping)
            logger.info("Moved %d files from '%s' -> '%s'", cnt, src, dst)
            total_moved += cnt

    # 3. Move PYQs from data/s3_s4/pyqs to canonical corpus
    s3_s4_pyqs_dir = "data/s3_s4/pyqs"
    if os.path.exists(s3_s4_pyqs_dir):
        pyq_targets = {
            "COA_": "corpus/Semester_3/Computer Organization and Architecture/PYQ",
            "DAA_": "corpus/Semester_4/Design and Analysis of Algorithms/PYQ",
            "DBMS_": "corpus/Semester_4/Database Management Systems/PYQ",
            "DSA_": "corpus/Semester_3/Data Structures and Algorithms/PYQ",
            "OS_": "corpus/Semester_3/Operating Systems/PYQ",
        }
        for item in os.listdir(s3_s4_pyqs_dir):
            src_item = os.path.join(s3_s4_pyqs_dir, item)
            if os.path.isfile(src_item) and item.lower().endswith(".pdf"):
                matched_dest_dir = None
                for prefix, dest_dir in pyq_targets.items():
                    if item.startswith(prefix):
                        matched_dest_dir = dest_dir
                        break
                if matched_dest_dir:
                    os.makedirs(matched_dest_dir, exist_ok=True)
                    dst_file = os.path.join(matched_dest_dir, item)
                    src_hash = sha256_file(src_item)
                    if os.path.exists(dst_file):
                        if sha256_file(dst_file) == src_hash:
                            os.remove(src_item)
                        else:
                            base, ext = os.path.splitext(item)
                            dst_file = os.path.join(matched_dest_dir, f"{base}_alt_{src_hash[:8]}{ext}")
                            shutil.move(src_item, dst_file)
                            assert sha256_file(dst_file) == src_hash
                            total_moved += 1
                    else:
                        shutil.move(src_item, dst_file)
                        assert sha256_file(dst_file) == src_hash
                        total_moved += 1
                    path_mapping[src_item] = dst_file
            elif os.path.isdir(src_item) and item == "dsa_dec_imgs":
                dst_img_dir = "corpus/Semester_3/Data Structures and Algorithms/PYQ/dsa_dec_imgs"
                cnt = move_directory_contents(src_item, dst_img_dir, path_mapping)
                logger.info("Moved %d dsa images to %s", cnt, dst_img_dir)
                total_moved += cnt

    # 4. Move higher-semester staging folders from data/1 Year
    staging_1year_moves = [
        ("data/1 Year/Control Systems", "corpus/Semester_4/Control Systems"),
        ("data/1 Year/Digital Electronic Principles", "corpus/Semester_3/Digital Electronic Principles"),
        ("data/1 Year/Electronic Devices", "corpus/Semester_3/Electronic Devices"),
        ("data/1 Year/COI", "corpus/Semester_1/Constitution of India"),
        ("data/1 Year/Hardware and troubleshoot", "corpus/Semester_1/Hardware and Troubleshooting"),
        ("data/1 Year/Measuring Instrument", "corpus/Semester_1/Measuring Instruments"),
    ]
    for src, dst in staging_1year_moves:
        if os.path.exists(src):
            cnt = move_directory_contents(src, dst, path_mapping)
            logger.info("Moved %d files from '%s' -> '%s'", cnt, src, dst)
            total_moved += cnt

    # 5. Update Manifests
    logger.info("Updating path references in manifest files...")
    update_manifests(path_mapping)

    # 6. Update Database
    logger.info("Updating database references in production_corpus.db...")
    db = SessionLocal()
    try:
        update_database(path_mapping, db)
    finally:
        db.close()

    logger.info("=== Canonical Corpus Reorganization Complete. Total files moved/reorganized: %d ===", total_moved)


if __name__ == "__main__":
    main()
