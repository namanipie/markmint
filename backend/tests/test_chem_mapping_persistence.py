"""
Tests for Chemistry question-to-topic persistence, idempotency, and conflict preservation.
Uses an isolated temporary SQLite database fixture to verify zero database side-effects.
"""
import shutil
import sqlite3
from pathlib import Path
import pytest
from scripts.curriculum.map_chemistry_questions_to_topics import run_chemistry_mapping


@pytest.fixture
def temp_db(tmp_path: Path) -> str:
    """Create an isolated temporary copy of production_corpus.db starting from 0 Course 2 mappings."""
    src = Path("production_corpus.db")
    dst = tmp_path / "test_corpus.db"
    shutil.copy(src, dst)
    conn = sqlite3.connect(str(dst))
    conn.execute("""
        DELETE FROM question_topic
        WHERE question_id IN (
            SELECT q.id FROM questions q
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 2
        )
    """)
    conn.commit()
    conn.close()
    return str(dst)


def test_dry_run_does_not_mutate_db(temp_db: str) -> None:
    """Verifies that --dry-run writes 0 rows and leaves question_topic unchanged."""
    res = run_chemistry_mapping(temp_db, apply_changes=False, verbose_samples=False)
    assert res["to_insert_count"] > 0
    assert res["inserted_count"] == 0

    conn = sqlite3.connect(temp_db)
    c2_count = conn.execute("""
        SELECT count(*) FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 2
    """).fetchone()[0]
    conn.close()
    assert c2_count == 0


def test_apply_inserts_only_missing_mappings(temp_db: str) -> None:
    """Verifies that --apply inserts proposed mappings and preserves other courses."""
    conn = sqlite3.connect(temp_db)
    calc_before = conn.execute("""
        SELECT count(*) FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 1
    """).fetchone()[0]
    conn.close()
    assert calc_before == 17

    res = run_chemistry_mapping(temp_db, apply_changes=True, verbose_samples=False)
    assert res["inserted_count"] == res["to_insert_count"]
    assert res["inserted_count"] > 0

    conn = sqlite3.connect(temp_db)
    calc_after = conn.execute("""
        SELECT count(*) FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 1
    """).fetchone()[0]
    chem_after = conn.execute("""
        SELECT count(*) FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 2
    """).fetchone()[0]
    conn.close()

    assert calc_after == 17, "Calculus mappings must remain untouched!"
    assert chem_after == res["inserted_count"]


def test_idempotent_rerun_does_not_change_counts(temp_db: str) -> None:
    """Verifies that running --apply multiple times is strictly idempotent (0 new insertions on second pass)."""
    res1 = run_chemistry_mapping(temp_db, apply_changes=True, verbose_samples=False)
    assert res1["inserted_count"] > 0

    res2 = run_chemistry_mapping(temp_db, apply_changes=True, verbose_samples=False)
    assert res2["inserted_count"] == 0
    assert res2["preserved_existing_count"] == res1["inserted_count"]
    assert res2["to_insert_count"] == 0


def test_pre_existing_mapping_is_preserved_and_not_clobbered(temp_db: str) -> None:
    """Verifies a pre-existing manual/verified mapping is preserved."""
    conn = sqlite3.connect(temp_db)
    # Insert a manual mapping for Chemistry question 27 to Topic 45
    conn.execute("INSERT INTO question_topic (question_id, topic_id) VALUES (27, 45)")
    conn.commit()
    conn.close()

    res = run_chemistry_mapping(temp_db, apply_changes=True, verbose_samples=False)
    assert res["preserved_existing_count"] >= 1

    conn = sqlite3.connect(temp_db)
    topic_id = conn.execute("SELECT topic_id FROM question_topic WHERE question_id = 27").fetchone()[0]
    conn.close()
    assert topic_id == 45


def test_conflicting_classifier_proposal_does_not_overwrite_existing(temp_db: str) -> None:
    """Verifies that if an existing mapping conflicts with classifier proposal, existing mapping is PRESERVED."""
    conn = sqlite3.connect(temp_db)
    # Question 27 is Schrodinger (classifier proposes 45). Manually bind it to conflicting Topic 20
    conn.execute("INSERT INTO question_topic (question_id, topic_id) VALUES (27, 20)")
    conn.commit()
    conn.close()

    res = run_chemistry_mapping(temp_db, apply_changes=True, verbose_samples=False)
    assert res["conflicts_count"] >= 1
    assert any(c["question_id"] == 27 for c in res["conflicts"])

    # Verify DB still has existing topic 20 and was NOT overwritten by 45
    conn = sqlite3.connect(temp_db)
    topic_id = conn.execute("SELECT topic_id FROM question_topic WHERE question_id = 27").fetchone()[0]
    conn.close()
    assert topic_id == 20, "Existing conflicting mapping must be preserved!"


def test_no_duplicate_question_topic_rows(temp_db: str) -> None:
    """Verifies no duplicate (question_id, topic_id) pairs are created."""
    run_chemistry_mapping(temp_db, apply_changes=True, verbose_samples=False)

    conn = sqlite3.connect(temp_db)
    duplicates = conn.execute("""
        SELECT question_id, topic_id, count(*)
        FROM question_topic
        GROUP BY question_id, topic_id
        HAVING count(*) > 1
    """).fetchall()
    conn.close()
    assert len(duplicates) == 0, f"Found duplicate question_topic pairs: {duplicates}"
