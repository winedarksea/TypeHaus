"""Staged backfill: the court is a structure while it is being filled (free body §13).

The completed body's sliding row assumes every retained side full. While they are filled, a
side may stand higher than another. Each retained side is taken at a fill fraction f of its
H on a grid of twelfths: earth thrust ½ K0 γ (H f)² over that side's projected width (the
apron comes later), the soil on its heel to its fill line, the corner squares at the lower
of their two sides. The spliced braced walls stand EMPTY until their tops are braced and
add their concrete only, as in the completed body.

**The permitted sequence is part of the design**: the row grades the worst stage the rule
allows — no retained side more than :data:`RULE` of its height above another — and the
drawing's backfill note prints the generated values.
"""

from __future__ import annotations

import itertools

from typehaus.engineering.retaining_system_body import STONE_PCF, Body, _exterior

#: The field rule graded: no retained side more than half its height above another.
RULE = 0.5
_GRID = tuple(i / 12.0 for i in range(13))


def _split(body: Body, members, stem_ft: float  # type: ignore[no-untyped-def]
           ) -> tuple[list[tuple[float, float, tuple[int, ...]]], float]:
    """``([(soil sf, column sf, members it stands beyond)], weight of everything else)``."""
    soil = next(p for p in body.prisms if p.label == "heel soil")
    column = next((p for p in body.prisms if p.label == "heel soil:drain column"), None)
    halves = [_exterior(m, stem_ft) for m in members]
    regions: dict[tuple[int, ...], list[float]] = {}
    pieces = [soil.shape] if soil.shape.geom_type == "Polygon" else list(soil.shape.geoms)
    for piece in pieces:
        for keys in _keys(len(members)):
            region = piece
            for i, half in enumerate(halves):
                region = region.intersection(half) if i in keys else region.difference(half)
            if region.area > 1e-6:
                col = region.intersection(column.shape).area if column else 0.0
                acc = regions.setdefault(keys, [0.0, 0.0])
                acc[0] += region.area
                acc[1] += col
    rest = sum(p.weight() for p in body.prisms if not p.label.startswith("heel soil"))
    return [(a, c, k) for k, (a, c) in regions.items()], rest


def _keys(n: int):  # type: ignore[no-untyped-def]
    for size in range(1, n + 1):
        yield from itertools.combinations(range(n), size)


def staged(body: Body, members, footing_top_ft: float, stem_ft: float  # type: ignore[no-untyped-def]
           ) -> tuple[float, float, float]:
    """``(worst FS under the rule, worst with one side empty, worst under the rule with the
    spliced braced walls' concrete left out)``."""
    regions, rest = _split(body, members, stem_ft)
    pushes = list(body.pushes)
    heights = [p.top_ft - body.plane_ft for p in pushes]
    depth = footing_top_ft - body.plane_ft
    column = next((p for p in body.prisms if p.label == "heel soil:drain column"), None)
    col_h = column.z1_ft - column.z0_ft if column else 0.0

    def fs(fills: tuple[float, ...], credit: float) -> float:
        rx = ry = 0.0
        for p, f, h in zip(pushes, fills, heights, strict=True):
            t = 0.5 * p.efp * (h * f) ** 2 * p.width_ft
            rx += t * p.direction[0]
            ry += t * p.direction[1]
        demand = (rx * rx + ry * ry) ** 0.5
        if demand < 1.0:
            return float("inf")
        soil = 0.0
        for area, col, keys in regions:
            rise = max(0.0, min(heights[k] * fills[k] for k in keys) - depth)
            soil += area * body.soil_pcf * rise + col * (STONE_PCF - body.soil_pcf) * min(
                rise, col_h)
        return body.friction * (rest - credit + soil) / demand

    spliced = sum(p.weight() for p in body.prisms
                  if p.label.partition(":")[2] in body.spliced)
    worst = min(fs(c, 0.0) for c in itertools.product(_GRID, repeat=len(pushes))
                if max(c) - min(c) <= RULE + 1e-9 and max(c) > 0)
    empty = min(fs(c, 0.0) for c in itertools.product(_GRID, repeat=len(pushes))
                if max(c) > 0)
    loop_only = min(fs(c, spliced) for c in itertools.product(_GRID, repeat=len(pushes))
                    if max(c) - min(c) <= RULE + 1e-9 and max(c) > 0)
    return worst, empty, loop_only

