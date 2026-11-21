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

from plan import interior_door_products as products
from plan.opening_products import HALIFAX_KEYED, HOLD_OPEN_CLOSER, STEEL_PREHUNG_HINGE
from typehaus import BypassDoorSpec, DoorHardwareItem, DoorType
from typehaus.library.doors import DT_INT_ACCESS24, DT_POCKET_INT_36, STANDARD_DOOR_TYPES
from typehaus.quantities import ft, inch

# Every commodity leaf is a stock 6'-8" prehung cut down on site (owner, 2026-11-06): jamb
# legs trimmed, the 80" slab cut to its undercut in the 81.51" RO over the finished floor
# (resolve/door_sizing derives the cut). TRIM-STANDARD hangs a leaf 1/2"; a door that is its
# room's relief path takes 3/4", the top of the 1/2"-3/4" range.
_PREHUNG = (" Stock 6'-8in prehung, cut down on site to the 81 1/2in RO: jamb legs trimmed, "
            "slab cut to its {undercut} undercut over the finished floor.")
_HOLLOW = ("1 3/8in flush hollow-core prehung, smooth, paint grade, 3 hinges US15; "
           "Kwikset Halifax Square {lever}, satin nickel 15.")
_SOLID = ("1 3/8in flush solid-core prehung, smooth, paint grade, 3 hinges US15; "
          "Kwikset Halifax Square privacy, satin nickel 15.")
_RELIEF = inch(0.75)  # the range's top: a relief door's undercut
_LIBRARY = {t.tag: t for t in STANDARD_DOOR_TYPES}


def _swing(tag: str, width, function: str, core: str, source: str, *, relief=False,
           sealed=False, product=None) -> DoorType:
    product = product or (products.FLUSH_SC_PREHUNG if core == "solid"
                          else products.FLUSH_HC_PREHUNG)
    return DoorType(tag=tag, width=width, height=ft(6, 8), function=function, core=core,
                    leaf_thickness=inch(1.375), undercut=_RELIEF if relief else None,
                    bottom_seal=sealed, product_ref=product.tag,
                    source=source + _PREHUNG.format(undercut="3/4in" if relief else "1/2in"))


