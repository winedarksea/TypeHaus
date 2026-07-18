"""Sunken garden / porch / balcony structure — parametric module (WP3.1).

One freestanding concrete structure immediately south of the house (5" gap from the
house cladding face): a two-storey arched porch box against the house, continuing
south as the sunken-garden retaining walls. Ported from ``catlin_house.py``
``SunkenGardenSpec`` + the porch/garden build section.

Coordinates are in the shared project-north plan frame (house sheathing SW corner at
0,0). Everything here is generated — these elements carry no editable-source location.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus import (
    Arch,
    Footing,
    FoundationWall,
    Node,
    RoughOpening,
    Slab,
    from_node,
    ft,
    inch,
    pt,
)

from params.arches import arch_offsets_ft


@dataclass(frozen=True)
class SunkenGardenSpec:
    clear_width_ft: float = 18.0  # E-W between wall inner faces
    clear_length_ft: float = 28.0  # N-S between wall inner faces
    porch_clear_depth_ft: float = 8.0  # N-S inside the porch box
    gap_to_house_in: float = 5.0  # house cladding face -> north wall outer face
    wall_thickness_in: float = 12.0
    footing_width_in: float = 84.0  # 36" toe + 12" wall + 36" heel
    footing_thickness_in: float = 12.0
    house_size_ft: float = 36.0
    house_ext_layers_in: float = 5.0  # polyiso+EPS+furring+cladding beyond sheathing
    basement_depth_ft: float = 9.0
    slab_thickness_in: float = 3.5
    deck_thickness_in: float = 1.5
    box_top_ft: float = 9.0  # deck walking surface (second-storey elevation)
    retaining_top_ft: float = 0.5
    arches_per_wall: int = 2
    arch_clear_width_ft: float = 8.0
    arch_outer_pier_ft: float = 1.0
    arch_opening_height_ft: float = 8.0
    side_door_width_ft: float = 4.0
    side_door_height_ft: float = 8.0


SPEC = SunkenGardenSpec()

_t = SPEC.wall_thickness_in / 12.0
_half = _t / 2.0

# E-W: garden centered on the house centerline.
_cx = SPEC.house_size_ft / 2.0
_x_in_w = _cx - SPEC.clear_width_ft / 2.0  # 9.0
_x_in_e = _cx + SPEC.clear_width_ft / 2.0  # 27.0
_x_ax_w = _x_in_w - _half
_x_ax_e = _x_in_e + _half

# N-S: north wall outer face sits gap_to_house south of the house cladding face.
_y_out_n = -(SPEC.house_ext_layers_in + SPEC.gap_to_house_in) / 12.0
_y_ax_n = _y_out_n - _half
_y_in_n = _y_out_n - _t
_y_in_arch = _y_in_n - SPEC.porch_clear_depth_ft
_y_ax_arch = _y_in_arch - _half
_y_in_s = _y_in_n - SPEC.clear_length_ft
_y_ax_s = _y_in_s - _half

_wall_bottom = ft(-(SPEC.basement_depth_ft + 0.75))
_box_top = ft(SPEC.box_top_ft)
_ret_top = ft(SPEC.retaining_top_ft)
_slab_top = -SPEC.basement_depth_ft + SPEC.slab_thickness_in / 12.0

NODES = [
    Node(uid="SGN001AAAA", tag="N-SG-NW", position=pt(ft(_x_ax_w), ft(_y_ax_n))),
    Node(uid="SGN002AAAA", tag="N-SG-NE", position=pt(ft(_x_ax_e), ft(_y_ax_n))),
    Node(uid="SGN003AAAA", tag="N-SG-MW", position=pt(ft(_x_ax_w), ft(_y_ax_arch))),
    Node(uid="SGN004AAAA", tag="N-SG-ME", position=pt(ft(_x_ax_e), ft(_y_ax_arch))),
    Node(uid="SGN005AAAA", tag="N-SG-SW", position=pt(ft(_x_ax_w), ft(_y_ax_s))),
    Node(uid="SGN006AAAA", tag="N-SG-SE", position=pt(ft(_x_ax_e), ft(_y_ax_s))),
]

WALLS = [
    # Porch box (full height: garden floor to deck).
    FoundationWall(uid="SGW101AAAA", tag="W-SG-N", start_node="N-SG-NW",
                   end_node="N-SG-NE", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_box_top, bottom_elevation=_wall_bottom),
    FoundationWall(uid="SGW102AAAA", tag="W-SG-ARCH", start_node="N-SG-MW",
                   end_node="N-SG-ME", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_box_top, bottom_elevation=_wall_bottom),
    FoundationWall(uid="SGW103AAAA", tag="W-SG-W1", start_node="N-SG-NW",
                   end_node="N-SG-MW", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_box_top, bottom_elevation=_wall_bottom),
    FoundationWall(uid="SGW104AAAA", tag="W-SG-E1", start_node="N-SG-NE",
                   end_node="N-SG-ME", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_box_top, bottom_elevation=_wall_bottom),
    # Garden retaining run (to just above grade).
    FoundationWall(uid="SGW105AAAA", tag="W-SG-W2", start_node="N-SG-MW",
                   end_node="N-SG-SW", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom),
    FoundationWall(uid="SGW106AAAA", tag="W-SG-E2", start_node="N-SG-ME",
                   end_node="N-SG-SE", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom),
    FoundationWall(uid="SGW107AAAA", tag="W-SG-S", start_node="N-SG-SW",
                   end_node="N-SG-SE", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom),
]

FOOTINGS = [
    Footing(uid=f"SGF10{i}AAAA", tag=f"FT-{w.tag[2:]}", under=w.tag,
            width=inch(SPEC.footing_width_in), depth=inch(SPEC.footing_thickness_in))
    for i, w in enumerate(WALLS, start=1)
]

# --- arches -------------------------------------------------------------------
# Both arched walls carry two tiers of arches: garden level and porch level.
_axis_len = _x_ax_e - _x_ax_w
_offsets = arch_offsets_ft(
    wall_length_ft=_axis_len,
    n_arches=SPEC.arches_per_wall,
    arch_width_ft=SPEC.arch_clear_width_ft,
    outer_pier_ft=SPEC.arch_outer_pier_ft + (_x_in_w - _x_ax_w),
)
_arch = Arch(rise=ft(SPEC.arch_clear_width_ft / 2.0))
_door_arch = Arch(rise=ft(SPEC.side_door_width_ft / 2.0))

# Sills are relative to the basement storey elevation (-9').
_garden_sill = ft(SPEC.slab_thickness_in / 12.0)
_porch_sill = ft(SPEC.basement_depth_ft)

ARCH_OPENINGS = []
_uid_seq = 0
for _wall_tag, _node_tag in (("W-SG-N", "N-SG-NW"), ("W-SG-ARCH", "N-SG-MW")):
    for _level_name, _sill in (("G", _garden_sill), ("P", _porch_sill)):
        for _k, _off in enumerate(_offsets, start=1):
            _uid_seq += 1
            ARCH_OPENINGS.append(
                RoughOpening(
                    uid=f"SGA{_uid_seq:03d}AAAA",
                    tag=f"AO-{_wall_tag[5:]}-{_level_name}{_k}",
                    host=_wall_tag,
                    position=from_node(_node_tag, ft(_off)),
                    width=ft(SPEC.arch_clear_width_ft),
                    height=ft(SPEC.arch_opening_height_ft),
                    sill_height=_sill,
                    arch=_arch,
                )
            )

# Side-wall arched doorways at porch level (west + east), centered in the box bay.
_door_off = (SPEC.porch_clear_depth_ft + _t - SPEC.side_door_width_ft) / 2.0
ARCH_OPENINGS.extend([
    RoughOpening(uid="SGA901AAAA", tag="AO-W1-P", host="W-SG-W1",
                 position=from_node("N-SG-NW", ft(_door_off)),
                 width=ft(SPEC.side_door_width_ft),
                 height=ft(SPEC.side_door_height_ft),
                 sill_height=_porch_sill, arch=_door_arch),
    RoughOpening(uid="SGA902AAAA", tag="AO-E1-P", host="W-SG-E1",
                 position=from_node("N-SG-NE", ft(_door_off)),
                 width=ft(SPEC.side_door_width_ft),
                 height=ft(SPEC.side_door_height_ft),
                 sill_height=_porch_sill, arch=_door_arch),
])

# --- slabs / decks ---------------------------------------------------------------
GARDEN_SLAB = Slab(
    uid="SGS501AAAA", tag="SL-SG-FLOOR",
    outline=(pt(ft(_x_in_w), ft(_y_in_s)), pt(ft(_x_in_e), ft(_y_in_s)),
             pt(ft(_x_in_e), ft(_y_in_n)), pt(ft(_x_in_w), ft(_y_in_n))),
    thickness=inch(SPEC.slab_thickness_in),
)

PORCH_FLOOR = Slab(
    uid="SGS502AAAA", tag="SL-SG-PORCH",
    outline=(pt(ft(_x_in_w), ft(_y_in_arch)), pt(ft(_x_in_e), ft(_y_in_arch)),
             pt(ft(_x_in_e), ft(_y_in_n)), pt(ft(_x_in_w), ft(_y_in_n))),
    thickness=inch(SPEC.deck_thickness_in),
)

DECK_FLOOR = Slab(
    uid="SGS503AAAA", tag="SL-SG-DECK",
    outline=(pt(ft(_x_in_w), ft(_y_in_arch)), pt(ft(_x_in_e), ft(_y_in_arch)),
             pt(ft(_x_in_e), ft(_y_in_n)), pt(ft(_x_in_w), ft(_y_in_n))),
    thickness=inch(SPEC.deck_thickness_in),
)

BASEMENT_ELEMENTS = [*NODES, *WALLS, *FOOTINGS, *ARCH_OPENINGS, GARDEN_SLAB]
MAIN_ELEMENTS = [PORCH_FLOOR]
SECOND_ELEMENTS = [DECK_FLOOR]
