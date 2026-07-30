# haus: editable
# Basement — 12" concrete walkout box, 18' center grid, sauna, stair (WP3.1).
# South wall is the walkout side facing the sunken garden. Perimeter walls align on the
# concrete exterior face so the 4" of exterior XPS stacks directly under the framed
# wall's 4" polyiso+EPS (#43 control-layer continuity).
from typehaus import (
    Alarm,
    AlarmKind,
    Door,
    FloorOpening,
    FoundationWall,
    Layer,
    LayerFunction,
    Node,
    Occupancy,
    Room,
    Slab,
    SlabThermalBreak,
    SlabThermalBreak,
    Wall,
    Window,
    face,
    from_node,
    ft,
    inch,
    pt,
)

# Plan datums this storey is dimensioned to (reference: catlin_floorplan/
# "Colin House_Basement_Level 1.png"). Every one of them is a *clear* face dimension,
# so the node line each wall sits on is back-calculated from the finished faces:
#   furnace room 8'-6" | stair shaft 7'-0" | playroom 16'-6"   across the north row
#   workshop leg 7'-6" | sauna 8'-0"       | playroom 16'-6"   across the south row
# The stair shaft's 7'-0" is the code-minimum well: two 3'-3 3/4" flights either side of
# a 4 1/2" 2x4 well partition. Putting W-B-STR on x=10' as 12" concrete lands the shaft
# and the furnace room on both reference numbers at once, because the 18' bearing grid
# fixes the shaft's east face at 17'-6".
NODES = [
    # Perimeter (split at grid lines + partition tees)
    Node(uid="CBN001AAAA", tag="N-B-SW", position=pt(ft(0), ft(0))),
    Node(uid="CBN002AAAA", tag="N-B-S1", position=pt(ft(8, 10), ft(0))),
    Node(uid="CBN003AAAA", tag="N-B-S2", position=pt(ft(18), ft(0))),
    Node(uid="CBN004AAAA", tag="N-B-SE", position=pt(ft(36), ft(0))),
    Node(uid="CBN005AAAA", tag="N-B-E1", position=pt(ft(36), ft(18))),
    Node(uid="CBN006AAAA", tag="N-B-NE", position=pt(ft(36), ft(36))),
    Node(uid="CBN007AAAA", tag="N-B-N1", position=pt(ft(18), ft(36))),
    Node(uid="CBN008AAAA", tag="N-B-N2", position=pt(ft(10), ft(36))),
    Node(uid="CBN009AAAA", tag="N-B-NW", position=pt(ft(0), ft(36))),
    Node(uid="CBN010AAAA", tag="N-B-W1", position=pt(ft(0), ft(18))),
    # Interior grid + stair + sauna
    Node(uid="CBN011AAAA", tag="N-B-C", position=pt(ft(18), ft(18))),
    Node(uid="CBN012AAAA", tag="N-B-C1", position=pt(ft(18), ft(13, 10))),
    # The stair shaft runs the full north-row depth and lands on the center wall, so its
    # west wall tees into it rather than dying in the middle of the furnace room.
    Node(uid="CBN013AAAA", tag="N-B-STR", position=pt(ft(10), ft(18))),
    Node(uid="CBN014AAAA", tag="N-B-SA1", position=pt(ft(8, 10), ft(13, 10))),
    # The stair-foot bathroom's north partition (2026-07-30). It spans the shaft's full 7'-0"
    # clear width, so the nodes sit on the two concrete walls' own node lines (x=10' and
    # x=18') and the partition tees into them rather than dying in mid-air. y=21'-9 3/8" is
    # back-calculated from the clear face: the room wants 3'-0" of depth off W-B-CW2's north
    # face at 18'-6", and INT_2X6_STAGGERED_PLUMBING is 6 3/4" thick, so its centreline is
    # 21'-6" + 3 3/8".
    Node(uid="CBN015AAAA", tag="N-B-BA-W", position=pt(ft(10), ft(21, 9.375))),
    Node(uid="CBN016AAAA", tag="N-B-BA-E", position=pt(ft(18), ft(21, 9.375))),
]

