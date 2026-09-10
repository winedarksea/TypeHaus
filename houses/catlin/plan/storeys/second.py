# haus: editable
# Second floor — EXT_2X6 on the same sheathing plane (2x6 on every framed
# storey), three east bedrooms, west suite, plant room + study south, duct soffit (WP3.1).
#
# Every interior partition is set to the Sensopia survey `catlin_floorplan/Colin House -
# 2nd Floor.svg` (path #0, 74.7029 px/m, rounded to the nearest inch). Fidelity policy:
# interior partitions move to the source; exterior envelope, x=18' bearing line and the
# 16" framing module do not. `preferences.toml`'s `[[underlay]]` is calibrated to the same
# polygon so `haus render --view plan` overlays the survey for comparison.
#
# Known, deliberate divergences from the source:
# - The centre line's big break (y=22'-4"..30'-10") carries no wall at all —
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
    FloorHeat,
    FloorOpening,
    FramingSpec,
    HumidityClass,
    Layer,
    LayerFunction,
    LayerMaterial,
    Node,
    Occupancy,
    RadiantSystem,
    Railing,
    RailingKind,
    Post,
    Room,
    RoughOpening,
    Soffit,
    SoffitOpening,
    Stair,
    StructuralRole,
    Wall,
    WallLiningException,
    WallPaneling,
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
    Node(uid="CSN012AAAA", tag="N-S-W1", position=pt(ft(0), ft(26, 6))),
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
    Node(uid="CSN034AAAA", tag="N-S-V2", position=pt(ft(5, 10.5), ft(26, 6))),
    # Stair shaft west line
    Node(uid="CSN025AAAA", tag="N-S-BA1", position=pt(ft(10), ft(26, 6))),
    # Plain flush split on the east wall: used to be the mechanical chase's SE
    # corner (N-S-CH3); kept as its own node so W-S-BA-E1B's wall_ref in fixtures.py (the
    # hall-bath lav) doesn't move now that the chase itself has moved to the NW corner.
    Node(uid="CSN038AAAA", tag="N-S-BA-SPLIT", position=pt(ft(10), ft(33, 4))),
    # The mechanical chase moved NE -> NW corner of the hall bath to stack on
    # RM-M-MECH below. N-S-CH1 is its inner (SE) corner; N-S-CH2/CH3 tee into the exterior
    # north/west walls.
    #
    # Both south corners came 3 1/8" south on 2026-08-21, off the 33'-4" line RM-M-MECH's
    # own south wall still holds below. That is exactly the offset that lands W-S-CH-S's
    # bathroom face on y 32'-10 1/2" — FX-S-BATH1-SH's apron line, and now
    # FURN-S-BATH1-SHELF's front too — so the room's whole north band is one straight line
    # instead of a 3 1/8" jog. It buys two real things beyond the line: the shaft's clear
    # depth goes 1'-11" -> 2'-2 1/8" (this is the house's basement-to-attic pipe highway,
    # and it was the tightest it has ever needed to be), and W-S-CH-W now runs the tub's
    # full 30" instead of stopping 3 1/8" short of its front, so the insert's west flange
    # finally has stud behind all of it.
    #
    # What it costs, and this one was not cheap: W-S-W1 lays its studs from N-S-CH3, so
    # moving that node re-phased the whole wall's grid by 3 1/8" — and a grid is a property
    # of the node, not of the openings on it, so no window move can put it back
    # (structural.window_framing_module says exactly that in its own fix hint). The house
    # spent the west facade's 31'-4" column on this: WIN-S-BATH-W rides south to the new
    # bay centre at 31'-0 7/8" and no longer stacks on WIN-M-MUD, which stays at 31'-4"
    # because it is centred on FURN-M-MUD-BENCH's aisle. The west face now stacks four
    # exact columns farther south; this constrained service group remains a 3 1/8"
    # near-column (houses/catlin/CLAUDE.md, Facade rules). It also takes 3 1/8" out
    # of the only standing room in front of the shaft: the floor between FX-S-BATH1-WC's
    # clearance and the chase face is 1'-7 1/4" now, not 1'-10 3/8".
    Node(uid="CSN035AAAA", tag="N-S-CH1", position=pt(ft(2, 9), ft(33, 0.875))),
    Node(uid="CSN036AAAA", tag="N-S-CH2", position=pt(ft(2, 9), ft(36))),
    Node(uid="CSN037AAAA", tag="N-S-CH3", position=pt(ft(0), ft(33, 0.875))),
]

