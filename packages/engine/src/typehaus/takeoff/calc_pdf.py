"""``out/calcs.pdf`` — the calculation package as a flattened, page-anchored PDF.

Markdown stays the source of truth. ``docs/calc-package-format.md``'s reasoning is
unchanged and this module does not touch it: the ``{path: markdown}`` that
:mod:`typehaus.takeoff.calc_package` produces is byte-deterministic, diffable, and the
thing a reviewer marks up in an editor. What Markdown cannot be is *submitted*.

**No jurisdiction accepts Markdown, and a seal has to bind to a flattened document.** Under
the NCEES Model Rules a professional seal is applied so that any change to the document
invalidates it, which means the sealed artefact has to be a single flattened file — not a
folder of text a reviewer can edit without trace. That is the whole reason this exists.

What real sealed residential packages do, and what is copied here (City of Pleasanton's ADU
sample; Buker Engineering's Hinckley Residence, Mercer Island permit 2408-045):

**Section-prefixed page numbers** — ``C-1``, ``D-3``, ``S-12``. A reviewer's comment is
page-anchored, and a resubmittal that inserts one page into the loads section must not
renumber the footings section under their comment. A flat 1..N cannot promise that; a
per-section sequence can.

**A detailed index with page ranges**, which CBC/IBC 1603A.3 requires rather than suggests.

**A per-page title block** — project, sheet id, date, designer, checker — because a page
photocopied out of a package still has to say what it belongs to.

**A reserved seal area on the cover**, empty. The engine never draws a stamp; ``haus print``
and ``schedules/structural.py`` take the same line, and it is the same line: drawing one
would be forging it.

**Right-margin whitespace**, deliberately, so a PE can do arithmetic beside a number.

Content is not softened on the way through. The INCOMPLETE items keep saying INCOMPLETE and
the deferred items keep naming who owns them; a PDF that reads better than the register it
came from would be the wrong artefact.

** THIS WAS A MATPLOTLIB RENDERER UNTIL 2026-09-18, AND IT COULD NOT BE FIXED IN PLACE. **
It drew every glyph with ``ax.text`` into ``PdfPages``: no table engine, no text flow, and
no outline or link API, so bookmarks were not a small change there. Three defects followed
from the absence of a layout model rather than from any of its settings, and all three are
gone with it:

* a markdown table printed its pipes **literally**, as the source text;
* every line was truncated at ``COLUMNS + 24`` characters, which runs to x ≈ 8.15" on an
  8.5" page and **silently dropped the rest** — 305 lines of catlin's own package sat at
  that cap, the longest source row 860 characters;
* the index printed until it ran out of cover and then hit a hard ``break``: 25 rows of 40.

Platypus gives real tables, flowing paragraphs, a document outline, internal links and a
two-pass index over true page labels. ``reportlab`` is a declared runtime dependency, so
``scripts/ci_local.sh`` (a throwaway venv from the declared extras alone) is the gate that
sees it — ``scripts/verify.sh`` runs in ``.venv`` and is blind to a missing one.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.takeoff.calc_markdown import (
    Bullets,
    Code,
    Heading,
    Paragraph_,
    Rule,
    Table_,
    inline,
    parse,
)

#: Page-number prefix per front-matter file, and the section title the index prints. The
#: order here is the order of the package.
SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("00-cover.md", "C", "COVER"),
    ("01-design-criteria.md", "D", "DESIGN CRITERIA"),
    ("02-item-register.md", "R", "ITEM REGISTER"),
    ("03-open-items.md", "O", "OPEN ITEMS"),
    ("04-assumptions.md", "A", "ASSUMPTIONS"),
    # Two letters, because the item sheets already own "S" and a reviewer citing "S-4"
    # must not have to ask which series it came from.
    ("05-scope-of-review.md", "SR", "SCOPE OF REVIEW"),
)

#: Every per-item sheet takes this prefix. One section, because the sheets are one series a
#: reviewer walks in order; the item id in the title block says which is which.
ITEM_PREFIX = "S"

#: Files that are repository navigation rather than package content.
_SKIP = frozenset({"README.md"})

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

#: How many passes the index is allowed to take to reach a fixed point. Growing the index
#: shifts every page after it, which can change the index — two passes settle it in
#: practice and the cap is what stops a pathological package spinning.
_INDEX_PASSES = 4


@dataclass(frozen=True)
class Page:
    """One page's identity, for the index. The CONTENT is Platypus' business now.

    Kept as a type because ``index_rows`` is the code-required index (CBC/IBC 1603A.3) and
    is derived from real page labels rather than authored — the same property it always had,
    now sourced from a layout engine instead of from a line count.
    """

    number: str            #: "C-1", "S-12"
    section: str           #: "COVER", "sunken garden retaining wall"


@dataclass(frozen=True)
class PdfInputs:
    house: str
    generated: str
    engine_version: str
    content_hash: str
    designer: str = "TYPE:HAUS"
    checker: str = ""
    code_edition: str = ""
    asce_edition: str = ""
    scope: str = ""


#: On the cover of every package this emitter writes, and it stays true until a person
#: applies a seal to the flattened file — which this engine has no way to do and must not.
_NOT_SEALED = (
    "NOT FOR CONSTRUCTION — this package carries no professional seal. Every result in it "
    "is this engine's own draft calculation, oracled against a hand-worked note. Nothing "
    "here may be built from until a licensed engineer has reviewed it and applied a seal "
    "to this document."
)


def sheet_order(files: dict[str, str]) -> list[tuple[str, str, str]]:
    """``(filename, page prefix, section title)`` in package order — front matter first.

    The one definition of what goes into the PDF and under which series, so the index, the
    outline and the page stamps cannot disagree about it.
    """
    out = [(name, prefix, title) for name, prefix, title in SECTIONS if name in files]
    known = {name for name, _, _ in SECTIONS}
    for name in sorted(n for n in files if n not in _SKIP and n not in known):
        out.append((name, ITEM_PREFIX, _sheet_title(files[name], name)))
    return out


def _sheet_title(text: str, name: str) -> str:
    """A per-item sheet's own H1, else its filename. The title block prints it verbatim."""
    for block in parse(text, source=name):
        if isinstance(block, Heading) and block.level == 1:
            return block.text
    return name.rsplit("/", 1)[-1].removesuffix(".md")


