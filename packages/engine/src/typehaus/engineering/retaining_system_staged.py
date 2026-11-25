"""Staged backfill: the court is a structure while it is being filled (free body §13).

The completed body's sliding row assumes every retained side full. While they are filled, a
side may stand higher than another. Each retained side is taken at a fill fraction f of its
H on a grid (2" steps under RULE_FT, else twelfths): earth thrust ½ K0 γ (H f)² over that
side's projected width (the apron comes later), the soil on its heel to its fill line, the
corner squares at the lower of their two sides. The spliced braced walls stand EMPTY until
their tops are braced and add their concrete only, as in the completed body.

**The permitted sequence is part of the design**: the row grades the worst stage the rule
allows — no retained side more than :data:`RULE_FT` above another (else :data:`RULE` of its
height) — and the drawing's backfill note (AN-SG-BACKFILL) states that rule.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from typehaus.engineering.retaining_system_body import STONE_PCF, Body, _exterior

#: The rule as a fraction of H on a grid of twelfths, graded only when RULE_FT is None.
RULE = 0.5
_GRID = tuple(i / 12.0 for i in range(13))
#: The field rule graded (AN-SG-BACKFILL, free body §15e): no retained side more than 3'-0"
#: above another. The grid steps 2" down from full height, so a whole-foot difference lies on
#: it. The note prints four 8" lifts (2'-8"), 4" inside it.
RULE_FT: float | None = 3.0
_STEP_FT = 2.0 / 12.0


def _rule_and_grid(height_ft: float) -> tuple[float, tuple[float, ...]]:
    if RULE_FT is None:
        return RULE, _GRID
    step = _STEP_FT / height_ft
    grid = {max(0.0, 1.0 - k * step) for k in range(int(1.0 / step) + 2)} | {0.0}
    return RULE_FT / height_ft + 1e-9, tuple(sorted(grid))


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


@dataclass(frozen=True)
class Stage:
    """One fill stage, every term the sheet prints (``staged_steps``)."""

    fills: tuple[float, ...]
    #: Per push: ``(tag, unit direction, fill height ft, thrust lb)``.
    thrusts: tuple[tuple[str, tuple[float, float], float, float], ...]
    rx: float
    ry: float
    demand: float
    #: Everything but the heel soil (concrete, strut, stems, spliced walls), lb.
    rest: float
    credit: float
    #: Heel soil per region: ``(label, soil sf, drain-column sf, rise ft, column rise ft)``.
    soil_parts: tuple[tuple[str, float, float, float, float], ...]
    soil: float
    weight: float
    friction: float
    fs: float


def staged(body: Body, members, footing_top_ft: float, stem_ft: float,  # type: ignore[no-untyped-def]
           key: tuple[float, tuple[float, float]] | None = None
           ) -> tuple[float, float, float, Stage]:
    """``(worst FS under the rule, worst with one side empty, worst under the rule with the
    spliced braced walls' concrete left out, the governing stage under the rule)``. ``key``:
    a resistance ``(K lb, unit direction)`` that acts along one direction only
    (``directional_fs``)."""
    regions, rest = _split(body, members, stem_ft)
    pushes = list(body.pushes)
    heights = [p.top_ft - body.plane_ft for p in pushes]
    depth = footing_top_ft - body.plane_ft
    column = next((p for p in body.prisms if p.label == "heel soil:drain column"), None)
    col_h = column.z1_ft - column.z0_ft if column else 0.0

    def stage(fills: tuple[float, ...], credit: float) -> Stage:
        rx = ry = 0.0
        thrusts = []
        for p, f, h in zip(pushes, fills, heights, strict=True):
            t = 0.5 * p.efp * (h * f) ** 2 * p.width_ft
            thrusts.append((p.tag, p.direction, h * f, t))
            rx += t * p.direction[0]
            ry += t * p.direction[1]
        demand = (rx * rx + ry * ry) ** 0.5
        soil = 0.0
        parts = []
        for area, col, keys in regions:
            rise = max(0.0, min(heights[k] * fills[k] for k in keys) - depth)
            col_rise = min(rise, col_h)
            soil += area * body.soil_pcf * rise + col * (STONE_PCF - body.soil_pcf) * col_rise
            parts.append((" + ".join(pushes[k].tag for k in keys), area, col, rise, col_rise))
        weight = rest - credit + soil
        friction = body.friction * weight
        if demand < 1.0:
            fs = float("inf")
        elif key is not None:
            fs = directional_fs((rx, ry), friction, *key)
        else:
            fs = friction / demand
        return Stage(fills, tuple(thrusts), rx, ry, demand, rest, credit, tuple(parts),
                     soil, weight, friction, fs)

    spliced = sum(p.weight() for p in body.prisms
                  if p.label.partition(":")[2] in body.spliced)
    rule, steps = _rule_and_grid(max(heights))
    grid = list(itertools.product(steps, repeat=len(pushes)))
    ruled = [c for c in grid if max(c) - min(c) <= rule + 1e-9 and max(c) > 0]
    governing = min((stage(c, 0.0) for c in ruled), key=lambda s: s.fs)
    empty = min(stage(c, 0.0).fs for c in grid if max(c) > 0)
    loop_only = min(stage(c, spliced).fs for c in ruled)
    return governing.fs, empty, loop_only, governing



def directional_fs(thrust, friction: float, k: float, direction) -> float:  # type: ignore[no-untyped-def]
    """FS where friction (a disc) and a one-way resistance ``k`` along ``direction`` resist
    the thrust vector: the root of |FS T − k d| = friction."""
    tx, ty = thrust
    tt = tx * tx + ty * ty
    if tt < 1.0:
        return float("inf")
    td = tx * direction[0] + ty * direction[1]
    disc = (k * td) ** 2 - tt * (k * k - friction * friction)
    return (k * td + max(0.0, disc) ** 0.5) / tt
