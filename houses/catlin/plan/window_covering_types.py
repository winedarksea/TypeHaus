"""Window coverings: VIDGA curtain tracks and SmartWings cellular shades.

Placed in plan/window_coverings.py; why and how in notes/window_coverings.md. Each track type
is one run: its envelope is the CLOSED curtain (run x 6" x the drop from a 1/2" floor kiss to
the ceiling, or to the rail top on the wall run), and its model draws the curtains open in
the stacks listed. Stack stations read from the run's local -x end, which with the 180-degree
south-wall rotation is the EAST end, and with the bedroom's 90 degrees the SOUTH end.
"""

from __future__ import annotations

from library.placeables.allowances import CELLULAR_BLIND_2748

from typehaus.model import (
    CurtainStack,
    CurtainTrackSpec,
    FurnitureType,
    Mount,
    MountKind,
    Product,
    inch,
)

VIDGA_RAIL = Product(
    tag="PROD-IKEA-VIDGA-RAIL", brand="IKEA", model="VIDGA single track rail",
    sku="204.929.16", name='VIDGA single track rail, 140 cm / 55", white',
    url="https://ikea.pr/mayaguez/en/pd/vidga-single-track-rail-white-art-20492916",
    source=("IKEA PR listing read 2026-10-29: 140 cm rail with ceiling fittings, connectors "
            "and end caps, $8.99; 11 lb max load. Cut to length. Wall fittings, gliders/hooks, "
            "the end-closing set (s594.282.60) and the corner piece are separate articles; "
            "confirm the US article numbers at order."),
)
SMARTWINGS_CELLULAR_MOTORIZED = Product(
    tag="PROD-SMARTWINGS-CELLULAR-MATTER", brand="SmartWings",
    model="Cellular shade, light filtering, Matter-over-Thread motor",
    name="SmartWings motorized cellular shade, inside mount, rechargeable + solar panel",
    url="https://www.smartwingshome.com/",
    source=("Made to measure. Matter-over-Thread motor (runs locally in Home Assistant through "
            "a Thread border router), rechargeable lithium battery, solar panel option on the "
            "glass side. Reviews read 2026-10-29: cnx-software.com 2025-05-15 (solar, HA), "
            "smarthomescene.com skylight review (Thread, HA). Confirm the motorized minimum "
            "width and the fabric at order."),
)
SMARTWINGS_CELLULAR_CORDLESS = Product(
    tag="PROD-SMARTWINGS-CELLULAR-CORDLESS", brand="SmartWings",
    model="Cellular shade, light filtering, cordless",
    name="SmartWings cordless cellular shade, inside mount",
    url="https://www.smartwingshome.com/",
    source="Made to measure; the motorized line's fabric with a cordless lift. Read 2026-10-29.",
)
WINDOW_COVERING_PRODUCTS = (VIDGA_RAIL, SMARTWINGS_CELLULAR_MOTORIZED,
                            SMARTWINGS_CELLULAR_CORDLESS)

_TRACK_SOURCE = ("IKEA VIDGA single track, white, cut to the run, fittings at <= 140 cm "
                 "(2 minimum); IKEA block-out curtain panels on multi-heading tape at ~1.8-2x "
                 "fullness, hemmed to kiss the floor. See notes/window_coverings.md.")
_CEILING = Mount(kind=MountKind.CEILING)
_WALL = Mount(kind=MountKind.WALL)


def _track(tag: str, name: str, run: float, height: float, mount: Mount,
           stacks: tuple[tuple[float, float], ...],
           fixings: tuple[float, ...] = ()) -> FurnitureType:
    # A wall run's fittings sit at the rail's centre, 3/8" under the envelope top.
    return FurnitureType(
        tag=tag, name=name, footprint=(inch(run), inch(6)), height=inch(height),
        plan_symbol=None, mount=mount, product_ref=VIDGA_RAIL.tag, source=_TRACK_SOURCE,
        wall_fixing_points=tuple((inch(x), inch(height - 0.375)) for x in fixings),
        curtain_track=CurtainTrackSpec(stacks=tuple(
            CurtainStack(start=inch(start), width=inch(width)) for start, width in stacks)),
    )


