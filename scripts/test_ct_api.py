import urllib.request
import urllib.parse
import json

subjs = [
    'Design and Analysis of Algorithms',
    'Computer Organization and Architecture',
    'Database Management Systems',
    'Programming for Problem Solving',
    'Chemistry'
]

for s in subjs:
    url = f"http://127.0.0.1:8000/api/practice/cycle-tests/{urllib.parse.quote(s)}?limit=3"
    with urllib.request.urlopen(url, timeout=5) as resp:
        d = json.load(resp)
        sample = d["questions"][0]["question_text"][:60].replace("\n", " ") if d.get("questions") else "N/A"
        print(f"[{s}] Total: {d['total_available']} | Sample: {repr(sample)}")
