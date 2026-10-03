"""
modern.py
---------
"Modern" layout: big left-aligned title, color strip across the top of every page,
section headings with a vertical accent bar.
Good for pitches, one-pagers, guides, event info.
"""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from ..utils import hex_to_color, safe
from .base import MUTED, BaseTemplate


class ModernTemplate(BaseTemplate):
    name = "modern"
    label = "Modern"
    margin_top = 26 * mm

    def cover(self, spec, theme, st, width):
        title = ParagraphStyle(
            "m_title", fontName=st["bold_font"], fontSize=32, leading=37, textColor=hex_to_color(theme.primary), spaceAfter=10
        )
        sub = ParagraphStyle("m_sub", fontName=st["regular_font"], fontSize=14, leading=20, textColor=colors.HexColor("#4B5563"), spaceAfter=8)
        meta = ParagraphStyle("m_meta", fontName=st["regular_font"], fontSize=9, leading=12, textColor=MUTED, spaceAfter=4)

        out = [Spacer(1, 6), Paragraph(safe(spec.title), title)]
        out.append(HRFlowable(width=54, thickness=5, color=hex_to_color(theme.accent), spaceAfter=12, hAlign="LEFT"))
        if spec.subtitle.strip():
            out.append(Paragraph(safe(spec.subtitle), sub))
        out.append(Paragraph(safe(self.meta_line(spec)), meta))
        out.append(Spacer(1, 10))
        return out

    def section_heading(self, text, theme, st, width):
        style = ParagraphStyle("m_h", parent=st["h_section"], spaceBefore=0, spaceAfter=0, leftIndent=0)
        bar = Table([["", Paragraph(safe(text), style)]], colWidths=[5, width - 5])
        bar.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), hex_to_color(theme.accent)),
                    ("LEFTPADDING", (0, 0), (0, 0), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 0),
                    ("LEFTPADDING", (1, 0), (1, 0), 11),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return [Spacer(1, 16), bar, Spacer(1, 9)]

    def draw_chrome(self, c, page, total, spec, theme, w, h):
        c.saveState()
        c.setFillColor(hex_to_color(theme.primary))
        c.rect(0, h - 7 * mm, w, 7 * mm, stroke=0, fill=1)
        c.setFillColor(hex_to_color(theme.accent))
        c.rect(self.margin_x, h - 7 * mm, 26 * mm, 7 * mm, stroke=0, fill=1)
        c.restoreState()
        self.draw_footer(c, page, total, spec, w, h)
