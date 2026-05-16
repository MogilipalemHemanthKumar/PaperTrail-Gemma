# PaperTrail
### *Find anything in your documents — just ask.*

**PRD: Papers & Receipts Upload and Natural Language Search using Gemma 4**

---

## 1. Overview

A local-first document intelligence app that lets users upload papers and receipts (images or PDFs) and search through them using plain English queries, powered by Google's Gemma 4 multimodal model.

---

## 2. Problem Statement

Every year, individuals and knowledge workers drown in a growing pile of unstructured documents — crumpled receipts shoved in a drawer, research papers scattered across a Downloads folder, invoices buried in email threads. The real problem isn't storage. It's **retrieval under pressure**.

Today's tools fail in three distinct ways:

- **Search engines need keywords, not intent.** When you can't remember the exact vendor name or paper title, traditional search returns nothing. You already know what you're looking for — you just can't phrase it like a database.
- **Manual organization is a tax on your time.** Folders, tags, spreadsheets — every system requires discipline upfront and breaks down within weeks. People don't organize documents; they dump them and hope.
- **Cloud-based AI tools trade privacy for convenience.** Uploading financial receipts or proprietary research to third-party APIs is a non-starter for privacy-conscious users, researchers handling sensitive data, or anyone operating under compliance constraints.

The gap: **no tool lets you ask a human-style question about your own private documents and get a direct, accurate answer — without sending your data anywhere.**

This product closes that gap. By running Gemma 4 entirely on-device, it understands what's *in* your documents — line items, dates, authors, topics — and answers questions the way a smart assistant would, without ever leaving your machine.

---

## 3. Target Audience

### Who This Is For

| Segment | Profile | Core Pain |
|---------|---------|-----------|
| **Independent Researchers & Grad Students** | Accumulate 100s of PDFs — papers, notes, citations — across multiple projects. Spend hours re-reading to locate a specific argument or methodology. | "I know I read this somewhere, but I can't find it." |
| **Freelancers & Self-Employed Professionals** | Handle their own bookkeeping — receipts from client dinners, software subscriptions, travel. Tax season becomes archaeology. | "I need all receipts over $100 from Q1 — where are they?" |
| **Privacy-First Power Users** | Technical users who refuse cloud AI tools for personal documents. Want the intelligence of GPT-4V but locally, with no data leakage. | "I won't upload my bank statements to OpenAI." |
| **Small Business Owners** | Manage invoices, vendor receipts, and contracts without a dedicated finance team. Need fast answers without hiring an accountant to dig through files. | "Did we pay the contractor in March or April?" |
| **Academic & Corporate Librarians** | Curate and surface institutional knowledge — white papers, policy docs, internal research. Current systems require manual indexing. | "Our document archive is useless unless you know what's in it already." |

### Why These Users, Why Now

1. **Gemma 4's on-device multimodal capability is new.** Prior open-weight models couldn't reliably extract structured data from receipt images or understand paper abstracts without fine-tuning. Gemma 4 changes this — making a local-first product viable for the first time.

2. **AI fatigue is creating a privacy backlash.** Post-2024, users are increasingly wary of uploading personal documents to cloud services. A capable local alternative has a clear, growing market.

3. **The freelance/creator economy is expanding.** 73 million Americans freelance. Most manage their own receipts. None of them have a CFO. They need tools that work like a smart accountant but cost nothing per query.

4. **Research volume is exploding.** arXiv publishes 20,000+ papers per month. A researcher's personal library is no longer manageable by hand. Semantic search over their *own curated collection* is the missing layer.

---

## 4. Solution

Use Gemma 4's vision and language capabilities to understand document content and answer natural language queries like *"show me all receipts from Costco over $50"* or *"find the paper about transformer attention mechanisms from 2023"* — entirely on your own machine, with zero data leaving your environment.

---

## 5. Goals

- Users can upload receipts and papers (PDF, PNG, JPG, JPEG) via drag-and-drop or file picker
- Documents are processed by Gemma 4 to extract structured metadata and semantic content
- Users can search using natural language and get relevant results instantly
- All processing runs locally — no data sent to external APIs

---

## 6. Non-Goals

- Cloud sync or multi-user support (v1)
- Editing or annotating documents
- OCR for handwritten text beyond Gemma 4's native capability
- Mobile app

---

## 7. User Stories

| # | As a... | I want to... | So that... |
|---|---------|--------------|------------|
| 1 | User | Upload a batch of receipt images | I don't have to add them one by one |
| 2 | User | Ask "how much did I spend on groceries in April?" | I get a summarized answer without manual sorting |
| 3 | User | Search "paper about RAG with citations" | I find the right research paper immediately |
| 4 | User | See a preview of the matched document | I can confirm it's the one I need |
| 5 | User | Filter results by document type (receipt vs. paper) | I narrow down results faster |

---

## 8. Features

### 5.1 Document Upload
- Drag-and-drop or file picker (PDF, PNG, JPG, JPEG)
- Batch upload support (up to 50 files at once)
- Progress indicator per file
- Duplicate detection (hash-based)

### 5.2 Document Processing Pipeline
- **Step 1 — Ingest:** Save original file to local storage
- **Step 2 — Vision extraction:** Send image/page to Gemma 4 multimodal model to extract:
  - Document type (receipt, invoice, academic paper, contract, etc.)
  - Key fields (vendor name, date, total amount, line items for receipts; title, authors, abstract for papers)
  - Full text content
