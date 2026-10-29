import re

path = 'backend/api/endpoints/practice.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = 'matched.sort(key=lambda x: (x.get("answer_key") is None, x.get("q_num", 999)))'
replacement = '''def _parse_qnum(val):
        try:
            cleaned = re.sub(r"[^0-9]", "", str(val))
            return int(cleaned) if cleaned else 999
        except Exception:
            return 999

    matched.sort(key=lambda x: (x.get("answer_key") is None, _parse_qnum(x.get("q_num"))))'''

if target in content:
    content = content.replace(target, replacement, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched practice.py!")
else:
    print("Target string not found in practice.py")
