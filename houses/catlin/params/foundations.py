"""Generated foundation support: house footings, garage ICF stem + slab.

- House: strip footings (20" x 8") under every basement concrete wall.
- Garage: freestanding ICF stem (6" core) from frost depth to 22" above grade,
  wood walls bear on top (the ``garage`` storey elevation), footing under.
- House footings additionally get a bedding-prep record (undercut, geotextile, drain
  tile, compacted washed-stone bed, perimeter foam) — see ``HOUSE_FOOTING_BEDDING``.

The breezeway's pads/piers/posts used to live here as a roofless stub; they now belong to
the whole structure in ``params/breezeway.py``.
"""

from __future__ import annotations

from typehaus import (
    DrainTile,
    Drywell,
    Footing,
    FootingBedding,
    FoundationWall,
    Node,
    Service,
    Slab,
    SlabThermalBreak,
    SleevePenetration,
    face,
    ft,
    inch,
    pt,
)

# The ICF form's own dimensions, from the assembly that declares them. The stem's
# alignment and the slab's inset are both measured off the section, so neither is
# repeated here.
from plan.assemblies import GARAGE_ICF_CORE, GARAGE_ICF_EPS

# One source of truth for where the garage stands: the wall lines the wood walls above are
# authored on. The stem must sit under them and the slab inside them, so both derive from
# there rather than repeating the literal.
from plan.storeys.garage import (
    GARAGE_STEM_REVEAL,
    GARAGE_Y_NORTH,
    GARAGE_Y_SOUTH,
    OVERHEAD_DOOR_OFFSET,
    OVERHEAD_DOOR_WIDTH,
    SERVICE_DOOR_OFFSET,
    SERVICE_DOOR_WIDTH,
)

# --- house strip footings --------------------------------------------------------
_HOUSE_WALL_TAGS = [
    "W-B-S1", "W-B-S2", "W-B-S3", "W-B-E1", "W-B-E2", "W-B-N1", "W-B-N2",
    "W-B-N3", "W-B-W1", "W-B-W2", "W-B-CS", "W-B-CS2", "W-B-CN", "W-B-CN2", "W-B-CW",
    "W-B-CE", "W-B-STR", "W-B-STR2",
    # Appended, not inserted: the uid is enumerate()'d over this list, so a new tag goes on
    # the end or every footing after it silently renumbers. W-B-CW3 is the 2026-08-02 split
    # of W-B-CW at the ESS closet (plan/storeys/basement.py) — same 12" concrete, so the
    # same 20"x8" strip runs under it.
    "W-B-CW3",
]

HOUSE_FOOTINGS = [
    Footing(uid=f"CF{i:03d}AAAAA", tag=f"FT-{t[2:]}", under=t,
            width=inch(20), depth=inch(8))
    for i, t in enumerate(_HOUSE_WALL_TAGS, start=1)
]

# Bearing prep below every house footing: dig 6-8" (7" nominal) past the footing
# underside, line with non-woven (no-slip) geotextile, run drain tile through the bed,
# then compacted ASTM C33 #57 washed crushed stone — a well-drained bearing surface
# that also breaks direct footing-to-wet-clay thermal contact. Perimeter foam (4",
# matching CATLIN_BASEMENT_12's 2x2" exterior XPS) continues the wall's insulation
# down over the footing sides.
HOUSE_FOOTING_BEDDING = [
    FootingBedding(uid=f"CFB{i:03d}AAAA", tag=f"FB-{f.tag[3:]}", host_ref=f.tag,
                   undercut=inch(7), perimeter_insulation=inch(4),
                   drain_tile_spec=DrainTile(diameter=inch(4), sock=True,
                                             discharge="daylight"))
    for i, f in enumerate(HOUSE_FOOTINGS, start=1)
]

