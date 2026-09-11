"""North entry DECK, tiers, guards and screen — what sits on the structure.

The structure itself — piers, footings, columns, headers and the seven beams — is
`params/north_entry_frame.py`, split out on 2026-09-10 for AGENTS.md's 500-line rule. Every
geometry constant is defined there and imported here so the two cannot drift; nothing in
this file re-derives one.

The four terrace tiers are the exception to "structure lives next door", and deliberately:
they are cast pours with no framing, so they sit with the thing they carry (the flight)
rather than with the frame that carries the roof.

See `notes/north_entry_structure.md` for the bearing map, and that module's docstring for
the house-wide KDAT longevity spec every treated member here also carries.
"""

from typehaus import (
    Annotation, Connector, ConnectorKind, DeckLayer, FloorSystem, Footing, JoistSpec,
    Node, Post, Railing, RailingKind, Slab, SlatScreen, Stair, Wall,
    ft, inch, pt,
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
    FIELD_EAST_X_FT,
    FIELD_WEST_X_FT,
    FRAME_Y0_FT,
    FRAME_Y1_FT,
    GARAGE_CLADDING_Y_FT,
    GARAGE_INSIDE_Y_FT,
    GARAGE_LANDING_EAST_FT,
    GARAGE_LANDING_END_Y_FT,
    GARAGE_LANDING_WEST_FT,
    GARAGE_SEAT_Y_FT,
    HEADER_SOFFIT_FT,
    HEADER_TOP_FT,
    HOUSE_CLADDING_Y_FT,
    HOUSE_SEAT_Y_FT,
    LANDING_EAST_FT,
    LANDING_WEST_FT,
    MOVEMENT_GAP_IN,
    PIER_LINE_Y_FT,
    ROOF_COLUMN_EAST_X_FT,
    SCREEN_PANEL_TOP_FT,
    rectangle,
)
from plan.storeys.garage import GARAGE_Y_SOUTH

# ** THE JOISTS RUN NORTH-SOUTH, STRAIGHT ON THE TWO SEAT BEAMS (owner, 2026-09-10). **
# They used to run east-west on a middle tier of north-south floor beams that in turn sat on
# these seats -- three tiers of framing under a landing 5'-6" square. The middle tier is gone
# (`params/north_entry_frame.py` carries the reasoning and why the SEATS are what survived).
#
# 4'-11 3/4" clear between the seats, cantilevering 9 1/2" south and 7 1/4" north, both inside
# R507.5.1's quarter of the back span (14 15/16"). 2x8 at 12" o.c. is far more joist than a
# 5'-0" span needs and is kept deliberately: it is the section and spacing the two garage
# carriers beside it are, and one joist size on a landing this small is a purchasing decision,
# not a structural one.
#
# ** THE FIELD IS NARROWER THAN THE DECK AND BOTH EDGES ARE FORCED. ** West, PT-BW-CW and
# PT-BW-CNW are 6x6 canopy columns standing on the pier line at x=6'-0" and rising through the
# deck's own -1" to -8 1/4" band, so the westmost joist face stops at their east face. East,
# BM-BW-FE occupies x=9'-4" to 9'-7" (11'-3"..11'-6" until 2026-09-11, when the deck came in
# to the service door's east jamb). The boards oversail 3 3/4" each side onto the blocking
# named in AN-BW-STRUCTURE -- a composite board is not cantilevered at its END, so that strip
# is blocked between joists, not left flying.
FLOOR = FloorSystem(
    uid="BWFS01AAAA", tag="FS-BW-FLOOR",
    top_elevation=ft(DECK_JOIST_TOP_FT),
    joists=JoistSpec(member="2x8", spacing=inch(12), direction="y",
                     bearing_refs=("BM-BW-HOUSE-SEAT", "BM-BW-GARAGE-SEAT"),
                     cantilever_start=ft(HOUSE_SEAT_Y_FT - FRAME_Y0_FT),
                     cantilever_end=ft(FRAME_Y1_FT - GARAGE_SEAT_Y_FT)),
    outline=rectangle(FIELD_WEST_X_FT, FRAME_Y0_FT, FIELD_EAST_X_FT, FRAME_Y1_FT),
    subfloor_outline=rectangle(LANDING_WEST_FT, DECK_SHEET_SOUTH_Y_FT,
                               LANDING_EAST_FT, GARAGE_Y_SOUTH.feet),
    subfloor=DeckLayer(material_ref="composite-deck", thickness=inch(1)),
    service="deck", top_protection="butyl-tape",
    source="shared upper landing on two piered seat beams; north_entry_structure.md",
)

