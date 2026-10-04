"""RM-M-CLOSET's fit-out catalog: two PAX frames, the extended wire corner, the mirror.

House-local because each row is a CONFIGURATION fitted to this closet (a PAX frame with a
stated interior, a wire shelf cut to the corner), not a bare product. The products themselves are
the ``PROD-IKEA-*`` records below. The placements are in plan/closet.py.

IKEA US listings read 2026-10-01; numbers are what the pages printed that day.
"""

from __future__ import annotations

from typehaus.model import (
    ElectricalDeviceType,
    Footprint2D,
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
    m,
    pt,
)
from typehaus.model.placeable_symbols.furniture import wardrobe_corner_points

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
PAX_WALL_FRAME_20 = Product(
    tag="PROD-IKEA-PAX-WALL-20", brand="IKEA", model="PAX wall-mounted storage frame",
    name='PAX wall-mounted storage frame, white, 19 5/8 x 22 7/8 x 92 7/8"', sku="405.881.59",
    url="https://www.ikea.com/us/en/p/pax-wall-mounted-storage-frame-white-40588159/",
    source="IKEA US listing, read 2026-10-02: $170.00; the 39 3/8\" frame's rail and "
           "adjustable feet. Two side by side are 39 1/4\".",
)
PAX_WALL_FRAME_30 = Product(
    tag="PROD-IKEA-PAX-WALL-30", brand="IKEA", model="PAX wall-mounted storage frame",
    name='PAX wall-mounted storage frame, white, 29 1/2 x 22 7/8 x 92 7/8"', sku="605.890.06",
    source="IKEA US listing, read 2026-10-03: $180.00; the same rail and feet as the 39 3/8\".",
)
SUPERSLIDE_SHELF = Product(
    tag="PROD-CLOSETMAID-SUPERSLIDE-12-NI", brand="ClosetMaid", model="SuperSlide",
    name='SuperSlide ventilated wire shelf, 12" deep, nickel',
    url="https://homedepot.closetmaid.com/en-US/Installation/Pages/how-to-guides.aspx",
    source="ClosetMaid installation guide, read 2026-10-04: cut shelving with bolt cutters "
           "or a hacksaw. Separate SuperSlide rod and supports underneath; cap cut wires. "
           "Stock length and shelf SKU to confirm at purchase.",
)
SUPERSLIDE_CORNER_BAR = Product(
    tag="PROD-CLOSETMAID-56333-NI", brand="ClosetMaid", model="56333",
    name='SuperSlide corner bar, 10 1/4 x 10 1/4", nickel',
    source="Joins two SuperSlide rods round an inside corner. The west rod continues to "
           "the south wall; support each corner-bar connection with a closet rod support.",
)
OVERSIDAN = Product(
    tag="PROD-IKEA-OVERSIDAN", brand="IKEA", model="OVERSIDAN",
    name="OVERSIDAN LED wardrobe lighting strip with sensor, dimmable white",
    url="https://www.ikea.com/us/en/p/oeversidan-led-wardrobe-lighting-strp-w-sensor-dimmable-white-60475019/",
    source="IKEA US listing, read 2026-10-01: 28\" is 3.5 W / 270 lm; the 38\" fits a 39 3/8\" "
           "frame and the 18\" a 19 5/8\" one. The door sensor does nothing on an open "
           "frame, so the closet switch is the control.",
)
TRADFRI_30 = Product(
    tag="PROD-IKEA-TRADFRI-30", brand="IKEA", model="TRADFRI driver 30 W", sku="603.426.61",
    name="TRADFRI driver for wireless control, 30 W, with ANSLUTA power supply cord",
    source="IKEA wardrobe lighting guide, read 2026-10-01: up to 9 light sources, 30 W; "
           "plugs into an ordinary receptacle through the ANSLUTA cord (sold separately).",
)

# PAX_WALL_FRAME_20 is the bedroom wardrobes' (plan/bedroom_wardrobe_types.py).
CLOSET_PRODUCTS = (PAX_WALL_FRAME, PAX_WALL_FRAME_20, PAX_WALL_FRAME_30, SUPERSLIDE_SHELF,
                   SUPERSLIDE_CORNER_BAR, OVERSIDAN, TRADFRI_30)

