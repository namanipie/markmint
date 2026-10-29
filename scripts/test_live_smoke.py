import urllib.request
import urllib.parse
import json

base = "https://markmint.onrender.com"
tests = [
    "/api/health",
    "/api/courses/",
    "/api/curriculum/stats",
    "/api/intelligence/1",
    "/api/intelligence/2",
    "/api/intelligence/13",
    "/api/study/plan/Chemistry",
    "/api/study/plan/SPCM",
    "/api/practice/Calculus%20And%20Linear%20Algebra",
    "/api/practice/21MAB101T",
    "/api/practice/21CYB101J",
]

print("=" * 80)
print(f"TESTING LIVE PRODUCTION ENDPOINTS: {base}")
print("=" * 80)

results = {}

for t in tests:
    url = base + t
    req = urllib.request.Request(url, headers={"User-Agent": "MarkMint-Smoke/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            info = ""
            if "intelligence" in t:
                info = f"mode={data.get('prediction_mode')}, preds={len(data.get('predictions', []))}, has_tax={data.get('has_topic_taxonomy')}"
            elif "practice" in t:
                info = f"questions={len(data.get('questions', []))}"
            elif "curriculum" in t:
                info = f"total={data.get('total_entries')}, matched={data.get('matched_entries')}"
            elif "health" in t:
                info = f"status={data.get('status')}"
            elif "study" in t:
                info = f"priorities={len(data.get('priorities', []))}, mode={data.get('plan_mode')}"
            elif "courses" in t:
                info = f"count={len(data) if isinstance(data, list) else len(data.get('courses', []))}"
            print(f"[200 OK] {t:<45} -> {info}")
            results[t] = {"status": 200, "data": data}
    except urllib.error.HTTPError as e:
        print(f"[{e.code} ERR] {t:<45} -> {e.reason}")
        results[t] = {"status": e.code, "error": e.reason}
    except Exception as e:
        print(f"[EXC ERR] {t:<45} -> {e}")
        results[t] = {"status": "EXC", "error": str(e)}

print("\n" + "=" * 80)
# Check if a731481 is deployed
# Signatures of a731481 / new code:
# 1. /api/intelligence/1 has prediction_mode == "topic"
# 2. /api/practice/21MAB101T is 200 OK (not 404)
# 3. /api/practice/Calculus%20And%20Linear%20Algebra is 200 OK (not 500)
c1_intel = results.get("/api/intelligence/1", {})
c1_mode = c1_intel.get("data", {}).get("prediction_mode") if c1_intel.get("status") == 200 else None

calc_practice_canon = results.get("/api/practice/21MAB101T", {}).get("status")
calc_practice_name = results.get("/api/practice/Calculus%20And%20Linear%20Algebra", {}).get("status")

print("DEPLOYMENT VERIFICATION RESULT:")
print(f"  Intelligence C1 prediction_mode : {c1_mode} (Expected in new code: 'topic')")
print(f"  Practice with canonical code   : {calc_practice_canon} (Expected in new code: 200)")
print(f"  Practice with full name        : {calc_practice_name} (Expected in new code: 200)")

if c1_mode == "topic" and calc_practice_canon == 200 and calc_practice_name == 200:
    print("\nCONFIRMED: Live Render service IS SERVING the updated code (commit a731481)!")
else:
    print("\nNOT YET LIVE: Render service is still serving the older deployment (commit ecd0f83).")
    print("Action required: Render is either still building or requires a manual deploy trigger in dashboard.")
