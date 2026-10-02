"""RM-M-CLOSET's fit-out catalog: two PAX frames, SEKTION drawers, the custom bay, pegs, mirror.

House-local because each row is a CONFIGURATION fitted to this closet (a PAX frame with a
stated interior, a rod cut to a 32" bay), not a bare product. The products themselves are
the ``PROD-IKEA-*`` records below. The placements are in plan/closet.py.

IKEA US listings read 2026-10-01; numbers are what the pages printed that day.
"""

from __future__ import annotations

from typehaus.model import (
    ElectricalDeviceType,
    FurnitureType,
    LuminaireForm,
    LuminaireType,
    Mount,
    MountKind,
    Product,
    Service,
    ServicePort,
    ft,
    inch,
)

_WALL = Mount(kind=MountKind.WALL)
_POWER_120 = (ServicePort(tag="power", service=Service.POWER_120,
                          position=(ft(0), ft(0), ft(0))),)

# --- products ---------------------------------------------------------------------------

PAX_WALL_FRAME = Product(
    tag="PROD-IKEA-PAX-WALL", brand="IKEA", model="PAX wall-mounted storage frame",
    name='PAX wall-mounted storage frame, white, 39 3/8 x 22 7/8 x 92 7/8"', sku="705.881.67",
    url="https://www.ikea.com/us/en/p/pax-wall-mounted-storage-frame-white-70588167/",
    source="IKEA US listing, read 2026-10-01: hangs on an included wall rail with no floor "
           "contact; 93 1/8\" overall; needs 93 1/4\" ceiling to stand up. Interiors are "
           "KOMPLEMENT.",
)
SEKTION_MAXIMERA_24_DRAWER = Product(
    tag="PROD-IKEA-SEKTION-MAXIMERA-24-3D", brand="IKEA",
    model="SEKTION / MAXIMERA 24x15x30, 3 drawers",
    name="SEKTION / MAXIMERA base cabinet with 3 drawers, white/Aspudden matte white",
    sku="296.240.12",
    url=("https://www.ikea.com/us/en/p/sektion-maximera-base-cabinet-with-3-drawers-"
         "white-aspudden-matte-white-s29624012/"),
    source=("IKEA US listing, read 2026-10-01: 24\" W x 15\" system depth (15 1/2\" overall) "
            "x 30\" frame, three MAXIMERA drawers with ASPUDDEN fronts. The four 4 1/2\" "
            "legs, suspension rail and handles are separate; the linked set was listed at "
            "$367.00."),
)
OVERSIDAN = Product(
    tag="PROD-IKEA-OVERSIDAN", brand="IKEA", model="OVERSIDAN",
    name="OVERSIDAN LED wardrobe lighting strip with sensor, dimmable white",
    url="https://www.ikea.com/us/en/p/oeversidan-led-wardrobe-lighting-strp-w-sensor-dimmable-white-60475019/",
    source="IKEA US listing, read 2026-10-01: 28\" is 3.5 W / 270 lm; the 38\" fits a 39 3/8\" "
           "frame. The door sensor does nothing on an open frame, so the closet switch "
           "is the control.",
)
TRADFRI_30 = Product(
    tag="PROD-IKEA-TRADFRI-30", brand="IKEA", model="TRADFRI driver 30 W", sku="603.426.61",
    name="TRADFRI driver for wireless control, 30 W, with ANSLUTA power supply cord",
    source="IKEA wardrobe lighting guide, read 2026-10-01: up to 9 light sources, 30 W; "
           "plugs into an ordinary receptacle through the ANSLUTA cord (sold separately).",
)

CLOSET_PRODUCTS = (PAX_WALL_FRAME, SEKTION_MAXIMERA_24_DRAWER, OVERSIDAN, TRADFRI_30)

# --- north wall: two PAX frames and the custom bay ---------------------------------------
#
# Open frames, no doors (owner, 2026-10-01): the aisle in front is ~31", and an east door
# would swing over the mirror.

_PAX_SOURCE = ("PAX wall-mounted frame on its rail, open, with KOMPLEMENT interior. "
               "Hung 1/4\" off the carpet, so nothing bears on the pad.")