# Heights: ceiling 107 1/2" datum less the room's finished floor and the 1/2" kiss.
# Living south: x 301" (end-closing curve) to 425 1/4" (the SE corner). Two panels
# anchored mid-pier at x 352"; open, they stack 337-352" and 352-367".
TRACK_LIV_S = _track("FT-CURTAIN-TRACK-LIV-S", 'Ceiling curtain track, living south, 124 1/4"',
                     124.25, 106.0625, _CEILING, ((58.25, 15), (73.25, 15)))
# D-M-BALC: wall run under EQ-M-HP2-LIVING (its bottom 90" AFF), rail top 88" AFF.
# x 219 1/2" (C1 corner) to 291" (end-closing, 1" short of ED-M-PORCH-SW). A split pair.
# Three wall fittings (<= 140 cm apart): the ends on BK-M-S2-ROD and the king packs at x 220"
# and 290 3/4"; the middle over D-M-BALC's header, which stands 1 1/4" behind the stud face,
# so it takes a ripped 2x nailer on the header face (preferences.toml suppress).
TRACK_LIV_BALC = _track("FT-CURTAIN-TRACK-LIV-BALC", 'Wall curtain track, balcony door, 71 1/2"',
                        71.5, 87.5, _WALL, ((0, 7), (64.5, 7)),
                        fixings=(-35.5, 0, 35.25))
# Bedroom west: SW corner to NW corner (y 6 3/4"-153 1/2"); panels anchored mid-pier at
# y 88", stacked in the W1/W2 pier.
TRACK_BED_W = _track("FT-CURTAIN-TRACK-BED-W", 'Ceiling curtain track, main bedroom west, 146 3/4"',
                     146.75, 105.5, _CEILING, ((66.25, 15), (81.25, 15)))
# Study 2, D-S-DECK-E: x 219 1/2" (corner) to 291" (end-closing, 1" clear of
# ED-S-STUDY2-SPOT1). One panel, stacking into the west corner.
TRACK_STUDY_DECK = _track("FT-CURTAIN-TRACK-STUDY-DECK",
                          'Ceiling curtain track, study 2 deck door, 71 1/2"',
                          71.5, 105.5, _CEILING, ((57.5, 14),))


def _shade(tag: str, width: float, drop: float, product: Product) -> FurnitureType:
    kind = "motorized" if product is SMARTWINGS_CELLULAR_MOTORIZED else "cordless"
    return CELLULAR_BLIND_2748.model_copy(update=dict(
        tag=tag, name=f'Cellular shade, {kind}, {width:g} x {drop:g}" opening',
        footprint=(inch(width), inch(2)), height=inch(drop), product_ref=product.tag,
        source=f"{product.name}; inside mount at the reveal's room edge."))


SHADE_3048_MOTOR = _shade("FT-CELLULAR-SHADE-3048-MOTOR", 30, 48, SMARTWINGS_CELLULAR_MOTORIZED)
SHADE_2748_MOTOR = _shade("FT-CELLULAR-SHADE-2748-MOTOR", 27, 48, SMARTWINGS_CELLULAR_MOTORIZED)
SHADE_2754_MOTOR = _shade("FT-CELLULAR-SHADE-2754-MOTOR", 27, 54, SMARTWINGS_CELLULAR_MOTORIZED)
SHADE_3048_CORDLESS = _shade("FT-CELLULAR-SHADE-3048-CORDLESS", 30, 48,
                             SMARTWINGS_CELLULAR_CORDLESS)
# WIN-A-S3's 14" is likely under the motorized minimum width.
SHADE_1424_CORDLESS = _shade("FT-CELLULAR-SHADE-1424-CORDLESS", 14, 24,
                             SMARTWINGS_CELLULAR_CORDLESS)

WINDOW_COVERING_TYPES = (TRACK_LIV_S, TRACK_LIV_BALC, TRACK_BED_W, TRACK_STUDY_DECK,
                         SHADE_3048_MOTOR, SHADE_2748_MOTOR, SHADE_2754_MOTOR,
                         SHADE_3048_CORDLESS, SHADE_1424_CORDLESS)
