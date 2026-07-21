# haus: editable
# Garage — freestanding 24'x24' ICF stem + 2x6 wood walls, 12' north of the house
# (west walls aligned). Wood walls sit on the ICF stem 22" above grade; the storey
# elevation is the top of the stem. Overhead door faces east (driveway side).
from typehaus import (
    Door,
    Node,
    Occupancy,
    Pitch,
    Roof,
    RoofForm,
    Room,
    StructuralRole,
    Wall,
    Window,
    face,
    from_node,
    ft,
    pt,
)

NODES = [
    Node(uid="CGN001AAAA", tag="N-G-SW", position=pt(ft(0), ft(48))),
    Node(uid="CGN002AAAA", tag="N-G-SE", position=pt(ft(24), ft(48))),
    Node(uid="CGN003AAAA", tag="N-G-NE", position=pt(ft(24), ft(72))),
    Node(uid="CGN004AAAA", tag="N-G-NW", position=pt(ft(0), ft(72))),
]

WALLS = [
    Wall(uid="CGW101AAAA", tag="W-G-S", start_node="N-G-SW", end_node="N-G-SE",
         assembly="GARAGE_WALL_2X6", alignment=face("zip-r-ext"), top=ft(8),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CGW102AAAA", tag="W-G-E", start_node="N-G-SE", end_node="N-G-NE",
         assembly="GARAGE_WALL_2X6", alignment=face("zip-r-ext"), top=ft(8),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CGW103AAAA", tag="W-G-N", start_node="N-G-NE", end_node="N-G-NW",
         assembly="GARAGE_WALL_2X6", alignment=face("zip-r-ext"), top=ft(8),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CGW104AAAA", tag="W-G-W", start_node="N-G-NW", end_node="N-G-SW",
         assembly="GARAGE_WALL_2X6", alignment=face("zip-r-ext"), top=ft(8),
         structural_role=StructuralRole.NONBEARING),
]

OPENINGS = [
    Door(uid="CGD201AAAA", tag="D-G-OVERHEAD", host="W-G-E",
         type_ref="DT-GARAGE192", position=from_node("N-G-SE", ft(4))),
    Door(uid="CGD202AAAA", tag="D-G-SERVICE", host="W-G-S", type_ref="DT-EXT36",
         position=from_node("N-G-SW", ft(5))),
    # Bearing gable wall: use the 27" RO/jack-stud module, centered on stud lines.
    # WT-2736, not WT-2760: the garage wall is only 8' (vs. the house's 10'), so the
    # 60"-tall type would push the header above the top plate at this sill height.
    Window(uid="CGX301AAAA", tag="WIN-G-N1", host="W-G-N", type_ref="WT-2736",
           position=from_node("N-G-NW", ft(6, 10.5)), sill_height=ft(3, 6)),
    Window(uid="CGX302AAAA", tag="WIN-G-N2", host="W-G-N", type_ref="WT-2736",
           position=from_node("N-G-NW", ft(14, 10.5)), sill_height=ft(3, 6)),
]

ROOMS = [
    Room(uid="CGR401AAAA", tag="RM-GARAGE", seed=pt(ft(12), ft(60)),
         occupancy=Occupancy.GARAGE, conditioned=False,
         floor_finish="sealed-concrete"),
]

# Gable roof, ridge E-W (rotated 90° vs the house), 16" overhangs.
ROOFS = [
    Roof(uid="CGRF01AAAA", tag="RF-GARAGE", form=RoofForm.GABLE,
         pitch=Pitch(4, 12), bearing_refs=("W-G-S", "W-G-N"),
         assembly="GARAGE_ROOF", overhang=ft(1, 4), ridge_direction="x"),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ROOFS]
