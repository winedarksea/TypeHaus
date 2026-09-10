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
    _water_closet_required_clearance,
)

from typehaus.model import FixtureType, Footprint2D, Service, ft, inch, m, pt
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
# ``_water_closet_required_clearance`` draws UPC 402.5's 15"/24" envelope off the DEPTH
# alone, so the manufactured width below is a drawing dimension and changes no finding.

# RM-M-BATH1. ** Built by copying the library type rather than by re-declaring it, and that
# is deliberate: ** FX-TOILET-WH's ports, its 1 3/8" mount and its 19 3/4" ``carrier_bay_width``
# are carefully authored against the carrier frame, and ``resolve/framing/carriers.py`` turns
# that last number into a stud keepout. Re-typing them by hand here would let the two drift.
# The SP's china is 15" wide, which is the library figure exactly; its projection was NOT
# confirmable from a spec sheet, so 19.3" stands and is flagged rather than invented.
TOTO_SP_WALL_HUNG = TOILET_WALL_HUNG.model_copy(update={
    "tag": "FX-TOTO-SP-WH",
    "name": "SP wall-hung water closet on a DuoFit carrier",
    "product_ref": "PROD-TOTO-CT449CFGT60",
    "source": 'TOTO SP CT449CFGT60#01 bowl on a TOTO DuoFit WT173M in-wall tank '
              '(PROD-TOTO-CT449CFGT60 + PROD-TOTO-WT173M), owner selection 2026-09-06. '
              '15" china (confirmed), 16 1/8" rim, 19 3/8" rough-in, 1.28/0.9 gpf dual '
              'flush, CEFIONTECT. ** PROJECTION NOT CONFIRMED FROM A SPEC SHEET: ** the '
              '19.3" depth is the library allowance\'s figure, carried unchanged, and the '
              'clearance envelope is drawn off it. Confirm before the carrier is set. '
              '** THE CARRIER MUST BE ON AN INTERIOR PARTITION. ** A concealed cistern in a '
              'EXT_2X6 bay displaces insulation, sits outboard of the vapour control '
              'and puts standing water in the coldest part of a Minnesota wall. ** CARRIER '
              'DEPTH IS A DIFFERENT PART NUMBER, not an adjustment ** (Geberit 111.597.00.1 '
              'for 2x4 against 111.902.00.5 for 2x6), and the wall carries an 880 lb point '
              'load, so the bay is a purpose-framed opening with a header and a sill. ** THE '
              'BIDET DECIDES THE CARRIER BRAND: ** a WASHLET+ routes its supply concealed '
              'through the bowl and only TOTO\'s own frame has that connection; buy Geberit '
              'and a braided hose crosses the finished tile forever.',
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
    product_ref="PROD-TOTO-CST614CEFGAT40",
    needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(_water_closet_required_clearance(inch(30)),),
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
    product_ref="PROD-TOTO-CST446CEMGN",
    needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(_water_closet_required_clearance(inch(27.5625)),),
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
    product_ref="PROD-TOTO-CST776CEFG",
    needs=frozenset({Service.WATER_COLD, Service.DRAIN, Service.VENT}),
    clearances=(_water_closet_required_clearance(inch(28.375)),),
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
# pressure-balance only. Pressure balance is what is actually bought in all four: every
# shower here is single-outlet (a tub-shower combo is a diverted single outlet), thermostatic
# earns its 3-5x only on multi-outlet showers, and a thermostatic element drifts and fails
# where a PB spool is nearly inert. The ~$1,500-2,000 saved covers the tub filler outright.
#
# ** A HANDSHOWER IS A SECOND OUTLET AND THEREFORE A DIVERTER AND A SECOND RISER — and that
# is true whether it hangs on a slide bar or on a wall elbow with a hook. ** Swapping the bar
# for a hook saves the blocking, not the valve. Only a true two-in-one magnetic combo head is
# one outlet, which is why the two low-use showers take one and the two tubs do not.
#
# ** BLOCKING IS THE ONLY IRREVERSIBLE ITEM IN THIS FILE, AND IT IS NOW MODELLED. ** As of
# 2026-09-09 every band below is a `WallBacking` in `plan/backing.py`, so it reaches the
# framer on the S-sheets and the lumber yard through the takeoff instead of living here as
# an instruction nobody downstream can read. `advisory.wall_backing_present` reports a
# wall-mounted body with nothing behind it, and `notes/wall_backing.md` carries the height
# schedule with its sources. One correction the modelling forced: the "about twelve
# dollars" below is right for the 12" strip this paragraph describes and wrong for the 48"
# band that actually covers the 40"-80" range in one piece, which is ~13 sheets of ply.
# The paragraph is kept verbatim because the REASONING in it is still the reasoning.
#
# ** BLOCKING IS THE ONLY IRREVERSIBLE ITEM IN THIS FILE. ** A 3/4" plywood strip, 12" wide,
# spanning two stud bays, ~40" to ~80" AFF, in ALL FIVE wet walls including the ones with no
# slide bar planned — blocking only where today's model's screws land pins the house to
# today's model forever, and a continuous band costs about twelve dollars. Block the drop
# elbow, the valve, the tub spout and the shower arm in the same pass, and ** put grab-bar
# backing at 33"-36" AFF **: without it everyone grabs the bar anyway, toggles in cement
# board work loose, and water wicks down the anchor holes into the stud bay as a concealed
# leak. Retrofit after tile is $1,500-4,000. Tub spouts are specified THREADED (IPS), never
# slip-fit: a slip-fit spout seals on an O-ring over a bare copper stub and when it ages the
# leak is behind the tile.

# RM-M-BATH2's 36" shower — the primary, and the one that gets the adjustable-height
# handshower, because adjustable height is the actual benefit and this is the shower used
# daily. Diverter rough stacks above the MultiChoice body.
SHOWER_36_DIVERTED = SHOWER.model_copy(update={
    "tag": "FX-SHOWER-36-DIVERTED",
    "name": 'Shower, 36", pressure-balance valve with diverter and slide bar',
    "product_ref": "PROD-DELTA-R10000-UNBX",
    "source": 'RM-M-BATH2, owner selection 2026-09-06. Delta MultiChoice R10000-UNBX rough '
              '(ASSE 1016) with a pressure-balance cartridge, PLUS a diverter rough and a '
              'second riser feeding a slide-bar handshower — two outlets, two-handle trim. '
              'Fixed head is Speakman S-2005-H-1 (PROD-SPEAKMAN-S-2005-H) at 2.5 gpm, which '
              'the 2018 UPC Table 403.1 allows and Minnesota does not amend down. Geometry '
              'is the library allowance\'s, unchanged; what this type carries is the valve.',
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
              'this valve stay on an interior partition inside the thermal envelope.',
})

# RM-S-BATH1 and RM-S-SUITEBATH. The two 60" combos, and the two places a handshower earns
# its diverter outright: bathing children, rinsing hair over the rim, rinsing the tub itself.
# Slide bar in one, wall elbow and hook in the other — same valve either way.
TUBSHOWER_60_DIVERTED = TUB_SHOWER.model_copy(update={
    "tag": "FX-TUBSHOWER-60-DIVERTED",
    "name": 'Alcove tub-shower, 60", complete trim with diverter and handshower',
    "product_ref": "PROD-DELTA-T14459-SS",
    "source": 'RM-S-BATH1 and RM-S-SUITEBATH, owner selection 2026-09-06. Delta MultiChoice '
              'R10000-UNBX rough (ASSE 1016) under a Delta T14459-SS COMPLETE trim — valve '
              'trim, H2Okinetic showerhead and tub spout in one box, which removes the '
              'spout-matching problem and means these two rooms need no separately specified '
              'head — plus a diverter rough and a second riser for the handshower. '
              'H2Okinetic Touch-Clean: soft rubber spray holes, so calcium wipes off with a '
              'thumb and there is nothing to soak. ** CONFIRM THE -SS FINISH IS IN STOCK '
              'BEFORE THE PLUMBER ORDERS: ** Delta is thinning its stainless SHOWERING line '
              'hard and several sibling SKUs came back discontinued. If it has gone, the '
              'substitute is Moen Spot Resist Brushed Nickel throughout — mixing Delta '
              'SpotShield BN and Moen Spot Resist BN across rooms is fine, mixing them in '
              'the SAME room is not, they are visibly different tones.',
})

WC_AND_SHOWER_TYPES = (
    TOTO_SP_WALL_HUNG, TOTO_CARLYLE_II, TOTO_AQUIA_IV, TOTO_DRAKE,
    SHOWER_36_DIVERTED, SHOWER_36_COMBO, SHOWER_36_NEO_COMBO, TUBSHOWER_60_DIVERTED,
)