# ** THE INTERIOR LANDING SITS IN THE GARAGE'S SW CORNER (2026-09-11). ** Joists span
# carrier to carrier (7'-1 5/8"..9'-5 1/2"); the sheet runs from the door RO's west jamb at
# 6'-7", a quarter inch off W-G-W's gyp face, to the stem's finished face plus 3'-0" at
# 9'-11 5/8", which is also where the stair below it is flush. It oversails the carriers
# 6 5/8" west and 6 1/8" east, inside `structural.subfloor_oversail`'s 8". The west edge is
# closed by W-G-W itself; RL-BW-GARAGE-E below guards the east. Boards share the main
# landing's finish datum and direction.
GARAGE_FLOOR = FloorSystem(
    uid="BWFS02AAAA", tag="FS-BW-GARAGE",
    top_elevation=ft(DECK_JOIST_TOP_FT),
    joists=JoistSpec(member="2x8", spacing=inch(12), direction="x",
                     bearing_refs=("BM-BW-FC", "BM-BW-FE")),
    outline=rectangle(BEAM_X_FT[0], GARAGE_Y_SOUTH.feet + MOVEMENT_GAP_IN / 12,
                      BEAM_X_FT[1], GARAGE_LANDING_END_Y_FT),
    subfloor_outline=rectangle(GARAGE_LANDING_WEST_FT,
                               GARAGE_Y_SOUTH.feet + MOVEMENT_GAP_IN / 12,
                               GARAGE_LANDING_EAST_FT, GARAGE_LANDING_END_Y_FT),
    subfloor=DeckLayer(material_ref="composite-deck", thickness=inch(1)),
    service="deck", top_protection="butyl-tape",
    source="FS-BW-FLOOR continuation; 1/4in threshold joint; replaces SL-G-STEP-0",
)

STAIR_Y0_FT = HOUSE_CLADDING_Y_FT + 3 / 12
STAIR_Y1_FT = GARAGE_CLADDING_Y_FT - 3 / 12
STAIR_WIDTH_FT = STAIR_Y1_FT - STAIR_Y0_FT
# The going is 18", down from 24". Five 6.8" risers are unchanged, so the run drops from
# 8'-0" to 6'-0" and the stair foot moved west from x=19'-6" to x=17'-6" (2026-09-10), then
# to x=15'-7" when the landing's east edge came in to the door jamb (2026-09-11). 2R + T is 31.6",
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

# ** FOUR CAST TIERS ON A COMPACTED BASE, WHICH IS WHERE THIS ARRIVED AFTER TWO WRONG TURNS. **
# A cut stringer was tried first and fails three ways at this pitch: the horizontal span was
# 8'-0" against DCA 6 Fig. 28 / IRC R507.13.1's 6'-0"; the throat left after notching 6.8:24
# was 4.71" against 5"; and no 2x is wide enough to fix it, because the notch depth
# R*T/hypot(R,T) is driven by the LONG going, so flattening the pitch removes MORE material
# (5" at 6.8:18 wants an 11.54" throat; a 2x12 is 0.29" short).
#
# KDAT box frames on eight 42"-deep piers were tried second, and the piers were the defect:
# laid out east of a flight that runs WEST, so all eight stood under open ground carrying
# nothing at all. They are deleted, and so is the framing they were holding up.
#
# What is here now is the ordinary detail for an exterior terrace and the owner's call
# (2026-09-10): four solid pours, wedding-caked, on a compacted washed-rock base. The
# `Stair` below states the flight's CODE geometry and frames nothing (`carriage="cast"`);
# the concrete is `TIER_SLABS`, four `Slab` elements with their own mix and elevations.
# Read `plan/assemblies.py::ENTRY_STEP_TIER` for why this is not frost-founded and what
# that costs.
#
# ** THE ONE JOINT TO WATCH IS AT THE TOP, NOT THE BOTTOM. ** The fourth tier meets a deck
# landing that stands on piers to -9'-9 7/16" and will not move; the tiers will. Riser
# uniformity has 3/8" of tolerance (R311.7.5.1) and that joint is where it is spent. At the
# bottom the pavers are a flexible field and no riser depends on them.
TIERS = Stair(
    uid="BWST01AAAA", tag="ST-BW-ENTRY", from_storey="main", to_storey="main",
    base_elevation=SITE_GRADE, top_elevation=ft(DECK_FINISH_FT),
    width=ft(STAIR_WIDTH_FT), start=pt(ft(STAIR_FOOT_X_FT), ft(STAIR_Y0_FT)),
    run_direction="x", run_reversed=True, tread_depth=ft(TREAD_DEPTH_FT),
    nosing_depth=inch(0), material="concrete", carriage="cast",
)