# --- glazed-brick veneer plinth (W-B-BRICK) ---------------------------------------
# Deliberately NOT appended to _HOUSE_WALL_TAGS: that loop pours a 20"x8" strip monolithic
# with the house footing, which is the thermal bridge this detail exists to avoid.
#
# What it actually is: a shallow plinth cast ON the house footing's projecting toe rather
# than a strip poured beside it, because there is nowhere beside it to pour. FT-B-S2/
# FT-B-S3 are 20" wide centred on the y=0 node line, so the toe already runs 10" south,
# and the veneer's outer brick face lands at -9.175" — inside that edge by 0.8". The wythe
# has to bear on the toe; the only question is what separates the two pours.
#
# So the thermal break is a 2" XPS bed *under* the plinth (FB-B-BRICK below), not a block
# beside it, and that is why this detail authors no ``Dowel``: the sunken garden's
# DW-SG-W1/E1/COL cross a vertical joint where two footings meet edge to edge, and
# ``Dowel.axis`` is "x" or "y" only, so it cannot describe a horizontal bed. The bars that
# pin the plinth back are the veneer's own masonry ties, which are a construction note here
# the same way the garden's dowels were before they became elements (plans/TODO.md).
#
# 10" x 5". The width is centred on the veneer's own node line at y=-4.55" (a Footing takes
# its parent wall's axis), and the brick's outer face is at -9.175", so 9" would have left
# the face 0.12" proud of its own plinth; 10" carries it with ~0.4" to spare and stops well
# inside the house footing's -10" edge. The 5" of depth over the 2" bed tops out at -8'-5" —
# D-B-PATIO's raised threshold, which is the highest it can go without stepping across the
# door. See the note on W-B-BRICK in plan/storeys/basement.py for the full derivation.
#
# x=28' coordination: the veneer stops on the sunken garden's east wall axis, where
# FT-SG-E1 already breaks thermally from the house footing (params/sunken_garden.py). No
# third break is invented there and no solid collides: FT-SG-E1 is 84" wide but sits in the
# -9.75'..-10.75' band under a wall whose bottom is -9.75', a clear 1'-5" below this plinth.
VENEER_PLINTH = [
    Footing(uid="CFV301AAAA", tag="FT-B-BRICK", under="W-B-BRICK",
            width=inch(10), depth=inch(5)),
]

# The 2" of 40 psi XPS between the plinth and the house footing it bears on — the same
# ``cast_foam_in_aggregate`` record the sunken garden's house-adjacent footings carry, used
# here for a bed rather than a block. No drain tile: this sits a foot above the house
# footing's own tile, inside the sunken garden, with nothing to collect.
VENEER_PLINTH_BEDDING = [
    FootingBedding(uid="CFV351AAAA", tag="FB-B-BRICK", host_ref="FT-B-BRICK",
                   undercut=inch(2), geotextile=False, drain_tile=False,
                   cast_foam_in_aggregate=True),
]

# --- garage ICF stem (basement storey; absolute elevations) -----------------------
_FROST = 42.0 / 12.0  # frost depth below grade
# Exposed above grade, and the garage storey datum besides — one value, authored next to
# the wall lines it belongs with (plan/storeys/garage.py).
_STEM_TOP = GARAGE_STEM_REVEAL
# A car can't climb a 22" ICF stem, so the east stem gaps at the overhead door: the two
# flanking segments keep the full reveal, and the segment behind the door becomes a grade
# beam topping out flush with the slab at 0'-0", leaving flat concrete from driveway to
# slab with no curb across the opening. Nothing above changes — W-G-E still bears on the
# uniform stem-top datum for its whole length (splitting *that* wall would break the ridge
# closure it carries), so this is a foundation detail; the *door* is what reaches down to
# the slab, via the negative sill_height in plan/storeys/garage.py.
_GRADE_BEAM_TOP = ft(0)
# How much wider than the opening the service door's stem gap is formed — see N-GF-S-DRW.
_SERVICE_GAP_MARGIN = ft(0, 3)

