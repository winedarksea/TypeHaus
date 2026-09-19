"""What an *interior partition* is — the one answer three passes share.

``roof_geometry`` has to know which raked walls it must not rake, ``platform`` has to know
which walls carry no skin, and ``partition_top`` has to know which walls take a deflection
gap. Three private predicates would be three definitions of "partition", and the first time
they disagreed one pass would rake a wall the next pass then lowered.

Imports ``model`` and ``resolve.model`` only: ``resolve`` → ``joints`` is a cycle
(``tests/test_package_leaves.py``), so the ``bearing_refs`` sweep below is generic rather
than a reach into ``joints/`` for a helper.
"""

from __future__ import annotations

from typing import Any

from typehaus.model.enums import StructuralRole
from typehaus.model.refs import ToRoof
from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedModel

#: How far an interior partition's top plate stops clear of the structure over it.
#:
#: One screw's polymer sleeve, not a house preference: it is the gap a Simpson Strong-Drive
#: SDPW DEFLECTOR sets, and the number is 3/4" rather than 1/2" or 1" because the 3-1/2"
#: SDPW is published for "up to 3/4 in" and the offset driver bit in the box is what sets
#: it. A named module constant for the same reason ``platform._MAX_BAND_M`` and
#: ``roof_geometry.MIN_COUNTABLE_HEAD_M`` are (AGENTS.md §1.3 forbids *magic* numbers, not
#: named ones carrying their source). It lives in this module rather than in
#: ``partition_top`` because :func:`runs_full_storey_height` has to know it — see the
#: tolerance below — and ``partition`` may not import ``partition_top``.
#:
#: The promotion path, for the day a house needs two of these: a per-joint field on the
#: wall, read with this as the default — never a ``Preferences`` entry, which lives in
#: ``checks/`` and is not reachable from ``resolve`` without re-signing ``resolve()``.
#:
#: See ``houses/catlin/notes/partition_top_deflection.md``.
DEFLECTION_GAP_M = inch(0.75).meters

# How far a wall's framing top may sit from its storey's ceiling line and still be a
# full-height partition: one plate course. Catlin's distribution has a clean hole in it and
# that is the honest basis — *in* at 0" (main, second) and 15/16" (the basement's authored
# 8'-0" against a 96 15/16" storey), *out* at 6 15/16" and worse, with nothing between.
_FULL_HEIGHT_TOLERANCE_M = inch(1.5).meters


def is_clad(wall: Any) -> bool:
    """Does this wall carry a cladding layer — is it envelope, or is it partition?"""
    return any(layer.function == "cladding" for layer in wall.layers)


def bearing_ref_tags(plan: Any) -> frozenset[str]:
    """Every wall tag some element names as the thing it bears on.

    Generic over element kinds rather than over the three that first came to mind. A
    ``Stair`` and a ``FloorOpening`` carry ``bearing_refs`` too, and on catlin they hold
    the two walls a narrower sweep gets wrong: ``W-S-SS2`` (in ``ST-S2A.bearing_refs``) and
    ``W-S-SN3``, a header at a deck hole. A wall something lands on is not a partition
    however little the author wrote on it.
    """
    tags: set[str] = set()
    for element in plan.all_elements():
        tags.update(getattr(element, "bearing_refs", ()) or ())
        joists = getattr(element, "joists", None)
        if joists is not None:
            tags.update(getattr(joists, "bearing_refs", ()) or ())
    return frozenset(tags)


def framing_top_z_m(wall: Any) -> float:
    """Where the wall's FRAMING tops out — the plate, not the body.

    A lifted wall's body spans floor-to-floor and its plate stays at the old ceiling line
    (``platform._lift``), so ``z1_m`` is the wrong number to ask any framing question of.
    """
    return wall.z1_m if wall.plate_top_z_m is None else wall.plate_top_z_m


def is_interior_partition(model: ResolvedModel, wall: Any,
                          bearing_refs: frozenset[str]) -> bool:
    """A non-bearing, unclad, non-foundation wall nothing lands on.

    The role test is the same reach ``platform`` already makes onto the authored element:
    ``ResolvedWall`` does not carry ``structural_role``, and an authored BEARING wall is a
    load path whatever its layer stack looks like.
    """
    if wall.is_foundation or is_clad(wall):
        return False
    if wall.tag in bearing_refs:
        return False
    authored = model.plan.by_tag(wall.tag)
    return getattr(authored, "structural_role", None) is not StructuralRole.BEARING


def runs_full_storey_height(model: ResolvedModel, wall: Any) -> bool:
    """Does this wall go all the way up to what is over it?

    The gate that keeps a *room inside a room* out. Catlin's sauna hot room
    (``W-B-SA-N``/``-N2``/``-W``), its 20" tub-deck curbs, the fireplace's brick wythe
    segments and the breezeway screen skirt all pass :func:`is_interior_partition` and
    none of them reaches the structure above — three of them sit inside
    ``platform._MAX_BAND_M``, so that guard does not save them either. A wall that stops
    short of the deck has no deflection joint to detail, and pulling its plate up to one
    would invent 7'-6" of stud.

    An authored ``ToRoof`` top is full height by construction.
    """
    authored = model.plan.by_tag(wall.tag)
    if isinstance(getattr(authored, "top", None), ToRoof):
        return True
    storey = next((s for s in model.plan.storeys if s.tag == wall.storey), None)
    if storey is None:
        return False
    ceiling_m = storey.elevation.meters + storey.default_ceiling_height.meters
    # Asymmetric downward by exactly the deflection gap, because this must answer the SAME
    # question before and after ``apply_partition_tops`` has run: the pass lowers the plate
    # it selects, and ``takeoff/partition_fasteners.py`` then asks this of the RESOLVED
    # model. Without the extra 3/4" ``W-B-CE`` — whose plate lands at -14 3/16" under
    # ``SL-M-DECK`` — would stop being a partition the moment it was treated as one.
    # It does not widen the set: the nearest wall on the other side of the hole is 6 15/16"
    # out.
    return (-_FULL_HEIGHT_TOLERANCE_M - DEFLECTION_GAP_M
            <= framing_top_z_m(wall) - ceiling_m <= _FULL_HEIGHT_TOLERANCE_M)


def takes_a_deflection_gap(model: ResolvedModel, wall: Any,
                           bearing_refs: frozenset[str]) -> bool:
    """The combined predicate ``partition_top`` writes against.

    Its own function because ``roof_geometry`` must ask *exactly* this question to know
    which walls to leave alone: a ``ToRoof`` wall skipped there but not picked up by
    ``apply_partition_tops`` would keep whatever top it had before either pass ran.
    """
    return (is_interior_partition(model, wall, bearing_refs)
            and runs_full_storey_height(model, wall))
