# haus: editable
# Garage — freestanding 24'x24' ICF stem + 2x6 wood walls, 4' north of the house
# (west walls aligned). Wood walls sit on the ICF stem 22" above grade; the storey
# elevation is the top of the stem. Overhead door faces east (driveway side).
from typehaus import (
    Alarm,
    AlarmKind,
    Connector,
    ConnectorKind,
    Door,
    Downspout,
    EaveGutter,
    EaveTrim,
    FasciaBoard,
    Flashing,
    FoundationWall,
    Node,
    Occupancy,
    Pitch,
    Railing,
    RailingKind,
    Roof,
    RoofForm,
    Room,
    Stair,
    StructuralRole,
    TrimKind,
    Wall,
    Window,
    face,
    from_node,
    ft,
    inch,
    pt,
)

# The garage's two N-S wall lines, published so the ICF stem (params/foundations.py), the
# slab, and the breezeway (params/breezeway.py) all derive from one number.
#
# 40'-8 5/8" is set by the breezeway off the *cladding*, not the stem: the stem's exterior
# EPS face is coplanar with the wood wall's SHEATHING face (both land on this line), so the
# most-proud plane is the 7/8" corrugated panel at y = 40'-7 3/4" — what the breezeway
# deck/glazing butt against, 4'-0 1/2" north of the house's cladding face
# (y = 36'-7 1/4"): one UNCUT 4'-0" polycarbonate panel with a 1/2" reveal.
#
# Moved 5 5/8" south from 41'-0" on 2026-08-15 when the stem was aligned to it and dropped
# from an 8" core to 6". Moving the wall lines with the stem (rather than aligning the stem
# alone) keeps the breezeway slot and its uncut panel unchanged — see CLAUDE.md's ICF
# stem/wood-wall coplanarity note; do not move these nodes independently of the stem.
#
# ** MOVED 1/2" NORTH ON 2026-08-23, A FURTHER 1" ON 2026-08-26, 3/8" MORE THE SAME DAY,
# AND 3/8" AGAIN ON 2026-08-31, and the whole 24'x24' went with it every time. ** The
# Swinburne truss wall put the house's cladding face 1/2" further out (5.02" -> 5.5" proud
# of the y=36' sheathing plane); the catlin truss then put it another 1" out (5.5" -> 6.5"),
# the four flat girt layers standing where the 3 1/2" outrigger band did; then the 1 1/4"
# exposed-fastener PBR panel replaced the 1/2" snap-lock seam and took it to 7.25".
#
# That third move was 3/4" at the house and only 3/8" here, and the difference was a
# correction rather than a rounding: params/breezeway.py carried a 3/8" rainscreen furring
# on the GARAGE face that GARAGE_WALL_2X6 dropped on 2026-08-20. Fixing that gave back
# exactly half the move.
#
# ** THE FOURTH MOVE IS THIS BUILDING'S OWN, AND IT COMES FROM THE GARAGE END OF THE SLOT.
# ** GARAGE_WALL_2X6 went to a 7/8" corrugated exposed-fastener panel on 2026-08-31 where a
# 1/2" nail strip stood (and the Zip-R behind it became 5/8" CDX, which moves nothing: both
# the old zip-R face and the new sheathing face land on this node line by the wall's own
# `alignment`). 3/8" more panel standing proud of an unmoved node line is 3/8" less clear
# slot, so the node line goes 3/8" north to give it back.
#
# Each move spends the breezeway's reveal exactly: the slot closes to 4'-0" on the nose and
# an uncut 4'-0" sheet cannot be glazed into an opening it exactly fills. Ripping the sheet
# was the detail-scale answer and is retired; this is the site-scale one, and it is the
# better trade because the reveal is the only thing in the slot that was ever free.
#
# ** DO NOT INSTEAD RECESS THE SHEATHING BEHIND THE NODE LINE to hold the cladding face
# still. ** That re-opens the 2026-08-15 rain-shelf defect the stem alignment was built to
# fix: the stem's exterior EPS face would then stand proud of the wall above it, and the
# ledge that leaves is exactly the shelf water sits on.
# BOTH lines move together — the garage stays 24'-0" square, the stem, footings, slab and
# breezeway all derive from these two numbers, and nothing north of the house is dimensioned
# to a property line closer than 40'. Do NOT move the stem alone: CLAUDE.md's 1/2"
# ``_axis_match`` tolerance means the whole foundation follows via ``Footing.center_on``.
GARAGE_Y_SOUTH = ft(40, 8.625)
GARAGE_Y_NORTH = ft(64, 8.625)

# ICF stem height above grade == this storey's elevation (wood walls sit on the stem top).
# Published so the storey table, the stem (params/foundations.py) and the overhead door's
# drop to grade all read one value instead of three copies of 1'-10".
GARAGE_STEM_REVEAL = ft(1, 10)

NODES = [
    Node(uid="CGN001AAAA", tag="N-G-SW", position=pt(ft(0), GARAGE_Y_SOUTH)),
    Node(uid="CGN002AAAA", tag="N-G-SE", position=pt(ft(24), GARAGE_Y_SOUTH)),
    Node(uid="CGN003AAAA", tag="N-G-NE", position=pt(ft(24), GARAGE_Y_NORTH)),
    Node(uid="CGN004AAAA", tag="N-G-NW", position=pt(ft(0), GARAGE_Y_NORTH)),
]

