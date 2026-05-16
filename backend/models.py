from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentBase(BaseModel):
    file_name: str
    file_type: str
    doc_type: str  # receipt | paper | invoice | other


class DocumentRecord(DocumentBase):
    id: str
    file_path: str
    upload_date: str
    doc_date: Optional[str] = None
    extracted_text: Optional[str] = None
    metadata: Optional[dict] = None

    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    query: str
    doc_type_filter: Optional[str] = None  # receipt | paper | invoice | other | None
    limit: int = 10


class SearchResult(BaseModel):
    document: DocumentRecord
    score: float
    matched_excerpt: str
    gemma_answer: Optional[str] = None


class UploadResponse(BaseModel):
    id: str
    file_name: str
    doc_type: str
    status: str
    message: str
