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
    Node(uid="CAN011AAAA", tag="N-A-V1", position=pt(ft(22, 4), ft(0))),
    Node(uid="CAN004AAAA", tag="N-A-SE", position=pt(ft(36), ft(0))),
    Node(uid="CAN005AAAA", tag="N-A-E1", position=pt(ft(36), ft(9))),
    Node(uid="CAN006AAAA", tag="N-A-NE", position=pt(ft(36), ft(36))),
    Node(uid="CAN007AAAA", tag="N-A-N1", position=pt(ft(18), ft(36))),
    Node(uid="CAN008AAAA", tag="N-A-NW", position=pt(ft(0), ft(36))),
    # Den north wall, y=5'-7" (source 5.611); band wall, y=9'-0" (source 9.228).
    Node(uid="CAN009AAAA", tag="N-A-C1", position=pt(ft(18), ft(5, 7))),
    Node(uid="CAN012AAAA", tag="N-A-C2", position=pt(ft(18), ft(9))),
    Node(uid="CAN010AAAA", tag="N-A-D1", position=pt(ft(10), ft(5, 7))),
    Node(uid="CAN013AAAA", tag="N-A-V2", position=pt(ft(22, 4), ft(5, 7))),
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
    # Center bearing wall under the ridge, full length, frames to the roof. This is
    # NOT a partition: RB-HOUSE bears on it continuously, so it is the reason the roof
    # is a structural-ridge system (rafters simply span ridge->knee wall, no thrust on
    # the 5' knee walls). Opening this line up without a beam would dump ~1.5 klf of
    # thrust into the knee walls. 2x6 to match the bearing stack below (W-S-C1/C3).
    Wall(uid="CAW109AAAA", tag="W-A-C1", start_node="N-A-S2", end_node="N-A-C1",
         assembly="CATLIN_INT_2X6_BRG", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-C1"),
    Wall(uid="CAW115AAAA", tag="W-A-C1B", start_node="N-A-C1", end_node="N-A-C2",
         assembly="CATLIN_INT_2X6_BRG", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-C2"),
    Wall(uid="CAW110AAAA", tag="W-A-C2", start_node="N-A-C2", end_node="N-A-N1",
         assembly="CATLIN_INT_2X6_BRG", top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-C3"),
    # South rooms: den (west of center) + study (east of center). Framed to the roof
    # deck like the other attic partitions; the den's ft(7,6) dropped ceiling (see its
    # Room.ceiling below) is a finish elevation for headroom checks, not a wall height.
    #
    # WHY THE DEN MOVED WEST INSTEAD OF ONTO ITS SOURCE FOOTPRINT (see the structural-ridge
    # note above): the source draws the Den at x 13'-9"..22'-4", straddling the bearing line,
    # and its own centre wall is dashed and stops short of the south gable. RB-HOUSE bears
    # continuously on W-A-C1/C1B/C2, so that line cannot open up. Shifting the Den to
    # x 10'-0"..18'-0", y 0..5'-7" keeps *both* source dimensions (8'-0" x 4'-10 1/2" clear)
    # and lets RM-A-WEST run full depth to the south gable for x 0..10', which is what the
    # source's "588.12 sq ft, 17'-3 3/4" x 35'-4"" west loft actually is. The cost is
    # ~21 sf: our Den takes 8' of the west loft's south end where the source's takes 4'-3".
    Wall(uid="CAW111AAAA", tag="W-A-DN", start_node="N-A-D1", end_node="N-A-C1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    Wall(uid="CAW112AAAA", tag="W-A-DW", start_node="N-A-S1", end_node="N-A-D1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    Wall(uid="CAW113AAAA", tag="W-A-SN", start_node="N-A-C2", end_node="N-A-E1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    # Stair vestibule screen: the source's Den east + north walls, kept where the source
    # draws them (x 22.31, y 5.611) even though the Den itself moved west. They wrap the
    # head of ST-S2A so the arrival is enclosed on the Study side. Being a dangling pair
    # they close no polygonized face, so RM-A-STUDY still reads as one room around them —
    # which is also how the source's 123.39 sf "Study" reads.
    Wall(uid="CAW116AAAA", tag="W-A-VE", start_node="N-A-V1", end_node="N-A-V2",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    Wall(uid="CAW117AAAA", tag="W-A-VN", start_node="N-A-V3", end_node="N-A-V2",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
]

OPENINGS = [
    Door(uid="CAD201AAAA", tag="D-A-HALVES", host="W-A-C2", type_ref="DT-INT32",
         position=from_node("N-A-N1", ft(4))),
    Door(uid="CAD202AAAA", tag="D-A-DEN", host="W-A-DN", type_ref="DT-INT30",
         position=from_node("N-A-D1", ft(1))),
    # The band wall's opening onto the stair head — the source's 2'-7 1/2" gap at
    # x 18'-6"..21'-1 3/4", the only way between the east loft and the stair vestibule.
    Door(uid="CAD203AAAA", tag="D-A-STUDY", host="W-A-SN", type_ref="DT-INT30",
         position=from_node("N-A-C2", ft(0, 8.875))),                 # x 19'-11 7/8"
    Door(uid="CAD204AAAA", tag="D-A-VEST", host="W-A-VE", type_ref="DT-INT30",
         position=from_node("N-A-V1", ft(0, 11.25))),                 # y 2'-2 1/4"
    # The gables take the shared 30"x36" type (its 36" height was chosen for exactly
    # these walls — heads below the cathedral-roof framing); every opening starts 24"
    # above the finished attic floor per the brief.
    #
    # The source's three south-gable openings are 2'-7 1/2" at x 7'-5", 4'-0" at
    # x 17'-11 3/4" and 2'-7 1/2" at x 28'-11". The middle one is centred on the bearing
    # wall and cannot be built, so WIN-A-DEN-S takes the westernmost (now in the west
    # loft, since the Den moved off the gable's centre) and WIN-A-STUDY-S2 the eastern;
    # WIN-A-STUDY-S1 stays in a clear bay with no source counterpart.
    Window(uid="CAX301AAAA", tag="WIN-A-DEN-S", host="W-A-S1", type_ref="WT-3036",
           position=from_node("N-A-SW", ft(6, 9)), sill_height=ft(2)),   # x 8'-0"
    Window(uid="CAX302AAAA", tag="WIN-A-STUDY-S1", host="W-A-S4",
           type_ref="WT-3036", position=from_node("N-A-V1", ft(1, 5)),
           sill_height=ft(2)),                                          # x 25'-0"
    Window(uid="CAX303AAAA", tag="WIN-A-STUDY-S2", host="W-A-S4",
           type_ref="WT-3036", position=from_node("N-A-V1", ft(5, 5)),
           sill_height=ft(2)),                                          # x 29'-0"
    # The source attic has no north, east or west opening at all; these three are kept for
    # daylight and cross-ventilation and are this storey's only openings with no counterpart.
    Window(uid="CAX304AAAA", tag="WIN-A-N1", host="W-A-N2", type_ref="WT-3036",
           position=from_node("N-A-NW", ft(6, 1)), sill_height=ft(2)),
    Window(uid="CAX305AAAA", tag="WIN-A-N2", host="W-A-N1", type_ref="WT-3036",
           position=from_node("N-A-NE", ft(6, 9)), sill_height=ft(2)),
    Window(uid="CAX306AAAA", tag="WIN-A-W-SM", host="W-A-W1", type_ref="WT-1424",
           position=from_node("N-A-NW", ft(17, 5)), sill_height=ft(2)),
]

ROOMS = [
    Room(uid="CAR401AAAA", tag="RM-A-WEST", seed=pt(ft(9), ft(20)),
         occupancy=Occupancy.MEDIA, floor_finish="carpet",
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
    Room(uid="CAR402AAAA", tag="RM-A-EAST", seed=pt(ft(27), ft(20)),
         occupancy=Occupancy.LIVING, floor_finish="carpet",
         ceiling=FollowRoof(roof_ref="RF-HOUSE")),
    Room(uid="CAR403AAAA", tag="RM-A-DEN", seed=pt(ft(14), ft(4)),
         occupancy=Occupancy.STORAGE, floor_finish="carpet",
         ceiling=ft(7, 6)),
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
         assembly="CATLIN_ROOF", overhang=ft(0), ridge_direction="y"),
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

# The well is the source's (x 21'-1 3/4"..35'-9", y 5'-10 3/4"..8'-11 3/8"), snapped to the
# *finished* faces around it the way FO-S-STAIR is: east is the east wall's inside gwb face
# (36' less 6 5/8" of sheathing + stud + board), north is W-S-SS2's south gwb face (9'-0"
# less 2 3/8"), and the south edge is then a clean 3'-0" back so ST-S2A's 3'-0" width fits
# the well exactly. That is what puts the outer winder carriage on a wall it can bear on;
# the port had this edge on the x=36' sheathing plane, where the carriage's wall ledger
# resolved *outside* the building.
#
# The well lands in RM-S-STUDY2 below, which is where the source draws the flight; the port
# had it in RM-S-BED1, which is also why D-S-BED1 used to open into the stair band.
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
                                 bearing_refs=("W-S-W3", "W-S-C1", "W-S-E2")),
                subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=inch(0.75)),
                openings=("FO-A-STAIR",)),
]

# Guard the open west edge of the attic stair well, where the uppermost tread arrives in
# RM-A-STUDY. This reuses the balcony guard's 42" metal fascia-mounted railing family and
# post spacing, but starts at the attic walking surface rather than the exterior deck datum.
STAIR_GUARD = Railing(
    uid="CARL01AAAA", tag="RL-A-STAIR", path=(
        pt(ft(21, 2), ft(5, 9.625)),
        pt(ft(21, 2), ft(8, 9.625)),
    ),
    kind=RailingKind.METAL_FASCIA_MOUNT, height=ft(3.5),
    base_elevation=ft(20), post_spacing=inch(60), post_size="2x2", rail_count=2,
    mount="fascia", assembly="POST_WHITE_PAINT",
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
            *FLOOR, STAIR_GUARD, *STAIRS]