- **Step 3 — Embedding:** Generate semantic embeddings from extracted text using Gemma 4
- **Step 4 — Index:** Store embeddings + metadata in a local vector store (ChromaDB)

### 5.3 Natural Language Search
- Text input for free-form queries
- Query is embedded and matched against document index (vector similarity)
- Gemma 4 re-ranks and summarizes top results in context of the query
- Results display: thumbnail, document type badge, matched excerpt, relevance score

### 5.4 Filters & Sorting
- Filter by: document type, date range, amount range (receipts), tags
- Sort by: relevance, date uploaded, date on document

### 5.5 Document Viewer
- In-app preview of the original file
- Highlighted matched sections

---

## 9. Technical Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (UI)                     │
│         React + Tailwind  or  Python Gradio          │
└────────────────────────┬────────────────────────────┘
                         │ REST / WebSocket
┌────────────────────────▼────────────────────────────┐
│                   Backend (API)                      │
│                  FastAPI (Python)                    │
│                                                      │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────┐  │
│  │  Ingest     │   │  Gemma 4     │   │  Search  │  │
│  │  Service    │──▶│  Processor   │──▶│  Service │  │
│  │  (upload,   │   │  (vision +   │   │  (query, │  │
│  │   dedup)    │   │   extract)   │   │   rank)  │  │
│  └─────────────┘   └──────────────┘   └──────────┘  │
└──────────────────────────┬──────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌─────────────┐  ┌───────────┐  ┌──────────────┐
   │  File Store │  │ ChromaDB  │  │  SQLite DB   │
   │  (originals)│  │ (vectors) │  │  (metadata)  │
   └─────────────┘  └───────────┘  └──────────────┘
```

### Key Components

| Component | Technology |
|-----------|------------|
| LLM / Vision Model | Gemma 4 (via Ollama or HuggingFace Transformers) |
| Vector Store | ChromaDB (local) |
| Metadata Store | SQLite |
| Backend API | FastAPI (Python) |
| Frontend | Gradio (quick) or React (polished) |
| File Storage | Local filesystem |
| PDF Rendering | pdf2image / PyMuPDF |

---

## 10. Gemma 4 Integration Details

- **Model:** `gemma-4` multimodal (vision + text)
- **Inference:** Run locally via Ollama (`ollama run gemma4`) or HuggingFace pipeline
- **Extraction prompt (receipts):**
  ```
  Extract from this receipt image: vendor name, date, total amount,
  individual line items with prices, payment method.
  Return as JSON.
  ```
- **Extraction prompt (papers):**
  ```
  Extract from this academic paper: title, authors, publication year,
  abstract, key topics, and a 3-sentence summary.
  Return as JSON.
  ```
- **Search re-ranking prompt:**
  ```
  Given the query: "{query}"
  And these document summaries: {summaries}
  Rank them by relevance and explain why the top result matches.
  ```

---

## 11. Data Model

### Document
```json
{
  "id": "uuid",
  "file_path": "string",
  "file_name": "string",
  "file_type": "pdf | png | jpg",
  "doc_type": "receipt | paper | invoice | other",
  "upload_date": "ISO 8601",
  "doc_date": "ISO 8601 | null",
  "extracted_text": "string",
  "metadata": {},
  "embedding_id": "string"
}
```

### Receipt Metadata
```json
{
  "vendor": "string",
  "total": "float",
  "currency": "string",
  "line_items": [{"name": "string", "price": "float"}],
  "payment_method": "string"
}
```

### Paper Metadata
```json
{
  "title": "string",
  "authors": ["string"],
  "year": "int",
  "abstract": "string",
  "topics": ["string"],
  "summary": "string"
}
```

---

## 12. User Interface Screens

### Screen 1 — Dashboard
- Upload zone (drag-and-drop)
- Search bar (prominent, top-center)
- Recent documents grid
- Stats: total docs, total receipts, total papers

### Screen 2 — Search Results
- Query displayed at top
- Gemma 4 answer/summary card (synthesized response)
- Ranked document cards with thumbnail + excerpt
- Sidebar filters

### Screen 3 — Document Detail
- Original file preview
- Extracted metadata panel
- Related documents (similar embeddings)

---

## 13. Milestones

| Phase | Scope | Target |
|-------|-------|--------|
| **Phase 1 — MVP** | Upload, Gemma 4 extraction, basic keyword + vector search, Gradio UI | Week 2 |
| **Phase 2 — Polish** | Filters, batch upload, duplicate detection, React UI | Week 4 |
| **Phase 3 — Intelligence** | Gemma 4 re-ranking, summarized answers, related docs | Week 6 |

---

## 14. Success Metrics

- Search returns correct top result in >85% of test queries
- Document processing time <10s per page on consumer hardware
- Supports library of 1,000+ documents without degraded search speed (<1s query)

---

## 15. Open Questions

1. Should we support multi-page PDFs as a single document or index each page separately?
2. GPU required for Gemma 4 locally — fallback to Ollama CPU mode acceptable for v1?
3. Should extracted metadata be editable by the user for correction?
4. Privacy: add option to auto-redact sensitive fields (credit card numbers, SSNs) before storing?
