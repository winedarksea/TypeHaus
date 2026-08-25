# haus: editable
# Attic — habitable hot-roofed cathedral storey (WP3.1, WP3.11); 2x6 envelope walls.
# 5' knee walls east/west (eave sides), gable walls north/south frame ToRoof,
# ridge runs N-S over the center wall line, 4:12, zero overhang (first-class).
from typehaus import (
    Alarm,
    AlarmKind,
    Beam,
    Door,
    DeckLayer,
    FloorOpening,
    FloorSystem,
    FollowRoof,
    JoistSpec,
    Node,
    Occupancy,
    Pitch,
    Railing,
    RailingKind,
    Roof,
    RoofForm,
    Room,
    Stair,
    StructuralRole,
    ToRoof,
    Wall,
    Window,
    face,
    from_node,
    ft,
    inch,
    pt,
)

NODES = [
    Node(uid="CAN001AAAA", tag="N-A-SW", position=pt(ft(0), ft(0))),
    Node(uid="CAN002AAAA", tag="N-A-S1", position=pt(ft(10), ft(0))),
    Node(uid="CAN003AAAA", tag="N-A-S2", position=pt(ft(18), ft(0))),
    # Vestibule screen line, 22'-8" not the source's 22.31 (2026-08-01 gable pass): W-A-S4
    # starts here and a wall's stud grid lays out from its start node, so this x sets the
    # phase of the east gable's bay centres. 22'-8" = 272" = 16x17, keeping W-A-S4 and
    # W-A-S1 in phase so they mirror exactly about x=18' (22'-4" was 4" out of phase). The
    # screen closes no room polygon (see W-A-VE), so the move is free and only widens the
    # gap to the stair well at x 21'-1 3/4".
    Node(uid="CAN011AAAA", tag="N-A-V1", position=pt(ft(22, 8), ft(0))),
    Node(uid="CAN004AAAA", tag="N-A-SE", position=pt(ft(36), ft(0))),
    Node(uid="CAN005AAAA", tag="N-A-E1", position=pt(ft(36), ft(9))),
    Node(uid="CAN006AAAA", tag="N-A-NE", position=pt(ft(36), ft(36))),
    Node(uid="CAN007AAAA", tag="N-A-N1", position=pt(ft(18), ft(36))),
    Node(uid="CAN008AAAA", tag="N-A-NW", position=pt(ft(0), ft(36))),
    # Den north wall y=5'-7" (source 5.611); band wall y=9'-0" (source 9.228). 9'-0" is 12"
    # out of phase with the 16" module, costing the east knee pair its mirror (WIN-A-E-N) —
    # kept anyway: W-A-SN's south face closes FO-A-STAIR's north edge, and moving to 9'-4"
    # opens 3'-0" of unguarded well (code.R312_1_guard, caught 2026-08-15).
    Node(uid="CAN009AAAA", tag="N-A-C1", position=pt(ft(18), ft(5, 7))),
    Node(uid="CAN012AAAA", tag="N-A-C2", position=pt(ft(18), ft(9))),
    Node(uid="CAN010AAAA", tag="N-A-D1", position=pt(ft(10), ft(5, 7))),
    Node(uid="CAN013AAAA", tag="N-A-V2", position=pt(ft(22, 8), ft(5, 7))),
    # A legitimate wing-wall terminus: the vestibule's north screen stops at the stair
    # well's west edge, exactly as the source's Den north wall does.
    Node(uid="CAN014AAAA", tag="N-A-V3", position=pt(ft(21, 2), ft(5, 7)),
         open_end=True),
]

