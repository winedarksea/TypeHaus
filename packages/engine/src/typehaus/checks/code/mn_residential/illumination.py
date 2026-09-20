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
  The landing is a SURFACE and the rule is graded against it: the whole of R303.8 is "an
  artificial light source located at the top landing of the stairway", with no illuminance,
  no switching and no distance from the treads in it. See ``_landing_region`` — this is the
  one place the two stair rules part company, and R303.7 stays tread-centric because its
  own text is.
* **R302.7** — an enclosed space under a stair, reached by a door, is lined with 1/2"
  gypsum on the enclosed side. Applicability is a geometry question (is there a room under
  the flight?) followed by an access question (does a door open into it?).

*Where* the fixture is, however, is graded in three dimensions. The plan region that finds
a luminaire over a stair says nothing about height, and the elevation half of the question is
not a refinement: a sconce authored below the treads it is drawn to light lights nothing, and
counting it is how a stair reads as lit when it is dark. Every candidate is measured against
the *sloped* nosing line of the flight it stands beside — see ``_lights_near``.

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
from typehaus.resolve.stairs.walkline import flight_walklines, walkline_z_at

# R303.7: "a wall switch at each floor level ... where the stairway has six or more risers".
_SWITCHED_RISER_THRESHOLD = 6
# How far from the stair outline a luminaire still counts as lighting it. A ceiling fixture
# over a stair well is rarely inside the run's own plan ring — it hangs over the landing or
# just off the top nosing — so the ring is buffered rather than tested for containment.
# R303.8 unions this with the arrival deck (``_landing_region``); R303.7 uses it alone.
_STAIR_LIGHT_REACH = ft(4)
# How far off a flight centreline the nosing line is still the surface a fixture is being
# measured against. The plan region above is the stair outline buffered by 4 ft, and the
# walking line it is measured to is the flight *centre*, so the lateral reach has to carry
# that buffer plus half a code-width flight; short of it the fixture is simply off the
# stair and no nosing elevation applies to it.
_NOSING_LATERAL_REACH_M = _STAIR_LIGHT_REACH.meters + 2.0
# How far under the nosing line a luminaire may still sit and be lighting the stair: one
# riser. That is the riser FACE — the band a step light is set into, between the tread it
# washes and the tread above it — and a fitting in it lights the flight from the side, which
# is what a step light is for. Below one full riser the fitting is behind the tread, inside
# the stringer, and lights the framing. The stair's own riser height is the measure; the
# fallback is R311.7.5.1's maximum, for a synthetic stair that resolves none.
_STEP_LIGHT_BAND_FALLBACK_M = ft(0, 7.75).meters
# R303.8's subject is the LANDING, not the treads, and a landing is a surface. These three
# find the one a flight arrives on. A deck is that surface when its top is the stair's own
# arrival elevation (2" of tolerance, for a deck built up in layers) and it lies within a
# threshold of the flight: ST-SG-PORCH steps off its top nosing across the 12" top of
# W-SG-E1 before it reaches FS-SG-PORCH, and a threshold that size is a detail of the pour,
# not a second room. Matched on elevation and adjacency rather than on a storey name,
# because the porch deck's storey is `court-main` while the stair's is `main` — the same
# reason `_stair_is_indoors` derives its answer instead of reading a flag.
_LANDING_ELEVATION_TOLERANCE_M = ft(0, 2).meters
_LANDING_THRESHOLD = ft(1, 6)
# A deck's RIM is not the edge of its landing — the walls that bound it are, and the light
# "located at" a landing is very often mounted on one of those. A wall fixture's position is
# already outboard of the deck by half its own body (the footprint is centred), and the deck
# stops short of the cladding besides: ED-M-STAIR-LT's centre lands 1/4" north of
# FS-SG-PORCH's north edge while its back is on the wall over that deck. Six inches is the
# deepest fixture body this catalog carries, doubled, and it buys nothing a landing does not
# already touch.
_LANDING_RIM = ft(1)
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


def _resolved_light_z(ctx: CheckContext) -> dict[str, float]:
    """Absolute project-frame elevation per luminaire tag, from the RESOLVED model.

    The authored element carries a ``Mount`` — a height above *something* — and two
    fixtures with the same authored 7'-6" sit fourteen feet apart in the project frame
    when they hang on different storeys. ``ResolvedCanvasObject.z_m`` and
    ``ResolvedLightRun.z_m`` are the resolver's answer to that, and they are the only
    numbers comparable with a stair's nosing elevations. A wall mount's ``z_m`` is the
    *base* of the fixture, which is exactly the edge the nosing line has to clear.
    """
    heights = {obj.tag: obj.z_m for obj in ctx.model.canvas_objects}
    heights.update({run.tag: run.z_m for run in ctx.model.light_runs})
    return heights


