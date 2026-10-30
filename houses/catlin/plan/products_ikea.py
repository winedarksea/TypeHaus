"""Catlin's IKEA records: the SEKTION kitchen and every bought part round it (→ plan/products.py).

Identity only, never a price (#28): article number, name, retail pack and stick length.
``haus order houses/catlin --brand IKEA`` lists these against the cabinets that use them;
the counts come from ``library/placeables/sektion_parts.py`` (oracle:
notes/ikea_sektion_order.md). A ``sku=""`` is an article nobody has read yet, and the order
list reports it as unresolved rather than guessing.

Frame-and-front records that belong to one room stay beside that room's types
(bath1_storage_types, study_nook_types, bed_desk_types, living_east_run_types, bath2_vanity_types).
"""

from __future__ import annotations

from typehaus.model import Product, inch

# IKEA US listings read 2026-10-30 (prices in prices.toml). "selector" = the size table on a
# sibling listing; the article is the listing URL's number, confirm at order.
_READ = "IKEA US listing, read 2026-10-30."
_SELECTOR = ("IKEA US size selector, read 2026-10-30; article from the listing URL, "
             "confirm at order.")


def _ikea(tag: str, sku: str, model: str, name: str, source: str = _SELECTOR, *,
          pack: int = 1, stock_in: float | None = None) -> Product:
    return Product(tag=tag, brand="IKEA", model=model, name=name, sku=sku,
                   url=f"https://www.ikea.com/us/en/p/-{sku.replace('.', '')}/" if sku else None,
                   source=source, pack_quantity=pack,
                   stock_length=inch(stock_in) if stock_in else None)


