"""Starter kitchen/utility casework catalog — the fitted millwork half of the placeables.

Casework is not furniture that happens to be big: it is built in place, its back is the wall
and its ends are the neighbouring units, so it carries **no clearance zones**. The aisle in
front of a run is a property of the room's layout, not of any one cabinet, and giving every
24" base a 2' pull-out band would report an ordinary continuous run as a pile of
encroachments. Appliance doors — a refrigerator's, a dishwasher's — keep their zones, and
those are what the aisles actually have to clear.

Countertops are not separate elements: the ``base-cabinet`` symbol is ``counter_case``, which
already draws the slab, the carcass under it and the toe kick, so a run of bases *is* the
counter run. Tall units are 96" under a 9' plate — "floor to ceiling" as the brief asks, with
the 12" of soffit/crown above them left unmodeled.

Widths are the standard 3" cabinet module (12/15/18/24/30/36), so a run is composed the way a
shop would quote it, and a leftover under 3" is a scribe/filler on the drawing rather than a
type of its own.
"""

from __future__ import annotations

from typehaus.model import FurnitureType, ft, inch

REFERENCE = "Standard frameless cabinet modules; final millwork selection by owner."

_BASE_DEPTH = ft(2)
_BASE_HEIGHT = ft(3)
_WALL_DEPTH = inch(13)
_WALL_HEIGHT = ft(3, 6)
_TALL_HEIGHT = ft(8)


def _base(tag: str, width) -> FurnitureType:
    return FurnitureType(
        tag=tag, name=f'{width.inches:.0f}" base cabinet', footprint=(width, _BASE_DEPTH),
        height=_BASE_HEIGHT, plan_symbol="base-cabinet", storage=True, source=REFERENCE,
    )


def _wall(tag: str, width) -> FurnitureType:
    return FurnitureType(
        tag=tag, name=f'{width.inches:.0f}" wall cabinet', footprint=(width, _WALL_DEPTH),
        height=_WALL_HEIGHT, plan_symbol="wall-cabinet", storage=True, source=REFERENCE,
    )


BASE_15 = _base("CASE-B15", inch(15))
BASE_24 = _base("CASE-B24", ft(2))
BASE_30 = _base("CASE-B30", inch(30))
BASE_36 = _base("CASE-B36", ft(3))
# A sink base is a different cabinet, not a base with a hole in it: no drawer box (the bowls
# take the space), doors instead of fronts, and a counter that is cut. The ``sink-base`` symbol
# models it as the shell it is, which is also the only way the sink dropped into it is visible.
SINK_BASE_36 = FurnitureType(
    tag="CASE-SINK-BASE-36", name='36" sink base', footprint=(ft(3), _BASE_DEPTH),
    height=_BASE_HEIGHT, plan_symbol="sink-base", storage=True, source=REFERENCE,
)

WALL_18 = _wall("CASE-W18", inch(18))
WALL_24 = _wall("CASE-W24", ft(2))
WALL_30 = _wall("CASE-W30", inch(30))
# Past ~36" a single box stops being buildable, but a *run* of uppers behind one continuous
# face frame is ordinary shop work — a 66" upper is two ganged boxes (30" + 36") that read and
# install as one cabinet. Modelling it as one element is the honest description of the result.
WALL_66 = _wall("CASE-W66", inch(66))

# Over-appliance uppers: the dead 24" between a 72" cold box and the 96" top of the tall run.
# Full base depth rather than the 13" of a counter upper, so their faces line up with the tall
# cabinets beside them instead of floating a shallow box over a deep appliance.
OVER_APPLIANCE_36 = FurnitureType(
    tag="CASE-OVER-36", name='36" over-appliance cabinet', footprint=(ft(3), _BASE_DEPTH),
    height=ft(2), plan_symbol="wall-cabinet", storage=True, source=REFERENCE,
)

# Tall pull-outs: one full-height door hiding a slide-out larder, which is why they read as a
# single cell rather than a drawer stack. 12" and 18" are the two widths that fit the leftover
# ends of a run without stealing counter frontage.
TALL_PANTRY_12 = FurnitureType(
    tag="CASE-TALL-PANTRY-12", name='12" tall pantry pull-out', footprint=(ft(1), _BASE_DEPTH),
    height=_TALL_HEIGHT, plan_symbol="tall-cabinet", storage=True, source=REFERENCE,
)
TALL_PANTRY_18 = FurnitureType(
    tag="CASE-TALL-PANTRY-18", name='18" tall pantry pull-out',
    footprint=(inch(18), _BASE_DEPTH), height=_TALL_HEIGHT, plan_symbol="tall-cabinet",
    storage=True, source=REFERENCE,
)
# The closet-style pantry: same carcass, but a swing door onto fixed shelves — the unit that
# holds the bulk goods a pull-out cannot.
PANTRY_CLOSET_24 = FurnitureType(
    tag="CASE-PANTRY-CLOSET-24", name='24" pantry closet', footprint=(ft(2), _BASE_DEPTH),
    height=_TALL_HEIGHT, plan_symbol="tall-cabinet", storage=True, source=REFERENCE,
)
# The double-width closet pantry: two 24" doors on one 48" carcass. Twice the shelf run of the
# 24" for the same 24" of depth, and the width at which a pantry stops being a leftover-end
# filler and becomes the room's larder — which is why it wants a wall of its own rather than a
# gap in a counter run.
PANTRY_CLOSET_48 = FurnitureType(
    tag="CASE-PANTRY-CLOSET-48", name='48" pantry closet', footprint=(ft(4), _BASE_DEPTH),
    height=_TALL_HEIGHT, plan_symbol="tall-cabinet-double", storage=True, source=REFERENCE,
)
# The linen/utility closet: three 24" doors on one 72" carcass, half again the shelf run of
# the 48" for the same depth. Wide enough that it is the storage wall of the room it stands
# in rather than a unit in a run, which is why it appears in a bathroom and not a kitchen.
PANTRY_CLOSET_72 = FurnitureType(
    tag="CASE-PANTRY-CLOSET-72", name='72" pantry closet', footprint=(ft(6), _BASE_DEPTH),
    height=_TALL_HEIGHT, plan_symbol="tall-cabinet-triple", storage=True, source=REFERENCE,
)

# An island is a base run turned loose in the room: 36" deep is 24" of carcass plus the 12"
# overhang the stools tuck under, which is why the seating side reads as counter with nothing
# below it.
ISLAND_60 = FurnitureType(
    tag="CASE-ISLAND-60", name='60" kitchen island', footprint=(ft(5), ft(3)),
    height=_BASE_HEIGHT, plan_symbol="base-cabinet", storage=True, source=REFERENCE,
)
# Counter-height seating. No pull-out zone of its own for the same reason a dining chair has
# none: the stool lives in the island's overhang, and a zone there would report the correct
# arrangement as a conflict.
BAR_STOOL = FurnitureType(
    tag="FURN-BAR-STOOL", name="Counter bar stool", footprint=(inch(16), inch(16)),
    height=ft(2, 6), plan_symbol="dining-chair", source=REFERENCE,
)

STARTER_CASEWORK_TYPES = (
    BASE_15, BASE_24, BASE_30, BASE_36, SINK_BASE_36,
    WALL_18, WALL_24, WALL_30, WALL_66, OVER_APPLIANCE_36,
    TALL_PANTRY_12, TALL_PANTRY_18, PANTRY_CLOSET_24, PANTRY_CLOSET_48,
    PANTRY_CLOSET_72,
    ISLAND_60, BAR_STOOL,
)
