"""
PaperTrail — Clean light-mode chat UI
"""

import os
import requests
from pathlib import Path
import gradio as gr

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# ── API ───────────────────────────────────────────────────────────────────────

def _get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=30)
        return r.json() if r.ok else []
    except Exception:
        return []

def _post(path, **kwargs):
    try:
        return requests.post(f"{API_BASE}{path}", timeout=120, **kwargs)
    except Exception:
        return None

# ── Chat helpers ──────────────────────────────────────────────────────────────

TYPE_BADGE = {
    "receipt": ("Receipt", "#065f46", "#d1fae5"),
    "paper":   ("Paper",   "#1e40af", "#dbeafe"),
    "invoice": ("Invoice", "#92400e", "#fef3c7"),
    "other":   ("Other",   "#4b5563", "#f3f4f6"),
}

def ask(query, doc_type, history):
    if not query.strip():
        return history, "", _render_chat(history)

    resp = _post("/search", json={
        "query": query,
        "doc_type_filter": doc_type if doc_type != "All" else None,
        "limit": 6,
    })

    if resp is None:
        ai_content = _ai_bubble("⚠️ Cannot reach backend. Is the server running?", [])
    elif not resp.ok:
        ai_content = _ai_bubble(f"⚠️ Server error: {resp.text[:120]}", [])
    else:
        results = resp.json()
        if not results:
            ai_content = _ai_bubble(
                "No matching documents found. Try uploading some documents first, or rephrase your question.", []
            )
        else:
            answer  = results[0].get("gemma_answer") or "Here are the most relevant documents I found:"
            sources = []
            for r in results:
                doc  = r["document"]
                meta = doc.get("metadata") or {}
                sources.append({
                    "label":   meta.get("vendor") or meta.get("title") or doc["file_name"],
                    "type":    doc["doc_type"],
                    "score":   int(r["score"] * 100),
                    "date":    doc.get("doc_date") or meta.get("date") or "",
                    "total":   str(meta.get("total", "")),
                    "excerpt": r["matched_excerpt"][:180],
                })
            ai_content = _ai_bubble(answer, sources)

    history = history + [("user", query), ("ai", ai_content)]
    return history, "", _render_chat(history)

def _user_bubble(text):
    return f"""
<div style="display:flex;justify-content:flex-end;margin-bottom:24px;">
  <div style="max-width:72%;background:#6366f1;color:#fff;border-radius:20px 20px 4px 20px;
              padding:13px 18px;font-size:0.95rem;line-height:1.6;
              box-shadow:0 2px 8px rgba(99,102,241,0.3);">
    {text}
  </div>
</div>"""

def _ai_bubble(answer, sources):
    source_html = ""
    if sources:
        cards = ""
        for s in sources:
            label, text_c, bg_c = TYPE_BADGE.get(s["type"], TYPE_BADGE["other"])
            meta_bits = []
            if s["date"]:  meta_bits.append(f"📅 {s['date']}")
            if s["total"]: meta_bits.append(f"💰 {s['total']}")
            meta_str = "  ·  ".join(meta_bits)

            cards += f"""
<div style="background:#f9fafb;border:1px solid #d1d5db;border-radius:12px;
            padding:12px 14px;margin-bottom:8px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap;">
    <span style="background:{bg_c};color:{text_c};font-size:0.65rem;font-weight:700;
                 text-transform:uppercase;letter-spacing:0.5px;border-radius:999px;
                 padding:2px 9px;">{label}</span>
    <span style="color:#111827;font-size:0.875rem;font-weight:700;flex:1;
                 white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{s['label']}</span>
    <span style="background:#ede9fe;color:#6d28d9;font-size:0.7rem;font-weight:700;
                 border-radius:999px;padding:2px 8px;">{s['score']}%</span>
  </div>
  {f'<div style="color:#374151;font-size:0.78rem;font-weight:500;margin-bottom:6px;">{meta_str}</div>' if meta_str else ''}
  <div style="color:#374151;font-size:0.82rem;font-style:italic;line-height:1.55;
              border-left:3px solid #a5b4fc;padding-left:10px;">"{s['excerpt']}…"</div>
</div>"""

        source_html = f"""
<div style="margin-top:14px;padding-top:14px;border-top:1px solid #e5e7eb;">
  <div style="color:#6b7280;font-size:0.7rem;font-weight:700;text-transform:uppercase;
              letter-spacing:1px;margin-bottom:10px;">Sources</div>
  {cards}
</div>"""

    return f"""
<div style="display:flex;gap:12px;margin-bottom:24px;align-items:flex-start;">
  <div style="width:34px;height:34px;background:linear-gradient(135deg,#6366f1,#8b5cf6);
              border-radius:999px;flex-shrink:0;display:flex;align-items:center;
              justify-content:center;font-size:0.85rem;color:#fff;font-weight:800;
              margin-top:2px;">G</div>
  <div style="flex:1;background:#fff;border:1px solid #d1d5db;border-radius:4px 16px 16px 16px;
              padding:18px 20px;box-shadow:0 1px 6px rgba(0,0,0,0.08);">
    <div style="color:#111827;font-size:0.97rem;line-height:1.8;font-weight:400;">{answer}</div>
    {source_html}
  </div>
</div>"""

