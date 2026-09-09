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

**Section-prefixed page numbers** — ``C-1``, ``L-3``, ``F-12``. A reviewer's comment is
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
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass

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
#: Columns of monospace that fit between the margins at ``BODY_PT``.
COLUMNS = 78

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_RULE = re.compile(r"^\s*([-*_])\1{2,}\s*$")
_BOLD = re.compile(r"\*\*(.+?)\*\*")


@dataclass(frozen=True)
class Page:
    """One laid-out page: the lines on it and the identity in its title block."""

    number: str            #: "C-1", "S-12"
    section: str           #: "COVER", "sunken garden retaining wall"
    lines: tuple[str, ...]


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


def paginate(files: dict[str, str]) -> list[Page]:
    """Lay the package's markdown out into numbered pages, front matter first.

    Section-prefixed and restarting at 1 per section, which is the property the numbering
    exists for: inserting a page into the loads section renumbers the loads section and
    nothing else, so a reviewer's page-anchored comment survives a resubmittal.
    """
    pages: list[Page] = []
    ordered = [(name, prefix, title) for name, prefix, title in SECTIONS if name in files]
    for name, prefix, title in ordered:
        pages.extend(_lay_out(files[name], prefix, title, start=1))
    item_files = sorted(n for n in files
                        if n not in _SKIP and n not in {s[0] for s in SECTIONS})
    counter = 1
    for name in item_files:
        laid = _lay_out(files[name], ITEM_PREFIX, _sheet_title(files[name], name),
                        start=counter)
        pages.extend(laid)
        counter += len(laid)
    return pages


def _sheet_title(text: str, name: str) -> str:
    """A per-item sheet's own H1, else its filename. The title block prints it verbatim."""
    for line in text.splitlines():
        head = _HEADING.match(line)
        if head and len(head.group(1)) == 1:
            return _plain(head.group(2))
    return name.rsplit("/", 1)[-1].removesuffix(".md")


def _plain(text: str) -> str:
    """Markdown emphasis out. Nothing else — a calc sheet's content is already plain, and
    a table's pipes are load-bearing alignment that must survive."""
    return _BOLD.sub(r"\1", text).replace("`", "")


def _lay_out(markdown: str, prefix: str, title: str, *, start: int) -> list[Page]:
    rows = _wrap(markdown)
    per_page = int((PAGE[1] - MARGIN_T - MARGIN_B) * 72.0 / LINE_PT)
    pages: list[Page] = []
    for index in range(0, max(len(rows), 1), per_page):
        pages.append(Page(number=f"{prefix}-{start + len(pages)}", section=title,
                          lines=tuple(rows[index:index + per_page])))
    return pages


def _wrap(markdown: str) -> list[str]:
    """Markdown to printable rows, at :data:`COLUMNS`.

    Headings keep their text and lose their hashes; a horizontal rule becomes a rule of
    dashes; a table row is passed through UNWRAPPED, because wrapping one destroys the
    column alignment that is the only thing making it a table — a calc sheet's tables are
    demand/capacity/ratio rows a reviewer reads down, and a ragged one is unreadable.
    """
    out: list[str] = []
    fenced = False
    for raw in markdown.splitlines():
        if raw.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced or raw.lstrip().startswith("|"):
            out.append(_plain(raw.rstrip())[:COLUMNS + 24])
            continue
        if _RULE.match(raw):
            out.append("-" * COLUMNS)
            continue
        line = _plain(raw.rstrip())
        head = _HEADING.match(line)
        if head:
            text = head.group(2)
            out.extend(["", text.upper() if len(head.group(1)) <= 2 else text])
            if len(head.group(1)) <= 2:
                out.append("-" * min(COLUMNS, len(text)))
            continue
        if not line.strip():
            out.append("")
            continue
        indent = "  " if line.lstrip().startswith(("-", "*", "•")) else ""
        out.extend(textwrap.wrap(line, width=COLUMNS, subsequent_indent=indent) or [""])
    return out


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


def write_calc_pdf(files: dict[str, str], out, inputs: PdfInputs) -> object:
    """Render the package to a flattened, text-searchable PDF at ``out``.

    Text-searchable because matplotlib's PDF backend embeds real text rather than curves —
    which matters: a reviewer searches a 200-page package for a member tag, and a package of
    outlines cannot be searched, quoted or accessibility-checked.
    """
    from matplotlib.backends.backend_pdf import PdfPages

    pages = paginate(files)
    out.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(out) as pdf:
        _draw_cover(pdf, inputs, pages)
        for page in pages:
            _draw_page(pdf, inputs, page)
    return out


