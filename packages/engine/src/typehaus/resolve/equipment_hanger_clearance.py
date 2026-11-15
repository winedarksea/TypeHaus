"""A trapeze's rods, struts and bridges against the run envelopes (``resolve/mep_envelopes``).

One measure, two readers: ``resolve/equipment_hangers`` slides a strut until its parts clear,
and ``structural.equipment_hanger_clearance`` grades what is left. A rod is a riser at its
plan point; a strut or bridge a horizontal leg inset half its section at each end, so the
round cap stops at the box's end. ``mep_clearance.segment_clearance`` takes the depth, an
STRtree over the prisms the coarse filter (as in ``mep.run_interference``).
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.duct_part_solids import ROD_DIAMETER_M
from typehaus.resolve.equipment_hangers import (
    ROD_TAIL_M,
    STRUT_SECTION_M,
    ResolvedEquipmentHanger,
)
from typehaus.resolve.mep_clearance import Contact, Segment

#: Two bodies drawn to touch are drawn to touch: ``mep.run_interference``'s 1/16".
TOUCH_TOLERANCE_M = 0.0625 * M_PER_IN
_HALF_STRUT_M = STRUT_SECTION_M / 2.0


def hanger_segments(rods: list[ResolvedEquipmentHanger]) -> list[tuple[str, Segment]]:
    """``(part label, Segment)`` for every seated rod, its bridge, and each strut."""
    out: list[tuple[str, Segment]] = []
    struts: dict[tuple[str, int], list[ResolvedEquipmentHanger]] = {}
    for rod in rods:
        struts.setdefault((rod.equipment_tag, rod.strut), []).append(rod)
        if rod.hangs_from is None:
            continue
        bottom = rod.strut_top_z_m - STRUT_SECTION_M - ROD_TAIL_M
        out.append((f"rod {rod.rod}", Segment(
            f"{rod.equipment_tag}-ROD-{rod.rod}", 0, rod.point, rod.point, bottom,
            bottom + rod.rod_length_m, ROD_DIAMETER_M / 2.0, ROD_DIAMETER_M / 2.0)))
        if rod.bridge and len(rod.bridge_ends) == 2:
            z = rod.bridge_z_m + _HALF_STRUT_M
            a, b = _inset(*rod.bridge_ends, _HALF_STRUT_M)
            out.append((f"bridge {rod.rod}", Segment(
                f"{rod.equipment_tag}-BRIDGE-{rod.rod}", 0, a, b, z, z,
                _HALF_STRUT_M, _HALF_STRUT_M)))
    for (tag, strut), pair in sorted(struts.items()):
        p, q = pair[0].point, pair[-1].point
        span = math.dist(p, q)
        if span <= 0.0:
            continue
        reach = (pair[0].strut_length_m - span) / 2.0
        ux, uy = (q[0] - p[0]) / span, (q[1] - p[1]) / span
        a, b = _inset((p[0] - reach * ux, p[1] - reach * uy),
                      (q[0] + reach * ux, q[1] + reach * uy), _HALF_STRUT_M)
        z = pair[0].strut_top_z_m - _HALF_STRUT_M
        out.append((f"strut {strut}", Segment(f"{tag}-STRUT-{strut}", 0, a, b, z, z,
                                              _HALF_STRUT_M, _HALF_STRUT_M)))
    return out


def _inset(a: tuple[float, float], b: tuple[float, float],
           by: float) -> tuple[tuple[float, float], tuple[float, float]]:
    length = math.dist(a, b)
    if length <= 2.0 * by:
        mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        return mid, mid
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    return (a[0] + by * ux, a[1] + by * uy), (b[0] - by * ux, b[1] - by * uy)


class RunEnvelopes:
    """Every placed run's legs, indexed by prism footprint. Schematic raceways are left out,
    as ``mep.run_interference`` leaves them: their z is a convention, not a placement."""

    def __init__(self, model: Any) -> None:
        from shapely import STRtree

        from typehaus.resolve.mep_envelopes import (
            envelopes,
            insulation_thickness_m,
            run_polylines,
            run_sections,
        )
        from typehaus.resolve.mep_queries import schematic_conduits

        skip = set(schematic_conduits(model))
        self.prisms = [p for e in envelopes(model) if e.tag not in skip for p in e.prisms]
        self.tree = STRtree([p.footprint for p in self.prisms]) if self.prisms else None
        sections = run_sections(model)
        self.legs: dict[tuple[str, int], Segment] = {}
        for _kind, tag, path, z in run_polylines(model):
            if tag in skip or len(path) < 2 or len(z) != len(path):
                continue
            half_w, half_d, insulation = sections.get(tag, (0.0, 0.0, None))
            lag = insulation_thickness_m(insulation) or 0.0
            for leg in range(len(path) - 1):
                self.legs[(tag, leg)] = Segment(tag, leg, path[leg], path[leg + 1], z[leg],
                                                z[leg + 1], half_w + lag, half_d + lag)

    def clashes(self, part: Segment) -> dict[str, Contact]:
        """``run tag -> deepest contact`` deeper than :data:`TOUCH_TOLERANCE_M`."""
        from shapely.geometry import LineString, Point

        from typehaus.resolve.mep_clearance import segment_clearance

        if self.tree is None:
            return {}
        line = Point(part.a) if part.is_riser else LineString([part.a, part.b])
        footprint = line.buffer(part.half_w_m)
        z0 = min(part.za, part.zb) - part.half_d_m
        z1 = max(part.za, part.zb) + part.half_d_m
        out: dict[str, Contact] = {}
        for i in self.tree.query(footprint):
            prism = self.prisms[int(i)]
            if min(z1, prism.z1_m) - max(z0, prism.z0_m) <= TOUCH_TOLERANCE_M:
                continue
            if not footprint.intersects(prism.footprint):
                continue
            leg = self.legs.get((prism.tag, prism.segment))
            contact = None if leg is None else segment_clearance(part, leg)
            if contact is None or contact.score_m <= TOUCH_TOLERANCE_M:
                continue
            if prism.tag not in out or contact.score_m > out[prism.tag].score_m:
                out[prism.tag] = contact
        return out

    def worst(self, rods: list[ResolvedEquipmentHanger]) -> float:
        """The deepest overlap any part of ``rods`` makes with a run (0 when all clear)."""
        return max((c.score_m for _label, seg in hanger_segments(rods)
                    for c in self.clashes(seg).values()), default=0.0)