TIER_RISE_IN = 34.0 / 5.0   # five equal risers from SITE_GRADE to the deck; 6.8" each
# Wedding-caked, so every tier but the lowest is fully bedded on the one under it and
# nothing spans: tier i runs from the LANDING edge east to the front of its own tread, and
# only the strip past the tier above it is walked on. The flight runs west (run_reversed),
# so the lowest tier is the longest and the easternmost.
TIER_SLABS = [
    Slab(uid=f"BWTS0{_i + 1}AAA", tag=f"SL-BW-TIER{_i + 1}",
         outline=rectangle(LANDING_EAST_FT, STAIR_Y0_FT,
                           STAIR_FOOT_X_FT - _i * TREAD_DEPTH_FT, STAIR_Y1_FT),
         thickness=inch(TIER_RISE_IN),
         top_elevation=ft(SITE_GRADE.feet + (_i + 1) * TIER_RISE_IN / 12),
         assembly="ENTRY_STEP_TIER")
    for _i in range(TREAD_COUNT)
]


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
# ** RL-BW-GARAGE-W IS GONE (2026-09-11): the interior landing stands against W-G-W. ** Its
# uid BWRGGWAAAA is retired and must not be reused. The east guard stands on the landing's
# east edge, which is the stem's finished face plus the 3'-0" stair width -- derived, not
# the 11.5 literal it carried until then.
RAILINGS = [
    guard("BWRGGEAAAA", "RL-BW-GARAGE-E", ((GARAGE_LANDING_EAST_FT, GARAGE_INSIDE_Y_FT),
                                          (GARAGE_LANDING_EAST_FT, GARAGE_LANDING_END_Y_FT))),
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
               text="CANOPY RF-BW-CANOPY IS FREESTANDING AND BRACES ITSELF: 4 trusses @24in span 24ft on BM-BW-RW/RE. EAST header lands on PT-BW-RE and PT-BW-RNE, 12in CAST CONCRETE COLUMNS running unbroken from footing to header soffit, FIXED at the base — these are the east lateral system, and they take a shim pack + HGAM10 gusset at the top, NOT a post cap (no wood under that header). WEST header on two 6x6 KDAT columns PT-BW-CW/CNW over 12in piers; the west lateral system is W-BW-SCREEN, the sheathed panel under the slats. NO gravity bearing on W-G-W/W-G-E or on any garage framing. Each truss ties to its header with a stainless H2.5ASS both ends (CN-BW-TRTIE-*). Headers run 8in past the north columns so the roof plane reaches the garage wall; sheathing CONTINUOUS across the garage south wall line and TIED with 7 LSTA24 straps @4ft o.c. (CN-BW-JOINT-1..7) — the two roofs are ONE plane and move together; the strap line carries in-plane shear and tension only, never gravity. Both eaves get the garage's own fascia and a CONTINUOUS 5in trough falling north to TR-G-LEADER-E/-W; NO leader at the canopy south end. No soffit — open tails. South gable of RF-GARAGE and both ends of RF-BW-CANOPY are CLOSE RAKES (sheathing cantilever + fascia), no ladder framing, no barge rafter. Design snow 42psf balanced + 50psf drift surcharge over 9.8ft from the house gable (ASCE 7 §7.7, p_g=50); truss fabricator to price the two southernmost garage trusses as drift trusses"),

    Annotation(uid="BWAN01AAAA", tag="AN-BW-STRUCTURE", position=pt(ft(7), ft(39)),
               text="LANDING: ONE tier of beams. Two seat beams east-west on the piers at -0ft 8-1/4in; 2x8 joists @12in o.c. run NORTH-SOUTH straight on them, cantilevering 9-1/2in south and 7-1/4in north. BM-BW-FC/FE run north-south in the SAME plane (not a second tier) and exist only to reach the interior landing under D-G-SERVICE's sill, 3-3/4in over the continuous ICF stem; they are posted at their tips on PT-BW-IC and PT-BW-IE, 4x4 KDAT 25-3/4in tall on ABU44 standoff bases with cast-in AB-058-10-SS bolts. Thicken SL-G-FLOOR to 10in over a 2ft square under each post, cast monolithic with the slab (not modelled — no element says 'monolithic'). The interior landing's west edge is closed by W-G-W; ST-G-SERVICE's handrail is wall-mounted on 2x blocking (BK-G-W-RAIL-*). No bearing on the house and none on the garage. TWO PIER DEPTHS ON PURPOSE: the three HOUSE-side piers (PT-BW-W/E/RE) bottom at -9ft 9-7/16in and must be cast WITH the basement excavation while it is open — casting them after backfill undermines the house footing, and the depth costs shaft only because the hole is already there. The three GARAGE-side piers (PT-BW-GW/GE/RNE) bottom at -7ft 0in, coplanar with the garage strip footings, and are cast with the garage foundation in the same pour. PT-BW-RE and PT-BW-RNE carry on ABOVE the bearing plane as full-height columns — one continuous pour each, footing to header soffit, no cold joint at the deck. Hold deck boards 1/2in off the house cladding and let the gap drain"),

    Annotation(uid="BWAN02AAAA", tag="AN-BW-TIERS", position=pt(ft(16), ft(39)),
               text="TERRACE: 5 equal 6.8in rises; four CAST tiers (SL-BW-TIER1..4), 18in going, wedding-caked so each is fully bedded on the one below, on a compacted washed-rock base — NOT frost-founded, and that is a decision: a monolithic pour moves as one piece and the joint that matters is at the TOP, against a deck landing on piers that will not move (R311.7.5.1 allows 3/8in of riser variation and that joint is where it is spent). EXPOSED_MIX (ACI 318-19 F3+C2), broom finish, 1/4in per foot of cross-fall to the east. No wood, no stringers, no piers — the eight drilled piers this replaced stood east of the flight under open ground"),
    Annotation(uid="BWAN04AAAA", tag="AN-BW-KDAT", position=pt(ft(9), ft(41)),
               text="ALL KDAT: 304 stainless fasteners (IRC R317.3.1); butyl joist tape over every beam/rim top; field-treat every cut end, notch and hole with 2% copper naphthenate per AWPA M4 (IRC R317.1.1 — required, not advisory); finish with a PIGMENTED penetrating oil on installation, recoat 2-3yr horizontal. NO silicate/'liquid glass' — it is a masonry densifier, leaches from wood and adds no UV protection. W-BW-SCREEN is KDAT 2x4 framing under CDX and corrugated on BOTH faces; every cut end inside that panel gets the same M4 treatment before it is closed up, because nothing reaches it afterwards"),
]

