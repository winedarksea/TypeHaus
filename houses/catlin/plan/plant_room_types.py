"""Plant-room display products and illustrative plants; mounting detail in the room note."""

from __future__ import annotations

from typehaus import (
    ClearanceZone,
    Footprint2D,
    FurnitureType,
    Mount,
    MountKind,
    Product,
    inch,
    pt,
)

SKUGGRONA_HEIGHT_IN = 30.75
SKUGGRONA_WIDTH_IN = 5.5
SKUGGRONA_BRACKET_SPACING_MM = 720
SKUGGRONA_MAX_SHELF_LOAD_LB = 6.6
SKUGGRONA_SHELF_TOPS_IN = (2.0, 14.25, 27.0)
SMALL_PLANT_HEIGHT_IN = 8
HANGING_ASSEMBLY_HEIGHT_IN = 46
HANGING_FOLIAGE_DIAMETER_IN = 16
HANGING_SATURATED_LOAD_ALLOWANCE_LB = 50

SKUGGRONA = Product(
    tag="PROD-IKEA-SKUGGRONA-20562018", brand="IKEA", model="SKUGGRÖNA",
    sku="205.620.18", name="SKUGGRÖNA black wall-mounted three-shelf plant stand",
    url="https://www.ikea.com/us/en/p/skuggroena-wall-mounted-plant-stand-black-20562018/",
    source=("IKEA US listing and AA-2435064-2 mounting template, read 2026-10-04: "
            "30 3/4-inch height, 5 1/2-inch width, recommended maximum pot diameter "
            "3 1/2 inches, 6.6 lb per shelf. Broad-face brackets are 720 mm apart. "
            "Depth and tray heights are illustrative; verify against the delivered stand."),
)

_POT_OCCUPANCY = Footprint2D(points=(
    pt(inch(-2.75), inch(-2.75)), pt(inch(2.75), inch(-2.75)),
    pt(inch(2.75), inch(2.75)), pt(inch(-2.75), inch(2.75)),
))
SMALL_PLANT = FurnitureType(
    tag="FT-PLANT-ROOM-POT-3P5", name='Illustrative plant in a 3 1/2-inch pot',
    footprint=(inch(SKUGGRONA_WIDTH_IN), inch(SKUGGRONA_WIDTH_IN)),
    height=inch(SMALL_PLANT_HEIGHT_IN), plan_symbol="small-potted-plant",
    mount=Mount(kind=MountKind.FLOOR),
    source=("White 3 1/2-inch pot with illustrative tropical foliage; 5 1/2-inch canopy. "
            "Pot, saturated medium, plant and retained water together must remain "
            "within the stand's 6.6 lb per-shelf rating; species and pot product unselected."),
)
WALL_STAND = FurnitureType(
    tag="FT-PLANT-ROOM-SKUGGRONA", name="SKUGGRÖNA black three-shelf plant stand",
    footprint=(inch(SKUGGRONA_WIDTH_IN), inch(SKUGGRONA_WIDTH_IN)),
    height=inch(SKUGGRONA_HEIGHT_IN), plan_symbol="wall-plant-stand",
    product_ref=SKUGGRONA.tag, mount=Mount(kind=MountKind.WALL),
    # The occupancy zone groups all three vertically stacked pots with their stand.
    clearances=(ClearanceZone(footprint=_POT_OCCUPANCY, purpose="plants supported by the stand",
                              occupant_types=(SMALL_PLANT.tag,)),),
    source=("Broad back against north wall; three separate potted plants on illustrative "
            "tray tops 2, 14 1/4 and 27 inches above the stand's bottom. Upper and lower "
            "brackets screw through sealed rigid spacers into two stud-bay 2x8 blocks. "
            "Use the manufacturer's 720 mm mounting template, not the drawn tray heights. "
            "notes/plant_room.md — Plant displays and mounting support."),
)
HANGING_VINE = FurnitureType(
    tag="FT-PLANT-ROOM-HANGING-VINE-12", name='12-inch hanging basket with trailing vines',
    footprint=(inch(HANGING_FOLIAGE_DIAMETER_IN), inch(HANGING_FOLIAGE_DIAMETER_IN)),
    height=inch(HANGING_ASSEMBLY_HEIGHT_IN), plan_symbol="hanging-vine-planter",
    mount=Mount(kind=MountKind.CEILING),
    source=("Illustrative 12-inch terracotta basket, 16-inch foliage envelope, "
            "24-inch trailing vines and 22-inch cords to a closed-eye joist plate. "
            f"Provisional fully watered load allowance {HANGING_SATURATED_LOAD_ALLOWANCE_LB} lb "
            "per basket; actual joist series, plate and fasteners remain to be specified "
            "against the selected manufacturer's bottom-flange attachment requirements. "
            "notes/plant_room.md — Plant displays and mounting support."),
)

PLANT_ROOM_FURNITURE_TYPES = (WALL_STAND, SMALL_PLANT, HANGING_VINE)
PLANT_ROOM_PRODUCTS = (SKUGGRONA,)
