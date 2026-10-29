import json
import re

def run():
    print("Loading data/extracted_cycle_test_questions.json...")
    with open("data/extracted_cycle_test_questions.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for i, q in enumerate(data):
        txt = q.get("question_text", "")
        # Guard: If question is a Bankers' Algorithm table or 8-15 mark descriptive question, restore as descriptive!
        is_descriptive_exception = any(kw in txt.lower() for kw in [
            "allocation | max", "allocation max available", "banker", "fischer projection",
            "draw the flowchart", "write the algorithm", "give the differences between",
            "explain the 6 steps", "class cube extends", "fit a straight line", "runge-kutta"
        ]) or q.get("marks", 1) >= 4
        
        if is_descriptive_exception and q.get("is_mcq") and "banker" in txt.lower() or "allocation | max" in txt.lower() or "allocation max available" in txt.lower() or "fischer projection" in txt.lower():
            q["is_mcq"] = False
            q["q_type"] = "Part B (Medium Answer)" if q.get("marks", 0) <= 8 else "Part C (Comprehensive)"
            q["section"] = "Part B (Medium Answer Questions)" if q.get("marks", 0) <= 8 else "Part C (Comprehensive Questions)"
            print(f"Restored #{i} as descriptive: {txt[:60]}")

    with open("data/extracted_cycle_test_questions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Guard pass completed.")

if __name__ == "__main__":
    run()
