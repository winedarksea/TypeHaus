# haus: editable
# Second floor — CATLIN_EXT_2X6 on the same sheathing plane (2x6 on every framed
# storey), three east bedrooms, west suite, plant room + study south, duct soffit (WP3.1).
#
# Every interior partition on this storey is set to the Sensopia survey drawing
# `catlin_floorplan/Colin House - 2nd Floor.svg`, read off `path` #0 (the wall-fill
# polygon) at that drawing's 74.7029 px/m and rounded to the nearest inch. The fidelity
# policy is: interior partitions move to the source; the exterior envelope, the x=18'
# bearing line and the 16" framing module do not. `preferences.toml`'s `[[underlay]]` for
# this storey is calibrated to the same polygon, so `haus render --view plan` draws the
# survey under this plan and the two can be compared by eye.
#
# Known, deliberate divergences from the source:
# - The source opens the centre line up between y=22'-7" and y=31'-1 1/2" and again at the
#   suite and plant-room doors. The suite and plant-room breaks are modelled as *openings
#   in* the wall — D-S-SUITE, D-S-PLANT — the way `main.py` does with O-M-HALL/O-M-DRESS.
#   The big one is real: as of 2026-07-28 the centre line carries no wall at all between
#   y=22'-4" and y=30'-10" (nearly the source's own break), just BM-S-HALL, three plies of
#   11-7/8" LVL. The bearing stack is still continuous — the beam *is* the stack there —
#   and the source's single 181.02 sf "Hallway" now reads as one room, RM-S-HALL, taking
#   in the old landing and the open stair well; RL-S-STAIR guards the well's east edge.
# - The source's south-wall openings are four 6'/5'-3" runs and its bearing-wall windows are
#   2'-8"; `preferences.toml` caps a bearing RO at 30" (raised from 27" on 2026-08-01 for
#   WIN-S-BED1/BED2) and a non-bearing one at 42". The existing window *types* are kept and
#   only their positions move onto the source openings.
# - `WIN-S-BATH-W` and `WIN-S-BATH-N` have no counterpart — the source draws no opening in
#   the west wall north of y=25'-8" and none in the north wall west of x=21'-10". Both are
#   kept for bathroom daylight.
# - `RM-S-BATH1` is the hall bath (the source's 80.73 sf "Bathroom"); the suite's own bath
#   is RM-S-SUITEBATH. It was tagged `RM-S-ENSUITE` until 2026-07-27, which it never was —
#   the rename ran through fixtures.py, mep.py, views.py, lighting.py and electrical.py.
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
    # The three east bedrooms are equal 9'-0" bays (source 9.035 / 17.991 / 26.947),
    # replacing the 8'-0" bays the port started with.
    Node(uid="CSN004AAAA", tag="N-S-E1", position=pt(ft(36), ft(9))),
    Node(uid="CSN005AAAA", tag="N-S-E2", position=pt(ft(36), ft(18))),
    Node(uid="CSN006AAAA", tag="N-S-E3", position=pt(ft(36), ft(27))),
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
    Node(uid="CSN019AAAA", tag="N-S-B2", position=pt(ft(21, 11), ft(18))),
    Node(uid="CSN020AAAA", tag="N-S-B3", position=pt(ft(21, 11), ft(27))),
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
    # The mechanical chase moved from the hall bath's NE corner to its NW corner
    # (2026-07-28): it now stacks on RM-M-MECH below and the attic exit above, riding the
    # radon+plumbing riser. N-S-CH1 is the chase's inner (SE) corner; N-S-CH2/CH3 are its
    # tees into the exterior north/west walls.
    Node(uid="CSN035AAAA", tag="N-S-CH1", position=pt(ft(2, 9), ft(33, 4))),
    Node(uid="CSN036AAAA", tag="N-S-CH2", position=pt(ft(2, 9), ft(36))),
    Node(uid="CSN037AAAA", tag="N-S-CH3", position=pt(ft(0), ft(33, 4))),
]

