# haus: editable
from typehaus import (
    Door,
    DoorType,
    FloorSystem,
    JoistSpec,
    Node,
    Occupancy,
    Room,
    Wall,
    Window,
    WindowType,
    centered,
    from_node,
    ft,
    inch,
    pt,
    u_us,
)

# --- library-of-the-house types ---------------------------------------------
DOOR_TYPES = [
    DoorType(tag="DT-EXT36", width=ft(3), height=ft(6, 8), exterior=True,
             u_factor=u_us(0.20)),
]
WINDOW_TYPES = [
    WindowType(tag="WT-3050", width=ft(3), height=ft(5),
               u_factor=u_us(0.25), shgc=0.35, vt=0.5, operation="double_hung"),
]

# --- topology: a 24' x 20' rectangle ----------------------------------------
NODES = [
    Node(uid="N001AAAAAA", tag="N-1", position=pt(ft(0), ft(0))),
    Node(uid="N002AAAAAA", tag="N-2", position=pt(ft(24), ft(0))),
    Node(uid="N003AAAAAA", tag="N-3", position=pt(ft(24), ft(20))),
    Node(uid="N004AAAAAA", tag="N-4", position=pt(ft(0), ft(20))),
]

WALLS = [
    Wall(uid="W101AAAAAA", tag="W-101", start_node="N-1", end_node="N-2",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9)),
    Wall(uid="W102AAAAAA", tag="W-102", start_node="N-2", end_node="N-3",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9)),
    Wall(uid="W103AAAAAA", tag="W-103", start_node="N-3", end_node="N-4",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9)),
    Wall(uid="W104AAAAAA", tag="W-104", start_node="N-4", end_node="N-1",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9)),
]

OPENINGS = [
    Door(uid="D101AAAAAA", tag="D-101", host="W-101", type_ref="DT-EXT36",
         position=from_node("N-1", ft(3))),
    Window(uid="WN10AAAAAA", tag="WIN-101", host="W-103", type_ref="WT-3050",
           position=centered(), sill_height=ft(2)),
]

ROOMS = [
    Room(uid="RMMNAAAAAA", tag="RM-Main", seed=pt(ft(12), ft(10)),
         occupancy=Occupancy.LIVING, floor_finish="oak"),
]

FLOOR = [
    FloorSystem(uid="FSMNAAAAAA", tag="FS-MAIN",
                joists=JoistSpec(member="11.875 I-joist", spacing=inch(16), direction="y",
                                 bearing_refs=("W-101", "W-103"))),
]
