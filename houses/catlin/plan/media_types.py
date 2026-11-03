"""The theatre: a 98" screen on a stand-off mount and two wall tapestries, RM-B-PLAY-N
(plan/placeables.py).

The shared FURN-TV-98-WALL is a 4" envelope with the mount folded in. Here the body is the
panel alone and the mount is the placement's ``normal_gap``, so ED-B-PLAY-N-RC1 and -DATA1
(surface boxes, 2 5/8" with cover) sit behind the panel (geometry review C6-E11, adopted
2026-11-01). TCL 98QM8L on a Monoprice 12994 since 2026-11-02.
"""

from typehaus import FurnitureType, ModelRepresentation, Mount, MountKind, Product, inch
from typehaus.model import ProductPart

#: Wall to panel back: the Monoprice tilt mount at zero tilt. Box plus raised cover is
#: 2 5/8" and a flat plug 7/8", so 3 1/2" is the floor; fixed and low-tilt mounts sit at 1-2 5/8".
TV_MOUNT_STANDOFF = inch(5.125)

TCL_98QM8L = Product(
    tag="PROD-TCL-98QM8L", brand="TCL", model="98QM8L",
    name='98" QM8L SQD Mini-LED 4K Google TV (2026)',
    url="https://www.pcrichard.com/tcl-98-class-qm8l-qled-mini-led-4k-uhd-smart-google-tv/98QM8L.html",
    source="Owner, 2026-11-02. PC Richard and displayinput.com, read 2026-11-02: 85.3 x 48.7 x "
           "2.1 in. without stand, 121.3-126.8 lb. VESA 600 x 500 (M8) per the 98QM8K "
           "sibling: CONFIRM in the QM8L manual before ordering the mount.",
)
MONOPRICE_12994 = Product(
    tag="PROD-MONOPRICE-12994", brand="Monoprice", model="12994",
    name='Stable Series extra-wide tilt TV wall mount, 60-100"',
    url="https://www.monoprice.com/product?p_id=12994",
    source="Newegg and retailer listings, read 2026-11-02: back of TV 5.1 in. off the wall, "
           "+/-15 deg tilt, VESA to 1000 x 800, 220 lb (one distributor says 175.9: either "
           "clears the TV), brick/concrete/wood. CONFIRM the concrete anchors in the kit, "
           "else sleeve anchors into W-B-N1's pour.",
)

TV_98_PANEL = FurnitureType(
    tag="FT-TV-98-PANEL", name='98" television (TCL 98QM8L) on a 5 1/8" tilt wall mount',
    footprint=(inch(85.3), inch(2.125)), height=inch(48.7), plan_symbol="tv-wall",
    mount=Mount(kind=MountKind.WALL), product_ref=TCL_98QM8L.tag,
    parts=(ProductPart(role="fitting", product_ref=MONOPRICE_12994.tag),),
    source=TCL_98QM8L.source + " Mount: Monoprice 12994 at zero tilt.",
)

#: The east wall's first-reflection hanging: woven cotton, landscape, clipped to
#: FT-TAPESTRY-ROD-96. Its glyph is the outline and the viewer paints the face. The body is
#: the fabric alone; the placement's ``normal_gap`` is the air behind it.
DRAGON_TAPESTRY = FurnitureType(
    tag="FT-TAPESTRY-DRAGON-80X60", name='Medieval dragon woven tapestry, 80" x 60"',
    footprint=(inch(80), inch(0.25)), height=inch(60),
    plan_symbol="wall-tapestry", mount=Mount(kind=MountKind.WALL),
    source="owner, 2026-11-01: Etsy listing 4423258589 (Medieval Tapestry, Vintage Dragon "
           "Blanket), 60 x 80 in. size, hung 80 in. wide. Woven cotton throw on clip rings.",
)

HUNT_TAPESTRY = FurnitureType(
    tag="FT-TAPESTRY-HUNT-80X60", name='Medieval mounted hunt woven tapestry, 80" x 60"',
    footprint=(inch(80), inch(0.25)), height=inch(60),
    plan_symbol="wall-tapestry", mount=Mount(kind=MountKind.WALL),
    source="Owner, 2026-11-02: medieval men riding to hunt, woven cotton hanging, "
           "80 in. wide x 60 in. high, with 14 clip rings. Product not selected.",
)

#: Its rod: 96" so the end brackets clear the 80" fabric, a 4" bracket return so the fabric
#: hangs ~3" off the wall. Four-inch hardware envelope includes the 14 clip rings.
TAPESTRY_ROD = FurnitureType(
    tag="FT-TAPESTRY-ROD-96", name='Curtain rod, 96", 1" dia., 4" return, 14 clip rings',
    footprint=(inch(96), inch(4)), height=inch(4),
    model_representation=ModelRepresentation(symbol="tapestry-rod-clips"),
    mount=Mount(kind=MountKind.WALL),
    source="Generic 1 in. black adjustable rod (48-96 in.), three brackets with 4 in. return, "
           "masonry anchors east / stud fasteners west; 14 clip rings at about 6 in. "
           "Retail, not a selected product.",
)

MEDIA_TYPES = (TV_98_PANEL, DRAGON_TAPESTRY, HUNT_TAPESTRY, TAPESTRY_ROD)
MEDIA_PRODUCTS = (TCL_98QM8L, MONOPRICE_12994)
