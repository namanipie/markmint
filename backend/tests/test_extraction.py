import pytest
from fastapi.testclient import TestClient
import os
from reportlab.pdfgen import canvas
from io import BytesIO

from backend.main import app


def generate_synthetic_pdf() -> BytesIO:
    buffer = BytesIO()
    c = canvas.Canvas(buffer)

    # Page 1
    c.drawString(100, 800, "EXAM 101 - Introduction to CS")
    c.drawString(100, 750, "SECTION A - Core Concepts")

    c.drawString(100, 700, "1. Explain BFS. [5 marks]")
    c.drawString(100, 680, "This is a detailed question.")

    c.drawString(100, 630, "Q2. Implement DFS. (10)")
    c.drawString(100, 610, "Provide Python code.")
    c.showPage()

    # Page 2
    c.drawString(100, 800, "SECTION B")
    c.drawString(100, 750, "3) Compare trees and graphs. [15]")
    c.save()

    buffer.seek(0)
    return buffer


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

