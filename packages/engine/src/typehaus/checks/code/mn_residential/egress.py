"""R310 emergency escape and R311.2 egress door width.

Split out of ``rules.py``. R310.1 is two rules, not one: every *sleeping room* needs an
escape opening, and so does every *basement* whether or not anyone sleeps in it. Only the
first was encoded.
"""

from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.checks.code.mn_residential._common import (_fail, _pass, _room_windows,
                                                         _rooms_by_storey,
                                                         _storey_is_below_grade, _unknown,
                                                         _wall_is_exterior)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import SLEEPING_OCCUPANCIES, Occupancy
from typehaus.quantities import inch

_MIN_EGRESS_WIDTH = inch(20)
_MIN_EGRESS_HEIGHT = inch(24)
_MAX_EGRESS_SILL = inch(44)
_MIN_EGRESS_AREA_SF = 5.7  # grade-floor 5.0; upper 5.7 (R310.2.1)
_MIN_DOOR_CLEAR = inch(31.75)  # 32" nominal clear (R311.2)

# R310.1 applies to a basement holding habitable space. "Habitable" is R202's list — living,
# sleeping, eating, cooking — and explicitly excludes bathrooms, closets, halls, storage and
# utility space, which is why a mechanical-only cellar is not on the hook for an escape
# opening and a finished rec room is.
HABITABLE_OCCUPANCIES = frozenset({
    Occupancy.BEDROOM, Occupancy.LIVING, Occupancy.DINING, Occupancy.KITCHEN,
    Occupancy.MEDIA, Occupancy.OFFICE,
})


def _meets_r310_2_1(opening, *, grade_floor: bool) -> bool:
    """Does this opening satisfy the R310.2.1 net-clear dimensions?"""
    area_sf = opening.width_m * opening.height_m * 10.7639
    minimum = 5.0 if grade_floor else _MIN_EGRESS_AREA_SF
    return (opening.width_m >= _MIN_EGRESS_WIDTH.meters
            and opening.height_m >= _MIN_EGRESS_HEIGHT.meters
            and area_sf >= minimum
            and opening.sill_m <= _MAX_EGRESS_SILL.meters)


@check(Tier.CODE, "code.R310_egress")
def egress_windows(ctx: CheckContext) -> list[Finding]:
    """Every sleeping room needs a compliant emergency escape opening (R310)."""
    out: list[Finding] = []
    for room in ctx.plan.all_elements():
        if room.element_kind != "Room" or room.occupancy not in SLEEPING_OCCUPANCIES:
            continue
        resolved_room = next((item for item in ctx.model.rooms if item.tag == room.tag), None)
        wins = _room_windows(ctx, resolved_room, Point, Polygon)
        best = next((op for op in wins if _meets_r310_2_1(op, grade_floor=False)), None)
        if best is not None:
            out.append(_pass("code.R310_egress",
                             f"{room.tag} has egress window {best.tag}", "R310.1"))
        elif not wins:
            out.append(_fail("code.R310_egress",
                             f"sleeping room {room.tag} has no egress window", (room.tag,),
                             "R310.1"))
        else:
            out.append(_fail("code.R310_egress",
                             f"sleeping room {room.tag} window fails egress dimensions",
                             (room.tag,), "R310.2"))
    return out


