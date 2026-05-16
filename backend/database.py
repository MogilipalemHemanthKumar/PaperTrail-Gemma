import sqlite3
import json
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/db/papertrail.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id          TEXT PRIMARY KEY,
            file_name   TEXT NOT NULL,
            file_path   TEXT NOT NULL,
            file_type   TEXT NOT NULL,
            doc_type    TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            doc_date    TEXT,
            extracted_text TEXT,
            metadata    TEXT
        )
    """)
    conn.commit()
    conn.close()


def insert_document(doc: dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO documents
            (id, file_name, file_path, file_type, doc_type, upload_date, doc_date, extracted_text, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        doc["id"],
        doc["file_name"],
        doc["file_path"],
        doc["file_type"],
        doc["doc_type"],
        doc["upload_date"],
        doc.get("doc_date"),
        doc.get("extracted_text"),
        json.dumps(doc.get("metadata", {})),
    ))
    conn.commit()
    conn.close()


def get_document(doc_id: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["metadata"] = json.loads(d["metadata"] or "{}")
        return d
    return None


def get_all_documents(doc_type: Optional[str] = None) -> list[dict]:
    conn = get_connection()
    if doc_type:
        rows = conn.execute(
            "SELECT * FROM documents WHERE doc_type = ? ORDER BY upload_date DESC", (doc_type,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY upload_date DESC"
        ).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["metadata"] = json.loads(d["metadata"] or "{}")
        result.append(d)
    return result


def get_documents_by_ids(ids: list[str]) -> list[dict]:
    if not ids:
        return []
    conn = get_connection()
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT * FROM documents WHERE id IN ({placeholders})", ids
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["metadata"] = json.loads(d["metadata"] or "{}")
        result.append(d)
    return result
