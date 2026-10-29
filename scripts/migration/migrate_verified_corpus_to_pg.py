#!/usr/bin/env python3
"""
MarkMint Verified Production Database Migration Tool
Transfers the audited, verified first-year academic corpus from SQLite (production_corpus.db)
into Render Managed PostgreSQL with complete referential integrity, sequence repair, and dry-run support.

Usage:
  python -m scripts.migration.migrate_verified_corpus_to_pg <SOURCE_SQLITE_URL> <TARGET_PG_URL> [--dry-run] [--confirm-production-mutation]
"""

import os
import sys
import time
import json
import argparse
import logging
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Set, Tuple

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migrate_verified_corpus")


def mask_url(url: str) -> str:
    """Mask credentials in a database URL for safe logging."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.password:
            netloc = f"{parsed.username}:***@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urllib.parse.urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
        return url
    except Exception:
        return "<DATABASE_URL masked>"


def normalize_target_url(url: str) -> str:
    """Convert postgres:// or postgresql:// dialect to postgresql+psycopg2:// with SSL enforcement."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if "sslmode=" not in url and "?" in url:
        url = f"{url}&sslmode=require"
    elif "sslmode=" not in url:
        url = f"{url}?sslmode=require"
    return url


def execute_multi_row_insert(
    session,
    table_name: str,
    cols: List[str],
    rows: List[Dict[str, Any]],
    chunk_size: int,
    json_cols: Set[str] = None,
    bool_cols: Set[str] = None
) -> Tuple[int, int, float]:
    """
    Executes batched multi-row parameterized INSERT statements inside the current transaction.
    Emits SQL: INSERT INTO <table> (c1, c2, ...) VALUES (:p0_c1, :p0_c2, ...), (:p1_c1, :p1_c2, ...), ...
    Guarantees exactly ceil(len(rows) / chunk_size) network round-trips!
    Returns: (row_count, num_statements, elapsed_seconds)
    """
    if not rows:
        return 0, 0, 0.0
    json_cols = json_cols or set()
    bool_cols = bool_cols or set()
    num_statements = 0
    t0 = time.time()
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        val_clauses = []
        params = {}
        for r_idx, row in enumerate(chunk):
            p_cols = []
            for c in cols:
                p_name = f"p_{r_idx}_{c}"
                val = row.get(c)
                if c in json_cols:
                    if val is not None and isinstance(val, str) and val.strip().lower() in ("null", "", "none"):
                        val = None
                    elif val is not None and not isinstance(val, str):
                        val = json.dumps(val)
                    params[p_name] = val
                    p_cols.append(f"CAST(:{p_name} AS json)")
                elif c in bool_cols:
                    params[p_name] = bool(val) if val is not None else None
                    p_cols.append(f":{p_name}")
                else:
                    params[p_name] = val
                    p_cols.append(f":{p_name}")
            val_clauses.append(f"({', '.join(p_cols)})")
        
        sql = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES {', '.join(val_clauses)}"
        session.execute(text(sql), params)
        num_statements += 1
    elapsed = time.time() - t0
    return len(rows), num_statements, elapsed


