"""RM-M-CLOSET's fit-out catalog: two PAX frames, BESTA drawers, the custom bay, pegs, mirror.

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
BESTA_FRAME = Product(
    tag="PROD-IKEA-BESTA-38", brand="IKEA", model="BESTA frame 60x40x38",
    name='BESTA frame, white, 23 5/8 x 15 3/4 x 15"', sku="702.458.48",
    url="https://www.ikea.com/us/en/p/besta-frame-white-70245848/",
    source="IKEA US listing, read 2026-10-01. Two BESTA drawer frames (703.515.13, 5 7/8\" "
           "each) per carcass, with fronts and legs bought to taste.",
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

CLOSET_PRODUCTS = (PAX_WALL_FRAME, BESTA_FRAME, OVERSIDAN, TRADFRI_30)

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
    plan_symbol=None, mount=_WALL,
    source="Painted poplar or white melamine, top flush with the PAX frames' top line.",
)
CLOSET_PLINTH = FurnitureType(
    tag="FT-M-CLOSET-PLINTH", name='Custom bay bottom: white shoe deck, 3" fascia',
    footprint=(inch(32), inch(22.875)), height=inch(3),
    storage=True, work_surface=False, plan_symbol=None, mount=_WALL,
    source="As the valance; the bottom board on the PAX bottom line, a deck for shoes.",
)

# --- west wall: BESTA drawers -------------------------------------------------------------

BESTA_DRAWER = FurnitureType(
    tag="FURN-M-BESTA-DRAWER",
    name='BESTA 23 5/8 x 15 3/4 x 15" frame, two drawers, fronts, on 4 3/4" legs',
    footprint=(inch(23.625), inch(16.5)), height=inch(19.75),
    storage=True, work_surface=False, plan_symbol="nightstand",
    product_ref="PROD-IKEA-BESTA-38",
    source=("15 3/4\" frame plus ~3/4\" fronts. On legs, so the top stays at ~20\" and under "
            "the lower rod's short hang. Strapped to W-M-BA2E2 against tipping."),
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
                          BESTA_DRAWER, PEG_RAIL_42)

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
