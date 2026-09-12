"""IKEA SEKTION casework — the published frameless ladder, as dimensions.

``casework.py`` is a generic US 3"-module catalog: 13" uppers, 42" upper height, a 96" tall
frame and a 12" stacker. Those are reasonable shop numbers and **none of them is a SEKTION
size**, so a house that has decided on SEKTION and still composes runs out of ``CASE-*`` is
dimensioning against boxes it cannot order. This module is the ladder it can.

** THIS IS A DIMENSION SET, NOT A PURCHASE. ** No ``product_ref``, no fronts, no prices. A
house's choice of carcass supplier and door line is the house's, recorded in its own
``plan/products_*.py`` and ``prices.toml``; SEKTION's frame ladder is published, and
Semihandmade, Barker and every other aftermarket door shop builds to it, so a house on
those doors uses these same types. The shared catalog carries the sizes; the house carries
the order.

The ladder (ikea.com/us, verified 2026-09-11):

* base frames 30" high, 24" deep, widths 12/15/18/21/24/30/36/38/47
* wall frames 15/20/30/40" high, in 15" and 24" depths
* high frames 80" and 90", in 15" and 24" depths
* legs nominally 4 1/2" and adjustable; FÖRBÄTTRA toe kick is a board cut on site

** THE LEG IS THE ONE FREE VARIABLE, AND IT IS WHAT CLOSES A CEILING. ** Heights on this
ladder are all multiples of 5, so a stack reaches 70" from a counter and never 72", and 108"
is unreachable from a 4 1/2" leg: 4.5 + 90 + 15 overshoots to 109 1/2 and 4.5 + 80 + 20
stops 3 1/2" short. Shortening the leg is ordinary — it is a screw-adjustable foot behind a
cut board — so the elevations below are stated as the FINISHED object and the toe height is
a house's stack-up note, not a catalog constant. A 3" leg closes 108" exactly:
3 + 90 + 15 for a tall run, 40 + 15 hung at 53 for a counter run.

The same arithmetic runs the other way at the counter. A 30" frame on a 3" leg tops at 33",
so a 36" counter wants 3" of build-up plus top; a 1 1/2" laminate needs 1 1/2" of sub-top
and a 3 cm stone needs 1 13/16". That build-up is invisible under the top and is why the
base types below are 36" tall rather than 33".

Like ``casework.py``, nothing here carries a clearance zone: the aisle in front of a run is
a property of the room, not of any one box.
"""

from __future__ import annotations

from typehaus.model import FurnitureType, ft, inch

REFERENCE = ("IKEA SEKTION frame ladder (ikea.com/us, 2026-09-11). Frame sizes only — "
             "carcass supplier and door line are the house's own decision.")

_BASE_DEPTH = ft(2)
_BASE_HEIGHT = ft(3)
# 15" is SEKTION's shallow wall depth. There is no 13": the generic catalog's number is a
# face-frame convention and the frameless ladder does not have it.
_WALL_DEPTH = inch(15)
_DEEP = _BASE_DEPTH
# A 90" frame on a 3" leg. The tag names the FRAME, which is what is ordered; the height is
# what the box occupies on the floor.
_HIGH_90 = inch(93)


def _base(tag: str, width) -> FurnitureType:
    return FurnitureType(
        tag=tag, name=f'SEKTION {width.inches:.0f}" base cabinet',
        footprint=(width, _BASE_DEPTH), height=_BASE_HEIGHT, plan_symbol="base-cabinet",
        storage=True, work_surface=True, source=REFERENCE,
    )


def _wall(tag: str, width, height, depth) -> FurnitureType:
    return FurnitureType(
        tag=tag, name=f'SEKTION {width.inches:.0f}x{height.inches:.0f} wall cabinet',
        footprint=(width, depth), height=height, plan_symbol="wall-cabinet", storage=True,
        source=REFERENCE,
    )


def _high(tag: str, width) -> FurnitureType:
    return FurnitureType(
        tag=tag, name=f'SEKTION {width.inches:.0f}" high cabinet, 90 in. frame',
        footprint=(width, _DEEP), height=_HIGH_90, plan_symbol="tall-cabinet", storage=True,
        work_surface=False, source=REFERENCE,
    )


# --- bases ------------------------------------------------------------------------------
BASE_12 = _base("SEKT-B12", ft(1))
BASE_15 = _base("SEKT-B15", inch(15))
BASE_18 = _base("SEKT-B18", inch(18))
BASE_24 = _base("SEKT-B24", ft(2))
BASE_30 = _base("SEKT-B30", inch(30))
BASE_36 = _base("SEKT-B36", ft(3))
# Same frame as SEKT-B36; a different cabinet because the bowls take the drawer space and
# the top is cut. The ``sink-base`` symbol is what draws that.
SINK_BASE_36 = FurnitureType(
    tag="SEKT-SINK-B36", name='SEKTION 36" sink base', footprint=(ft(3), _BASE_DEPTH),
    height=_BASE_HEIGHT, plan_symbol="sink-base", storage=True, work_surface=True,
    source=REFERENCE,
)

