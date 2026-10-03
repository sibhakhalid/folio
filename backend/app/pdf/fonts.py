"""
fonts.py
--------
ReportLab's built-in fonts (Helvetica, Times) only support basic Latin letters.
If your text has symbols like ₹ € or accented names, they can show up as black boxes.

So we try to register a real TrueType font that is already installed on your computer
(Arial/Times on Windows and macOS, DejaVu on Linux). If none is found, we fall back
to the built-in fonts and everything still works for normal English text.

Want a custom font? Drop .ttf files into backend/fonts/ and add them to CANDIDATES.
"""

import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_FONTS = os.path.normpath(os.path.join(HERE, "..", "..", "fonts"))

# (regular, bold, italic, bold-italic) file paths to try, in order.
SANS_CANDIDATES = [
    tuple(os.path.join(LOCAL_FONTS, f) for f in ("Sans-Regular.ttf", "Sans-Bold.ttf", "Sans-Italic.ttf", "Sans-BoldItalic.ttf")),
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/ariali.ttf", "C:/Windows/Fonts/arialbi.ttf"),
    ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
     "/System/Library/Fonts/Supplemental/Arial Italic.ttf", "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"),
]
SERIF_CANDIDATES = [
    tuple(os.path.join(LOCAL_FONTS, f) for f in ("Serif-Regular.ttf", "Serif-Bold.ttf", "Serif-Italic.ttf", "Serif-BoldItalic.ttf")),
    ("C:/Windows/Fonts/times.ttf", "C:/Windows/Fonts/timesbd.ttf", "C:/Windows/Fonts/timesi.ttf", "C:/Windows/Fonts/timesbi.ttf"),
    ("/System/Library/Fonts/Supplemental/Times New Roman.ttf", "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
     "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf", "/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"),
]

_cache = {}


def _register(family: str, candidates, fallback: str):
    """Register the first complete font set found. Returns the family name to use."""
    for files in candidates:
        if all(os.path.exists(f) for f in files):
            names = [f"{family}", f"{family}-Bold", f"{family}-Italic", f"{family}-BoldItalic"]
            for name, path in zip(names, files):
                pdfmetrics.registerFont(TTFont(name, path))
            pdfmetrics.registerFontFamily(
                family, normal=names[0], bold=names[1], italic=names[2], boldItalic=names[3]
            )
            return family
    return fallback  # built-in font; <b> and <i> already work for these


def get_fonts() -> dict:
    """Returns {'sans': name, 'serif': name} (each is a *family* name)."""
    if not _cache:
        sans = _register("FolioSans", SANS_CANDIDATES, "Helvetica")
        serif = _register("FolioSerif", SERIF_CANDIDATES, "Times-Roman")
        _cache.update(
            sans=sans,
            sans_bold=f"{sans}-Bold",
            sans_italic=f"{sans}-Italic" if sans != "Helvetica" else "Helvetica-Oblique",
            serif=serif,
            serif_bold=f"{serif}-Bold",
            serif_italic=f"{serif}-Italic",
        )
    return _cache
