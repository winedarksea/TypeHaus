"""The page furniture of ``calcs.pdf``: styles, tables, the cover and the title block.

Split out of :mod:`typehaus.takeoff.calc_pdf` (which keeps the story, the pagination and
the document template) so both stay under the repo's 500-line ceiling.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING

from typehaus.takeoff.calc_markdown import Table_, inline
from typehaus.takeoff.calc_sheet import is_member_sheet

if TYPE_CHECKING:
    from typehaus.takeoff.calc_pdf import PdfInputs

#: Where the per-member data lives, and the title of the X series that says so.
APPENDIX_DIR = "appendix/"
APPENDIX_TITLE = "APPENDIX — PER-MEMBER DATA"

#: Page geometry, inches. US Letter portrait — a calc package is read and marked up at a
#: desk, not pinned to a wall, and every sealed residential package sampled is letter.
PAGE = (8.5, 11.0)
MARGIN_L = 0.90
#: Wide on purpose. A PE checks arithmetic in the margin beside the number it belongs to,
#: and a package with 0.5" margins forces that onto a separate sheet that then has to be
#: cross-referenced back.
MARGIN_R = 2.10
MARGIN_T = 1.10
MARGIN_B = 0.90

BODY_PT = 8.5
LINE_PT = BODY_PT * 1.55

#: Internal links print in this colour, so a reviewer can see what is clickable.
LINK_COLOUR = "#1a4f8a"

#: On the cover of every package this emitter writes, and it stays true until a person
#: applies a seal to the flattened file — which this engine has no way to do and must not.
_NOT_SEALED = (
    "NOT FOR CONSTRUCTION — this package carries no professional seal. Every result in it "
    "is this engine's own draft calculation, oracled against a hand-worked note. Nothing "
    "here may be built from until a licensed engineer has reviewed it and applied a seal "
    "to this document."
)


def _styles():  # type: ignore[no-untyped-def]
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.styles import ParagraphStyle

    body = ParagraphStyle(
        "body", fontName="Helvetica", fontSize=BODY_PT, leading=LINE_PT,
        alignment=TA_LEFT, spaceAfter=4.5, allowWidows=0, allowOrphans=0)
    return {
        "body": body,
        "h1": ParagraphStyle("h1", parent=body, fontName="Helvetica-Bold", fontSize=13.5,
                             leading=17, spaceBefore=6, spaceAfter=8),
        "h2": ParagraphStyle("h2", parent=body, fontName="Helvetica-Bold", fontSize=10.5,
                             leading=14, spaceBefore=11, spaceAfter=5),
        "h3": ParagraphStyle("h3", parent=body, fontName="Helvetica-Bold", fontSize=9,
                             leading=12, spaceBefore=8, spaceAfter=4),
        "bullet": ParagraphStyle("bullet", parent=body, leftIndent=12, bulletIndent=2,
                                 spaceAfter=2.5),
        "cell": ParagraphStyle("cell", parent=body, fontSize=7.4, leading=9.2,
                               spaceAfter=0),
        "cellhead": ParagraphStyle("cellhead", parent=body, fontName="Helvetica-Bold",
                                   fontSize=7.4, leading=9.2, spaceAfter=0),
        "code": ParagraphStyle("code", parent=body, fontName="Courier", fontSize=7.4,
                               leading=9.4, leftIndent=8, spaceAfter=1),
        "meta": ParagraphStyle("meta", parent=body, fontSize=7.5, leading=9.5,
                               textColor="#555555"),
        "warn": ParagraphStyle("warn", parent=body, fontSize=8, leading=10.5,
                               textColor="#8a1c1c"),
    }


def _table(block: Table_, styles, width: float, link=None):  # type: ignore[no-untyped-def]
    """A markdown pipe table as a real Platypus table.

    ** THIS IS WHERE THE PIPES USED TO BE PRINTED LITERALLY. ** Every cell is a wrapping
    ``Paragraph``, so a 400-character citation in a limit-state row flows down its column
    instead of being cut off at a character count — which was the single largest source of
    silently lost content in the old renderer, and it fell most often on exactly the
    citations a reviewer needs.

    ** COLUMN WIDTHS ARE A FLOOR PLUS A SHARE, NOT A BARE PROPORTION. ** A proportional
    split by longest cell gives a 400-character prose column almost the whole frame and
    squeezes "Items" into two characters, so the header itself wraps to "Item / s". Each
    column first reserves the width its longest UNBREAKABLE word needs — a header word, an
    element tag, a citation's section number — and only the slack left over is shared out,
    weighted by content length with a cap so one long column cannot take all of it.
    """
    from reportlab.lib import colors
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.platypus import Paragraph, Table, TableStyle

    columns = len(block.header)
    if not columns:
        return None
    padding = 6.0
    cells = [[row[i] if i < len(row) else "" for row in (block.header, *block.rows)]
             for i in range(columns)]

    def word_width(text: str, header: bool) -> float:
        """The widest unbreakable token in one cell, in the font it will be DRAWN in.

        Backticks become Courier in :func:`inline`, and Courier is a third wider than
        Helvetica at the same size — measuring a monospaced element tag in Helvetica
        under-reserves its column by exactly the amount that makes it wrap.
        """
        mono = "`" in text
        font = ("Courier-Bold" if header else "Courier") if mono else (
            "Helvetica-Bold" if header else "Helvetica")
        widest = 0.0
        for word in text.replace("`", "").split() or [""]:
            widest = max(widest, stringWidth(word, font, 7.4))
        return widest

    floors = [min(padding + max(
        [word_width(cells[i][0], header=True)]
        + [word_width(text, header=False) for text in cells[i][1:]] or [0.0]),
        0.42 * width) for i in range(columns)]
    # A column's share of the SLACK is its content length, capped: past ~90 characters a
    # column is prose and reads fine at any reasonable width, so letting it keep growing
    # only starves the short columns beside it.
    weights = [min(max((len(text) for text in cells[i]), default=1), 90)
               for i in range(columns)]
    slack = max(width - sum(floors), 0.0)
    total = max(sum(weights), 1)
    widths = [floors[i] + slack * weights[i] / total for i in range(columns)]
    if sum(widths) > width:
        widths = _water_fill(widths, width)

    data = [[Paragraph(inline(cell), styles["cellhead"]) for cell in block.header]]
    for row in block.rows:
        padded = list(row) + [""] * (columns - len(row))
        data.append([Paragraph(inline(cell, link), styles["cell"])
                     for cell in padded[:columns]])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#bbbbbb")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return table


def _water_fill(widths: list[float], total: float) -> list[float]:
    """Bring ``widths`` down to ``total`` by CAPPING the widest, never by scaling all.

    ** THIS IS WHY "d/c" USED TO PRINT AS "d/ c". ** An eight-column register whose floors
    already overflowed the frame was rescaled proportionally, so a 3-character header that
    needed 18 points lost the same fraction as a prose column that had 200 to spare — and
    the only columns narrow enough to break were the ones that could least afford it.

    Water-filling finds the one cap ``c`` where ``sum(min(w, c)) == total``: every column
    under it keeps its width exactly, and the overflow comes wholly out of the columns
    wide enough to absorb it.
    """
    order = sorted(range(len(widths)), key=lambda i: widths[i])
    remaining, left = total, len(widths)
    cap = total
    for index in order:
        if widths[index] * left <= remaining:
            remaining -= widths[index]
            left -= 1
            continue
        cap = remaining / left
        break
    return [min(value, cap) for value in widths]


def _cover(inputs: PdfInputs, rows: list[tuple[str, str]], styles, width: float,
           targets: Mapping[str, str]) -> list:  # type: ignore[no-untyped-def]
    """Identity, the code editions named exactly, the FULL index, and an empty seal area.

    ** THE INDEX IS A FLOWING TABLE AND SPILLS ONTO A SECOND PAGE WHERE IT NEEDS TO. ** It
    used to be drawn line by line into the space left on the cover and cut off with a hard
    ``break`` when it ran out — 25 of catlin's 40 rows. An index that stops is worse than no
    index: a reviewer looking for the fifteenth section concludes it is not in the package.
    """
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    out: list = [
        Paragraph("STRUCTURAL CALCULATIONS", styles["h1"]),
        Paragraph(inline(inputs.house), styles["h2"]),
        Spacer(1, 6),
    ]
    meta = [
        ("PREPARED BY", inputs.designer),
        ("CHECKED BY", inputs.checker or "______________________"),
        ("DATE", inputs.generated),
        ("ENGINE", inputs.engine_version),
        ("MODEL", inputs.content_hash[:16]),
        # Named exactly, not "the current code": a package that does not say which edition
        # it was worked to cannot be reviewed against one.
        ("CODE", inputs.code_edition or "see the design criteria sheet"),
        ("LOADS", inputs.asce_edition or "see the design criteria sheet"),
    ]
    meta_table = Table([[Paragraph(f"<b>{label}</b>", styles["cell"]),
                         Paragraph(inline(value), styles["cell"])] for label, value in meta],
                       colWidths=[1.25 * 72, width - 1.25 * 72 - 2.8 * 72], hAlign="LEFT")
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    out.append(meta_table)
    if inputs.scope:
        out += [Spacer(1, 6), Paragraph(inline(inputs.scope), styles["body"])]
    out += [Spacer(1, 10), _seal_box(), Spacer(1, 12),
            Paragraph("INDEX", styles["h2"])]

    data = [[Paragraph("<b>Section</b>", styles["cellhead"]),
             Paragraph("<b>Pages</b>", styles["cellhead"])]]
    # Each row links to its section's first page: 1603A.3 asks for an index, and a
    # reviewer with a 60-page PDF open wants it to be one they can click.
    data += [[Paragraph(_linked(inline(section), targets.get(section)), styles["cell"]),
              Paragraph(span, styles["cell"])] for section, span in rows]
    index = Table(data, colWidths=[width - 1.4 * 72, 1.4 * 72], repeatRows=1,
                  hAlign="LEFT")
    index.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#bbbbbb")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    out += [index, Spacer(1, 14), Paragraph(_NOT_SEALED, styles["warn"])]
    return out


def _seal_box():  # type: ignore[no-untyped-def]
    """The seal area. Outlined, captioned, and empty — the engine never draws a stamp."""
    from reportlab.graphics.shapes import Drawing, Rect, String

    side = 2.3 * 72
    drawing = Drawing(side, side)
    drawing.add(Rect(0, 0, side, side, fillColor=None, strokeColor="#999999",
                     strokeWidth=0.6, strokeDashArray=[4, 3]))
    drawing.add(String(side / 2.0, side / 2.0 + 5, "SEAL AND", fontSize=8,
                       fontName="Helvetica", fillColor="#999999", textAnchor="middle"))
    drawing.add(String(side / 2.0, side / 2.0 - 6, "SIGNATURE", fontSize=8,
                       fontName="Helvetica", fillColor="#999999", textAnchor="middle"))
    drawing.hAlign = "RIGHT"
    return drawing


def _title_block(canvas, inputs: PdfInputs, number: str, section: str) -> None:  # type: ignore[no-untyped-def]
    top = (PAGE[1] - MARGIN_T) * 72
    right = (PAGE[0] - MARGIN_L * 0.5) * 72
    canvas.saveState()
    canvas.setLineWidth(0.6)
    canvas.setStrokeColorRGB(0.1, 0.1, 0.1)
    canvas.line(MARGIN_L * 72, top + 21, right, top + 21)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(MARGIN_L * 72, top + 31, inputs.house)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawRightString(right, top + 30, number)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColorRGB(0.33, 0.33, 0.33)
    canvas.drawString(MARGIN_L * 72, top + 9, section[:78])
    canvas.drawRightString(right, top + 9,
                           f"{inputs.generated}  ·  BY {inputs.designer}  ·  CHK ____")
    canvas.restoreState()




def _linked(html: str, anchor: str | None) -> str:
    return f'<a href="#{anchor}" color="{LINK_COLOUR}">{html}</a>' if anchor else html


def file_anchor(name: str) -> str:
    """The destination at a printed file's first page; what every internal link targets."""
    return "file_" + re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")


