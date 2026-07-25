# haus: editable
# Second floor — CATLIN_EXT_2X4 on the same sheathing plane (#43 stack jog),
# three east bedrooms, west suite, plant room + study south, duct soffit (WP3.1).
from typehaus import (
    Alarm,
    AlarmKind,
    Door,
    DeckLayer,
    FloorOpening,
    FloorSystem,
    JoistSpec,
    Node,
    Occupancy,
    Room,
    RoughOpening,
    Soffit,
    Stair,
    StructuralRole,
    Wall,
    Window,
    face,
    from_node,
    ft,
    inch,
    pt,
)

NODES = [
    # Perimeter with partition tees
    Node(uid="CSN001AAAA", tag="N-S-SW", position=pt(ft(0), ft(0))),
    Node(uid="CSN002AAAA", tag="N-S-S1", position=pt(ft(18), ft(0))),
    Node(uid="CSN003AAAA", tag="N-S-SE", position=pt(ft(36), ft(0))),
    Node(uid="CSN004AAAA", tag="N-S-E1", position=pt(ft(36), ft(8, 8))),
    Node(uid="CSN005AAAA", tag="N-S-E2", position=pt(ft(36), ft(12))),
    Node(uid="CSN006AAAA", tag="N-S-E3", position=pt(ft(36), ft(20))),
    Node(uid="CSN007AAAA", tag="N-S-E4", position=pt(ft(36), ft(28))),
    Node(uid="CSN008AAAA", tag="N-S-NE", position=pt(ft(36), ft(36))),
    Node(uid="CSN009AAAA", tag="N-S-N1", position=pt(ft(18), ft(36))),
    Node(uid="CSN010AAAA", tag="N-S-N2", position=pt(ft(10), ft(36))),
    Node(uid="CSN011AAAA", tag="N-S-NW", position=pt(ft(0), ft(36))),
    Node(uid="CSN012AAAA", tag="N-S-W1", position=pt(ft(0), ft(26, 4))),
    Node(uid="CSN013AAAA", tag="N-S-W2", position=pt(ft(0), ft(13, 4))),
    Node(uid="CSN014AAAA", tag="N-S-W3", position=pt(ft(0), ft(8, 8))),
    # Center line ties
    Node(uid="CSN015AAAA", tag="N-S-C1", position=pt(ft(18), ft(8, 8))),
    Node(uid="CSN016AAAA", tag="N-S-C2", position=pt(ft(18), ft(13, 4))),
    Node(uid="CSN017AAAA", tag="N-S-C3", position=pt(ft(18), ft(26, 4))),
    # East bedroom block
    Node(uid="CSN018AAAA", tag="N-S-B1", position=pt(ft(22, 8), ft(8, 8))),
    Node(uid="CSN019AAAA", tag="N-S-B2", position=pt(ft(22, 8), ft(12))),
    Node(uid="CSN020AAAA", tag="N-S-B3", position=pt(ft(22, 8), ft(20))),
    Node(uid="CSN021AAAA", tag="N-S-B4", position=pt(ft(22, 8), ft(28))),
    Node(uid="CSN022AAAA", tag="N-S-B5", position=pt(ft(22, 8), ft(36))),
    # West block
    Node(uid="CSN023AAAA", tag="N-S-D1", position=pt(ft(8), ft(8, 8))),
    Node(uid="CSN024AAAA", tag="N-S-D2", position=pt(ft(8), ft(13, 4))),
    Node(uid="CSN025AAAA", tag="N-S-BA1", position=pt(ft(10), ft(26, 4))),
    Node(uid="CSN026AAAA", tag="N-S-STR2", position=pt(ft(10), ft(25))),
    Node(uid="CSN027AAAA", tag="N-S-C3B", position=pt(ft(18), ft(25))),
]