def _render_chat(history):
    if not history:
        return """
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
            height:100%;min-height:340px;text-align:center;padding:40px 24px;">
  <div style="width:52px;height:52px;background:linear-gradient(135deg,#6366f1,#8b5cf6);
              border-radius:14px;display:flex;align-items:center;justify-content:center;
              font-size:1.4rem;color:#fff;font-weight:900;margin-bottom:18px;
              box-shadow:0 6px 20px rgba(99,102,241,0.35);">✦</div>
  <div style="color:#111827;font-size:1.15rem;font-weight:700;margin-bottom:8px;">
    How can I help with your documents?
  </div>
  <div style="color:#6b7280;font-size:0.88rem;line-height:1.65;max-width:380px;">
    Ask questions across all your uploaded receipts, papers, and invoices.
    I'll search and summarise the answers for you.
  </div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-top:22px;">
    <div style="background:#f5f3ff;border:1px solid #ddd6fe;border-radius:10px;
                padding:8px 14px;color:#6d28d9;font-size:0.8rem;">
      "Total groceries in March?"
    </div>
    <div style="background:#f5f3ff;border:1px solid #ddd6fe;border-radius:10px;
                padding:8px 14px;color:#6d28d9;font-size:0.8rem;">
      "Find the attention paper"
    </div>
    <div style="background:#f5f3ff;border:1px solid #ddd6fe;border-radius:10px;
                padding:8px 14px;color:#6d28d9;font-size:0.8rem;">
      "All invoices over $200"
    </div>
  </div>
</div>"""

    html = ""
    for role, content in history:
        html += _user_bubble(content) if role == "user" else content
    return html

# ── Library ───────────────────────────────────────────────────────────────────

