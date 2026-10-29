import json
import os
import urllib.request
import re

targets = [
    # Discrete Mathematics
    {"course": "Discrete Mathematics", "title": "CT Papers 2024", "url": "https://drive.google.com/file/d/1bYWTTc_VH3_onAAQLF5wqdReHKGhfAUW/view?usp=sharing", "cycle": "CT1"},
    {"course": "Discrete Mathematics", "title": "CT Papers 2025", "url": "https://drive.google.com/file/d/11AYA6S8SsDgS2gOi9RZzHCVAIxCJWsbj/view?usp=sharing", "cycle": "CT2"},
    # Probability and Queueing Theory
    {"course": "Probability and Queueing Theory", "title": "CT Papers Compilation", "url": "https://drive.google.com/file/d/1zQh4mtmGc7YuIYe0IbfOzbjGUIH1crrz/view?usp=sharing", "cycle": "CT1"},
    # Advanced Calculus and Complex Analysis
    {"course": "Advanced Calculus and Complex Analysis", "title": "CT Papers Compilation", "url": "https://drive.google.com/file/d/1EPidinguoZeL9azdQzBy20iik9YSaVoH/view?usp=drive_link", "cycle": "CT1"},
    # Compiler Design
    {"course": "Compiler Design", "title": "Question Bank", "url": "https://drive.google.com/file/d/1AneYgWczqDwJWZHN2bWZzX4D_x1s2tS-/view?usp=drive_link", "cycle": "CT1"},
    {"course": "Compiler Design", "title": "Important Questions", "url": "https://drive.google.com/file/d/1XPsCvtVbJ65ExXeqTUrPhTNEsLBiPkHR/view?usp=drive_link", "cycle": "CT2"},
    # Object Oriented Design and Programming
    {"course": "Object Oriented Design and Programming", "title": "Question Bank", "url": "https://drive.google.com/file/d/19Ej9QRZcqDCrN_1qOPCxu0gsTvVvfj98/view?usp=drive_link", "cycle": "CT1"},
    {"course": "Object Oriented Design and Programming", "title": "Important Questions", "url": "https://drive.google.com/file/d/14pwsNMxHBLdd2T57GuInfIJK032JDxmt/view?usp=drive_link", "cycle": "CT2"},
    # Internet of Things
    {"course": "Internet of Things", "title": "CT PYQs", "url": "https://drive.google.com/file/d/1Iizy1bV8yNpDemFB5ZMxsipzR_5xsvBC/view?usp=sharing", "cycle": "CT1"},
    # Operating Systems
    {"course": "Operating Systems", "title": "OS CT Paper", "url": "https://drive.google.com/file/d/1PO-afGBfv4lTbzYTyo4lSDeVggL3ydUq/view?usp=sharing", "cycle": "CT1"},
    # Artificial Intelligence
    {"course": "Artificial Intelligence", "title": "AI CT Papers Collection", "url": "https://drive.google.com/file/d/1pCG0pKs4m1zvgIs8fgLpRzcbzAm-hh3D/view?usp=sharing", "cycle": "CT1"},
    {"course": "Artificial Intelligence", "title": "AI CT Question Paper", "url": "https://drive.google.com/file/d/1EsSF6vd9pbfXWPE4w3VKgxFNcsLo7mse/view?usp=sharing", "cycle": "CT2"},
    # Electromagnetic Physics
    {"course": "Electromagnetic Theory, Quantum Mechanics, Waves and Optics", "title": "CT1 2025", "url": "https://drive.google.com/file/d/1VHarprAMKjnmZda8ZxKSlf7iGYBzo70Z/view?usp=sharing", "cycle": "CT1"},
    {"course": "Electromagnetic Theory, Quantum Mechanics, Waves and Optics", "title": "Question Bank", "url": "https://drive.google.com/file/d/18ubPMug4jRVTf36oTVcFbG7BJMwYOSPs/view?usp=drive_link", "cycle": "CT2"},
    # Fundamental of Economics
    {"course": "Fundamental Of Economics (FOE)", "title": "Questions Bank", "url": "https://docs.google.com/document/d/1HW-C1-X8DRIdmMUOB2APuuq8YCKV1RtH/edit?usp=drive_link&ouid=104856686103320873965&rtpof=true&sd=true", "cycle": "CT1"},
    # Philosophy of Engineering
    {"course": "Philosophy Of Engineering", "title": "MCQ Test 2025", "url": "https://drive.google.com/file/d/1locHTKR_KMWMiUWPvRvfkdtc5xOGdixF/view?usp=sharing", "cycle": "CT1"}
]

out_dir = "data/downloads/more_cycle_tests"
os.makedirs(out_dir, exist_ok=True)

print(f"Downloading {len(targets)} candidate CT documents to {out_dir}...")

for t in targets:
    url = t["url"]
    m = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if not m:
        m = re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if not m:
        print(f"Skipping (no drive ID): {t['title']}")
        continue
    
    fid = m.group(1)
    direct_dl = f"https://drive.google.com/uc?export=download&id={fid}"
    safe_course = re.sub(r'[^a-zA-Z0-9_-]', '_', t['course'])
    safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', t['title'])
    dest = os.path.join(out_dir, f"{safe_course}_{t['cycle']}_{safe_title}.pdf")
    
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"  Already exists: {os.path.basename(dest)} ({os.path.getsize(dest)//1024} KB)")
        continue
        
    try:
        req = urllib.request.Request(direct_dl, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as resp, open(dest, 'wb') as out_f:
            out_f.write(resp.read())
        size_kb = os.path.getsize(dest) // 1024
        print(f"  Downloaded: {os.path.basename(dest)} ({size_kb} KB)")
    except Exception as e:
        print(f"  Failed {t['title']} ({fid}): {e}")