def index_rows(pages: list[Page]) -> list[tuple[str, str]]:
    """``(section, page range)`` — the code-required index, derived from the pagination.

    Derived rather than authored, so it cannot promise a page the package does not have.
    Consecutive pages of one section collapse to a range; that is the whole table.
    """
    rows: list[tuple[str, str]] = []
    for page in pages:
        if rows and rows[-1][0] == page.section:
            first = rows[-1][1].split("..")[0]
            rows[-1] = (page.section, f"{first}..{page.number}")
        else:
            rows.append((page.section, page.number))
    return rows


# --- the renderer ------------------------------------------------------------------------

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


class _SectionMark:
    """A zero-height flowable that tells the doc template a new series has started."""

    def __init__(self, prefix: str, title: str, first: bool) -> None:
        self.prefix, self.title, self.first = prefix, title, first
        self.width = self.height = 0

    def wrap(self, *_args):  # type: ignore[no-untyped-def]
        return (0, 0)

    def drawOn(self, canvas, x, y, _sW=0):  # type: ignore[no-untyped-def]
        return None

    # Platypus calls these on every flowable; the defaults are fine.
    def split(self, *_args):  # type: ignore[no-untyped-def]
        return []

    def getKeepWithNext(self):  # type: ignore[no-untyped-def]
        return False

    def isIndexing(self):  # type: ignore[no-untyped-def]
        return 0


def _table(block: Table_, styles, width: float):  # type: ignore[no-untyped-def]
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

    def word_floor(index: int) -> float:
        font = "Helvetica-Bold" if index < 0 else "Helvetica"
        widest = 0.0
        for text in cells[index]:
            for word in text.replace("`", "").split() or [""]:
                widest = max(widest, stringWidth(word, font, 7.4))
        return min(widest + padding, 0.42 * width)

    floors = [max(word_floor(i), stringWidth(cells[i][0], "Helvetica-Bold", 7.4) / 2.0)
              for i in range(columns)]
    # A column's share of the SLACK is its content length, capped: past ~90 characters a
    # column is prose and reads fine at any reasonable width, so letting it keep growing
    # only starves the short columns beside it.
    weights = [min(max((len(text) for text in cells[i]), default=1), 90)
               for i in range(columns)]
    slack = max(width - sum(floors), 0.0)
    total = max(sum(weights), 1)
    widths = [floors[i] + slack * weights[i] / total for i in range(columns)]
    scale = width / sum(widths)
    widths = [value * scale for value in widths]

    data = [[Paragraph(inline(cell), styles["cellhead"]) for cell in block.header]]
    for row in block.rows:
        padded = list(row) + [""] * (columns - len(row))
        data.append([Paragraph(inline(cell), styles["cell"]) for cell in padded[:columns]])
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