# 8'-4" plates, not 8'-0" (2026-08-21). The garage went down 4" with grade while
# D-G-SERVICE's threshold stayed pinned to the breezeway deck at 0'-0" — so the door climbed
# 4" inside its own wall and its 3-ply LVL header pushed straight through the top plate into
# the truss heels (structural.member_interference caught it). Growing the plates by the same
# 4" puts the garage roof back at the absolute elevation it had before the lift and restores
# the 8" the header needs above the rough head. The slab went down with grade too, so the
# interior clear height is unchanged.
WALLS = [
    Wall(uid="CGW101AAAA", tag="W-G-S", start_node="N-G-SW", end_node="N-G-SE",
         assembly="GARAGE_WALL_2X6", alignment=face("cdx-ext"), top=ft(8, 4),
         structural_role=StructuralRole.BEARING),
    # The overhead-door wall carried Western States "Classic Green" nail-strip for part of
    # 2026-08-26 and is back to the house white. The revert is one line: drop the
    # `layer_materials=` override and it is `GARAGE_WALL_2X6` like its three neighbours.
    # `standing-seam-nailstrip-26-green` is still in the catalog, referenced by nothing —
    # the same convention `glazed-green-brick` is kept under, so going green again is a
    # one-line change rather than a re-derivation.
    Wall(uid="CGW102AAAA", tag="W-G-E", start_node="N-G-SE", end_node="N-G-NE",
         assembly="GARAGE_WALL_2X6", alignment=face("cdx-ext"), top=ft(8, 4),
         structural_role=StructuralRole.NONBEARING),
    Wall(uid="CGW103AAAA", tag="W-G-N", start_node="N-G-NE", end_node="N-G-NW",
         assembly="GARAGE_WALL_2X6", alignment=face("cdx-ext"), top=ft(8, 4),
         structural_role=StructuralRole.BEARING),
    Wall(uid="CGW104AAAA", tag="W-G-W", start_node="N-G-NW", end_node="N-G-SW",
         assembly="GARAGE_WALL_2X6", alignment=face("cdx-ext"), top=ft(8, 4),
         structural_role=StructuralRole.NONBEARING),
]

# --- east brick wainscot (2026-08-26) ----------------------------------------------------
#
# A short off-white-brick wainscot on the two 4'-0" strips of east wall flanking the
# overhead door, wrapped 4'-0" further around each of the SE/NE corners onto the south and
# north walls (2026-08-26) — the most-seen, most-abused surface on the building. Modelled as
# its own short veneer wall standing in front of the existing wall, exactly W-B-BRICK's
# precedent (storeys/basement.py), because a full 3 5/8" wythe on a 1" cavity is not
# something a WallPaneling band can carry. Assemblies, the coursing table and the ledge
# form: plan/assemblies.py's GARAGE_BRICK_WAINSCOT / GARAGE_ICF_6_BRICKLEDGE. Brick unit:
# Glen-Gery Columbia Roman Maximus (glengery.com/brick-catalog/columbia-roman-maximus),
# swapped 2026-08-26 for the black colourway of the same unit — see assemblies.py's
# off-white-brick Material comment.
#
# ** FILED ON THE GARAGE STOREY, NEVER ON `basement`, and that is load bearing. **
# `_storey_is_conditioned` (checks/building_science/energy_scope.py) returns False for the
# garage (RM-GARAGE conditioned=False), so the veneer drops out of the block load cleanly.
# Filed on `basement` it would read as a foundation wall not between two conditioned rooms,
# `_is_envelope_wall` would return True, and this wythe would be summed into
# `building_science.energy_load` and `mep.heating_capacity` — silently inflating the
# heating/cooling load rather than erroring. The only escape would be adding the tag to the
# hard-coded `_FREESTANDING_WALL_PREFIXES` in engine code, i.e. leaking a house naming fact
# into the engine. Don't go there.
#
# ** THE NODES MUST BE NEW AND LOCAL. ** Node lookup is storey-scoped
# (resolve/topology.py's `_storey_nodes` filters `plan.storey_elements(storey_tag)`), and
# the garage stem is filed on the BASEMENT storey (params/foundations.py puts
# GARAGE_STEM_NODES into BASEMENT_ELEMENTS), so `N-GF-*` is invisible from here twice over
# — and a wall whose node does not resolve comes back None SILENTLY: no geometry, no
# finding. Even if the storeys matched, joining the stem's closed loop would hand this
# veneer that loop's outward sign and create tee junctions. `open_end=True` for the same
# reason W-B-BRICK's nodes carry it: two open ends, its own wall-graph component, no
# `integrity.wall_loop_open` ERROR.
#
# The y values are literals because this file is `# haus: editable` and the dialect bans
# arithmetic — they are GARAGE_Y_SOUTH, GARAGE_Y_SOUTH + OVERHEAD_DOOR_OFFSET (4'-0"),
# that + OVERHEAD_DOOR_WIDTH (16'-0"), and GARAGE_Y_NORTH, in that order. The two piers
# are 4'-0" flush with the door jambs BECAUSE the door offset is 4'-0"; they are not a free
# choice, and test_catlin_contract_m3.py pins them.
#
# ** x is the BRICK FACE, ft(24, 4.625), not the east node line, and that is deliberate. **
# The obvious authoring — nodes on x = 24'-0" with `alignment=face("air-gap-int")`, so the
# 1" cavity begins exactly on the plane where the wood wall's zip-R face and the stem's
# exterior EPS face already land (they are deliberately coplanar) — is geometrically right
# and puts the veneer's LAYOUT LINE on top of the stem's and the wood wall's. `_axis_match`
# (resolve/stacking.py) matches collinear axes within a 1/2" tolerance, so W-GF-E1 then had
# two candidates above it (W-G-E and this veneer) and `integrity.stack_ambiguous` was a hard
# ERROR. W-B-BRICK never hits this only because its own node line happens to sit 4.55" off
# the wall it stands against.
#
# Aligning on `face("brick-ext")` off a node line at the brick face says the same thing from
# the other end and puts the layout line 4 5/8" clear of the tolerance. Back of brick still
# lands at 24'-1" and the cavity still starts on 24'-0". Nothing in the 40'-7 7/8"
# breezeway chain is touched — that is a y-axis constraint and this projects on x.
#
# ** THE CORNER RETURNS PUSH TWO OF THESE NODES PAST THE ENVELOPE LINE, ON PURPOSE. ** The
# SE/NE corner returns (BRICK_WALLS below) are their own perpendicular veneer walls running
# along the south/north faces, each on its own `face("brick-ext")` node line offset 4 5/8"
# off ITS OWN envelope line (GARAGE_Y_SOUTH/GARAGE_Y_NORTH) — the same idiom as the east
# piers, rotated 90 degrees. For the two wythes to actually meet at a real outside corner
# instead of leaving a gap, the east pier's corner-adjacent node has to sit at the return's
# offset line too, not at the building's y = GARAGE_Y_SOUTH/GARAGE_Y_NORTH the un-wrapped
# pier used. N-G-BRICK-S-S and N-G-BRICK-N-N are therefore shared endpoints: the corner of
# the pier AND the corner of its return. Neither is `open_end` any more — a corner joining
# two wall segments is not a dead end, and the two true dead ends left are each return's own
# west tip.
BRICK_NODES = [
    Node(uid="9XGFXC1W6Y", tag="N-G-BRICK-S-S",
         position=pt(ft(24, 4.625), ft(40, 4))),
    Node(uid="1AVRM4GDPB", tag="N-G-BRICK-S-N", position=pt(ft(24, 4.625), ft(44, 8.625)),
         open_end=True),
    Node(uid="SDYMFBKVJ6", tag="N-G-BRICK-N-S", position=pt(ft(24, 4.625), ft(60, 8.625)),
         open_end=True),
    Node(uid="ESY1X83CXW", tag="N-G-BRICK-N-N",
         position=pt(ft(24, 4.625), ft(65, 1.25))),
    Node(uid="H4KBZK98W6", tag="N-G-BRICK-SRET-W", position=pt(ft(20, 4.625), ft(40, 4)),
         open_end=True),
    Node(uid="K3JVR3JJF1", tag="N-G-BRICK-NRET-W", position=pt(ft(20, 4.625), ft(65, 1.25)),
         open_end=True),
]

