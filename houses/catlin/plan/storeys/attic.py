# haus: editable
# Attic — habitable hot-roofed cathedral storey (WP3.1, WP3.11).
# 5' knee walls east/west (eave sides), gable walls north/south frame ToRoof,
# ridge runs N-S over the center wall line, 4:12, zero overhang (first-class).
from typehaus import (
    Alarm,
    AlarmKind,
    Beam,
    Door,
    DeckLayer,
    EaveTrim,
    FasciaBoard,
    FloorOpening,
    FloorSystem,
    FollowRoof,
    JoistSpec,
    Node,
    Occupancy,
    Pitch,
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
    Node(uid="CAN004AAAA", tag="N-A-SE", position=pt(ft(36), ft(0))),
    Node(uid="CAN005AAAA", tag="N-A-E1", position=pt(ft(36), ft(8, 8))),
    Node(uid="CAN006AAAA", tag="N-A-NE", position=pt(ft(36), ft(36))),
    Node(uid="CAN007AAAA", tag="N-A-N1", position=pt(ft(18), ft(36))),
    Node(uid="CAN008AAAA", tag="N-A-NW", position=pt(ft(0), ft(36))),
    Node(uid="CAN009AAAA", tag="N-A-C1", position=pt(ft(18), ft(8, 8))),
    Node(uid="CAN010AAAA", tag="N-A-D1", position=pt(ft(10), ft(8, 8))),
]

