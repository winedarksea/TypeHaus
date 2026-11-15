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

# The glazed breezeway is retired; the `-BW-` tag infix and this module's name are historical.

from typehaus import (
    Annotation, Connector, ConnectorKind, FloorSystem, Footing, JoistSpec,
    Node, Post, Railing, RailingKind, ShearPanelSpec, Slab, SnowRetentionSpec, Stair, Wall,
    face, ft, inch, pt,
)

from typehaus.library import TREX_ENHANCE_BASICS_DECK_LAYER
from typehaus.resolve.connector_geometry.hangers import LUS_DIMENSIONS, SHEET_THICKNESS_IN
from params.column_heads import STANDOFF_PACK_IN
from params.foundations import SITE_GRADE
from params.garage_roof_wind_clamps import EAST_CLAMP_X_IN
from params.landing_tie import LANDING_TIES
from params.entry_screen_finish import FINISH_ELEMENTS
from params.north_entry_frame import (
    BEARING_TOP_FT,
    COLUMN_HALF_FT,
    DECK_FINISH_FT,
    DECK_JOIST_TOP_FT,
    DECK_SHEET_SOUTH_Y_FT,
    DECK_SHEET_NORTH_Y_FT,
    ENTRY_PIER_CAGE,
    FRAME_ELEMENTS,
    FIELD_EAST_X_FT,
    FIELD_WEST_X_FT,
    FRAME_Y0_FT,
    FRAME_Y1_FT,
    GARAGE_CLADDING_Y_FT,
    GARAGE_SEAT_Y_FT,
    HEADER_SOFFIT_FT,
    HEADER_TOP_FT,
    HEADER_NORTH_Y_FT,
    HOUSE_CLADDING_Y_FT,
    HOUSE_SEAT_Y_FT,
    LANDING_EAST_FT,
    LANDING_WEST_FT,
    EAST_POST_SYSTEM,
    PIER_LINE_Y_FT,
    PIER_TOP_FT,
    ROOF_COLUMN_EAST_X_FT,
    SCREEN_AXIS_X_FT,
    SCREEN_CLADDING_WEST_X_FT,
    SCREEN_PANEL_TOP_FT,
    SEAT_START_X_FT,
    SEAT_TOP_FT,
    TRUSS_DATUM_Y_FT,
    rectangle,
)
from params.east_posts import east_head_parts, landing_note, roof_note
from plan.storeys.garage import GARAGE_Y_SOUTH

# Joists run N-S straight on the two seat beams (one tier; params/north_entry_frame.py).
# 2x8 at 12" o.c. is more than a 5'-0" span needs, kept to match the two garage carriers beside
# it. Cantilevers of 9 1/2" south and 7 1/4" north stay inside R507.5.1's quarter of the back span.
#
# The field is narrower than the deck: west, the canopy columns PT-BW-CW/-CNW stand on the pier
# line at x=6'-3 3/8" and stop the westmost joist at their east face; east, BM-BW-FE does. Boards
# oversail 3 3/4" each side onto the blocking named in AN-BW-STRUCTURE (a composite board is not
# cantilevered at its end, so that strip is blocked between joists).
FLOOR = FloorSystem(
    uid="BWFS01AAAA", tag="FS-BW-FLOOR",
    top_elevation=ft(DECK_JOIST_TOP_FT),
    joists=JoistSpec(member="2x8", spacing=inch(12), direction="y",
                     bearing_refs=("BM-BW-HOUSE-SEAT", "BM-BW-GARAGE-SEAT"),
                     cantilever_start=ft(HOUSE_SEAT_Y_FT - FRAME_Y0_FT),
                     cantilever_end=ft(FRAME_Y1_FT - GARAGE_SEAT_Y_FT),
                     rim_member="2x8"),  # no 1 1/4" treated rim is stocked; LUSZ is 1 9/16"
    outline=rectangle(FIELD_WEST_X_FT, FRAME_Y0_FT, FIELD_EAST_X_FT, FRAME_Y1_FT),
    subfloor_outline=rectangle(LANDING_WEST_FT, DECK_SHEET_SOUTH_Y_FT,
                               LANDING_EAST_FT, DECK_SHEET_NORTH_Y_FT),
    subfloor=TREX_ENHANCE_BASICS_DECK_LAYER,
    service="deck", top_protection="butyl-tape",
    source="shared upper landing on two piered seat beams; north_entry_structure.md",
)

# D-G-SERVICE swings OUT onto this deck, so ST-G-SERVICE rises straight to the threshold with no
# interior landing (IRC R311.7.6 exception; notes/garage_service_door_outswing.md).
STAIR_Y0_FT = HOUSE_CLADDING_Y_FT + 3 / 12
STAIR_Y1_FT = GARAGE_CLADDING_Y_FT - 3 / 12
STAIR_WIDTH_FT = STAIR_Y1_FT - STAIR_Y0_FT
# 18" going, five risers; 2R + T is 31.6", outside the 24"-25" comfort rule (inherent to a tiered
# terrace, not a code limit). The lever is the going; SL-WK-C's west edge follows the foot.
# The flight springs from the SL-WK-C entry walk, 1" over grade (`params/landscape_walk.TOP`,
# -2'-9", which imports this module: restated here, a test pins the two). Off grade the first
# riser would be 1" outside R311.7.5.1's 3/8" uniformity.
STAIR_BASE_FT = SITE_GRADE.feet + 1 / 12
TREAD_DEPTH_FT = 1.5
TREAD_COUNT = 4
STAIR_FOOT_X_FT = LANDING_EAST_FT + TREAD_COUNT * TREAD_DEPTH_FT
LOWER_LANDING_END_X_FT = STAIR_FOOT_X_FT + 3

