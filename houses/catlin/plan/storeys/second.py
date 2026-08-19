# haus: editable
# Second floor — CATLIN_EXT_2X6 on the same sheathing plane (2x6 on every framed
# storey), three east bedrooms, west suite, plant room + study south, duct soffit (WP3.1).
#
# Every interior partition is set to the Sensopia survey `catlin_floorplan/Colin House -
# 2nd Floor.svg` (path #0, 74.7029 px/m, rounded to the nearest inch). Fidelity policy:
# interior partitions move to the source; exterior envelope, x=18' bearing line and the
# 16" framing module do not. `preferences.toml`'s `[[underlay]]` is calibrated to the same
# polygon so `haus render --view plan` overlays the survey for comparison.
#
# Known, deliberate divergences from the source:
# - The centre line's big break (y=22'-4"..30'-10", 2026-07-28) carries no wall at all —
#   just BM-S-HALL, three plies of 11-7/8" LVL, still a continuous bearing stack. The
#   source's single 181.02 sf "Hallway" now reads as RM-S-HALL, including the old landing
#   and open stair well (RL-S-STAIR guards the well's east edge). Suite/plant-room breaks
#   are modelled as openings in the wall (D-S-SUITE, D-S-PLANT), per main.py's O-M-HALL.
# - Source bearing-wall windows are 2'-8"; `preferences.toml` caps a bearing RO at 30"
#   (raised from 27" on 2026-08-01 for WIN-S-BED1/BED2), 42" non-bearing. Existing window
#   types are kept; only positions move onto the source openings.
# - `WIN-S-BATH-W`/`WIN-S-BATH-N` have no source counterpart — kept for bathroom daylight.
# - `RM-S-BATH1` is the hall bath; the suite's own bath is RM-S-SUITEBATH. Renamed from
#   `RM-S-ENSUITE` (2026-07-27, which it never was) across fixtures/mep/views/lighting/electrical.
from typehaus import (
    Alarm,
    AlarmKind,
    Beam,
    ControlLayer,
    Door,
    DeckLayer,
    FloorHeat,
    FloorOpening,
    FloorSystem,
    FramingSpec,
    HumidityClass,
    JoistSpec,
    Layer,
    LayerFunction,
    Node,
    Occupancy,
    RadiantSystem,
    Railing,
    RailingKind,
    Post,
    Room,
    RoughOpening,
    Soffit,
    Stair,
    StructuralRole,
    Wall,
    WallLiningException,
    Window,
    face,
    from_node,
    ft,
    in_slab,
    inch,
    pt,
)

NODES = [
    # Perimeter with partition tees
    Node(uid="CSN001AAAA", tag="N-S-SW", position=pt(ft(0), ft(0))),
    Node(uid="CSN002AAAA", tag="N-S-S1", position=pt(ft(18), ft(0))),
    Node(uid="CSN003AAAA", tag="N-S-SE", position=pt(ft(36), ft(0))),
    # The three east bedrooms started as equal 9'-0" bays (source 9.035/17.991/26.947).
    # N-S-E2/E3 moved 4" south (18'-0"->17'-8", 27'-0"->26'-8", 2026-08-15 facade pass) so
    # W-S-E3/E4's stud grids (a wall lays studs from its own start node) let the four east
    # windows mirror about y=18'-0" on stud lines. BED1 shrinks 4" (its 0.05 sf R303.1
    # margin allows it); BED3 grows 4" (it has two windows).
    Node(uid="CSN004AAAA", tag="N-S-E1", position=pt(ft(36), ft(9))),
    Node(uid="CSN005AAAA", tag="N-S-E2", position=pt(ft(36), ft(17, 8))),
    Node(uid="CSN006AAAA", tag="N-S-E3", position=pt(ft(36), ft(26, 8))),
    Node(uid="CSN008AAAA", tag="N-S-NE", position=pt(ft(36), ft(36))),
    Node(uid="CSN009AAAA", tag="N-S-N1", position=pt(ft(18), ft(36))),
    Node(uid="CSN010AAAA", tag="N-S-N2", position=pt(ft(10), ft(36))),
    Node(uid="CSN011AAAA", tag="N-S-NW", position=pt(ft(0), ft(36))),
    Node(uid="CSN012AAAA", tag="N-S-W1", position=pt(ft(0), ft(26, 4))),
    Node(uid="CSN013AAAA", tag="N-S-W2", position=pt(ft(0), ft(22, 4))),
    Node(uid="CSN014AAAA", tag="N-S-W3", position=pt(ft(0), ft(9))),
    # Center line ties
    Node(uid="CSN015AAAA", tag="N-S-C1", position=pt(ft(18), ft(9))),
    Node(uid="CSN016AAAA", tag="N-S-C2", position=pt(ft(18), ft(12, 5))),
    Node(uid="CSN028AAAA", tag="N-S-C2B", position=pt(ft(18), ft(15, 11))),
    Node(uid="CSN029AAAA", tag="N-S-C2C", position=pt(ft(18), ft(22, 4))),
    # N-S-C3B (18', 25'-0") retired 2026-07-28 with W-S-BD-N2: the stair's south wall is
    # gone, so nothing ties to it.
    # N-S-C3 (18', 26'-4") retired 2026-07-28 with W-S-C3C/W-S-C4: it only ever split
    # the two wall segments the BM-S-HALL opening replaced, and no element ties to it.
    Node(uid="CSN030AAAA", tag="N-S-C3D", position=pt(ft(18), ft(30, 10))),
    # East bedroom block — the hall/bedroom partition is x=21'-11" (source 21.894/21.898)
    Node(uid="CSN018AAAA", tag="N-S-B1", position=pt(ft(21, 11), ft(9))),
    Node(uid="CSN019AAAA", tag="N-S-B2", position=pt(ft(21, 11), ft(17, 8))),
    Node(uid="CSN020AAAA", tag="N-S-B3", position=pt(ft(21, 11), ft(26, 8))),
    Node(uid="CSN021AAAA", tag="N-S-B4", position=pt(ft(21, 11), ft(30, 10))),
    Node(uid="CSN022AAAA", tag="N-S-B5", position=pt(ft(21, 11), ft(36))),
    # West block: suite / walk-in / suite bath partition at x=9'-7 1/2" (source 9.616)
    Node(uid="CSN023AAAA", tag="N-S-D1", position=pt(ft(9, 7.5), ft(9))),
    Node(uid="CSN024AAAA", tag="N-S-D2", position=pt(ft(9, 7.5), ft(12, 5))),
    Node(uid="CSN031AAAA", tag="N-S-D3", position=pt(ft(9, 7.5), ft(15, 11))),
    Node(uid="CSN032AAAA", tag="N-S-D4", position=pt(ft(9, 7.5), ft(22, 4))),
    # Vanity alcove (source 5.873 / 26.374)
    Node(uid="CSN033AAAA", tag="N-S-V1", position=pt(ft(5, 10.5), ft(22, 4))),
    Node(uid="CSN034AAAA", tag="N-S-V2", position=pt(ft(5, 10.5), ft(26, 4))),
    # Stair shaft west line
    Node(uid="CSN025AAAA", tag="N-S-BA1", position=pt(ft(10), ft(26, 4))),
    # Plain flush split on the east wall (2026-07-28): used to be the mechanical chase's SE
    # corner (N-S-CH3); kept as its own node so W-S-BA-E1B's wall_ref in fixtures.py (the
    # hall-bath lav) doesn't move now that the chase itself has moved to the NW corner.
    Node(uid="CSN038AAAA", tag="N-S-BA-SPLIT", position=pt(ft(10), ft(33, 4))),
    # The mechanical chase moved NE -> NW corner of the hall bath (2026-07-28) to stack on
    # RM-M-MECH below. N-S-CH1 is its inner (SE) corner; N-S-CH2/CH3 tee into the exterior
    # north/west walls.
    Node(uid="CSN035AAAA", tag="N-S-CH1", position=pt(ft(2, 9), ft(33, 4))),
    Node(uid="CSN036AAAA", tag="N-S-CH2", position=pt(ft(2, 9), ft(36))),
    Node(uid="CSN037AAAA", tag="N-S-CH3", position=pt(ft(0), ft(33, 4))),
]

