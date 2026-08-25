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

from typehaus.model import FurnitureType, Mount, MountKind, ft, inch

from library.placeables._zones import front_zone

REFERENCE = "Standard frameless cabinet modules; final millwork selection by owner."

_BASE_DEPTH = ft(2)
_BASE_HEIGHT = ft(3)
_WALL_DEPTH = inch(13)
_WALL_HEIGHT = ft(3, 6)
_TALL_HEIGHT = ft(8)
# The stacker course: 96" upper top -> 108" ceiling. A 12" box is a stock size (the
# "wall bridge"), so closing that gap is a catalog part and not a custom height.
_STACK_HEIGHT = ft(1)

BESTA_UNIT = FurnitureType(
    tag="FURN-BESTA-2358",
    name='IKEA BESTA with doors, 23 5/8 x 16 1/2 x 25 1/4 in on 2x4 frame',
    footprint=(inch(23.625), inch(16.5)),
    height=inch(29.75),
    plan_symbol="besta",
    storage=True,
    source=("IKEA BESTA with doors on a 2x4 frame, wall-matching baseboard, and a "
            "continuous 1-inch white countertop."),
)


def _base(tag: str, width) -> FurnitureType:
    return FurnitureType(
        tag=tag, name=f'{width.inches:.0f}" base cabinet', footprint=(width, _BASE_DEPTH),
        height=_BASE_HEIGHT, plan_symbol="base-cabinet", storage=True, work_surface=True,
        source=REFERENCE,
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
    height=_BASE_HEIGHT, plan_symbol="sink-base", storage=True, work_surface=True,
    source=REFERENCE,
)

# The missing rung on this module's own width ladder (18/24/30/66), and a stock size
# everywhere: 12" is what is left over the head of a small window at the end of a run.
WALL_12 = _wall("CASE-W12", ft(1))
# 15" is on the module and on every stock list; the base ladder has had CASE-B15 since the
# beginning and the wall ladder simply never needed one until a 15" gap turned up.
WALL_15 = _wall("CASE-W15", inch(15))
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
    height=_TALL_HEIGHT, plan_symbol="tall-cabinet", storage=True, work_surface=False,
    source=REFERENCE,
)
TALL_PANTRY_18 = FurnitureType(
    tag="CASE-TALL-PANTRY-18", name='18" tall pantry pull-out',
    footprint=(inch(18), _BASE_DEPTH), height=_TALL_HEIGHT, plan_symbol="tall-cabinet",
    storage=True, work_surface=False, source=REFERENCE,
)
# The closet-style pantry: same carcass, but a swing door onto fixed shelves — the unit that
# holds the bulk goods a pull-out cannot.
PANTRY_CLOSET_24 = FurnitureType(
    tag="CASE-PANTRY-CLOSET-24", name='24" pantry closet', footprint=(ft(2), _BASE_DEPTH),
    height=_TALL_HEIGHT, plan_symbol="tall-cabinet", storage=True, work_surface=False,
    source=REFERENCE,
)
# The double-width closet pantry: two 24" doors on one 48" carcass. Twice the shelf run of the
# 24" for the same 24" of depth, and the width at which a pantry stops being a leftover-end
# filler and becomes the room's larder — which is why it wants a wall of its own rather than a
# gap in a counter run.
PANTRY_CLOSET_48 = FurnitureType(
    tag="CASE-PANTRY-CLOSET-48", name='48" pantry closet', footprint=(ft(4), _BASE_DEPTH),
    height=_TALL_HEIGHT, plan_symbol="tall-cabinet-double", storage=True, work_surface=False,
    source=REFERENCE,
)
# The linen/utility closet: three 24" doors on one 72" carcass, half again the shelf run of
# the 48" for the same depth. Wide enough that it is the storage wall of the room it stands
# in rather than a unit in a run, which is why it appears in a bathroom and not a kitchen.
PANTRY_CLOSET_72 = FurnitureType(
    tag="CASE-PANTRY-CLOSET-72", name='72" pantry closet', footprint=(ft(6), _BASE_DEPTH),
    height=_TALL_HEIGHT, plan_symbol="tall-cabinet-triple", storage=True, work_surface=False,
    source=REFERENCE,
)

# An island is a base run turned loose in the room: 36" deep is 24" of carcass plus the 12"
# overhang the stools tuck under, which is why the seating side reads as counter with nothing
# below it.
ISLAND_60 = FurnitureType(
    tag="CASE-ISLAND-60", name='60" kitchen island', footprint=(ft(5), ft(3)),
    height=_BASE_HEIGHT, plan_symbol="base-cabinet", storage=True, work_surface=True,
    source=REFERENCE,
)
# A peninsula is an island with one end landed on a wall, so the aisle it used to need on
# that side becomes counter. 39" deep, not the 36" ISLAND_60 carries: 24" of carcass plus
# NKBA's **15"** of knee space for a 36"-high counter. The 12" overhang above is the figure
# for a 42" BAR-height top, where the legs tuck under differently — at 36" it is short, and
# ISLAND_60's 36" total was always the wrong number for a seated counter.
#
# Deliberately no ``clearances``, per this module's header rule: which side overhangs and
# what sits against the far end are properties of the layout, stated at the instance and by
# the stools, not of the type. ``advisory.clearance_overlap`` therefore does not grade it.
PENINSULA_120 = FurnitureType(
    tag="CASE-PENINSULA-120", name='120" kitchen peninsula', footprint=(ft(10), inch(39)),
    height=_BASE_HEIGHT, plan_symbol="base-cabinet", storage=True, work_surface=True,
    source=REFERENCE,
)