def _plan_points(element) -> list[tuple[float, float]]:
    """The plan points a luminaire occupies: a device's position, a run's vertices."""
    if element.element_kind == "LightRun":
        return [p.xy_m for p in element.path]
    return [element.position.xy_m]


def _lights_near(ctx: CheckContext, region, storeys: set[str], *, stair=None):
    """``(serving, buried)`` luminaires whose plan position lands in ``region``.

    Plan proximity alone answered this until ED-S-STUDY2-STAIR-SC1, a wall sconce authored
    2'-11 1/2" *below* the tread it was drawn to light, passed every rule in the engine: the
    4 ft buffer is a plan ring and a plan ring has no opinion about height. A fixture under
    the nosing line is inside the flight, not over it, and it lights nothing.

    The line is sampled per flight and sloped — ``walkline_z_at`` interpolates between
    consecutive nosings of the *one* flight the fixture stands beside — because a single
    flat elevation for a stair is wrong at both ends of it by half the storey rise. A
    fixture that projects onto no flight within reach (a landing pendant off the side of
    the well) has no nosing under it to be below, and is kept: absence of a walking line is
    not evidence of a buried fixture.
    """
    from shapely.geometry import LineString, Point

    # ``include_arrival=False``: the synthetic station a tread flight is extended by is the
    # arrival DECK, one riser above the top nosing, and it is not a tread. Sampling it put a
    # wall-mounted step light beside the top of ST-SG-PORCH 7.5" under a "nosing" that is
    # really the porch floor it hangs below.
    lines = flight_walklines(stair, include_arrival=False) if stair is not None else []
    heights = _resolved_light_z(ctx) if lines else {}
    band = (stair.riser_height_m if stair is not None and stair.riser_height_m > 1e-6
            else _STEP_LIGHT_BAND_FALLBACK_M)
    serving, buried = [], []
    for storey in ctx.plan.storeys:
        if storey.tag not in storeys:
            continue
        for element in ctx.plan.storey_elements(storey.tag):
            kind = element.element_kind
            if kind == "LightRun":
                if not (len(element.path) >= 2 and region.intersects(
                        LineString([p.xy_m for p in element.path]))):
                    continue
            elif (kind == "ElectricalDevice"
                  and getattr(element.kind, "value", None) == "light"):
                if not region.covers(Point(*element.position.xy_m)):
                    continue
            else:
                continue
            nosing = _nosing_under(lines, heights, element, band)
            if nosing is not None:
                buried.append((element, nosing))
            else:
                serving.append(element)
    return serving, buried


def _nosing_under(lines, heights: dict[str, float], element, band: float):
    """``(nosing_z, fixture_z)`` when this luminaire sits more than ``band`` under the nosings.

    ``None`` — the fixture is over the treads (or in the riser band beside them), or the
    model gives no answer: an unresolved tag or a plan position off every flight. Both
    silences are kept rather than guessed.
    """
    fixture_z = heights.get(element.tag)
    if fixture_z is None:
        return None
    worst = None
    for point in _plan_points(element):
        nosing_z = walkline_z_at(lines, point, _NOSING_LATERAL_REACH_M)
        if nosing_z is None:
            continue
        if worst is None or nosing_z > worst:
            worst = nosing_z
    if worst is None or fixture_z >= worst - band - 1e-6:
        return None
    return (worst, fixture_z)


def _buried_note(buried) -> str:
    """The parenthetical naming the fixtures a stair rule had to discount, and by how much."""
    if not buried:
        return ""
    parts = [f"{element.tag} sits {(nosing - z) / 0.0254:.1f}\" below the nosing line"
             for element, (nosing, z) in sorted(buried, key=lambda item: item[0].tag)]
    return f" ({'; '.join(parts)})"


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


