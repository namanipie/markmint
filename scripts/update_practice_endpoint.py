from pathlib import Path

with open('backend/api/endpoints/practice.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'CT_QUESTIONS_PATH = Path("data/extracted_cycle_test_questions.json")',
    'CT_QUESTIONS_PATH = Path(__file__).resolve().parents[3] / "data" / "extracted_cycle_test_questions.json"'
)

with open('backend/api/endpoints/practice.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated CT_QUESTIONS_PATH successfully")
