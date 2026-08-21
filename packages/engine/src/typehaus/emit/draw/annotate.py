"""Shared label-layout helpers for detail/section annotations (→ 20 §Drawing IR).

Both the layer-label ladder (``section._emit_wall_cut``) and the continuity seed-callout
column (``details._seed_nodes``) place stacks of leadered text beside a cut. Doing that
placement here — IR-side, once — is what keeps the UI SVG renderer and the matplotlib
PDF/PNG writer in agreement: they both draw the same pre-laid-out scene.

Text extents are *estimates* (monospace advance width as a fraction of cap height), the
same reservation convention ``pdf_writer._scene_bounds`` uses. The layout is deterministic
stacked-column placement plus a cheap one-pass vertical dodge — never force-directed, so
the same model always renders the same drawing (golden-testable).
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, replace

from typehaus.emit.draw import typography
from typehaus.emit.draw.typography import (
    CHAR_ASPECT as _CHAR_ASPECT,
)
from typehaus.emit.draw.typography import (
    LEADER_WRAP_COLUMNS,
    TEXT_PT,
)
from typehaus.emit.draw.typography import (
    LINE_SPACING as _LINE_SPACING,
)

__all__ = ["COLUMN_PAD_PT", "DODGE_GAP_PT", "LEADER_WRAP_COLUMNS", "LabelSpec",
           "PlacedLabel", "dodge", "label_box", "leader_box", "model_in_per_pt",
           "place_column", "text_extent", "wrap_label"]

# What a point was worth in model inches before paper space: the ladder authored 1.6"
# lettering and meant TEXT_PT. Every frameless caller (a plain building section, a plan)
# still measures in this, so its drawings are unchanged; only a scene that has *chosen* a
# sheet converts through the real scale, and there the same label comes out about half the
# size, which is the oversize lettering being fixed.
LEGACY_IN_PER_PT = 1.6 / TEXT_PT


def model_in_per_pt(scale: float | None) -> float:
    """Model inches per printed point, or the frameless convention when ``scale`` is None."""
    return LEGACY_IN_PER_PT if scale is None else typography.model_in_per_pt(scale)

# Vertical air kept between two label boxes after dodging, **points**. It was 0.5 model
# inches, which is the same thing at the frameless conversion — a gap is a property of the
# lettering it separates, not of the building.
DODGE_GAP_PT = 0.5 / LEGACY_IN_PER_PT

# Minimum air between successive rows *within* a placed column, points. Smaller than
# DODGE_GAP_PT so a single-line ladder keeps its authored uniform rung step instead of every
# rung being pushed apart by the estimate's padding.
COLUMN_PAD_PT = 0.3 / LEGACY_IN_PER_PT


def wrap_label(text: str, columns: int = LEADER_WRAP_COLUMNS) -> str:
    """Wrap leader note text to ``columns``; pre-existing line breaks are respected."""
    out: list[str] = []
    for line in text.split("\n"):
        out.extend(textwrap.wrap(line, columns) or [line])
    return "\n".join(out)


@dataclass(frozen=True)
class LabelSpec:
    """One label to place: its (possibly multi-line) text and the point it describes.

    ``target`` is the model-space (u, z) the leader points at — ``None`` for plain text
    that has nothing to point to. ``key`` is opaque provenance (dedupe key, uid…) the
    caller reads back off the placed result.
    """

    text: str
    target: tuple[float, float] | None = None
    key: object = None


@dataclass(frozen=True)
class PlacedLabel:
    """A label with its resolved text anchor and estimated bbox (u0, z0, u1, z1).

    ``at`` follows the writers' convention: the text block is vertically centred on the
    anchor (matplotlib ``va="center"``) and grows left/right per ``align``.
    """

    spec: LabelSpec
    at: tuple[float, float]
    align: str  # "left" | "right"
    height_pt: float
    box: tuple[float, float, float, float]  # model inches


def text_extent(text: str, height_pt: float) -> tuple[float, float]:
    """Estimated (width, height) of a text block, **points** — what it prints as.

    This is the line the whole paper-space change turns on. Lettering is a printed size, so
    its extent is a paper measurement; converting to model inches is the caller's problem
    and depends on the scale the sheet chose. Estimating in model inches instead is what let
    the ladder reserve room for a 1.6" label and then print a 3" one.
    """
    lines = text.split("\n")
    width = max(len(line) for line in lines) * height_pt * _CHAR_ASPECT
    return width, height_pt * _LINE_SPACING * len(lines)


def label_box(at: tuple[float, float], text: str, height_pt: float,
              align: str, scale: float | None = None) -> tuple[float, float, float, float]:
    """Estimated bbox of a text block anchored at ``at`` (va=center convention).

    Returns **model inches**, because that is what the ladder and :func:`dodge` place in —
    but sized from ``height_pt`` at ``scale``. Reservation equals reality only if the two
    are the same number, and this is where they meet.
    """
    per_pt = model_in_per_pt(scale)
    width_pt, block_pt = text_extent(text, height_pt)
    width, block_h = width_pt * per_pt, block_pt * per_pt
    if align == "right":
        u0 = at[0] - width
    elif align == "center":
        u0 = at[0] - width / 2
    else:
        u0 = at[0]
    return (u0, at[1] - block_h / 2, u0 + width, at[1] + block_h / 2)


def leader_box(node, scale: float | None = None) -> tuple[float, float, float, float]:
    """Estimated bbox of an existing ``Leader``/``Text`` IR node.

    Mirrors ``pdf_writer._leader_align``: a note left of its target grows leftward.
    Used to hand a scene's already-placed labels to :func:`dodge` as fixed obstacles.
    """
    to = getattr(node, "to", None)
    at = getattr(node, "at", None) or getattr(node, "anchor", None)
    text = getattr(node, "text", None) or getattr(node, "content", "")
    if isinstance(to, tuple) and isinstance(at, tuple):
        align = "right" if at[0] < to[0] else "left"
    else:
        align = getattr(node, "align", "left")
    height_pt = getattr(node, "height_pt", None)
    if height_pt is not None:
        return label_box(at, text, height_pt, align, scale)
    # A node that never took a printed size: its ``height`` is model inches, so convert it
    # back into points through the same scale rather than mixing the two units.
    return label_box(at, text, getattr(node, "height", 1.6) / model_in_per_pt(scale),
                     align, scale)


def place_column(entries: list[LabelSpec], x: float, z_top: float, step_pt: float,
                 height_pt: float = TEXT_PT, align: str = "left",
                 scale: float | None = None) -> list[PlacedLabel]:
    """Stack labels down a column at ``x``, first row anchored at ``z_top``.

    Each row advances by at least ``step``, growing whenever two adjacent text blocks
    would otherwise touch — so a wrapped multi-line callout pushes its neighbours clear
    while a single-line ladder keeps the uniform ``step``. Deterministic: order in =
    order down the column.
    """
    per_pt = model_in_per_pt(scale)
    halves = [text_extent(spec.text, height_pt)[1] / 2 for spec in entries]
    out: list[PlacedLabel] = []
    z = None
    for index, spec in enumerate(entries):
        if z is None:
            z = z_top - halves[0] * per_pt  # first block's top sits at z_top
        else:
            z -= max(step_pt, halves[index - 1] + COLUMN_PAD_PT + halves[index]) * per_pt
        at = (x, z)
        out.append(PlacedLabel(spec=spec, at=at, align=align, height_pt=height_pt,
                               box=label_box(at, spec.text, height_pt, align, scale)))
    return out


def dodge(placed: list[PlacedLabel], fixed: tuple = (),
          gap_pt: float = DODGE_GAP_PT, scale: float | None = None) -> list[PlacedLabel]:
    """Cheap one-pass vertical-overlap resolver over estimated label boxes.

    Boxes are visited top-down (sorted by box top, descending); a box that intersects an
    already-settled box — or any ``fixed`` obstacle box — is pushed straight down until it
    clears. Deterministic stacking, NOT force-directed: input order ties are broken by
    (u0, text) so the same scene always dodges the same way. The returned list preserves
    the input order (only anchors/boxes move).
    """
    gap = gap_pt * model_in_per_pt(scale)
    order = sorted(range(len(placed)),
                   key=lambda i: (-placed[i].box[3], placed[i].box[0],
                                  placed[i].spec.text))
    taken: list[tuple[float, float, float, float]] = [tuple(b) for b in fixed]
    out = list(placed)
    for i in order:
        label = out[i]
        u0, z0, u1, z1 = label.box
        moved = True
        while moved:
            moved = False
            for (fu0, fz0, fu1, fz1) in taken:
                if u0 < fu1 and fu0 < u1 and z0 < fz1 and fz0 < z1:
                    shift = (fz0 - gap) - z1  # new top sits below the obstacle
                    z0 += shift
                    z1 += shift
                    moved = True
        if z1 != label.box[3]:
            dz = z1 - label.box[3]
            label = replace(label, at=(label.at[0], label.at[1] + dz),
                            box=(u0, z0, u1, z1))
            out[i] = label
        taken.append((u0, z0, u1, z1))
    return out
