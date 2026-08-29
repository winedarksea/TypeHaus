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
    Layer,
    LayerFunction,
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
    # x 8'-8" since 2026-08-27 (was 10'-0"). This node's only remaining job is to split two
    # otherwise identical collinear gable walls — RM-A-DEN was deleted the same day and
    # W-A-DW, which used to tee in here, went with it.
    #
    # ** IT MOVED BY EXACTLY 16", AND THAT IS THE WHOLE POINT. ** A wall's stud grid lays
    # out from its start node, so W-A-S2's grid is phased off this x. 10'-0" = 120" and
    # 8'-8" = 104", and 120 - 104 = 16, so the phase is unchanged and every bay under
    # WIN-A-S-JUL-W/E stays exactly where it was. Merging W-A-S1/W-A-S2 instead (the
    # 2026-08-24 W-M-E1/E2 precedent) would have rephased that half by 8" — 120 mod 16 = 8
    # — moving the framing under a 27" RO pair whose 21" clear pier carries RB-HOUSE's
    # south bearing point. Moving the node was the cheap way to the same place.
    Node(uid="CAN002AAAA", tag="N-A-S1", position=pt(ft(8, 8), ft(0))),
    Node(uid="CAN003AAAA", tag="N-A-S2", position=pt(ft(18), ft(0))),
    # Vestibule screen line, 22'-8" not the source's 22.31 (2026-08-01 gable pass): W-A-S4
    # starts here and a wall's stud grid lays out from its start node, so this x sets the
    # phase of the east gable's bay centres. 22'-8" = 272" = 16x17, keeping W-A-S4 and
    # W-A-S1 in phase so they mirror exactly about x=18' (22'-4" was 4" out of phase). The
    # screen closes no room polygon (see W-A-VE), so the move is free and only widens the
    # gap to the stair well at x 21'-1 3/4".
    Node(uid="CAN011AAAA", tag="N-A-V1", position=pt(ft(22, 8), ft(0))),
    Node(uid="CAN004AAAA", tag="N-A-SE", position=pt(ft(36), ft(0))),
    # y 9'-4" since 2026-08-27 (was 9'-0"), moved with N-A-C2 when W-A-SN became the study's
    # 12 3/4" bookcase wall — see that node's comment for the whole derivation.
    Node(uid="CAN005AAAA", tag="N-A-E1", position=pt(ft(36), ft(9, 4))),
    Node(uid="CAN006AAAA", tag="N-A-NE", position=pt(ft(36), ft(36))),
    Node(uid="CAN007AAAA", tag="N-A-N1", position=pt(ft(18), ft(36))),
    Node(uid="CAN008AAAA", tag="N-A-NW", position=pt(ft(0), ft(36))),
    # Den north wall y=5'-7" (source 5.611); band wall y=9'-4" (source 9.228).
    #
    # 9'-4" ARRIVES BY ARITHMETIC, NOT BY PREFERENCE (2026-08-27). W-A-SN's SOUTH face is the
    # only thing covering FO-A-STAIR's north edge, so it is pinned at the well edge,
    # 8'-9 5/8" = 105.625". A Wall is centred on its axis, so the axis sits at
    # 105.625 + thickness/2 — and CATLIN_INT_2X4_BOOKCASE_12's 12.750" puts that at
    # 112.000", y = 9'-4" exactly. The wall was THICKENED, not moved: the face stayed put.
    #
    # This is why the 2026-08-15 attempt at 9'-4" FAILED and this one does not. That pass
    # moved a 4 3/4" partition, which carried its south face 4" north of the well edge and
    # opened 3'-0" of unguarded well (code.R312_1_guard). Same axis, opposite meaning.
    #
    # Two things fall out for free: the axis is now ON the 16" module (FS-ATTIC's joists sit
    # at y = 16k, so there is a joist directly under the sole plate where the thin wall had
    # none), and the source-survey error at both nodes drops 2.74" -> 1.26". W-A-SN must
    # keep interior_room="RM-A-STUDY" — the stack-up is asymmetric now and the gwb face
    # belongs on the loft side.
    Node(uid="CAN009AAAA", tag="N-A-C1", position=pt(ft(18), ft(5, 7))),
    Node(uid="CAN012AAAA", tag="N-A-C2", position=pt(ft(18), ft(9, 4))),
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
    # SPLIT AT N-A-N3 (x=10'-0") ON 2026-08-29, because W-A-BA-E tees in there and
    # `resolve/topology.py`'s junction solver needs a shared endpoint or the two bands'
    # solids overlap. N-A-N3 mirrors N-S-N2 exactly, so the attic north wall finally
    # segments where the storey below already does.
    #
    # ** THE TAG AND UID STAY ON THE WEST PIECE. ** That is what preserves WIN-A-N1's
    # `host` and its `from_node("N-A-NW", ...)` verbatim, and what preserves
    # test_catlin_outdoor_structures.py's assertion that the PV/NEMA boxes ride W-A-N2.
    # Its `stacks_on` had to move with the split: W-S-N2 is now under W-A-N2B, and the
    # west piece spans W-S-N3 and W-S-N3B, so it names W-S-N3 to break the tie.
    Wall(uid="CAW105AAAA", tag="W-A-N2", start_node="N-A-N3", end_node="N-A-NW",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-N3"),
    Wall(uid="03GPR9ZAA5", tag="W-A-N2B", start_node="N-A-N1", end_node="N-A-N3",
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
    # SPLIT AT N-A-PK-W (y=22'-4") ON 2026-08-29 — the third split this change forces, and
    # the third for one reason: W-A-STU-N (storeys/attic_studio.py) tees in here, and a
    # mid-span tee leaves `resolve/topology.py`'s junction solver without a shared endpoint.
    # N-A-PK-W mirrors N-S-W2 below it exactly.
    #
    # The split is SAFE for the two windows on this wall, and that is worth stating rather
    # than hoping: `CATLIN_EXT_2X6` sets `layout_origin="line"`, so the stud module runs
    # THROUGH the seam from the facade's own layout line — "moving a node no longer
    # re-phases anything", as CLAUDE.md puts it. Both keep their bay centres and take no
    # header. `structural.window_framing_module` is re-run anyway.
    #
    # ** TAG AND UID STAY ON THE NORTH PIECE **, which preserves WIN-A-W-N's `host` and its
    # `from_node("N-A-NW", ...)` offset verbatim. Both pieces keep start->end running north
    # to south, as the undivided wall did: `alignment=face("sheathing-ext")` and the outward
    # sign are read off the wall's own direction, so reversing a segment would turn its
    # stack-up around. `stacks_on` splits with them — W-S-W2 is y 22'-4"..29'-4" and W-S-W3
    # is y 9'-0"..22'-4", so each piece names the one actually under it.
    Wall(uid="CAW108AAAA", tag="W-A-W1", start_node="N-A-NW", end_node="N-A-PK-W",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(5),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-W1"),
    Wall(uid="8PJW960EK6", tag="W-A-W1B", start_node="N-A-PK-W", end_node="N-A-SW",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(5),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-W3"),
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
    # SPLIT AT N-A-C3 (y=22'-4") ON 2026-08-29, for the same reason W-A-N2 was: W-A-HALL-S
    # tees in there, and a mid-span tee leaves the junction solver without a shared
    # endpoint. The split is free on the stud grid — CATLIN_INT_2X6_BRG is
    # `layout_origin="line"`, so both segments lay out from the same global line rather
    # than from their own start nodes.
    #
    # It also makes the note below TRUE SEGMENT BY SEGMENT for the first time. The old
    # single wall ran y 9'-4"..36'-0" and had to describe two different load paths in one
    # comment: south of y=22'-4" it stands on W-S-C2C, north of it there is no wall at all
    # for 8'-6" and BM-S-HALL carries it. Now each segment says its own.
    #
    # It splits TWICE, not once: the guest bath's SE corner N-A-BW-E lands on this line at
    # y=17'-4" — a joist line, 208" = 13 x 16 (storeys/attic_studio.py) — and needs the same
    # shared endpoint W-A-HALL-S
    # needs at N-A-C3, or `integrity.wall_loop_open` reports the bath as an unclosed face.
    # Both southern pieces stand on W-S-C2C (y ..22'-4") and both keep BEARING: this is the
    # ridge line, and RB-HOUSE names every segment of it.
    Wall(uid="CAW110AAAA", tag="W-A-C2", start_node="N-A-C2", end_node="N-A-BW-E",
         assembly="CATLIN_INT_2X6_BRG", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-C2C"),
    Wall(uid="78VGE6A81J", tag="W-A-C2M", start_node="N-A-BW-E", end_node="N-A-C3",
         assembly="CATLIN_INT_2X6_BRG", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-C2C"),
    # y 22'-4"..36'-0". Between y=22'-4" and 30'-10" the storey below carries no wall —
    # BM-S-HALL (three plies 11-7/8" LVL) is there instead — so this wall (and RB-HOUSE
    # through it) lands on that beam. `stacks_on` names W-S-C4B since the tiebreaker needs
    # a *wall*. It is also the east edge of FO-A-HALL: the void's maxx is this wall's axis.
    Wall(uid="S9N320V34H", tag="W-A-C2B", start_node="N-A-C3", end_node="N-A-N1",
         assembly="CATLIN_INT_2X6_BRG", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-C4B"),
    # ** THE DEN IS GONE (2026-08-27, by decision). ** W-A-DN (N-A-D1 -> N-A-C1) and W-A-DW
    # (N-A-S1 -> N-A-D1) stood here, boxing a 43 sf nook at x 10'-0"..18'-0", y 0..5'-7"
    # out of the south end of the west loft, with D-A-DEN in the north wall and node
    # N-A-D1 at their corner. All five are deleted and the space folds back into
    # RM-A-WEST-UNFIN, which now runs the full x 0..18' width of the storey.
    #
    # The Den had already been moved west off its source footprint (x 13'-9"..22'-4",
    # which straddles the RB-HOUSE bearing line W-A-C1/C1B/C2 and so could not open up)
    # and had lost its 7'-6" dropped ceiling on 2026-07-31 because that ceiling buried
    # WIN-A-S-JUL-W's 8'-0" head. What it never got was a reason to be a room: it was
    # tagged STORAGE like both lofts, and its only fixture needed an integral switch
    # because the way in had no wall to put a switch on. Deleting it also freed N-A-S1
    # to move (see that node) and, with it, WIN-A-S2.
    #
    # RM-A-WEST-UNFIN inherits the space at ITS finish, which is none — the 43 sf of
    # carpet the Den carried is not billed any more. See the ROOMS note below.
    # THE STUDY'S BOOKCASE WALL (2026-08-27). 12 3/4" of built-in shelving, not a partition:
    # the owner wanted a bookcase wall at the stair head with D-A-STUDY hidden inside it.
    # ** DO NOT MOVE THIS WALL AND DO NOT SPLIT IT. ** Its SOUTH face is the only thing
    # covering FO-A-STAIR's north edge; push it north and code.R312_1_guard FAILs with
    # ~14'-3" of unguarded well. The face is pinned at 8'-9 5/8" and the depth grew NORTH,
    # which is what put N-A-C2/N-A-E1 on y=9'-4" (see N-A-C2's note for the arithmetic).
    # Splitting off the west 1'-6" for a thinner assembly re-opens the same FAIL: a 4 3/4"
    # wall centred on this axis has its south face 4" north of the well edge. One wall, one
    # assembly, end to end.
    #
    # `interior_room` is the highest-consequence kwarg on this line. The stack-up is
    # asymmetric — millwork south, gwb north — and without it `orientation.wall_outward_sign`
    # may put the gwb face on the well edge and the case pocket in the storage loft.
    #
    # THE CASE RUN starts at x=22'-8", not the well's 21'-2": the WALL covers the well edge,
    # the casework does not have to (code.R312_1_guard reads the wall footprint union, not
    # the millwork). 22'-8" is a 16" station and N-A-V1's own line, which buys three things —
    # RL-A-HANDRAIL's upper return at 22'-5 3/8" gets solid wall to die into, ED-A-STUDY-SW
    # stays exactly where it is, and the run reads as beginning where the vestibule ends.
    # The 1'-6" west of it is the run's flush end panel. Five bays, each topped off the
    # usable height at its EAST end (5'-0" + (36' - x)/3, less ~3" of build-up and seat):
    #     1  22'-8"  -> 25'-4"     usable 8'-3 2/3"    case top 7'-6"
    #     2  25'-4"  -> 28'-0"     usable 7'-5"        case top 7'-0"
    #     3  28'-0"  -> 30'-8"     usable 6'-6 1/3"    case top 6'-0"
    #     4  30'-8"  -> 33'-4"     usable 5'-7 2/3"    case top 5'-6"
    #     5  33'-4"  -> 35'-5 3/8" usable 4'-11 1/4"   case top 4'-6"
    # Nothing is placed in plan/placeables.py for this: both catalog bookcases are 1'-0"
    # deep against a 9 7/8" pocket, so every case would stand 2 1/8" PROUD — out over the
    # well, the exact lie this wall exists to avoid — and neither fits bays 4 or 5. The run
    # is carried by the assembly's source=, this comment, and a prices.toml [allowances]
    # lump (the house's existing idiom, per the roof's vent mat). The BOM legitimately sees
    # only the case-back sheet area and the nailers.
    #
    # D-A-STUDY's hinge-side jamb wants a full-depth 3-ply post through-bolted to the sole
    # plate and the assembly's 4'-0" blocking row: a ~250 lb bookcase leaf on a 10" moment
    # arm is TORSION, not bending, which is why no header_spec is authored (and why
    # structural.header_prescriptive, which never fires under 8'-0", would not have caught
    # it). There is no schema field for that jamb — it lives here and on the type.
    Wall(uid="CAW113AAAA", tag="W-A-SN", start_node="N-A-C2", end_node="N-A-E1",
         assembly="CATLIN_INT_2X4_BOOKCASE_12", interior_room="RM-A-STUDY",
         top=ToRoof(roof_ref="RF-HOUSE")),
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
    Door(uid="CAD201AAAA", tag="D-A-HALVES", host="W-A-C1B", type_ref="DT-INT-SWING32",
         position=from_node("N-A-C1", ft(0, 5.0625))),
    # The band wall's opening onto the stair head — the source's 2'-7 1/2" gap at
    # x 18'-6"..21'-1 3/4", the only way between the east loft and the stair vestibule.
    # THE MURPHY BOOKCASE DOOR (2026-08-27). A RETYPE IN PLACE — everything that says
    # "Murphy" lives on DT-INT-BOOKCASE30, so this Door keeps its uid and IFC GlobalId, and
    # keeps its position: the offset runs along x, which N-A-C2's y move does not touch.
    # Same RO as DT-INT-SWING30, so nothing re-phases and the jamb pack is unchanged.
    # `flip_hinge` parks the leaf WEST against the centreline wall; hinged east it swings
    # out toward the well. See W-A-SN above for the hinge-side jamb this leaf's weight needs.
    Door(uid="CAD203AAAA", tag="D-A-STUDY", host="W-A-SN", type_ref="DT-INT-BOOKCASE30",
         position=from_node("N-A-C2", ft(0, 8.875)), flip_hinge=True),  # x 19'-11 7/8"
    Door(uid="CAD204AAAA", tag="D-A-VEST", host="W-A-VE", type_ref="DT-INT-SWING30",
         position=from_node("N-A-V1", ft(0, 11.25))),                 # y 2'-2 1/4"
    # South gable, SIX openings west→east: S1, S2, JUL-W, JUL-E, S3, S4 — mirror-symmetric
    # about the ridge (CLAUDE.md's "gables read symmetric" rule).
    #
    # The 2026-08-01 pass left four: two WT-1448 flankers at x 8'-8"/27'-4" and the juliet
    # pair. It cut the corner pair (x 3'-4"/32'-8") on the grounds that the 4:12 rake leaves
    # only ~6' of wall there, "not enough for anything that doesn't look like a stamp".
    # 2026-08-27 revives exactly those two stations, because two things changed: the juliets
    # grew to 27" (below), and a corner unit is now the THIRD member of a group rather than a
    # lone stamp — the gable reads as one six-opening composition instead of a pair plus two.
    # The tags come back too, so the west→east sequence is whole again and S2/S3 keep their
    # uids/IFC GlobalIds.
    #
    # ** THE 8" COLUMN MISS IS PERMANENT, not an authoring accident. ** A 14" RO must sit on
    # a BAY CENTRE (8" mod 16", structural.window_framing_module), and every south column the
    # storeys below stack is on a STUD LINE (48", 112", 176", 256", 320", 384"). So no 14"
    # unit can ever column with 4'-0"/32'-0"; 3'-4"/32'-8" (40"/392", each ≡ 8 mod 16) are the
    # nearest bay centres and are an exact mirror about x=18'-0". Do not "fix" this by moving
    # them 8" — that trades a clean framing module for a header the rake will not take.
    #
    # Rake clearance at both stations: the roof plane is 5'-0" + (36' − x)/3 above the attic
    # datum, ~6'-1 1/3" there, less ~3" of floor build-up and rafter seat — the 4'-8" head
    # clears by about 1'-2". WT-1424 needs no header, no jack and no king: the RO lands wholly
    # inside one bay. Sill 2'-8", the gable's shared sill.
    #
    # WIN-A-S1 lands in RM-A-WEST-UNFIN and WIN-A-S4 in RM-A-STUDY. Neither loft becomes
    # habitable — 2.33 sf does not move a 598 sf STORAGE room near R303.1 — so neither room
    # is retagged.
    #
    # The WT-1448 flankers took that type rather than the juliet family (which they would
    # otherwise share) because an 18" RO needs a jamb pack whose header, at the nearest stud
    # line, is 1.8" too tall to clear the rake there. WIN-A-S3 at x 27'-4" mirrors WIN-A-S2's
    # 8'-8" only because N-A-V1 moved to 22'-8" (see its node note); both are bay centres, as
    # a 14" RO must be. Cost: no flanker caps a lower-storey column — the ridge wins.
    Window(uid="P411E2J64J", tag="WIN-A-S1", host="W-A-S1", type_ref="WT-1424",
           position=from_node("N-A-SW", ft(2, 9)), sill_height=ft(2, 8)),   # x 3'-4"
    # 2026-08-27: the flanker pair drawn 16" INWARD, 8'-8"/27'-4" -> 10'-0"/26'-0". Still an
    # exact mirror about x=18'-0" (10 + 26 = 36), and still bay centres on their hosts'
    # grids — 16" off N-A-S1 and 40" off N-A-V1, both 8 mod 16 — so neither breaks a stud
    # or takes a header, which is the whole reason the WT-1448 flankers are 14" wide.
    #
    # ** S2 CHANGED HOSTS TO GET HERE, AND IT HAD TO. ** It sat on W-A-S1, which used to end
    # at x=10'-0"; a 14" RO centred on that end needs 7" of wall that isn't there, and
    # `integrity.opening_fits` (2" minimum edge distance) is an ERROR on exactly that. The
    # fix was three moves that had to happen together: RM-A-DEN deleted, which freed N-A-S1;
    # N-A-S1 moved 10'-0" -> 8'-8", which is 16" and so leaves W-A-S2's stud phase alone
    # (see the node); and this window rehosted onto W-A-S2, where it now stands 9" off the
    # start node with 7'-5" of wall to spare on the far side. The centre never depended on
    # any of it — 10'-0" is 10'-0" either way.
    Window(uid="CAX302AAAA", tag="WIN-A-S2", host="W-A-S2", type_ref="WT-1448",
           position=from_node("N-A-S1", ft(0, 9)), sill_height=ft(2, 8)),   # x 10'-0"
    Window(uid="CAX303AAAA", tag="WIN-A-S3", host="W-A-S4", type_ref="WT-1448",
           position=from_node("N-A-V1", ft(2, 9)), sill_height=ft(2, 8)),   # x 26'-0"
    Window(uid="BM8GAX9FBG", tag="WIN-A-S4", host="W-A-S4", type_ref="WT-1424",
           position=from_node("N-A-V1", ft(9, 5)), sill_height=ft(2, 8)),   # x 32'-8"
    # The blank middle of the same gable: a pair of 27x64 casements straddling the ridge,
    # reading like a juliet balcony without being one (no door/guard/walking surface — the
    # 2'-8" sill clears R312.2's 24" fall-protection trigger by 8"). Shrank from an initial
    # 32x76 (2026-07-31) to 50x64 overall, grew 18" -> 24" each (2026-08-24), and 24" -> 27"
    # each on 2026-08-27 (30" was offered and declined).
    #
    # The 2026-08-24 note that the inboard jambs "cannot move" was true of a 14" pier and is
    # not true now. That pier only has to carry RB-HOUSE's south bearing point on W-A-C1, for
    # which 11 1/2" of stud+jack+king is the arithmetic minimum; 14" was that number with
    # margin. This pass spends the slack the other way: each unit grows 1 1/2" PER SIDE, so
    # the CENTRES do not move (16'-0" and 20'-0", both stud lines) and the clear pier closes
    # 24" -> 21" — still 7" over the 14" requirement, and still reading as the composition's
    # mullion. from_node offsets are to the NEAR JAMB, not the centre
    # (resolve/pipeline.py::_opening_center), which is why the offsets drop 1 1/2".
    #
    # Jambs now land at 14'-10 1/2"/17'-1 1/2" and 18'-10 1/2"/21'-1 1/2". Each RO still
    # breaks exactly one stud (the 16'-8"/19'-4" lines), and the pair stays an exact mirror
    # about x=18'-0", which is the gable rule that governs here. W-A-S2/W-A-S3 are
    # NONBEARING, so the governing width cap is 30" and 27" sits inside it with room.
    # Tags are descriptive, not positional, since a mid-sequence insertion couldn't join the
    # west→east WIN-A-S* numbering without renumbering (and breaking IFC GlobalIds) the rest.
    Window(uid="CAX311AAAA", tag="WIN-A-S-JUL-W", host="W-A-S2", type_ref="WT-2764",
           # +16" on 2026-08-27, and it is NOT a move: N-A-S1 went 10'-0" -> 8'-8" that day
           # (see the node), and this offset is measured off it, so 4'-10 1/2" would have
           # dragged the unit to 14'-8". 6'-2 1/2" holds the CENTRE on 16'-0" where it has
           # always been. The pier, the jambs and the bearing arithmetic below are unchanged.
           position=from_node("N-A-S1", ft(6, 2.5)), sill_height=ft(2, 8)),  # ctr x 16'-0"
    Window(uid="CAX312AAAA", tag="WIN-A-S-JUL-E", host="W-A-S3", type_ref="WT-2764",
           position=from_node("N-A-S2", ft(0, 10.5)), sill_height=ft(2, 8)),  # ctr x 20'-0"
    # The source attic has no north, east or west opening at all; these three are kept for
    # daylight and cross-ventilation and are this storey's only openings with no counterpart.
    # WIN-A-N1 moved 7'-4" -> 8'-0" (2026-08-25) to mirror WIN-A-N2, then WIN-A-N2's whole
    # three-storey column moved 28'-0" -> 29'-4" (2026-08-26) to bring WIN-M-KITCH onto the
    # kitchen sink below; WIN-A-N1 moved to 6'-8" to hold the mirror about x=18'-0".
    Window(uid="CAX304AAAA", tag="WIN-A-N1", host="W-A-N2", type_ref="WT-3036",
           position=from_node("N-A-NW", ft(5, 5)), sill_height=ft(2)),
    Window(uid="CAX305AAAA", tag="WIN-A-N2", host="W-A-N1", type_ref="WT-3036",
           position=from_node("N-A-NE", ft(5, 5)), sill_height=ft(2)),
    # Knee-wall windows, one at each end of the east and west walls (2026-07-30 facade
    # pass). The 5' knee walls are the one place the 14" family is chosen for height, not
    # width: at sill 2'-6" the head sits at 4'-6", 3" under the double top plate — all a
    # 5' wall has to give. West moved one bay inward for the facade pass and is symmetric
    # at 4'-8" / 31'-4" about y=18'. East is 4" off (32'-4" vs. 32'-8") because W-A-E2's
    # grid starts at N-A-E1 (y=9'), not the corner, so 32'-8" isn't a bay centre there.
    # 2026-08-15: left as-is after pricing the alternative — moving N-A-E1 to 8'-8" (to
    # column WIN-A-E-N with WIN-S-BED3 at 32'-0") or 9'-4" (for the pair's own mirror) both
    # drag N-A-C2/W-A-SN with them, and 9'-4" was tried and reverted the same day when
    # code.R312_1_guard flagged 3'-0" of unguarded well at FO-A-STAIR.
    # N-A-E1 IS AT 9'-4" AS OF 2026-08-27 — but by THICKENING W-A-SN, not by moving it, so
    # the guard is untouched (see N-A-C2). The grid on this wall shifted 4" with it; the
    # windows below hold their centres and their offsets absorbed the move.
    # RE-ANCHORED 2026-08-29 WITHOUT MOVING: the west wall split at N-A-PK-W and this window
    # fell on the south piece. `from_node` measures to the opening's LEADING edge along the
    # wall's own direction, which still runs north to south, so the offset is
    # 22'-4" - 5'-3" = 17'-1" and the centre stays at y = 4'-8" to the millimetre. The old
    # 30'-9" was the same edge measured from N-A-NW over the undivided 36'-0" run.
    Window(uid="CAX308AAAA", tag="WIN-A-W-S", host="W-A-W1B", type_ref="WT-1424",
           position=from_node("N-A-PK-W", ft(17, 1)), sill_height=ft(2, 6)),   # y 4'-8"
    Window(uid="CAX306AAAA", tag="WIN-A-W-N", host="W-A-W1", type_ref="WT-1424",
           position=from_node("N-A-NW", ft(4, 1)), sill_height=ft(2, 6)),    # y 31'-4"
    Window(uid="CAX309AAAA", tag="WIN-A-E-S", host="W-A-E1", type_ref="WT-1424-T",
           position=from_node("N-A-SE", ft(2, 9)), sill_height=ft(2, 6)),    # y 3'-4"
    # 2026-08-27: WIN-A-E-N pushed 32'-8" -> 34'-0" centre to column with WIN-S-BED3
    # (retyped to a 14" unit and moved to 34'-0" the same day) and WIN-M-KIT-E below it —
    # the east face's first three-storey 14" column. This spends the east pair's own mirror
    # about y=18'-0" (WIN-A-E-S stays at 3'-4"), which the 2026-08-15 note above priced and
    # declined; the column is what was bought with it. It stays a BAY CENTRE on this wall's
    # grid — 34'-0" - 9'-4" = 296", 296 mod 16 = 8 — so like the other three WT-1424s it
    # breaks no stud and takes no header. (It did not at N-A-E1's old y=9'-0", where the
    # residue was 12"; the bookcase-wall node move fixed that for free.) Near jamb: 34'-0" - 7" - 9'-4" = 24'-1" (the offset dropped 4" on
    # 2026-08-27 when N-A-E1 moved 9'-0" -> 9'-4"; the CENTRE did not move).
    Window(uid="CAX310AAAA", tag="WIN-A-E-N", host="W-A-E2", type_ref="WT-1424",
           position=from_node("N-A-E1", ft(24, 1)), sill_height=ft(2, 6)),   # y 34'-0"
]

ROOMS = [
    # STORAGE, not MEDIA (2026-08-01, by decision): 598 sf under a 4:12 cathedral with two
    # 14" knee-wall units can't meet R303.1's 47.8 sf glazing requirement for a habitable
    # room. Joins RM-A-EAST-UNFIN, STORAGE for the same reason — only RM-A-STUDY has
    # the gable to glaze. Retagging is honest; it keeps the permit set from claiming a
    # bedroom-grade room the daylight can't support.
    # ** NO FLOOR FINISH ON PURPOSE (2026-08-25). ** These two lofts are unfinished bulk
    # storage — the STORAGE tag above is not a hedge, it is what they are, and since
    # 2026-08-27 the tags say -UNFIN so nobody has to read this comment to find out — so the
    # walking surface is FS-ATTIC's own deck and nothing goes over it.
    # `floor_finish=None` is the honest way to say that: `takeoff/finishes.py` skips a room
    # with no finish entirely, so no carpet, no pad and no tack strip bill for 1,080 sf that
    # will never be laid. RM-A-DEN used to keep its carpet as the one loft used as a room;
    # it was deleted 2026-08-27 (see the WALLS note above) and its 43 sf came here, to
    # `floor_finish=None`, so that carpet is off the BOM as well.
    #
    # RM-A-WEST-UNFIN now runs the full x 0..18' width, y 0..36', and picks up the west
    # half of the south gable with it: WIN-A-S-JUL-W and WIN-A-S2 stand in this room now.
    # That is glazing a STORAGE room does not need and does not have to justify — R303.1
    # asks nothing of it — but the seed at (9', 20') is still inside the merged face, so
    # nothing about the claim had to move.
    #
    # What the deck IS, therefore, matters here in a way it does not on any other storey:
    # FS-ATTIC below is specified `plywood-underlayment-sanded` — a sanded-face, plugged
    # T&G panel — precisely because these two rooms walk on it bare. The lower decks are
    # `plywood-subfloor`, which is a covered sheet and, at a Minnesota supply house, quietly
    # interchangeable with OSB.
    # RM-A-STUDIO — the old RM-A-WEST-UNFIN, retagged and re-occupied — moved to
    # plan/storeys/attic_studio.py on 2026-08-29 with the rest of the guest suite, keeping
    # uid CAR401AAAA and therefore its IFC GlobalId. A uid follows the ELEMENT, not the file
    # it is authored in, and ~30 lines of comment here about an unfinished loft went with it.
    Room(uid="CAR402AAAA", tag="RM-A-EAST-UNFIN", seed=pt(ft(27), ft(20)),
         occupancy=Occupancy.STORAGE, floor_finish=None,
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
    Room(uid="CAR404AAAA", tag="RM-A-STUDY", seed=pt(ft(27), ft(4)),
         occupancy=Occupancy.OFFICE, floor_finish="oak",
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
]

ALARMS = [
    # ** RE-POINTED TO RM-A-STUDY ON 2026-08-29, AND NOT TO THE STUDIO. ** Same device, same
    # place; only the room claim moved. Sending it the OTHER way — following the retag into
    # what is now a bedroom — is the failure this comment exists to prevent:
    # `code.R315_co_every_sleeping_area` FAILs outright if every CO alarm on a storey sits
    # inside a bedroom, and `code.R314_R315_alarms` wants one outside the sleeping area
    # besides. RM-A-STUDY is the stair head, which is literally R315.3's "immediate vicinity
    # of the bedrooms, outside the separate sleeping area". The bedroom's own alarm is
    # AL-A-STUDIO, in storeys/attic_studio.py. Tag, uid and CKT-LT-BACKUP all unchanged.
    Alarm(uid="CAA701AAAA", tag="AL-A-COMBO", kind=AlarmKind.COMBO, room="RM-A-STUDY",
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
    # Ridge beam over the center wall line: 2 plies of 1.75x14 LVL (3.5x14), 36'-0".
    #
    # ** IT SPANS NOTHING, AND ITS DEPTH IS A HANGER DIMENSION, NOT A BENDING ONE. **
    # W-A-C1/C1B/C2 hold it up end to end, so there is no clear span between the gables and
    # no moment to size for — ply count here buys strength nobody is asking for. It was
    # 3-1.75x11.875 until 2026-08-28, and that section was wrong in BOTH directions: three
    # plies answered no load, and 11 7/8" was too SHALLOW. The 5.25" was never an
    # engineering result either — resolve/framing/roof.py's RIDGE_BEAM_DEFAULT recorded it
    # as "approximating the user's 6x12 ask".
    #
    # What sets the depth: the resolver pins this beam's TOP to the roof plane at the peak
    # (the ZIP deck bears across it) and trims each rafter back to its face, where the
    # rafter is cut PLUMB and hung on an LSSR. An 11 7/8" I-joist at 4:12 has a 12.52"
    # plumb face (11.875 x 1.0541), and the face sits 1.75" off the peak, another 0.58"
    # down the plane — so the beam has to reach 13.10" below the ridge line. At 11 7/8" the
    # bottom flange and the hanger's seat hung 1.52" past the soffit, with nothing behind
    # them. LVL is made in 9.5/11.875/14/16/18", so 14" is the answer; there is no 13.5".
    # `structural.ridge_beam_depth` holds it now and reports the 0.90" that is left.
    #
    # THREE THINGS A FRAMER HAS TO BE TOLD, all in notes/ridge_beam_detail.md:
    #  - 3.5" is only defensible because the demand is small. LSSR header fasteners are
    #    (14) 10d x 2.5" and 28 rafter PAIRS land opposite each other, so two mirrored
    #    patterns overlap through a 1.5" band and the usual escape — clinch the tips on the
    #    back face — is blocked by the other hanger. IAPMO-ES ER-280 sec 3.2.2 allows a
    #    support thinner than the fastener when the NDS penetration reduction is taken; at
    #    ~600 lb per rafter against an LSSR2.37's 1,565 lb there is room several times over.
    #    On a beam that was actually working, this width would not be available.
    #  - Beveled web stiffeners both sides at this end (Weyerhaeuser H5, APA D710 10c), and
    #    an LSTA24 over the peak per pair — H5S makes the strap mandatory above 3:12.
    #  - The two plies are stitched with SDW22 3-3/4" (Trus Joist SE-N101 Assembly A, side
    #    loaded, 4 per hanger, one face). A 3-ply would want 5" screws from BOTH faces.
    #
    # ORDERED IN THREE 12s, NOT ONE 36. A beam supported everywhere may be butt-spliced over
    # any bearing point, so the takeoff buys the run off the ordinary ladder instead of as one
    # over-length special order that needs a crane: 36'-0" divides exactly three ways with no
    # waste, and a 12' ply of this section is about 92 lb — two framers, no lift. Same lineal
    # feet, same money. `FramedMember.continuously_supported` is derived from bearing_refs
    # actually reaching, not claimed. STAGGER the two plies: cut one stick of ply B in half so
    # it reads 6+12+12+6, putting its joints at 6'/18'/30' against ply A's 12'/24'. Same three
    # sticks per ply, no offcut, and the beam is continuous in one ply at every station.
    #
    # bearing_refs names all THREE segments of the line, which is what the framing schedule
    # prints and what the continuity derivation measures. W-A-C1B (y 5'-7"..9'-4") was
    # missing until 2026-08-28; nothing read it then, and the splice rule reads it now.
    Beam(uid="CABM01AAAA", tag="RB-HOUSE", start_node="N-A-S2",
         end_node="N-A-N1", size="2-1.75x14 LVL",
         bearing_refs=("W-A-C1", "W-A-C1B", "W-A-C2", "W-A-C2M", "W-A-C2B")),
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
                # NOT `plywood-subfloor` like every other deck in the house (2026-08-27):
                # RM-A-WEST-UNFIN and RM-A-EAST-UNFIN take no covering, so this sheet is
                # their finished floor and is specified as the sanded-face underlayment
                # grade it has to be. Same 3/4" (23/32 Performance Category), same species
                # and R-value — a grade and a price change, not a section change.
                # RM-A-STUDY gets oak over it and is indifferent.
                subfloor=DeckLayer(material_ref="plywood-underlayment-sanded",
                                   thickness=inch(0.75)),
                # The SECOND storey's ceiling, and the last deck in the house to get one:
                # the same 5/8" board FS-M-* / SL-M-DECK hang over the basement and
                # FS-S-WEST/EAST over the main floor. Without it every bedroom, the study
                # and the hall below resolved open to the I-joists — a whole storey of
                # ceiling absent from the model and from the order. Restated inline rather
                # than imported from params/: this file is `# haus: editable` and the
                # dialect forbids the import (same reason RM-S-PLANT restates its liner).
                ceiling_below=(
                    Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
                          function=LayerFunction.FINISH),
                ),
                # FO-A-HALL joins FO-A-STAIR on 2026-08-29: the stair hall is open to the
                # roof now. Its outline, its four chosen edges and the reason x=10'-0" is
                # NOT in `joists.bearing_refs` are all in plan/storeys/stair_hall_void.py.
                openings=("FO-A-STAIR", "FO-A-HALL")),
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