# Four cast tiers, wedding-caked on a compacted washed-rock base, cast as ONE stepped placement
# with the walks. The `Stair` states the flight's code geometry and frames nothing
# (`carriage="cast"`); the concrete is `TIER_SLABS`. Why not frost-founded: `plan/assemblies/`
# ENTRY_STEP_TIER. The joint to watch is the top, where tier 4 meets a deck landing on piers that
# will not move: R311.7.5.1's 3/8" riser tolerance is spent there.
TIERS = Stair(
    uid="BWST01AAAA", tag="ST-BW-ENTRY", from_storey="main", to_storey="main",
    base_elevation=ft(STAIR_BASE_FT), top_elevation=ft(DECK_FINISH_FT),
    width=ft(STAIR_WIDTH_FT), start=pt(ft(STAIR_FOOT_X_FT), ft(STAIR_Y0_FT)),
    run_direction="x", run_reversed=True, tread_depth=ft(TREAD_DEPTH_FT),
    nosing_depth=inch(0), material="concrete", carriage="cast",
)

TIER_RISE_IN = (DECK_FINISH_FT - STAIR_BASE_FT) * 12 / 5   # five equal risers; 6.6" each
# Every tier but the lowest is fully bedded on the one under it: tier i runs from the landing edge
# east to the front of its own tread. The flight runs west (run_reversed), so tier 1 is longest.
TIER_SLABS = [
    Slab(uid=f"BWTS0{_i + 1}AAA", tag=f"SL-BW-TIER{_i + 1}", kind="pour",
         outline=rectangle(LANDING_EAST_FT, STAIR_Y0_FT,
                           STAIR_FOOT_X_FT - _i * TREAD_DEPTH_FT, STAIR_Y1_FT),
         thickness=inch(TIER_RISE_IN),
         top_elevation=ft(STAIR_BASE_FT + (_i + 1) * TIER_RISE_IN / 12),
         assembly="ENTRY_STEP_TIER")
    for _i in range(TREAD_COUNT)
]


def guard(uid, tag, path):
    return Railing(uid=uid, tag=tag, path=tuple(pt(ft(x), ft(y)) for x, y in path),
                   height=inch(36), base_elevation=ft(DECK_FINISH_FT),
                   post_spacing=inch(36), post_size="2x2", rail_count=2,
                   kind=RailingKind.METAL_SURFACE_MOUNT, mount="surface",
                   assembly="RAILING_DARK_METAL", infill="balusters", baluster_spacing=inch(3.5))


# The entry guard's head post stays beyond the service leaf sweep; the tier supports it without
# moving the deck edge or narrowing the 36in stair.
ENTRY_GUARD_HEAD_OFFSET_IN = 1.5
RAILINGS = [
    Railing(uid="BWRHE1AAAA", tag="RL-BW-ENTRY",
            path=(pt(ft(STAIR_FOOT_X_FT), ft(STAIR_Y1_FT)),
                  pt(ft(LANDING_EAST_FT + ENTRY_GUARD_HEAD_OFFSET_IN / 12), ft(STAIR_Y1_FT))),
            kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
            base_elevation=ft(STAIR_BASE_FT), post_spacing=inch(36), post_size="2x2",
            rail_count=1, mount="surface", assembly="RAILING_DARK_METAL",
            role="guard_and_handrail", serves_stair="ST-BW-ENTRY", top_height=inch(36),
            graspable_profile="1.5in round — Type I", infill="balusters",
            baluster_spacing=inch(3.5)),
]

