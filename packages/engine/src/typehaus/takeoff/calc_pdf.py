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

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

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
from typehaus.takeoff.calc_pdf_layout import (
    APPENDIX_DIR,
    APPENDIX_TITLE,
    MARGIN_B,
    MARGIN_L,
    MARGIN_R,
    MARGIN_T,
    PAGE,
    _cover,
    _linker,
    _styles,
    _table,
    _title_block,
    appendix_divider,
    file_anchor,
)
from typehaus.takeoff.calc_sheet import is_member_sheet

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
    # S-1: the conventions every family calculation after it shares, said once.
    ("06-conventions.md", "S", "READING THE CALCULATIONS"),
)

#: Every FAMILY calculation takes this prefix. One section, because the calculations are
#: one series a reviewer walks in order; the family name in the title block says which is
#: which. ``S`` for "structural calculations", the series a reviewer cites.
ITEM_PREFIX = "S"

#: The per-member data behind the schedules. Its own series, after every calculation, so
#: that citing "S-4" is never ambiguous and so that the machine data is visibly an
#: appendix rather than the document.
APPENDIX_PREFIX = "X"

#: The appendix divider's key in :func:`pdf_sources`. Not a file: the page is written here,
#: because what it must say depends on whether the appendix was printed.
APPENDIX_DIVIDER = "appendix/00-divider"

#: Files that are repository navigation rather than package content.
_SKIP = frozenset({"README.md"})

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
    #: Print the per-family appendix tables (``haus calcs --pdf --appendix``). Off by
    #: default: the divider page then says where the data is, and the PDF is the package.
    include_appendix: bool = False


@dataclass(frozen=True)
class _Layout:
    """What pass N learned that pass N+1 prints: the index and each file's first page."""

    rows: tuple[tuple[str, str], ...] = ()
    starts: Mapping[str, str] = field(default_factory=dict)


def sheet_order(files: Mapping[str, str], *, include_appendix: bool = False
                ) -> list[tuple[str, str, str]]:
    """``(filename, page prefix, section title)`` in package order — front matter first.

    The one definition of what goes into the PDF and under which series, so the index, the
    outline and the page stamps cannot disagree about it.

    ** NOTHING IS OMITTED SILENTLY. ** The per-member sheets never print, and the per-family
    appendix tables print only when asked — and either way the :data:`APPENDIX_DIVIDER`
    page is in the order and says where the unprinted data lives.
    """
    out = [(name, prefix, title) for name, prefix, title in SECTIONS if name in files]
    known = {name for name, _, _ in SECTIONS}
    rest = sorted(n for n in files if n not in _SKIP and n not in known)
    # Calculations first, then the appendix — and anything unfiled rides with the
    # calculations rather than vanishing.
    for name in rest:
        if not name.startswith(APPENDIX_DIR):
            out.append((name, ITEM_PREFIX, _sheet_title(files[name], name)))
    appendix = [name for name in rest if name.startswith(APPENDIX_DIR)]
    if appendix:
        out.append((APPENDIX_DIVIDER, APPENDIX_PREFIX, APPENDIX_TITLE))
    if include_appendix:
        out += [(name, APPENDIX_PREFIX, _sheet_title(files[name], name))
                for name in appendix if not is_member_sheet(name)]
    return out


def pdf_sources(files: Mapping[str, str], *, include_appendix: bool = False
                ) -> dict[str, str]:
    """Every markdown source the PDF prints, the divider page included."""
    order = sheet_order(files, include_appendix=include_appendix)
    sources = {name: files[name] for name, _, _ in order if name != APPENDIX_DIVIDER}
    if any(name == APPENDIX_DIVIDER for name, _, _ in order):
        sources[APPENDIX_DIVIDER] = appendix_divider(files, include_appendix)
    return sources


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


class _SectionMark:
    """A zero-height flowable that tells the doc template a new series has started."""

    def __init__(self, prefix: str, title: str, first: bool, anchor: str) -> None:
        self.prefix, self.title, self.first, self.anchor = prefix, title, first, anchor
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


