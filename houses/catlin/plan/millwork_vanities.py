# haus: editable
# Catlin house millwork — the one shelf inside each bath vanity's sink base.
#
# Split out of plan/millwork.py (which had passed the 500-line rule): eight banks, one per
# vanity, all the same reasoning.
#
# ** THE CABINET'S OWN SHELF, NOT OWNER OAK ** (owner, 2026-10-07). Each is the one
# adjustable shelf a plain two-door sink base ships with, so it is INCLUDED_IN_HOST: priced
# in the FX-VANITY-* row, out of `haus millwork`. Hidden under a trap is the worst place in
# a bath for hardwood. `material_ref` is `cabinet-plywood` for that reason.
#
# The owner asked for drawer AND shelf space. Drawers are NOT modelled (no drawer
# vocabulary), but the bank keeps the shelf on record. `shelf_count=2` is that shelf plus the
# case top, per ShelfBay's convention. A drawer base runs ~1.5x a door base, which is why
# these are door boxes.
#
# `host` IS A FIXTURE, which is legal: `resolve/millwork.py` builds its placeable map from
# `model.canvas_objects`, which carries Fixtures alongside Furniture.
#
# `depth` IS AUTHORED ON EVERY ONE, AND MUST BE: `_carcass_depth_m` is keyed on
# FurnitureTypes and every host here is a FixtureType, so an underived depth is a hard
# finding. It is the carcass less a 3/4" back and a 1 3/4" scribe/trap set-off — 18 1/2"
# in a 21" (-SINGLE) cabinet, 15 1/2" in an 18" (-SHALLOW) one. `width` is the sink base
# less 1 1/2" of case sides. `clear_height` is 34 1/2" of carcass less a 4 1/2" toe kick
# and the 3/4" counter substrate.

from typehaus import inch
from typehaus.model import ShelfBank, ShelfBay, ShelfProcurement

BASEMENT_VANITY_SHELVES = [
    ShelfBank(
        uid="6BNKG0ZT0K", tag="SB-B-BATH-VAN",
        # 36" x 18" carcass; the depth is the door swing's, not a preference.
        host="FX-B-BATH-LAV",
        material_ref="cabinet-plywood",
        thickness=inch(0.75),
        depth=inch(15.5),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(34.5), clear_height=inch(29.25), shelf_count=2),),
    ),
]

MAIN_VANITY_SHELVES = [
    ShelfBank(
        uid="3EWQ9BGVH8", tag="SB-M-BATH1-VAN",
        # 24" x 18" carcass, the smallest vanity in the house.
        host="FX-M-BATH1-LAV",
        material_ref="cabinet-plywood",
        thickness=inch(0.75),
        depth=inch(15.5),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(22.5), clear_height=inch(29.25), shelf_count=2),),
    ),
    ShelfBank(
        uid="830F8WP640", tag="SB-M-BATH2-VAN",
        # The 30" sink base at the SOUTH end of the 48" vanity; the 18" drawer bank is not
        # shelved. 15 1/2", not 18 1/2": the carcass went 21" -> 18" deep on 2026-09-09 and
        # an 18 1/2" shelf would have stood proud of the box it sits in.
        host="FX-M-BATH2-SINK",
        material_ref="cabinet-plywood",
        thickness=inch(0.75),
        depth=inch(15.5),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(28.5), clear_height=inch(29.25), shelf_count=2),),
    ),
]

SECOND_VANITY_SHELVES = [
    ShelfBank(
        uid="FT01G11CY0", tag="SB-S-BATH1-VAN",
        # The 30" SINK BASE half of the 48" vanity; the north 18" is a drawer
        # bank and is not shelved. 21" carcass, so 18 1/2" clear.
        host="FX-S-BATH1-LAV",
        material_ref="cabinet-plywood",
        thickness=inch(0.75),
        depth=inch(18.5),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(28.5), clear_height=inch(29.25), shelf_count=2),),
    ),
    ShelfBank(
        uid="XT028WRQR2", tag="SB-S-SUITEBATH-VAN",
        host="FX-S-SUITEBATH-LAV",
        material_ref="cabinet-plywood",
        thickness=inch(0.75),
        depth=inch(18.5),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(28.5), clear_height=inch(29.25), shelf_count=2),),
    ),
    ShelfBank(
        uid="Q97KQAVZHT", tag="SB-S-VANITY-VAN1",
        # The alcove's two 30" bases under one 61" double top: two cabinets,
        # so two banks. 18" carcasses, so 15 1/2" clear.
        host="FX-S-VANITY-LAV1",
        material_ref="cabinet-plywood",
        thickness=inch(0.75),
        depth=inch(15.5),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(28.5), clear_height=inch(29.25), shelf_count=2),),
    ),
    ShelfBank(
        uid="BHTA4WVJDW", tag="SB-S-VANITY-VAN2",
        host="FX-S-VANITY-LAV2",
        material_ref="cabinet-plywood",
        thickness=inch(0.75),
        depth=inch(15.5),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(28.5), clear_height=inch(29.25), shelf_count=2),),
    ),
]

ATTIC_VANITY_SHELVES = [
    ShelfBank(
        uid="CK6J1BJ391", tag="SB-A-STUBATH-VAN",
        # FX-VANITY-24-SHALLOW, the twin of SB-M-BATH1-VAN: same carcass, same shelf.
        host="FX-A-STUBATH-LAV",
        material_ref="cabinet-plywood",
        thickness=inch(0.75),
        depth=inch(15.5),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(22.5), clear_height=inch(29.25), shelf_count=2),),
    ),
]
