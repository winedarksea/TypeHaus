"""Soffit framing: the two-ladder box that hangs a dropped ceiling (→ 11 §Framing).

A soffit resolved only as a solid is a shape, not construction — nothing in the BOM, the
framing sheets, or the interference check knows there is lumber inside it. This module
turns a soffit's authored ``FramingSpec`` into the members a carpenter actually builds:
two vertical ladder frames, one per long side, tied together by rungs.

**Why the stock size is load-bearing.** catlin's SF-S-DUCT is 32" wide and carries two
14" round ducts side by side — 28" of duct. Two 2x2 ladders leave ~29.5" between their
inner faces before lining; two 2x4 ladders leave 25" and the ducts do not fit at all.
So the spec on that soffit is deliberately 2x2, and this generator frames whatever stock
the spec names — never widening to a default 2x4, and never assuming a size when the
spec is absent (a soffit with ``framing=None`` frames nothing at all).

The lining costs more than that rationale allows for, and this module is where it
becomes visible: a 32" *finished* box gives up 2 x 5/8" of gypsum before any lumber, so
the clear span between two 2x2 ladders is 27.75" — a quarter inch short of the pair of
ducts. The generator does not quietly recover it by framing to the finished face; the
box has to be drawn wider (see ``tests/test_soffit_framing.py``).

v1 handles axis-aligned rectangles only. A non-rectangular soffit gets a WARN/UNKNOWN
finding rather than guessed geometry: an L-shaped duct chase is a different framing
problem (it has an internal corner to post), and inventing a ladder for it would put
wrong lumber in the take-off under a passing build.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.findings import Finding, Result, Severity
from typehaus.quantities import inch
from typehaus.resolve.framing.solver import _module_stations
from typehaus.resolve.framing.tables import DEFAULT_SPACING, member_actual
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedSoffit

# The gypsum lining wrapping the finished box. Members are framed *inside* it on every
# face, so the resolved solid stays the finished dimension the drawings carry and the
# lumber does not poke through its own skin.
SOFFIT_LINING_THICKNESS = inch(0.625)

#: The ``FramedMember.key`` prefix every ladder rung carries. Exported because
#: ``checks/structural/soffit.py`` grades exactly these members and nothing else — the
#: rails do not span, they are screwed to the deck — and a check that re-derived the
#: rung set from geometry could drift from what this generator actually builds.
SOFFIT_RUNG_KEY_PREFIX = "soffit-rung-"

# Plan tolerance for "this outline is an axis-aligned rectangle" (metres). Authored
# corners come from foot/inch quantities, so they land on the box exactly; this only
# absorbs float round-trip noise.
_RECT_TOLERANCE_M = 1e-6


@dataclass(frozen=True)
class SoffitClearSection:
    """The usable cavity inside a framed soffit — **derived**, never authored.

    Every clearance claim about a duct box in this house used to be hand arithmetic in a
    plan comment ("the plan's 2'-8" box loses 4 1/4" total to framing/lining, leaving only
    27 3/4" clear"). The arithmetic was right, but a comment cannot be re-run when the
    ``FramingSpec`` changes from 2x2 to 2x3, and nothing was checking that the two 14"
    ducts it was computed for still fit. An authored ``clear_width`` would have been no
    better: it is a second source of truth for a number the framing already states.

    So the section comes off exactly the geometry :func:`_frame_one` builds — the lining
    on every face, then a ladder rail of stock depth down each long side, then the rails
    top and bottom — and the check reads it. ``long_axis`` is the direction the box runs;
    ``across`` and ``z`` bound the cavity, ``along`` bounds the run.
    """

    long_axis: str  # "x" | "y" — the direction the ladders run
    along: tuple[float, float]  # between the two end blocking pieces
    across: tuple[float, float]  # clear cavity, between the two ladders' inner faces
    z: tuple[float, float]  # from the top of the bottom rungs to the deck above

    @property
    def width_m(self) -> float:
        return self.across[1] - self.across[0]

    @property
    def drop_m(self) -> float:
        return self.z[1] - self.z[0]


def soffit_clear_section(soffit: ResolvedSoffit) -> SoffitClearSection | None:
    """The cavity inside ``soffit``, or None when it has no framing to derive one from.

    None rather than a guess in the two cases :func:`_frame_one` also declines: a soffit
    with no ``FramingSpec`` (drawn but not built, so there is no lumber to measure against)
    and a non-rectangular one (v1 frames rectangles only). A caller that cannot get a
    section reports UNKNOWN — it does not fall back to the finished box, which would credit
    the run with 4 1/4" of gypsum and lumber as if it were air.
    """
    if soffit.framing is None:
        return None
    box = _rectangle(soffit.outline)
    if box is None:
        return None
    rail_profile, rung_profile = _ladder_stock(soffit.framing)
    rail_thickness, rail_depth = _stock_actual_m(rail_profile)
    rung_thickness, _rung_depth = _stock_actual_m(rung_profile)
    lining = SOFFIT_LINING_THICKNESS.meters
    minx, miny, maxx, maxy = box
    x0, x1 = minx + lining, maxx - lining
    y0, y1 = miny + lining, maxy - lining
    z_bottom, z_top = soffit.z0_m + lining, soffit.z1_m - lining
    if x1 <= x0 or y1 <= y0 or z_top - z_bottom <= rail_thickness + rung_thickness:
        return None
    long_is_x = (x1 - x0) >= (y1 - y0)
    along_raw = (x0, x1) if long_is_x else (y0, y1)
    across_raw = (y0, y1) if long_is_x else (x0, x1)
    # The two ladders eat a full stock *depth* off each long side; the end blocking closes
    # each end with a piece of stock *thickness*.
    across = (across_raw[0] + rail_depth, across_raw[1] - rail_depth)
    along = (along_raw[0] + rail_thickness, along_raw[1] - rail_thickness)
    if across[1] <= across[0] or along[1] <= along[0]:
        return None
    # Vertically the cavity runs from the top of the bottom rungs — the only members that
    # cross the box — to the deck the soffit hangs from. The *top* rail is deliberately not
    # subtracted: it sits directly over the bottom rail, one stock depth in from each long
    # face, which is already outside ``across``. Subtracting it too would take 1 1/2" off
    # the middle of the box where there is nothing, and that missing inch and a half is the
    # difference between EQ-S-HP1-AH's 11" case fitting SF-S-DUCT and not.
    return SoffitClearSection(
        long_axis="x" if long_is_x else "y", along=along, across=across,
        z=(z_bottom + rung_thickness, z_top),
    )


def frame_soffits(model: ResolvedModel) -> list[Finding]:
    """Generate ladder framing for every soffit that authored a ``FramingSpec``."""
    findings: list[Finding] = []
    for soffit in model.soffits:
        if soffit.framing is None:
            continue
        members, soffit_findings = _frame_one(soffit)
        soffit.members = members
        findings.extend(soffit_findings)
    return findings


def _ladder_stock(spec: object) -> tuple[str, str]:
    """``(rail_profile, rung_profile)`` for one ``FramingSpec``.

    A soffit ladder is two sticks doing two jobs, and framing them out of one profile —
    which this module did until 2026-08-31 — makes both jobs worse. The RAIL is a plate:
    it is screwed to the deck above, it carries nothing between supports, and its *depth*
    is what sets the cavity width the ducts and machines have to fit in. The RUNG spans
    the box: it is the member deflection is about, and it is the nailer the underside
    gypsum hangs on.

    So they take the two fields ``FramingSpec`` already has. ``plate_member`` is documented
    as "the plate size when it differs from ``member``" and the rails are already emitted
    with category ``"plate"``; ``member`` stays the rung. Defaulting ``plate_member`` to
    ``member`` leaves every soffit that does not set it framed byte-identically.

    This is what lets SF-S-HP1's rungs go to 2x4 for L/495 while its rails stay 2x2 — the
    72 3/4" clear cavity and the cavity floor both unmoved, which a single-profile upsize
    could not do (it takes one stock depth off each long side and evicts the mixing box).
    """
    member = getattr(spec, "member", "2x4") or "2x4"
    rail = getattr(spec, "plate_member", None) or member
    return rail, member


def _stock_actual_m(nominal: str) -> tuple[float, float]:
    """Dressed (thickness, depth) of the spec's member, in metres.

    Soffit ladders run small stock (2x2, 2x3); ``tables.LUMBER_ACTUAL`` carries those
    rows, so it stays the single source for dressed sizes.
    """
    thickness_in, depth_in = member_actual(nominal)
    return inch(thickness_in).meters, inch(depth_in).meters


def _rectangle(outline) -> tuple[float, float, float, float] | None:
    """The outline's (minx, miny, maxx, maxy) when it *is* that rectangle, else None."""
    points = [(round(x, 9), round(y, 9)) for x, y in outline]
    # A closed ring may repeat its first point; that is still a rectangle.
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    if len(points) != 4:
        return None
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    if maxx - minx <= _RECT_TOLERANCE_M or maxy - miny <= _RECT_TOLERANCE_M:
        return None
    corners = {(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)}
    for x, y in points:
        near = next((c for c in corners
                     if abs(c[0] - x) <= _RECT_TOLERANCE_M
                     and abs(c[1] - y) <= _RECT_TOLERANCE_M), None)
        if near is None:
            return None
        corners.discard(near)
    return minx, miny, maxx, maxy


