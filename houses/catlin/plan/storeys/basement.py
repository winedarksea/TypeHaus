# haus: editable
# Basement — 12" concrete walkout box, 18' center grid, sauna, stair (WP3.1).
# South wall is the walkout side facing the sunken garden. Perimeter walls align on the
# concrete exterior face so the 4" of exterior XPS stacks directly under the framed
# wall's 4" polyiso+EPS (#43 control-layer continuity).
from typehaus import (
    Door,
    FloorOpening,
    FoundationWall,
    Layer,
    LayerFunction,
    Node,
    Occupancy,
    Room,
    Slab,
    Wall,
    Window,
    face,
    from_node,
    ft,
    inch,
    pt,
)

NODES = [
    # Perimeter (split at grid lines + partition tees)
    Node(uid="CBN001AAAA", tag="N-B-SW", position=pt(ft(0), ft(0))),
    Node(uid="CBN002AAAA", tag="N-B-S1", position=pt(ft(10), ft(0))),
    Node(uid="CBN003AAAA", tag="N-B-S2", position=pt(ft(18), ft(0))),
    Node(uid="CBN004AAAA", tag="N-B-SE", position=pt(ft(36), ft(0))),
    Node(uid="CBN005AAAA", tag="N-B-E1", position=pt(ft(36), ft(18))),
    Node(uid="CBN006AAAA", tag="N-B-NE", position=pt(ft(36), ft(36))),
    Node(uid="CBN007AAAA", tag="N-B-N1", position=pt(ft(18), ft(36))),
    Node(uid="CBN008AAAA", tag="N-B-N2", position=pt(ft(11), ft(36))),
    Node(uid="CBN009AAAA", tag="N-B-NW", position=pt(ft(0), ft(36))),
    Node(uid="CBN010AAAA", tag="N-B-W1", position=pt(ft(0), ft(18))),
    # Interior grid + stair + sauna
    Node(uid="CBN011AAAA", tag="N-B-C", position=pt(ft(18), ft(18))),
    Node(uid="CBN012AAAA", tag="N-B-C1", position=pt(ft(18), ft(13, 4))),
    Node(uid="CBN013AAAA", tag="N-B-STR", position=pt(ft(11), ft(25)),
         open_end=True),
    Node(uid="CBN014AAAA", tag="N-B-SA1", position=pt(ft(10), ft(13, 4))),
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
    FoundationWall(uid="CBW111AAAA", tag="W-B-CS", start_node="N-B-S2",
                   end_node="N-B-C1", assembly="CATLIN_CONC_12_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW112AAAA", tag="W-B-CS2", start_node="N-B-C1",
                   end_node="N-B-C", assembly="CATLIN_CONC_12_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW113AAAA", tag="W-B-CN", start_node="N-B-C",
                   end_node="N-B-N1", assembly="CATLIN_CONC_12_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW114AAAA", tag="W-B-CW", start_node="N-B-W1",
                   end_node="N-B-C", assembly="CATLIN_CONC_12_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    FoundationWall(uid="CBW115AAAA", tag="W-B-CE", start_node="N-B-C",
                   end_node="N-B-E1", assembly="CATLIN_CONC_12_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    # Stair side wall — 8" concrete, immediately west of the stair opening.
    FoundationWall(uid="CBW116AAAA", tag="W-B-STR", start_node="N-B-N2",
                   end_node="N-B-STR", assembly="CATLIN_CONC_8_INT",
                   top_elevation=ft(0), bottom_elevation=ft(-9)),
    # Sauna partitions (2x4), east wall is the center concrete wall.
    Wall(uid="CBW117AAAA", tag="W-B-SA-W", start_node="N-B-S1",
         end_node="N-B-SA1", assembly="INT_2X4_PARTITION", top=ft(7, 6)),
    Wall(uid="CBW118AAAA", tag="W-B-SA-N", start_node="N-B-SA1",
         end_node="N-B-C1", assembly="INT_2X4_PARTITION", top=ft(7, 6)),
]

OPENINGS = [
    # Interior circulation
    Door(uid="CBD201AAAA", tag="D-B-FURN", host="W-B-CW", type_ref="DT-INT32",
         position=from_node("N-B-W1", ft(3))),
    Door(uid="CBD202AAAA", tag="D-B-PLAY", host="W-B-CE", type_ref="DT-INT60",
         position=from_node("N-B-C", ft(6))),
    Door(uid="CBD203AAAA", tag="D-B-GYM", host="W-B-CS2", type_ref="DT-INT32",
         position=from_node("N-B-C1", ft(1))),
    Door(uid="CBD204AAAA", tag="D-B-NE", host="W-B-CN", type_ref="DT-INT32",
         position=from_node("N-B-C", ft(4))),
    Door(uid="CBD205AAAA", tag="D-B-SAUNA", host="W-B-SA-W", type_ref="DT-INT24",
         position=from_node("N-B-S1", ft(2))),
    # Walkout to the sunken garden (south wall) + garden-lit glazing.
    Door(uid="CBD206AAAA", tag="D-B-PATIO", host="W-B-S3", type_ref="DT-PATIO60",
         position=from_node("N-B-S2", ft(1, 4))),
    Window(uid="CBX301AAAA", tag="WIN-B-SAUNA", host="W-B-S2",
           type_ref="WT-3050", position=from_node("N-B-S1", ft(2, 9)),
           sill_height=ft(3)),
    Window(uid="CBX302AAAA", tag="WIN-B-WSHOP", host="W-B-S1",
           type_ref="WT-3050", position=from_node("N-B-SW", ft(3, 9)),
           sill_height=ft(3)),
    Window(uid="CBX303AAAA", tag="WIN-B-GYM", host="W-B-S3",
           type_ref="WT-3050", position=from_node("N-B-SE", ft(4, 9)),
           sill_height=ft(3)),
]

_SAUNA_LINING = (
    Layer(name="cedar-tg", material_ref="cedar-tg", thickness=inch(0.75),
          function=LayerFunction.FINISH),
)

ROOMS = [
    Room(uid="CBR401AAAA", tag="RM-B-FURNACE", seed=pt(ft(5), ft(30)),
         occupancy=Occupancy.MECHANICAL, floor_finish="sealed-concrete"),
    Room(uid="CBR402AAAA", tag="RM-B-WORKSHOP", seed=pt(ft(5), ft(8)),
         occupancy=Occupancy.UTILITY, floor_finish="sealed-concrete"),
    Room(uid="CBR403AAAA", tag="RM-B-SAUNA", seed=pt(ft(14), ft(6)),
         occupancy=Occupancy.BATHROOM, floor_finish="tile",
         wall_lining=_SAUNA_LINING),
    Room(uid="CBR404AAAA", tag="RM-B-PLAY-N", seed=pt(ft(27), ft(27)),
         occupancy=Occupancy.MEDIA, floor_finish="carpet"),
    Room(uid="CBR405AAAA", tag="RM-B-GYM", seed=pt(ft(27), ft(9)),
         occupancy=Occupancy.LIVING, floor_finish="rubber"),
]

SLABS = [
    Slab(uid="CBS501AAAA", tag="SL-B-FLOOR",
         outline=(pt(ft(0), ft(0)), pt(ft(36), ft(0)), pt(ft(36), ft(36)),
                  pt(ft(0), ft(36))),
         thickness=inch(3.5)),
]

FLOOR_OPENINGS = [
    # Shower recess is a finish-zone concern; the stair arrives via the slab above.
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *SLABS, *FLOOR_OPENINGS]
