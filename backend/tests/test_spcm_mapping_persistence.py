"""
Tests for SPCM question-to-topic persistence, idempotency, and conflict preservation.
Uses an isolated temporary SQLite database fixture to verify zero unwanted side-effects.
"""
import shutil
import sqlite3
from pathlib import Path
import pytest
from scripts.curriculum.map_spcm_questions_to_topics import run_spcm_mapping


@pytest.fixture
def temp_spcm_db(tmp_path: Path) -> str:
    """Create an isolated temporary copy of production_corpus.db starting with 0 SPCM mappings."""
    src = Path("production_corpus.db")
    dst = tmp_path / "test_spcm_corpus.db"
    shutil.copy(src, dst)
    conn = sqlite3.connect(str(dst))
    conn.execute("""
        DELETE FROM question_topic
        WHERE question_id IN (
            SELECT q.id FROM questions q
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 13
        )
    """)
    conn.commit()
    conn.close()
    return str(dst)


def test_spcm_dry_run_does_not_mutate_db(temp_spcm_db: str) -> None:
    """Verifies that --dry-run executes zero database mutations."""
    res = run_spcm_mapping(temp_spcm_db, apply_changes=False, verbose_samples=False)
    assert res["rows_to_insert"] > 0
    assert res["mutations_executed"] == 0

    conn = sqlite3.connect(temp_spcm_db)
    count = conn.execute("""
        SELECT count(*) FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 13
    """).fetchone()[0]
    conn.close()
    assert count == 0


def test_spcm_apply_inserts_only_missing_mappings(temp_spcm_db: str) -> None:
    """Verifies that --apply inserts missing mappings while keeping Calculus and Chemistry invariant."""
    conn = sqlite3.connect(temp_spcm_db)
    calc_before = conn.execute("""
        SELECT count(*) FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 1
    """).fetchone()[0]
    chem_before = conn.execute("""
        SELECT count(*) FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 2
    """).fetchone()[0]
    conn.close()

    res = run_spcm_mapping(temp_spcm_db, apply_changes=True, verbose_samples=False)
    assert res["mutations_executed"] > 500
    assert res["total_active_spcm_mappings"] == res["mutations_executed"]

    conn = sqlite3.connect(temp_spcm_db)
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

    assert calc_before == calc_after, "Calculus mappings must remain completely invariant"
    assert chem_before == chem_after, "Chemistry mappings must remain completely invariant"


def test_spcm_idempotent_rerun_does_not_duplicate_rows(temp_spcm_db: str) -> None:
    """Verifies that running apply multiple times does not insert duplicate rows."""
    res1 = run_spcm_mapping(temp_spcm_db, apply_changes=True, verbose_samples=False)
    assert res1["mutations_executed"] > 0

    res2 = run_spcm_mapping(temp_spcm_db, apply_changes=True, verbose_samples=False)
    assert res2["mutations_executed"] == 0
    assert res2["rows_to_insert"] == 0
    assert res2["total_active_spcm_mappings"] == res1["total_active_spcm_mappings"]


def test_spcm_conflicting_mapping_is_preserved_not_clobbered(temp_spcm_db: str) -> None:
    """Verifies that an existing mapping is preserved even if the classifier proposes a different topic."""
    conn = sqlite3.connect(temp_spcm_db)
    # Find an SPCM question
    q_id = conn.execute("""
        SELECT q.id FROM questions q
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 13
        LIMIT 1
    """).fetchone()[0]

    # Assign it intentionally to an arbitrary topic
    target_topic_id = 73  # Classical Free Electron Theory
    conn.execute("INSERT INTO question_topic (question_id, topic_id) VALUES (?, ?)", (q_id, target_topic_id))
    conn.commit()
    conn.close()

    res = run_spcm_mapping(temp_spcm_db, apply_changes=True, verbose_samples=False)

    conn = sqlite3.connect(temp_spcm_db)
    current_topic = conn.execute(
        "SELECT topic_id FROM question_topic WHERE question_id = ?", (q_id,)
    ).fetchone()[0]
    conn.close()

    assert current_topic == target_topic_id, "Existing manual/prior mapping must be preserved"


def test_no_cross_course_mappings_exist(temp_spcm_db: str) -> None:
    """Verifies zero cross-course mappings exist for Course 13."""
    run_spcm_mapping(temp_spcm_db, apply_changes=True, verbose_samples=False)

    conn = sqlite3.connect(temp_spcm_db)
    violations = conn.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        JOIN topics t ON qt.topic_id = t.id
        JOIN units u ON t.unit_id = u.id
        JOIN syllabuses syl ON u.syllabus_id = syl.id
        WHERE e.course_id = 13 AND syl.course_id != 13
    """).fetchone()[0]
    conn.close()

    assert violations == 0, "No SPCM question may be mapped to a non-SPCM topic"
