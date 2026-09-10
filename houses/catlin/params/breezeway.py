"""North entry DECK, tiers, guards and screen — what sits on the structure.

The structure itself — piers, footings, columns, headers and the five beams — is
`params/north_entry_frame.py`, split out on 2026-09-10 for AGENTS.md's 500-line rule. Every
geometry constant is defined there and imported here so the two cannot drift; nothing in
this file re-derives one.

See `notes/north_entry_structure.md` for the bearing map, and that module's docstring for
the house-wide KDAT longevity spec every treated member here also carries.
"""

from typehaus import (
    Annotation, Connector, ConnectorKind, DeckLayer, FloorSystem, Footing, JoistSpec,
    Post, Railing, RailingKind, SlatScreen, Stair, ft, inch, pt,
)

from params.foundations import SITE_GRADE
from params.north_entry_frame import (
    BEAM_X_FT,
    BEARING_TOP_FT,
    DECK_FINISH_FT,
    DECK_JOIST_TOP_FT,
    DECK_SHEET_SOUTH_Y_FT,
    ENTRY_PIER_CAGE,
    FRAME_ELEMENTS,
    FRAME_Y0_FT,
    FRAME_Y1_FT,
    GARAGE_CLADDING_Y_FT,
    GARAGE_INSIDE_Y_FT,
    GARAGE_LANDING_END_Y_FT,
    GARAGE_LANDING_WEST_FT,
    GARAGE_SEAT_Y_FT,
    HEADER_SOFFIT_FT,
    HOUSE_CLADDING_Y_FT,
    HOUSE_SEAT_Y_FT,
    LANDING_EAST_FT,
    LANDING_WEST_FT,
    MOVEMENT_GAP_IN,
    PIER_LINE_Y_FT,
    ROOF_COLUMN_EAST_X_FT,
    rectangle,
)
from plan.storeys.garage import GARAGE_Y_SOUTH

FLOOR = FloorSystem(
    uid="BWFS01AAAA", tag="FS-BW-FLOOR",
    top_elevation=ft(DECK_JOIST_TOP_FT),
    joists=JoistSpec(member="2x8", spacing=inch(12), direction="x",
                     bearing_refs=("BM-BW-FW", "BM-BW-FC", "BM-BW-FE")),
    outline=rectangle(BEAM_X_FT[0], FRAME_Y0_FT, BEAM_X_FT[-1], FRAME_Y1_FT),
    subfloor_outline=rectangle(LANDING_WEST_FT, DECK_SHEET_SOUTH_Y_FT,
                               LANDING_EAST_FT, GARAGE_Y_SOUTH.feet),
    subfloor=DeckLayer(material_ref="composite-deck", thickness=inch(1)),
    service="deck", top_protection="butyl-tape",
    source="shared upper landing on two piered seat beams; north_entry_structure.md",
)

# A narrower framing zone preserves the main landing identity while keeping the garage
# wall out of the rectangular joist field. Boards share the finish datum and direction.
GARAGE_FLOOR = FloorSystem(
    uid="BWFS02AAAA", tag="FS-BW-GARAGE",
    top_elevation=ft(DECK_JOIST_TOP_FT),
    joists=JoistSpec(member="2x8", spacing=inch(12), direction="x",
                     bearing_refs=("BM-BW-FC", "BM-BW-FE")),
    outline=rectangle(BEAM_X_FT[1], GARAGE_Y_SOUTH.feet + MOVEMENT_GAP_IN / 12,
                      BEAM_X_FT[2], GARAGE_LANDING_END_Y_FT),
    subfloor_outline=rectangle(GARAGE_LANDING_WEST_FT,
                               GARAGE_Y_SOUTH.feet + MOVEMENT_GAP_IN / 12,
                               LANDING_EAST_FT, GARAGE_LANDING_END_Y_FT),
    subfloor=DeckLayer(material_ref="composite-deck", thickness=inch(1)),
    service="deck", top_protection="butyl-tape",
    source="FS-BW-FLOOR continuation; 1/4in threshold joint; replaces SL-G-STEP-0",
)

