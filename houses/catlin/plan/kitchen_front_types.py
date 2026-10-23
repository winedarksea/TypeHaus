"""Catlin's AXSTAD/BAGGANÄS configuration over the finish-neutral SEKTION ladder.

The same B24 frame is drawers in the peninsula and doors in the living room. Fronts and
support heights are house configurations; the shared cabinet frames stay unchanged.
"""

from typehaus import inch

from typehaus.library.placeables.sektion import SEKTION_CASEWORK_TYPES

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

# All four living-room bases are doors/shelves (installation note K5, 2026-10-20).
# Local left is north at rotation -90: the B24's north hinge opens away from the slats.
LIVING_DOOR_TYPES = tuple(
    cabinet.model_copy(update={
        "tag": cabinet.tag + "-AXSTAD-DOOR",
        "name": cabinet.name + ", AXSTAD doors and shelves",
        "height": inch(36.5625),
        "plan_symbol": PREFIX + "base-door-raised",
        "source": (cabinet.source or "") + " Standard SEKTION legs at 4 1/16 inches; "
                  "floor-bearing feet and toe panel, 30-inch frame, top 36 9/16 inches.",
    }) for cabinet in KITCHEN_SEKTION_TYPES if cabinet.tag in {"SEKT-B18", "SEKT-B24", "SEKT-B36"}
)
LIVING_DOOR_TYPE_REFS = {cabinet.tag.removesuffix("-AXSTAD-DOOR"): cabinet.tag
                         for cabinet in LIVING_DOOR_TYPES}