def load_library(doc_type):
    all_docs = _get("/documents")
    counts = {}
    for d in all_docs:
        t = d.get("doc_type", "other")
        counts[t] = counts.get(t, 0) + 1

    filtered = _get("/documents",
        params={"doc_type": doc_type.lower()} if doc_type != "All" else None)

    stats = f"""
<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px;">
  {_stat_chip("Total",    len(all_docs),           "#6366f1", "#ede9fe")}
  {_stat_chip("Receipts", counts.get("receipt",0), "#059669", "#d1fae5")}
  {_stat_chip("Papers",   counts.get("paper",0),   "#2563eb", "#dbeafe")}
  {_stat_chip("Invoices", counts.get("invoice",0), "#d97706", "#fef3c7")}
</div>"""

    if not filtered:
        return stats + """
<div style="text-align:center;padding:56px 20px;">
  <div style="font-size:2rem;margin-bottom:12px;">📂</div>
  <div style="color:#374151;font-size:0.95rem;font-weight:600;">No documents yet.</div>
  <div style="color:#9ca3af;font-size:0.85rem;margin-top:6px;">
    Go to <strong>Upload</strong> to add your first document.
  </div>
</div>"""

    cards = ""
    for doc in filtered:
        meta  = doc.get("metadata") or {}
        dtype = doc["doc_type"]
        label = meta.get("vendor") or meta.get("title") or doc["file_name"]
        date  = doc.get("doc_date") or meta.get("date") or "—"
        amt   = str(meta.get("total", ""))
        badge_label, text_c, bg_c = TYPE_BADGE.get(dtype, TYPE_BADGE["other"])

        amount_row = f'<div style="color:#d97706;font-size:0.82rem;font-weight:700;margin-top:4px;">💰 {amt}</div>' if amt else ""

        cards += f"""
<div style="background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:16px;
            transition:all 0.2s;cursor:default;box-shadow:0 1px 3px rgba(0,0,0,0.05);"
     onmouseover="this.style.borderColor='#a5b4fc';this.style.boxShadow='0 4px 16px rgba(99,102,241,0.15)';this.style.transform='translateY(-2px)'"
     onmouseout="this.style.borderColor='#e5e7eb';this.style.boxShadow='0 1px 3px rgba(0,0,0,0.05)';this.style.transform='translateY(0)'">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
    <span style="background:{bg_c};color:{text_c};font-size:0.65rem;font-weight:700;
                 text-transform:uppercase;letter-spacing:0.5px;border-radius:999px;
                 padding:3px 10px;">{badge_label}</span>
    <span style="font-size:0.68rem;color:#d1d5db;font-family:monospace;">{doc['id'][:8]}</span>
  </div>
  <div style="color:#111827;font-weight:700;font-size:0.92rem;line-height:1.4;margin-bottom:6px;
              white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="{label}">{label}</div>
  <div style="color:#6b7280;font-size:0.75rem;">📅 {date}</div>
  {amount_row}
  <div style="color:#d1d5db;font-size:0.7rem;margin-top:8px;white-space:nowrap;
              overflow:hidden;text-overflow:ellipsis;" title="{doc['file_name']}">📄 {doc['file_name']}</div>
</div>"""

    grid = f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px;">{cards}</div>'
    return stats + grid

def _stat_chip(label, value, text_c, bg_c):
    return f"""
<div style="background:{bg_c};border-radius:12px;padding:14px 22px;
            text-align:center;min-width:90px;">
  <div style="color:{text_c};font-size:1.6rem;font-weight:800;line-height:1;">{value}</div>
  <div style="color:{text_c};opacity:0.7;font-size:0.72rem;text-transform:uppercase;
              letter-spacing:0.8px;margin-top:4px;">{label}</div>
</div>"""

# ── Upload ────────────────────────────────────────────────────────────────────

def upload_files(files):
    if not files:
        return _upload_placeholder()
    html = ""
    for file in (files if isinstance(files, list) else [files]):
        fname = Path(file.name).name
        with open(file.name, "rb") as f:
            resp = _post("/upload", files={"file": (fname, f)})
        if resp is None:
            html += _file_row(fname, "error", "Backend unreachable")
        elif resp.ok:
            d = resp.json()
            if d.get("status") == "duplicate":
                html += _file_row(fname, "dup", "Already in your library")
            else:
                html += _file_row(fname, "ok", f"Indexed as <b>{d['doc_type']}</b>")
        else:
            html += _file_row(fname, "error", resp.json().get("detail", resp.text)[:80])
    return html

def _file_row(name, status, msg):
    cfg = {
        "ok":    ("#065f46", "#d1fae5", "#059669", "✓"),
        "dup":   ("#92400e", "#fef3c7", "#d97706", "◈"),
        "error": ("#991b1b", "#fee2e2", "#dc2626", "✕"),
    }
    tc, bg, ac, icon = cfg[status]
    return f"""
<div style="display:flex;align-items:center;gap:12px;padding:12px 16px;
            background:{bg};border-radius:10px;margin-bottom:8px;">
  <span style="color:{ac};font-size:1rem;font-weight:700;width:20px;text-align:center;">{icon}</span>
  <div style="flex:1;min-width:0;">
    <div style="color:{tc};font-size:0.88rem;font-weight:600;
                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>
    <div style="color:{ac};font-size:0.76rem;margin-top:1px;">{msg}</div>
  </div>
</div>"""

def _upload_placeholder():
    return '<div style="color:#9ca3af;font-size:0.85rem;text-align:center;padding:16px;">Select files and click Upload & Index.</div>'

# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
/* Force light background everywhere */
*, body, .gradio-container, .main, footer {
    background-color: #f9fafb !important;
}

