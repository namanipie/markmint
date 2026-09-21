"""
Corpus Directory Integrity Test Suite.

Verifies:
1. corpus/Semester_{1..8} directory hierarchy exists
2. No Sem 3/4 courses in corpus/Semester_1 (specifically APP and AI are absent)
3. No Sem 1 courses in corpus/Semester_2 and no Sem 3 courses in corpus/Semester_2 (Microbiology is absent)
4. Sem 3 courses are properly placed under corpus/Semester_3
5. Sem 4 courses are properly placed under corpus/Semester_4
6. CurriculumResolver resolves known aliases and provides canonical_semester
7. Manifest paths point to existing files
"""

import os
import json
import pytest
from sqlalchemy.orm import Session
from backend.core.database import SessionLocal
from backend.services.scraper.curriculum_resolver import CurriculumResolver
from backend.services.scraper.models import CurriculumMatchState


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_semester_1_to_8_directories_exist():
    """Verify that corpus/Semester_1 through corpus/Semester_8 exist."""
    for sem in range(1, 9):
        sem_path = os.path.join("corpus", f"Semester_{sem}")
        assert os.path.exists(sem_path) and os.path.isdir(sem_path), f"Missing {sem_path}"


def test_semester_1_has_no_misplaced_courses():
    """Verify that Sem 2, 3, and 4 courses are NOT present in corpus/Semester_1."""
    sem1_path = os.path.join("corpus", "Semester_1")
    sem1_folders = [f.lower() for f in os.listdir(sem1_path) if os.path.isdir(os.path.join(sem1_path, f))]

    # Must NOT contain APP (Sem 3)
    assert not any("advanced programming practice" in f or "app" in f for f in sem1_folders), (
        "APP must not be in Semester_1"
    )
    # Must NOT contain AI (Sem 4)
    assert not any("artificial intelligence" in f for f in sem1_folders), (
        "Artificial Intelligence must not be in Semester_1"
    )
    # Must NOT contain ACCA (Sem 2)
    assert not any("advanced calculus and complex analysis" in f for f in sem1_folders), (
        "ACCA must not be in Semester_1"
    )


def test_semester_2_has_no_misplaced_courses():
    """Verify that Sem 3 courses like Microbiology are NOT present in corpus/Semester_2."""
    sem2_path = os.path.join("corpus", "Semester_2")
    sem2_folders = [f.lower() for f in os.listdir(sem2_path) if os.path.isdir(os.path.join(sem2_path, f))]

    # Must NOT contain Microbiology (Sem 3)
    assert not any("microbiology" in f for f in sem2_folders), (
        "Microbiology must not be in Semester_2"
    )


def test_semester_3_contains_canonical_courses():
    """Verify that Sem 3 contains APP, Microbiology, DSA, OS, COA."""
    sem3_path = os.path.join("corpus", "Semester_3")
    sem3_folders = [f.lower() for f in os.listdir(sem3_path) if os.path.isdir(os.path.join(sem3_path, f))]

    assert any("advanced programming practice" in f for f in sem3_folders)
    assert any("microbiology" in f for f in sem3_folders)
    assert any("data structures" in f for f in sem3_folders)
    assert any("operating systems" in f for f in sem3_folders)
    assert any("computer organization" in f for f in sem3_folders)


def test_semester_4_contains_canonical_courses():
    """Verify that Sem 4 contains AI, DAA, DBMS, Control Systems."""
    sem4_path = os.path.join("corpus", "Semester_4")
    sem4_folders = [f.lower() for f in os.listdir(sem4_path) if os.path.isdir(os.path.join(sem4_path, f))]

    assert any("artificial intelligence" in f for f in sem4_folders)
    assert any("design and analysis of algorithms" in f for f in sem4_folders)
    assert any("database management systems" in f for f in sem4_folders)
    assert any("control systems" in f for f in sem4_folders)


def test_curriculum_resolver_aliases_and_canonical_semester(db: Session):
    """Verify that CurriculumResolver maps aliases to canonical courses and canonical semesters."""
    resolver = CurriculumResolver(db)

    # Test APP alias
    res_app = resolver.resolve("APP")
    assert res_app.status in (CurriculumMatchState.MATCHED, CurriculumMatchState.CATALOG_ONLY)
    assert res_app.canonical_semester == 3

    # Test AI alias
    res_ai = resolver.resolve("AI")
    assert res_ai.status in (CurriculumMatchState.MATCHED, CurriculumMatchState.CATALOG_ONLY)
    assert res_ai.canonical_semester == 4

    # Test DSA alias
    res_dsa = resolver.resolve("DSA")
    assert res_dsa.status in (CurriculumMatchState.MATCHED, CurriculumMatchState.CATALOG_ONLY)
    assert res_dsa.canonical_semester == 3

    # Test DAA alias
    res_daa = resolver.resolve("DAA")
    assert res_daa.status in (CurriculumMatchState.MATCHED, CurriculumMatchState.CATALOG_ONLY)
    assert res_daa.canonical_semester == 4


def test_curriculum_resolver_multi_semester_branch_variation(db: Session):
    """Verify that CurriculumResolver correctly handles courses with multi-semester branch variation."""
    resolver = CurriculumResolver(db)

    # Chemistry is taught in Sem 1 (Group A) and Sem 2 (Group B)
    res_chem_s1 = resolver.resolve("Chemistry", semester=1)
    assert 1 in res_chem_s1.valid_semesters and 2 in res_chem_s1.valid_semesters
    assert res_chem_s1.canonical_semester == 1

    res_chem_s2 = resolver.resolve("Chemistry", semester=2)
    assert res_chem_s2.canonical_semester == 2

    # Microbiology is only in Sem 3 (21BTC201T). If scraper encountered it in Sem 2, resolver canonicalizes to 3
    res_micro_s2 = resolver.resolve("Microbiology", semester=2)
    assert res_micro_s2.valid_semesters == [3]
    assert res_micro_s2.canonical_semester == 3


def test_manifest_files_reference_valid_paths():
    """Verify that data/manifest.json paths exist on filesystem."""
    manifest_path = "data/manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            local_path = item.get("local_path")
            if local_path:
                assert os.path.exists(local_path), f"Manifest references non-existent file: {local_path}"
                assert "Semester_1\\Advanced Programming Practice" not in local_path
                assert "Semester_1/Advanced Programming Practice" not in local_path
                assert "Semester_1\\Artificial Intelligence" not in local_path
                assert "Semester_1/Artificial Intelligence" not in local_path
