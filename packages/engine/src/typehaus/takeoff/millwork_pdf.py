"""The mill's shop schedule: one compact landscape page, then numbered notes.

Reads the same flattened rows as the CSV/Markdown exports (``cli/cmd_millwork._flat_rows``).
Page 1 is the whole cut list grouped by species; anything that does not fit a table cell —
stock and cut notes, plywood purchasing, species totals — is a numbered note on
the pages after it. Byte-deterministic, like ``calc_pdf``.
"""
from __future__ import annotations

import io
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

INK, ACCENT, MUTED, STRIPE = "#233746", "#477B73", "#64727B", "#F2F5F4"
PAGE_W, PAGE_H, MARGIN = 11 * 72, 8.5 * 72, 0.28 * 72
BODY_W = PAGE_W - 2 * MARGIN
CELL_PT, SMALL_PT = 7.0, 5.8
#: species, use / location, qty / cover, finished / sheet dims, stock, rough BF.
COLUMN_WIDTHS_IN = (0.95, None, 0.95, 2.6, 1.55, 0.8)
HEADERS = ("SPECIES", "USE / LOCATION", "QTY / COVER", "FINISHED / SHEET DIMENSIONS",
           "STOCK", "ROUGH BF")
NUMBER = re.compile(r"([0-9]+(?:\.[0-9]+)?)")
TIMES = " × "


@dataclass
class _Note:
    text: str
    tags: list[str] = field(default_factory=list)


def number(value: object) -> str:
    """``1.250`` -> ``1.25``, ``8.0`` -> ``8``; blank for an empty cell."""
    if value in (None, ""):
        return ""
    return f"{float(str(value)):.3f}".rstrip("0").rstrip(".")


def dimensions(row: dict) -> tuple[str, bool]:
    """``(T x W x L, False)`` for a cut piece, ``(W x L, True)`` for a sheet, else blank."""
    finished = NUMBER.findall(str(row.get("finished_size") or ""))
    if len(finished) == 3:
        return TIMES.join(number(v) for v in finished), False
    sheet = NUMBER.findall(str(row.get("sheet_size") or ""))
    if len(sheet) == 2:
        return TIMES.join(number(v) for v in sheet), True
    return "", False


def quantity(row: dict) -> str:
    for key, unit in (("sheets_to_order", "sheets"), ("pieces", "pcs"),
                      ("coverage_sqft", "sq ft")):
        if number(row.get(key)):
            return f"{number(row.get(key))} {unit}"
    return ""


def _tags(row: dict) -> list[str]:
    return [tag.strip() for tag in str(row.get("element_tags") or "").split(",") if tag.strip()]


def schedule(hardwood: Iterable[dict], panels: Iterable[dict]
             ) -> tuple[list[tuple[dict, int | None]], list[_Note]]:
    """Rows sorted by species (input order within one), each with its note number.

    Identical note texts share one number and gather every tag that cites them, so the
    four door casings that read "rip from the wide stack" do not print it four times.
    """
    rows = sorted([*hardwood, *panels], key=lambda r: str(r.get("species") or "").casefold())
    notes: list[_Note] = []
    by_text: dict[str, int] = {}
    numbered: list[tuple[dict, int | None]] = []
    for row in rows:
        parts = [str(row.get("stock_note") or "").strip().rstrip(".")]
        grain = str(row.get("grain_direction") or "")
        if grain and row.get("stock_kind") != "panel":
            parts.append(f"grain {grain}")
        text = "; ".join(p for p in parts if p and p != "None")
        if not text:
            numbered.append((row, None))
            continue
        if text not in by_text:
            notes.append(_Note(text))
            by_text[text] = len(notes)
        index = by_text[text]
        notes[index - 1].tags.extend(t for t in _tags(row) if t not in notes[index - 1].tags)
        numbered.append((row, index))
    return numbered, notes


def species_totals(rows: Iterable[dict]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for row in rows:
        if number(row.get("rough_board_feet")):
            species = str(row.get("species") or "unknown")
            totals[species] = totals.get(species, 0.0) + float(str(row["rough_board_feet"]))
    return dict(sorted(totals.items()))


def write_millwork_pdf(path: Path, house: str, hardwood: list[dict], panels: list[dict]
                       ) -> None:
    from reportlab import rl_config

    path.parent.mkdir(parents=True, exist_ok=True)
    previous = rl_config.invariant
    rl_config.invariant = 1
    try:
        buffer = io.BytesIO()
        _build(buffer, house, hardwood, panels)
        path.write_bytes(buffer.getvalue())
    finally:
        rl_config.invariant = previous


def _styles():  # type: ignore[no-untyped-def]
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle

    cell = ParagraphStyle("cell", fontName="Helvetica", fontSize=CELL_PT,
                          leading=CELL_PT + 0.5, textColor=HexColor("#111111"))
    return {
        "cell": cell,
        "right": ParagraphStyle("right", parent=cell, alignment=TA_RIGHT),
        "head": ParagraphStyle("head", parent=cell, fontName="Helvetica-Bold",
                               textColor=HexColor("#FFFFFF")),
        "head_right": ParagraphStyle("head_right", parent=cell, fontName="Helvetica-Bold",
                                     textColor=HexColor("#FFFFFF"), alignment=TA_RIGHT),
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=12.5,
                                leading=15, textColor=HexColor("#FFFFFF")),
        "band": ParagraphStyle("band", fontName="Helvetica", fontSize=6.8, leading=8,
                               textColor=HexColor("#FFFFFF"), alignment=TA_RIGHT),
        "legend": ParagraphStyle("legend", fontName="Helvetica", fontSize=6.1, leading=8,
                                 textColor=HexColor(MUTED)),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=8.5, leading=11,
                             textColor=HexColor(ACCENT), spaceBefore=8, spaceAfter=3),
        "note": ParagraphStyle("note", parent=cell, leading=CELL_PT + 2.2),
    }


