"""Study 2 window seat under ST-S2A: three SEKTION top frames and an 18" open high frame.

All stand on a 3 1/2" 2x4 base, not on IKEA legs. IKEA sells
no MAXIMERA drawer for the 24x24x15 top frame, so each seat unit opens with a lift-up
front, as IKEA configures it. Configured material prices live in prices.toml.
"""

from __future__ import annotations

from typehaus.library.placeables._zones import front_zone
from typehaus.model import FurnitureType, Product, inch

SEKTION_TOP_FRAME_24_15 = Product(
    tag="PROD-IKEA-SEKTION-TOP-24-24-15", brand="IKEA", model="SEKTION 24x24x15 top",
    sku="904.997.35", name='SEKTION white top cabinet with ventilation, 24 x 24 x 15"',
    url="https://www.ikea.com/us/en/p/sektion-top-cabinet-with-ventilation-white-90499735/",
    source=("IKEA US listing, read 2026-10-02: $88; 23 5/8\" without rail, 24\" with rail; "
            "15\" frame, 3/4\" panels, vent cut-outs in top and bottom panels. IKEA's "
            "configuration pairs it with a 24x15 front on UTRUSTA 804.654.15 horizontal "
            "hinges ($52/2-pack)."),
)
SEKTION_HIGH_FRAME_18_80 = Product(
    tag="PROD-IKEA-SEKTION-HIGH-18-24-80", brand="IKEA", model="SEKTION 18x24x80",
    sku="002.654.44", name='SEKTION white high cabinet frame, 18 x 24 x 80"',
    url="https://www.ikea.com/us/en/p/sektion-high-cabinet-white-00265444/",
    source=("IKEA US listing, read 2026-10-02: $152; 23 5/8\" without rail, 24\" with rail; "
            "80\" frame, 3/4\" panels, one reinforced adjustable shelf."),
)
FORBATTRA_MATTE_WHITE_80 = Product(
    tag="PROD-IKEA-FORBATTRA-MATTE-25-80", brand="IKEA", model="FÖRBÄTTRA matte white 25x80",
    sku="205.678.36", name='FÖRBÄTTRA matte white cover panel, 25 x 80"',
    url="https://www.ikea.com/us/en/p/foerbaettra-cover-panel-matte-white-20567836/",
    source='IKEA US listing, read 2026-10-02: $127; 24 5/8" x 80", 1/2" thick.',
)
FORBATTRA_MATTE_WHITE_30 = Product(
    tag="PROD-IKEA-FORBATTRA-MATTE-25-30", brand="IKEA", model="FÖRBÄTTRA matte white 25x30",
    sku="405.678.35", name='FÖRBÄTTRA matte white cover panel, 25 x 30"',
    url="https://www.ikea.com/us/en/p/foerbaettra-cover-panel-matte-white-40567835/",
    source='IKEA US listing, read 2026-10-02: $53; 24 5/8" x 30", 1/2" thick, site-cuttable.',
)
STUDY_NOOK_PRODUCTS = (SEKTION_TOP_FRAME_24_15, SEKTION_HIGH_FRAME_18_80,
                       FORBATTRA_MATTE_WHITE_80, FORBATTRA_MATTE_WHITE_30)

_BASE = "3 1/2\" 2x4 base with a baseboard-matching kick."

STUDY_NOOK_SEAT = FurnitureType(
    tag="FURN-S-STUDY-NOOK-SEAT-24", name='SEKTION 24x24x15 seat unit, lift-up front, 19 1/2" top',
    footprint=(inch(24), inch(24.875)), height=inch(19.5), carcass_depth=inch(24),
    storage=True, work_surface=False, plan_symbol="sektion-seat-base",
    product_ref=SEKTION_TOP_FRAME_24_15.tag,
    clearances=(front_zone(inch(24), inch(24.875), inch(15), "VOXTORP lift-up front swing"),),
    source=("SEKTION 904.997.35 frame; one VOXTORP 24x15 matte white 602.733.42 front on "
            "UTRUSTA 804.654.15 horizontal hinges. " + _BASE + " One continuous 1\" white "
            "top runs over the whole run, flush with the fronts; the cushion must not "
            "overhang them or the fronts cannot lift. No drawer: IKEA offers no MAXIMERA "
            "for this frame."),
)
STUDY_NOOK_SHELF = FurnitureType(
    tag="FURN-S-STUDY-NOOK-SHELF-18", name='SEKTION 18x24x80 open shelves, 83 1/2" installed',
    footprint=(inch(18), inch(24)), height=inch(83.5), carcass_depth=inch(24),
    storage=True, work_surface=False, plan_symbol="sektion-open-high",
    product_ref=SEKTION_HIGH_FRAME_18_80.tag,
    source=("SEKTION 002.654.44, no fronts, adjustable shelves facing the room. " + _BASE
            + " Screens the seat from traffic through D-S-STUDY2; rail-anchored to W-S-SS2."),
)
STUDY_NOOK_COVER = FurnitureType(
    tag="FT-S-STUDY-NOOK-COVER-80", name='FÖRBÄTTRA matte white cover, 1/2 x 24 5/8 x 80"',
    footprint=(inch(0.5), inch(24.625)), height=inch(80), plan_symbol="sektion-cover-panel",
    product_ref=FORBATTRA_MATTE_WHITE_80.tag,
    source="West face of the shelf frame, toward the door. Starts on the base.",
)
STUDY_NOOK_SEAT_END = FurnitureType(
    tag="FT-S-STUDY-NOOK-SEAT-END", name='FÖRBÄTTRA matte white seat end, 1/2 x 24 5/8 x 16"',
    footprint=(inch(0.5), inch(24.625)), height=inch(16), plan_symbol="sektion-cover-panel",
    product_ref=FORBATTRA_MATTE_WHITE_30.tag,
    source="Site-cut from a 25x30 panel; covers the east seat frame and the top's end grain.",
)
# The FT-STUDY-BENCH spec: 3" HR foam settles ~1 1/2" under an adult, so the 19 1/2" top
# seats you at ~21" and lies at 22 1/2". Held 1/2" back so the lift-up fronts clear it.
STUDY_NOOK_CUSHION = FurnitureType(
    tag="FT-S-STUDY-NOOK-CUSHION", name='Window-seat cushion, 72 x 24 3/8 x 3"',
    footprint=(inch(72), inch(24.375)), height=inch(3), plan_symbol="seat-cushion",
    storage=False, work_surface=False,
    source=("Custom one-piece cushion: 3\" HR foam (2.5 lb/ft3, ILD ~35) in a zippered, "
            "welted performance-fabric cover, non-slip base. Back on the wall, front 1/2\" "
            "behind the VOXTORP faces; runs from the shelf frame to the east end."),
)
STUDY_NOOK_TYPES = (STUDY_NOOK_SEAT, STUDY_NOOK_SHELF, STUDY_NOOK_COVER, STUDY_NOOK_SEAT_END,
                    STUDY_NOOK_CUSHION)
