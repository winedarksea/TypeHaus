"""Hall-bath SEKTION: two open lower bays beside the WC, one full drawer stack.

The 90-inch frames stand on 4½-inch legs. VOXTORP adds ⅞ inch to the 24-inch rail/frame
envelope. Product records carry identity; configured material prices live in prices.toml.
"""

from __future__ import annotations

from plan.sektion_hardware import VOXTORP_HARDWARE
from typehaus.library.placeables._zones import front_zone
from typehaus.library.placeables.sektion_parts import FrontLayout, FrontRow, sektion_parts
from typehaus.model import FurnitureType, Product, inch

SEKTION_HIGH_FRAME_24 = Product(
    tag="PROD-IKEA-SEKTION-HIGH-24-24-90", brand="IKEA", model="SEKTION 24x24x90",
    sku="702.654.45", name='SEKTION white high cabinet frame, 24 x 24 x 90"',
    url="https://www.ikea.com/us/en/p/sektion-high-cabinet-white-70265445/",
    source=("IKEA US listing, read 2026-10-02: 23 5/8\" without rail, 24\" with rail; "
            "90\" frame, 3/4\" panels, one reinforced adjustable shelf. Configured with "
            "PROD-IKEA-VOXTORP-WH fronts and PROD-IKEA-MAXIMERA drawers; legs and rail "
            "are additional components, included in the configured price rows."),
)
FORBATTRA_MATTE_WHITE_90 = Product(
    tag="PROD-IKEA-FORBATTRA-MATTE-25-90", brand="IKEA", model="FÖRBÄTTRA matte white 25x90",
    sku="005.678.37", name='FÖRBÄTTRA matte white cover panel, 25 x 90"',
    url="https://www.ikea.com/us/en/p/foerbaettra-cover-panel-matte-white-00567837/",
    source='IKEA US listing, read 2026-10-02: actual depth 24 5/8", thickness 1/2", height 90".',
)
SEKTION_HIGH_FRAME_18 = Product(
    tag="PROD-IKEA-SEKTION-HIGH-18-24-90", brand="IKEA", model="SEKTION 18x24x90",
    sku="002.654.39", name='SEKTION white high cabinet frame, 18 x 24 x 90"',
    url="https://www.ikea.com/us/en/p/sektion-high-cabinet-white-00265439/",
    source='IKEA US listing, read 2026-10-21: 18" wide, 23 5/8" without rail, '
           '24" with rail, 90" frame. Legs, rail, shelves, fronts and drawers are additional.',
)
BATH1_STORAGE_PRODUCTS = (SEKTION_HIGH_FRAME_24, SEKTION_HIGH_FRAME_18,
                         FORBATTRA_MATTE_WHITE_90)

_WIDTH = inch(24)
_DEPTH = inch(24.875)
_HEIGHT = inch(94.5)
_SOURCE = ("4 1/2\" legs and white plinth. Upper VOXTORP doors hinged at east edges; shelf divider "
           "at frame 40\", adjustable shelves at 55/70/80\". Rail offset is included "
           "in the 24\" mounting envelope, not an additional wall gap.")

# Fronts bottom to top. Shelves: open lower at 15/30" plus 55/70/80" above the fixed one (5);
# the drawer unit keeps only the upper three.
_OPEN_LOWER_LAYOUT = FrontLayout(90, (FrontRow("open", 30), FrontRow("drawer", 10),
                                      FrontRow("door", 30), FrontRow("door", 20)))
_DRAWER_LOWER_LAYOUT = FrontLayout(90, (FrontRow("drawer", 15), FrontRow("drawer", 15),
                                        FrontRow("drawer", 10), FrontRow("door", 30),
                                        FrontRow("door", 20)))

SEKTION_OPEN_LOWER = FurnitureType(
    tag="FURN-S-SEKTION-LINEN-OPEN-24",
    name='SEKTION 24x24x90: open lower 30", one drawer, upper doors',
    footprint=(_WIDTH, _DEPTH), height=_HEIGHT, carcass_depth=inch(24),
    storage=True, work_surface=False, plan_symbol="sektion-tall-open-lower",
    product_ref=SEKTION_HIGH_FRAME_24.tag,
    parts=sektion_parts(24, 24, _OPEN_LOWER_LAYOUT, "legs", VOXTORP_HARDWARE, shelves=5),
    source=(_SOURCE + " SEKTION 702.654.45; upper doors 24x30 (102.733.30) + "
            "24x20 (302.733.29). Owner, 2026-10-02: bottom two drawer positions remain OPEN, "
            "with shelves at frame 15/30\", because the unchanged toilet blocks their "
            "sweeps. One medium MAXIMERA 802.656.66 with a 24x10 VOXTORP 802.733.41 "
            "front starts at 34 1/2\" AFF, above the toilet's 29 1/8\" top. The model's "
            "clearance zones have no per-zone height, so its sweep is checked in 3D "
            "rather than reporting a false floor-level toilet conflict."),
)
SEKTION_DRAWER_LOWER_18 = FurnitureType(
    tag="FURN-S-SEKTION-LINEN-DRAWER-18", name='SEKTION 18x24x90: three lower drawers, upper doors',
    footprint=(inch(18), _DEPTH), height=_HEIGHT, carcass_depth=inch(24),
    storage=True, work_surface=False, plan_symbol="sektion-tall-drawers",
    product_ref=SEKTION_HIGH_FRAME_18.tag,
    parts=sektion_parts(18, 24, _DRAWER_LOWER_LAYOUT, "legs", VOXTORP_HARDWARE, shelves=3),
    clearances=(front_zone(inch(18), _DEPTH, inch(21.375), "MAXIMERA full-extension drawer"),),
    source=(_SOURCE + " Owner, 2026-10-21: SEKTION 002.654.39; upper doors 18x30 "
            "(802.733.22) + 18x20 (002.733.21). Two high MAXIMERA 502.656.82 with "
            "18x15 VOXTORP 202.733.20 fronts below one medium 002.656.65 / "
            "18x10 front 402.733.38. Bottom-to-top fronts 15+15+10\"; drawers stand "
            "east of the toilet's footprint. IKEA US listings checked 2026-10-21."),
)
SEKTION_END_PANEL = FurnitureType(
    tag="FT-S-SEKTION-COVER-90", name='FÖRBÄTTRA matte white end cover, 1/2 x 24 5/8 x 90"',
    footprint=(inch(0.5), inch(24.625)), height=inch(90), plan_symbol="sektion-cover-panel",
    product_ref=FORBATTRA_MATTE_WHITE_90.tag,
    source='Starts above the plinth, front flush with VOXTORP; rear 1/4" gap is sealed to wall.',
)
SEKTION_WEST_SCRIBE = FurnitureType(
    tag="FT-S-SEKTION-SCRIBE-90", name='White west scribe, 3/8 x 24 7/8 x 90"',
    footprint=(inch(0.375), _DEPTH), height=inch(90), plan_symbol="sektion-cover-panel",
    source=("Site-cut white filler, caulked to the west wall; ends on the cabinet top and bottom. "
            "24 7/8 deep, past FÖRBÄTTRA's 24 5/8, so shop stock rather than an IKEA panel."),
)
BATH1_STORAGE_TYPES = (SEKTION_OPEN_LOWER, SEKTION_DRAWER_LOWER_18, SEKTION_END_PANEL,
                       SEKTION_WEST_SCRIBE)
