"""What ``haus handoff`` draws for the engineer: the structural sheets and a key plan.

A PE signs a paper set, and a tag like ``PT-SG-BF3`` means nothing until it can be found.
Two files answer that, both byte-deterministic (no creation date, no producer clock):

* ``drawings/structural_sheets.pdf`` — the permit set's own S-sheets (the sheet ids that
  ``03-open-items.md`` and the register cite), composed by the same sheet index.
* ``drawings/key_plan.pdf`` — one plan per level, every engineered item's element drawn in
  its kind's colour and labelled by tag, with a 10 ft grid and a tag table.

:func:`item_locations` is the same lookup as data (level and plan position per item), for a
"where" column in the register.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

M_TO_FT = 1.0 / 0.3048
GRID_FT = 10.0
#: Matplotlib omits a metadata key set to ``None`` — here, the only clock in a PDF.
_PDF_META = {"CreationDate": None, "Creator": "Type:Haus", "Producer": "Type:Haus"}
_PAGE_IN = (36.0, 24.0)  # ARCH D landscape, like the structural sheets
_PALETTE = ("#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf", "#8c564b",
            "#e377c2", "#bcbd22", "#7f7f7f", "#0b3d91", "#a50f15", "#006d2c", "#54278f",
            "#b35806", "#08519c", "#cb181d", "#31a354", "#756bb1", "#e6550d")


@dataclass(frozen=True)
class Geom:
    """One piece of plan geometry: a wall's axis (``line``) or a closed outline (``poly``)."""

    shape: str
    points: tuple[tuple[float, float], ...]
    storey: str

    @property
    def centre(self) -> tuple[float, float]:
        xs, ys = [p[0] for p in self.points], [p[1] for p in self.points]
        return (sum(xs) / len(xs), sum(ys) / len(ys))


@dataclass(frozen=True)
class Location:
    """Where an item is: its level, and the plan position of its key element (feet)."""

    level: str
    x_ft: float
    y_ft: float


# --- structural sheets ---------------------------------------------------------------------

def write_structural_sheets(model, preferences, profile, house_dir: Path, report,
                            path: Path) -> list[str]:
    """The permit set's S-sheets as one PDF at ARCH D; returns their sheet numbers.

    Composed from ``build_sheet_index`` like ``write_permit_set`` and filtered to the S
    discipline, so a sheet id in the register is a page in this file.
    """
    from matplotlib.backends.backend_pdf import PdfPages

    from typehaus.emit.draw.paper import ARCH_D
    from typehaus.emit.draw.pdf_writer import _close
    from typehaus.emit.draw.sheet_writer import compose_sheet, set_paper
    from typehaus.emit.draw.sheets import build_sheet_index
    from typehaus.emit.draw.title_block import (
        NOT_FOR_CONSTRUCTION,
        seal_block_for,
        set_issue_status,
        set_seal_block,
    )

    sheets = [sheet for sheet in build_sheet_index(
        model, preferences, profile, paper=ARCH_D, house_dir=house_dir, sets="permit",
        report=report) if sheet.number.startswith("S-")]
    path.parent.mkdir(parents=True, exist_ok=True)
    with (set_issue_status(NOT_FOR_CONSTRUCTION), set_seal_block(
            seal_block_for(profile, None)), set_paper(ARCH_D),
          PdfPages(path, metadata=_PDF_META) as pdf):
        for sheet in sheets:
            if sheet.page is not None:
                sheet.page(pdf, model, sheet.number, sheet.title)
            elif sheet.scene is not None:
                fig = compose_sheet(sheet.scene(model), sheet, model, size=sheet.size)
                pdf.savefig(fig)
                _close(fig)
    return [sheet.number for sheet in sheets]


# --- locating items ------------------------------------------------------------------------

