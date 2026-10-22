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

from typehaus.model import FixtureType, Footprint2D, Mount, MountKind, Service, ft, inch, m, pt
from typehaus.model.placeable_symbols.plumbing import NEO_ANGLE_CUT_FRACTION, neo_angle_points

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
    "ports": tuple(port.model_copy(update={
        "position": (port.position[0], inch(12.875), port.position[2]),
    }) for port in TOILET_WALL_HUNG.ports),
    "source": 'TOTO SS-02352 v.01 p.2, read 2026-10-21: CT426CFGT40#01 AP '
              'wall-hung bowl, 14 15/16 x 21 1/4 in., 16 1/8 in. rim installation shown, '
              '1.28/0.9 gpf. CWT4263446CMFG pairs it with WT173M DuoFit, '
              'SW3446#01 S5 and THU805 connection kit. Interior carrier wall only. '
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
    footprint=(inch(18.25), inch(30)),
    height=inch(28.25),
    plan_symbol="toilet",
    basin=False,
    product_ref="PROD-TOTO-CST614CEFGAT40",
    needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(water_closet_required_clearance(inch(30)),),
    source='TOTO Carlyle II CST614CEFGAT40#01, owner selection 2026-09-06. TOTO USA spec '
           'sheet read 2026-09-06: 30" L x 18 1/4" W x 28 1/4" H, 12" rough-in, 1.28 gpf '
           'Tornado Flush, CEFIONTECT, one-piece skirted. The AT40 suffix is WASHLET+ '
           'readiness — the concealed supply the S5 seat (PROD-TOTO-SW3446) uses — so this '
           'bowl needs a GFCI receptacle 6"-12" AFF, offset to the rear-left cord exit and '
           'clear of the tank, on a 20 A circuit that is NOT shared with the other washlet '
           'bath: an instant-heat seat draws 1.2-1.4 kW while heating.',
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
    source='TOTO Aquia IV CST446CEMGN#01, owner selection 2026-09-06. TOTO USA spec sheet '
           'read 2026-09-06: 27 9/16" D x 15 1/2" W x 29 1/8" H, rim 14 15/16", 12" '
           'rough-in, 1.28/0.9 gpf dual flush, CEFIONTECT, skirted trapway. ** THAT RIM '
           'HEIGHT IS REGULAR, NOT COMFORT/UNIVERSAL. ** If universal height is wanted in '
           'these two rooms it is a different suffix and must be confirmed with the '
           'supplier before ordering — it is the one open question on this fixture.',
)

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
    source='TOTO Drake CST776CEFG#01, owner selection 2026-09-06. Published dimensions read '
           '2026-09-06: 28 3/8" D x 17 3/16" W x 30 1/8" H, rim 16 1/8" (universal height), '
           '12" rough-in, 2 1/8" trapway, 1.28 gpf Tornado Flush, CEFIONTECT. Seat is the '
           'Kohler Cachet K-4636-0 (PROD-KOHLER-K-4636) on this and the Aquia IVs — '
           '** fit-check one against a TOTO rim before buying four **, because TOTO\'s '
           'elongated profile differs from Kohler\'s and a lip at the rear corners is '
           'exactly the crevice quick-release exists to remove.',
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
# stops short of the ceiling on purpose. There is no glass element in the engine, so this
# text and the prices.toml row carry the glass, as on FX-SHOWER-36-NEO-COMBO.
SHOWER_36_THERMO_COMBO = SHOWER.model_copy(update={
    "tag": "FX-SHOWER-36-THERMO-COMBO",
    "name": 'Shower, 36", thermostatic valve with a two-in-one rainshower combo',
    "product_ref": "PROD-DELTA-T17T",
    "source": 'RM-M-BATH2, owner selection 2026-10-12, replacing FX-SHOWER-36-DIVERTED. '
              'Delta MultiChoice R10000-UNBX rough (ASSE 1016) under a TempAssure 17T '
              'thermostatic trim (PROD-DELTA-T17T): separate temperature and volume, no '
              'diverter. Head: Moen Attract Magnetix 26008 rainshower combo, 1.75 gpm, ONE '
              'outlet. Base: a matching 36x36 compression-moulded solid-surface base '
              '(PROD-SOLID-SURFACE-SHOWER) under floor-to-ceiling panels (WP-M-BATH2-SURR). '
              'GLASS: on the tub (north) side, floor to ceiling on the W-M-TUBDK-S knee wall; on '
              'the front (west) a fixed panel and door to 7\'-6" (90"), leaving ~16" open '
              'under the 106" ceiling. No transom: that gap is the steam path to REG-M-EXH2, '
              'which sits just outside it (notes/bath2_shower.md). WET WALLS: behind every '
              'panel, floor to ceiling, glass-mat gypsum or cement backer, then a bonded '
              'liquid membrane (RedGard / Hydro Ban class) lapped OVER the base flange, then '
              'the panel bonded over that. Base flanged E/S/N, threshold W, fully bedded, no '
              'radiant cable under it. Mould-inhibiting 100% silicone at panel-to-base, the '
              'corner and the knee-wall cap; escutcheons sealed to the panel and the R10000 '
              'plaster guard set to the panel face. No niche, and no bottom track on the '
              'door: a sweep and drip rail.',
})