# Absolute elevations, off a garage grade of -2'-10". Coursing is Glen-Gery Black Roman
# Maximus, 1 5/8" + 3/8" joint == a 2" module (not modular's 2 2/3" — see
# plan/assemblies.py's GARAGE_BRICK_LEDGE_RISE). The shelf sits one course (2") ABOVE finish
# grade — the cheapest durability move there is, lifting the base course clear of the worst
# splash and snow-contact zone. 20 courses of field brick (40") then a sloped rowlock cap
# (4", the unit's 3 5/8" bed depth on edge — unaffected by the coursing change) land the top
# of brick at +1'-0" on the nose, and 2" of metal cap flashing over it puts the top of cap
# at 4'-0" above grade, ALSO on the nose: both anchors are unchanged from the original
# modular scheme, only the interior split moved.
WAINSCOT_LEDGE_TOP = inch(-32.0)       # -2'-8": the shelf, and the base course on it
WAINSCOT_BRICK_TOP = inch(12.0)        # +1'-0": top of the sloped rowlock
WAINSCOT_CAP_TOP = inch(14.0)          # +1'-2" == 4'-0" above grade

# ** AUTHORED NORTH NODE -> SOUTH NODE, and nothing will catch a flip. ** A lone component
# with no closed loop gets UNRECOVERABLE_WINDING_OUTWARD_SIGN = 1.0
# (resolve/orientation.py). The interior face sits at `-sign * normal(start->end)` where
# `normal(d) = (-dy, dx)` (resolve/geometry.py). The interior here is the air gap, which
# must be on the WEST side — n = (+1, 0) — which requires dy = -1: north node first.
#
# This is the OPPOSITE winding from W-B-BRICK, which runs E->W. That checks out: E->W puts
# n south, interior north into the concrete and brick facing south, which is what its own
# comment describes. Copying its node order would have put this brick INSIDE the garage.
# `advisory.cladding_side_mismatch` cannot flag it — that rule needs a shared node and a
# CLADDING-function layer, and this wythe is STRUCTURE. Confirm it in the viewer instead.
#
# FoundationWall elevations are ABSOLUTE and replace the storey z entirely
# (resolve/topology.py), which is exactly what lets the wainscot cross the garage datum at
# -1'-0" — ~19 3/8" of it backs onto the ICF stem and ~24 5/8" onto the wood wall above.
# THE BACKING CHANGES AND SO DO THE TIES: two-piece adjustable screw-on ties into studs
# above the datum (corrugated ties are only valid where the brick back is within 1" of
# framing, and across the zip-R it is not), ICF ties below. `unbalanced_fill=ft(0)` keeps
# `structural.foundation_unbalanced_fill` quiet, as W-B-BRICK does — this wythe retains no
# soil.
#
# THE RETURNS ARE THEIR OWN SEGMENTS, JOINED AT A SHARED NODE, NOT A CONTINUOUS CHAIN
# THROUGH THE CORNER. Each return has its own `face("brick-ext")` alignment off its own
# envelope line, exactly like the piers — a wall's `alignment` answers "which face lands on
# MY node line," and a single wall cannot carry two different answers for two different
# faces meeting at a right angle. The resolver does not attempt an outside-corner miter
# between two independent FoundationWall solids sharing an endpoint (that treatment exists
# for closed wall LOOPS, and this component is deliberately open — see the note above on
# why). What SHARING the node buys is only that both wythes terminate at the same point in
# space rather than leaving a gap; a hairline reveal or a slightly proud corner at the miter
# is the honest result of two independently-extruded prisms meeting there, the same class of
# simplification as BRICK_CAP_FLASHING's one-turn-down limitation below. Confirm the corner
# reads acceptably in the viewer; do not chase sub-inch miter perfection into the resolver.
#
# Direction picks the interior side exactly as the piers' own note explains
# (UNRECOVERABLE_WINDING_OUTWARD_SIGN = 1.0, interior = -normal(start->end)). The south
# return's interior must be north (into the building): d = (-1, 0) west needs
# normal(d) = (0, 1)... solving -normal(d) = (0, 1) gives d = (-1, 0), i.e. authored
# corner -> west (east to west), matching the pier's own south-to-north authoring pattern of
# ending each wall on the corner-adjacent node. The north return's interior must be south:
# by the same solve, d = (1, 0), i.e. west -> corner (west to east) — the OPPOSITE order
# from the south return, because the corner node is now the wall's END rather than its
# START. Both are internally consistent; do not "fix" them to match each other.
BRICK_WALLS = [
    FoundationWall(uid="7X5HA9829P", tag="W-G-BRICK-S", start_node="N-G-BRICK-S-N",
                   end_node="N-G-BRICK-S-S", assembly="GARAGE_BRICK_WAINSCOT",
                   alignment=face("brick-ext"), unbalanced_fill=ft(0),
                   top_elevation=WAINSCOT_BRICK_TOP,
                   bottom_elevation=WAINSCOT_LEDGE_TOP),
    FoundationWall(uid="SG7W4PEBAJ", tag="W-G-BRICK-N", start_node="N-G-BRICK-N-N",
                   end_node="N-G-BRICK-N-S", assembly="GARAGE_BRICK_WAINSCOT",
                   alignment=face("brick-ext"), unbalanced_fill=ft(0),
                   top_elevation=WAINSCOT_BRICK_TOP,
                   bottom_elevation=WAINSCOT_LEDGE_TOP),
    FoundationWall(uid="K6G7Q6B2AN", tag="W-G-BRICK-SRET", start_node="N-G-BRICK-S-S",
                   end_node="N-G-BRICK-SRET-W", assembly="GARAGE_BRICK_WAINSCOT",
                   alignment=face("brick-ext"), unbalanced_fill=ft(0),
                   top_elevation=WAINSCOT_BRICK_TOP,
                   bottom_elevation=WAINSCOT_LEDGE_TOP),
    FoundationWall(uid="TS0TKQF3BM", tag="W-G-BRICK-NRET", start_node="N-G-BRICK-NRET-W",
                   end_node="N-G-BRICK-N-N", assembly="GARAGE_BRICK_WAINSCOT",
                   alignment=face("brick-ext"), unbalanced_fill=ft(0),
                   top_elevation=WAINSCOT_BRICK_TOP,
                   bottom_elevation=WAINSCOT_LEDGE_TOP),
]

