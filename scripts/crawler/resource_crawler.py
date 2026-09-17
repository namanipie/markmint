"""
MarkMint Academic Resource Crawler & Ingestion CLI.
Discovers, traverses, downloads, verifies, classifies, maps, and ingests academic PDFs
from Studique and The Helpers into MarkMint's production corpus.

Usage examples:
    python scripts/resource_crawler.py --source studique
    python scripts/resource_crawler.py --source helpers
    python scripts/resource_crawler.py --source all
    python scripts/resource_crawler.py --source all --resume
    python scripts/resource_crawler.py --source helpers --semester 1
    python scripts/resource_crawler.py --manifest
    python scripts/resource_crawler.py --download-only
    python scripts/resource_crawler.py --ingest-manifest
    python scripts/resource_crawler.py --source all --live --limit 10
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timezone

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.services.scraper.models import DownloadStatus
from backend.services.scraper.manifest import ManifestManager
from backend.services.scraper.downloader import ResourceDownloader
from backend.services.scraper.crawler import AcademicResourceCrawler
from backend.services.scraper.ingester import CorpusIngester

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("crawler_cli")


def print_manifest_summary(manifest_path: str = "data/manifest.json"):
    """Displays a human-readable summary of the current manifest state."""
    if not os.path.exists(manifest_path):
        print(f"\n[!] No manifest file found at {manifest_path}")
        return

    mgr = ManifestManager(manifest_path=manifest_path)
    report = mgr.generate_audit_report()

    print("\n" + "=" * 70)
    print("                 MARKMINT MANIFEST AUDIT SUMMARY")
    print("=" * 70)
    print(f"Manifest Path:           {manifest_path}")
    print(f"Total Resources:         {report.resources_discovered}")
    print(f"PDFs Downloaded:         {report.pdfs_downloaded}")
    print(f"Duplicate Files:         {report.duplicates}")
    print(f"Invalid / Corrupted:     {report.pdfs_invalid}")
    print(f"Failed Downloads:        {report.pdfs_failed}")
    print("-" * 70)
    print(f"PYQs Classified:         {report.pyqs}")
    print(f"Study Materials:         {report.study_materials}")
    print(f"Unknown Classification:  {report.unknown_classifications}")
    print("-" * 70)
    print(f"Curriculum MATCHED:      {report.matched}")
    print(f"Curriculum CATALOG_ONLY: {report.catalog_only}")
    print(f"Curriculum AMBIGUOUS:    {report.ambiguous}")
    print(f"Curriculum UNMATCHED:    {report.unmatched}")
    print("-" * 70)
    print(f"Database INGESTED:       {report.ingested}")
    print(f"Failed Ingestions:       {report.failed_ingestion}")
    print(f"Action Required Items:   {len(report.actions_required)}")
    print("=" * 70)

    if report.actions_required:
        print("\n" + "!" * 70)
        print("  ACTION REQUIRED (MANUAL ASSISTANCE NEEDED)")
        print("!" * 70)
        for idx, act in enumerate(report.actions_required, 1):
            print(f"\n[{idx}] SOURCE: {act.source}")
            print(f"    URL:     {act.url}")
            print(f"    PROBLEM: {act.problem}")
            print(f"    ACTION:  {act.what_is_needed}")


def ingest_existing_manifest(manifest_path: str = "data/manifest.json"):
    """Ingests all valid downloaded records from an existing manifest file."""
    if not os.path.exists(manifest_path):
        print(f"[!] Manifest file not found at {manifest_path}")
        return

    print(f"\n[Ingest] Ingesting resources from {manifest_path} into database...")
    mgr = ManifestManager(manifest_path=manifest_path)
    db = SessionLocal()
    ingester = CorpusIngester(db)

    try:
        count = 0
        for key, rec in mgr.records.items():
            if rec.download_status in [DownloadStatus.DOWNLOADED, DownloadStatus.DUPLICATE] and rec.local_path:
                if rec.ingestion_status != "INGESTED":
                    ingester.ingest_record(rec)
                    mgr.add_or_update_record(rec)
                    count += 1
        print(f"[Ingest] Ingestion complete. Processed {count} records.")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="MarkMint Academic Resource Crawler & Ingestion Pipeline")
    parser.add_argument("--source", choices=["studique", "helpers", "all"], default="all", help="Target source")
    parser.add_argument("--semester", type=int, default=None, help="Filter by semester number (1-8)")
    parser.add_argument("--subject", type=str, default=None, help="Filter by subject title substring")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of resources to download")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume from existing manifest (default True)")
    parser.add_argument("--no-resume", dest="resume", action="store_false", help="Do not skip previously completed files")
    parser.add_argument("--live", action="store_true", help="Execute live crawl against target sites")
    parser.add_argument("--download-only", action="store_true", help="Download and validate files without DB ingestion")
    parser.add_argument("--ingest-manifest", action="store_true", help="Ingest existing completed manifest into DB")
    parser.add_argument("--manifest", action="store_true", help="Print summary of manifest and exit")
    parser.add_argument("--manifest-path", type=str, default="data/manifest.json", help="Path to manifest JSON")
    parser.add_argument("--output-dir", type=str, default="corpus", help="Corpus download directory")
    parser.add_argument("--rate-limit", type=float, default=0.5, help="Delay in seconds between requests")
    parser.add_argument("--report", type=str, default="data/crawl_audit_report.json", help="Path for JSON audit report")

    args = parser.parse_args()

    if args.manifest:
        print_manifest_summary(args.manifest_path)
        return

    if args.ingest_manifest:
        ingest_existing_manifest(args.manifest_path)
        print_manifest_summary(args.manifest_path)
        return

    # Execute crawl
    db = SessionLocal()
    manifest_mgr = ManifestManager(manifest_path=args.manifest_path)
    downloader = ResourceDownloader(corpus_dir=args.output_dir)

    crawler = AcademicResourceCrawler(
        db=db,
        manifest_manager=manifest_mgr,
        downloader=downloader,
        rate_limit_seconds=args.rate_limit,
        download_only=args.download_only,
    )

    try:
        report = crawler.run(
            source=args.source,
            semester=args.semester,
            subject=args.subject,
            limit=args.limit,
            resume=args.resume,
        )

        # Save machine-readable audit report
        os.makedirs(os.path.dirname(args.report), exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
        print(f"\n[+] Audit report saved to {args.report}")

        # Display summary
        print_manifest_summary(args.manifest_path)

    finally:
        db.close()


if __name__ == "__main__":
    main()
