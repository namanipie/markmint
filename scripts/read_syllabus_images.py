import os
import glob
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

client = genai.Client()

images = sorted(glob.glob("data/s3_s4/syllabus/images/*.png"))

prompt = """Read this syllabus page carefully. Extract the Course Code, Course Title, and for each Unit (Unit 1 to Unit 5), list the Unit Name, and all specific topics/subtopics mentioned verbatim. If this page only has some units or learning outcomes, extract whatever is visible."""

for img_path in images:
    course_name = os.path.basename(img_path)
    print(f"=== {course_name} ===")
    with open(img_path, "rb") as f:
        img_bytes = f.read()
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            prompt
        ]
    )
    print(response.text)
    print("\n" + "="*50 + "\n")