# The cap is the durability crux and the thing not to value-engineer away: a 4' wainscot
# that stops mid-wall is a HORIZONTAL TERMINATION, and that is where these details fail in a
# freeze-thaw climate. Formed metal cap flashing with a drip edge over the sloped rowlock,
# in the house's one exterior dark (#1c1f24), which every other envelope metal shares.
#
# `DRIP_FLASHING` resolves as a bent angle — a flat leg with a turn-down at the outboard end
# — which is precisely this. `thickness` is the projection out from the edge (over the
# 3 5/8" wythe plus a bit of throw), `depth` the vertical turn-down face. Precedent:
# params/sunken_garden.py's TR-SG-DRIP.
#
# ONE HONEST LIMITATION: DRIP_FLASHING has only the one OUTBOARD turn-down, and no
# coping/sill/cap kind exists in TrimKind. The inboard kick-out — the leg that runs up
# behind the rainscreen above so water leaves the wall instead of tracking down behind the
# cladding — cannot be modelled by the same run and is carried in `source=` below. Do not
# invent a new TrimKind for it.
#
# The paths run north->south to match their walls. `thickness` is the flat leg's full
# width and it is CENTRED ON THE PATH, so the path is NOT the brick face: it is the
# mid-line of what the cap has to cover, which is the whole 4 5/8" of cavity + wythe
# (24'-0" to 24'-4 5/8") plus about 1" of throw past the face — 5 5/8" spanning 24'-0" to
# 24'-5 5/8", whose middle is 24'-2 13/16". Run on the brick face instead, the cap would
# hang 2 3/4" out in the air and leave the cavity's back open.
# `Flashing` carries no `source=` field, so the rest of the specification lives here: a
# second through-wall flashing under the cap, and through-wall flashing + weeps at 33" o.c.
# max at the BASE course on the ledge (IRC R703.8) — with only 4'-0" of wall each side that
# is a weep near each end. Both are also recorded in the house CLAUDE.md.
#
# `back_side="right"`: the paths run north->south, d = (0, -1), so the LEFT-hand normal
# `normal(d) = (-dy, dx)` points EAST. The building is west of these runs, so the back is
# the right-hand side and the drip's turn-down hangs off the east (outboard) end, throwing
# water clear of the brick instead of back at it.
#
# `depth=inch(2.0)`, not the pre-Roman-coursing 1 1/3": this is the gap between the top of
# the sloped rowlock and the flashing's own top elevation, and it moved with the coursing
# recompute above (see WAINSCOT_CAP_TOP's comment) — a metal detail sized to close the
# course budget exactly, not a fixed manufactured dimension.
#
# The returns get the same cap, run along their own walls (east-west, not north-south), so
# their centreline and back_side derivations mirror the piers' from the OTHER axis: the
# south return's path runs corner -> west, d = (-1, 0), LEFT-hand normal points SOUTH
# (outboard, away from the building) — so back_side="right" again, same value, different
# reason. The north return runs west -> corner, d = (1, 0), LEFT-hand normal points NORTH
# (also outboard) — "right" again. Centrelines use the SAME half-span offset (2 13/16") off
# each return's own envelope line (GARAGE_Y_SOUTH/GARAGE_Y_NORTH), projected outward
# (south/north) instead of the piers' east, and the path's x-run is the return's envelope
# span (24' corner to 20' tip) rather than the piers' envelope y-run.
BRICK_CAP_FLASHING = [
    Flashing(uid="91QT40BPXE", tag="TR-G-BRICK-CAP-S", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(24, 2.8125), ft(44, 8.625)), pt(ft(24, 2.8125), ft(40, 8.625))),
             top_elevation=WAINSCOT_CAP_TOP, depth=inch(2.0), thickness=inch(5.625),
             material="metal-dark-exterior", back_side="right"),
    Flashing(uid="HJEFTKKFG6", tag="TR-G-BRICK-CAP-N", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(24, 2.8125), ft(64, 8.625)), pt(ft(24, 2.8125), ft(60, 8.625))),
             top_elevation=WAINSCOT_CAP_TOP, depth=inch(2.0), thickness=inch(5.625),
             material="metal-dark-exterior", back_side="right"),
    Flashing(uid="Z91V9H686X", tag="TR-G-BRICK-CAP-SRET", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(24), ft(40, 5.8125)), pt(ft(20), ft(40, 5.8125))),
             top_elevation=WAINSCOT_CAP_TOP, depth=inch(2.0), thickness=inch(5.625),
             material="metal-dark-exterior", back_side="right"),
    Flashing(uid="YRF9848XRM", tag="TR-G-BRICK-CAP-NRET", kind=TrimKind.DRIP_FLASHING,
             path=(pt(ft(20), ft(64, 11.4375)), pt(ft(24), ft(64, 11.4375))),
             top_elevation=WAINSCOT_CAP_TOP, depth=inch(2.0), thickness=inch(5.625),
             material="metal-dark-exterior", back_side="right"),
]