.gradio-container {
    max-width: 1080px !important;
    margin: 0 auto !important;
    padding: 0 32px 60px !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

/* Remove Gradio footer */
footer { display: none !important; }

/* ── Header ── */
#pt-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 22px 0 20px;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 20px;
}
.pt-logo-row { display: flex; align-items: center; gap: 10px; }
.pt-logo-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; color: #fff; font-weight: 900;
}
.pt-logo-name { font-size: 1.15rem; font-weight: 800; color: #111827; letter-spacing: -0.3px; }
.pt-logo-sub  { font-size: 0.72rem; color: #9ca3af; margin-left: 4px; }
.pt-header-right { color: #9ca3af; font-size: 0.78rem; }

/* ── Tabs ── */
.tabs > .tab-nav {
    border-bottom: 2px solid #e5e7eb !important;
    background: transparent !important;
    margin-bottom: 0 !important;
}
.tabs > .tab-nav button {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
    color: #6b7280 !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    padding: 10px 18px !important;
    border-radius: 0 !important;
    transition: color 0.15s !important;
}
.tabs > .tab-nav button.selected {
    color: #6366f1 !important;
    border-bottom-color: #6366f1 !important;
}
.tabs > .tab-nav button:hover:not(.selected) { color: #374151 !important; }
.tabitem { padding-top: 20px !important; border: none !important; background: transparent !important; }

/* ── Chat box ── */
#chat-box {
    background: #f8f9fa;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 28px 24px;
    min-height: 500px;
    max-height: 640px;
    overflow-y: auto;
    margin-bottom: 16px;
}
#chat-box::-webkit-scrollbar { width: 4px; }
#chat-box::-webkit-scrollbar-track { background: transparent; }
#chat-box::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }

/* ── Chat input ── */
#chat-input textarea {
    background: #fff !important;
    border: 1.5px solid #e5e7eb !important;
    border-radius: 12px !important;
    color: #111827 !important;
    font-size: 1rem !important;
    padding: 14px 16px !important;
    line-height: 1.6 !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
#chat-input textarea:focus {
    border-color: #818cf8 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
    outline: none !important;
}
#chat-input textarea::placeholder { color: #9ca3af !important; }
#chat-input label { color: #6b7280 !important; font-size: 0.8rem !important; }

/* ── Filter dropdown ── */
#doc-filter { min-width: 100px !important; }
#doc-filter select {
    background: #f9fafb !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    color: #374151 !important;
    font-size: 0.82rem !important;
    padding: 6px 10px !important;
    height: 36px !important;
}
#doc-filter label { display: none !important; }
#doc-filter .wrap-inner { padding: 0 !important; }

/* ── Send button ── */
#send-btn {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    width: 100% !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    padding: 12px !important;
    box-shadow: 0 3px 10px rgba(99,102,241,0.4) !important;
    transition: all 0.15s !important;
    margin-top: 6px !important;
}
#send-btn:hover { transform: translateY(-1px) !important; box-shadow: 0 5px 16px rgba(99,102,241,0.5) !important; }

/* ── Upload zone ── */
#upload-zone {
    background: #fff !important;
    border: 2px dashed #d1d5db !important;
    border-radius: 14px !important;
    transition: all 0.2s !important;
    min-height: 160px !important;
}
#upload-zone:hover { border-color: #818cf8 !important; background: #fafaff !important; }
#upload-zone .wrap span { color: #6b7280 !important; }

/* ── Upload button ── */
#upload-btn {
    background: #059669 !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    padding: 11px 24px !important;
    box-shadow: 0 2px 10px rgba(5,150,105,0.3) !important;
    transition: all 0.15s !important;
    width: 100% !important;
}
#upload-btn:hover { background: #047857 !important; box-shadow: 0 4px 16px rgba(5,150,105,0.4) !important; }

/* ── Library controls ── */
#lib-filter select {
    background: #fff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    color: #374151 !important;
    font-size: 0.875rem !important;
    padding: 8px 12px !important;
}
#lib-filter label { display: none !important; }
#refresh-btn {
    background: #fff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
}
#refresh-btn:hover { background: #f9fafb !important; border-color: #818cf8 !important; color: #6366f1 !important; }

