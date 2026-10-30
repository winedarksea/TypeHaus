"""Catlin's AXSTAD/BAGGANÄS configuration over the finish-neutral SEKTION ladder.

The same B24 frame is drawers in the peninsula and doors in the living room. Fronts and
support heights are house configurations; the shared cabinet frames stay unchanged.
"""

from plan.sektion_hardware import AXSTAD_HARDWARE
from typehaus import inch
from typehaus.library.placeables.sektion import SEKTION_CASEWORK_TYPES
from typehaus.library.placeables.sektion_parts import FrontLayout, kitchen_layout, sektion_parts
from typehaus.model import ProductPart

PREFIX = "sektion-axstad-kitchen-"


def _kitchen_symbol(cabinet):
    if cabinet.tag == "SEKT-CORNER-B38":
        return PREFIX + "corner-base"
    if cabinet.tag == "SEKT-CORNER-W26-30":
        return PREFIX + "corner-wall"
    if cabinet.tag == "SEKT-SINK-B36":
        return PREFIX + "sink"
    if cabinet.plan_symbol == "base-cabinet":
        return PREFIX + ("base-door" if cabinet.tag == "SEKT-B12" else "drawers")
    if cabinet.plan_symbol == "tall-cabinet":
        return PREFIX + ("tall-raised" if cabinet.tag == "SEKT-HIGH24-80" else "tall")
    return PREFIX + ("lift" if cabinet.tag.startswith("SEKT-TS24-15") else "wall")


# The frame each placed size orders, and how it stands: legs and toe kick, or hung on the rail.
# B24/B36 are the free-standing peninsula (floor anchor, no rail). Unplaced sizes order nothing.
_FRAMES = {
    "SEKT-B12": "PROD-IKEA-SEKTION-BASE-12-24-30", "SEKT-B18": "PROD-IKEA-SEKTION-BASE-18-24-30",
    "SEKT-B24": "PROD-IKEA-SEKTION-BASE24-30", "SEKT-B36": "PROD-IKEA-SEKTION-BASE-36-24-30",
    "SEKT-SINK-B36": "PROD-IKEA-SEKTION-BASE-36-24-30",
    "SEKT-CORNER-B38": "PROD-IKEA-SEKTION-CORNER-BASE-38",
    "SEKT-CORNER-W26-30": "PROD-IKEA-SEKTION-CORNER-W26-30",
    "SEKT-W12-30": "PROD-IKEA-SEKTION-WALL12-30",
    "SEKT-W30-30": "PROD-IKEA-SEKTION-WALL-30-15-30",
    "SEKT-W36-30": "PROD-IKEA-SEKTION-WALL-36-15-30",
    "SEKT-W30-20": "PROD-IKEA-SEKTION-WALL-30-15-20",
    "SEKT-W36-20": "PROD-IKEA-SEKTION-WALL-36-15-20",
    "SEKT-TS24-15": "PROD-IKEA-SEKTION-TOP-24-24-15",
    "SEKT-TS30-20": "PROD-IKEA-SEKTION-TOP-30-24-20",
    "SEKT-HIGH24-80": "PROD-IKEA-SEKTION-HIGH-24-24-80",
    "SEKT-HIGH18-90": "PROD-IKEA-SEKTION-HIGH-18-24-90",
}
_PENINSULA = {"SEKT-B24", "SEKT-B36"}
_CORNER_TOE_KICK_IN = 28  # both 14" notch faces of the 38x38 L
_KNOB = ProductPart(role="knob", product_ref="PROD-IKEA-BAGGANAS-KNOB-BLACK")


def _depth_in(cabinet):
    return round(cabinet.footprint[1].inches)