# Published so params/foundations.py can gap the ICF stem under the overhead door instead
# of repeating this offset/width: there is no 22"-above-grade stem wall under a vehicle
# door (it would be a curb the car has to climb), so the stem drops to a grade beam there.
# ** 4'-0" STAYS, unlike SERVICE_DOOR_OFFSET below (2026-08-30, and again 2026-08-31). **
# The 16'-0" opening's centre is at 12'-0", 12" off the 24" module, and it cuts 9 stud lines
# where 8 would do — `structural.door_framing_module` reports it and names 11'-0"/13'-0" as
# the nearest legal centres. It was 8" off the old 16" module, cutting 13 where 12 would do;
# the miss got bigger with the wider spacing and the answer did not change.
# It is not taken. This constant is not just the door's offset: params/foundations.py gaps
# the ICF stem into a grade beam on it, and W-G-BRICK-S/N stand on the stem segments that
# leaves, so the piers' JAMB-TO-CORNER span IS this number and their inboard ends ARE the
# door jambs (houses/catlin/CLAUDE.md, and
# test_garage_brick_wainscot_piers_are_the_door_jambs_and_cap_at_four_feet asserts it).
# Moving the door 12" north makes the two piers flanking it 5'-0" and 3'-0" where they are
# 4'-0" and 4'-0" today: a visibly asymmetric masonry wainscot on the garage's main facade,
# bought with one stud. Recorded as a decided advisory in preferences.toml's `[checks]
# suppress`, per element and with the reason beside it — not silenced, decided.
OVERHEAD_DOOR_OFFSET = ft(4)
OVERHEAD_DOOR_WIDTH = ft(16)  # DT-EXT-OVERHEAD192

# Same pair for the service door (2026-08-01): identical treatment for the identical
# reason — it opens off the slab at grade, not the stem top its host wall starts on, so
# the stem gaps to a grade beam here too. Previously stood 1'-10" above the slab and the
# breezeway deck, a "known, deferred mismatch" that code.R311_3_exterior_landing eventually
# failed outright.
# ** 5'-0" -> 5'-10" ON 2026-08-30, AND NOT TO THE NEARER STATION. ** The 36" leaf's centre
# was at 78", 6" off the 16" module, cutting three studs where two will do. The module offered
# 24"/40"/56"/72"/88"/104"..., and only 88" worked:
#
#   72", 56", 104"  the threshold runs off the end of SL-BW-DECK and
#                   `code.R311_3_exterior_landing` FAILs outright. That is the failure this
#                   door already had once, for this reason, before 2026-08-01.
#   88"             clean, once SP-GF-S-HYD is rehomed — see below.
#
# ** 5'-10" -> 6'-6" ON 2026-08-31, AND THE 88" STATION IS GONE WITH THE 16" MODULE. **
# GARAGE_WALL_2X6 is 24" o.c. now, so W-G-S frames stud lines at 24n along the wall and a
# 36" RO must centre on one of them; 88" is 8" off, cutting two studs where one will do.
# 96" is the nearest, and it is also the BETTER station rather than merely the legal one:
# `D-M-ENTRY` is centred on x = 8'-0" too, so the two doors this breezeway spans are finally
# concentric. `params/breezeway.py::_GLAZING_CENTER_X` — the midpoint of the two — goes
# 7'-8" -> 8'-0" with it, taking SL-BW-DECK to x 6'-0"..10'-0" and leaving this 36" leaf's
# jambs (7'-6"/9'-6") a foot of landing clear at each side.
#
# Moving this constant is never just moving a door: params/foundations.py gaps the ICF stem
# into a grade beam on it, so FT-GF-S-DR travels east too, and the water service's protection
# sleeve at x=5'-0" was left standing in the wrong pour. `integrity.sleeve_in_opening` caught
# it as an ERROR the moment the constant moved; the sleeve now names FT-GF-S1, the stem
# footing that is actually over it (plan/mep_sleeves.py). Nothing about the pipe changed —
# and FT-GF-S1 only grows westward-to-eastward as this offset climbs, so x=5'-0" stays over
# it.
SERVICE_DOOR_OFFSET = ft(6, 6)
SERVICE_DOOR_WIDTH = ft(3)  # DT-EXT-SWING36