@check(Tier.CODE, "code.R310_1_storey_egress")
def basement_storey_egress(ctx: CheckContext) -> list[Finding]:
    """R310.1 — a basement with habitable space needs its own escape opening.

    The sibling rule ``code.R310_egress`` walks sleeping rooms; this walks *storeys*. A
    finished basement rec room with no bedroom in it is the case both an inspector and the
    old checklist missed: nobody sleeps there, so no room-level rule fires, and the only way
    out in a fire is back up the stair the fire is in.

    Openings are counted broadly and deliberately: an exterior door satisfies R310.1 outright
    (a walkout basement is the ordinary way to comply), and an opening is *not* filtered on
    having a resolved window type. This house's sunken-garden archways are ``RoughOpening``
    elements with ``type_ref=None`` — 64 sf of unobstructed opening each — and a
    type-ref filter would have reported a false FAIL against them.
    """
    cid, code = "code.R310_1_storey_egress", "R310.1"
    out: list[Finding] = []
    rooms_by_storey = _rooms_by_storey(ctx)
    for storey in ctx.plan.storeys:
        rooms = [e for e in ctx.plan.storey_elements(storey.tag)
                 if e.element_kind == "Room" and e.occupancy in HABITABLE_OCCUPANCIES]
        if not rooms:
            continue
        below = _storey_is_below_grade(ctx, storey)
        if below is None:
            out.append(_unknown(cid, f"storey {storey.tag} holds habitable space but the "
                                "site states no average-grade datum, so it cannot be "
                                "classified as a basement", (storey.tag,), code))
            continue
        if not below:
            continue
        room_tags = {room.tag for room in rooms}
        found = None
        for opening in ctx.model.openings:
            wall = ctx.model.wall(opening.host_wall)
            if wall is None or wall.storey != storey.tag:
                continue
            if not _wall_is_exterior(ctx, wall, rooms_by_storey):
                continue
            # An exterior door out of the storey is an escape route by itself; R310.1 asks
            # for an opening "opening directly into a public way, yard or court".
            if opening.is_door or _meets_r310_2_1(opening, grade_floor=True):
                found = opening
                break
        if found is not None:
            kind = "door" if found.is_door else "opening"
            out.append(_pass(cid, f"basement storey {storey.tag} escapes through exterior "
                             f"{kind} {found.tag}", code))
        else:
            out.append(_fail(cid, f"basement storey {storey.tag} holds habitable space "
                             f"({', '.join(sorted(room_tags))}) with no exterior escape "
                             "opening meeting R310.2.1", (storey.tag, *sorted(room_tags)),
                             code))
    return out


# R311.3: a landing or floor on each side of an exterior door, 36" in the direction of
# travel and no narrower than the door.
_MIN_LANDING_DEPTH = inch(36)
# R311.3.1: the exterior landing may sit at most 1.5" below the threshold. A door that is not
# the required egress door and does not swing over the landing gets 7.75" (one riser).
_MAX_LANDING_STEP_DOWN = inch(1.5)
_MAX_NONREQUIRED_STEP_DOWN = inch(7.75)