INTERIOR_DOOR_TYPES = (
    _swing("DT-INT-SWING30", ft(2, 6), "passage", "hollow", _HOLLOW.format(lever="passage")),
    # Bedrooms, the suite bath: each room's relief path (notes/system1_return_path.md).
    _swing("DT-INT-SWING30-PRIV", ft(2, 6), "privacy", "hollow", _HOLLOW.format(lever="privacy"),
           relief=True),
    # D-S-BED3 (2026-11-11): its room balances through REG-S-HP-BED3-RET, so the stock 1/2".
    _swing("DT-INT-SWING30-PRIV-STOCK", ft(2, 6), "privacy", "hollow",
           _HOLLOW.format(lever="privacy")),
    _swing("DT-INT-SWING30-PRIV-SOLID", ft(2, 6), "privacy", "solid", _SOLID
           + " Sealed: kerf-in seal at stops and head plus a door-bottom sweep across the "
             "undercut; the bath's makeup air comes through the REG-S-XFER-BATH1 grille pair.",
           sealed=True),
    _swing("DT-INT-SWING32", ft(2, 8), "passage", "hollow", _HOLLOW.format(lever="passage")),
    # D-A-HALVES (System 1 return), D-M-BATH2 (RM-M-BED's 15 cfm out).
    _swing("DT-INT-SWING32-PRIV", ft(2, 8), "privacy", "hollow", _HOLLOW.format(lever="privacy"),
           relief=True),
    _swing("DT-INT-SWING32-PRIV-SOLID", ft(2, 8), "privacy", "solid", _SOLID
           + " The powder room's exhaust makes up under it.", relief=True),
    # D-S-SUITE (2026-11-09): the suite balances through its own ducted return.
    _swing("DT-INT-SWING32-PRIV-SOLID-SEALED", ft(2, 8), "privacy", "solid", _SOLID
           + " Sealed: kerf-in seal at stops and head plus a door-bottom sweep across the "
             "undercut; the suite returns through REG-S-HP-SUITE-RET.", sealed=True),
    _swing("DT-INT-SWING24-PRIV", ft(2), "privacy", "hollow", _HOLLOW.format(lever="privacy"),
           relief=True),
    _swing("DT-INT-SWING36", ft(3), "passage", "hollow", _HOLLOW.format(lever="passage")
           + " D-B-SHOP's makeup air passes under it.", relief=True),
    DoorType(
        tag="DT-INT-STEEL36-KEYED", width=ft(3), height=ft(6, 8), function="passage",
        leaf_thickness=inch(1.75), bottom_seal=True,
        product_ref=products.STEEL_FLUSH_PREHUNG.tag,
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
    # D-S-PLANT (2026-11-12): the plant room is sealed and holds its own humidity, so its door
    # is a stock exterior-grade steel prehung, the plant room the weather side, swinging into
    # Study 2. Not a storm door: those are built to sit in front of a primary door.
    DoorType(
        tag="DT-INT-STEEL30-SEALED", width=ft(2, 6), height=ft(6, 8), function="passage",
        glazed=True, tempered=True, leaf_thickness=inch(1.75), bottom_seal=True,
        self_closing=True, product_ref=products.STEEL_FULL_LITE_PREHUNG.tag,
        hardware=(
            DoorHardwareItem(role="closer", product_ref=HOLD_OPEN_CLOSER.tag, height=inch(78),
                             installation="Study 2 face; hold-open arm for the open-door "
                                          "summer fallback."),
            *(DoorHardwareItem(role="hinge", product_ref=STEEL_PREHUNG_HINGE.tag,
                               height=inch(height),
                               installation="Coordination height; order the prehung with US15 "
                                            "hinges.")
              for height in (10, 40, 70)),
        ),
        source="Stock 30x80 insulated steel prehung, full tempered lite (Menards Mastercraft "
               "class, <= $500): composite frame, compression/magnetic weatherstrip, "
               "adjustable sill, no undercut. Halifax Square passage. Jamb extended to the "
               "7.43in wall. The membrane returns at the jambs; the reducer under the sill "
               "stays the spill dam's base. notes/plant_room.md."),
    DoorType(
        tag="DT-INT-SAUNA24", width=ft(2), height=ft(6, 8),
        leaf_material_ref="cedar-sauna-trim", leaf_thickness=inch(1.75), bottom_seal=True,
        product_ref=products.SAUNA_DOOR.tag,
        source="Stock 24x80 insulated all-wood sauna door slab (Finnleo / Saunacore class, or "
               "equal): ships with its own wood handle, roller catch and hinges, NO lock. Swings "
               "out into the gym on the 3/4 x 9 1/4 cedar flat jamb; the RO is the 24in leaf's "
               "derived one, unchanged. Sealed: the ERV supply and exhaust balance "
               "at 20/20 cfm (notes/erv_static_budget.md). Oiled, never painted."),
    DoorType(tag="DT-INT-CLOSET32", width=ft(2, 8), height=ft(6), function="closet",
             core="hollow", leaf_thickness=inch(1.375),
             product_ref=products.FLUSH_HC_PREHUNG.tag,
             source="2'-8in x 6'-0in under-stair closet leaf, the full-height way in to "
                    "PA-B-MAIN-SHUTOFF; the head under ST-B2M cannot give 6'-8in plus a header."
                    + _PREHUNG.format(undercut="1/2in")),
    DoorType(tag="DT-INT-SWING30-GLAZED", width=ft(2, 6), height=ft(6, 8), glazed=True,
             tempered=True, function="passage", product_ref=products.GLAZED_SLAB.tag,
             source="Tempered-lite stile-and-rail prehung, Halifax Square passage, satin nickel "
                    "15. D-S-PLANT keeps the conventional 1/2in undercut: its room's pressure is "
                    "held by an interlocked damper (notes/system1_return_path.md)."
                    + _PREHUNG.format(undercut="1/2in")),
    DoorType(tag="DT-INT-DOUBLE60", width=ft(5), height=ft(6, 8), operation="double_swing",
             core="solid", function="passage", leaf_thickness=inch(1.375), undercut=_RELIEF,
             product_ref=products.FLUSH_SC_PREHUNG.tag,
             source="Flush 1 3/8in solid-core pair, unglazed: one Halifax Square passage set, a "
                    "dummy and top/bottom flush bolts on the passive leaf. Jamb and head gaskets "
                    "plus an astragal; the play room's 30 cfm supply leaves under it."
                    + _PREHUNG.format(undercut="3/4in")),
    DT_POCKET_INT_36.model_copy(update={
        "pocket_frame": "eclisse", "function": "passage", "leaf_thickness": inch(1.375),
        "core": "hollow", "product_ref": products.FLUSH_HC_SLAB_36.tag,
        "source": DT_POCKET_INT_36.source + "; a flush pull and an edge pull, retail parts"}),
    DT_POCKET_INT_36.model_copy(update={
        "tag": "DT-POCKET-INT-36-PRIV", "pocket_frame": "eclisse", "function": "pocket_privacy",
        "leaf_thickness": inch(1.375), "core": "hollow",
        "product_ref": products.FLUSH_HC_SLAB_36.tag,
        "source": DT_POCKET_INT_36.source + "; pocket privacy lock (turn inside, emergency "
                  "release outside) plus a flush pull and an edge pull, retail parts"}),
    # D-M-MUDC (owner, 2026-11-20): two 24x80 flush HC slabs on a Johnson 138F482D set, cased
    # like every other door. IN183834: opening 2W - 1in, door + 2 3/8in, 3/8in at the floor.
    DoorType(
        tag="DT-INT-BYPASS48", width=ft(4), height=ft(6, 8), operation="slide",
        function="closet", core="hollow", leaf_thickness=inch(1.375),
        product_ref=products.FLUSH_HC_SLAB_24.tag,
        bypass_door=BypassDoorSpec(
            track_width=inch(3.459), track_height=inch(2.187), lane_pitch=inch(1.6875),
            floor_clearance=inch(0.375), head_over_leaf=inch(2.375), overlap=inch(1),
            door_thickness=inch(1.375), guide_width=inch(1.25), guide_depth=inch(4.5),
            guide_height=inch(0.75), pull_diameter=inch(2.125), pull_height=inch(36),
            product_ref=products.JOHNSON_138F482D.tag,
            source="Johnson Hardware 138F (page, catalog CA138FSD Rev 03/16, install sheet "
                   "IN183834 Rev 9/23): track 3.459 x 2.187in (138F600x600.jpg); lanes "
                   "~1 11/16in c-c MEASURED off that drawing; 2135 guide size estimated off "
                   "the catalog image; pull centred 36in up."),
        source="Two 24x80 flush hollow-core primed slabs (Steves J62H1FADLC99) on a Johnson "
               "138F482D 48in two-door set: 1120 hangers, 2135 guide, #30 cup pulls. Finished "
               "opening 47 x 82 3/8in over the LVP; each leaf laps the other 1in."),
    _LIBRARY["DT-INT-BIFOLD56"].model_copy(update={
        "core": "solid", "product_ref": products.FLUSH_BIFOLD.tag}),
    DT_INT_ACCESS24.model_copy(update={
        "core": "hollow", "leaf_thickness": inch(1.375),
        "product_ref": products.FLUSH_HC_SLAB_24.tag}),
)

INTERIOR_DOOR_TAGS = frozenset(t.tag for t in INTERIOR_DOOR_TYPES)