# --- 15"-deep wall cabinets, 40" high -----------------------------------------------------
#
# 40" is the tallest wall frame, and on this ladder it is the one that pays: hung at 53" it
# tops at 93", leaving exactly one 15" course to a 9' ceiling. A 30" frame hung at the same
# 53" would need 25" above it, which is two courses and a filler.
WALL_12_40 = _wall("SEKT-W12-40", ft(1), inch(40), _WALL_DEPTH)
WALL_15_40 = _wall("SEKT-W15-40", inch(15), inch(40), _WALL_DEPTH)
WALL_18_40 = _wall("SEKT-W18-40", inch(18), inch(40), _WALL_DEPTH)
WALL_24_40 = _wall("SEKT-W24-40", ft(2), inch(40), _WALL_DEPTH)
WALL_30_40 = _wall("SEKT-W30-40", inch(30), inch(40), _WALL_DEPTH)
WALL_36_40 = _wall("SEKT-W36-40", ft(3), inch(40), _WALL_DEPTH)

# --- 15"-deep wall cabinets, 15" high: the stacker course --------------------------------
#
# The shortest wall frame, doing the job ``CASE-WS*-12`` does in the generic catalog — with
# the difference that 15" is a real SEKTION height where 12" is not. At 93" this course is
# above every window head in an ordinary room, so it can run straight across an opening the
# 53" boxes had to stop either side of.
WALL_12_15 = _wall("SEKT-W12-15", ft(1), inch(15), _WALL_DEPTH)
WALL_15_15 = _wall("SEKT-W15-15", inch(15), inch(15), _WALL_DEPTH)
WALL_18_15 = _wall("SEKT-W18-15", inch(18), inch(15), _WALL_DEPTH)
WALL_24_15 = _wall("SEKT-W24-15", ft(2), inch(15), _WALL_DEPTH)
WALL_30_15 = _wall("SEKT-W30-15", inch(30), inch(15), _WALL_DEPTH)
WALL_36_15 = _wall("SEKT-W36-15", ft(3), inch(15), _WALL_DEPTH)

# --- 24"-deep wall cabinets ---------------------------------------------------------------
#
# The over-appliance boxes, and the depth is the whole point: a 15" box floating over a 27"
# refrigerator column reads as a shelf, where a 24" one lands its face on the tall cabinets
# beside it. ``TW`` for "tall-depth wall", the prefix carrying the depth because the width
# cannot — a 24"-wide box exists in both families.
TW_24_30 = _wall("SEKT-TW24-30", ft(2), inch(30), _DEEP)
TW_24_40 = _wall("SEKT-TW24-40", ft(2), inch(40), _DEEP)
TW_30_30 = _wall("SEKT-TW30-30", inch(30), inch(30), _DEEP)
TW_36_30 = _wall("SEKT-TW36-30", ft(3), inch(30), _DEEP)

# --- 24"-deep high cabinets, and the course that closes them to the ceiling ----------------
#
# 90" is the taller of the two high frames. On a 3" leg it tops at 93", which is why the
# stacker below is 15" and not the generic catalog's 12".
HIGH_18_90 = _high("SEKT-HIGH18-90", inch(18))
HIGH_24_90 = _high("SEKT-HIGH24-90", ft(2))
HIGH_30_90 = _high("SEKT-HIGH30-90", inch(30))
# ``TS`` = the 15" course at base depth, over a high cabinet or an over-appliance box. A
# narrow rung exists for the same reason it does in ``casework.py``: a tall cabinet that
# oversails the end of its wall takes the widest box that still lands clear of that end,
# so the course stops where the wall does rather than carrying the oversail 8' up.
TS_18_15 = _wall("SEKT-TS18-15", inch(18), inch(15), _DEEP)
TS_24_15 = _wall("SEKT-TS24-15", ft(2), inch(15), _DEEP)
TS_30_15 = _wall("SEKT-TS30-15", inch(30), inch(15), _DEEP)

SEKTION_CASEWORK_TYPES = (
    BASE_12, BASE_15, BASE_18, BASE_24, BASE_30, BASE_36, SINK_BASE_36,
    WALL_12_40, WALL_15_40, WALL_18_40, WALL_24_40, WALL_30_40, WALL_36_40,
    WALL_12_15, WALL_15_15, WALL_18_15, WALL_24_15, WALL_30_15, WALL_36_15,
    TW_24_30, TW_24_40, TW_30_30, TW_36_30,
    HIGH_18_90, HIGH_24_90, HIGH_30_90,
    TS_18_15, TS_24_15, TS_30_15,
)
