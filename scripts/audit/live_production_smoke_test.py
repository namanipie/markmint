import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def get_json(endpoint):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "MarkMint-SmokeTest"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
            return status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            data = json.loads(body)
        except Exception:
            data = body
        return e.code, data

def main():
    print("================================================================")
    print("           MARKMINT PRODUCTION SMOKE TEST REPORT")
    print("================================================================")

    # -------------------------------------------------------------
    # 7. Production health
    # -------------------------------------------------------------
    print("\n--- 7. PRODUCTION HEALTH ---")
    st, health = get_json("/health")
    print(f"GET /health: {st} -> {health}")
    assert st == 200 and health.get("status") == "ok", "Root health check failed"

    st, api_health = get_json("/api/health")
    print(f"GET /api/health: {st} -> {api_health}")
    assert st == 200 and api_health.get("status") == "ok", "API health check failed"

    # -------------------------------------------------------------
    # 1. Calculus
    # -------------------------------------------------------------
    print("\n--- 1. CALCULUS (Course 1 / 21MAB101T) ---")
    st, calc_intel = get_json("/api/intelligence/1")
    assert st == 200, f"Calculus intelligence failed with status {st}"
    print(f"GET /api/intelligence/1: status={st}, availability={calc_intel.get('data_availability_status')}")

    # Check units in frontend catalog & DB taxonomy
    from backend.core.database import SessionLocal
    from backend.models.core import Course, Syllabus, Unit, Topic
    db = SessionLocal()
    calc = db.query(Course).get(1)
    calc_syl = db.query(Syllabus).filter(Syllabus.course_id == 1).first()
    calc_units = db.query(Unit).filter(Unit.syllabus_id == calc_syl.id).order_by(Unit.number).all()
    print(f"Calculus DB syllabus units: {len(calc_units)}")
    assert len(calc_units) == 5, f"Calculus has {len(calc_units)} units, expected 5"
    for u in calc_units:
        assert 1 <= u.number <= 5, f"Illegal unit number {u.number}"
        topics_count = db.query(Topic).filter(Topic.unit_id == u.id).count()
        print(f"  Unit {u.number}: {u.name} ({topics_count} topics)")

    # Verify no Unit 6+ appears anywhere in predictions or study priorities
    preds = calc_intel.get("topic_predictions", [])
    pred_units = {p.get("unit_number") for p in preds if p.get("unit_number") is not None}
    print(f"Calculus predicted topic unit numbers: {sorted(list(pred_units))}")
    assert all(1 <= u <= 5 for u in pred_units), "Found predicted topic with unit number outside 1..5"

    priorities = calc_intel.get("study_priorities", [])
    prio_units = {p.get("unit_number") for p in priorities if p.get("unit_number") is not None}
    print(f"Calculus study priority unit numbers: {sorted(list(prio_units))}")
    assert all(1 <= u <= 5 for u in prio_units), "Found study priority with unit number outside 1..5"
    print("Calculus 5-unit verification: PASSED (Zero Unit 6+)")

    # -------------------------------------------------------------
    # 2. Chemistry
    # -------------------------------------------------------------
    print("\n--- 2. CHEMISTRY (Course 2 / 21CYB101J) ---")
    st, chem_intel = get_json("/api/intelligence/2")
    assert st == 200, f"Chemistry intelligence failed with status {st}"
    print(f"GET /api/intelligence/2: status={st}, availability={chem_intel.get('data_availability_status')}")

    chem = db.query(Course).get(2)
    chem_syl = db.query(Syllabus).filter(Syllabus.course_id == 2).first()
    chem_units = db.query(Unit).filter(Unit.syllabus_id == chem_syl.id).order_by(Unit.number).all()
    print(f"Chemistry DB syllabus units: {len(chem_units)}")
    assert len(chem_units) == 5, f"Chemistry has {len(chem_units)} units, expected 5"
    for u in chem_units:
        assert 1 <= u.number <= 5, f"Illegal unit number {u.number}"
        topics_count = db.query(Topic).filter(Topic.unit_id == u.id).count()
        print(f"  Unit {u.number}: {u.name} ({topics_count} topics)")

    chem_preds = chem_intel.get("topic_predictions", [])
    chem_pred_units = {p.get("unit_number") for p in chem_preds if p.get("unit_number") is not None}
    print(f"Chemistry predicted topic unit numbers: {sorted(list(chem_pred_units))}")
    assert all(1 <= u <= 5 for u in chem_pred_units), "Found predicted topic with unit number outside 1..5"

    chem_obs = chem_intel.get("observed_scope", {})
    obs_units = chem_obs.get("unit_numbers", [])
    print(f"Chemistry observed scope unit numbers: {obs_units}")
    assert all(1 <= u <= 5 for u in obs_units), "Found observed unit outside 1..5"
    print("Chemistry 5-unit verification: PASSED (Zero 12-unit leakage)")

    # -------------------------------------------------------------
    # 3. Foreign Languages
    # -------------------------------------------------------------
    print("\n--- 3. FOREIGN LANGUAGES (Course 8 / 21LEH-ELECTIVE) ---")
    # Parent course intelligence must require track selection
    st, fl_parent = get_json("/api/intelligence/8")
    print(f"GET /api/intelligence/8: status={st}, response={fl_parent}")
    assert st == 400, f"Expected status 400 TRACK_SELECTION_REQUIRED, got {st}"
    assert "TRACK_SELECTION_REQUIRED" in fl_parent.get("detail", ""), "Expected TRACK_SELECTION_REQUIRED in detail"
    print("Parent course track selection requirement: PASSED (Returned 400 TRACK_SELECTION_REQUIRED)")

    # Parent syllabus units in DB
    fl_course_syl = db.query(Syllabus).filter(Syllabus.course_id == 8, Syllabus.track_id == None).first()
    fl_parent_units = len(fl_course_syl.units) if fl_course_syl else 0
    print(f"Foreign Languages parent syllabus units: {fl_parent_units} (must be 0, no 30-unit aggregate)")
    assert fl_parent_units == 0, f"Parent course has {fl_parent_units} units; should be 0"

    # Track German
    st, fl_german = get_json("/api/intelligence/8?track=german")
    assert st == 200
    print(f"GET /api/intelligence/8?track=german: status={st}, track={fl_german.get('track')}")
    assert fl_german.get("track", {}).get("track_key") == "german"

    # Check track units
    from backend.models.core import CourseTrack
    german_track = db.query(CourseTrack).filter(CourseTrack.course_id == 8, CourseTrack.track_key == "german").first()
    german_syl = db.query(Syllabus).filter(Syllabus.track_id == german_track.id).first()
    german_units = db.query(Unit).filter(Unit.syllabus_id == german_syl.id).order_by(Unit.number).all()
    print(f"German track units count: {len(german_units)}")
    assert len(german_units) == 5, f"German track has {len(german_units)} units, expected 5"
    for u in german_units:
        assert 1 <= u.number <= 5
        print(f"  German Unit {u.number}: {u.name}")

    # Verify no French/Spanish cross-contamination
    german_topics = db.query(Topic).join(Unit).filter(Unit.syllabus_id == german_syl.id).all()
    german_topic_titles = [t.name.lower() for t in german_topics]
    assert not any("french" in t or "espagnol" in t or "kanji" in t for t in german_topic_titles)
    print("Foreign Languages track isolation: PASSED")

    # -------------------------------------------------------------
    # 4. Assessment Scope Decoupling & Invariants
    # -------------------------------------------------------------
    print("\n--- 4. ASSESSMENT SCOPE DECOUPLING ---")
    for cycle in ["CT1", "CT2", "ENDSEM"]:
        st, c_intel = get_json(f"/api/intelligence/1?cycle={cycle}")
        assert st == 200
        scope = c_intel.get("assessment_scope", {})
        intended = c_intel.get("intended_scope")
        evidence = c_intel.get("evidence_status")
        observed = c_intel.get("observed_scope")
        print(f"Calculus cycle={cycle}: evidence_status={evidence}, intended_scope={intended}")
        assert intended is None, f"Expected intended_scope to be None for {cycle}, got {intended}"
        assert evidence == "UNPLANNED_OBSERVED_ONLY", f"Expected UNPLANNED_OBSERVED_ONLY for {cycle}, got {evidence}"
        assert scope.get("unit_numbers") == [], f"Expected in-scope unit_numbers to be empty, got {scope.get('unit_numbers')}"
        if observed:
            print(f"  Observed scope: {observed.get('paper_count')} papers, {observed.get('mapped_questions_count')} mapped questions, units={observed.get('unit_numbers')}")

    print("Assessment scope truthful reporting: PASSED (Zero invented intended unit ranges)")

    # -------------------------------------------------------------
    # 5. Corpus / Resource Resolution
    # -------------------------------------------------------------
    print("\n--- 5. CORPUS / RESOURCE RESOLUTION ---")
    from backend.services.scraper.curriculum_resolver import CurriculumResolver
    resolver = CurriculumResolver(db)

    test_cases = [
        ("Sem 1: Calculus", "Calculus And Linear Algebra", 1, 1),
        ("Sem 1: Chemistry", "Chemistry", 1, 1),
        ("Sem 1: EEE", "Electrical and Electronics Engineering", 1, 1),
        ("Sem 1: PPS", "Programming For Problem Solving", 1, 1),
        ("Sem 2: Chemistry (Branch B)", "Chemistry", 2, 2),
        ("Sem 2: ACCA", "Advanced Calculus and Complex Analysis", 2, 2),
        ("Sem 2: Building Materials", "Building Materials in the Built Environment", 2, 2),
        ("Sem 2: ESPCB", "Electronic System and PCB Design", 2, 2),
        ("Sem 3: Microbiology", "Microbiology", 2, 3),  # Scraped with sem=2, resolved canonical sem=3
        ("Sem 3: APP", "Advanced Programming Practice", 3, 3),
        ("Sem 3: DSA", "Data Structures and Algorithms", 3, 3),
        ("Sem 3: OS", "Operating Systems", 3, 3),
        ("Sem 3: COA", "Computer Organization and Architecture", 3, 3),
        ("Sem 4: AI", "Artificial Intelligence (AI)", 4, 4),
        ("Sem 4: DAA", "Design and Analysis of Algorithms", 4, 4),
        ("Sem 4: DBMS", "Database Management Systems", 4, 4),
        ("Sem 4: Control Systems", "Control Systems", 4, 4),
    ]

    for label, name, in_sem, expected_sem in test_cases:
        res = resolver.resolve(name, semester=in_sem)
        print(f"  {label:38s} -> status={res.status.value:12s}, canonical_sem={res.canonical_semester}, valid={res.valid_semesters}")
        assert res.canonical_semester == expected_sem, f"Expected {expected_sem}, got {res.canonical_semester} for {label}"

    # Verify moved physical resources exist and are accessible on disk
    import os
    moved_resource_dirs = [
        ("corpus/Semester_1/Constitution of India", 5),
        ("corpus/Semester_1/Hardware and Troubleshooting", 7),
        ("corpus/Semester_1/Measuring Instruments", 1),
        ("corpus/Semester_3/Advanced Programming Practice (APP)", 6),
        ("corpus/Semester_3/Microbiology", 5),
        ("corpus/Semester_4/Artificial Intelligence (AI)", 10),
        ("corpus/Semester_4/Control Systems", 9),
        ("corpus/Semester_3/Digital Electronic Principles", 12),
        ("corpus/Semester_3/Electronic Devices", 10),
    ]
    print("\n  Verifying moved physical resources on disk:")
    for path, expected_count in moved_resource_dirs:
        assert os.path.exists(path), f"Missing path {path}"
        total_files = sum(len(f) for _, _, f in os.walk(path))
        print(f"    {path:55s}: {total_files} files (expected >= {expected_count})")
        assert total_files >= expected_count, f"Expected at least {expected_count} files in {path}, found {total_files}"

    print("Corpus and semester resolution: PASSED")

    # -------------------------------------------------------------
    # 6. Cache Consistency & Performance
    # -------------------------------------------------------------
    print("\n--- 6. CACHE CONSISTENCY & RE-GENERATION ---")
    st1, p1_first = get_json("/api/intelligence/1")
    st2, p1_second = get_json("/api/intelligence/1")
    assert st1 == 200 and st2 == 200
    v1 = p1_second.get("metadata", {}).get("taxonomy_version")
    print(f"Calculus metadata.taxonomy_version: {v1}")
    assert v1 == "2.0.0", f"Expected taxonomy_version 2.0.0, got {v1}"

    st1_c, p2_first = get_json("/api/intelligence/2")
    st2_c, p2_second = get_json("/api/intelligence/2")
    assert st1_c == 200 and st2_c == 200
    v2 = p2_second.get("metadata", {}).get("taxonomy_version")
    print(f"Chemistry metadata.taxonomy_version: {v2}")
    assert v2 == "2.0.0", f"Expected taxonomy_version 2.0.0, got {v2}"

    # Verify persistent cache table in DB
    from backend.models.core import IntelligenceSnapshot
    snaps = db.query(IntelligenceSnapshot).all()
    print(f"Persistent IntelligenceSnapshot rows in DB: {len(snaps)}")
    for s in snaps:
        assert s.taxonomy_version == "2.0.0", f"Found stale snapshot {s.id} with version {s.taxonomy_version}"
        payload = s.payload or {}
        # Course units in DB payload
        c_units = payload.get("course", {}).get("units", [])
        assert len(c_units) in (0, 5), f"Snapshot {s.id} contains {len(c_units)} units!"

    print("Cache consistency and zero stale snapshots: PASSED")

    db.close()
    print("\n================================================================")
    print("      ALL PRODUCTION SMOKE TESTS COMPLETED SUCCESSFULLY!")
    print("================================================================")

if __name__ == "__main__":
    main()