WALLS = [
    # --- exterior loop (2x4 storey of the #43 stack) ---------------------------
    Wall(uid="CSW101AAAA", tag="W-S-S1", start_node="N-S-SW", end_node="N-S-S1",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-S1"),
    Wall(uid="CSW102AAAA", tag="W-S-S2", start_node="N-S-S1", end_node="N-S-SE",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-S2"),
    Wall(uid="CSW103AAAA", tag="W-S-E1", start_node="N-S-SE", end_node="N-S-E1",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E1"),
    Wall(uid="CSW102BAAA", tag="W-S-E2", start_node="N-S-E1", end_node="N-S-E2",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E1"),
    Wall(uid="CSW104AAAA", tag="W-S-E3", start_node="N-S-E2", end_node="N-S-E3",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E2"),
    Wall(uid="CSW105AAAA", tag="W-S-E4", start_node="N-S-E3", end_node="N-S-E4",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E2"),
    Wall(uid="CSW106AAAA", tag="W-S-E5", start_node="N-S-E4", end_node="N-S-NE",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E2"),
    Wall(uid="CSW107AAAA", tag="W-S-N1", start_node="N-S-NE", end_node="N-S-B5",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N1"),
    Wall(uid="CSW135AAAA", tag="W-S-N1B", start_node="N-S-B5", end_node="N-S-N1",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N1"),
    Wall(uid="CSW108AAAA", tag="W-S-N2", start_node="N-S-N1", end_node="N-S-N2",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N2"),
    Wall(uid="CSW109AAAA", tag="W-S-N3", start_node="N-S-N2", end_node="N-S-NW",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N3"),
    Wall(uid="CSW110AAAA", tag="W-S-W1", start_node="N-S-NW", end_node="N-S-W1",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-W1"),
    Wall(uid="CSW111AAAA", tag="W-S-W2", start_node="N-S-W1", end_node="N-S-W2",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-W3"),
    Wall(uid="CSW112AAAA", tag="W-S-W3", start_node="N-S-W2", end_node="N-S-W3",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-W4"),
    Wall(uid="CSW113AAAA", tag="W-S-W4", start_node="N-S-W3", end_node="N-S-SW",
         assembly="CATLIN_EXT_2X4", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-W4"),
    # --- center bearing wall (2x6 carries the attic floor) ---------------------
    Wall(uid="CSW114AAAA", tag="W-S-C1", start_node="N-S-S1", end_node="N-S-C1",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C1"),
    Wall(uid="CSW115AAAA", tag="W-S-C2", start_node="N-S-C1", end_node="N-S-C2",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C2"),
    Wall(uid="CSW116AAAA", tag="W-S-C3", start_node="N-S-C2", end_node="N-S-C3B",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C3"),
    Wall(uid="CSW136AAAA", tag="W-S-C3C", start_node="N-S-C3B", end_node="N-S-C3",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C4B"),
    Wall(uid="CSW117AAAA", tag="W-S-C4", start_node="N-S-C3", end_node="N-S-N1",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C5"),
    # --- south band: plant room | study2 ---------------------------------------
    Wall(uid="CSW118AAAA", tag="W-S-PS1", start_node="N-S-W3", end_node="N-S-D1",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW119AAAA", tag="W-S-PS2", start_node="N-S-D1", end_node="N-S-C1",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW120AAAA", tag="W-S-SS1", start_node="N-S-C1", end_node="N-S-B1",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW121AAAA", tag="W-S-SS2", start_node="N-S-B1", end_node="N-S-E1",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- east bedroom block ------------------------------------------------------
    Wall(uid="CSW122AAAA", tag="W-S-BW1", start_node="N-S-B1", end_node="N-S-B2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW123AAAA", tag="W-S-BW2", start_node="N-S-B2", end_node="N-S-B3",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW124AAAA", tag="W-S-BW3", start_node="N-S-B3", end_node="N-S-B4",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW125AAAA", tag="W-S-BW4", start_node="N-S-B4", end_node="N-S-B5",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW126AAAA", tag="W-S-BD1", start_node="N-S-B2", end_node="N-S-E2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW127AAAA", tag="W-S-BD2", start_node="N-S-B3", end_node="N-S-E3",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW128AAAA", tag="W-S-BD3", start_node="N-S-B4", end_node="N-S-E4",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- west block: dressing corridor, suite, ensuite --------------------------
    Wall(uid="CSW129AAAA", tag="W-S-DC1", start_node="N-S-D1", end_node="N-S-D2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW130AAAA", tag="W-S-BD-S", start_node="N-S-W2", end_node="N-S-D2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW131AAAA", tag="W-S-BD-S2", start_node="N-S-D2", end_node="N-S-C2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW132AAAA", tag="W-S-BD-N", start_node="N-S-W1", end_node="N-S-BA1",
         assembly="INT_2X6_PLUMBING", top=ft(9)),
    Wall(uid="CSW133AAAA", tag="W-S-BD-N2", start_node="N-S-STR2", end_node="N-S-C3B",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW134AAAA", tag="W-S-BA-E", start_node="N-S-N2", end_node="N-S-BA1",
         assembly="INT_2X6_PLUMBING", top=ft(9)),
    Wall(uid="CSW137AAAA", tag="W-S-BA-E2", start_node="N-S-BA1", end_node="N-S-STR2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
]

OPENINGS = [
    # Bedroom doors from the hallway
    Door(uid="CSD201AAAA", tag="D-S-BED1", host="W-S-BW1", type_ref="DT-INT30",
         position=from_node("N-S-B2", ft(0, 4)), flip_swing=True),
    Door(uid="CSD202AAAA", tag="D-S-BED2", host="W-S-BW3", type_ref="DT-INT30",
         position=from_node("N-S-B3", ft(0, 6))),
    Door(uid="CSD203AAAA", tag="D-S-BED3", host="W-S-BW4", type_ref="DT-INT30",
         position=from_node("N-S-B4", ft(0, 6))),
    Door(uid="CSD204AAAA", tag="D-S-STUDY2", host="W-S-SS1", type_ref="DT-INT30",
         position=from_node("N-S-C1", ft(1))),
    Door(uid="CSD206AAAA", tag="D-S-SUITE", host="W-S-BD-S2", type_ref="DT-INT32",
         position=from_node("N-S-D2", ft(1))),
    Door(uid="CSD207AAAA", tag="D-S-CLOS", host="W-S-DC1", type_ref="DT-INT30",
         position=from_node("N-S-D1", ft(1))),
    Door(uid="CSD208AAAA", tag="D-S-ENSUITE", host="W-S-BD-N", type_ref="DT-INT30",
         position=from_node("N-S-W1", ft(5))),
    # Open stair head onto the hallway (cased, no door).
    RoughOpening(uid="CSD209AAAA", tag="O-S-STAIRTOP", host="W-S-BD-N2",
                 position=from_node("N-S-STR2", ft(0, 6)), width=ft(6),
                 height=ft(6, 8)),
    # Deck doors (south wall, flanking the center line) — French (double-swing) leaves.
    Door(uid="CSD210AAAA", tag="D-S-DECK-W", host="W-S-S1", type_ref="DT-FRENCH36",
         position=from_node("N-S-S1", ft(2))),
    Door(uid="CSD211AAAA", tag="D-S-DECK-E", host="W-S-S2", type_ref="DT-FRENCH36",
         position=from_node("N-S-S1", ft(2))),
    # Windows — east bedrooms (bearing wall: WT-2736, egress-capable)
    Window(uid="CSX301AAAA", tag="WIN-S-BED1", host="W-S-E3", type_ref="WT-2736",
           position=from_node("N-S-E2", ft(2, 10.5)), sill_height=ft(3)),
    Window(uid="CSX302AAAA", tag="WIN-S-BED2", host="W-S-E4", type_ref="WT-2736",
           position=from_node("N-S-E3", ft(2, 10.5)), sill_height=ft(3)),
    Window(uid="CSX303AAAA", tag="WIN-S-BED3", host="W-S-E5", type_ref="WT-2736",
           position=from_node("N-S-E4", ft(2, 10.5)), sill_height=ft(3)),
    # West suite (bearing wall)
    Window(uid="CSX304AAAA", tag="WIN-S-SUITE1", host="W-S-W2", type_ref="WT-2736",
           position=from_node("N-S-W1", ft(4, 2.5)), sill_height=ft(3)),
    Window(uid="CSX305AAAA", tag="WIN-S-SUITE2", host="W-S-W2", type_ref="WT-2736",
           position=from_node("N-S-W1", ft(8, 2.5)), sill_height=ft(3)),
    # Plant room — south glazing (non-bearing: WT-3036 row)
    Window(uid="CSX306AAAA", tag="WIN-S-PLANT1", host="W-S-S1", type_ref="WT-3036",
           position=from_node("N-S-SW", ft(2, 9)), sill_height=ft(2)),
    Window(uid="CSX307AAAA", tag="WIN-S-PLANT2", host="W-S-S1", type_ref="WT-3036",
           position=from_node("N-S-SW", ft(6, 9)), sill_height=ft(2)),
    # The plant room's west window is on W-S-W4, a bearing wall, so it takes the 27" bearing
    # type and not the 30" south-glazing one — "resize windows to fit the grid" (CLAUDE.md).
    Window(uid="CSX308AAAA", tag="WIN-S-PLANT3", host="W-S-W4", type_ref="WT-2736",
           position=from_node("N-S-W3", ft(4, 2.5)), sill_height=ft(2)),
    Window(uid="CSX309AAAA", tag="WIN-S-STUDY1", host="W-S-S2", type_ref="WT-3036",
           position=from_node("N-S-SE", ft(4, 9)), sill_height=ft(2, 6)),
    Window(uid="CSX310AAAA", tag="WIN-S-STUDY2", host="W-S-S2", type_ref="WT-3036",
           position=from_node("N-S-SE", ft(8, 9)), sill_height=ft(2, 6)),
    # Baths + north
    # W-S-N3 shortened by 1' when N-S-N2 moved to the stair shaft's new line, which moved
    # every 16" bay centre on it by 4"; the RO follows so it still fits one clear bay.
    Window(uid="CSX311AAAA", tag="WIN-S-BATH-N", host="W-S-N3", type_ref="WT-1424",
           position=from_node("N-S-NW", ft(4, 9)), sill_height=ft(4)),
    Window(uid="CSX312AAAA", tag="WIN-S-BATH-W", host="W-S-W1", type_ref="WT-1424",
           position=from_node("N-S-NW", ft(4, 1)), sill_height=ft(4)),
    Window(uid="CSX313AAAA", tag="WIN-S-HALL-N", host="W-S-N1", type_ref="WT-3036",
           position=from_node("N-S-NE", ft(6, 9)), sill_height=ft(3)),
]

ROOMS = [
    Room(uid="CSR401AAAA", tag="RM-S-PLANT", seed=pt(ft(9), ft(4)),
         occupancy=Occupancy.LIVING, floor_finish="tile"),
    Room(uid="CSR402AAAA", tag="RM-S-STUDY2", seed=pt(ft(27), ft(4)),
         occupancy=Occupancy.OFFICE, floor_finish="oak"),
    Room(uid="CSR403AAAA", tag="RM-S-BED1", seed=pt(ft(29), ft(16)),
         occupancy=Occupancy.BEDROOM, floor_finish="carpet"),
    Room(uid="CSR404AAAA", tag="RM-S-BED2", seed=pt(ft(29), ft(24)),
         occupancy=Occupancy.BEDROOM, floor_finish="carpet"),
    Room(uid="CSR405AAAA", tag="RM-S-BED3", seed=pt(ft(29), ft(32)),
         occupancy=Occupancy.BEDROOM, floor_finish="carpet"),
    Room(uid="CSR406AAAA", tag="RM-S-SUITE", seed=pt(ft(9), ft(20)),
         occupancy=Occupancy.BEDROOM, floor_finish="carpet"),
    Room(uid="CSR407AAAA", tag="RM-S-CLOSET", seed=pt(ft(4), ft(11)),
         occupancy=Occupancy.STORAGE, floor_finish="carpet"),
    Room(uid="CSR411AAAA", tag="RM-S-DRESS", seed=pt(ft(13), ft(11)),
         occupancy=Occupancy.HALLWAY, floor_finish="carpet"),
    Room(uid="CSR408AAAA", tag="RM-S-ENSUITE", seed=pt(ft(5), ft(31)),
         occupancy=Occupancy.BATHROOM, floor_finish="tile"),
    Room(uid="CSR409AAAA", tag="RM-S-HALL", seed=pt(ft(20), ft(20)),
         occupancy=Occupancy.HALLWAY, floor_finish="oak"),
    Room(uid="CSR410AAAA", tag="RM-S-STAIR", seed=pt(ft(14, 6), ft(31)),
         occupancy=Occupancy.STAIR, floor_finish="oak"),
]

ALARMS = [
    Alarm(uid="CSA701AAAA", tag="AL-S-BED1", kind=AlarmKind.COMBO, room="RM-S-BED1"),
    Alarm(uid="CSA702AAAA", tag="AL-S-BED2", kind=AlarmKind.COMBO, room="RM-S-BED2"),
    Alarm(uid="CSA703AAAA", tag="AL-S-BED3", kind=AlarmKind.COMBO, room="RM-S-BED3"),
    Alarm(uid="CSA704AAAA", tag="AL-S-SUITE", kind=AlarmKind.COMBO, room="RM-S-SUITE"),
    Alarm(uid="CSA705AAAA", tag="AL-S-HALL", kind=AlarmKind.COMBO, room="RM-S-HALL"),
]

# The hallway duct soffit (HRV + heat mains) — dashed on plan, framed in 3D.
SOFFITS = [
    Soffit(uid="CSF601AAAA", tag="SF-S-DUCT",
           outline=(pt(ft(19, 4), ft(8, 8)), pt(ft(20, 8), ft(8, 8)),
                    pt(ft(20, 8), ft(36)), pt(ft(19, 4), ft(36))),
           drop=inch(14)),
]

# Drawn to the main floor's *finished* well, the way FO-M-STAIR is drawn to the basement's:
# W-M-STRW's and W-M-C5's stair-side gwb faces, W-M-STRS's north face, and the exterior
# wall's inside face. That is both the shaft the flight climbs and the line the outer
# stringers bear on — an opening on the wall centrelines instead put the stringers inside
# the stud cavities and left the flight to be posted down (plans/TODO.md D3).
#
# This well is 7'-5 1/4" where the basement's is 7'-0", because the 2x6 walls here are
# thinner than the 12" concrete they stack on. Each flight is sized to its own storey's
# well rather than forcing one width on both, so both outer stringers land on a wall.
FLOOR_OPENINGS = [
    FloorOpening(uid="CSF602AAAA", tag="FO-S-STAIR",
                 outline=(pt(ft(10, 3.375), ft(25, 2.375)),
                          pt(ft(17, 8.625), ft(25, 2.375)),
                          pt(ft(17, 8.625), ft(35, 5.375)),
                          pt(ft(10, 3.375), ft(35, 5.375))),
                 # Both long edges are carried by bearing wall, so neither needs a header:
                 # W-M-STRW/STRW2 west, W-M-C5/C4B (the center bearing line) east.
                 bearing_refs=("W-M-STRW", "W-M-STRW2", "W-M-C5", "W-M-C4B")),
]

# Structural deck: 11-7/8" I-joists spanning E-W on the three bearing lines.
FLOOR = [
    FloorSystem(uid="CSF603AAAA", tag="FS-SECOND",
                joists=JoistSpec(member="11.875 I-joist", spacing=inch(16),
                                 direction="x",
                                 bearing_refs=("W-M-W2", "W-M-C2", "W-M-E1")),
                subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=inch(0.75)),
                openings=("FO-S-STAIR",)),
]

STAIRS = [
    # 7'-5 1/4" well = 3'-6 3/8" + 4 1/2" well partition + 3'-6 3/8". Landing is the
    # R311.7.6 36" minimum, floored at the flight width to keep the U-turn walkable.
    Stair(uid="CST702AAAA", tag="ST-M2S", floor_opening="FO-S-STAIR",
          from_storey="main", to_storey="second", width=ft(3, 6.375),
          layout="u_split_landing", run_direction="y",
          start=pt(ft(10, 3.375), ft(25, 2.375)), landing_depth=ft(3)),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *SOFFITS, *FLOOR_OPENINGS, *FLOOR,
            *STAIRS]
