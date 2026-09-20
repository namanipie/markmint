from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

courses_to_test = [
    ("Calculus", "21MAB101T", None),
    ("Chemistry", "21CYB101J", None),
    ("EEE", "21EEB101J", None),
    ("OODP", "21CSC201J", None),
    ("DAA (Sem 3)", "21CSC202J", None),
    ("German Track", "Foreign Languages", "german"),
    ("French Track", "Foreign Languages", "french")
]

print("=== BETA QA LIVE VERIFICATION ===")
for label, code, lang in courses_to_test:
    params = {}
    if lang:
        params["language"] = lang
    resp = client.get(f"/api/predictions/{code}", params=params)
    assert resp.status_code == 200, f"Failed {label}: {resp.status_code} {resp.text}"
    data = resp.json()
    preds = data.get("predictions", [])
    scope = data.get("assessment_scope")
    years = data.get("observed_years", [])
    scope_topics = scope.get("total_in_scope_topics") if scope else 0
    print(f"[OK] {label} ({code}): predictions={len(preds)}, years={len(years)}, in_scope_topics={scope_topics}")

print("\n=== BETA METRICS ENDPOINT VERIFICATION ===")
metrics_resp = client.get("/api/analytics/beta-metrics")
assert metrics_resp.status_code == 200
m = metrics_resp.json()
print(f"[OK] Beta Metrics: total_sessions={m.get('total_beta_sessions')}")
print(f"[OK] Funnel Sessions: {m.get('funnel_sessions')}")
print(f"[OK] Conversions: {m.get('conversion_rates')}")
print(f"[OK] Feedback Summary: {m.get('feedback_summary')}")
