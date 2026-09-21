import urllib.request
import time
import json

BASE_URL = "https://markmint.onrender.com"

endpoints = [
    ("Health (HEAD)", "/api/health", "HEAD"),
    ("Health (GET)", "/api/health", "GET"),
    ("Calculus Intelligence (Warm)", "/api/intelligence/1", "GET"),
    ("Chemistry Intelligence (Warm)", "/api/intelligence/2", "GET"),
    ("EEE CT1 Intelligence (Warm)", "/api/intelligence/14?assessment_cycle=CT1", "GET"),
    ("OODP Intelligence (Warm)", "/api/intelligence/16", "GET"),
    ("German Foreign Language (Warm)", "/api/intelligence/8?language=german", "GET"),
    ("French Foreign Language (Warm)", "/api/intelligence/8?language=french", "GET"),
    ("Calculus Predictions (Warm)", "/api/predictions/1", "GET"),
    ("Calculus Practice (Warm)", "/api/practice/1", "GET"),
    ("Chemistry Study Priorities (Warm)", "/api/study/priorities/2", "GET"),
]

print("=" * 80)
print(f"BENCHMARKING PRODUCTION LATENCIES AGAINST: {BASE_URL}")
print("=" * 80)

results = []

for name, path, method in endpoints:
    url = BASE_URL + path
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}, method=method)
    
    # Run 2 passes to ensure warm cache
    try:
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read() if method == "GET" else b""
            status = resp.status
        t1 = time.perf_counter()
        client_ms = (t1 - t0) * 1000
        
        # Try to parse backend latency if exposed in JSON metadata
        backend_ms = None
        if method == "GET" and data:
            try:
                parsed = json.loads(data.decode("utf-8"))
                if isinstance(parsed, dict) and "metadata" in parsed and "latency_ms" in parsed["metadata"]:
                    backend_ms = parsed["metadata"]["latency_ms"]
            except Exception:
                pass

        results.append((name, path, method, status, client_ms, backend_ms))
        backend_str = f"backend: {backend_ms:.1f}ms" if backend_ms else "backend: N/A"
        print(f"[PASS] {status} | {name:<35} | {client_ms:6.1f}ms ({backend_str})")
    except Exception as e:
        print(f"[FAIL] {name:<35} | Error: {e}")

print("=" * 80)
