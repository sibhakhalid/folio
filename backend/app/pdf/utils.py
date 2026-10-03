"""
utils.py
--------
Small helpers: color math and making text safe for ReportLab paragraphs.
"""

import re
from xml.sax.saxutils import escape

from reportlab.lib import colors


def hex_to_color(hex_str: str) -> colors.Color:
    return colors.HexColor(hex_str)


def luminance(hex_str: str) -> float:
    """0 = black, 1 = white. Used to pick readable text on top of a color."""
    c = colors.HexColor(hex_str)
    return 0.2126 * c.red + 0.7152 * c.green + 0.0722 * c.blue


def tint(hex_str: str, amount: float) -> colors.Color:
    """Mix a color with white. amount=0.9 -> very light version of the color."""
    c = colors.HexColor(hex_str)
    return colors.Color(
        c.red + (1 - c.red) * amount,
        c.green + (1 - c.green) * amount,
        c.blue + (1 - c.blue) * amount,
    )


def on_color(hex_str: str) -> colors.Color:
    """White text on dark colors, near-black text on light colors."""
    return colors.white if luminance(hex_str) < 0.6 else colors.HexColor("#14171C")


_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)")


def safe(text: str) -> str:
    """
    Make AI text safe for ReportLab's Paragraph (which reads a mini-HTML).
    - Escapes &, <, > so odd characters can't break the PDF.
    - Turns **bold** and *italic* into <b> and <i>.
    - Keeps line breaks.
    """
    text = escape(text or "")
    text = _BOLD.sub(r"<b>\1</b>", text)
    text = _ITALIC.sub(r"<i>\1</i>", text)
    return text.replace("\n", "<br/>")


_NUMERIC = re.compile(r"^[\s$€£₹¥+\-–(]*[\d.,]+\s*(%|[kKmMbB])?[)\s]*$")


def looks_numeric(cell: str) -> bool:
    return bool(_NUMERIC.match(cell or ""))