# ** THE WEST SIDE IS A SOLID SHEAR PANEL WITH A SLAT CLERESTORY OVER IT (owner, 2026-09-10). **
# The whole west edge was open slats standing beside a separate metal guard, and neither of
# those is true any more. Bottom: `W-BW-SCREEN`, a sheathed KDAT wall from the PIER TOPS at
# -1'-3 1/2" up to +4'-0" -- the canopy's north-south lateral system, the guard, and the
# closure over the deck framing, all one element (→ plan/assemblies.py::ENTRY_SCREEN_WALL).
# Top: the slats below, now a 2'-4 3/4" clerestory band from +4'-0" to the header soffit.
#
# ** THE PANEL STARTS AT -0'-1", THE JOIST PLANE, AND NOT AT THE PIER TOPS. ** The first
# intent was to run it the whole way down to the cast tops at -1'-3 1/2", and the framing in
# that band is what stopped it: the two seat beams and the deck joists already occupy -0'-1"
# to -1'-3 1/2" on this line, and a sill plate down there is in the same space as both seats
# (`structural.member_interference` says so, twice). It stands on BM-BW-SCSILL instead -- its
# own 2x8, spanning the two seats between the two columns -- which is a real bearing line
# rather than a plate over air, and which doubles as the deck's west rim.
#
# What that leaves exposed below the panel is 7 1/4" of deck framing and, under it, the seat
# beams over their piers: treated stock with a butyl cap, standing on concrete, both meant to
# be seen and both reachable to inspect. The shear still reaches concrete in one step -- the
# sill lands on the two seats, and each of those crosses this line directly over a pier, with
# PT-BW-CW and PT-BW-CNW standing on the same two tops.
#
# ** THE SLATS ARE IN-FILL AGAIN, AND THE ROLE FIELD SAYS SO. ** With a solid wall covering
# the guard zone, `SC-BW-WEST` is back to `role="screen"`: it is above the guard line, it
# guards nothing, and a slat band claiming to be a guard when a wall beside it already is one
# would put the same edge in the census twice. It stands on the panel's own top plate; the
# two cross rails an earlier pass added for it are deleted (→ params/north_entry_frame.py).
SCREEN_PITCH_IN = 3.0
SCREEN_START_Y_FT = DECK_SHEET_SOUTH_Y_FT
SCREEN_END_Y_FT = GARAGE_Y_SOUTH.feet
SCREEN_SLAT_COUNT = int((SCREEN_END_Y_FT - SCREEN_START_Y_FT) * 12 / SCREEN_PITCH_IN) + 1
SCREEN_PANEL_NODES = [
    Node(uid="BWNS01AAAA", tag="N-BW-SCREEN-S",
         position=pt(ft(LANDING_WEST_FT), ft(SCREEN_START_Y_FT)), open_end=True),
    Node(uid="BWNS02AAAA", tag="N-BW-SCREEN-N",
         position=pt(ft(LANDING_WEST_FT), ft(SCREEN_END_Y_FT)), open_end=True),
]
# ** IT IS FILED ON THE GARAGE STOREY, NOT ON MAIN, AND THAT IS NOT A FILING DETAIL. **
# Every derivation that answers "how big is this building" and "where are its braced wall
# lines" is scoped BY STOREY -- it is the only thing keeping the garage's own walls out of
# the house's numbers. Filed on `main`, this screen made `braced_wall_lines("main")` return a
# fifth perimeter line for a freestanding panel forty feet from the house, and stretched the
# overall dimension chain from 36'-0" to 43'-2 5/8". It belongs with `RF-BW-CANOPY`, which is
# authored on the garage storey for the same reason (a roof belongs to a storey), and which
# is the thing this panel braces. `base_elevation` is absolute, so the storey datum does not
# move it.
GARAGE_STOREY_ELEMENTS = []
SCREEN_PANEL = Wall(
    uid="BWWS01AAAA", tag="W-BW-SCREEN",
    start_node="N-BW-SCREEN-S", end_node="N-BW-SCREEN-N",
    assembly="ENTRY_SCREEN_WALL", base_elevation=ft(DECK_JOIST_TOP_FT),
    top=ft(SCREEN_PANEL_TOP_FT - DECK_JOIST_TOP_FT), guard=True,
)
GARAGE_STOREY_ELEMENTS.extend([*SCREEN_PANEL_NODES, SCREEN_PANEL])
SCREEN = SlatScreen(
    uid="BWSC001AAA", tag="SC-BW-WEST", start=pt(ft(LANDING_WEST_FT), ft(SCREEN_START_Y_FT)),
    end=pt(ft(LANDING_WEST_FT), ft(SCREEN_END_Y_FT)),
    base_elevation=ft(SCREEN_PANEL_TOP_FT),
    height=ft(HEADER_SOFFIT_FT - SCREEN_PANEL_TOP_FT),
    slat_face=inch(1.5), slat_depth=inch(3.5), clear_gap=inch(1.5),
    assembly="POST_KDAT", supported_by="W-BW-SCREEN",
    engineering_note="In-fill only, and above the guard line: the slats carry IRC Table R301.5 fn. f's 50 lb over 1 sqft (d/c ~0.33) over a 2ft 4-3/4in span between W-BW-SCREEN's top plate and BM-BW-RW's soffit. The guard is W-BW-SCREEN below them, and the 200 lb guard load never reaches a slat.",
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
              kind=ConnectorKind.POST_CAP, position=pt(ft(_x), ft(_y)),
              elevation=ft(HEADER_SOFFIT_FT), size="CCQ46SDS2.5",
              connects=("BM-BW-RW", f"PT-BW-C{_s}"))
    for _i, (_s, _x, _y) in enumerate((("W", LANDING_WEST_FT, PIER_LINE_Y_FT),
                                       ("NW", LANDING_WEST_FT, GARAGE_SEAT_Y_FT)))
]

