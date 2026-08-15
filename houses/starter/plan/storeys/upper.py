# haus: editable
from typehaus import (
    Alarm,
    AlarmKind,
    Door,
    Node,
    Occupancy,
    Room,
    Wall,
    Window,
    centered,
    ft,
    pt,
)

# Upper storey shares the wall lines of the main storey so the vertical stacking
# pass (#43) derives a wall-line stack and emits a storey-stack condition.
#
# The outer rectangle is the main storey's; the node inside the loop (N-206) and the two on
# it (N-205, N-207) carry an L of partition that takes the north-west 8' x 8' out of the
# floor as a landing. That landing is not decoration: R314.3 wants a smoke alarm *outside* the
# sleeping area as well as in it, and R315.3 puts the CO alarm outside each separate
# sleeping area — neither has anywhere to go on a storey that is one bedroom wall to wall.
NODES = [
    Node(uid="N201AAAAAA", tag="N-201", position=pt(ft(0), ft(0))),
    Node(uid="N202AAAAAA", tag="N-202", position=pt(ft(24), ft(0))),
    Node(uid="N203AAAAAA", tag="N-203", position=pt(ft(24), ft(20))),
    # The north wall tees here, at the landing's east side.
    Node(uid="N205AAAAAA", tag="N-205", position=pt(ft(8), ft(20))),
    Node(uid="N204AAAAAA", tag="N-204", position=pt(ft(0), ft(20))),
    # The landing's inside corner, and the tee where its south wall meets the west wall.
    Node(uid="N207AAAAAA", tag="N-207", position=pt(ft(0), ft(12))),
    Node(uid="N206AAAAAA", tag="N-206", position=pt(ft(8), ft(12))),
]

WALLS = [
    Wall(uid="W201AAAAAA", tag="W-201", start_node="N-201", end_node="N-202",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9)),
    Wall(uid="W202AAAAAA", tag="W-202", start_node="N-202", end_node="N-203",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9)),
    # The north and west walls are each split at the node where a partition tees into
    # them — a wall is an edge between exactly two nodes, so a tee is two walls, not one.
    # Two upper walls over one lower wall is an ambiguous stack, so the longer segment of
    # each pair names the wall below it and takes the storey-stack edge.
    Wall(uid="W203AAAAAA", tag="W-203", start_node="N-203", end_node="N-205",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9), stacks_on="W-103"),
    Wall(uid="W23BAAAAAA", tag="W-203B", start_node="N-205", end_node="N-204",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9)),
    Wall(uid="W204AAAAAA", tag="W-204", start_node="N-204", end_node="N-207",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9)),
    Wall(uid="W24BAAAAAA", tag="W-204B", start_node="N-207", end_node="N-201",
         assembly="HOUSE_WALL_2X6_WITH_ZIPR", top=ft(9), stacks_on="W-104"),
    # --- landing partitions ------------------------------------------------------
    Wall(uid="W205AAAAAA", tag="W-205", start_node="N-205", end_node="N-206",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="W206AAAAAA", tag="W-206", start_node="N-206", end_node="N-207",
         assembly="INT_2X4_PARTITION", top=ft(9)),
]

# RM-Upper resolves to 411 sf, so R303.1 wants 33 sf of glazing and 16.5 sf openable; the
# three bedroom units below give 45 sf and 22.5 sf (a double hung's openable half is what
# counts). WIN-204 lights the landing, which R303.1 does not reach — a hallway is not a
# habitable room — but a landing that arrives in the dark is an unpleasant house.
OPENINGS = [
    # The R310 escape opening, unchanged: a 3'-0" x 5'-0" double hung at a 2'-6" sill.
    Window(uid="WN20AAAAAA", tag="WIN-201", host="W-201", type_ref="WT-3050",
           position=centered(), sill_height=ft(2, 6)),
    Window(uid="WN21AAAAAA", tag="WIN-202", host="W-202", type_ref="WT-3050",
           position=centered(), sill_height=ft(2, 6)),
    Window(uid="WN22AAAAAA", tag="WIN-203", host="W-203", type_ref="WT-3050",
           position=centered(), sill_height=ft(2, 6)),
    Window(uid="WN23AAAAAA", tag="WIN-204", host="W-203B", type_ref="WT-3050",
           position=centered(), sill_height=ft(2, 6)),
    Door(uid="D201AAAAAA", tag="D-201", host="W-205", type_ref="DT-INT32",
         position=centered()),
]

ROOMS = [
    Room(uid="RMUPAAAAAA", tag="RM-Upper", seed=pt(ft(16), ft(8)),
         occupancy=Occupancy.BEDROOM, floor_finish="carpet"),
    Room(uid="RMUHAAAAAA", tag="RM-Upper-Hall", seed=pt(ft(4), ft(16)),
         occupancy=Occupancy.HALLWAY, floor_finish="oak"),
]

ALARMS = [
    Alarm(uid="ALUPAAAAAA", tag="AL-Upper-Bed", kind=AlarmKind.COMBO, room="RM-Upper",
          circuit="CKT-ALARMS"),
    # The head R314.3 puts "outside each separate sleeping area, in the immediate vicinity
    # of the bedrooms", and the one R315.3 asks for on the same words. It is a COMBO so it
    # answers both, and it is on the landing rather than in the bedroom because "outside"
    # is the whole point of the sentence.
    Alarm(uid="ALUHAAAAAA", tag="AL-Upper-Hall", kind=AlarmKind.COMBO,
          room="RM-Upper-Hall", circuit="CKT-ALARMS"),
]