WALLS = [
    # Gable ends (south/north) — raked studs, sloped plates via ToRoof (WP3.11).
    Wall(uid="CAW101AAAA", tag="W-A-S1", start_node="N-A-SW", end_node="N-A-S1",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S1"),
    Wall(uid="CAW102AAAA", tag="W-A-S2", start_node="N-A-S1", end_node="N-A-S2",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S1"),
    Wall(uid="CAW103AAAA", tag="W-A-S3", start_node="N-A-S2", end_node="N-A-SE",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-S2"),
    Wall(uid="CAW104AAAA", tag="W-A-N1", start_node="N-A-NE", end_node="N-A-N1",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-N1"),
    Wall(uid="CAW105AAAA", tag="W-A-N2", start_node="N-A-N1", end_node="N-A-NW",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"),
         top=ToRoof(roof_ref="RF-HOUSE"),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-S-N2"),
    # Knee walls (east/west eave sides) — 5', carry the low roof edge.
    Wall(uid="CAW106AAAA", tag="W-A-E1", start_node="N-A-SE", end_node="N-A-E1",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(5),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-E1"),
    Wall(uid="CAW107AAAA", tag="W-A-E2", start_node="N-A-E1", end_node="N-A-NE",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(5),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-E3"),
    Wall(uid="CAW108AAAA", tag="W-A-W1", start_node="N-A-NW", end_node="N-A-SW",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(5),
         structural_role=StructuralRole.BEARING, stacks_on="W-S-W1"),
    # Center partition under the ridge, full length, frames to the roof.
    Wall(uid="CAW109AAAA", tag="W-A-C1", start_node="N-A-S2", end_node="N-A-C1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE"),
         stacks_on="W-S-C1"),
    Wall(uid="CAW110AAAA", tag="W-A-C2", start_node="N-A-C1", end_node="N-A-N1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE"),
         stacks_on="W-S-C3"),
    # South rooms: den (west of center) + study (east of center). Framed to the roof
    # deck like the other attic partitions; the den's ft(7,6) dropped ceiling (see its
    # Room.ceiling below) is a finish elevation for headroom checks, not a wall height.
    Wall(uid="CAW111AAAA", tag="W-A-DN", start_node="N-A-D1", end_node="N-A-C1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    Wall(uid="CAW112AAAA", tag="W-A-DW", start_node="N-A-S1", end_node="N-A-D1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
    Wall(uid="CAW113AAAA", tag="W-A-SN", start_node="N-A-C1", end_node="N-A-E1",
         assembly="INT_2X4_PARTITION", top=ToRoof(roof_ref="RF-HOUSE")),
]

OPENINGS = [
    Door(uid="CAD201AAAA", tag="D-A-HALVES", host="W-A-C2", type_ref="DT-INT32",
         position=from_node("N-A-N1", ft(4))),
    Door(uid="CAD202AAAA", tag="D-A-DEN", host="W-A-DN", type_ref="DT-INT30",
         position=from_node("N-A-D1", ft(1))),
    Door(uid="CAD203AAAA", tag="D-A-STUDY", host="W-A-SN", type_ref="DT-INT30",
         position=from_node("N-A-C1", ft(1))),
    # Attic windows are 36" tall so their heads stay below the roof framing;
    # every opening starts 24" above the finished attic floor per the brief.
    Window(uid="CAX301AAAA", tag="WIN-A-DEN-S", host="W-A-S2", type_ref="WT-3036-ATTIC",
           position=from_node("N-A-S1", ft(2, 9)), sill_height=ft(2)),
    Window(uid="CAX302AAAA", tag="WIN-A-STUDY-S1", host="W-A-S3",
           type_ref="WT-3036-ATTIC", position=from_node("N-A-S2", ft(6, 9)),
           sill_height=ft(2)),
    Window(uid="CAX303AAAA", tag="WIN-A-STUDY-S2", host="W-A-S3",
           type_ref="WT-3036-ATTIC", position=from_node("N-A-S2", ft(12, 1)),
           sill_height=ft(2)),
    Window(uid="CAX304AAAA", tag="WIN-A-N1", host="W-A-N2", type_ref="WT-3036-ATTIC",
           position=from_node("N-A-NW", ft(6, 1)), sill_height=ft(2)),
    Window(uid="CAX305AAAA", tag="WIN-A-N2", host="W-A-N1", type_ref="WT-3036-ATTIC",
           position=from_node("N-A-NE", ft(6, 9)), sill_height=ft(2)),
    Window(uid="CAX306AAAA", tag="WIN-A-W-SM", host="W-A-W1", type_ref="WT-1424-ATTIC",
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
    Alarm(uid="CAA701AAAA", tag="AL-A-COMBO", kind=AlarmKind.COMBO, room="RM-A-WEST"),
]

# The hot roof itself: gable, 4:12, ridge N-S, zero overhang (first-class #29).
# Eave/rake fascia is derived from the resolved roof plane (resolve/roof_edge.py): a 2x
# spf sub-fascia nailed over the rafter tails/deck edge, lapped by an aluminum face. Its
# depth closes the band the golden eave detail closes with extended wall sheathing —
# from the deck plane (~10.7" above the knee-wall plate, eave_z_m datum) down ~2" past
# the plate. Zero overhang -> no soffit (derivation skips a flush edge). The box gutter
# and drip edge ride in params/roof_trim.py (authored runs, not derivable from a plane).
_HOUSE_EAVE_TRIM = EaveTrim(
    fascia=(FasciaBoard(material="spf", thickness=inch(1.5), depth=inch(12.75)),
            FasciaBoard(material="aluminum", thickness=inch(0.75), depth=inch(13.25))),
)

ROOFS = [
    Roof(uid="CARF01AAAA", tag="RF-HOUSE", form=RoofForm.GABLE,
         pitch=Pitch(4, 12), bearing_refs=("W-A-E1", "W-A-E2", "W-A-W1"),
         assembly="CATLIN_ROOF", overhang=ft(0), ridge_direction="y",
         eave_trim=_HOUSE_EAVE_TRIM),
]

BEAMS = [
    # Ridge beam over the center wall line: 3 plies of 1.75x11.875 LVL (5.25x11.875).
    Beam(uid="CABM01AAAA", tag="RB-HOUSE", start_node="N-A-S2",
         end_node="N-A-N1", size="3-1.75x11.875 LVL",
         bearing_refs=("W-A-S2", "W-A-N1")),
]

FLOOR_OPENINGS = [
    FloorOpening(uid="CAF601AAAA", tag="FO-A-STAIR",
                 outline=(pt(ft(22, 8), ft(8, 8)), pt(ft(36), ft(8, 8)),
                          pt(ft(36), ft(12)), pt(ft(22, 8), ft(12)))),
]

FLOOR = [
    FloorSystem(uid="CAF602AAAA", tag="FS-ATTIC",
                joists=JoistSpec(member="11.875 I-joist", spacing=inch(16),
                                 direction="x",
                                 bearing_refs=("W-S-W2", "W-S-C3", "W-S-E4")),
                subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=inch(0.75)),
                openings=("FO-A-STAIR",)),
]

STAIRS = [
    Stair(uid="CST703AAAA", tag="ST-S2A", floor_opening="FO-A-STAIR",
          from_storey="second", to_storey="attic", width=ft(3),
          # Enter north at the east edge, then three lower winders turn the climb west.
          layout="right_angle_winder", turn_direction="left",
          run_direction="x", run_reversed=True, winder_count=3,
          start=pt(ft(36), ft(8, 8))),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *ROOFS, *BEAMS, *FLOOR_OPENINGS,
            *FLOOR, *STAIRS]
