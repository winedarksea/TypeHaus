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
#   suite and plant-room doors. `W-S-C1..C4B` stays a continuous bearing stack (house fact,
#   CLAUDE.md), so those three breaks are modelled as *openings in* the wall — D-S-PLANT,
#   D-S-SUITE and O-S-HALLW — the way `main.py` already does with O-M-HALL / O-M-DRESS.
#   The source's single 181.02 sf "Hallway" therefore reads here as RM-S-HALL (east of the
#   bearing line) + RM-S-LANDING + RM-S-STAIR (west of it).
# - The source's south-wall openings are four 6'/5'-3" runs and its bearing-wall windows are
#   2'-8"; `preferences.toml` caps a bearing RO at 27" and a non-bearing one at 30". The
#   existing window *types* are kept and only their positions move onto the source openings.
# - `WIN-S-BATH-W` and `WIN-S-BATH-N` have no counterpart — the source draws no opening in
#   the west wall north of y=25'-8" and none in the north wall west of x=21'-10". Both are
#   kept for bathroom daylight.
# - `RM-S-BATH1` is the hall bath (the source's 80.73 sf "Bathroom"); the suite's own bath
#   is RM-S-SUITEBATH. It was tagged `RM-S-ENSUITE` until 2026-07-27, which it never was —
#   the rename ran through fixtures.py, mep.py, views.py, lighting.py and electrical.py.
from typehaus import (
    Alarm,
    AlarmKind,
    Door,
    DeckLayer,
    FloorHeat,
    FloorOpening,
    FloorSystem,
    JoistSpec,
    Node,
    Occupancy,
    RadiantSystem,
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
    Node(uid="CSN027AAAA", tag="N-S-C3B", position=pt(ft(18), ft(25))),
    Node(uid="CSN017AAAA", tag="N-S-C3", position=pt(ft(18), ft(26, 4))),
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
    # Stair shaft west line + the 2'x2' mechanical chase in the hall bath's NE corner
    Node(uid="CSN025AAAA", tag="N-S-BA1", position=pt(ft(10), ft(26, 4))),
    Node(uid="CSN026AAAA", tag="N-S-STR2", position=pt(ft(10), ft(25))),
    Node(uid="CSN035AAAA", tag="N-S-CH1", position=pt(ft(7, 8), ft(33, 4))),
    Node(uid="CSN036AAAA", tag="N-S-CH2", position=pt(ft(7, 8), ft(36))),
    Node(uid="CSN037AAAA", tag="N-S-CH3", position=pt(ft(10), ft(33, 4))),
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
    # Split at N-S-CH2, where the mechanical chase's west wall tees into the north wall.
    Wall(uid="CSW109AAAA", tag="W-S-N3", start_node="N-S-N2", end_node="N-S-CH2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N3"),
    Wall(uid="CSW153AAAA", tag="W-S-N3B", start_node="N-S-CH2", end_node="N-S-NW",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N3"),
    Wall(uid="CSW110AAAA", tag="W-S-W1", start_node="N-S-NW", end_node="N-S-W1",
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
    Wall(uid="CSW116AAAA", tag="W-S-C3", start_node="N-S-C2C", end_node="N-S-C3B",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C4"),
    Wall(uid="CSW136AAAA", tag="W-S-C3C", start_node="N-S-C3B", end_node="N-S-C3",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C4B"),
    Wall(uid="CSW117AAAA", tag="W-S-C4", start_node="N-S-C3", end_node="N-S-C3D",
         assembly="CATLIN_INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C5"),
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
    # RM-S-SUITEBATH's west + south walls carry its drain stack, so both are the 2x6
    # plumbing assembly: `advisory.wet_wall_depth` reads preferences.toml's
    # `drain_stack_required_structure_in = 5.5`, which a 2x4 partition cannot hold.
    Wall(uid="CSW142AAAA", tag="W-S-DC2", start_node="N-S-D3", end_node="N-S-D4",
         assembly="INT_2X6_PLUMBING", top=ft(9)),
    Wall(uid="CSW143AAAA", tag="W-S-CLN", start_node="N-S-D2", end_node="N-S-C2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW144AAAA", tag="W-S-SBS", start_node="N-S-D3", end_node="N-S-C2B",
         assembly="INT_2X6_PLUMBING", top=ft(9)),
    Wall(uid="CSW145AAAA", tag="W-S-SN1", start_node="N-S-W2", end_node="N-S-V1",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW146AAAA", tag="W-S-SN2", start_node="N-S-V1", end_node="N-S-D4",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW147AAAA", tag="W-S-SN3", start_node="N-S-D4", end_node="N-S-C2C",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW148AAAA", tag="W-S-VE", start_node="N-S-V1", end_node="N-S-V2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW132AAAA", tag="W-S-BD-N", start_node="N-S-W1", end_node="N-S-V2",
         assembly="INT_2X6_PLUMBING", top=ft(9)),
    Wall(uid="CSW149AAAA", tag="W-S-BD-N1B", start_node="N-S-V2", end_node="N-S-BA1",
         assembly="INT_2X6_PLUMBING", top=ft(9)),
    Wall(uid="CSW133AAAA", tag="W-S-BD-N2", start_node="N-S-STR2", end_node="N-S-C3B",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW134AAAA", tag="W-S-BA-E", start_node="N-S-N2", end_node="N-S-CH3",
         assembly="INT_2X6_PLUMBING", top=ft(9)),
    Wall(uid="CSW150AAAA", tag="W-S-BA-E1B", start_node="N-S-CH3", end_node="N-S-BA1",
         assembly="INT_2X6_PLUMBING", top=ft(9)),
    Wall(uid="CSW137AAAA", tag="W-S-BA-E2", start_node="N-S-BA1", end_node="N-S-STR2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    # 2'x2' mechanical chase in the hall bath's NE corner (source void x 8'-2 3/4"..
    # 10'-2 3/4", y 33'-6"..35'-6"), which is what makes RM-S-BATH1 the source's
    # L-shaped 80.73 sf bathroom. Its east side is the stair-shaft wall above.
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
    Door(uid="CSD201AAAA", tag="D-S-BED1", host="W-S-BW1", type_ref="DT-INT30",
         position=from_node("N-S-B1", ft(4, 3.1875)), flip_swing=True),      # y 15'-2"
    Door(uid="CSD202AAAA", tag="D-S-BED2", host="W-S-BW2", type_ref="DT-INT30",
         position=from_node("N-S-B2", ft(4, 10))),                       # y 24'-1"
    Door(uid="CSD203AAAA", tag="D-S-BED3", host="W-S-BW3", type_ref="DT-INT30",
         position=from_node("N-S-B3", ft(0, 8))),                        # y 28'-11"
    Door(uid="CSD204AAAA", tag="D-S-STUDY2", host="W-S-SS1", type_ref="DT-INT30",
         position=from_node("N-S-C1", ft(1, 0.625))),                    # x 20'-3 5/8"
    # Three doors through the centre bearing line, on the source's own gaps. Each takes a
    # header exactly like O-M-HALL / O-M-DRESS one storey down; the wall itself is unbroken.
    # Full-lite glass leaf admits daylight from the south-facing plant room into the hall.
    Door(uid="CSD212AAAA", tag="D-S-PLANT", host="W-S-C1", type_ref="DT-INT30-GLASS",
         position=from_node("N-S-S1", ft(3, 2.5))),                      # y 4'-5 1/2"
    Door(uid="CSD206AAAA", tag="D-S-SUITE", host="W-S-C2B", type_ref="DT-INT32",
         position=from_node("N-S-C2", ft(0, 4.875))),                    # y 14'-1 7/8"
    RoughOpening(uid="CSD216AAAA", tag="O-S-HALLW", host="W-S-C4",
                 position=from_node("N-S-C3", ft(0, 9)), width=ft(3),
                 height=ft(6, 8)),                                       # y 28'-7"
    # West block
    # The walk-in's 4'-7 1/8" source opening, cased. Not a DT-INT56 bifold, which is the
    # obvious stock door for a closet this wide and would keep `advisory.window_size_variety`
    # at its historical 8 (that check counts every RoughOpening as a glazing size): the
    # resolver draws a bifold's clearance as a full 4'-8" quarter-disc swing, which reaches
    # across the whole suite arm and reads as four spurious `integrity.door_swing_conflict`
    # findings. An opening with no leaf is both the truer model and the quieter one.
    RoughOpening(uid="CSD213AAAA", tag="O-S-CLOSET", host="W-S-CLN",
                 position=from_node("N-S-D2", ft(1, 10)), width=ft(4, 7),
                 height=ft(6, 8)),                                       # x 13'-9"
    # The source's gap starts hard against the corner at x=9'-10 11/16"; ours starts 3"
    # further east so the leaf's king stud clears W-S-DC2's corner pack instead of
    # pinwheeling through it (test_wall_corner_and_opening_framing).
    Door(uid="CSD214AAAA", tag="D-S-SUITEBATH", host="W-S-SBS", type_ref="DT-INT30",
         position=from_node("N-S-D3", ft(0, 6.5))),                      # x 11'-5"
    RoughOpening(uid="CSD215AAAA", tag="O-S-VANITY", host="W-S-VE",
                 position=from_node("N-S-V1", ft(0, 3)), width=ft(2, 8),
                 height=ft(6, 8)),                                       # y 23'-11"
    Door(uid="CSD208AAAA", tag="D-S-BATH1", host="W-S-BD-N1B", type_ref="DT-INT30",
         position=from_node("N-S-V2", ft(1, 4.5))),                      # x 8'-6"
    Door(uid="CSD217AAAA", tag="D-S-NCLOSET", host="W-S-CLN-S", type_ref="DT-INT30",
         position=from_node("N-S-C3D", ft(0, 8.5))),                     # x 19'-11 1/2"
    # Open stair head onto the landing (cased, no door).
    RoughOpening(uid="CSD209AAAA", tag="O-S-STAIRTOP", host="W-S-BD-N2",
                 position=from_node("N-S-STR2", ft(0, 6)), width=ft(6),
                 height=ft(6, 8)),
    # Balcony door — ONE opening in the source (x 18'-8"..23'-11", 5'-3", drawn with two
    # leaves), east of the centre line, not the pair of them the port had flanking it.
    # DT-FRENCH36 is itself a double-swing: one Door, two leaves, a centre mullion. So the
    # count and the kind match the source and only the width falls short — 3'-0" against
    # 5'-3", because the catalog carries one type per width family (CLAUDE.md) and has no
    # wider double-swing leaf. Two of them side by side would be 6'-0" of RO whose king and
    # jack studs interpenetrate, which is what the port's pair became once both moved here.
    Door(uid="CSD211AAAA", tag="D-S-DECK-E", host="W-S-S2", type_ref="DT-FRENCH36",
         position=from_node("N-S-S1", ft(1, 10))),                       # x 21'-4"
    # Windows — east wall, on the source's four 2'-8" openings (we build 27", the bearing cap)
    Window(uid="CSX314AAAA", tag="WIN-S-STUDY3", host="W-S-E1", type_ref="WT-2736",
           position=from_node("N-S-SE", ft(2, 10.5)), sill_height=ft(2, 6)),  # y 4'-0"
    Window(uid="CSX301AAAA", tag="WIN-S-BED1", host="W-S-E2", type_ref="WT-2736",
           position=from_node("N-S-E1", ft(4, 2.5)), sill_height=ft(3)),      # y 14'-4"
    Window(uid="CSX302AAAA", tag="WIN-S-BED2", host="W-S-E3", type_ref="WT-2736",
           position=from_node("N-S-E2", ft(4, 2.5)), sill_height=ft(3)),      # y 23'-4"
    Window(uid="CSX303AAAA", tag="WIN-S-BED3", host="W-S-E4", type_ref="WT-2736",
           position=from_node("N-S-E3", ft(4, 2.5)), sill_height=ft(3)),      # y 32'-4"
    # West suite (bearing wall) — source openings at y 12'-7" and 19'-4"
    Window(uid="CSX304AAAA", tag="WIN-S-SUITE1", host="W-S-W3", type_ref="WT-2736",
           position=from_node("N-S-W2", ft(8, 2.5)), sill_height=ft(3)),      # y 13'-0"
    Window(uid="CSX305AAAA", tag="WIN-S-SUITE2", host="W-S-W3", type_ref="WT-2736",
           position=from_node("N-S-W2", ft(1, 6.5)), sill_height=ft(3)),      # y 19'-8"
    # Plant room — south glazing (non-bearing: WT-3036 row), centred in the source's two
    # 6'-0" openings (x 2'-3"..8'-3" and 10'-1"..16'-1").
    Window(uid="CSX306AAAA", tag="WIN-S-PLANT1", host="W-S-S1", type_ref="WT-3036",
           position=from_node("N-S-SW", ft(4, 1)), sill_height=ft(2)),        # x 5'-4"
    Window(uid="CSX307AAAA", tag="WIN-S-PLANT2", host="W-S-S1", type_ref="WT-3036",
           position=from_node("N-S-SW", ft(12, 1)), sill_height=ft(2)),       # x 13'-4"
    # The plant room's west window is on W-S-W4, a bearing wall, so it takes the 27" bearing
    # type and not the 30" south-glazing one — "resize windows to fit the grid" (CLAUDE.md).
    Window(uid="CSX308AAAA", tag="WIN-S-PLANT3", host="W-S-W4", type_ref="WT-2736",
           position=from_node("N-S-W3", ft(2, 10.5)), sill_height=ft(2)),     # y 5'-0"
    # Study 2's south pair, both inside the source's single 6'-0" opening at 28'-10"..34'-10".
    Window(uid="CSX309AAAA", tag="WIN-S-STUDY1", host="W-S-S2", type_ref="WT-3036",
           position=from_node("N-S-S1", ft(10, 9)), sill_height=ft(2, 6)),    # x 30'-0"
    Window(uid="CSX310AAAA", tag="WIN-S-STUDY2", host="W-S-S2", type_ref="WT-3036",
           position=from_node("N-S-S1", ft(14, 9)), sill_height=ft(2, 6)),    # x 34'-0"
    # Baths + north. The source draws no opening in the north wall west of x=21'-10" and
    # none in the west wall north of y=25'-8"; WIN-S-BATH-N/W are kept anyway so the hall
    # bath has daylight, and are the storey's only two openings with no source counterpart.
    Window(uid="CSX311AAAA", tag="WIN-S-BATH-N", host="W-S-N3B", type_ref="WT-1424",
           position=from_node("N-S-CH2", ft(0, 3.875)), sill_height=ft(4)),       # x 3'-0"
    Window(uid="CSX312AAAA", tag="WIN-S-BATH-W", host="W-S-W1", type_ref="WT-1424",
           position=from_node("N-S-NW", ft(4, 1)), sill_height=ft(4)),
    Window(uid="CSX313AAAA", tag="WIN-S-HALL-N", host="W-S-N1", type_ref="WT-3036",
           position=from_node("N-S-NE", ft(5, 5)), sill_height=ft(3)),        # x 29'-4"
]

ROOMS = [
    Room(uid="CSR401AAAA", tag="RM-S-PLANT", seed=pt(ft(9), ft(4)),
         occupancy=Occupancy.LIVING, floor_finish="tile"),
    Room(uid="CSR402AAAA", tag="RM-S-STUDY2", seed=pt(ft(27), ft(4)),
         occupancy=Occupancy.OFFICE, floor_finish="oak"),
    Room(uid="CSR403AAAA", tag="RM-S-BED1", seed=pt(ft(29), ft(13, 6)),
         occupancy=Occupancy.BEDROOM, floor_finish="carpet"),
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
    # The west half of the source's one big "Hallway": the landing outside the suite that
    # links the stair head, the vanity alcove and the hall bath.
    Room(uid="CSR414AAAA", tag="RM-S-LANDING", seed=pt(ft(13), ft(23, 6)),
         occupancy=Occupancy.HALLWAY, floor_finish="lvp"),
    Room(uid="CSR408AAAA", tag="RM-S-BATH1", seed=pt(ft(5), ft(31)),
         occupancy=Occupancy.BATHROOM, floor_finish="lvp"),
    Room(uid="CSR409AAAA", tag="RM-S-HALL", seed=pt(ft(20), ft(20)),
         occupancy=Occupancy.HALLWAY, floor_finish="lvp"),
    # Both walk-ins are carpet — a closet floor is never walked on in shoes, and carpet
    # continues out of the bedroom it opens off.
    Room(uid="CSR415AAAA", tag="RM-S-NCLOSET", seed=pt(ft(20), ft(33)),
         occupancy=Occupancy.STORAGE, floor_finish="carpet"),
    Room(uid="CSR410AAAA", tag="RM-S-STAIR", seed=pt(ft(14, 6), ft(31)),
         occupancy=Occupancy.STAIR, floor_finish="oak"),
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
                    pt(ft(7, 11), ft(31, 3)), pt(ft(3), ft(31, 3)),
                    pt(ft(3), ft(28, 6)), pt(ft(0, 5), ft(28, 6))),
              system=RadiantSystem.ELECTRIC, spacing=inch(3), embed=in_slab(inch(0.5)),
              stat=pt(ft(1, 6), ft(32))),
]

# The hallway duct soffit (HRV + heat mains) — dashed on plan, framed in 3D. Its south end
# follows the band wall from 8'-8" to 9'-0"; the x-range is left alone (source 20.0->20.6,
# ours 19'-4"->20'-8", inside the 2" fidelity band).
SOFFITS = [
    Soffit(uid="CSF601AAAA", tag="SF-S-DUCT",
           outline=(pt(ft(19, 4), ft(9)), pt(ft(20, 8), ft(9)),
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
# Deliberately NOT moved onto the source: it is drawn to the *main* storey's finished
# faces, so moving it means moving main.py.
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

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *FLOOR_HEAT, *SOFFITS,
            *FLOOR_OPENINGS, *FLOOR, *STAIRS]
