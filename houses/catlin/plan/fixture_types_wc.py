"""Catlin water closets and showering fixtures — the chosen products (→ plan/fixture_types.py).

A second file beside ``fixture_types.py`` for the 500-line rule in ``AGENTS.md``, split where
the subject splits: that file is the vanities, this one is everything the plumber roughs into
a wet wall. Same contract — NOT ``# haus: editable`` (catalog definitions, and ``needs`` is a
``frozenset``), identity by ``product_ref`` into ``plan/products_interior.py``, money in
``prices.toml``, argument in ``notes/interior_selections.md``.

** THE WHOLE SHOWERING SECTION TURNS ON ONE FACT, SO IT IS STATED ONCE HERE. ** Minn. R.
4714.0408 amends only UPC 408.7 (receptor lining and pitch) and leaves **408.3 intact**, so
every shower and tub-shower needs an individual **ASSE 1016** compensating valve at the point
of use — a master ASSE 1017 valve at the water heater does not eliminate it, and DLI's own
interpretation says so. Minn. R. 4714.0301 then requires the manufacturer's mark **cast or
stamped on the part**: *"field markings shall not be acceptable."* A certificate PDF cannot
cure a missing mark. That is why the rough-in valve is the one item in this house that is
bought domestically without argument, and why "cUPC certified" on an import listing is not
the same claim — that phrase almost always means ASME A112.18.1 + NSF 372, which are the
cheap common listings, not ASSE 1016.
"""

from __future__ import annotations

from library.placeables.fixtures import (
    SHOWER,
    TOILET_WALL_HUNG,
    TUB_SHOWER,
    water_closet_required_clearance,
)

from plan.shower_assemblies import (ATTIC_SHOWER, BATH2_SHOWER_ASSEMBLY, SAUNA_SHOWER,
                                   TUB_SHOWER_ASSEMBLY)
from plan.wet_ports import floor_drain_port, floor_wc_ports
from typehaus.model import (
    FixtureType,
    Footprint2D,
    Mount,
    MountKind,
    PortCertainty,
    Service,
    ServicePort,
    ft,
    inch,
    m,
    pt,
)
from typehaus.model.placeable_symbols._swanstone_flex_config import BATH2_SHOWER
from typehaus.model.placeable_symbols.plumbing import NEO_ANGLE_CUT_FRACTION, neo_angle_points
from typehaus.model.placeables import ModelRepresentation

# ---------------------------------------------------------------------------
# WATER CLOSETS
# ---------------------------------------------------------------------------
#
# Six bowls, four models. The split is deliberate: wall-hung + skirted + rimless is the
# cleanability ceiling and it is bought where it is seen, and the attic guest bath and the
# basement sauna rinse take the Drake — same Tornado Flush, same CeFiONtect glaze, half the
# money, and what it gives up is the skirt. All-Aquia-IV across the four workhorses is
# $2,152 against $1,598 for the split, and it would still leave two tank designs.
#
# ** THE FOOTPRINT IS THE CHINA, THE CLEARANCE IS THE CODE, AND THEY ARE SEPARATE. **
# ``water_closet_required_clearance`` draws UPC 402.5's 15"/24" envelope off the DEPTH
# alone, so the manufactured width below is a drawing dimension and changes no finding.