NOTES = [
    Annotation(uid="BWAN03AAAA", tag="AN-BW-ROOF", position=pt(ft(22), ft(40)),
               text=("CANOPY RF-BW-CANOPY BEARS ON ITS OWN FOUR SUPPORTS AND BRACES OFF THE GARAGE: 3 trusses @24in span 24ft on BM-BW-RW/RE. "
                     + roof_note(EAST_POST_SYSTEM) + ". "
                     + "HEADERS are 5-1/2x11-7/8 treated glulam (24F-V4 DF), both 65-1/4in long, ending FLUSH on the outer faces of their end posts, NO tails: open air at both ends (about 8in to the house, 5-1/4in to the garage cladding); keep both gaps OPEN and re-seal the end grain. WEST header on two 6x6 KDAT columns PT-BW-CW/CNW on 14in piers: ACE6Z end caps at both CW and CNW, MAX nailing, A35Z angles on the free post faces; cast-in CBSTQ66Z-SDS2 bases, F2 along the screen, straps >= 3in from the pier edge, the four #5 on the cage diagonals. W-BW-SCREEN, the sheathed panel under the band, is graded at 100% of N-S: 8d at 4in edges, nailed to both 6x6 chords. THE BAND OVER IT is SB-BW-BAND: a 2x6 sill and top plate, a 6x6 centre post and ONE 6x6 KDAT knee brace per bay, exactly corner to corner from each chord post up to the top plate at the centre post, faces flush, two open-knee KBS1Z at each brace end (8 total), 8 SDWS22400DB through each plate, two A35Z at each end of the centre post; the deck's shear path into the header uses 6 LTP4Z (CN-BW-EAVE-1..6) nailed directly to bevelled 2-ply SPF 2x8 heel blocking (laminated 8d HDG, two near each end and 12in o.c.) and the glulam, 12 0.131x1.5in HDG nails each (six per member). Blocks seat on each header flush with its INBOARD face, one LS30Z at each truss end (six 0.148x1.5in HDG nails per angle, three per leg, never through a truss plate); the fully nailed deck restrains rotation. One LTP4Z (CN-BW-EAVE-E) ties the east joint-bay block to BM-BW-RE for the east chord force. Deck boundary: 8d HDG at 6in; panel-edge blocking: bevelled SPF 2x4 on edge at 3ft 9in horizontal from the ridge, in every canopy bay and RF-GARAGE's first bay, three 8d HDG toenails each end; cut standard 4ft-wide sheets to fit the pitched module with 1/8in gaps. LATERAL LOAD crosses the joint into RF-GARAGE: E-W through continuous deck panels nailed at 6in into the garage gable top chord and 7 LTP4 clips (CN-BW-GCLIP-1..7) from RF-GARAGE's south gable frame into W-G-S (STHD14 CN-G-BWHD-S-DR at D-G-SERVICE's east jamb); N-S through RF-GARAGE to W-G-E / W-G-W (notes/canopy_garage_diaphragm.md). Canopy trusses bear on their own headers; the last deck bay also bears on the garage gable frame. Each truss ties to its header with a stainless H2.5ASS both ends (CN-BW-TRTIE-*). Headers stop at the north posts' outer faces and the deck oversails 6-1/8in to the garage wall; truss 1 sits flush with the headers' south ends, and the deck bridges the last 1ft 11-3/8in from truss 3 to RF-GARAGE's own gable truss, leaving the garage south wall plane clear for its cladding and the fire/draft closure; sheathing CONTINUOUS across the garage south wall line; 6 LSTA24 straps @4ft o.c. (CN-BW-JOINT-1..3, -5..7; none at the ridge) direct to bevelled 2-ply SPF 2x6 longitudinal nailers BEFORE the deck, between truss faces on both sides of the garage gable; the end straps sit on the 2-2x8 collector blocks, 1-1/4in inboard of the header centrelines. Six OUTERMOST 0.148x2.5in HDG nails per leg (12 total), omit middle six holes, >=2-3/8in wood end and >=3/4in edge distances; installed axial capacity 823lb (1235 x 12/18). One LS30Z at each nailer end (six 0.148x1.5in HDG nails each, three per leg); the fully nailed deck restrains rotation; deck-to-nailer two staggered rows 8d HDG at 3in, one per ply, clear of the strap. NO sheathing seam at the garage gable; see canopy_garage_diaphragm.md Sec 3b — the two roofs are ONE plane and move together; straps carry axial N-S tension and the E-W rotation couple; E-W shear uses deck boundary nailing. Both eaves get the garage's own fascia and a CONTINUOUS 5in trough falling north to TR-G-LEADER-E/-W; NO leader at the canopy south end. No soffit — open tails. South gable of RF-GARAGE and both ends of RF-BW-CANOPY are CLOSE RAKES (sheathing cantilever + fascia), no ladder framing, no barge rafter. NEITHER END OF THE CANOPY IS A GABLE END: all three canopy trusses are ordinary FIELD trusses spanning 24ft, NOT gable-end frames -- a gable-end frame is supported continuously by the wall under its bottom chord and does not span, and there is no wall under either canopy end. Design snow 42psf balanced + 50psf drift surcharge over 9.8ft from the house gable (ASCE 7 §7.7, p_g=50); truss fabricator to price the two southernmost garage trusses as drift trusses\"")),

    Annotation(uid="BWAN01AAAA", tag="AN-BW-STRUCTURE", position=pt(ft(7), ft(39)),
               text=("LANDING: ONE tier of beams. Two seat beams east-west on the piers at the library-derived joist soffit; 2x8 joists @12in o.c. run NORTH-SOUTH straight on them, cantilevering 9-1/2in south and 7-1/4in north. BM-BW-FE, the east edge beam, runs north-south in the SAME plane (not a second tier), seat to seat; nothing crosses the garage stem or W-G-S. D-G-SERVICE SWINGS OUT onto this deck, hinged on its WEST jamb, with a frame-mounted overhead stop-only set at 87deg: no interior landing (IRC R311.7.6 exception); ST-G-SERVICE rises straight to the threshold and its stringer heads seat on the stem-top ledge inside W-G-S (notes/garage_service_door_outswing.md). The deck ties to the garage on two lines (params/landing_tie.py). No bearing on the house and none on the garage. TWO PIER DEPTHS ON PURPOSE: the three HOUSE-side piers (PT-BW-W/E and the east-line pier) bear at -9ft 11-7/16in (pad bottoms, the house footing underside) and must be cast WITH the basement excavation while it is open — casting them after backfill undermines the house footing, and the depth costs shaft only because the hole is already there. The three GARAGE-side piers (PT-BW-GW/GE and the east-line pier) bear at -7ft 4in (pad bottoms; pad tops level with the garage strip footings' tops) and are cast with the garage foundation. " + landing_note(EAST_POST_SYSTEM) + ". Hold deck boards 1/2in off the house cladding and let the gap drain")),

    Annotation(uid="BWAN02AAAA", tag="AN-BW-TIERS", position=pt(ft(16), ft(39)),
               text="TERRACE: 5 equal 6.6in rises off the SL-WK-C entry walk; four CAST tiers (SL-BW-TIER1..4) in ONE stepped placement with the walks, 18in going, wedding-caked so each is fully bedded on the one below, on a compacted washed-rock base — NOT frost-founded, and that is a decision: a monolithic pour moves as one piece and the joint that matters is at the TOP, against a deck landing on piers that will not move (R311.7.5.1 allows 3/8in of riser variation and that joint is where it is spent). EXPOSED_MIX (ACI 318-19 F3+C2), broom finish, 1/4in per foot of cross-fall to the east. No wood, no stringers, no piers — the eight drilled piers this replaced stood east of the flight under open ground"),
    # Minted with typehaus.model.ids.new_uid().
    Annotation(uid="SG5P5RZE02", tag="AN-BW-HETA-TRIM", position=pt(ft(12), ft(41)),
               text="HOLD POINT, HETA20Z SEAT TIES (CN-BW-TIE-EA/EB/GEA/GEB): set each 16in strap in the pour from a template of the seat beam's faces; after the beam is on its 3/4in SS316 pack, FIELD-TRIM each strap flush with the beam top (8in above the pier top) BEFORE the joists go on. No HETA12/16 is published in ZMAX or stainless (G90 only, wrong against KDAT), so the 20 is cut. Nail 6 - 16d HDG per strap, 12 per pair (FL11473 Table 3): the LOWEST FOUR holes (Table 2 note 2) then the next two up, all on the beam face; confirm the lowest hole stands above the pack, and confirm the trim with Simpson before the pour."),
    Annotation(uid="BWAN04AAAA", tag="AN-BW-KDAT", position=pt(ft(9), ft(41)),
               text="ALL KDAT: 304 stainless fasteners (IRC R317.3.1), with connector-specific fasteners as scheduled; TREX walking boards use 316 stainless Cap-Tor xd per AN-G-COMPOSITE-DECKING; butyl joist tape over every beam/rim top; field-treat every cut end, notch and hole with 2% copper naphthenate per AWPA M4 (IRC R317.1.1 — required, not advisory); finish with a PIGMENTED penetrating oil on installation, recoat 2-3yr horizontal. NO silicate/'liquid glass' — it is a masonry densifier, leaches from wood and adds no UV protection. W-BW-SCREEN is KDAT 2x4 framing with CDX and corrugated on the WEST face, and directly mounted white-painted 3/4in exterior MDO on the EAST face, recessed 1-1/4in behind the exposed timber. One solid KDAT SP No.2 6x6 lower centre timber lines up with the upper centre post and the chord posts on both faces; five 2x4 edge nailers. The MDO stops at the north chord post: the end pack and the garage ties north of it stay exposed. FRAME THE LOWER TIMBER IN LIKE A STUD: four S10ACN through each plate into its ends, on the flat, before the band goes on. Use removable stainless face screws into framing, sealed cut edges and holes, and compatible exterior primer/topcoats on both faces. No east WRB, rails or ventilation cavity. Keep the garage tie block and its bolts accessible. See notes/entry_screen_mdo.md. W-BW-SCREEN-SKIRT carries the west corrugated down over the sill, the seat beams and the two column standoff bases, stopping 1in ABOVE the pier tops — do not seal that edge to the concrete, it is how the flutes drain and the column bases dry"),
]

