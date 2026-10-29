import urllib.request
import json
import time

url = "https://markmint.onrender.com/api/curriculum/initial-scope"
print("Waiting for Render deployment of commit a2c559f...")
for i in range(25):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            branches = len(data.get("branches", []))
            print(f"Attempt {i+1}: DEPLOYMENT LIVE! Status {resp.status}, branches={branches}")
            break
    except urllib.error.HTTPError as e:
        print(f"Attempt {i+1}: HTTP {e.code} ({e.reason}) - build still in progress...")
    except Exception as e:
        print(f"Attempt {i+1}: {e}")
    time.sleep(10)
