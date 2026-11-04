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

_HOLLOW = ("1 3/8in hollow-core molded prehung, paint grade, 3 hinges US15; "
           "Kwikset Halifax Square {lever}, satin nickel 15.")
_SOLID = ("1 3/8in solid-core MDF prehung, paint grade, 3 hinges US15; "
          "Kwikset Halifax Square privacy, satin nickel 15.")


def _swing(tag: str, width, function: str, core: str, source: str) -> DoorType:
    return DoorType(tag=tag, width=width, height=ft(6, 8), function=function, core=core,
                    source=source)


INTERIOR_DOOR_TYPES = (
    _swing("DT-INT-SWING30", ft(2, 6), "passage", "hollow", _HOLLOW.format(lever="passage")),
    _swing("DT-INT-SWING30-PRIV", ft(2, 6), "privacy", "hollow", _HOLLOW.format(lever="privacy")),
    _swing("DT-INT-SWING30-PRIV-SOLID", ft(2, 6), "privacy", "solid", _SOLID
           + " Sealed: kerf-in seal at stops and head plus a door-bottom sweep, no undercut; "
             "the bath's makeup air comes through the REG-S-XFER-BATH1 grille pair."),
    _swing("DT-INT-SWING32", ft(2, 8), "passage", "hollow", _HOLLOW.format(lever="passage")),
    _swing("DT-INT-SWING32-PRIV", ft(2, 8), "privacy", "hollow", _HOLLOW.format(lever="privacy")),
    _swing("DT-INT-SWING32-PRIV-SOLID", ft(2, 8), "privacy", "solid", _SOLID
           + " Keeps its 3/4in undercut: the powder room's exhaust makes up under it."),
    _swing("DT-INT-SWING24-PRIV", ft(2), "privacy", "hollow", _HOLLOW.format(lever="privacy")),
    _swing("DT-INT-SWING36", ft(3), "passage", "hollow", _HOLLOW.format(lever="passage")
           + " Keeps its undercut: D-B-SHOP's makeup air passes under it."),
    DoorType(
        tag="DT-INT-STEEL36-KEYED", width=ft(3), height=ft(6, 8), function="passage",
        hardware=(
            DoorHardwareItem(role="passage", product_ref=HALIFAX_KEYED.tag, height=inch(36),
                             installation="Keyed entry, locked from the hall; 2-3/8in backset."),
            DoorHardwareItem(role="hinge", product_ref=STEEL_PREHUNG_HINGE.tag, quantity=3,
                             installation="Order the prehung with US15 hinges."),
        ),
        source="Stock 36x80 flush insulated steel prehung (the cheap exterior line) in a wood "
               "jamb, ordered without a sill: compression weatherstrip at jambs and head plus a "
               "door-bottom sweep, no threshold and no undercut. The workshop makes up through "
               "D-B-FURN's undercut, which must stay."),
    DoorType(
        tag="DT-INT-SAUNA24", width=ft(2), height=ft(6, 8),
        leaf_material_ref="cedar-sauna-trim",
        source="Stock 24x80 insulated all-wood sauna door slab (Finnleo / Saunacore class, or "
               "equal): ships with its own wood handle, roller catch and hinges, NO lock. Swings "
               "out into the gym on the 3/4 x 9 1/4 cedar flat jamb; the RO is the 24in leaf's "
               "derived one, unchanged. Sealed, no undercut: the ERV supply and exhaust balance "
               "at 20/20 cfm (notes/erv_static_budget.md). Oiled, never painted."),
    DoorType(tag="DT-INT-SWING30-GLAZED", width=ft(2, 6), height=ft(6, 8), glazed=True,
             tempered=True, function="passage",
             source="Tempered-lite stile-and-rail prehung, Halifax Square passage, satin nickel "
                    "15. D-S-PLANT keeps a conventional undercut (notes/system1_return_path.md)."),
    DoorType(tag="DT-INT-DOUBLE60", width=ft(5), height=ft(6, 8), operation="double_swing",
             core="solid", function="passage",
             source="Flush solid-core pair, unglazed: one Halifax Square passage set, a dummy and "
                    "top/bottom flush bolts on the passive leaf. Jamb and head gaskets plus an "
                    "astragal; keeps its 3/4in undercut, where the play room's 30 cfm supply leaves."),
    DT_POCKET_INT_36.model_copy(update={
        "pocket_frame": "eclisse", "function": "passage",
        "source": DT_POCKET_INT_36.source + "; a flush pull and an edge pull, retail parts"}),
    DT_POCKET_INT_36.model_copy(update={
        "tag": "DT-POCKET-INT-36-PRIV", "pocket_frame": "eclisse", "function": "pocket_privacy",
        "source": DT_POCKET_INT_36.source + "; pocket privacy lock (turn inside, emergency "
                  "release outside) plus a flush pull and an edge pull, retail parts"}),
)

INTERIOR_DOOR_TAGS = frozenset(t.tag for t in INTERIOR_DOOR_TYPES)