# ** THE EAST HEADER LANDS ON A CAST TOP, WHICH IS A DIFFERENT JOINT AND A DIFFERENT PART. **
# A CCQ46SDS2.5 is a post cap: it joins a 4x beam to a 6x6 WOOD post and is fastened into
# wood on both legs. There is no wood under BM-BW-RE any more. The joint here is the one the
# porch columns and the two seat beams already use, and for the same two reasons: a stainless
# shim pack holds the treated soffit clear of the pour so water cannot stand in the joint and
# the copper treatment never touches concrete, and an HGAM10 gusset -- #14 screws into the
# wood leg, Titen Turbo into the concrete -- is the TIE, because a beam merely resting on a
# column is a break in the uplift chain that `structural.uplift_path_coverage` will find.
EAST_HEADER_BEARINGS = []
for _i, (_t, _y) in enumerate((("E", PIER_LINE_Y_FT), ("NE", GARAGE_SEAT_Y_FT))):
    EAST_HEADER_BEARINGS.append(Connector(
        uid=f"BWEB{_i}AAAAAA"[:10], tag=f"CN-BW-STDF-R{_t}",
        kind=ConnectorKind.BEARING_STANDOFF, position=pt(ft(ROOF_COLUMN_EAST_X_FT), ft(_y)),
        elevation=ft(HEADER_SOFFIT_FT), size="SS316-SHIM-35",
        connects=("BM-BW-RE", f"PT-BW-R{'E' if _t == 'E' else 'NE'}")))
    EAST_HEADER_BEARINGS.append(Connector(
        uid=f"BWEG{_i}AAAAAA"[:10], tag=f"CN-BW-TIE-R{_t}",
        kind=ConnectorKind.POST_CAP, position=pt(ft(ROOF_COLUMN_EAST_X_FT), ft(_y)),
        elevation=ft(HEADER_SOFFIT_FT), size="HGAM10",
        connects=("BM-BW-RE", f"PT-BW-R{'E' if _t == 'E' else 'NE'}")))