@check(Tier.CODE, "code.R311_3_exterior_landing")
def exterior_door_landing(ctx: CheckContext) -> list[Finding]:
    """R311.3 — every exterior door lands on something 36" deep and no more than a step down.

    The landing is not a distinct element in this model and does not need to be: what R311.3
    asks for is a *surface*, and four kinds of authored surface already are one — an
    ``ImperviousSurface`` hardscape (a stoop or walk), a slab, a deck's ``deck_outline``, and
    a stair's landing platform. The test is coverage: project a 36"-deep rectangle outward
    from the door and ask whether one of them covers it.

    Every candidate is filtered by elevation first, and that is not a refinement — it is what
    makes the rule mean anything. In the plan frame a second-floor deck door sits directly
    over the sunken-garden patio, and a coverage test that ignores z reports that the door
    "lands on" a slab twenty feet below it. So a surface qualifies only if its top sits at
    the threshold or within one riser under it, which is also exactly R311.3.1's own
    measurement — presence and step-down turn out to be one test, not two.
    """
    cid, code = "code.R311_3_exterior_landing", "R311.3"
    door_types = {t.tag: t for t in ctx.plan.library.door_types}
    rooms_by_storey = _rooms_by_storey(ctx)
    surfaces = _landing_surfaces(ctx)
    storeys = {s.tag: s for s in ctx.plan.storeys}
    out: list[Finding] = []
    for opening in ctx.model.openings:
        if not opening.is_door:
            continue
        door_type = door_types.get(opening.type_ref)
        if door_type is None or not getattr(door_type, "exterior", False):
            continue
        if getattr(getattr(door_type, "operation", None), "value", None) == "overhead":
            # A sectional garage door is a vehicular opening. R311.3 is about the floor or
            # landing on each side of a door people walk through; requiring a 36" stoop at
            # the head of a driveway would be reading it against its own subject.
            continue
        wall = ctx.model.wall(opening.host_wall)
        storey = storeys.get(wall.storey) if wall else None
        if wall is None or storey is None:
            out.append(_unknown(cid, f"{opening.tag} resolves no host wall and storey to "
                                "project a landing from", (opening.tag,), code))
            continue
        if not surfaces:
            out.append(_unknown(cid, f"{opening.tag} is an exterior door but the plan models "
                                "no walk, slab, deck or stair landing to measure against",
                                (opening.tag,), code))
            continue
        patch = _landing_patch(ctx, wall, opening, rooms_by_storey)
        if patch is None:
            out.append(_unknown(cid, f"{opening.tag} has a degenerate host-wall axis",
                                (opening.tag,), code))
            continue
        threshold = storey.elevation.meters + opening.sill_m
        covered = [(name, top) for name, poly, top in surfaces
                   if threshold - _MAX_NONREQUIRED_STEP_DOWN.meters - 1e-6 <= top
                   <= threshold + 0.05
                   and poly.intersection(patch).area >= patch.area * _LANDING_COVERAGE]
        if not covered:
            wrong_height = sorted({name for name, poly, _top in surfaces
                                   if poly.intersection(patch).area
                                   >= patch.area * _LANDING_COVERAGE})
            hint = (f" ({', '.join(wrong_height)} covers the patch in plan but sits more "
                    "than one riser below the threshold)" if wrong_height else "")
            out.append(_fail(cid, f"{opening.tag} has no landing: nothing at threshold height "
                             f"covers the 36\"-deep patch outside it{hint}; R311.3 requires a "
                             "floor or landing on each side of every exterior door",
                             (opening.tag,), code))
            continue
        name, top = max(covered, key=lambda item: item[1])
        step = threshold - top
        if step > _MAX_LANDING_STEP_DOWN.meters + 1e-6:
            # Still a landing, and still legal for a door that is not the required egress
            # door and does not swing out over it. Which door is *the* required egress door
            # is not modeled, so this reports the allowance rather than assuming the strict
            # case and failing an ordinary back door.
            out.append(_pass(cid, f"{opening.tag} lands on {name}, {step / .0254:.1f}\" below "
                             "the threshold — within R311.3.1's one-riser allowance for a "
                             "non-required door that does not swing over the landing", code))
        else:
            out.append(_pass(cid, f"{opening.tag} lands on {name}, {step / .0254:.1f}\" below "
                             "the threshold (<= 1.5\")", code))
    return out


# How much of the 36" patch a surface must cover to be its landing. Not 1.0: the patch is
# projected from the wall *axis* offset by half the wall thickness, so its inner edge can
# clip a stoop authored to the finished face.
_LANDING_COVERAGE = 0.85


def _landing_surfaces(ctx: CheckContext):
    """(label, polygon, top_elevation_m) for every surface that can serve as a landing."""
    from shapely.geometry import Polygon

    out = []
    for surface in getattr(ctx.plan.project.site, "impervious_surfaces", ()):
        verts = [p.xy_m for p in surface.outline]
        if len(verts) >= 3:
            # The near edge is the one against the building, which is the edge a door lands
            # on; the far edge is lower by the 2% fall R401.3 requires of it.
            out.append((f"'{surface.label}'", Polygon(verts), surface.near_elevation.meters))
    for solid in ctx.model.solids:
        if solid.category == "slab" and len(solid.outline) >= 3:
            out.append((solid.tag, Polygon(solid.outline), solid.z1_m))
    for floor in ctx.model.floors:
        if floor.deck_outline and len(floor.deck_outline) >= 3:
            out.append((floor.tag, Polygon(floor.deck_outline), floor.deck_z1_m))
    for stair in ctx.model.stairs:
        for member in stair.members:
            if member.category == "landing" and member.plan_outline:
                ring = list(member.plan_outline)
                if len(ring) >= 3:
                    out.append((f"{stair.tag}/{member.child_key}", Polygon(ring), member.z1_m))
    return [(name, poly, top) for name, poly, top in out
            if poly.is_valid and poly.area > 1e-9]


