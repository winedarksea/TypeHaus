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
    FoundationWall(uid="CBW113AAAA", tag="W-B-CN", start_node="N-B-C",
                   end_node="N-B-N1", assembly="CATLIN_CONC_12_INT",
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
    FoundationWall(uid="CBW116AAAA", tag="W-B-STR", start_node="N-B-N2",
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
]

OPENINGS = [
    # Interior circulation
    Door(uid="CBD201AAAA", tag="D-B-FURN", host="W-B-CW", type_ref="DT-INT-SWING32",
         position=from_node("N-B-W1", ft(3))),
    Door(uid="CBD202AAAA", tag="D-B-PLAY", host="W-B-CE", type_ref="DT-INT-BIFOLD56",
         position=from_node("N-B-C", ft(6))),
    # Centred in the 3'-4" aisle the sauna's north wall leaves against the center wall.
    # ``from_node`` offsets the opening's near *edge*, so 8" leaves ~4" of concrete jamb
    # at each end of the 4'-2" W-B-CS2 segment.
    Door(uid="CBD203AAAA", tag="D-B-GYM", host="W-B-CS2", type_ref="DT-INT-SWING32",
         position=from_node("N-B-C1", inch(8)), flip_swing=False, flip_hinge=False),
    Door(uid="CBD204AAAA", tag="D-B-NE", host="W-B-CN", type_ref="DT-INT-SWING32",
         position=from_node("N-B-C", ft(4))),
    # Way out of the enclosed stair shaft, into the workshop rather than through the
    # mechanical room (reference draws this door in the center wall too). Set in the
    # descending flight's lane rather than centred, so it is not head-on to the well
    # partition at x=14'.
    Door(uid="CBD207AAAA", tag="D-B-STAIR", host="W-B-CW2", type_ref="DT-INT-SWING32",
         position=from_node("N-B-STR", inch(10))),
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
