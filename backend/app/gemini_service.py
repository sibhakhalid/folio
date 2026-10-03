"""
gemini_service.py
-----------------
Talks to Gemini. Its only job: turn (user message + chat history + current document)
into  {"reply": "...", "document": {...} or null}.

We ask Gemini to answer in JSON, then check the JSON with our pydantic schema.
Gemini never draws the PDF. It only decides the content and structure.
"""

import json
import re

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ValidationError

from . import config
from .schemas import DocumentSpec, HistoryItem


class GeminiError(Exception):
    """A problem we can explain to the user. `status` becomes the HTTP status code."""

    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.message = message
        self.status = status


class AIResult(BaseModel):
    reply: str = ""
    document: DocumentSpec | None = None


SYSTEM_PROMPT = """
You are the brain of a PDF-making chatbot. The user describes a document or pastes raw
notes. You organise it into a clean, well-structured document. Another program turns
your JSON into the PDF, so you NEVER write PDF code. You only return JSON.

OUTPUT: return ONE JSON object and nothing else:
{
  "reply": "1-2 friendly sentences telling the user what you made or changed",
  "document": { ...document... }   // or null if you must ask a question first
}

DOCUMENT SHAPE:
{
  "title": "string",
  "subtitle": "string (optional, may be empty)",
  "author": "string (only if the user gave one, else empty)",
  "date": "string (only if the user gave one, else empty)",
  "template": "report" | "modern" | "classic",
  "theme": { "primary": "#RRGGBB dark main color", "accent": "#RRGGBB contrasting highlight color" },
  "sections": [
    { "heading": "string",
      "blocks": [ ...blocks... ] }
  ]
}

BLOCK TYPES (use the fields shown, leave others out):
- {"type":"paragraph","text":"..."}                       (use **bold** for key phrases; blank line = new paragraph)
- {"type":"bullets","items":["...","..."]}
- {"type":"numbered","items":["...","..."]}               (steps or ranked lists)
- {"type":"highlight","title":"optional","text":"..."}    (one key takeaway or warning per section at most)
- {"type":"table","title":"optional caption","columns":["A","B"],"rows":[["1","2"]]}
- {"type":"cards","cards":[{"title":"...","text":"..."}]} (2-6 short cards: features, pillars, key metrics)

TEMPLATES:
- "report"  : solid color title block. Reports, summaries, proposals, meeting notes. (default)
- "modern"  : big title, color strip. Pitches, one-pagers, guides, event or product info.
- "classic" : serif, formal. Letters, policies, essays, legal or academic documents.

RULES:
1. Use ONLY the facts the user gave. Never invent numbers, names, dates or quotes.
   If you add structure (headings, a summary), keep it faithful to their content.
   If the user only gives a topic and no details, write sensible general content and say so in "reply".
2. Make it skimmable: short paragraphs, bullets for lists, a table when comparing items
   or listing figures, cards for 2-6 parallel ideas, a highlight for the one thing to remember.
   Do not use every block type. Choose what fits the content.
3. Choose colors that match the subject (finance: deep blue/green, creative: bold, legal: dark neutral).
   Primary must be dark enough for white text. Both must be 6-digit hex like "#1F3A5F".
4. Plain text only inside strings. No HTML or markdown headings. Only **bold** and *italic* are allowed.
5. EDITING: if CURRENT DOCUMENT is provided, the user wants a change to it. Return the COMPLETE updated
   document (not a diff). Keep everything that the user did not ask to change.
   - "change colors"            -> change theme only
   - "more professional"        -> tighten wording, use "classic" or "report", calmer colors
   - "shorter"                  -> cut words and less important sections, keep the key facts
   - "add/remove a section"     -> do exactly that
   - "change layout"            -> change template (and maybe block types, e.g. bullets -> cards)
6. If the request is too vague to build anything (e.g. just "hi"), return "document": null and use
   "reply" to ask ONE short question.
7. Write the document in the same language as the user's content.
""".strip()


