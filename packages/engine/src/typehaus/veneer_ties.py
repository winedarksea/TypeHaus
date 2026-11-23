"""Anchored masonry veneer: how far its ties reach, and IRC Table R703.8.4(1) by edition.

A leaf like ``wind.py``: it reads the resolved model and imports neither ``checks`` nor
``engineering``, so ``structural.veneer_cavity_width`` grades with it and the
``veneer_anchor`` deferral keys off the same measurement.

**Subject.** An anchored wythe: a wall whose STRUCTURE layer is masonry standing behind its
own AIRGAP layer, with no authored ``lateral_support`` (a wythe braced some other way is not
tied back). The backing is every other wall standing behind the cavity over the wythe's
height; where two do, the one sharing more of its height.

**Two measurements, across the wythe's length.** Back of the wythe to the backing's
STRUCTURE face (the stud or concrete a tie fastens into): the table's maximum, worst
station governs. Back of the wythe to the backing's nearest face (sheathing or foam): the
1" nominal airspace minimum, least station governs.

**Table R703.8.4(1)** (UpCodes: MN 2018, Colorado 2021, Oklahoma 2024, read 2026-11-23;
notes/sunken_garden_veneer_beam.md §6k). The maximum is to the BACKING; the minimum airspace
is 1" nominal from the sheathing or foam. Every row is WOOD-STUD backing here.

=================  ====================================  =======================
edition            W1.7 adjustable wire (9 ga)          W2.8 adjustable (3/16")
=================  ====================================  =======================
2015 / 2018 IRC    4 1/2"                                no row
2021 IRC           4 5/8"                                6 5/8"
2024 IRC           4 5/8"                                6 5/8"
=================  ====================================  =======================

**No row has concrete or masonry backing** (F-02), so a tie goes on a stud and never into a
concrete stretch: :mod:`typehaus.veneer_tie_layout` stations the ties on the studs.

R703.8.4.1: each tie carries at most 2.67 sf of wall, 32" o.c. horizontally and 24" o.c.
vertically; 2 sf where the wind pressure exceeds 30 psf.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

_M_PER_IN = 0.0254
_TOL_M = 1e-4
#: How far behind a wythe's back a backing face may stand and still be what it is tied to.
_REACH_IN = 12.0
_PARALLEL = math.cos(math.radians(5.0))
_MASONRY = ("brick", "block", "cmu", "stone")

MIN_AIRSPACE_IN = 1.0
TIE_AREA_SF = 2.67
TIE_AREA_HIGH_WIND_SF = 2.0
HIGH_WIND_PSF = 30.0
TIE_SPACING_H_IN = 32.0
TIE_SPACING_V_IN = 24.0

#: TMS 402-22 Table 6 as BIA TN 3C (2022) prints it, "veneer ties meeting the prescriptive tie
#: type and backing requirements": (axial stiffness lb/in, allowable lb, design strength lb).
#: ``adjustable_pintle`` is the two-leg eye-and-pintle the W2.8 row needs.
TIE_TABLE_6 = {"adjustable_pintle": (2500.0, 125.0, 210.0),
               "adjustable_slotted": (3000.0, 200.0, 330.0)}
#: TN 3C Table 7, the tributary-area method: tie force = factor x p x At, by tie stiffness
#: (k <= 2,500 lb/in: 2; <= 5,000: 2.5).
TIE_FORCE_FACTOR_SOFT = 2.0
#: Friction of brick and mortar on the base flashing sheet, the input the drag row needs. No
#: maker publishes it; McGinley and Borchelt, "Friction at Supports of Clay Brick Walls" (TMS
#: Journal 9(2), 1991) tested it with common flashing and its values were not opened (paywalled).
#: ``None`` keeps ``structural.veneer_tie_force`` UNKNOWN; set it from a source, never a guess.
FRICTION_BRICK_ON_FLASHING: float | None = None


@dataclass(frozen=True)
class TieRow:
    tie: str
    max_to_backing_in: float


#: Table R703.8.4(1), the rows each edition publishes, lightest tie first (wood-stud backing).
_ROWS_2018 = (TieRow("W1.7 adjustable wire (9 ga)", 4.5),)
_ROWS_2021 = (TieRow("W1.7 adjustable wire (9 ga)", 4.625),
              TieRow("W2.8 adjustable wire (3/16\")", 6.625))
#: 2024: the 2021 rows, footnotes unchanged (e: 2 pintle legs, offset <= 1 1/4"; f: brick
#: face to pintle end <= 2"; backing eye >= W2.8, barrel >= 1/4" OD, or plate >= 0.074" x 1 1/4").
_ROWS_2024 = _ROWS_2021
_ROWS = {2015: _ROWS_2018, 2018: _ROWS_2018, 2021: _ROWS_2021, 2024: _ROWS_2024}
#: The edition the ties are DETAILED to (decision 10): the W2.8 row, in force in a 2024-based code.
DETAIL_EDITION = 2024
TIE_DETAIL = ("W2.8 (3/16\") adjustable wire tie, 2 pintle legs, offset at most 1 1/4\", brick "
              "face to pintle end at most 2\"; backing eye or barrel per Table R703.8.4(1) "
              "(eye W2.8, barrel 1/4\" OD or plate 0.074\" x 1 1/4\"); fastener not smaller than "
              "an 8d common nail, long enough to seat in the stud through the foam and sheathing")


def irc_edition(irc_base: str | None) -> int | None:
    """The IRC year an ``irc_base`` names ("2018 IRC + MN amendments" -> 2018)."""
    match = re.search(r"(\d{4})\s*IRC", irc_base or "")
    return int(match.group(1)) if match else None


def table_rows(irc_base: str | None) -> tuple[TieRow, ...] | None:
    """The edition's rows, or ``None`` for an edition this table is not transcribed for."""
    return _ROWS.get(irc_edition(irc_base))


