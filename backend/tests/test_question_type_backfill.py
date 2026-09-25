"""
Comprehensive Integration & Safety Tests for Question Type Backfill and Exam DNA Integration.
"""

import pytest
import sqlite3
import tempfile
import os

from backend.services.question_type_classifier import (
    DeterministicQuestionTypeClassifier,
    QuestionType,
    ClassificationConfidence,
)
from scripts.migration.backfill_question_types import execute_backfill, compute_safety_checksums
from backend.services.dna.analyzer import DNAAnalyzerService


@pytest.fixture
def temp_corpus_db():
    """Creates a temporary sqlite database replicating the production schema."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE courses (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            code VARCHAR,
            canonical_code VARCHAR,
            regulation_year INTEGER,
            department VARCHAR
        );

        CREATE TABLE exams (
            id INTEGER PRIMARY KEY,
            course_id INTEGER NOT NULL,
            document_id INTEGER,
            year INTEGER,
            term VARCHAR,
            assessment_type VARCHAR,
            track_id INTEGER
        );

        CREATE TABLE sections (
            id INTEGER PRIMARY KEY,
            exam_id INTEGER NOT NULL,
            name VARCHAR,
            instructions TEXT
        );

        CREATE TABLE questions (
            id INTEGER PRIMARY KEY,
            section_id INTEGER NOT NULL,
            family_id INTEGER,
            question_number VARCHAR,
            original_text TEXT,
            normalized_text TEXT,
            marks FLOAT,
            is_alternative BOOLEAN DEFAULT 0,
            structured_content JSON,
            needs_review BOOLEAN DEFAULT 0,
            extraction_method VARCHAR,
            extraction_confidence FLOAT,
            question_type VARCHAR,
            cognitive_level VARCHAR,
            difficulty FLOAT,
            classification_confidence FLOAT,
            classification_input TEXT,
            classification_metadata JSON
        );
    """)

    # Seed Courses
    cursor.execute("INSERT INTO courses (id, name) VALUES (1, 'Calculus'), (2, 'Programming in C')")
    # Seed Exams
    cursor.execute("INSERT INTO exams (id, course_id, year, assessment_type) VALUES (10, 1, 2023, 'END_SEM'), (20, 2, 2023, 'END_SEM')")
    # Seed Sections
    cursor.execute("INSERT INTO sections (id, exam_id, name) VALUES (100, 10, 'Part A'), (101, 10, 'Part B'), (200, 20, 'Part B')")

    # Seed Questions:
    # 1. High-confidence MCQ
    cursor.execute("INSERT INTO questions (id, section_id, marks, original_text, question_type) VALUES (1, 100, 1.0, 'What is derivative? (A) Rate of change (B) Area (C) Volume (D) Density', NULL)")
    # 2. High-confidence Numerical
    cursor.execute("INSERT INTO questions (id, section_id, marks, original_text, question_type) VALUES (2, 101, 8.0, 'Find the eigenvalues and eigenvectors of matrix A', NULL)")
    # 3. High-confidence Programming
    cursor.execute("INSERT INTO questions (id, section_id, marks, original_text, question_type) VALUES (3, 200, 10.0, 'Write a C program to implement bubble sort', NULL)")
    # 4. Pre-classified / Curated Question (MUST NOT BE OVERWRITTEN)
    cursor.execute("INSERT INTO questions (id, section_id, marks, original_text, question_type) VALUES (4, 101, 8.0, 'Curated conceptual question', 'Custom Curated Type')")
    # 5. Ambiguous / Malformed text question
    cursor.execute("INSERT INTO questions (id, section_id, marks, original_text, question_type) VALUES (5, 101, 8.0, 'xyz', NULL)")
    # 6. Missing marks question with clear stem
    cursor.execute("INSERT INTO questions (id, section_id, marks, original_text, question_type) VALUES (6, 101, NULL, 'Distinguish between stack and queue', NULL)")

    conn.commit()
    conn.close()

    yield path

    if os.path.exists(path):
        os.remove(path)