def _tag_index(model) -> dict[str, list[Geom]]:
    """Every plan tag -> its geometry, across the collections an item's elements live in."""
    index: dict[str, list[Geom]] = {}
    walls = {wall.tag: wall for wall in model.walls}
    for wall in model.walls:
        index.setdefault(wall.tag, []).append(
            Geom("line", tuple(tuple(p) for p in wall.axis), wall.storey))
    for solid in model.solids:
        if len(solid.outline) >= 3:
            index.setdefault(solid.tag, []).append(
                Geom("poly", tuple(tuple(p) for p in solid.outline), solid.storey))
    for floor in model.floors:
        if len(floor.deck_outline) >= 3:
            index.setdefault(floor.tag, []).append(
                Geom("poly", tuple(tuple(p) for p in floor.deck_outline), floor.storey))
    for roof in model.roofs:
        if len(roof.footprint) >= 3:
            index.setdefault(roof.tag, []).append(
                Geom("poly", tuple(tuple(p) for p in roof.footprint), roof.storey))
    for opening in model.openings:
        host = walls.get(opening.host_wall)
        if host is not None:
            index.setdefault(opening.tag, []).append(
                Geom("line", tuple(tuple(p) for p in host.axis), host.storey))
    return index


def _levels(model) -> dict[str, str]:
    """Storey tag -> the tag of the level (shared datum) it is drawn on."""
    return {storey.tag: primary.tag
            for primary, here in model.plan.levels() for storey in here}


def _placed(model, records: Sequence) -> list[tuple[object, list[Geom], Geom | None]]:
    """``(record, geometry of every element tag, geometry of the key)`` per record."""
    index = _tag_index(model)
    out = []
    for record in records:
        tags = tuple(dict.fromkeys((record.key, *record.element_tags)))
        geoms = [g for tag in tags for g in index.get(tag, ())]
        keyed = index.get(record.key) or geoms
        out.append((record, geoms, keyed[0] if keyed else None))
    return out


def item_locations(model, records: Iterable) -> dict[str, Location]:
    """``item_id -> Location`` for every record whose key element is in the plan."""
    levels = _levels(model)
    result: dict[str, Location] = {}
    for record, _geoms, key in _placed(model, list(records)):
        if key is not None:
            x, y = key.centre
            result[record.item_id] = Location(levels.get(key.storey, key.storey),
                                              round(x * M_TO_FT, 1), round(y * M_TO_FT, 1))
    return result


# --- the key plan --------------------------------------------------------------------------

def write_key_plan(model, records: Sequence, path: Path) -> list[str]:
    """One page per level that holds an item; returns the ``K-n`` sheet ids written."""
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.figure import Figure

    levels = _levels(model)
    placed = _placed(model, list(records))
    kinds = sorted({record.kind for record in records})
    colour = {kind: _PALETTE[i % len(_PALETTE)] for i, kind in enumerate(kinds)}
    order = [primary.tag for primary, _ in model.plan.levels()]
    by_level: dict[str, list] = {}
    unlocated = []
    for record, geoms, key in placed:
        if key is None:
            unlocated.append(record)
        else:
            by_level.setdefault(levels.get(key.storey, key.storey), []).append(
                (record, geoms, key))
    path.parent.mkdir(parents=True, exist_ok=True)
    ids: list[str] = []
    with PdfPages(path, metadata=_PDF_META) as pdf:
        for level in sorted(by_level, key=lambda t: order.index(t) if t in order else 99):
            ids.append(f"K-{len(ids) + 1}")
            fig = Figure(figsize=_PAGE_IN)
            _draw_level(fig, model, level, by_level[level], colour, levels,
                        f"{ids[-1]}  Key plan — level {level}")
            pdf.savefig(fig)
        if unlocated or not ids:
            ids.append(f"K-{len(ids) + 1}")
            fig = Figure(figsize=_PAGE_IN)
            _draw_unlocated(fig, unlocated, f"{ids[-1]}  Items with no plan position")
            pdf.savefig(fig)
    return ids


