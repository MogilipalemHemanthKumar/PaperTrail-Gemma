# PaperTrail ✦

> **Find anything in your documents — just ask.**

PaperTrail is a local-first document intelligence app. Upload receipts, tax statements, invoices, and research papers — then ask questions across your entire library in plain English. Powered by **Gemma 4** running locally via LM Studio. No cloud. No subscriptions. Your data never leaves your machine.

---

## Demo

| Chat | Library | Upload |
|------|---------|--------|
| Ask questions across all documents | Browse your indexed library | Drop PDFs, images, scanned docs |

---

## Features

- **Natural language search** — Ask *"How much did I spend on groceries in March?"* or *"Find the transformer attention paper"* and get a direct answer
- **Cross-document Q&A** — Queries run across your entire library, not just one file
- **Multi-format support** — PDF, PNG, JPG, JPEG, WEBP, TIFF, BMP, scanned documents
- **Smart extraction** — Gemma 4 extracts structured metadata (vendor, date, total, authors, topics) from every document
- **100% local & private** — Runs entirely on your machine via LM Studio. Nothing sent to any API
- **Semantic search** — Nomic Embed finds relevant documents even when you don't remember exact keywords
- **Chat-style UI** — Clean ChatGPT-like interface built with Gradio

---

## How It Works

```
Upload a document
       ↓
PyMuPDF  ──  extracts text from PDFs (native)
Tesseract ── OCR for scanned images & image-based PDFs
       ↓
Gemma 4 (LM Studio) ── classifies doc type, extracts structured metadata
       ↓
Nomic Embed (LM Studio) ── generates semantic embeddings
       ↓
ChromaDB ── stores embeddings locally for fast similarity search
       ↓
Ask a question → Gemma 4 synthesises an answer from top matching docs
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Gemma 4 E2B-it via LM Studio |
| Embeddings | nomic-embed-text-v1.5 via LM Studio |
| OCR | PyMuPDF (digital PDFs) + Tesseract 5 (scanned) |
| Vector store | ChromaDB (local, persistent) |
| Metadata store | SQLite |
| Backend API | FastAPI + Uvicorn |
| Frontend | Gradio 5 |
| LM Studio API | OpenAI-compatible (`localhost:1234`) |

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | 3.14 tested |
| [LM Studio](https://lmstudio.ai) | Latest | Free desktop app |
| [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) | 5.x | For scanned documents |
| macOS / Linux | — | Windows untested |

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/your-username/papertrail.git
cd papertrail
```

### 2. Install Tesseract

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt install tesseract-ocr
```

### 3. Set up LM Studio

1. Download [LM Studio](https://lmstudio.ai) and open it
2. Download both of these models from the Discover tab:
   - `google/gemma-4-E2B-it` — the main LLM (5 GB)
   - `nomic-ai/nomic-embed-text-v1.5` — embeddings (84 MB)
3. Go to **Local Server** → load both models → Start Server
4. Server should be running at `http://localhost:1234`

### 4. Install Python dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

> **Note:** If you're behind a corporate proxy with a self-signed certificate, add `--trusted-host pypi.org --trusted-host files.pythonhosted.org`

### 5. Configure environment

Copy and edit the env file:

```bash
cp .env.example .env
```

Default `.env` (no changes needed if using LM Studio defaults):

```env
LMS_BASE_URL=http://localhost:1234/v1
GEMMA_MODEL=gemma-4-e2b-it
EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5
UPLOAD_DIR=data/uploads
DB_PATH=data/db/papertrail.db
CHROMA_PATH=data/db/chroma
```

### 6. Run

```bash
./run.sh
```

| Service | URL |
|---------|-----|
| Frontend UI | http://localhost:7860 |
| Backend API docs | http://localhost:8000/docs |

---

## Usage

### Uploading documents

1. Open http://localhost:7860
2. Click **Upload** tab
3. Drag and drop files or click to browse
4. Click **Upload & Index**
5. Gemma 4 will read, classify, and index each document automatically

**Supported file types:** PDF, PNG, JPG, JPEG, WEBP, TIFF, BMP