def _parts(cabinet, frame_symbol):
    """``cabinet`` is the configured kitchen type; ``frame_symbol`` the ladder's own glyph."""
    symbol = cabinet.plan_symbol
    width = round(cabinet.footprint[0].inches)
    if cabinet.tag == "SEKT-CORNER-B38":
        # Carousel, bifold hinges and fronts are the corner set; legs, rail and knob are not.
        return sektion_parts(width, 24, FrontLayout(30, ()), "legs", AXSTAD_HARDWARE,
                             toe_kick_in=_CORNER_TOE_KICK_IN, extra=(
            ProductPart(role="fitting", product_ref="PROD-IKEA-UTRUSTA-CAROUSEL"),
            ProductPart(role="hinge", product_ref="PROD-IKEA-UTRUSTA-HINGE-CORNER"),
            ProductPart(role="front", product_ref="PROD-IKEA-AXSTAD-CORNER-PAIR-13-30"), _KNOB))
    if cabinet.tag == "SEKT-CORNER-W26-30":
        # Hinges come with the frame; its two backs each take a 26" rail.
        return (ProductPart(role="front", product_ref="PROD-IKEA-AXSTAD-DOOR-15-30"), _KNOB,
                ProductPart(role="rail", product_ref="PROD-IKEA-SEKTION-RAIL-84", quantity=2,
                            length=inch(26)))
    layout = kitchen_layout(symbol, width, cabinet.height.inches)
    if cabinet.tag == "SEKT-HIGH24-80":
        # The lower bay holds the Rev-A-Shelf swing-out; AXILO feet behind a cut panel toe.
        return sektion_parts(width, 24, layout, "none", AXSTAD_HARDWARE, shelves=1, extra=(
            ProductPart(role="fitting", product_ref="PROD-REVASHELF-5374-24FL"),
            ProductPart(role="leg", product_ref="PROD-HAFELE-AXILO-637-76-355", quantity=4),
            ProductPart(role="toe_kick", product_ref="PROD-IKEA-FORBATTRA-MATTE-25-30",
                        cut=(inch(width), inch(6)))))
    support = "legs" if frame_symbol in ("base-cabinet", "sink-base", "tall-cabinet") else "none"
    return sektion_parts(width, _depth_in(cabinet), layout, support, AXSTAD_HARDWARE,
                         rail=cabinet.tag not in _PENINSULA,
                         fixed_frame_shelf=frame_symbol == "tall-cabinet")


def _ordered(cabinet, frame):
    if cabinet.tag not in _FRAMES:
        return {}
    return {"product_ref": _FRAMES[cabinet.tag], "parts": _parts(cabinet, frame.plan_symbol)}


KITCHEN_SEKTION_TYPES = tuple(
    cabinet.model_copy(update={
        "plan_symbol": (PREFIX + "tall-aligned" if cabinet.tag == "SEKT-HIGH18-90"
                        else _kitchen_symbol(cabinet)),
        **({"height": inch(93.5)} if cabinet.tag == "SEKT-HIGH18-90" else {}),
        **({"height": inch(86)} if cabinet.tag == "SEKT-HIGH24-80" else {}),
        "source": (cabinet.source or "") + " Catlin: AXSTAD matte white fronts; BAGGANÄS "
                  "black knobs on doors, 5 5/8-inch pulls with washers on drawers. "
                  "Nominal frame/rail envelope; 3/4-inch fronts and hardware project beyond it." +
                  (" Stock 80-inch frame on 6-inch AXILO 637.76.355 levelers; top 86 inches."
                   if cabinet.tag == "SEKT-HIGH24-80" else ""),
    }) for cabinet in SEKTION_CASEWORK_TYPES
)
KITCHEN_SEKTION_TYPES = tuple(
    cabinet.model_copy(update=_ordered(cabinet, frame))
    for cabinet, frame in zip(KITCHEN_SEKTION_TYPES, SEKTION_CASEWORK_TYPES, strict=True))

# All four living-room bases are doors/shelves (installation note K5, 2026-10-20).
# Local left is north at rotation -90: the B24's north hinge opens away from the slats.
LIVING_DOOR_TYPES = tuple(
    cabinet.model_copy(update={
        "tag": cabinet.tag + "-AXSTAD-DOOR",
        "name": cabinet.name + ", AXSTAD doors and shelves",
        "height": inch(36.5625),
        "plan_symbol": PREFIX + "base-door-raised",
        "parts": sektion_parts(round(cabinet.footprint[0].inches), 24,
                               kitchen_layout(PREFIX + "base-door-raised",
                                              cabinet.footprint[0].inches, 36.5625),
                               "legs", AXSTAD_HARDWARE),
        "source": (cabinet.source or "") + " Standard SEKTION legs at 4 1/16 inches; "
                  "floor-bearing feet and toe panel, 30-inch frame, top 36 9/16 inches.",
    }) for cabinet in KITCHEN_SEKTION_TYPES if cabinet.tag in {"SEKT-B18", "SEKT-B24", "SEKT-B36"}
)
LIVING_DOOR_TYPE_REFS = {cabinet.tag.removesuffix("-AXSTAD-DOOR"): cabinet.tag
                         for cabinet in LIVING_DOOR_TYPES}