STAIR_Y0_FT = HOUSE_CLADDING_Y_FT + 3 / 12
STAIR_Y1_FT = GARAGE_CLADDING_Y_FT - 3 / 12
STAIR_WIDTH_FT = STAIR_Y1_FT - STAIR_Y0_FT
# The going is 18", down from 24". Five 6.8" risers are unchanged, so the run drops from
# 8'-0" to 6'-0" and the stair foot moves west from x=19'-6" to x=17'-6". 2R + T is 31.6",
# still outside the 24"-25" comfort rule -- which is inherent to a tiered terrace and is not
# a code limit. If it reads wrong on site the lever is the going, and the paver landing in
# plan/site.py follows it again.
TREAD_DEPTH_FT = 1.5
TREAD_COUNT = 4
STAIR_FOOT_X_FT = LANDING_EAST_FT + TREAD_COUNT * TREAD_DEPTH_FT
LOWER_LANDING_END_X_FT = STAIR_FOOT_X_FT + 3
# ** 9" O.C., AND IT IS THE TREAD RATING, NOT THE DECKING RATING. ** A composite board is
# rated for a UNIFORM load as decking and a 300 lb CONCENTRATED load as a stair tread (IRC
# Table R301.5 fn. c; ICC-ES AC174 Sec 4.1.1 tests it at 1/8" of deflection under 300 lb, an
# ABSOLUTE limit, not L/288). The same board is 16" as decking and 8"-12" as a tread across
# the major brands -- ESR-3771 shows 16" and 11" on one product. `composite-deck` in this
# house names no manufacturer, so 9" is the floor of the mainstream distribution (Trex
# Enhance 9", Trex Select 9", TimberTech Premier 9", ReliaBoard 9") and survives a purchasing
# change after the boxes are built. IRC R507.2.2.5 makes the delivered board's instruction
# binding and IRC Table R507.7 excludes stairways outright: if the board's ASTM D7032 label
# says less than 9", the layout follows the board. Square-edge, face-fastened only -- Fiberon
# and TimberTech both prohibit grooved planks as stair treads outright.
TREAD_SUPPORT_SPACING_IN = 9.0

# ** BOX FRAMES, NOT CUT STRINGERS, AND A CUT STRINGER FAILS ON THREE COUNTS HERE. **
# At the old 24" going the horizontal span was 8'-0" against DCA 6 Fig. 28 / IRC R507.13.1's
# 6'-0"; the remaining throat was 4.71" against 5"; and the treads wanted supports closer
# than 12". Narrowing the going to 18" fixes the span and does NOT fix the throat: the notch
# depth R*T/hypot(R,T) is driven by the LONG going, so a flatter pitch removes MORE material,
# and holding 5" at 6.8:18 would take an 11.54"-wide member -- a 2x12 is 0.29" short and the
# next size is off every prescriptive table.
#
# Four boxes instead, each ~6'-0" x 1'-6", on footings at 42" below finished grade. That
# depth is not a range: Minn. R. 1303.1600 sets "the minimum allowable footing depth in feet
# due to freezing is five feet in Zone I and 3-1/2 feet in Zone II", and Zone II is named to
# include Hennepin. (The 60" figure is northern Minnesota, a different zone.) A deep
# washed-rock section is NOT a prescriptive alternative: IRC R403.3 applies only to buildings
# kept at 64F or warmer and says outright it "shall not be used for unheated spaces such as
# porches", and Minnesota's Rules 1309.0403 amendment carries no exceptions -- the aggregate
# route reaches it only through ASCE 32, a stamped engineered submittal.
#
# ** THE SUPPORT WAS ALWAYS WORSE THAN THE MEMBER. ** The old flight was pinned at the top to
# a 9'-9" pier and sat at the bottom on pavers on soil. Heave merely lifts a simply-supported
# member; SETTLEMENT is the failure, because it turns the span into a cantilever off
# BM-BW-FE, which nothing in that assembly can do -- and riser uniformity has only 3/8" of
# tolerance (R311.7.5.1), less than one winter gives up. DCA 6 is explicit: "Stringers shall
# not bear on new or existing concrete pads or patios that are not founded below this depth."
# Accept movement in exactly ONE place: the joint between the bottom box and the paver
# landing, where the pavers are a flexible field and no riser depends on them.
TIERS = Stair(
    uid="BWST01AAAA", tag="ST-BW-ENTRY", from_storey="main", to_storey="main",
    base_elevation=SITE_GRADE, top_elevation=ft(DECK_FINISH_FT),
    width=ft(STAIR_WIDTH_FT), start=pt(ft(STAIR_FOOT_X_FT), ft(STAIR_Y0_FT)),
    run_direction="x", run_reversed=True, tread_depth=ft(TREAD_DEPTH_FT),
    nosing_depth=inch(0), material="kdat", carriage="box",
    stringer_spacing=inch(TREAD_SUPPORT_SPACING_IN),
    tread_material="composite-deck", tread_thickness=inch(1),
)

