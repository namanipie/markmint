import pytest
from fastapi.testclient import TestClient
import os
from io import BytesIO
from backend.main import app

def generate_synthetic_pdf() -> BytesIO:
    c1 = "BT /F1 12 Tf 72 720 Td 15 TL (EXAM 101 - Introduction to CS) Tj T* (SECTION A - Core Concepts) Tj T* (1. Explain BFS. [5 marks]) Tj T* (This is a detailed question.) Tj T* (Q2. Implement DFS. \\(10\\)) Tj T* (Provide Python code.) Tj ET"
    c2 = "BT /F1 12 Tf 72 720 Td 15 TL (SECTION B) Tj T* (3\\) Compare trees and graphs. [15]) Tj ET"
    pdf_str = f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R 6 0 R] /Count 2 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length {len(c1)} >>
stream
{c1}
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
6 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 7 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
7 0 obj << /Length {len(c2)} >>
stream
{c2}
endstream
endobj
xref
0 8
0000000000 65535 f 
0000000009 00000 n 
0000000056 00000 n 
0000000119 00000 n 
0000000232 00000 n 
0000000288 00000 n 
0000000358 00000 n 
0000000471 00000 n 
trailer << /Size 8 /Root 1 0 R >>
startxref
530
%%EOF"""
    return BytesIO(pdf_str.encode("latin1"))




def test_extract_questions_from_pdf(client: TestClient) -> None:
    pdf_buffer = generate_synthetic_pdf()

    response = client.post(
        "/api/papers/upload",
        files={"file": ("synthetic_exam.pdf", pdf_buffer, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["successful"] is True
    assert data["total_pages"] == 2

    sections = data["sections"]
    assert len(sections) == 2

    # Check Section A
    sec_a = sections[0]
    assert sec_a["name"] == "Section A"
    assert len(sec_a["questions"]) == 2

    q1 = sec_a["questions"][0]
    assert q1["question_number"] == "1"
    assert q1["marks"] == 5.0
    assert q1["page_number"] == 1
    assert "Explain BFS." in q1["original_text"]
    assert "This is a detailed question." in q1["original_text"]

    q2 = sec_a["questions"][1]
    assert q2["question_number"] == "2"
    assert q2["marks"] == 10.0

    # Check Section B
    sec_b = sections[1]
    assert sec_b["name"] == "Section B"
    assert len(sec_b["questions"]) == 1

    q3 = sec_b["questions"][0]
    assert q3["question_number"] == "3"
    assert q3["marks"] == 15.0
    assert "Compare trees and graphs." in q3["original_text"]
    assert q3["page_number"] == 2


def test_upload_non_pdf_rejected(client: TestClient) -> None:
    buffer = BytesIO(b"Hello world, plain text")
    response = client.post(
        "/api/papers/upload",
        files={"file": ("notes.txt", buffer, "text/plain")},
    )
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]


def test_upload_fake_pdf_header_rejected(client: TestClient) -> None:
    buffer = BytesIO(b"MALICIOUS_EXE_OR_CORRUPT_HEADER")
    response = client.post(
        "/api/papers/upload",
        files={"file": ("test.pdf", buffer, "application/pdf")},
    )
    assert response.status_code == 400
    assert "missing '%PDF-' header signature" in response.json()["detail"]


def test_upload_oversized_file_rejected(client: TestClient) -> None:
    oversized = BytesIO(b"%PDF-" + b"0" * (20 * 1024 * 1024 + 10))
    response = client.post(
        "/api/papers/upload",
        files={"file": ("huge.pdf", oversized, "application/pdf")},
    )
    assert response.status_code == 413
    assert "20MB limit" in response.json()["detail"]


def test_pdf_symbol_preservation(): pass  # ponytail: regression slot — run with known math/chem PDF

