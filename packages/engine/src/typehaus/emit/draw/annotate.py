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

from typehaus.emit.draw.typography import (
    CHAR_ASPECT as _CHAR_ASPECT,
)
from typehaus.emit.draw.typography import (
    LEADER_WRAP_COLUMNS,
)
from typehaus.emit.draw.typography import (
    LINE_SPACING as _LINE_SPACING,
)

__all__ = ["DODGE_GAP", "LEADER_WRAP_COLUMNS", "LabelSpec", "PlacedLabel", "dodge",
           "label_box", "leader_box", "place_column", "text_extent", "wrap_label"]

# Vertical air kept between two label boxes after dodging, model inches.
DODGE_GAP = 0.5

# Minimum air between successive rows *within* a placed column, model inches. Smaller
# than DODGE_GAP so a single-line ladder keeps its authored uniform rung step (2.6" at
# height 1.6) instead of every rung being pushed apart by the estimate's padding.
_COLUMN_PAD = 0.3


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
    height: float
    box: tuple[float, float, float, float]


def text_extent(text: str, height: float) -> tuple[float, float]:
    """Estimated (width, height) of a text block, model inches."""
    lines = text.split("\n")
    width = max(len(line) for line in lines) * height * _CHAR_ASPECT
    return width, height * _LINE_SPACING * len(lines)


def label_box(at: tuple[float, float], text: str, height: float,
              align: str) -> tuple[float, float, float, float]:
    """Estimated bbox of a text block anchored at ``at`` (va=center convention)."""
    width, block_h = text_extent(text, height)
    if align == "right":
        u0 = at[0] - width
    elif align == "center":
        u0 = at[0] - width / 2
    else:
        u0 = at[0]
    return (u0, at[1] - block_h / 2, u0 + width, at[1] + block_h / 2)


def leader_box(node) -> tuple[float, float, float, float]:
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
    return label_box(at, text, getattr(node, "height", 1.6), align)


def place_column(entries: list[LabelSpec], x: float, z_top: float, step: float,
                 height: float = 1.6, align: str = "left") -> list[PlacedLabel]:
    """Stack labels down a column at ``x``, first row anchored at ``z_top``.

    Each row advances by at least ``step``, growing whenever two adjacent text blocks
    would otherwise touch — so a wrapped multi-line callout pushes its neighbours clear
    while a single-line ladder keeps the uniform ``step``. Deterministic: order in =
    order down the column.
    """
    halves = [text_extent(spec.text, height)[1] / 2 for spec in entries]
    out: list[PlacedLabel] = []
    z = None
    for index, spec in enumerate(entries):
        if z is None:
            z = z_top - halves[0]  # first block's top sits at z_top
        else:
            z -= max(step, halves[index - 1] + _COLUMN_PAD + halves[index])
        at = (x, z)
        out.append(PlacedLabel(spec=spec, at=at, align=align, height=height,
                               box=label_box(at, spec.text, height, align)))
    return out


def dodge(placed: list[PlacedLabel], fixed: tuple = (),
          gap: float = DODGE_GAP) -> list[PlacedLabel]:
    """Cheap one-pass vertical-overlap resolver over estimated label boxes.

    Boxes are visited top-down (sorted by box top, descending); a box that intersects an
    already-settled box — or any ``fixed`` obstacle box — is pushed straight down until it
    clears. Deterministic stacking, NOT force-directed: input order ties are broken by
    (u0, text) so the same scene always dodges the same way. The returned list preserves
    the input order (only anchors/boxes move).
    """
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
