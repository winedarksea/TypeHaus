"""A wall that passes THROUGH a floor deck cuts the sheet — and nothing else (decision #78).

Catlin's fireplace surround stands on ``W-B-E1``'s pour and rises through ``FS-M-EAST``'s
joist zone to the living-room floor. It used to do that through an authored ``FloorOpening``,
which framed a 2-ply LVL header, four full-span trimmer plies, four hangers and web
stiffeners around a hole the brick then filled — framing for a premise that was never true
(``houses/catlin/notes/east_breast_bearing.md`` §4: a 3 5/8" wythe standing 2 1/2" clear of a
5 1/2" mudsill does not cut a joist short of its bearing). The joists run through; what the
wall really takes out of the deck is a piece of **plywood**, and nobody should have to author
that. So it is derived here.

**Read FRAMING extents, never body extents. That is the whole blast radius.**
``platform._drop`` grows a framed wall's *body* down over the mudsill and rim;
``platform._lift`` grows it up to the wall stacked above. Both leave the framing where it is,
in ``plate_base_z_m`` / ``plate_top_z_m``, which is what :attr:`ResolvedWall.base_ref_z_m` and
:func:`partition.framing_top_z_m` read. Ask the body instead and ``W-M-E1`` qualifies —
dropped to ≈ −13 7/16", lifted to +120", footprint squarely in the deck — and every
platform-framed exterior wall in the house subtracts a 6" strip of subfloor along its whole
run. Its framing base is 0", a foot above the soffit.

**The footprint must be CONTAINED in the deck outline, not merely meet it.** A deck outline
runs to the *axis* of the line it dies into, so every wall standing at a deck's edge overlaps
it by half its own thickness — catlin's ``W-G-S`` overlaps the two breezeway landings that way
and passes every other clause. The sheet is already drawn to that wall; cutting it again
deducts the same strip twice. A wall the deck *surrounds* is the other thing entirely. The
deck's own ``bearing_refs`` are excluded for the same reason, one level more explicitly: a
line a deck is carried BY is a support, and ``resolve/floor_ends.py`` already owns its seat.

``Railing`` and ``Stair`` are out of scope by the ``isinstance(_, Wall)`` clause, and
deliberately: a stair genuinely does span a deck, and its well is a ``FloorOpening`` — which
is the right article for it, because a stair well is a hole somebody walks down and needs the
header and trimmers an opening brings.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import Polygon

from typehaus.model.elements import Wall
from typehaus.quantities import inch
from typehaus.resolve.ceiling_over import polygon_parts
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.model import FramedMember, Ring
from typehaus.resolve.overlay import difference, intersection, union_all
from typehaus.resolve.partition import framing_top_z_m

#: How far past a deck plane a wall's framing must reach to be passing *through* it.
#: Three walls in catlin die exactly at a deck plane (``params/breezeway.py``'s two seats,
#: ``params/sunken_garden.py``'s porch wall). A wall that stops at a deck does not pass
#: through it, and an exact ``>=`` would decide that on float noise.
_THROUGH_TOL_M = inch(1 / 16).meters

#: How much air the sheet leaves round the thing passing through it — a *derivation*
#: constant, a saw cut that moves a quantity and never a verdict, which is why it lives here
#: beside the geometry like ``ceiling_over._FILLED_FRACTION`` and not in ``Preferences``.
#: The check's own minimum (``min_through_deck_clearance_in``) is a verdict threshold and is
#: a preference; ``tests/test_through_deck_clearance.py`` pins ``_SHEET_CLEARANCE_M <=`` it.
_SHEET_CLEARANCE_M = inch(0.5).meters

#: Below this a wall/deck overlap is a noding sliver, not a piece of sheet. Same 1.6 sq in
#: ``ceiling_over._MIN_REGION_M2`` uses, and for the same reason.
_MIN_CUT_M2 = 1e-3


def _wall_face(wall: Any) -> Any:
    """The wall's plan footprint — the union of its LAYER polygons.

    Layers rather than ``_structure_polygon`` so a coating cannot be silently dropped: the
    fireplace wythe carries a 1/8" silicate wash on its room face and the saw goes round the
    built thing, not round the structural half of it.
    """
    faces = [Polygon(layer.polygon) for layer in wall.layers if len(layer.polygon) >= 3]
    return union_all(faces) if faces else None


def through_deck_walls(model: Any, system: Any, floor_z0_m: float, floor_z1_m: float,
                       deck_outline: Ring) -> tuple[Any, ...]:
    """Walls whose FRAMING band spans this deck and whose footprint stands in it.

    ``floor_z0_m`` is the naked structure soffit and ``floor_z1_m`` the top of the sheet.
    Four clauses, all of which have to hold:

    1. the wall's framing base is at or below the soffit — it starts under the deck;
    2. its framing top is above the sheet by more than :data:`_THROUGH_TOL_M` — it comes out
       the other side;
    3. its footprint, clearance included, is **covered by** the deck outline;
    4. it is an authored ``Wall``, and not one this deck bears on.

    Clause 3 is containment rather than mere intersection, and that is not tidiness. A deck
    outline runs to the *axis* of the line it dies into, so every wall standing at a deck's
    edge overlaps it by half its own thickness — catlin's ``W-G-S`` overlaps the two
    breezeway landings by 59 and 285 sq in that way, and it satisfies clauses 1, 2 and 4.
    That wall is what the boards stop *at*; the sheet is already drawn to it and cutting it
    again would deduct the same strip twice. A wall the deck *surrounds* is the other thing.
    """
    if len(deck_outline) < 3:
        return ()
    sheet = Polygon(deck_outline)
    if not sheet.is_valid or sheet.area <= _MIN_CUT_M2:
        return ()
    bearing = frozenset(getattr(system.joists, "bearing_refs", ()) or ())
    out: list[Any] = []
    for wall in model.walls:
        if wall.tag in bearing:
            continue
        if wall.base_ref_z_m > floor_z0_m + _THROUGH_TOL_M:
            continue
        if framing_top_z_m(wall) < floor_z1_m + _THROUGH_TOL_M:
            continue
        if not isinstance(model.plan.by_tag(wall.tag), Wall):
            continue
        face = _wall_face(wall)
        if face is None or face.is_empty:
            continue
        if not sheet.covers(face.buffer(_SHEET_CLEARANCE_M, join_style=2)):
            continue
        out.append(wall)
    return tuple(out)


def through_deck_cuts(walls: tuple[Any, ...], members: list[FramedMember],
                      deck_outline: Ring) -> tuple[Ring, ...]:
    """What to take out of the sheet for each wall in ``walls``: footprint + clearance, less
    every member footprint.

    **The frame subtraction is not tidying — it is what makes the clearance constant safe.**
    Raise it to 3/4" and the derived cut runs 1/8" over catlin's joists 005 and 008 (they
    clear the wythe by 5/8" each side, which is residue of a 44 1/4" panel on a 16" module
    rather than a chosen margin): plywood removed from the very member it is nailed to,
    silently, off a constant nobody was looking at. Cutting the sheet back to the framing is
    also what is built — the sheet is nailed to the joists and the saw stops at them.
    """
    if not walls or len(deck_outline) < 3:
        return ()
    sheet = Polygon(deck_outline)
    frame = union_all([Polygon(ring) for ring, _z0, _z1 in map(member_footprint, members)])
    rings: list[Ring] = []
    for wall in walls:
        face = _wall_face(wall)
        if face is None or face.is_empty:
            continue
        cut = intersection(face.buffer(_SHEET_CLEARANCE_M, join_style=2), sheet)
        if not frame.is_empty:
            cut = difference(cut, frame)
        for part in polygon_parts(cut):
            if part.area > _MIN_CUT_M2:
                rings.append([(x, y) for x, y in part.exterior.coords[:-1]])
    return tuple(rings)
