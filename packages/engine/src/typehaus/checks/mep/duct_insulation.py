"""MN 1322 Table R403.2.1 — minimum duct and plenum insulation, graded per stretch of run.

Minn. R. 1322.0403 subp. 1 replaces IECC R403.2.1: every outdoor-air intake, exhaust, supply
and return duct and plenum is insulated per the table (revisor.mn.gov/rules/1322.0403, read
2026-11-21). Rows, paraphrased: outside the building R-8 with a vapour retarder (V) and a
weatherproof barrier (W); attics, garages and vented crawl spaces R-8 and V; outdoor-air
intakes and exhaust ducts within conditioned space R-3.3 and V; in a slab or the ground
R-3.5 and V; anywhere else within conditioned space (and basements with insulated walls)
none. Note a: inside conditioned space insulation is required only within 3 ft of the
exterior or unconditioned space. V is IMC 604.11's retarder, installed independently of the
envelope insulation. Whole table: docs/local-code-notes/mn-1322-r403-2-1.md.

Each run is stepped in 3D. A step's class comes from the room owning it on the storey its
height lies in (``room_lookup``): a conditioned room, an unconditioned one, below the lowest
storey (ground), or no room. Over a room's flat ceiling with no room on a storey above, it
is an attic unless a Room says otherwise: R-8 + V met passes, anything less is UNKNOWN.
No room within ``WALL_ZONE_M`` of a room cell is the envelope wall the run passes through:
a penetration, sealed by its own element, ungraded here but the edge note a measures from
(unless it lies between two conditioned stretches: then the run only passes a wall's end).
An OA, exhaust or dryer step in conditioned space takes the
R-3.3 row within 3 ft (developed) of such an edge. The spec is read off the house's
``DuctStandard.insulations`` row; no row is UNKNOWN.
"""

from __future__ import annotations

import math
from typing import Any

from shapely.geometry import Point, Polygon
from shapely.prepared import prep

from typehaus.checks._authoring import by_result
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_FT
from typehaus.resolve.room_lookup import axis_ring

CID = "mep.duct_insulation"
CODE = "MN Energy Code (Minn. R. 1322.0403) Table R403.2.1"

STEP_M = 0.05
WALL_ZONE_M = 0.3
#: A storey's rooms own heights up to this far over its datum (attic under a ridge).
STOREY_REACH_M = 6.0
NOTE_A_M = 3.0 * M_PER_FT
#: Systems carrying outdoor-temperature air: the table's conditioned-space rows.
COLD_SYSTEMS = frozenset({"outdoor_air", "exhaust", "dryer"})
#: (required R, vapour retarder, weatherproof barrier) by step class.
ROWS = {"exterior": (8.0, True, True), "unconditioned": (8.0, True, False),
        "over_ceiling": (8.0, True, False),
        "ground": (3.5, True, False), "cold_conditioned": (3.3, True, False)}
LABEL = {"exterior": "outside the building", "unconditioned": "in unconditioned space",
         "over_ceiling": "over a top ceiling with no room above (an attic?)",
         "ground": "below the lowest floor", "cold_conditioned":
         "in conditioned space within 3 ft of the envelope"}


class _Cells:
    """Room axis cells per storey, prepared once; storeys tried from the highest under z."""

    def __init__(self, model: Any) -> None:
        self.cells: dict[str, list] = {}
        tops: dict[str, float] = {}
        for c in model.ceilings:
            if c.z1_m is not None:
                tops[c.room_ref] = max(tops.get(c.room_ref, c.z1_m), c.z1_m)
        for room in model.rooms:
            ring = axis_ring(room)
            if len(ring) >= 3:
                poly = Polygon(ring)
                self.cells.setdefault(room.storey, []).append(
                    (room, prep(poly), poly, tops.get(room.tag)))
        # Only storeys with rooms: site and court levels share elevations with them.
        self.levels = sorted(((s.elevation.meters, s.tag) for s in model.plan.storeys
                              if s.tag in self.cells), reverse=True)

    def classify(self, x: float, y: float, z: float) -> str:
        if not self.levels or z < self.levels[-1][0] - 1e-3:
            return "ground"
        point = Point(x, y)
        near = [self.cells[tag] for elev, tag in self.levels
                if elev - 1e-3 <= z <= elev + STOREY_REACH_M]
        for cells in near:
            for room, prepared, _, top in cells:
                if prepared.covers(point):
                    if not room.conditioned:
                        return "unconditioned"
                    if top is not None and z > top + 1e-3 and not self._roomed_above(point, z):
                        return "over_ceiling"  # an attic, unless a Room says otherwise
                    return "conditioned"
        if any(poly.distance(point) <= WALL_ZONE_M for cells in near for _, _, poly, _ in cells):
            return "wall"
        return "exterior"

    def _roomed_above(self, point: Point, z: float) -> bool:
        """A room on a storey over ``z`` covers the point: the run is in a floor cavity."""
        return any(prepared.covers(point) for elev, tag in self.levels
                   if z < elev <= z + STOREY_REACH_M for _, prepared, _, _ in self.cells[tag])