WALLS = [
    # Perimeter foundation walls (12" + exterior XPS), CCW from SW corner.
    FoundationWall(uid="CBW101AAAA", tag="W-B-S1", start_node="N-B-SW",
                   end_node="N-B-S1", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW102AAAA", tag="W-B-S2", start_node="N-B-S1",
                   end_node="N-B-S2", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW103AAAA", tag="W-B-S3", start_node="N-B-S2",
                   end_node="N-B-SE", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW104AAAA", tag="W-B-E1", start_node="N-B-SE",
                   end_node="N-B-E1", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW105AAAA", tag="W-B-E2", start_node="N-B-E1",
                   end_node="N-B-NE", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW106AAAA", tag="W-B-N1", start_node="N-B-NE",
                   end_node="N-B-N1", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW107AAAA", tag="W-B-N2", start_node="N-B-N1",
                   end_node="N-B-N2", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW108AAAA", tag="W-B-N3", start_node="N-B-N2",
                   end_node="N-B-NW", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW109AAAA", tag="W-B-W1", start_node="N-B-NW",
                   end_node="N-B-W1", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW110AAAA", tag="W-B-W2", start_node="N-B-W1",
                   end_node="N-B-SW", assembly="CATLIN_BASEMENT_12",
                   alignment=face("concrete-ext"),
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    # Center cross walls (12" concrete) — the 18' bearing grid.
    # This segment is exactly the sauna's east boundary, so it carries the liner stack
    # directly on the concrete. Aligned on the concrete's far face so the 18' bearing
    # grid stays put and the liner grows into the sauna.
    FoundationWall(uid="CBW111AAAA", tag="W-B-CS", start_node="N-B-C1",
                   end_node="N-B-S2", assembly="SAUNA_LINER_ON_CONCRETE",
                   alignment=face("concrete-ext", offset=inch(-6)),
                   interior_room="RM-B-SAUNA",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW112AAAA", tag="W-B-CS2", start_node="N-B-C1",
                   end_node="N-B-C", assembly="CATLIN_CONC_12_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    # Split at N-B-BA-E on 2026-07-30, the same way W-B-CW is split at N-B-STR and for the
    # same reason: the stair-foot bathroom's north partition tees into this line, and a tee
    # has to land on a node both walls share or `integrity.wall_loop_open` reads the partition
    # as a wall with a free end. W-B-CN keeps the tag, the uid and the north 14'-2 5/8" —
    # which is the whole run W-M-C5 stacks on, so the bearing stack above is untouched.
    FoundationWall(uid="CBW113AAAA", tag="W-B-CN", start_node="N-B-BA-E",
                   end_node="N-B-N1", assembly="CATLIN_CONC_12_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW121AAAA", tag="W-B-CN2", start_node="N-B-C",
                   end_node="N-B-BA-E", assembly="CATLIN_CONC_12_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    # Split at the stair shaft's west wall so the shaft is a real tee, not a wall end.
    FoundationWall(uid="CBW114AAAA", tag="W-B-CW", start_node="N-B-W1",
                   end_node="N-B-STR", assembly="CATLIN_CONC_12_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW119AAAA", tag="W-B-CW2", start_node="N-B-STR",
                   end_node="N-B-C", assembly="CATLIN_CONC_12_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW115AAAA", tag="W-B-CE", start_node="N-B-C",
                   end_node="N-B-E1", assembly="CATLIN_CONC_12_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    # Stair shaft's west wall — 12" concrete on x=10', running the full north-row depth
    # so the shaft encloses (reference: "Stairway 7' x 16' 6 1/2""). 12" rather than 8"
    # because that is what puts the shaft's west face on 9'-6": the furnace room then
    # reads its reference 8'-6" clear and the shaft its 7'-0" off the same wall.
    # Split at N-B-BA-W, the west end of that same partition (2026-07-30). W-B-STR keeps the
    # tag, the uid and the north 14'-2 5/8", which is what W-M-STRW / W-M-STRW2 stack on;
    # W-B-STR2 is the 3'-3 3/8" stub alongside the bathroom, and it is the segment the room's
    # three ceiling-level service crossings are cast into (plan/mep.py's WALL_SLEEVES).
    FoundationWall(uid="CBW116AAAA", tag="W-B-STR", start_node="N-B-N2",
                   end_node="N-B-BA-W", assembly="CATLIN_CONC_12_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW122AAAA", tag="W-B-STR2", start_node="N-B-BA-W",
                   end_node="N-B-STR", assembly="CATLIN_CONC_12_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    # Sauna partitions — SAUNA_2X4 carries the hot-side liner (T&G over furring over
    # foil-faced polyiso) as part of the wall type, so the vapour control layer is a
    # property of the assembly rather than a room finish override. East wall is the
    # center concrete wall, which takes the liner via SAUNA_LINER_ON_CONCRETE.
    # Both are interior partitions, so the storey's outer loop says nothing about which
    # way they face; interior_room names the side the liner must land on.
    Wall(uid="CBW117AAAA", tag="W-B-SA-W", start_node="N-B-S1",
         end_node="N-B-SA1", assembly="SAUNA_2X4", top=ft(7, 6),
         interior_room="RM-B-SAUNA"),
    Wall(uid="CBW118AAAA", tag="W-B-SA-N", start_node="N-B-SA1",
         end_node="N-B-C1", assembly="SAUNA_2X4", top=ft(7, 6),
         interior_room="RM-B-SAUNA"),
    # The stair-foot bathroom's only framed wall (2026-07-30). Everything else enclosing this
    # room is already cast: W-B-CW2 south, W-B-STR west, W-B-CN east.
    #
    # INT_2X6_STAGGERED_PLUMBING, not a 2x4 partition, and non-bearing rather than the
    # continuous-stud INT_2X6_PLUMBING: this wall is the *only* stud cavity the room has, so
    # it is where the lavatory's and the water closet's shared 1 1/2" vent rises before it
    # turns west for the chase (PR-B-BATH-VENT, plan/mep.py). The three concrete walls cannot
    # take a stack, and a 2x4 could not either — `advisory.wet_wall_depth` holds a drain
    # fixture's chase to preferences.toml's 5 1/2", which is exactly this cavity.
    #
    # Runs the shaft's full width, node line to node line, so it tees into both concrete
    # walls instead of dying 6" short of each. Top is the 8'-3" underside of SL-M-DECK less
    # the 3" the vent needs to turn over the top plate: 8'-0" is the plate line the room's
    # ceiling hangs from.
    Wall(uid="CBW120AAAA", tag="W-B-BA-N", start_node="N-B-BA-W",
         end_node="N-B-BA-E", assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(8),
         interior_room="RM-B-BATH"),
]

OPENINGS = [
    # Interior circulation
    Door(uid="CBD201AAAA", tag="D-B-FURN", host="W-B-CW", type_ref="DT-INT-SWING32",
         position=from_node("N-B-W1", ft(3))),
    Door(uid="CBD202AAAA", tag="D-B-PLAY", host="W-B-CE", type_ref="DT-INT-FRENCH60",
         position=from_node("N-B-C", ft(6))),
    # Centred in the 3'-4" aisle the sauna's north wall leaves against the center wall.
    # ``from_node`` offsets the opening's near *edge*, so 8" leaves ~4" of concrete jamb
    # at each end of the 4'-2" W-B-CS2 segment.
    Door(uid="CBD203AAAA", tag="D-B-GYM", host="W-B-CS2", type_ref="DT-INT-SWING32",
         position=from_node("N-B-C1", inch(8)), flip_swing=False, flip_hinge=False),
    # Pushed 6" north on 2026-07-30 (was ft(4), a near edge at y=22'-0"): the stair-foot
    # bathroom's north partition resolves to a 22'-0 3/4" north face, which would have landed
    # 3/4" inside this opening's south jamb. At 22'-6" the door keeps 5 1/4" of concrete jamb
    # south of it, and the flight it faces still springs 1'-4" further north at 26'-0 3/8".
    Door(uid="CBD204AAAA", tag="D-B-NE", host="W-B-CN", type_ref="DT-INT-SWING32",
         position=from_node("N-B-BA-E", inch(8.625))),
    # The stair shaft's south door, which used to be D-B-STAIR — the way out into the
    # workshop through W-B-CW2's concrete. On 2026-07-30 the south 3'-0" of the shaft became
    # RM-B-BATH, so this leaf moved off the concrete and onto the bathroom's north partition
    # (the owner's call: "removing D-B-STAIR, or moving it as the bathroom door"). Same uid —
    # it is the same door, rehung — and the same 32" leaf, which is more than a 3'-deep
    # bathroom needs but is the width that keeps the room usable from a wheelchair.
    #
    # It swings OUTWARD, into the stair landing, and that is not a style choice: the room is
    # 3'-0" deep, and an inswing leaf would sweep the whole floor — through the water closet's
    # IRC P2705.1 clearance zone on the west, the lavatory on the east and the receptacle
    # beside it, all of which `integrity.door_swing_conflict` reads as conflicts, correctly.
    # Outward is the *default* swing on this wall: the sweep rotates from the closed leaf
    # toward the wall's left-hand normal, and W-B-BA-N runs west-to-east, so leaving
    # `flip_swing` alone throws the leaf north. `flip_swing=True` was the first attempt and
    # put it back inside the room.
    #
    # Positioned so the leaf clears both fixtures' plan footprints: jambs at x 12'-8"..15'-4"
    # sit between the WC's clearance zone (which ends at x=13'-5", so the opening overlaps
    # only clear floor, never the fixture) and the lavatory's west edge at 15'-10".
    Door(uid="CBD207AAAA", tag="D-B-BATH", host="W-B-BA-N", type_ref="DT-INT-SWING32",
         position=from_node("N-B-BA-W", ft(2, 8))),
    Door(uid="CBD205AAAA", tag="D-B-SAUNA", host="W-B-SA-W", type_ref="DT-INT-SWING24",
         position=from_node("N-B-S1", ft(10, 10.4375))),
    # Raise the exterior threshold above the basement floor to resist sunken-garden flooding.
    Door(uid="CBD206AAAA", tag="D-B-PATIO", host="W-B-S3", type_ref="DT-EXT-SLIDE60",
         position=from_node("N-B-S2", ft(1, 4)), sill_height=inch(7)),
    Window(uid="CBX301AAAA", tag="WIN-B-SAUNA", host="W-B-S2",
           type_ref="WT-3660", position=from_node("N-B-S1", ft(2, 6)),
           sill_height=ft(3)),
]

ROOMS = [
    Room(uid="CBR401AAAA", tag="RM-B-FURNACE", seed=pt(ft(5), ft(30)),
         occupancy=Occupancy.MECHANICAL, floor_finish="sealed-concrete"),
    # W-B-STR now separates this from the furnace room, so the stair bottom is its own
    # space instead of dumping arrivals into the mechanical room.
    Room(uid="CBR406AAAA", tag="RM-B-STAIR", seed=pt(ft(14), ft(30)),
         occupancy=Occupancy.STAIR, floor_finish="sealed-concrete"),
    # The stair-foot bathroom (2026-07-30). The south 3'-0" of the shaft, below the flight —
    # ST-B2M's bottom riser is at y=26'-0 3/8", so this takes floor the stair never used.
    # Clear face x 10'-6"..17'-6", y 18'-6"..21'-6": 7'-0" x 3'-0", 21 sf.
    #
    # Why the fixtures run east-west rather than facing the long wall: 3'-0" of depth cannot
    # hold a water closet facing north or south (19"-28" of bowl plus IRC P2705.1's 21" in
    # front needs 40"+), but it holds one *sideways* with room to spare, because the 30" the
    # code wants across the bowl fits in 36" and the 21" in front runs down the room's length
    # instead of across it. That is the whole reason the WC is on the west end and the
    # lavatory on the east — see plan/fixtures.py.
    Room(uid="CBR407AAAA", tag="RM-B-BATH", seed=pt(ft(14), ft(20)),
         occupancy=Occupancy.BATHROOM, floor_finish="tile"),
    Room(uid="CBR402AAAA", tag="RM-B-WORKSHOP", seed=pt(ft(5), ft(8)),
         occupancy=Occupancy.UTILITY, floor_finish="sealed-concrete"),
    # No wall_lining override: the liner is part of SAUNA_2X4 / SAUNA_LINER_ON_CONCRETE.
    Room(uid="CBR403AAAA", tag="RM-B-SAUNA", seed=pt(ft(14), ft(6)),
         occupancy=Occupancy.BATHROOM, floor_finish="tile"),
    Room(uid="CBR404AAAA", tag="RM-B-PLAY-N", seed=pt(ft(27), ft(27)),
         occupancy=Occupancy.MEDIA, floor_finish="carpet"),
    Room(uid="CBR405AAAA", tag="RM-B-GYM", seed=pt(ft(27), ft(9)),
         occupancy=Occupancy.LIVING, floor_finish="rubber"),
]

ALARMS = [
    Alarm(uid="CBA701AAAA", tag="AL-B-COMBO", kind=AlarmKind.COMBO, room="RM-B-PLAY-N",
          circuit="CKT-LT-BACKUP"),
]

# No radiant floor in the basement. RM-B-SAUNA had FH-B-SAUNA until 2026-07-25: a heated
# floor under a room that already runs at 190 °F is heat with nowhere to go, and its stat
# had no honest place to read from (see the note that used to sit on ED-B-SAUNA-FH-STAT).
# The electric radiant zones are all on the storeys above — main.py and second.py.

SLABS = [
    Slab(uid="CBS501AAAA", tag="SL-B-FLOOR",
         outline=(pt(ft(0), ft(0)), pt(ft(36), ft(0)), pt(ft(36), ft(36)),
                  pt(ft(0), ft(36))),
         thickness=inch(3.5), assembly="CATLIN_SLAB_FLOOR",
         perimeter_thermal_break=SlabThermalBreak(material_ref="xps", thickness=inch(1))),
]

FLOOR_OPENINGS = [
    # Shower recess is a finish-zone concern; the stair arrives via the slab above.
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *SLABS, *FLOOR_OPENINGS]
