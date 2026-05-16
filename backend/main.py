"""
PaperTrail — FastAPI backend
Endpoints: upload, search, list, detail
"""

import os
import io
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
import fitz  # PyMuPDF — PDF → PNG conversion only
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.models import UploadResponse, SearchQuery, SearchResult, DocumentRecord
from backend import database, vector_store, processor

load_dotenv()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "data/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="PaperTrail", description="Find anything in your documents — just ask.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files", StaticFiles(directory=str(UPLOAD_DIR)), name="files")


@app.on_event("startup")
def startup():
    database.init_db()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def _pdf_first_page_to_png(pdf_path: str) -> str:
    """Render first page of PDF to a PNG and return its path."""
    png_path = pdf_path.replace(".pdf", "_p1.png")
    if not os.path.exists(png_path):
        doc = fitz.open(pdf_path)
        pix = doc[0].get_pixmap(dpi=150)
        pix.save(png_path)
    return png_path


def _get_image_path(file_path: str, file_type: str) -> str:
    """Return a path to an image file LM Studio can read via base64."""
    if file_type == "pdf":
        return _pdf_first_page_to_png(file_path)
    return file_path


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    allowed = {"pdf", "png", "jpg", "jpeg", "webp", "tiff", "bmp"}
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {allowed}")

    data = await file.read()
    file_hash = _file_hash(data)

    # Deduplicate
    for doc in database.get_all_documents():
        if file_hash in doc["file_path"]:
            return UploadResponse(
                id=doc["id"],
                file_name=doc["file_name"],
                doc_type=doc["doc_type"],
                status="duplicate",
                message="Document already exists.",
            )

    doc_id   = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{doc_id}_{file_hash}.{ext}"

    async with aiofiles.open(save_path, "wb") as f:
        await f.write(data)

    # Get image path (convert PDF page if needed)
    image_path = _get_image_path(str(save_path), ext)

    # Process with Gemma 4 via LM Studio
    try:
        doc_type       = processor.classify_document(image_path)
        metadata       = processor.extract_metadata(image_path, doc_type)
        extracted_text = processor.extract_text_for_embedding(image_path)
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(500, f"Gemma 4 processing failed: {e}")

    doc_record = {
        "id":             doc_id,
        "file_name":      file.filename,
        "file_path":      str(save_path),
        "file_type":      ext,
        "doc_type":       doc_type,
        "upload_date":    datetime.now(timezone.utc).isoformat(),
        "doc_date":       metadata.get("date"),
        "extracted_text": extracted_text,
        "metadata":       metadata,
    }
    database.insert_document(doc_record)

    vector_store.add_document(
        doc_id=doc_id,
        text=f"{file.filename}\n{extracted_text}",
        metadata={"doc_type": doc_type, "file_name": file.filename},
    )

    return UploadResponse(
        id=doc_id,
        file_name=file.filename,
        doc_type=doc_type,
        status="success",
        message=f"Processed as {doc_type}.",
    )


@app.post("/search", response_model=list[SearchResult])
def search_documents(query: SearchQuery):
    hits = vector_store.search(
        query=query.query,
        n_results=query.limit,
        doc_type=query.doc_type_filter,
    )
    if not hits:
        return []

    doc_map   = {d["id"]: d for d in database.get_documents_by_ids([h["id"] for h in hits])}
    top_texts = "\n---\n".join(h["text"][:500] for h in hits[:3])

    try:
        gemma_answer = processor.answer_query(query.query, top_texts)
    except Exception:
        gemma_answer = None

    results = []
    for hit in hits:
        doc = doc_map.get(hit["id"])
        if not doc:
            continue
        results.append(SearchResult(
            document=DocumentRecord(**doc),
            score=round(hit["score"], 4),
            matched_excerpt=hit["text"][:300].strip(),
            gemma_answer=gemma_answer if hit == hits[0] else None,
        ))
    return results


@app.get("/documents", response_model=list[DocumentRecord])
def list_documents(doc_type: str = Query(None)):
    return database.get_all_documents(doc_type)


@app.get("/documents/{doc_id}", response_model=DocumentRecord)
def get_document(doc_id: str):
    doc = database.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    doc = database.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    Path(doc["file_path"]).unlink(missing_ok=True)
    vector_store.delete_document(doc_id)
    return {"status": "deleted"}