def test_staged_backfill_execution_and_idempotence(temp_corpus_db):
    """Verifies Stage 1 and Stage 2 execution, safety, and idempotence."""
    # 1. Execute Stage 1 (High confidence only)
    res1 = execute_backfill(stage=1, dry_run=False, db_path=temp_corpus_db)
    assert res1["updated_count"] == 4  # Questions 1, 2, 3, 6
    assert res1["skipped_already_classified"] == 1  # Question 4

    conn = sqlite3.connect(temp_corpus_db)
    cursor = conn.cursor()
    cursor.execute("SELECT id, question_type FROM questions ORDER BY id ASC")
    types_stage1 = dict(cursor.fetchall())
    conn.close()

    assert types_stage1[1] == QuestionType.OBJECTIVE_MCQ.value
    assert types_stage1[2] == QuestionType.NUMERICAL.value
    assert types_stage1[3] == QuestionType.PROGRAMMING.value
    assert types_stage1[4] == "Custom Curated Type"  # Preserved!
    assert types_stage1[5] is None  # Ambiguous: deferred to Stage 2
    assert types_stage1[6] == QuestionType.COMPARISON.value  # High conf comparison despite missing marks

    # 2. Idempotent rerun of Stage 1
    res1_rerun = execute_backfill(stage=1, dry_run=False, db_path=temp_corpus_db)
    assert res1_rerun["updated_count"] == 0

    # 3. Execute Stage 2 (Remaining + Unclassified fallback)
    res2 = execute_backfill(stage=2, dry_run=False, db_path=temp_corpus_db)
    assert res2["updated_count"] == 1  # Question 5

    conn = sqlite3.connect(temp_corpus_db)
    cursor = conn.cursor()
    cursor.execute("SELECT id, question_type FROM questions ORDER BY id ASC")
    types_stage2 = dict(cursor.fetchall())
    conn.close()

    assert types_stage2[5] == QuestionType.UNCLASSIFIED.value
    assert types_stage2[4] == "Custom Curated Type"  # Still strictly preserved!

    # 4. Idempotent rerun of Stage 2
    res2_rerun = execute_backfill(stage=2, dry_run=False, db_path=temp_corpus_db)
    assert res2_rerun["updated_count"] == 0
    assert res2_rerun["skipped_already_classified"] == 6


def test_backfill_safety_invariants(temp_corpus_db):
    """Verifies checksums and invariants before and after backfill."""
    conn = sqlite3.connect(temp_corpus_db)
    before = compute_safety_checksums(conn)
    conn.close()

    execute_backfill(stage=1, dry_run=False, db_path=temp_corpus_db)
    execute_backfill(stage=2, dry_run=False, db_path=temp_corpus_db)

    conn = sqlite3.connect(temp_corpus_db)
    after = compute_safety_checksums(conn)
    conn.close()

    assert before["count"] == after["count"]
    assert before["total_marks"] == after["total_marks"]
    assert before["total_text_len"] == after["total_text_len"]
    assert before["count_with_family"] == after["count_with_family"]
    assert before["distinct_sections"] == after["distinct_sections"]


def test_empty_corpus_backfill():
    """Verifies backfill runs safely without errors on an empty database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE sections (id INTEGER PRIMARY KEY, name VARCHAR);
        CREATE TABLE questions (id INTEGER PRIMARY KEY, section_id INTEGER, marks FLOAT, original_text TEXT, question_type VARCHAR, family_id INTEGER);
    """)
    conn.commit()
    conn.close()

    res = execute_backfill(stage=1, dry_run=False, db_path=path)
    assert res["total_questions"] == 0
    assert res["updated_count"] == 0

    if os.path.exists(path):
        os.remove(path)


def test_exam_dna_integration_with_backfilled_data():
    """Verifies that Exam DNA correctly analyzes backfilled question types."""
    synthetic_exams = [
        {
            "id": 101,
            "year": 2023,
            "exam_type": "END_SEM",
            "course_id": 1,
            "questions": [
                {"id": 1, "marks": 1.0, "is_alternative": False, "question_type": QuestionType.OBJECTIVE_MCQ.value},
                {"id": 2, "marks": 8.0, "is_alternative": False, "question_type": QuestionType.NUMERICAL.value},
                {"id": 3, "marks": 8.0, "is_alternative": False, "question_type": QuestionType.DERIVATION.value},
                {"id": 4, "marks": 8.0, "is_alternative": False, "question_type": QuestionType.UNCLASSIFIED.value},
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(synthetic_exams, target_course_id=1)
    type_map = {qt.question_type: qt for qt in dna.question_types}

    assert QuestionType.OBJECTIVE_MCQ.value in type_map
    assert QuestionType.NUMERICAL.value in type_map
    assert QuestionType.DERIVATION.value in type_map
    assert QuestionType.UNCLASSIFIED.value in type_map

    # Check percentages
    assert type_map[QuestionType.NUMERICAL.value].count == 1
    assert type_map[QuestionType.NUMERICAL.value].percentage == 0.25
    # Numerical marks: 8.0 out of 25.0 = 32%
    assert round(type_map[QuestionType.NUMERICAL.value].marks_weighting, 2) == 0.32