# W-BW-SCREEN: a sheathed KDAT wall from the joist plane up to SCREEN_PANEL_TOP_FT. It is the
# canopy's N-S lateral system, the deck's west guard and the closure over the deck framing
# (plan/assemblies/entry_screen.py::ENTRY_SCREEN_WALL). The band above is SB-BW-BAND
# (params/entry_band_brace.py).
#
# It stands on BM-BW-SCSILL, a 2x8 between the two columns that is also the deck's west rim: a
# sill plate lower down would share space with the seats and joists
# (`structural.member_interference`).
# Shear still reaches concrete in one step: the sill lands on the seats, each directly over a pier.
SCREEN_START_Y_FT = DECK_SHEET_SOUTH_Y_FT
# Ends on W-G-S's corrugated face, not its node line (E2-101).
SCREEN_END_Y_FT = GARAGE_CLADDING_Y_FT
SCREEN_PANEL_NODES = [
    Node(uid="BWNS01AAAA", tag="N-BW-SCREEN-S",
         position=pt(ft(SCREEN_AXIS_X_FT), ft(SCREEN_START_Y_FT)), open_end=True),
    Node(uid="BWNS02AAAA", tag="N-BW-SCREEN-N",
         position=pt(ft(SCREEN_AXIS_X_FT), ft(SCREEN_END_Y_FT)), open_end=True),
]
# Filed on the GARAGE storey, with the RF-BW-CANOPY it braces (a roof belongs to a storey). Braced
# wall lines and the overall dimension chain are derived per storey: filed on `main`, this
# freestanding panel added a fifth perimeter line and stretched the chain. `base_elevation` is
# absolute.
GARAGE_STOREY_ELEMENTS = []
# The stud line holds the datum: the 2x4s die into PT-BW-CW/-CNW flush with their west faces
# (owner, 2026-11-10), so the west corrugated shares a plane with the garage's own panel.
# `face("stud-ext", offset=inch(-1.75))` is a hardcoded half of the 2x4 (same idiom and trap as
# `W-B-CS`/`W-B-CS3` in params/main_deck.py): if it stops matching the stud, the axis slides off
# SCREEN_AXIS_X_FT silently. The west cladding face resolves to SCREEN_CLADDING_WEST_X_FT, which
# the skirt reads. Both columns carry `within_wall="W-BW-SCREEN"`, so the plates are cut at their
# faces.
#
# `ShearPanelSpec` is the fastener schedule that lets the engine split the canopy shear between
# panel and columns (IBC 2018 1604.4). The 15/32" SDPWS row is quoted for the 5/8" panel and the
# softer plywood G_a is used, which gives the columns the larger share. `anchorage_slip` is an
# assumption (1/16" bearing take-up at the two 6x6s), not a published slip for the base.
SCREEN_PANEL = Wall(
    uid="BWWS01AAAA", tag="W-BW-SCREEN",
    start_node="N-BW-SCREEN-S", end_node="N-BW-SCREEN-N",
    assembly="ENTRY_SCREEN_WALL", base_elevation=ft(DECK_JOIST_TOP_FT),
    top=ft(SCREEN_PANEL_TOP_FT - DECK_JOIST_TOP_FT), guard=True,
    alignment=face("stud-ext", offset=inch(-1.75)),
    shear_panel=ShearPanelSpec(
        sheathing_layer="cdx-out",
        fastening=('8d common (0.131" x 2 1/2") at 4" o.c. at every panel edge and 12" '
                   'o.c. in the field, panel edges BLOCKED, the sheet nailed to both 6x6 '
                   'chords; 2x4 KDAT framing at 16" o.c. — the WEST face alone, the east '
                   'MDO is finish and is not counted'),
        source=("AWC SDPWS-2015 Table 4.3A, wood structural panels - sheathing, 15/32\" "
                "with 8d at 4\" edges, v_w 530 plf nominal / 2.0 — quoted for this 5/8\" "
                "panel because thicker sheathing at the same schedule is not weaker; G_a "
                "kept at the 6\" plywood row's 11.0, the softer end"),
        unit_shear_asd_plf=265.0,
        apparent_stiffness_kips_per_in=11.0,
        chords=("PT-BW-CW and PT-BW-CNW, the two 6x6 KDAT columns this wall is framed "
                "around (`within_wall`), 4.979ft centre to centre, each on a cast-in "
                "CBSTQ66Z-SDS2 in its 14in pier; the band over the panel is the slat brace "
                "SB-BW-BAND of params/entry_band_brace.py (notes/canopy_west_band.md)"),
        chord_refs=("PT-BW-CW", "PT-BW-CNW"),
        chord_member="6x6", chord_plies=1,
        anchorage_slip=inch(0.0625),
        # Hold-down: the cast-in CBSTQ66Z-SDS2 under each chord. Its cracked uplift (ESR-3050
        # Table 2, 3,060 lb) is through the concrete, so no separate bolt or ACI Ch. 17 row.
        holdown="CBSTQ66Z-SDS2",
        aspect_ratio_limit=3.5,
    ),
)
GARAGE_STOREY_ELEMENTS.extend([*SCREEN_PANEL_NODES, SCREEN_PANEL, *FINISH_ELEMENTS])