GARAGE_STEM_NODES = [
    Node(uid="CGF001AAAA", tag="N-GF-SW", position=pt(ft(0), GARAGE_Y_SOUTH)),
    Node(uid="CGF002AAAA", tag="N-GF-SE", position=pt(ft(24), GARAGE_Y_SOUTH)),
    Node(uid="CGF003AAAA", tag="N-GF-NE", position=pt(ft(24), GARAGE_Y_NORTH)),
    Node(uid="CGF004AAAA", tag="N-GF-NW", position=pt(ft(0), GARAGE_Y_NORTH)),
    Node(uid="CGF005AAAA", tag="N-GF-E-DRS", position=pt(ft(24), GARAGE_Y_SOUTH + OVERHEAD_DOOR_OFFSET)),
    Node(uid="CGF006AAAA", tag="N-GF-E-DRN",
         position=pt(ft(24), GARAGE_Y_SOUTH + OVERHEAD_DOOR_OFFSET + OVERHEAD_DOOR_WIDTH)),
    # The service door's gap in the south stem (2026-08-01), the same two nodes one wall
    # over. W-GF-S runs west-to-east from N-GF-SW, so these are plain x stations.
    #
    # 3" of margin each side, where the overhead door's gap has none: the hydrant line
    # (PR-G-HYDRANT-CW) crosses this wall buried at x = 5'-0", which is the door's west jamb
    # to the inch. A gap that starts exactly there puts the crossing on the joint between two
    # footings, belonging to neither, and mep.footing_clearance rightly asks for a sleeve in
    # both. Forming the block-out a few inches wider than the opening is what actually
    # happens on site anyway, and it puts the crossing unambiguously inside the grade beam.
    Node(uid="CGF007AAAA", tag="N-GF-S-DRW",
         position=pt(SERVICE_DOOR_OFFSET - _SERVICE_GAP_MARGIN, GARAGE_Y_SOUTH)),
    Node(uid="CGF008AAAA", tag="N-GF-S-DRE",
         position=pt(SERVICE_DOOR_OFFSET + SERVICE_DOOR_WIDTH + _SERVICE_GAP_MARGIN,
                     GARAGE_Y_SOUTH)),
]

# Where the 11" section sits across the node line. The wood walls above are authored
# `alignment=face("zip-r-ext")`, so the 24'x24' line IS their zip-R plane; putting the
# stem's exterior EPS face on that same line makes the two coplanar, and the rainscreen +
# cladding (7/8") then project past the foam and drip clear of it. Left unaligned the
# section straddled the line and stood 5 5/8" proud of the cladding — a horizontal shelf
# right round the garage for rain to pool on (plans/TODO.md).
#
# `face("concrete-ext")` and not `face("eps-ext")`: the face matcher in
# resolve/topology.py is a fuzzy prefix test, so "eps-ext" matches the *eps-int* layer
# first and silently returns the wrong face. The concrete face is unambiguous, and it is
# the datum the basement walls already align to. `_axis_offset_from_interior` puts that
# face on the axis and then shifts the axis outboard by `offset`, so one EPS thickness of
# offset carries the exterior foam face out to the node line.
_ALIGN = face("concrete-ext", offset=GARAGE_ICF_EPS)

_STEM = dict(assembly="GARAGE_ICF_6", alignment=_ALIGN, top_elevation=_STEM_TOP,
             bottom_elevation=ft(-_FROST))
_GRADE_BEAM = dict(assembly="GARAGE_ICF_6", alignment=_ALIGN,
                   top_elevation=_GRADE_BEAM_TOP,
                   bottom_elevation=ft(-_FROST))