# Four tier footings per box line, at the Zone II 42". Fine Homebuilding's box-frame footings
# sit "about 4 feet apart because the rim joist of the box can span the distance between the
# footings" -- the only span guidance published anywhere for a box tier, since no prescriptive
# table covers one. DCA 6's nearest hook is that an intermediate stair landing "must be
# designed and constructed as a non-ledger deck using the details in this document", so the
# rims and joists size off DCA 6's DECK tables and not off any stair table.
TIER_FOOTING_DEPTH_IN = 42.0
TIER_FOOTING_THICKNESS_IN = 8.0
TIER_RISE_IN = 6.8
TIER_FRAME_DROP_IN = 1.0 + 7.25   # the 1" tread board and the 2x8 under it
_TIER_FOOTING_BOTTOM_FT = SITE_GRADE.feet - TIER_FOOTING_DEPTH_IN / 12
_TIER_FOOTING_TOP_FT = _TIER_FOOTING_BOTTOM_FT + TIER_FOOTING_THICKNESS_IN / 12
TIER_PIERS = []
TIER_FOOTINGS = []
for _i in range(TREAD_COUNT):
    # Two shafts per box, ~4'-0" apart under a 6'-0" rim, per the only published span
    # guidance for a box tier. The shaft top is the box's FRAMING underside, so each tier's
    # pier is one riser taller than the one below it.
    _x = STAIR_FOOT_X_FT + _i * TREAD_DEPTH_FT + TREAD_DEPTH_FT / 2
    _top = SITE_GRADE.feet + (_i + 1) * TIER_RISE_IN / 12 - TIER_FRAME_DROP_IN / 12
    for _j, _y in enumerate((STAIR_Y0_FT + 0.5, STAIR_Y1_FT - 0.5)):
        _t = f"PT-BW-T{_i + 1}{'WE'[_j]}"
        TIER_PIERS.append(Post(
            uid=f"BWTP{_i}{_j}AAAA", tag=_t, position=pt(ft(_x), ft(_y)),
            size="12 round", height=ft(_top - _TIER_FOOTING_TOP_FT),
            assembly="PIER_CONCRETE_12",
            # The top tier's shaft is h/d 4.4, past the 3 where a PLAIN cast column stops
            # being gradeable, so all eight carry the cage rather than four of them.
            vertical_reinforcement='(4) #5 vertical, #3 ties @ 10" o.c.',
            reinforcement=ENTRY_PIER_CAGE,
            supported_by=f"FT-BW-T{_i + 1}{'WE'[_j]}"))
        TIER_FOOTINGS.append(Footing(
            uid=f"BWTF{_i}{_j}AAAA", tag=f"FT-BW-T{_i + 1}{'WE'[_j]}", under=_t,
            width=inch(24), depth=inch(TIER_FOOTING_THICKNESS_IN),
            assembly="PIER_BASE_12", bottom_elevation=ft(_TIER_FOOTING_BOTTOM_FT)))


