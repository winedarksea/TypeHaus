# haus: editable
# Main floor — 36'x36' at sheathing, 16" o.c. module, east half open living (WP3.1).
# Exterior walls: CATLIN_EXT_2X6, sheathing exterior face on the 0/36 lines.
# Bearing lines: west wall, center N-S wall (x=18), east wall (18' I-joist spans, E-W).
# Smaller windows follow the stud-bay rules: WT-1424 fits one bay unbroken; WT-3036
# breaks one stud (non-bearing walls only); WT-2736 adds jacks on bearing walls.
from typehaus import (
    Alarm,
    AlarmKind,
    Door,
    DoorType,
    FloorOpening,
    Node,
    Occupancy,
    Room,
    RoughOpening,
    Slab,
    Stair,
    StructuralRole,
    Wall,
    Window,
    WindowType,
    face,
    from_node,
    ft,
    inch,
    pt,
    u_us,
)

# --- library-of-the-house types ----------------------------------------------
DOOR_TYPES = [
    DoorType(tag="DT-EXT36", width=ft(3), height=ft(6, 8), exterior=True,
             u_factor=u_us(0.20)),
    DoorType(tag="DT-FRENCH36", width=ft(3), height=ft(6, 8), exterior=True,
             operation="double_swing", u_factor=u_us(0.20)),
    DoorType(tag="DT-PATIO60", width=ft(5), height=ft(6, 8), exterior=True,
             operation="slide", u_factor=u_us(0.25)),
    DoorType(tag="DT-INT32", width=ft(2, 8), height=ft(6, 8)),
    DoorType(tag="DT-INT30", width=ft(2, 6), height=ft(6, 8)),
    DoorType(tag="DT-INT24", width=ft(2), height=ft(6, 8)),
    DoorType(tag="DT-INT60", width=ft(5), height=ft(6, 8), operation="bifold"),
    DoorType(tag="DT-INT56", width=ft(4, 8), height=ft(6, 8), operation="bifold"),
    DoorType(tag="DT-GARAGE192", width=ft(16), height=ft(7), exterior=True,
             operation="overhead"),
]
# One size per width family: every placement of a family shares one height, chosen as
# the tallest that still fits the family's most constrained wall anywhere in the house.
WINDOW_TYPES = [
    # 14" RO — falls between studs on the 16" grid without breaking a stud line. 24"
    # tall because the 5' attic knee wall (WIN-A-W-SM) needs room for the modeled
    # header above the opening below its top plate.
    WindowType(tag="WT-1424", width=inch(14), height=ft(2), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="awning"),
    # 27" RO — bearing-wall size (N*2-9): one stud broken, jacks added. 36" tall
    # because the garage's 8' wall can't take a 60" height at a 42" sill (header would
    # land above the top plate). 27x36 still clears R310 egress (6.75 sf > 5.7).
    WindowType(tag="WT-2736", width=inch(27), height=ft(3), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
    # 30" RO — non-load-bearing size (N*2-6): one stud broken. 36" tall keeps the
    # attic-gable heads below the cathedral-roof framing.
    WindowType(tag="WT-3036", width=inch(30), height=ft(3), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
    # 36" RO — concrete basement wall only (no stud module to respect down there).
    WindowType(tag="WT-3660", width=ft(3), height=ft(5), u_factor=u_us(0.25),
               shgc=0.35, vt=0.5, operation="casement"),
]

NODES = [
    # Perimeter (splits mirror the basement + partition tees)
    Node(uid="CMN001AAAA", tag="N-M-SW", position=pt(ft(0), ft(0))),
    Node(uid="CMN002AAAA", tag="N-M-S1", position=pt(ft(18), ft(0))),
    Node(uid="CMN003AAAA", tag="N-M-SE", position=pt(ft(36), ft(0))),
    Node(uid="CMN004AAAA", tag="N-M-E1", position=pt(ft(36), ft(18))),
    Node(uid="CMN005AAAA", tag="N-M-NE", position=pt(ft(36), ft(36))),
    Node(uid="CMN006AAAA", tag="N-M-N1", position=pt(ft(18), ft(36))),
    Node(uid="CMN007AAAA", tag="N-M-N2", position=pt(ft(10), ft(36))),
    Node(uid="CMN008AAAA", tag="N-M-NW", position=pt(ft(0), ft(36))),
    Node(uid="CMN009AAAA", tag="N-M-W1", position=pt(ft(0), ft(26, 4))),
    Node(uid="CMN010AAAA", tag="N-M-W2", position=pt(ft(0), ft(21, 8))),
    Node(uid="CMN011AAAA", tag="N-M-W3", position=pt(ft(0), ft(13, 4))),
    # Center bearing line ties
    Node(uid="CMN012AAAA", tag="N-M-C1", position=pt(ft(18), ft(13, 4))),
    Node(uid="CMN013AAAA", tag="N-M-C2", position=pt(ft(18), ft(21, 8))),
    Node(uid="CMN014AAAA", tag="N-M-C3", position=pt(ft(18), ft(26, 4))),
    # Interior tees
    Node(uid="CMN015AAAA", tag="N-M-STR1", position=pt(ft(10), ft(25))),
    Node(uid="CMN024AAAA", tag="N-M-STRJ", position=pt(ft(10), ft(26, 4))),
    Node(uid="CMN025AAAA", tag="N-M-C3B", position=pt(ft(18), ft(25))),
    Node(uid="CMN016AAAA", tag="N-M-BA1", position=pt(ft(4), ft(26, 4))),
    Node(uid="CMN017AAAA", tag="N-M-BA2", position=pt(ft(4), ft(21, 8))),
    Node(uid="CMN018AAAA", tag="N-M-D1", position=pt(ft(8), ft(21, 8))),
    Node(uid="CMN019AAAA", tag="N-M-D2", position=pt(ft(8), ft(17, 4))),
    Node(uid="CMN020AAAA", tag="N-M-D3", position=pt(ft(8), ft(13, 4))),
    Node(uid="CMN021AAAA", tag="N-M-E2", position=pt(ft(13, 4), ft(17, 4))),
    Node(uid="CMN022AAAA", tag="N-M-E3", position=pt(ft(13, 4), ft(21, 8))),
    Node(uid="CMN023AAAA", tag="N-M-E4", position=pt(ft(18), ft(17, 4))),
]

WALLS = [
    # --- exterior loop (CCW), sheathing-ext on the line -----------------------
    Wall(uid="CMW101AAAA", tag="W-M-S1", start_node="N-M-SW", end_node="N-M-S1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CMW102AAAA", tag="W-M-S2", start_node="N-M-S1", end_node="N-M-SE",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CMW103AAAA", tag="W-M-E1", start_node="N-M-SE", end_node="N-M-E1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CMW104AAAA", tag="W-M-E2", start_node="N-M-E1", end_node="N-M-NE",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CMW105AAAA", tag="W-M-N1", start_node="N-M-NE", end_node="N-M-N1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CMW106AAAA", tag="W-M-N2", start_node="N-M-N1", end_node="N-M-N2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CMW107AAAA", tag="W-M-N3", start_node="N-M-N2", end_node="N-M-NW",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CMW108AAAA", tag="W-M-W1", start_node="N-M-NW", end_node="N-M-W1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W1"),
    Wall(uid="CMW109AAAA", tag="W-M-W2", start_node="N-M-W1", end_node="N-M-W2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W1"),
    Wall(uid="CMW110AAAA", tag="W-M-W3", start_node="N-M-W2", end_node="N-M-W3",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W2"),
    Wall(uid="CMW111AAAA", tag="W-M-W4", start_node="N-M-W3", end_node="N-M-SW",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-W2"),
    # --- center bearing wall (2x6), stacks on the basement concrete line ------
    Wall(uid="CMW112AAAA", tag="W-M-C1", start_node="N-M-S1", end_node="N-M-C1",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CS"),
    Wall(uid="CMW113AAAA", tag="W-M-C2", start_node="N-M-C1", end_node="N-M-E4",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CS2"),
    Wall(uid="CMW114AAAA", tag="W-M-C3", start_node="N-M-E4", end_node="N-M-C2",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CS2"),
    Wall(uid="CMW115AAAA", tag="W-M-C4", start_node="N-M-C2", end_node="N-M-C3B",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CN"),
    Wall(uid="CMW133AAAA", tag="W-M-C4B", start_node="N-M-C3B", end_node="N-M-C3",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CN"),
    Wall(uid="CMW116AAAA", tag="W-M-C5", start_node="N-M-C3", end_node="N-M-N1",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-CN"),
    # --- stair / storage block --------------------------------------------------
    # This wall line carries the cut second-floor joists and stacks directly over the
    # basement concrete stair wall.  It is split only at the storage-wall tee.
    Wall(uid="CMW117AAAA", tag="W-M-STRW", start_node="N-M-N2",
         end_node="N-M-STRJ", assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-STR"),
    Wall(uid="CMW134AAAA", tag="W-M-STRW2", start_node="N-M-STRJ",
         end_node="N-M-STR1", assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-B-STR"),
    Wall(uid="CMW118AAAA", tag="W-M-STRS", start_node="N-M-STR1",
         end_node="N-M-C3B", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW119AAAA", tag="W-M-STOS", start_node="N-M-W1",
         end_node="N-M-BA1", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW120AAAA", tag="W-M-STOS2", start_node="N-M-BA1",
         end_node="N-M-STRJ", assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- powder bath west of hallway -------------------------------------------
    Wall(uid="CMW121AAAA", tag="W-M-BAE", start_node="N-M-BA1",
         end_node="N-M-BA2", assembly="INT_2X6_PLUMBING", top=ft(9)),
    # --- hallway south wall band ------------------------------------------------
    Wall(uid="CMW122AAAA", tag="W-M-HS1", start_node="N-M-W2",
         end_node="N-M-BA2", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW123AAAA", tag="W-M-HS2", start_node="N-M-BA2",
         end_node="N-M-D1", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW124AAAA", tag="W-M-HS3", start_node="N-M-D1",
         end_node="N-M-E3", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW125AAAA", tag="W-M-HS4", start_node="N-M-E3",
         end_node="N-M-C2", assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- bath2 / laundry / study / closet block ---------------------------------
    Wall(uid="CMW126AAAA", tag="W-M-BA2E", start_node="N-M-D1",
         end_node="N-M-D2", assembly="INT_2X6_PLUMBING", top=ft(9)),
    Wall(uid="CMW127AAAA", tag="W-M-BA2E2", start_node="N-M-D2",
         end_node="N-M-D3", assembly="INT_2X6_PLUMBING", top=ft(9)),
    Wall(uid="CMW128AAAA", tag="W-M-LS", start_node="N-M-E2",
         end_node="N-M-E3", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW129AAAA", tag="W-M-CLN", start_node="N-M-D2",
         end_node="N-M-E2", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW130AAAA", tag="W-M-CLN2", start_node="N-M-E2",
         end_node="N-M-E4", assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- bedroom north wall ------------------------------------------------------
    Wall(uid="CMW131AAAA", tag="W-M-BDN1", start_node="N-M-W3",
         end_node="N-M-D3", assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CMW132AAAA", tag="W-M-BDN2", start_node="N-M-D3",
         end_node="N-M-C1", assembly="INT_2X4_PARTITION", top=ft(9)),
]

OPENINGS = [
    # Exterior
    Door(uid="CMD201AAAA", tag="D-M-ENTRY", host="W-M-N3", type_ref="DT-EXT36",
         position=from_node("N-M-NW", ft(4))),
    Door(uid="CMD202AAAA", tag="D-M-BALC", host="W-M-S2", type_ref="DT-PATIO60",
         position=from_node("N-M-S1", ft(1, 4))),
    # Interior
    Door(uid="CMD203AAAA", tag="D-M-STAIR", host="W-M-STRS", type_ref="DT-INT32",
         position=from_node("N-M-STR1", ft(2))),
    Door(uid="CMD204AAAA", tag="D-M-STOR", host="W-M-STOS2", type_ref="DT-INT32",
         position=from_node("N-M-BA1", ft(2))),
    Door(uid="CMD205AAAA", tag="D-M-BATH1", host="W-M-BAE", type_ref="DT-INT24",
         position=from_node("N-M-BA1", ft(1))),
    Door(uid="CMD206AAAA", tag="D-M-BATH2", host="W-M-BDN1", type_ref="DT-INT30",
         position=from_node("N-M-W3", ft(1, 6.5))),
    Door(uid="CMD207AAAA", tag="D-M-LAUN", host="W-M-HS3", type_ref="DT-INT56",
         position=from_node("N-M-D1", ft(0, 4))),
    Door(uid="CMD208AAAA", tag="D-M-STUDY", host="W-M-HS4", type_ref="DT-INT30",
         position=from_node("N-M-E3", ft(1))),
    Door(uid="CMD210AAAA", tag="D-M-BED", host="W-M-BDN2", type_ref="DT-INT32",
         position=from_node("N-M-D3", ft(5))),
    # Cased pass-through into the hall — door-sized (DT-INT32's 2'-8" x 6'-8") but
    # never leafed, so it carries no swing symbol and no IfcDoor.
    RoughOpening(uid="CMD209AAAA", tag="O-M-HALL", host="W-M-C4",
                 position=from_node("N-M-C2", ft(0, 6)), width=ft(2, 8),
                 height=ft(6, 8)),
    # Cased pass-through: living room → dressing corridor (per floorplan).
    RoughOpening(uid="CMD211AAAA", tag="O-M-DRESS", host="W-M-C2",
                 position=from_node("N-M-C1", ft(0, 6)), width=ft(3),
                 height=ft(6, 8)),
    # Windows — west (bearing: WT-2736), south (non-bearing: WT-3036), east (bearing)
    Window(uid="CMX301AAAA", tag="WIN-M-BED-W1", host="W-M-W4",
           type_ref="WT-2736", position=from_node("N-M-SW", ft(4, 2.5)),
           sill_height=ft(2)),
    Window(uid="CMX302AAAA", tag="WIN-M-BED-W2", host="W-M-W4",
           type_ref="WT-2736", position=from_node("N-M-SW", ft(9, 6.5)),
           sill_height=ft(2)),
    Window(uid="CMX303AAAA", tag="WIN-M-BED-S1", host="W-M-S1",
           type_ref="WT-3036", position=from_node("N-M-SW", ft(4, 1)),
           sill_height=ft(2)),
    Window(uid="CMX304AAAA", tag="WIN-M-BED-S2", host="W-M-S1",
           type_ref="WT-3036", position=from_node("N-M-SW", ft(9, 5)),
           sill_height=ft(2)),
    Window(uid="CMX305AAAA", tag="WIN-M-BATH2", host="W-M-W3",
           type_ref="WT-1424", position=from_node("N-M-W3", ft(4, 5)),
           sill_height=ft(4)),
    Window(uid="CMX306AAAA", tag="WIN-M-STOR", host="W-M-W1",
           type_ref="WT-2736", position=from_node("N-M-NW", ft(4, 2.5)),
           sill_height=ft(3)),
    Window(uid="CMX307AAAA", tag="WIN-M-LIV-S1", host="W-M-S2",
           type_ref="WT-3036", position=from_node("N-M-SE", ft(3, 5)),
           sill_height=ft(2)),
    Window(uid="CMX308AAAA", tag="WIN-M-LIV-S2", host="W-M-S2",
           type_ref="WT-3036", position=from_node("N-M-SE", ft(7, 5)),
           sill_height=ft(2)),
    Window(uid="CMX309AAAA", tag="WIN-M-LIV-E1", host="W-M-E1",
           type_ref="WT-2736", position=from_node("N-M-SE", ft(6, 10.5)),
           sill_height=ft(2, 6)),
    Window(uid="CMX310AAAA", tag="WIN-M-LIV-E2", host="W-M-E1",
           type_ref="WT-2736", position=from_node("N-M-SE", ft(10, 10.5)),
           sill_height=ft(2, 6)),
    # The dining pair, pushed south of where it started (centres were 22' and 26'). The 48"
    # pantry closet now takes the east wall from 22'-8" to 26'-8" and a tall cabinet over a
    # window is not a window, so the glass moved rather than the casework: centres 16'-0" and
    # 20'-8", the northern one clearing the pantry's south end by 8 1/2" of framing.
    #
    # The pair no longer reads at the 4' spacing the living windows below it use, and cannot:
    # E1 crosses onto the south wall segment, and each segment lays its studs out from its own
    # start, so W-M-E1's grid (16" from y=0) and W-M-E2's (16" from y=18') are 8" out of phase
    # with each other. A 27" RO in a bearing wall has to break exactly one stud, which pins
    # each centre to its own host's grid — 16'-0" is 12 bays up W-M-E1, 20'-8" is 2 bays up
    # W-M-E2 — and 4'-8" apart is where that lands them. The node at y=18' is a collinear
    # split rather than a corner, so the wall itself runs through unbroken.
    Window(uid="CMX311AAAA", tag="WIN-M-DIN-E1", host="W-M-E1",
           type_ref="WT-2736", position=from_node("N-M-SE", ft(14, 10.5)),
           sill_height=ft(2, 6)),
    Window(uid="CMX312AAAA", tag="WIN-M-DIN-E2", host="W-M-E2",
           type_ref="WT-2736", position=from_node("N-M-E1", ft(1, 6.5)),
           sill_height=ft(2, 6)),
    Window(uid="CMX313AAAA", tag="WIN-M-KITCH", host="W-M-E2",
           type_ref="WT-2736", position=from_node("N-M-NE", ft(2, 2.5)),
           sill_height=ft(3, 6)),
    # The cooking window, and the north wall's only one. A recirculating hood moves no air
    # outdoors, so the only way to clear a scorched pan is to open something next to the
    # stove: a 14" awning, immediately west of the range and reachable across the counter.
    # Centre x = 24'-8" is a bay centre on the 16" module, so it breaks no stud; sill 42"
    # clears the 36" counter by 6". The 30x60 that used to sit east of the range at
    # 29'-5"..31'-11" is gone: that stretch of wall is now one 5'-6" run of uppers, which is
    # the trade this kitchen wants — a north window on a north wall buys little light, and the
    # east wall's WIN-M-KITCH already lights the sink.
    Window(uid="82WVR597PA", tag="WIN-M-KITCH-N", host="W-M-N1", type_ref="WT-1424",
           position=from_node("N-M-NE", ft(10, 9)), sill_height=ft(3, 6)),
]

ROOMS = [
    Room(uid="CMR401AAAA", tag="RM-M-LIVING", seed=pt(ft(27), ft(12)),
         occupancy=Occupancy.LIVING, floor_finish="oak"),
    Room(uid="CMR402AAAA", tag="RM-M-BED", seed=pt(ft(9), ft(6)),
         occupancy=Occupancy.BEDROOM, floor_finish="oak"),
    Room(uid="CMR403AAAA", tag="RM-M-BATH1", seed=pt(ft(2), ft(24, 6)),
         occupancy=Occupancy.BATHROOM, floor_finish="tile"),
    Room(uid="CMR404AAAA", tag="RM-M-BATH2", seed=pt(ft(4), ft(18)),
         occupancy=Occupancy.BATHROOM, floor_finish="tile"),
    Room(uid="CMR405AAAA", tag="RM-M-LAUNDRY", seed=pt(ft(10, 6), ft(20)),
         occupancy=Occupancy.LAUNDRY, floor_finish="tile"),
    Room(uid="CMR406AAAA", tag="RM-M-STUDY", seed=pt(ft(15, 8), ft(20)),
         occupancy=Occupancy.OFFICE, floor_finish="oak"),
    Room(uid="CMR407AAAA", tag="RM-M-CLOSET", seed=pt(ft(13), ft(15, 4)),
         occupancy=Occupancy.STORAGE, floor_finish="oak"),
    Room(uid="CMR408AAAA", tag="RM-M-HALL", seed=pt(ft(11), ft(23, 4)),
         occupancy=Occupancy.HALLWAY, floor_finish="oak"),
    Room(uid="CMR409AAAA", tag="RM-M-STORAGE", seed=pt(ft(5), ft(31)),
         occupancy=Occupancy.STORAGE, floor_finish="sealed-concrete"),
    Room(uid="CMR410AAAA", tag="RM-M-STAIR", seed=pt(ft(14, 6), ft(31)),
         occupancy=Occupancy.STAIR, floor_finish="oak"),
]

ALARMS = [
    Alarm(uid="CMA701AAAA", tag="AL-M-BED", kind=AlarmKind.COMBO, room="RM-M-BED"),
    Alarm(uid="CMA702AAAA", tag="AL-M-HALL", kind=AlarmKind.COMBO, room="RM-M-HALL"),
]

# Structural deck of the main floor: 9" concrete over the basement.
SLABS = [
    Slab(uid="CMS501AAAA", tag="SL-M-DECK",
         outline=(pt(ft(0), ft(0)), pt(ft(36), ft(0)), pt(ft(36), ft(36)),
                  pt(ft(0), ft(36))),
         thickness=inch(9), openings=("FO-M-STAIR",), assembly="CATLIN_DECK_9_INT"),
]

# The opening is drawn to the *finished* well, not to the wall centrelines: it is the
# shaft a stair actually climbs, and the u-split resolver anchors its flights to the
# opening's near corner. West/east are W-B-STR's and W-B-CN's basement concrete faces —
# 12" concrete is thicker than the 2x6 walls stacked on it, so the basement is the
# narrowest point of the shaft and the one that sizes the flights. South is W-M-STRS's
# stair-side face (the door at the top of the stairs), north the exterior wall's.
FLOOR_OPENINGS = [
    FloorOpening(uid="CMF601AAAA", tag="FO-M-STAIR",
                 outline=(pt(ft(10, 6), ft(25, 2.375)), pt(ft(17, 6), ft(25, 2.375)),
                          pt(ft(17, 6), ft(35)), pt(ft(10, 6), ft(35))),
                 bearing_refs=("W-M-STRW", "W-M-STRW2")),
]

# 7'-0" well = 3'-3 3/4" + 4 1/2" well partition + 3'-3 3/4". Each flight clears the
# IRC R311.7.1 36" minimum above the handrail with room for the rail to project; the
# landing is the R311.7.6 36" minimum, which the resolver floors at the flight width to
# keep the U-turn walkable.
STAIRS = [
    Stair(uid="CST701AAAA", tag="ST-B2M", floor_opening="FO-M-STAIR",
          from_storey="basement", to_storey="main", width=ft(3, 3.75),
          layout="u_split_landing", run_direction="y",
          start=pt(ft(10, 6), ft(25, 2.375)), landing_depth=ft(3)),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *SLABS, *FLOOR_OPENINGS, *STAIRS]
