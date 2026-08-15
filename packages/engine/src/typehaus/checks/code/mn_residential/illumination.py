"""R303.7/R303.8 stairway illumination and R302.7 under-stair protection.

Three rules that share a subject — the stair — and that a plan reviewer reads off the
lighting plan and the stair section rather than the framing plan. All three were absent
from the profile while the model already carried everything needed to grade them: resolved
stairs with riser counts, a full luminaire schedule with ``controlled_by`` switch legs, and
rooms whose occupancy says whether a space is enclosed and used.

What each rule actually asks, and what is graded here:

* **R303.7** — an interior stairway has a light source over its treads and landings, and a
  wall switch *at each floor level* where the flight has six or more risers. The switch
  count is the half that gets missed on drawings, and it is exactly what ``controlled_by``
  already records.
* **R303.8** — an exterior stairway has a light at the *top* landing, and one at the bottom
  as well where it descends to a basement from outdoor grade. This house has both shapes.
* **R302.7** — an enclosed space under a stair, reached by a door, is lined with 1/2"
  gypsum on the enclosed side. Applicability is a geometry question (is there a room under
  the flight?) followed by an access question (does a door open into it?).

Illuminance itself is not graded. R303.7's 1 foot-candle at the tread centre is a
photometric result, and this model carries lamp *types*, not IES files; asserting a lux
level from a fixture count would be inventing an answer. Presence and switching are the
plan-reviewable half, and they are what these rules report.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import Occupancy
from typehaus.quantities import ft
from typehaus.resolve.geometry import opening_center

# R303.7: "a wall switch at each floor level ... where the stairway has six or more risers".
_SWITCHED_RISER_THRESHOLD = 6
# How far from the stair outline a luminaire still counts as lighting it. A ceiling fixture
# over a stair well is rarely inside the run's own plan ring — it hangs over the landing or
# just off the top nosing — so the ring is buffered rather than tested for containment.
_STAIR_LIGHT_REACH = ft(4)
# Rooms that are enclosed usable space rather than circulation. R302.7's subject is the
# closet or store under the flight, not the stair hall the flight stands in.
_UNDER_STAIR_OCCUPANCIES = frozenset({
    Occupancy.STORAGE, Occupancy.UTILITY, Occupancy.MECHANICAL, Occupancy.BATHROOM,
})


def _stair_outline(stair):
    from shapely.geometry import Polygon

    if not stair.outline or len(stair.outline) < 3:
        return None
    polygon = Polygon(stair.outline)
    return polygon if polygon.is_valid and polygon.area > 1e-9 else None


def _lights_near(ctx: CheckContext, region, storeys: set[str]) -> list:
    """Luminaires and light runs whose plan position lands in ``region``, on ``storeys``."""
    from shapely.geometry import LineString, Point

    out = []
    for storey in ctx.plan.storeys:
        if storey.tag not in storeys:
            continue
        for element in ctx.plan.storey_elements(storey.tag):
            kind = element.element_kind
            if kind == "LightRun":
                if len(element.path) >= 2 and region.intersects(
                        LineString([p.xy_m for p in element.path])):
                    out.append(element)
            elif (kind == "ElectricalDevice"
                  and getattr(element.kind, "value", None) == "light"
                  and region.covers(Point(*element.position.xy_m))):
                out.append(element)
    return out


def _switch_storeys(ctx: CheckContext, lights) -> set[str]:
    """The storeys carrying a wall switch that controls any of ``lights``."""
    wanted = {name for light in lights for name in (getattr(light, "controlled_by", ()) or ())}
    if not wanted:
        return set()
    found = set()
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            if (element.element_kind == "ElectricalDevice"
                    and getattr(element.kind, "value", None) == "switch"
                    and element.tag in wanted):
                found.add(storey.tag)
    return found


def _stair_is_indoors(ctx: CheckContext, stair, region) -> bool:
    """Does a conditioned room stand over this stair's footprint?

    Derived rather than named, for the same reason the envelope rules derive an exterior
    wall: there is no ``Stair.exterior`` flag, and a tag-prefix test would compile one
    house's naming into the engine. R303.7 and R303.8 split on exactly this answer.
    """
    from shapely.geometry import Polygon

    for room in ctx.model.rooms:
        if room.storey != stair.storey or len(room.clear_face) < 3:
            continue
        polygon = Polygon(room.clear_face)
        if polygon.is_valid and polygon.intersects(region) and room.conditioned:
            return True
    return False


@check(Tier.CODE, "code.R303_7_stairway_illumination")
def stairway_illumination(ctx: CheckContext) -> list[Finding]:
    """R303.7 — interior stairs are lit, and switched from both ends when 6+ risers."""
    cid, code = "code.R303_7_stairway_illumination", "R303.7"
    if not ctx.model.stairs:
        return [_pass(cid, "the plan models no stairway", code)]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        polygon = _stair_outline(stair)
        if polygon is None:
            out.append(_unknown(cid, f"stair {stair.tag} resolves no outline to find a light "
                                     "over", (stair.tag,), code))
            continue
        region = polygon.buffer(_STAIR_LIGHT_REACH.meters)
        served = {stair.storey, stair.to_storey}
        if not _stair_is_indoors(ctx, stair, polygon):
            continue  # R303.8's subject, graded by the sibling rule below
        lights = _lights_near(ctx, region, served)
        if not lights:
            out.append(_fail(cid, f"stair {stair.tag} has no luminaire over its treads or "
                                  "landings; R303.7 requires an artificial light source",
                             (stair.tag,), code))
            continue
        if stair.riser_count < _SWITCHED_RISER_THRESHOLD:
            out.append(_pass(cid, f"stair {stair.tag} is lit by "
                                  f"{', '.join(sorted(x.tag for x in lights))} "
                                  f"({stair.riser_count} risers — under R303.7's six-riser "
                                  "two-switch threshold)", code))
            continue
        switched = _switch_storeys(ctx, lights)
        missing = sorted(served - switched)
        if missing:
            out.append(_fail(cid, f"stair {stair.tag} ({stair.riser_count} risers) has no "
                                  f"wall switch for its light on storey(s) "
                                  f"{', '.join(missing)}; R303.7 requires one at each floor "
                                  "level the stairway serves", (stair.tag,), code))
        else:
            out.append(_pass(cid, f"stair {stair.tag} ({stair.riser_count} risers) is lit by "
                                  f"{', '.join(sorted(x.tag for x in lights))} and switched "
                                  f"at {', '.join(sorted(served))}", code))
    return out


@check(Tier.CODE, "code.R303_8_exterior_stairway_illumination")
def exterior_stairway_illumination(ctx: CheckContext) -> list[Finding]:
    """R303.8 — an exterior stair is lit at its top landing (and at the bottom into a basement).

    The bottom-landing half applies to a stair "providing access to a basement from the
    outdoor grade level", which is precisely the sunken-garden condition, so the rule is
    scoped on the stair's own lower storey rather than on anything authored.
    """
    cid, code = "code.R303_8_exterior_stairway_illumination", "R303.8"
    from typehaus.checks.code.mn_residential._common import _storey_is_below_grade

    stairs = []
    for stair in ctx.model.stairs:
        polygon = _stair_outline(stair)
        if polygon is not None and not _stair_is_indoors(ctx, stair, polygon):
            stairs.append((stair, polygon))
    if not stairs:
        return [_pass(cid, "the plan models no exterior stairway", code)]

    storeys = {s.tag: s for s in ctx.plan.storeys}
    out: list[Finding] = []
    for stair, polygon in stairs:
        region = polygon.buffer(_STAIR_LIGHT_REACH.meters)
        top_lights = _lights_near(ctx, region, {stair.to_storey})
        bottom_lights = _lights_near(ctx, region, {stair.storey})
        lower = storeys.get(stair.storey)
        into_basement = (lower is not None
                         and _storey_is_below_grade(ctx, lower) is True)
        if not top_lights:
            out.append(_fail(cid, f"exterior stair {stair.tag} has no light at its top "
                                  f"landing (storey {stair.to_storey}); R303.8 requires one",
                             (stair.tag,), code))
        elif into_basement and not bottom_lights:
            out.append(_fail(cid, f"exterior stair {stair.tag} descends to below-grade storey "
                                  f"{stair.storey} with no light at the bottom landing; "
                                  "R303.8 requires one where the stair reaches a basement "
                                  "from outdoor grade", (stair.tag,), code))
        else:
            where = "top and bottom landings" if into_basement else "top landing"
            out.append(_pass(cid, f"exterior stair {stair.tag} is lit at its {where}", code))
    return out


@check(Tier.CODE, "code.R302_7_under_stair_protection")
def under_stair_protection(ctx: CheckContext) -> list[Finding]:
    """R302.7 — an enclosed, door-accessed space under a stair is lined with 1/2" gypsum.

    Two screens before the gypsum question, and both matter. A space under a flight is only
    in scope when it is *enclosed usable space* — a stair landing or the hall the flight
    stands in is neither — and only when it is *accessed by a door or access panel*, which
    is R302.7's own trigger. A room open to the space beside it is not what the rule
    protects.
    """
    from shapely.geometry import Polygon

    cid, code = "code.R302_7_under_stair_protection", "R302.7"
    if not ctx.model.stairs:
        return [_pass(cid, "the plan models no stairway", code)]
    occupancy = {room.tag: room.occupancy
                 for room in ctx.plan.all_elements() if room.element_kind == "Room"}

    out: list[Finding] = []
    enclosed: list = []
    for stair in ctx.model.stairs:
        polygon = _stair_outline(stair)
        if polygon is None:
            continue
        for room in ctx.model.rooms:
            if room.storey != stair.storey or len(room.clear_face) < 3:
                continue
            face = Polygon(room.clear_face)
            if not face.is_valid or face.area <= 1e-9:
                continue
            if face.intersection(polygon).area / face.area < 0.5:
                continue  # the flight only clips it; this is not a space under the stair
            if occupancy.get(room.tag) not in _UNDER_STAIR_OCCUPANCIES:
                continue
            if _bounding_openings(ctx, room, doors_only=True):
                enclosed.append((stair, room))
    if not enclosed:
        return [_pass(cid, "no enclosed usable space sits under a stair and opens through a "
                           "door, so R302.7 has nothing to protect", code)]
    for stair, room in enclosed:
        finishes = _gypsum_finishes(ctx, room)
        if finishes:
            out.append(_pass(cid, f"{room.tag} under {stair.tag} is lined with "
                                  f"{', '.join(sorted(finishes))}", code))
        else:
            out.append(_fail(cid, f"{room.tag} is enclosed usable space under {stair.tag}, "
                                  "reached by a door, and its bounding walls carry no gypsum "
                                  "finish; R302.7 requires 1/2\" gypsum board on the enclosed "
                                  "side", (room.tag, stair.tag), code))
    return out


# How far past a room's clear face a wall axis or an opening centre may sit and still count
# as bounding it. A clear face is the *inside* of the lining, so the wall axis it belongs to
# lies half a wall thickness plus the lining beyond it; 12" reaches a 12" concrete wall's
# centreline without claiming the wall on the far side of a closet.
_ROOM_BOUNDARY_BAND = ft(1)


def _bounding_walls(ctx: CheckContext, room) -> list:
    """Resolved walls whose axis runs along this room's clear face."""
    from shapely.geometry import LineString, Polygon

    face = Polygon(room.clear_face)
    if not face.is_valid or face.area <= 1e-9:
        return []
    band = face.boundary.buffer(_ROOM_BOUNDARY_BAND.meters)
    return [wall for wall in ctx.model.walls
            if wall.storey == room.storey
            and band.intersects(LineString([wall.axis[0], wall.axis[1]]))]


