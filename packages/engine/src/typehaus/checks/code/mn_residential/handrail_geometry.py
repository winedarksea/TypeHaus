"""R311.7.8, measured: the handrail that was *drawn*, not the one that was authored.

Split out of ``stairs.py`` the way :mod:`typehaus.resolve.stairs.walkline` was, and for the
same reason — that module was past the repo's 500-line policy and this is a cohesive piece
of it.

Everything ``stairs.py`` asks about a handrail before calling in here is an authored field:
``top_height`` as a number, ``continuous`` as a bool, ``graspable_profile`` as a string.
Three of those are claims, and a claim is what a code check should not be satisfied by — it
is how ``RL-M-HANDRAIL-E``, a rail that stopped short of its flight, passed R311.7.8.2:
``continuous=True`` is the field's default and nothing ever looked at the rail.
``code.R312_1_3_guard_opening_limit`` already cross-checks drawn geometry against authored
values for the guard half of the pair; this is the same move for the handrail half.
"""

from __future__ import annotations

import math

from typehaus.checks.code.mn_residential._common import _fail
from typehaus.checks.registry import CheckContext
from typehaus.findings import Finding
from typehaus.model.structure import Railing
from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedSolid, ResolvedStair
from typehaus.resolve.stairs.walkline import (
    RAIL_LATERAL_REACH_M,
    flight_stations,
    flight_walklines,
    walkline_z_at,
)
from typehaus.resolve.sweep import clean_path

#: R311.7.8.1's band: a handrail tops out 34"-38" above the nosings. Defined here rather
#: than in ``stairs.py`` so the authored grade and the measured one cannot drift apart —
#: ``stairs.py`` imports it back, which is the direction that has no cycle in it.
#: A plan point, and the band list ``_drawn_rail_bands`` hands the other helpers.
Vec = tuple[float, float]
Bands = list[tuple[Vec, float, float]]

MIN_HANDRAIL_HEIGHT = inch(34)
MAX_HANDRAIL_HEIGHT = inch(38)

# R311.7.8.3 Type I, the circular case: 1-1/4" to 2" in diameter. (The section also admits
# a non-circular Type I on a 4"-6-1/4" perimeter, and a shaped Type II; neither is a
# diameter, so neither is graded here.)
_MIN_TYPE_I_DIAMETER = inch(1.25)
_MAX_TYPE_I_DIAMETER = inch(2)
#: How far a nosing may be from the nearest drawn rail and still be served by it. Not a
#: code number — R311.7.8 states no reach — but the distance past which a rail is plainly
#: not the one you would put your hand on climbing that tread. Half a code-minimum 36"
#: stairway, so a single rail serves a stair of that width and a wider one needs the
#: second rail R311.7.8 would ask for anyway.
_HANDRAIL_REACH_M = inch(18).meters
#: A step in the sampled nosing line, across one band, past which the band is judged to be
#: crossing a flight junction rather than raking along a flight. Half a maximum riser: no
#: flight climbs that fast, and any two consecutive nosings of one differ by less.
_JUNCTION_STEP_M = inch(3.875).meters
#: How far apart the stations a swept rail is measured at sit. The quarter metre the rail
#: was itself sampled at (``resolve/railings/spans.RAIL_BAND_STEP_M``) — close enough that
#: every nosing on a code stair has one beside it, which is what R311.7.8.2 asks.
_BAND_SAMPLE_M = 0.25


