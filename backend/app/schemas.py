"""
schemas.py
----------
These classes describe the "shape" of the data that moves around the app.

The most important one is DocumentSpec: a plain JSON description of a PDF
(title, sections, bullets, tables...). Gemini produces it, the frontend stores it,
and the PDF builder turns it into a real PDF.

Keeping the document as JSON is what makes "change the colors" or "shorten it"
easy: we just send the JSON back to Gemini and ask for an updated version.
"""

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _to_text(value) -> str:
    """Gemini sometimes returns numbers instead of strings. Make everything text."""
    if value is None:
        return ""
    return str(value)


class Theme(BaseModel):
    primary: str = "#1F3A5F"  # main brand color (headings, table headers, cover)
    accent: str = "#E07A2F"   # small highlights (rules, bullets, callout bars)

    @field_validator("primary", "accent", mode="before")
    @classmethod
    def valid_hex(cls, v, info):
        # If the AI invents a bad color, quietly fall back to a safe default.
        default = "#1F3A5F" if info.field_name == "primary" else "#E07A2F"
        if isinstance(v, str) and HEX_RE.match(v.strip()):
            return v.strip()
        return default


class Card(BaseModel):
    title: str = ""
    text: str = ""

    @field_validator("title", "text", mode="before")
    @classmethod
    def clean_text(cls, v):
        return _to_text(v)


class Block(BaseModel):
    """One piece of content inside a section. `type` decides which fields are used."""

    type: Literal["paragraph", "bullets", "numbered", "highlight", "table", "cards"] = "paragraph"
    text: str = ""                      # paragraph, highlight
    title: str = ""                     # highlight (optional title), table caption
    items: list[str] = Field(default_factory=list)          # bullets, numbered
    columns: list[str] = Field(default_factory=list)        # table header
    rows: list[list[str]] = Field(default_factory=list)     # table body
    cards: list[Card] = Field(default_factory=list)         # cards

    @field_validator("type", mode="before")
    @classmethod
    def known_type(cls, v):
        # If the AI invents a block type, show its text as a plain paragraph instead of failing.
        allowed = {"paragraph", "bullets", "numbered", "highlight", "table", "cards"}
        return v if v in allowed else "paragraph"

    @field_validator("text", "title", mode="before")
    @classmethod
    def clean_text(cls, v):
        return _to_text(v)

    @field_validator("items", "columns", mode="before")
    @classmethod
    def clean_list(cls, v):
        return [_to_text(x) for x in (v or [])]

    @field_validator("rows", mode="before")
    @classmethod
    def clean_rows(cls, v):
        return [[_to_text(c) for c in (row or [])] for row in (v or [])]


class Section(BaseModel):
    heading: str = ""
    blocks: list[Block] = Field(default_factory=list)

    @field_validator("heading", mode="before")
    @classmethod
    def clean_heading(cls, v):
        return _to_text(v)


class DocumentSpec(BaseModel):
    title: str = "Untitled document"
    subtitle: str = ""
    author: str = ""
    date: str = ""
    # Which layout to use. See app/pdf/templates/ to add more.
    template: Literal["report", "modern", "classic"] = "report"
    theme: Theme = Field(default_factory=Theme)
    sections: list[Section] = Field(default_factory=list)

    @field_validator("title", "subtitle", "author", "date", mode="before")
    @classmethod
    def clean_text(cls, v):
        return _to_text(v)

    @field_validator("template", mode="before")
    @classmethod
    def known_template(cls, v):
        return v if v in ("report", "modern", "classic") else "report"


# ---- API request / response shapes -------------------------------------------------


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    text: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=30000)
    history: list[HistoryItem] = Field(default_factory=list, max_length=40)
    # The document currently shown in the preview (None for a brand-new chat).
    document: Optional[DocumentSpec] = None


class ChatResponse(BaseModel):
    reply: str
    document: Optional[DocumentSpec] = None
    pdf_id: Optional[str] = None
    pdf_url: Optional[str] = None