def _frame_one(soffit: ResolvedSoffit) -> tuple[list[FramedMember], list[Finding]]:
    box = _rectangle(soffit.outline)
    if box is None:
        return [], [Finding(
            severity=Severity.WARN, check_id="framing.soffit_shape",
            message=(f"soffit {soffit.tag} is not an axis-aligned rectangle; its framing "
                     "cannot be generated (v1 frames rectangular soffits only)"),
            element_tags=(soffit.tag,), result=Result.UNKNOWN,
            fix_hint="split the soffit into rectangular segments, or drop its FramingSpec",
        )]
    spec = soffit.framing
    rail_profile, rung_profile = _ladder_stock(spec)
    thickness, depth = _stock_actual_m(rail_profile)
    rung_thickness, _rung_depth = _stock_actual_m(rung_profile)
    spacing_q = getattr(spec, "spacing", None) or DEFAULT_SPACING
    spacing = spacing_q.meters

    lining = SOFFIT_LINING_THICKNESS.meters
    minx, miny, maxx, maxy = box
    # Every face of the finished box gives up the lining before any lumber is placed.
    x0, x1 = minx + lining, maxx - lining
    y0, y1 = miny + lining, maxy - lining
    z_bottom, z_top = soffit.z0_m + lining, soffit.z1_m - lining
    if x1 - x0 <= 0 or y1 - y0 <= 0 or z_top - z_bottom <= thickness + rung_thickness:
        return [], [Finding(
            severity=Severity.WARN, check_id="framing.soffit_shape",
            message=(f"soffit {soffit.tag} is too small to frame in {rail_profile}: its "
                     "lined interior does not clear the ladder rails"),
            element_tags=(soffit.tag,), result=Result.UNKNOWN,
        )]

    # The ladders run the long way; the rungs span the short way.
    long_is_x = (x1 - x0) >= (y1 - y0)
    run_length = (x1 - x0) if long_is_x else (y1 - y0)
    side_keys = ("s", "n") if long_is_x else ("w", "e")
    end_keys = ("w", "e") if long_is_x else ("s", "n")
    # Rail centrelines: one stock depth in from each long face of the lined interior.
    side_low = (y0 if long_is_x else x0) + depth / 2.0
    side_high = (y1 if long_is_x else x1) - depth / 2.0
    span_low = (y0 if long_is_x else x0) + depth  # inner face of the low-side ladder
    span_high = (y1 if long_is_x else x1) - depth
    run_origin = x0 if long_is_x else y0
    run_direction = (1.0, 0.0) if long_is_x else (0.0, 1.0)

    def point(station: float, across: float) -> tuple[float, float]:
        along = run_origin + station
        return (along, across) if long_is_x else (across, along)

    # Both end stations plus the module grid, from the same helper the wall solver uses,
    # so a soffit hung under a 16" o.c. deck shares that deck's rhythm instead of
    # inventing a second one. Stations are local to the soffit run, as they are local to
    # the wall run there.
    end_stations = (thickness / 2.0, run_length - thickness / 2.0)
    stations = sorted(_module_stations(run_length, spacing, thickness, end_stations,
                                       end_stations))

    members: list[FramedMember] = []

    # --- ladder rails: continuous top + bottom plate down each long side --------
    for side_key, across in zip(side_keys, (side_low, side_high), strict=True):
        start, end = point(0.0, across), point(run_length, across)
        for name, rail_z0 in (("top", z_top - thickness), ("bottom", z_bottom)):
            members.append(FramedMember(
                soffit.uid, f"soffit-plate-{name}-{side_key}", "plate", rail_profile,
                start, end, rail_z0, rail_z0 + thickness, run_length,
            ))

    # --- ladder studs: one per side per station, between the rails --------------
    stud_z0, stud_z1 = z_bottom + thickness, z_top - thickness
    for index, station in enumerate(stations):
        for side_key, across in zip(side_keys, (side_low, side_high), strict=True):
            at = point(station, across)
            members.append(FramedMember(
                soffit.uid, f"soffit-stud-{index:03d}-{side_key}", "stud", rail_profile,
                at, at, stud_z0, stud_z1, stud_z1 - stud_z0, orient=run_direction,
            ))

    # --- rungs: the bottom tie across the box at each interior station ----------
    # The two end stations are closed by end blocking instead — a rung there would sit in
    # the same square, which reads as two members where the carpenter cuts one.
    rung_length = span_high - span_low
    for index, station in enumerate(stations):
        if any(abs(station - end) <= _RECT_TOLERANCE_M for end in end_stations):
            continue
        members.append(FramedMember(
            soffit.uid, f"{SOFFIT_RUNG_KEY_PREFIX}{index:03d}", "blocking", rung_profile,
            point(station, span_low), point(station, span_high),
            z_bottom, z_bottom + rung_thickness, rung_length,
        ))

    # --- end blocking: the full-depth piece closing each end of the box ---------
    for end_key, station in zip(end_keys, end_stations, strict=True):
        members.append(FramedMember(
            soffit.uid, f"soffit-end-{end_key}", "blocking", rail_profile,
            point(station, span_low), point(station, span_high),
            stud_z0, stud_z1, rung_length,
        ))

    return members, []