def drawn_handrail_findings(ctx: CheckContext, stair: ResolvedStair, rail: Railing,
                            cid: str
                             ) -> tuple[list[Finding], str]:
    """Grade the handrail that was *drawn*, not only the one that was authored.

    Everything above this point reads authored fields: ``top_height`` as a number,
    ``continuous`` as a bool, ``graspable_profile`` as a string. Three of those are claims,
    and a claim is exactly what a code check should not be satisfied by — it is how
    ``RL-M-HANDRAIL-E``, a 5'-0" rail on a flight half again that long, passed R311.7.8.2:
    ``continuous=True`` is the field's default, and nothing ever looked at the rail.
    ``code.R312_1_3_guard_opening_limit`` already cross-checks drawn geometry against
    authored values for the guard half of this pair; this is the same move for the handrail.

    Returns the findings that *disagree* with the authored verdict — so an empty list means
    "the drawing bears the authoring out" and the caller passes — plus a note naming
    anything the measurement had to step around, which rides on that pass rather than
    going unsaid.
    """
    out: list[Finding] = []
    bands = _drawn_rail_bands(ctx, rail)
    if not bands:
        # Nothing drawn to cross-check against. That is not a deficiency in the handrail and
        # must not demote the authored verdict — a resolver that drew no rail is a resolver
        # bug, and `integrity` is where one is reported. Said out loud on the pass instead of
        # passing silently on authored values while appearing to have measured something.
        return [], " (no rail solids resolved — not cross-checked against drawn geometry)"

    # --- R311.7.8.1, measured: the bar's own line above the nosings it rakes over --------
    #
    # Skipping the band that straddles a *flight junction*. Where a winder turn meets the
    # straight run, the nosing line turns 90 degrees away from a rail that carries straight
    # on past the corner, so within one band the nearest nosing changes flight and steps a
    # full riser. The rail is 36" over the nosing at each end of that band and the average
    # of the two in the middle, which is neither a defect in the rail nor something this
    # rule can put a number on — the code's datum ("the sloped plane adjoining the tread
    # nosing") is not single-valued there. Named rather than dropped.
    raking = flight_walklines(stair)
    heights, junctions = [], 0
    for point, centre_z, reach in bands:
        surface = walkline_z_at(raking, point, RAIL_LATERAL_REACH_M)
        if surface is None:
            continue
        span = _local_nosing_step_m(raking, point, reach)
        if span is not None and span > _JUNCTION_STEP_M:
            junctions += 1
            continue
        heights.append(centre_z - surface)
    if heights:
        low, high = min(heights), max(heights)
        if (low < MIN_HANDRAIL_HEIGHT.meters - 1e-6
                or high > MAX_HANDRAIL_HEIGHT.meters + 1e-6):
            out.append(_fail(cid, f"handrail {rail.tag} as drawn runs "
                             f"{low / 0.0254:.1f}\"-{high / 0.0254:.1f}\" above the nosings "
                             f"of {stair.tag}; R311.7.8.1 requires 34\"-38\" over the whole "
                             "flight", (rail.tag, stair.tag), "R311.7.8.1"))
    note = ("" if not junctions else
            f" ({junctions} band(s) at a flight junction not height-measured — the nosing "
            f"line turns away from the rail there and R311.7.8.1's datum is not "
            f"single-valued)")
    if not heights:
        return out, note + " (no measurable nosing line under it — height not cross-checked)"

    # --- R311.7.8.3, measured: a stated diameter has to be a graspable one ---------------
    diameter = _stated_round_diameter_m(rail)
    if diameter is not None and not (_MIN_TYPE_I_DIAMETER.meters - 1e-9 <= diameter
                                     <= _MAX_TYPE_I_DIAMETER.meters + 1e-9):
        out.append(_fail(cid, f"handrail {rail.tag} states a {diameter / 0.0254:.2f}\" "
                         "circular section; R311.7.8.3 Type I admits 1-1/4\"-2\"",
                         (rail.tag,), "R311.7.8.3"))
    return out, note


def _drawn_rail_bands(ctx: CheckContext, rail: Railing
                      ) -> list[tuple[tuple[float, float], float, float]]:
    """``(plan centre, bar centreline elevation, half the band's plan length)`` per band.

    A rail that carries a :class:`~typehaus.resolve.model.SolidSweep` *is* its centreline —
    one solid whose 3D polyline is exactly the line R311.7.8.1 measures. It is resampled at
    :data:`_BAND_SAMPLE_M` here rather than read vertex for vertex, because the sweep is
    simplified down to the points a carpenter cuts at (a straight flight is two of them) and
    both this rule and R311.7.8.2's nosing coverage want stations *along* the bar.

    The band-stack branch below it is the legacy prism reading, kept for any rail solid that
    carries no sweep: a round rail used to be faceted into a stack of solids sharing one plan
    axis, so the band was the stack, not the solid, and its centreline the middle of the
    stack's full z extent. Solids sharing an axis are split where they are not *touching* in
    z, because a guard with ``rail_count=2`` puts a top and a bottom rail on the same axis
    and averaging the pair would report a rail height halfway between them, which is nowhere.
    """
    out: list[tuple[tuple[float, float], float, float]] = []
    stacks: dict[tuple[float, float], list[ResolvedSolid]] = {}
    prefix = f"{rail.tag}-RAIL"
    for solid in ctx.model.solids:
        if not solid.tag.startswith(prefix):
            continue
        if solid.sweep is not None:
            out.extend(_sweep_bands(solid))
            continue
        if not solid.outline:
            continue
        cx = sum(x for x, _y in solid.outline) / len(solid.outline)
        cy = sum(y for _x, y in solid.outline) / len(solid.outline)
        stacks.setdefault((round(cx, 4), round(cy, 4)), []).append(solid)
    for (cx, cy), group in sorted(stacks.items()):
        widest = max(group, key=lambda solid: len(solid.outline))
        reach = max(math.hypot(x - cx, y - cy) for x, y in widest.outline)
        run: list[ResolvedSolid] = []
        for solid in sorted(group, key=lambda item: item.z0_m):
            if run and solid.z0_m > max(piece.z1_m for piece in run) + 1e-9:
                out.append(((cx, cy), _mid_z(run), reach))
                run = []
            run.append(solid)
        if run:
            out.append(((cx, cy), _mid_z(run), reach))
    return out