# ** THE FOUR COLUMN BASES, AUTHORED FOR THE SAME REASON THE TRUSS TIES ARE. **
# `takeoff/uplift_joints.py::post_base_rows` derives a base from the post's SECTION and names
# the catalog model for it, which is the galvanized ABU66 -- there is no field on a `Post`
# that says "buy the stainless variant". So the order said ABU66 while prices.toml carried a
# note pricing that row at the stainless rate, which is a lie told twice: the BOM named the
# wrong part and the drawings named none at all.
#
# These four columns are treated southern pine standing 25 3/4" out of the ground at a salted
# entry, on the wet side of a house that buys 304/316 stainless at every KDAT joint. Authoring
# the base stands the derived rule down (`tags_covered_by` is by tag for a post base, and a
# post has exactly one) and puts ABU66SS on the schedule. The cast-in bolt is NOT stood down
# with it -- `post_base_anchor_rows` unions the authored and derived populations on purpose,
# so all four keep their AB-058-10-SS.
#
# ** AND THE STAINLESS BASE IS UNRATED, WHICH IS WHY THIS IS A DETAIL NOTE AND NOT A CAPACITY
# CLAIM. ** ESR-1622 Table 2 lists no SS model; 316L's yield is below the A653 SS Grade 33/40
# the ABU tables are built on, so the galvanized number is not even obviously conservative.
# `library/hardware.py::ABU66SS_POST_BASE` carries `allowable=None` and says so. What makes
# that acceptable here is that uplift is not the governing case: net 0.6D+0.6W is ~230 lb per
# column (north_entry_frame.py), and the base is a standoff and a hold-down, never a moment
# connection.
COLUMN_BASES = [
    Connector(uid=f"BWCB{_i}AAAAAA"[:10], tag=f"CN-BW-BASE-{_s}",
              kind=ConnectorKind.POST_BASE, position=pt(ft(_x), ft(_y)),
              elevation=ft(BEARING_TOP_FT), size="ABU66SS",
              connects=(f"PT-BW-C{_s}", _pier))
    for _i, (_s, _x, _y, _pier) in enumerate((
        ("W", LANDING_WEST_FT, PIER_LINE_Y_FT, "PT-BW-W"),
        ("NW", LANDING_WEST_FT, GARAGE_SEAT_Y_FT, "PT-BW-GW"),
    ))
]