def guard(uid, tag, path):
    return Railing(uid=uid, tag=tag, path=tuple(pt(ft(x), ft(y)) for x, y in path),
                   height=inch(36), base_elevation=ft(DECK_FINISH_FT),
                   post_spacing=inch(36), post_size="2x2", rail_count=2,
                   kind=RailingKind.METAL_SURFACE_MOUNT, mount="surface",
                   assembly="RAILING_DARK_METAL", infill="balusters", baluster_spacing=inch(3.5))


# ** THE GUARD MOVED INTO THE SCREEN LINE, WHICH IS WHY RL-BW-WEST IS GONE. **
# RL-BW-WEST stood 1 1/2" west of SC-BW-WEST -- two elements an inch apart doing one job, and
# a plan clash. The screen cannot take the guard load itself: IRC Table R301.5 puts 200 lb
# CONCENTRATED on a guard (the 50 plf line load is IBC Sec 1607.8.1, not a residential
# provision), and a 2x4 on edge cantilevered 36" off the deck is d/c 1.34 at C_D 1.6 and 1.65
# in SPF. Worse, the 2018 IRC's footnote says the 200 lb acts "in any direction", which
# permits it PARALLEL to the screen, bending a slat about its 1 1/2" face where S = 1.31 in3.
# And the base connection is worse than the member: Virginia Tech's full-scale tests behind
# DCA 6 measured 178 lb ultimate for 1/2" lag screws and 237 lb for 1/2" bolts, while
# resolving this base moment over a 5 1/4" arm needs ~1,700 lb of tension per slat -- a
# hold-down every three inches into a 1 1/2" member. Not buildable.
#
# So the guard is one element ON the screen line, anchored to the deck framing and to
# PT-BW-CW, and the slats are demoted to IN-FILL carrying only Table R301.5 footnote f's
# 50 lb over one square foot (d/c ~0.33) -- which also makes them immune to the 2018-vs-2021
# "any direction" question that would otherwise decide the whole detail.
#
# Two openings to check that are NOT the sphere between slats: the gap under the bottom of
# the slats to the deck surface, and the end gaps where the screen meets the house and the
# garage. Both are openings in a required guard and both count.
RAILINGS = [
    guard("BWRGW1AAAA", "RL-BW-SCREEN", ((LANDING_WEST_FT, FRAME_Y0_FT),
                                         (LANDING_WEST_FT, FRAME_Y1_FT))),
    guard("BWRGGWAAAA", "RL-BW-GARAGE-W", ((8.5, GARAGE_INSIDE_Y_FT),
                                          (8.5, GARAGE_LANDING_END_Y_FT))),
    guard("BWRGGEAAAA", "RL-BW-GARAGE-E", ((11.5, GARAGE_INSIDE_Y_FT),
                                          (11.5, GARAGE_LANDING_END_Y_FT))),
    Railing(uid="BWRHE1AAAA", tag="RL-BW-ENTRY",
            path=(pt(ft(STAIR_FOOT_X_FT), ft(STAIR_Y1_FT)),
                  pt(ft(LANDING_EAST_FT), ft(STAIR_Y1_FT))),
            kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
            base_elevation=SITE_GRADE, post_spacing=inch(36), post_size="2x2",
            rail_count=1, mount="surface", assembly="RAILING_DARK_METAL",
            role="guard_and_handrail", serves_stair="ST-BW-ENTRY", top_height=inch(36),
            graspable_profile="1.5in round — Type I", infill="balusters",
            baluster_spacing=inch(3.5)),
]