def _bounding_openings(ctx: CheckContext, room, *, doors_only: bool = False) -> list:
    """Openings centred on this room's boundary — how the model says "you get in here"."""
    from shapely.geometry import Point, Polygon

    face = Polygon(room.clear_face)
    if not face.is_valid or face.area <= 1e-9:
        return []
    band = face.boundary.buffer(_ROOM_BOUNDARY_BAND.meters)
    walls = {wall.tag for wall in _bounding_walls(ctx, room)}
    found = []
    for opening in ctx.model.openings:
        if doors_only and not opening.is_door:
            continue
        if opening.host_wall not in walls:
            continue
        wall = ctx.model.wall(opening.host_wall)
        point = opening_center(wall, opening) if wall is not None else None
        if point is not None and band.covers(Point(*point)):
            found.append(opening)
    return found


def _gypsum_finishes(ctx: CheckContext, room) -> set[str]:
    """Names of gypsum finish layers on the assemblies of the room's bounding walls."""
    from typehaus.model.enums import LayerFunction

    assemblies = {a.tag: a for a in ctx.plan.library.assemblies}
    found: set[str] = set()
    for wall in _bounding_walls(ctx, room):
        assembly = assemblies.get(getattr(wall, "assembly", "") or "")
        if assembly is None:
            continue
        for layer in assembly.layers:
            if layer.function is LayerFunction.FINISH and "gyp" in (
                    (layer.material_ref or "") + layer.name).lower():
                found.add(f"{assembly.tag}/{layer.name}")
    return found
