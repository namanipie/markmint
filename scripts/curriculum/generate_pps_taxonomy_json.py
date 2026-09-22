"""
Generate course_05_pps.json declarative taxonomy definition for PPS (Course 5).
Includes enhanced rules for formatted I/O, control flow, functions, storage classes, and Python basics.
"""
import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.services.taxonomy_rules.pps_rules import PPS_TAXONOMY_RULES

PPS_DATA = {
    "schema_version": "1.0",
    "taxonomy_version": "1.0.0",
    "course": {
        "id": 5,
        "name": "Programming For Problem Solving",
        "canonical_code": "21CSS101J",
        "code": "SEM1-PPS",
        "regulation_year": 2021,
        "department": "Computer Science and Engineering"
    },
    "provenance": {
        "source_document": "SRMIST B.Tech Regulation 2021 Curriculum & Syllabus - 21CSS101J Programming For Problem Solving",
        "regulation": "2021",
        "approved_by": "Academic Council SRMIST",
        "notes": "Authoritative 5-unit syllabus covering Problem Solving & C Basics, Control Flow & Pointers, Strings & Functions, Python Basics, and NumPy/Pandas."
    },
    "units": [
        {
            "id": 5,
            "number": 1,
            "name": "Problem Solving and C Basics",
            "topics": []
        },
        {
            "id": 58,
            "number": 2,
            "name": "Control Flow, Arrays, and Pointers",
            "topics": []
        },
        {
            "id": 59,
            "number": 3,
            "name": "Strings, Functions, and Storage Classes",
            "topics": []
        },
        {
            "id": 60,
            "number": 4,
            "name": "Introduction to Python and Data Structures",
            "topics": []
        },
        {
            "id": 61,
            "number": 5,
            "name": "Data Analysis with NumPy and Pandas",
            "topics": []
        }
    ]
}

# Map rules into units
unit_map = {u["id"]: u for u in PPS_DATA["units"]}

for r in PPS_TAXONOMY_RULES:
    # Add enhancements
    strong = list(r.strong_phrases)
    specific = list(r.specific_keywords)

    if r.topic_id == 142: # C Program Structure & Tokens
        strong.extend(["scanf function", "printf function", "header file is used for", "clrscr", "main function is mandatory", "format identifier"])
        specific.extend(["scanf", "printf", "header file"])
    elif r.topic_id == 143: # Data Types & Operators
        strong.extend(["hexadecimal values", "format identifier %d", "%d data type", "ternary operator", "bitwise operator", "logical operator &&", "sizeof operator", "type casting in c"])
        specific.extend(["format identifier", "hexadecimal", "bitwise operator", "ternary operator"])
    elif r.topic_id == 144: # Conditional Branching
        strong.extend(["switch-case statement", "switch case", "nested if statement", "if-else statement"])
    elif r.topic_id == 145: # Loops
        strong.extend(["entry controlled loop", "exit controlled loop", "entry-controlled", "exit-controlled", "do-while loop", "while is an entry", "infinite loop in c", "break and continue in c"])
        specific.extend(["entry controlled", "exit controlled", "entry-controlled", "exit-controlled"])
    elif r.topic_id == 148: # Character Arrays & Strings
        strong.extend(["string handling functions", "strlen", "strcpy", "strcat", "strcmp", "string in c", "null character in string"])
    elif r.topic_id == 149: # Functions & Parameter Passing
        strong.extend(["user-defined functions", "call by value", "call by reference", "actual and formal arguments", "parameter passing in c"])
    elif r.topic_id == 150: # Recursion
        strong.extend(["recursion function", "recursive function in c", "base case in recursion", "calculate the sum of digits using recursion", "factorial using recursion"])
    elif r.topic_id == 151: # Storage Classes
        strong.extend(["storage classes in c", "auto extern static register", "static storage class", "register storage class", "extern storage class", "variable scope and linkage"])
        specific.extend(["storage classes", "storage class"])
    elif r.topic_id == 152: # Python Basics
        strong.extend(["in python string indexing", "ord function", "chr function", "python built-in data types", "s = 'foobar'", "concatenate strings in python"])

    t_dict = {
        "id": r.topic_id,
        "name": r.topic_name,
        "canonical_name": r.topic_name,
        "aliases": [r.topic_name],
        "strong_phrases": strong,
        "specific_keywords": specific,
        "negative_guards": list(r.negative_guards),
        "context_hints": ["c programming", "python", "problem solving"]
    }
    unit_map[r.unit_id]["topics"].append(t_dict)

target_path = os.path.join(
    BASE_DIR, "backend", "services", "taxonomy_registry", "definitions", "course_05_pps.json"
)
with open(target_path, "w", encoding="utf-8") as f:
    json.dump(PPS_DATA, f, indent=2)

print(f"Successfully generated {target_path}")
