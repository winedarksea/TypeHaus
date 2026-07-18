"""Generated foundation support: house footings, garage ICF stem, breezeway posts.

- House: strip footings (20" x 8") under every basement concrete wall.
- Garage: freestanding ICF stem (8" core) from frost depth to 22" above grade,
  wood walls bear on top (the ``garage`` storey elevation), footing under.
- Breezeway: the porch roof between house and garage rides on freestanding 6x6
  posts on isolated pads — never attached to either structure.
"""

from __future__ import annotations

from typehaus import Footing, FoundationWall, Node, Pad, Post, Slab, ft, inch, pt

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

# --- garage ICF stem (basement storey; absolute elevations) -----------------------
_FROST = 42.0 / 12.0  # frost depth below grade
_STEM_TOP = 22.0 / 12.0  # exposed above grade

GARAGE_STEM_NODES = [
    Node(uid="CGF001AAAA", tag="N-GF-SW", position=pt(ft(0), ft(48))),
    Node(uid="CGF002AAAA", tag="N-GF-SE", position=pt(ft(24), ft(48))),
    Node(uid="CGF003AAAA", tag="N-GF-NE", position=pt(ft(24), ft(72))),
    Node(uid="CGF004AAAA", tag="N-GF-NW", position=pt(ft(0), ft(72))),
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

# --- breezeway posts (freestanding; roof is future work) --------------------------
_POST_XY = [(5.0, 44.0), (9.0, 44.0), (5.0, 47.5), (9.0, 47.5)]

BREEZEWAY_PADS = [
    Pad(uid=f"CP{i}00AAAAA", tag=f"PD-BW-{i}",
        outline=(pt(ft(x - 1), ft(y - 1)), pt(ft(x + 1), ft(y - 1)),
                 pt(ft(x + 1), ft(y + 1)), pt(ft(x - 1), ft(y + 1))),
        thickness=ft(1))
    for i, (x, y) in enumerate(_POST_XY, start=1)
]

BREEZEWAY_POSTS = [
    Post(uid=f"CP{i}50AAAAA", tag=f"PT-BW-{i}", position=pt(ft(x), ft(y)),
         size="6x6", height=ft(8), supported_by=f"PD-BW-{i}")
    for i, (x, y) in enumerate(_POST_XY, start=1)
]

GARAGE_SLAB = Slab(
    uid="CGS501AAAA", tag="SL-G-FLOOR",
    outline=(pt(ft(0.5), ft(48.5)), pt(ft(23.5), ft(48.5)),
             pt(ft(23.5), ft(71.5)), pt(ft(0.5), ft(71.5))),
    thickness=inch(3.5),
)

BASEMENT_ELEMENTS = [*HOUSE_FOOTINGS, *GARAGE_STEM_NODES, *GARAGE_STEM_WALLS,
                     *GARAGE_FOOTINGS]
MAIN_ELEMENTS = [*BREEZEWAY_PADS, *BREEZEWAY_POSTS, GARAGE_SLAB]