# W-BW-SCREEN-SKIRT carries the west skin down over the sill, seat beams and column bases, keeping
# bulk water off the treated wood and the CBSTQ bases (still reachable from the east). Its bottom
# edge stops above the pier tops and stays OPEN: that is how the flutes drain and the bases dry.
# Do not seal it to the concrete. Its own element and nodes (`open_end=True`): sharing
# N-BW-SCREEN-S/-N would put two walls on one node pair. No `stacks_on`: the gap between the walls
# is zero. `haus fmt` does not visit params/*.py, so these uids are hand-assigned (BW namespace).
# Base: 1" over the seat soffit plane.
SCREEN_SKIRT_BASE_FT = BEARING_TOP_FT + 1 / 12          # -1'-2 1/2"
SCREEN_SKIRT_NODES = [
    Node(uid="BWNS03AAAA", tag="N-BW-SKIRT-S",
         position=pt(ft(SCREEN_CLADDING_WEST_X_FT + 0.875 / 24), ft(SCREEN_START_Y_FT)),
         open_end=True),
    Node(uid="BWNS04AAAA", tag="N-BW-SKIRT-N",
         position=pt(ft(SCREEN_CLADDING_WEST_X_FT + 0.875 / 24), ft(SCREEN_END_Y_FT)),
         open_end=True),
]
SCREEN_SKIRT = Wall(
    uid="BWWS02AAAA", tag="W-BW-SCREEN-SKIRT",
    start_node="N-BW-SKIRT-S", end_node="N-BW-SKIRT-N",
    assembly="ENTRY_SCREEN_SKIRT", base_elevation=ft(SCREEN_SKIRT_BASE_FT),
    top=ft(DECK_JOIST_TOP_FT - SCREEN_SKIRT_BASE_FT),
)
GARAGE_STOREY_ELEMENTS.extend([*SCREEN_SKIRT_NODES, SCREEN_SKIRT])

# Each seat-beam bearing is two parts. The SS316-SHIM-35 pack is the BEARING: it holds the treated
# soffit off the pour (water cannot sit in the joint, copper never touches concrete) and takes
# the levelling tolerance. The HETA20Z pair is the TIE (`structural.uplift_path_coverage`): spoons
# cast into the pier top, straps nailed to the beam faces with HDG 16d; cast in because the
# HGAM10's Titen Turbo screws may not be exposed to weather (column_head_connector_options.md).
# The pack is a solid: piers are cast STANDOFF_PACK_IN under the soffit (`PIER_TOP_FT`), the
# marker runs pier top to pack top (`elevation` is its centre). At W/GW the beam end sits in the
# LUS26-2Z, so the pack stops one 18 ga seat under the soffit and an 18 ga SS316 strip fills
# the rest.
_HANGER_SEAT_FT = SHEET_THICKNESS_IN[LUS_DIMENSIONS["LUS26-2"].gauge] / 12
SEAT_BEARINGS = []
for _i, (_t, _x, _y, _beam) in enumerate((
    # W/GW: the 3 1/2" pack starts at the beam end, clear of the base strap.
    ("W", SEAT_START_X_FT + 1.75 / 12, HOUSE_SEAT_Y_FT, "BM-BW-HOUSE-SEAT"),
    ("E", LANDING_EAST_FT, HOUSE_SEAT_Y_FT, "BM-BW-HOUSE-SEAT"),
    ("GW", SEAT_START_X_FT + 1.75 / 12, GARAGE_SEAT_Y_FT, "BM-BW-GARAGE-SEAT"),
    ("GE", LANDING_EAST_FT, GARAGE_SEAT_Y_FT, "BM-BW-GARAGE-SEAT"),
)):
    _pack_top_ft = BEARING_TOP_FT - (_HANGER_SEAT_FT if _t in ("W", "GW") else 0.0)
    SEAT_BEARINGS.append(Connector(
        uid=f"BWSD{_i}AAAAAA"[:10], tag=f"CN-BW-STDF-{_t}",
        kind=ConnectorKind.BEARING_STANDOFF, position=pt(ft(_x), ft(_y)),
        elevation=ft((PIER_TOP_FT + _pack_top_ft) / 2), size="SS316-SHIM-35",
        connects=(_beam, f"PT-BW-{_t}")))
    # None on the west piers: the seat beam hangs off PT-BW-CW/-CNW on an LUS26-2Z, and that
    # column's cast-in CBSTQ66Z-SDS2 already ties it to the pier.
    if _t in ("W", "GW"):
        continue
    # A pair, one per beam face: a one-sided tie is an eccentric rotation restraint (NDS 3.3.3).
    # FL11473 Table 3 rates the pair as one installation on a 2- or 3-ply member with anchors
    # >= 3" apart; the 2-2x8 seat beam is 3", the minimum. Authored at the faces (1-1/2" off the
    # centreline). `elevation` is the POUR top; the strap is field-trimmed at the beam top
    # (`AN-BW-HETA-TRIM`).
    for _side, _dy in (("A", -1.5), ("B", 1.5)):
        SEAT_BEARINGS.append(Connector(
            uid=f"BWS{_side}{_i}AAAAAA"[:10], tag=f"CN-BW-TIE-{_t}{_side}",
            kind=ConnectorKind.HURRICANE_TIE,
            position=pt(ft(_x), ft(_y) + inch(_dy)),
            elevation=ft(PIER_TOP_FT), size="HETA20Z",
            connects=(_beam, f"PT-BW-{_t}")))