def _flowables(markdown: str, name: str, styles, width: float,  # type: ignore[no-untyped-def]
               link: Callable[[str], str | None] | None = None) -> list:
    from reportlab.platypus import HRFlowable, Paragraph, Spacer

    out: list = []
    for block in parse(markdown, source=name):
        if isinstance(block, Heading):
            style = styles["h1" if block.level == 1 else
                           "h2" if block.level == 2 else "h3"]
            # The anchor is what the outline entry and any internal link both point at.
            out.append(Paragraph(f'<a name="{block.anchor}"/>{inline(block.text)}', style))
        elif isinstance(block, Paragraph_):
            out.append(Paragraph(inline(block.text, link), styles["body"]))
        elif isinstance(block, Bullets):
            out.extend(Paragraph(inline(item, link), styles["bullet"], bulletText="–")
                       for item in block.items)
            out.append(Spacer(1, 3))
        elif isinstance(block, Table_):
            table = _table(block, styles, width, link)
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
                #: The file anchor the next page begins, and each one's page label.
                self.start_anchor: str | None = None
                self.starts: dict[str, str] = {}
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
                    self.start_anchor = mark.anchor
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
                if self.start_anchor is not None:
                    canvas.bookmarkPage(self.start_anchor)
                    self.starts[self.start_anchor] = number
                    self.start_anchor = None
                _title_block(canvas, self.inputs, number, self.section)

        cls._cls = CalcDoc
        return cls._cls


def _story(files: Mapping[str, str], inputs: PdfInputs, layout: _Layout,
           styles, width: float) -> list:  # type: ignore[no-untyped-def]
    from reportlab.platypus import PageBreak, Paragraph

    sources = pdf_sources(files, include_appendix=inputs.include_appendix)
    order = sheet_order(files, include_appendix=inputs.include_appendix)
    link = _linker(sources, layout.starts)
    # The index links each section to its first page. COVER is the index page itself.
    targets = {title: file_anchor(name) for name, _prefix, title in order}
    story: list = list(_cover(inputs, list(layout.rows), styles, width, targets))
    # The title-and-index page is itself C-1, so the ``00-cover.md`` section that follows it
    # must NOT restart the series — two pages labelled C-1 is the same failure the
    # per-section numbering exists to prevent, one level up. A section restarts the counter
    # exactly when its PREFIX changes, which is also what makes the item sheets one
    # continuous S series rather than 160 sheets all called S-1.
    previous = "C"
    for name, prefix, title in order:
        # The mark goes BEFORE the break: it sets what the NEXT page begins, and the stamp
        # runs at page begin. See ``CalcDoc.pending``.
        story.append(_SectionMark(prefix, title, first=prefix != previous,
                                  anchor=file_anchor(name)))
        story.append(PageBreak())
        story.extend(_flowables(sources[name], name, styles, width, link))
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
    return re.sub(r"<[^>]+>", "", getattr(flowable, "text", "") or "").strip()


def write_calc_pdf(files: Mapping[str, str], out, inputs: PdfInputs) -> object:
    """Render the package to a flattened, text-searchable PDF at ``out``.

    Text-searchable because the text is real text with embedded fonts, not curves — which
    matters: a reviewer searches a 200-page package for a member tag, and a package of
    outlines cannot be searched, quoted or accessibility-checked.

    **Passes to a fixed point, because the index and the "(X-3)" link labels quote page
    labels that their own length moves.** The first pass lays the package out with neither
    and records the true label of every page; later passes rebuild with them, until nothing
    moves (capped at :data:`_INDEX_PASSES`).

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
        layout = _Layout()
        for _ in range(_INDEX_PASSES):
            labels, starts = _build(files, inputs, layout, io.BytesIO())
            fresh = _Layout(tuple(index_rows(labels)), dict(sorted(starts.items())))
            if fresh == layout:
                break
            layout = fresh
        buffer = io.BytesIO()
        _build(files, inputs, layout, buffer)
        out.write_bytes(buffer.getvalue())
    finally:
        rl_config.invariant = previous_invariant
    return out


def _build(files: Mapping[str, str], inputs: PdfInputs, layout: _Layout,
           target) -> tuple[list[Page], dict[str, str]]:  # type: ignore[no-untyped-def]
    styles = _styles()
    width = (PAGE[0] - MARGIN_L - MARGIN_R) * 72
    doc = _Doc.get()(
        target, pagesize=(PAGE[0] * 72, PAGE[1] * 72),
        leftMargin=MARGIN_L * 72, rightMargin=MARGIN_R * 72,
        topMargin=MARGIN_T * 72, bottomMargin=MARGIN_B * 72,
        title=f"{inputs.house} — structural calculations",
        author=inputs.designer, subject="Structural calculations (DRAFT, unsealed)",
        creator="Type:Haus", inputs=inputs)
    doc.build(_story(files, inputs, layout, styles, width))
    return doc.labels, doc.starts


def paginate(files: Mapping[str, str], *, include_appendix: bool = False) -> list[Page]:
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
                                       content_hash="", include_appendix=include_appendix),
                      _Layout(), io.BytesIO())[0]
    finally:
        rl_config.invariant = previous