# AP/S5 drawing SS-02352 v.01: 14 15/16" wide, 21 1/4" projection. Preserve the
# carrier services' wall-relative setback when replacing the library's shorter bowl.
TOTO_AP_WALL_HUNG = TOILET_WALL_HUNG.model_copy(update={
    "tag": "FX-TOTO-AP-WH",
    "name": "AP wall-hung water closet on a DuoFit carrier",
    "product_ref": "PROD-TOTO-CT426CFGT40",
    "footprint": (inch(14.9375), inch(21.25)),
    "height": inch(13.125),
    "mount": Mount(kind=MountKind.WALL, elevation=inch(3)),
    "clearances": (water_closet_required_clearance(inch(21.25)),),
    # z is from the bowl base, 3" over the finished floor, so the deck crossing is -3".
    # The drop rides W-M-HS1's axis (house setout: SS-02352 dimensions no outlet).
    "ports": (
        ServicePort(tag="waste", service=Service.DRAIN,
                    position=(inch(0), inch(13.875), inch(-3)), connection_size=inch(3),
                    direction=(0, 0, -1), certainty=PortCertainty.EXACT,
                    notes="Carrier drop on the wet-wall axis, crossing the finished floor"),
        ServicePort(tag="vent", service=Service.VENT,
                    position=(inch(0), inch(13.875), inch(1)), connection_size=inch(2),
                    notes="2\" vent takeoff on the carrier waste fitting"),
        ServicePort(tag="cold", service=Service.WATER_COLD,
                    position=(inch(-8.8), inch(13.875), inch(8.75)), connection_size=inch(0.5),
                    notes="WT173M 1/2\" NPT inlet, lower left of the frame. z is published: "
                          "7/8\" below D, 11 3/4\" AFF at this rim (0GU190 p.4); x and y are "
                          "scaled, so the port stays approximate"),
    ),
    "source": 'TOTO SS-02352 v.01 p.2, read 2026-10-21: CT426CFGT40#01 AP '
              'wall-hung bowl, 14 15/16 x 21 1/4 in., 16 1/8 in. rim installation shown, '
              '1.28/0.9 gpf. CWT4263446CMFG pairs it with WT173M DuoFit, '
              'SW3446#01 S5 and THU805 connection kit. Interior carrier wall only. '
              'Supply height: TOTO WT173M Installation & Owner\'s Manual 0GU190 p.4 '
              '(Before Installation + Table 1), read 2026-11-07: 1/2 in. NPT supply 7/8 in. '
              'below the D line, D = 12 5/8 in. at the 16 1/8 in. rim, so 11 3/4 in. AFF; x/y '
              'undimensioned. https://www.totousa.com/filemanager_uploads/product_assets/'
              'InstallationManual/0GU190_WT173M_IM.pdf. '
              'Replaces SP CT449CFGT60 (22 7/8 in. overall, SS-01776 p.2). '
              'https://www.totousa.com/filemanager_uploads/product_assets/SpecSheet/'
              'SS-02352_CWT4263446CMFG.pdf',
})

# RM-M-BATH2, the second showpiece. One-piece skirted: no tank-to-bowl gasket line, no gap
# behind the tank, and a skirt that closes the trapway's washboard. 30" is the deepest bowl
# in the house and the clearance envelope grows with it — checked against the room.
TOTO_CARLYLE_II = FixtureType(
    tag="FX-TOTO-CARLYLE-II",
    name="Carlyle II one-piece skirted water closet",
    footprint=(inch(16.5), inch(28.3125)),
    height=inch(28.75),
    plan_symbol="toilet",
    basin=False,
    product_ref="PROD-TOTO-CST614CEFGAT40",
    needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(water_closet_required_clearance(inch(28.3125)),),
    # SS-02299 v.01 p.2: tank 3/4" [18 mm] off the finished wall, flange at 12". Its one
    # placement backs the DuoFit carrier wall (W-M-HS1), whose frame fills the bay, so the
    # stop is floor-fed: PR-B-BATH2-WC-CW rises 1.14" off the wall at TOTO's 6" / 8".
    ports=floor_wc_ports(28.3125, 0.75, source="TOTO SS-02299 v.01 p.2",
                         floor_stop=(6.0, 1.14, 8.0)),
    source='TOTO Carlyle II CST614CEFGAT40#01, owner selection 2026-09-06. 28 5/16" D x '
           '16 1/2" W x 28 3/4" H (TOTO SS-01809, same bowl/tank as MS614124CEF(R)G; '
           'Ferguson CST614CEFGAT40 listing, 2026-10-31), 12" rough-in, 1.28 gpf '
           'Tornado Flush, CEFIONTECT, one-piece skirted. The AT40 suffix is WASHLET+ '
           'readiness — the concealed supply the S5 seat (PROD-TOTO-SW3446) uses — so this '
           'bowl needs a GFCI receptacle 6"-12" AFF, offset to the rear-left cord exit and '
           'clear of the tank, on a 20 A circuit that is NOT shared with the other washlet '
           'bath: an instant-heat seat draws 1.2-1.4 kW while heating. Stop station: TOTO '
           'SS-02299 v.01 p.2 (MW6143446CEFG, names CST614CEFGAT40), read 2026-11-07: '
           '*6 in. left, *8 in. AFF, "Suggested Dimension / Supply as Req\'d" — a wall '
           'supply; this bowl is floor-fed, its stop set by the plumber clear of the china. '
           'https://www.totousa.com/filemanager_uploads/product_assets/SpecSheet/'
           'SS-02299_MW6143446CEFG.pdf',
)