def covering_row(irc_base: str | None, reach_in: float) -> TieRow | None:
    """The lightest row whose maximum reaches ``reach_in``; ``None`` past every row."""
    return next((row for row in table_rows(irc_base) or ()
                 if reach_in <= row.max_to_backing_in + 1e-6), None)


@dataclass(frozen=True)
class WytheReach:
    tag: str
    #: back of wythe -> backing STRUCTURE face, the worst station (in)
    to_structure_in: float
    #: back of wythe -> nearest backing face, the least station (in)
    airspace_in: float
    #: the backing at the governing station
    backing: str
    backings: tuple[str, ...]
    #: wythe length with no backing behind it (in)
    unbacked_in: float


def is_masonry_wythe(wall: Any) -> bool:
    """A masonry structure layer on its own air space: a veneer, not the building's wall."""
    structure = [ly for ly in wall.layers if ly.function == "structure" and ly.polygon]
    return (bool(structure) and any(m in structure[0].material_ref for m in _MASONRY)
            and any(ly.function == "airgap" and ly.thickness_m > 0 for ly in wall.layers))


def is_anchored_wythe(model: Any, wall: Any) -> bool:
    authored = model.plan.by_tag(wall.tag)
    return is_masonry_wythe(wall) and getattr(authored, "lateral_support", None) is None


def anchored_wythes(model: Any) -> list[Any]:
    return sorted((w for w in model.walls if is_anchored_wythe(model, w)), key=lambda w: w.tag)