WALLS = [
    # --- exterior loop (2x6, same stack as main) -------------------------------
    # The plant room's two exterior walls carry PLANT_EXT_2X6_HUMID, not CATLIN_EXT_2X6:
    # same stack outboard of the sheathing, a sealed PVC/membrane liner inboard of the
    # studs (plan/assemblies.py, notes/plant_room.md). `alignment=face("sheathing-ext")` is
    # unchanged on purpose — the sheathing datum does not move (decision #43) and the liner
    # grows into the room, exactly as W-B-CS does for the sauna. `interior_room` is what
    # names which face the liner lands on; without it an asymmetric wall would take the
    # component's outward sign and could line the wrong side.
    Wall(uid="CSW101AAAA", tag="W-S-S1", start_node="N-S-SW", end_node="N-S-S1",
         assembly="PLANT_EXT_2X6_HUMID", alignment=face("sheathing-ext"), top=ft(9),
         interior_room="RM-S-PLANT",
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-S1"),
    Wall(uid="CSW102AAAA", tag="W-S-S2", start_node="N-S-S1", end_node="N-S-SE",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-S2"),
    Wall(uid="CSW103AAAA", tag="W-S-E1", start_node="N-S-SE", end_node="N-S-E1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E1"),
    Wall(uid="CSW102BAAA", tag="W-S-E2", start_node="N-S-E1", end_node="N-S-E2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E1"),
    Wall(uid="CSW104AAAA", tag="W-S-E3", start_node="N-S-E2", end_node="N-S-E3",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E2"),
    Wall(uid="CSW105AAAA", tag="W-S-E4", start_node="N-S-E3", end_node="N-S-NE",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E2"),
    Wall(uid="CSW107AAAA", tag="W-S-N1", start_node="N-S-NE", end_node="N-S-B5",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N1"),
    Wall(uid="CSW135AAAA", tag="W-S-N1B", start_node="N-S-B5", end_node="N-S-N1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N1"),
    Wall(uid="CSW108AAAA", tag="W-S-N2", start_node="N-S-N1", end_node="N-S-N2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N2"),
    # Split at N-S-CH2, where the mechanical chase's east wall tees into the north wall
    # (moved to the NW corner 2026-07-28 — see the node comment above).
    Wall(uid="CSW109AAAA", tag="W-S-N3", start_node="N-S-N2", end_node="N-S-CH2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N3"),
    Wall(uid="CSW153AAAA", tag="W-S-N3B", start_node="N-S-CH2", end_node="N-S-NW",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N3B"),
    # Split at N-S-CH3, where the chase's south wall tees into the west wall
    # (2026-07-28).
    Wall(uid="CSW154AAAA", tag="W-S-W1B", start_node="N-S-NW", end_node="N-S-CH3",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-W1B"),
    Wall(uid="CSW110AAAA", tag="W-S-W1", start_node="N-S-CH3", end_node="N-S-W1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-W1"),
    Wall(uid="CSW111AAAA", tag="W-S-W2", start_node="N-S-W1", end_node="N-S-W2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-W2"),
    Wall(uid="CSW112AAAA", tag="W-S-W3", start_node="N-S-W2", end_node="N-S-W3",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-W3"),
    Wall(uid="CSW113AAAA", tag="W-S-W4", start_node="N-S-W3", end_node="N-S-SW",
         assembly="PLANT_EXT_2X6_HUMID", alignment=face("sheathing-ext"), top=ft(9),
         interior_room="RM-S-PLANT",
         structural_role=StructuralRole.BEARING, stacks_on="W-M-W4"),
    # --- center bearing wall (2x6 carries the attic floor) ---------------------
    # Continuous from gable to gable — the attic's structural ridge bears on the stack this
    # line belongs to. The three source breaks are doors/cased openings, not gaps.
    # The plant room's east boundary. Same 2x6 bearing line as the rest of W-S-C*, with the
    # humid liner on the plant-room face and painted gypsum on RM-S-STUDY2's — the sauna's
    # asymmetry one storey up.
    # `alignment` keeps the 2x6 STUDS centred on the x=18' grid, exactly as W-B-CS keeps
    # the sauna's concrete centred (`face("concrete-ext", offset=inch(-6))`, basement.py):
    # 2.75" back off the stud's outboard face is its centreline. Without it the wall centres
    # on its own new total and the whole bearing line — which W-M-C1 stacks under and the
    # attic ridge stacks over — slides 5/16" east, taking RM-S-STUDY2's face and two of its
    # receptacles with it. The liner is what grows; the grid does not move.
    Wall(uid="CSW114AAAA", tag="W-S-C1", start_node="N-S-S1", end_node="N-S-C1",
         assembly="PLANT_INT_2X6_BRG_HUMID", top=ft(9), interior_room="RM-S-PLANT",
         alignment=face("stud-ext", offset=inch(-2.75)),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C1"),
    Wall(uid="CSW115AAAA", tag="W-S-C2", start_node="N-S-C1", end_node="N-S-C2",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C1"),
    Wall(uid="CSW138AAAA", tag="W-S-C2B", start_node="N-S-C2", end_node="N-S-C2B",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C2"),
    Wall(uid="CSW139AAAA", tag="W-S-C2C", start_node="N-S-C2B", end_node="N-S-C2C",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C3"),
    # y 22'-4" .. 30'-10" IS NOT A WALL — it is the BM-S-HALL flitch of LVL below.
    # W-S-C3 / W-S-C3C / W-S-C4 used to stand here; the whole 8'-6" is now open so the
    # hall, the landing and the stair well read as one room (2026-07-28). The bearing
    # stack is unbroken because the beam is *in* it: see BEAMS below.
    Wall(uid="CSW140AAAA", tag="W-S-C4B", start_node="N-S-C3D", end_node="N-S-N1",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C5"),
    # --- south band north wall, y=9'-0" (source 9.035): plant room | study2 ------
    # These two are the plant room's north side, so they leave INT_2X4_PARTITION for
    # PLANT_INT_2X4_HUMID: the room's membrane has to be continuous on all six surfaces or
    # it is not a barrier at all, and a partition is the easiest place to forget that.
    # Same alignment idiom as W-S-C1 above, half a 2x4 instead of half a 2x6: the studs stay
    # on the survey's y=9'-0" line and the liner grows south into the plant room, so
    # RM-S-STUDY2 keeps its face and its dimensions.
    Wall(uid="CSW118AAAA", tag="W-S-PS1", start_node="N-S-W3", end_node="N-S-D1",
         assembly="PLANT_INT_2X4_HUMID", top=ft(9), interior_room="RM-S-PLANT",
         alignment=face("stud-ext", offset=inch(-1.75))),
    Wall(uid="CSW119AAAA", tag="W-S-PS2", start_node="N-S-D1", end_node="N-S-C1",
         assembly="PLANT_INT_2X4_HUMID", top=ft(9), interior_room="RM-S-PLANT",
         alignment=face("stud-ext", offset=inch(-1.75))),
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
    # North-centre closet (source 30.853 / 21.898), off the hall's north end.
    Wall(uid="CSW141AAAA", tag="W-S-CLN-S", start_node="N-S-C3D", end_node="N-S-B4",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- west block: walk-in, suite, suite bath, vanity alcove ------------------
    Wall(uid="CSW129AAAA", tag="W-S-DC1", start_node="N-S-D1", end_node="N-S-D2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    # RM-S-SUITEBATH's west + south walls carry its drain stack, so both are the
    # staggered wet-wall assembly (2x4 studs on 2x6 plates, 5.5" continuous cavity):
    # `advisory.wet_wall_depth` reads preferences.toml's
    # `drain_stack_required_structure_in = 5.5`, which a 2x4 partition cannot hold.
    Wall(uid="CSW142AAAA", tag="W-S-DC2", start_node="N-S-D3", end_node="N-S-D4",
         assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(9)),
    Wall(uid="CSW143AAAA", tag="W-S-CLN", start_node="N-S-D2", end_node="N-S-C2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW144AAAA", tag="W-S-SBS", start_node="N-S-D3", end_node="N-S-C2B",
         assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(9)),
    Wall(uid="CSW145AAAA", tag="W-S-SN1", start_node="N-S-W2", end_node="N-S-V1",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW146AAAA", tag="W-S-SN2", start_node="N-S-V1", end_node="N-S-D4",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW147AAAA", tag="W-S-SN3", start_node="N-S-D4", end_node="N-S-C2C",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW148AAAA", tag="W-S-VE", start_node="N-S-V1", end_node="N-S-V2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW132AAAA", tag="W-S-BD-N", start_node="N-S-W1", end_node="N-S-V2",
         assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(9)),
    Wall(uid="CSW149AAAA", tag="W-S-BD-N1B", start_node="N-S-V2", end_node="N-S-BA1",
         assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(9)),
    # W-S-BD-N2 (the stair's south wall on y=25', with the 6'-0" O-S-STAIRTOP through it)
    # came out on 2026-07-28 with the centre line: a wall pierced by a 6' hole between two
    # halves of what is now one room was doing nothing but hiding the stair. The well head
    # is guarded by RL-S-STAIRHEAD instead, which stops at the flight's own throat.
    Wall(uid="CSW134AAAA", tag="W-S-BA-E", start_node="N-S-N2", end_node="N-S-BA-SPLIT",
         assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(9)),
    Wall(uid="CSW150AAAA", tag="W-S-BA-E1B", start_node="N-S-BA-SPLIT", end_node="N-S-BA1",
         assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(9)),
    # W-S-BA-E2 (N-S-BA1 to the stair shaft's freed N-S-STR2 corner) came out with this
    # edit: since W-S-BD-N2 came out it was a stub dead-ending on an open node, poking into
    # the hallway with nothing on its far end to tie into.
    # 2'x2' mechanical chase, moved to the hall bath's NW corner (2026-07-28, was the NE
    # corner) so it stacks on RM-M-MECH below and the attic exit above. This is what makes
    # RM-S-BATH1 the source's L-shaped 80.73 sf bathroom, now notched NW instead of NE.
    Wall(uid="CSW151AAAA", tag="W-S-CH-W", start_node="N-S-CH1", end_node="N-S-CH2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW152AAAA", tag="W-S-CH-S", start_node="N-S-CH1", end_node="N-S-CH3",
         assembly="INT_2X4_PARTITION", top=ft(9)),
]

# Openings are placed on the gaps measured in the source wall polygon. `from_node` offsets
# are to the opening's near *edge* (resolve/pipeline.py:195), not its centre, so each
# comment below records the resulting centre.
OPENINGS = [
    # Bedroom doors — on the hall/bedroom partition, not on the cross walls. The source
    # puts three 2'-7 1/2" gaps at y 15'-2", 24'-1", 28'-11"; hosting them on the cross
    # walls (as the port did) put D-S-BED1's centre at (22.67, 10.42), inside the attic
    # stair band rather than inside RM-S-BED1.
    Door(uid="CSD201AAAA", tag="D-S-BED1", host="W-S-BW1", type_ref="DT-INT-SWING30",
         position=from_node("N-S-B1", ft(4, 11)), flip_swing=True),          # y 15'-2"
    Door(uid="CSD202AAAA", tag="D-S-BED2", host="W-S-BW2", type_ref="DT-INT-SWING30",
         position=from_node("N-S-B2", ft(4, 10))),                       # y 24'-1"
    Door(uid="CSD203AAAA", tag="D-S-BED3", host="W-S-BW3", type_ref="DT-INT-SWING30",
         position=from_node("N-S-B3", ft(0, 8))),                        # y 28'-11"
    # Just an opening, framed the same as a 30" door: no leaf needed for this passthrough.
    RoughOpening(uid="CSD204AAAA", tag="D-S-STUDY2", host="W-S-SS1",
                 position=from_node("N-S-C1", ft(1, 0.625)), width=ft(2, 6),
                 height=ft(6, 8)),                                       # x 20'-3 5/8"
    # Three doors through the centre bearing line, on the source's own gaps. Each takes a
    # header exactly like O-M-HALL / O-M-DRESS one storey down; the wall itself is unbroken.
    # Full-lite glass leaf admits daylight from the south-facing plant room into
    # RM-S-STUDY2 — this door opens on the study, not the hall (corrected 2026-08-18).
    Door(uid="CSD212AAAA", tag="D-S-PLANT", host="W-S-C1", type_ref="DT-INT-SWING30-GLAZED",
         position=from_node("N-S-S1", ft(3, 2.5))),                      # y 4'-5 1/2"
    Door(uid="CSD206AAAA", tag="D-S-SUITE", host="W-S-C2B", type_ref="DT-INT-SWING32",
         position=from_node("N-S-C2", ft(0, 4.875))),                    # y 14'-1 7/8"
    # O-S-HALLW (a 3'-0" cased opening at y 28'-7") is gone: the whole 8'-6" between
    # N-S-C2C and N-S-C3D is open under BM-S-HALL now, so there is no wall left to host it.
    # West block
    # Bifold closet door, DT-INT-BIFOLD56 (4'-8"), replacing the former bare RoughOpening.
    Door(uid="CSD213AAAA", tag="O-S-CLOSET", host="W-S-CLN", type_ref="DT-INT-BIFOLD56",
         position=from_node("N-S-D2", ft(1, 10))),                       # x 13'-9"
    # The source's gap starts hard against the corner at x=9'-10 11/16"; ours starts 3"
    # further east so the leaf's king stud clears W-S-DC2's corner pack instead of
    # pinwheeling through it (test_wall_corner_and_opening_framing).
    Door(uid="CSD214AAAA", tag="D-S-SUITEBATH", host="W-S-SBS", type_ref="DT-INT-SWING30",
         position=from_node("N-S-D3", ft(0, 6.5)), flip_hinge=True),                      # x 11'-5"
    RoughOpening(uid="CSD215AAAA", tag="O-S-VANITY", host="W-S-VE",
                 position=from_node("N-S-V1", ft(0, 3)), width=ft(2, 8),
                 height=ft(6, 8)),                                       # y 23'-11"
    # Pulled 3" west of its original 1'-4.5" (2026-07-29): at that offset the door's own
    # king stud landed inside N-S-BA1's corner square and punched into W-S-BA-E1B's end
    # stud (the same class of overlap as N-M-MECH2 in test_wall_corner_and_opening_framing).
    Door(uid="CSD208AAAA", tag="D-S-BATH1", host="W-S-BD-N1B", type_ref="DT-INT-SWING30",
         position=from_node("N-S-V2", ft(1, 1.5))),                      # x 8'-3"
    Door(uid="CSD217AAAA", tag="D-S-NCLOSET", host="W-S-CLN-S", type_ref="DT-INT-SWING30",
         position=from_node("N-S-C3D", ft(0, 8.5))),                     # x 19'-11 1/2"
    # O-S-STAIRTOP, the 6'-0" cased stair head, went with its host wall W-S-BD-N2.
    # Balcony doors. The source draws ONE opening (x 18'-8"..23'-11", 5'-3", with two
    # leaves), east of the centre line; that is D-S-DECK-E, standardized to the catalog's
    # 5'-0" French pair rather than distorted into a narrow 3'-0" double door.
    # D-S-DECK-W is a deliberate addition to the source (2026-07-31): the balcony runs the
    # full x 7'-6"..28'-6" and only the study reached it, so the plant room now opens onto
    # it too, at the exact mirror of the east door about the x=18' centre line — centre
    # x 13'-8", the same 5'-0" French pair. Mirroring a *pair* is position only: the glyph
    # is symmetric about the opening and `flip_swing` names the side along the wall normal,
    # not a hand, so this carries the east door's flag verbatim to swing out onto the deck.
    # Authoring it flipped instead (flip_hinge, no flip_swing) drew both leaves sweeping
    # north into the plant room — caught in `haus render --view plan`, not by any check.
    # The mirror station is what forced the two balcony condensers off the plant room's
    # wall band: see SECOND_EQUIPMENT in plan/electrical.py.
    Door(uid="CSD218AAAA", tag="D-S-DECK-W", host="W-S-S1", type_ref="DT-EXT-FRENCH60",
         position=from_node("N-S-SW", ft(11, 2)), flip_swing=True),                       # x 13'-8"
    Door(uid="CSD211AAAA", tag="D-S-DECK-E", host="W-S-S2", type_ref="DT-EXT-FRENCH60",
         position=from_node("N-S-S1", ft(1, 10)), flip_swing=True),                       # x 22'-4"
    # Windows — east wall, on the source's four 2'-8" openings (we build 27", the bearing cap).
    # WIN-S-STUDY3 moved off its source position (y 3'-10", 2026-07-30) to y=5'-4" for an
    # exact 9'-0" rhythm on one sill line — within-storey rhythm wins over between-storey
    # stacking here.
    #
    # 2026-08-15: that beat (5'-4"/14'-4"/23'-4"/32'-4") was off-centre (5'-4" of wall south
    # vs 3'-8" north). Now 4'-0"/13'-0"/23'-0"/32'-0" — mirrored about the house centreline,
    # rhythm 9'-0"/10'-0"/9'-0", widths and heads already mirrored, so nothing retyped.
    # Achieved with two node moves (N-S-E2/E3 to 17'-8"/26'-8", which fix W-S-E3/E4's stud
    # phase — see NODES), not four window moves; BED2/BED3's authored offsets never changed.
    # Bonus: WIN-S-STUDY3 now lands over WIN-M-LIV-E1, the east face's first two-storey
    # column; WIN-A-E-N at 32'-4" is the one alignment given up (attic.py).
    Window(uid="CSX314AAAA", tag="WIN-S-STUDY3", host="W-S-E1", type_ref="WT-2736-T",
           position=from_node("N-S-SE", ft(2, 10.5)), sill_height=ft(3)),     # y 4'-0"
    # BED1/BED2 carry the 30" unit, not the east wall's 27" bearing cap (2026-08-01, by
    # decision): both rooms are 124.3 sf with one window, so R303.1 wants 9.95 sf glazed /
    # 4.97 sf openable and a 27x36 falls a third short. `preferences.toml [framing]
    # max_window_ro_bearing_in` moved 27 -> 30 to allow it. WT-3048 clears both thresholds
    # by only 0.05/0.03 sf — arithmetic, not comfort; growing either room's clear face fails
    # R303.1 again, and the fix then is a taller unit, not wider.
    #
    # Sill stays on the shared 3'-0" east-face line; 48" height puts these heads at 7'-0"
    # where WIN-S-STUDY3/BED3 stay at 6'-0". BED1 lost 4" of depth in the 2026-08-15 node
    # move (it had the margin to spare); BED3 gained 4" (it has a second window, 14.2 sf).
    # BED1 carries WT-3048-T because at y=13'-0" the glass falls inside 60" of ST-S2A,
    # R308.4.5's stair band.
    Window(uid="CSX301AAAA", tag="WIN-S-BED1", host="W-S-E2", type_ref="WT-3048-T",
           position=from_node("N-S-E1", ft(2, 9)), sill_height=ft(3)),      # y 13'-0"
    Window(uid="CSX302AAAA", tag="WIN-S-BED2", host="W-S-E3", type_ref="WT-3048",
           position=from_node("N-S-E2", ft(4, 1)), sill_height=ft(3)),      # y 23'-0"
    Window(uid="CSX303AAAA", tag="WIN-S-BED3", host="W-S-E4", type_ref="WT-2736",
           position=from_node("N-S-E3", ft(4, 2.5)), sill_height=ft(3)),    # y 32'-0"
    # West suite (bearing wall) — source openings at y 12'-7" and 19'-4". SUITE2 became a
    # column on 2026-08-15 without moving: N-M-W2 came up to 22'-4" instead, putting
    # W-M-W3's grid in phase (see main.py). SUITE1 stays at 13'-0" and uncolumned — both
    # candidate shared stud lines put a jamb pack into a tee's stud pack (see
    # WIN-M-BED-W2).
    Window(uid="CSX304AAAA", tag="WIN-S-SUITE1", host="W-S-W3", type_ref="WT-2736",
           position=from_node("N-S-W2", ft(8, 2.5)), sill_height=ft(3)),      # y 13'-0"
    Window(uid="CSX305AAAA", tag="WIN-S-SUITE2", host="W-S-W3", type_ref="WT-2736",
           position=from_node("N-S-W2", ft(1, 6.5)), sill_height=ft(3)),      # y 19'-8"
    # Plant room — south glazing: centres 4'-0" and 9'-4" are stud lines on W-S-S1's grid,
    # stacking exactly over WIN-M-BED-S1/2. Sill 2'-8" = the shared 6'-8" head line.
    # Narrowed 42" -> 30" and moved 8" east off the old bay centres (WT-3048, 2026-08-01,
    # see WIN-M-BED-S1/2). Grow pots/LED tubes (placeables.py/lighting.py) stay at
    # x 3'-4"/8'-8", still inside each window's 30" of glass.
    # Retyped to the U-0.14 twins 2026-08-18 (WT-*-HP in main.py): at 75 F / 70% RH the
    # room's dew point is 64.4 F and a U-0.25 unit's inner glass runs 59.7 F at design —
    # these windows ran wet below about +13 F outdoors, which is most of the winter. Same
    # width, same height, same sill, same centres: a retype moves nothing.
    Window(uid="CSX306AAAA", tag="WIN-S-PLANT1", host="W-S-S1", type_ref="WT-3048-HP",
           position=from_node("N-S-SW", ft(2, 9)), sill_height=ft(2, 8)),     # x 4'-0"
    Window(uid="CSX307AAAA", tag="WIN-S-PLANT2", host="W-S-S1", type_ref="WT-3048-HP-T",
           position=from_node("N-S-SW", ft(8, 1)), sill_height=ft(2, 8)),     # x 9'-4"
    # The plant room's west window is on W-S-W4, a bearing wall, so it takes the 27" bearing
    # type, not the 30" south-glazing one ("resize windows to fit the grid", CLAUDE.md).
    # Sill raised to 3'-0" (2026-07-30) for the shared 6'-0" head line. Unmoved by the
    # 2026-08-15 column pass — W-S-W4 starts at N-S-W3 (y=9'-0"), which can't move without
    # dragging the whole east row off its mirror — so WIN-M-BED-W1 came up to meet it
    # instead.
    Window(uid="CSX308AAAA", tag="WIN-S-PLANT3", host="W-S-W4", type_ref="WT-2736-HP",
           position=from_node("N-S-W3", ft(2, 10.5)), sill_height=ft(3)),     # y 5'-0"
    # Study 2's south pair: centres 27'-4" and 32'-8" are stud lines on W-S-S2's grid,
    # stacking exactly over WIN-M-LIV-S2/S1. Moved 8" west off the old bay centres with the
    # WT-3048 narrowing (2026-08-01, see WIN-M-BED-S1/2); the two south segments stay 8"
    # out of phase, the same unavoidable mirror miss as always. Sill 2'-8" is the shared
    # 6'-8" head line; D-S-DECK-E's RO stays clear by 1'-3".
    Window(uid="CSX309AAAA", tag="WIN-S-STUDY1", host="W-S-S2", type_ref="WT-3048-T",
           position=from_node("N-S-S1", ft(8, 1)), sill_height=ft(2, 8)),     # x 27'-4"
    Window(uid="CSX310AAAA", tag="WIN-S-STUDY2", host="W-S-S2", type_ref="WT-3048",
           position=from_node("N-S-S1", ft(13, 5)), sill_height=ft(2, 8)),    # x 32'-8"
    # Baths + north. WIN-S-BATH-N/W have no source counterpart, kept for hall-bath daylight.
    # Re-hosted off W-S-N3 (2026-07-28): W-S-N3B is now the chase's own wall, not the
    # bathroom's. Nudged to 8" off N-S-CH2 (2026-07-29): at 1' the RO straddled the module
    # stud line instead of centering in the bay, breaking two studs and pulling in a
    # header/jacks a 14" RO should never need
    # (test_catlin_small_windows_have_no_header_and_keep_their_flanking_studs).
    Window(uid="CSX311AAAA", tag="WIN-S-BATH-N", host="W-S-N3", type_ref="WT-1424-T",
           position=from_node("N-S-CH2", ft(0, 8)), sill_height=ft(4)),
    # Re-hosted off N-S-CH3 (2026-07-28) after the chase split W-S-W1 there. Same physical
    # position, centre y=31'-4" — the west face's fourth column: WIN-M-MUD is the same 14"
    # unit at the same centre, both hosts starting at y=33'-4", the face's only true column
    # since before the others.
    Window(uid="CSX312AAAA", tag="WIN-S-BATH-W", host="W-S-W1", type_ref="WT-1424-T",
           position=from_node("N-S-CH3", ft(1, 5)), sill_height=ft(4)),
    # Moved 29'-4" -> 28'-0" (2026-07-30 facade pass): WIN-M-KITCH below and WIN-A-N2
    # above are both centred at x 28'-0", and 28'-0" is a stud line on W-S-N1's own
    # grid too, so the north facade gets one exact three-storey column.
    Window(uid="CSX313AAAA", tag="WIN-S-HALL-N", host="W-S-N1", type_ref="WT-3036",
           position=from_node("N-S-NE", ft(6, 9)), sill_height=ft(3)),        # x 28'-0"
    # Stairwell daylight (2026-07-30 facade pass): the north facade was blank from the
    # entry column to x=21'-11". Centre x 12'-8" is the stud line inside the arriving
    # upper flight's lane. WIN-A-N1 could stack on this (12'-8" is a stud line on W-A-N2
    # too) but deliberately stays at 7'-4" instead, so the north gable reads
    # near-symmetric about the ridge — the same read that governs the south gable pair.
    Window(uid="CSX315AAAA", tag="WIN-S-STAIR-N", host="W-S-N2", type_ref="WT-3036-T",
           position=from_node("N-S-N1", ft(4, 1)), sill_height=ft(3)),        # x 12'-8"
]

ROOMS = [
    # The tropical room: held at ~75 F / 70% RH year-round, including at the site's -15 F
    # heating design temperature. `humidity_class` is a separate axis from `occupancy`
    # deliberately — this genuinely is a LIVING room, and it is the humidity, not the use,
    # that governs every assembly bounding it. The explicit pair of setpoints is authored
    # because dew point is a function of both: 75 F / 70% RH is 64.4 F, and every surface
    # in the room colder than that is wet.
    #
    # RH strategy on the equipment side (notes/plant_room.md): hold 70% whenever outdoors
    # is >= +10 F and reset down to about 55% at -15 F. The model carries the design
    # figure, which is the one the assemblies have to survive.
    #
    # `floor_finish` leaves "tile" for heat-welded sheet vinyl with a 6" integral flash
    # cove that laps up the wall and dies behind the wall membrane, so floor and wall are
    # one tray with no base joint. Nothing impermeable goes under it — a second Class I
    # layer beneath sheet vinyl sandwiches the plywood subfloor with no drying path either
    # way. The cove IS the waterproofing.
    Room(uid="CSR401AAAA", tag="RM-S-PLANT", seed=pt(ft(9), ft(4)),
         occupancy=Occupancy.LIVING, humidity_class=HumidityClass.HUMID,
         design_relative_humidity=0.70, design_temperature_f=75.0,
         floor_finish="vinyl-sheet"),
    Room(uid="CSR402AAAA", tag="RM-S-STUDY2", seed=pt(ft(27), ft(4)),
         occupancy=Occupancy.OFFICE, floor_finish="oak"),
    # BED1's east wall is the house's one painted accent (spruce green-blue): swaps the
    # lining stack for assemblies.py's ACCENT_GWB_LINING (same film/gypsum/thickness, only
    # paint differs). Re-stated inline, not imported, because the editable dialect can't
    # import a sibling plan module — keep in step with ACCENT_GWB_LINING by hand.
    Room(uid="CSR403AAAA", tag="RM-S-BED1", seed=pt(ft(29), ft(13, 6)),
         occupancy=Occupancy.BEDROOM, floor_finish="carpet",
         wall_lining_exceptions=(
             WallLiningException(
                 uid="CSL501AAAA", tag="LX-S-BED1-E", wall_ref="W-S-E2",
                 lining=(
                     Layer(name="paint", material_ref="latex-paint-accent",
                           thickness=inch(0.01), function=LayerFunction.FINISH,
                           control={ControlLayer.VAPOR}),
                     Layer(name="gwb-int", material_ref="gwb", thickness=inch(0.625),
                           function=LayerFunction.FINISH),
                 )),
         )),
    Room(uid="CSR404AAAA", tag="RM-S-BED2", seed=pt(ft(29), ft(22, 6)),
         occupancy=Occupancy.BEDROOM, floor_finish="carpet"),
    Room(uid="CSR405AAAA", tag="RM-S-BED3", seed=pt(ft(29), ft(31, 6)),
         occupancy=Occupancy.BEDROOM, floor_finish="carpet"),
    # The suite is the source's L: the full west strip plus the arm that reaches the centre
    # line between the walk-in and the suite bath.
    Room(uid="CSR406AAAA", tag="RM-S-SUITE", seed=pt(ft(5), ft(16)),
         occupancy=Occupancy.BEDROOM, floor_finish="carpet"),
    Room(uid="CSR407AAAA", tag="RM-S-CLOSET", seed=pt(ft(14), ft(10, 8)),
         occupancy=Occupancy.STORAGE, floor_finish="carpet"),
    # LVP through the wet rooms and the circulation: one continuous plank floor from the
    # stair head through both hallways and into all three second-storey baths, so the
    # traffic route has no thresholds in it and the baths get a waterproof plank instead of
    # tile. RM-S-BATH1 puts LVP over the FH-S-BATH1 electric radiant zone — allowed, but
    # surface-temperature limited, which advisory.floor_finish_over_radiant flags.
    Room(uid="CSR412AAAA", tag="RM-S-SUITEBATH", seed=pt(ft(14), ft(19)),
         occupancy=Occupancy.BATHROOM, floor_finish="lvp"),
    Room(uid="CSR413AAAA", tag="RM-S-VANITY", seed=pt(ft(3), ft(24, 4)),
         occupancy=Occupancy.BATHROOM, floor_finish="lvp"),
    Room(uid="CSR408AAAA", tag="RM-S-BATH1", seed=pt(ft(5), ft(31)),
         occupancy=Occupancy.BATHROOM, floor_finish="lvp"),
    # RM-S-HALL is the source's single 181.02 sf "Hallway" again: taking the centre line
    # out between y 22'-4" and 30'-10" left one polygonized face spanning the old hall,
    # landing and open stair well, so RM-S-LANDING/RM-S-STAIR were retired into this claim
    # rather than billing the same face three times. RL-S-STAIR guards the well's east edge.
    Room(uid="CSR409AAAA", tag="RM-S-HALL", seed=pt(ft(20), ft(20)),
         occupancy=Occupancy.HALLWAY, floor_finish="lvp"),
    # Both walk-ins are carpet — a closet floor is never walked on in shoes, and carpet
    # continues out of the bedroom it opens off.
    Room(uid="CSR415AAAA", tag="RM-S-NCLOSET", seed=pt(ft(20), ft(33)),
         occupancy=Occupancy.STORAGE, floor_finish="carpet"),
]

ALARMS = [
    Alarm(uid="CSA701AAAA", tag="AL-S-BED1", kind=AlarmKind.COMBO, room="RM-S-BED1",
          circuit="CKT-LT-BACKUP"),
    Alarm(uid="CSA702AAAA", tag="AL-S-BED2", kind=AlarmKind.COMBO, room="RM-S-BED2",
          circuit="CKT-LT-BACKUP"),
    Alarm(uid="CSA703AAAA", tag="AL-S-BED3", kind=AlarmKind.COMBO, room="RM-S-BED3",
          circuit="CKT-LT-BACKUP"),
    Alarm(uid="CSA704AAAA", tag="AL-S-SUITE", kind=AlarmKind.COMBO, room="RM-S-SUITE",
          circuit="CKT-LT-BACKUP"),
    Alarm(uid="CSA705AAAA", tag="AL-S-HALL", kind=AlarmKind.COMBO, room="RM-S-HALL",
          circuit="CKT-LT-BACKUP"),
]

# Electric radiant floor in the NW bathroom (2026-07-25): RM-S-BATH1 is the hall bath (see
# header note), the only one heated on this storey. Same recipe as main.py's zones: 12 W/ft2
# 120V mat at a 3" serpentine. `in_slab` is just the enum mode name — this floor is
# FS-SECOND's I-joists/plywood, and the mat lies in the thinset above it. CKT-FH-BATH1 and
# ED-S-BATH1-FH-STAT carry it.
#
# The zone is drawn to the fixtures (plan/fixtures.py's de-overlapped WC/lav/shower
# positions), not the room outline, holding 3" off every fixture: total 31.6 ft2 across a
# south band, an east step to the lav, and a centre panel between WC and shower. The strips
# north of the WC and west of the pan are left unheated rather than run a 3"-wide corridor.
FLOOR_HEAT = [
    FloorHeat(uid="CSH801AAAA", tag="FH-S-BATH1", room_ref="RM-S-BATH1",
              zone=(pt(ft(0, 5), ft(26, 9)), pt(ft(9, 7), ft(26, 9)),
                    pt(ft(9, 7), ft(29, 9)), pt(ft(7, 11), ft(29, 9)),
                    pt(ft(7, 11), ft(31, 3)), pt(ft(3, 3), ft(31, 3)),
                    pt(ft(3, 3), ft(28, 6)), pt(ft(0, 5), ft(28, 6))),
              system=RadiantSystem.ELECTRIC, spacing=inch(3), embed=in_slab(inch(0.5)),
              # 42.4 ft2 at the 12 W/ft2 of plan/circuits.py -> 509 W, carried at 510.
              watts=510,
              stat=pt(ft(1, 6), ft(32))),
]

# The hallway duct soffit (HRV + heat mains), plans/TODO.md's "2nd floor hallway dropped
# ceiling for HVAC" — dashed on plan, framed in 3D. Widened 2026-07-29 to enclose BOTH of
# System 1's ducts side by side (DU-S-HP-SUP at x=19'-4", DU-S-HP-RET at x=20'-8", each
# 14"x8", plan/mep.py DUCTS_HVAC_SECOND); 14" drop clears duct + 2x4 framing/hangers.
# Runs y 6'-0"..34'-0", reaching south into RM-S-STUDY2 to meet EQ-S-HP1-AH's trunk collars.
# LR-S-HALL-GAP already washes the soffit's flanks at x=18'-6"/21'-6", so no new lighting.
#
# WIDTH: the plan's 2'-8" box loses 4 1/4" total to framing/lining, leaving only 27 3/4"
# clear — short of the 28" the two 14" ducts need side by side (2" gap for hangers/flanges).
# Box widened to 35" (x 18'-6 1/2"..21'-5 1/2", still centred on the duct centrelines) for
# 30 3/4" clear. Face elevation unchanged at 7'-10"; ED-S-HALL-CAN1/2/3 set into it.
SOFFITS = [
    Soffit(uid="CSF601AAAA", tag="SF-S-DUCT",
           outline=(pt(ft(18, 6.5), ft(6)), pt(ft(21, 5.5), ft(6)),
                    pt(ft(21, 5.5), ft(34)), pt(ft(18, 6.5), ft(34))),
           drop=inch(14),
           framing=FramingSpec(member="2x2", spacing=inch(16))),
    # The west branch to the suite (DU-S-HP-SUITE) — rerouted 2026-07-30 onto the short
    # straight line over D-S-SUITE and the suite's entry arm, instead of a 2026-07-29 detour
    # crossing RM-S-SUITEBATH's fixtures. The duct passes through W-S-C2B in the cripple
    # zone above the door header — the right place to cross a bearing wall already broken
    # by a door below.
    #
    # The soffit is the arm's ceiling, sitting 3" off both arm-wall axes (y 12'-8"..15'-8")
    # — the same shadow-gap inset SF-S-DUCT uses, needed because an outline ON the wall
    # lines puts the ladder rails inside the walls' own stud zones
    # (structural.member_interference). Runs x 12'-0" (D-S-SUITEBATH's jamb) to 18'-6 1/2"
    # (abutting SF-S-DUCT, reading as one continuous box). 36" plan width clears a single
    # 10" duct with room to spare.
    Soffit(uid="CSF6S1AAAA", tag="SF-S-SUITE",
           outline=(pt(ft(12), ft(12, 8)), pt(ft(18, 6.5), ft(12, 8)),
                    pt(ft(18, 6.5), ft(15, 8)), pt(ft(12), ft(15, 8))),
           drop=inch(14),
           framing=FramingSpec(member="2x2", spacing=inch(16))),
]

# Drawn to the main floor's *finished* well, the way FO-M-STAIR is drawn to the basement's
# — the shaft a stair actually climbs. An opening on the wall centrelines instead would put
# the stringers inside the stud cavities and leave the flight to be posted down
# (plans/TODO.md D3).
#
# This well is 7'-5 1/4" where the basement's is 7'-0", because the 2x6 walls here are
# thinner than the 12" concrete they stack on — each flight sizes to its own storey's well.
# Run north to south (2026-07-28): north is W-M-N2's inside gwb face (y=35'-5 3/8"), 9'-5"
# back to the R311.7.6 landing plus seven 11" treads gives the south edge at 26'-0 3/8".
# This head runs 5 3/8" further north than FO-M-STAIR's (which stops on the concrete at
# 35'-0") because only the wall's outer 6" is under anything — the inner half of the 12"
# concrete is free plan area up here. Deliberately NOT moved onto the source: it's drawn to
# the *main* storey's finished faces, so moving it means moving main.py.
FLOOR_OPENINGS = [
    FloorOpening(uid="CSF602AAAA", tag="FO-S-STAIR",
                 outline=(pt(ft(10, 3.375), ft(26, 0.375)),
                          pt(ft(17, 8.625), ft(26, 0.375)),
                          pt(ft(17, 8.625), ft(35, 5.375)),
                          pt(ft(10, 3.375), ft(35, 5.375))),
                 # Both long edges are carried by bearing wall, so neither needs a header:
                 # W-M-STRW/STRW2 west, W-M-C5 east (which since 2026-07-28 starts at
                 # N-M-C3 on the stair wall's line, so it still reaches this edge's south
                 # end even though W-M-C4B under it is gone).
                 bearing_refs=("W-M-STRW", "W-M-STRW2", "W-M-C5")),
]

# The beam that lets the centre line be open (2026-07-28). Per CLAUDE.md, x=18' is a
# bearing line footings-to-ridge, and opening it *without a beam* would dump ~1.5 klf of
# ridge thrust into 5' knee walls rated for ~0.1 klf; this LVL is that bearing line for its
# 8'-6", and W-A-C2 lands on it.
#
# Load, per foot: FS-ATTIC's 18' tributary (~990 plf) + RB-HOUSE's 18' tributary at the
# site's Pf = 35 psf snow load (~900 plf, corrected 2026-08-01 from an under-counted
# 810 plf/30 psf) + wall plate (~100 plf) = ~1,990 plf total. Over 8'-6": M = 18.0 ft-k,
# V = 8.5 k. Three plies of 1.75x11.875 LVL give Sx = 123 in^3 (26.7 ft-k) and 62 in^2
# shear area (11.8 k), deflecting 0.16" against L/360 = 0.28" — same section/ply count as
# RB-HOUSE, one LVL depth on the job.
#
# Bears on the ends of the walls it replaced (W-S-C2C/W-S-C4B), stacking to the footings.
# Framed FLUSH (`top_elevation` at the attic joist datum) so the 9' ceiling stays unbroken
# across the hall — the default derivation can't reach this since it drops a beam below its
# *own* storey datum, but this beam carries the floor of the storey above.
BEAMS = [
    Beam(uid="CSBM01AAAA", tag="BM-S-HALL", start_node="N-S-C2C", end_node="N-S-C3D",
         size="3-1.75x11.875 LVL", bearing_refs=("W-S-C2C", "W-S-C4B"),
         top_elevation=ft(20)),
]

# Guards on the two open sides of the stair well: attic RL-A-STAIR product, 42" height,
# fascia mounted to the well rim (BM-S-HALL on the east side). They leave exactly one
# gap — the flight's own throat, where the upper flight arrives southbound on the well's
# west half. Both moved north and swapped hands on 2026-07-28 with the well itself.
# Drawn to FO-S-STAIR's own coordinates, not the retired wall centrelines.
STAIR_GUARDS = [
    Railing(
        uid="CSRL01AAAA", tag="RL-S-STAIR", type_ref="RAILING-INT-STAIR-GUARD", path=(
            pt(ft(17, 8.625), ft(26, 0.375)),
            pt(ft(17, 8.625), ft(30, 10)),
        ),
        kind=RailingKind.METAL_FASCIA_MOUNT, height=ft(3.5),
        base_elevation=ft(10), post_spacing=inch(60), post_size="2x2", rail_count=2,
        mount="fascia", assembly="RAILING_DARK_METAL",
        # R312.1.3: vertical balusters between the 60" posts, 4" clear gap — the largest
        # opening the 4"-sphere rule admits.
        infill="balusters", baluster_spacing=inch(4),
    ),
    # 3'-6 7/8" from the west jamb of the throat — the well partition's west face — to the
    # well's east edge, where RL-S-STAIR turns the corner.
    Railing(
        uid="CSRL02AAAA", tag="RL-S-STAIRHEAD", type_ref="RAILING-INT-STAIR-GUARD", path=(
            pt(ft(13, 9.75), ft(26, 0.375)),
            pt(ft(17, 8.625), ft(26, 0.375)),
        ),
        kind=RailingKind.METAL_FASCIA_MOUNT, height=ft(3.5),
        base_elevation=ft(10), post_spacing=inch(60), post_size="2x2", rail_count=2,
        mount="fascia", assembly="RAILING_DARK_METAL",
        infill="balusters", baluster_spacing=inch(4),
    ),
]

# ST-M2S handrails (R311.7.8): one wall-mounted rail per flight, graded by
# code.R311_7_8_handrail via `serves_stair`, raked along each flight's nosing line
# (`top_height` 34"-38"). Lower flight (east lane) rails on W-M-C5's stair face; upper
# flight (west lane) rails on W-M-STRW2's face — each 2" off its wall (bracket standoff).
# rail_count=1: a handrail, not a guard frame; role="handrail" keeps these out of the
# R312.1.3 guard-infill census.
STAIR_HANDRAILS = [
    Railing(
        uid="CSRL03AAAA", tag="RL-S-HANDRAIL-E", path=(
            pt(ft(17, 6.625), ft(26, 0.375)),
            pt(ft(17, 6.625), ft(31, 10.375)),
        ),
        kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
        base_elevation=ft(0), post_spacing=inch(48), post_size="2x2", rail_count=1,
        mount="wall", assembly="RAILING_DARK_METAL",
        role="handrail", serves_stair="ST-M2S", top_height=inch(36),
        graspable_profile="1.5in round — Type I",
    ),
    Railing(
        uid="CSRL04AAAA", tag="RL-S-HANDRAIL-W", path=(
            pt(ft(10, 5.375), ft(31, 10.375)),
            pt(ft(10, 5.375), ft(26, 10.375)),
        ),
        kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
        base_elevation=ft(10), post_spacing=inch(48), post_size="2x2", rail_count=1,
        mount="wall", assembly="RAILING_DARK_METAL",
        role="handrail", serves_stair="ST-M2S", top_height=inch(36),
        graspable_profile="1.5in round — Type I",
    ),
]

# Structural deck: 11-7/8" I-joists spanning E-W on the three bearing lines.
FLOOR = [
    FloorSystem(uid="CSF603AAAA", tag="FS-SECOND",
                joists=JoistSpec(member="11.875 I-joist", spacing=inch(16),
                                 direction="x",
                                 # BM-M-HALL is the centre line for its 4'-2"; the joists
                                 # either side of the hall opening hang off it, exactly as
                                 # FS-ATTIC's do off BM-S-HALL one storey up.
                                 bearing_refs=("W-M-W2", "W-M-C2", "W-M-E1",
                                               "BM-M-HALL")),
                subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=inch(0.75)),
                # The main floor's ceiling: this deck's underside *is* that ceiling. Until
                # authored, a whole storey of ceiling gypsum was missing from the order —
                # nothing else in the plan says a ceiling exists. Plain board, not type X:
                # R302.13 doesn't reach this floor. Layered ceiling assemblies stay
                # deferred; the living room's resilient channel rides on it separately as
                # CR-LIVING-CEIL-RC (plan/assemblies.py).
                ceiling_below=DeckLayer(material_ref="gwb", thickness=inch(0.625)),
                openings=("FO-S-STAIR",)),
]

# The suite bedroom's four "tudor" posts (plans/TODO.md §Hardwood): custom 6-1/8" square
# elm timbers standing in W-S-W3's stud line, flush with the drywall plane. Deliberately
# NOT a change to CATLIN_EXT_2X6 — each post is a deviation within the stud line, so the
# wall assembly is untouched. Centre x=3-9/16" off the sheathing-ext plane; cut 8'-11 1/4"
# to top out flush with the 9' plate. y-positions keep >6" clear of both WT-2736 ROs.
POSTS = [
    Post(uid="CSK901AAAA", tag="P-S-TUDOR1", position=pt(inch(3.5625), ft(10, 8)),
         size="6.125x6.125", height=ft(8, 11.25), supported_by="FS-SECOND",
         within_wall="W-S-W3", assembly="ELM_TIMBER"),
    Post(uid="CSK902AAAA", tag="P-S-TUDOR2", position=pt(inch(3.5625), ft(15, 4)),
         size="6.125x6.125", height=ft(8, 11.25), supported_by="FS-SECOND",
         within_wall="W-S-W3", assembly="ELM_TIMBER"),
    Post(uid="CSK903AAAA", tag="P-S-TUDOR3", position=pt(inch(3.5625), ft(17, 4)),
         size="6.125x6.125", height=ft(8, 11.25), supported_by="FS-SECOND",
         within_wall="W-S-W3", assembly="ELM_TIMBER"),
    Post(uid="CSK904AAAA", tag="P-S-TUDOR4", position=pt(inch(3.5625), ft(21, 4)),
         size="6.125x6.125", height=ft(8, 11.25), supported_by="FS-SECOND",
         within_wall="W-S-W3", assembly="ELM_TIMBER"),
]

STAIRS = [
    # 7'-5 1/4" well = 3'-6 3/8" + 4 1/2" well partition + 3'-6 3/8". Landing is the
    # R311.7.6 36" minimum. `turn_direction="left"`, same hand as ST-B2M below: the flight
    # springs east lane on main, arrives west lane on second, so the stack alternates sides
    # as one continuous run.
    Stair(uid="CST702AAAA", tag="ST-M2S", floor_opening="FO-S-STAIR",
          from_storey="main", to_storey="second", width=ft(3, 6.375),
          layout="u_split_landing", run_direction="y", turn_direction="left",
          start=pt(ft(10, 3.375), ft(26, 0.375)), landing_depth=ft(3)),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *FLOOR_HEAT, *SOFFITS,
            *FLOOR_OPENINGS, *BEAMS, *STAIR_GUARDS, *STAIR_HANDRAILS, *FLOOR, *POSTS,
            *STAIRS]