**Works with:**
- Digital PDFs (tax statements, invoices, contracts)
- Scanned PDFs (Tesseract OCR kicks in automatically)
- Receipt photos taken on your phone
- Research paper PDFs
- Any image of a document

### Asking questions

1. Click the **Chat** tab
2. Type your question and press Enter
3. Gemma 4 searches your library and answers with source citations

**Example queries:**
```
How much did I spend on groceries in April?
Find all Amazon receipts over $50
What is the main contribution of the attention paper?
Show me all invoices from last quarter
Summarise my tax statement
```

### Filtering by document type

Use the dropdown next to the search bar to restrict results to:
- All (default)
- Receipt
- Paper
- Invoice
- Other

---

## Project Structure

```
papertrail/
├── backend/
│   ├── main.py          # FastAPI routes (upload, search, list, delete)
│   ├── processor.py     # Gemma 4 via LM Studio (classify, extract, answer)
│   ├── vector_store.py  # ChromaDB + nomic-embed embeddings
│   ├── database.py      # SQLite document metadata store
│   └── models.py        # Pydantic schemas
├── frontend/
│   └── app.py           # Gradio chat UI
├── data/                # Created at runtime (gitignored)
│   ├── uploads/         # Original files
│   └── db/              # SQLite + ChromaDB
├── .env                 # Config (gitignored)
├── .env.example         # Template
├── requirements.txt
└── run.sh               # Start everything
```

---

## API Reference

The FastAPI backend exposes a REST API. Full interactive docs at `http://localhost:8000/docs`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload and index a document |
| `POST` | `/search` | Natural language search |
| `GET` | `/documents` | List all documents |
| `GET` | `/documents/{id}` | Get a single document |
| `DELETE` | `/documents/{id}` | Delete a document |

### Search request body

```json
{
  "query": "total grocery spend in March",
  "doc_type_filter": "receipt",
  "limit": 6
}
```

### Search response

```json
[
  {
    "document": {
      "id": "uuid",
      "file_name": "costco_march.jpg",
      "doc_type": "receipt",
      "metadata": {
        "vendor": "Costco",
        "date": "2026-03-14",
        "total": 127.43,
        "currency": "USD"
      }
    },
    "score": 0.91,
    "matched_excerpt": "Costco Wholesale — Member since...",
    "gemma_answer": "You spent $127.43 at Costco on March 14th."
  }
]
```

---

## Reset / Clear database

```bash
rm -rf data/
mkdir -p data/uploads data/db
./run.sh
```

---

## Troubleshooting

### `Model does not support images`
The GGUF format does not bundle the vision encoder. PaperTrail handles this by using **Tesseract OCR + PyMuPDF** for text extraction before sending to Gemma 4 (text-only). No action needed — this is expected behaviour.

### `Address already in use`
The `run.sh` script auto-kills processes on ports 8000 and 7860. If it still fails:
```bash
lsof -ti tcp:8000 | xargs kill
lsof -ti tcp:7860 | xargs kill
./run.sh
```

### LM Studio server not running
Open LM Studio → Local Server tab → load `gemma-4-e2b-it` and `nomic-embed-text-v1.5` → click **Start Server**.

### OCR returns empty text on a PDF
The PDF is likely scanned (image-based). PaperTrail automatically falls back to Tesseract OCR for these. If results are still poor, increase DPI in `processor.py`:
```python
pix = page.get_pixmap(dpi=300)   # default is 200
```

### Slow processing
Gemma 4 E2B runs three separate inference calls per document (classify → extract → OCR text). On Apple Silicon with LM Studio's Metal acceleration, expect ~5–15 seconds per document.

---

## Roadmap

- [ ] Multi-page PDF indexing (all pages, not just first)
- [ ] Batch upload with progress bar
- [ ] Delete documents from the Library tab
- [ ] Export search results to CSV
- [ ] Docker Compose deployment
- [ ] Chat history persistence across sessions

---

## Contributing

Pull requests welcome. Please open an issue first to discuss significant changes.

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a pull request

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">
  Built with <a href="https://lmstudio.ai">LM Studio</a> · <a href="https://huggingface.co/google/gemma-4-E2B-it">Gemma 4</a> · <a href="https://www.gradio.app">Gradio</a>
</div>