# --- Kitchen system and front lines ----------------------------------------------------
#
# ** POLAND IS A 'DON'T', AND THE OWNER'S OWN MILL IS WHY. ** Section 232 puts 25% on wooden
# cabinets, vanities AND PARTS THEREOF from 2025-10-14 (the scheduled 50% was delayed to
# 2027-01-01; the EU cap is 15%), EU carcasses are 600 mm deep and 870 mm high against a US
# 24" and 34.5", there is no warranty recourse across an ocean, and the whole reason to
# import is a wood front at a low price -- which $2/sf white oak off family land, in 4/4 and
# 8/4 up to 18" wide, beats outright with no lead time. If you want European engineering, buy
# the HARDWARE (Blum/Hettich) and put it in domestic boxes.
#
# SEKTION carcasses are manufactured in the US, so the box half of the kitchen is
# structurally insulated from the 25% while nearly every RTA competitor eats it. Fronts are
# imported. Time the order to the IKEA kitchen event, historically Feb-April.
IKEA_SEKTION = Product(
    tag="PROD-IKEA-SEKTION", brand="IKEA", model="SEKTION",
    name="SEKTION frameless kitchen cabinet system, US-manufactured carcasses",
    source="IKEA US product literature and 2025-26 tariff position, read 2026-09-06. The "
           "carcass system only; kitchen fronts are PROD-IKEA-AXSTAD-WH. Frameless, which is what "
           "makes a 24\" box give a 22 1/2\" clear opening and is why the Rev-A-Shelf "
           "5374-24FL swing-out in plan/placeables.py fits at all.",
)
IKEA_VOXTORP_WHITE = Product(
    tag="PROD-IKEA-VOXTORP-WH", brand="IKEA", model="VOXTORP matt white",
    name="VOXTORP matt white slab door and drawer front",
    source="IKEA US product listing, read 2026-09-06. Best cleanability of the slab lines: "
           "matte foil, wipes with a damp cloth, no fingerprints. A SLAB, not a shaker -- "
           "the inside corner of a shaker rail is where cooking grease lives, which is why "
           "AXSTAD loses on the top criterion despite being durable. RINGHULT high gloss is "
           "the worst possible surface beside an induction range and BODBYN's painted MDF "
           "chips (IKEA sells touch-up paint for exactly that reason). ** WATCH THE ONE "
           "WEAKNESS: ** the integrated edge pull collects grease on the underside where you "
           "cannot see it, which is why real pulls (PROD-TOPKNOBS-BAR-SS) are still bought. "
           "Do NOT pay IKEA $459 a door for VEDHAMN oak when you mill oak.",
)
# Frame, front and drawer mechanism remain separate purchases. The configured symbols
# now record the kitchen's door/drawer divisions; prices.toml carries installed allowances.
IKEA_MAXIMERA = Product(
    tag="PROD-IKEA-MAXIMERA", brand="IKEA", model="MAXIMERA",
    name="MAXIMERA soft-close full-extension drawer, high/medium/low",
    source="IKEA US product literature, read 2026-09-11. ** MAXIMERA, NOT FORVARA: ** "
           "FORVARA is the basic drawer and is what a SEKTION base ships with if nobody "
           "chooses; MAXIMERA is full-extension with integrated soft-close, and full "
           "extension is the whole argument for a drawer base over a door base — a drawer "
           "you cannot pull all the way out is a cupboard with a lid. Fronts sit on the "
           "5/10/15 in. ladder, so a 30 in. base is 5+10+15 or 10+10+10 and the fronts "
           "line up across a run either way. Fits every base and pantry width in this "
           "kitchen where specified. The B12 and carousel corners use doors, not drawer "
           "boxes. Kitchen fronts and hardware are AXSTAD/BAGGANÄS (2026-10-22).",
)
IKEA_AXSTAD_WHITE = Product(
    tag="PROD-IKEA-AXSTAD-WH", brand="IKEA", model="AXSTAD matte white",
    name="AXSTAD matte white recessed-panel kitchen doors and drawer fronts",
    url="https://www.ikea.com/us/en/p/axstad-door-matte-white-50426048/",
    source="Owner selection 2026-10-22 replaces VOXTORP in the kitchen and connected living "
           "run. 3/4-inch fronts, 1/8-inch nominal reveals. Solid 15x20 doors above cold "
           "storage; AXSTAD glass is only listed in 30/40-inch heights, so glass is deferred.",
)
IKEA_BAGGANAS_KNOB_BLACK = Product(
    tag="PROD-IKEA-BAGGANAS-KNOB-BLACK", brand="IKEA", model="BAGGANÄS black knob",
    sku="903.384.17", name="BAGGANÄS black knob, 13/16-inch diameter", pack_quantity=2,
    url="https://www.ikea.com/us/en/p/bagganaes-knob-black-90338417/",
    source="IKEA US read 2026-10-22: diameter 13/16, projection 15/16 inch; $7/2-pack. "
           "Selected for kitchen/living cabinet doors, at opening-edge rails.",
)
IKEA_BAGGANAS_PULL_BLACK = Product(
    tag="PROD-IKEA-BAGGANAS-PULL-BLACK", brand="IKEA", model="BAGGANÄS black handle",
    sku="803.384.13", name="BAGGANÄS black pull, 5 5/8 inches, with washers", pack_quantity=2,
    url="https://www.ikea.com/us/en/p/bagganaes-handle-black-80338413/",
    source="IKEA US read 2026-10-22: length 5 5/8, hole spacing 5 1/16, projection 1 1/4, "
           "width 3/8 inch; $9/2-pack. One horizontal pull per kitchen drawer front. "
           "Use the included washers. The custom garage retains its lift/roll-up operation.",
)


# --- Frames (frame only; fronts, hinges, legs, rail and shelves are their own rows) --------
BASE_FRAME_12 = _ikea("PROD-IKEA-SEKTION-BASE-12-24-30", "102.653.92", "SEKTION 12x24x30 base",
                      'SEKTION white base cabinet frame, 12 x 24 x 30"')
BASE_FRAME_18 = _ikea("PROD-IKEA-SEKTION-BASE-18-24-30", "202.653.96", "SEKTION 18x24x30 base",
                      'SEKTION white base cabinet frame, 18 x 24 x 30"')