OPENINGS = [
    # 16' opening is past the prescriptive header table, hence the named engineered beam:
    # a 2-ply 14" LVL.
    #
    # Threshold is the slab at grade, not the host wall's own floor: W-G-E starts at the
    # stem top, GARAGE_STEM_REVEAL above the slab, so the door reaches *down* past its host
    # — the plan's one negative sill_height, the exact negation of that reveal (spelled out
    # rather than computed; the dialect bans arithmetic). It stays -1'-10" through the
    # 2026-08-18 lift: the slab is still at grade and the stem top is still 1'-10" over it,
    # and both simply moved down together. The tie is held by
    # test_catlin_contract_m3.py::test_garage_overhead_door_opens_from_the_slab_at_grade.
    # Head follows the threshold down to 7'-0" above the slab. params/foundations.py gaps
    # the stem to a grade beam under this opening so there's no curb for the car to climb.
    Door(uid="CGD201AAAA", tag="D-G-OVERHEAD", host="W-G-E",
         type_ref="DT-EXT-OVERHEAD192", position=from_node("N-G-SE", OVERHEAD_DOOR_OFFSET),
         sill_height=ft(-1, -10), header_spec='2-ply 14" LVL'),
    # **This door no longer reaches down to the slab; it reaches up to the breezeway.**
    # Until 2026-08-18 it carried D-G-OVERHEAD's negative sill for the same reason — both
    # thresholds and the breezeway deck were one plane at 0'-0". Then grade dropped 2'-6"
    # and took the garage with it while the house and the breezeway deck stayed. The deck is
    # still the landing outside this door (code.R311_3_exterior_landing, and the house rule
    # that both breezeway doors open onto it at one level), so the threshold has to stay at
    # 0'-0" absolute: +1'-0" over a garage storey that now sits at -1'-0" (it was +0'-8"
    # over -0'-8" until the house rose 4" on 2026-08-21 and the garage went down with grade).
    # Inside, ST-G-STEPS takes the 2'-10" down to the slab.
    #
    # The head lands 8" under the top plate — 6'-8" of door in a wall whose plate is at
    # +7'-4" — which is why this opening now names a header the way the overhead door does.
    # There is 6 1/2" between the rough head and the top of wall, and the table's 2-2x8
    # (7 1/4") does not fit it: the solver grows a header up from the rough head, so an
    # oversized one pushes straight through the plates into the truss bottom chords
    # (structural.member_interference caught exactly that). A 5 1/2"-deep 3-ply LVL does
    # fit, three plies filling the 2x6 wall, and it is the ordinary answer for a tall
    # opening in a garage wall: a continuous header carried at the plate line rather than
    # dropped below it (IRC R602.7.2 lets the header take the top plate's place).
    Door(uid="CGD202AAAA", tag="D-G-SERVICE", host="W-G-S", type_ref="DT-EXT-SWING36",
         position=from_node("N-G-SW", SERVICE_DOOR_OFFSET), sill_height=ft(1),
         header_spec='3-ply 5.5" LVL'),
    # This 8' wall (vs. the house's 10') is why the 27" family is 36" tall: a 60" height at
    # this 42" sill would push the header above the top plate. Nudged to 1'-5" (2026-07-29):
    # at 1'-4 5/8" the RO missed the bay centre by 3/8", enough to break two studs and pull
    # in a header a 14" RO should never need
    # (test_catlin_small_windows_have_no_header_and_keep_their_flanking_studs).
    #
    # ** RE-STATIONED 1'-5" -> 2'-5" ON 2026-08-31, and it is the GRID that moved, not the
    # window. ** GARAGE_WALL_2X6 went to 24" o.c., so W-G-W's stud lines are at 24n along
    # the wall and its bay centres at 12 + 24n. The old 2'-0" centre was a 16"-grid bay
    # centre and is a 24"-grid STUD LINE — `structural.window_framing_module` reported it
    # 12" off, breaking one stud and pulling in the header a 14" RO exists to avoid. 3'-0"
    # (position 2'-5" + half of the 14" RO) is the nearest bay centre on the new grid.
    Window(uid="CGX301AAAA", tag="WIN-G-N1", host="W-G-W", type_ref="WT-1424",
           position=from_node("N-G-NW", ft(2, 5)), sill_height=ft(3, 6)),
    # WIN-G-N1's mirror at the south end (2026-07-30): 21'-0" off N-G-NW is the exact mirror
    # of N1's 3'-0" about the wall's 12'-0" midpoint, and also a bay centre (12" + 24"x10 on
    # W-G-W's grid), so the pair stays symmetric and both keep the unbroken stud bay a 14" RO
    # exists to get. Same 3'-6" sill (above a workbench). It moved 22'-0" -> 21'-0" with its
    # mirror on 2026-08-31, for the reason written on WIN-G-N1 above.
    Window(uid="CGX302AAAA", tag="WIN-G-S1", host="W-G-W", type_ref="WT-1424",
           position=from_node("N-G-NW", ft(20, 5)), sill_height=ft(3, 6)),
]

ROOMS = [
    Room(uid="CGR401AAAA", tag="RM-GARAGE", seed=pt(ft(12), ft(60)),
         occupancy=Occupancy.GARAGE, conditioned=False,
         floor_finish="sealed-concrete"),
]

