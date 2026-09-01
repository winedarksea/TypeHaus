# haus: editable
# Attic — habitable hot-roofed cathedral storey (WP3.1, WP3.11); 2x6 envelope walls.
# Flat 2x6 rafter plates east/west (eave sides) — no knee walls since 2026-08-29 —
# gable walls north/south frame ToRoof, ridge runs N-S over the center wall line,
# 6:12, zero overhang (first-class). Roof underside above this floor: 1 1/2" + x/2.
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
    LayerMaterial,
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
    # N-A-V1 (x 22'-8", CAN011AAAA) DELETED 2026-08-29 with the vestibule. It existed to
    # start W-A-S4 and set the phase of the east gable's bay centres; W-A-S3 now runs the
    # whole east half N-A-S2 -> N-A-SE, and `layout_origin="line"` lays that grid out from
    # the facade's own global line rather than from a start node, so removing the seam
    # re-phases nothing.
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
    # N-A-V2 (CAN013AAAA) and N-A-V3 (CAN014AAAA) DELETED 2026-08-29 with W-A-VE/W-A-VN.
    # The stair well's south closure — see W-A-GC-S for why the guard stops and a wall
    # takes over at x=29'-4 1/2". Both axes are set by pinning a FACE to the well edge and
    # growing INT_2X4_PARTITION's 4 3/4" AWAY from the opening, the same rule W-A-SN uses on
    # the north edge: 5'-9 5/8" - 2 3/8" = 5'-7 1/4" south, 35'-5 3/8" + 2 3/8" = 35'-7 3/4"
    # east. A wall centred ON the edge would hang half its thickness over the void.
    #
    # Both ends are `open_end` and both for a real reason, not to quiet the loop check:
    # GC1 is where the closure hands over to RL-A-STAIR and the study runs on past it, and
    # GC2 is the free east end, stopped ON the well edge and so 5/8" short of W-A-E1's rafter
    # plate. Neither terminus closes a polygon, so `integrity.wall_loop_open` is answering
    # correctly and the flag is the authored way to say so. N-A-GC3 (SDBE5SHZGH) existed for
    # a day to carry W-A-GC-E's north end and went with it.
    Node(uid="BPSA3Z9JYP", tag="N-A-GC1", position=pt(ft(29, 4.5), ft(5, 7.25)),
         open_end=True),
    Node(uid="67H4TA4EDQ", tag="N-A-GC2", position=pt(ft(35, 5.375), ft(5, 7.25)),
         open_end=True),
]