def _flowables(markdown: str, name: str, styles, width: float) -> list:  # type: ignore[no-untyped-def]
    from reportlab.platypus import HRFlowable, Paragraph, Spacer

    out: list = []
    for block in parse(markdown, source=name):
        if isinstance(block, Heading):
            style = styles["h1" if block.level == 1 else
                           "h2" if block.level == 2 else "h3"]
            # The anchor is what the outline entry and any internal link both point at.
            out.append(Paragraph(f'<a name="{block.anchor}"/>{inline(block.text)}', style))
        elif isinstance(block, Paragraph_):
            out.append(Paragraph(inline(block.text), styles["body"]))
        elif isinstance(block, Bullets):
            out.extend(Paragraph(inline(item), styles["bullet"], bulletText="–")
                       for item in block.items)
            out.append(Spacer(1, 3))
        elif isinstance(block, Table_):
            table = _table(block, styles, width)
            if table is not None:
                out.extend([Spacer(1, 2), table, Spacer(1, 6)])
        elif isinstance(block, Code):
            out.extend(Paragraph(inline(line) or "&nbsp;", styles["code"])
                       for line in block.lines)
            out.append(Spacer(1, 4))
        elif isinstance(block, Rule):
            out.append(HRFlowable(width="100%", thickness=0.4, color="#cccccc",
                                  spaceBefore=4, spaceAfter=6))
    return out