WALLS = [
    # Gable ends (south/north) — raked studs, sloped plates via ToRoof (WP3.11).
    Wall(uid="CAW101AAAA", tag="W-A-S1", start_node="N-A-SW", end_node="N-A-S1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S1"),
    Wall(uid="CAW102AAAA", tag="W-A-S2", start_node="N-A-S1", end_node="N-A-S2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S1"),
    Wall(uid="CAW103AAAA", tag="W-A-S3", start_node="N-A-S2", end_node="N-A-V1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S2"),
    Wall(uid="CAW114AAAA", tag="W-A-S4", start_node="N-A-V1", end_node="N-A-SE",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S2"),
    Wall(uid="CAW104AAAA", tag="W-A-N1", start_node="N-A-NE", end_node="N-A-N1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-N1"),
    Wall(uid="CAW105AAAA", tag="W-A-N2", start_node="N-A-N1", end_node="N-A-NW",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-N2"),
    # Knee walls (east/west eave sides) — 5', carry the low roof edge.
    Wall(uid="CAW106AAAA", tag="W-A-E1", start_node="N-A-SE", end_node="N-A-E1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(5),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-E1"),
    Wall(uid="CAW107AAAA", tag="W-A-E2", start_node="N-A-E1", end_node="N-A-NE",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(5),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-E2"),
    Wall(uid="CAW108AAAA", tag="W-A-W1", start_node="N-A-NW", end_node="N-A-SW",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(5),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-W1"),
    # Center bearing wall under the ridge, full length. NOT a partition: RB-HOUSE bears on
    # it continuously, making this a structural-ridge roof (rafters simply span ridge->knee
    # wall, no thrust on the 5' knee walls). Opening this line without a beam would dump
    # ~1.5 klf of thrust into the knee walls. 2x6 to match the bearing stack below (W-S-C1/C3).
    Wall(uid="CAW109AAAA", tag="W-A-C1", start_node="N-A-S2", end_node="N-A-C1",
         assembly="CATLIN_INT_2X6_BRG", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-C1"),
    Wall(uid="CAW115AAAA", tag="W-A-C1B", start_node="N-A-C1", end_node="N-A-C2",
         assembly="CATLIN_INT_2X6_BRG", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-C2"),
    # y 9'..36'. Between y=22'-4" and 30'-10" the storey below carries no wall — BM-S-HALL
    # (three plies 11-7/8" LVL) is there instead — so this wall (and RB-HOUSE through it)
    # lands on that beam. `stacks_on` names W-S-C4B since the tiebreaker needs a *wall*.
    Wall(uid="CAW110AAAA", tag="W-A-C2", start_node="N-A-C2", end_node="N-A-N1",
         assembly="CATLIN_INT_2X6_BRG", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-C4B"),
    # South rooms: den (west of center) + study (east of center), framed to the roof deck.
    # Since 2026-07-31 the den follows the roof too (Room.ceiling below) — it lost its
    # 7'-6" dropped ceiling, which would have buried the south gable juliet pair's 8'-0" head.
    #
    # THE DEN MOVED WEST off its source footprint (x 13'-9"..22'-4") because that straddles
    # the RB-HOUSE bearing line (W-A-C1/C1B/C2), which cannot open up. Shifted to
    # x 10'-0"..18'-0", y 0..5'-7", it keeps both source dimensions (8'-0" x 4'-10 1/2" clear)
    # and lets RM-A-WEST run full depth for x 0..10' — the source's 588.12 sf west loft.
    # Costs ~21 sf: the Den now takes 8' of the west loft's south end vs. the source's 4'-3".
    Wall(uid="CAW111AAAA", tag="W-A-DN", start_node="N-A-D1", end_node="N-A-C1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    Wall(uid="CAW112AAAA", tag="W-A-DW", start_node="N-A-S1", end_node="N-A-D1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    Wall(uid="CAW113AAAA", tag="W-A-SN", start_node="N-A-C2", end_node="N-A-E1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    # Stair vestibule screen: the source's Den east + north walls, kept near their source
    # position (y 5.611 exact; x moved 22.31 -> 22'-8" by the 2026-08-01 gable pass, see
    # N-A-V1) even though the Den itself moved west. Wraps ST-S2A's head so the arrival is
    # enclosed on the Study side. A dangling pair closing no polygonized face, so
    # RM-A-STUDY still reads as one room — matching the source's 123.39 sf "Study".
    Wall(uid="CAW116AAAA", tag="W-A-VE", start_node="N-A-V1", end_node="N-A-V2",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    Wall(uid="CAW117AAAA", tag="W-A-VN", start_node="N-A-V3", end_node="N-A-V2",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
]

OPENINGS = [
    Door(uid="CAD201AAAA", tag="D-A-HALVES", host="W-A-C2", type_ref="DT-INT-SWING32",
         position=from_node("N-A-N1", ft(4))),
    Door(uid="CAD202AAAA", tag="D-A-DEN", host="W-A-DN", type_ref="DT-INT-SWING30",
         position=from_node("N-A-D1", ft(1))),
    # The band wall's opening onto the stair head — the source's 2'-7 1/2" gap at
    # x 18'-6"..21'-1 3/4", the only way between the east loft and the stair vestibule.
    Door(uid="CAD203AAAA", tag="D-A-STUDY", host="W-A-SN", type_ref="DT-INT-SWING30",
         position=from_node("N-A-C2", ft(0, 8.875))),                 # x 19'-11 7/8"
    Door(uid="CAD204AAAA", tag="D-A-VEST", host="W-A-VE", type_ref="DT-INT-SWING30",
         position=from_node("N-A-V1", ft(0, 11.25))),                 # y 2'-2 1/4"
    # South gable, 2026-08-01 pass: two WT-1448 flanking the juliet pair below — four
    # openings, mirror-symmetric about the ridge (CLAUDE.md's "gables read symmetric" rule).
    # Replaced an earlier pass of four WT-1424 capping the lower storeys' four south columns
    # (x 3'-4", 8'-8", 28'-0", 33'-4"): 14x24 next to the 18x64 juliet pair read as vents,
    # on a second head line, with 8' of blank gable between groups — and it wasn't symmetric.
    # The corner pair (x 3'-4"/33'-8") was cut: the 4:12 rake leaves only ~6' of wall there,
    # not enough for anything that doesn't look like a stamp. The survivors (x 8'-8" and its
    # mirror) took WT-1448 instead of the juliet family (which they would share) because an 18"
    # RO needs a jamb pack whose header, at the nearest stud line, is 1.8" too tall to clear
    # the rake there — a 14" RO fits inside a bay and needs no pack.
    # WIN-A-S3 at x 27'-4" mirrors WIN-A-S2's 8'-8" only because N-A-V1 moved to 22'-8" (see
    # its node note); both are bay centres, as a 14" RO must be. Cost: neither flanker caps
    # a lower-storey column anymore — the gable rule says the ridge wins over the columns.
    # WIN-A-S1/S4 (the retired corner pair) are gone, not renumbered, so S2/S3 keep their
    # uids/IFC GlobalIds; the surviving sequence reads S2, JUL-W, JUL-E, S3 west→east.
    Window(uid="CAX302AAAA", tag="WIN-A-S2", host="W-A-S1", type_ref="WT-1448",
           position=from_node("N-A-SW", ft(8, 1)), sill_height=ft(2, 8)),   # x 8'-8"
    Window(uid="CAX303AAAA", tag="WIN-A-S3", host="W-A-S4", type_ref="WT-1448",
           position=from_node("N-A-V1", ft(4, 1)), sill_height=ft(2, 8)),   # x 27'-4"
    # The blank middle of the same gable: a pair of 24x64 casements straddling the ridge,
    # reading like a juliet balcony without being one (no door/guard/walking surface — the
    # 2'-8" sill clears R312.2's 24" fall-protection trigger by 8"). Shrank from an initial
    # 32x76 (2026-07-31) to 50x64 overall: the bigger glass overwhelmed the then-14x24
    # flankers and read as two windows rather than one mullioned opening.
    #
    # WIDENED 18" -> 24" EACH, OUTWARD ONLY (2026-08-24), so the pair now reads 62" overall.
    # The inboard jambs (17'-5" and 18'-7") did NOT move and cannot: the clear pier between
    # the two ROs is 14", centred on W-A-C1/the RB-HOUSE bearing point — enough to carry the
    # bearing (11-1/2" of stud+jack+king) with 2-1/2" to spare and let the kings double as
    # drywall backing, where 12" is the arithmetic minimum. That pier also reads as the
    # composition's mullion, which is the other reason it is fixed.
    #
    # Growing outward moved the centres off the STUD LINES they used to sit on (16'-8" and
    # 19'-4") to 16'-5" and 19'-7". The frame is no worse for it — the outboard jambs now
    # land 1" inside the 15'-4" and 20'-8" stud lines, so each RO still breaks exactly one
    # stud (the 16'-8"/19'-4" lines), and the king studs pack against the flanking stud
    # rather than standing free in a bay. The pair stays an exact mirror about x=18'-0",
    # which is the gable rule that governs here.
    # Tags are descriptive, not positional, since a mid-sequence insertion couldn't join the
    # west→east WIN-A-S* numbering without renumbering (and breaking IFC GlobalIds) the rest.
    Window(uid="CAX311AAAA", tag="WIN-A-S-JUL-W", host="W-A-S2", type_ref="WT-2464",
           position=from_node("N-A-S1", ft(5, 0)), sill_height=ft(2, 8)),   # x 16'-5"
    Window(uid="CAX312AAAA", tag="WIN-A-S-JUL-E", host="W-A-S3", type_ref="WT-2464",
           position=from_node("N-A-S2", ft(1, 0)), sill_height=ft(2, 8)),   # x 19'-7"
    # The source attic has no north, east or west opening at all; these three are kept for
    # daylight and cross-ventilation and are this storey's only openings with no counterpart.
    Window(uid="CAX304AAAA", tag="WIN-A-N1", host="W-A-N2", type_ref="WT-3036",
           position=from_node("N-A-NW", ft(6, 9)), sill_height=ft(2)),
    Window(uid="CAX305AAAA", tag="WIN-A-N2", host="W-A-N1", type_ref="WT-3036",
           position=from_node("N-A-NE", ft(6, 9)), sill_height=ft(2)),
    # Knee-wall windows, one at each end of the east and west walls (2026-07-30 facade
    # pass). The 5' knee walls are the one place the 14" family is chosen for height, not
    # width: at sill 2'-6" the head sits at 4'-6", 3" under the double top plate — all a
    # 5' wall has to give. West moved one bay inward for the facade pass and is symmetric
    # at 4'-8" / 31'-4" about y=18'. East is 4" off (32'-4" vs. 32'-8") because W-A-E2's
    # grid starts at N-A-E1 (y=9'), not the corner, so 32'-8" isn't a bay centre there.
    # 2026-08-15: left as-is after pricing the alternative — moving N-A-E1 to 8'-8" (to
    # column WIN-A-E-N with WIN-S-BED3 at 32'-0") or 9'-4" (for the pair's own mirror) both
    # drag N-A-C2/W-A-SN with them, and 9'-4" was tried and reverted the same day when
    # code.R312_1_guard flagged 3'-0" of unguarded well at FO-A-STAIR. Not worth reworking
    # the stair well for.
    Window(uid="CAX308AAAA", tag="WIN-A-W-S", host="W-A-W1", type_ref="WT-1424",
           position=from_node("N-A-NW", ft(30, 9)), sill_height=ft(2, 6)),   # y 4'-8"
    Window(uid="CAX306AAAA", tag="WIN-A-W-N", host="W-A-W1", type_ref="WT-1424",
           position=from_node("N-A-NW", ft(4, 1)), sill_height=ft(2, 6)),    # y 31'-4"
    Window(uid="CAX309AAAA", tag="WIN-A-E-S", host="W-A-E1", type_ref="WT-1424-T",
           position=from_node("N-A-SE", ft(2, 9)), sill_height=ft(2, 6)),    # y 3'-4"
    Window(uid="CAX310AAAA", tag="WIN-A-E-N", host="W-A-E2", type_ref="WT-1424",
           position=from_node("N-A-E1", ft(23, 1)), sill_height=ft(2, 6)),   # y 32'-4"
]

ROOMS = [
    # STORAGE, not MEDIA (2026-08-01, by decision): 598 sf under a 4:12 cathedral with two
    # 14" knee-wall units can't meet R303.1's 47.8 sf glazing requirement for a habitable
    # room. Joins RM-A-EAST and RM-A-DEN, STORAGE for the same reason — only RM-A-STUDY has
    # the gable to glaze. Retagging is honest; it keeps the permit set from claiming a
    # bedroom-grade room the daylight can't support.
    # ** NO FLOOR FINISH ON PURPOSE (2026-08-25). ** These two lofts are unfinished bulk
    # storage — the STORAGE tag above is not a hedge, it is what they are — so the walking
    # surface is FS-ATTIC's own 3/4" plywood-subfloor deck and nothing goes over it.
    # `floor_finish=None` is the honest way to say that: `takeoff/finishes.py` skips a room
    # with no finish entirely, so no carpet, no pad and no tack strip bill for 1,080 sf that
    # will never be laid. RM-A-DEN keeps its carpet — it is the one loft used as a room.
    Room(uid="CAR401AAAA", tag="RM-A-WEST", seed=pt(ft(9), ft(20)),
         occupancy=Occupancy.STORAGE, floor_finish=None,
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
    Room(uid="CAR402AAAA", tag="RM-A-EAST", seed=pt(ft(27), ft(20)),
         occupancy=Occupancy.STORAGE, floor_finish=None,
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
    # Cathedral like the other three (2026-07-31): the 7'-6" dropped ceiling it used to
    # carry would have buried the 8'-0" head of WIN-A-S-JUL-W, which stands in this room's
    # stretch of the south gable. Under RF-HOUSE the Den's clear face (x 10'-18') runs
    # 9'-4" to 12'-0" of headroom, so R305 is satisfied with room to spare.
    Room(uid="CAR403AAAA", tag="RM-A-DEN", seed=pt(ft(14), ft(4)),
         occupancy=Occupancy.STORAGE, floor_finish="carpet",
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
    Room(uid="CAR404AAAA", tag="RM-A-STUDY", seed=pt(ft(27), ft(4)),
         occupancy=Occupancy.OFFICE, floor_finish="oak",
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
]

ALARMS = [
    Alarm(uid="CAA701AAAA", tag="AL-A-COMBO", kind=AlarmKind.COMBO, room="RM-A-WEST",
          circuit="CKT-LT-BACKUP"),
]

# The hot roof itself: gable, 4:12, ridge N-S, zero overhang (first-class #29).
# No fascia: the standing-seam siding and roofing are one continuous skin over the flush
# edge — the resolver carries the wall metal to the roofing underside and caps the joint
# with corner trim (resolve/roof_trim.py), and the ridge cap derives from the roof's vent
# channel. The box gutter and drip edge ride in params/roof_trim.py (authored runs, not
# derivable from a plane).

ROOFS = [
    Roof(uid="CARF01AAAA", tag="RF-HOUSE", form=RoofForm.GABLE,
         pitch=Pitch(4, 12), bearing_refs=("W-A-E1", "W-A-E2", "W-A-W1"),
         assembly="CATLIN_ROOF", overhang=ft(0), ridge_direction="y",
         # The barge-board answer for a roof that cannot have a barge board (2026-08-01).
         # With zero overhang the formed corner trim is the only piece standing at the rake,
         # and it was ordered in the panels' own white — so the gable read as a knife edge.
         # Ordered in the casings' charcoal instead, its 4" leg draws a 4-1/2" dark band
         # down both rakes, round both eaves and along the ridge: one outline, no new
         # geometry, no custom fabrication, just a second coil colour.
         edge_trim_material="metal-dark-exterior"),
]

BEAMS = [
    # Ridge beam over the center wall line: 3 plies of 1.75x11.875 LVL (5.25x11.875).
    # Continuously supported by the W-A-C1/C2 bearing wall directly beneath it — not a
    # 36' clear span between the gables (no LVL spans that at ~500 plf). bearing_refs
    # names the wall it seats on, which is what the framing schedule prints.
    Beam(uid="CABM01AAAA", tag="RB-HOUSE", start_node="N-A-S2",
         end_node="N-A-N1", size="3-1.75x11.875 LVL",
         bearing_refs=("W-A-C1", "W-A-C2")),
]

# The well is the source's, snapped to the *finished* faces around it like FO-S-STAIR: east
# is the east wall's inside gwb face, north is W-S-SS2's south gwb face, south is a clean
# 3'-0" back for ST-S2A's width. This puts the outer winder carriage on a wall it can bear
# on — an earlier version had this edge on the sheathing plane, with the ledger resolving
# outside the building. Lands in RM-S-STUDY2 below, matching the source's flight.
FLOOR_OPENINGS = [
    FloorOpening(uid="CAF601AAAA", tag="FO-A-STAIR",
                 outline=(pt(ft(21, 2), ft(5, 9.625)),
                          pt(ft(35, 5.375), ft(5, 9.625)),
                          pt(ft(35, 5.375), ft(8, 9.625)),
                          pt(ft(21, 2), ft(8, 9.625)))),
]

FLOOR = [
    FloorSystem(uid="CAF602AAAA", tag="FS-ATTIC",
                joists=JoistSpec(member="11.875 I-joist", spacing=inch(16),
                                 direction="x",
                                 # BM-S-HALL is the centre line for its 8'-6"; the joists
                                 # either side of the hall opening hang off it.
                                 bearing_refs=("W-S-W3", "W-S-C1", "W-S-E2",
                                               "BM-S-HALL")),
                subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=inch(0.75)),
                openings=("FO-A-STAIR",)),
]

# Guard the open south edge of the attic stair well in RM-A-STUDY. This reuses the balcony
# guard's 42" metal fascia-mounted railing family and post spacing, but starts at the attic
# walking surface rather than the exterior deck datum.
STAIR_GUARD = Railing(
    uid="CARL01AAAA", tag="RL-A-STAIR", type_ref="RAILING-INT-STAIR-GUARD", path=(
        pt(ft(21, 2), ft(5, 9.625)),
        pt(ft(35, 5.375), ft(5, 9.625)),
    ),
    kind=RailingKind.METAL_FASCIA_MOUNT, height=ft(3.5),
    base_elevation=ft(20), post_spacing=inch(60), post_size="2x2", rail_count=2,
    mount="fascia", assembly="RAILING_DARK_METAL",
    # R312.1.3: 4" clear between balusters — the largest opening the sphere rule admits.
    infill="balusters", baluster_spacing=inch(4),
)

# ST-S2A handrail (R311.7.8), wall-mounted on W-S-SS2, raked along the flight's nosing line
# (`serves_stair`).
#
# It used to stop at x=32'-5 3/8", where the straight run leaves the turn, on the reasoning
# that "there's no raking wall line to mount a rail on until the flight leaves the turn".
# The turn is a LEFT one out of an east entry, so its outside — the wide end of all three
# winders — is against this same north wall, which runs on to x=36'-0": there is wall, and
# the winders are beside it. The rail now continues east to x=34'-2" so it is beside the
# winder fan as well as the straight run, which is what R311.7.8.2 asks of it ("continuous
# for the full length of the flight"). It ends over the outer corner of the lowest winder
# tread, 10" from it. Nothing was asking until 2026-08-22, when `code.R311_7_8_handrail`
# started measuring the drawn rail against the drawn flight instead of reading
# `continuous=True` off the element; it named the three unserved winders straight away.
STAIR_HANDRAIL = Railing(
    uid="CARL02AAAA", tag="RL-A-HANDRAIL", path=(
        pt(ft(35, 5), ft(8, 7.625)),
        pt(ft(22, 5.375), ft(8, 7.625)),
    ),
    kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
    base_elevation=ft(20), post_spacing=inch(48), post_size="2x2", rail_count=1,
    mount="wall", assembly="RAILING_DARK_METAL",
    role="handrail", serves_stair="ST-S2A", top_height=inch(36),
    graspable_profile="1.5in round — Type I",
)

STAIRS = [
    Stair(uid="CST703AAAA", tag="ST-S2A", floor_opening="FO-A-STAIR",
          from_storey="second", to_storey="attic", width=ft(3), newel_profile="6x6",
          # Enter north at the east edge, then three lower winders turn the climb west.
          # `start` is the origin the run walks from (resolve/stairs/dispatch.py), and with
          # run_reversed on x that is the well's SE corner.
          layout="right_angle_winder", turn_direction="left",
          run_direction="x", run_reversed=True, winder_count=3,
          # The turn is a tiered box (Haun), and a box has to be carried on its outside
          # edges: W-S-E1 takes the east leg, W-S-SS2 the north one. Both are the walls the
          # well was snapped to, so a ledger lands on their finished faces. Without naming
          # them the box corners post down onto bare I-joist deck, which
          # `structural.landing_post_bearing` correctly refuses.
          bearing_refs=("W-S-E1", "W-S-SS2"),
          start=pt(ft(35, 5.375), ft(5, 9.625))),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *ROOFS, *BEAMS, *FLOOR_OPENINGS,
            *FLOOR, STAIR_GUARD, STAIR_HANDRAIL, *STAIRS]
