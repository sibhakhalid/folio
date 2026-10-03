"""
blocks.py
---------
Turns each content "block" (paragraph, bullets, table, ...) into ReportLab flowables.
Templates share these, so a table looks consistent in every layout while the
cover page, headings and page header/footer can differ per template.

ReportLab vocabulary, in plain words:
  Flowable   = anything that can be placed on a page (paragraph, table, spacer...)
  Paragraph  = text that wraps and can be styled
  Table      = grid of cells; can split across pages and repeat its header row
"""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    CondPageBreak,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .utils import hex_to_color, looks_numeric, on_color, safe, tint

GREY_LINE = colors.HexColor("#D9DDE3")


def render_block(block, theme, st: dict, width: float) -> list:
    """Dispatch on block.type. `st` is the dict of paragraph styles from the template."""
    kind = block.type
    if kind == "paragraph":
        return paragraph(block, st)
    if kind == "bullets":
        return bullet_list(block, theme, st, numbered=False)
    if kind == "numbered":
        return bullet_list(block, theme, st, numbered=True)
    if kind == "highlight":
        return highlight(block, theme, st, width)
    if kind == "table":
        return table(block, theme, st, width)
    if kind == "cards":
        return cards(block, theme, st, width)
    return []


# --- paragraph -----------------------------------------------------------------------


def paragraph(block, st):
    if not block.text.strip():
        return []
    # Blank lines in the text start a new paragraph.
    parts = [p.strip() for p in block.text.split("\n\n") if p.strip()]
    return [Paragraph(safe(p), st["body"]) for p in parts]


# --- bullets / numbered --------------------------------------------------------------


def bullet_list(block, theme, st, numbered: bool):
    items = [i for i in block.items if i.strip()]
    if not items:
        return []
    flow_items = [ListItem(Paragraph(safe(i), st["list_item"]), spaceAfter=3) for i in items]
    if numbered:
        lst = ListFlowable(
            flow_items,
            bulletType="1",
            bulletFormat="%s.",
            bulletFontName=st["bold_font"],
            bulletFontSize=st["body"].fontSize,
            bulletColor=hex_to_color(theme.primary),
            leftIndent=20,
        )
    else:
        lst = ListFlowable(
            flow_items,
            bulletType="bullet",
            start="\u2022",
            bulletFontSize=st["body"].fontSize + 2,
            bulletColor=hex_to_color(theme.accent),
            leftIndent=16,
        )
    return [lst, Spacer(1, 6)]


# --- highlight (callout box) ---------------------------------------------------------


def highlight(block, theme, st, width):
    content = []
    if block.title.strip():
        content.append(Paragraph(safe(block.title), st["callout_title"]))
    if block.text.strip():
        content.append(Paragraph(safe(block.text), st["callout_text"]))
    if not content:
        return []
    box = Table([[content]], colWidths=[width])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), tint(theme.accent, 0.88)),
                ("LINEBEFORE", (0, 0), (0, -1), 3.5, hex_to_color(theme.accent)),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
            ]
        )
    )
    return [KeepTogether([box]), Spacer(1, 10)]


# --- table ---------------------------------------------------------------------------


def table(block, theme, st, width):
    columns = list(block.columns)
    rows = [list(r) for r in block.rows]
    if not columns and rows:
        columns = rows.pop(0)  # no header given: treat the first row as the header
    if not columns:
        return []

    n = len(columns)
    rows = [(r + [""] * n)[:n] for r in rows]  # make every row exactly n cells long

    # Which columns hold numbers? Right-align those so figures line up.
    numeric = [bool(rows) and all(looks_numeric(r[i]) or not r[i].strip() for r in rows) for i in range(n)]
    right = ParagraphStyle("cell_right", parent=st["cell"], alignment=TA_RIGHT)
    right_head = ParagraphStyle("head_right", parent=st["cell_head"], alignment=TA_RIGHT)

    header = [Paragraph(safe(c), right_head if numeric[i] else st["cell_head"]) for i, c in enumerate(columns)]
    body = [
        [Paragraph(safe(cell), right if numeric[i] else st["cell"]) for i, cell in enumerate(r)]
        for r in rows
    ]

    # Column widths: every column gets at least enough room for its longest single word
    # (so numbers like $100,000 never break in half). Leftover space is shared out
    # in proportion to how much text each column holds.
    font, size, pad = st["regular_font"], st["cell"].fontSize, 18
    mins, wants = [], []
    for i in range(n):
        cells = [columns[i]] + [r[i] for r in rows]
        longest_word = max((stringWidth(w, st["bold_font"], size) for c in cells for w in c.split()), default=20)
        mins.append(longest_word + pad)
        wants.append(min(max(len(c) for c in cells), 60) + 4)
    spare = max(width - sum(mins), 0)
    col_widths = [m + spare * w / sum(wants) for m, w in zip(mins, wants)]
    if sum(col_widths) > width:  # extremely wide table: shrink evenly
        col_widths = [w * width / sum(col_widths) for w in col_widths]

    t = Table([header] + body, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), hex_to_color(theme.primary)),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, tint(theme.primary, 0.94)]),
                ("LINEBELOW", (0, 1), (-1, -1), 0.4, GREY_LINE),
                ("BOX", (0, 0), (-1, -1), 0.5, GREY_LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    out = []
    if block.title.strip():
        out += [CondPageBreak(90), Paragraph(safe(block.title), st["caption"])]
    out += [t, Spacer(1, 12)]
    return out


# --- cards (2-column grid) -----------------------------------------------------------


def cards(block, theme, st, width):
    items = [c for c in block.cards if c.title.strip() or c.text.strip()]
    if not items:
        return []
    gap = 12
    card_w = (width - gap) / 2

    data, row_heights, styles = [], [], []
    light = tint(theme.primary, 0.94)
    accent = hex_to_color(theme.accent)

    for start in range(0, len(items), 2):
        r = len(data)
        pair = items[start : start + 2]
        row = []
        for c_index, card in enumerate(pair):
            cell = []
            if card.title.strip():
                cell.append(Paragraph(safe(card.title), st["card_title"]))
            if card.text.strip():
                cell.append(Paragraph(safe(card.text), st["card_text"]))
            row.append(cell)
            col = 0 if c_index == 0 else 2
            styles += [
                ("BACKGROUND", (col, r), (col, r), light),
                ("LINEABOVE", (col, r), (col, r), 2.5, accent),
            ]
        while len(row) < 2:
            row.append("")
        data.append([row[0], "", row[1]])
        row_heights.append(None)  # None = "fit the content"
        data.append(["", "", ""])  # spacer row between card rows
        row_heights.append(gap)

    data, row_heights = data[:-1], row_heights[:-1]  # drop the last spacer row
    t = Table(data, colWidths=[card_w, gap, card_w], rowHeights=row_heights)
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                # gutter column has no padding so it stays exactly `gap` wide
                ("LEFTPADDING", (1, 0), (1, -1), 0),
                ("RIGHTPADDING", (1, 0), (1, -1), 0),
            ]
            + styles
        )
    )
    return [t, Spacer(1, 12)]