# North/south walls below carry the board & batten `layer_materials=` override — see the
# note above WALLS in plan/storeys/main.py, and the Material in plan/assemblies.py.
WALLS = [
    # Gable ends (south/north) — raked studs, sloped plates via ToRoof (WP3.11).
    Wall(uid="CAW101AAAA", tag="W-A-S1", start_node="N-A-SW", end_node="N-A-S1",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S1"),
    Wall(uid="CAW102AAAA", tag="W-A-S2", start_node="N-A-S1", end_node="N-A-S2",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S1"),
    # MERGED 2026-08-29: W-A-S3 now runs the whole east half of the south gable,
    # N-A-S2 (x=18') -> N-A-SE (x=36'). W-A-S4 (CAW114AAAA) and node N-A-V1 are deleted —
    # the seam between them only ever existed to terminate the vestibule screen, and both
    # pieces already named the same `stacks_on="W-S-S2"`. It is free on the stud grid
    # because CATLIN_EXT_2X6 is `layout_origin="line"`: the module runs through the old
    # seam from the facade's global layout line, so WIN-A-S3's 23'-4" is the same bay
    # centre either way. The merge is what gives WIN-A-S3 the wall it needs — a 14" RO at
    # 23'-4" needs 2" of edge distance and the old 18'..22'-8" piece had none to give.
    Wall(uid="CAW103AAAA", tag="W-A-S3", start_node="N-A-S2", end_node="N-A-SE",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S2"),
    Wall(uid="CAW104AAAA", tag="W-A-N1", start_node="N-A-NE", end_node="N-A-N1",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
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
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-N3"),
    Wall(uid="03GPR9ZAA5", tag="W-A-N2B", start_node="N-A-N1", end_node="N-A-N3",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-N2"),
    # RAFTER PLATES (east/west eave sides) — 2026-08-29. These were 5'-0" knee walls,
    # built around a misreading of R305: that every square foot of a sloped-ceiling room
    # needed 5'-0" of headroom. Minn. R. 1309.0305 R305.1 Exception 1 and IRC R304.1/R304.3
    # scope both clauses to the *required* floor area (70 sf), not the whole room, and
    # R304.3 says floor under 5'-0" simply does not count rather than disqualifying the
    # room. With that read the knee walls have no job left, so they are gone: what stands
    # here now is a single 2x6 laid FLAT on the attic subfloor, over the second-storey wall
    # line, and the rafters birdsmouth straight onto it. See CATLIN_RAFTER_PLATE.
    #
    # ** TAGS AND UIDS ARE PRESERVED ** — test_uplift_takeoff.py asserts the tag set, and
    # mep_electrical.py connects to W-A-W1 and W-A-E2. They stay Walls (rather than
    # vanishing) because a Room polygon is strictly wall-bounded: delete these four and all
    # five attic rooms go `integrity.room_unclaimed`, the storey loses its only closed walk,
    # and every attic wall's outward_sign flips to +1. The plate is not fiction anyway —
    # it is what actually gets built, it has to be in the BOM, and it genuinely is the
    # enclosure's edge on this line.
    #
    # base_elevation is ABSOLUTE — ft(20, 0.75) is the 20'-0" storey datum plus 3/4" subfloor; `top` is a height
    # above it, so the plate top is 20'-2 1/4" and the roof's bearing_z_m follows.
    # The alignment moves the axis 1/2" outboard of the plate's own outer face, which puts
    # the plate over the STUDS below rather than out on the sheathing line: CATLIN_EXT_2X6
    # is datumed at sheathing-ext, so its 5.5" studs run 0.5"..6.0" in from the node line
    # and the plate now covers exactly that.
    Wall(uid="CAW106AAAA", tag="W-A-E1", start_node="N-A-SE", end_node="N-A-E1",
         assembly="CATLIN_RAFTER_PLATE", alignment=face("plate-ext", inch(0.5)),
         base_elevation=ft(20, 0.75), top=inch(1.5),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-E1"),
    Wall(uid="CAW107AAAA", tag="W-A-E2", start_node="N-A-E1", end_node="N-A-NE",
         assembly="CATLIN_RAFTER_PLATE", alignment=face("plate-ext", inch(0.5)),
         base_elevation=ft(20, 0.75), top=inch(1.5),
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
         assembly="CATLIN_RAFTER_PLATE", alignment=face("plate-ext", inch(0.5)),
         base_elevation=ft(20, 0.75), top=inch(1.5),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-W1"),
    Wall(uid="8PJW960EK6", tag="W-A-W1B", start_node="N-A-PK-W", end_node="N-A-SW",
         assembly="CATLIN_RAFTER_PLATE", alignment=face("plate-ext", inch(0.5)),
         base_elevation=ft(20, 0.75), top=inch(1.5),
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
    # The 1'-6" west of it is the run's flush end panel.
    #
    # ** THE RUN IS THREE BAYS, NOT FIVE, SINCE 2026-08-30. ** The five-bay table here was
    # derived from `5'-0" + (36' - x)/3` — the 4:12 roof over a 5'-0" knee wall — and it was
    # never re-derived when the storey went to a 6:12 rake on flat plates. Under the governing
    # `1 1/2" + (36' - x)/2` every one of those five case tops was taller than the roof above
    # it, the fifth by more than four feet. Bays 4 and 5 do not exist as shelving at all now;
    # bay 3 is a two-shelf base unit. Re-derived, less ~3" of build-up and seat:
    #     1  22'-8"  -> 25'-4"     usable 5'-5 1/2"    clear height 5'-0"   5 shelves
    #     2  25'-4"  -> 28'-0"     usable 4'-1 1/2"    clear height 3'-6"   4 shelves
    #     3  28'-0"  -> 30'-8"     usable 2'-9 1/2"    clear height 2'-6"   3 shelves
    # (the heights and counts are authored on SB-A-STUDY in plan/millwork.py, which is what
    # `haus millwork` cuts from; this table must follow that bank, not lead it)
    # East of 30'-8" the wall runs on as a raked closure and carries no casework: the usable
    # height at 33'-4" is 1'-5 1/2" and at the wall's east end 4 3/4". That is a plinth, not a
    # bookcase, and billing case backs and nailers for it would be billing joinery nobody can
    # reach past. THE WALL ITSELF DOES NOT SHORTEN — it still has to cover FO-A-STAIR's north
    # edge to x=36'-0", which is the whole reason it is one wall end to end.
    #
    # D-A-STUDY sits in bay 1, the only bay still tall enough to take a leaf.
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
    # ** THE STAIR WELL'S SOUTH-EAST CLOSURE (2026-08-30). A GUARD CANNOT STAND HERE. **
    # RL-A-STAIR was drawn along the whole south edge on 2026-08-29, when the east end of
    # this storey was still being thought about as if it had a knee wall. It does not. The
    # roof underside is `1 1/2" + (36' - x)/2` above the finished floor, so a 42" guard
    # (top at 240" + 42" = 282") only fits while the underside clears 282", i.e. west of
    # x=29'-4 1/2". East of that the guard was inside the roof — 3 of 5 posts, 20 of 40
    # balusters and the whole east leg, ending 35 7/8" proud of the rafters at x=35'-5 3/8"
    # where there is 4 3/4" of clear height. `haus check` reported 0 FAIL through all of it
    # until `integrity.element_above_roof` was written; only the 3D view showed it.
    #
    # So the guard stops at 29'-4 1/2" and a ToRoof partition closes the rest. That is not a
    # workaround, it is the construction: where a rake meets a floor you sheet the triangle,
    # and R312.1 is satisfied by a wall exactly as it is by a railing (`stairwell_guard`
    # reads the wall footprint union). The panel tapers from 3'-6" at its west end to
    # nothing at the eave, which is what the wedge is.
    #
    # ** THE WELL'S EAST EDGE GETS NOTHING, AND THAT IS THE ANSWER RATHER THAN AN OMISSION. **
    # A W-A-GC-E was drawn up that edge first, and it was wrong twice over: it stood under
    # 3 5/8" of roof, and at 4 3/4" thick it could not fit the 5/8" between the well edge at
    # x=35'-5 3/8" and W-A-E1's rafter plate at 35'-6" — `structural.member_interference` put
    # its studs straight through the plate. The reason it fit nowhere is that it had no job.
    # R312.1.1 guards WALKING SURFACES, and with 4 3/4" of clear height there is no walking
    # surface on either side of that edge; the roof plane closes it more completely than a
    # 36" guard could. `code.R312_1_guard` says so out loud in its PASS message now rather
    # than being satisfied by a token wall.
    #
    # This wall closes a face with nothing: the west end at x=29'-4 1/2" is open to
    # RM-A-STUDY where the railing continues, so no new room polygon is carved and no outward
    # sign flips. Non-bearing, no opening, and it stops 5/8" short of the rafter plate.
    Wall(uid="HKFW104YS3", tag="W-A-GC-S", start_node="N-A-GC1", end_node="N-A-GC2",
         assembly="INT_2X4_PARTITION", interior_room="RM-A-STUDY",
         top=ToRoof(roof_ref="RF-HOUSE")),
    # ** THE STAIR VESTIBULE SCREEN IS GONE (2026-08-29). ** W-A-VE (CAW116AAAA),
    # W-A-VN (CAW117AAAA) and D-A-VEST (CAD204AAAA) were the source's Den east and north
    # walls, wrapping ST-S2A's head so the arrival read as enclosed on the Study side. They
    # were always a dangling pair closing no polygonized face, so deleting them changes no
    # room polygon and no outward sign.
    #
    # The 6:12 roof is what retires them: they stood at x 21'-2"..22'-8" where the roof
    # underside is now 11'-4" (west) sloping to... nothing useful — a full-height partition
    # under a rake that low is a soffit, not a screen, and D-A-VEST's 6'-8" head has no
    # room at all. Their footprint (x 21'-2"..22'-8", y 0..5'-7") is the natural home for
    # FURN-A-STUDY-DESK, which the low east strip evicted (see plan/placeables.py).
    #
    # Two prose citations pointed here as the free-end and slip-gap precedent
    # (attic_studio.py); they are repointed to W-A-STU-N, which is the storey's remaining
    # open-ended wall.
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
         position=from_node("N-A-C2", ft(1, 5)), flip_hinge=True),  # x 19'-11 7/8"
    # South gable, FOUR openings west→east: S2, JUL-W, JUL-E, S3 — mirror-symmetric about
    # the ridge (CLAUDE.md's "gables read symmetric" rule).
    #
    # ** REBUILT 2026-08-29 FOR THE 6:12 RAKE. ** The gable carried six until this pass: a
    # corner pair (WIN-A-S1/S4, WT-1424 at x 3'-4"/32'-8"), a WT-1448 flanker pair at
    # 10'-0"/26'-0", and the juliets. The rake is the whole story. The roof underside above
    # the attic floor is now
    #
    #     H(x) = 1 1/2" + x/2,   mirrored past x = 18'-0"
    #
    # and a window's OUTER jamb is where that bites: a head at h needs h + 2" of rake (the
    # raked plate plus a flat 2x4 nonbearing header), so the rule is
    #
    #     x_outer_jamb >= 2 x (head + 2")
    #
    # The corner pair dies outright — at x 3'-4" there is 21 1/2" of roof over the floor and
    # nothing fits under it. The flankers survive by MOVING INWARD AND SHORTENING: WT-1448
    # (head 6'-8" = 80", so it needs 164" = 13'-8" of jamb clearance) becomes WT-1436
    # (head 5'-8" = 68", needing 140"), and the stations go 10'-0"/26'-0" -> 12'-8"/23'-4",
    # where the outer jambs stand at 12'-1" (145") and 12'-0" from the east eave (144").
    # Four inches of margin each, and still an exact mirror about x=18'-0"
    # (12'-8" + 23'-4" = 36'-0"). Both are bay centres — 152" and 280", each = 8 mod 16 —
    # so like every 14" RO in this house they break no stud and take no header.
    #
    # ** S3 REHOSTED FROM W-A-S4 TO W-A-S3, WHICH IS NOW THE WHOLE EAST HALF. ** W-A-S4 and
    # node N-A-V1 went with the vestibule (see WALLS). `layout_origin="line"` means the merge
    # re-phases nothing: the stud module runs through the old seam from the facade's own
    # layout line, so 23'-4" is the same bay centre it would have been either way.
    #
    # TAGS AND UIDS: S2 keeps CAX302AAAA and S3 keeps CAX303AAAA through the retype and the
    # move, so both keep their IFC GlobalIds. S1 (P411E2J64J) and S4 (BM8GAX9FBG) are gone.
    # The west→east sequence is S2, JUL-W, JUL-E, S3 — a gap at S1/S4 rather than a
    # renumbering, because renumbering would break the GlobalIds of the two that survive.
    #
    # WIN-A-S2 stands in RM-A-STUDIO and WIN-A-S3 in RM-A-STUDY. The study is the one that
    # NEEDS them: at 165 sf R303.1 asks 13.2 sf and the single WT-1436 gives 13.625 sf, which
    # is why the flanker is 36" and not WT-1424's 24" (see WT-1436's own note in main.py).
    Window(uid="CAX302AAAA", tag="WIN-A-S2", host="W-A-S2", type_ref="WT-1436",
           position=from_node("N-A-S1", ft(3, 5)), sill_height=ft(2, 8)),   # ctr x 12'-8"
    Window(uid="CAX303AAAA", tag="WIN-A-S3", host="W-A-S3", type_ref="WT-1436",
           position=from_node("N-A-S2", ft(4, 9)), sill_height=ft(2, 8)),   # ctr x 23'-4"
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
    # ** RETYPED WT-2764 -> WT-2754 ON 2026-08-29, 64" -> 54" TALL. ** Width-identical, so
    # the centres, the from_node offsets and the 21" clear pier carrying RB-HOUSE's south
    # bearing point are all untouched — this is a retype that moves no datum. The 6:12 rake
    # is what asks for it: at the outer jambs (x 14'-10 1/2" / 21'-1 1/2", i.e. 178 1/2"
    # from the nearer eave) the roof underside is 90 3/4" over the floor, and a 64" unit on
    # the gable's 2'-8" sill wants 98". At 54" the head lands at 7'-2" and needs 88" —
    # 2 3/4" of margin. If a framer wants air, WT-2748 buys another 6".
    Window(uid="CAX311AAAA", tag="WIN-A-S-JUL-W", host="W-A-S2", type_ref="WT-2754",
           # +16" on 2026-08-27, and it is NOT a move: N-A-S1 went 10'-0" -> 8'-8" that day
           # (see the node), and this offset is measured off it, so 4'-10 1/2" would have
           # dragged the unit to 14'-8". 6'-2 1/2" holds the CENTRE on 16'-0" where it has
           # always been. The pier, the jambs and the bearing arithmetic below are unchanged.
           position=from_node("N-A-S1", ft(6, 2.5)), sill_height=ft(2, 8)),  # ctr x 16'-0"
    Window(uid="CAX312AAAA", tag="WIN-A-S-JUL-E", host="W-A-S3", type_ref="WT-2754",
           position=from_node("N-A-S2", ft(0, 10.5)), sill_height=ft(2, 8)),  # ctr x 20'-0"
    # NORTH GABLE, a mirrored pair. The source attic has no north opening at all; these two
    # are kept for daylight and cross-ventilation.
    #
    # ** BOTH MOVED INWARD ON 2026-08-29 FOR THE 6:12 RAKE, NEITHER SHRANK. ** They were at
    # x 6'-8" / 29'-4" — a mirror the 2026-08-26 kitchen-sink column had already spent, and
    # a station the new roof cannot host: WT-3036 on the gable's 2'-0" sill puts the head at
    # 5'-0" (60"), which needs 2 x (60 + 2) = 124" of clearance to the outer jamb, and at
    # 6'-8" there are 65".
    #
    # 12'-0" / 24'-0" is the nearest legal mirrored pair, and it is legal for two separate
    # reasons that both have to hold: a 30" RO BREAKS studs and so must centre on a STUD
    # LINE (144" and 288", each = 0 mod 16 — unlike the 14" family, which must sit on a bay
    # CENTRE), and the outer jambs land at 129" from their eaves against the 124" the rake
    # allows. Five inches. No shrink is needed, and shrinking would not buy much: the height
    # is what the rake charges for and 30x36 is already the shortest unit in the 30" family.
    #
    # ** WIN-A-N1 REHOSTS W-A-N2 -> W-A-N2B. ** x=12'-0" is east of N-A-N3 (x=10'-0"), where
    # the north wall split on 2026-08-29, so the window is simply on the other piece now.
    # W-A-N2's own comment spends a paragraph arguing that keeping the tag on the WEST piece
    # is what preserves this window's host and its from_node offset verbatim — that argument
    # is now spent, and the tag stays on the west piece for the PV/NEMA boxes alone
    # (test_catlin_outdoor_structures.py). W-A-N2B runs N-A-N1 (x=18') -> N-A-N3 (x=10'), so
    # the offset is measured east-to-west: 18'-0" - 4'-9" - 15" = the 12'-0" centre.
    #
    # At x=12'-0" the west unit fronts FO-A-HALL, the stair void — it daylights a
    # double-height space rather than a room. That is an amenity, not a code problem: the
    # sill is 11'-0" above the floor below and nowhere near R312.2's 24" fall-protection
    # trigger, and R303.1 asks nothing of a hall.
    Window(uid="CAX304AAAA", tag="WIN-A-N1", host="W-A-N2B", type_ref="WT-3036",
           position=from_node("N-A-N1", ft(4, 9)), sill_height=ft(2)),   # ctr x 12'-0"
    Window(uid="CAX305AAAA", tag="WIN-A-N2", host="W-A-N1", type_ref="WT-3036",
           position=from_node("N-A-NE", ft(10, 9)), sill_height=ft(2)),  # ctr x 24'-0"
    # ** THE FOUR EAVE WINDOWS ARE GONE (2026-08-29). ** WIN-A-W-S (CAX308AAAA), WIN-A-W-N
    # (CAX306AAAA), WIN-A-E-S (CAX309AAAA) and WIN-A-E-N (CAX310AAAA) were the knee-wall
    # pair on each side — WT-1424s chosen for HEIGHT rather than width, because a 5'-0" knee
    # wall at a 2'-6" sill has exactly 24" under its double top plate. There is no knee wall
    # any more; their hosts are 1 1/2" plates laid flat (see WALLS), and a plate has nothing
    # to glaze. This is where most of the ~595 sf of deleted CATLIN_EXT_2X6 goes, and with
    # it four units, four bucks, four flashings and eight jamb returns.
    #
    # What it costs: RM-A-STUDIO's daylight drops about a third (21.3 sf -> 13.6 sf, the
    # south pair alone), so R303.1 Exception 1's electric-light substitute is now doing real
    # work there — the studio's six cans plus sconce, 6,000 lm against the 4,450 lm the
    # exception needs at 6 fc. RELOCATE THOSE FIXTURES, NEVER DELETE ONE (lighting.py).
    # The only levers that would give the daylight back are a shed dormer or a roof
    # penetration, and both are excluded.
]

ROOMS = [
    # STORAGE, not MEDIA (2026-08-01, by decision): 598 sf under a cathedral ceiling with
    # two 14" knee-wall units couldn't meet R303.1's 47.8 sf glazing requirement for a
    # habitable room. ** The decision only hardened on 2026-08-29: ** those two knee-wall
    # units are gone with the knee wall itself, so this loft now has NO glazing at all.
    # Joins RM-A-EAST-UNFIN, STORAGE for the same reason — only RM-A-STUDY has
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

# The hot roof itself: gable, 6:12, ridge N-S, zero overhang (first-class #29).
#
# 6:12 SINCE 2026-08-29. It was 4:12, and that pitch was never chosen — it FELL OUT of the
# 5'-0" knee walls, which in turn fell out of the R305 misreading the plate walls above
# describe. With the eave down on a 1 1/2" plate, the pitch is free to be whatever the
# headroom wants, and 6:12 is the shallowest standard pitch that carries the attic rooms:
#
#     roof underside above the attic finished floor:  H(x) = 1 1/2" + x/2
#
# mirrored past x=18'. 9'-1 1/2" at the ridge, 7'-0" at x=13'-9", 5'-0" at x=9'-9".
# ** EVERY ATTIC STATION ANSWERS TO THAT ONE LINE ** — window heads, can lights, the
# receptacle band, the ERV manifold, both vent runs. The building also got 1'-9 1/2"
# SHORTER than it was at 4:12 with 5' knee walls (ridge 32'-0 5/8" -> 30'-3"), because the
# eave dropped 4'-11" and the extra rise only bought back 3'-1 1/2".
# No fascia: the standing-seam siding and roofing are one continuous skin over the flush
# edge — the resolver carries the wall metal to the roofing underside and caps the joint
# with corner trim (resolve/roof_trim.py), and the ridge cap derives from the roof's vent
# channel. The box gutter and drip edge ride in params/roof_trim.py (authored runs, not
# derivable from a plane).

ROOFS = [
    Roof(uid="CARF01AAAA", tag="RF-HOUSE", form=RoofForm.GABLE,
         # bearing_refs names all FOUR plates. W-A-W1B was missing here — a stale artifact
         # of the 2026-08-29 west split that nothing read while the knee walls carried the
         # edge, and that resolve/envelope.py's birdsmouth and roof_edge's closure both read
         # now.
         pitch=Pitch(6, 12),
         bearing_refs=("W-A-E1", "W-A-E2", "W-A-W1", "W-A-W1B"),
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
    # Ridge beam over the center wall line: 2 plies of 1.75x16 LVL (3.5x16), 36'-0".
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
    # rafter is cut PLUMB and hung on an LSSR. RE-DERIVED AT 6:12 ON 2026-08-29: an
    # 11 7/8" I-joist on a 6:12 plane has a 13.28" plumb face (11.875 x 1.1180), and the
    # face sits 1.75" off the peak, another 0.875" down the plane — so the beam has to
    # reach 14.15" below the ridge line. ** 14" FAILS THAT BY 0.15" **, which is exactly
    # the sort of miss that reads as fine on a drawing and leaves the hanger seat hanging
    # in air. LVL is made in 9.5/11.875/14/16/18", so 16" is the answer and it leaves
    # 1.85". `structural.ridge_beam_depth` holds it and reports what is left.
    #
    # The beam now hangs 16" into the room, so the clear height under the ridge reads
    # ~9'-1 1/2" between beams and ~7'-9 1/2" directly under it. Backing the pitch off to
    # 5.5:12 would hold the 14" beam and save a couple hundred dollars, at the cost of
    # 5 1/2" of ridge, a nonstandard pitch and tighter R305 margins. Not worth it.
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
         end_node="N-A-N1", size="2-1.75x16 LVL",
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
                                 # ** LSL RIM SINCE 2026-08-29, AND THE REASON IS BEARING,
                                 # NOT BANDING — BUT READ THE GEOMETRY BEFORE BELIEVING
                                 # THAT. ** The joists run in x, so this deck's rims land at
                                 # x=0 and x=432 running in y, on the sheathing datum. The
                                 # rafter plates above them are aligned 1/2" INBOARD of that
                                 # datum so they sit over the second-storey studs, so plate
                                 # and rim overlap by only about 3/8" (see the blessed
                                 # detail_wall_roof-CATLIN_EXT_2X6-CATLIN_ROOF golden: the
                                 # rim runs u 431.13..432.88 and the plate u 426..431.5).
                                 #
                                 # So the rafter reaction is NOT carried by the rim alone.
                                 # It lands on the subfloor over the joist ends and the rim
                                 # together, directly above the stud line below. That is a
                                 # legitimate story-and-a-half detail and it is what a
                                 # framer will build, but it is a bearing question rather
                                 # than a banding one, and a 1 1/4" OSB band board on this
                                 # line would crush under the perimeter share of it. ** IF
                                 # THE RAFTER EVER DEEPENS OR THE SNOW LOAD RISES, THE
                                 # ANSWER IS SQUASH BLOCKS AT EACH RAFTER, NOT A DEEPER
                                 # RIM. ** The engine models neither; this note is the
                                 # record.
                                 rim_member="1.75x11.875 LSL",
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

# Guard the open south AND EAST edges of the attic stair well in RM-A-STUDY. This reuses
# the balcony guard's 42" metal fascia-mounted railing family and post spacing, but starts
# at the attic walking surface rather than the exterior deck datum.
#
# ** THE RAILING STOPS AT x=29'-4 1/2" AND W-A-GC-S CLOSES THE REST (2026-08-30). **
# It ran the full south edge and turned north up the east one for a day, which was wrong in
# 3D and right in plan — the guard check is 2D and never asked whether 42" of railing fits
# under a 6:12 rake that is 4 3/4" tall at the east end. The whole derivation, and why a
# wall rather than a shorter railing is the honest answer, is on W-A-GC-S in WALLS above.
#
# What the east end used to have was the inside gwb face of the W-A-E1 knee wall, which
# landed on the well edge exactly: CATLIN_EXT_2X6 is 13 1/4" deep off a sheathing datum at
# x=36'-0", so its finish face stood at 35'-5 3/8". W-A-E1 is a 1 1/2" rafter plate now and
# a plate guards nothing, so the closure is the honest price of the ~360 sf of knee wall the
# storey stopped building — 6'-1" of low partition instead of 9'-1" of railing.
STAIR_GUARD = Railing(
    uid="CARL01AAAA", tag="RL-A-STAIR", type_ref="RAILING-INT-STAIR-GUARD", path=(
        pt(ft(21, 2), ft(5, 9.625)),
        pt(ft(29, 4.5), ft(5, 9.625)),
    ),
    kind=RailingKind.METAL_FASCIA_MOUNT, height=ft(3.5),
    base_elevation=ft(20), post_spacing=inch(60), post_size="2x2", rail_count=2,
    mount="fascia", assembly="RAILING_DARK_METAL",
    # R312.1.3: 4" clear between balusters — the largest opening the sphere rule admits.
    infill="balusters", baluster_spacing=inch(4),
)

# ** THE FLIGHT'S OWN OPEN SIDE (2026-08-29). ** RL-A-STAIR above guards the *attic deck*
# edge at 20'-0"; W-A-GC-S closes the rest of that line. Neither of them guards ST-S2A
# itself. The well is cut to exactly the stair's 3'-0" width, and the north face of the
# flight is W-S-SS2 — but the SOUTH face, y=5'-9 5/8", stands open over RM-S-STUDY2's floor
# at 10'-0" for the whole straight run. Measured off the resolved nosing line, the walking
# surface there is 30" above that floor at the first straight riser (x=32'-5 3/8") and 120"
# at the top, so R312.1.1 asks for a guard over 10'-0" of it and nothing in the plan was
# providing one. Every check passed: `code.R312_1_guard` grades the four edges of a floor
# OPENING against the deck that hosts it, and a flight's own open side is not one of them.
#
# The three winders below x=32'-5 3/8" are deliberately outside this run. Their treads sit
# 7 1/2", 15" and 22 1/2" above the study floor — under R312.1.1's 30" trigger — and their
# south side is the narrow inside of the turn, where a guard would have to be built to the
# fan rather than to a line. The newel lands on the first straight riser instead, which is
# both the 30" station and the corner a builder would set it on.
#
# ONE ELEMENT, TWO SECTIONS. R312.1.2 exception 1 measures a stair guard from the line
# joining the nosings and asks 34"; R311.7.8.1 wants a handrail 34"-38" off the same line.
# A single 36" top bar with a Type I section satisfies both, so this is `guard_and_handrail`
# rather than a guard with a second rail bolted to it — and it is what makes the run
# affordable, since RAILING-INT-STAIR-GUARD is priced as a component system in prices.toml
# and a separately-billed handrail on top of it would double-count the same bar.
#
# ** IT OVERLAPS RL-A-STAIR, AND THAT IS THE HONEST READING, NOT A SLIP. ** Both run on
# y=5'-9 5/8". East of x=26'-5 3/8" the rake's 36" band is entirely under the attic deck
# and the two never touch; west of it the rake climbs through 20'-0" and the bands cross,
# 0" at x=26'-5 3/8" growing to the full 36" at the top nosing — 4'-0" of double cover. On
# site this is ONE balustrade whose cap rakes up and lands on the level run at the top
# newel; a `Railing` is a path with one height over one base, so two elements is the only
# way to say it. The alternative — stopping this run at x=26'-5 3/8" — reads tidier and is
# actually unsafe: RL-A-STAIR's *base* is the attic deck, so the flight below it would then
# carry 0"-36" of open edge over an 84" fall with nothing but daylight under the rail. The
# takeoff bills both runs at full length, which over-counts the line by 4'-0" and roughly
# pays for the raked triangle of infill the box IR cannot draw.
#
# RL-A-HANDRAIL below STAYS. It is the rail that reaches the winder fan (R311.7.8.2 wants
# continuity from above the lowest riser), which this one cannot, and two rails on a 36"
# flight still clear 32 1/2" — R311.7.1 allows 27" with a rail on both sides, against
# 31 1/2" with one. `base_elevation` is the second storey's 10'-0", not the attic's 20'-0": the
# rake comes from `serves_stair`, and the datum is the floor this guard stops a fall onto.
FLIGHT_GUARD = Railing(
    uid="C75VZB9VX8", tag="RL-A-FLIGHT-GUARD", type_ref="RAILING-INT-STAIR-GUARD", path=(
        pt(ft(32, 5.375), ft(5, 9.625)),
        pt(ft(22, 5.375), ft(5, 9.625)),
    ),
    # 60" o.c., the spacing RL-A-STAIR, RL-S-STAIR and RL-S-STAIRHEAD all use: over a
    # 10'-0" run that is 3 posts where 48" is 4, and the baluster count does not move —
    # 24 either way, because the 4" sphere sets it, not the post rhythm.
    kind=RailingKind.METAL_FASCIA_MOUNT, height=inch(36),
    base_elevation=ft(10), post_spacing=inch(60), post_size="2x2", rail_count=2,
    mount="fascia", assembly="RAILING_DARK_METAL",
    role="guard_and_handrail", serves_stair="ST-S2A", top_height=inch(36),
    graspable_profile="1.5in round — Type I",
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
            *FLOOR, STAIR_GUARD, FLIGHT_GUARD, STAIR_HANDRAIL, *STAIRS]
