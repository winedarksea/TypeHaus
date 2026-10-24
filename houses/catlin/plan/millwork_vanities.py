# haus: editable
# Cabinet-included shelves in the SEKTION vanities only. ÄNGSJÖN drawers and Chulton's
# purchased interior have no additional shelf-bank charge. Each bay includes its stock
# adjustable shelf and cabinet top; these are excluded from owner-milled hardwood takeoff.

from typehaus import inch
from typehaus.model import ShelfBank, ShelfBay, ShelfProcurement

BASEMENT_VANITY_SHELVES = []

MAIN_VANITY_SHELVES = [
    ShelfBank(
        uid="830F8WP640", tag="SB-M-BATH2-VAN",
        # The floating vanity's two cabinets, south to north (2026-10-22): the 12" storage
        # cabinet, then the 36" sink cabinet. Each bay is one shelf plus the case top, 14" deep
        # inside the carcass, as on every vanity. Bought with the cabinets; confirm at order.
        host="FX-M-BATH2-SINK",
        material_ref="cabinet-plywood",
        thickness=inch(0.625),
        depth=inch(14),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(10.5), clear_height=inch(28.5), shelf_count=2),
              ShelfBay(width=inch(34.5), clear_height=inch(28.5), shelf_count=2)),
    ),
]

SECOND_VANITY_SHELVES = [
    ShelfBank(
        uid="Q97KQAVZHT", tag="SB-S-VANITY-VAN1",
        # Two 30 in. wall cabinets under one fabricated 61 in. top; stock 14 in. shelves.
        host="FX-S-VANITY-LAV1",
        material_ref="cabinet-plywood",
        thickness=inch(0.75),
        depth=inch(14),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(28.5), clear_height=inch(28.5), shelf_count=2),),
    ),
    ShelfBank(
        uid="BHTA4WVJDW", tag="SB-S-VANITY-VAN2",
        host="FX-S-VANITY-LAV2",
        material_ref="cabinet-plywood",
        thickness=inch(0.75),
        depth=inch(14),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(28.5), clear_height=inch(28.5), shelf_count=2),),
    ),
]

ATTIC_VANITY_SHELVES = [
    ShelfBank(
        uid="CK6J1BJ391", tag="SB-A-STUBATH-VAN",
        # SEKTION 24 wall cabinet with its included stock shelf.
        host="FX-A-STUBATH-LAV",
        material_ref="cabinet-plywood",
        thickness=inch(0.75),
        depth=inch(14),
        profile="S4S",
        procurement=ShelfProcurement.INCLUDED_IN_HOST,
        bays=(ShelfBay(width=inch(22.5), clear_height=inch(28.5), shelf_count=2),),
    ),
]
