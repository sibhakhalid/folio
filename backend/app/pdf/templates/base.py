"""
base.py
-------
BaseTemplate holds everything the layouts have in common.
A new layout only needs to override a few methods:

    styles()          -> fonts, sizes, text colors
    cover()           -> the title area at the top of page 1
    section_heading() -> how each section title looks
    draw_chrome()     -> page header / footer drawn on every page (page numbers live here)
"""

import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm

from ..fonts import get_fonts
from ..utils import hex_to_color, on_color

INK = colors.HexColor("#22262E")
MUTED = colors.HexColor("#6B7280")
LINE = colors.HexColor("#D9DDE3")


def today_text() -> str:
    return datetime.date.today().strftime("%d %B %Y").lstrip("0")


class BaseTemplate:
    name = "base"
    label = "Base"
    page_size = A4
    margin_x = 20 * mm
    margin_top = 24 * mm
    margin_bottom = 20 * mm

    # Subclasses choose a font family: "sans" or "serif".
    font_family = "sans"
    body_size = 10.5

    # ---- fonts & styles --------------------------------------------------------

    def fonts(self):
        f = get_fonts()
        if self.font_family == "serif":
            return f["serif"], f["serif_bold"], f["serif_italic"]
        return f["sans"], f["sans_bold"], f["sans_italic"]

    def styles(self, theme) -> dict:
        regular, bold, italic = self.fonts()
        size = self.body_size
        primary = hex_to_color(theme.primary)

        def style(name, **kw):
            base = dict(fontName=regular, fontSize=size, leading=size * 1.55, textColor=INK, alignment=TA_LEFT)
            base.update(kw)
            return ParagraphStyle(name, **base)

        return {
            "regular_font": regular,
            "bold_font": bold,
            "italic_font": italic,
            "body": style("body", spaceAfter=7),
            "list_item": style("list_item"),
            "caption": style("caption", fontName=bold, fontSize=size - 1, textColor=MUTED, spaceAfter=5),
            "cell": style("cell", fontSize=size - 1.5, leading=(size - 1.5) * 1.4),
            "cell_head": style(
                "cell_head", fontName=bold, fontSize=size - 1.5, leading=(size - 1.5) * 1.4, textColor=on_color(theme.primary)
            ),
            "callout_title": style("callout_title", fontName=bold, textColor=primary, spaceAfter=3),
            "callout_text": style("callout_text"),
            "card_title": style("card_title", fontName=bold, textColor=primary, spaceAfter=3),
            "card_text": style("card_text", fontSize=size - 1, leading=(size - 1) * 1.5),
            "h_section": style(
                "h_section", fontName=bold, fontSize=16, leading=20, textColor=primary, spaceBefore=16, spaceAfter=6
            ),
        }

    # ---- pieces subclasses override -------------------------------------------

    def cover(self, spec, theme, st, width) -> list:
        raise NotImplementedError

    def section_heading(self, text, theme, st, width) -> list:
        raise NotImplementedError

    def draw_chrome(self, c, page, total, spec, theme, w, h):
        self.draw_footer(c, page, total, spec, w, h)

    # ---- shared helpers --------------------------------------------------------

    def meta_line(self, spec) -> str:
        parts = []
        if spec.author.strip():
            parts.append(f"Prepared by {spec.author.strip()}")
        parts.append(spec.date.strip() or today_text())
        return "   |   ".join(parts)

    def draw_footer(self, c, page, total, spec, w, h, align_title="left"):
        regular, _, _ = self.fonts()
        c.saveState()
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        y = self.margin_bottom - 8 * mm
        c.line(self.margin_x, y + 5 * mm, w - self.margin_x, y + 5 * mm)
        c.setFont(regular, 8)
        c.setFillColor(MUTED)
        title = spec.title if len(spec.title) <= 70 else spec.title[:67] + "..."
        if align_title == "left":
            c.drawString(self.margin_x, y, title)
        else:
            c.drawCentredString(w / 2, y, title)
        c.drawRightString(w - self.margin_x, y, f"Page {page} of {total}")
        c.restoreState()

    def draw_running_header(self, c, page, spec, w, h, theme):
        """Small title line on pages after the first."""
        if page == 1:
            return
        regular, _, _ = self.fonts()
        c.saveState()
        c.setFont(regular, 8)
        c.setFillColor(MUTED)
        title = spec.title if len(spec.title) <= 80 else spec.title[:77] + "..."
        c.drawString(self.margin_x, h - 12 * mm, title)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.line(self.margin_x, h - 14 * mm, w - self.margin_x, h - 14 * mm)
        c.restoreState()