# North/south walls below carry the board & batten `layer_materials=` override — see the
# note above WALLS in plan/storeys/main.py, and the Material in plan/assemblies.py.
WALLS = [
    # --- exterior loop (2x6, same stack as main) -------------------------------
    # The plant room's two exterior walls carry PLANT_EXT_2X6_HUMID, not EXT_2X6:
    # same stack outboard of the sheathing, a sealed PVC/membrane liner inboard of the
    # studs (plan/assemblies.py, notes/plant_room.md). `alignment=face("sheathing-ext")` is
    # unchanged on purpose — the sheathing datum does not move (decision #43) and the liner
    # grows into the room, exactly as W-B-CS does for the sauna. `interior_room` is what
    # names which face the liner lands on; without it an asymmetric wall would take the
    # component's outward sign and could line the wrong side.
    Wall(uid="CSW101AAAA", tag="W-S-S1", start_node="N-S-SW", end_node="N-S-S1",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="PLANT_EXT_2X6_HUMID", alignment=face("sheathing-ext"), top=ft(9),
         interior_room="RM-S-PLANT",
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-S1"),
    Wall(uid="CSW102AAAA", tag="W-S-S2", start_node="N-S-S1", end_node="N-S-SE",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-S2"),
    Wall(uid="CSW103AAAA", tag="W-S-E1", start_node="N-S-SE", end_node="N-S-E1",
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E1"),
    Wall(uid="CSW102BAAA", tag="W-S-E2", start_node="N-S-E1", end_node="N-S-E2",
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E1"),
    # stacks_on repointed to W-M-E1: main.py merged W-M-E1/E2 into one wall
    # for WIN-M-EAST-MID, retiring the W-M-E2 tag. The resolver links only one upper wall
    # per lower wall, and W-S-E1 already claims that slot, so this segment's own
    # STOREY_STACK/WALL_FOUNDATION boundary condition is dropped rather than merely
    # repointed — see the note on the merged wall in main.py.
    Wall(uid="CSW104AAAA", tag="W-S-E3", start_node="N-S-E2", end_node="N-S-E3",
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E1"),
    Wall(uid="CSW105AAAA", tag="W-S-E4", start_node="N-S-E3", end_node="N-S-NE",
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E1"),
    Wall(uid="CSW107AAAA", tag="W-S-N1", start_node="N-S-NE", end_node="N-S-B5",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N1"),
    # Re-pointed W-M-N1 -> W-M-N1B: the main storey's north wall split at
    # x=24'-4" for RM-M-PANTRY's east partition, and this segment (x 21'-11"..18'-0") sits
    # entirely under the WESTERN half. Left naming W-M-N1 it would have been one of two
    # authored tiebreakers for the same lower wall, and the resolver links only one upper
    # wall per lower — so the segment actually over it would have lost the edge.
    Wall(uid="CSW135AAAA", tag="W-S-N1B", start_node="N-S-B5", end_node="N-S-N1",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N1B"),
    Wall(uid="CSW108AAAA", tag="W-S-N2", start_node="N-S-N1", end_node="N-S-N2",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N2"),
    # Split at N-S-CH2, where the mechanical chase's east wall tees into the north wall
    # (moved to the NW corner 2026-07-28 — see the node comment above).
    Wall(uid="CSW109AAAA", tag="W-S-N3", start_node="N-S-N2", end_node="N-S-CH2",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N3"),
    Wall(uid="CSW153AAAA", tag="W-S-N3B", start_node="N-S-CH2", end_node="N-S-NW",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N3B"),
    # Split at N-S-CH3, where the chase's south wall tees into the west wall
    #.
    Wall(uid="CSW154AAAA", tag="W-S-W1B", start_node="N-S-NW", end_node="N-S-CH3",
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-W1B"),
    Wall(uid="CSW110AAAA", tag="W-S-W1", start_node="N-S-CH3", end_node="N-S-W1",
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-W1"),
    Wall(uid="CSW111AAAA", tag="W-S-W2", start_node="N-S-W1", end_node="N-S-W2",
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-W2"),
    Wall(uid="CSW112AAAA", tag="W-S-W3", start_node="N-S-W2", end_node="N-S-W3",
         assembly="EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
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
         assembly="INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C1"),
    Wall(uid="CSW138AAAA", tag="W-S-C2B", start_node="N-S-C2", end_node="N-S-C2B",
         assembly="INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C2"),
    Wall(uid="CSW139AAAA", tag="W-S-C2C", start_node="N-S-C2B", end_node="N-S-C2C",
         assembly="INT_2X6_BRG", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-C3"),
    # y 22'-4" .. 30'-10" IS NOT A WALL — it is the BM-S-HALL flitch of LVL below.
    # W-S-C3 / W-S-C3C / W-S-C4 used to stand here; the whole 8'-6" is now open so the
    # hall, the landing and the stair well read as one room. The bearing
    # stack is unbroken because the beam is *in* it: see BEAMS below.
    Wall(uid="CSW140AAAA", tag="W-S-C4B", start_node="N-S-C3D", end_node="N-S-N1",
         assembly="INT_2X6_BRG", top=ft(9),
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
    # ** MEASURED AND NOT TAKEN. ** W-S-SS1 lays out from N-S-C1, which is off
    # the module, and D-S-STUDY2 — a bare RoughOpening in it — has no legal station at that
    # phase at all: `structural.door_framing_module` reports UNKNOWN for it. An
    # `INT_2X4_PARTITION_LINE` variant (same assembly, `layout_origin="line"`) was built and
    # tried; it does what it was supposed to, opening a station at 24" with the node and
    # every neighbour untouched. It was reverted anyway: at 24" the opening's king studs on
    # BOTH sides land in CSF601's soffit bottom plate, taking
    # `structural.member_interference` from one overlap to three. Two pieces of wood in the
    # same place is a worse answer than one extra cut stud, so the UNKNOWN stands and says so.
    Wall(uid="CSW120AAAA", tag="W-S-SS1", start_node="N-S-C1", end_node="N-S-B1",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    # ** W-S-SS2 IS INT_2X4_RC, AND THE CHANNEL IS ON THE NORTH FACE. **
    # RM-S-BED1 (sleeping) on the north, RM-S-STUDY2 (office) on the south — the one
    # bedroom-facing partition left on the plain preset when INT_2X4_PARTITION lost its
    # cavity that day. Same retype the five walls below took on 2026-08-30, same two
    # authored fields, same reasoning; read that block for why `alignment` is not optional.
    #
    # ** WHICH FACE GETS THE CHANNEL IS NOT A COIN FLIP HERE — IT IS THE STAIR. ** Everything
    # on this wall's SOUTH face is spoken for: ST-S2A's flight runs along it (its north face
    # IS this wall), `ledger-W-S-SS2-stringer-1` is a 2x10 lag-fastened to it, the R311.7.8
    # handrail is mounted on it, and `plan/storeys/attic.py` defines a void boundary as
    # literally "W-S-SS2's south gwb face". Two things follow, and either alone settles it:
    #   1. The channel-side face moves outboard 1/2". On the south that is INTO a stair well
    #      cut to EXACTLY 3'-0", which would leave 35 1/2" against R311.7.1's 36" minimum —
    #      a code FAIL bought for nothing.
    #   2. A stringer ledger and a handrail lag-screwed THROUGH resilient channel short it
    #      out. A channel bridged by fasteners is a channel that has stopped working, and it
    #      is also the wrong way to hang a stair.
    # So the channel faces RM-S-BED1. Acoustically that is a free choice — decoupling one
    # leaf works whichever leaf it is — and the 1/2" comes out of BED1's real width, which
    # `resolve/rooms.py` does not record (it polygonises from AXES and the axis does not
    # move under this alignment, so no area, glazing or egress verdict changes).
    # Nothing is hosted on either face: no device, fixture, luminaire or MEP run names this
    # wall, so unlike the 2026-08-30 block there is nothing to follow the face.
    Wall(uid="CSW121AAAA", tag="W-S-SS2", start_node="N-S-B1", end_node="N-S-E1",
         assembly="INT_2X4_RC", interior_room="RM-S-BED1", top=ft(9),
         alignment=face("stud-ext", offset=inch(-1.75))),
    # --- east bedroom block ------------------------------------------------------
    #
    # ** THE FIVE SLEEPING-SIDE PARTITIONS ARE INT_2X4_RC. ** They were
    # INT_2X4_PARTITION, then at STC 36 with a batt in it — a bedroom-to-bedroom wall you
    # can hold a conversation through, and three corridor walls between the stair head and
    # every bedroom door. (That preset is UNINSULATED and STC 34 since 2026-08-31, which
    # only sharpens the argument for this retype: there is no batt left to fall back on.)
    # INT_2X4_RC is the same 2x4 stud and the same 5/8" board with 1/2" resilient channel on
    # ONE face: STC 48, twelve points, and 12 points is the difference between "audible" and
    # "not a nuisance" on every published scale. W-S-BW4 joined them on the HP1 move (see
    # its own block below) — geometry, not acoustics, is what forced it.
    #
    # Two things have to be authored or the retype moves the framing.
    #
    # `alignment` — the assembly is ASYMMETRIC (0.625 gwb + 0.5 channel + 3.5 stud +
    # 0.625 gwb = 5.25", against the partition's symmetric 4.75"), so the default centred
    # alignment would put the axis at 2.625" from the channel face and the studs 0.25" off
    # the node line. `face("stud-ext", offset=inch(-1.75))` puts the axis 2.875" in — the
    # stud layer's own centre — so every stud stands exactly where it stood before and every
    # stacking, opening and interference verdict on this block is unchanged.
    #
    # `interior_room` — layer 0 is the resilient-channel face, and which side gets it is an
    # acoustic decision the geometry cannot make. The corridor is the noise source for
    # BW1/2/3 (stair head, three doors, one landing), so the channel faces the hall; between
    # two bedrooms the channel goes on the lower-numbered one, arbitrarily but consistently.
    # It is a Room reference rather than a flip so that swapping the nodes cannot silently
    # invert it.
    #
    # What moves: the channel-side face, by 1/2". Room AREAS do not change at all —
    # `resolve/rooms.py` polygonises from wall AXES and insets only by lining, so wall
    # thickness never enters and R303.1 / R304 / egress are untouched. Four wall-mounted
    # devices follow the face (plan/electrical.py). The rooms lose 1/2" of real width the
    # model does not record.
    Wall(uid="CSW122AAAA", tag="W-S-BW1", start_node="N-S-B1", end_node="N-S-B2",
         assembly="INT_2X4_RC", interior_room="RM-S-HALL", top=ft(9),
         alignment=face("stud-ext", offset=inch(-1.75))),
    Wall(uid="CSW123AAAA", tag="W-S-BW2", start_node="N-S-B2", end_node="N-S-B3",
         assembly="INT_2X4_RC", interior_room="RM-S-HALL", top=ft(9),
         alignment=face("stud-ext", offset=inch(-1.75))),
    Wall(uid="CSW124AAAA", tag="W-S-BW3", start_node="N-S-B3", end_node="N-S-B4",
         assembly="INT_2X4_RC", interior_room="RM-S-HALL", top=ft(9),
         alignment=face("stud-ext", offset=inch(-1.75))),
    # W-S-BW4 is RC too, and the reason is GEOMETRIC before it is acoustic. SF-S-HP1 now
    # spans this wall and W-S-BW3 both: BW3 (RC, channel to the hall) puts the hall's east
    # finished face at 21'-8 1/8", and BW4 as a plain partition put the closet's at
    # 21'-8 5/8". A box drawn to both would jog 1/2" at y=30'-10", and `_rectangle` returns
    # None on a non-rectangle — sending EVERY occupant of the box to UNKNOWN. The
    # alternative, drawing to the wider face, leaves a 1/2" ledge.
    # Channel on the RM-S-NCLOSET side is forced as well: FURN-S-BED3-WARD stands 0.113"
    # off the BED3 face and has nowhere to go. Stated plainly: this NARROWS the closet by
    # 1/2", to 40 3/4". The STC 34 -> 48 next to a bedroom now sharing a wall with the air
    # handler is the bonus, not the argument.
    Wall(uid="CSW125AAAA", tag="W-S-BW4", start_node="N-S-B4", end_node="N-S-B5",
         assembly="INT_2X4_RC", interior_room="RM-S-NCLOSET", top=ft(9),
         alignment=face("stud-ext", offset=inch(-1.75))),
    Wall(uid="CSW126AAAA", tag="W-S-BD1", start_node="N-S-B2", end_node="N-S-E2",
         assembly="INT_2X4_RC", interior_room="RM-S-BED1", top=ft(9),
         alignment=face("stud-ext", offset=inch(-1.75))),
    Wall(uid="CSW127AAAA", tag="W-S-BD2", start_node="N-S-B3", end_node="N-S-E3",
         assembly="INT_2X4_RC", interior_room="RM-S-BED2", top=ft(9),
         alignment=face("stud-ext", offset=inch(-1.75))),
    # North-centre closet (source 30.853 / 21.898), off the hall's north end.
    Wall(uid="CSW141AAAA", tag="W-S-CLN-S", start_node="N-S-C3D", end_node="N-S-B4",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- west block: walk-in, suite, suite bath, vanity alcove ------------------
    Wall(uid="CSW129AAAA", tag="W-S-DC1", start_node="N-S-D1", end_node="N-S-D2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    # RM-S-SUITEBATH's west wall carries the WC's drain stack, so it is the staggered
    # wet-wall assembly (2x4 studs on 2x6 plates, 5.5" continuous cavity):
    # `advisory.wet_wall_depth` reads preferences.toml's
    # `drain_stack_required_structure_in = 5.5`, which a 2x4 partition cannot hold. It stays
    # this depth for a real reason beyond FX-S-SUITEBATH-WC's flange: `checks/mep/
    # plumbing_dwv.py::wet_wall_depth` keys off `Fixture.wall_ref`, not off any actually
    # modelled `PipeRun` — no `PipeRun.wall_refs` names DC2 or SBS at all, so this is planning
    # allowance, not a real chase a 2x4-plus-resilient-channel retype could borrow room from.
    Wall(uid="CSW142AAAA", tag="W-S-DC2", start_node="N-S-D3", end_node="N-S-D4",
         assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(9)),
    Wall(uid="CSW143AAAA", tag="W-S-CLN", start_node="N-S-D2", end_node="N-S-C2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    # South wall — plain 2x4. Nothing actually backs onto this wall: the lav
    # that used to point its `wall_ref` here for the depth allowance stands against W-S-SN3
    # instead (10.5" north of its centreline, `plan/fixtures.py`'s `FX-S-SUITEBATH-LAV`), and
    # the `wall_ref` moved there with it, so `advisory.wet_wall_depth` no longer reads this
    # wall at all.
    Wall(uid="CSW144AAAA", tag="W-S-SBS", start_node="N-S-D3", end_node="N-S-C2B",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    # The suite's north wall: RM-S-SUITE (sleeping) on one face, the vanity alcove and the
    # suite bath on the other. Both runs are the library's staggered-stud partition (2x4
    # studs alternating on 2x6 plates, 3.5" fiberglass) rather than the house's default
    # single-stud INT_2X4_PARTITION, because a wall whose far face carries a vanity and a
    # bath is the one the sleeper hears through — the staggered studs decouple the two
    # faces even without a second gypsum layer (`library/assemblies.py`, no STC claimed,
    # a comparable single-layer build lists around STC 48 against the partition's 34).
    # Single 5/8" gypsum each face since 2026-08-30 (was two): the double layer only buys
    # a few more points over the staggered studs' own decoupling, at a gypsum-heavy cost
    # (`prices.toml`), so it was the more expensive half of the assembly to cut, not the
    # fiberglass. It is 6.75" wide against the partition's 4.75", which the suite and the
    # vanity split.
    Wall(uid="CSW145AAAA", tag="W-S-SN1", start_node="N-S-W2", end_node="N-S-V1",
         assembly="INT_2X4_STAGGERED_GWB", top=ft(9)),
    Wall(uid="CSW146AAAA", tag="W-S-SN2", start_node="N-S-V1", end_node="N-S-D4",
         assembly="INT_2X4_STAGGERED_GWB", top=ft(9)),
    # NOT BEARING (reverted 2026-08-30; was BEARING from 2026-08-29 to 2026-08-30). The
    # BEARING call was reasoned from FO-A-HALL's doubled trimmer pair delivering the attic
    # floor opening's south edge to "two points" — one on BM-S-BATH-E, whose own south end
    # sits at (10', 22'-4"), directly on this wall's run. But BM-S-BATH-E's ~600 lb reaction
    # (RM-A-POCKET above it is STORAGE, not habitable, so its live load is the lighter
    # storage rate, not a habitable one) does not need a dedicated wall-bearing load path at
    # all: the floor opening's own south edge is closed by a doubled trimmer joist running
    # the full 8' from x=10' to x=18' (the "south trimmer pair" the FloorOpening comment
    # already names), and BM-S-BATH-E's south end is the ordinary case of a header hung by
    # joist hanger into that trimmer, exactly the way its own north end already lands on a
    # real bearing wall (W-S-BD-N1B) rather than needing one at both ends. A hung header
    # does not push its reaction down through the wall under it — it rides the trimmer to
    # wherever THAT joist actually bears, which is not this wall. (The model has no field
    # for "hung on a trimmer" — `Beam.bearing_refs` only resolves Wall/Beam tags — so this
    # is a framing call recorded here in prose, not something a check can verify either way.)
    #
    # Back to INT_2X6_STAGGERED_PLUMBING accordingly — the original ask, and valid again now
    # that nothing requires continuous studs: `FX-S-SUITEBATH-WC` and `FX-S-SUITEBATH-LAV`
    # both back onto this wall and `PR-S-SUITEBATH-VENT` takes off on it
    # (`plan/fixtures.py`, `plan/mep_venting.py`), so this is the suite bath's real wet wall,
    # not W-S-SBS across the room — and SBS gave up its own staggered assembly in the same
    # pass, because nothing was ever against it.
    #
    # ** THE WALL IS 2.02" THICKER THAN THE PARTITION IT REPLACED (4.75" -> 6.77"), SO BOTH
    # FACES MOVED 1.000" AND EIGHT THINGS HAD TO FOLLOW. ** South (bath) face 265.625" ->
    # 264.625": FX-S-SUITEBATH-LAV, ED-S-SUITEBATH-RC1, ED-S-SUITEBATH-MIRROR. North (hall)
    # face 270.375" -> 271.375": ED-S-LANDING-SW, ED-S-STAIR-SW. Only the vanity is caught by
    # a test; the four devices were found by
    # `test_wall_mounted_devices_resolve_against_a_wall_face`, which grades the resolved body
    # against the wall solid, and a fixture other than a vanity is graded by nothing at all —
    # which is how FX-S-SUITEBATH-WC turned out to have been standing 1.92" off this wall
    # since long before any of this. It is flush now.
    #
    # `stacks_on` still names W-M-HS3, but for an unrelated reason: `resolve/stacking.py`
    # derives a `storey_stack:rim` boundary condition for EVERY wall with a collinear overlap
    # below it, bearing or not, and this wall overlaps both W-M-HS3 and W-M-HS4 on the main
    # storey's unbroken y=22'-4" band — `integrity.stack_ambiguous` is a hard ERROR on that
    # overlap without a tiebreaker regardless of structural_role. W-M-HS3 runs x
    # 8'-0"..13'-4", which is also where W-M-HS4 (D-M-LAUN's 4'-0" pocket, off-limits per
    # CLAUDE.md) would otherwise have been the only other candidate.
    Wall(uid="CSW147AAAA", tag="W-S-SN3", start_node="N-S-D4", end_node="N-S-C2C",
         assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(9), stacks_on="W-M-HS3"),
    Wall(uid="CSW148AAAA", tag="W-S-VE", start_node="N-S-V1", end_node="N-S-V2",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    Wall(uid="CSW132AAAA", tag="W-S-BD-N", start_node="N-S-W1", end_node="N-S-V2",
         assembly="INT_2X6_STAGGERED_PLUMBING", top=ft(9)),
    # Retyped and declared BEARING on 2026-08-29 with the two x=10' segments below: it
    # carries BM-S-BATH-E's north end at N-S-BA1. Same swap, same reason, same price —
    # plan/assemblies.py's INT_2X6_BRG_PLUMBING has the whole argument.
    Wall(uid="CSW149AAAA", tag="W-S-BD-N1B", start_node="N-S-V2", end_node="N-S-BA1",
         assembly="INT_2X6_BRG_PLUMBING", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-STOS2"),
    # W-S-BD-N2 (the stair's south wall on y=25', with the 6'-0" O-S-STAIRTOP through it)
    # came out on 2026-07-28 with the centre line: a wall pierced by a 6' hole between two
    # halves of what is now one room was doing nothing but hiding the stair. The well head
    # is guarded by RL-S-STAIRHEAD instead, which stops at the flight's own throat.
    # ** THE x=10'-0" LINE IS A BEARING LINE SINCE 2026-08-29. ** FO-A-HALL opens the attic
    # deck over the stair hall (plan/storeys/stair_hall_void.py), so these two segments now
    # carry the cut ends of the attic joists over y 26'-4"..36'-0" — a light load (a 10'
    # half-span of an 11 7/8" I-joist field, plus W-A-BA-E standing on them), which is what
    # "load bearing, slightly" means. It still has to be DECLARED: nothing in the model
    # infers bearing (model/enums.py), and without the kwarg both
    # `integrity.floor_bearing_grid` and FO-A-HALL's opening-edge test come up empty.
    #
    # The assembly changed with the role, and that is not decoration —
    # `structural.wet_wall_bearing` FAILs any BEARING wall framed with staggered studs.
    # INT_2X6_BRG_PLUMBING is the same 6.77" total, so no face moves, no room area
    # changes, and FX-S-BATH1-LAV's `wall_ref` is untouched. Read that assembly's own note.
    #
    # `stacks_on="W-M-STRW"` is MANDATORY, not decorative: `resolve/stacking.py` walks each
    # LOWER wall looking up for a collinear overlapping upper, and W-M-STRW (main, y
    # 26'-6"..36') has TWO — both W-S-BA-E and W-S-BA-E1B sit on the same x=10' line above
    # it, each overlapping it by more than the 2' minimum. That is what
    # `integrity.stack_ambiguous` raises as a hard ERROR without a tiebreaker (W-M-STRW2,
    # the short segment south of N-M-STRJ, is not a factor either way — at 5 3/8" it never
    # clears that 2' minimum, above or below, so it never enters this resolution). W-M-STRW
    # is already BEARING, already a bearing ref of FO-S-STAIR, and already
    # `stacks_on="W-B-STR"`, so the path runs footings -> W-B-STR -> W-M-STRW -> here ->
    # attic joists, unbroken and already built. Its `alignment=face(...)` on a 6.75"
    # assembly puts its axis on x=10'-0" exactly, inside `_axis_match`'s 1/2" tolerance.
    # ** ONLY ONE UPPER SEGMENT MAY CLAIM IT ** — the resolver links one upper wall per
    # lower wall (resolve/stacking.py) — so W-S-BA-E1B takes it and W-S-BA-E carries NO
    # `stacks_on` at all. That is a limit of the link, not a gap in the building: W-M-STRW
    # runs the whole y 26'-6"..36'-0" line, so W-S-BA-E (y 33'-4"..36'-0") is standing on
    # exactly the same wall its neighbour names. Do not "fix" it by pointing W-S-BA-E at
    # W-M-STRW too; that is the ambiguity the tiebreaker exists to resolve, from the other
    # side.
    Wall(uid="CSW134AAAA", tag="W-S-BA-E", start_node="N-S-N2", end_node="N-S-BA-SPLIT",
         assembly="INT_2X6_BRG_PLUMBING", top=ft(9),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CSW150AAAA", tag="W-S-BA-E1B", start_node="N-S-BA-SPLIT", end_node="N-S-BA1",
         assembly="INT_2X6_BRG_PLUMBING", top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-STRW"),
    # W-S-BA-E2 (N-S-BA1 to the stair shaft's freed N-S-STR2 corner) came out with this
    # edit: since W-S-BD-N2 came out it was a stub dead-ending on an open node, poking into
    # the hallway with nothing on its far end to tie into.
    # 2'x2' mechanical chase, moved to the hall bath's NW corner (2026-07-28, was the NE
    # corner) so it stacks on RM-M-MECH below and the attic exit above. This is what makes
    # RM-S-BATH1 the source's L-shaped 80.73 sf bathroom, now notched NW instead of NE.
    # 2 1/8" deeper than 2'x2' since 2026-08-21 (the south-corner move in NODES); the
    # source's shaft was 2'x2' and test_hall_bath_chase_is_the_source_two_foot_shaft still
    # grades it against that to +/- 3".
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
    # 4'-11" -> 5'-5" on 2026-08-30: centre 6'-2" -> 6'-8", a stud line on W-S-BW1's own grid,
    # and one fewer stud cut. It is the one nudge in this pass that was NOT free — at 6'-8"
    # the wall space between the room's SW corner and the door's south jamb grows past NEC
    # 210.52(A)(1)'s 6 ft, so ED-S-BED1-RC5 goes in with it (plan/electrical.py). Exactly the
    # fix ED-S-BED2-RC5 records for the same wall one bedroom north, for the same reason.
    Door(uid="CSD201AAAA", tag="D-S-BED1", host="W-S-BW1", type_ref="DT-INT-SWING30",
         position=from_node("N-S-B1", ft(5, 5)), flip_swing=True),           # y 15'-8"
    # 8 15/16" north of the source gap (24'-1"), unlike its two neighbours, and the only
    # opening on this storey that leaves the survey: `flip_swing` on 2026-08-24 turned the
    # leaf toward FURN-S-BED2-WARD, and the wardrobe has nowhere to go — the bed's side zone
    # bounds it east, the swing bounds it west whichever hand the leaf takes. Moving the door
    # was the way out. Asserted at its real y in test_openings_land_on_the_source_gaps.
    Door(uid="CSD202AAAA", tag="D-S-BED2", host="W-S-BW2", type_ref="DT-INT-SWING30",
         position=from_node("N-S-B2", ft(4, 1.0625)), flip_swing=True),          # y 23'-0 1/16"
    Door(uid="CSD203AAAA", tag="D-S-BED3", host="W-S-BW3", type_ref="DT-INT-SWING30",
         position=from_node("N-S-B3", ft(0, 8)), flip_swing=True),                        # y 28'-11"
    # Just an opening, framed the same as a 30" door: no leaf needed for this passthrough.
    RoughOpening(uid="CSD204AAAA", tag="D-S-STUDY2", host="W-S-SS1",
                 position=from_node("N-S-C1", ft(1, 0.625)), width=ft(2, 6),
                 height=ft(6, 8)),                                       # x 20'-3 5/8"
    # Three doors through the centre bearing line, on the source's own gaps. Each takes a
    # header exactly like O-M-HALL / O-M-DRESS one storey down; the wall itself is unbroken.
    # Full-lite glass leaf admits daylight from the south-facing plant room into
    # RM-S-STUDY2 — this door opens on the study, not the hall (corrected 2026-08-18).
    Door(uid="CSD212AAAA", tag="D-S-PLANT", host="W-S-C1", type_ref="DT-INT-SWING30-GLAZED",
         position=from_node("N-S-S1", ft(2, 9))),                      # y 4'-5 1/2"
    Door(uid="CSD206AAAA", tag="D-S-SUITE", host="W-S-C2B", type_ref="DT-INT-SWING32",
         position=from_node("N-S-C2", ft(0, 4.875))),                    # y 14'-1 7/8"
    # O-S-HALLW (a 3'-0" cased opening at y 28'-7") is gone: the whole 8'-6" between
    # N-S-C2C and N-S-C3D is open under BM-S-HALL now, so there is no wall left to host it.
    # West block
    # Bifold closet door, DT-INT-BIFOLD56 (4'-8"), replacing the former bare RoughOpening.
    Door(uid="CSD213AAAA", tag="O-S-CLOSET", host="W-S-CLN", type_ref="DT-INT-BIFOLD56",
         position=from_node("N-S-D2", ft(1, 8))),                       # x 13'-9"
    # The source's gap starts hard against the corner at x=9'-10 11/16"; ours started 3"
    # further east so the leaf's king stud clears W-S-DC2's corner pack instead of
    # pinwheeling through it (test_wall_corner_and_opening_framing).
    #
    # +8" more since 2026-08-30: W-S-SBS retyped from INT_2X6_STAGGERED_PLUMBING to plain
    # INT_2X4_PARTITION (the wet-wall duty moved to W-S-SN3), and the plain wall's module
    # residue off N-S-D3 is 3.5", not the staggered wall's — `structural.door_framing_module`
    # wanted this door's centre on 3.5" + n*16", and 9"-edge/24"-centre missed it, cutting an
    # extra stud. 17" edge / 32" centre is the nearest legal station.
    Door(uid="CSD214AAAA", tag="D-S-SUITEBATH", host="W-S-SBS", type_ref="DT-INT-SWING30",
         position=from_node("N-S-D3", inch(17)), flip_hinge=True),                     # x 12'-1"
    # 4 5/8" off N-S-V1, not the authored 3": W-S-SN1/SN2 became the 8" staggered sound
    # wall on 2026-08-21, so the node square this wall starts past grew from 2 3/8" to 4",
    # and at 3" the void's first inch was cut inside the corner (the IFC self-diff read the
    # emitted opening 1" narrower than the authored 2'-8"). 4 5/8" restores the 5/8" the
    # opening always had between its jamb and the corner square.
    RoughOpening(uid="CSD215AAAA", tag="O-S-VANITY", host="W-S-VE",
                 position=from_node("N-S-V1", inch(8)), width=ft(2, 8),
                 height=ft(6, 8)),                                       # y 24'-0 5/8"
    # Pulled 3" west of its original 1'-4.5": at that offset the door's own
    # king stud landed inside N-S-BA1's corner square and punched into W-S-BA-E1B's end
    # stud (the same class of overlap as N-M-MECH2 in test_wall_corner_and_opening_framing).
    # ** IT STAYS AT 1'-1 1/2", AND `structural.door_framing_module` REPORTS IT. ** Centre
    # 28 1/2" is 3 1/2" off the module and costs one extra stud. The only station on this wall
    # that would fix it is 32", and 32" leaves the RO 2 1/2" from N-S-V2 — the king and jack
    # on that side would be inside the corner pack, which is nine `member_interference`
    # overlaps traded for one stud. (It also needs `flip_swing` there, because at 32" the old
    # swing sweeps FX-S-BATH1-LAV; that part works, and is moot.) The wall is 5'-1" long and
    # carries a 30" leaf: there is no station on it that clears both ends.
    #
    # ** `flip_hinge` IS LOAD BEARING: IT IS WHAT KEEPS THE LEAF OFF FX-S-BATH1-LAV. **
    # W-S-BD-N1B runs +x, so the unflipped jamb is the EAST one at x=9'-6", and a leaf hung
    # there sweeps its FULL quadrant across the vanity — 15.6 in2 of the cabinet, which is
    # what the plan sheet was drawing until 2026-09-09. Hinged at the WEST jamb the same
    # leaf clears it: 0.0 sf, 0.21" at the closest point (the arithmetic is in
    # plan/fixtures.py). Do not "tidy" this flag away.
    #
    # The other two ways out were both worse. `flip_swing` throws the leaf into the hall,
    # and the 4'-0" stub north of this wall is where you stand to open the door
    # (storeys/attic_studio.py). Shrinking the cabinet costs a volume SKU: 42" is
    # special-order where 48" is stock, and it buys clearance the door never needed.
    #
    # The arc is a 90 DEGREE quarter-disc. Past 90 the leaf does reach the cabinet, so this
    # door takes a stop. The engine models no such thing — it is a hardware note only.
    Door(uid="CSD208AAAA", tag="D-S-BATH1", host="W-S-BD-N1B", type_ref="DT-INT-SWING30",
         position=from_node("N-S-V2", ft(1, 1.5)), flip_hinge=True),     # x 8'-3"
    Door(uid="CSD217AAAA", tag="D-S-NCLOSET", host="W-S-CLN-S", type_ref="DT-INT-SWING30",
         position=from_node("N-S-C3D", ft(0, 8.5)), flip_swing=True, flip_hinge=True),                     # x 19'-11 1/2"
    # O-S-STAIRTOP, the 6'-0" cased stair head, went with its host wall W-S-BD-N2.
    # Balcony door. The source draws ONE opening (x 18'-8"..23'-11", 5'-3", with two
    # leaves), east of the centre line; that is D-S-DECK-E, standardized to the catalog's
    # 5'-0" French pair rather than distorted into a narrow 3'-0" double door.
    #
    # There was a second, D-S-DECK-W, a mirror of this one at x 14'-8" giving the plant room
    # its own balcony access. IT IS GONE (2026-09-03): a 60" French door is the one hole in
    # RM-S-PLANT's six-sided sealed liner that no detail fixes. Its threshold condenses at
    # design (notes/plant_room.md — the frame and edge of glass run 5-8 F below centre, and
    # a door has far more frame than a window), every use of it dumps 70%-RH air onto the
    # balcony and pulls -15 F air onto the liner, and it is the one opening in the room that
    # cannot be a fixed, gasketed, thermally broken unit. WIN-S-PLANT4 takes its station.
    # The study still reaches the balcony through D-S-DECK-E, which is what the source drew.
    Door(uid="CSD211AAAA", tag="D-S-DECK-E", host="W-S-S2", type_ref="DT-EXT-FRENCH60",
         position=from_node("N-S-S1", ft(0, 10)), flip_swing=True),                       # x 21'-4"
    # Windows — east wall, on the source's four 2'-8" openings (we build 27", the bearing cap).
    # WIN-S-STUDY3 moved off its source position (y 3'-10") to y=5'-4" for an
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
    # 2026-08-27: retyped WT-2736-T -> WT-2748-T, 36" -> 48" tall. Same 27" bearing width,
    # so the mirrored 4'-0"/13'-4"/22'-8"/32'-0" beat and every offset below are untouched;
    # the head moves 6'-0" -> 7'-0". It still columns with WIN-M-LIV-E1 below, which took
    # the same retype the same day.
    Window(uid="CSX314AAAA", tag="WIN-S-STUDY3", host="W-S-E1", type_ref="WT-2748-T",
           position=from_node("N-S-SE", ft(2, 10.5)), sill_height=ft(3)),     # y 4'-0"
    # BED1/BED2 ARE BACK ON THE 27" BEARING CAP, AND THE 2026-08-01 NOTE THAT
    # PUT THEM ON 30" WAS WRONG ABOUT WHY IT HAD TO. That note read: "a 27x36 falls a third
    # short [of R303.1] ... 27" cannot reach it at any height that fits under the 9'-0"
    # plate", and moved `preferences.toml [framing] max_window_ro_bearing_in` 27 -> 30 to
    # allow a 30x48. The first half is true and the second half is not. R303.1 binds on
    # AREA, and area is width x height:
    #   * BED1 is 119.66 sf -> 9.573 sf glazed / 4.786 openable; BED2 is the binding one at
    #     124.32 sf -> 9.945 / 4.973. (The 2026-08-01 note called both 124.3; BED1 lost 4"
    #     of depth in the 2026-08-15 node move, which that note predates.)
    #   * 27x36 = 6.75 sf. Short by 2.8/3.2 sf, as the note said.
    #   * 27x48 = 9.00 sf. Still short of BOTH (-0.57 BED1, -0.95 BED2).
    #   * 27x54 = 10.125 sf / 5.063 openable. CLEARS BOTH — BED1 by +0.55/+0.28 sf and
    #     BED2 by +0.18/+0.09, wider margins than the 30x48 this replaces (+0.43/+0.21 and
    #     +0.055/+0.027). Openable is half the RO in this engine, and it never binds first.
    # 54" fits under the plate with room to spare: on the shared 3'-0" sill the head lands
    # at 7'-6", leaving 18" to the 9'-0" top of wall — a 2-2x8 header is 7 1/4" and the
    # double top plate 3", so 7 3/4" of cripple remains. The 2026-08-01 note simply never
    # tried a height above 48".
    #
    # So the east bearing wall keeps the one framing rule the whole house is built on — one
    # broken stud, jacks on a bearing header (R602.7.5) — and R303.1 is paid in height.
    # Sill stays on the shared 3'-0" east-face line, which is the datum this face actually
    # holds; the head moves 7'-0" -> 7'-6", and the face already carried two head lines
    # (WIN-S-STUDY3/BED3 sit at 6'-0"), so it is not giving one up.
    #
    # ``from_node`` is the NEAR JAMB, so both offsets moved +1 1/2" — half the 3" of lost
    # width — which holds the CENTRES on y=13'-4" and y=22'-8" and on their stud lines.
    # (Those are the real stations: the inner pair moved 4" outward earlier on 2026-08-25
    # with the line-based stud module, and the trailing comments on these two lines said
    # 13'-0"/23'-0" until this edit. The row is a mirror — 13'-4" + 22'-8" = 36'-0" — and
    # `test_catlin_contract_m3.py::test_the_east_second_storey_window_row_mirrors_about_
    # the_house_centreline` pins it.) The one thing the narrowing moved is the head, from
    # 7'-0" to 7'-6"; the outer pair stayed at 6'-0", so the row stepped up to the middle.
    # (Both halves of that sentence were undone later the same day — see the retype note
    # below and WIN-S-STUDY3's — and the row is level at 7'-0" now.)
    # BED1 lost 4" of depth in the 2026-08-15 node move (it had the margin to spare); BED3
    # gained 4" (it has a second window, 14.2 sf). BED1 carries the -T twin because at
    # y=13'-4" the glass falls inside 60" of ST-S2A, R308.4.5's stair band.
    #
    # ** 2026-08-27, BY DECISION: BED1/BED2 RETYPED WT-2754 -> WT-2748, 54" -> 48" TALL. **
    # This gives back exactly the height the 2026-08-25 note above bought R303.1 with, and
    # that note's arithmetic still holds: 27x48 = 9.00 sf against 9.6 sf required for BED1
    # and 9.9 sf for BED2, so both rooms are short on GLAZED AREA again. Neither fails.
    # Both are carried by R303.1 Exception 1 — 3600 lm gives 14.4 / 13.9 fc and the ERV
    # delivers 210 cfm of outdoor air (206 certified; either clears the exception's
    # 15 cfm/person) — the same exception RM-M-LIVING has always leaned
    # on. What the 54" bought was compliance without the exception; that is what is spent
    # here, not compliance itself. R310 egress is unaffected (9.00 sf > 5.7 net).
    # Head drops 7'-6" -> 7'-0"; width, sill, centres and the mirror about the house
    # centreline are unchanged (same 27" bearing RO), so nothing on the facade or in the
    # framing moved. BED1 keeps the -T twin for R308.4.5's stair band.
    Window(uid="CSX301AAAA", tag="WIN-S-BED1", host="W-S-E2", type_ref="WT-2748-T",
           position=from_node("N-S-E1", ft(3, 2.5)), sill_height=ft(3)),    # y 13'-4"
    Window(uid="CSX302AAAA", tag="WIN-S-BED2", host="W-S-E3", type_ref="WT-2748",
           position=from_node("N-S-E2", ft(3, 10.5)), sill_height=ft(3)),   # y 22'-8"
    # BED3 MOVED OFF THE ROW: retyped WT-2736 -> WT-1424 and moved 32'-0" ->
    # 34'-0" centre, matching WIN-M-KIT-E below in both size and station so the two column.
    # RM-S-BED3 loses 4.4 sf of glass by it (6.75 -> 2.33 from THIS window) and joined
    # BED1/BED2 on R303.1 Exception 1; its R310 egress was never this window's job —
    # WIN-S-HALL-N carries it. 2026-09-06: the ARITHMETIC here was wrong, though the
    # exception is real. The resolver credits WIN-S-HALL-N (a BED3 window despite the tag)
    # to the room, so BED3 was never at 2.33 sf but at 9.83 against 10.32 required — 0.49 sf
    # short, not 8. A fourth north window was added that day to close the 0.49 and then
    # withdrawn when the facade was solved by moving windows instead (see WIN-S-HALL-N
    # below), so the room stays on Exception 1 — over it by half a square foot, lit at
    # 13.4 fc and ventilated on 210 cfm.
    # WIN-A-E-N moved 32'-8" -> 34'-0" the same day (attic.py) to complete a three-storey
    # 14" column on the east face. ``from_node`` is the near jamb, so 34'-0" - 7" = 33'-5"
    # off N-S-E3 at y=26'-8" -> 6'-9". The east second-storey row is now three units, and
    # the mirror test's north member is gone with it. ** THE SILL WENT TO 4'-0" WITH THE
    # RETYPE AND THIS NOTE SAID 3'-0" UNTIL 2026-09-06 ** — it left the east face's 3'-0"
    # datum (BED1/BED2 still hold it) for the 14" family's own 4'-0", which is the rule the
    # west face keeps and the head line that follows from it. WIN-M-KIT-E's 3'-6" is a
    # counter height and does not travel up.
    Window(uid="CSX303AAAA", tag="WIN-S-BED3", host="W-S-E4", type_ref="WT-1424",
           position=from_node("N-S-E3", ft(6, 9)), sill_height=ft(4)),      # y 34'-0"
    # West suite (bearing wall). SUITE1 moved 13'-0" -> 10'-4" for the third exact
    # main/second west column. Its header crosses W-S-W3's top ladder-backing rung, so the
    # solver omits that nonstructural rung while preserving the header and every other rung.
    Window(uid="CSX304AAAA", tag="WIN-S-SUITE1", host="W-S-W3", type_ref="WT-2736",
           position=from_node("N-S-W2", ft(10, 6.5)), sill_height=ft(3)),   # y 10'-4"
    Window(uid="CSX305AAAA", tag="WIN-S-SUITE2", host="W-S-W3", type_ref="WT-2736",
           position=from_node("N-S-W2", ft(1, 2.5)), sill_height=ft(3)),      # y 19'-8"
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
    Window(uid="CSX307AAAA", tag="WIN-S-PLANT2", host="W-S-S1", type_ref="WT-3048-HP",
           position=from_node("N-S-SW", ft(8, 1)), sill_height=ft(2, 8)),     # x 9'-4"
    # WIN-S-PLANT4 stands where D-S-DECK-W did, and it is why PLANT2 above is no longer the
    # tempered twin: R308.4.2 made that unit hazardous only because it sat within 24" of a
    # door, and there is no door on this wall any more. Same 30x48 HP unit, same 2'-8" sill
    # and 6'-8" head as PLANT1/2, and centre x 14'-8" continues their exact 5'-4" beat — the
    # station is a stud line on W-S-S1's grid (it is the one the door was moved onto on
    # 2026-08-24) and still columns over WIN-M-BED-S2 one storey down. Three equal windows
    # on one line where there were two and a door.
    Window(uid="T84MSZYSVQ", tag="WIN-S-PLANT4", host="W-S-S1", type_ref="WT-3048-HP",
           position=from_node("N-S-SW", ft(13, 5)), sill_height=ft(2, 8)),    # x 14'-8"
    # The plant room's west window is on W-S-W4, a bearing wall, so it takes the 27" bearing
    # type, not the 30" south-glazing one ("resize windows to fit the grid", CLAUDE.md).
    # Sill raised to 3'-0" for the shared 6'-0" head line. Unmoved by the
    # 2026-08-15 column pass — W-S-W4 starts at N-S-W3 (y=9'-0"), which can't move without
    # dragging the whole east row off its mirror — so WIN-M-BED-W1 came up to meet it
    # instead.
    Window(uid="CSX308AAAA", tag="WIN-S-PLANT3", host="W-S-W4", type_ref="WT-2736-HP",
           position=from_node("N-S-W3", ft(2, 6.5)), sill_height=ft(3)),     # y 5'-0"
    # Restores west daylight to the double-vanity alcove without competing with its two
    # north-wall sinks and mirror lights. Paired exactly with WIN-M-BATH1-W below; the 14"
    # RO fits one stud bay, and the tempered awning shares the facade's 6'-0" head line.
    # 1'-3" off N-S-W1 since 2026-08-29, the twin of WIN-M-BATH1-W's identical compensation
    # one storey down: N-S-W1 moved 2" north with the y=26'-6" line, and a `from_node` offset
    # rides its node. Left at 1'-1" the unit slid 2" north with it and
    # `structural.window_framing_module` caught it immediately — W-S-W2 lays out from
    # LL-W-A-W1, so its legal stations are 14" + n×16" and a 2" drift interrupts a stud.
    # 1'-3" restores y=25'-3" and with it the exact pairing with WIN-M-BATH1-W below.
    Window(uid="RGC7QGVF7Y", tag="WIN-S-VANITY-W", host="W-S-W2", type_ref="WT-1424-T",
           position=from_node("N-S-W1", ft(1, 3)), sill_height=ft(4)),       # y 24'-4"
    # Study 2's south pair: centres 27'-4" and 32'-8" are stud lines on W-S-S2's grid,
    # STUDY1 stacking exactly over WIN-M-LIV-S1 (STUDY2's partner below, WIN-M-LIV-S2, was
    # deleted 2026-08-24, so STUDY2 no longer columns with anything). Moved 8" west off the old bay centres with the
    # WT-3048 narrowing (2026-08-01, see WIN-M-BED-S1/2); the two south segments stay 8"
    # out of phase, the same unavoidable mirror miss as always. Sill 2'-8" is the shared
    # 6'-8" head line; D-S-DECK-E's RO stays clear by 1'-3".
    Window(uid="CSX309AAAA", tag="WIN-S-STUDY1", host="W-S-S2", type_ref="WT-3048-T",
           position=from_node("N-S-S1", ft(7, 5)), sill_height=ft(2, 8)),     # x 27'-4"
    Window(uid="CSX310AAAA", tag="WIN-S-STUDY2", host="W-S-S2", type_ref="WT-3048",
           position=from_node("N-S-S1", ft(12, 9)), sill_height=ft(2, 8)),    # x 32'-8"
    # Baths + north. WIN-S-BATH-N/W have no source counterpart, kept for hall-bath daylight.
    # Re-hosted off W-S-N3: W-S-N3B is now the chase's own wall, not the
    # bathroom's. Nudged to 8" off N-S-CH2: at 1' the RO straddled the module
    # stud line instead of centering in the bay, breaking two studs and pulling in a
    # header/jacks a 14" RO should never need
    # (test_catlin_small_windows_have_no_header_and_keep_their_flanking_studs).
    Window(uid="CSX312AAAA", tag="WIN-S-BATH-W", host="W-S-W1", type_ref="WT-1424-T",
           position=from_node("N-S-CH3", ft(1, 1.875)), sill_height=ft(4)),
    # ** MOVED 29'-4" -> 24'-0" ON 2026-09-06, AND THE THREE-STOREY COLUMN IS SPENT. **
    # It was at 29'-4" to column with WIN-M-KITCH over the kitchen sink below; the 6:12 rake
    # had already pulled WIN-A-N2 off that station in 2026-09-03, so what remained was a
    # two-storey stack, and this move gives it up entirely. WIN-M-KITCH now stands alone on
    # the main storey — it cannot follow, being dead-centred on the sink run.
    #
    # What is bought is the whole upper facade. The north face carried three units that
    # almost made a rectangle with the lower-east corner empty. Rather than adding a fourth
    # unit at 23'-4" — the only station the module and node N-S-B5 left, 8" off the ideal
    # and off every column — the four windows already in the house moved onto ONE rectangle:
    # this one and WIN-A-N2 to 24'-0", WIN-A-N1 and WIN-S-STAIR-N to 12'-0". Both stations
    # are 16" multiples, which is what a 27" or 30" RO needs (either breaks studs and so
    # cannot take a bay centre), and they mirror on the 18'-0" ridge, so each attic unit
    # stacks EXACTLY on its second-storey partner.
    #
    # ** RETYPED WT-3036 -> WT-2748 ON 2026-09-10, AND THE SILL CAME DOWN TO 2'-3 1/2". **
    # 30x36 is 1:1.2 and read too square in elev_north.png. 27x48 is 1:1.78, and it is a
    # RETYPE plus a sill move — the centre stays on 24'-0", so the facade rectangle, the
    # stud line and the stack on WIN-A-N2 are all untouched. The offset had to grow 1 1/2"
    # to hold that centre: `from_node` resolves to the opening's near JAMB, not its centre
    # (resolve/pipeline.py's `_opening_center`), so a 3" narrowing drags the centre 1 1/2"
    # unless the offset absorbs it. Same arithmetic at all four north units.
    #
    # ** THE SILL IS 2'-3 1/2" BECAUSE 27 1/2" IS AN EXACT GIRT COURSE HIT. ** The course
    # module is 24" o.c. at phase zero off the framing base, so a course tops out flush at
    # 27 1/2" and the sill course IS the field course — no sliver. That is the second half
    # of CLAUDE.md's NEW-OPENING RULE ("head on a 24" multiple, or sill 3-1/2" above one"),
    # and taking it moved test_truss_girt_courses.py from 12 exact hits to 14 with the
    # sliver count unchanged at 33. It is also 3 1/2" clear of R312.2's 24" fall-protection
    # trigger, which matters because `sill_m` is measured off the SUBFLOOR and the finished
    # floor is 15/16" higher — an authored 24" would be 23 1/16" to an inspector's tape.
    # The head follows to 6'-3 1/2", which is 3 1/2" over WIN-S-BED3-N's 6'-0"; the two were
    # 6" apart before, so the facade's head lines converge rather than diverge.
    #
    # (The prose here and in CLAUDE.md claimed a 3'-0" sill and a 6'-0" head until
    # 2026-09-10. Commit 5487fd79 had raised both north sills ft(3) -> ft(3, 6) in a silent
    # hunk, putting the head at 6'-6"; nothing was updated to match. That is a doc
    # correction, not a move — the move is the one above it.)
    #
    # 24'-0" clears node N-S-B5 (x 21'-11", the closet/BED3 partition): the RO runs
    # 22'-10 1/2"..25'-1 1/2", so the west jamb has 11 1/2" to the node — enough for the
    # jamb pack, which 22'-8" itself would not have had at any width. FURN-S-BED3-WARD stood
    # 6'-6" tall right here (x 22'-1.5"..24'-1.5") and swaps slots with FURN-S-DESK3 in
    # placeables.py. ** FURN-S-DESK3's top is 30", now 2 1/2" ABOVE this sill ** — a desk
    # under a window, the way the study table sits under WIN-S-STUDY1, and nothing in the
    # engine grades it either way.
    Window(uid="CSX313AAAA", tag="WIN-S-HALL-N", host="W-S-N1", type_ref="WT-2748",
           position=from_node("N-S-NE", ft(10, 10.5)), sill_height=ft(2, 3.5)),  # ctr x 24'-0"
    # Stairwell daylight (2026-07-30 facade pass): the north facade was blank from the
    # entry column to x=21'-11". W-S-N2 runs 18'-0" -> 10'-0", so the offset is measured
    # east-to-west and 4'-10 1/2" off N-S-N1 is a near jamb at 13'-1 1/2", a CENTRE at
    # x 12'-0" and an RO of 10'-10 1/2"..13'-1 1/2" — a stud line, which is what a 27" or
    # 30" RO must have. WIN-A-N1 on the gable above is at that same 12'-0", so the two are
    # exactly stacked.
    #
    # ** RETYPED WT-3036-T -> WT-2748-T ON 2026-09-10 ** with WIN-S-HALL-N, sill and all —
    # see that unit's note for the proportion, the 1 1/2" offset growth and why 2'-3 1/2"
    # is the sill. The tempered twin is carried through the retype rather than dropped:
    # code.R308_4_safety_glazing does not currently name this unit, and lowering the sill
    # 14 1/2" toward ST-S2A's walking surface is not the moment to find out why.
    #
    # ** MOVED 13'-4" -> 12'-0" ON 2026-09-06 **, one stud bay west, as the west half of
    # the facade rectangle described at WIN-S-HALL-N above. The west jamb lands 10 1/2" off
    # node N-S-N2 (x 10'-0"), which the jamb pack fits. (This note read "12'-8"" and claimed an
    # 8" miss against WIN-A-N1 until 2026-09-06; the offset always resolved to 13'-4" and
    # the prose was simply wrong. The move below is a real move; that correction was not.)
    Window(uid="CSX315AAAA", tag="WIN-S-STAIR-N", host="W-S-N2", type_ref="WT-2748-T",
           position=from_node("N-S-N1", ft(4, 10.5)), sill_height=ft(2, 3.5)),   # ctr x 12'-0"
    # ** THE NE CORNER PAIR, COMPLETED ONE STOREY UP (2026-09-06). ** RM-S-BED3 already had
    # WIN-S-BED3 on its east wall at y=34'-0"; this is its twin on the north wall at
    # x=34'-0" — same WT-1424, plain glass, operable awning. The two now wrap the north-east
    # corner exactly the way WIN-M-KITCH-N and WIN-M-KIT-E wrap it on the main storey below,
    # each unit 2'-0" off the corner on its own wall.
    #
    # ** SILL 4'-0" — THE SAME AS ITS TWIN, AND THE SAME RULE. ** WIN-S-BED3 is at 4'-0"
    # too (its own note claimed 3'-0" until 2026-09-06; the authored value was always
    # ft(4)). That is the rule the west face keeps, per CLAUDE.md's Head lines: 27" units at
    # a 3'-0" sill, 14" units at 4'-0", every head on one 6'-0" line. So this unit heads at
    # 6'-0" exactly, on the 72" girt course, and the corner pair is a true twin in plan, in
    # type AND in section.
    #
    # ** IT DOES NOT SHARE A HEAD WITH WIN-S-HALL-N / WIN-S-STAIR-N, AND NEVER DID. ** This
    # note claimed all four north units headed on the 6'-0" line until 2026-09-10; commit
    # 5487fd79 had already put those two at 6'-6". Since their 2026-09-10 retype they head
    # at 6'-3 1/2", so the gap is 3 1/2" rather than 6" — closer, still not one line. The
    # north face's second storey is a ROW, not a head line: three units on one rectangle
    # with this 14" corner unit outboard of it.
    #
    # It costs one girt sliver and buys one exact hit, and that trade is forced rather than
    # chosen: a 24"-tall unit holds its sill course bottom and its head 27-1/2" apart, so on
    # the 24" course module one edge is always exact and the other always 3-1/2" off. At
    # 4'-0" the head lands on 72" exactly and the sill course sits 3-1/2" under the field
    # course at 48"; at 3'-0" neither edge is within 8-1/2" of a course, so it would cast no
    # sliver and hit nothing. test_truss_girt_courses.py was re-swept for this and moved
    # 13/30 -> 14/31; course_offset stays 0.
    #
    # The station is taken from WIN-M-KITCH-N verbatim — `from_node("N-M-NE", ft(1, 5))`
    # there, `from_node("N-S-NE", ft(1, 5))` here, both walls running west off x=36'-0" —
    # so this sits DIRECTLY above it and the north face gains a two-storey 14" column at
    # 34'-0" to set against the one it lost when WIN-S-HALL-N moved to 24'-0". 408" is
    # 8 mod 16, a BAY CENTRE on the shared layout line, so the 14" RO (33'-5"..34'-7")
    # falls wholly inside one bay: no header, no jacks, no kings. It leaves 17" to the
    # corner at N-S-NE and 8'-2" to WIN-S-HALL-N's east jamb, so it crowds neither.
    #
    # ** IT TAKES RM-S-BED3 OFF R303.1 EXCEPTION 1. ** The room was 9.83 sf glazed against
    # 10.32 required — 0.49 sf short — and had been on the exception since 2026-08-27, when
    # WIN-S-BED3 was retyped to a 14" unit to complete the three-storey east column. 2.33 sf
    # more takes it to 12.17 glazed / 6.08 openable and it passes outright.
    #
    # The tag had a few hours' prior life the same day on a WT-1436 at x 23'-4", added to
    # fill the facade's lower-east corner and withdrawn when the four existing windows were
    # moved onto one rectangle instead (see WIN-S-HALL-N above). Different station,
    # different type, different argument; the uid is new.
    Window(uid="A4BAA399PA", tag="WIN-S-BED3-N", host="W-S-N1", type_ref="WT-1424",
           position=from_node("N-S-NE", ft(1, 5)), sill_height=ft(4)),        # ctr x 34'-0"
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
    # Ceiling: PVC panel on furring over the same membrane as the walls, continuous with
    # them at the perimeter (notes/plant_room.md "Ceiling — specified, not yet modelled").
    # Restated rather than imported — assemblies.py's `_HUMID_LINER` is the same three
    # layers in the same order, but the editable dialect cannot import a sibling plan
    # module (see ACCENT_GWB_LINING above). Keep the two in step by hand.
    Room(uid="CSR401AAAA", tag="RM-S-PLANT", seed=pt(ft(9), ft(4)),
         occupancy=Occupancy.LIVING, humidity_class=HumidityClass.HUMID,
         design_relative_humidity=0.70, design_temperature_f=75.0,
         floor_finish="vinyl-sheet",
         ceiling_lining=(
             Layer(name="pvc-panel", material_ref="pvc-panel", thickness=inch(0.5),
                   function=LayerFunction.FINISH),
             Layer(name="liner-furring", material_ref="spf", thickness=inch(0.75),
                   function=LayerFunction.FURRING,
                   framing=FramingSpec(member="1x4", direction="horizontal")),
             Layer(name="humid-membrane", material_ref="humid-room-membrane",
                   thickness=inch(0.04), function=LayerFunction.MEMBRANE,
                   control={ControlLayer.VAPOR, ControlLayer.AIR}),
         )),
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
    # ** 2026-09-05: CARPET -> WALNUT -> OAK, AND THE WALNUT WENT UP THE WALL. ** The suite
    # and its walk-in were briefly one 181.7 SF field of site-milled `walnut-floor`. Three
    # things killed it, all specific to THIS room:
    #   * Walnut photo-LIGHTENS — it fades toward honey-grey under UV — and WIN-S-SUITE1/2
    #     are on W-S-W3, the WEST exterior wall, the harshest afternoon load in the house.
    #     Rugs and furniture would print permanent ghost marks into the floor.
    #   * It is soft for a floor: ~1010 Janka against white oak's ~1360.
    #   * It is the worst use of the family stock. 200 SF of flooring wants long, wide, clear
    #     boards — the most demanding cut off a log pile — for the one surface that lives
    #     under a bed and a rug.
    # None of that applies to a vertical surface at eye level, so the walnut moved to
    # WP-S-SUITE-HEADBOARD (see PANELING below) and the floor is `oak`, matching RM-S-STUDY2
    # and RM-A-STUDY. That also puts the second storey's oak on one sand-and-finish set-up
    # (~340 SF here) instead of a trip for a single room; prices.toml [floor_finishes] `oak`
    # carries the mobilisation arithmetic. The walk-in follows the suite for the same reason
    # it followed the walnut: a species change in a 27 SF doorway buys a reducer strip and a
    # second set-up for nothing.
    Room(uid="CSR406AAAA", tag="RM-S-SUITE", seed=pt(ft(5), ft(16)),
         occupancy=Occupancy.BEDROOM, floor_finish="oak"),
    Room(uid="CSR407AAAA", tag="RM-S-CLOSET", seed=pt(ft(14), ft(10, 8)),
         occupancy=Occupancy.STORAGE, floor_finish="oak"),
    # LVP through the unheated wet rooms and the circulation: one continuous plank floor
    # from the stair head through both hallways and into the two baths with no radiant in
    # them, so the traffic route has no thresholds in it and those baths get a waterproof
    # plank instead of tile.
    Room(uid="CSR412AAAA", tag="RM-S-SUITEBATH", seed=pt(ft(14), ft(19)),
         occupancy=Occupancy.BATHROOM, floor_finish="lvp"),
    Room(uid="CSR413AAAA", tag="RM-S-VANITY", seed=pt(ft(3), ft(24, 4)),
         occupancy=Occupancy.BATHROOM, floor_finish="lvp"),
    # ** RM-S-BATH1 IS TILE, NOT PLANK (2026-09-05), AND FH-S-BATH1 IS THE WHOLE REASON. **
    # It carried the hall's LVP over the electric radiant zone, which
    # advisory.floor_finish_over_radiant flagged: plank is surface-temperature limited at
    # 80-85 F, so the one heated floor on this storey was the one covering that throttles
    # the heat it is there to deliver. Tile has no such cap and is the mat's mass.
    # Spec is the mudroom's cheap porcelain (prices.toml [floor_finishes] `tile`), not a
    # designer tile — with one difference the mudroom does not have: the uncoupling
    # membrane under a heated floor is the DITRA-HEAT variant, the cable's own base, not
    # the plain 1/8" sheet the takeoff's companion row prices. See that row's note.
    # The cost of the change is one threshold at D-S-BATH1, tile ~5/16" proud of the hall
    # plank — the same dirt-step detail D-M-MUD already builds downstairs.
    #
    # ** THE DECK UNDER IT IS THE SHORT END OF FS-S-WEST, NOT THE 18' BAY. ** FO-S-STAIR
    # takes x 10'-3 3/8"..17'-8 5/8" out of this deck from y=26'-0 3/8" north, so the eight
    # trusses over this room land on that opening's west header instead of running through
    # to the x=18' line: 10'-1 5/8" tip to tip, ~9'-9" clear, against the 17'-11" the twenty
    # trusses south of the well really do span. `structural.ijoist_span` grades a deck by its
    # WORST joist and so prints 17.9' for FS-S-WEST — that number is the south half and says
    # nothing about this room. `resolve/floor_ends.py` already cuts these eight correctly;
    # the BOM and the fabrication schedule have the short length.
    #
    # Which is why the tile is comfortable here and it is worth writing down: ~9'-9" is
    # roughly the mudroom's own 9.9' span, and at half the table limit the L/360 basis
    # is no longer the binding number it would have been out in the 18' field.
    Room(uid="CSR408AAAA", tag="RM-S-BATH1", seed=pt(ft(5), ft(31)),
         occupancy=Occupancy.BATHROOM, floor_finish="tile"),
    # RM-S-HALL is the source's single 181.02 sf "Hallway" again: taking the centre line
    # out between y 22'-4" and 30'-10" left one polygonized face spanning the old hall,
    # landing and open stair well, so RM-S-LANDING/RM-S-STAIR were retired into this claim
    # rather than billing the same face three times. RL-S-STAIR guards the well's east edge.
    Room(uid="CSR409AAAA", tag="RM-S-HALL", seed=pt(ft(20), ft(20)),
         occupancy=Occupancy.HALLWAY, floor_finish="lvp"),
    # RM-S-NCLOSET opens off the hall, not a bedroom (D-S-NCLOSET hosts on W-S-CLN-S), so
    # the hall's LVP runs straight in — no threshold, and the linen shelving sits on plank.
    Room(uid="CSR415AAAA", tag="RM-S-NCLOSET", seed=pt(ft(20), ft(33)),
         occupancy=Occupancy.STORAGE, floor_finish="lvp"),
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

# Electric radiant floor in the NW bathroom: RM-S-BATH1 is the hall bath (see
# header note), the only one heated on this storey. Same recipe as main.py's zones: 12 W/ft2
# 120V mat at a 3" serpentine. `in_slab` is just the enum mode name — this floor is
# FS-SECOND's I-joists/plywood, and the mat lies in the thinset above it. CKT-FH-BATH1 and
# ED-S-BATH1-FH-STAT carry it.
#
# The covering over it is TILE as of 2026-09-05 (see RM-S-BATH1 above) — it was plank, and
# plank caps the surface at 80-85 F. That also names the base: DITRA-HEAT, the dimpled
# membrane whose studs hold the cable, rather than the plain uncoupling sheet the takeoff's
# companion row prices for the mudroom's unheated tile. See prices.toml's note on that row.
#
# The zone is drawn to the fixtures (plan/fixtures.py's de-overlapped WC/lav/shower
# positions), not the room outline, holding 3" off every fixture: total 31.6 ft2 across a
# south band, an east step to the lav, and a centre panel between WC and shower. The strips
# north of the WC and west of the pan are left unheated rather than run a 3"-wide corridor.
FLOOR_HEAT = [
    FloorHeat(uid="CSH801AAAA", tag="FH-S-BATH1", room_ref="RM-S-BATH1",
              # South edge 26'-11", not the 26'-9" it read until 2026-08-29: W-S-BD-N moved
              # 2" north with the y=26'-6" line and at 26'-9" the mat would have run 3/8"
              # under the wall's own bottom plate.
              #
              # ** THE EAST LOBE WAS CUT BACK ON 2026-08-30 FOR THE 48" VANITY. ** The
              # cabinet stands x 95.62"..116.62", y 345.88"..393.88" and the mat used to run
              # straight under it -- `advisory.floor_heat_fixture_keepout` FAILed the moment
              # the vanity landed, and it is right to: heating cable under a closed-toe
              # cabinet has no way to dump its heat, and Schluter's own instructions forbid
              # it outright. The lobe now stops at y=343.88" and the middle at x=93.62",
              # which is the manufacturer's ** 2" ** standoff from a fixed cabinet on both
              # faces. 29.43 ft2 -> 27.31 ft2.
              #
              # ** THE 42.4 ft2 THIS COMMENT USED TO CLAIM WAS NEVER THE POLYGON'S AREA. **
              # The eight points below enclosed 29.43 ft2, not 42.4, so the "42.4 x 12 W" that
              # produced 510 W was wrong twice over -- wrong area, and `area x 12` is not a
              # thing you can buy. See the wattage note below.
              zone=(pt(ft(0, 5), ft(26, 11)), pt(ft(9, 7), ft(26, 11)),
                    pt(ft(9, 7), inch(343.88)), pt(inch(93.62), inch(343.88)),
                    pt(inch(93.62), ft(31, 3)), pt(ft(3, 3), ft(31, 3)),
                    pt(ft(3, 3), ft(28, 6)), pt(ft(0, 5), ft(28, 6))),
              system=RadiantSystem.ELECTRIC, spacing=inch(3.625), embed=in_slab(inch(0.5)),
              # ** 338 W IS A PART NUMBER, NOT AN ARITHMETIC RESULT. ** Schluter
              # DITRA-HEAT-E-HK cable is sold in fixed, UNCUTTABLE lengths, so this field is
              # a purchased nameplate: DHEHK12027, 26.7 ft2 / 338 W / 2.8 A at 120 V, the
              # largest unit that does not exceed the 27.31 ft2 zone. The surplus 0.61 ft2 is
              # the buffer zone Schluter requires. `spacing` is 3 5/8" (3-stud), which is what
              # puts 26.7 ft2 of cable at the 12.7 W/ft2 the ladder is rated at.
              #
              # ** RM-S-BATH1 HAS NO SUPPLY REGISTER EITHER. ** REG-S-EXH1 is ERV *exhaust*;
              # there is no REG-S-HP-BATH1. So this mat, like RM-M-BATH2's, is the room's ONLY
              # heat source. At Schluter's 18.6 BTU/h/ft2 delivered it puts out ~497 BTU/h.
              # The room's design loss has NOT been computed here (RM-M-BATH2's was, and came
              # to ~303 BTU/h over a room 15% smaller) -- so this one looks comfortable rather
              # than proven, and it is worth an hour with the block load before the permit set.
              watts=338,
              stat=pt(ft(1, 6), ft(32))),
]

# The hallway duct soffit (HRV + heat mains), plans/TODO.md's "2nd floor hallway dropped
# ceiling for HVAC" — dashed on plan, framed in 3D. Widened 2026-07-29 to enclose BOTH of
# System 1's ducts side by side; 14" drop clears duct + 2x4 framing/hangers.
# LR-S-HALL-GAP already washes the soffit's flanks at x=18'-6"/21'-6", so no new lighting.
#
# ** IT NOW RUNS y 2'-10"..27'-8", AND BOTH ENDS MOVED ON THE 2026-09-04 HP1 MOVE. **
# The air handler used to live at this box's south end; then (2026-08-30) in SF-S-HP1 in
# RM-S-STUDY2's ceiling; it is now in the ceiling of RM-S-NCLOSET and the north hall, and
# the trunk runs SOUTH out of it. So:
#
#   NORTH END y=27'-8" — it ABUTS SF-S-HP1 there, never overlaps it. Overlapping soffits
#   are unchecked *as soffits*, but SF-S-HP1's end blocking would interpenetrate this box's
#   bottom rails, and that is a plate/blocking pair away from any junction, so the 10" gate
#   in checks/structural/interference.py does NOT excuse it. Abut, or take a new FAIL.
#
#   SOUTH END y=2'-10" — back out to where it was before 2026-08-30, because reversing the
#   trunk strands DU-S-HP-SOUTH-RISE, which has to reach y=3'-4" to hand off to
#   DU-S-HP-SOUTH. The old argument for stopping at 7'-6" was ledger-W-S-SS2-stringer-1,
#   the 2x10 carrying ST-S2A's stringer on the wall at y 104 1/8"..105 5/8", raking through
#   this z band from x=273 7/8" eastward. That argument bound a 77"-wide box reaching
#   x >= 22'-9 7/8". This box is 35" wide and tops out at x=21'-5 1/2"; it never touches
#   the ledger. The 4.4 sf of RM-S-STUDY2 ceiling south of y=7'-6" comes back down to
#   7'-10", and that is a real, chosen cost.
#
# WIDTH: widened from the plan's 2'-8" to 35" (x 18'-6 1/2"..21'-5 1/2", centred on the duct
# centrelines) because the two 14" trunks need 28" side by side plus 2" for hangers and
# flanges, and a finished box gives up its lining and both ladder rails before any of that.
# The arithmetic used to be written out here and was nobody's to re-run; since 2026-08-25
# `mep.duct_soffit_occupancy` derives the clear section from THIS soffit's own drop, member
# and lining and measures every occupant against it. Read the check, not a comment.
# The box now carries the 18x8 supply trunk and, at its south cap, DU-S-HP-SOUTH-RISE as a
# COLLINEAR reducer — the old east dogleg only ever existed to clear the old machine.
# Face elevation unchanged at 7'-10"; ED-S-HALL-CAN1/2/3 (all south of y=27'-8") set into it.
SOFFITS = [
    Soffit(uid="CSF601AAAA", tag="SF-S-DUCT",
           outline=(pt(ft(18, 6.5), ft(2, 10)), pt(ft(21, 5.5), ft(2, 10)),
                    pt(ft(21, 5.5), ft(27, 8)), pt(ft(18, 6.5), ft(27, 8))),
           # ** THE FACE IS PINNED, NOT DROPPED (2026-09-07). ** 7'-10" AFF is a stated
           # design elevation — the paragraph above quotes it and DU-S-HP-SOUTH-RISE is sized
           # to the cavity it leaves. `drop` measures from the plane overhead, and that plane
           # stopped being the storey's 9'-0" nominal when soffits started hanging off the
           # deck's real underside (`resolve/envelope.py`): 1/8" of ceiling took 1/8" of
           # cavity with it and the duct read 0.1" proud. 94" states the face itself.
           underside_elevation=inch(94),
           framing=FramingSpec(member="2x2", spacing=inch(16))),
    # THE AIR-HANDLER BOX — the ceiling of RM-S-NCLOSET and the north end of RM-S-HALL,
    # abutting SF-S-DUCT on the y=27'-8" seam and reading as one continuous soffit with it.
    # It moved here from RM-S-STUDY2 on 2026-09-04, with the outdoor unit (params/hp1_north_pad.py).
    #
    # ** ONE RECTANGLE. ** `soffit_clear_section` frames axis-aligned rectangles only; a
    # non-rectangular outline returns None and every occupant goes UNKNOWN rather than
    # graded. This box is FLUSH on all four finished faces — it IS the closet/hall ceiling,
    # not a bulkhead in a wide room, so there is no shadow-gap inset here the way there is
    # on SF-S-DUCT and SF-S-SUITE. That flushness is what forces W-S-BW4's retype to
    # INT_2X4_RC (see its block above): without it the east face jogs 1/2" at y=30'-10" and
    # the outline stops being a rectangle at all.
    #
    # 40 3/4" (x) x 7'-9 3/8" (y), so the LONG axis is y and `soffit_clear_section` measures
    # every occupant ACROSS x: 36.50" clear across, 18.25" clear cavity at a 21" drop. That
    # ordering is load-bearing — a box longer in x would have graded the trunk's travel as
    # its "width".
    #
    # THE LANES, west -> east: 1 7/8 | cabinet 21 1/4 | 2 3/8 | return 10 | 1. The machine
    # is turned (rotation=deg(90)), so its 43 1/2" runs ALONG the box where there is 7'-9"
    # and no pressure, and only the 21 1/4" case depth competes for the 36.50". The one
    # machine-graded pair is cabinet<->return at 2 3/8" against the 2" HANGER_GAP_M. The
    # heat strip sits south of the cabinet in the discharge, not beside it, and EQ-S-ERV-MIX
    # sits at the SOUTH end on the return: 16 + 2 + 10 = 28.00 against 36.50, 8 1/2" spare.
    #
    # DROP 21", FACE 7'-3" — today's proven condition, kept deliberately. 24" was considered
    # and rejected: `room_floor_elevation` measures from the storey datum, so a reported
    # 7'-0" is about 6'-11 1/4" real and no check would ever report it. 7'-3" clears IRC
    # R305.1's 7'-0" honestly, graded by `code.R305_ceiling_height` off the room's minimum
    # underside.
    #
    # `framing` is a LADDER WITH TWO STOCKS. `plate_member="2x2"` holds the RAILS at the
    # size that sets this cavity; `member="2x4"` gives the rungs I = 0.984 in^4 against
    # IRC R301.7's L/360 (`structural.soffit_rung_span`). Upsizing one shared profile would
    # widen the rails and eat the cavity instead.
    #
    # THE PRICE, STATED PLAINLY. RM-S-STUDY2 gets ~29 sf of its ceiling back to full height
    # and the remainder rises 7"; RM-S-NCLOSET's whole ceiling and about 7'-9" of the north
    # hall drop to 7'-3", and the closet loses 1/2" of width to the RC channel. That is the
    # trade, made with open eyes: a study people work in against a closet and a hall's dead
    # end. `RM-S-HALL`'s graded clear_height is unchanged at 8'-11 1/2" — the check's
    # unsoffited-area escape holds. A modelled ceiling access panel goes in under the
    # cabinet (plan/placeables.py::FURN-S-NCLOSET-AP), which the old box never had.
    Soffit(uid="6DAADXAD7P", tag="SF-S-HP1",
           outline=(pt(ft(18, 3.375), ft(27, 8)), pt(ft(21, 8.125), ft(27, 8)),
                    pt(ft(21, 8.125), ft(35, 5.375)), pt(ft(18, 3.375), ft(35, 5.375))),
           drop=inch(21),
           framing=FramingSpec(member="2x4", plate_member="2x2", spacing=inch(16)),
           # ** THE SERVICE HATCH IS FRAMED, NOT JUST DRAWN. ** The lid is
           # FURN-S-NCLOSET-AP (plan/placeables.py); THIS is the hole it covers, and until
           # `Soffit.openings` existed the generator laid a 2x4 rung straight through the
           # middle of it at y=33'-0 5/8" with nothing to report the collision — a panel
           # the model said could not be opened.
           #
           # 30" (x) x 29" (y), clear, at x 18'-10"..21'-4" by y 31'-10"..34'-3". It heads
           # off exactly ONE station (the rung at y=33'-0 5/8") between the rungs at
           # 31'-8 5/8" and 34'-4 5/8", so the two headers span 32" along the box at
           # x=18'-10" and x=21'-4" and the cut rung leaves a 4 1/2" stub west and a 2"
           # stub east. `structural.soffit_opening` grades that header.
           #
           # It is wholly inside RM-S-NCLOSET (y 30'-10"..36'-0") and it sits under the
           # air handler's north two-thirds AND its return face at y=34'-0", which is the
           # point: one opening reaches the filter rack, the coil, the blower and the
           # condensate trap. A hand-sized panel between two rungs reaches none of them.
           openings=(SoffitOpening(
               tag="AO-S-HP1-AP",
               outline=(pt(ft(18, 10), ft(31, 10)), pt(ft(21, 4), ft(31, 10)),
                        pt(ft(21, 4), ft(34, 3)), pt(ft(18, 10), ft(34, 3)))),)),
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
    # (abutting SF-S-DUCT, reading as one continuous box). 36" of plan width for a single
    # 10" duct — `mep.duct_soffit_occupancy` prints what that leaves once the lining and the
    # ladders are taken off, so the number is not restated here.
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
# Run north to south: north is W-M-N2's inside gwb face (y=35'-5 3/8"), 9'-5"
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
                 # East edge is carried by bearing wall, so it needs no header: W-M-C5
                 # (which since 2026-07-28 starts at N-M-C3 on the stair wall's line, so it
                 # still reaches this edge's south end even though W-M-C4B under it is gone),
                 # plus W-M-C5B, joined 2026-08-24: the centre wall split at N-M-PAN1
                 # (y=32'-9") for RM-M-PANTRY, and this edge runs to y=35'-5 3/8", so the
                 # north 2'-8 3/8" of it is carried by the NEW segment. Named, not derived —
                 # without it structural.floor_opening_header emits a 9.4' LVL placeholder
                 # for an edge that is fully bearing-supported along its whole length.
                 #
                 # West edge: W-M-STRW covers 26'-6"..36'; W-M-STRW2, trimmed 2026-08-30 to
                 # exactly the 5 3/8" between N-M-STRJ and this edge's own south end
                 # (26'-0 3/8", fixed by the stair's tread count, not the wall grid), covers
                 # the rest. Both are needed: drop either tag and this whole ~9'-4" edge
                 # reads as unsupported, and structural.floor_opening_header emits a full
                 # LVL header for it rather than the 5 3/8" that actually went missing — see
                 # W-M-STRW2's comment in main.py.
                 bearing_refs=("W-M-STRW", "W-M-STRW2", "W-M-C5", "W-M-C5B")),
]

# The beam that lets the centre line be open. Per CLAUDE.md, x=18' is a
# bearing line footings-to-ridge, and opening it *without a beam* would dump ~1.5 klf of
# ridge thrust into the attic eave line rated for ~0.1 klf; this LVL is that bearing line
# for its 8'-6", and W-A-C2 lands on it. (That eave line was a 5'-0" knee wall when this was
# written and is a flat rafter plate since 2026-08-29 — which takes even less thrust, so the
# argument for the beam only got stronger.)
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
         assembly="BEAM_LVL", top_elevation=ft(20)),
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
# flight (west lane) rails on W-M-STRW's face (y 26'-10 3/8"..31'-10 3/8", well north of
# W-M-STRW2's 5 3/8" stub) — each 2" off its wall (bracket standoff).
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

# Structural deck: since 2026-08-21 split west/east at x=18' — open-web trusses west
# (services cross the webs), I-joists east — in params/second_deck.py (SECOND_ELEMENTS,
# tags FS-S-WEST/FS-S-EAST). Kept empty here rather than deleted so ELEMENTS below is
# unchanged. Precedent: STACK_SLEEVES in plan/mep_sleeves.py.
FLOOR = []

# The suite bedroom's four "tudor" posts (plans/TODO.md §Hardwood): custom 6-1/8" square
# elm timbers standing in W-S-W3's stud line, flush with the drywall plane. Deliberately
# NOT a change to EXT_2X6 — each post is a deviation within the stud line, so the
# wall assembly is untouched. Centre x=3-9/16" off the sheathing-ext plane; cut 8'-11 1/4"
# to top out flush with the 9' plate. y-positions keep >6" clear of both WT-2736 ROs.
POSTS = [
    Post(uid="CSK901AAAA", tag="P-S-TUDOR1", position=pt(inch(3.5625), ft(10, 8)),
         size="6.125x6.125", height=ft(8, 11.25), supported_by="FS-S-WEST",
         within_wall="W-S-W3", assembly="ELM_TIMBER"),
    Post(uid="CSK902AAAA", tag="P-S-TUDOR2", position=pt(inch(3.5625), ft(15, 4)),
         size="6.125x6.125", height=ft(8, 11.25), supported_by="FS-S-WEST",
         within_wall="W-S-W3", assembly="ELM_TIMBER"),
    Post(uid="CSK903AAAA", tag="P-S-TUDOR3", position=pt(inch(3.5625), ft(17, 4)),
         size="6.125x6.125", height=ft(8, 11.25), supported_by="FS-S-WEST",
         within_wall="W-S-W3", assembly="ELM_TIMBER"),
    Post(uid="CSK904AAAA", tag="P-S-TUDOR4", position=pt(inch(3.5625), ft(21, 4)),
         size="6.125x6.125", height=ft(8, 11.25), supported_by="FS-S-WEST",
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

PANELING = [
    # The suite's headboard band: the family's milled walnut, on the one surface in this
    # room that earns it. `walnut-tg` is DELIBERATELY the study wainscot's own tag — same
    # 4/4 T&G board, one mill order, one [wood_surfaces] row. (Unlike the floor it replaces,
    # there is no double-billing trap: both bands are wall area on the same table.)
    #
    # ** `walls=` IS NOT OPTIONAL. ** `room=` alone panels every bounding wall of the L —
    # all eight, ~50 lineal feet — including the window wall with its four flush elm tudor
    # posts (P-S-TUDOR1..4, `within_wall="W-S-W3"`), which the model cannot scribe around.
    #
    # ** `height` IS A BAND HEIGHT ADDED TO `offset`, NOT A TOP ELEVATION ** — see
    # resolve/paneling.py, which computes `offset + height` and clamps to the wall top.
    # `offset` defaults to 0, so ft(6) is a band 0 -> 6'-0". WP-M-STUDY-FELT in main.py
    # shouts the same thing for the same reason.
    #
    # `replaces_wall_finish` stays False: W-S-SN1/SN2 are INT_2X4_STAGGERED_GWB, which
    # carries its gypsum in `layers` and not in `default_lining`, so there is nothing to
    # replace — the reasoning main.py already records for WP-M-STUDY-FELT on this assembly.
    # Those two are also the staggered-stud SOUND wall between the suite and the vanity, so
    # 3/4" of solid wood on them adds a little mass to a wall built for exactly that.
    #
    # ED-S-SUITE-RC5 (16" AFF on W-S-SN1) sits inside the band: ordinary, but 3/4" of
    # combustible finish means a box extender per NEC 314.20. Nothing grades that; it is an
    # ordering note. The cap is unmodelled trim, as the study wainscot's is.
    WallPaneling(uid="0D53MRPGKZ", tag="WP-S-SUITE-HEADBOARD", room="RM-S-SUITE",
                 material_ref="walnut-tg", height=ft(6),
                 walls=("W-S-SN1", "W-S-SN2")),
]

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *FLOOR_HEAT, *SOFFITS,
            *FLOOR_OPENINGS, *BEAMS, *STAIR_GUARDS, *STAIR_HANDRAILS, *FLOOR, *POSTS,
            *STAIRS, *PANELING]