WALLS = [
    # --- exterior loop (2x6, same stack as main) -------------------------------
    Wall(uid="CSW101AAAA", tag="W-S-S1", start_node="N-S-SW", end_node="N-S-S1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
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
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-W4"),
    # --- center bearing wall (2x6 carries the attic floor) ---------------------
    # Continuous from gable to gable — the attic's structural ridge bears on the stack this
    # line belongs to. The three source breaks are doors/cased openings, not gaps.
    Wall(uid="CSW114AAAA", tag="W-S-C1", start_node="N-S-S1", end_node="N-S-C1",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
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
    # Full-lite glass leaf admits daylight from the south-facing plant room into the hall.
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
    # WIN-S-STUDY3 departs from its source position (y 3'-10") on purpose (2026-07-30
    # facade pass): at y 4'-0" the row read 10'-4"/9'-0"/9'-0" and its 2'-6" sill broke
    # the storey's 3'-0" line. At y 5'-4" (a stud line) the four windows run an exact
    # 9'-0" rhythm and one sill line — the facade now favors within-storey rhythm over
    # between-storey stacking on this side (LIV-E1 below no longer stacks under it).
    Window(uid="CSX314AAAA", tag="WIN-S-STUDY3", host="W-S-E1", type_ref="WT-2736-T",
           position=from_node("N-S-SE", ft(4, 2.5)), sill_height=ft(3)),      # y 5'-4"
    # BED1/BED2 carry the 30" unit, not the east wall's 27" bearing size (2026-08-01, by
    # decision). Both rooms are 124.3 sf with one window each, so R303.1 wants 9.95 sf of
    # glazing and 4.97 sf openable and a 27x36 delivers 6.75/3.38 — a third short. The east
    # wall is a bearing line, where the house's own cap is a 27" RO, and the decision was to
    # widen anyway and frame it properly: a 30" RO centred on a stud line breaks one stud and
    # takes the ordinary jack/king/header pack the solver already builds for it.
    # `preferences.toml [framing] max_window_ro_bearing_in` moved 27 -> 30 with this.
    #
    # WT-3048 rather than a new size: 10.0 sf glazed / 5.0 sf openable, which clears both
    # thresholds — but by 0.05 sf and 0.03 sf respectively, so the margin is arithmetic, not
    # comfort. Anything that grows these two rooms' clear face fails R303.1 again and the
    # answer then is a taller unit, not a wider one (the 9'-0" plate takes a 54" leaf at this
    # sill).
    #
    # The sill stays on the east face's 3'-0" line — that line and the 9'-0" beat are what
    # this facade is organized by, per CLAUDE.md, and the 48" height puts these two heads at
    # 7'-0" where WIN-S-STUDY3 and WIN-S-BED3 stay at 6'-0". BED3 needs nothing: it has a
    # second window and reads 14.2 sf.
    Window(uid="CSX301AAAA", tag="WIN-S-BED1", host="W-S-E2", type_ref="WT-3048",
           position=from_node("N-S-E1", ft(4, 1)), sill_height=ft(3)),      # y 14'-4"
    Window(uid="CSX302AAAA", tag="WIN-S-BED2", host="W-S-E3", type_ref="WT-3048",
           position=from_node("N-S-E2", ft(4, 1)), sill_height=ft(3)),      # y 23'-4"
    Window(uid="CSX303AAAA", tag="WIN-S-BED3", host="W-S-E4", type_ref="WT-2736",
           position=from_node("N-S-E3", ft(4, 2.5)), sill_height=ft(3)),      # y 32'-4"
    # West suite (bearing wall) — source openings at y 12'-7" and 19'-4"
    Window(uid="CSX304AAAA", tag="WIN-S-SUITE1", host="W-S-W3", type_ref="WT-2736",
           position=from_node("N-S-W2", ft(8, 2.5)), sill_height=ft(3)),      # y 13'-0"
    Window(uid="CSX305AAAA", tag="WIN-S-SUITE2", host="W-S-W3", type_ref="WT-2736",
           position=from_node("N-S-W2", ft(1, 6.5)), sill_height=ft(3)),      # y 19'-8"
    # Plant room — south glazing: centres 4'-0" and 9'-4" are stud lines on W-S-S1's grid
    # (one stud broken each) and stack exactly over WIN-M-BED-S1/2 below. Sill 2'-8" = the
    # shared 6'-8" head line. Narrowed 42" -> 30" and moved 8" east off the old
    # 3'-4"/8'-8" bay centres (WT-3048, 2026-08-01) — see WIN-M-BED-S1/2 for why the
    # module's ideal position flips with the RO width. The grow pots and their LED tubes
    # (placeables.py / lighting.py) stay at x 3'-4"/8'-8": each still stands inside its
    # window's 30" of glass (RO 2'-9"..5'-3" and 8'-1"..10'-7"), so the daylight the tubes
    # supplement still lands on the foliage.
    Window(uid="CSX306AAAA", tag="WIN-S-PLANT1", host="W-S-S1", type_ref="WT-3048",
           position=from_node("N-S-SW", ft(2, 9)), sill_height=ft(2, 8)),     # x 4'-0"
    Window(uid="CSX307AAAA", tag="WIN-S-PLANT2", host="W-S-S1", type_ref="WT-3048-T",
           position=from_node("N-S-SW", ft(8, 1)), sill_height=ft(2, 8)),     # x 9'-4"
    # The plant room's west window is on W-S-W4, a bearing wall, so it takes the 27" bearing
    # type and not the 30" south-glazing one — "resize windows to fit the grid" (CLAUDE.md).
    # Sill raised 2'-0" -> 3'-0" (2026-07-30 facade pass): the west facade's 27" units
    # all sit on the 3'-0" sill so every head lands on one 6'-0" line.
    Window(uid="CSX308AAAA", tag="WIN-S-PLANT3", host="W-S-W4", type_ref="WT-2736",
           position=from_node("N-S-W3", ft(2, 10.5)), sill_height=ft(3)),     # y 5'-0"
    # Study 2's south pair: centres 27'-4" and 32'-8" are stud lines on W-S-S2's grid and
    # stack exactly over WIN-M-LIV-S2/S1. Moved 8" west off the old 28'-0"/33'-4" bay
    # centres with the WT-3048 narrowing (2026-08-01) — see WIN-M-BED-S1/2. The two south
    # segments' stud grids are 8" out of phase, so the mirror of the plant pair stays 8"
    # away whichever line these sit on; this is that phase-minimum miss, unchanged. Sill
    # 2'-8" is the shared 6'-8" head line, and D-S-DECK-E's french-door RO (ends 24'-10")
    # stays clear by 1'-3".
    Window(uid="CSX309AAAA", tag="WIN-S-STUDY1", host="W-S-S2", type_ref="WT-3048-T",
           position=from_node("N-S-S1", ft(8, 1)), sill_height=ft(2, 8)),     # x 27'-4"
    Window(uid="CSX310AAAA", tag="WIN-S-STUDY2", host="W-S-S2", type_ref="WT-3048",
           position=from_node("N-S-S1", ft(13, 5)), sill_height=ft(2, 8)),    # x 32'-8"
    # Baths + north. The source draws no opening in the north wall west of x=21'-10" and
    # none in the west wall north of y=25'-8"; WIN-S-BATH-N/W are kept anyway so the hall
    # bath has daylight, and are the storey's only two openings with no source counterpart.
    # Re-hosted off W-S-N3 (2026-07-28): W-S-N3B is now the chase's own short north wall,
    # not the bathroom's — a window there would light the mechanical closet, not the room.
    # 1' clear of the N-S-CH2 tee, well past the old 1"-edge-clearance pinch this wall used
    # to have (that note no longer applies to either segment). Nudged to 8" (2026-07-29):
    # at 1' the RO straddled the module stud line instead of centering in the bay, breaking
    # two studs and pulling in a header/jacks a 14" RO should never need
    # (test_catlin_small_windows_have_no_header_and_keep_their_flanking_studs).
    Window(uid="CSX311AAAA", tag="WIN-S-BATH-N", host="W-S-N3", type_ref="WT-1424-T",
           position=from_node("N-S-CH2", ft(0, 8)), sill_height=ft(4)),
    # Re-hosted off N-S-CH3 (2026-07-28): W-S-W1 no longer starts at N-S-NW now that the
    # chase's south wall splits it there. Same physical window position (y=31'-11").
    Window(uid="CSX312AAAA", tag="WIN-S-BATH-W", host="W-S-W1", type_ref="WT-1424-T",
           position=from_node("N-S-CH3", ft(1, 5)), sill_height=ft(4)),
    # Moved 29'-4" -> 28'-0" (2026-07-30 facade pass): WIN-M-KITCH below and WIN-A-N2
    # above are both centred at x 28'-0", and 28'-0" is a stud line on W-S-N1's own
    # grid too, so the north facade gets one exact three-storey column.
    Window(uid="CSX313AAAA", tag="WIN-S-HALL-N", host="W-S-N1", type_ref="WT-3036",
           position=from_node("N-S-NE", ft(6, 9)), sill_height=ft(3)),        # x 28'-0"
    # Stairwell daylight (2026-07-30 facade pass): W-S-N2 is the wall over ST-M2S's
    # well, and the north facade was blank from the entry column to x=21'-11". Centre
    # x 12'-8" is the stud line inside the arriving upper flight's lane (x 10'-3"..
    # 13'-9"); RO edges keep 1'-5" clear of the N-S-N2 corner. Same type and 3'-0"
    # sill as WIN-S-HALL-N — the landing it lights sits a half-storey below, so the
    # glass is well out of guard territory. WIN-A-N1 could stack on this (12'-8" is a
    # stud line on W-A-N2 too) but deliberately does not: it stays at 7'-4" so the
    # north gable reads near-symmetric about the ridge (10'-8" west vs 10'-0" east),
    # the same way the south gable pair does. On a gable end ridge symmetry is the
    # stronger read than a two-storey column, and the two gables then match.
    Window(uid="CSX315AAAA", tag="WIN-S-STAIR-N", host="W-S-N2", type_ref="WT-3036-T",
           position=from_node("N-S-N1", ft(4, 1)), sill_height=ft(3)),        # x 12'-8"
]

ROOMS = [
    Room(uid="CSR401AAAA", tag="RM-S-PLANT", seed=pt(ft(9), ft(4)),
         occupancy=Occupancy.LIVING, floor_finish="tile"),
    Room(uid="CSR402AAAA", tag="RM-S-STUDY2", seed=pt(ft(27), ft(4)),
         occupancy=Occupancy.OFFICE, floor_finish="oak"),
    # BED1's east wall is the house's one painted accent (spruce green-blue): the exception
    # swaps that wall's lining stack for assemblies.py's ACCENT_GWB_LINING — same film, same
    # gypsum, same thickness, only the paint *material* differs. The two layers are re-stated
    # inline because the editable dialect imports only from typehaus.*/library.*, never from
    # a sibling plan module; keep them in step with ACCENT_GWB_LINING. W-S-E2 is exterior,
    # so no second room can claim it (integrity.wall_lining_conflict stays quiet), and
    # CATLIN_EXT_2X6 carries the default_lining the override replaces.
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
    # RM-S-HALL is now the source's single 181.02 sf "Hallway" again. Taking the centre
    # line out between y 22'-4" and 30'-10" left one polygonized face spanning the old
    # hall (east of x=18'), the landing outside the suite, and the open stair well — so
    # RM-S-LANDING (CSR414AAAA) and RM-S-STAIR (CSR410AAAA) were retired into this claim
    # rather than left as extra seeds in the same face, which would have billed the floor
    # three times. The well's east edge is guarded by RL-S-STAIR below.
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

# Electric radiant floor in the NW bathroom (2026-07-25). RM-S-BATH1 is the hall bath —
# see the tag note in this file's header — and it is the one bathroom on this storey that
# gets a warm floor. Same recipe as the two main-storey zones (main.py): 12 W/ft2 of 120V
# mat at a 3" serpentine, buried in the tile setting bed. `in_slab` is the mode name the
# enum has, not a claim about structure: this floor is FS-SECOND's I-joists and 3/4"
# plywood, and the mat lies in the thinset *above* the subfloor, which is neither of the
# two modes `Embed` can spell. CKT-FH-BATH1 and ED-S-BATH1-FH-STAT carry it.
#
# The zone is drawn to the fixtures, not the room. The clear face runs
# x 0'-0 5/8"..9'-11 3/8", y 26'-4 11/16"..35'-11 3/8" (itself an L — the NE corner past
# x=7'-7 3/8" stops at y=33'-3 3/8"), and the mat stops 4" off every wall. The de-overlap
# pass (plan/fixtures.py) put the WC on the west wall (x 0'-3"..2'-9", y 28'-9"..31'-3"),
# the lav on the east (x 8'-2"..9'-11", y 30'-0"..32'-0") and kept the shower pan at
# x 3'-6"..6'-6", y 31'-6"..34'-6", so the mat is now a south band (x 0'-5"..9'-7",
# y 26'-9"..28'-6", 16.0 ft2) with an east step up to the lav (x 7'-11"..9'-7",
# y 28'-6"..29'-9", 2.1 ft2) and a centre panel between WC and lav reaching up to the
# pan (x 3'-0"..7'-11", y 28'-6"..31'-3", 13.5 ft2), everything holding 3" off every
# fixture: 31.6 ft2. The strips north of the WC and west of the pan are left unheated
# rather than tying them in through a 3"-wide cable corridor.
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

# The hallway duct soffit (HRV + heat mains) — dashed on plan, framed in 3D. Its south end
# follows the band wall from 8'-8" to 9'-0"; the x-range is left alone (source 20.0->20.6,
# ours 19'-4"->20'-8", inside the 2" fidelity band).
# The hallway HVAC chase (plans/TODO.md: "2nd floor hallway dropped ceiling for HVAC").
# Widened and extended 2026-07-29 for the three-system HVAC design: it now encloses BOTH of
# System 1's ducts side by side — DU-S-HP-SUP at x=19'-4" and DU-S-HP-RET at x=20'-8", each
# 14"x8" (plan/mep.py DUCTS_HVAC_SECOND) — instead of the single 16"-wide box it was. The
# 14" drop clears an 8" duct plus its 2x4 framing and hangers with room for the boots that
# turn out through the bedroom walls.
#
# It runs y 6'-0" .. 34'-0": the south 3' is over RM-S-STUDY2, where EQ-S-HP1-AH sits above
# the ceiling and the trunk starts, so the box has to reach the unit's collars rather than
# stopping at the hall wall. A soffit polygon spanning rooms is expected (#40).
#
# LIGHTING TIE-IN: LR-S-HALL-GAP already runs the hall at x=18'-6" and x=21'-6", i.e. just
# outside both soffit edges — the shadow-gap strips wash the soffit's flanks, which is the
# effect the notes ask for and needs no new lighting here.
#
# WIDTH ARITHMETIC (2026-07-29). The box was 2'-8" = 32" in plan, which does not fit what
# it has to enclose once it is framed rather than drawn:
#   - framing loss, per side: 1 1/2" (the 2x2 ladder below) + 5/8" lining inset = 2 1/8",
#     so clear = plan width − 4 1/4".
#   - what has to fit: DU-S-HP-SUP at x=19'-4" and DU-S-HP-RET at x=20'-8", 14" wide each,
#     so their outer faces are 18'-9" and 21'-3" — 30" across, being 28" of duct plus the
#     2" gap between them that the hangers and the joint flanges live in.
#   32" plan − 4 1/4" = 27 3/4" clear, which is short of the 28" of bare duct alone.
# The box is now 35" — x 18'-6 1/2" .. 21'-5 1/2", still centred on 20'-0" between the two
# duct centrelines — giving 30 3/4" clear: the 30" it needs plus 3/8" a side to set the
# ducts in. It stays inside the hall (clear x 18'-2 3/4" .. 21'-8"), and the two
# LR-S-HALL-GAP strips at 18'-6"/21'-6" now sit 1/2" off each flank, which is a shadow gap
# rather than a coincident edge — the wash the notes ask for, if anything more literally.
# The soffit face elevation is unchanged at 7'-10": ED-S-HALL-CAN1/2/3 are set into it.
SOFFITS = [
    Soffit(uid="CSF601AAAA", tag="SF-S-DUCT",
           outline=(pt(ft(18, 6.5), ft(6)), pt(ft(21, 5.5), ft(6)),
                    pt(ft(21, 5.5), ft(34)), pt(ft(18, 6.5), ft(34))),
           drop=inch(14),
           framing=FramingSpec(member="2x2", spacing=inch(16))),
    # The west branch to the suite, carrying DU-S-HP-SUITE — rerouted 2026-07-30 onto the
    # short straight line: over D-S-SUITE and down the suite's own entry arm, instead of the
    # 2026-07-29 detour at y 19'-4"..21'-4" that crossed RM-S-SUITEBATH and its three
    # fixtures. The duct passes through W-S-C2B in the cripple zone above the door's header
    # (the 14" drop puts it at z ~7'-10"..9', over a ~7'-4" header top), which is exactly
    # where a branch should cross a bearing wall that is already broken by a door below.
    #
    # The soffit is the arm's ceiling — the arm walls' axes are y 12'-5" (W-S-CLN) and
    # 15'-11" (W-S-SBS), and the box sits at y 12'-8" .. 15'-8", 3" off each axis, the same
    # shadow-gap inset SF-S-DUCT keeps off the hall walls: an outline ON the wall lines
    # puts the ladder rails inside the walls' own stud zones (structural.member_interference
    # lit up with 25 soffit-vs-CSW143/144 pairs when it was drawn that way). x 12'-0"
    # (about D-S-SUITEBATH's east jamb — the leaf is x 10'-2"..12'-8" — so the box stops at
    # the bathroom door rather than running the arm's full depth; the grille is in its west
    # end face) .. 18'-6 1/2" (abutting SF-S-DUCT's west face, same 14" drop, so the two
    # read as one continuous box turning west). Both door heads under it (D-S-SUITE at
    # 6'-8", and the box's west face lands beside D-S-SUITEBATH) clear the 7'-10" soffit
    # face by over a foot.
    #
    # Width arithmetic, same rule as above: 36" plan − 4 1/4" framing/lining = 31 3/4"
    # clear against a single 10"-wide duct — room to spare, which the boot up to
    # REG-A-HP-WEST (plan/mep.py) is glad of.
    Soffit(uid="CSF6S1AAAA", tag="SF-S-SUITE",
           outline=(pt(ft(12), ft(12, 8)), pt(ft(18, 6.5), ft(12, 8)),
                    pt(ft(18, 6.5), ft(15, 8)), pt(ft(12), ft(15, 8))),
           drop=inch(14),
           framing=FramingSpec(member="2x2", spacing=inch(16))),
]

# Drawn to the main floor's *finished* well, the way FO-M-STAIR is drawn to the basement's:
# W-M-STRW's and W-M-C5's stair-side faces, W-M-STRS's north face extended east, and the exterior
# wall's inside face. That is both the shaft the flight climbs and the line the outer
# stringers bear on — an opening on the wall centrelines instead put the stringers inside
# the stud cavities and left the flight to be posted down (plans/TODO.md D3).
#
# This well is 7'-5 1/4" where the basement's is 7'-0", because the 2x6 walls here are
# thinner than the 12" concrete they stack on. Each flight is sized to its own storey's
# well rather than forcing one width on both, so both outer stringers land on a wall.
#
# Run, north to south (2026-07-28), the way FO-M-STAIR now is: north is W-M-N2's inside
# gwb face at y=35'-5 3/8", and the 9'-5" back from there is the IRC R311.7.6 36" landing
# plus seven 11" treads, so the south edge lands at 26'-0 3/8".
#
# This head runs 5 3/8" further north than FO-M-STAIR's, which stops on the basement
# concrete at 35'-0". That is the point of the 12" wall: only its outer 6" is under
# anything — the main-storey 2x6 stack lines its sheathing and insulation up with the
# concrete's outer face, so the studs sit at y 35'-6"..35'-11 1/2" — and this well is cut
# in the *second* floor deck, so the inner half of the concrete is free plan area to it.
# Deliberately NOT moved onto the source: it is drawn to the *main* storey's finished
# faces, so moving it means moving main.py.
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

# The beam that lets the centre line be open (2026-07-28).
#
# CLAUDE.md's house fact is that the x=18' line is a bearing line all the way from the
# footings to RB-HOUSE, and that opening it up *without a beam* dumps ~1.5 klf of ridge
# thrust into 5' knee walls that can take ~0.1. This does not open it up: the LVL is the
# bearing line for these 8'-6", and W-A-C2 lands on it.
#
# Load, per foot of beam, all of it collected on the x=18' line:
#   attic floor  FS-ATTIC, 18' tributary (half of each 18' I-joist span), 40 psf LL +
#                15 psf DL habitable                                        ~ 990 plf
#   roof         RB-HOUSE bears continuously on W-A-C1/C1B/C2 and takes half of each
#                18' rafter run either side, 18' tributary at the site's flat-roof snow
#                load Pf = 35 psf (0.7 x the 50 psf Pg in plan/site.py, at
#                Ce = Ct = Is = 1.0) + 15 psf DL
#                                                                           ~ 900 plf
#   walls        W-A-C2 above plus this storey's own plate                  ~  100 plf
#                                                                    total ~ 1,990 plf
# (The roof line read 810 plf at 30 psf until 2026-08-01 — a snow load this house does not
# have. Correcting it to Pf moves the beam, not the answer.)
# Over an 8'-6" clear span that is M = wL^2/8 = 18.0 ft-k and V = 8.5 k. Three plies of
# 1.75x11.875 LVL give Sx = 123 in^3 (26.7 ft-k at Fb = 2,600 psi) and 62 in^2 of shear
# area (11.8 k), and deflect 0.16" against the L/360 = 0.28" limit at E = 2.0e6 — still
# comfortably within capacity on all three. Same section and same ply count as RB-HOUSE,
# which keeps one LVL depth on the job.
#
# It bears on the ends of the wall segments it replaced — W-S-C2C south, W-S-C4B north —
# each of which needs a jack pack under it, and both stack onto the main-storey centre
# wall and down to the footings, so the reaction has somewhere to go.
# It is framed FLUSH, not dropped: `top_elevation` pins its top to the attic datum, which
# is top-of-joist, so the attic I-joists hang off it in face-mount hangers and its soffit
# lands on the 19'-0" plate line of the walls either side. That keeps the 9' ceiling
# unbroken across the hall — a dropped beam would hang its full 11-7/8" into the opening
# and leave 8'-0" of headroom under it. The default derivation cannot reach this: it drops
# a beam a joist depth below *its own* storey datum (ft(10) here), and this beam carries
# the floor of the storey above, not of its own.
BEAMS = [
    Beam(uid="CSBM01AAAA", tag="BM-S-HALL", start_node="N-S-C2C", end_node="N-S-C3D",
         size="3-1.75x11.875 LVL", bearing_refs=("W-S-C2C", "W-S-C4B"),
         top_elevation=ft(20)),
]

# Guards on the two open sides of the stair well. Both use the attic RL-A-STAIR product,
# post spacing and 42" height, ride the second-storey walking surface at ft(10) and are
# fascia mounted to the well rim — which on the east side is BM-S-HALL itself.
#
# Between them they leave exactly one gap: the flight's own throat. ST-M2S is a u-split
# turning left, so the *upper* flight arrives southbound on the west half of the well — the
# resolved treads run x 10'-3 3/8"..13'-9 3/4" — and you step off it onto the floor at the
# well's south edge. East of that throat the same south edge stands over the head of the
# lower flight, a ~9'-6" drop, and the east edge stands over that flight all the way to
# where W-S-C4B (RM-S-NCLOSET's west wall) picks the line back up at y=30'-10".
#
# Both moved north and swapped hands on 2026-07-28 with the well itself: the head guard was
# on the *west* of the throat while the flight arrived on the east, and the mirror put the
# throat on the west.
#
# The well's own coordinates are used, not the retired wall centrelines: these guards are
# drawn to FO-S-STAIR the way its bearing was.
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

# ST-M2S handrails (R311.7.8): one wall-mounted rail per flight, both graded by
# code.R311_7_8_handrail via `serves_stair`, and both raked along the flight's nosing line
# by the resolver (`top_height` is the R311.7.8.1 above-the-nosings datum, 34"-38").
#
# Placement reads off the resolved flights (u_split, turn left): the LOWER flight springs
# in the east lane (x 14'-2 1/4"..17'-8 5/8"), so its rail mounts on the well's east wall
# (W-M-C5's stair face at 17'-8 5/8") and runs the flight's own y-span — first riser at
# y 26'-0 3/8" to the lower-landing edge at 31'-10 3/8". The UPPER flight climbs back
# south in the west lane (x 10'-3 3/8"..13'-9 3/4"), rail on the well's west wall
# (W-M-STRW2's face at 10'-3 3/8"), upper-landing edge down to one going past the top
# riser (y 26'-10 3/8", the arrival edge). Each path sits 2" off its wall face — the
# bracket standoff — and `base_elevation` is only the off-flight fallback (the rail never
# leaves its flight). rail_count=1: a handrail is the one graspable rail, not a guard
# frame; role="handrail" keeps these out of the R312.1.3 guard-infill census.
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
                # The main floor's ceiling: this deck's underside *is* that ceiling, and
                # 5/8" board is what hangs there. Until it was authored a whole storey of
                # ceiling gypsum was missing from the order — the sheet take-off reads
                # `ceiling_below`, and nothing else in the plan says a ceiling exists at
                # all. Plain board, not type X: R302.13 reaches the floor over a basement,
                # not this one. Layered ceiling assemblies (channel, insulation, a separate
                # finish, as an authored stack) stay deferred — this is the sheet, billed,
                # not a ceiling-assembly schema. The living room's resilient channel rides
                # on it as CR-LIVING-CEIL-RC (plan/assemblies.py).
                ceiling_below=DeckLayer(material_ref="gwb", thickness=inch(0.625)),
                openings=("FO-S-STAIR",)),
]

# The suite bedroom's four "tudor" posts (plans/TODO.md §Hardwood): custom 6-1/8" square
# elm timbers standing in W-S-W3's stud line, faces flush with the drywall plane.
# Deliberately NOT a change to CATLIN_EXT_2X6 — each post is a deviation *within* the stud
# line, so the wall assembly, its framing counts and the sheathing plane are untouched.
# Geometry: the axis is the sheathing-ext plane (x=0); sheathing 1/2" + stud 5.5" + gwb
# 5/8" puts the 6.125" body from x=1/2" (back of the stud bay) to x=6-5/8" (drywall face),
# centre x=3-9/16". Standing on FS-SECOND's subfloor (10'-0 3/4"), cut 8'-11 1/4" to top
# out flush with the 9' plate; ordered as 10' sections and cut down. y-positions keep
# >6" clear of both WT-2736 ROs (y 11'-10 1/2"..14'-1 1/2" and 18'-6 1/2"..20'-9 1/2").
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
    # R311.7.6 36" minimum measured in the direction of travel.
    #
    # `turn_direction="left"`, the same hand as ST-B2M below it: the flight springs from the
    # main floor in the *east* lane (x 14'-2 1/4"..17'-8 5/8") and arrives on the second
    # floor in the *west* one (x 10'-3 3/8"..13'-9 3/4"). Both storeys' U-turns therefore
    # read the same way, and the stack alternates sides as one continuous run — east up to
    # main, west off it, east up to second, west off that.
    Stair(uid="CST702AAAA", tag="ST-M2S", floor_opening="FO-S-STAIR",
          from_storey="main", to_storey="second", width=ft(3, 6.375),
          layout="u_split_landing", run_direction="y", turn_direction="left",
          start=pt(ft(10, 3.375), ft(26, 0.375)), landing_depth=ft(3)),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *FLOOR_HEAT, *SOFFITS,
            *FLOOR_OPENINGS, *BEAMS, *STAIR_GUARDS, *STAIR_HANDRAILS, *FLOOR, *POSTS,
            *STAIRS]
