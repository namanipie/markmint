"""
Benchmark live production Render intelligence endpoints across representative courses.
Measures latency over 5 repeated warm requests per endpoint.
"""
import urllib.request
import json
import time
import statistics

BASE_URL = "https://markmint.onrender.com"

ENDPOINTS = [
    ("Calculus", f"{BASE_URL}/api/intelligence/1"),
    ("Chemistry", f"{BASE_URL}/api/intelligence/2"),
    ("EEE CT1", f"{BASE_URL}/api/intelligence/14?assessment_cycle=CT1"),
    ("OODP", f"{BASE_URL}/api/intelligence/16"),
    ("German", f"{BASE_URL}/api/intelligence/8?language=german"),
    ("French", f"{BASE_URL}/api/intelligence/8?language=french"),
]

def wait_for_render():
    health_url = f"{BASE_URL}/api/health"
    print("Waiting for Render deployment to be live...", flush=True)
    for i in range(1, 40):
        try:
            req = urllib.request.Request(health_url, headers={"User-Agent": "Benchmark/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    print(f"[{i}] Render is healthy and reachable (HTTP 200)!", flush=True)
                    return True
        except Exception as e:
            print(f"[{i}] Waiting for health endpoint: {e}", flush=True)
        time.sleep(10)
    return False

def benchmark():
    if not wait_for_render():
        print("Render is not reachable. Exiting.")
        return

    # Wait an extra 15 seconds to ensure newly deployed container has stabilized
    time.sleep(15)

    print("\n" + "=" * 80)
    print("BENCHMARKING PRODUCTION INTELLIGENCE ENDPOINTS (5 REPEATS PER ENDPOINT)")
    print("=" * 80)
    print(f"{'Endpoint':<12} | {'Warm Median':<12} | {'Min':<8} | {'Max':<8} | {'Payload':<8} | {'Cache Hit'}")
    print("-" * 80)

    for label, url in ENDPOINTS:
        latencies = []
        payload_bytes = 0
        cache_hits = []

        for r in range(5):
            t0 = time.perf_counter()
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Benchmark/1.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    dt = (time.perf_counter() - t0) * 1000
                    latencies.append(dt)
                    payload_bytes = len(json.dumps(data))
                    cache_hits.append(data.get("metadata", {}).get("cache_hit", False))
            except Exception as e:
                print(f"Error requesting {label}: {e}")
            time.sleep(0.3)

        if latencies:
            median_lat = statistics.median(latencies)
            min_lat = min(latencies)
            max_lat = max(latencies)
            has_cache = any(cache_hits)
            print(f"{label:<12} | {median_lat:7.1f} ms    | {min_lat:5.0f}ms | {max_lat:5.0f}ms | {payload_bytes/1024:5.1f}KB | {str(has_cache)}")
        else:
            print(f"{label:<12} | FAILED")

    print("-" * 80)

if __name__ == "__main__":
    benchmark()