def _sweep_bands(solid: ResolvedSolid) -> list[tuple[tuple[float, float], float, float]]:
    """One station every :data:`_BAND_SAMPLE_M` along a swept rail's own 3D polyline."""
    path = clean_path(solid.sweep.path)
    bands: list[tuple[tuple[float, float], float, float]] = []
    for a, b in zip(path[:-1], path[1:], strict=True):
        run = math.hypot(b[0] - a[0], b[1] - a[1])
        steps = max(int(math.ceil(run / _BAND_SAMPLE_M)), 1)
        for k in range(steps):
            t = (k + 0.5) / steps
            bands.append(((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t),
                          a[2] + (b[2] - a[2]) * t, run / (2.0 * steps)))
    if not bands and path:
        bands.append(((path[0][0], path[0][1]), path[0][2], 0.0))
    return bands


def _mid_z(group: list[ResolvedSolid]) -> float:
    return (min(s.z0_m for s in group) + max(s.z1_m for s in group)) / 2.0


def _local_nosing_step_m(lines: list[list[tuple[float, float, float]]],
                         point: Vec, reach: float) -> float | None:
    """How far the sampled nosing elevation moves across one band's own footprint."""
    samples = []
    for dx, dy in ((reach, 0.0), (-reach, 0.0), (0.0, reach), (0.0, -reach)):
        z = walkline_z_at(lines, (point[0] + dx, point[1] + dy), RAIL_LATERAL_REACH_M)
        if z is not None:
            samples.append(z)
    return None if len(samples) < 2 else max(samples) - min(samples)


def flight_continuity_findings(ctx: CheckContext, stair: ResolvedStair,
                               serving: list[Railing], cid: str) -> list[Finding]:
    """R311.7.8.2 for one stair: is every flight of it covered by *some* handrail?

    ``continuous`` is an authored bool defaulting to ``True``, so it has never been evidence
    of anything. This is the measurement behind it.
    """
    bands = [band for rail in serving for band in _drawn_rail_bands(ctx, rail)]
    if not bands:
        return []
    unserved, total = _unserved_nosings(stair, bands)
    if not unserved:
        return []
    tags = tuple(rail.tag for rail in serving)
    return [_fail(cid, f"{stair.tag} has {unserved} of {total} nosings with no handrail "
                  f"within {_HANDRAIL_REACH_M / 0.0254:.0f}\" of them "
                  f"({', '.join(tags)} between them reach the rest); R311.7.8.2 requires a "
                  "handrail continuous for the full length of the flight, from a point "
                  "above the lowest riser to a point above the top riser",
                  (stair.tag, *tags), "R311.7.8.2")]


def _unserved_nosings(stair: ResolvedStair, bands: Bands) -> tuple[int, int]:
    """``(nosings with no rail within reach, nosings in the stair's flights)``.

    Measured nosing by nosing against the *riser lines themselves* — a station is
    ``(a, b, z)``, the full width of the tread — rather than against the reduced walking
    centreline. That distinction is the whole difficulty of a winder: its walking line is
    12" from the narrow end and swings away from the wall through the turn, while the
    treads themselves still run out to that wall, and a rail screwed to it is beside every
    one of them. Projecting the rail onto the centreline says the opposite.

    Landings are skipped (R311.7.8.2 permits an interruption at a turn or a landing) and so
    is the synthetic arrival station :func:`flight_stations` extends a tread flight by —
    the code measures to a point above the *top riser*, not out onto the deck past it.
    """
    unserved = total = 0
    for key, stations in flight_stations(stair).items():
        if not (key.startswith("tread") or key == "winder"):
            continue
        used = (stations[:-1] if key.startswith("tread") and len(stations) >= 3
                else stations)
        for a, b, _z in used:
            total += 1
            if not any(_point_to_segment_m(point, a, b) <= _HANDRAIL_REACH_M + 1e-9
                       for point, _z_band, _reach in bands):
                unserved += 1
    return unserved, total


def _point_to_segment_m(point: Vec, a: Vec, b: Vec) -> float:
    """Plan distance from ``point`` to the segment ``a→b``."""
    (px, py), (x0, y0), (x1, y1) = point, a, b
    dx, dy = x1 - x0, y1 - y0
    run2 = dx * dx + dy * dy
    t = 0.0 if run2 < 1e-18 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / run2))
    return math.hypot(px - (x0 + dx * t), py - (y0 + dy * t))


def _stated_round_diameter_m(rail: Railing) -> float | None:
    """The diameter a ``graspable_profile`` names, when it names a circular section."""
    from typehaus.resolve.railings.parts import round_rail_radius_m

    radius = round_rail_radius_m(rail, None, 0.0)
    return None if not radius else 2.0 * radius
