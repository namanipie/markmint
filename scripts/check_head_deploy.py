import urllib.request
import time

url = "https://markmint.onrender.com/api/health"
print("Monitoring Render rollout for HEAD /api/health support...", flush=True)

for attempt in range(1, 35):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[{attempt}] SUCCESS! HEAD status {resp.status}, Content-Length: {resp.headers.get('content-length')}", flush=True)
            exit(0)
    except urllib.error.HTTPError as e:
        print(f"[{attempt}] HEAD HTTP {e.code} ({e.reason}) - build still rolling out...", flush=True)
    except Exception as e:
        print(f"[{attempt}] Error: {e}", flush=True)
    time.sleep(10)

print("Timeout waiting for deployment.", flush=True)
exit(1)