# RM-S-BATH1 and RM-S-SUITEBATH. Skirted, so the trapway washboard is closed, but two-piece
# and without the showpieces' bidet readiness — the two upstairs baths are used daily and
# are not the ones guests see.
TOTO_AQUIA_IV = FixtureType(
    tag="FX-TOTO-AQUIA-IV",
    name="Aquia IV skirted dual-flush water closet",
    footprint=(inch(15.5), inch(27.5625)),
    height=inch(29.125),
    plan_symbol="toilet",
    basin=False,
    product_ref="PROD-TOTO-CST446CEMGN",
    needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(water_closet_required_clearance(inch(27.5625)),),
    # SS-02072 v.02 p.2: tank 3/4" [20 mm] off the finished wall, flange at 12"; it suggests
    # the stop at 4 3/4" AFF ("as req'd"), and 7" clears the 3 1/2" base.
    ports=floor_wc_ports(27.5625, 0.75, wall_stop=(5.875, 7.0),
                         source='TOTO SS-02072 v.02 p.2 x; z kept at 7" over its suggested 4 3/4"',
                         stop_note=' Use a 90-degree angle stop; max protrusion with the '
                                   'shutoff 3 1/8" [80 mm] off the finished wall (same page).'),
    source='TOTO Aquia IV CST446CEMGN#01, owner selection 2026-09-06. TOTO USA spec sheet '
           'read 2026-09-06: 27 9/16" D x 15 1/2" W x 29 1/8" H, rim 14 15/16", 12" '
           'rough-in, 1.28/0.9 gpf dual flush, CEFIONTECT, skirted trapway. ** THAT RIM '
           'HEIGHT IS REGULAR, NOT COMFORT/UNIVERSAL. ** If universal height is wanted in '
           'these two rooms it is a different suffix and must be confirmed with the '
           'supplier before ordering — it is the one open question on this fixture. Stop '
           'station: TOTO SS-02072 v.02 p.2, read 2026-11-07: *5 7/8 in. left, *4 3/4 in. '
           'AFF suggested; 90-degree angle stop required; max protrusion with shutoff 3 1/8 '
           'in. [80 mm]. https://www.totousa.com/filemanager_uploads/product_assets/SpecSheet/'
           'SS-02072_CST446CEMGN.pdf',
)
# RM-S-BATH1's Aquia backs exterior W-S-W1, which nothing enters (owner 2026-10-31), so its
# stop is floor-fed: PR-S-BATH1-WC-CW rises 1 1/4" off the wall, clear of the base, and
# 10 1/2" left of centre, clear of the 15 1/2" china. Same product; only the stop differs.
TOTO_AQUIA_IV_FLOOR = TOTO_AQUIA_IV.model_copy(update={
    "tag": "FX-TOTO-AQUIA-IV-FLOOR",
    "name": "Aquia IV skirted dual-flush water closet, floor-fed stop",
    "ports": floor_wc_ports(27.5625, 0.75, source="TOTO SS-02072 v.02 p.2",
                            floor_stop=(10.5, 1.25, 7.0),
                            stop_note=" Use a 90-degree angle stop (same page)."),
    "source": TOTO_AQUIA_IV.source + ' FLOOR-FED VARIANT: SS-02072\'s stop station is a wall '
              'supply\'s; a floor-fed stop is set by the plumber clear of the china.',
})

