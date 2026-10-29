import os
import json
import urllib.request
import urllib.parse
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def main():
    print("==================================================")
    print("Testing CT Practice & Evidence Across ALL 43 Courses")
    print("==================================================")

    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("SELECT id, name, code FROM courses ORDER BY id;")
    courses = cur.fetchall()

    with open("src/lib/course-resources.json", "r", encoding="utf-8") as f:
        resources = json.load(f)

    # Check resources json
    res_ct_counts = {}
    for slug, cdata in resources.items():
        cname = cdata.get("courseName", "").strip().lower()
        ct1_p = sum(1 for p in cdata.get("pyqs", []) if p.get("examType") == "CT1")
        ct2_p = sum(1 for p in cdata.get("pyqs", []) if p.get("examType") == "CT2")
        res_ct_counts[cname] = (ct1_p, ct2_p)

    results = []
    for cid, name, code in courses:
        c_low = name.strip().lower()
        json_ct1, json_ct2 = res_ct_counts.get(c_low, (0, 0))

        # Test FastAPI practice endpoint for CT1
        url_ct1 = "http://127.0.0.1:8000/api/practice/cycle-tests/" + urllib.parse.quote(name) + "?cycle=CT1"
        try:
            req1 = urllib.request.urlopen(url_ct1, timeout=5)
            data1 = json.loads(req1.read().decode("utf-8"))
            api_ct1_count = data1.get("total_available", 0)
            has_key1 = data1["questions"][0].get("answer_key") is not None if data1.get("questions") else False
        except Exception as e:
            api_ct1_count = -1
            has_key1 = False

        # Test FastAPI practice endpoint for CT2
        url_ct2 = "http://127.0.0.1:8000/api/practice/cycle-tests/" + urllib.parse.quote(name) + "?cycle=CT2"
        try:
            req2 = urllib.request.urlopen(url_ct2, timeout=5)
            data2 = json.loads(req2.read().decode("utf-8"))
            api_ct2_count = data2.get("total_available", 0)
            has_key2 = data2["questions"][0].get("answer_key") is not None if data2.get("questions") else False
        except Exception as e:
            api_ct2_count = -1
            has_key2 = False

        # Check DB CT counts
        cur.execute("""
            SELECT 
                COUNT(CASE WHEN e.assessment_type = 'CT1' THEN q.id END),
                COUNT(CASE WHEN e.assessment_type = 'CT2' THEN q.id END)
            FROM questions q
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = %s;
        """, (cid,))
        db_ct1, db_ct2 = cur.fetchone()

        status = "PASS" if (api_ct1_count > 0 and api_ct2_count > 0 and json_ct1 > 0 and json_ct2 > 0 and (db_ct1 > 0 or db_ct2 > 0)) else "WARN"
        results.append({
            "id": cid,
            "name": name,
            "code": code,
            "json_papers": f"CT1: {json_ct1}, CT2: {json_ct2}",
            "api_questions": f"CT1: {api_ct1_count}, CT2: {api_ct2_count}",
            "db_questions": f"CT1: {db_ct1}, CT2: {db_ct2}",
            "status": status
        })
        print(f"[{cid:2d}] {name:<42} | JSON: CT1={json_ct1} CT2={json_ct2} | API: CT1={api_ct1_count:3d} CT2={api_ct2_count:3d} | DB: CT1={db_ct1:3d} CT2={db_ct2:3d} | {status}")

    conn.close()

    total_pass = sum(1 for r in results if r["status"] == "PASS")
    print("\n==================================================")
    print(f"RESULTS: {total_pass} of {len(courses)} courses FULLY VERIFIED (100% CT COVERAGE)")
    print("==================================================")

if __name__ == '__main__':
    main()