# Gable roof, ridge E-W (rotated 90° vs the house), 16" overhangs. E/W walls stay flat 8'
# rather than `top=ToRoof`: a raked wall top must split at the ridge, but the 16' overhead
# door is centered on the ridge, so W-G-E can't be split. Both gable triangles are instead
# closed by the wall→roof closure in resolve/roof_edge.py, which reads its cladding
# material straight off the host wall's own layers — so a `Wall.layer_materials` override
# on one of these walls would carry into its gable triangle with nothing authored for the
# closure itself. None is authored today; W-G-E's green was reverted 2026-08-26.
# Eave + rake trim is two-layer: a 2x6 wood sub-fascia (structural nailer) lapped by the
# weather face. That face was 5/4 cellular PVC until 2026-08-26 and is now brake-formed
# PVDF metal in "Copper Penny" — six pieces, two eaves and four rakes, THE SAME COIL AS THE
# RIDGE CAP (2026-08-27; it was Western States "Regal Blue" for a day in between). One coil
# and one order for both: a cap in a different colour from the fascia under it reads as a
# mistake rather than as a choice. The substrate changed with the colour on purpose — a
# PVDF metallic is a metal coil finish PVC cannot be ordered in, and a dark trim colour on
# cellular PVC is the classic failure (PVC's thermal movement forces a solar-reflective
# vinyl-safe coating and an LRV cap). See the `metal-copper-penny` Material comment in
# plan/assemblies.py.
# The SOFFIT stays cellular PVC and stays white: vented, out of the weather, and a white
# soffit is what keeps an overhang from reading as a shadow. A vented PVC soffit closes the
# overhang and feeds the vent channel. Elevations derive from the resolved roof plane so the
# raised-heel lift carries the trim with it.
# The SOUTH eave gets a 5" aluminum gutter: that slope faces the 4' breezeway gap and the
# house wall people walk under, and now also catches what sheds off the breezeway roof.
# North eave stays free-draining onto open ground. Declared here rather than in params/
# for the same reason as the fascia — the raised-heel truss lifts the deck plane at the
# envelope stage, so an absolute elevation would drift off the eave.
_GARAGE_EAVE_TRIM = EaveTrim(
    fascia=(FasciaBoard(material="spf", thickness=inch(1.5), depth=inch(5.5)),
            FasciaBoard(material="metal-copper-penny", thickness=inch(1), depth=inch(6))),
    soffit_material="pvc-cellular", soffit_thickness=inch(0.5), soffit_vented=True,
    gutter=EaveGutter(material="aluminum", depth=inch(5), thickness=inch(5),
                      top_drop=inch(0.5), edges=("south",),
                      slope="1/16 in/ft to the east downspout",
                      downspout_ref="TR-G-LEADER-E"),
)

# The leader the south gutter has always sloped to; named in the slope note but never
# authored until now, so it drained to nothing. 3" round, not the house's 4": this slope
# sheds ~290 sq ft against each house eave's 648, and 3" clears ~425 sq ft at the 8 in/hr
# design intensity (params/roof_trim.py works the number).
# test_drainage_elements.py holds this and the EaveGutter together so a roof change that
# moves the trough fails there instead of leaving a leader hanging beside it.
_GARAGE_LEADER = Downspout(
    uid="CGDS01AAAA", tag="TR-G-LEADER-E",
    position=pt(ft(25), ft(39, 5.375)),     # east end of the trough, on its centreline
    # Both absolute, and both dropped 2'-6" on 2026-08-18 when grade did and the garage
    # went down with it. The trough they bracket is derived from the roof plane, so it moved
    # on its own; these are the two numbers that had to follow it by hand.
    top_elevation=ft(7, 6),             # inside the trough floor
    bottom_elevation=ft(-1, -6),        # splash block, a foot above the apron
    diameter=inch(3), material="aluminum", gutter_ref="RF-GARAGE",
)

ROOFS = [
    # `edge_trim_material` names the coil the FORMED EDGE TRIM is ordered in, which on this
    # roof is the vented ridge cap and nothing else (2026-08-26). The field drives the ridge
    # cap and the corner trim (resolve/roof_trim.py::_edge_trim_material); a 16" overhang
    # frames fascia + soffit and no corner trim, so this recolours exactly one member.
    # The fascia is NOT reached by this field — it names its own material on the FasciaBoard
    # above — so the two must be kept in step BY HAND. They are the same coil since
    # 2026-08-27; change one and change the other, or the cap and the fascia under it drift
    # apart with nothing to catch it.
    Roof(uid="CGRF01AAAA", tag="RF-GARAGE", form=RoofForm.GABLE,
         pitch=Pitch(4, 12), bearing_refs=("W-G-S", "W-G-N"),
         assembly="GARAGE_ROOF", overhang=ft(1, 4), ridge_direction="x",
         edge_trim_material="metal-copper-penny",
         eave_trim=_GARAGE_EAVE_TRIM),
]