PAX_SHOW = FurnitureType(
    tag="FURN-M-PAX-SHOW",
    name='PAX 39 3/8" open frame: drawers below (some glass-front for show), tall shelves above',
    footprint=(inch(39.375), inch(22.875)), height=inch(92.875),
    storage=True, work_surface=False, plan_symbol="wardrobe-show",
    product_ref="PROD-IKEA-PAX-WALL", source=_PAX_SOURCE,
)
PAX_HANG = FurnitureType(
    tag="FURN-M-PAX-HANG",
    name='PAX 39 3/8" open frame: one low drawer, dress-length rail, two shelves on top',
    footprint=(inch(39.375), inch(22.875)), height=inch(92.875),
    storage=True, work_surface=False, plan_symbol="wardrobe-hang",
    product_ref="PROD-IKEA-PAX-WALL", source=_PAX_SOURCE,
)
# The custom bay: two rods cut to the 32" between the west wall and the central frame's
# side panel, and a board top and bottom on the PAX lines so the wall reads as one piece.
CLOSET_ROD_32 = FurnitureType(
    tag="FT-M-CLOSET-ROD-32", name='Closet rod, 1 5/16" round, 32" cut, end sockets',
    footprint=(inch(1.3125), inch(32)), height=inch(1.3125),
    storage=True, work_surface=False, plan_symbol=None, mount=_WALL,
    source=("Steel or oak rod in flange sockets: the west end screws to W-M-BA2E2, the east "
            "end to the central PAX's side panel. Footprint DEPTH is the run off the wall."),
)
CLOSET_VALANCE = FurnitureType(
    tag="FT-M-CLOSET-VALANCE", name='Custom bay top: white cap board with 3" fascia',
    footprint=(inch(32), inch(22.875)), height=inch(3),
    plan_symbol="closet-board", mount=_WALL,
    source="Painted poplar or white melamine, top flush with the PAX frames' top line.",
)
CLOSET_PLINTH = FurnitureType(
    tag="FT-M-CLOSET-PLINTH", name='Custom bay bottom: white shoe deck, 3" fascia',
    footprint=(inch(32), inch(22.875)), height=inch(3),
    storage=True, work_surface=False, plan_symbol="closet-board", mount=_WALL,
    source="As the valance; the bottom board on the PAX bottom line, a deck for shoes.",
)

# --- west wall: SEKTION drawers ----------------------------------------------------------

SEKTION_DRAWER_24 = FurnitureType(
    tag="FURN-M-SEKTION-24-DRAWER",
    name='SEKTION 24 x 15 x 30" frame, three drawers, four legs, 36" nominal with slab',
    footprint=(inch(24), inch(16.5)), height=inch(35.681),
    carcass_depth=inch(15.5), storage=True, work_surface=True,
    plan_symbol="sektion-drawer-base",
    product_ref="PROD-IKEA-SEKTION-MAXIMERA-24-3D",
    source=("Two 24\" units make a 48\" run. IKEA lists 15\" system depth and 15 1/2\" "
            "overall cabinet depth. The 30\" frame, 4 1/2\" legs and 3 cm slab total "
            "35 11/16\" (36\" nominal). The slab projects 1\" beyond the drawer fronts. "
            "Anchor through the SEKTION rail into W-M-BA2E2's 32\"..39 1/4\" backing band; "
            "the unselected toe plinth is not modeled, so the four legs remain exposed."),
)

# --- south wall: robe pegs ----------------------------------------------------------------

PEG_RAIL_42 = FurnitureType(
    tag="FT-M-PEG-RAIL-42", name='Solid oak peg rail, 42", six knobs',
    footprint=(inch(42), inch(4)), height=inch(3.5),
    plan_symbol="peg-rail", mount=_WALL,
    source=("42\" solid-oak backplate with six rounded, projecting oak knobs, inspired by the "
            "linked IKEA HÖVOLM rack. Screwed through into BK-M-BDN2-PEGS."),
)

CLOSET_FURNITURE_TYPES = (PAX_SHOW, PAX_HANG, CLOSET_ROD_32, CLOSET_VALANCE, CLOSET_PLINTH,
                          SEKTION_DRAWER_24, PEG_RAIL_42)

# --- lighting: the lit mirror, the PAX strips and their driver ---------------------------

CLOSET_LUMINAIRE_TYPES = (
    LuminaireType(tag="ED-T-LT-MIRROR-CLOSET",
                  name='24" x 60" front-lit full-length LED mirror, hardwired',
                  form=LuminaireForm.MIRROR_LIGHT, type_mark="P2",
                  footprint=(inch(24), inch(1.5)), height=inch(60),
                  plan_symbol="mirror-light",
                  lamp="LED integrated, front-lit perimeter band", watts=36.0,
                  lumens=2400.0, cct_k=3000, cri=90, dimmable=True, integral_switch=True,
                  load_va=40.0, ports=_POWER_120,
                  source="Allowance: no SKU chosen. Hardwired so no cord shows; its own "
                         "touch switch, so it names no wall switch."),
    LuminaireType(tag="ED-T-LT-PAX-STRIP", name='IKEA OVERSIDAN 38" wardrobe LED strip',
                  form=LuminaireForm.STRIP, type_mark="E2",
                  footprint=(inch(0.5), inch(0.5)), height=inch(0.5),
                  lamp="LED strip, IKEA low-voltage", watts_per_ft=1.5, lumens=116.0,
                  cct_k=2700, voltage=24, dimmable=True,
                  product_ref="PROD-IKEA-OVERSIDAN",
                  source="1.5 W/ft and 116 lm/ft from the 28\" listing (3.5 W, 270 lm)."),
)
CLOSET_SUPPLY_TYPES = (
    ElectricalDeviceType(tag="ED-T-LT-PSU-TRADFRI-30",
                         name="IKEA TRADFRI 30 W LED driver, plug-in",
                         footprint=(inch(7.25), inch(2.5)), height=inch(1.25),
                         load_va=30.0, ports=_POWER_120,
                         product_ref="PROD-IKEA-TRADFRI-30",
                         source="Sits on top of the PAX; ANSLUTA cord to ED-M-CLOSET-RC1."),
)
