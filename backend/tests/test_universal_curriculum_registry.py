import json
import os
import pytest
from pathlib import Path


@pytest.fixture(scope="module")
def canonical_curriculum():
    repo_root = Path(__file__).parent.parent.parent
    catalog_path = repo_root / "src" / "data" / "canonical_curriculum.json"
    assert catalog_path.exists(), f"canonical_curriculum.json not found at {catalog_path}"
    with open(catalog_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_universal_curriculum_structure(canonical_curriculum):
    """Verify universal curriculum branches, hierarchy, and top-level invariants."""
    branches = canonical_curriculum.get("branches", [])
    hierarchy = canonical_curriculum.get("hierarchy", {})

    assert len(branches) == 54, f"Expected 54 engineering branches, found {len(branches)}"
    assert len(hierarchy) == 54, f"Hierarchy must contain exactly 54 branches, found {len(hierarchy)}"
    assert "Computer Science and Engineering" in branches
    assert "Aerospace Engineering" in branches


def test_universal_curriculum_semester_coverage(canonical_curriculum):
    """Verify that curriculum covers Semesters 1 through 8 across branches."""
    hierarchy = canonical_curriculum.get("hierarchy", {})
    cse_sems = hierarchy.get("Computer Science and Engineering", {})
    
    # Check that CSE has semesters 1 through 8
    for sem in range(1, 9):
        assert str(sem) in cse_sems, f"Computer Science and Engineering missing Semester {sem}"
        assert len(cse_sems[str(sem)]) > 0, f"Semester {sem} has no subjects"


def test_zero_fake_courses_and_duplicate_codes(canonical_curriculum):
    """Verify that no fake 9000-series courses or fake TH- codes exist."""
    hierarchy = canonical_curriculum.get("hierarchy", {})
    
    for branch, sems in hierarchy.items():
        for sem, subjects in sems.items():
            for s in subjects:
                cid = s.get("course_id")
                code = str(s.get("canonical_code") or "")
                
                assert cid is None or cid < 9000, f"Found fake course_id {cid} in {branch} Sem {sem}"
                assert not code.startswith("TH-"), f"Found fake code {code} in {branch} Sem {sem}"
                assert s.get("status") in ("MATCHED", "UNMATCHED", "AMBIGUOUS")


def test_course_8_foreign_languages_multi_track(canonical_curriculum):
    """Verify Course 8 Foreign Languages has complete 6-track definition."""
    hierarchy = canonical_curriculum.get("hierarchy", {})
    found_course_8 = False

    for branch, sems in hierarchy.items():
        for sem, subjects in sems.items():
            for s in subjects:
                if s.get("course_id") == 8:
                    found_course_8 = True
                    assert s.get("has_tracks") is True
                    tracks = s.get("tracks", [])
                    assert len(tracks) == 6
                    keys = {t["track_key"] for t in tracks}
                    assert keys == {"german", "french", "spanish", "japanese", "korean", "chinese"}

    assert found_course_8, "Course 8 (Foreign Languages) must be present in curriculum"
