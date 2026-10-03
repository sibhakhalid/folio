"""
pdf_store.py
------------
Saves generated PDFs on disk with a random id, and deletes old ones.
(A real product would use cloud storage; a folder is plenty for learning.)
"""

import re
import time
import uuid
from pathlib import Path

from . import config
from .pdf.builder import build_pdf

ID_RE = re.compile(r"^[a-f0-9]{32}$")


def create_pdf(spec) -> str:
    config.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    pdf_id = uuid.uuid4().hex
    build_pdf(spec, str(config.GENERATED_DIR / f"{pdf_id}.pdf"))
    return pdf_id


def path_for(pdf_id: str) -> Path | None:
    """Return the file path if the id is valid and the file exists, else None."""
    if not ID_RE.match(pdf_id):  # blocks things like ../../secret
        return None
    p = config.GENERATED_DIR / f"{pdf_id}.pdf"
    return p if p.exists() else None


def cleanup_old_files():
    if not config.GENERATED_DIR.exists():
        return
    cutoff = time.time() - config.PDF_MAX_AGE_HOURS * 3600
    for f in config.GENERATED_DIR.glob("*.pdf"):
        if f.stat().st_mtime < cutoff:
            f.unlink(missing_ok=True)