def _cover(inputs: PdfInputs, rows: list[tuple[str, str]], styles,
           width: float) -> list:  # type: ignore[no-untyped-def]
    """Identity, the code editions named exactly, the FULL index, and an empty seal area.

    ** THE INDEX IS A FLOWING TABLE AND SPILLS ONTO A SECOND PAGE WHERE IT NEEDS TO. ** It
    used to be drawn line by line into the space left on the cover and cut off with a hard
    ``break`` when it ran out — 25 of catlin's 40 rows. An index that stops is worse than no
    index: a reviewer looking for the fifteenth section concludes it is not in the package.
    """
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    from typehaus.takeoff.calc_pdf import _seal_box  # local: keeps the drawing beside it

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
    data += [[Paragraph(inline(section), styles["cell"]),
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


class _Doc:
    """A ``BaseDocTemplate`` subclass, built lazily so importing this module is cheap."""

    _cls = None

    @classmethod
    def get(cls):  # type: ignore[no-untyped-def]
        if cls._cls is not None:
            return cls._cls
        from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

        class CalcDoc(BaseDocTemplate):
            """Section-restarting page labels, a per-page title block, and an outline."""

            def __init__(self, *args, inputs: PdfInputs, **kwargs):  # type: ignore[no-untyped-def]
                super().__init__(*args, **kwargs)
                self.inputs = inputs
                self.prefix, self.section, self.counter = "C", "COVER", 0
                #: The section the NEXT page begins, set by a ``_SectionMark`` that sits
                #: just before the ``PageBreak`` into it. The stamp runs at page BEGIN,
                #: before any flowable on that page has been handled, so a mark consumed
                #: after the break would label its own first page with the section before
                #: it — which is how two short item sheets on one page silently lost one of
                #: them from the index.
                self.pending: tuple[str, str, bool] | None = None
                self.labels: list[Page] = []
                frame = Frame(
                    MARGIN_L * 72, MARGIN_B * 72,
                    (PAGE[0] - MARGIN_L - MARGIN_R) * 72,
                    (PAGE[1] - MARGIN_T - MARGIN_B) * 72,
                    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                    id="body")
                self.addPageTemplates([PageTemplate(id="calc", frames=[frame],
                                                    onPage=self._stamp)])

            def handle_flowable(self, flowables):  # type: ignore[no-untyped-def]
                if flowables and isinstance(flowables[0], _SectionMark):
                    mark = flowables.pop(0)
                    self.pending = (mark.prefix, mark.title, mark.first)
                    return
                super().handle_flowable(flowables)

            def handle_pageBegin(self):  # type: ignore[no-untyped-def]
                if self.pending is not None:
                    self.prefix, self.section, first = self.pending
                    if first:
                        self.counter = 0
                    self.pending = None
                super().handle_pageBegin()

            def afterFlowable(self, flowable):  # type: ignore[no-untyped-def]
                """Bookmarks and the document outline, off the headings themselves."""
                anchor = getattr(flowable, "_calc_anchor", None)
                if anchor is None:
                    return
                level, text, name = anchor
                self.canv.bookmarkPage(name)
                self.canv.addOutlineEntry(text[:110], name, level=min(level - 1, 3),
                                          closed=level > 1)

            def _stamp(self, canvas, doc):  # type: ignore[no-untyped-def]
                self.counter += 1
                number = f"{self.prefix}-{self.counter}"
                self.labels.append(Page(number=number, section=self.section))
                _title_block(canvas, self.inputs, number, self.section)

        cls._cls = CalcDoc
        return cls._cls


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


def _story(files: dict[str, str], inputs: PdfInputs, rows: list[tuple[str, str]],
           styles, width: float) -> list:  # type: ignore[no-untyped-def]
    from reportlab.platypus import PageBreak, Paragraph

    story: list = list(_cover(inputs, rows, styles, width))
    # The title-and-index page is itself C-1, so the ``00-cover.md`` section that follows it
    # must NOT restart the series — two pages labelled C-1 is the same failure the
    # per-section numbering exists to prevent, one level up. A section restarts the counter
    # exactly when its PREFIX changes, which is also what makes the item sheets one
    # continuous S series rather than 160 sheets all called S-1.
    previous = "C"
    for name, prefix, title in sheet_order(files):
        # The mark goes BEFORE the break: it sets what the NEXT page begins, and the stamp
        # runs at page begin. See ``CalcDoc.pending``.
        story.append(_SectionMark(prefix, title, first=prefix != previous))
        story.append(PageBreak())
        story.extend(_flowables(files[name], name, styles, width))
        previous = prefix
    # Tag the heading paragraphs so ``afterFlowable`` can build the outline from them.
    for flowable in story:
        if isinstance(flowable, Paragraph):
            text = getattr(flowable, "text", "") or ""
            if '<a name="' in text:
                anchor = text.split('<a name="', 1)[1].split('"', 1)[0]
                flowable._calc_anchor = (_level_of(flowable, styles),
                                         _plain_text(flowable), anchor)
    return story


def _level_of(flowable, styles) -> int:  # type: ignore[no-untyped-def]
    for level, key in ((1, "h1"), (2, "h2"), (3, "h3")):
        if flowable.style is styles[key]:
            return level
    return 3


def _plain_text(flowable) -> str:  # type: ignore[no-untyped-def]
    import re as _re

    return _re.sub(r"<[^>]+>", "", getattr(flowable, "text", "") or "").strip()


def write_calc_pdf(files: dict[str, str], out, inputs: PdfInputs) -> object:
    """Render the package to a flattened, text-searchable PDF at ``out``.

    Text-searchable because the text is real text with embedded fonts, not curves — which
    matters: a reviewer searches a 200-page package for a member tag, and a package of
    outlines cannot be searched, quoted or accessibility-checked.

    **Two passes, because the index quotes page labels that the index's own length moves.**
    The first lays the package out with an empty index and records the true label of every
    page; the second rebuilds with the real rows. It iterates to a fixed point (capped at
    :data:`_INDEX_PASSES`) because a longer index pushes content down and can change the
    very ranges it prints.

    **Byte-deterministic.** ``rl_config.invariant`` fixes the producer string, the creation
    and modification dates and the document id, so two runs over an unchanged model produce
    identical bytes and a changed hash is a changed model rather than a re-run. That is the
    property ``MANIFEST.json`` rests on.
    """
    import io

    from reportlab import rl_config

    out.parent.mkdir(parents=True, exist_ok=True)
    previous_invariant = rl_config.invariant
    rl_config.invariant = 1
    try:
        rows: list[tuple[str, str]] = []
        labels: list[Page] = []
        for _ in range(_INDEX_PASSES):
            labels = _build(files, inputs, rows, io.BytesIO())
            fresh = index_rows(labels)
            if fresh == rows:
                break
            rows = fresh
        buffer = io.BytesIO()
        _build(files, inputs, rows, buffer)
        out.write_bytes(buffer.getvalue())
    finally:
        rl_config.invariant = previous_invariant
    return out


def _build(files: dict[str, str], inputs: PdfInputs, rows: list[tuple[str, str]],
           target) -> list[Page]:  # type: ignore[no-untyped-def]
    styles = _styles()
    width = (PAGE[0] - MARGIN_L - MARGIN_R) * 72
    doc = _Doc.get()(
        target, pagesize=(PAGE[0] * 72, PAGE[1] * 72),
        leftMargin=MARGIN_L * 72, rightMargin=MARGIN_R * 72,
        topMargin=MARGIN_T * 72, bottomMargin=MARGIN_B * 72,
        title=f"{inputs.house} — structural calculations",
        author=inputs.designer, subject="Structural calculations (DRAFT, unsealed)",
        creator="Type:Haus", inputs=inputs)
    doc.build(_story(files, inputs, rows, styles, width))
    return doc.labels


def paginate(files: dict[str, str]) -> list[Page]:
    """Every page's identity, in order, by laying the package out.

    Kept as a function because the index and the tests both ask this question, and it is
    now answered by the layout engine rather than by a line count. It costs a full render,
    which is why ``write_calc_pdf`` does not call it — it reads the labels off its own
    first pass instead.
    """
    import io

    from reportlab import rl_config

    previous = rl_config.invariant
    rl_config.invariant = 1
    try:
        return _build(files, PdfInputs(house="", generated="", engine_version="",
                                       content_hash=""), [], io.BytesIO())
    finally:
        rl_config.invariant = previous