# West glulam ends flush on both posts: ACE6Z end caps, MAX nailing (ESR-2604 §3.1.3). The
# across-beam direction is the A35Z angles of params/entry_band_brace.py.
COLUMN_CAPS = [
    Connector(uid=f"BWCC{_i}AAAAAA"[:10], tag=f"CN-BW-CAP-{_s}",
              kind=ConnectorKind.POST_CAP, position=pt(ft(_x), ft(_y)),
              elevation=ft(HEADER_SOFFIT_FT), size=_size,
              connects=("BM-BW-RW", f"PT-BW-C{_s}"))
    for _i, (_s, _x, _y, _size) in enumerate((("W", LANDING_WEST_FT, PIER_LINE_Y_FT, "ACE6Z"),
                                              ("NW", LANDING_WEST_FT, GARAGE_SEAT_Y_FT, "ACE6Z")))
]

# The seat beams hang off the canopy columns: each is authored to the column line, so its end sits
# inside the 6x6. A hanger flange has no model representation; an authored Connector makes
# `_hung_pairs` clear exactly this pair and no other. LUS26-2Z on the double-2x8 seat beams, LUS28Z
# on the single-2x8 sill (demand: notes/north_entry_piers.md §12). ZMAX, not stainless (the beam
# bears on the pack, so a coating failure is not catastrophic), not HUC (made for a pour).
# Hanger bottoms rest on the pack (`_HANGER_SEAT_FT`), so gravity bears on the pier. At CW/CNW the
# hanger is nailed over two 11/32" treated-plywood strips either side of the CBSTQ strap, a field
# item unmodelled like the flange (notes/canopy_west_band.md, 2026-11-06 amendment (b)).
SEAT_BEAM_HANGERS = [
    Connector(uid="BWSH01AAAA", tag="CN-BW-HGR-CW", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(LANDING_WEST_FT), ft(HOUSE_SEAT_Y_FT)),
              elevation=ft(SEAT_TOP_FT), size="LUS26-2Z",
              connects=("BM-BW-HOUSE-SEAT", "PT-BW-CW")),
    Connector(uid="BWSH02AAAA", tag="CN-BW-HGR-CNW", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(LANDING_WEST_FT), ft(GARAGE_SEAT_Y_FT)),
              elevation=ft(SEAT_TOP_FT), size="LUS26-2Z",
              connects=("BM-BW-GARAGE-SEAT", "PT-BW-CNW")),
    Connector(uid="BWSH03AAAA", tag="CN-BW-HGR-SCS-S", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(SCREEN_AXIS_X_FT), ft(PIER_LINE_Y_FT + COLUMN_HALF_FT)),
              elevation=ft(SEAT_TOP_FT), size="LUS28Z",
              connects=("BM-BW-SCSILL", "PT-BW-CW")),
    Connector(uid="BWSH04AAAA", tag="CN-BW-HGR-SCS-N", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(SCREEN_AXIS_X_FT), ft(GARAGE_SEAT_Y_FT - COLUMN_HALF_FT)),
              elevation=ft(SEAT_TOP_FT), size="LUS28Z",
              connects=("BM-BW-SCSILL", "PT-BW-CNW")),
]

# Each column carries two hangers on adjacent faces (the seat beam on its east face, BM-BW-SCSILL
# on the face square to it); both land at SEAT_TOP_FT. Why the sill hangs at all: the beam in
# params/north_entry_frame.py.

