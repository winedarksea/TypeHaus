"""Catlin's interior door types: function, core and seal per type (owner, 2026-11-03).

`function` drives the hardware rows in prices.toml [allowances] (Kwikset Halifax Square,
satin nickel 15, house-wide); only D-B-SHOP's keyed set is authored, so it bills in
[hardware]. Hollow core on every commodity leaf; the solid, steel and sauna leaves are the
owner's exceptions. Per-door function, core, seal and relief path:
notes/interior_door_schedule.md.

House-local types merged by tag in plan/manifest.py: a redefined library tag drops the
library preset. NOT ``# haus: editable``: catalog definitions, nothing placed.
"""

from __future__ import annotations

from typehaus import DoorHardwareItem, DoorType
from typehaus.library.doors import DT_POCKET_INT_36
from typehaus.quantities import ft, inch

from plan.opening_products import HALIFAX_KEYED, STEEL_PREHUNG_HINGE

# Every commodity leaf is a stock 6'-8" prehung cut down on site (owner, 2026-11-06): jamb
# legs trimmed, the 80" slab cut to its undercut in the 81.51" RO over the finished floor
# (resolve/door_sizing derives the cut). TRIM-STANDARD hangs a leaf 1/2"; a door that is its
# room's relief path takes 3/4", the top of the 1/2"-3/4" range.
_PREHUNG = (" Stock 6'-8in prehung, cut down on site to the 81 1/2in RO: jamb legs trimmed, "
            "slab cut to its {undercut} undercut over the finished floor.")
_HOLLOW = ("1 3/8in hollow-core molded prehung, paint grade, 3 hinges US15; "
           "Kwikset Halifax Square {lever}, satin nickel 15.")
_SOLID = ("1 3/8in solid-core MDF prehung, paint grade, 3 hinges US15; "
          "Kwikset Halifax Square privacy, satin nickel 15.")
_RELIEF = inch(0.75)  # the range's top: a relief door's undercut


def _swing(tag: str, width, function: str, core: str, source: str, *, relief=False,
           sealed=False) -> DoorType:
    return DoorType(tag=tag, width=width, height=ft(6, 8), function=function, core=core,
                    leaf_thickness=inch(1.375), undercut=_RELIEF if relief else None,
                    bottom_seal=sealed,
                    source=source + _PREHUNG.format(undercut="3/4in" if relief else "1/2in"))