# --- PAX frames: two on the north wall; retired west type stays priced ------------------
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
# The east 39 3/8" slot (owner, 2026-10-03; two 19 5/8" frames since 2026-10-02): SHOW's
# drawers under one long rail. Interiors: model/placeable_symbols/_wardrobe.py.
PAX_SHOW_HANG = FurnitureType(
    tag="FURN-M-PAX-SHOW-HANG",
    name='PAX 39 3/8" open frame: the display drawers below, one long rail above (~40" hang)',
    footprint=(inch(39.375), inch(22.875)), height=inch(92.875),
    storage=True, work_surface=False, plan_symbol="wardrobe-show-hang",
    product_ref="PROD-IKEA-PAX-WALL", source=_PAX_SOURCE,
)
PAX_DOUBLE_30 = FurnitureType(
    tag="FURN-M-PAX-DOUBLE-30",
    name='PAX 29 1/2" open frame: two rails on the closet\'s 79"/39" lines, one shelf on top',
    footprint=(inch(29.5), inch(22.875)), height=inch(92.875),
    storage=True, work_surface=False, plan_symbol="wardrobe-double-hang",
    product_ref="PROD-IKEA-PAX-WALL-30", source=_PAX_SOURCE,
)

# --- the north-west corner: SuperSlide wire, two tiers ----------------------------------
#
# An L of 12" shelf per tier: 32" along the north wall, 24 3/4"
# down the west, continued by a 29 1/2" straight section. The 56333 bar rounds the inner
# corner. Both shelf types share the same representative shelf/rod height envelope.
_WIRE_W, _WIRE_D, _WIRE_LEG = inch(32), inch(24.75), inch(12)
_wire_ring = wardrobe_corner_points(_WIRE_W.meters, _WIRE_D.meters, _WIRE_LEG.meters)
CLOSET_CORNER_WIRE = FurnitureType(
    tag="FT-M-CLOSET-CORNER-WIRE",
    name='SuperSlide wire corner, nickel: 12" shelf and rod, 32" x 24 3/4" L',
    footprint=(_WIRE_W, _WIRE_D), height=inch(1.5),
    footprint_shape=Footprint2D(points=tuple(pt(m(x), m(y)) for x, y in _wire_ring)),
    storage=True, work_surface=False, plan_symbol="closet-corner-wire", mount=_WALL,
    product_ref="PROD-CLOSETMAID-SUPERSLIDE-12-NI",
    source=("Per tier: SuperSlide shelves and separate rods cut to each leg, north end "
            "supported at the PAX side, west end joined to the straight extension. Back "
            "clips into W-M-CLN and W-M-BA2E2, front brackets and one 56333 corner bar. "
            "See notes/closet_wire.md for supported joints and field-cut allowances."),
)

CLOSET_WEST_WIRE = FurnitureType(
    tag="FT-M-CLOSET-WEST-WIRE",
    name='SuperSlide wire extension, nickel: 12" shelf with rod beneath, 29 1/2" run',
    footprint=(inch(29.5), inch(12)), height=inch(1.5),
    storage=True, work_surface=False, plan_symbol="closet-wire", mount=_WALL,
    product_ref="PROD-CLOSETMAID-SUPERSLIDE-12-NI",
    source=("Two tiers continue the corner's west leg at identical elevations. Cut stock "
            "shelving and a fixed SuperSlide rod to fit; supported shelf joiner and rod "
            "connector at the seam, back clips and front brackets into wall backing, "
            "south side-wall end bracket. See notes/closet_wire.md."),
)

CLOSET_FURNITURE_TYPES = (PAX_SHOW, PAX_SHOW_HANG, PAX_DOUBLE_30, CLOSET_CORNER_WIRE,
                        CLOSET_WEST_WIRE)

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
    LuminaireType(tag="ED-T-LT-PAX-STRIP", name="IKEA OVERSIDAN wardrobe LED strip",
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
