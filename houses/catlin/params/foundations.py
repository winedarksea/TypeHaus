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

# Bearing prep below every house footing: 7" undercut, geotextile, drain tile, compacted
# washed stone — a drained bearing surface that also breaks footing-to-wet-clay thermal
# contact. 4" perimeter foam matches CATLIN_BASEMENT_12's exterior XPS.
HOUSE_FOOTING_BEDDING = [
    FootingBedding(uid=f"CFB{i:03d}AAAA", tag=f"FB-{f.tag[3:]}", host_ref=f.tag,
                   undercut=inch(7), perimeter_insulation=inch(4),
                   drain_tile_spec=DrainTile(diameter=inch(4), sock=True,
                                             discharge="daylight"))
    for i, f in enumerate(HOUSE_FOOTINGS, start=1)
]

# --- glazed-brick veneer plinth (W-B-BRICK) ---------------------------------------
# Deliberately NOT appended to _HOUSE_WALL_TAGS: that loop pours a 20"x8" strip monolithic
# with the house footing, which is the thermal bridge this detail exists to avoid. Instead
# it's a shallow plinth cast ON the house footing's projecting toe (FT-B-S2/S3's toe runs
# 10" south of the brick face), separated by a 2" XPS bed (FB-B-BRICK) rather than a
# ``Dowel`` block — ``Dowel.axis`` can't describe a horizontal bed, so the veneer's own
# masonry ties do that job instead (plans/TODO.md).
#
# 10"x5": 10" wide clears the brick's outer face (-9.175") with ~0.4" to spare and stays
# inside the house footing's -10" edge; 5" deep over the 2" bed tops out at -8'-5",
# D-B-PATIO's raised threshold — the highest it can go without crossing the door. Full
# derivation on W-B-BRICK in plan/storeys/basement.py.
#
# Stops at x=28' on the sunken garden's east wall axis, where FT-SG-E1 already breaks
# thermally from the house footing — no third break needed, no collision (FT-SG-E1 sits
# 1'-5" below this plinth).
VENEER_PLINTH = [
    Footing(uid="CFV301AAAA", tag="FT-B-BRICK", under="W-B-BRICK",
            width=inch(10), depth=inch(5)),
]

# Same ``cast_foam_in_aggregate`` record the sunken garden's house-adjacent footings carry
# (2" 40psi XPS), used here as a bed rather than a block. No drain tile: sits a foot above
# the house footing's own tile with nothing to collect.
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
# A car can't climb a 22" ICF stem, so the east stem gaps at the overhead door: the flanking
# segments keep the full reveal, and the segment behind the door becomes a grade beam flush
# with the slab (0'-0"), no curb across the opening. W-G-E above is untouched (splitting it
# would break the ridge closure it carries) — the door reaches down via a negative
# sill_height in plan/storeys/garage.py instead.
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
    # Service door gap in the south stem (2026-08-01). Unlike the overhead door's gap, this
    # one gets 3" margin each side: the hydrant line (PR-G-HYDRANT-CW) crosses buried at
    # x=5'-0", exactly the door's west jamb, so a flush gap would land the crossing on the
    # joint between two footings and trip mep.footing_clearance in both. The wider block-out
    # puts it unambiguously inside the grade beam.
    Node(uid="CGF007AAAA", tag="N-GF-S-DRW",
         position=pt(SERVICE_DOOR_OFFSET - _SERVICE_GAP_MARGIN, GARAGE_Y_SOUTH)),
    Node(uid="CGF008AAAA", tag="N-GF-S-DRE",
         position=pt(SERVICE_DOOR_OFFSET + SERVICE_DOOR_WIDTH + _SERVICE_GAP_MARGIN,
                     GARAGE_Y_SOUTH)),
]

# Aligns the stem's exterior EPS face to the 24'x24' node line, which is also the wood
# walls' zip-R plane (`alignment=face("zip-r-ext")` above) — coplanar, so only the 7/8"
# rainscreen + cladding projects past and drips clear. Left unaligned it stood 5 5/8" proud
# of the cladding, a shelf for rain to pool on (plans/TODO.md).
#
# Uses `face("concrete-ext")`, not `face("eps-ext")`: the fuzzy prefix matcher in
# resolve/topology.py would match "eps-ext" to the *eps-int* layer first. Concrete face is
# unambiguous and already the basement walls' datum; offsetting the axis outward by one EPS
# thickness lands the exterior foam face on the node line.
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

