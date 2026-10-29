import urllib.request
import json
import time

url = "https://markmint.onrender.com/api/curriculum/initial-scope"
print("Monitoring Render deployment of a2c559f...", flush=True)

for attempt in range(1, 31):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[{attempt}] SUCCESS! Status {resp.status}, Branches: {len(data.get('branches', []))}", flush=True)
            exit(0)
    except urllib.error.HTTPError as e:
        print(f"[{attempt}] HTTP {e.code} ({e.reason})", flush=True)
    except Exception as e:
        print(f"[{attempt}] Error: {e}", flush=True)
    time.sleep(10)

print("Timeout waiting for deployment.", flush=True)
exit(1)