BASE_FRAME_36 = _ikea("PROD-IKEA-SEKTION-BASE-36-24-30", "802.653.98", "SEKTION 36x24x30 base",
                      'SEKTION white base cabinet frame, 36 x 24 x 30"',
                      _READ + " Not sold online: stock check in store. Sink base uses it too.")
CORNER_BASE_FRAME = _ikea(
    "PROD-IKEA-SEKTION-CORNER-BASE-38", "705.967.56", "SEKTION corner base 38x24x30",
    'SEKTION white corner base cabinet frame, 38 x 24 x 30"',
    "IKEA US s79582533 sub-articles, read 2026-10-30: frame 705.967.56, UTRUSTA carousel "
    "606.018.00, corner hinges 104.272.62 and VALLSTENA fronts; legs and knob separate. "
    "Hang each bifold leaf on the end AWAY from the range: the slide-in stands 3\" proud.")
WALL_FRAME_30_30 = _ikea("PROD-IKEA-SEKTION-WALL-30-15-30", "702.654.69", "SEKTION 30x15x30 wall",
                         'SEKTION white wall cabinet frame, 30 x 14 3/4 x 30"', _READ)
WALL_FRAME_36_30 = _ikea("PROD-IKEA-SEKTION-WALL-36-15-30", "902.654.49", "SEKTION 36x15x30 wall",
                         'SEKTION white wall cabinet frame, 36 x 14 3/4 x 30"')
WALL_FRAME_30_20 = _ikea("PROD-IKEA-SEKTION-WALL-30-15-20", "102.654.53", "SEKTION 30x15x20 wall",
                         'SEKTION white wall cabinet frame, 30 x 14 3/4 x 20"')
WALL_FRAME_36_20 = _ikea("PROD-IKEA-SEKTION-WALL-36-15-20", "302.654.71", "SEKTION 36x15x20 wall",
                         'SEKTION white wall cabinet frame, 36 x 14 3/4 x 20"')
HIGH_FRAME_24_80 = _ikea("PROD-IKEA-SEKTION-HIGH-24-24-80", "202.654.38", "SEKTION 24x24x80 high",
                         'SEKTION white high cabinet frame, 24 x 24 x 80"', _READ)
TOP_FRAME_30_20 = _ikea(
    "PROD-IKEA-SEKTION-TOP-30-24-20", "402.655.12", "SEKTION 30x24x20 top, ventilated",
    'SEKTION white top cabinet with ventilation, 30 x 24 x 20"',
    "IKEA US listing, verified 2026-10-05: 23 5/8 bare depth, 24 with suspension rail.")

