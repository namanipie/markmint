import urllib.request
import urllib.error
import json
import os

BASE_URL = "https://markmint.onrender.com"

tests = [
    ("Health Check", "/api/health", 200),
    ("Bundled Initial Scope (Phase 16/Bug fix)", "/api/curriculum/initial-scope", 200),
    ("Course 14 Intelligence (CT1)", "/api/intelligence/14?assessment_cycle=CT1", 200),
    ("Course 14 Predictions (CT1)", "/api/predictions/14?assessment_cycle=CT1", 200),
    ("Course 16 Study Priorities", "/api/study/priorities/16", 200),
    ("Course 14 Practice", "/api/practice/14", 200),
    ("Course 8 Track Selection Enforcement", "/api/intelligence/8", 400),
    ("Course 8 German Track Intelligence", "/api/intelligence/8?language=german", 200),
    ("Course 8 French Track Intelligence", "/api/intelligence/8?language=french", 200),
    ("Calculus Intelligence", "/api/intelligence/1", 200),
    ("Chemistry Intelligence", "/api/intelligence/2", 200),
    ("SPCM Intelligence", "/api/intelligence/13", 200),
]

print("=" * 80)
print(f"RUNNING COMPREHENSIVE PRODUCTION SMOKE TEST ON: {BASE_URL}")
print("=" * 80)

all_passed = True
results = []

for name, path, expected_status in tests:
    url = BASE_URL + path
    req = urllib.request.Request(url, headers={"User-Agent": "MarkMint-Live-Audit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            if status == expected_status:
                results.append((name, path, status, "PASS", None))
                print(f"[PASS] {status} | {name:<42} | {path}")
            else:
                results.append((name, path, status, "FAIL", f"Expected {expected_status}, got {status}"))
                print(f"[FAIL] {status} | {name:<42} | {path} (Expected {expected_status})")
                all_passed = False
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode("utf-8")
        try:
            data = json.loads(body)
        except Exception:
            data = body
        if status == expected_status:
            results.append((name, path, status, "PASS", data))
            print(f"[PASS] {status} | {name:<42} | {path} (Expected error status: {status})")
        else:
            results.append((name, path, status, "FAIL", f"Expected {expected_status}, got {status}: {data}"))
            print(f"[FAIL] {status} | {name:<42} | {path} (Expected {expected_status}, got {status})")
            all_passed = False
    except Exception as e:
        results.append((name, path, 0, "ERROR", str(e)))
        print(f"[ERROR] 0 | {name:<42} | {path} -> {e}")
        all_passed = False

print("=" * 80)
if all_passed:
    print("ALL PRODUCTION ENDPOINTS PASSED VERIFICATION!")
else:
    print("SOME CHECKS FAILED.")
print("=" * 80)
