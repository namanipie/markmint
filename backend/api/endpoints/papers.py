import io
import re
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Any

from backend.schemas import DocumentExtractionResult
from backend.services.extraction.pdf_parser import PDFParser
from backend.services.extraction.question_extractor import QuestionExtractor

router = APIRouter()

MAX_PDF_SIZE_BYTES = 20 * 1024 * 1024  # 20MB


@router.post("/papers/upload", response_model=DocumentExtractionResult)
async def upload_paper(file: UploadFile = File(...)) -> Any:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    if len(content) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File size exceeds the 20MB limit.")

    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF file format: missing '%PDF-' header signature.")

    # Sanitize filename
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", Path(file.filename).name)

    try:
        pages_data = PDFParser.extract_text_with_pages(io.BytesIO(content))
        result = QuestionExtractor.extract(pages_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