def _landing_patch(ctx: CheckContext, wall, opening, rooms_by_storey):
    """The 36"-deep rectangle outside the door, in the plan frame."""
    from shapely.geometry import Point, Polygon

    (sx, sy), (ex, ey) = wall.axis
    run = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    if run <= 1e-9:
        return None
    ux, uy = (ex - sx) / run, (ey - sy) / run
    nx, ny = -uy, ux
    cx = sx + ux * opening.center_along_m
    cy = sy + uy * opening.center_along_m
    # Outward is whichever side has no room on it. Both sides roomless (a garden wall) or
    # both occupied cannot happen for a door the type calls exterior, but if it does, the
    # positive normal is as good a guess as any and the coverage test still decides.
    reach = wall.thickness_m / 2.0 + 0.15
    rooms = rooms_by_storey.get(wall.storey, ())
    sign = 1.0
    if any(poly.covers(Point(cx + nx * reach, cy + ny * reach)) for _r, poly in rooms):
        sign = -1.0
    half = max(opening.width_m, 0.1) / 2.0
    depth = _MIN_LANDING_DEPTH.meters
    base_x, base_y = cx + nx * sign * wall.thickness_m / 2.0, cy + ny * sign * wall.thickness_m / 2.0
    corners = [
        (base_x - ux * half, base_y - uy * half),
        (base_x + ux * half, base_y + uy * half),
        (base_x + ux * half + nx * sign * depth, base_y + uy * half + ny * sign * depth),
        (base_x - ux * half + nx * sign * depth, base_y - uy * half + ny * sign * depth),
    ]
    patch = Polygon(corners)
    return patch if patch.is_valid and patch.area > 1e-9 else None