# Snow retention on the south slope: the garage roof sheds toward the breezeway's
# polycarbonate canopy (GL-BW-ROOF), which sits 3.0' below this eave in the discharge band
# (structural.sliding_snow) — a willing 4:12 standing-seam slope over an unwilling
# multiwall-polycarbonate target.
# S-5! ColorGard: a continuous crossbar on seam clamps (StructuralHardware.requires_role
# bills the clamps automatically). Row runs x 1'-4"..8'-0" — canopy width plus a full bay of
# margin each end, since snow releases at an angle. Row count/spacing at Pg = 50 psf is the
# manufacturer's calculation; the check only screens for retention being *authored*.
# Placed 4" up-slope of the eave (y = 39'-6 7/8", z = 8'-1"), deliberately close to it since
# retention holds the pack where the load lives. (Position moved 5 5/8" south with the wall
# line on 2026-08-15; height didn't, since the wall didn't get taller. It dropped 2'-6" on
# 2026-08-18, when the garage followed grade down and the roof it clamps to went with it —
# an absolute elevation on a structure that moved.)
# Written out, not generated: the editable dialect allows no comprehensions.
_SNOW_GUARD_Y = ft(39, 7.25)
_SNOW_GUARD_Z = ft(8, 1)
_SNOW_GUARD_SIZE = "S-5! ColorGard"
SNOW_GUARDS = [
    Connector(uid="CGSG01AAAA", tag="CN-G-SNOW-1", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(1, 4), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG02AAAA", tag="CN-G-SNOW-2", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(2, 8), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG03AAAA", tag="CN-G-SNOW-3", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(4), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG04AAAA", tag="CN-G-SNOW-4", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(5, 4), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG05AAAA", tag="CN-G-SNOW-5", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(6, 8), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
    Connector(uid="CGSG06AAAA", tag="CN-G-SNOW-6", kind=ConnectorKind.SNOW_GUARD,
              position=pt(ft(8), _SNOW_GUARD_Y), elevation=_SNOW_GUARD_Z,
              size=_SNOW_GUARD_SIZE, connects=("RF-GARAGE",)),
]

ALARMS = [
    # A garage gets a *heat* detector, not smoke: exhaust, dust and outdoor-swing temps would
    # nuisance-trip a smoke head, which is why R315 asks for CO coverage adjacent to the
    # garage rather than a smoke alarm inside it. On CKT-LT-BACKUP because R314.4 wants an
    # unswitched circuit and CKT-RC-GARAGE (GFCI) is wrong for a life-safety device.
    Alarm(uid="CGA701AAAA", tag="AL-G-HEAT", kind=AlarmKind.HEAT, room="RM-GARAGE",
          circuit="CKT-LT-BACKUP"),
]

# --- service-door stair (ST-G-SERVICE) --------------------------------------------------
#
# Five risers from the garage slab at -2'-10" up to D-G-SERVICE's threshold at 0'-0", the
# same 5 x 6.8" risers on 11" treads at 3'-0" wide that five concrete `Slab`s used to be
# (SL-G-STEP-0..4 in params/foundations.py). SL-G-STEP-0, the 3'-0" landing at the
# threshold, is still a Slab and belongs there — a landing is a floor, not a flight. The
# four treads below it are this.
#
# PRESSURE-TREATED WOOD, not concrete (owner, 2026-08-22): KDAT southern yellow pine, kiln-
# dried after treatment so it is stable enough to cut and fit like framing. The garden's
# beams and the breezeway already use it (BEAM_KDAT / POST_KDAT), so it is the house's
# established exterior-wood answer. Where the stringers land on the garage slab they need a
# capillary break — a strip of the same 10-mil under-slab retarder, which is on site anyway.
# PT stops the fungus that follows wicked water; it does not stop the wicking.
#
# `Stair` could not express this until 2026-08-22: it took its rise from a pair of storey
# elevations through a FloorOpening in the storey above, and this is a step-down *within* one
# storey with no floor to open. `floor_opening` is optional now and `base_elevation` /
# `top_elevation` state the rise directly. That is what puts the flight in front of
# `structural.stair_riser_uniformity` and `code.R311_7_8_handrail`, neither of which could
# see a stack of slabs, and what RL-G-SERVICE below is the answer to.
#
# The elevations are literals because this file is `# haus: editable` and may hold only
# literals; -2'-10" is `params/foundations.SITE_GRADE`, which `plan/site.py` repeats as
# `Site.grade` and `plan/manifest.py` asserts the two agree. `start` is the foot of the
# flight — GARAGE_Y_SOUTH + 3'-0" of landing + 4 x 11" of tread = 47'-2 3/8" — and it climbs
# south (`run_reversed`) back to the landing's north edge. All three y literals below
# went up 1/2" on 2026-08-23 with GARAGE_Y_SOUTH.
#
# 11" treads with NO nosing, which keeps the run at the 3'-8" the four slabs occupied and
# leaves an 11" going against R311.7.5.2's 10" minimum. A nose would shorten the run and buy
# nothing here.
STAIRS = [
    Stair(uid="X99TD38ZS3", tag="ST-G-SERVICE",
          from_storey="garage", to_storey="garage",
          base_elevation=ft(-2, -10), top_elevation=ft(0),
          width=ft(3), start=pt(ft(5), ft(47, 3.25)),
          run_direction="y", run_reversed=True,
          tread_depth=inch(11), nosing_depth=inch(0),
          material="kdat"),
]

# R311.7.8 wants a handrail on any flight of four or more risers, and this one has five.
# Nothing was asking for it while the flight was five slabs, because both handrail rules
# iterate `model.stairs`.
#
# Post-mounted on the west side of the run, not wall-mounted: the flight stands in the
# open on the garage floor at x=5'..8', with the nearest wall 5'-0" away. The posts stand on
# the treads (`serves_stair` rakes the rail along the flight's nosing line) and the rail
# tops out 36" above them, inside R311.7.8.1's 34"-38".
#
# FLAGGED, NOT ANSWERED: the landing at 0'-0" is **34" above the garage slab**, over
# R312.1.1's 30" threshold, so its open east and north sides want a guard as well as this
# handrail. That is a design decision with a cost and a look to it, and it is the owner's,
# not this file's.
#
# **Nothing in the engine will ask.** `code.R312_1_guard_height` censuses `FloorSystem`s and
# `code.R312_1_guard` censuses `FloorOpening`s; SL-G-STEP-0 is a `Slab`, so it is in neither
# census and its 34" drop is invisible to both. That is a real coverage gap, not a pass —
# recorded in plans/TODO.md rather than papered over here, because the fix is a rule that
# walks slab edges and belongs with the guard rules, not with this stair.
RAILINGS = [
    Railing(uid="CX7KN0MZE0", tag="RL-G-SERVICE",
            path=(pt(ft(5), ft(47, 3.25)), pt(ft(5), ft(43, 7.25))),
            kind=RailingKind.METAL_SURFACE_MOUNT, height=inch(36),
            base_elevation=ft(-2, -10), post_spacing=inch(36), post_size="2x2",
            rail_count=1, mount="surface", assembly="RAILING_DARK_METAL",
            role="handrail", serves_stair="ST-G-SERVICE", top_height=inch(36),
            graspable_profile="1.5in round — Type I"),
]

ELEMENTS = [*NODES, *BRICK_NODES, *WALLS, *BRICK_WALLS, *OPENINGS, *ROOMS, *ROOFS,
            _GARAGE_LEADER, *SNOW_GUARDS, *ALARMS, *STAIRS, *RAILINGS,
            *BRICK_CAP_FLASHING]