def _linker(sources: Mapping[str, str], starts: Mapping[str, str]
            ) -> Callable[[str], str | None]:
    """Code spans that name a printed file, or an item of a printed family, become links.

    ``appendix/deck_post.md`` links to its first page and says which (``X-3``) once the
    first pass has laid it out; ``deck_post/PT-SG-BF1`` links to ``calcs/deck_post.md``.
    A span naming something this PDF does not print stays plain text.
    """
    def link(span: str) -> str | None:
        target = span if span in sources else None
        label = ""
        if target is None and "/" in span and not span.endswith(".md"):
            family = f"calcs/{span.split('/', 1)[0]}.md"
            target = family if family in sources else None
        elif target is not None:
            label = starts.get(file_anchor(target), "")
        if target is None:
            return None
        suffix = f" ({label})" if label else ""
        return f'<a href="#{file_anchor(target)}" color="{LINK_COLOUR}">{{}}</a>{suffix}'
    return link


def appendix_divider(files: Mapping[str, str], include_appendix: bool) -> str:
    """The X-1 page: what the appendix holds, and where, printed or not."""
    tables = sorted(n for n in files if n.startswith(APPENDIX_DIR) and not is_member_sheet(n))
    members = sorted(n for n in files if is_member_sheet(n))
    where = ("the `appendix/` folder of the calculation package this PDF was generated "
             "from: `out/calcs/appendix/` from `haus calcs`, `calcs/appendix/` in a "
             "`haus handoff` bundle")
    lines = [f"# {APPENDIX_TITLE}", ""]
    if include_appendix:
        lines += [f"The per-family tables follow, {len(tables)} of them: every input and "
                  "limit state of every member, one column per member."]
    else:
        lines += [f"**Not printed in this document.** The per-member data behind every "
                  f"schedule is in {where}. Print it here with `haus calcs --pdf "
                  f"--appendix` (or `haus handoff --full`)."]
    lines += ["", *[f"- `{name}`" for name in tables], "",
              "Each table is one design family, member by member: the summaries, the "
              "inputs with their fingerprint quanta, and every limit state as "
              "`demand / capacity = d/c` with the citation's number in that family's §2 "
              "references. The family calculation carries the rest — the schedule "
              "(status, governing state, d/c, coverage, seal), the open inputs, the "
              "oracle notes and the fingerprints.", "",
              f"The {len(members)} per-member nine-section sheets "
              "(`appendix/<kind>__<tag>.md`) are diffable machine data and are never "
              f"printed; they are in {where}. Every field they hold is in the tables "
              "above or on the family calculation."]
    return "\n".join(lines) + "\n"