# --- AXSTAD matte white fronts --------------------------------------------------------------
AXSTAD_DOORS = (
    _ikea("PROD-IKEA-AXSTAD-DOOR-12-30", "104.260.45", "AXSTAD door 12x30",
          'AXSTAD door, matte white, 12 x 30"'),
    _ikea("PROD-IKEA-AXSTAD-DOOR-15-20", "504.260.48", "AXSTAD door 15x20",
          'AXSTAD door, matte white, 15 x 20"'),
    _ikea("PROD-IKEA-AXSTAD-DOOR-15-30", "304.260.49", "AXSTAD door 15x30",
          'AXSTAD door, matte white, 15 x 30"'),
    _ikea("PROD-IKEA-AXSTAD-DOOR-18-20", "304.260.54", "AXSTAD door 18x20",
          'AXSTAD door, matte white, 18 x 20"'),
    _ikea("PROD-IKEA-AXSTAD-DOOR-18-30", "004.260.55", "AXSTAD door 18x30",
          'AXSTAD door, matte white, 18 x 30"', _READ),
    _ikea("PROD-IKEA-AXSTAD-DOOR-18-40", "804.260.56", "AXSTAD door 18x40",
          'AXSTAD door, matte white, 18 x 40"'),
    _ikea("PROD-IKEA-AXSTAD-DOOR-24-30", "004.260.79", "AXSTAD door 24x30",
          'AXSTAD door, matte white, 24 x 30"', _READ),
    _ikea("PROD-IKEA-AXSTAD-DOOR-24-50", "", "AXSTAD door 24x50",
          'AXSTAD door, matte white, 24 x 50"',
          "Size listed in the US selector; article not read."),
    _ikea("PROD-IKEA-AXSTAD-CORNER-PAIR-13-30", "", "AXSTAD bifold pair for corner base",
          'AXSTAD 2-piece door for corner base cabinet, matte white, 13 x 30"',
          "Replaces the VALLSTENA pair in s79582533; AXSTAD corner set not yet read."),
)
AXSTAD_DRAWER_FRONTS = (
    _ikea("PROD-IKEA-AXSTAD-DRAWER-18-10", "204.260.64", "AXSTAD drawer front 18x10",
          'AXSTAD drawer front, matte white, 18 x 10"'),
    _ikea("PROD-IKEA-AXSTAD-DRAWER-24-10", "504.260.67", "AXSTAD drawer front 24x10",
          'AXSTAD drawer front, matte white, 24 x 10"'),
    _ikea("PROD-IKEA-AXSTAD-DRAWER-36-10", "304.260.73", "AXSTAD drawer front 36x10",
          'AXSTAD drawer front, matte white, 36 x 10"'),
    # The 24x24x15 top's lift-up front: IKEA sells no 24x15 door, so its drawer front.
    _ikea("PROD-IKEA-AXSTAD-DRAWER-24-15", "", "AXSTAD drawer front 24x15",
          'AXSTAD front, matte white, 24 x 15", as a lift-up door',
          "Size listed in the US selector; article not read."),
)
MAXIMERA_MEDIUM = (
    _ikea("PROD-IKEA-MAXIMERA-MEDIUM-18-24", "002.656.65", "MAXIMERA medium 18x24",
          'MAXIMERA drawer, medium, white, 18 x 24"', "IKEA US listing, read 2026-10-21."),
    _ikea("PROD-IKEA-MAXIMERA-MEDIUM-24-24", "802.656.66", "MAXIMERA medium 24x24",
          'MAXIMERA drawer, medium, white, 24 x 24"', "IKEA US listing, read 2026-10-02."),
    _ikea("PROD-IKEA-MAXIMERA-MEDIUM-36-24", "602.656.67", "MAXIMERA medium 36x24",
          'MAXIMERA drawer, medium, white, 36 x 24"'),
    _ikea("PROD-IKEA-MAXIMERA-HIGH-18-24", "502.656.82", "MAXIMERA high 18x24",
          'MAXIMERA drawer, high, white, 18 x 24"', "IKEA US listing, read 2026-10-21."),
)
VOXTORP_FRONTS = tuple(
    _ikea(f"PROD-IKEA-VOXTORP-{kind.upper()}-{w}-{h}", sku, f"VOXTORP {kind} {w}x{h}",
          f'VOXTORP {kind}, matte white, {w} x {h}"', "IKEA US listing, read 2026-10-02/21.")
    for kind, w, h, sku in (("door", 24, 30, "102.733.30"), ("door", 24, 20, "302.733.29"),
                            ("drawer", 24, 10, "802.733.41"), ("door", 18, 30, "802.733.22"),
                            ("door", 18, 20, "002.733.21"), ("drawer", 18, 15, "202.733.20"),
                            ("drawer", 18, 10, "402.733.38"), ("door", 24, 15, "602.733.42")))

# --- Hardware: hinges carry the soft close (a built-in damper); MAXIMERA closes itself ------
UTRUSTA_HINGE = _ikea("PROD-IKEA-UTRUSTA-HINGE-110", "805.248.82", "UTRUSTA hinge 110",
                      "UTRUSTA hinge with built-in damper for kitchen, 110°, 2-pack", _READ, pack=2)
UTRUSTA_HORIZONTAL_HINGE = _ikea(
    "PROD-IKEA-UTRUSTA-HINGE-HORIZONTAL", "804.654.15", "UTRUSTA horizontal hinge",
    "UTRUSTA hinge with damper for horizontal door, white, 2-pack", _READ, pack=2)
