"""
PaperTrail — document processor.
Text extraction: PyMuPDF (PDFs) + pytesseract (images)
LLM: Gemma 4 via LM Studio text-only API
"""

import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

LMS_BASE_URL = os.getenv("LMS_BASE_URL", "http://localhost:1234/v1")
GEMMA_MODEL  = os.getenv("GEMMA_MODEL",  "gemma-4-e2b-it")

_client: OpenAI = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=LMS_BASE_URL, api_key="lm-studio")
    return _client


# ── Text extraction ───────────────────────────────────────────────────────────

def _ocr_image_file(image_path: str) -> str:
    """Run Tesseract OCR on a single image file."""
    import pytesseract
    from PIL import Image
    text = pytesseract.image_to_string(Image.open(image_path), config="--psm 3").strip()
    return text


def _extract_text_from_pdf(file_path: str) -> str:
    import fitz
    doc = fitz.open(file_path)

    # Try embedded text first (fast, perfect for digital PDFs)
    pages_text = [page.get_text().strip() for page in doc]
    embedded   = "\n\n".join(t for t in pages_text if t)

    if embedded and len(embedded) > 50:
        doc.close()
        return embedded

    # Fallback: render each page as image and OCR it (scanned PDFs)
    import tempfile, os
    from PIL import Image
    import pytesseract

    ocr_pages = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            pix.save(tmp.name)
            try:
                ocr_pages.append(
                    pytesseract.image_to_string(Image.open(tmp.name), config="--psm 3").strip()
                )
            finally:
                os.unlink(tmp.name)

    doc.close()
    result = "\n\n".join(p for p in ocr_pages if p)
    return result or "[Could not extract text from this PDF]"


def _extract_text_from_image(file_path: str) -> str:
    try:
        return _ocr_image_file(file_path)
    except ImportError:
        return "[pytesseract not installed — run: pip install pytesseract]"
    except Exception as e:
        return f"[OCR error: {e}]"


def extract_raw_text(file_path: str) -> str:
    """Extract plain text from any supported file."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return _extract_text_from_pdf(file_path)
    return _extract_text_from_image(file_path)


# ── LM Studio (text-only) ─────────────────────────────────────────────────────

def _chat(system: str, user: str, max_tokens: int = 1024) -> str:
    resp = _get_client().chat.completions.create(
        model=GEMMA_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=1.0,
        top_p=0.95,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


# ── Prompts ───────────────────────────────────────────────────────────────────

_SYS_PARSER = "You are a precise document parser. Return only valid JSON, no extra text."

CLASSIFY_PROMPT = """Based on this document text, reply with ONLY one word for the document type: receipt, paper, invoice, or other.

Document text:
{text}"""

RECEIPT_PROMPT = """Extract fields from this receipt text and return ONLY a valid JSON object:
{{
  "vendor": "store or restaurant name",
  "date": "YYYY-MM-DD or null",
  "total": 0.00,
  "currency": "USD",
  "line_items": [{{"name": "item", "price": 0.00}}],
  "payment_method": "cash/card/unknown",
  "doc_type": "receipt"
}}

Receipt text:
{text}"""

PAPER_PROMPT = """Extract fields from this academic paper text and return ONLY a valid JSON object:
{{
  "title": "paper title",
  "authors": ["author names"],
  "year": null,
  "abstract": "brief abstract",
  "topics": ["topic 1", "topic 2"],
  "summary": "2-3 sentence plain English summary",
  "doc_type": "paper"
}}

Paper text:
{text}"""

INVOICE_PROMPT = """Extract fields from this invoice text and return ONLY a valid JSON object:
{{
  "vendor": "company name",
  "date": "YYYY-MM-DD or null",
  "total": 0.00,
  "currency": "USD",
  "invoice_number": "or null",
  "doc_type": "invoice"
}}

Invoice text:
{text}"""


# ── Public API ────────────────────────────────────────────────────────────────

def classify_document(image_path: str) -> str:
    text   = extract_raw_text(image_path)
    result = _chat(_SYS_PARSER, CLASSIFY_PROMPT.format(text=text[:2000])).lower().strip()
    for label in ["receipt", "paper", "invoice"]:
        if label in result:
            return label
    return "other"


def extract_metadata(image_path: str, doc_type: str) -> dict:
    text = extract_raw_text(image_path)
    if doc_type == "receipt":
        prompt = RECEIPT_PROMPT.format(text=text[:3000])
    elif doc_type == "paper":
        prompt = PAPER_PROMPT.format(text=text[:3000])
    elif doc_type == "invoice":
        prompt = INVOICE_PROMPT.format(text=text[:3000])
    else:
        prompt = f"Describe this document. Return JSON with keys: title, summary, doc_type.\n\n{text[:2000]}"
    return _extract_json(_chat(_SYS_PARSER, prompt))


def extract_text_for_embedding(image_path: str) -> str:
    """Return raw OCR/extracted text — used for ChromaDB embedding."""
    return extract_raw_text(image_path)


def answer_query(query: str, context: str) -> str:
    return _chat(
        "You are a helpful document assistant. Answer based only on the provided context.",
        f'Query: "{query}"\n\nContext from documents:\n{context}',
        max_tokens=256,
    )
