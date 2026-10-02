"""Hall-bath SEKTION: two open lower bays beside the WC, one full drawer stack.

The 90-inch frames stand on 4½-inch legs. VOXTORP adds ⅞ inch to the 24-inch rail/frame
envelope. Product records carry identity; configured material prices live in prices.toml.
"""

from __future__ import annotations

from typehaus.library.placeables._zones import front_zone
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
BATH1_STORAGE_PRODUCTS = (SEKTION_HIGH_FRAME_24, FORBATTRA_MATTE_WHITE_90)

_WIDTH = inch(24)
_DEPTH = inch(24.875)
_HEIGHT = inch(94.5)
_SOURCE = ("SEKTION 702.654.45; 4 1/2\" legs and white plinth. Upper VOXTORP doors "
           "24x30 (102.733.30) + 24x20 (302.733.29), both right-hinged; shelf divider "
           "at frame 40\", adjustable shelves at 55/70/80\". Rail offset is included "
           "in the 24\" mounting envelope, not an additional wall gap.")

SEKTION_OPEN_LOWER = FurnitureType(
    tag="FURN-S-SEKTION-LINEN-OPEN-24", name='SEKTION 24x24x90: open lower 30", one drawer, upper doors',
    footprint=(_WIDTH, _DEPTH), height=_HEIGHT, carcass_depth=inch(24),
    storage=True, work_surface=False, plan_symbol="sektion-tall-open-lower",
    product_ref=SEKTION_HIGH_FRAME_24.tag,
    source=(_SOURCE + " Owner, 2026-10-02: bottom two drawer positions remain OPEN, "
            "with shelves at frame 15/30\", because the unchanged toilet blocks their "
            "sweeps. One medium MAXIMERA 802.656.66 with a 24x10 VOXTORP 802.733.41 "
            "front starts at 34 1/2\" AFF, above the toilet's 29 1/8\" top. The model's "
            "clearance zones have no per-zone height, so its sweep is checked in 3D "
            "rather than reporting a false floor-level toilet conflict."),
)
SEKTION_DRAWER_LOWER = FurnitureType(
    tag="FURN-S-SEKTION-LINEN-DRAWER-24", name='SEKTION 24x24x90: three lower drawers, upper doors',
    footprint=(_WIDTH, _DEPTH), height=_HEIGHT, carcass_depth=inch(24),
    storage=True, work_surface=False, plan_symbol="sektion-tall-drawers",
    product_ref=SEKTION_HIGH_FRAME_24.tag,
    clearances=(front_zone(_WIDTH, _DEPTH, inch(21.375), "MAXIMERA full-extension drawer"),),
    source=(_SOURCE + " Two high MAXIMERA 102.656.79 with 24x15 VOXTORP 602.733.42 "
            "fronts below one medium 802.656.66 / 24x10 front. Bottom-to-top fronts "
            "15+15+10\"; drawers stand east of the toilet's footprint."),
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
    source="Site-cut white filler, caulked to the west wall; ends on the cabinet top and bottom.",
)
BATH1_STORAGE_TYPES = (SEKTION_OPEN_LOWER, SEKTION_DRAWER_LOWER, SEKTION_END_PANEL,
                       SEKTION_WEST_SCRIBE)