def _client() -> genai.Client:
    if not config.GEMINI_API_KEY:
        raise GeminiError("The server has no Gemini API key. Add GEMINI_API_KEY to backend/.env and restart.", 500)
    return genai.Client(api_key=config.GEMINI_API_KEY)


def _build_prompt(message: str, history: list[HistoryItem], document: DocumentSpec | None) -> str:
    parts = []
    if document is not None:
        parts.append("CURRENT DOCUMENT (JSON):\n" + document.model_dump_json())
    if history:
        lines = [f"{h.role.upper()}: {h.text[:1500]}" for h in history[-8:]]
        parts.append("RECENT CHAT:\n" + "\n".join(lines))
    parts.append("NEW USER MESSAGE:\n" + message)
    return "\n\n".join(parts)


def _parse(raw: str) -> AIResult:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)  # remove ```json fences if present
    data = json.loads(text)
    if isinstance(data, list) and data:  # model returned [ {...} ]
        data = data[0]
    return AIResult.model_validate(data)


def generate(message: str, history: list[HistoryItem], document: DocumentSpec | None) -> AIResult:
    client = _client()
    prompt = _build_prompt(message, history, document)
    cfg = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        temperature=0.5,
    )

    fallback_models = []
    if config.GEMINI_MODEL:
        fallback_models.append(config.GEMINI_MODEL)
    for model in ("gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"):
        if model not in fallback_models:
            fallback_models.append(model)

    last_problem = ""
    for model_attempt_index, model_name in enumerate(fallback_models):
        for attempt in range(2):
            contents = prompt if attempt == 0 else prompt + "\n\nYour last answer was not valid JSON. Return ONLY the JSON object."
            try:
                response = client.models.generate_content(model=model_name, contents=contents, config=cfg)
            except genai_errors.ClientError as e:
                code = getattr(e, "code", None)
                msg = str(e)
                if code == 404 or "no longer available" in msg.lower() or "NOT_FOUND" in msg:
                    if model_attempt_index < len(fallback_models) - 1:
                        continue
                    raise GeminiError(
                        "The configured Gemini model is no longer available. Update GEMINI_MODEL in backend/.env to gemini-3.5-flash-lite and restart the backend.",
                        502,
                    )
                if code == 429:
                    if model_attempt_index < len(fallback_models) - 1:
                        break
                    raise GeminiError(
                        "Gemini quota is exhausted for this key. Try again later or switch GEMINI_MODEL to gemini-3.5-flash-lite / a paid plan.",
                        429,
                    )
                if code in (401, 403):
                    raise GeminiError("Gemini rejected the API key. Check GEMINI_API_KEY in backend/.env.", 502)
                if code == 400:
                    raise GeminiError("Gemini could not process that request. Try rephrasing or shortening it.", 502)
                raise GeminiError("Gemini is unavailable right now. Try again in a moment.", 502)
            except genai_errors.APIError as e:
                code = getattr(e, "code", None)
                if code == 429:
                    if model_attempt_index < len(fallback_models) - 1:
                        break
                    raise GeminiError(
                        "Gemini quota is exhausted for this key. Try again later or switch GEMINI_MODEL to gemini-3.5-flash-lite / a paid plan.",
                        429,
                    )
                if code in (401, 403):
                    raise GeminiError("Gemini rejected the API key. Check GEMINI_API_KEY in backend/.env.", 502)
                if code == 400:
                    raise GeminiError("Gemini could not process that request. Try rephrasing or shortening it.", 502)
                raise GeminiError("Gemini is unavailable right now. Try again in a moment.", 502)
            except Exception:
                raise GeminiError("Could not reach Gemini. Check your internet connection.", 502)

            raw = response.text or ""
            if not raw.strip():
                last_problem = "Gemini returned an empty answer (it may have blocked the request)."
                continue
            try:
                return _parse(raw)
            except (json.JSONDecodeError, ValidationError) as e:
                last_problem = f"Gemini returned an answer in the wrong format. ({type(e).__name__})"

    raise GeminiError(last_problem + " Please try again.", 502)