# RM-A-STUBATH and RM-B-BATH. The workhorse: same flush and same glaze as the showpieces,
# an exposed trapway instead of a skirt, and half the price. A skirt does not earn its keep
# in an attic guest bath used a few weeks a year or in a basement sauna rinse.
TOTO_DRAKE = FixtureType(
    tag="FX-TOTO-DRAKE",
    name="Drake two-piece elongated water closet",
    footprint=(inch(17.1875), inch(28.375)),
    height=inch(30.125),
    plan_symbol="toilet",
    basin=False,
    product_ref="PROD-TOTO-CST776CEFG",
    needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(water_closet_required_clearance(inch(28.375)),),
    # SS-02049 v.04 p.2: tank 13/16" [20 mm] off the finished wall, flange at 12".
    ports=floor_wc_ports(28.375, 0.8125, wall_stop=(4.3125, 7.5),
                         source="TOTO SS-02049 v.04 p.2 suggested"),
    source='TOTO Drake CST776CEFG#01, owner selection 2026-09-06. Published dimensions read '
           '2026-09-06: 28 3/8" D x 17 3/16" W x 30 1/8" H, rim 16 1/8" (universal height), '
           '12" rough-in, 2 1/8" trapway, 1.28 gpf Tornado Flush, CEFIONTECT. Seat is the '
           'Kohler Cachet K-4636-0 (PROD-KOHLER-K-4636) on this and the Aquia IVs — '
           '** fit-check one against a TOTO rim before buying four **, because TOTO\'s '
           'elongated profile differs from Kohler\'s and a lip at the rear corners is '
           'exactly the crevice quick-release exists to remove. Stop station: TOTO SS-02049 '
           'v.04 p.2, read 2026-11-07: *4 5/16 in. left, *7 1/2 in. AFF suggested, "Supply '
           'as Req\'d". https://www.totousa.com/filemanager_uploads/product_assets/SpecSheet/SS-02049_CST776CEF(R)(G).pdf',
)

# ---------------------------------------------------------------------------
# SHOWERING
# ---------------------------------------------------------------------------
#
# ** ONE ROUGH-IN PART IN ALL FIVE WET WALLS. ** Delta's MultiChoice R10000-UNBX accepts a
# single, dual, or dual THERMOSTATIC cartridge — the cartridge lives in the trim — so the
# pressure-balance-versus-thermostatic choice stays reversible from outside the tile in 2041.
# Moen makes you commit at rough-in across three different bodies; Kohler's Rite-Temp is
# pressure-balance only. Pressure balance stays the default: a PB spool is nearly inert where
# a thermostatic element drifts and fails, and the three low-use or tub showers gain nothing.
#
# ** BATH2 IS THE EXCEPTION, AND THE REASON IS THE TANK, NOT THE OUTLET COUNT ** (2026-10-12).
# A PB valve holds the hot-to-cold RATIO, so as the 80-gal heat-pump tank (EQ-B-WH) cools late
# in a long shower, the head cools with it. A thermostatic valve re-mixes to hold the set
# temperature, and the 17T adds a separate volume control. That is the daily, long shower.
# notes/bath2_shower.md has the hand calc (~40 min of 105 F from one tank).
#
# ** EVERY HEAD IS <= 1.75 GPM ** (house standard, 2026-10-12): 26008 and 26010SRN at 1.75,
# 52535-SS at 1.75 in the tub-showers. The ratings live on the product records.
#
# ** A HANDSHOWER IS A SECOND OUTLET AND THEREFORE A DIVERTER AND A SECOND RISER — and that
# is true whether it hangs on a slide bar or on a wall elbow with a hook. ** Swapping the bar
# for a hook saves the blocking, not the valve. Only a true two-in-one magnetic combo head is
# one outlet, which is why the three stall showers take one and the two tubs do not.
#
# ** BLOCKING IS THE ONLY IRREVERSIBLE ITEM IN THIS FILE, AND IT IS MODELLED. ** Every band
# is a `WallBacking` in `plan/backing.py` / `plan/backing_wet.py`, so it reaches the framer
# on the S-sheets and the lumber yard through the takeoff. Since 2026-10-10 it follows a
# designated body: a grab-bar course (2x8, 32"-39 1/4") only where a tub, shower or WC
# stands, and mirror/cabinet courses only behind a modelled mirror or cabinet. The old
# "block every wet wall where a screw might land" policy is retired (DESIGN-LOG.md,
# `notes/wall_backing.md` §4). Without grab-bar backing everyone grabs the bar anyway,
# toggles in cement board work loose, and water wicks down the anchor holes into the stud
# bay as a concealed leak; retrofit after tile is $1,500-4,000. The drop elbow, valve, tub
# spout and shower arm are the plumber's rough-in blocking, set in the same pass. Tub spouts
# are specified THREADED (IPS), never slip-fit: a slip-fit spout seals on an O-ring over a
# bare copper stub and when it ages the leak is behind the tile.

