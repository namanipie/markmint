import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.core.database import SessionLocal
from backend.models.core import Course
from backend.api.endpoints.predictions import get_prediction

main_db = SessionLocal()
courses_data = [(c.id, c.code, c.name, [t.track_key for t in c.tracks] if c.tracks else []) for c in main_db.query(Course).order_by(Course.id).all()]
main_db.close()

print(f"Total courses to verify concurrently: {len(courses_data)}", flush=True)

cycles = ['CT1', 'CT2', 'ENDSEM']

def verify_single_course(course_info):
    c_id, c_code, c_name, c_tracks = course_info
    db = SessionLocal()
    t0 = time.time()
    course_res = {
        "id": c_id,
        "code": c_code,
        "name": c_name,
        "cycles": {}
    }
    lang = c_tracks[0] if c_tracks else None
    
    try:
        for cycle in cycles:
            try:
                res = get_prediction(subject=str(c_id), target_year=2024, assessment_cycle=cycle, language=lang, db=db)
                status = res.get("evidence_status", "UNKNOWN")
                pred_count = len(res.get("predictions", []))
                breakdown = res.get("empirical_unit_breakdown", [])
                units_present = [u["unit_number"] for u in breakdown]
                is_baseline = breakdown[0].get("is_baseline", False) if breakdown else False
                course_res["cycles"][cycle] = {
                    "ok": True,
                    "status": status,
                    "is_baseline": is_baseline,
                    "pred_count": pred_count,
                    "units": units_present
                }
            except Exception as e:
                course_res["cycles"][cycle] = {
                    "ok": False,
                    "error": str(e)
                }
    finally:
        db.close()
    
    elapsed = time.time() - t0
    c_ok = all(course_res["cycles"][cy].get("ok", False) for cy in cycles)
    return course_res, c_ok, elapsed

results = []
start_total = time.time()

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(verify_single_course, c): c for c in courses_data}
    count = 0
    for future in as_completed(futures):
        count += 1
        c_res, c_ok, elapsed = future.result()
        results.append(c_res)
        status_str = "PASS" if c_ok else "FAIL"
        print(f"[{count:02d}/{len(courses_data)}] {c_res['code']} ({c_res['name'][:28]}): {status_str} in {elapsed:.1f}s", flush=True)
        if not c_ok:
            for cy in cycles:
                if not c_res["cycles"][cy].get("ok"):
                    print(f"    -> {cy} Error: {c_res['cycles'][cy].get('error')}", flush=True)

total_elapsed = time.time() - start_total
passed = sum(1 for r in results if all(r["cycles"][cy].get("ok", False) for cy in cycles))
print(f"\n==========================================", flush=True)
print(f"FINAL AUDIT SUMMARY: {passed}/{len(courses_data)} COURSES PASSED in {total_elapsed:.1f}s", flush=True)
print(f"==========================================", flush=True)

for cy in cycles:
    emp = sum(1 for r in results if r["cycles"][cy].get("ok") and not r["cycles"][cy].get("is_baseline"))
    base = sum(1 for r in results if r["cycles"][cy].get("ok") and r["cycles"][cy].get("is_baseline"))
    print(f"Cycle {cy}: {emp} empirical courses, {base} syllabus-baseline fallback courses", flush=True)
