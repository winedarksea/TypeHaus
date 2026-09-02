"""R305 ceiling height and R401.3 lot drainage (→ 12).

Every rule is tri-state (#32): a rule that cannot evaluate reports UNKNOWN with the reason
and is counted separately, never as a pass.

The rest of the MN residential rules live in topic modules beside it (``egress``,
``stairs``, ``fall_protection``, ``alarms``, ``circulation``, ``fire_separation``,
``ventilation``, ``attic``), all sharing :mod:`._common`.
"""

from __future__ import annotations

from typing import Any

from typehaus.checks.code.mn_residential._common import (
    HABITABLE_OCCUPANCIES,
    SF_PER_M2,
    _fail,
    _foundation_footprint,
    _pass,
    _room_storey,
    _storey_is_below_grade,
    _unknown,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import Occupancy
from typehaus.model.refs import FollowRoof
from typehaus.quantities import Length, ft, inch, m
from typehaus.resolve.roof_geometry import roof_headroom_areas

#: Who R305.1 is *about*, as Minn. R. 1309.0305 names them: "habitable space, hallways,
#: bathrooms, toilet rooms, and laundry rooms". This is an ALLOWLIST on purpose. It used to
#: be a denylist of {UNCONDITIONED, GARAGE}, which meant every occupancy anyone added later
#: was silently graded against a habitable-space minimum without a decision being taken —
#: and it is how a storage pocket under an eave came to be judged by a rule that does not
#: reach it. A closet, a workshop, a pantry and a mechanical room are none of the five
#: things the sentence names, and grading one here is a category error, not strict reading.
_R305_SUBJECT = HABITABLE_OCCUPANCIES | frozenset({
    Occupancy.HALLWAY, Occupancy.BATHROOM, Occupancy.LAUNDRY,
})

#: The rooms outside that subject are not simply ungraded: Minn. R. 1309.0305 R305.1.1 gives
#: them their own, lower floor — "portions of basements that do not contain habitable space,
#: hallways, bathrooms, toilet rooms, and laundry rooms shall have a ceiling height of not
#: less than 6 feet 8 inches". So a basement utility space is still graded, at 6'-8". Above
#: grade the code says nothing about a closet's head height and neither does this check;
#: stairs have their own rule and their own finding (code.R311_7_2_stair_headroom).
_MIN_BASEMENT_CEILING = inch(80)

_MIN_CEILING = ft(7)
_MIN_SLOPED_CEILING = ft(5)
_MIN_SLOPED_CEILING_FRACTION = 0.5

#: R304.1 — the minimum floor area of a habitable room, and the base R305.1's sloped-ceiling
#: exception measures against. THIS IS THE WHOLE POINT OF THE EXCEPTION: both of its clauses
#: read "the *required* floor area", not "the room", and R304.3 says outright that floor
#: under 5'-0" "shall not be considered as contributing to the minimum required habitable
#: area". A 356 sf attic room has to find 70 good square feet inside itself; the other 286
#: may be any height at all, including none. Grading both clauses against the whole room
#: would make a story-and-a-half impossible to draw, which is a check bug, not a design
#: constraint. It is the reason catlin carried 5'-0" knee walls.
_MIN_HABITABLE_AREA_M2 = 70.0 / SF_PER_M2

# R401.3 lot drainage: grade must fall away from the foundation within the first 10'. Pervious
# ground needs 5% (6" per 10'), measured from spot elevations (code.R401_3_grading). Impervious
# surfaces (walks, patios, driveways, slabs abutting the house) need only 2%, evaluated from the
# authored ImperviousSurface hardscapes (code.R401_3_impervious).
_GRADING_BAND = ft(10)
_MIN_GROUND_SLOPE = 0.05  # 6" per 10' away from the foundation (pervious ground)
_MIN_IMPERVIOUS_SLOPE = 0.02  # 2% away from the foundation (walks/patios/slabs)
_SLOPE_EPS = 1e-3


@check(Tier.CODE, "code.R305_ceiling_height")
def ceiling_height(ctx: CheckContext) -> list[Finding]:
    """R305.1 clear height, measured to the structure that is actually overhead.

    ``Storey.default_ceiling_height`` is not a measurement — it
    is a convenience number the plan author types once per storey and nothing reconciles
    against the decks. Catlin's basement authors 9'-0" while the joisted halves and the EPS
    deck band over it leave 8'-3 1/2" and 8'-4 1/8" — the storey default runs eight inches
    generous. A room that authored 7'-6" over a deck that left 6'-9" would have PASSED.
    Grading a code minimum against a number the model never checks is grading nothing.

    So the underside is derived (``resolve/ceiling_over.py``, shared with the resilient-
    channel return so the drawing and the check cannot disagree), and the MINIMUM underside
    over the room's clear face governs — a room under two structures gets the lower of them,
    because that is the head somebody walks into. An explicit ``Room.ceiling`` still wins:
    a dropped or vaulted ceiling authored on the room is a statement about the room, not a
    guess about the deck.

    Where nothing covers the room the finding is UNKNOWN, not a pass on the storey default.
    A room with no ceiling element over it is a modelling gap, and saying so is the whole
    point of the tri-state.
    """
    out: list[Finding] = []
    for room in ctx.plan.all_elements():
        if room.element_kind != "Room":
            continue
        minimum, unknown_reason = _applicable_minimum(ctx, room)
        if unknown_reason is not None:
            out.append(_unknown("code.R305_ceiling_height", unknown_reason,
                                (room.tag,), "R305.1"))
            continue
        if minimum is None:
            continue
        if isinstance(room.ceiling, FollowRoof):
            out.append(_follow_roof_ceiling_finding(ctx, room, minimum))
            continue
        if room.ceiling is not None and hasattr(room.ceiling, "meters"):
            out.append(_graded_ceiling(room.tag, room.ceiling, "authored", minimum))
            continue
        derived, source = _derived_clear_height(ctx, room)
        if derived is None:
            out.append(_unknown("code.R305_ceiling_height", source, (room.tag,), "R305.1"))
        else:
            out.append(_graded_ceiling(room.tag, derived, source, minimum))
    return out


def _applicable_minimum(ctx: CheckContext,
                       room: Any) -> tuple[Length | None, str | None]:
    """``(clear height this room owes, UNKNOWN reason)``; both ``None`` where R305 is silent.

    Two tiers and a gap, which is exactly what the amended section says: R305.1's 7'-0" for
    its five named subjects, R305.1.1's 6'-8" for everything else *in a basement*, and
    nothing at all for a closet or a pantry above grade. The gap is deliberate and is not a
    coverage hole to be filled by grading those rooms anyway — a rule invented to keep a
    finding count up is worse than no finding.

    The one genuine unknown is the basement test. ``_storey_is_below_grade`` answers ``None``
    — not ``False`` — where the site states no grade datum, and "we do not know where grade
    is" is not "this storey is above it". A non-subject room on a storey we cannot place is
    a room whose applicable minimum we cannot name, so it reports UNKNOWN rather than
    silently passing out of scope.
    """
    if room.occupancy in _R305_SUBJECT:
        return _MIN_CEILING, None
    storey = _room_storey(ctx, room.tag)
    if storey is None:
        return None, None
    below = _storey_is_below_grade(ctx, storey)
    if below is None:
        return None, ("the site states no grade datum, so whether R305.1.1's 6'-8\" basement "
                      "minimum reaches this room cannot be decided")
    return (_MIN_BASEMENT_CEILING, None) if below else (None, None)


def _graded_ceiling(room_tag: str, height: Length, source: str,
                    minimum: Length) -> Finding:
    if height < minimum:
        return _fail("code.R305_ceiling_height",
                     f"{room_tag} ceiling {height.fmt()} < {minimum.fmt()} minimum ({source})",
                     (room_tag,), "R305.1")
    return _pass("code.R305_ceiling_height",
                 f"{room_tag} ceiling {height.fmt()} >= {minimum.fmt()} ({source})", "R305.1")


def _derived_clear_height(ctx: CheckContext,
                          room: Any) -> tuple[Length | None, str]:
    """``(clear height, source phrase)`` for a room with no authored ceiling.

    ``resolve.rooms`` derives the height once, over decks AND soffits — a walk that stopped
    at ``ceiling_over._is_ceiling_deck``, which admits a ``FloorSystem`` and a non-walking
    ``Slab`` only, would leave a ``Soffit`` invisible to it — and every consumer reads the
    same number: see ``ResolvedRoom.clear_height_m``.

    The height is measured from the room's FLOOR LEVEL, taken as its storey datum. That
    omits the subfloor sheet standing on the joists — a known and deliberate gap
    (``resolve.rooms.room_floor_elevation`` shares it, and closing it moves every placeable
    in every wood-floored room), so the derived height reads 3/4" GENEROUS on a joisted
    floor. Recorded so nobody reads the number as exact.

    ** THE SOFFITED AREA IS DELIBERATELY NOT A SEPARATE MINIMUM, AND THIS IS THE DECISION. **
    A flat "lowest point in the room must clear 7'-0"" would be wrong, not merely strict:
    SF-S-HP1 covers 47 sf of RM-S-STUDY2's 159 sf, and R305.1 has never asked that every
    square foot of a room be full height — R305.1's own sloped-ceiling exception and R304.3
    both say the opposite, that floor under a low head simply does not count toward the
    required area. The honest reading of a duct box is the same one
    ``_follow_roof_ceiling_finding`` applies to a rake: grade the required floor area, and
    let the room spend its surplus on the low bit. So a room whose UN-SOFFITED area still
    makes R304.1's 70 sf is graded on the deck height, and only a room that cannot is
    graded on the soffit. ``ResolvedRoom.soffit_area_m2`` is what makes that decidable, and
    catlin's two subjects (RM-S-HALL under SF-S-DUCT, RM-S-STUDY2 under SF-S-HP1) both keep
    well over 70 sf clear of their boxes.
    """
    storey = _room_storey(ctx, room.tag)
    resolved = next((item for item in ctx.model.rooms if item.tag == room.tag), None)
    if storey is None or resolved is None or len(resolved.clear_face) < 3:
        return None, "room does not resolve a clear face"
    if resolved.clear_height_m is None:
        return None, "no ceiling element over the room"
    unsoffited = resolved.area_m2 - resolved.soffit_area_m2
    if resolved.soffit_area_m2 > 1e-9 and unsoffited + 1e-9 >= _MIN_HABITABLE_AREA_M2:
        deck = _deck_only_clear_height(ctx, storey, resolved)
        if deck is not None:
            return m(deck), (
                f"clear under the deck; {unsoffited * SF_PER_M2:.0f} sf clear of "
                f"{resolved.soffit_area_m2 * SF_PER_M2:.0f} sf of soffit, which leaves more "
                f"than R304.1's required floor area at full height")
    return m(resolved.clear_height_m), "clear under the lowest ceiling element, soffits included"


def _deck_only_clear_height(ctx: CheckContext, storey: Any, resolved: Any) -> float | None:
    """Height to the deck alone, ignoring soffits — the surplus-area case above."""
    from shapely.geometry import Polygon

    from typehaus.resolve.ceiling_over import ceiling_decks_over, ceiling_underside_m

    face = Polygon([tuple(point) for point in resolved.clear_face])
    undersides = [value for value in
                  (ceiling_underside_m(deck_storey, deck)
                   for deck_storey, deck in ceiling_decks_over(ctx.plan, storey.tag, face))
                  if value is not None]
    if not undersides:
        return None
    return min(undersides) - storey.elevation.meters


def _follow_roof_ceiling_finding(ctx: CheckContext, room, minimum: Length) -> Finding:
    """R305.1's sloped-ceiling exception, graded against the REQUIRED floor area.

    Minn. R. 1309.0305, Exception 1: "at least 50 percent of the required floor area of the
    room shall have a ceiling height of at least 7 feet and no portion of the required floor
    area may have a ceiling height of less than 5 feet." Both clauses take *the required
    floor area* as their subject — R304.1's 70 sf — not the room. R304.3 completes the
    thought from the other side: floor under 5'-0" "shall not be considered as contributing
    to the minimum required habitable area for that room". So the sub-5' strip under a rake
    does not disqualify the room; it simply does not count, and a room only has to assemble
    70 good square feet somewhere inside itself.

    That makes the test decidable in closed form. ``roof_headroom_areas`` returns NESTED
    regions — the ≥7' area is inside the ≥5' area is inside the room — so the required floor
    area may always be taken from the tallest part of the room downward, and the best
    achievable fraction is ``min(at_seven, required) / required``. There is no packing
    problem to solve.

    NOT tested here, and the docstring is the only place that says so:

    * **R304.2's 7'-0" minimum horizontal dimension** over that required area.
      ``roof_headroom_areas`` returns scalars, not the qualifying polygon, so there is
      nothing here to measure a width on — a room could satisfy the area test with a 3'-wide
      ribbon and pass. That is a ``code.R304_2_*`` check with a geometry return, not a clause
      bolted onto this one. Do not read a pass here as a pass on R304.2.
    * The thresholds are compared against ``eave_z_m``/``ridge_z_m``, which are the roof
      DECK plane — the rafter-top, not the ceiling somebody stands under. The honest clear
      height is a rafter depth lower, so this check reads GENEROUS, by about two feet of
      station on a 6:12. Fixing it means adding the structure depth at both call sites and
      re-blessing ``code.R807_1_attic_access`` with it, which is its own change.
    """
    roof = next((item for item in ctx.model.roofs if item.tag == room.ceiling.roof_ref), None)
    resolved_room = next((item for item in ctx.model.rooms if item.tag == room.tag), None)
    storey = _room_storey(ctx, room.tag)
    if roof is None or resolved_room is None or storey is None:
        return _unknown("code.R305_ceiling_height", "unresolved roof-following ceiling",
                        (room.tag,), "R305.1")
    elevation = storey.elevation.meters
    area, at_min = roof_headroom_areas(
        resolved_room.clear_face, roof, elevation, minimum.meters,
    )
    _, at_five = roof_headroom_areas(
        resolved_room.clear_face, roof, elevation, _MIN_SLOPED_CEILING.meters,
    )
    if area <= 1e-9:
        return _unknown("code.R305_ceiling_height", "room has no area beneath referenced roof",
                        (room.tag,), "R305.1")
    # A room smaller than R304.1's 70 sf has to make the whole of itself work; a larger one
    # only has to find 70 sf, and may spend the remainder on rake.
    required = min(area, _MIN_HABITABLE_AREA_M2)
    achieved = min(at_min, required) / required
    detail = (f"{required * SF_PER_M2:.0f} sf required floor area, "
              f"{at_five * SF_PER_M2:.0f} sf at or above 5'-0\", "
              f"{at_min * SF_PER_M2:.0f} sf at or above {minimum.fmt()} "
              f"(room is {area * SF_PER_M2:.0f} sf)")
    if at_five + 1e-9 < required:
        return _fail(
            "code.R305_ceiling_height",
            f"{room.tag} cannot assemble a required floor area above 5'-0\" — {detail}",
            (room.tag,), "R305.1",
        )
    if achieved + 1e-9 < _MIN_SLOPED_CEILING_FRACTION:
        return _fail(
            "code.R305_ceiling_height",
            f"{room.tag} has {achieved:.0%} of its required floor area at or above "
            f"{minimum.fmt()}; R305.1's sloped-ceiling exception needs 50% — {detail}",
            (room.tag,), "R305.1",
        )
    return _pass("code.R305_ceiling_height",
                 f"{room.tag} follows {roof.tag}: {achieved:.0%} of its required floor area "
                 f"at or above {minimum.fmt()} — {detail}", "R305.1")


@check(Tier.CODE, "code.R401_3_grading")
def foundation_grading(ctx: CheckContext) -> list[Finding]:
    """R401.3 lot drainage — grade must fall away from the foundation within 10 feet.

    The primary building footprint is reconstructed from the foundation walls; every spot
    elevation outside it and within 10' is a drainage station, and the shallowest measured
    slope must reach 5% (6" per 10'). Impervious-surface grading (2%) is the sibling
    requirement asserted separately by ``code.R401_3_impervious``.
    """
    from shapely.geometry import Point

    site = ctx.plan.project.site
    if site.grade is None:
        return [_unknown("code.R401_3_grading", "no average-grade datum on the site",
                         (), "R401.3")]
    if not site.spot_elevations:
        return [_unknown("code.R401_3_grading",
                         "no spot elevations to measure grade slope", (), "R401.3")]
    if not any(wall.is_foundation for wall in ctx.model.walls):
        return [_unknown("code.R401_3_grading", "no foundation walls to grade around",
                         (), "R401.3")]
    footprint = _foundation_footprint(ctx)
    if footprint is None:
        return [_unknown("code.R401_3_grading",
                         "could not reconstruct a foundation footprint", (), "R401.3")]
    boundary = footprint.exterior

    grade_m = site.grade.meters
    band_m = _GRADING_BAND.meters
    worst: tuple[float, float, float] | None = None  # (slope, distance_m, elevation_m)
    stations = 0
    for spot in site.spot_elevations:
        point = Point(spot.position.xy_m)
        if footprint.covers(point):
            continue  # interior grade point, not a perimeter drainage station
        distance_m = boundary.distance(point)
        if distance_m <= 1e-6 or distance_m > band_m + 1e-9:
            continue
        stations += 1
        elevation_m = spot.elevation.meters
        slope = (grade_m - elevation_m) / distance_m  # positive = falls away from the wall
        if worst is None or slope < worst[0]:
            worst = (slope, distance_m, elevation_m)
    if worst is None:
        return [_unknown("code.R401_3_grading",
                         "no spot elevations within 10' of the building foundation",
                         (), "R401.3")]
    slope, distance_m, elevation_m = worst
    if slope + _SLOPE_EPS < _MIN_GROUND_SLOPE:
        fall_in = (grade_m - elevation_m) / 0.0254
        run_ft = distance_m / 0.3048
        return [_fail("code.R401_3_grading",
                      f"grade only falls {slope * 100:.1f}% away from the foundation "
                      f"({fall_in:+.1f}\" over {run_ft:.1f}'); R401.3 requires "
                      f"{_MIN_GROUND_SLOPE * 100:.0f}% (6\" within 10')", (), "R401.3")]
    return [_pass("code.R401_3_grading",
                  f"grade falls at least {_MIN_GROUND_SLOPE * 100:.0f}% away from the foundation "
                  f"at all {stations} station(s) within 10' (shallowest {slope * 100:.1f}%)",
                  "R401.3")]


@check(Tier.CODE, "code.R401_3_impervious")
def impervious_surface_grading(ctx: CheckContext) -> list[Finding]:
    """R401.3 — impervious surfaces abutting the house must slope >= 2% away from the foundation.

    Each authored ``ImperviousSurface`` (walk/patio/driveway/slab) whose nearest edge lies within
    10' of the primary foundation footprint is a station. The run away from the foundation comes
    from the outline (far-edge reach minus near-edge reach), the fall from the authored near/far
    grade elevations, and the shallowest surface slope must reach 2%. Mirrors
    ``code.R401_3_grading`` and emits one finding for the worst surface.
    """
    from shapely.geometry import Point

    site = ctx.plan.project.site
    surfaces = getattr(site, "impervious_surfaces", ())
    if not surfaces:
        return []  # no impervious surfaces modeled abutting the foundation; rule does not apply
    footprint = _foundation_footprint(ctx)
    if footprint is None:
        return [_unknown("code.R401_3_impervious",
                         "no foundation footprint to grade impervious surfaces against",
                         (), "R401.3")]
    boundary = footprint.exterior
    band_m = _GRADING_BAND.meters
    worst: tuple[float, str, float, float] | None = None  # (slope, label, run_m, drop_m)
    stations = 0
    for surface in surfaces:
        verts = [p.xy_m for p in surface.outline]
        if len(verts) < 2:
            continue
        dists = [boundary.distance(Point(v)) for v in verts]
        near_i = min(range(len(verts)), key=dists.__getitem__)
        far_i = max(range(len(verts)), key=dists.__getitem__)
        if dists[near_i] > band_m + 1e-9:
            continue  # surface lies entirely beyond 10' of the foundation
        run_m = dists[far_i] - dists[near_i]
        if run_m <= _SLOPE_EPS:
            continue  # degenerate outline with no reach away from the foundation
        stations += 1
        drop_m = surface.near_elevation.meters - surface.far_elevation.meters
        slope = drop_m / run_m  # positive = falls away from the foundation
        if worst is None or slope < worst[0]:
            worst = (slope, surface.label, run_m, drop_m)
    if worst is None:
        return []  # no impervious surface within 10' of the foundation to grade
    slope, label, run_m, drop_m = worst
    if slope + _SLOPE_EPS < _MIN_IMPERVIOUS_SLOPE:
        fall_in = drop_m / 0.0254
        run_ft = run_m / 0.3048
        return [_fail("code.R401_3_impervious",
                      f"impervious surface '{label}' only falls {slope * 100:.1f}% away from the "
                      f"foundation ({fall_in:+.1f}\" over {run_ft:.1f}'); R401.3 requires "
                      f"{_MIN_IMPERVIOUS_SLOPE * 100:.0f}% for walks/patios/slabs", (), "R401.3")]
    return [_pass("code.R401_3_impervious",
                  f"impervious surfaces slope at least {_MIN_IMPERVIOUS_SLOPE * 100:.0f}% away "
                  f"from the foundation at all {stations} surface(s) within 10' "
                  f"(shallowest {slope * 100:.1f}% at '{label}')", "R401.3")]
