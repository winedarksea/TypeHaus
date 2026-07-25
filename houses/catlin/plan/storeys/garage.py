# haus: editable
# Garage — freestanding 24'x24' ICF stem + 2x6 wood walls, 12' north of the house
# (west walls aligned). Wood walls sit on the ICF stem 22" above grade; the storey
# elevation is the top of the stem. Overhead door faces east (driveway side).
from typehaus import (
    Door,
    EaveGutter,
    EaveTrim,
    FasciaBoard,
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
    inch,
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

# Gable roof, ridge E-W (rotated 90° vs the house), 16" overhangs. The gable ends are the
# E/W walls; they stay flat 8' walls rather than `top=ToRoof` because a raked wall top is a
# straight line between its two endpoints, so a gable wall must be split at the ridge — and
# the 16' overhead door is centered exactly on the ridge, so W-G-E cannot be split. Both
# gable triangles (and the raised-heel band on the eave walls) are instead closed by the
# wall→roof closure in resolve/roof_edge.py, which carries each wall's zip-r/rainscreen/
# cladding skin up to the roof underside and splits at the ridge itself.
# Eave + rake trim is two-layer: a 2x6 wood sub-fascia nailed to the truss tails and barge
# rafters (the structural nailer), lapped by a 5/4 cellular-PVC fascia (the weather face,
# which never rots at a drip edge). A vented PVC soffit closes the overhang underside and
# feeds the eave-to-ridge vent channel. Elevations are derived from the resolved roof plane,
# so the raised-heel lift carries the trim with it.
# The SOUTH eave gets a 5" aluminum gutter: that slope faces the 12' breezeway gap and the
# house wall across it, so its run-off is the only one that lands on somewhere people walk.
# The north eave sheds onto open ground and stays free-draining. The channel is declared
# here rather than authored in params/ for the same reason the fascia is — the raised-heel
# truss lifts the deck plane in the envelope stage, and an absolute elevation would drift off
# the eave it drains. Its top sits 1/2" below the plane so its back closes the fascia face
# and its bottom lands on the sub-fascia's underside.
_GARAGE_EAVE_TRIM = EaveTrim(
    fascia=(FasciaBoard(material="spf", thickness=inch(1.5), depth=inch(5.5)),
            FasciaBoard(material="pvc-cellular", thickness=inch(1), depth=inch(6))),
    soffit_material="pvc-cellular", soffit_thickness=inch(0.5), soffit_vented=True,
    gutter=EaveGutter(material="aluminum", depth=inch(5), thickness=inch(5),
                      top_drop=inch(0.5), edges=("south",),
                      slope="1/16 in/ft to the east downspout"),
)

ROOFS = [
    Roof(uid="CGRF01AAAA", tag="RF-GARAGE", form=RoofForm.GABLE,
         pitch=Pitch(4, 12), bearing_refs=("W-G-S", "W-G-N"),
         assembly="GARAGE_ROOF", overhang=ft(1, 4), ridge_direction="x",
         eave_trim=_GARAGE_EAVE_TRIM),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ROOFS]