def _muted(text: str, size: float = SMALL_PT) -> str:
    return f'<font size="{size}" color="{MUTED}">{escape(text, quote=False)}</font>'


def _dash() -> str:
    return _muted("–", CELL_PT)


def _header_band(house: str, rows: int, total_bf: float, styles):  # type: ignore[no-untyped-def]
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import Paragraph, Table, TableStyle

    title = (f"{escape(house.upper())} HOUSE&nbsp;&nbsp;<font color='{ACCENT}'>|</font>"
             "&nbsp;&nbsp;MILLWORK")
    stats = f"{rows} rows&nbsp;&nbsp;•&nbsp;&nbsp;{number(round(total_bf, 1))} rough BF"
    band = Table([[Paragraph(title, styles["title"]), Paragraph(stats, styles["band"])]],
                 colWidths=(BODY_W * 0.6, BODY_W * 0.4))
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(INK)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return band


def _schedule_table(numbered: list[tuple[dict, int | None]], styles):  # type: ignore[no-untyped-def]
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import LongTable, Paragraph, TableStyle

    def cell(html: str, style: str = "cell"):  # type: ignore[no-untyped-def]
        return Paragraph(html, styles[style])

    data = [[cell(h, "head") for h in HEADERS[:-1]] + [cell(HEADERS[-1], "head_right")]]
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), HexColor(ACCENT)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor(STRIPE), HexColor("#FFFFFF")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.2), ("RIGHTPADDING", (0, 0), (-1, -1), 3.2),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0.6),
        ("TOPPADDING", (0, 0), (-1, 0), 1.5), ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
    ]
    previous = None
    for index, (row, note) in enumerate(numbered, start=1):
        species = str(row.get("species") or "").title()
        if previous is not None and species != previous:
            commands.append(("LINEABOVE", (0, index), (-1, index), 0.45, HexColor(INK)))
        previous = species
        use = f"<b>{escape(str(row.get('use') or row.get('material') or '').title())}</b>"
        if row.get("stock_kind") == "panel":
            use = "<b>Plywood Sheets</b>"
        if row.get("location"):
            use += " " + _muted(f"/ {row['location']}")
        if note is not None:
            use += f' <font color="{ACCENT}"><super rise="2.2" size="5">{note}</super></font>'
        dims, is_sheet = dimensions(row)
        dims_html = (f"<b>{dims}</b>" + (" " + _muted("sheet") if is_sheet else "")
                     if dims else _dash())
        qty = quantity(row)
        qty_html = "<b>{}</b> {}".format(*qty.split(" ", 1)) if qty else _dash()
        stock = escape(str(row.get("nominal_stock") or ""), quote=False)
        profile = str(row.get("milling_profile") or "")
        stock_html = (f"<b>{stock}</b>" + (" " + _muted(f"· {profile}", CELL_PT - 0.6)
                                           if profile else "")) if stock else _dash()
        bf = number(row.get("rough_board_feet"))
        data.append([cell(f'<font color="{INK}"><b>{escape(species)}</b></font>'),
                     cell(use), cell(qty_html), cell(dims_html), cell(stock_html),
                     cell(f"<b>{bf}</b>" if bf else _dash(), "right")])
    fixed = sum(w for w in COLUMN_WIDTHS_IN if w is not None) * 72
    widths = [w * 72 if w is not None else BODY_W - fixed for w in COLUMN_WIDTHS_IN]
    table = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle(commands))
    return table


def _build(target, house: str, hardwood: list[dict], panels: list[dict]) -> None:  # type: ignore[no-untyped-def]
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

    from typehaus.takeoff.millwork_pdf_notes import notes_story

    styles = _styles()
    numbered, notes = schedule(hardwood, panels)
    totals = species_totals([*hardwood, *panels])
    legend = "&nbsp;&nbsp;•&nbsp;&nbsp;".join((
        "SIZE = FINISHED THICKNESS × WIDTH × LENGTH (IN)",
        "PANEL ROW = SHEET WIDTH × LENGTH", "STOCK = NOMINAL THICKNESS · PROFILE",
        "ROUGH BF = ESTIMATE", f'<font color="{ACCENT}"><super>n</super></font> = NOTE n'))
    story = [_header_band(house, len(numbered), sum(totals.values()), styles),
             Spacer(1, 3), Paragraph(legend, styles["legend"]), Spacer(1, 2),
             _schedule_table(numbered, styles), PageBreak(),
             *notes_story(notes, panels, totals, styles)]

    def footer(canvas, document):  # type: ignore[no-untyped-def]
        canvas.saveState()
        canvas.setStrokeColor(HexColor(ACCENT))
        canvas.setLineWidth(0.65)
        canvas.line(MARGIN, MARGIN, PAGE_W - MARGIN, MARGIN)
        canvas.setFillColor(HexColor(MUTED))
        canvas.setFont("Helvetica", SMALL_PT)
        canvas.drawString(MARGIN, MARGIN - 8,
                          "Unpriced shop view: every quantity is billed in its own estimate "
                          "section. Rough board feet are per line; area quantities are square "
                          "feet. Confirm supplied thickness before joinery.")
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 8, f"Millwork — {document.page}")
        canvas.restoreState()

    SimpleDocTemplate(target, pagesize=(PAGE_W, PAGE_H), leftMargin=MARGIN,
                      rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN + 3,
                      title=f"{house} millwork", creator="Type:Haus").build(
                          story, onFirstPage=footer, onLaterPages=footer)