GARAGE_STEM_WALLS = [
    # South stem, split three ways at the service door on 2026-08-01 — the east wall's
    # pattern exactly. W-GF-S1 keeps the original uid as the remnant of the single wall;
    # the grade beam and the far segment are new.
    FoundationWall(uid="CGF101AAAA", tag="W-GF-S1", start_node="N-GF-SW",
                   end_node="N-GF-S-DRW", **_STEM),
    FoundationWall(uid="CGF107AAAA", tag="W-GF-S-DR", start_node="N-GF-S-DRW",
                   end_node="N-GF-S-DRE", **_GRADE_BEAM),
    FoundationWall(uid="CGF108AAAA", tag="W-GF-S2", start_node="N-GF-S-DRE",
                   end_node="N-GF-SE", **_STEM),
    FoundationWall(uid="CGF102AAAA", tag="W-GF-E1", start_node="N-GF-SE",
                   end_node="N-GF-E-DRS", **_STEM),
    FoundationWall(uid="CGF105AAAA", tag="W-GF-E-DR", start_node="N-GF-E-DRS",
                   end_node="N-GF-E-DRN", **_GRADE_BEAM),
    FoundationWall(uid="CGF106AAAA", tag="W-GF-E2", start_node="N-GF-E-DRN",
                   end_node="N-GF-NE", **_STEM),
    FoundationWall(uid="CGF103AAAA", tag="W-GF-N", start_node="N-GF-NE",
                   end_node="N-GF-NW", **_STEM),
    FoundationWall(uid="CGF104AAAA", tag="W-GF-W", start_node="N-GF-NW",
                   end_node="N-GF-SW", **_STEM),
]

# Not a comprehension any more: the east wall split into three, and giving each a fresh
# uid would reassign CGF203/204AAAA (footings that didn't conceptually change) to the new
# door pieces instead. S/N/W and the E1 remnant of the old single E wall keep their
# original uids; only the grade beam and the far side of the door split are genuinely new.
#
# `center_on="wall"` on every one of them: a Footing otherwise centres its strip on the
# raw node line, which alignment never reaches. The stem now runs 0"..11" inboard of that
# line, so a 20" strip centred on it would leave 10" of toe under nothing and hang 1" of
# stem off the far edge. Centred on the resolved section instead, the toe is a symmetric
# 4 1/2" each side.
_GARAGE_FOOTING = dict(width=inch(20), depth=inch(8), center_on="wall")

GARAGE_FOOTINGS = [
    Footing(uid="CGF201AAAA", tag="FT-GF-S1", under="W-GF-S1", **_GARAGE_FOOTING),
    Footing(uid="CGF207AAAA", tag="FT-GF-S-DR", under="W-GF-S-DR", **_GARAGE_FOOTING),
    Footing(uid="CGF208AAAA", tag="FT-GF-S2", under="W-GF-S2", **_GARAGE_FOOTING),
    Footing(uid="CGF202AAAA", tag="FT-GF-E1", under="W-GF-E1", **_GARAGE_FOOTING),
    Footing(uid="CGF205AAAA", tag="FT-GF-E-DR", under="W-GF-E-DR", **_GARAGE_FOOTING),
    Footing(uid="CGF206AAAA", tag="FT-GF-E2", under="W-GF-E2", **_GARAGE_FOOTING),
    Footing(uid="CGF203AAAA", tag="FT-GF-N", under="W-GF-N", **_GARAGE_FOOTING),
    Footing(uid="CGF204AAAA", tag="FT-GF-W", under="W-GF-W", **_GARAGE_FOOTING),
]

# Filed on the house's "main" storey key rather than the "garage" storey because the garage
# storey datum is the ICF stem top (1'-10"), while this slab is poured at grade. The inset
# from the wall lines keeps the pour inside the ICF stem: the whole 11" section now stands
# inboard of the node line, so the inset is that section plus the same 1/2" gap between
# slab edge and stem interior face the pour has always had.
_SLAB_GAP = inch(0.5)
_SLAB_INSET = GARAGE_ICF_CORE + GARAGE_ICF_EPS + GARAGE_ICF_EPS + _SLAB_GAP
_slab_y_s = GARAGE_Y_SOUTH + _SLAB_INSET
_slab_y_n = GARAGE_Y_NORTH - _SLAB_INSET
GARAGE_SLAB = Slab(
    uid="CGS501AAAA", tag="SL-G-FLOOR",
    outline=(pt(_SLAB_INSET, _slab_y_s), pt(ft(24) - _SLAB_INSET, _slab_y_s),
             pt(ft(24) - _SLAB_INSET, _slab_y_n), pt(_SLAB_INSET, _slab_y_n)),
    thickness=inch(3.5), assembly="GARAGE_SLAB_ON_GRADE",
    perimeter_thermal_break=SlabThermalBreak(material_ref="xps", thickness=inch(1)),
)