NOTES = [
    Annotation(uid="BWAN03AAAA", tag="AN-BW-ROOF", position=pt(ft(22), ft(40)),
               text="CANOPY RF-BW-CANOPY: 3 trusses @24in span 24ft between BM-BW-RW/RE on PT-BW-CW/CE; sheathing CONTINUOUS across the garage south wall line — that diaphragm path IS the lateral system; design snow 42psf balanced + 50psf drift surcharge over 9.8ft from the house gable (ASCE 7 §7.7, p_g=50); truss fabricator to price the two southernmost garage trusses as drift trusses"),
    Annotation(uid="BWAN01AAAA", tag="AN-BW-STRUCTURE", position=pt(ft(7), ft(39)),
               text="LANDING: thicken SL-G-FLOOR to 10in over a 2ft square under PT-BW-IC and PT-BW-IE, cast monolithic with the slab (not modelled — no element says 'monolithic'); seat beams on cast concrete to -0ft 8-1/4in BOTH sides; no bearing on the house; piers cast WITH the basement excavation to -9ft 9-7/16in — casting them after backfill undermines the house footing; hold deck boards 1/2in off the cladding and let the gap drain"),
    Annotation(uid="BWAN02AAAA", tag="AN-BW-TIERS", position=pt(ft(16), ft(39)),
               text="5 equal 6.8in rises; four 18in composite box tiers on 42in footings (Minn. R. 1303.1600 Zone II); NO cut stringers; tread supports at 9in o.c. max — read the delivered board's ASTM D7032 STAIR row, not its decking row; square-edge face-fastened treads only"),
    Annotation(uid="BWAN04AAAA", tag="AN-BW-KDAT", position=pt(ft(9), ft(41)),
               text="ALL KDAT: 304 stainless fasteners (IRC R317.3.1); butyl joist tape over every beam/rim top; field-treat every cut end, notch and hole with 2% copper naphthenate per AWPA M4 (IRC R317.1.1 — required, not advisory); finish with a PIGMENTED penetrating oil on installation, recoat 2-3yr horizontal. NO silicate/'liquid glass' — it is a masonry densifier, leaches from wood and adds no UV protection"),
]

# On-edge 2x4s: 3.5in projection in x, 1.5in faces and gaps along y. The screen now runs from
# PT-BW-CW north to the garage wall — 5'-5 1/2", under the 6'-0" post spacing the prescriptive
# guidance assumes — and stops at the header soffit, so it is a simply-supported panel rather
# than an 8'-0" free-standing cantilever. That top restraint is what deletes its unsolved base
# moment, and it is free once the canopy is built. One member settles three things at once:
# PT-BW-CW holds the roof up, restrains the slat tops, and takes the guard load.
SCREEN_PITCH_IN = 3.0
SCREEN_START_Y_FT = PIER_LINE_Y_FT
SCREEN_END_Y_FT = FRAME_Y1_FT - 1.5 / 12
SCREEN_SLAT_COUNT = int((SCREEN_END_Y_FT - SCREEN_START_Y_FT) * 12 / SCREEN_PITCH_IN) + 1
SCREEN = SlatScreen(
    uid="BWSC001AAA", tag="SC-BW-WEST", start=pt(ft(LANDING_WEST_FT), ft(SCREEN_START_Y_FT)),
    end=pt(ft(LANDING_WEST_FT), ft(SCREEN_END_Y_FT)), base_elevation=ft(DECK_JOIST_TOP_FT),
    height=ft(HEADER_SOFFIT_FT - DECK_JOIST_TOP_FT),
    slat_face=inch(1.5), slat_depth=inch(3.5), clear_gap=inch(1.5),
    assembly="POST_KDAT", supported_by="BM-BW-FW",
    engineering_note="In-fill only: slats carry IRC Table R301.5 fn. f's 50 lb over 1 sqft (d/c ~0.33), NOT the 200 lb guard load, which RL-BW-SCREEN and PT-BW-CW take. Top restrained on BM-BW-RW's soffit and south end framed into PT-BW-CW, so the base moment the old free-standing cantilever could not resolve does not arise.",
)

