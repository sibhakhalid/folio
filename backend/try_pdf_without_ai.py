"""
Step 1 of the tutorial: test the PDF engine on its own, with NO Gemini and NO API key.

    cd backend
    python try_pdf_without_ai.py

It writes sample_report.pdf, sample_modern.pdf and sample_classic.pdf in this folder.
Open them to see the three templates. Then edit SAMPLE below and run it again.
"""

from app.pdf.builder import build_pdf
from app.schemas import DocumentSpec

SAMPLE = {
    "title": "Neighbourhood Food Share",
    "subtitle": "A pilot proposal for reducing food waste on Maple Street",
    "author": "Community Team",
    "theme": {"primary": "#1B4D3E", "accent": "#F2A33A"},
    "sections": [
        {
            "heading": "The idea",
            "blocks": [
                {"type": "paragraph", "text": "Households throw away **good food** every week. A simple app lets neighbours post surplus food and collect it nearby."},
                {"type": "highlight", "title": "Goal", "text": "Keep 500 kg of food out of the bin in the first six months."},
            ],
        },
        {
            "heading": "How it works",
            "blocks": [
                {"type": "cards", "cards": [
                    {"title": "Post", "text": "Take a photo and add a pickup window."},
                    {"title": "Claim", "text": "A neighbour reserves it with one tap."},
                    {"title": "Collect", "text": "Meet at the door or a shared shelf."},
                ]},
                {"type": "bullets", "items": ["No money changes hands", "Allergen notes are required", "Posts expire after 24 hours"]},
            ],
        },
        {
            "heading": "Budget",
            "blocks": [
                {"type": "table", "title": "Six-month estimate", "columns": ["Item", "Cost", "Notes"],
                 "rows": [["App development", "4,000", "Part-time contractor"], ["Shared shelves", "600", "Three locations"], ["Printing", "150", "Posters and flyers"]]},
            ],
        },
    ],
}

for template in ("report", "modern", "classic"):
    spec = DocumentSpec.model_validate({**SAMPLE, "template": template})
    pages = build_pdf(spec, f"sample_{template}.pdf")
    print(f"sample_{template}.pdf  ({pages} page{'s' if pages != 1 else ''})")