# RM-B-SAUNA's rinse and RM-A-STUBATH's guest shower. ** ONE OUTLET, ON PURPOSE. ** A
# two-in-one magnetic combo gives a handheld for cleaning off a plain single-function valve:
# no diverter, no second riser, no blocking. Spending ~$500 of valve and trim to put a
# separate handshower in a basement sauna rinse is bad value, and RM-A-STUBATH has a second
# reason to stay simple — see the freeze note below.
SHOWER_36_COMBO = SHOWER.model_copy(update={
    "tag": "FX-SHOWER-36-COMBO",
    "name": 'Shower, 36", pressure-balance valve with a two-in-one combo head',
    "product_ref": "PROD-MOEN-26010SRN",
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
    "tag": "FX-SHOWER-36-NEO-COMBO",
    "name": 'Shower, 36" neo-angle, pressure-balance valve with a two-in-one combo head',
    "plan_symbol": "shower-neo-angle",
    "footprint_shape": Footprint2D(points=tuple(
        pt(m(x), m(y)) for x, y in neo_angle_points(
            _NEO_SIZE[0].meters, _NEO_SIZE[1].meters,
            _NEO_SIZE[0].meters * NEO_ANGLE_CUT_FRACTION))),
    "source": 'RM-A-STUBATH, owner selection 2026-09-09, replacing the 36" square pan. Same '
              'Delta MultiChoice R10000-UNBX rough (ASSE 1016), same single-function trim, '
              'same Moen Engage Magnetix 26010SRN two-in-one head; what changes is the base '
              'and the enclosure. CLASS ALLOWANCE for the base and glass: a 36" x 36" '
              'neo-angle acrylic or solid-surface receptor with a three-panel pivot '
              'enclosure (DreamLine Prism / Kohler Purist class). ** THE 16" CORNER CUT IS '
              'THE SPECIFICATION AND IT IS NOT UNIVERSAL: ** confirm the ordered base before '
              'the enclosure is bought, because a deeper cut takes the P2708.1 circle under '
              '30". The freeze note on SHOWER_36_COMBO applies unchanged — every supply and '
              'this valve stay on an interior partition inside the thermal envelope. WET '
              'WALLS: glass-mat gypsum or cement backer behind WP-A-STUBATH-SURR, then a '
              'bonded liquid membrane (RedGard / Hydro Ban class) lapped over the base '
              'flange, then the panel; silicone at every panel joint and escutcheon.',
})

# RM-S-BATH1 and RM-S-SUITEBATH. The two 60" combos, and the two places a handshower earns
# its diverter outright: bathing children, rinsing hair over the rim, rinsing the tub itself.
# Slide bar in one, wall elbow and hook in the other — same valve either way.
#
# ** SURROUND: INTEGRAL, SO NO `WallPaneling`. ** Both are flanged inserts whose walls come
# with the unit (one-piece, or the 3-piece kit a second floor takes), and the FX-TUBSHOWER-60
# price basis already buys and hangs them. The type's 7'-0" height is that surround's head;
# the flanges nail to the two framed walls plus each alcove's millwork return
# (FT-BATH1-SHELF-2030, FT-SUITEBATH-SHELF-1130). A panel over it would bill the walls twice.
# Of the five showers: BATH2 and STUBATH carry a modelled panel (WP-M-BATH2-SURR,
# WP-A-STUBATH-SURR), the sauna a tile splash (WP-B-SAUNA-SPLASH), these two are integral.
TUBSHOWER_60_DIVERTED = TUB_SHOWER.model_copy(update={
    "tag": "FX-TUBSHOWER-60-DIVERTED",
    "name": 'Alcove tub-shower, 60", complete trim with diverter and handshower',
    "product_ref": "PROD-DELTA-T14459-SS",
    "source": 'RM-S-BATH1 and RM-S-SUITEBATH, owner selection 2026-09-06. Delta MultiChoice '
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
              'PENETRATES THE INTEGRAL INSERT ** except the valve and spout knockouts: no '
              'niche, no grab-bar screw, no accessory. Use the moulded shelves; a hole in a '
              'one-piece insert has nothing behind it to lap to.',
})

WC_AND_SHOWER_TYPES = (
    TOTO_AP_WALL_HUNG, TOTO_CARLYLE_II, TOTO_AQUIA_IV, TOTO_DRAKE,
    SHOWER_36_THERMO_COMBO, SHOWER_36_COMBO, SHOWER_36_NEO_COMBO, TUBSHOWER_60_DIVERTED,
)
