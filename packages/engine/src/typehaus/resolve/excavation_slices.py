"""Level-by-level slicing of an over-dig: the arithmetic behind ``resolve/excavation.py``.

Pure plan geometry and elevations in, volumes and level prisms out, so a hand rectangle can
check it without a house around it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shapely.geometry import JOIN_STYLE, Polygon

from typehaus.resolve.overlay import difference, intersection, union_all
from typehaus.resolve.wall_column import parts

NATIVE, CAP = "backfill_native", "backfill_cap"
_MITRE = JOIN_STYLE.mitre
_EPS_Z = 1e-6
#: Breaks closer than this merge: a sliver slice is drawing noise, not accuracy.
_MIN_SLICE_M = 0.5 * 0.0254


@dataclass(frozen=True)
class Hole:
    """``digs``: ``(core, floor, top, sloped)`` per bed — a sloped bed's dig lays back from
    its core; an interior bed's is its core alone. ``interiors``: ``(plan, underside)`` of
    each floor inside the outline. ``obstacles``: ``(plan, z0, z1)`` standing in the hole.
    ``toe``: a plumb lower face, cut only where a dig is no deeper than ``toe_max_depth``."""

    outline: Any
    digs: list[tuple[Any, float, float, bool]]
    interiors: list[tuple[Any, float]]
    obstacles: list[tuple[Any, float, float]]
    grade: float
    z_struct: float
    working_space: float
    h_per_v: float
    cap: float
    toe: float = 0.0
    toe_max_depth: float = float("inf")

    def reach(self, floor: float, top: float, z: float) -> float:
        """How far a bed's dig reaches past its core at ``z``."""
        toe = self.toe if top - floor <= self.toe_max_depth + _EPS_Z else 0.0
        return self.working_space + self.h_per_v * max(z - floor - toe, 0.0)


def slice_hole(hole: Hole, marks: list[float]
               ) -> tuple[float, float, float, list[tuple[str, Polygon, float, float]]]:
    """``(cut, fill, cap, prisms)``: bank cut, placed fill and cap in m3, and the
    ``(category, plan, z0, z1)`` prisms that draw exactly what was measured."""
    cut = fill = cap = 0.0
    prisms: list[tuple[str, Polygon, float, float]] = []
    standing: dict[tuple[int, ...], Any] = {}  # consecutive slices share a set
    for za, zb in zip(marks[:-1], marks[1:], strict=True):
        zm, dz = (za + zb) / 2, zb - za
        pieces, slopes, cap_zone = [], [], []
        if zm <= hole.grade:
            if zm >= hole.z_struct:
                pieces.append(hole.outline)
            pieces.extend(p for p, z0 in hole.interiors if z0 <= zm)
        for core, bed_floor, top, sloped in hole.digs:
            if not bed_floor <= zm <= top:
                continue
            reach = hole.reach(bed_floor, top, zm)
            dig = core.buffer(reach, join_style=_MITRE) if sloped else core
            pieces.append(core)
            if sloped:
                slopes.append(dig)
            if zm > top - hole.cap:
                cap_zone.append(dig)  # the outline is subtracted from the fill below
        if slopes:
            pieces.append(difference(union_all(slopes), hole.outline))
        if not pieces:
            continue
        dug = union_all(pieces)
        cut += dug.area * dz
        active = tuple(i for i, (_p, a, b) in enumerate(hole.obstacles)
                       if a - _EPS_Z <= zm <= b + _EPS_Z)
        if active not in standing:
            standing[active] = union_all([hole.outline,
                                          *(hole.obstacles[i][0] for i in active)])
        backfill = difference(dug, standing[active])
        capped = intersection(backfill, union_all(cap_zone)) if cap_zone else Polygon()
        native = difference(backfill, capped) if cap_zone else backfill
        fill += backfill.area * dz
        cap += capped.area * dz
        for category, geometry in ((NATIVE, native), (CAP, capped)):
            prisms.extend((category, part, za, zb) for part in parts(geometry))
    return cut, fill, cap, prisms


def levels(floor: float, roof: float, step: float, breaks: list[float]) -> list[float]:
    """Slice boundaries: every break inside the hole, then no slice taller than ``step``."""
    marks = sorted({round(z, 6) for z in (floor, roof, *breaks) if floor <= z <= roof})
    out = [marks[0]]
    for z in marks[1:]:
        if z - out[-1] < _MIN_SLICE_M and z != marks[-1]:
            continue
        count = max(1, int(-(-(z - out[-1]) // step)))
        base = out[-1]
        out.extend(base + (z - base) * (k + 1) / count for k in range(count))
    return out