@check(Tier.CODE, "code.R311_door_width")
def egress_door_width(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for door in (e for e in ctx.plan.all_elements() if e.element_kind == "Door"):
        dt = next((t for t in ctx.plan.library.door_types if t.tag == door.type_ref), None)
        if dt is None:
            out.append(_unknown("code.R311_door_width", "unknown door type",
                                (door.tag,), "R311.2"))
            continue
        if dt.exterior and dt.width < _MIN_DOOR_CLEAR:
            out.append(_fail("code.R311_door_width",
                             f"egress door {door.tag} width {dt.width.fmt()} < 32\" clear",
                             (door.tag,), "R311.2"))
        else:
            out.append(_pass("code.R311_door_width", f"door {door.tag} width ok", "R311.2"))
    return out


# R310.2.3: a well serving a below-grade escape opening is at least 9 sf, and at least 36"
# in both horizontal projection and width. Deeper than 44" it needs a fixed ladder or steps.
_MIN_WELL_AREA_SF = 9.0
_MIN_WELL_DIMENSION = inch(36)
_MAX_WELL_DEPTH_WITHOUT_LADDER = inch(44)
_MIN_WELL_LADDER_WIDTH = inch(12)


@check(Tier.CODE, "code.R310_2_3_window_well")
def window_well(ctx: CheckContext) -> list[Finding]:
    """R310.2.3 — a below-grade escape opening has a well you can actually climb out of.

    Applicability is the interesting half. A well is required exactly where an escape
    opening's sill sits below the grade outside it, so this walks the openings first and the
    wells second — a house whose escape openings are all above grade scope-passes, and one
    whose below-grade opening has no well reports UNKNOWN rather than PASS, because the
    absence of a well element is not evidence of an unobstructed opening.
    """
    from typehaus.model.site import WindowWell

    cid, code = "code.R310_2_3_window_well", "R310.2.3"
    grade = ctx.plan.project.site.grade
    if grade is None:
        return [_unknown(cid, "the site states no average-grade datum, so no opening can be "
                         "classified as below grade", (), code)]
    storeys = {s.tag: s for s in ctx.plan.storeys}
    wells = {w.serves_opening: w for w in ctx.plan.all_elements()
             if isinstance(w, WindowWell)}

    below: list = []
    for opening in ctx.model.openings:
        if opening.is_door:
            continue
        wall = ctx.model.wall(opening.host_wall)
        storey = storeys.get(wall.storey) if wall else None
        if storey is None:
            continue
        if not _meets_r310_2_1(opening, grade_floor=True):
            continue  # not an escape opening, so R310.2.3 has nothing to serve
        if storey.elevation.meters + opening.sill_m < grade.meters - 1e-6:
            below.append(opening)
    if not below:
        return [_pass(cid, "no emergency escape opening sits below grade, so no window well "
                      "is required", code)]

    out: list[Finding] = []
    for opening in below:
        well = wells.get(opening.tag)
        if well is None:
            out.append(_unknown(cid, f"escape opening {opening.tag} sits below grade and no "
                                "WindowWell serves it; R310.2.3 requires one, and its "
                                "absence from the model is not evidence there is none",
                                (opening.tag,), code))
            continue
        area_sf = _ring_area_sf(well.outline)
        xs = [p.xy_m[0] for p in well.outline]
        ys = [p.xy_m[1] for p in well.outline]
        span_x, span_y = max(xs) - min(xs), max(ys) - min(ys)
        smallest = min(span_x, span_y)
        depth = ctx.plan.project.site.grade.meters - well.floor_elevation.meters
        if area_sf + 1e-6 < _MIN_WELL_AREA_SF:
            out.append(_fail(cid, f"{well.tag} is {area_sf:.1f} sf; R310.2.3 requires 9 sf "
                             "of net clear area", (well.tag, opening.tag), code))
        elif smallest + 1e-9 < _MIN_WELL_DIMENSION.meters:
            out.append(_fail(cid, f"{well.tag} measures {smallest / .0254:.0f}\" across; "
                             "R310.2.3 requires 36\" of both projection and width",
                             (well.tag, opening.tag), code))
        elif depth > _MAX_WELL_DEPTH_WITHOUT_LADDER.meters + 1e-9 and not well.ladder:
            out.append(_fail(cid, f"{well.tag} is {depth / .0254:.0f}\" deep with no ladder; "
                             "R310.2.3.1 requires permanently affixed steps or a ladder "
                             "over 44\"", (well.tag, opening.tag), "R310.2.3.1"))
        elif (well.ladder and well.ladder_width is not None
              and well.ladder_width.meters + 1e-9 < _MIN_WELL_LADDER_WIDTH.meters):
            out.append(_fail(cid, f"{well.tag}'s ladder is "
                             f"{well.ladder_width.inches:.0f}\" wide; R310.2.3.1 requires "
                             "12\"", (well.tag,), "R310.2.3.1"))
        else:
            out.append(_pass(cid, f"{well.tag} serves {opening.tag}: {area_sf:.1f} sf, "
                             f"{smallest / .0254:.0f}\" across, {depth / .0254:.0f}\" deep",
                             code))
    return out


def _ring_area_sf(outline) -> float:
    from shapely.geometry import Polygon

    if len(outline) < 3:
        return 0.0
    polygon = Polygon([p.xy_m for p in outline])
    return polygon.area * 10.7639 if polygon.is_valid else 0.0