# RM-M-BATH2's 36" shower — the primary, used daily and long. Thermostatic trim on the same
# R10000 rough, one magnetic combo outlet (the diverter rough, second riser and slide bar of
# FX-SHOWER-36-DIVERTED are gone, 2026-10-12), solid-surface walls and base, and glass that
# stops short of the ceiling on purpose. The generated model carries the stock Flex
# front and the stock clipped return (2026-11-05); the post detail remains open.
SHOWER_36_THERMO_COMBO = SHOWER.model_copy(update={
    "shower_assembly": BATH2_SHOWER_ASSEMBLY,
    "excludes_floor_finish": True,
    "tag": "FX-SHOWER-36-THERMO-COMBO",
    "height": inch(BATH2_SHOWER.model_height),
    "flood_rim_height": inch(4.5),  # the base's threshold
    "model_representation": ModelRepresentation(
        symbol="swanstone-flex-3636", material_refs={"solid-surface": "solid-surface-base"}),
    "name": 'Shower, 36", thermostatic valve with a two-in-one rainshower combo',
    "product_ref": "PROD-DELTA-T17T",
    # Swan form 200-06-10 p.12: pipe centered in the molded drain, top 1/4" below subfloor.
    # Keep approximate until the delivered base is measured; the valve hubs remain estimated.
    "ports": (floor_drain_port(0, 0, -0.25, note="SS-3636 molded centre drain; Fit-Flo 2 in. "
                               "pipe top 1/4 in. below subfloor (Swan form 200-06-10 p.12); "
                               "verify delivered base before cutting"),
              *BATH2_SHOWER_ASSEMBLY.inlet_ports()),
    "source": 'RM-M-BATH2, owner selection 2026-10-12, replacing FX-SHOWER-36-DIVERTED. '
              'Delta MultiChoice R10000-UNBX rough (ASSE 1016) under a Trinsic T17T059 17T '
              'thermostatic trim (PROD-DELTA-T17T): separate temperature and volume, no '
              'diverter. Head: Moen Attract Magnetix 26008 rainshower combo, 1.75 gpm, ONE '
              'outlet. Base: a Swanstone SS-3636 36x36 centre-drain solid-surface base '
              '(PROD-SOLID-SURFACE-SHOWER) under floor-to-ceiling Modern Subway panels '
              '(WP-M-BATH2-SURR), White (.010), owner 2026-10-29. '
              'GLASS: on the tub (north) side, a STOCK 32 x 80 in. 3/8 in. clear frameless '
              'fixed panel, chrome clips (owner 2026-11-05), on 1/4 in. setting blocks on the '
              'Corian deck\'s S leg over W-M-TUBDK-S, top at 103 in., 3 in. open to the '
              'ceiling; deck top sloped >= 1/4 in. into the stall, no joint under the glass '
              '(notes/bath2_tub_deck_finish.md); on '
              'the front (west), DreamLine Flex SHDR-22327200-01, chrome, 32-36 in. opening, '
              '72 in. above the 4 1/2 in. threshold, with supplied rails, seals and south-side '
              'pivot. PROD-DREAMLINE-FLEX-3272. The north post is a 1 1/2 x 2 1/2 in. aluminium '
              'tube, deck to ceiling backing; its inside face forms the north jamb, its depth '
              'takes up the 36 in. pan the 32 in. panel does not, and the panel clips to it '
              'and the east wall. Buy the panel first and cut the post to its actual glass '
              'width. DreamLine confirms the door-to-post mounting. Base bears on the 3/4 in. subfloor without '
              'room tile beneath it. Front rail top 77 1/4 in. above storey datum, '
              'leaving 28 3/4 in. open to the ceiling. No transom: the gap leads to REG-M-EXH2, '
              'which sits just outside it (notes/bath2_shower.md). WET WALLS: behind every '
              'panel, floor to ceiling, primed glass-mat gypsum or cement backer over the '
              'base flange, then the panel siliconed and taped to it per Swan\'s guide; no '
              'liquid membrane (owner 2026-11-05). Base flanged E/S/N, threshold W, fully bedded, no '
              'radiant cable under it. Mould-inhibiting 100% silicone at panel-to-base, the '
              'corner and the Corian stall face; escutcheons sealed to the panel and the R10000 '
              'plaster guard set to the panel face. No niche. The stock Flex bottom rail '
              'supersedes the earlier trackless-door preference. Molded pan drain and pipe '
              'are centered; FS-M-WEST moves joist 011 to y=170 in. and adds y=186 in., '
              'retaining full-span joists and <=16 in. spacing (bath2_shower.md).',
})