# `cast` variant only: no wood under BM-BW-RE, so an AC/ACE cap does not apply. The joint is the
# seat beams' own: a shim pack and a cast-in HETA20Z pair.
def _cast_east_head_parts():
    """The `cast` variant's joint: pack + cast-in HETA20Z pair, the column cast one pack low."""
    out = []
    for _i, (_t, _y) in enumerate((("E", PIER_LINE_Y_FT), ("NE", GARAGE_SEAT_Y_FT))):
        out.append(Connector(
            uid=f"BWEB{_i}AAAAAA"[:10], tag=f"CN-BW-STDF-R{_t}",
            kind=ConnectorKind.BEARING_STANDOFF,
            position=pt(ft(ROOF_COLUMN_EAST_X_FT), ft(_y)),
            elevation=ft(HEADER_SOFFIT_FT - STANDOFF_PACK_IN / 24), size="SS316-SHIM-35",
            connects=("BM-BW-RE", f"PT-BW-R{'E' if _t == 'E' else 'NE'}")))
        # Paired as at SEAT_BEARINGS; the header runs north-south, so the offset (half the
        # glulam) is in x. Prefix BWQ, not BWE: "BWEB0AAAAA" is CN-BW-STDF-RE's uid.
        for _side, _dx in (("A", -2.75), ("B", 2.75)):
            out.append(Connector(
                uid=f"BWQ{_side}{_i}AAAAAA"[:10], tag=f"CN-BW-TIE-R{_t}{_side}",
                kind=ConnectorKind.HURRICANE_TIE,
                position=pt(ft(ROOF_COLUMN_EAST_X_FT) + inch(_dx), ft(_y)),
                elevation=ft(HEADER_SOFFIT_FT - STANDOFF_PACK_IN / 12), size="HETA20Z",
                connects=("BM-BW-RE", f"PT-BW-R{'E' if _t == 'E' else 'NE'}")))
    return out


# EAST_POST_SYSTEM picks what BM-BW-RE lands on: `steel` (welded HSS saddle on a base plate),
# `kdat` (ACE6Z caps and CBSTQ66Z-SDS2 bases, as the west pair) or `cast` (the pack and HETA pair
# above). params/east_posts.py holds all three.
EAST_HEADER_BEARINGS = east_head_parts(
    EAST_POST_SYSTEM, x_ft=ROOF_COLUMN_EAST_X_FT,
    stations={"RE": PIER_LINE_Y_FT, "RNE": GARAGE_SEAT_Y_FT},
    header_soffit_ft=HEADER_SOFFIT_FT, cast_parts=_cast_east_head_parts)

# West column bases: cast-in CBSTQ66Z-SDS2 (ZMAX). They are the panel's hold-downs, so uplift must
# be a published row through the concrete (ESR-3050 Table 2, 3,060 lb cracked). `axis="y"` puts
# F2 (1,270 lb, C-C-2026 p. 85 fn. 5) along the screen, where in-plane base shear arrives; the
# strap leaves are then on the E/W faces, so the seat beams stop short of them
# (north_entry_frame.SEAT_START_X_FT). Straps >= 3" from the pier edge (fn. 4), pier cage on the
# diagonals (canopy_west_band.md §5).
COLUMN_BASES = [
    Connector(uid=f"BWCB{_i}AAAAAA"[:10], tag=f"CN-BW-BASE-{_s}",
              kind=ConnectorKind.POST_BASE, position=pt(ft(_x), ft(_y)),
              elevation=ft(PIER_TOP_FT), size="CBSTQ66Z-SDS2", axis="y",
              connects=(f"PT-BW-C{_s}", _pier))
    for _i, (_s, _x, _y, _pier) in enumerate((
        ("W", LANDING_WEST_FT, PIER_LINE_Y_FT, "PT-BW-W"),
        ("NW", LANDING_WEST_FT, GARAGE_SEAT_Y_FT, "PT-BW-GW"),
    ))
]


# Truss bearings are authored (stainless H2.5ASS), not derived: `takeoff/uplift.py::
# bearing_uplift_tie_rows` would derive commodity H2.5A, the wrong part for treated wood at a
# salted entry, and a derived row draws nothing. Authoring all of them stands the derived rule
# down (`authored_joints` is pairwise). One tie per truss per header; gross uplift is in
# notes/north_entry_piers.md Sec 4. The stainless tie has no allowable in `library/hardware/`.
#
# Three trusses at the layout's 24" stations from TRUSS_DATUM_Y_FT. `RF-BW-CANOPY` authors
# `gable_ends=()`, so no fourth station stands at the headers' north ends; the deck bridges the
# last bay to RF-GARAGE's own gable truss. Truss 1's south face is flush with the beam end, so
# its tie goes on its north face, clear of the end grain.
TRUSS_STATION_Y_FT = (TRUSS_DATUM_Y_FT, TRUSS_DATUM_Y_FT + 2.0, TRUSS_DATUM_Y_FT + 4.0)
_TRUSS_HALF_WIDTH_FT = 0.75 / 12
_TIE_Y_FT = (TRUSS_STATION_Y_FT[0] + _TRUSS_HALF_WIDTH_FT, *TRUSS_STATION_Y_FT[1:])
TRUSS_TIES = [
    Connector(uid=f"BWTT{_i}{_s}AAAA"[:10], tag=f"CN-BW-TRTIE-{_s}{_i + 1}",
              kind=ConnectorKind.HURRICANE_TIE, position=pt(ft(_x), ft(_y)),
              elevation=ft(HEADER_TOP_FT), size="H2.5ASS",
              connects=("RF-BW-CANOPY", f"BM-BW-R{_s}"))
    for _s, _x in (("W", LANDING_WEST_FT), ("E", ROOF_COLUMN_EAST_X_FT))
    for _i, _y in enumerate(_TIE_Y_FT)
]

