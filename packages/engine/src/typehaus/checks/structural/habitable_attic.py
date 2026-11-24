"""IRC 2018 R325.6: is the habitable attic a story? Graded, not assumed (review D-R1).

R325.6 reads "A habitable attic shall not be considered a story where complying with all of
the following": (1) occupiable floor area >= 70 sf per R304; (2) that area has a ceiling
height per R305; (3) the space is enclosed by the roof assembly above, knee walls (if
applicable) on the sides and the floor-ceiling assembly below; (4) the attic floor does not
extend beyond the exterior walls of the floor below. Text read 2026-11-23 on UpCodes
(up.codes/s/habitable-attic, "2018 R325.6", a republication under the Texas 2018 IRC; the ICC's own
page is a 403, so a primary read is still owed) and in WABO's 2019 comment ("maintains the
existing specifications"). It carries NO area
fraction: the 1/3 (1/2 sprinklered) cap is the 2021 IRC R326.3, which Minnesota has not
adopted (Minn. R. 1309.0010 adopts the 2018 IRC; ch. 1309 has no part amending R325; read
2026-11-23 at revisor.mn.gov; ``notes/wall_bracing_layout.md`` §2).

Conditions 1-2 replay ``code.R304_1_floor_area`` / ``code.R305_ceiling_height``'s own
arithmetic (R305.1's sloped-ceiling exception: half of the REQUIRED floor area, R304.1's 70 sf, at
7'-0" and none under 5'-0"); a condition that cannot be shown counts the attic as a story
(conservative).
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from shapely.geometry import Polygon

from typehaus.checks.code.mn_residential._common import HABITABLE_OCCUPANCIES, SF_PER_M2
from typehaus.checks.code.mn_residential.room_area import walkable_face
from typehaus.model.refs import FollowRoof
from typehaus.quantities import ft, inch
from typehaus.resolve.overlay import difference, union_all
from typehaus.resolve.roof_geometry import MIN_COUNTABLE_HEAD_M, room_countable_polygon
from typehaus.resolve.room_floor import room_finished_floor_elevation

_MIN_AREA_M2 = 70.0 / SF_PER_M2
_HEIGHT_M = ft(7).meters
_SLOPED_FRACTION = 0.5
_TOL_M2 = inch(1).meters ** 2  # an overhang under 1 sq in is rounding


@dataclass(frozen=True)
class AtticCondition:
    number: int
    holds: bool
    words: str


@dataclass(frozen=True)
class AtticReading:
    storey: str
    conditions: tuple[AtticCondition, ...]

    @property
    def is_story(self) -> bool:
        return not all(c.holds for c in self.conditions)

    def describe(self) -> str:
        head = ("counts as a story: " if self.is_story else "is not a story, all four hold: ")
        return f"R325.6, attic '{self.storey}' {head}" + "; ".join(
            f"({c.number}) {'ok' if c.holds else 'FAILS'} {c.words}" for c in self.conditions)


def habitable_attic_storeys(model, building: str, top_braced: str | None) -> list[str]:
    """Storeys of ``building`` above the topmost braced one that hold a habitable room."""
    if top_braced is None:
        return []
    above = model.plan.storey(top_braced).elevation.meters
    habitable = {o.value for o in HABITABLE_OCCUPANCIES}
    return [s.tag for s in sorted(model.plan.storeys, key=lambda s: s.elevation.meters)
            if s.building == building and s.elevation.meters > above
            and any(r.storey == s.tag and r.occupancy in habitable for r in model.rooms)]


def attic_reading(model, storey_tag: str) -> AtticReading:
    storey = model.plan.storey(storey_tag)
    below = [s for s in model.plan.storeys if s.building == storey.building
             and s.elevation.meters < storey.elevation.meters]
    lower = max(below, key=lambda s: s.elevation.meters) if below else None
    habitable = {o.value for o in HABITABLE_OCCUPANCIES}
    rooms = [r for r in model.rooms if r.storey == storey_tag and r.occupancy in habitable]
    ctx = SimpleNamespace(plan=model.plan, model=model)
    decks = [Polygon(f.deck_outline) for f in model.floors
             if f.storey == storey_tag and len(f.deck_outline) >= 3]
    roofs = [Polygon(r.footprint) for r in model.roofs
             if r.storey == storey_tag and len(r.footprint) >= 3]
    return AtticReading(storey_tag, (
        *_area_and_height(model, ctx, storey, rooms),
        _enclosure(model, storey_tag, rooms, decks, roofs),
        _footprint(model, storey, lower, decks),
    ))


def _area_and_height(model, ctx, storey, rooms) -> tuple[AtticCondition, AtticCondition]:
    """Conditions 1 and 2: R304.1/R304.3's 70 sf at 5'-0" head, then R305.1's sloped-ceiling
    exception (half the required area at 7'-0", none of it under 5'-0")."""
    if not rooms:
        none = "no habitable room resolves on the storey"
        return AtticCondition(1, False, none), AtticCondition(2, False, none)
    lines, area_ok, height_ok = [], False, True
    for room in rooms:
        floor = walkable_face(ctx, room, storey.tag)
        at_five = room_countable_polygon(model, floor, storey.elevation.meters,
                                         MIN_COUNTABLE_HEAD_M).area
        at_seven = room_countable_polygon(model, floor, room_finished_floor_elevation(model, room),
                                          _HEIGHT_M).area
        required = min(floor.area, _MIN_AREA_M2)
        area_ok = area_ok or at_five + 1e-9 >= _MIN_AREA_M2
        fine = at_five + 1e-9 >= required and at_seven + 1e-9 >= _SLOPED_FRACTION * required
        height_ok = height_ok and fine
        lines.append((f"{room.tag} {at_five * SF_PER_M2:.0f} sf at 5'-0\"",
                      f"{room.tag} {at_seven * SF_PER_M2:.0f} sf at 7'-0\" of "
                      f"{required * SF_PER_M2:.0f} sf required"))
    return (AtticCondition(1, area_ok, "occupiable floor >= 70 sf (R304): "
                           + "; ".join(a for a, _ in lines)),
            AtticCondition(2, height_ok, "head per R305.1's sloped-ceiling exception: "
                           + "; ".join(b for _, b in lines)))


def _enclosure(model, storey_tag, rooms, decks, roofs) -> AtticCondition:
    """Condition 3: each habitable room is under a roof it follows, over a floor deck."""
    covered = union_all(roofs) if roofs else Polygon()
    floor = union_all(decks) if decks else Polygon()
    ceilings = {e.tag: getattr(e, "ceiling", None) for e in model.plan.all_elements()
                if getattr(e, "element_kind", None) == "Room"}
    bad = []
    for room in rooms:
        ring = Polygon(room.clear_face)
        if not isinstance(ceilings.get(room.tag), FollowRoof):
            bad.append(f"{room.tag} has no roof-following ceiling")
        elif difference(ring, covered).area > _TOL_M2:
            bad.append(f"{room.tag} reaches past the roof footprint")
        elif difference(ring, floor).area > _TOL_M2:
            bad.append(f"{room.tag} has no floor deck below it")
    return AtticCondition(3, not bad and bool(rooms), (
        "enclosed by roof above, plates/knee walls, floor-ceiling below" if not bad
        else "; ".join(bad)))


def _footprint(model, storey, lower, decks) -> AtticCondition:
    """Condition 4: the attic deck lies within the deck of the storey below."""
    if lower is None or not decks:
        return AtticCondition(4, False, "no storey or attic deck to compare")
    under = [Polygon(f.deck_outline) for f in model.floors
             if f.storey == lower.tag and len(f.deck_outline) >= 3]
    over = difference(union_all(decks), union_all(under)) if under else union_all(decks)
    return AtticCondition(4, over.area <= _TOL_M2, (
        f"attic deck {union_all(decks).area * SF_PER_M2:.0f} sf, "
        f"{over.area * SF_PER_M2:.0f} sf beyond '{lower.tag}''s deck"))