# Not a comprehension any more: the east wall split into three, and a fresh uid per item
# would reassign CGF203/204AAAA (footings that didn't conceptually change) to the new door
# pieces. Original uids are kept; only the grade beam and far door-split piece are new.
#
# `center_on="wall"`: the stem runs 0"..11" inboard of the raw node line, so a 20" strip
# centred on the node line (the default) would leave 10" of toe under nothing. Centred on
# the resolved section instead, the toe is a symmetric 4 1/2" each side.
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

# Filed on "main", not "garage": the garage storey datum is the ICF stem top (1'-10"), but
# this slab pours at grade. Inset from the wall lines = the 11" stem section + the usual
# 1/2" gap to the stem's interior face, keeping the pour inside the stem.
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
# FX-G-HYDRANT stands on the west wall near the NW corner. The sleeve and drywell below it
# are not UI-movable, so they live here rather than in editable plan/fixtures.py.
#
# ``_FROST`` above is the *footing* frost depth (42"); the hydrant's 72" bury is a separate
# number — its own shutoff-valve depth, 2'-6" below the ICF stem bottom, consistent but not
# the same thing.
#
# Position (2026-08-15): the hydrant is freestanding, not wall-mounted, because nowhere on
# a wall clears the footings' 45° bearing-influence line at this bury depth. The old NW
# corner spot (1'-6", 62') had the weep-stone pocket overlapping FT-GF-W outright — only
# passing footing_clearance because of a sleeve that bore concrete the pipe never touched
# (deleted). The clear zone is x >= 4'-10 1/2", y <= 59'-7 7/8", floor not wall — no wall
# position works here, so it stands free like a yard hydrant should (Y34 barrel, unlike the
# two wall hydrants in plan/fixtures.py).
#
# x=5'-0" sits on the existing supply line (PR-G-HYDRANT-CW runs north at x=5'-0" through
# three sleeves), keeping the run straight instead of jogging. y=59'-6" clears FT-GF-N by
# 35 7/8" (34" required) and stays inside the overhead door's 45'..61' band.
#
# Consequence: the hydrant sits 5' out into the parking area, not against the wall — every
# compliant position here is in the room. Mitigate with a bollard/wheel stop if needed;
# don't move it back to the wall.
HYDRANT_X_FT = 5.0          # on the service line — the run reaches it without a jog
HYDRANT_Y_FT = 59.5         # north bay, clear of FT-GF-N's influence line
HYDRANT_BURY_FT = 6.0       # shutoff depth below grade — the code number for this fixture

# A 4" topping pedestal (SL-G-HYDRANT-PED) that lifted the slab penetration above the
# salt-slush wet line was retired 2026-08-03 by owner decision. Replaced by spec, not
# geometry — a flexible chloride-tolerant sealant at the penetration instead (see
# notes/garage_hydrant.md). Bury, sleeve, and drywell below grade are unchanged.

# Filed on "main" with SL-G-FLOOR (the slab it passes through), because
# ``_missing_sleeve_findings`` scopes its containment test to ``solid.storey == storey.tag``
# — the fixture above is on "garage". purpose=WATER_COLD, not the DRAIN default: carries
# supply down only.
GARAGE_HYDRANT_SLEEVE = SleevePenetration(
    uid="CGP602AAAA", tag="SP-G-HYDRANT", host_ref="SL-G-FLOOR",
    position=pt(ft(HYDRANT_X_FT), ft(HYDRANT_Y_FT)),
    pipe_diameter=inch(0.75), sleeve_diameter=inch(2),
    serves_fixture="FX-G-HYDRANT", purpose=Service.WATER_COLD,
)

# The gravel bed FX-G-HYDRANT's own weep drains into: a Woodford Y34-style frost-free
# hydrant self-drains through a weep hole at its buried shutoff, into stone packed around
# the valve. Not a catch basin for wash-down water, no floor-drain reading (see
# notes/garage_hydrant.md) — solely the hydrant's own weep. Modeled as a FootingBedding only
# because that was the closest thing available; the stand-in was billing its excavation
# perimeter as (nonexistent) perimeter drain tile in the sitework take-off.
#
# Sits directly on the hydrant's own stack (HYDRANT_X_FT/Y_FT) — the pocket, being the
# deepest excavation in the assembly, is what the 45° influence line grades hardest, so it
# (not the pipe) sets how far out the fixture stands. See HYDRANT_X_FT above.
#
# Re-sized 2026-08-15 from 2'x4' deep (12.6 cu ft, bottom -9'-0", overlapped FT-GF-W by 4"
# in plan — nothing was grading it, since `mep.footing_clearance` only walks pipe runs) down
# to 1'-6"x1'-6" deep, top -5'-6", ~2.6 cu ft. Bottom -7'-0" is 34" below bearing; the
# stone's edge stands 35 1/2" off FT-GF-W and 35 7/8" off FT-GF-N — no slack left in either.
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