# ** THE FOUR SEAT-BEAM BEARINGS ARE REAL HARDWARE NOW, NOT SIX INVENTED PART NUMBERS. **
# The retired CN-BW-*-SEAT connectors borrowed ConnectorKind.HOLD_DOWN with a part number in
# no catalog ("BW-ENGINEERED-FIXED-SEAT"), and `takeoff/anchors.py` priced it as a custom
# fabrication allowance -- which is how a missing structure billed $1,350-4,050 and graded
# clean. A KDAT beam landing on a cast pier is an ordinary detail and the house already has
# it at the porch columns: a stainless shim pack holding the treated soffit off the pour, so
# water cannot sit in the joint and the copper treatment never touches the concrete.
#
# Two parts per bearing, and they do different jobs. The SS316-SHIM-35 pack is the BEARING:
# it holds the treated soffit off the pour so water cannot sit in the joint and the copper
# treatment never touches the concrete, and it is where the levelling tolerance is taken. The
# HGAM10 gusset is the TIE: #14 screws into the wood leg, Titen Turbo into the concrete leg,
# 1 1/2" minimum edge distance. `structural.uplift_path_coverage` grades the second one --
# a shim pack is not a hold-down, and a beam simply resting on a pier is a break in the chain.
SEAT_BEARINGS = []
for _i, (_t, _x, _y, _beam) in enumerate((
    ("W", LANDING_WEST_FT, HOUSE_SEAT_Y_FT, "BM-BW-HOUSE-SEAT"),
    ("E", LANDING_EAST_FT, HOUSE_SEAT_Y_FT, "BM-BW-HOUSE-SEAT"),
    ("GW", LANDING_WEST_FT, GARAGE_SEAT_Y_FT, "BM-BW-GARAGE-SEAT"),
    ("GE", LANDING_EAST_FT, GARAGE_SEAT_Y_FT, "BM-BW-GARAGE-SEAT"),
)):
    SEAT_BEARINGS.append(Connector(
        uid=f"BWSD{_i}AAAAAA"[:10], tag=f"CN-BW-STDF-{_t}",
        kind=ConnectorKind.BEARING_STANDOFF, position=pt(ft(_x), ft(_y)),
        elevation=ft(BEARING_TOP_FT), size="SS316-SHIM-35",
        connects=(_beam, f"PT-BW-{_t}")))
    SEAT_BEARINGS.append(Connector(
        uid=f"BWSG{_i}AAAAAA"[:10], tag=f"CN-BW-TIE-{_t}",
        kind=ConnectorKind.POST_CAP, position=pt(ft(_x), ft(_y)),
        elevation=ft(BEARING_TOP_FT), size="HGAM10",
        connects=(_beam, f"PT-BW-{_t}")))

# The two header caps. A 3-ply 2x12 is 4 1/2" wide, which is the "4x beam" the CCQ46 is
# published for, on the 6x6 it names. `structural.uplift_path_coverage` would otherwise take
# a DERIVED KBS1Z strap here -- a knee brace standing in for a cap, which is not the detail.
COLUMN_CAPS = [
    Connector(uid=f"BWCC{_i}AAAAAA"[:10], tag=f"CN-BW-CAP-{_s}",
              kind=ConnectorKind.POST_CAP, position=pt(ft(_x), ft(PIER_LINE_Y_FT)),
              elevation=ft(HEADER_SOFFIT_FT), size="CCQ46SDS2.5",
              connects=(f"BM-BW-R{_s}", f"PT-BW-C{_s}"))
    for _i, (_s, _x) in enumerate((("W", LANDING_WEST_FT),
                                   ("E", ROOF_COLUMN_EAST_X_FT)))
]

# Procurement allowance at the two eaves over the entry zone. Supplier must size rail
# lengths, row spacing and clamp demand for the actual drift load and roof profile.
SNOW_RETENTION = [
    Connector(uid=f"BWNS{side}{i}AAAA", tag=f"CN-BW-SNOW-{side}-{i}",
              kind=ConnectorKind.SNOW_GUARD, position=pt(ft(x), ft(y)),
              elevation=ft(8, 2), size="S-5! ColorGard", connects=("RF-GARAGE",),
              source="north_entry_structure.md — provisional entry-zone snow-rail layout")
    for side, x in (("W", 5.5), ("E", 30.5))
    for i, y in enumerate((38.5, 42.5), 1)
]

MAIN_ELEMENTS = [*FRAME_ELEMENTS, FLOOR, GARAGE_FLOOR, TIERS, *TIER_PIERS, *TIER_FOOTINGS,
                 SCREEN, *RAILINGS, *SEAT_BEARINGS, *COLUMN_CAPS, *SNOW_RETENTION, *NOTES]