# The stacker course. Its whole design is the DEPTH split, which is not an oversight: a
# stacker inherits the depth of the box it sits on, so one over a 13" counter upper is 13"
# deep and one over a 24" over-appliance box is 24" deep. A single depth would either float
# a shallow box over the cold run or hang a 24" box 8' up over a work counter.
def _stacker(tag: str, width, depth) -> FurnitureType:
    return FurnitureType(
        tag=tag, name=f'{width.inches:.0f}" stacker cabinet', footprint=(width, depth),
        height=_STACK_HEIGHT, plan_symbol="wall-cabinet", storage=True, source=REFERENCE,
    )


# WS = over a 13"-deep WALL cabinet. TS = over a 24"-deep TALL or over-appliance one. The
# prefix carries the depth because the width alone cannot: a 24" stacker exists in both.
STACK_W15 = _stacker("CASE-WS15-12", inch(15), _WALL_DEPTH)
STACK_W24 = _stacker("CASE-WS24-12", ft(2), _WALL_DEPTH)
STACK_W30 = _stacker("CASE-WS30-12", inch(30), _WALL_DEPTH)
# 36" is the stock "bridge" width — the box sold to span a range or a sink. It earns its
# place in the stacker family for the reason a stacker course exists at all: at 96" the
# course is ABOVE every window head, so it can run straight across an opening the 54"
# uppers had to stop either side of (catlin's WIN-M-KITCH, head 78").
STACK_W36 = _stacker("CASE-WS36-12", ft(3), _WALL_DEPTH)
# The rung that closes a 96" tall cabinet to a 108" ceiling. Same box as CASE-WS24-12 at
# twice the depth, which is the whole reason the two cannot share a tag.
STACK_T24 = _stacker("CASE-TS24-12", ft(2), _BASE_DEPTH)
# The narrow rungs of the same course. A tall cabinet that oversails the end of its wall —
# which is how a 24" box against a short return ends up standing in a doorway — takes one of
# these instead, so the course stops where the wall does rather than carrying the oversail 8'
# up over a passage. Pick the widest that still lands clear of the wall's end; catlin's
# FURN-M-KIT-PANTRYC-ST has been both, at 15" and then 18" once its oversail shrank.
STACK_T15 = _stacker("CASE-TS15-12", inch(15), _BASE_DEPTH)
STACK_T18 = _stacker("CASE-TS18-12", inch(18), _BASE_DEPTH)
# 32 7/8" is not on the 3" module and never will be: it is an appliance width (see the
# catlin house's FT-KIT-OVER-COLD-3278), carried up so the stacker's face lines up with the
# over-appliance box below it rather than leaving a 3" step at 8'-0".
STACK_T3278 = _stacker("CASE-TS3278-12", inch(32.875), _BASE_DEPTH)

# Counter-height seating. No pull-out zone of its own for the same reason a dining chair has
# none: the stool lives in the island's overhang, and a zone there would report the correct
# arrangement as a conflict.
BAR_STOOL = FurnitureType(
    tag="FURN-BAR-STOOL", name="Counter bar stool", footprint=(inch(16), inch(16)),
    height=ft(2, 6), plan_symbol="dining-chair", source=REFERENCE,
)

# The fold-down drying rack over a laundry tub. The one piece of casework in this module that
# *does* carry a clearance zone, and for the reason the module header gives for withholding
# them elsewhere: a cabinet's front is where you stand, but this rack's front is where it
# physically goes. Folded flat it is a 5" board on the wall; folded down it swings its arms
# 16" into the room, and that band has to be clear of anything tall.
#
# ``occupant_types`` names the laundry tub because the rack hangs *over* it — the sink under
# the deployed arms is the arrangement working, not an encroachment, so it groups with the
# rack instead of reporting against it. (The vertical body test would clear a 43" sink under
# a 48" rack anyway; naming it here makes the intent explicit rather than incidental.)
WALL_DRYING_RACK_24 = FurnitureType(
    tag="FURN-WALL-RACK-24", name='24" fold-down wall drying rack',
    footprint=(inch(24), inch(5)), height=inch(30), plan_symbol="wall-rack", storage=True,
    mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
    clearances=(front_zone(inch(24), inch(5), inch(16), "drying rack, folded down",
                           occupant_types=("FX-LAUNDRY-SINK-24",)),),
    source="Wall-mounted folding drying rack; 5\" deep stowed, ~16\" of arm deployed. "
           "Final selection by owner.",
)

STARTER_CASEWORK_TYPES = (
    BESTA_UNIT, BASE_15, BASE_24, BASE_30, BASE_36, SINK_BASE_36,
    WALL_18, WALL_24, WALL_30, WALL_66, OVER_APPLIANCE_36,
    TALL_PANTRY_12, TALL_PANTRY_18, PANTRY_CLOSET_24, PANTRY_CLOSET_48,
    PANTRY_CLOSET_72,
    ISLAND_60, PENINSULA_120, BAR_STOOL, WALL_DRYING_RACK_24,
    WALL_12, WALL_15, STACK_W15, STACK_W24, STACK_W30, STACK_W36,
    STACK_T15, STACK_T18, STACK_T24, STACK_T3278,
)
