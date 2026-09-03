"""R311.7 stairways — built geometry, headroom, width, landings and handrails.

Split out of ``rules.py`` unchanged. The doctrine here is measure-the-output: every rule
reads the *resolved* members rather than re-deriving the flight from authored inputs, which
is what caught a stretched first riser that authored rise and riser count agreed on.
"""

from __future__ import annotations

import math

from shapely.geometry import Point, Polygon

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.code.mn_residential.handrail_geometry import (
    MAX_HANDRAIL_HEIGHT,
    MIN_HANDRAIL_HEIGHT,
    drawn_handrail_findings,
    flight_continuity_findings,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, not_applicable
from typehaus.quantities import ft, inch
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.roof_geometry import roof_underside_at
from typehaus.resolve.stairs.walkline import flight_stations

_MAX_STAIR_RISER = inch(7.75)
_MIN_STAIR_GOING = inch(10)
_MIN_STAIR_HEADROOM = ft(6, 8)
_MIN_STAIR_WIDTH = inch(36)  # R311.7.1, above the handrail / between finished walls
_MIN_STAIR_LANDING_DEPTH = inch(36)  # R311.7.6, in the direction of travel
_MIN_HANDRAIL_RISERS = 4  # R311.7.8: required on flights with four or more risers
# R311.7.8.1: handrail top measured above the sloped nosing line, not above any floor.
# Plumb-clearance sampling along the sloped nosing line: plan step between samples, and
# where across the flight each station is probed (both edges + centre — the worst point
# under a raking well header is at one side, not the middle).
_HEADROOM_SAMPLE_STEP_M = 0.05
_HEADROOM_LATERAL_FRACTIONS = (0.0, 0.5, 1.0)
# An obstruction must clear the walking surface by at least this to count as *overhead*
# rather than the surface's own construction.
_HEADROOM_OVERHEAD_EPS_M = 0.001
# Floor/soffit cover shrinks by this before containment: stair edges are authored on the
# well's edges, so boundary samples otherwise flip between in-void and under-deck on
# float summation error. 5 mm decides no real header.
_HEADROOM_PLAN_EPS_M = 0.005


@check(Tier.CODE, "code.R311_7_stair_geometry")
def stair_geometry(ctx: CheckContext) -> list[Finding]:
    """Verify the built walking sequence reaches the next finished floor with code geometry.

    The resolver owns the exact opening and roof geometry.  This check intentionally measures
    its output rather than re-solving it from authored inputs, catching a dropped/level tread
    even when the design rise and riser count still look mathematically consistent.
    """
    if not ctx.model.stairs:
        return [_unknown("code.R311_7_stair_geometry", "no resolved stairs", (), "R311.7")]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        source = ctx.plan.storey(stair.storey)
        target = ctx.plan.storey(stair.to_storey)
        if source is None or target is None:
            out.append(_unknown("code.R311_7_stair_geometry", "unresolved stair storey",
                                (stair.tag,), "R311.7"))
            continue
        walking = sorted(member.z1_m for member in stair.members
                         if member.category in {"tread", "winder", "landing"})
        # The flight's own ends where it states them. A run between two storeys states
        # nothing and the storey table is the answer, exactly as before; a step-down within
        # one storey states both, and re-deriving them from ``from_storey``/``to_storey``
        # would grade it against a datum it never touches.
        springing = (stair.base_elevation_m if stair.base_elevation_m is not None
                     else source.elevation.meters)
        arrival = (stair.arrival_elevation_m if stair.arrival_elevation_m is not None
                   else target.elevation.meters)
        expected = [springing + stair.riser_height_m * step
                    for step in range(1, stair.riser_count)]
        # Headroom is NOT this check's business: it is a plumb measurement against the
        # overhead structure, made by code.R311_7_2_stair_headroom. Reporting the arrival
        # storey's nominal ceiling height here — as this check once did — is not headroom.
        valid = (
            stair.riser_height_m <= _MAX_STAIR_RISER.meters + 1e-9
            and stair.going_depth_m >= _MIN_STAIR_GOING.meters - 1e-9
            and len(walking) == len(expected)
            and all(abs(actual - wanted) <= 1e-6
                    for actual, wanted in zip(walking, expected, strict=True))
            and abs(springing + stair.riser_count * stair.riser_height_m - arrival) <= 1e-6
        )
        if valid:
            out.append(_pass("code.R311_7_stair_geometry",
                             f"{stair.tag} reaches {stair.to_storey} with "
                             f"{stair.riser_count} built risers at "
                             f"{stair.riser_height_m / .0254:.2f}\" on a "
                             f"{stair.going_depth_m / .0254:.1f}\" going", "R311.7"))
        else:
            out.append(_fail("code.R311_7_stair_geometry",
                             f"{stair.tag} fails built rise or going",
                             (stair.tag,), "R311.7"))
    return out


# The per-flight nosing-station derivation moved to ``resolve/stairs/walkline.py`` so the
# accessory resolver can rake a ``serves_stair`` Railing along the very line these checks
# measure. Re-exported under its historical name: ``fall_protection.py`` (and tests) import
# ``_flight_stations`` from this module.
_flight_stations = flight_stations


def _walk_samples(stations):
    """Points ``(x, y, z)`` densely covering the sloped walking line between stations."""
    for (a0, b0, z0), (a1, b1, z1) in zip(stations, stations[1:], strict=False):
        span = max(math.hypot(a1[0] - a0[0], a1[1] - a0[1]),
                   math.hypot(b1[0] - b0[0], b1[1] - b0[1]))
        steps = max(1, math.ceil(span / _HEADROOM_SAMPLE_STEP_M))
        for step in range(steps + 1):
            t = step / steps
            ax, ay = a0[0] + (a1[0] - a0[0]) * t, a0[1] + (a1[1] - a0[1]) * t
            bx, by = b0[0] + (b1[0] - b0[0]) * t, b0[1] + (b1[1] - b0[1]) * t
            z = z0 + (z1 - z0) * t
            for u in _HEADROOM_LATERAL_FRACTIONS:
                yield (ax + (bx - ax) * u, ay + (by - ay) * u, z)


@check(Tier.CODE, "code.R311_7_2_stair_headroom")
def stair_headroom(ctx: CheckContext) -> list[Finding]:
    """Measure the plumb clearance from the sloped nosing line to the structure above.

    A storey's nominal ceiling height is not headroom over any tread, so
    ``code.R311_7_stair_geometry`` does not answer this. Here every flight's nosing line is
    sampled and probed plumb against the resolved
    overhead structure: floor decks (outside their stair-well voids) down to their
    deepest framing, roof planes at their structural underside, and soffit faces.
    Structure only — ceiling finishes, freestanding beams and ducts are not modeled
    against the walk — and never PASS by absence: a stair with something over it that this
    engine did not resolve reports UNKNOWN.

    The one case that is not a gap is a flight with nothing over it *in plan at all*: no
    floor deck, no roof footprint and no soffit outline covers a single sample of its
    walking line. That is open sky, which is positive evidence that R311.7.2's subject does
    not exist here rather than an absence of data, so it earns NOT_APPLICABLE. Two things
    keep that from becoming a pass-by-absence in disguise:

    * Plan containment is tested SEPARATELY from the plumb probe. A deck whose underside is
      *below* the nosings covers the flight in plan and keeps it UNKNOWN — the flight passes
      over something, and what is above that something has not been accounted for.
    * The model must resolve at least one **roof** before the absence means anything. A house
      whose envelope is not modelled has no cover polygons for any reason, and "no roof in
      the model" is a gap, not a sky.
    """
    cid, code = "code.R311_7_2_stair_headroom", "R311.7.2"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    floors = []
    for floor in ctx.model.floors:
        if not floor.deck_outline:
            continue
        underside = min([member.z0_m for member in floor.members] + [floor.deck_z0_m])
        cover = Polygon(floor.deck_outline,
                        holes=[list(void) for void in floor.deck_voids]
                        ).buffer(-_HEADROOM_PLAN_EPS_M)
        if not cover.is_empty:
            floors.append((cover, underside, floor.tag))
    roofs = [(Polygon(roof.footprint), roof) for roof in ctx.model.roofs if roof.footprint]
    soffits = []
    for soffit in ctx.model.soffits:
        if not soffit.outline:
            continue
        cover = Polygon(soffit.outline).buffer(-_HEADROOM_PLAN_EPS_M)
        if not cover.is_empty:
            soffits.append((cover, soffit.z0_m, soffit.tag))
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        worst: tuple[float, tuple[float, float], str] | None = None
        covered = False  # anything at all standing over the walk in plan
        for stations in _flight_stations(stair).values():
            for x, y, z in _walk_samples(stations):
                point = Point(x, y)
                lowest: tuple[float, str] | None = None
                if not covered:
                    covered = (any(p.contains(point) for p, _, _ in floors)
                               or any(p.contains(point) for p, _ in roofs)
                               or any(p.contains(point) for p, _, _ in soffits))
                for polygon, underside, tag in floors:
                    if (underside > z + _HEADROOM_OVERHEAD_EPS_M and polygon.contains(point)
                            and (lowest is None or underside < lowest[0])):
                        lowest = (underside, tag)
                for polygon, roof in roofs:
                    if polygon.contains(point):
                        underside = roof_underside_at(ctx.model, roof, (x, y))
                        if underside > z + _HEADROOM_OVERHEAD_EPS_M and (
                                lowest is None or underside < lowest[0]):
                            lowest = (underside, roof.tag)
                for polygon, underside, tag in soffits:
                    if (underside > z + _HEADROOM_OVERHEAD_EPS_M and polygon.contains(point)
                            and (lowest is None or underside < lowest[0])):
                        lowest = (underside, tag)
                if lowest is None:
                    continue
                clearance = lowest[0] - z
                if worst is None or clearance < worst[0]:
                    worst = (clearance, (x, y), lowest[1])
        if worst is None:
            if not covered and roofs:
                out.append(not_applicable(
                    cid, f"{stair.tag} is open to the sky — no floor deck, roof plane or "
                    "soffit stands over any point of its walking line, so R311.7.2 has no "
                    "headroom to measure", (stair.tag,), code))
                continue
            out.append(_unknown(cid, f"{stair.tag}: no resolved structure overhead of "
                                "the walking line (floors, roofs, soffits)",
                                (stair.tag,), code))
            continue
        clearance, (x, y), tag = worst
        where = (f"{clearance / .3048:.2f}' plumb under {tag} at "
                 f"({x / .3048:.1f}', {y / .3048:.1f}')")
        if clearance >= _MIN_STAIR_HEADROOM.meters - 1e-9:
            out.append(_pass(cid, f"{stair.tag} headroom {where} (>= 6'-8\"; structure "
                             "only, finishes unmodeled)", code))
        else:
            out.append(_fail(cid, f"{stair.tag} headroom {where} < 6'-8\"",
                             (stair.tag, tag), code))
    return out


# R311.7.1's clear-width-past-handrail limits: 31.5" with a handrail on one side of the
# flight, 27" with handrails both sides. Measured against the authored rail's plan line
# plus the 1.5" section the resolver frames (half of it each side of the line).
_MIN_WIDTH_PAST_ONE_RAIL = inch(31.5)
_MIN_WIDTH_PAST_TWO_RAILS = inch(27)
_RAIL_HALF_SECTION = inch(0.75)
# A rail whose plan line sits farther than this outside a flight's tread edge belongs to
# some other run (the same stair's opposite lane), not to this flight's side.
_RAIL_LATERAL_REACH = inch(12)
_RAIL_PARALLEL_DOT = 0.9  # rail runs along the flight, not across it


def _flight_rail_projections(stair, rails) -> dict[str, tuple[float, float, float]]:
    """Per straight flight, ``(width, low-side projection, high-side projection)`` in m.

    Geometry is measured, never assumed: the flight's edges come off its tread boards'
    endpoints, the handrail's plan line off the authored path. A rail counts against a
    flight when it runs parallel to it, overlaps its run extent, and sits within
    ``_RAIL_LATERAL_REACH`` of one edge; its projection into the flight is however far the
    near face of its 1.5" section reaches past that edge. Winders are excluded exactly as
    before — only ``tread`` boards define a lane.
    """
    flights: dict[str, list] = {}
    for member in stair.members:
        if member.category == "tread":
            flights.setdefault(member.child_key.rsplit("-", 1)[0], []).append(member)
    out: dict[str, tuple[float, float, float]] = {}
    for key, treads in flights.items():
        (x0, y0), (x1, y1) = treads[0].p0, treads[0].p1
        span = math.hypot(x1 - x0, y1 - y0)
        if span < 1e-9:
            continue
        cross = ((x1 - x0) / span, (y1 - y0) / span)  # across the lane
        run = (-cross[1], cross[0])  # along the climb

        def c_of(p, cross=cross):  # noqa: E306 - tiny projection helpers, scoped to this flight
            return p[0] * cross[0] + p[1] * cross[1]

        def r_of(p, run=run):
            return p[0] * run[0] + p[1] * run[1]

        ends = [p for t in treads for p in (t.p0, t.p1)]
        e0, e1 = min(c_of(p) for p in ends), max(c_of(p) for p in ends)
        r0, r1 = min(r_of(p) for p in ends), max(r_of(p) for p in ends)
        proj0 = proj1 = 0.0
        for rail in rails:
            pts = [p.xy_m for p in rail.path]
            for a, b in zip(pts[:-1], pts[1:], strict=True):
                seg = math.hypot(b[0] - a[0], b[1] - a[1])
                if seg < 1e-9:
                    continue
                u = ((b[0] - a[0]) / seg, (b[1] - a[1]) / seg)
                if abs(u[0] * run[0] + u[1] * run[1]) < _RAIL_PARALLEL_DOT:
                    continue
                if min(r_of(a), r_of(b)) > r1 or max(r_of(a), r_of(b)) < r0:
                    continue  # alongside a different flight of the same stair
                c = c_of(((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0))
                if not (e0 - _RAIL_LATERAL_REACH.meters <= c
                        <= e1 + _RAIL_LATERAL_REACH.meters):
                    continue
                if abs(c - e0) <= abs(c - e1):
                    proj0 = max(proj0, min(c + _RAIL_HALF_SECTION.meters - e0, e1 - e0))
                else:
                    proj1 = max(proj1, min(e1 - (c - _RAIL_HALF_SECTION.meters), e1 - e0))
        out[key] = (e1 - e0, max(proj0, 0.0), max(proj1, 0.0))
    return out


@check(Tier.CODE, "code.R311_7_1_stair_width")
def stair_width(ctx: CheckContext) -> list[Finding]:
    """Built flight width from the tread boards (R311.7.1: 36" minimum), and — now that
    handrails are authored elements — the clear width past them.

    Two numbers per flight, both measured off the output: 36" between finished walls
    (the minimum tread board), and where a ``serves_stair`` handrail runs alongside a
    flight, the width that remains past the rail's 1.5" section — 31.5" with a rail on
    one side, 27" with rails both sides. Until the handrail role existed this check
    could only measure the first number. The winder turn is excluded: its width is the
    turn square's by construction, and its own code minimums are the narrow-end and
    walk-line checks.
    """
    cid, code = "code.R311_7_1_stair_width", "R311.7.1"
    from typehaus.model.structure import Railing

    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    plan = getattr(ctx, "plan", None)
    handrails = [e for e in plan.all_elements() if isinstance(e, Railing)
                 and e.role in ("handrail", "guard_and_handrail")] if plan else []
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        widths = [member.length_m for member in stair.members
                  if member.category == "tread"]
        if not widths:
            out.append(_unknown(cid, f"{stair.tag} has no tread boards to measure",
                                (stair.tag,), code))
            continue
        width = min(widths)
        if width < _MIN_STAIR_WIDTH.meters - 1e-9:
            out.append(_fail(cid, f"{stair.tag} flight width {width / .0254:.2f}\" "
                             "< 36\"", (stair.tag,), code))
            continue
        serving = [r for r in handrails if r.serves_stair == stair.tag]
        if not serving:
            out.append(_pass(cid, f"{stair.tag} flight width {width / .0254:.2f}\" "
                             ">= 36\" (no handrail authored to project into it)", code))
            continue
        clear_fail = False
        worst: tuple[float, float, int] | None = None  # (clear, limit, sides)
        for key, (flight_w, proj0, proj1) in sorted(
                _flight_rail_projections(stair, serving).items()):
            sides = (proj0 > 1e-9) + (proj1 > 1e-9)
            if sides == 0:
                continue
            clear = flight_w - proj0 - proj1
            limit = (_MIN_WIDTH_PAST_TWO_RAILS if sides == 2
                     else _MIN_WIDTH_PAST_ONE_RAIL).meters
            if worst is None or clear - limit < worst[0] - worst[1]:
                worst = (clear, limit, sides)
            if clear < limit - 1e-9:
                clear_fail = True
                out.append(_fail(cid, f"{stair.tag} {key} clears {clear / .0254:.2f}\" "
                                 f"past its handrail{'s' if sides == 2 else ''}; "
                                 f"R311.7.1 requires {limit / .0254:.1f}\"",
                                 (stair.tag,), code))
        if clear_fail:
            continue
        if worst is None:
            out.append(_pass(cid, f"{stair.tag} flight width {width / .0254:.2f}\" "
                             ">= 36\" (its handrails project into no measured flight)",
                             code))
        else:
            clear, limit, sides = worst
            out.append(_pass(cid, f"{stair.tag} flight width {width / .0254:.2f}\" "
                             f">= 36\" and {clear / .0254:.2f}\" clear past "
                             f"{'handrails both sides' if sides == 2 else 'its handrail'} "
                             f"(>= {limit / .0254:.1f}\")", code))
    return out


@check(Tier.CODE, "code.R311_7_6_landing_depth")
def stair_landing_depth(ctx: CheckContext) -> list[Finding]:
    """Built landing platforms measured off the members (R311.7.6).

    Two numbers, on two axes: 36" in the direction of travel (the deck member's run),
    and never narrower than the stairway served (its swept width against the widest
    tread). The resolver *floors* authored depths at 36", but this measures what was
    built — the doctrine that caught the stretched first risers is measure-the-output,
    not trust-the-generator. Stairs without landing members (a straight or winder run
    between floors) have nothing to measure: the floors they arrive at serve as the
    R311.7.6 landing.
    """
    cid, code = "code.R311_7_6_landing_depth", "R311.7.6"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        stair_width_m = max([member.length_m for member in stair.members
                             if member.category == "tread"], default=0.0)
        for member in stair.members:
            if member.category != "landing":
                continue
            depth = member.length_m
            width = cross_section(member.profile).width_m
            if depth < _MIN_STAIR_LANDING_DEPTH.meters - 1e-9:
                out.append(_fail(cid, f"{stair.tag} {member.child_key} runs "
                                 f"{depth / .0254:.2f}\" in the direction of travel "
                                 "< 36\"", (stair.tag,), code))
            elif width < stair_width_m - 1e-9:
                out.append(_fail(cid, f"{stair.tag} {member.child_key} is "
                                 f"{width / .0254:.2f}\" wide, narrower than the "
                                 f"{stair_width_m / .0254:.2f}\" stairway it serves",
                                 (stair.tag,), code))
            else:
                out.append(_pass(cid, f"{stair.tag} {member.child_key} "
                                 f"{depth / .0254:.2f}\" deep x {width / .0254:.2f}\" "
                                 "wide", code))
    return out


@check(Tier.CODE, "code.R311_7_8_handrail")
def stair_handrail(ctx: CheckContext) -> list[Finding]:
    """R311.7.8 — a flight of four or more risers has a graspable handrail 34"-38" up.

    This reported UNKNOWN for as long as it existed, because nothing in the model *was* a
    handrail: a ``Railing`` was a guard — a plan path with a height — with no role, no
    graspability and no continuity. It now carries all three, so the rule measures.

    The height datum is the one thing worth being careful about. A guard's ``height`` is
    measured from the deck it stands on; a handrail's is measured from the *nosings*, which
    on a flight is a sloped line, not a floor. That is why ``top_height`` is a separate
    field rather than a reuse of ``height`` — reusing it would silently measure a stair
    handrail from the landing at the bottom of the flight.
    """
    cid, code = "code.R311_7_8_handrail", "R311.7.8"
    from typehaus.model.structure import Railing

    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    railings: list | None = None  # looked up lazily: a house of short flights needs none
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        if stair.riser_count < _MIN_HANDRAIL_RISERS:
            out.append(_pass(cid, f"{stair.tag} has {stair.riser_count} risers — no "
                             "handrail required", code))
            continue
        if railings is None:
            railings = [e for e in ctx.plan.all_elements() if isinstance(e, Railing)
                        and e.role in ("handrail", "guard_and_handrail")]
        serving = [r for r in railings if r.serves_stair == stair.tag]
        if not serving:
            # Distinguish "no handrail" from "handrails are not authored in this house at
            # all". The first is a deficiency; the second is a modeling gap, and calling it
            # a deficiency would fail every house that has not adopted the field yet.
            if not railings:
                out.append(_unknown(cid, f"{stair.tag} ({stair.riser_count} risers) requires "
                                    "a handrail and no Railing in the plan declares a "
                                    "handrail role", (stair.tag,), code))
            else:
                out.append(_fail(cid, f"{stair.tag} ({stair.riser_count} risers) has no "
                                 "handrail; R311.7.8 requires one on every flight of four "
                                 "or more risers", (stair.tag,), code))
            continue
        for rail in serving:
            top = rail.top_height
            if top is None:
                out.append(_unknown(cid, f"handrail {rail.tag} on {stair.tag} states no "
                                    "top_height above the nosings", (rail.tag,), code))
            elif not (MIN_HANDRAIL_HEIGHT.meters - 1e-9 <= top.meters
                      <= MAX_HANDRAIL_HEIGHT.meters + 1e-9):
                out.append(_fail(cid, f"handrail {rail.tag} on {stair.tag} tops out at "
                                 f"{top.inches:.1f}\" above the nosings; R311.7.8.1 requires "
                                 "34\"-38\"", (rail.tag, stair.tag), "R311.7.8.1"))
            elif not rail.continuous:
                out.append(_fail(cid, f"handrail {rail.tag} on {stair.tag} is not continuous "
                                 "for the full length of the flight",
                                 (rail.tag, stair.tag), "R311.7.8.2"))
            elif rail.graspable_profile is None:
                out.append(_unknown(cid, f"handrail {rail.tag} on {stair.tag} states no "
                                    "graspable_profile, so R311.7.8.3 type I/II "
                                    "graspability cannot be evaluated", (rail.tag,),
                                    "R311.7.8.3"))
            else:
                drawn, note = drawn_handrail_findings(ctx, stair, rail, cid)
                out.extend(drawn)
                if not drawn:
                    out.append(_pass(cid, f"{stair.tag} has handrail {rail.tag} at "
                                     f"{top.inches:.1f}\" ({rail.graspable_profile}) as "
                                     f"drawn, continuous{note}", code))
        # Continuity is the one question that belongs to the *stair*, not to any one rail:
        # ST-B2M is two lanes with a rail apiece, and asking each rail whether it covers
        # the other lane's flight would fail both for doing exactly what they should.
        out.extend(flight_continuity_findings(ctx, stair, serving, cid))
    return out
