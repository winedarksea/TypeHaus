"""Where an in-wall fixture carrier stands, and the framing that makes room for it.

A wall-hung water closet does not hang off the drywall. It bolts to a steel frame — a
Geberit Duofix, a TOTO DuoFit, a Zurn carrier — that stands on the floor *inside* the wall
and carries the concealed cistern, the 3" waste bend and the whole seated load. The frame
is 500 mm wide, so it needs a clear bay, or the framing solver's module studs march
straight through one, silently. ``W-M-HS1`` is
``INT_2X6_STAGGERED_PLUMBING``, whose staggered layout *halves* the module — an 8"
combined rhythm — so the studs it plants in a carrier's way are twice as many as usual.

Two things follow from a carrier, and they are the two halves of this leaf:

* **A keepout.** The bay is exactly the shape of problem ``framing/pockets.py`` already
  solves for a pocket-door cavity — "keep module studs out of this band of this wall" —
  and reaches ``frame_wall`` through the same ``stud_keepouts`` seam rather than growing a
  second mechanism.
* **Framing of its own.** An empty bay is not a framed bay: the module studs the keepout
  removed have to be replaced by flanking studs at the bay's edges, with blocking at the
  frame's head and base. Those are real sticks and reach the BOM through
  ``takeoff/framing.py`` like any other member.

The host wall is resolved from **geometry**, not from ``Fixture.wall_ref``. In this repo
``wall_ref`` names the *wet* wall a fixture plumbs into (see ``houses/catlin/plan/
fixtures.py``), which for catlin's one wall-hung bowl is a different wall entirely from the
one its carrier stands in. The wall a carrier occupies is the wall the china's back faces,
so that is what is measured here.

A leaf: it imports ``model``/``resolve`` and is imported by ``framing/solver.py``, never
the other way round.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.model.enums import Service
from typehaus.model.placeables import MountKind
from typehaus.model.plan import PlanModel
from typehaus.model.spatial import Fixture
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.tables import member_actual
from typehaus.resolve.geometry import add, scale
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedWall

__all__ = ["CarrierBay", "CARRIER_FRAME_HEIGHT_M", "append_carrier_framing", "backing_wall",
           "carrier_bands", "carrier_bays", "carrier_keepouts"]

# Geberit's Duofix element for a wall-hung WC stands 1120 mm (44 1/8") from the floor to the
# top of its frame, and TOTO's DuoFit is within an inch of it. That is where the head
# blocking goes: above it the bay is ordinary wall, below it the frame fills the cavity.
# One number for the class rather than a per-type field, because every frame in the class
# is this tall — what actually varies product to product is the *width*, which is why that
# one is declared on ``FixtureType.carrier_bay_width``.
CARRIER_FRAME_HEIGHT_M = 1.120

# How far past the clear bay a module stud has to stay: the flanking stud's own face
# dimension. Anything closer would interpenetrate the stud that frames the bay.
_FLANKING_ALLOWANCE_M = 1.5 * M_PER_IN

# A carrier's china sits ON the finish face, so the back of the body should land within a
# whisker of the wall's outermost layer. The slack absorbs an authored position rounded to
# a sixteenth and a fixture set with a scribe gap; it is deliberately under an inch, so a
# bowl standing free in the room matches no wall at all rather than the nearest one.
_FACE_TOLERANCE_M = 0.75 * M_PER_IN

# cos of the angle between the wall axis and the way the bowl faces. A carrier's wall is
# square to its fixture; this tolerance is for floating-point, not for skew.
_SQUARE_TOLERANCE = 0.05


@dataclass(frozen=True)
class CarrierBay:
    """One fixture carrier's clear bay, in its host wall's own axis coordinates."""

    wall_tag: str
    fixture_tag: str
    center_m: float
    half_m: float

    @property
    def low_m(self) -> float:
        return self.center_m - self.half_m

    @property
    def high_m(self) -> float:
        return self.center_m + self.half_m


def carrier_bays(plan: PlanModel, model: ResolvedModel) -> tuple[CarrierBay, ...]:
    """Every in-wall carrier in the plan, located on the wall it actually stands in.

    A fixture qualifies on three counts, all of which have to hold: its type mounts on a
    WALL, it DRAINs (a hung lavatory needs no frame — it needs a bracket and backing), and
    its type declares a ``carrier_bay_width``. The last is the deliberate gate: a type
    that has not stated a frame width has not stated that there is a frame.
    """
    types = {item.tag: item for item in plan.library.fixture_types}
    walls = {wall.tag: wall for wall in model.walls}
    bays: list[CarrierBay] = []
    for storey_tag in plan.elements:
        storey_walls = [walls[element.tag]
                        for element in plan.storey_elements(storey_tag)
                        if element.element_kind == "Wall" and element.tag in walls]
        for element in plan.storey_elements(storey_tag):
            if not isinstance(element, Fixture):
                continue
            fixture_type = types.get(element.type_ref)
            if fixture_type is None or fixture_type.carrier_bay_width is None:
                continue
            if fixture_type.mount.kind is not MountKind.WALL:
                continue
            if Service.DRAIN not in fixture_type.needs:
                continue
            found = _backing_wall(storey_walls, element, fixture_type)
            if found is None:
                continue
            wall, station = found
            bays.append(CarrierBay(wall.tag, element.tag, station,
                                   fixture_type.carrier_bay_width.meters / 2.0))
    return tuple(bays)


def carrier_bands(plan: PlanModel,
                  model: ResolvedModel) -> dict[str, list[tuple[float, float]]]:
    """``{wall_tag: [(centre_m, half_CLEAR_m), ...]}`` — the bays themselves.

    What ``append_carrier_framing`` frames. Deliberately *not* the keepout band: the
    flanking studs go on the clear bay's edges, and widening it here would push them out
    and leave the frame rattling in a bay four inches too big.
    """
    bands: dict[str, list[tuple[float, float]]] = {}
    for bay in carrier_bays(plan, model):
        bands.setdefault(bay.wall_tag, []).append((bay.center_m, bay.half_m))
    return bands


def carrier_keepouts(plan: PlanModel,
                     model: ResolvedModel) -> dict[str, list[tuple[float, float]]]:
    """``{wall_tag: [(centre_m, half_m), ...]}`` module studs must stay out of.

    Widened past the clear bay by a stud face each side, so a module stud never lands on
    top of the flanking stud ``append_carrier_framing`` puts there.
    """
    return {wall_tag: [(center, half + _FLANKING_ALLOWANCE_M) for center, half in bands]
            for wall_tag, bands in carrier_bands(plan, model).items()}


def append_carrier_framing(members: list[FramedMember], rw: ResolvedWall, member: str,
                           direction, wall_start, stud_bottom: float, axis_len: float,
                           top_at, bays: tuple[tuple[float, float], ...],
                           dropped_stations: tuple[float, ...] = ()) -> None:
    """Frame each carrier bay: flanking studs, a course at its base and head, cripples over.

    A frame standing full-depth from the floor to 44" is a hole in the stud field, and the
    conventional way to frame a hole is not to leave it empty. The base course is the
    frame's own anchor line — a Duofix's feet bolt down through it — and the head course
    closes the cavity above the frame, catches the drywall over it, and carries the cripples
    that put the module back.

    **The cripples are the load path.** ``W-S-SN1`` stacks on catlin's ``W-M-HS1``, and
    without them the wall above bears on plate alone across the whole 19 3/4" the bay
    displaced. ``dropped_stations`` is exactly the module ``frame_wall``'s exclusions
    removed, so the line restored above the head is the wall's own rhythm rather than a
    second one invented here. It does not restore the *metric*
    (``_stud_grid.orphan_studs`` counts category "stud" and a cripple is not one, by
    design — the same way a window's cripples are not), which is why the pin in
    ``test_upper_storey_studs_stand_over_studs`` moved with a reason written beside it.
    """
    thickness = member_actual(member)[0] * M_PER_IN
    for index, (center, half) in enumerate(sorted(bays)):
        stations = [center - half - thickness / 2.0, center + half + thickness / 2.0]
        stations = [s for s in stations if 0.0 <= s <= axis_len]
        for side, station in enumerate(stations):
            point = add(wall_start, scale(direction, station))
            top = top_at(station)
            if top <= stud_bottom:
                continue
            members.append(FramedMember(
                rw.uid, f"carrier-{index}-stud-{side}", "stud", member, point, point,
                stud_bottom, top, top - stud_bottom, orient=direction))
        if len(stations) < 2:
            continue  # a bay running off the end of the wall has no course to block
        a = add(wall_start, scale(direction, stations[0] + thickness / 2.0))
        b = add(wall_start, scale(direction, stations[1] - thickness / 2.0))
        clear = stations[1] - stations[0] - thickness
        if clear <= 0.0:
            continue
        head = stud_bottom + CARRIER_FRAME_HEIGHT_M
        bay_top = min(top_at(stations[0]), top_at(stations[1]))
        # Both courses are category "blocking", not "header", and the head one deliberately
        # so: ``test_opening_framing_registers_with_the_opening_it_frames`` holds every
        # member categorised "header" to the head of a real ``ResolvedOpening``, and a
        # carrier bay is not an opening in the wall — nothing passes through it. What it is
        # is a flat 2x course at the frame's head, which is what "blocking" means here.
        for course, base, key in ((0, stud_bottom, "block"), (1, head, "head")):
            if bay_top < base + thickness:
                continue  # a raking bay whose studs stop below this course
            members.append(FramedMember(
                rw.uid, f"carrier-{index}-{key}-{course}", "blocking", member, a, b,
                base, base + thickness, clear))
        cripple_bottom = head + thickness
        if bay_top <= cripple_bottom:
            continue  # the frame's head is at the top plate: no cripple bay to fill
        # A dropped station within a stud face of a flanking stud is not a bay to fill: at
        # catlin the 16" module lands 0.22" from the jamb at 15.78", and a cripple there
        # interpenetrates it (``structural.member_interference`` catches exactly this). The
        # jamb is already the full-height member on that line, so the module loses nothing.
        inside = [s for s in sorted(dropped_stations)
                  if stations[0] + thickness <= s <= stations[1] - thickness]
        for ordinal, station in enumerate(inside):
            point = add(wall_start, scale(direction, station))
            top = top_at(station)
            if top <= cripple_bottom:
                continue
            members.append(FramedMember(
                rw.uid, f"carrier-{index}-cripple-{ordinal:03d}", "cripple", member,
                point, point, cripple_bottom, top, top - cripple_bottom, orient=direction))


def backing_wall(plan: PlanModel, model: ResolvedModel, fixture: Fixture,
                 fixture_type) -> tuple[ResolvedWall, float] | None:
    """``(wall, station)`` for the wall a wall-mounted body backs onto, or ``None``.

    **Shared-derivation invariant.** ``resolve/mep_sleeves`` reads this too, so the wall a
    carrier's bay is framed in and the wall its waste drops inside are the same wall by
    construction rather than by two agreeing guesses. Emphatically not ``wall_ref``, which
    in this repo names the *wet* wall a fixture plumbs into.
    """
    walls = {wall.tag: wall for wall in model.walls}
    for storey_tag in plan.elements:
        elements = plan.storey_elements(storey_tag)
        if not any(element.tag == fixture.tag for element in elements):
            continue
        storey_walls = [walls[element.tag] for element in elements
                        if element.element_kind == "Wall" and element.tag in walls]
        return _backing_wall(storey_walls, fixture, fixture_type)
    return None


def _backing_wall(walls: list[ResolvedWall], fixture: Fixture,
                  fixture_type) -> tuple[ResolvedWall, float] | None:
    """``(wall, station along its axis)`` for the wall the fixture's back faces, or None."""
    depth = fixture_type.footprint[1].meters
    radians = math.radians(_degrees(fixture.rotation))
    cos, sin = math.cos(radians), math.sin(radians)
    # Local ``+y`` is the object's back, by the placeable-symbol frame's own contract.
    back = (-sin, cos)
    px, py = fixture.position.xy_m
    back_point = (px + back[0] * depth / 2.0, py + back[1] * depth / 2.0)
    best: tuple[float, ResolvedWall, float] | None = None
    for wall in walls:
        (x0, y0), (x1, y1) = wall.axis
        dx, dy = x1 - x0, y1 - y0
        span = math.hypot(dx, dy)
        if span < 1e-9:
            continue
        tangent = (dx / span, dy / span)
        if abs(tangent[0] * back[0] + tangent[1] * back[1]) > _SQUARE_TOLERANCE:
            continue  # the wall does not run square to the way this fixture faces
        station = (px - x0) * tangent[0] + (py - y0) * tangent[1]
        if not -1e-9 <= station <= span + 1e-9:
            continue  # square to the wall's line, but past its end
        normal = (-tangent[1], tangent[0])
        offset = abs((back_point[0] - x0) * normal[0] + (back_point[1] - y0) * normal[1])
        if offset > _half_depth(wall) + _FACE_TOLERANCE_M:
            continue  # the body stands off this wall, it does not back onto it
        if best is None or offset < best[0]:
            best = (offset, wall, station)
    return None if best is None else (best[1], best[2])


def _half_depth(wall: ResolvedWall) -> float:
    """The wall's outermost layer face, as a distance from its axis.

    Read off the resolved layer polygons for the reason ``resolve/placeables.py`` reads
    them: they encode the assembly that was actually resolved, so a retype moves this
    without an authored wall-depth number anywhere to go stale.
    """
    (x0, y0), (x1, y1) = wall.axis
    dx, dy = x1 - x0, y1 - y0
    span = math.hypot(dx, dy)
    if span < 1e-9:
        return 0.0
    normal = (-dy / span, dx / span)
    offsets = [abs((px - x0) * normal[0] + (py - y0) * normal[1])
               for layer in wall.layers for px, py in layer.polygon]
    return max(offsets) if offsets else 0.0


def _degrees(value: object) -> float:
    degrees = getattr(value, "degrees", None)
    return float(degrees) if degrees is not None else 0.0