def _steps(duct: Any, cells: _Cells) -> list[tuple[float, float, str]]:
    """``(station m, length m, class)`` along the run's developed centreline."""
    out, station = [], 0.0
    pts = [(p[0], p[1], z) for p, z in zip(duct.path, duct.z_m, strict=False)]
    for a, b in zip(pts, pts[1:], strict=False):
        length = math.dist(a, b)
        n = max(1, math.ceil(length / STEP_M))
        for i in range(n):
            t = (i + 0.5) / n
            mid = tuple(a[k] + (b[k] - a[k]) * t for k in range(3))
            out.append((station + length * t, length / n, cells.classify(*mid)))
        station += length
    return out


def _envelope(steps: list) -> list[tuple[float, float, str]]:
    """A wall stretch between two conditioned ones is a pass by a wall's end, not the
    envelope: it reads as conditioned. One at a run end, or beside the outside, stays."""
    out = list(steps)
    i = 0
    while i < len(out):
        if out[i][2] != "wall":
            i += 1
            continue
        j = i
        while j < len(out) and out[j][2] == "wall":
            j += 1
        if i > 0 and j < len(out) and out[i - 1][2] == out[j][2] == "conditioned":
            out[i:j] = [(s, ln, "conditioned") for s, ln, _ in out[i:j]]
        i = j
    return out


def _required(duct: Any, steps: list) -> dict[str, float]:
    """``{row class: length m}`` of the stretches the table asks insulation on."""
    steps = _envelope(steps)
    edges = [s for s, _, cls in steps if cls != "conditioned"]
    need: dict[str, float] = {}
    for station, length, cls in steps:
        if cls == "conditioned":
            if duct.system not in COLD_SYSTEMS or not edges:
                continue
            if min(abs(station - e) for e in edges) > NOTE_A_M:
                continue
            cls = "cold_conditioned"
        if cls in ROWS:
            need[cls] = need.get(cls, 0.0) + length
    return need


@check(Tier.CODE, CID)
def duct_insulation(ctx: CheckContext) -> list[Finding]:
    """Table R403.2.1 — each run's insulation spec against the rows its stretches fall in."""
    from typehaus.resolve.duct_standard import duct_standard

    ducts = [d for d in ctx.model.ducts if len(d.path) >= 2 and len(d.z_m) == len(d.path)]
    if not ducts:
        return [by_result(CID, Result.NOT_APPLICABLE, "no duct run is modeled", (), CODE)]
    standard, _ = duct_standard(ctx.plan)
    cells = _Cells(ctx.model)
    out, indoor = [], []
    for duct in sorted(ducts, key=lambda d: d.tag):
        steps = _steps(duct, cells)
        need = _required(duct, steps)
        if not need:
            if duct.system == "outdoor_air" and all(c == "conditioned" for _, _, c in steps):
                out.append(by_result(CID, Result.UNKNOWN, f"{duct.tag} is outdoor air but "
                                     "never reaches the envelope as modeled", (duct.tag,), CODE))
            else:
                indoor.append(duct.tag)
            continue
        out.append(_grade(duct, need, standard))
    if indoor:
        out.append(by_result(CID, Result.NOT_APPLICABLE, f"{len(indoor)} run(s) lie wholly "
                             "in conditioned space with no stretch the table insulates "
                             f"(indoor air, or exhaust beyond 3 ft of the envelope): "
                             f"{', '.join(indoor)}", tuple(indoor), CODE))
    return out


def _grade(duct: Any, need: dict[str, float], standard: Any) -> Finding:
    r_need = max(ROWS[c][0] for c in need)
    v_need = any(ROWS[c][1] for c in need)
    w_need = any(ROWS[c][2] for c in need)
    where = "; ".join(f"{need[c] / M_PER_FT:.1f} ft {LABEL[c]} (R-{ROWS[c][0]:g}"
                      f"{' + V' if ROWS[c][1] else ''}{' + W' if ROWS[c][2] else ''})"
                      for c in sorted(need))
    tags = (duct.tag,)
    if not duct.insulation:
        verdict = Result.UNKNOWN if set(need) == {"over_ceiling"} else Result.FAIL
        return by_result(CID, verdict, f"{duct.tag} is bare: {where}", tags, CODE,
                         fix="name a DuctStandard.insulations spec on the run")
    row = standard.insulation(duct.insulation) if standard is not None else None
    if row is None:
        return by_result(CID, Result.UNKNOWN, f"{duct.tag}'s insulation {duct.insulation!r} "
                         f"is no DuctStandard row, so its R is unread; it needs {where}",
                         tags, CODE)
    short = [s for s, bad in ((f"R-{row.r_value:g} < R-{r_need:g}", row.r_value < r_need),
                              ("no vapour retarder", v_need and not row.vapour_retarder),
                              ("no weatherproof barrier", w_need and not row.weather_barrier))
             if bad]
    if short and "over_ceiling" in need:
        return by_result(CID, Result.UNKNOWN, f"{duct.tag}: {row.spec} falls short "
                         f"({', '.join(short)}) for {where}; whether that space is an attic "
                         "is unread", tags, CODE,
                         fix="author a Room over the ceiling (conditioned or not), or insulate "
                             "to R-8 + V")
    if short:
        return by_result(CID, Result.FAIL, f"{duct.tag}: {row.spec} falls short "
                         f"({', '.join(short)}) for {where}", tags, CODE)
    return by_result(CID, Result.PASS, f"{duct.tag}: {row.spec} meets {where}", tags, CODE)
