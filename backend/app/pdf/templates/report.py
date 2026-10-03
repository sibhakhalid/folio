"""
report.py
---------
"Report" layout: a solid colored title block on page 1, accent rule under section headings.
Good for reports, summaries, proposals, meeting notes.
"""

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from ..utils import hex_to_color, on_color, safe, tint
from .base import BaseTemplate


class ReportTemplate(BaseTemplate):
    name = "report"
    label = "Report"

    def cover(self, spec, theme, st, width):
        fg = on_color(theme.primary)
        soft = tint(theme.primary, 0.78) if fg == colors.white else colors.HexColor("#3A3F47")
        title = ParagraphStyle("cover_title", fontName=st["bold_font"], fontSize=27, leading=32, textColor=fg, spaceAfter=6)
        sub = ParagraphStyle("cover_sub", fontName=st["regular_font"], fontSize=13, leading=18, textColor=soft, spaceAfter=14)
        meta = ParagraphStyle("cover_meta", fontName=st["regular_font"], fontSize=9, leading=12, textColor=soft)

        cell = [Paragraph(safe(spec.title), title)]
        if spec.subtitle.strip():
            cell.append(Paragraph(safe(spec.subtitle), sub))
        cell.append(Paragraph(safe(self.meta_line(spec)), meta))

        box = Table([[cell]], colWidths=[width])
        box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), hex_to_color(theme.primary)),
                    ("LINEBEFORE", (0, 0), (0, -1), 7, hex_to_color(theme.accent)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 26),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 24),
                    ("TOPPADDING", (0, 0), (-1, -1), 30),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 26),
                ]
            )
        )
        return [box, Spacer(1, 8)]

    def section_heading(self, text, theme, st, width):
        head = Paragraph(safe(text), st["h_section"])
        rule = HRFlowable(width=36, thickness=2.5, color=hex_to_color(theme.accent), spaceAfter=9, hAlign="LEFT")
        return [head, rule]

    def draw_chrome(self, c, page, total, spec, theme, w, h):
        self.draw_running_header(c, page, spec, w, h, theme)
        self.draw_footer(c, page, total, spec, w, h)
