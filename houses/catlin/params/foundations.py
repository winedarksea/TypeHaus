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
    Footing,
    FootingBedding,
    FoundationWall,
    Node,
    Slab,
    SlabThermalBreak,
    ft,
    inch,
    pt,
)

# One source of truth for where the garage stands: the wall lines the wood walls above are
# authored on. The stem must sit under them and the slab inside them, so both derive from
# there rather than repeating the literal.
from plan.storeys.garage import GARAGE_Y_NORTH, GARAGE_Y_SOUTH

# --- house strip footings --------------------------------------------------------
_HOUSE_WALL_TAGS = [
    "W-B-S1", "W-B-S2", "W-B-S3", "W-B-E1", "W-B-E2", "W-B-N1", "W-B-N2",
    "W-B-N3", "W-B-W1", "W-B-W2", "W-B-CS", "W-B-CS2", "W-B-CN", "W-B-CW",
    "W-B-CE", "W-B-STR",
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

# --- garage ICF stem (basement storey; absolute elevations) -----------------------
_FROST = 42.0 / 12.0  # frost depth below grade
_STEM_TOP = 22.0 / 12.0  # exposed above grade

GARAGE_STEM_NODES = [
    Node(uid="CGF001AAAA", tag="N-GF-SW", position=pt(ft(0), GARAGE_Y_SOUTH)),
    Node(uid="CGF002AAAA", tag="N-GF-SE", position=pt(ft(24), GARAGE_Y_SOUTH)),
    Node(uid="CGF003AAAA", tag="N-GF-NE", position=pt(ft(24), GARAGE_Y_NORTH)),
    Node(uid="CGF004AAAA", tag="N-GF-NW", position=pt(ft(0), GARAGE_Y_NORTH)),
]

_STEM = dict(assembly="GARAGE_ICF_8", top_elevation=ft(_STEM_TOP),
             bottom_elevation=ft(-_FROST))

GARAGE_STEM_WALLS = [
    FoundationWall(uid="CGF101AAAA", tag="W-GF-S", start_node="N-GF-SW",
                   end_node="N-GF-SE", **_STEM),
    FoundationWall(uid="CGF102AAAA", tag="W-GF-E", start_node="N-GF-SE",
                   end_node="N-GF-NE", **_STEM),
    FoundationWall(uid="CGF103AAAA", tag="W-GF-N", start_node="N-GF-NE",
                   end_node="N-GF-NW", **_STEM),
    FoundationWall(uid="CGF104AAAA", tag="W-GF-W", start_node="N-GF-NW",
                   end_node="N-GF-SW", **_STEM),
]

GARAGE_FOOTINGS = [
    Footing(uid=f"CGF20{i}AAAA", tag=f"FT-{w.tag[2:]}", under=w.tag,
            width=inch(20), depth=inch(8))
    for i, w in enumerate(GARAGE_STEM_WALLS, start=1)
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

BASEMENT_ELEMENTS = [*HOUSE_FOOTINGS, *HOUSE_FOOTING_BEDDING, *GARAGE_STEM_NODES,
                     *GARAGE_STEM_WALLS, *GARAGE_FOOTINGS]
MAIN_ELEMENTS = [GARAGE_SLAB]