UTRUSTA_CORNER_HINGES = _ikea(
    "PROD-IKEA-UTRUSTA-HINGE-CORNER", "104.272.62", "UTRUSTA hinges for corner base",
    "UTRUSTA hinges with damper for the corner base bifold", "s79582533 sub-article, 2026-10-30.")
UTRUSTA_CAROUSEL = _ikea("PROD-IKEA-UTRUSTA-CAROUSEL", "606.018.00", "UTRUSTA carousel",
                         "UTRUSTA carousel for corner base cabinet",
                         "s79582533 sub-article, 2026-10-30.")
SEKTION_LEG = _ikea("PROD-IKEA-SEKTION-LEG", "905.560.71", "SEKTION leg",
                    'SEKTION leg for cabinet, 4 1/2" (3 1/2-5 1/8" adjustable), 2-pack', _READ,
                    pack=2)
FORBATTRA_TOE_KICK = _ikea("PROD-IKEA-FORBATTRA-TOEKICK-84", "602.668.17", "FÖRBÄTTRA toe kick",
                           'FÖRBÄTTRA toe kick, white, 84 x 4 1/2 x 3/8"', _READ, stock_in=84)
UTRUSTA_SHELVES = tuple(
    _ikea(f"PROD-IKEA-UTRUSTA-SHELF-{w}-{d}", sku, f"UTRUSTA shelf {w}x{d}",
          f'UTRUSTA shelf, white, {w} x {"14 3/4" if d == 15 else d}", 2-pack',
          _READ if sku == "002.655.33" else _SELECTOR, pack=2)
    for w, d, sku in ((12, 24, "902.655.24"), (18, 24, "202.655.32"), (24, 24, "002.655.33"),
                      (36, 24, "802.655.34"), (12, 15, "402.655.31"), (30, 15, "502.655.35"),
                      (36, 15, "402.655.26")))

# --- Not IKEA: what the kitchen buys elsewhere ---------------------------------------------
REV_A_SHELF_SWING_OUT = Product(
    tag="PROD-REVASHELF-5374-24FL", brand="Rev-A-Shelf", model="5374-24FL", sku="5374-24FL",
    name="Swing-out pantry insert, 24-inch, with door mount brackets",
    source="Kept in each 24-inch high pantry (notes/kitchen_stock_cabinet_details.md K4); "
           "needs a 22 1/4-inch clear opening.")
AXILO_LEVELER = Product(
    tag="PROD-HAFELE-AXILO-637-76-355", brand="Häfele", model="AXILO 637.76.355",
    sku="637.76.355", name="AXILO plinth leveler, 140-170 mm, with screw-mount plate",
    source="Häfele base fittings catalogue (K4): four per 24-inch high pantry, at 6 inches.")

IKEA_PRODUCTS = (
    IKEA_SEKTION, IKEA_VOXTORP_WHITE, IKEA_MAXIMERA, IKEA_AXSTAD_WHITE,
    IKEA_BAGGANAS_KNOB_BLACK, IKEA_BAGGANAS_PULL_BLACK,
    BASE_FRAME_12, BASE_FRAME_18, BASE_FRAME_36, CORNER_BASE_FRAME, WALL_FRAME_30_30,
    WALL_FRAME_36_30, WALL_FRAME_30_20, WALL_FRAME_36_20, HIGH_FRAME_24_80, TOP_FRAME_30_20,
    *AXSTAD_DOORS, *AXSTAD_DRAWER_FRONTS, *MAXIMERA_MEDIUM, *VOXTORP_FRONTS,
    UTRUSTA_HINGE, UTRUSTA_HORIZONTAL_HINGE, UTRUSTA_CORNER_HINGES, UTRUSTA_CAROUSEL,
    SEKTION_LEG, FORBATTRA_TOE_KICK, *UTRUSTA_SHELVES,
    REV_A_SHELF_SWING_OUT, AXILO_LEVELER,
)