def _draw_level(fig, model, level: str, entries: Sequence, colour: Mapping[str, str],
                levels: Mapping[str, str], title: str) -> None:
    from matplotlib.patches import Polygon

    ax = fig.add_axes((0.04, 0.06, 0.70, 0.86))
    here = {tag for tag, primary in levels.items() if primary == level}
    for floor in model.floors:
        if floor.storey in here and len(floor.deck_outline) >= 3:
            ax.add_patch(Polygon([(x * M_TO_FT, y * M_TO_FT) for x, y in floor.deck_outline],
                                 closed=True, fc="#f1f1ee", ec="#c9c9c4", lw=0.4, zorder=1))
    for wall in model.walls:
        if wall.storey in here:
            (x0, y0), (x1, y1) = wall.axis[0], wall.axis[-1]
            ax.plot([x0 * M_TO_FT, x1 * M_TO_FT], [y0 * M_TO_FT, y1 * M_TO_FT],
                    color="#9a9a96", lw=0.9, solid_capstyle="butt", zorder=2)
    rows: dict[str, list[str]] = {}
    for record, geoms, key in entries:
        for geom in geoms:
            if geom.storey not in here:
                continue
            pts = [(x * M_TO_FT, y * M_TO_FT) for x, y in geom.points]
            if geom.shape == "poly":
                ax.add_patch(Polygon(pts, closed=True, fc=colour[record.kind], alpha=0.55,
                                     ec=colour[record.kind], lw=0.6, zorder=4))
            else:
                ax.plot([pts[0][0], pts[-1][0]], [pts[0][1], pts[-1][1]],
                        color=colour[record.kind], lw=2.4, alpha=0.8,
                        solid_capstyle="butt", zorder=4)
        x, y = key.centre
        ax.annotate(record.key, (x * M_TO_FT, y * M_TO_FT), fontsize=8, zorder=6,
                    ha="center", va="center",
                    bbox={"boxstyle": "square,pad=0.1", "fc": "white", "ec": "none",
                          "alpha": 0.75})
        rows.setdefault(record.key, []).append(record.kind)
    ax.set_aspect("equal")
    ax.autoscale_view()
    _grid(ax)
    fig.text(0.04, 0.955, title, fontsize=22, weight="bold")
    fig.text(0.04, 0.93, "NOT FOR CONSTRUCTION. Engineered items outside the prescriptive "
             "tables; model plan coordinates in feet, 10 ft grid.", fontsize=11)
    _table(fig, rows, colour)


def _grid(ax) -> None:
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    ax.set_xticks([GRID_FT * k for k in range(math.floor(x0 / GRID_FT),
                                              math.ceil(x1 / GRID_FT) + 1)])
    ax.set_yticks([GRID_FT * k for k in range(math.floor(y0 / GRID_FT),
                                              math.ceil(y1 / GRID_FT) + 1)])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.grid(True, color="#dddddd", lw=0.4, zorder=0)
    ax.tick_params(labelsize=9)


def _table(fig, rows: Mapping[str, Sequence[str]], colour: Mapping[str, str]) -> None:
    """The tag -> kinds list down the right-hand side, a swatch per kind in the legend."""
    y = 0.92
    fig.text(0.76, y, "Tag  —  engineered kinds", fontsize=12, weight="bold")
    for tag in sorted(rows):
        y -= 0.0155
        kinds = sorted(set(rows[tag]))
        fig.text(0.76, y, f"{tag}  —  {', '.join(kinds)}", fontsize=9, color=colour[kinds[0]])
    fig.text(0.76, 0.04, "Colour is the first kind listed for the tag; a tag under several "
             "kinds appears once.", fontsize=8, style="italic")


def _draw_unlocated(fig, records: Sequence, title: str) -> None:
    fig.text(0.04, 0.94, title, fontsize=22, weight="bold")
    lines = [f"{record.item_id}" for record in records] or ["(every item has a plan position)"]
    for i, line in enumerate(lines):
        fig.text(0.04, 0.9 - i * 0.02, line, fontsize=11)


# --- the evidence folder -------------------------------------------------------------------

def evidence_files(house_dir: Path) -> list[tuple[str, Path]]:
    """``(bundle path, source)`` for every tracked review file under ``notes/``.

    Reports, scripts, supplier run reports and verifier calcs dropped under
    ``notes/engineering_review_*`` (and that review's summary note) ride in the bundle's
    ``evidence/`` so the engineer reads what the owner's reviewers found.
    """
    notes = house_dir / "notes"
    found: list[tuple[str, Path]] = []
    if not notes.is_dir():
        return found
    for top in sorted(notes.glob("engineering_review_*")):
        files = sorted(top.rglob("*")) if top.is_dir() else [top]
        for source in files:
            relative = source.relative_to(notes)
            if (not source.is_file() or source.suffix == ".pyc"
                    or any(part.startswith(".") or part == "__pycache__"
                           for part in relative.parts)):
                continue
            found.append(("evidence/" + relative.as_posix(), source))
    return found