# RM-B-SAUNA's rinse and RM-A-STUBATH's guest shower. ** ONE OUTLET, ON PURPOSE. ** A
# two-in-one magnetic combo gives a handheld for cleaning off a plain single-function valve:
# no diverter, no second riser, no blocking. Spending ~$500 of valve and trim to put a
# separate handshower in a basement sauna rinse is bad value, and RM-A-STUBATH has a second
# reason to stay simple — see the freeze note below.
SHOWER_36_COMBO = SHOWER.model_copy(update={
    "shower_assembly": SAUNA_SHOWER,
    "excludes_floor_finish": True,
    "tag": "FX-SHOWER-36-COMBO",
    # No base SKU: the threshold, at P2709.1's 9" most over the drain.
    "flood_rim_height": inch(9),
    "name": 'Shower, 36", pressure-balance valve with a two-in-one combo head',
    "product_ref": "PROD-MOEN-26010SRN",
    # RM-B-SAUNA only (the attic took the neo-angle type): pan drain at its centre on the
    # liner's 2" build-up, valve in W-B-CS east of the pan.
    "ports": (floor_drain_port(0, 0, 2, note="Curbed liner pan, no base SKU; centre drain"),
              *SAUNA_SHOWER.inlet_ports()),
    "source": 'RM-B-SAUNA and RM-A-STUBATH, owner selection 2026-09-06. Delta MultiChoice '
              'R10000-UNBX rough (ASSE 1016), single-function trim, and a Moen Engage '
              'Magnetix 26010SRN two-in-one head — ONE outlet, so no diverter and no second '
              'riser. ** RM-A-STUBATH IS THE HIGHEST-CONSEQUENCE ROUGH-IN IN THE HOUSE: ** '
              'every supply line and this valve must stay inside the thermal envelope on an '
              'interior partition. A shower valve in a Minnesota attic wall is a burst '
              'waiting for a January vacation.',
})

