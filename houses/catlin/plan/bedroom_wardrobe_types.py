"""BED1-3's wardrobes: a PAX/GRIMO corner set and two 19 5/8" shelf units in BED1 and BED2,
two 39 3/8" frames behind an AULI/MEHAMN sliding pair in BED3.

House-local for the reason plan/closet_types.py gives: each row is a configuration fitted to
these rooms. The bare frames are that file's ``PROD-IKEA-PAX-WALL`` / ``-20``. Placements are
in plan/bedroom_wardrobes.py.

IKEA US listings read 2026-10-02.
"""

from __future__ import annotations

from typehaus.model import (
    ClearancePolicy,
    ClearanceZone,
    Footprint2D,
    FurnitureType,
    Product,
    inch,
    m,
    pt,
)
from typehaus.model.placeable_symbols.furniture import wardrobe_corner_points

# --- products ---------------------------------------------------------------------------

PAX_GRIMO_CORNER = Product(
    tag="PROD-IKEA-PAX-GRIMO-CORNER", brand="IKEA", model="PAX / GRIMO corner wardrobe",
    name='PAX / GRIMO corner wardrobe, white, 43 3/8 x 43 3/8 x 93 1/8"', sku="s89560818",
    url="https://www.ikea.com/us/en/p/pax-grimo-corner-wardrobe-white-s89560818/",
    source=("IKEA US listing, read 2026-10-02: $695.00. One 39 3/8 x 22 7/8 x 92 7/8\" "
            "wall-mounted frame (705.881.67), add-on corner unit with 4 shelves (303.469.34, "
            "20 7/8 x 22 7/8\"), two GRIMO 19 1/2\" doors (903.434.66), corner hinges "
            "(503.684.92), two rails, one shelf. The frame listing: 'For a solution with an "
            "add-on corner unit, leave 7.6\"/19.3 cm' from the corner wall to the wall rail, "
            "and assemble the corner unit first; the frame then fixes to it."),
)
PAX_AULI_MEHAMN_79 = Product(
    tag="PROD-IKEA-PAX-AULI-MEHAMN-79", brand="IKEA",
    model="PAX pair of sliding door frames, AULI / MEHAMN panels",
    name='AULI / MEHAMN pair of sliding doors, mirror glass/white, 78 3/4 x 92 7/8"',
    sku="095.603.08",
    url="https://www.ikea.com/us/en/p/auli-mehamn-pair-of-sliding-doors-mirror-glass-white-09560308/",
    source=("IKEA US listing, read 2026-10-02: $470.00; 3 1/8\" built-in depth, 94 1/2\" "
            "minimum ceiling. Parts: PAX sliding door frames and rail 804.581.94, AULI "
            "mirror panels 605.877.43, MEHAMN white panels 804.211.86. The wall-mounted "
            "92 7/8\" frame's own listing says it takes a sliding door at that ceiling."),
)

BEDROOM_WARDROBE_PRODUCTS = (PAX_GRIMO_CORNER, PAX_AULI_MEHAMN_79)

# --- types ------------------------------------------------------------------------------

_PAX_SOURCE = ("PAX wall-mounted frame on its rail, hung 1/4\" off the carpet. Authored "
               "FLOOR for the backing-check reason in plan/closet.py.")
_CORNER = inch(43.375)
_LEG = inch(22.875)
_DOOR = inch(19.5)

_ring = wardrobe_corner_points(_CORNER.meters, _CORNER.meters, _LEG.meters)
_inner_x, _inner_y = _ring[2]


def _door_zone(x0: float, y0: float, x1: float, y1: float, purpose: str) -> ClearanceZone:
    return ClearanceZone(
        footprint=Footprint2D(points=tuple(pt(m(x), m(y)) for x, y in
                                           ((x0, y0), (x1, y0), (x1, y1), (x0, y1)))),
        purpose=purpose, policy=ClearancePolicy.RECOMMENDED, source="planning standard")


# The frame runs along the wall (+y) and the corner unit returns down the -x end, so the
# return is on the LEFT seen from the room. One 19 1/2" GRIMO door on each inner face of
# the L; each zone is that door's swing.
# The material ref colors only frame/shelf wood parts; door and metal roles keep their colors.
PAX_CORNER = FurnitureType(
    tag="FURN-S-PAX-CORNER",
    name='PAX/GRIMO corner wardrobe, 43 3/8" L both ways, two doors',
    footprint=(_CORNER, _CORNER), height=inch(93.125),
    footprint_shape=Footprint2D(points=tuple(pt(m(x), m(y)) for x, y in _ring)),
    storage=True, work_surface=False, plan_symbol="wardrobe-corner",
    wood_material_ref="pax-frame-white",
    product_ref="PROD-IKEA-PAX-GRIMO-CORNER",
    clearances=(
        _door_zone(_inner_x, _inner_y - _DOOR.meters, _CORNER.meters / 2, _inner_y,
                   "frame door swing"),
        _door_zone(_inner_x, -_CORNER.meters / 2, _inner_x + _DOOR.meters, _inner_y,
                   "corner unit door swing"),
    ),
    source=_PAX_SOURCE + " The frame is double-hung (rails 38 3/4\"/78 3/4\", shelf 81 1/2\")."
)
PAX_SHELF_20 = FurnitureType(
    tag="FURN-S-PAX-SHELF-20", name='PAX 19 5/8" open frame, six shelves',
    footprint=(inch(19.625), inch(22.875)), height=inch(92.875),
    storage=True, work_surface=False, plan_symbol="wardrobe-shelves",
    wood_material_ref="pax-frame-white",
    product_ref="PROD-IKEA-PAX-WALL-20", source=_PAX_SOURCE,
)
PAX_SHELF_40 = FurnitureType(
    tag="FURN-S-PAX-SHELF-40", name='PAX 39 3/8" frame, six shelves, behind sliders',
    footprint=(inch(39.375), inch(22.875)), height=inch(92.875),
    storage=True, work_surface=False, plan_symbol="wardrobe-shelves",
    wood_material_ref="pax-frame-white",
    product_ref="PROD-IKEA-PAX-WALL", source=_PAX_SOURCE,
)
PAX_DOUBLE_40 = FurnitureType(
    tag="FURN-S-PAX-DOUBLE-40",
    name='PAX 39 3/8" frame, two rails (38 3/4"/78 3/4"), shelf at 81 1/2", behind sliders',
    footprint=(inch(39.375), inch(22.875)), height=inch(92.875),
    storage=True, work_surface=False, plan_symbol="wardrobe-double-hang",
    wood_material_ref="pax-frame-white",
    product_ref="PROD-IKEA-PAX-WALL", source=_PAX_SOURCE,
)
# No clearance zone: it slides. work_surface=None so the frames behind it break the wall
# space once, not twice.
PAX_SLIDE_79 = FurnitureType(
    tag="FURN-S-PAX-SLIDE-79",
    name='PAX sliding pair, 78 3/4" x 92 7/8": AULI mirror (right) + MEHAMN white (left)',
    footprint=(inch(78.75), inch(3.125)), height=inch(92.875),
    work_surface=None, plan_symbol="wardrobe-sliding-pair",
    product_ref="PROD-IKEA-PAX-AULI-MEHAMN-79",
    source="Top and bottom rails fix to the frames' fronts; the mirror is the front track.",
)

BEDROOM_WARDROBE_TYPES = (PAX_CORNER, PAX_SHELF_20, PAX_SHELF_40, PAX_DOUBLE_40,
                          PAX_SLIDE_79)
