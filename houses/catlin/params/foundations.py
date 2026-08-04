"""Generated foundation support: house footings, garage ICF stem + slab.

- House: strip footings (20" x 8") under every basement concrete wall.
- Garage: freestanding ICF stem (8" core) from frost depth to 22" above grade,
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
    ft,
    inch,
    pt,
)

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

_STEM = dict(assembly="GARAGE_ICF_8", top_elevation=_STEM_TOP,
             bottom_elevation=ft(-_FROST))
_GRADE_BEAM = dict(assembly="GARAGE_ICF_8", top_elevation=_GRADE_BEAM_TOP,
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
GARAGE_FOOTINGS = [
    Footing(uid="CGF201AAAA", tag="FT-GF-S1", under="W-GF-S1", width=inch(20), depth=inch(8)),
    Footing(uid="CGF207AAAA", tag="FT-GF-S-DR", under="W-GF-S-DR",
            width=inch(20), depth=inch(8)),
    Footing(uid="CGF208AAAA", tag="FT-GF-S2", under="W-GF-S2", width=inch(20), depth=inch(8)),
    Footing(uid="CGF202AAAA", tag="FT-GF-E1", under="W-GF-E1", width=inch(20), depth=inch(8)),
    Footing(uid="CGF205AAAA", tag="FT-GF-E-DR", under="W-GF-E-DR",
            width=inch(20), depth=inch(8)),
    Footing(uid="CGF206AAAA", tag="FT-GF-E2", under="W-GF-E2", width=inch(20), depth=inch(8)),
    Footing(uid="CGF203AAAA", tag="FT-GF-N", under="W-GF-N", width=inch(20), depth=inch(8)),
    Footing(uid="CGF204AAAA", tag="FT-GF-W", under="W-GF-W", width=inch(20), depth=inch(8)),
]

# Filed on the house's "main" storey key rather than the "garage" storey because the garage
# storey datum is the ICF stem top (1'-10"), while this slab is poured at grade. The 6"
# inset from the wall lines keeps the pour inside the ICF stem.
_SLAB_INSET = ft(0.5)
_slab_y_s = GARAGE_Y_SOUTH + _SLAB_INSET
_slab_y_n = GARAGE_Y_NORTH - _SLAB_INSET
GARAGE_SLAB = Slab(
    uid="CGS501AAAA", tag="SL-G-FLOOR",
    outline=(pt(ft(0.5), _slab_y_s), pt(ft(23.5), _slab_y_s),
             pt(ft(23.5), _slab_y_n), pt(ft(0.5), _slab_y_n)),
    thickness=inch(3.5), assembly="GARAGE_SLAB_ON_GRADE",
    perimeter_thermal_break=SlabThermalBreak(material_ref="xps", thickness=inch(1)),
)

# --- garage hydrant: pedestal, supply sleeve, gravel pit --------------------------
#
# FX-G-HYDRANT stands on the west wall near the NW corner. Three pieces of foundation work
# go with it, and none is UI-movable, which is why they belong in this (non-editable) module
# while the fixture itself lives in the editable plan/fixtures.py.
#
# Elevations: garage slab top 0'-0", underside -3½"; ICF stem top +1'-10", bottom -3'-6";
# footings bear at about -4'-2". ``_FROST`` above is the *footing* frost depth (42"). The
# hydrant's 72" bury is a different number for a different purpose — the depth of its own
# shutoff valve, 2'-6" below the stem bottom and well clear of the frost line. The two are
# consistent, not in conflict.
HYDRANT_X_FT = 1.5          # 1'-6" off the west wall line
HYDRANT_Y_FT = 62.0         # near the NW corner, clear of both north windows
HYDRANT_BURY_FT = 6.0       # shutoff depth below grade — the code number for this fixture

# The raised pedestal. A garage floor runs salt slush all winter, and a sleeve entry at slab
# level sits in it; this lifts the penetration 4" clear so the sealant joint is above the wet
# line rather than in it.
#
# A ``Slab`` with ``datum="walking_surface"``, not a ``Pad``: a Pad is an isolated footing
# bearing on soil, which is what ``structural.frost_depth`` reads it as — and it is right to,
# because a Pad at 0'-0" really would be a footing above the frost line. This is a topping
# pour riding on SL-G-FLOOR, so it is filed with that slab on ``main`` (the garage storey
# datum is the stem top at +1'-10", not the slab) and rides 4" proud of the 0'-0" floor.
_PED_HALF = 0.75  # 1'-6" square
GARAGE_HYDRANT_PEDESTAL = Slab(
    uid="CGP601AAAA", tag="SL-G-HYDRANT-PED",
    outline=(pt(ft(HYDRANT_X_FT - _PED_HALF), ft(HYDRANT_Y_FT - _PED_HALF)),
             pt(ft(HYDRANT_X_FT + _PED_HALF), ft(HYDRANT_Y_FT - _PED_HALF)),
             pt(ft(HYDRANT_X_FT + _PED_HALF), ft(HYDRANT_Y_FT + _PED_HALF)),
             pt(ft(HYDRANT_X_FT - _PED_HALF), ft(HYDRANT_Y_FT + _PED_HALF))),
    thickness=inch(4), datum="walking_surface",
)

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
# So it sits right on the hydrant's own stack (HYDRANT_X_FT, HYDRANT_Y_FT), not offset to
# clear the west footing: the weep needs stone at the valve, not stone somewhere else that
# a pipe would have to carry it to. What clears the footing is depth, not plan offset — the
# stone starts a foot above the shutoff (well below the footing's -4'-2" bearing) and runs
# down past it, so nothing here is beside the footing at the footing's own depth.
GARAGE_HYDRANT_DRYWELL = Drywell(
    uid="CGP603AAAA", tag="DRW-G-HYDRANT",
    position=pt(ft(HYDRANT_X_FT), ft(HYDRANT_Y_FT)),
    diameter=ft(2), depth=ft(4), top_elevation=ft(-(HYDRANT_BURY_FT - 1)),
    geotextile=True, inlet_refs=("FX-G-HYDRANT",),
)

BASEMENT_ELEMENTS = [*HOUSE_FOOTINGS, *HOUSE_FOOTING_BEDDING, *VENEER_PLINTH,
                     *VENEER_PLINTH_BEDDING, *GARAGE_STEM_NODES,
                     *GARAGE_STEM_WALLS, *GARAGE_FOOTINGS, GARAGE_HYDRANT_DRYWELL]
MAIN_ELEMENTS = [GARAGE_SLAB, GARAGE_HYDRANT_PEDESTAL, GARAGE_HYDRANT_SLEEVE]