# RM-A-STUBATH's shower as built, and the reason it is not the plain 36" square above.
#
# ** THE CUT CORNER IS THE WHOLE POINT. ** The pan sits in the room's NE corner and the bath
# door is in the south wall opposite it, so the pan's SW corner is the thing a person walks
# into on the way in. A square 36" pan leaves 19 1/4" between its south face and the wall you
# enter through, across the full width of the door. Cutting that corner back 16" on each leg
# opens the diagonal: at the door's east jamb there are 20 3/8", at x=15'-0" there are
# 31 7/8", and the shower's own entrance — which now faces SW into the middle of the room
# rather than south at the door — has 38 1/2" in front of it instead of 19 1/4". That is the
# clearance IPC 405.3.1 and UPC 402.5 ask for at a shower entrance; the IRC, which is what
# actually governs this house, asks for none, so this is comfort bought deliberately.
# ** SINCE 2026-11-01 THE DOOR IS ONE MODULE EAST ** (RO 15'-3 1/2"..17'-5 3/4", for the roof,
# storeys/attic_studio.py): it now enters opposite the pan's flat south face, 18 3/8" off the
# wall face over most of its width and 27 1/2" at its west jamb, and swings out. The pan's
# own SW-facing entrance keeps its 38 1/2".
#
# ** IT STILL PASSES IRC P2708.1, AND THAT IS ARITHMETIC, NOT A PRODUCT CLAIM. ** P2708.1
# wants 900 sq in of interior area and a 30" minimum finished dimension, i.e. a 30" circle
# inscribed at the top of the threshold. For a corner pan of leg L with a 45 degree cut of
# `a` per leg, the inscribed circle has diameter 2(L + (L - a)) / (2 + sqrt 2) and the area is
# L^2 - a^2/2. Taken on the FINISHED interior — 34" legs inside a 36" base, a=16" — that is a
# ** 30 1/2" circle and 1,028 sq in **, both over. It is not over by much: the margin is half
# an inch, so ** confirm the ordered base's published door opening is 22 5/8" or less ** (16"
# of cut per leg is 16 x sqrt 2). A 38" base restores the margin and gives back 2" of the
# room, which is the trade this pan exists to avoid.
#
# ** THE PENTAGON IS THE PLAN OUTLINE, AND SINCE 2026-09-09 IT IS ALSO THE DRAWING. ** The
# type names `plan_symbol="shower-neo-angle"`, so the glyph on every sheet and the massing in
# the viewer and the .glb are the five-sided pan, not its 36" bounding box; `footprint_shape`
# comes off `neo_angle_points`, the same function the symbol draws from, so the outline the
# resolver collides against and the outline a person sees cannot drift. Local +y is the
# object's BACK, so the ring puts the wall corner at (+18, +18) and cuts the (-18, -18)
# corner; the fixture is authored with no rotation, which lands that corner in the room's NE.
#
# Valve, trim and head are SHOWER_36_COMBO's unchanged — one outlet, one magnetic combo head,
# and the same ASSE 1016 rough this file's header argument applies to every shower here.
_NEO_SIZE = (ft(3), ft(3))
SHOWER_36_NEO_COMBO = SHOWER_36_COMBO.model_copy(update={
    "shower_assembly": ATTIC_SHOWER,
    "tag": "FX-SHOWER-36-NEO-COMBO",
    "name": 'Shower, 36" neo-angle, pressure-balance valve with a two-in-one combo head',
    "plan_symbol": "shower-neo-angle",
    "ports": (floor_drain_port(0, 0, note="Class-allowance base: drain centre vs corner offset "
                               "varies by maker; confirm on the ordered base"),
              *ATTIC_SHOWER.inlet_ports()),
    "footprint_shape": Footprint2D(points=tuple(
        pt(m(x), m(y)) for x, y in neo_angle_points(
            _NEO_SIZE[0].meters, _NEO_SIZE[1].meters,
            _NEO_SIZE[0].meters * NEO_ANGLE_CUT_FRACTION))),
    "source": 'RM-A-STUBATH, owner selection 2026-09-09, replacing the 36" square pan. Same '
              'Delta MultiChoice R10000-UNBX rough (ASSE 1016), same single-function trim, '
              'same Moen Engage Magnetix 26010SRN two-in-one head; what changes is the base '
              'and the enclosure. BASE AND WALLS (owner 2026-11-05): DreamLine DL-6040C-01, '
              'a SlimLine 36" x 36" neo-angle acrylic base with QWALL-2 two-piece white '
              'acrylic/ABS corner backwalls (WP-A-STUBATH-SURR). GLASS: class allowance for '
              'a matching three-panel neo-angle pivot enclosure (DreamLine Prism class). ** '
              'THE 16" CORNER CUT IS THE SPECIFICATION AND IT IS NOT UNIVERSAL: ** confirm '
              'the SlimLine base\'s cut and its drain position before the enclosure is '
              'bought, because a deeper cut takes the P2708.1 circle under 30". The freeze '
              'note on SHOWER_36_COMBO applies unchanged — every supply and this valve stay '
              'on an interior partition inside the thermal envelope. WET WALLS: base flange '
              'to the studs, greenboard or cement board over it, QWALL-2 panels glued to '
              'that per DreamLine; no liquid membrane. Silicone at the panel-to-base joint, '
              'the corner and every escutcheon.',
})

