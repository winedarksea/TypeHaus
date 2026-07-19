# haus: editable
from typehaus import Alarm, AlarmKind, Node, Occupancy, Room, Wall, Window, centered, ft, pt

# Upper storey shares the wall lines of the main storey so the vertical stacking
# pass (#43) derives a wall-line stack and emits a storey-stack condition.
NODES = [
    Node(uid="N201AAAAAA", tag="N-201", position=pt(ft(0), ft(0))),
    Node(uid="N202AAAAAA", tag="N-202", position=pt(ft(24), ft(0))),
    Node(uid="N203AAAAAA", tag="N-203", position=pt(ft(24), ft(20))),
    Node(uid="N204AAAAAA", tag="N-204", position=pt(ft(0), ft(20))),
]

WALLS = [
    Wall(uid="W201AAAAAA", tag="W-201", start_node="N-201", end_node="N-202",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9)),
    Wall(uid="W202AAAAAA", tag="W-202", start_node="N-202", end_node="N-203",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9)),
    Wall(uid="W203AAAAAA", tag="W-203", start_node="N-203", end_node="N-204",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9)),
    Wall(uid="W204AAAAAA", tag="W-204", start_node="N-204", end_node="N-201",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9)),
]

OPENINGS = [
    Window(uid="WN20AAAAAA", tag="WIN-201", host="W-201", type_ref="WT-3050",
           position=centered(), sill_height=ft(2, 6)),
]

ROOMS = [
    Room(uid="RMUPAAAAAA", tag="RM-Upper", seed=pt(ft(12), ft(10)),
         occupancy=Occupancy.BEDROOM, floor_finish="carpet"),
]

ALARMS = [
    Alarm(uid="ALUPAAAAAA", tag="AL-Upper-Bed", kind=AlarmKind.COMBO, room="RM-Upper"),
]
