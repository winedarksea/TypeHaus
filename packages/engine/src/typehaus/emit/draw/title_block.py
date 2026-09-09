"""The NCS title block, the issue stamp and the seal block — the chrome, not the paper.

Split out of ``sheet_writer`` when the seal block landed: the composer's job is *where the
drawing goes* (viewport, scale ladder, scale bar), and this module's is *what the block
says*. They share only ``_MARGIN``/``_INK`` and the block's own width, which live here
because the block is what sets them.

Two invariants this module exists to hold:

* **The engine never draws a stamp.** Cell 5 reserves a dashed box and rules four lines —
  NAME / LICENSE NO. / DATE / SIGNATURE — because Minn. R. 1800.4200 subp. 3 requires the
  certification on *each* sheet a licensee is responsible for, and subp. 4's wording is the
  instrument. The graphic stamp is permissive (1800.4300) and drawing one would forge it.
* **Nothing is invented.** An address the model does not carry prints as nothing at all.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import date

from typehaus.emit.draw.typography import wrap_columns_for

_MARGIN = 0.25       # border inset from the paper edge, inches
_INK = "#1a1a1a"

#: Minimum title-block strip height, inches — what a four-cell strip needed. The block is
#: a full NCS one now (identity, preparer, revision block, seal box, issue status), so it
#: takes ``title_height(size)`` instead: proportional to the sheet, clamped between this and
#: ``_TITLE_H_MAX``. A fixed height cannot serve both papers — 1.9" of block is right on the
#: 24"-tall ARCH D deliverable and eats a fifth of an 11"-tall ledger review print.
_TITLE_H = 0.75
_TITLE_H_MAX = 1.90
#: Fraction of sheet height the block takes between those bounds.
_TITLE_H_FRACTION = 0.085

#: Width of the RIGHT-EDGE title block, paper inches, used on scene sheets.
#:
#: **Why there are two title-block geometries, and why that is not a smell.** A scene sheet
#: and a table page compete for different things. A plan's viewport is computed — it takes
#: whatever the chrome leaves — and on ARCH D catlin's foundation plan needs 21.4" of the
#: 22.25" available HEIGHT while using 22.2" of 35.3" of WIDTH. Height there is the scarce
#: resource and width is free: a full NCS title block as a bottom strip costs S-100 a whole
#: step of scale (3/16" to 1/8"), and the same block on the right edge costs nothing.
#:
#: A table page is the mirror. It lays its content out in FIGURE FRACTIONS across the full
#: width, with the bottom already reserved at 0.11 — so a right-edge block would run through
#: every schedule on the sheet while the bottom strip costs it nothing.
#:
#: Same cells, same content, placed where each sheet has room. ``_draw_chrome(edge=...)``
#: is the switch and ``viewport_box`` reserves to match.
TITLE_W = 2.60

#: Clear space between the drawn border and any lettering, inches.
_GUTTER = 0.35


def title_height(size: tuple[float, float]) -> float:
    """Title-block strip height for this paper, inches.

    Bounded below by what the identity cells need and above by what a PE seal wants
    (~2" of clear area). Schedule pages lay their content out from figure fraction 0.11,
    so the block must also stay under ``0.11 * height - _MARGIN`` — which the fraction
    does by construction: 0.085 + 0.25/height < 0.11 for every paper this set prints on.
    """
    return max(_TITLE_H, min(_TITLE_H_MAX, _TITLE_H_FRACTION * size[1]))


#: What the set currently being written may be used for. Every sheet carries it, and the
#: default is the honest one: this engine computes, it does not seal. ``haus print``
#: overrides it only when its own gate passes — the same gate that decides whether the set
#: may be printed at all, so the stamp and the gate cannot disagree.
NOT_FOR_CONSTRUCTION = "NOT FOR CONSTRUCTION"
FOR_PLAN_CHECK = "FOR PLAN CHECK ONLY"
_ISSUE: ContextVar[str] = ContextVar("_ISSUE", default=NOT_FOR_CONSTRUCTION)


@contextmanager
def set_issue_status(status: str) -> Iterator[None]:
    """Stamp ``status`` on every sheet composed in this block."""
    token = _ISSUE.set(status)
    try:
        yield
    finally:
        _ISSUE.reset(token)


#: Stamp ink. Red is a warning, and it belongs only on the engine's own two defaults —
#: they say the set may not be built from. A house that authored ``[print] issue`` has
#: made an affirmative statement about its own set, and printing that in alarm ink would
#: contradict it.
_ISSUE_WARNING_INK = "#8a1c1c"
_ISSUE_INK = "#1a1a1a"


def _issue_color(status: str) -> str:
    return (_ISSUE_WARNING_INK if status.split(" · ")[0]
            in (NOT_FOR_CONSTRUCTION, FOR_PLAN_CHECK) else _ISSUE_INK)


@dataclass(frozen=True)
class SealBlock:
    """What cell 5 may say about a professional seal on this set.

    ``certification`` is the jurisdiction's own sentence, verbatim, or ``None`` where the
    profile states none — a Minnesota sentence must never print over another state's set.

    ``credit`` is populated **only** past ``haus print --sealed``: a name, a licence number
    and a date read off ``engineering.toml``, which is a human act this engine records and
    never performs. Without it the four lines print ruled and blank, which is the
    instrument a licensee signs.
    """

    certification: str | None = None
    #: "Jane Doe, PE (MN 12345), 2026-09-14" — ``Signoff.credit()``, unparsed.
    credit: str | None = None
    engineer: str | None = None
    license: str | None = None
    sealed_on: str | None = None


_SEAL: ContextVar[SealBlock | None] = ContextVar("_SEAL", default=None)


@contextmanager
def set_seal_block(block: SealBlock | None) -> Iterator[None]:
    """Make ``block`` the seal cell of every sheet composed in this block."""
    token = _SEAL.set(block)
    try:
        yield
    finally:
        _SEAL.reset(token)


def seal_block() -> SealBlock | None:
    return _SEAL.get()


def _carries_seal(number: str) -> bool:
    """S-sheets and the cover, and nothing else.

    Subp. 3 puts the certification on each sheet the licensee is *responsible for*. That is
    the structural set; lettering it on a lighting plan would claim a scope no engineer
    took. The cover carries it because the set's gate statement is there.
    """
    return number.startswith("S-") or number in ("G-001", "A-000")


def content_box(size: tuple[float, float]) -> tuple[float, float, float, float]:
    """The area a table page may letter into: ``(x0, y0, x1, y1)`` in paper inches.

    :func:`sheet_chrome` states this bound in its docstring as "above ~0.10 on ledger" and
    every schedule writer then hard-codes figure *fractions* against it. A fraction is the
    wrong unit for a bound that is really the border plus the title strip — both fixed
    inches — so a layout tuned on 11x17 either crashes into the title block or floats a
    long way above it when the same page is composed on 24x36. Returning inches lets a page
    ask how much room it actually has, which is what the cover's sheet index needs in order
    to choose a column count instead of silently drawing rows off the edge.

    The extra ``_GUTTER`` inside the border is breathing room, not structure: lettering
    hard against a drawn border reads as an error even when it is inside it.
    """
    width, height = size
    return (_MARGIN + _GUTTER, _MARGIN + title_height(size) + _GUTTER,
            width - _MARGIN - _GUTTER, height - _MARGIN - _GUTTER)


def _draw_chrome(fig, model, number: str, title: str,
                 scale_label: str, size: tuple[float, float], *,
                 edge: bool = False) -> None:
    """Border rectangle + title block, drawn in paper-inch coordinates.

    ``edge`` puts the block down the right-hand side (scene sheets, where height is the
    scarce resource) instead of along the bottom (table pages, where width is). See
    :data:`TITLE_W` for the measurement behind that split.
    """
    from matplotlib.patches import Rectangle

    width, height = size
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], zorder=5)
    ax.set_xlim(0.0, width)
    ax.set_ylim(0.0, height)
    ax.axis("off")
    ax.patch.set_visible(False)

    m = _MARGIN
    ax.add_patch(Rectangle((m, m), width - 2 * m, height - 2 * m, fill=False,
                           edgecolor=_INK, linewidth=1.2))
    pad = 0.10

    # Six cells: identity · site · preparer + issue · revisions · seal · sheet. The order is
    # the reading order of a title block — who and where, then who drew it and what it may
    # be used for, then what changed, then who is answerable, then which sheet this is. The
    # sheet number is LAST because it is what a reader's thumb finds on the corner of a
    # stack, which on the right-edge block means the bottom of the column.
    #
    # Proportions are what each cell has to SAY, measured off the printed sheet rather than
    # split evenly: identity is a name and up to two address lines, the revision block needs
    # room for a description, and the seal box wants to be nearly square.
    #
    # A sheet that carries the certification widens cell 5 at the revision block's expense:
    # four ruled lines and a cross-reference need the room, and an empty revision block can
    # afford to give it.
    seal = _SEAL.get() if _carries_seal(number) else None
    fractions = (0.18, 0.32, 0.52, 0.72 if seal is not None else 0.76, 0.87)
    if edge:
        ax.plot([width - m - TITLE_W, width - m - TITLE_W], [m, height - m],
                color=_INK, linewidth=0.9)
        # Bottom-to-top: the sheet number sits at the bottom corner, so the cell order is
        # reversed against the fractions, which run "first cell first".
        cuts = [height - m - (height - 2 * m) * f for f in fractions]
        for y in cuts:
            ax.plot([width - m - TITLE_W, width - m], [y, y], color=_INK, linewidth=0.5)
        tops, bottoms = [height - m, *cuts], [*cuts, m]
        cells = [(width - m - TITLE_W, width - m, top, bottom)
                 for top, bottom in zip(tops, bottoms, strict=True)]
    else:
        strip_top = m + title_height(size)
        inner_w = width - 2 * m
        ax.plot([m, width - m], [strip_top, strip_top], color=_INK, linewidth=0.9)
        dividers = [m + inner_w * f for f in fractions]
        for x in dividers:
            ax.plot([x, x], [m, strip_top], color=_INK, linewidth=0.5)
        lefts, rights = [m, *dividers], [*dividers, width - m]
        cells = [(left, right, strip_top, m)
                 for left, right in zip(lefts, rights, strict=True)]

    edges = [cell[0] for cell in cells] + [cells[-1][1]]

    def rows(count: int, index: int = 0) -> list[float]:
        """``count`` evenly spaced text baselines down cell ``index``, top row first."""
        top, bottom = cells[index][2], cells[index][3]
        step = (top - bottom) / (count + 0.6)
        return [top - step * (i + 0.8) for i in range(count)]

    def label(x: float, y: float, text: str, size_pt: float = 6.0,
              weight: str = "normal", color: str = _INK) -> None:
        ax.text(x, y, text, fontsize=size_pt, family="monospace", va="center",
                color=color, weight=weight)

    project = getattr(getattr(model, "plan", None), "project", None)
    site = getattr(project, "site", None)

    # --- cell 1: project identity and address -------------------------------------
    r = rows(4, 0)
    name = getattr(project, "name", "") or ""
    if name:
        label(edges[0] + pad, r[0], name, 10.5, "bold")
    address = _project_address(project, site)
    for row, line in zip(r[1:3], address, strict=False):
        label(edges[0] + pad, row, line, 6.5)
    label(edges[0] + pad, r[3], "TYPE:HAUS — generated construction set", 5.5,
          color="#555555")

    # --- cell 2: where on earth ----------------------------------------------------
    # Deliberately ragged: any row may be absent (no lat/lon, no CRS, no elevation), so a
    # shorter list simply fills the cell from the top rather than leaving labelled blanks.
    for row, text in zip(rows(4, 1), _site_rows(site), strict=False):
        label(edges[1] + pad, row, text, 6.0)

    # --- cell 3: preparer, project number, scale, date, and the issue stamp ---------
    r = rows(5, 2)
    label(edges[2] + pad, r[0], f"PROJECT NO  {_project_number(project)}", 6.0)
    label(edges[2] + pad, r[1], f"DRAWN BY    {_preparer(project)}", 6.0)
    # CHECKED BY is blank because nobody has checked it. A pre-filled name on a line whose
    # whole purpose is to record a human act would be a forgery of that act — the same
    # reasoning that keeps the seal box empty.
    label(edges[2] + pad, r[2], "CHECKED BY  ______________", 6.0)
    label(edges[2] + pad, r[3], f"SCALE  {scale_label}      "
                                f"DATE  {date.today().isoformat()}", 6.0)
    label(edges[2] + pad, r[4], _ISSUE.get(), 7.5, "bold", _issue_color(_ISSUE.get()))

    # --- cell 4: the revision block ------------------------------------------------
    # A real block with ruled rows and a header, empty. It replaces a hard-coded "REV —",
    # which said there is no revision system rather than that there are no revisions yet.
    # The engine cannot fill it: a revision is an issue to somebody, which is a human act.
    r = rows(4, 3)
    label(edges[3] + pad, r[0], "REV  DATE        DESCRIPTION", 5.5, "bold")
    for row in r[1:]:
        ax.plot([cells[3][0] + pad, cells[3][1] - pad], [row - 0.055, row - 0.055],
                color="#999999", linewidth=0.3)

    # --- cell 5: the seal box ------------------------------------------------------
    _draw_seal_cell(ax, cells[4], pad, seal, label)

    # --- cell 6: sheet number and title --------------------------------------------
    r = rows(3, 5)
    label(edges[5] + pad, r[0], number, 13.0, "bold")
    # The cell is as wide as the paper made it, so that — not a constant — is the limit.
    # A fixed 46 was a ledger number: it clipped a title at the same place on 24x36, where
    # this cell is more than twice as wide and had the room to print it whole.
    columns = wrap_columns_for(cells[5][1] - cells[5][0] - 2 * pad, 6.5)
    label(edges[5] + pad, r[2], _shorten(title, columns), 6.5)


def _draw_seal_cell(ax, cell, pad: float, seal: SealBlock | None, label) -> None:
    """The reserved seal area, and — on a sheet that carries it — the ruled instrument.

    An outlined reserved area and a caption, and the engine still never DRAWS a stamp.
    ``schedules/structural.py`` puts it plainly: drawing a stamp would be forging one. What
    it does draw is the four lines Minn. R. 1800.4200 subp. 4 names, which is the thing a
    licensee actually signs. SIGNATURE stays ruled even under ``--sealed``: a recorded seal
    is a fact about a document somebody else signed, not a signature this engine may make.
    """
    from matplotlib.patches import Rectangle

    seal_l, seal_r, seal_top, seal_bot = cell
    box_x0, box_x1 = seal_l + pad, seal_r - pad
    if seal is None:
        ax.add_patch(Rectangle((box_x0, seal_bot + pad), box_x1 - box_x0,
                               (seal_top - seal_bot) - 2 * pad,
                               fill=False, edgecolor="#999999", linewidth=0.4,
                               linestyle=(0, (3, 2))))
        ax.text((box_x0 + box_x1) / 2.0, (seal_top + seal_bot) / 2.0, "SEAL", fontsize=6.0,
                family="monospace", va="center", ha="center", color="#999999")
        return

    # Top half: the dashed reserved area a physical or electronic stamp lands in.
    stamp_bot = seal_bot + (seal_top - seal_bot) * 0.46
    ax.add_patch(Rectangle((box_x0, stamp_bot), box_x1 - box_x0,
                           (seal_top - pad) - stamp_bot,
                           fill=False, edgecolor="#999999", linewidth=0.4,
                           linestyle=(0, (3, 2))))
    ax.text((box_x0 + box_x1) / 2.0, (seal_top - pad + stamp_bot) / 2.0, "SEAL",
            fontsize=6.0, family="monospace", va="center", ha="center", color="#999999")

    # Bottom half: the four lines, filled from the signoff where there is one.
    filled = {"NAME": seal.engineer, "LICENSE NO.": seal.license, "DATE": seal.sealed_on}
    span = stamp_bot - (seal_bot + pad)
    step = span / 4.6
    y = stamp_bot - step * 0.9
    for line in ("NAME", "LICENSE NO.", "DATE", "SIGNATURE"):
        value = filled.get(line)
        label(box_x0, y, f"{line} {value}" if value else f"{line} ____________", 5.0)
        y -= step
    label(box_x0, y, "SEE S-001 FOR CERTIFICATION", 4.5, color="#555555")


def _site_rows(site) -> list[str]:
    rows: list[str] = []
    lat, lon = getattr(site, "lat", None), getattr(site, "lon", None)
    if lat is not None and lon is not None:
        rows.append(f"SITE  {lat:.5f}, {lon:.5f}")
    crs = getattr(site, "crs", None)
    if crs:
        rows.append(f"CRS   {crs}")
    elevation = getattr(site, "elevation", None)
    if elevation is not None:
        with suppress(AttributeError):
            rows.append(f"ELEV  {elevation.meters:,.1f} m")
    return rows


def _project_address(project, site) -> list[str]:
    """Up to two lines of street address, or ``[]``.

    A permit set names the property it is for. Nothing here is invented: an address the
    model does not carry prints as nothing at all, because a plausible-looking address on a
    permit drawing is worse than a missing one.
    """
    for holder in (project, site):
        text = getattr(holder, "address", None)
        if text:
            return [line.strip() for line in str(text).splitlines() if line.strip()][:2]
    return []


def _project_number(project) -> str:
    """The project number a reviewer files the set under.

    Falls back to the first eight characters of ``project_uuid``, which is stable, unique
    and already in the model — a set with no number at all cannot be filed.
    """
    number = getattr(project, "number", None)
    if number:
        return str(number)
    uuid = str(getattr(project, "project_uuid", "") or "")
    return uuid[:8].upper() if uuid else "—"


def _preparer(project) -> str:
    """Who prepared the set. The engine did, unless the project names somebody."""
    for field in ("preparer", "firm", "architect"):
        value = getattr(project, field, None)
        if value:
            return str(value)[:16]
    return "TYPE:HAUS"


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"