/* ── Hint text ── */
.hint { color: #9ca3af; font-size: 0.75rem; text-align: center; margin-top: 8px; }

/* ── Responsive ── */
@media (max-width: 600px) {
    .gradio-container { padding: 0 12px 40px !important; }
    #chat-box { min-height: 300px; max-height: 400px; padding: 16px 12px; }
    #pt-header-right { display: none; }
}
"""

# ── App ───────────────────────────────────────────────────────────────────────

with gr.Blocks(
    css=CSS,
    theme=gr.themes.Soft(
        primary_hue=gr.themes.colors.violet,
        neutral_hue=gr.themes.colors.gray,
        font=gr.themes.GoogleFont("Inter"),
    ),
    title="PaperTrail",
) as demo:

    history_state = gr.State([])

    # Header
    gr.HTML("""
    <div id="pt-header">
      <div class="pt-logo-row">
        <div class="pt-logo-icon">✦</div>
        <span class="pt-logo-name">PaperTrail</span>
        <span class="pt-logo-sub">local AI</span>
      </div>
      <div class="pt-header-right">Gemma 4 &nbsp;·&nbsp; 100% private &nbsp;·&nbsp; all documents</div>
    </div>""")

    with gr.Tabs():

        # ── Chat ──────────────────────────────────────────────────────────────
        with gr.Tab("Chat"):

            chat_display = gr.HTML(value=_render_chat([]), elem_id="chat-box")

            with gr.Row():
                chat_input = gr.Textbox(
                    placeholder="Ask anything about your documents… (Press Enter to send)",
                    show_label=False,
                    lines=2,
                    max_lines=5,
                    scale=6,
                    elem_id="chat-input",
                )
                with gr.Column(scale=1, min_width=120):
                    doc_filter = gr.Dropdown(
                        choices=["All", "Receipt", "Paper", "Invoice", "Other"],
                        value="All",
                        show_label=False,
                        elem_id="doc-filter",
                    )
                    send_btn = gr.Button("↑  Send", elem_id="send-btn", variant="primary")

            gr.HTML('<p class="hint">Searches across <b>all</b> your documents · Press Enter or click Send</p>')

            def _submit(q, f, h):
                new_h, cleared, chat_html = ask(q, f, h)
                return new_h, cleared, chat_html

            for trigger in [send_btn.click, chat_input.submit]:
                trigger(
                    fn=_submit,
                    inputs=[chat_input, doc_filter, history_state],
                    outputs=[history_state, chat_input, chat_display],
                    queue=False,
                )

        # ── Library ───────────────────────────────────────────────────────────
        with gr.Tab("Library"):

            with gr.Row():
                lib_filter = gr.Dropdown(
                    choices=["All", "Receipt", "Paper", "Invoice", "Other"],
                    value="All", show_label=False, scale=3,
                    container=False, elem_id="lib-filter",
                )
                refresh_btn = gr.Button("↻  Refresh", scale=1, elem_id="refresh-btn")

            gr.HTML('<div style="height:12px"></div>')
            library_html = gr.HTML()

            refresh_btn.click(load_library, lib_filter, library_html)
            lib_filter.change(load_library, lib_filter, library_html)
            demo.load(lambda: load_library("All"), outputs=library_html)

        # ── Upload ────────────────────────────────────────────────────────────
        with gr.Tab("Upload"):

            gr.HTML("""
            <div style="text-align:center;padding:4px 0 22px;">
              <div style="color:#111827;font-size:1rem;font-weight:700;margin-bottom:6px;">
                Add documents to your library
              </div>
              <div style="color:#6b7280;font-size:0.875rem;line-height:1.65;">
                Gemma 4 reads and indexes every file — then ask questions<br>
                across your entire library in the Chat tab.
              </div>
            </div>""")

            upload_input = gr.File(
                label="Drop files here or click to browse",
                file_types=[".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"],
                file_count="multiple",
                elem_id="upload-zone",
            )
            gr.HTML('<p class="hint">PDF · PNG · JPG · JPEG · WEBP · TIFF · BMP · Scanned documents welcome</p>')
            gr.HTML('<div style="height:14px"></div>')
            upload_btn  = gr.Button("Upload & Index", elem_id="upload-btn")
            gr.HTML('<div style="height:14px"></div>')
            upload_result = gr.HTML(value=_upload_placeholder())

            upload_btn.click(upload_files, upload_input, upload_result)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
