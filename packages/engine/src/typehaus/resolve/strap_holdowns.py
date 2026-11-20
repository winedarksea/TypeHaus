"""Where each placed STHD sits in its concrete: the geometry ESR-2920 Table 1 is read at.

One reader for ``resolve/rebar/strap_bars.py`` (the No. 4 bar the report requires) and
``checks/structural/strap_holdown_embedment.py``. Distances are measured from the strap's
ENTRY (``EmbeddedStrap.entry_xy``), where it is cast, not from the leaf a jog bends back to.
"""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import LineString, Point, Polygon

from typehaus.hardware.esr2920 import (  # noqa: F401 - re-exported to resolve/rebar
    BAR_BAND_IN,
    CORNER_LEG_IN,
    EMBEDDED_WIDTH_IN,
    MIN_BAR,
    REBAR_LE,
    TABLE_1,
    sizes,
)
from typehaus.model.structure import Footing
from typehaus.quantities import M_PER_IN
from typehaus.resolve.overlay import intersection, union_all

_SAME_TOP_M = 1.0 * M_PER_IN
_REACH_M = 20.0


@dataclass(frozen=True)
class EndSide:
    """One end along the wall: the clear distance from the strap edge, and what is there."""

    sign: float               # +1 along ``along_xy``, -1 against it
    distance_in: float        # strap's cast-in edge to the end of the concrete
    turn_to: tuple | None     # unit direction a perpendicular core continues in, else None
    turn_core: tuple | None   # that core's polygon
    turn_core_tag: str | None


@dataclass(frozen=True)
class StrapSite:
    strap: object             # EmbeddedStrap
    top_z_m: float
    pour_bottom_z_m: float
    cast_with: str | None     # the footing placed in one pour with the wall, if any
    behind_in: float          # entry to the face behind it
    ahead_in: float           # entry to the far face, along the spoon
    centre_xy: tuple          # the core's mid-thickness, opposite the entry
    ends: tuple[EndSide, EndSide]
    core: tuple
    le_in: float | None       # the deepest Table 1 le the part could need
    corner_leg_in: float | None  # Figure 1's corner return for that size


def strap_le(part: str) -> tuple[float | None, float | None]:
    """``(le, corner return)`` of the deepest size ``part`` could be."""
    found = sizes(part)
    if not found:
        return None, None
    deepest = max(found, key=lambda s: TABLE_1[(6, s)].le_in)
    le = TABLE_1[(6, deepest)].le_in
    return le, CORNER_LEG_IN.get(deepest) or REBAR_LE * le


def _core(model, tag: str) -> tuple | None:
    wall = model.wall(tag)
    layer = next((lyr for lyr in wall.layers if lyr.function == "structure" and lyr.polygon),
                 None) if wall is not None else None
    return tuple(layer.polygon) if layer is not None else None


def _pours(model, top_z_m: float) -> list[tuple[str, tuple]]:
    out = []
    for wall in model.walls:
        if wall.is_foundation and abs(wall.z1_m - top_z_m) <= _SAME_TOP_M:
            core = _core(model, wall.tag)
            if core is not None:
                out.append((wall.tag, core))
    return out


def _run(union, origin, direction) -> float:
    """Distance from ``origin`` along ``direction`` to where the concrete ends."""
    far = (origin[0] + direction[0] * _REACH_M, origin[1] + direction[1] * _REACH_M)
    hit = intersection(LineString([origin, far]), union)
    start = Point(origin)
    parts = getattr(hit, "geoms", [hit])
    best = 0.0
    for part in parts:
        if part.is_empty or part.geom_type != "LineString":
            continue
        if part.distance(start) <= 1e-6:
            best = max(best, part.length)
    return best


def _offsets(poly, origin, axis) -> tuple[float, float]:
    vals = [(p[0] - origin[0]) * axis[0] + (p[1] - origin[1]) * axis[1] for p in poly]
    return min(vals), max(vals)


def _cast_with(model, wall_tag: str) -> Footing | None:
    plan = model.plan
    return next((el for el in plan.all_elements() if isinstance(el, Footing)
                 and el.under == wall_tag and el.material == "concrete"
                 and el.cast_with_wall), None) if plan is not None else None


def _footing_bottom(model, footing: Footing) -> float | None:
    solid = next((s for s in model.solids if s.tag == footing.tag), None)
    return solid.z0_m if solid is not None else None


def strap_site(model, strap) -> StrapSite | None:
    wall = model.wall(strap.core_tag)
    core = _core(model, strap.core_tag)
    if wall is None or core is None:
        return None
    top = wall.z1_m
    footing = _cast_with(model, wall.tag)
    bottom = wall.z0_m
    if footing is not None and (fb := _footing_bottom(model, footing)) is not None:
        bottom = min(bottom, fb)
    e, s, d = strap.entry_xy, strap.spoon_xy, strap.along_xy
    lo, hi = _offsets(core, e, s)
    mid = (lo + hi) / 2.0
    centre = (e[0] + s[0] * mid, e[1] + s[1] * mid)
    pours = _pours(model, top)
    union = union_all([Polygon(p) for _, p in pours])
    half = EMBEDDED_WIDTH_IN / 2.0
    ends = []
    for sign in (-1.0, 1.0):
        dirn = (d[0] * sign, d[1] * sign)
        run = _run(union, centre, dirn)
        turn = turn_core = turn_tag = None
        thick = hi - lo
        near = (centre[0] + dirn[0] * (run - 0.5 * M_PER_IN),
                centre[1] + dirn[1] * (run - 0.5 * M_PER_IN))
        for nsign in (-1.0, 1.0):
            probe = (near[0] + s[0] * nsign * (thick / 2 + 3 * M_PER_IN),
                     near[1] + s[1] * nsign * (thick / 2 + 3 * M_PER_IN))
            hit = next(((tag, p) for tag, p in pours if tag != strap.core_tag
                        and Polygon(p).contains(Point(probe))), None)
            if hit is not None:
                turn, turn_tag, turn_core = (s[0] * nsign, s[1] * nsign), hit[0], hit[1]
                break
        ends.append(EndSide(sign, run / M_PER_IN - half, turn, turn_core, turn_tag))
    return StrapSite(strap, top, bottom, footing.tag if footing else None,
                     -lo / M_PER_IN, hi / M_PER_IN, centre, (ends[0], ends[1]), core,
                     *strap_le(strap.part))


def strap_sites(model) -> list[StrapSite]:
    return [site for strap in model.embedded_straps
            if (site := strap_site(model, strap)) is not None]
