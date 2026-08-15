# haus: editable
from typehaus import (
    Alarm,
    AlarmKind,
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
    # Interior passage leaf — the upper storey's bedroom door off the landing. The library
    # lives on this storey for the whole house, which is why an upper-storey door type is
    # declared here.
    DoorType(tag="DT-INT32", width=ft(2, 8), height=ft(6, 8)),
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

# R303.1 asks a habitable room for glazing at 8% of its floor area and openable area at
# 4%. RM-Main resolves to 475 sf, so it wants 38 sf of glass and 19 sf that opens; the four
# double-hung units below give 60 sf and 30 sf (a double hung's openable half is what
# counts). One unit centred on each of the three blind walls, one beside the front door:
# a rectangle this simple has no reason to prefer an elevation, and centring each keeps the
# framing symmetric about the wall it sits in.
#
# `from_node` positions an opening's *near jamb*, not its centre, so WIN-102 runs x
# 16'..19'.
OPENINGS = [
    Door(uid="D101AAAAAA", tag="D-101", host="W-101", type_ref="DT-EXT36",
         position=from_node("N-1", ft(3))),
    # South (front) wall, east of the door: well clear of R308.4.2's 24" arc around the
    # leaf, which runs x 3'..6'.
    Window(uid="WN11AAAAAA", tag="WIN-102", host="W-101", type_ref="WT-3050",
           position=from_node("N-1", ft(16)), sill_height=ft(2)),
    # East wall — morning light into the dining end.
    Window(uid="WN12AAAAAA", tag="WIN-103", host="W-102", type_ref="WT-3050",
           position=centered(), sill_height=ft(2)),
    Window(uid="WN10AAAAAA", tag="WIN-101", host="W-103", type_ref="WT-3050",
           position=centered(), sill_height=ft(2)),
    # West wall.
    Window(uid="WN13AAAAAA", tag="WIN-104", host="W-104", type_ref="WT-3050",
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

ALARMS = [
    # R314.3 puts a smoke alarm on *every* storey of the dwelling, not only the sleeping
    # ones, and R314.4 wants its primary power from the building wiring — which is what
    # naming a circuit says. CKT-ALARMS is the unswitched branch this house reserves for
    # life safety; author it in a panel schedule and `electrical.circuit_refs` will
    # reconcile the two.
    Alarm(uid="ALMNAAAAAA", tag="AL-Main", kind=AlarmKind.COMBO, room="RM-Main",
          circuit="CKT-ALARMS"),
]
