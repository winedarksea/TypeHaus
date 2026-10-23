"""Catlin's AXSTAD/BAGGANÄS configuration over the finish-neutral SEKTION ladder.

The same B24 frame is drawers in the peninsula and doors in the living room. Keep those
specifications distinct without changing installation dimensions or the shared catalog.
"""

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
        return PREFIX + "tall"
    return PREFIX + ("lift" if cabinet.tag.startswith("SEKT-TS24-15") else "wall")


KITCHEN_SEKTION_TYPES = tuple(
    cabinet.model_copy(update={
        "plan_symbol": _kitchen_symbol(cabinet),
        "source": (cabinet.source or "") + " Catlin: AXSTAD matte white fronts; BAGGANÄS "
                  "black knobs on doors, 5 5/8-inch pulls with washers on drawers. "
                  "Nominal frame/rail envelope; 3/4-inch fronts and hardware project beyond it.",
    }) for cabinet in SEKTION_CASEWORK_TYPES
)

# All four living-room bases are doors/shelves (installation note K5, 2026-10-20).
# Local left is north at rotation -90: the B24's north hinge opens away from the slats.
LIVING_DOOR_TYPES = tuple(
    cabinet.model_copy(update={
        "tag": cabinet.tag + "-AXSTAD-DOOR",
        "name": cabinet.name + ", AXSTAD doors and shelves",
        "plan_symbol": PREFIX + "base-door",
    }) for cabinet in KITCHEN_SEKTION_TYPES if cabinet.tag in {"SEKT-B18", "SEKT-B24", "SEKT-B36"}
)
LIVING_DOOR_TYPE_REFS = {cabinet.tag.removesuffix("-AXSTAD-DOOR"): cabinet.tag
                         for cabinet in LIVING_DOOR_TYPES}