# ** THE TWO INTERIOR POST BASES, AUTHORED FOR A DIFFERENT REASON: THE STANDOFF IS THE DETAIL. **
# PT-BW-IC/-IE are 4x4 KDAT standing on the garage slab, inside, dry -- the galvanized ABU44
# is the right part and the derived rule would have named it. What the derived row cannot say
# is WHY: a 1" standoff off a slab that gets plowed snow walked onto it, so the end grain never
# sits in water, and the cast-in AB-058-10-SS that `post_base_anchor_rows` derives for a base
# on concrete. Authoring the base puts both on the drawings and takes the two posts out of
# the derived ABU44 row (`tags_covered_by` is by tag). Elevation is the slab top.
INTERIOR_POST_BASES = [
    Connector(uid=f"BWIB{_i}AAAAAA"[:10], tag=f"CN-BW-IBASE-{_s}",
              kind=ConnectorKind.POST_BASE, position=pt(ft(_x), ft(GARAGE_LANDING_END_Y_FT)),
              elevation=SITE_GRADE, size="ABU44",
              connects=(f"PT-BW-I{_s}", "SL-G-FLOOR"))
    for _i, (_s, _x) in enumerate(zip(("C", "E"), BEAM_X_FT, strict=True))
]

# ** THE CANOPY'S TRUSS BEARINGS, AUTHORED RATHER THAN DERIVED, AND IN STAINLESS. **
# `takeoff/uplift.py::bearing_uplift_tie_rows` was already deriving eight commodity H2.5A
# here, which is the right RULE and the wrong PART: this is a freestanding canopy whose
# trusses land on treated southern pine at a salted entry, and the house buys stainless at
# every KDAT joint. A derived row also draws nothing and names nothing on the set, which is
# how a joint that carries the whole roof's uplift ended up invisible. Authoring the eight
# stands the derived rule down (`authored_joints` is pairwise) and puts the part on the
# drawings.
#
# One per bearing, not two. Gross wind uplift on the canopy is 1,706 lb per header
# (notes/north_entry_piers.md Sec 4) over four bearings = 427 lb, so 0.6W is ~256 lb per tie
# with no dead relief taken at all. Even the lowest H2.5ASS figure in circulation covers
# that -- but NOT by the margin the galvanized tie's 700 lbf would suggest, which is why
# `library/hardware.py` carries the stainless tie as its own record with no allowable.
#
# The stations are the truss layout's own: `roof_gable.build_truss_layout` walks the bearing
# axis at the assembly's 24" spacing and always lands the last one on `along_hi`, so a bay
# that does not divide evenly puts the north truss hard against the garage wall.
TRUSS_STATION_Y_FT = (PIER_LINE_Y_FT, PIER_LINE_Y_FT + 2.0, PIER_LINE_Y_FT + 4.0,
                      GARAGE_Y_SOUTH.feet)
TRUSS_TIES = [
    Connector(uid=f"BWTT{_i}{_s}AAAA"[:10], tag=f"CN-BW-TRTIE-{_s}{_i + 1}",
              kind=ConnectorKind.HURRICANE_TIE, position=pt(ft(_x), ft(_y)),
              elevation=ft(HEADER_TOP_FT), size="H2.5ASS",
              connects=("RF-BW-CANOPY", f"BM-BW-R{_s}"))
    for _s, _x in (("W", LANDING_WEST_FT), ("E", ROOF_COLUMN_EAST_X_FT))
    for _i, _y in enumerate(TRUSS_STATION_Y_FT)
]

