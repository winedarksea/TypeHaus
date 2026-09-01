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
    # Plain flush split on the east wall (2026-07-28): used to be the mechanical chase's SE
    # corner (N-S-CH3); kept as its own node so W-S-BA-E1B's wall_ref in fixtures.py (the
    # hall-bath lav) doesn't move now that the chase itself has moved to the NW corner.
    Node(uid="CSN038AAAA", tag="N-S-BA-SPLIT", position=pt(ft(10), ft(33, 4))),
    # The mechanical chase moved NE -> NW corner of the hall bath (2026-07-28) to stack on
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
    # The plant room's two exterior walls carry PLANT_EXT_2X6_HUMID, not CATLIN_EXT_2X6:
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
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-S2"),
    Wall(uid="CSW103AAAA", tag="W-S-E1", start_node="N-S-SE", end_node="N-S-E1",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E1"),
    Wall(uid="CSW102BAAA", tag="W-S-E2", start_node="N-S-E1", end_node="N-S-E2",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E1"),
    # stacks_on repointed to W-M-E1 (2026-08-24): main.py merged W-M-E1/E2 into one wall
    # for WIN-M-EAST-MID, retiring the W-M-E2 tag. The resolver links only one upper wall
    # per lower wall, and W-S-E1 already claims that slot, so this segment's own
    # STOREY_STACK/WALL_FOUNDATION boundary condition is dropped rather than merely
    # repointed — see the note on the merged wall in main.py.
    Wall(uid="CSW104AAAA", tag="W-S-E3", start_node="N-S-E2", end_node="N-S-E3",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E1"),
    Wall(uid="CSW105AAAA", tag="W-S-E4", start_node="N-S-E3", end_node="N-S-NE",
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.BEARING, stacks_on="W-M-E1"),
    Wall(uid="CSW107AAAA", tag="W-S-N1", start_node="N-S-NE", end_node="N-S-B5",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N1"),
    # Re-pointed W-M-N1 -> W-M-N1B (2026-08-24): the main storey's north wall split at
    # x=24'-4" for RM-M-PANTRY's east partition, and this segment (x 21'-11"..18'-0") sits
    # entirely under the WESTERN half. Left naming W-M-N1 it would have been one of two
    # authored tiebreakers for the same lower wall, and the resolver links only one upper
    # wall per lower — so the segment actually over it would have lost the edge.
    Wall(uid="CSW135AAAA", tag="W-S-N1B", start_node="N-S-B5", end_node="N-S-N1",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N1B"),
    Wall(uid="CSW108AAAA", tag="W-S-N2", start_node="N-S-N1", end_node="N-S-N2",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N2"),
    # Split at N-S-CH2, where the mechanical chase's east wall tees into the north wall
    # (moved to the NW corner 2026-07-28 — see the node comment above).
    Wall(uid="CSW109AAAA", tag="W-S-N3", start_node="N-S-N2", end_node="N-S-CH2",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
         assembly="CATLIN_EXT_2X6", alignment=face("sheathing-ext"), top=ft(9),
         structural_role=StructuralRole.NONBEARING, stacks_on="W-M-N3"),
    Wall(uid="CSW153AAAA", tag="W-S-N3B", start_node="N-S-CH2", end_node="N-S-NW",
         layer_materials=(LayerMaterial(layer="cladding", material="board-batten-24"),),
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
    # ** MEASURED AND NOT TAKEN (2026-08-30). ** W-S-SS1 lays out from N-S-C1, which is off
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
    Wall(uid="CSW121AAAA", tag="W-S-SS2", start_node="N-S-B1", end_node="N-S-E1",
         assembly="INT_2X4_PARTITION", top=ft(9)),
    # --- east bedroom block ------------------------------------------------------
    #
    # ** THE FIVE SLEEPING-SIDE PARTITIONS ARE INT_2X4_RC (2026-08-30). ** They were
    # INT_2X4_PARTITION at STC 36 — a bedroom-to-bedroom wall you can hold a conversation
    # through, and three corridor walls between the stair head and every bedroom door.
    # INT_2X4_RC is the same 2x4 stud and the same 5/8" board with 1/2" resilient channel on
    # ONE face: STC 48, twelve points, and 12 points is the difference between "audible" and
    # "not a nuisance" on every published scale. W-S-BW4 is NOT retyped — it faces
    # RM-S-NCLOSET, a closet, and a closet does not need an acoustic wall.
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
    Wall(uid="CSW125AAAA", tag="W-S-BW4", start_node="N-S-B4", end_node="N-S-B5",
         assembly="INT_2X4_PARTITION", top=ft(9)),
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
    # South wall — plain 2x4 (2026-08-30). Nothing actually backs onto this wall: the lav
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
    # a comparable single-layer build lists around STC 48 against the partition's 36).
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
    # plan/assemblies.py's CATLIN_INT_2X6_BRG_PLUMBING has the whole argument.
    Wall(uid="CSW149AAAA", tag="W-S-BD-N1B", start_node="N-S-V2", end_node="N-S-BA1",
         assembly="CATLIN_INT_2X6_BRG_PLUMBING", top=ft(9),
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
    # CATLIN_INT_2X6_BRG_PLUMBING is the same 6.77" total, so no face moves, no room area
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
         assembly="CATLIN_INT_2X6_BRG_PLUMBING", top=ft(9),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CSW150AAAA", tag="W-S-BA-E1B", start_node="N-S-BA-SPLIT", end_node="N-S-BA1",
         assembly="CATLIN_INT_2X6_BRG_PLUMBING", top=ft(9),
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
    # Pulled 3" west of its original 1'-4.5" (2026-07-29): at that offset the door's own
    # king stud landed inside N-S-BA1's corner square and punched into W-S-BA-E1B's end
    # stud (the same class of overlap as N-M-MECH2 in test_wall_corner_and_opening_framing).
    # ** IT STAYS AT 1'-1 1/2", AND `structural.door_framing_module` REPORTS IT. ** Centre
    # 28 1/2" is 3 1/2" off the module and costs one extra stud. The only station on this wall
    # that would fix it is 32", and 32" leaves the RO 2 1/2" from N-S-V2 — the king and jack
    # on that side would be inside the corner pack, which is nine `member_interference`
    # overlaps traded for one stud. (It also needs `flip_swing` there, because at 32" the old
    # swing sweeps FX-S-BATH1-LAV; that part works, and is moot.) The wall is 5'-1" long and
    # carries a 30" leaf: there is no station on it that clears both ends.
    Door(uid="CSD208AAAA", tag="D-S-BATH1", host="W-S-BD-N1B", type_ref="DT-INT-SWING30",
         position=from_node("N-S-V2", ft(1, 1.5))),                      # x 8'-3"
    Door(uid="CSD217AAAA", tag="D-S-NCLOSET", host="W-S-CLN-S", type_ref="DT-INT-SWING30",
         position=from_node("N-S-C3D", ft(0, 8.5)), flip_swing=True, flip_hinge=True),                     # x 19'-11 1/2"
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
    #
    # Both doors moved 1'-0" inward on 2026-08-24 (13'-8"/22'-4" -> 14'-8"/21'-4"), still an
    # exact mirror about x=18'-0". 14'-8" is a stud line on W-S-S1's grid, and on W-M-S1's
    # below it, which is the point: WIN-M-BED-S2 moved there to column under this door.
    # The inward move also opened the west door's gap to WIN-S-PLANT2 from 7" to 1'-7";
    # it leaves 10" of wall to each inside corner, which is the trade.
    Door(uid="CSD218AAAA", tag="D-S-DECK-W", host="W-S-S1", type_ref="DT-EXT-FRENCH60",
         position=from_node("N-S-SW", ft(12, 2)), flip_swing=True),                       # x 14'-8"
    Door(uid="CSD211AAAA", tag="D-S-DECK-E", host="W-S-S2", type_ref="DT-EXT-FRENCH60",
         position=from_node("N-S-S1", ft(0, 10)), flip_swing=True),                       # x 21'-4"
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
    # 2026-08-27: retyped WT-2736-T -> WT-2748-T, 36" -> 48" tall. Same 27" bearing width,
    # so the mirrored 4'-0"/13'-4"/22'-8"/32'-0" beat and every offset below are untouched;
    # the head moves 6'-0" -> 7'-0". It still columns with WIN-M-LIV-E1 below, which took
    # the same retype the same day.
    Window(uid="CSX314AAAA", tag="WIN-S-STUDY3", host="W-S-E1", type_ref="WT-2748-T",
           position=from_node("N-S-SE", ft(2, 10.5)), sill_height=ft(3)),     # y 4'-0"
    # BED1/BED2 ARE BACK ON THE 27" BEARING CAP (2026-08-25), AND THE 2026-08-01 NOTE THAT
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
    # delivers 210 cfm of outdoor air — the same exception RM-M-LIVING has always leaned
    # on. What the 54" bought was compliance without the exception; that is what is spent
    # here, not compliance itself. R310 egress is unaffected (9.00 sf > 5.7 net).
    # Head drops 7'-6" -> 7'-0"; width, sill, centres and the mirror about the house
    # centreline are unchanged (same 27" bearing RO), so nothing on the facade or in the
    # framing moved. BED1 keeps the -T twin for R308.4.5's stair band.
    Window(uid="CSX301AAAA", tag="WIN-S-BED1", host="W-S-E2", type_ref="WT-2748-T",
           position=from_node("N-S-E1", ft(3, 2.5)), sill_height=ft(3)),    # y 13'-4"
    Window(uid="CSX302AAAA", tag="WIN-S-BED2", host="W-S-E3", type_ref="WT-2748",
           position=from_node("N-S-E2", ft(3, 10.5)), sill_height=ft(3)),   # y 22'-8"
    # BED3 MOVED OFF THE ROW (2026-08-27): retyped WT-2736 -> WT-1424 and moved 32'-0" ->
    # 34'-0" centre, matching WIN-M-KIT-E below in both size and station so the two column.
    # RM-S-BED3 loses 4.4 sf of glass by it (6.75 -> 2.33) and joins BED1/BED2 on R303.1
    # Exception 1; its R310 egress was never this window's job — WIN-S-HALL-N carries it.
    # WIN-A-E-N moved 32'-8" -> 34'-0" the same day (attic.py) to complete a three-storey
    # 14" column on the east face. ``from_node`` is the near jamb, so 34'-0" - 7" = 33'-5"
    # off N-S-E3 at y=26'-8" -> 6'-9". The east second-storey row is now three units, and
    # the mirror test's north member is gone with it. Sill stays on the 3'-0" east-face
    # datum; WIN-M-KIT-E's own 3'-6" is a counter height and does not travel up.
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
    Window(uid="CSX307AAAA", tag="WIN-S-PLANT2", host="W-S-S1", type_ref="WT-3048-HP-T",
           position=from_node("N-S-SW", ft(8, 1)), sill_height=ft(2, 8)),     # x 9'-4"
    # The plant room's west window is on W-S-W4, a bearing wall, so it takes the 27" bearing
    # type, not the 30" south-glazing one ("resize windows to fit the grid", CLAUDE.md).
    # Sill raised to 3'-0" (2026-07-30) for the shared 6'-0" head line. Unmoved by the
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
    # Re-hosted off W-S-N3 (2026-07-28): W-S-N3B is now the chase's own wall, not the
    # bathroom's. Nudged to 8" off N-S-CH2 (2026-07-29): at 1' the RO straddled the module
    # stud line instead of centering in the bay, breaking two studs and pulling in a
    # header/jacks a 14" RO should never need
    # (test_catlin_small_windows_have_no_header_and_keep_their_flanking_studs).
    Window(uid="CSX312AAAA", tag="WIN-S-BATH-W", host="W-S-W1", type_ref="WT-1424-T",
           position=from_node("N-S-CH3", ft(1, 1.875)), sill_height=ft(4)),
    # Moved 29'-4" -> 28'-0" (2026-07-30 facade pass), then back to 29'-4" (2026-08-26)
    # when the whole three-storey column returned there to bring WIN-M-KITCH onto the
    # kitchen sink below. WIN-A-N2 above moved with it, so the north facade keeps its one
    # exact three-storey column at the new station.
    Window(uid="CSX313AAAA", tag="WIN-S-HALL-N", host="W-S-N1", type_ref="WT-3036",
           position=from_node("N-S-NE", ft(5, 5)), sill_height=ft(3)),        # x 29'-4"
    # Stairwell daylight (2026-07-30 facade pass): the north facade was blank from the
    # entry column to x=21'-11". Centre x 12'-8" is the stud line inside the arriving
    # upper flight's lane. WIN-A-N1 could stack on this (12'-8" is a stud line on W-A-N2
    # too) but deliberately stays at 7'-4" instead, so the north gable reads
    # near-symmetric about the ridge — the same read that governs the south gable pair.
    Window(uid="CSX315AAAA", tag="WIN-S-STAIR-N", host="W-S-N2", type_ref="WT-3036-T",
           position=from_node("N-S-N1", ft(3, 5)), sill_height=ft(3)),        # x 12'-8"
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
# ** IT STOPS AT y=7'-6" SINCE 2026-08-30, AND WHAT IT USED TO REACH FOR IS SF-S-HP1. **
# It ran y 6'-0"..34'-0" so that its south end could hold the air handler. That end was
# 30 3/4" clear and the machine it was sized around — EQ-T-GREE-SLIM24, 43 x 21 — did not
# exist: an explicit "REPRESENTATIVE PLACEHOLDER … TODO verify datasheet" whose only real
# 43 3/8"-wide match, Gree's discontinued low-static DUCT24HP230V1AD, tops out at 589 cfm
# against the 750 this whole duct system is sized to. The real machine (see
# plan/electrical.py::EQ-T-GREE-FLEXX-ULTRA-24-AH) is 43 1/2" wide, which no 35" box holds, and
# the placeholder's 21" case is what plugged the lane and kept plans/TODO.md's south-branch
# riser open for weeks. The hall box is now a pure trunk run and nothing else: it costs the
# hall nothing, the cove and ED-S-HALL-CAN1/2/3 are untouched, and the machine moved into a
# wider, deeper box in RM-S-STUDY2's ceiling where the width is free.
#
# The seam is at y=7'-6" and NOT at W-S-SS1/SS2's south face (8'-9 5/8"), because ST-S2A's
# 2x10 stringer ledger is bolted to that wall at y 104 1/8"..105 5/8" and rakes down through
# this box's z band from x=273 7/8" eastward. SF-S-HP1 is 77" wide and would land its north
# end blocking straight on it — the one member of that stair the interference check does not
# excuse. 7'-6" clears the ledger by 14"; the hall box carries the trunk and the ERV feed
# the extra 18" south, which costs 4.4 sf of hall ceiling that was already soffited.
#
# WIDTH: widened from the plan's 2'-8" to 35" (x 18'-6 1/2"..21'-5 1/2", centred on the duct
# centrelines) because the two 14" trunks need 28" side by side plus 2" for hangers and
# flanges, and a finished box gives up its lining and both ladder rails before any of that.
# The arithmetic used to be written out here and was nobody's to re-run; since 2026-08-25
# `mep.duct_soffit_occupancy` derives the clear section from THIS soffit's own drop, member
# and lining and measures both trunks, EQ-S-HP1-AH and EQ-S-HP1-STRIP against it. Read the
# check, not a comment — and if the 2x2 ever becomes a 2x4, the check moves and this note
# does not. Face elevation unchanged at 7'-10"; ED-S-HALL-CAN1/2/3 set into it.
SOFFITS = [
    Soffit(uid="CSF601AAAA", tag="SF-S-DUCT",
           outline=(pt(ft(18, 6.5), ft(7, 6)), pt(ft(21, 5.5), ft(7, 6)),
                    pt(ft(21, 5.5), ft(34)), pt(ft(18, 6.5), ft(34))),
           drop=inch(14),
           framing=FramingSpec(member="2x2", spacing=inch(16))),
    # THE AIR-HANDLER BOX (2026-08-30) — the new wide bulkhead in RM-S-STUDY2's ceiling,
    # abutting SF-S-DUCT on the y=7'-6" seam and reading as one continuous soffit with it,
    # the same way SF-S-SUITE does at x=18'-6 1/2".
    #
    # ** TWO ABUTTING RECTANGLES, NOT AN L. ** `soffit_clear_section` frames axis-aligned
    # rectangles only; a non-rectangular outline returns None and every occupant in the box
    # goes UNKNOWN rather than being graded. So the shape is authored as two boxes.
    #
    # WHY IT IS IN THE STUDY AND NOT THE HALL, THE STAIR WELL OR THE LOFT: the hall is
    # 40 3/4" clear wall to wall (36 1/2" once a box gives up its lining and both ladders,
    # against a 43 1/2" cabinet) and LR-S-HALL-GAP's cove sits on the soffit's flanks;
    # ST-S2A's WELL is 3'-0" wide with no service face, and enclosing it pulls in
    # code.R302_7_under_stair_protection; the attic loft is the fallback, not the answer,
    # because it puts the machine outside the thermal envelope it serves.
    #
    # ** IT RUNS UNDER ST-S2A'S FLIGHT AND THAT IS DELIBERATE. ** The stair climbs west
    # along W-S-SS2 from x=32'-5 3/8" to the attic at x=22'-5 3/8", so its underside over
    # this box's north-east corner is at or above the box's own 7'-3" face — the two finish
    # as one plane, and the 3.8 sf of box that laps the flight is ceiling the stair was going
    # to soffit anyway. What the box may NOT touch is `ledger-W-S-SS2-stringer-1`, the 2x10
    # carrying that stringer on the wall at y 104 1/8"..105 5/8": that is a real member and
    # `structural.member_interference` reports it (it excuses the treads and stringers over
    # a soffit, not the ledger under one). Hence the y=7'-6" seam. East of about x=22'-7"
    # the ladders hang off the stringers rather than the deck, which is framing, not
    # geometry the model carries — no duct, no machine and no box goes into that corner.
    #
    # THE BOX RUNS NORTH-SOUTH ON PURPOSE. `soffit_clear_section` calls the LONGER plan
    # dimension the long axis and measures every occupant's width ACROSS it — so a box 77"
    # in x had to be more than 77" in y, or the check would have graded the trunk's whole
    # travel as its "width" and the two lanes beside the machine would never have been
    # compared to it at all. 80" in y against 77" in x; that ordering is load-bearing.
    #
    # SECTION, all derived by the check and none of it restated as arithmetic here: 77"
    # finished x 21" drop gives 72 3/4" clear x 18 1/4" clear. It carries, side by side, the
    # 43 1/2 x 21 1/4 x 18 1/8 cabinet, the 10x6 south-branch riser and its take-off leg, the
    # 4.6 kW heat kit in the discharge plenum, the 6" ERV mixing-box feed and the mixing box
    # itself, with 2" of hanger gap between every pair — HANGER_GAP_M, not a preference.
    #
    # ** THE DROP WENT 17" -> 21" ON THE FLEXX ULTRA RETYPE. ** The machine that replaced
    # EQ-T-GREE-DUC24 is 18 1/8" deep where the DUC24 was 11 13/16"; 21" of drop derives
    # 18 1/4" of clear cavity, which holds it with 1/8" to spare. Note what the deeper box
    # does NOT buy: the graded axis here is x (the box is 80" in y against 77" in x, so
    # `soffit_clear_section` measures every occupant ACROSS x), and the cabinet's long
    # dimension is what competes for that 72 3/4". It comes down 44 1/2" -> 43 1/2" — about
    # an inch of relief, not eight. The 21 1/4" runs ALONG the box, where there is 78 3/4"
    # and no pressure. What the shallower plan depth really bought is 8 7/16" of clear box
    # north of the discharge, and DU-S-HP-SOUTH-RISE's take-off leg and the heat kit are
    # what went into it (plan/electrical.py, plan/mep_hvac.py).
    #
    # Underside 7'-3", which still clears IRC R305.1's 7'-0" — graded by
    # `code.R305_ceiling_height` off the room's minimum underside, not off
    # `Storey.default_ceiling_height`. A 36k FLEXX Ultra was rejected partly here: its
    # smallest cabinet dimension is 21 1/4", needing a 24" drop, which lands the underside
    # exactly ON the 7'-0" floor with nothing in hand.
    #
    # `framing` is a LADDER WITH TWO STOCKS, and that is the 2026-08-31 fix, not a taste
    # call. `_frame_one` used to lay rails and rungs out of one profile; the rungs here span
    # the full 72 3/4" clear width laid flat, and a 2x2 rung deflects L/212 under 5 psf of
    # ceiling dead load — short of IRC R301.7's L/360, which `structural.soffit_rung_span`
    # now says out loud. `plate_member="2x2"` holds the RAILS at the size that sets this
    # cavity — so `across` is still 72 3/4" and z[0] does not move, which is what keeps
    # DU-S-HP-RET's 14" duct in its cavity — while `member="2x4"` gives the rungs I = 0.984
    # in^4 and L/495. Upsizing one shared profile would have widened the rails instead and
    # evicted EQ-S-ERV-MIX from the box.
    #
    # THE PRICE, STATED PLAINLY: 43 sf of RM-S-STUDY2's 160 sf ceiling drops to 7'-3", in
    # the room's north-west quadrant, of which ~4 sf was already under the old SF-S-DUCT and
    # ~4 sf is under ST-S2A. The study keeps its whole south and east glazing wall, its
    # table and its chairs at full 9'-0" height. That is the cost of keeping the machine
    # inside the thermal envelope, and the hall pays none of it.
    Soffit(uid="6DAADXAD7P", tag="SF-S-HP1",
           outline=(pt(ft(18, 4), ft(0, 10)), pt(ft(24, 9), ft(0, 10)),
                    pt(ft(24, 9), ft(7, 6)), pt(ft(18, 4), ft(7, 6))),
           drop=inch(21),
           framing=FramingSpec(member="2x4", plate_member="2x2", spacing=inch(16))),
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

# The beam that lets the centre line be open (2026-07-28). Per CLAUDE.md, x=18' is a
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
# NOT a change to CATLIN_EXT_2X6 — each post is a deviation within the stud line, so the
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

ELEMENTS = [*NODES, *WALLS, *OPENINGS, *ROOMS, *ALARMS, *FLOOR_HEAT, *SOFFITS,
            *FLOOR_OPENINGS, *BEAMS, *STAIR_GUARDS, *STAIR_HANDRAILS, *FLOOR, *POSTS,
            *STAIRS]
