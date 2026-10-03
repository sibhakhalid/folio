"""
classic.py
----------
"Classic" layout: serif type, centered title between thin rules, understated headings.
Good for letters, formal documents, essays, policies.
"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import HRFlowable, Paragraph, Spacer

from ..utils import hex_to_color, safe
from .base import LINE, MUTED, BaseTemplate


class ClassicTemplate(BaseTemplate):
    name = "classic"
    label = "Classic"
    font_family = "serif"
    body_size = 11

    def styles(self, theme):
        st = super().styles(theme)
        st["h_section"] = ParagraphStyle(
            "c_h", parent=st["h_section"], fontSize=14.5, leading=18, spaceBefore=18, spaceAfter=2
        )
        return st

    def cover(self, spec, theme, st, width):
        primary = hex_to_color(theme.primary)
        title = ParagraphStyle("c_title", fontName=st["bold_font"], fontSize=26, leading=31, textColor=primary, alignment=TA_CENTER, spaceAfter=6)
        sub = ParagraphStyle("c_sub", fontName=st["italic_font"], fontSize=13, leading=18, textColor=colors.HexColor("#4B5563"), alignment=TA_CENTER, spaceAfter=6)
        meta = ParagraphStyle("c_meta", fontName=st["regular_font"], fontSize=9.5, leading=13, textColor=MUTED, alignment=TA_CENTER, spaceAfter=4)

        out = [
            HRFlowable(width="100%", thickness=1.6, color=primary, spaceAfter=3),
            HRFlowable(width="100%", thickness=0.5, color=primary, spaceAfter=16),
            Paragraph(safe(spec.title), title),
        ]
        if spec.subtitle.strip():
            out.append(Paragraph(safe(spec.subtitle), sub))
        out.append(Paragraph(safe(self.meta_line(spec)), meta))
        out += [
            HRFlowable(width="100%", thickness=0.5, color=primary, spaceBefore=10, spaceAfter=3),
            HRFlowable(width="100%", thickness=1.6, color=primary, spaceAfter=10),
        ]
        return out

    def section_heading(self, text, theme, st, width):
        head = Paragraph(safe(text), st["h_section"])
        rule = HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=2, spaceAfter=9)
        return [head, rule]

    def draw_chrome(self, c, page, total, spec, theme, w, h):
        self.draw_running_header(c, page, spec, w, h, theme)
        self.draw_footer(c, page, total, spec, w, h, align_title="center")