def run_migration(source_url: str, target_url: str, dry_run: bool = True, confirm: bool = False):
    target_url = normalize_target_url(target_url)
    masked_source = mask_url(source_url)
    masked_target = mask_url(target_url)

    logger.info("==================================================")
    logger.info("MarkMint Verified Corpus Migration Initiated")
    logger.info("Source: %s", masked_source)
    logger.info("Target: %s", masked_target)
    logger.info("Execution Mode: %s", "DRY-RUN (WILL ROLLBACK)" if dry_run else "LIVE MUTATION")
    logger.info("==================================================")

    if not dry_run and not confirm:
        logger.error("FATAL: Live mutation requires explicit --confirm-production-mutation flag. Aborting.")
        sys.exit(1)

    source_engine = create_engine(source_url)
    target_engine = create_engine(target_url)

    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)

    source_db = SourceSession()
    target_db = TargetSession()

    try:
        # ==================================================
        # 1. VALIDATE SOURCE PRECONDITIONS (SQLite)
        # ==================================================
        logger.info("[Step 1/10] Validating local source preconditions...")
        source_counts = {
            t: source_db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            for t in [
                "courses", "syllabuses", "units", "topics", "concepts",
                "documents", "document_provenances", "exams", "sections",
                "questions", "study_evidences", "question_families",
                "question_family_memberships", "curriculum_mappings"
            ]
        }
        
        expected_source = {
            "courses": 23, "syllabuses": 23, "units": 44, "topics": 72, "concepts": 72,
            "documents": 689, "document_provenances": 1400, "exams": 264, "sections": 743,
            "questions": 7385, "study_evidences": 4937, "question_families": 6103,
            "question_family_memberships": 7385, "curriculum_mappings": 2810
        }

        for t, exp in expected_source.items():
            act = source_counts.get(t, 0)
            if act != exp:
                raise ValueError(f"Source validation failure on '{t}': actual={act} != expected={exp}")

        # Local FK integrity check
        fk_errors = source_db.execute(text("PRAGMA foreign_key_check")).fetchall()
        if fk_errors:
            raise ValueError(f"Source database has {len(fk_errors)} foreign key violations!")
        logger.info("Source database passed all 14 entity count checks and 0 FK violations.")

        # ==================================================
        # 2. VALIDATE TARGET PRECONDITIONS (PostgreSQL)
        # ==================================================
        logger.info("[Step 2/10] Validating remote target preconditions...")
        
        def get_target_count(tbl: str) -> int:
            try:
                return target_db.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar() or 0
            except Exception:
                return 0

        target_courses = get_target_count("courses")
        target_curriculum = get_target_count("curriculum_mappings")
        target_student_topic = get_target_count("student_topic_progress")
        target_student_resource = get_target_count("student_resource_progress")
        target_units = get_target_count("units")
        target_topics = get_target_count("topics")

        logger.info("Target Current Baseline: courses=%d, curriculum_mappings=%d, units=%d, topics=%d, student_progress=%d",
                    target_courses, target_curriculum, target_units, target_topics, target_student_topic)

        if target_courses != 12:
            raise ValueError(f"Target baseline mismatch: expected exactly 12 courses, found {target_courses}")
        if target_curriculum != 2810:
            raise ValueError(f"Target baseline mismatch: expected exactly 2,810 curriculum_mappings, found {target_curriculum}")
        if target_topics != 72:
            raise ValueError(f"Target baseline mismatch: expected exactly 72 topics, found {target_topics}")
        if target_units != 33:
            raise ValueError(f"Target baseline mismatch: expected exactly 33 units, found {target_units}")

        # Ensure no unit ID > 33 exists on target
        units_above_33 = target_db.execute(text("SELECT COUNT(*) FROM units WHERE id > 33")).scalar()
        if units_above_33 > 0:
            raise ValueError(f"Target baseline mismatch: expected 0 units with ID > 33, found {units_above_33}")

        logger.info("Remote baseline verified: exactly 12 courses, 33 units (IDs 1-33), 72 topics, 2,810 curriculum mappings, %d student progress row(s).", target_student_topic)

        # ==================================================
        # 3. INSERT COURSES 13-23
        # ==================================================
        logger.info("[Step 3/10] Inserting Courses 13-23...")
        new_courses = source_db.execute(
            text("SELECT id, name, code, canonical_code, regulation_year, department FROM courses WHERE id > 12 ORDER BY id")
        ).mappings().all()

        for c in new_courses:
            target_db.execute(
                text("""
                    INSERT INTO courses (id, name, code, canonical_code, regulation_year, department)
                    VALUES (:id, :name, :code, :canonical_code, :regulation_year, :department)
                """),
                dict(c)
            )
        logger.info("Inserted %d new courses (IDs 13-23).", len(new_courses))

        # ==================================================
        # 4. INSERT SYLLABUSES 13-23 & RECONCILE UNITS (DELETE >=34, INSERT 34-44)
        # ==================================================
        logger.info("[Step 4/10] Reconciling syllabuses and units...")
        # Syllabuses 13-23
        new_syll = source_db.execute(
            text("SELECT id, course_id, version FROM syllabuses WHERE id > 12 ORDER BY id")
        ).mappings().all()
        for s in new_syll:
            target_db.execute(
                text("INSERT INTO syllabuses (id, course_id, version) VALUES (:id, :course_id, :version)"),
                dict(s)
            )
        logger.info("Inserted %d new syllabuses (IDs 13-23).", len(new_syll))

        # Delete unused prototype units >= 34
        # Verify first that 0 topics reference them
        referenced_u_count = target_db.execute(
            text("SELECT COUNT(*) FROM topics WHERE unit_id >= 34")
        ).scalar()
        if referenced_u_count > 0:
            raise ValueError(f"Safety violation: {referenced_u_count} topics reference units >= 34 on target!")

        del_units = target_db.execute(text("DELETE FROM units WHERE id >= 34")).rowcount
        logger.info("Deleted %d unused prototype units (IDs >= 34).", del_units)

        # Insert canonical units 34-44
        new_units = source_db.execute(
            text("SELECT id, syllabus_id, name, number FROM units WHERE id >= 34 ORDER BY id")
        ).mappings().all()
        for u in new_units:
            target_db.execute(
                text("INSERT INTO units (id, syllabus_id, name, number) VALUES (:id, :syllabus_id, :name, :number)"),
                dict(u)
            )
        logger.info("Inserted %d canonical units (IDs 34-44). Total units on target is now 44.", len(new_units))

        # ==================================================
        # 5. SCOPED DELETION OF LEGACY CORPUS TABLES
        # ==================================================
        logger.info("[Step 5/10] Performing scoped deletion of legacy corpus tables in reverse dependency order...")
        corpus_delete_order = [
            "question_family_memberships",
            "evidences",
            "question_concept",
            "question_topic",
            "questions",
            "sections",
            "exams",
            "study_evidences",
            "question_families",
            "document_provenances",
            "documents"
        ]

        if target_student_resource > 0:
            logger.warning("Target has %d student_resource_progress rows; preserving.", target_student_resource)
        
        del_counts = {}
        for tbl in corpus_delete_order:
            rc = target_db.execute(text(f"DELETE FROM {tbl}")).rowcount
            del_counts[tbl] = rc
            logger.info("  - Deleted %5d legacy rows from %s", rc, tbl)

        # ==================================================
        # 6. BULK INSERT CANONICAL AUDITED CORPUS
        # ==================================================
        logger.info("[Step 6/10] Bulk inserting canonical audited corpus in strict dependency order (batched multi-row)...")
        timing_metrics = []
        
        # 1. documents (689)
        doc_cols = [
            "id", "source", "original_url", "title", "semester", "subject", "owner_id",
            "processing_status", "uploaded_at", "resource_type", "year", "exam_type",
            "document_hash", "extraction_status", "extraction_confidence"
        ]
        docs = [dict(r) for r in source_db.execute(text(
            f"SELECT {', '.join(doc_cols)} FROM documents ORDER BY id"
        )).mappings().all()]
        rc, stmts, el = execute_multi_row_insert(target_db, "documents", doc_cols, docs, chunk_size=250)
        timing_metrics.append(("documents", rc, 250, stmts, el))
        logger.info("  + Inserted %5d documents in %d statements (%.2fs)", rc, stmts, el)

        # 2. document_provenances (1,400)
        prov_cols = ["id", "document_id", "source_site", "source_url", "resolved_url", "source_priority", "created_at"]
        provs = [dict(r) for r in source_db.execute(text(
            f"SELECT {', '.join(prov_cols)} FROM document_provenances ORDER BY id"
        )).mappings().all()]
        rc, stmts, el = execute_multi_row_insert(target_db, "document_provenances", prov_cols, provs, chunk_size=500)
        timing_metrics.append(("document_provenances", rc, 500, stmts, el))
        logger.info("  + Inserted %5d document_provenances in %d statements (%.2fs)", rc, stmts, el)

        # 3. question_families (6,103)
        fam_cols = ["id", "canonical_name", "description", "subject", "first_seen_year", "latest_seen_year", "repetition_type"]
        families = [dict(r) for r in source_db.execute(text(
            f"SELECT {', '.join(fam_cols)} FROM question_families ORDER BY id"
        )).mappings().all()]
        rc, stmts, el = execute_multi_row_insert(target_db, "question_families", fam_cols, families, chunk_size=500)
        timing_metrics.append(("question_families", rc, 500, stmts, el))
        logger.info("  + Inserted %5d question_families in %d statements (%.2fs)", rc, stmts, el)

        # 4. study_evidences (4,937)
        ev_cols = ["id", "document_id", "concept_id", "knowledge_type", "content", "original_text", "page_number", "confidence"]
        evs = [dict(r) for r in source_db.execute(text(
            f"SELECT {', '.join(ev_cols)} FROM study_evidences ORDER BY id"
        )).mappings().all()]
        rc, stmts, el = execute_multi_row_insert(target_db, "study_evidences", ev_cols, evs, chunk_size=500)
        timing_metrics.append(("study_evidences", rc, 500, stmts, el))
        logger.info("  + Inserted %5d study_evidences in %d statements (%.2fs)", rc, stmts, el)

        # 5. exams (264)
        exam_cols = ["id", "course_id", "document_id", "year", "term", "assessment_type"]
        exams = [dict(r) for r in source_db.execute(text(
            f"SELECT {', '.join(exam_cols)} FROM exams ORDER BY id"
        )).mappings().all()]
        rc, stmts, el = execute_multi_row_insert(target_db, "exams", exam_cols, exams, chunk_size=250)
        timing_metrics.append(("exams", rc, 250, stmts, el))
        logger.info("  + Inserted %5d exams in %d statements (%.2fs)", rc, stmts, el)

        # 6. sections (743)
        sec_cols = ["id", "exam_id", "name", "instructions"]
        sections = [dict(r) for r in source_db.execute(text(
            f"SELECT {', '.join(sec_cols)} FROM sections ORDER BY id"
        )).mappings().all()]
        rc, stmts, el = execute_multi_row_insert(target_db, "sections", sec_cols, sections, chunk_size=250)
        timing_metrics.append(("sections", rc, 250, stmts, el))
        logger.info("  + Inserted %5d sections in %d statements (%.2fs)", rc, stmts, el)

        # 7. questions (7,385)
        q_cols = [
            "id", "section_id", "family_id", "question_number", "original_text", "normalized_text",
            "marks", "is_alternative", "structured_content", "needs_review", "extraction_method",
            "extraction_confidence", "question_type", "cognitive_level", "difficulty",
            "classification_confidence", "classification_input", "classification_metadata"
        ]
        questions = [dict(r) for r in source_db.execute(text(
            f"SELECT {', '.join(q_cols)} FROM questions ORDER BY id"
        )).mappings().all()]
        rc, stmts, el = execute_multi_row_insert(
            target_db, "questions", q_cols, questions, chunk_size=250,
            json_cols={"structured_content", "classification_metadata"},
            bool_cols={"is_alternative", "needs_review"}
        )
        timing_metrics.append(("questions", rc, 250, stmts, el))
        logger.info("  + Inserted %5d questions in %d statements (%.2fs)", rc, stmts, el)

        # 8. question_family_memberships (7,385)
        qfm_cols = ["id", "question_id", "family_id", "match_type", "similarity_score", "decision_method", "algorithm_version"]
        qfms = [dict(r) for r in source_db.execute(text(
            f"SELECT {', '.join(qfm_cols)} FROM question_family_memberships ORDER BY id"
        )).mappings().all()]
        rc, stmts, el = execute_multi_row_insert(target_db, "question_family_memberships", qfm_cols, qfms, chunk_size=500)
        timing_metrics.append(("question_family_memberships", rc, 500, stmts, el))
        logger.info("  + Inserted %5d question_family_memberships in %d statements (%.2fs)", rc, stmts, el)

        # 9. question_topic (17)
        qt_cols = ["question_id", "topic_id"]
        qts = [dict(r) for r in source_db.execute(text(
            f"SELECT {', '.join(qt_cols)} FROM question_topic"
        )).mappings().all()]
        if qts:
            rc, stmts, el = execute_multi_row_insert(target_db, "question_topic", qt_cols, qts, chunk_size=250)
            timing_metrics.append(("question_topic", rc, 250, stmts, el))
            logger.info("  + Inserted %5d question_topic links in %d statements (%.2fs)", rc, stmts, el)

        # Performance summary table
        logger.info("--------------------------------------------------------------------------------")
        logger.info("CORPUS BULK INSERT PERFORMANCE VERIFICATION:")
        logger.info("%-28s %-10s %-12s %-12s %-12s", "Table", "Rows", "Chunk Size", "Statements", "Elapsed (s)")
        logger.info("--------------------------------------------------------------------------------")
        total_rows = 0
        total_stmts = 0
        total_elapsed = 0.0
        for tbl, r_count, ch_size, s_count, s_el in timing_metrics:
            total_rows += r_count
            total_stmts += s_count
            total_elapsed += s_el
            logger.info("%-28s %-10d %-12d %-12d %-12.2f", tbl, r_count, ch_size, s_count, s_el)
        logger.info("--------------------------------------------------------------------------------")
        logger.info("%-28s %-10d %-12s %-12d %-12.2f", "TOTAL", total_rows, "-", total_stmts, total_elapsed)
        logger.info("--------------------------------------------------------------------------------")

        # ==================================================
        # 7. EXACT KEY CURRICULUM MAPPINGS UPDATE (240 ROWS)
        # ==================================================
        logger.info("[Step 7/10] Updating exactly 240 curriculum mappings using composite business key...")
        updates = source_db.execute(text("""
            SELECT branch_name, semester, curriculum_id, course_id, status 
            FROM curriculum_mappings 
            WHERE course_id >= 13
        """)).mappings().all()

        if len(updates) != 240:
            raise ValueError(f"Expected 240 curriculum mapping updates for Courses 13-23, found {len(updates)}!")

        target_db.execute(text("CREATE TEMP TABLE temp_cm_updates (branch_name text, semester int, curriculum_id text, course_id int, status text)"))
        cm_cols = ["branch_name", "semester", "curriculum_id", "course_id", "status"]
        execute_multi_row_insert(target_db, "temp_cm_updates", cm_cols, [dict(u) for u in updates], chunk_size=250)
        res = target_db.execute(text("""
            UPDATE curriculum_mappings cm
            SET course_id = t.course_id, status = t.status
            FROM temp_cm_updates t
            WHERE cm.branch_name = t.branch_name AND cm.semester = t.semester AND cm.curriculum_id = t.curriculum_id
        """))
        total_updated = res.rowcount
        target_db.execute(text("DROP TABLE temp_cm_updates"))
        logger.info("Updated %d curriculum_mappings via batched operation.", total_updated)

        if total_updated != 240:
            raise ValueError(f"Expected exactly 240 rows updated in curriculum_mappings, actually updated: {total_updated}")

        # Verify mapping status distribution
        matched_cnt = target_db.execute(text("SELECT COUNT(*) FROM curriculum_mappings WHERE status = 'MATCHED'")).scalar()
        ambig_cnt = target_db.execute(text("SELECT COUNT(*) FROM curriculum_mappings WHERE status = 'AMBIGUOUS'")).scalar()
        unmatched_cnt = target_db.execute(text("SELECT COUNT(*) FROM curriculum_mappings WHERE status = 'UNMATCHED'")).scalar()
        
        logger.info("Curriculum Mappings Distribution: MATCHED=%d, AMBIGUOUS=%d, UNMATCHED=%d (Total=%d)",
                    matched_cnt, ambig_cnt, unmatched_cnt, matched_cnt + ambig_cnt + unmatched_cnt)
        if matched_cnt != 490 or ambig_cnt != 40 or unmatched_cnt != 2280:
            raise ValueError(f"Curriculum mapping post-update counts unexpected: matched={matched_cnt} (exp 490), ambig={ambig_cnt} (exp 40), unmatched={unmatched_cnt} (exp 2280)")

        # ==================================================
        # 8. PRESERVE USER STATE (DO NOT INSERT TEST FIXTURES)
        # ==================================================
        logger.info("[Step 8/10] Preserving user progress (excluding test fixtures student_novice_99 / student_master_99)...")
        del_test_prog = target_db.execute(text(
            "DELETE FROM student_topic_progress WHERE student_id IN ('student_novice_99', 'student_master_99')"
        )).rowcount
        if del_test_prog > 0:
            logger.info("Removed %d pre-existing test fixture rows from student_topic_progress.", del_test_prog)

        final_prog_cnt = target_db.execute(text("SELECT COUNT(*) FROM student_topic_progress")).scalar()
        logger.info("Student progress state preserved (total rows: %d).", final_prog_cnt)

        # ==================================================
        # 9. DYNAMIC POSTGRESQL SEQUENCE REPAIR
        # ==================================================
        logger.info("[Step 9/10] Resynchronizing all PostgreSQL sequences dynamically...")
        tables_with_id = target_db.execute(text("""
            SELECT c.table_name 
            FROM information_schema.columns c
            JOIN information_schema.tables t ON c.table_name = t.table_name AND c.table_schema = t.table_schema
            WHERE c.table_schema = 'public' 
              AND t.table_type = 'BASE TABLE' 
              AND c.column_name = 'id'
        """)).fetchall()

        resynced_count = 0
        for (tbl,) in tables_with_id:
            seq = target_db.execute(text(f"SELECT pg_get_serial_sequence('{tbl}', 'id')")).scalar()
            if seq:
                max_id = target_db.execute(text(f"SELECT COALESCE(MAX(id), 1) FROM {tbl}")).scalar()
                target_db.execute(text(f"SELECT setval('{seq}', {max_id}, true)"))
                resynced_count += 1
        logger.info("Resynchronized %d table sequences dynamically to MAX(id).", resynced_count)

        # ==================================================
        # 10. POST-MIGRATION ASSERTIONS & ORPHAN CHECKS
        # ==================================================
        logger.info("[Step 10/10] Executing final integrity assertions and orphan checks...")
        final_counts = {
            t: target_db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            for t in [
                "courses", "syllabuses", "units", "topics", "concepts",
                "documents", "document_provenances", "exams", "sections",
                "questions", "study_evidences", "question_families",
                "question_family_memberships", "curriculum_mappings"
            ]
        }

        expected_final = {
            "courses": 23, "syllabuses": 23, "units": 44, "topics": 72, "concepts": 72,
            "documents": 689, "document_provenances": 1400, "exams": 264, "sections": 743,
            "questions": 7385, "study_evidences": 4937, "question_families": 6103,
            "question_family_memberships": 7385, "curriculum_mappings": 2810
        }

        for t, exp in expected_final.items():
            act = final_counts.get(t, 0)
            if act != exp:
                raise ValueError(f"Final integrity violation on '{t}': actual={act} != expected={exp}")

        orphan_checks = [
            ("orphan exams -> courses", "SELECT COUNT(*) FROM exams e LEFT JOIN courses c ON e.course_id = c.id WHERE c.id IS NULL"),
            ("orphan exams -> documents", "SELECT COUNT(*) FROM exams e LEFT JOIN documents d ON e.document_id = d.id WHERE e.document_id IS NOT NULL AND d.id IS NULL"),
            ("orphan sections -> exams", "SELECT COUNT(*) FROM sections s LEFT JOIN exams e ON s.exam_id = e.id WHERE e.id IS NULL"),
            ("orphan questions -> sections", "SELECT COUNT(*) FROM questions q LEFT JOIN sections s ON q.section_id = s.id WHERE s.id IS NULL"),
            ("orphan questions -> families", "SELECT COUNT(*) FROM questions q LEFT JOIN question_families f ON q.family_id = f.id WHERE q.family_id IS NOT NULL AND f.id IS NULL"),
            ("orphan QFM -> questions", "SELECT COUNT(*) FROM question_family_memberships qfm LEFT JOIN questions q ON qfm.question_id = q.id WHERE q.id IS NULL"),
            ("orphan QFM -> families", "SELECT COUNT(*) FROM question_family_memberships qfm LEFT JOIN question_families f ON qfm.family_id = f.id WHERE f.id IS NULL"),
            ("orphan provenances -> documents", "SELECT COUNT(*) FROM document_provenances dp LEFT JOIN documents d ON dp.document_id = d.id WHERE d.id IS NULL"),
            ("orphan study_evidences -> documents", "SELECT COUNT(*) FROM study_evidences se LEFT JOIN documents d ON se.document_id = d.id WHERE d.id IS NULL")
        ]

        for desc, qry in orphan_checks:
            cnt = target_db.execute(text(qry)).scalar()
            if cnt != 0:
                raise ValueError(f"Referential integrity failure: {cnt} {desc} detected!")

        logger.info("Integrity check complete: 0 orphan entities, 100% referential consistency.")

        if dry_run:
            logger.info("==================================================")
            logger.info("DRY-RUN COMPLETE: ROLLING BACK ALL CHANGES.")
            logger.info("NO PERSISTENT MUTATIONS WERE APPLIED TO TARGET.")
            logger.info("==================================================")
            target_db.rollback()
        else:
            logger.info("==================================================")
            logger.info("LIVE MIGRATION VALIDATED: COMMITTING TRANSACTION...")
            target_db.commit()
            logger.info("TRANSACTION COMMITTED SUCCESSFULLY!")
            logger.info("==================================================")

    except Exception as e:
        target_db.rollback()
        logger.error("FATAL ERROR DURING MIGRATION: %s", e)
        logger.error("TRANSACTION ROLLED BACK COMPLETELY.")
        sys.exit(1)
    finally:
        source_db.close()
        target_db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MarkMint Verified Corpus PostgreSQL Migration")
    parser.add_argument("source", help="Source SQLite URL (e.g. sqlite:///./production_corpus.db)")
    parser.add_argument("target", help="Target PostgreSQL URL (e.g. postgresql://user:pass@host/db)")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Run inside a transaction and rollback at the end")
    parser.add_argument("--confirm-production-mutation", action="store_true", default=False, help="Required flag to commit live mutation")

    args = parser.parse_args()
    is_dry_run = args.dry_run or not args.confirm_production_mutation
    run_migration(args.source, args.target, dry_run=is_dry_run, confirm=args.confirm_production_mutation)