# Garage joint: a tie, not a bearing. These carry in-plane shear and tension across the joint;
# no gravity crosses it (`bearing_refs` names no garage element). The two roofs are one plane and
# are tied as one; the only movement joint is at the HOUSE end.
# LSTA24 (ESR-2105 Table 3) at 4'-0" o.c. over the 24'-0" joint, none at the ridge: a flat strap
# cannot seat on the peak (its tag stays retired). Demand is graded in `lateral_system/
# RF-BW-CANOPY` (notes/north_entry_canopy_lateral.md §8e). Bevelled 2-ply SPF nailers back the
# outer six holes on each leg, clear of the garage gable and wood end distances; installed rating
# 1235 x 12/18 = 823 lb. Along-joint shear uses the continuous deck boundary nailing, not this
# axial rating. End straps sit on the centre of the 3" 2-2x8 collector blocks, flush to each
# header's inboard face: 1-1/4" inboard of the glulam centreline.
JOINT_TIE_COUNT = 7
_JOINT_INDICES = (0, 1, 2, 4, 5, 6)
_END_STRAP_INSET_FT = (5.5 - 3.0) / 2 / 12


def _joint_x_ft(i):
    if i == 0:
        return LANDING_WEST_FT + _END_STRAP_INSET_FT
    if i == JOINT_TIE_COUNT - 1:
        return ROOF_COLUMN_EAST_X_FT - _END_STRAP_INSET_FT
    return LANDING_WEST_FT + i * (ROOF_COLUMN_EAST_X_FT - LANDING_WEST_FT) / (JOINT_TIE_COUNT - 1)


JOINT_TIES = [
    Connector(uid=f"BWJT{_i:02d}AAAA"[:10], tag=f"CN-BW-JOINT-{_i + 1}",
              # TENSION_TIE, not HOLD_DOWN: a HOLD_DOWN naming a roof reads as "this roof's
              # bearing uplift is authored" (`structural.uplift_path_coverage`,
              # `takeoff/uplift.py`) and stands down RF-GARAGE's derived H2.5A truss ties.
              kind=ConnectorKind.TENSION_TIE,
              position=pt(ft(_joint_x_ft(_i)), ft(GARAGE_Y_SOUTH.feet)),
              roof_mount="RF-BW-CANOPY", size="LSTA24",
              connects=("RF-BW-CANOPY", "RF-GARAGE"),
              source="canopy_garage_diaphragm.md §3b — axial tie direct to 2-ply SPF nailers (2-2x8 collector blocks at the ends) before deck; six outer 0.148x2.5in HDG nails per leg, 823lb installed capacity")
    for _i in _JOINT_INDICES
]

# One LTP4 per strap station carries the canopy's E-W shear from RF-GARAGE's south gable frame into
# W-G-S (C-C-2019 p.280, SPF/HF 450 lb; notes/canopy_garage_diaphragm.md §3c). Nailed to the
# chord's and plate's inside faces, not over sheathing. TENSION_TIE for the JOINT_TIES' reason.
GABLE_CLIP_UIDS = ("644MFCK8V1", "0A22GEE3V6", "BHRTMX39H9", "64FMWMATE6", "DZ69EEJ40H",
                   "3DMD5550VF", "ZMTAAA1TKP")
GABLE_CLIPS = [
    Connector(uid=_uid, tag=f"CN-BW-GCLIP-{_i + 1}", kind=ConnectorKind.TENSION_TIE,
              position=pt(ft(LANDING_WEST_FT + _i * (ROOF_COLUMN_EAST_X_FT - LANDING_WEST_FT)
                             / (JOINT_TIE_COUNT - 1)), ft(GARAGE_Y_SOUTH.feet)),
              elevation=ft(HEADER_TOP_FT), size="LTP4", connects=("RF-GARAGE", "W-G-S"),
              source="canopy_garage_diaphragm.md §3c — RF-GARAGE's south gable frame into W-G-S's top plate; the canopy's E-W shear")
    for _i, _uid in enumerate(GABLE_CLIP_UIDS)
]

# One continuous east-canopy run; the supplier must still size the drift-load system. Rake
# oversails are 1-3/8" south and 6-1/8" north. The shared garage seam register needs a 7-5/8"
# south setback to keep the first clamp's cantilever under 8"; north keeps 2".
SNOW_RETENTION_EAST_X_FT = EAST_CLAMP_X_IN / 12  # 4 inches inside the roof eave
SNOW_RETENTION_SOUTH_SETBACK_IN = 7.625
SNOW_RETENTION_NORTH_SETBACK_IN = 2.0
SNOW_RETENTION_SOUTH_Y_FT = (TRUSS_DATUM_Y_FT - 1.375 / 12
                           + SNOW_RETENTION_SOUTH_SETBACK_IN / 12)
SNOW_RETENTION_NORTH_Y_FT = (HEADER_NORTH_Y_FT + 6.125 / 12
                           - SNOW_RETENTION_NORTH_SETBACK_IN / 12)
SNOW_RETENTION = [
    Connector(uid="BWNSE1AAAA", tag="CN-BW-SNOW-E-1",
              kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(SNOW_RETENTION_EAST_X_FT),
                          ft((SNOW_RETENTION_SOUTH_Y_FT + SNOW_RETENTION_NORTH_Y_FT) / 2)),
              axis="y", size="S-5! ColorGard", connects=("RF-BW-CANOPY",),
              snow_retention=SnowRetentionSpec(
                  length=ft(SNOW_RETENTION_NORTH_Y_FT - SNOW_RETENTION_SOUTH_Y_FT)),
              source="north_entry_structure.md — provisional continuous east entrance run")
]

MAIN_ELEMENTS = [*FRAME_ELEMENTS, FLOOR, TIERS, *TIER_SLABS,
                 *RAILINGS, *SEAT_BEARINGS, *COLUMN_BASES,
                 *COLUMN_CAPS, *SEAT_BEAM_HANGERS, *EAST_HEADER_BEARINGS,
                 *TRUSS_TIES, *JOINT_TIES, *GABLE_CLIPS, *LANDING_TIES,
                 *SNOW_RETENTION, *NOTES]
