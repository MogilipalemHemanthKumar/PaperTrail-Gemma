"""
ChromaDB vector store — embeddings via LM Studio's nomic-embed model.
"""

import os
from typing import Optional
from dotenv import load_dotenv

import chromadb
from chromadb.config import Settings
from openai import OpenAI

load_dotenv()

CHROMA_PATH     = os.getenv("CHROMA_PATH",     "data/db/chroma")
LMS_BASE_URL    = os.getenv("LMS_BASE_URL",    "http://localhost:1234/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5")
COLLECTION_NAME = "papertrail_docs"

_client:     OpenAI = None
_collection         = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=LMS_BASE_URL, api_key="lm-studio")
    return _client


def _embed(text: str) -> list[float]:
    resp = _get_client().embeddings.create(model=EMBEDDING_MODEL, input=text)
    return resp.data[0].embedding


def _get_collection():
    global _collection
    if _collection is None:
        os.makedirs(CHROMA_PATH, exist_ok=True)
        client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_document(doc_id: str, text: str, metadata: dict):
    _get_collection().upsert(
        ids=[doc_id],
        embeddings=[_embed(text)],
        documents=[text],
        metadatas=[{k: str(v) for k, v in metadata.items()}],
    )


def search(query: str, n_results: int = 10, doc_type: Optional[str] = None) -> list[dict]:
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return []

    results = collection.query(
        query_embeddings=[_embed(query)],
        n_results=min(n_results, count),
        where={"doc_type": doc_type} if doc_type else None,
        include=["documents", "metadatas", "distances"],
    )

    return [
        {
            "id":       results["ids"][0][i],
            "text":     results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "score":    1 - results["distances"][0][i],
        }
        for i in range(len(results["ids"][0]))
    ]


def delete_document(doc_id: str):
    _get_collection().delete(ids=[doc_id])