# --- garage hydrant: supply sleeve, gravel pit -------------------------------------
#
# FX-G-HYDRANT stands on the west wall near the NW corner. Two pieces of foundation work
# go with it, and neither is UI-movable, which is why they belong in this (non-editable)
# module while the fixture itself lives in the editable plan/fixtures.py.
#
# Elevations: garage slab top 0'-0", underside -3½"; ICF stem top +1'-10", bottom -3'-6";
# footings bear at about -4'-2". ``_FROST`` above is the *footing* frost depth (42"). The
# hydrant's 72" bury is a different number for a different purpose — the depth of its own
# shutoff valve, 2'-6" below the stem bottom and well clear of the frost line. The two are
# consistent, not in conflict.
# Where the hydrant can stand, and why it is not against a wall (2026-08-15).
#
# It was at (1'-6", 62'), tucked into the NW corner, and that position was not buildable.
# The shutoff is 6'-0" down; the garage footings bear at -4'-2". Anything at the valve is
# therefore 22" below the bearing plane and needs at least 22" of lateral clearance from
# the footing's edge before it is outside the 45° influence line — and the weep stone
# around the valve, which goes deeper still, needs more. At x = 1'-6" the riser had 8" and
# the stone pocket overlapped FT-GF-W's footprint outright. `mep.footing_clearance` was
# only passing because SP-GF-W-HYD sat near it, a sleeve boring through concrete the pipe
# never touched (deleted 2026-08-15, → plan/mep.py).
#
# The clear zone that leaves is x >= 4'-10 1/2", y <= 59'-7 7/8" — which is floor, not
# wall. (It tightened on 2026-08-15: the stem was aligned onto the wall line and the
# footings re-centred under it with ``center_on="wall"``, which walked FT-GF-W's east edge
# and FT-GF-N's south edge 5 1/2" further into the room, and the wall lines themselves
# 5 5/8" south. The zone moved with them; the fixture had to follow.) There
# is no wall position in this garage that works: the footing runs the full perimeter and
# the constraint is the fixture's own bury, not its plan location. So the hydrant stands
# free, as a *yard* hydrant is built to (it is a Y34 barrel, not a wall hydrant — see the
# two south-face ones in plan/fixtures.py for the contrast).
#
# x = 5'-0" is chosen over the 4'-8" minimum because it is the line the service already
# runs on: PR-G-HYDRANT-CW comes north at x = 5'-0" from the house water entry, through
# three basement wall sleeves and SP-GF-S-HYD, all at x = 5'-0". Standing the hydrant on
# that line makes the run dead straight and deletes the two-vertex west jog that was the
# thing inside FT-GF-W's influence line in the first place. The 2026-07-29 re-route moved
# the buried leg to x = 5' for exactly this reason and stopped one fixture short.
#
# y = 59'-6" puts the stone pocket 35 7/8" clear of FT-GF-N against the 34" it needs, and
# leaves the fixture inside the overhead door's y 45'..61' band.
#
# **Consequence to accept:** the hydrant is a post standing 5' out from the west wall at
# the front-left of the north bay, not a fitting on the wall. It is in the parking area
# because every compliant position in this garage is. A bollard or a wheel stop is the
# mitigation if it proves to be in the way; moving it back to the wall is not.
HYDRANT_X_FT = 5.0          # on the service line — the run reaches it without a jog
HYDRANT_Y_FT = 59.5         # north bay, clear of FT-GF-N's influence line
HYDRANT_BURY_FT = 6.0       # shutoff depth below grade — the code number for this fixture

# There was a 4" topping pedestal here (SL-G-HYDRANT-PED, an 18" square poured on top of
# SL-G-FLOOR) whose job was to lift the slab penetration and its sealant joint above the
# salt-slush wet line a garage floor runs from December to March. It was retired on
# 2026-08-03 by owner decision: the hydrant stands on the garage's own slab, like everything
# else in the room. What replaces it is specification, not geometry — a flexible,
# chloride-tolerant sealant at the penetration, inspected rather than elevated
# (notes/garage_hydrant.md). Nothing below grade changed; the bury, the sleeve and the
# drywell are the freeze protection and they are all still here.

