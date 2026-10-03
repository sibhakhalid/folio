# Folio: AI PDF generator chatbot

Describe a document (or paste raw notes) in a chat. Gemini organises it into a structure,
ReportLab draws a designed PDF, and you can keep asking for changes: *"make it shorter"*,
*"change the colors to green"*, *"add a pricing table"*. Every change becomes a new version.

```
React + Vite (browser)  --/api-->  FastAPI (Python)  --->  Gemini API   (key lives here only)
                                        |
                                        +--->  ReportLab  --->  PDF file
```

## How a message flows

1. You type a message. React sends it to `POST /api/chat` together with the **current document JSON**.
2. `gemini_service.py` asks Gemini to return JSON: `{ "reply": "...", "document": { title, sections, blocks... } }`.
3. `schemas.py` validates that JSON (bad colors, unknown block types and numbers-instead-of-text are fixed automatically).
4. `pdf/builder.py` picks a template and lays the content out across as many pages as needed.
5. The PDF is saved in `backend/generated/`, and React shows it in an `<iframe>` with a download button.

Because the document is just JSON, "change the colors" means "send the JSON back to Gemini and ask for
an updated copy". Gemini never writes PDF code.

## Project layout

```
ai-pdf-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py             API routes (/api/chat, /api/pdf/{id}, /api/health)
│   │   ├── config.py           reads .env (the API key lives here)
│   │   ├── gemini_service.py   the prompt + the call to Gemini
│   │   ├── schemas.py          shape of the document JSON
│   │   ├── pdf_store.py        saves PDFs, deletes old ones
│   │   └── pdf/
│   │       ├── builder.py      story -> pages, "Page X of Y"
│   │       ├── blocks.py       paragraph, bullets, table, cards, highlight
│   │       ├── fonts.py        picks a Unicode-capable font if installed
│   │       └── templates/      report.py, modern.py, classic.py  <- one file per layout
│   ├── try_pdf_without_ai.py   test the PDF engine alone
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── App.jsx             state + sending messages
        ├── api.js              the only file that calls the backend
        ├── components/         ChatPanel.jsx, Stage.jsx
        └── styles.css
```

## Setup

You need **Python 3.10+**, **Node 18+**, and a free Gemini key from <https://aistudio.google.com/apikey>.

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # Windows: copy .env.example .env
# open .env and paste your key after GEMINI_API_KEY=
```

**Optional check, no key needed:** `python try_pdf_without_ai.py` creates three sample PDFs.

Start the server:

```bash
uvicorn app.main:app --reload --port 8000
```

Open <http://127.0.0.1:8000/api/health>. You should see `"gemini_key_set": true`.

### 2. Frontend (second terminal)

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

## Try it

- *"One-page proposal for a neighbourhood food-sharing app"*
- Paste messy meeting notes, then: *"Turn this into a summary with action items"*
- After the PDF appears: *"Make it more professional"*, *"Switch to green"*, *"Add a budget table"*, *"Remove the last section"*

## Security notes

- The Gemini key is only read in `backend/app/config.py` from `backend/.env`. The frontend has no key, and `.env` is in `.gitignore`.
- PDF ids are random 32-character hex strings and are validated before any file is opened.
- AI text is escaped before it goes into ReportLab, so stray `<` or `&` can't break the PDF.
- Generated PDFs are deleted after 24 hours (`PDF_MAX_AGE_HOURS`).
- For production: restrict `ALLOWED_ORIGINS`, add rate limiting and user accounts, and store PDFs in cloud storage.

## Customising

**Add a template:** copy `templates/classic.py`, change `name`, fonts, `cover()`, `section_heading()` and
`draw_chrome()`, register it in `templates/__init__.py`, add its name to `Literal[...]` in `schemas.py`,
and describe it in the TEMPLATES list inside `SYSTEM_PROMPT` in `gemini_service.py`.

**Add a block type** (for example a quote): add it to `Block.type` in `schemas.py`, write a function in
`pdf/blocks.py`, call it from `render_block()`, and describe it in `SYSTEM_PROMPT`.

**Fonts:** `fonts.py` uses Arial/Times (Windows, macOS) or DejaVu (Linux) so symbols like ₹ and é work.
To use your own, put `Sans-Regular.ttf`, `Sans-Bold.ttf`, `Sans-Italic.ttf`, `Sans-BoldItalic.ttf` (and the
`Serif-*` equivalents) in `backend/fonts/`.

**Limits:** the preview uses the browser's built-in PDF viewer. Some phone browsers only show the first page
in an iframe, so use the **Open** button there. Scripts without spaces (Chinese, Thai, Arabic) need a font
that supports them and extra shaping work.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Can't reach the server" | Backend isn't running on port 8000 |
| "no Gemini API key" | `.env` is missing or isn't in `backend/`. Restart uvicorn after editing it |
| "rate-limiting" | Free-tier limit. Wait a minute, or try `GEMINI_MODEL=gemini-2.5-flash-lite` |
| Black boxes in the PDF | Text uses characters the font lacks. See **Fonts** above |
| Blank preview in Brave/Firefox | Allow the built-in PDF viewer, or use **Open** |