# ** THE JOINT TO THE GARAGE IS A REAL TIE NOW, AND IT IS NO LONGER THE LATERAL SYSTEM. **
# Until 2026-09-10 this file and the notes said two incompatible things about one plane: that
# the continuous sheathing across the garage south wall line was "the canopy's ONLY connection
# to the garage and IS its lateral system", and that "the two buildings move independently and
# the joint has to". A plane cannot be both a rigid shear transfer and a movement joint, and
# the scheme was indefensible for three further reasons a reviewer would reach in minutes: a
# diaphragm needs chords and a collector, and none were drawn; the two structures are
# separately founded, so differential movement works the nails; and four standoff bases and
# two pinned caps gave the frame no lateral stiffness of its own in either direction --
# Simpson's own catalogue says a post base does not resist rotation and is not for an
# unbraced carport.
#
# Both halves are settled, and in opposite directions (owner, 2026-09-10):
#
#  * **The canopy braces itself.** PT-BW-RE and PT-BW-RNE are cast concrete columns fixed at
#    the base, running unbroken footing to header, which is the same lateral system the
#    balcony's four corner pillars already are in this house. W-BW-SCREEN answers the west
#    side. The garage carries none of it.
#  * **And the two roofs really are one roof, so they are tied like one.** Sharing a plane and
#    a sheathing course while being free to move apart was the odd part, not the tie. These
#    straps make the continuity a drawn, counted connection instead of an assumption about
#    nailing. The movement joint that remains is at the HOUSE end, which is where two
#    independently founded structures actually meet (→ the RF-BW-CANOPY south closure).
#
# ** A TIE IS NOT A BEARING, AND THE DISTINCTION IS THE WHOLE POINT. ** These carry in-plane
# shear and tension across the joint. No gravity crosses it in either direction: the canopy's
# roof load goes to its own two headers, four columns and six piers, and `bearing_refs` names
# no garage element anywhere in this assembly. LSTA24 is the house's own strap (ESR-2105
# Table 3, already stocked for the ridge) at 4'-0" o.c. over the 24'-0" joint -- seven of them
# against a computed collector demand near 18 plf, which is nominal continuity rather than a
# governing number, and is deliberately sized that way.
JOINT_TIE_COUNT = 7
JOINT_TIES = [
    Connector(uid=f"BWJT{_i:02d}AAAA"[:10], tag=f"CN-BW-JOINT-{_i + 1}",
              # TENSION_TIE, not HOLD_DOWN, and the difference is not cosmetic. A HOLD_DOWN
              # naming a roof is what `structural.uplift_path_coverage` and
              # `takeoff/uplift.py` read as "this roof's BEARING uplift is authored" — so
              # seven straps across a joint stood down all twenty-six of RF-GARAGE's derived
              # H2.5A truss ties and the garage roof lost its hold-downs outright. A drag tie
              # across a diaphragm joint is not a bearing tie and must not be filed as one.
              kind=ConnectorKind.TENSION_TIE,
              position=pt(ft(LANDING_WEST_FT + _i * (ROOF_COLUMN_EAST_X_FT - LANDING_WEST_FT)
                             / (JOINT_TIE_COUNT - 1)), ft(GARAGE_Y_SOUTH.feet)),
              elevation=ft(HEADER_TOP_FT), size="LSTA24",
              connects=("RF-BW-CANOPY", "RF-GARAGE"),
              source="north_entry_structure.md §1 — diaphragm continuity across the garage south wall line; in-plane shear and tension only, no gravity")
    for _i in range(JOINT_TIE_COUNT)
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

MAIN_ELEMENTS = [*FRAME_ELEMENTS, FLOOR, GARAGE_FLOOR, TIERS, *TIER_SLABS,
                 SCREEN, *RAILINGS, *SEAT_BEARINGS, *COLUMN_BASES, *INTERIOR_POST_BASES,
                 *COLUMN_CAPS, *EAST_HEADER_BEARINGS, *TRUSS_TIES, *JOINT_TIES,
                 *SNOW_RETENTION, *NOTES]