def _figure():
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=PAGE)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0.0, PAGE[0])
    ax.set_ylim(0.0, PAGE[1])
    ax.axis("off")
    ax.patch.set_visible(False)
    return fig, ax


def _draw_cover(pdf, inputs: PdfInputs, pages: list[Page]) -> None:
    """Identity, the code editions named exactly, the index, and an empty seal area."""
    from matplotlib.patches import Rectangle

    fig, ax = _figure()
    y = PAGE[1] - 1.30
    ax.text(MARGIN_L, y, "STRUCTURAL CALCULATIONS", fontsize=17, family="monospace",
            weight="bold")
    y -= 0.42
    ax.text(MARGIN_L, y, inputs.house, fontsize=12.5, family="monospace")
    y -= 0.55
    rows = [
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
    for label, value in rows:
        ax.text(MARGIN_L, y, f"{label:<14}{value}", fontsize=9, family="monospace")
        y -= 0.24
    if inputs.scope:
        y -= 0.12
        for line in textwrap.wrap(inputs.scope, width=64):
            ax.text(MARGIN_L, y, line, fontsize=9, family="monospace")
            y -= 0.20

    # The seal area. Outlined, captioned, and empty — the engine never draws a stamp.
    box_w, box_h = 2.6, 2.6
    box_x, box_y = PAGE[0] - MARGIN_L - box_w, PAGE[1] - 1.55 - box_h
    ax.add_patch(Rectangle((box_x, box_y), box_w, box_h, fill=False,
                           edgecolor="#999999", linewidth=0.6, linestyle=(0, (4, 3))))
    ax.text(box_x + box_w / 2.0, box_y + box_h / 2.0,
            "SEAL AND\nSIGNATURE", fontsize=8, family="monospace",
            ha="center", va="center", color="#999999")

    y -= 0.35
    ax.text(MARGIN_L, y, "INDEX", fontsize=11, family="monospace", weight="bold")
    y -= 0.30
    for section, span in index_rows(pages):
        ax.text(MARGIN_L, y, f"{section[:52]:<54}{span}", fontsize=8.5,
                family="monospace")
        y -= 0.19
        if y < MARGIN_B + 0.4:
            break

    ax.text(MARGIN_L, MARGIN_B - 0.35, _NOT_SEALED, fontsize=7.5, family="monospace",
            color="#8a1c1c", va="top", wrap=True)
    pdf.savefig(fig)
    _close(fig)


#: On the cover of every package this emitter writes, and it stays true until a person
#: applies a seal to the flattened file — which this engine has no way to do and must not.
_NOT_SEALED = (
    "NOT FOR CONSTRUCTION — this package carries no professional seal.\n"
    "Every result in it is this engine's own draft calculation, oracled against a\n"
    "hand-worked note. Nothing here may be built from until a licensed engineer has\n"
    "reviewed it and applied a seal to this document."
)


def _draw_page(pdf, inputs: PdfInputs, page: Page) -> None:
    fig, ax = _figure()
    ax.plot([MARGIN_L, PAGE[0] - MARGIN_L * 0.5],
            [PAGE[1] - MARGIN_T + 0.30] * 2, color="#1a1a1a", linewidth=0.6)
    ax.text(MARGIN_L, PAGE[1] - MARGIN_T + 0.44, inputs.house, fontsize=8,
            family="monospace", weight="bold")
    ax.text(PAGE[0] - MARGIN_L * 0.5, PAGE[1] - MARGIN_T + 0.44, page.number,
            fontsize=10, family="monospace", weight="bold", ha="right")
    ax.text(MARGIN_L, PAGE[1] - MARGIN_T + 0.14, page.section[:60], fontsize=7,
            family="monospace", color="#555555")
    ax.text(PAGE[0] - MARGIN_L * 0.5, PAGE[1] - MARGIN_T + 0.14,
            f"{inputs.generated}  ·  BY {inputs.designer}  ·  CHK ____",
            fontsize=7, family="monospace", color="#555555", ha="right")

    y = PAGE[1] - MARGIN_T
    step = LINE_PT / 72.0
    for line in page.lines:
        ax.text(MARGIN_L, y, line, fontsize=BODY_PT, family="monospace", va="top")
        y -= step
    pdf.savefig(fig)
    _close(fig)


def _close(fig) -> None:
    import matplotlib.pyplot as plt

    plt.close(fig)