def _landing_region(ctx: CheckContext, stair, polygon, elevation_m: float | None):
    """``polygon`` widened to the walking surface this flight arrives on at ``elevation_m``.

    R303.8 asks for "an artificial light source located at the top landing of the stairway",
    and that is the whole of the sentence: no illuminance, no switch, and no distance from
    the treads. The 4 ft ring this rule shared with R303.7 was standing in for the landing,
    and it is the wrong shape for the question — R303.7 lights *treads and landings* and is
    properly tread-centric, while R303.8 names one surface and asks whether a fixture is on
    it. On this house the difference is the whole verdict: ST-SG-PORCH arrives on the 171 sf
    porch deck, its flood and its fan hang over that deck ten feet from the top nosing, and
    a ring drawn round the treads reported a stair with no light at a landing with two.

    The landing is the DECK, so the region is the union and never a replacement: a fitting
    at the head of a flight that overhangs no modelled deck is still at the top of the
    stair, and this rule has counted it since it was written. Where no deck matches, the
    ring is all there is and the answer is unchanged — widening is the only direction this
    can move a verdict, which is what makes it a correction to a rule and not a new one.
    """
    from shapely.geometry import Polygon

    if elevation_m is None:
        return polygon
    region = polygon
    for floor in ctx.model.floors:
        if floor.deck_z1_m is None or len(floor.deck_outline) < 3:
            continue
        if abs(floor.deck_z1_m - elevation_m) > _LANDING_ELEVATION_TOLERANCE_M:
            continue
        deck = Polygon([p.xy_m if hasattr(p, "xy_m") else p for p in floor.deck_outline])
        if not deck.is_valid or deck.area <= 1e-9:
            continue
        if deck.distance(polygon) <= _LANDING_THRESHOLD.meters:
            region = region.union(deck.buffer(_LANDING_RIM.meters))
    return region


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
        lights, buried = _lights_near(ctx, region, served, stair=stair)
        if not lights:
            out.append(_fail(cid, f"stair {stair.tag} has no luminaire over its treads or "
                                  "landings; R303.7 requires an artificial light source"
                                  f"{_buried_note(buried)}",
                             (stair.tag, *sorted(e.tag for e, _ in buried)), code))
            continue
        if stair.riser_count < _SWITCHED_RISER_THRESHOLD:
            out.append(_pass(cid, f"stair {stair.tag} is lit by "
                                  f"{', '.join(sorted(x.tag for x in lights))} "
                                  f"({stair.riser_count} risers — under R303.7's six-riser "
                                  f"two-switch threshold){_buried_note(buried)}", code))
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
                                  f"at {', '.join(sorted(served))}{_buried_note(buried)}",
                             code))
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
        ring = polygon.buffer(_STAIR_LIGHT_REACH.meters)
        # Two landings, two surfaces: the flight arrives on one and springs from the other,
        # and each is found at its own elevation. A stair whose deck the model does not
        # carry falls back to the ring for that end alone.
        top_region = _landing_region(ctx, stair, ring, stair.arrival_elevation_m)
        bottom_region = _landing_region(ctx, stair, ring, stair.base_elevation_m)
        top_lights, top_buried = _lights_near(ctx, top_region, {stair.to_storey}, stair=stair)
        bottom_lights, bottom_buried = _lights_near(ctx, bottom_region, {stair.storey},
                                                    stair=stair)
        # One census, two storey filters: a device on the storey that is both ``storey`` and
        # ``to_storey`` (a stair inside one level, like this porch flight) is found twice.
        buried = list({item[0].tag: item for item in top_buried + bottom_buried}.values())
        lower = storeys.get(stair.storey)
        into_basement = (lower is not None
                         and _storey_is_below_grade(ctx, lower) is True)
        if not top_lights:
            out.append(_fail(cid, f"exterior stair {stair.tag} has no light at its top "
                                  f"landing (storey {stair.to_storey}); R303.8 requires one"
                                  f"{_buried_note(buried)}",
                             (stair.tag, *sorted(e.tag for e, _ in buried)), code))
        elif into_basement and not bottom_lights:
            out.append(_fail(cid, f"exterior stair {stair.tag} descends to below-grade storey "
                                  f"{stair.storey} with no light at the bottom landing; "
                                  "R303.8 requires one where the stair reaches a basement "
                                  f"from outdoor grade{_buried_note(buried)}",
                             (stair.tag, *sorted(e.tag for e, _ in buried)), code))
        else:
            where = "top and bottom landings" if into_basement else "top landing"
            out.append(_pass(cid, f"exterior stair {stair.tag} is lit at its {where}"
                                  f"{_buried_note(buried)}", code))
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

    # RESOLVED, not authored: a variant's own ``layers`` is empty and its stack lives on
    # its base (#35), so a raw lookup reads it as no wall at all.
    assemblies = {a.tag: ctx.plan.library.resolve_assembly(a.tag)
                  for a in ctx.plan.library.assemblies}
    found: set[str] = set()
    for wall in _bounding_walls(ctx, room):
        assembly = assemblies.get(getattr(wall, "assembly", "") or "")
        if assembly is None:
            continue
        for layer in assembly.layers:
            if layer.function is LayerFunction.FINISH and any(
                    token in ((layer.material_ref or "") + layer.name).lower()
                    for token in ("gyp", "gwb")):
                found.add(f"{assembly.tag}/{layer.name}")
    return found