# RM-S-BATH1 and RM-S-SUITEBATH. The two 60" combos, and the two places a handshower earns
# its diverter outright: bathing children, rinsing hair over the rim, rinsing the tub itself.
# Slide bar in one, wall elbow and hook in the other — same valve either way.
#
# ** SURROUND: INTEGRAL, SO NO `WallPaneling`. ** Both are flanged inserts whose walls come
# with the unit, and the FX-TUBSHOWER-60
# price basis already buys and hangs them. The insert is a 4-piece Sterling Ensemble Medley
# 71370116: 73" finished, flange top 74 1/4" (2026-11-06). The flanges nail to the two
# framed walls plus each alcove's millwork return
# (FT-BATH1-SHELF-1630, FT-SUITEBATH-SHELF-0730). A panel over it would bill the walls twice.
# Of the five showers: BATH2 and STUBATH carry a modelled panel (WP-M-BATH2-SURR,
# WP-A-STUBATH-SURR), the sauna a tile splash (WP-B-SAUNA-SPLASH), these two are integral.
TUBSHOWER_60_DIVERTED = TUB_SHOWER.model_copy(update={
    "shower_assembly": TUB_SHOWER_ASSEMBLY,
    "excludes_floor_finish": True,
    "tag": "FX-TUBSHOWER-60-DIVERTED",
    "name": 'Alcove tub-shower, 60", complete trim with diverter and handshower',
    "height": inch(73),  # 71370116 finished height; the flange tops at 74 1/4"
    "product_ref": "PROD-DELTA-T14459-SS",
    # Plumbing end at local -x. The drain is the sheet's 8 1/4" off the end studs (the one-piece
    # 60x30 standard is 8 to 8 1/2": Aquatic, Florestone, Maax). Each plumbing end is a
    # deepened stud wall that carries the drain off the framing: notes/framing_bore_limits.md §12.
    "ports": (floor_drain_port(-21.75, 0, size_in=1.5, note="Waste-and-overflow 8 1/4\" off the "
                               "end studs (1214192-4-A p.2): confirm on the delivered bath"),
              *TUB_SHOWER_ASSEMBLY.inlet_ports()),
    "source": 'RM-S-BATH1 and RM-S-SUITEBATH, owner selection 2026-09-06. INSERT: Sterling '
              'Ensemble 30" bath and Medley wall surround with backer boards, left drain, '
              '71370116-0, Sterling spec sheet '
              '1214192-4-A p.1-2: 60 x 30 1/8 x 73 in. finished, 60 1/4 x 31 1/4 x 74 1/4 in. '
              'rough-in including the flange, 16 in. to the threshold, 4-piece modular. '
              'Delta MultiChoice '
              'R10000-UNBX rough (ASSE 1016) under a Delta T14459-SS COMPLETE trim — valve '
              'trim, H2Okinetic showerhead and tub spout in one box, which removes the '
              'spout-matching problem — plus a diverter rough and a second riser for the '
              'handshower. HEAD: the boxed head is swapped for a Delta 52535-SS 5-setting '
              '(1.75 gpm, 2026-10-12) to hold the house\'s 1.75 gpm standard. '
              'H2Okinetic Touch-Clean: soft rubber spray holes, so calcium wipes off with a '
              'thumb and there is nothing to soak. ** CONFIRM THE -SS FINISH IS IN STOCK '
              'BEFORE THE PLUMBER ORDERS: ** Delta is thinning its stainless SHOWERING line '
              'hard and several sibling SKUs came back discontinued. If it has gone, the '
              'substitute is Moen Spot Resist Brushed Nickel throughout — mixing Delta '
              'SpotShield BN and Moen Spot Resist BN across rooms is fine, mixing them in '
              'the SAME room is not, they are visibly different tones. ** NOTHING '
              'PENETRATES THE INTEGRAL INSERT ** except coordinated plumbing knockouts: no '
              'niche, no grab-bar screw, no accessory. Use the moulded shelves; a hole in a '
              'one-piece insert has nothing behind it to lap to.',
})

WC_AND_SHOWER_TYPES = (
    TOTO_AP_WALL_HUNG, TOTO_CARLYLE_II, TOTO_AQUIA_IV, TOTO_AQUIA_IV_FLOOR, TOTO_DRAKE,
    SHOWER_36_THERMO_COMBO, SHOWER_36_COMBO, SHOWER_36_NEO_COMBO, TUBSHOWER_60_DIVERTED,
)
