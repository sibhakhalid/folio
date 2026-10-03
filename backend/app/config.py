"""
config.py
---------
Reads settings from backend/.env. The Gemini key lives ONLY here, on the server.
The React app never sees it: it only talks to our own /api routes.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

# Generated PDFs are stored here and cleaned up after PDF_MAX_AGE_HOURS.
GENERATED_DIR = Path(os.getenv("GENERATED_DIR", BASE_DIR / "generated"))
PDF_MAX_AGE_HOURS = int(os.getenv("PDF_MAX_AGE_HOURS", "24"))
