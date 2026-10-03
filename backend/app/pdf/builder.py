"""
builder.py
----------
build_pdf(spec, path) is the one function the rest of the app calls.

Steps:
  1. pick a template (layout) by name
  2. turn the cover + every section/block into a "story" (list of flowables)
  3. let ReportLab lay the story out across as many pages as needed
  4. a custom canvas adds the header/footer and "Page X of Y" to every page
"""

from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, CondPageBreak, Frame, PageTemplate

from .blocks import render_block
from .templates import get_template


class NumberedCanvas(canvas.Canvas):
    """
    ReportLab only knows the total page count at the very end. This canvas remembers
    every page, then draws the header/footer once the total is known ("Page 2 of 5").
    """

    def __init__(self, *args, chrome=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_pages = []
        self._chrome = chrome

    def showPage(self):
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_pages)
        for state in self._saved_pages:
            self.__dict__.update(state)
            if self._chrome:
                self._chrome(self, self._pageNumber, total)
            super().showPage()
        super().save()


def build_pdf(spec, path: str) -> int:
    """Create the PDF file at `path`. Returns the number of pages."""
    tpl = get_template(spec.template)
    theme = spec.theme
    st = tpl.styles(theme)

    page_w, page_h = tpl.page_size
    doc = BaseDocTemplate(
        path,
        pagesize=tpl.page_size,
        leftMargin=tpl.margin_x,
        rightMargin=tpl.margin_x,
        topMargin=tpl.margin_top,
        bottomMargin=tpl.margin_bottom,
        title=spec.title,
        author=spec.author or "Folio",
        creator="Folio AI PDF Studio",
    )
    width = doc.width
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])

    story = tpl.cover(spec, theme, st, width)
    for section in spec.sections:
        if section.heading.strip():
            # If less than ~4cm is left on the page, start the section on a fresh page
            # so a heading is never stranded at the bottom.
            story.append(CondPageBreak(115))
            story += tpl.section_heading(section.heading, theme, st, width)
        for block in section.blocks:
            story += render_block(block, theme, st, width)

    def chrome(c, page, total):
        tpl.draw_chrome(c, page, total, spec, theme, page_w, page_h)

    doc.build(story, canvasmaker=lambda *a, **k: NumberedCanvas(*a, chrome=chrome, **k))
    return doc.page  # last page number = page count
