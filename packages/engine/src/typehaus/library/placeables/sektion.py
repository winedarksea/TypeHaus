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
* shallow wall frames 15/20/30/40" high, 15" deep; selected 24"-deep top frames
* high frames 80" and 90", in 15" and 24" depths
* legs nominally 4 1/2" and adjustable from 3 1/2"; FÖRBÄTTRA toe kick is cut on site

** THE LEG HEIGHT IS A HOUSE DECISION. ** Heights on this ladder are multiples of five,
while the leg may be adjusted within the manufacturer's range. Finished ceilings also need
clearance for mounting cabinets. The 80" high types below include a 3 1/2" support for
Catlin's layout; the 90" types retain their earlier 3" support as legacy catalog entries.

The same arithmetic runs the other way at the counter. A 30" frame on a 3 1/2" leg tops at
33 1/2". A 36" counter with 3 cm stone needs about 1 5/16" of substrate. That build-up is
invisible under the top and is why the base types below are 36" tall rather than 33 1/2".

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
_HIGH_80 = inch(83.5)
_FRAME_90 = inch(90)


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


def _high(tag: str, width, frame_height=_FRAME_90, installed_height=_HIGH_90) -> FurnitureType:
    return FurnitureType(
        tag=tag,
        name=f'SEKTION {width.inches:.0f}" high cabinet, {frame_height.inches:.0f} in. frame',
        footprint=(width, _DEEP), height=installed_height, plan_symbol="tall-cabinet", storage=True,
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
# 40" is the tallest wall frame. Catlin uses shorter frames below its finished ceiling.
WALL_12_40 = _wall("SEKT-W12-40", ft(1), inch(40), _WALL_DEPTH)
WALL_15_40 = _wall("SEKT-W15-40", inch(15), inch(40), _WALL_DEPTH)
WALL_18_40 = _wall("SEKT-W18-40", inch(18), inch(40), _WALL_DEPTH)
WALL_24_40 = _wall("SEKT-W24-40", ft(2), inch(40), _WALL_DEPTH)
WALL_30_40 = _wall("SEKT-W30-40", inch(30), inch(40), _WALL_DEPTH)
WALL_36_40 = _wall("SEKT-W36-40", ft(3), inch(40), _WALL_DEPTH)

# 30" lower boxes and a 20" top course fit below a finished ceiling while keeping
# the backsplash tall enough for ordinary counter use.
WALL_15_30 = _wall("SEKT-W15-30", inch(15), inch(30), _WALL_DEPTH)
WALL_24_30 = _wall("SEKT-W24-30", ft(2), inch(30), _WALL_DEPTH)
WALL_30_30 = _wall("SEKT-W30-30", inch(30), inch(30), _WALL_DEPTH)
WALL_15_20 = _wall("SEKT-W15-20", inch(15), inch(20), _WALL_DEPTH)
WALL_24_20 = _wall("SEKT-W24-20", ft(2), inch(20), _WALL_DEPTH)
WALL_30_20 = _wall("SEKT-W30-20", inch(30), inch(20), _WALL_DEPTH)
WALL_36_20 = _wall("SEKT-W36-20", ft(3), inch(20), _WALL_DEPTH)

# --- 15"-deep wall cabinets, 15" high: the stacker course --------------------------------
#
# The shortest wall frame, doing the job ``CASE-WS*-12`` does in the generic catalog — with
# the difference that 15" is a real SEKTION height where 12" is not.
WALL_12_15 = _wall("SEKT-W12-15", ft(1), inch(15), _WALL_DEPTH)
WALL_15_15 = _wall("SEKT-W15-15", inch(15), inch(15), _WALL_DEPTH)
WALL_18_15 = _wall("SEKT-W18-15", inch(18), inch(15), _WALL_DEPTH)
WALL_24_15 = _wall("SEKT-W24-15", ft(2), inch(15), _WALL_DEPTH)
WALL_30_15 = _wall("SEKT-W30-15", inch(30), inch(15), _WALL_DEPTH)
WALL_36_15 = _wall("SEKT-W36-15", ft(3), inch(15), _WALL_DEPTH)

# --- 24"-deep high cabinets and stock top cabinets ---------------------------------------
#
# The legacy 90" types include a 3" support; the 80" types use a standard 3 1/2" leg.
HIGH_18_90 = _high("SEKT-HIGH18-90", inch(18))
HIGH_24_90 = _high("SEKT-HIGH24-90", ft(2))
HIGH_30_90 = _high("SEKT-HIGH30-90", inch(30))
HIGH_18_80 = _high("SEKT-HIGH18-80", inch(18), inch(80), _HIGH_80)
HIGH_24_80 = _high("SEKT-HIGH24-80", ft(2), inch(80), _HIGH_80)
# IKEA sells a narrower range of 24"-deep top cabinets than shallow wall cabinets.
# Catlin's 18x24x20 and 24x24x20 top boxes are house-local custom millwork.
TS_24_15 = _wall("SEKT-TS24-15", ft(2), inch(15), _DEEP)
TS_30_15 = _wall("SEKT-TS30-15", inch(30), inch(15), _DEEP)

SEKTION_CASEWORK_TYPES = (
    BASE_12, BASE_15, BASE_18, BASE_24, BASE_30, BASE_36, SINK_BASE_36,
    WALL_12_40, WALL_15_40, WALL_18_40, WALL_24_40, WALL_30_40, WALL_36_40,
    WALL_15_30, WALL_24_30, WALL_30_30,
    WALL_15_20, WALL_24_20, WALL_30_20, WALL_36_20,
    WALL_12_15, WALL_15_15, WALL_18_15, WALL_24_15, WALL_30_15, WALL_36_15,
    HIGH_18_90, HIGH_24_90, HIGH_30_90, HIGH_18_80, HIGH_24_80,
    TS_24_15, TS_30_15,
)