INTERIOR_DOOR_TYPES = (
    _swing("DT-INT-SWING30", ft(2, 6), "passage", "hollow", _HOLLOW.format(lever="passage")),
    # Bedrooms, the suite bath: each room's relief path (notes/system1_return_path.md).
    _swing("DT-INT-SWING30-PRIV", ft(2, 6), "privacy", "hollow", _HOLLOW.format(lever="privacy"),
           relief=True),
    _swing("DT-INT-SWING30-PRIV-SOLID", ft(2, 6), "privacy", "solid", _SOLID
           + " Sealed: kerf-in seal at stops and head plus a door-bottom sweep across the "
             "undercut; the bath's makeup air comes through the REG-S-XFER-BATH1 grille pair.",
           sealed=True),
    _swing("DT-INT-SWING32", ft(2, 8), "passage", "hollow", _HOLLOW.format(lever="passage")),
    # D-S-SUITE, D-A-HALVES (System 1 return), D-M-BATH2 (RM-M-BED's 15 cfm out).
    _swing("DT-INT-SWING32-PRIV", ft(2, 8), "privacy", "hollow", _HOLLOW.format(lever="privacy"),
           relief=True),
    _swing("DT-INT-SWING32-PRIV-SOLID", ft(2, 8), "privacy", "solid", _SOLID
           + " The powder room's exhaust makes up under it.", relief=True),
    _swing("DT-INT-SWING24-PRIV", ft(2), "privacy", "hollow", _HOLLOW.format(lever="privacy"),
           relief=True),
    _swing("DT-INT-SWING36", ft(3), "passage", "hollow", _HOLLOW.format(lever="passage")
           + " D-B-SHOP's makeup air passes under it.", relief=True),
    DoorType(
        tag="DT-INT-STEEL36-KEYED", width=ft(3), height=ft(6, 8), function="passage",
        leaf_thickness=inch(1.75), bottom_seal=True,
        hardware=(
            DoorHardwareItem(role="passage", product_ref=HALIFAX_KEYED.tag, height=inch(36),
                             installation="Keyed entry, locked from the hall; 2-3/8in backset."),
            # One item per hinge, at a height (the plan/door_types.py idiom): a heightless
            # quantity=3 item draws one hinge on EACH edge at mid-leaf, latch side included.
            *(DoorHardwareItem(role="hinge", product_ref=STEEL_PREHUNG_HINGE.tag,
                               height=inch(height),
                               installation="Coordination height; order the prehung with US15 "
                                            "hinges.")
              for height in (10, 40, 70)),
        ),
        source="Stock 36x80 flush insulated steel prehung (the cheap exterior line) in a wood "
               "jamb, ordered without a sill: compression weatherstrip at jambs and head plus a "
               "door-bottom sweep across its 1/2in undercut, no threshold. The workshop makes up "
               "through D-B-FURN's undercut, which must stay."),
    DoorType(
        tag="DT-INT-SAUNA24", width=ft(2), height=ft(6, 8),
        leaf_material_ref="cedar-sauna-trim", leaf_thickness=inch(1.75), bottom_seal=True,
        source="Stock 24x80 insulated all-wood sauna door slab (Finnleo / Saunacore class, or "
               "equal): ships with its own wood handle, roller catch and hinges, NO lock. Swings "
               "out into the gym on the 3/4 x 9 1/4 cedar flat jamb; the RO is the 24in leaf's "
               "derived one, unchanged. Sealed: the ERV supply and exhaust balance "
               "at 20/20 cfm (notes/erv_static_budget.md). Oiled, never painted."),
    DoorType(tag="DT-INT-SWING30-GLAZED", width=ft(2, 6), height=ft(6, 8), glazed=True,
             tempered=True, function="passage",
             source="Tempered-lite stile-and-rail prehung, Halifax Square passage, satin nickel "
                    "15. D-S-PLANT keeps the conventional 1/2in undercut: its room's pressure is "
                    "held by an interlocked damper (notes/system1_return_path.md)."
                    + _PREHUNG.format(undercut="1/2in")),
    DoorType(tag="DT-INT-DOUBLE60", width=ft(5), height=ft(6, 8), operation="double_swing",
             core="solid", function="passage", leaf_thickness=inch(1.375), undercut=_RELIEF,
             source="Flush 1 3/8in solid-core pair, unglazed: one Halifax Square passage set, a "
                    "dummy and top/bottom flush bolts on the passive leaf. Jamb and head gaskets "
                    "plus an astragal; the play room's 30 cfm supply leaves under it."
                    + _PREHUNG.format(undercut="3/4in")),
    DT_POCKET_INT_36.model_copy(update={
        "pocket_frame": "eclisse", "function": "passage", "leaf_thickness": inch(1.375),
        "source": DT_POCKET_INT_36.source + "; a flush pull and an edge pull, retail parts"}),
    DT_POCKET_INT_36.model_copy(update={
        "tag": "DT-POCKET-INT-36-PRIV", "pocket_frame": "eclisse", "function": "pocket_privacy",
        "leaf_thickness": inch(1.375),
        "source": DT_POCKET_INT_36.source + "; pocket privacy lock (turn inside, emergency "
                  "release outside) plus a flush pull and an edge pull, retail parts"}),
)

INTERIOR_DOOR_TAGS = frozenset(t.tag for t in INTERIOR_DOOR_TYPES)