# The supply penetration through the garage slab. Filed on ``main`` with the slab it passes
# through — SL-G-FLOOR is a "main" element because the garage storey datum is the stem top
# while the slab is poured at grade — because ``_missing_sleeve_findings`` scopes its
# containment test to ``solid.storey == storey.tag``. The fixture above it is on ``garage``.
# purpose=WATER_COLD, not the DRAIN default: this carries supply down, and nothing up.
GARAGE_HYDRANT_SLEEVE = SleevePenetration(
    uid="CGP602AAAA", tag="SP-G-HYDRANT", host_ref="SL-G-FLOOR",
    position=pt(ft(HYDRANT_X_FT), ft(HYDRANT_Y_FT)),
    pipe_diameter=inch(0.75), sleeve_diameter=inch(2),
    serves_fixture="FX-G-HYDRANT", purpose=Service.WATER_COLD,
)

# The gravel bed FX-G-HYDRANT's own weep drains into — a Woodford Y34-style frost-free
# hydrant self-drains through a weep hole at its buried shutoff when the head closes, and
# that water has nowhere to go but into stone packed around the valve. It is *not* an
# exterior catch basin for garage wash-down water and there is no floor drain reading on it
# (notes/garage_hydrant.md); it exists solely to take the hydrant's own weep. It was a
# locally deepened FootingBedding only because FootingBedding was the closest thing the
# model had, and the cost of that stand-in was real — the excavation perimeter was billing
# as perimeter drain tile in the sitework take-off, tile that is not there.
#
# It sits on the hydrant's own stack (HYDRANT_X_FT, HYDRANT_Y_FT) and has to: the weep
# needs stone at the valve, not stone somewhere else that a pipe would have to carry it to.
# That makes the pocket, not the pipe, the thing that sets how far out the fixture stands —
# it is the deepest excavation in the assembly, so it is the one the 45° influence line
# grades hardest. → HYDRANT_X_FT above for the arithmetic.
#
# Re-sized 2026-08-15, from 2' across x 4' deep. That was 12.6 cu ft of stone for a weep
# that discharges a few quarts, and its -9'-0" bottom put it 4'-10" below the footings'
# bearing plane — an excavation that deep has to stand a long way off, and the old one did
# not stand off at all (it overlapped FT-GF-W's footprint by 4" in plan). Nothing was
# grading it: `mep.footing_clearance` walks pipe runs, and a Drywell is not one.
#
# 1'-6" across x 1'-6" deep, top -5'-6", is what the fixture actually calls for: ~2.6 cu ft
# of washed stone with the -6'-0" shutoff 6" below the top of it and a foot of stone under
# the weep. Bottom -7'-0" is 34" below bearing, and the stone's edge stands 35 1/2" off
# FT-GF-W and 35 7/8" off FT-GF-N — the two that bind. There is no slack left in either.
GARAGE_HYDRANT_DRYWELL = Drywell(
    uid="CGP603AAAA", tag="DRW-G-HYDRANT",
    position=pt(ft(HYDRANT_X_FT), ft(HYDRANT_Y_FT)),
    diameter=inch(18), depth=inch(18), top_elevation=ft(-(HYDRANT_BURY_FT - 0.5)),
    geotextile=True, inlet_refs=("FX-G-HYDRANT",),
)

BASEMENT_ELEMENTS = [*HOUSE_FOOTINGS, *HOUSE_FOOTING_BEDDING, *VENEER_PLINTH,
                     *VENEER_PLINTH_BEDDING, *GARAGE_STEM_NODES,
                     *GARAGE_STEM_WALLS, *GARAGE_FOOTINGS, GARAGE_HYDRANT_DRYWELL]
MAIN_ELEMENTS = [GARAGE_SLAB, GARAGE_HYDRANT_SLEEVE]
