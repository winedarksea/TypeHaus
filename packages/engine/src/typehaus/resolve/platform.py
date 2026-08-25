"""Platform framing: exterior/bearing walls span floor-to-floor (#43).

Revit and SketchUp both expect a wall to run from its base level to the level above, with
the floor system butting into it. TypeHaus used to stop every wall at its own ceiling
height and patch the leftover joist band with a separate ``ResolvedEnvelopeBand`` proxy
object — which left a stud-depth void inboard of the sheathing and handed importers a
non-wall object at every storey line.

Here the lower wall simply grows to meet the wall stacked on it. Its *framing* does not:
``plate_top_z_m`` keeps the double top plate at the original ceiling height, so the band
above the plate is rim board and joists, which is what platform framing actually is.

The same band exists at the *bottom* of the lowest framed storey, and for a while nothing
covered it. A framed wall starts at its storey datum; the foundation it lands on tops out a
mudsill, a gasket and a rim board below that (13 7/16" on catlin since the bearing seat
rework), and both loops here skip foundation walls, so the gap was left open — roughly 270 SF
of cladding, CI, WRB and trim missing from the order at ~240 LF of envelope, billed per wall
by ``envelope_layer_takeoff`` and therefore a real quantity shortfall rather than a render
artifact. ``extend_walls_to_foundation`` closes it the other way round: the *upper* (framed)
wall grows **down** over the mudsill and rim to lap the foundation's protection panel, which
is the detail as drawn (``notes/basement_to_framed_wall_detail.md``,
``detail_components/wall_base.py``). Its framing stays put, at ``plate_base_z_m``.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from typehaus.quantities import inch
from typehaus.resolve.layer_bands import reband
from typehaus.resolve.layout_lines import lines_by_wall
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.topology import site_grade_elevation_m_from_plan

# A storey line is a joist band. Anything deeper is a real void (a stairwell, a
# double-height space) and must not be silently absorbed into the wall below.
_MAX_BAND_M = inch(24).meters


def extend_walls_to_platform(model: ResolvedModel) -> None:
    """Grow each stacked lower wall up to the underside of the wall above it.

    The stack is the authored ``Wall.stacks_on`` graph — the same signal the old envelope
    band used — so this never guesses at which walls belong to one wall line.
    """
    lines = lines_by_wall(model.layout_lines)
    lifted: set[str] = set()
    for upper in model.walls:
        authored = model.plan.by_tag(upper.tag)
        lower_tag = getattr(authored, "stacks_on", None)
        if not lower_tag or lower_tag in lifted:
            continue
        lower = model.wall(lower_tag)
        if lower is None or lower.is_foundation:
            continue
        band = upper.z0_m - lower.z1_m
        if band <= 1e-6 or band > _MAX_BAND_M:
            continue
        # A raked top (gable, wall-to-roof) has no flat platform to reach for.
        if lower.top_z0_m is not None or lower.top_z1_m is not None:
            continue
        _lift(model, lower, upper.z0_m, lines)
        lifted.add(lower.tag)

    # ``stacks_on`` is authored by hand and is routinely incomplete — Catlin's attic names
    # 7 of the second storey's 15 walls. Everything it missed gets the geometric read:
    # a wall whose axis is covered by a wall above is on the same wall line.
    for lower in list(model.walls):
        if lower.tag in lifted or lower.is_foundation:
            continue
        if lower.top_z0_m is not None or lower.top_z1_m is not None:
            continue
        z = _platform_above(model, lower)
        if z is None:
            continue
        band = z - lower.z1_m
        if band <= 1e-6 or band > _MAX_BAND_M:
            continue
        _lift(model, lower, z, lines)
        lifted.add(lower.tag)


def extend_walls_to_foundation(model: ResolvedModel) -> None:
    """Drop each framed wall's base to the top of the foundation wall it stands on.

    The mirror of :func:`extend_walls_to_platform`, guard for guard — the same authored
    ``stacks_on`` first, the same geometric fallback, the same ``_MAX_BAND_M`` so a real
    void (a walkout, a stepped pour) is never silently absorbed. Only a *foundation* wall
    below counts: a framed-over-framed storey line is already covered from the other side by
    the upward lift, and taking it from both would clad the band twice.

    And only a wall with a cladding layer moves. This is the one place the mirror is not
    symmetric, because the band is not: *above* a wall, an interior partition really does run
    to the underside of the floor above. *Below* one, the band is the joist bay over the
    basement, and an interior bearing wall has no skin that could lap anything — extending
    catlin's five ``CATLIN_INT_2X6_BRG`` walls billed 73 SF of gypsum and paint down both
    faces of a floor system. The reason this pass exists is the lap onto the foundation's
    protection panel, and that is an envelope detail.
    """
    grade_m = site_grade_elevation_m_from_plan(model.plan)
    lines = lines_by_wall(model.layout_lines)
    dropped: set[str] = set()
    for upper in list(model.walls):
        if upper.is_foundation or upper.tag in dropped or not _is_clad(upper):
            continue
        authored = model.plan.by_tag(upper.tag)
        lower_tag = getattr(authored, "stacks_on", None)
        lower = model.wall(lower_tag) if lower_tag else None
        if lower is None or not lower.is_foundation:
            lower = _foundation_below(model, upper)
        if lower is None:
            continue
        band = upper.z0_m - lower.z1_m
        if band <= 1e-6 or band > _MAX_BAND_M:
            continue
        _drop(model, upper, lower.z1_m, grade_m, lines)
        dropped.add(upper.tag)


def _is_clad(wall: Any) -> bool:
    """Does this wall carry a cladding layer — is it envelope, or is it partition?"""
    return any(layer.function == "cladding" for layer in wall.layers)


def _foundation_below(model: ResolvedModel, upper: Any) -> Any | None:
    """The foundation wall whose top is where ``upper`` must reach to close its rim band.

    Not the highest under the run, and not the lowest — the highest at the *worst station*
    along it. A foundation wall shuts the band only over the stretch it actually runs, while
    the drop is one elevation for the whole wall, so the band is closed everywhere only if
    the wall reaches the lowest point of the run's closing profile.

    Catlin needs both halves of that. On the south wall ``W-M-S1`` spans 0'-0"..18'-0" over
    the pour ``W-B-S1`` (top -13 7/16") and over ``W-B-BRICK``, the freestanding glazed wythe
    that reaches 0'-0" but only from 8'-10" east. Reading the highest calls the band closed
    and bares the rim over the western 8'-10" the brick never covers — the FS-M-WEST joist
    band, in plain view. In the garage the error runs the other way: ``W-G-S`` stands on a
    stem topping at -12", stepped down to -34" across the 3'-6" door, and reading the lowest
    would drag 22" of siding down the whole 24'-0" wall for a threshold it never touches.

    So: sweep the run, take the highest top covering each station, and return the wall owning
    the *lowest* of those. Two kinds of station are skipped rather than counted as open. One
    no foundation reaches at all is a walkout, not a band, and must not pull the wall to
    -inf. One standing in a door that lands at or below the framing base has no skin to lap
    to begin with — that is the garage's stepped pour, whose two depressed stretches are
    exactly the door openings over them.

    ``_MAX_BAND_M`` is applied per candidate for the same reason: a stepped pour deep enough
    to be a real void is not a joist band to be absorbed, and excluding it lets the next
    candidate close what honestly can be closed.
    """
    tol = max(upper.thickness_m, 1e-3)
    spans = [
        (lo_t, hi_t, lower)
        for lower in model.walls
        if lower is not upper and lower.is_foundation
        and lower.z1_m <= upper.z0_m + 1e-6
        and upper.z0_m - lower.z1_m <= _MAX_BAND_M
        for lo_t, hi_t in (_project(upper.axis, lower.axis, tol),)
        if hi_t - lo_t > tol
    ]
    if not spans:
        return None
    thresholds = _door_thresholds(model, upper)
    stations = sorted({t for lo_t, hi_t, _ in spans for t in (lo_t, hi_t)})
    worst = None
    for start, end in zip(stations, stations[1:], strict=False):
        mid = (start + end) / 2.0
        if any(lo_t <= mid <= hi_t for lo_t, hi_t in thresholds):
            continue
        covering = [w for lo_t, hi_t, w in spans if lo_t <= mid <= hi_t]
        if not covering:
            continue
        highest = max(covering, key=lambda w: w.z1_m)
        if worst is None or highest.z1_m < worst.z1_m:
            worst = highest
    return worst


def _door_thresholds(model: ResolvedModel, wall: Any) -> list[tuple[float, float]]:
    """Station ranges of ``wall``'s doors, whose stations cannot set a cladding base.

    A stem is *gapped* under a door and picked up on a grade beam — catlin's garage says so
    outright: "there is no 22"-above-grade stem wall under a vehicle door (it would be a curb
    the car has to climb)", and the service door beside it gets "identical treatment for the
    identical reason". So the pour's step down at a doorway is a threshold, not a rim band,
    and reading it as one drags the siding down the whole wall to chase a grade beam.

    Doors only. A window has ordinary wall under it, and that wall's rim band is exactly what
    :func:`_foundation_below` is measuring.
    """
    return [
        (opening.center_along_m - opening.width_m / 2.0,
         opening.center_along_m + opening.width_m / 2.0)
        for opening in model.openings
        if opening.host_wall == wall.tag and opening.is_door
    ]


def _project(a: tuple[tuple[float, float], tuple[float, float]],
             b: tuple[tuple[float, float], tuple[float, float]],
             tol: float) -> tuple[float, float]:
    """``b``'s overlap with ``a``, as a station range along ``a``; empty if off its line."""
    (ax0, ay0), (ax1, ay1) = a
    dx, dy = ax1 - ax0, ay1 - ay0
    span = math.hypot(dx, dy)
    if span < 1e-9:
        return (0.0, 0.0)
    ux, uy = dx / span, dy / span
    ts = []
    for (px, py) in b:
        ex, ey = px - ax0, py - ay0
        if abs(-uy * ex + ux * ey) > tol:
            return (0.0, 0.0)
        ts.append(ux * ex + uy * ey)
    return (max(min(ts), 0.0), min(max(ts), span))


def _drop(model: ResolvedModel, upper: Any, z0: float, grade_m: float,
          lines: dict[str, Any]) -> None:
    index = next(i for i, w in enumerate(model.walls) if w is upper)
    model.walls[index] = replace(
        upper, z0_m=z0, plate_base_z_m=upper.z0_m,
        layers=reband(upper, z0, upper.z1_m, grade_m, lines.get(upper.tag)),
    )




def _lift(model: ResolvedModel, lower: Any, z1: float,
          lines: dict[str, Any]) -> None:
    """Grow ``lower`` to ``z1``, keeping its framing at the old top — and re-band its layers.

    The re-band is not incidental. ``resolve_storey_walls`` resolves every ``Layer.extent``
    to absolute elevations, and this pass runs after it, so a band on a lifted wall would
    otherwise stay pinned to the pre-lift top — including a ``top=None`` band, which means
    "run it out to the wall top" and had already been frozen to the *old* wall top. Latent
    until now only because ``CATLIN_EXT_2X6`` bands nothing (→ ``layer_bands.reband``).
    """
    index = next(i for i, w in enumerate(model.walls) if w is lower)
    grade_m = site_grade_elevation_m_from_plan(model.plan)
    model.walls[index] = replace(
        lower, z1_m=z1, plate_top_z_m=lower.z1_m,
        layers=reband(lower, lower.z0_m, z1, grade_m, lines.get(lower.tag)),
    )


def _platform_above(model: ResolvedModel, lower: Any) -> float | None:
    """Lowest ``z0_m`` among walls that sit on ``lower``'s axis, from above."""
    tol = max(lower.thickness_m, 1e-3)
    best: float | None = None
    for upper in model.walls:
        if upper is lower or upper.is_foundation or upper.z0_m < lower.z1_m - 1e-6:
            continue
        if not _collinear_overlap(lower.axis, upper.axis, tol):
            continue
        if best is None or upper.z0_m < best:
            best = upper.z0_m
    return best


def _collinear_overlap(a: tuple[tuple[float, float], tuple[float, float]],
                       b: tuple[tuple[float, float], tuple[float, float]],
                       tol: float) -> bool:
    """Do segments ``a`` and ``b`` share a direction, a line (within ``tol``), and length?"""
    (ax0, ay0), (ax1, ay1) = a
    dx, dy = ax1 - ax0, ay1 - ay0
    span = math.hypot(dx, dy)
    if span < 1e-9:
        return False
    ux, uy = dx / span, dy / span
    ts = []
    for (px, py) in b:
        ex, ey = px - ax0, py - ay0
        if abs(-uy * ex + ux * ey) > tol:  # perpendicular distance off a's line
            return False
        ts.append(ux * ex + uy * ey)
    lo, hi = min(ts), max(ts)
    return bool(min(hi, span) - max(lo, 0.0) > tol)
