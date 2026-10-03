"""
main.py
-------
The FastAPI app. Three routes:

  GET  /api/health        -> is the server alive, and is the key configured?
  POST /api/chat          -> message in, {reply, document, pdf_url} out
  GET  /api/pdf/{id}      -> the PDF file (inline for preview, ?download=1 to save)
"""

import logging
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from . import config, gemini_service, pdf_store
from .pdf.templates import TEMPLATES
from .schemas import ChatRequest, ChatResponse

log = logging.getLogger("folio")
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    pdf_store.cleanup_old_files()  # runs once when the server starts
    yield


app = FastAPI(title="Folio - AI PDF Chatbot", lifespan=lifespan)

# CORS lets the React dev server (another port) call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True, "gemini_key_set": bool(config.GEMINI_API_KEY), "templates": list(TEMPLATES)}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # 1) Ask Gemini to write / update the document JSON.
    try:
        result = gemini_service.generate(req.message, req.history, req.document)
    except gemini_service.GeminiError as e:
        raise HTTPException(status_code=e.status, detail=e.message)

    reply = result.reply or "Done."

    # Gemini asked a question instead of making a document.
    if result.document is None:
        return ChatResponse(reply=reply)

    # 2) Turn the JSON into a real PDF.
    try:
        pdf_id = pdf_store.create_pdf(result.document)
    except Exception:
        log.exception("PDF generation failed")
        raise HTTPException(status_code=500, detail="The document was written, but building the PDF failed. Try again, or ask for a simpler layout.")

    return ChatResponse(reply=reply, document=result.document, pdf_id=pdf_id, pdf_url=f"/api/pdf/{pdf_id}")


@app.get("/api/pdf/{pdf_id}")
def get_pdf(pdf_id: str, download: bool = False, name: str = "document"):
    path = pdf_store.path_for(pdf_id)
    if path is None:
        raise HTTPException(status_code=404, detail="That PDF no longer exists. Ask for it again.")
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")[:60] or "document"
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"{safe_name}.pdf",
        content_disposition_type="attachment" if download else "inline",
    )