def measure(model: Any, wythe: Any) -> WytheReach | None:
    """The wythe's tie reach and airspace, or ``None`` with nothing behind it to measure."""
    (ax, ay), (bx, by) = wythe.axis
    length = math.hypot(bx - ax, by - ay)
    u = ((bx - ax) / length, (by - ay) / length)
    n = (-u[1], u[0])

    def project(points):
        return ([(p[0] - ax) * u[0] + (p[1] - ay) * u[1] for p in points],
                [(p[0] - ax) * n[0] + (p[1] - ay) * n[1] for p in points])

    brick = next(ly for ly in wythe.layers if ly.function == "structure" and ly.polygon)
    gap = next(ly for ly in wythe.layers if ly.function == "airgap" and ly.thickness_m > 0)
    bu, bn = project(brick.polygon)
    _, gn = project(gap.polygon)
    side = 1.0 if sum(gn) / len(gn) > sum(bn) / len(bn) else -1.0
    back = max(bn) if side > 0 else min(bn)
    u0, u1 = min(bu), max(bu)
    height = wythe.z1_m - wythe.z0_m

    candidates = []
    for wall in model.walls:
        if wall.tag == wythe.tag:
            continue
        overlap = min(wall.z1_m, wythe.z1_m) - max(wall.z0_m, wythe.z0_m)
        (cx, cy), (dx, dy) = wall.axis
        run = math.hypot(dx - cx, dy - cy)
        # A backing runs beside the wythe; a wall butting into the cavity end-on does not.
        if (overlap <= 0.5 * min(height, wall.z1_m - wall.z0_m) or run <= _TOL_M
                or abs((dx - cx) * u[0] + (dy - cy) * u[1]) / run < _PARALLEL):
            continue
        faces, structure, us = [], [], []
        for layer in wall.layers:
            if layer.thickness_m <= 0 or not layer.polygon:
                continue
            lu, ln = project(layer.polygon)
            offsets = [side * (v - back) for v in ln]
            faces.append(min(offsets))
            us += lu
            if layer.function == "structure" and not layer.is_cavity:
                structure.append(min(offsets))
        if (not structure or min(faces) < -_TOL_M or min(faces) > _REACH_IN * _M_PER_IN
                or min(us) >= u1 - _TOL_M or max(us) <= u0 + _TOL_M):
            continue
        candidates.append((wall.tag, max(min(us), u0), min(max(us), u1), overlap,
                           min(structure), min(faces)))
    if not candidates:
        return None
    cuts = sorted({u0, u1, *(c[1] for c in candidates), *(c[2] for c in candidates)})
    worst, least, governing, used, unbacked = -1.0, math.inf, "", set(), 0.0
    for lo, hi in zip(cuts, cuts[1:], strict=False):
        mid = (lo + hi) / 2.0
        here = [c for c in candidates if c[1] <= mid <= c[2]]
        if not here:
            unbacked += hi - lo
            continue
        tag, _, _, _, to_structure, to_face = max(here, key=lambda c: c[3])
        used.add(tag)
        least = min(least, to_face)
        if to_structure > worst:
            worst, governing = to_structure, tag
    return WytheReach(wythe.tag, worst / _M_PER_IN, least / _M_PER_IN, governing,
                      tuple(sorted(used)), unbacked / _M_PER_IN)


def tie_area_sf(pressure_psf: float | None) -> float:
    """R703.8.4.1's wall area per tie; the high-wind area where the pressure is unknown."""
    if pressure_psf is None or pressure_psf > HIGH_WIND_PSF:
        return TIE_AREA_HIGH_WIND_SF
    return TIE_AREA_SF


def beyond_table(model: Any, irc_base: str | None) -> list[str]:
    """Every anchored wythe no row of the adopted edition covers (or that cannot be read)."""
    out = []
    for wythe in anchored_wythes(model):
        reach = measure(model, wythe)
        if reach is None or covering_row(irc_base, reach.to_structure_in) is None:
            out.append(wythe.tag)
    return out


def base_flashing(model: Any, wythe: Any) -> tuple[list[str], float]:
    """``(flashing runs, brick base left bare in)``: the authored ``Flashing`` runs hosted on
    the wythe with their top at its base (the bond break and R703.8.5 flashing in one), and
    the length of base along the wythe they do not cover, net of an opening that reaches the
    base (a door's reveal has no brick to flash under)."""
    (ax, ay), (bx, by) = wythe.axis
    length = math.hypot(bx - ax, by - ay)
    u = ((bx - ax) / length, (by - ay) / length)

    def along(p) -> float:
        return ((p[0] - ax) * u[0] + (p[1] - ay) * u[1]) / _M_PER_IN

    brick = next(ly for ly in wythe.layers if ly.function == "structure" and ly.polygon)
    us = [along(p) for p in brick.polygon]
    lo, hi = max(0.0, min(us)), min(length / _M_PER_IN, max(us))
    spans = [(wythe_u(model, o, -1), wythe_u(model, o, 1)) for o in model.openings
             if o.host_wall == wythe.tag and o.sill_m <= 1e-4]
    covered, tags = [], []
    for el in model.plan.all_elements():
        path = getattr(el, "path", None)
        if (getattr(el, "host_ref", None) != wythe.tag or path is None
                or abs(el.top_elevation.meters - wythe.z0_m) > 0.5 * _M_PER_IN):
            continue
        pts = [along((p.x.meters, p.y.meters)) for p in path]
        covered.append((min(pts), max(pts)))
        tags.append(el.tag)
    bare = 0.0
    cuts = sorted({lo, hi, *(c for pair in covered + spans for c in pair)})
    for a, b in zip(cuts, cuts[1:], strict=False):
        mid = (a + b) / 2.0
        if not lo <= mid <= hi:
            continue
        if not any(x <= mid <= y for x, y in covered + spans):
            bare += b - a
    return sorted(tags), bare


def wythe_u(model: Any, opening: Any, side: int) -> float:
    """An opening's edge along its wythe, in from the wall's start."""
    return opening.center_along_m / _M_PER_IN + side * opening.width_m / _M_PER_IN / 2.0
