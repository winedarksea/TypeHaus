"""Sunken garden / porch / balcony structure — parametric module (WP3.1, redesign).

One freestanding concrete + wood structure immediately south of the house (5" gap from
the house cladding face). It is fully independent of the house — the two share only a
compacted footing bed, with the footings doweled together through a fiberglass-rebar +
40 psi XPS foam thermal break (see FOOTING_BEDDING / the dowel note below).

Vertical stack (project-north frame; +X east, +Y north, +Z up):
- Sunken garden floor at the basement storey (-9'): a U-shaped cantilever-T retaining
  wall (open to the north) on a 42" compacted-aggregate base down to frost.
- The north 8' of that U is the *porch*: a 16" arched "front" cross-wall (three piers +
  two arches) on the south, two 12" side walls, and — on the north (house) side — NO
  concrete wall. That north edge is carried by a 12" sonotube column at midspan plus two
  PT 2x12 back beams hung into the side walls. PT 2x8 joists span N-S from the front-wall
  sill to the back beams; composite decking is the walking surface. Porch floor = main (0').
- A masonry "railing" (white brick / air gap / grouted CMU / stucco) rides the front + side
  walls as the porch guard; its grouted CMU cores receive the balcony post bases.
- The *balcony* one storey up (second, ~9-10') rides six 6x6 pillars (10' o.c. E-W, 8'
  o.c. N-S; rear row 2" taller for drainage slope) carrying three N-S double-2x10 beams,
  2x8 joists @ 16" o.c., and aluminum (Wahoo AridDeck-style) decking.

Everything here is generated — these elements carry no editable-source location. The
joist framing itself is authored as FloorSystems once the engine can bear joists on beams
and scope a floor to a sub-structure (Phase 2); until then the walking surfaces are Slabs
with a decking assembly and the joist intent lives in the deck-assembly source note.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus import (
    Arch,
    Beam,
    Connector,
    ConnectorKind,
    Dowel,
    Fascia,
    Flashing,
    FloorSystem,
    Footing,
    FootingBedding,
    FoundationWall,
    Gutter,
    JoistSpec,
    Node,
    Post,
    Railing,
    RailingKind,
    RoughOpening,
    Slab,
    TrimKind,
    from_node,
    ft,
    inch,
    pt,
)

from params.arches import arch_offsets_ft


@dataclass(frozen=True)
class SunkenGardenSpec:
    clear_width_ft: float = 19.0  # E-W between wall inner faces (widened for the 6x6 grid)
    clear_length_ft: float = 28.0  # N-S between wall inner faces
    porch_clear_depth_ft: float = 8.0  # N-S inside the porch box
    gap_to_house_in: float = 5.0  # house cladding face -> north edge (insulation gap)
    wall_thickness_in: float = 12.0  # side + retaining walls
    arch_wall_thickness_in: float = 16.0  # front cross-wall: arch piers + 3.5" joist bearing
    footing_width_in: float = 84.0  # 36" toe + 12" wall + 36" heel
    footing_thickness_in: float = 12.0
    aggregate_bedding_depth_in: float = 42.0
    house_size_ft: float = 36.0
    house_ext_layers_in: float = 5.0  # polyiso+EPS+furring+cladding beyond sheathing
    basement_depth_ft: float = 9.0
    slab_thickness_in: float = 3.5
    porch_top_ft: float = 0.0  # top of the porch concrete walls = porch floor / railing base
    railing_height_ft: float = 3.5  # 42" masonry guard above the porch floor
    retaining_top_ft: float = 0.5
    # arches (single garden-level tier, two arches across the 16" front wall)
    arches_per_wall: int = 2
    arch_clear_width_ft: float = 8.0
    arch_outer_pier_ft: float = 1.0
    arch_opening_height_ft: float = 8.0  # total: 4' straight + 4' semicircular rise
    # porch framing
    column_diameter_in: float = 12.0  # sonotube back-beam support
    porch_joist: str = "2x8"
    porch_joist_oc_in: float = 16.0
    back_beam: str = "2-2x12"  # PT, two ~9'6" spans column -> side-wall hangers
    porch_deck_thickness_in: float = 1.0  # composite plank
    # balcony framing
    pillar_size: str = "6x6"
    rear_pillar_rise_in: float = 2.0  # rear row taller for drainage slope
    balcony_beam: str = "2-2x10"  # three N-S beams over the pillar lines
    balcony_joist: str = "2x8"
    balcony_joist_oc_in: float = 16.0
    balcony_deck_thickness_in: float = 1.5  # aluminum plank
    joist_cantilever_in: float = 6.0  # deck joist tips overhang the outer beams
    balcony_level_ft: float = 10.0  # second storey


SPEC = SunkenGardenSpec()

_t = SPEC.wall_thickness_in / 12.0
_half = _t / 2.0
_arch_t = SPEC.arch_wall_thickness_in / 12.0
_arch_half = _arch_t / 2.0

# E-W: garden centered on the house centerline. Side-wall axes land 20' apart (19' clear
# + 2x 6" half-walls) so the balcony pillars sit on a clean 10' o.c. E-W grid.
_cx = SPEC.house_size_ft / 2.0  # 18.0
_x_in_w = _cx - SPEC.clear_width_ft / 2.0  # 8.5
_x_in_e = _cx + SPEC.clear_width_ft / 2.0  # 27.5
_x_ax_w = _x_in_w - _half  # 8.0
_x_ax_e = _x_in_e + _half  # 28.0

# N-S: the whole structure's north face sits gap_to_house south of the house cladding face
# (a 5" insulation gap). With the north wall removed there is no wall thickness to inset —
# the side-wall north-end nodes, the porch deck edge, and the back-beam/column line all land
# on that one north-edge line so the deck actually reaches to within 5" of the house.
_y_out_n = -(SPEC.house_ext_layers_in + SPEC.gap_to_house_in) / 12.0  # -0.833'
_y_ax_n = _y_out_n  # side-wall north-end nodes (open ends terminate here → face at the gap)
_y_in_n = _y_out_n  # porch deck north edge / back-beam + column line
_y_in_arch = _y_in_n - SPEC.porch_clear_depth_ft  # north (inner) face of the 16" front wall
_y_ax_arch = _y_in_arch - _arch_half  # front-wall axis (arch nodes + arch railing + front pillars)
_y_in_s = _y_in_n - SPEC.clear_length_ft
_y_ax_s = _y_in_s - _half

_wall_bottom = ft(-(SPEC.basement_depth_ft + 0.75))
_porch_top = ft(SPEC.porch_top_ft)
_ret_top = ft(SPEC.retaining_top_ft)
_railing_top = ft(SPEC.porch_top_ft + SPEC.railing_height_ft)
_balcony = ft(SPEC.balcony_level_ft)

# ============================================================================
# Basement: garden retaining walls, 16" arched front wall, footings, column.
# ============================================================================
NODES = [
    Node(uid="SGN001AAAA", tag="N-SG-NW", position=pt(ft(_x_ax_w), ft(_y_ax_n)),
         open_end=True),  # north wall removed — side wall terminates here (freestanding)
    Node(uid="SGN002AAAA", tag="N-SG-NE", position=pt(ft(_x_ax_e), ft(_y_ax_n)),
         open_end=True),
    Node(uid="SGN003AAAA", tag="N-SG-MW", position=pt(ft(_x_ax_w), ft(_y_ax_arch))),
    Node(uid="SGN004AAAA", tag="N-SG-ME", position=pt(ft(_x_ax_e), ft(_y_ax_arch))),
    Node(uid="SGN005AAAA", tag="N-SG-SW", position=pt(ft(_x_ax_w), ft(_y_ax_s))),
    Node(uid="SGN006AAAA", tag="N-SG-SE", position=pt(ft(_x_ax_e), ft(_y_ax_s))),
]

WALLS = [
    # Porch box: 16" arched front cross-wall + two 12" side walls, topping at the porch
    # floor (the balcony above rides on 6x6 pillars, not a concrete box).
    FoundationWall(uid="SGW102AAAA", tag="W-SG-ARCH", start_node="N-SG-MW",
                   end_node="N-SG-ME", assembly="SUNKEN_GARDEN_ARCH_16",
                   top_elevation=_porch_top, bottom_elevation=_wall_bottom),
    FoundationWall(uid="SGW103AAAA", tag="W-SG-W1", start_node="N-SG-NW",
                   end_node="N-SG-MW", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_porch_top, bottom_elevation=_wall_bottom),
    # East runs south→north (and the west runs north→south) so both side walls wind the same
    # way around the garden: with the basement storey's outward sign of -1, a wall's exterior
    # is the *right*-hand normal of its authored direction, so the east wall must be authored
    # ME→NE for its outer face to land east. (Latent here — SUNKEN_GARDEN_WALL is one layer of
    # concrete — but the same winding drives the layered railing above, so keep them in step.)
    FoundationWall(uid="SGW104AAAA", tag="W-SG-E1", start_node="N-SG-ME",
                   end_node="N-SG-NE", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_porch_top, bottom_elevation=_wall_bottom),
    # Garden retaining run (to just above grade), the U south of the porch.
    FoundationWall(uid="SGW105AAAA", tag="W-SG-W2", start_node="N-SG-MW",
                   end_node="N-SG-SW", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom),
    FoundationWall(uid="SGW106AAAA", tag="W-SG-E2", start_node="N-SG-SE",
                   end_node="N-SG-ME", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom),
    FoundationWall(uid="SGW107AAAA", tag="W-SG-S", start_node="N-SG-SW",
                   end_node="N-SG-SE", assembly="SUNKEN_GARDEN_WALL",
                   top_elevation=_ret_top, bottom_elevation=_wall_bottom),
]

# Sonotube column (12" round) at the porch's north edge midspan, carrying the two back
# beams. Its top lands on the 2x12 back-beam soffit (one beam depth below the 0' porch
# deck), so the beams seat directly on the column and it reads "slightly shorter than the
# arched front wall". Base at the column footing top (basement elevation, -9').
_back_beam_depth_ft = 11.25 / 12.0  # 2x12 actual depth
COLUMN = Post(uid="SGP001AAAA", tag="PT-SG-COL",
              position=pt(ft(_cx), ft(_y_in_n)), size="12 round",
              height=ft(SPEC.basement_depth_ft - _back_beam_depth_ft),
              supported_by="FT-SG-COL")

FOOTINGS = [
    Footing(uid=f"SGF10{i}AAAA", tag=f"FT-{w.tag[2:]}", under=w.tag,
            width=inch(SPEC.footing_width_in), depth=inch(SPEC.footing_thickness_in))
    for i, w in enumerate(WALLS, start=1)
]
# Spread footing (bell) under the sonotube column.
FOOTINGS.append(
    Footing(uid="SGF199AAAA", tag="FT-SG-COL", under="PT-SG-COL",
            width=inch(30), depth=inch(12))
)

# All footings bear on a shared 42" compacted-aggregate section. The footings adjacent to
# the house (the two porch side walls + the column, along the north edge) are additionally
# doweled to the house footing with fiberglass rebar across a 40 psi XPS foam block that
# breaks the thermal bridge; ``cast_foam_in_aggregate`` records that foam in the resolved
# geometry / IFC (the dowels themselves are annotation-only — see plans/TODO.md).
_HOUSE_ADJACENT = {"FT-SG-W1", "FT-SG-E1", "FT-SG-COL"}
FOOTING_BEDDING = [
    FootingBedding(
        uid=f"SGB{i:03d}AAAA",
        tag=f"FB-{f.tag[3:]}",
        host_ref=f.tag,
        undercut=inch(SPEC.aggregate_bedding_depth_in),
        cast_foam_in_aggregate=f.tag in _HOUSE_ADJACENT,
    )
    for i, f in enumerate(FOOTINGS, start=1)
]

# --- arches: one garden-level tier, two arches across the 16" front wall ----------
# Three piers + two arches ("three columns and an arched beam"). Sill at the garden slab.
_axis_len = _x_ax_e - _x_ax_w
_offsets = arch_offsets_ft(
    wall_length_ft=_axis_len,
    n_arches=SPEC.arches_per_wall,
    arch_width_ft=SPEC.arch_clear_width_ft,
    outer_pier_ft=SPEC.arch_outer_pier_ft + (_x_in_w - _x_ax_w),
)
_arch = Arch(rise=ft(SPEC.arch_clear_width_ft / 2.0))
_garden_sill = ft(SPEC.slab_thickness_in / 12.0)  # relative to the basement storey (-9')

ARCH_OPENINGS = [
    RoughOpening(
        uid=f"SGA{_k:03d}AAAA",
        tag=f"AO-ARCH-G{_k}",
        host="W-SG-ARCH",
        position=from_node("N-SG-MW", ft(_off)),
        width=ft(SPEC.arch_clear_width_ft),
        height=ft(SPEC.arch_opening_height_ft),
        sill_height=_garden_sill,
        arch=_arch,
    )
    for _k, _off in enumerate(_offsets, start=1)
]

# --- garden slab (basement floor of the sunken garden) ---------------------------
GARDEN_SLAB = Slab(
    uid="SGS501AAAA", tag="SL-SG-FLOOR",
    outline=(pt(ft(_x_in_w), ft(_y_in_s)), pt(ft(_x_in_e), ft(_y_in_s)),
             pt(ft(_x_in_e), ft(_y_in_n)), pt(ft(_x_in_w), ft(_y_in_n))),
    thickness=inch(SPEC.slab_thickness_in),
)

# Masonry "railing" on the front + two side walls (not the open north edge). Grouted CMU
# cores receive the balcony post bases. These stack on the concrete porch walls and render
# at 0'-3.5' via absolute elevations, so they stay filed with the freestanding structure
# on the basement storey key (the house's own main/second loops must contain only house
# walls, or storey-orientation detection traces this porch loop by mistake).
RAILING_WALLS = [
    FoundationWall(uid="SGRW01AAAA", tag="W-SG-RAIL-F", start_node="N-SG-MW",
                   end_node="N-SG-ME", assembly="PORCH_RAILING_MASONRY",
                   top_elevation=_railing_top, bottom_elevation=_porch_top),
    FoundationWall(uid="SGRW02AAAA", tag="W-SG-RAIL-W", start_node="N-SG-NW",
                   end_node="N-SG-MW", assembly="PORCH_RAILING_MASONRY",
                   top_elevation=_railing_top, bottom_elevation=_porch_top),
    # ME→NE (not NE→ME): the layered railing stack lays out along the wall's right-hand
    # normal on this storey, so the mirrored winding put the brick wythe on the porch side.
    FoundationWall(uid="SGRW03AAAA", tag="W-SG-RAIL-E", start_node="N-SG-ME",
                   end_node="N-SG-NE", assembly="PORCH_RAILING_MASONRY",
                   top_elevation=_railing_top, bottom_elevation=_porch_top),
]

# ============================================================================
# Main (porch, 0'): back beams on the column, composite deck.
# ============================================================================
MAIN_NODES = [
    Node(uid="SGNM01AAAA", tag="N-SGM-NW", position=pt(ft(_x_ax_w), ft(_y_in_n)),
         open_end=True),
    Node(uid="SGNM02AAAA", tag="N-SGM-NE", position=pt(ft(_x_ax_e), ft(_y_in_n)),
         open_end=True),
    Node(uid="SGNM03AAAA", tag="N-SGM-COL", position=pt(ft(_cx), ft(_y_in_n))),
]

# Two PT 2x12 back beams: sonotube column -> side-wall hangers (two ~9'6" spans).
BACK_BEAMS = [
    Beam(uid="SGBM01AAAA", tag="BM-SG-BKW", start_node="N-SGM-COL", end_node="N-SGM-NW",
         size=SPEC.back_beam, bearing_refs=("PT-SG-COL", "W-SG-W1")),
    Beam(uid="SGBM02AAAA", tag="BM-SG-BKE", start_node="N-SGM-COL", end_node="N-SGM-NE",
         size=SPEC.back_beam, bearing_refs=("PT-SG-COL", "W-SG-E1")),
]

# Composite decking walking surface (framing = PT 2x8 joists, N-S, front sill -> back beams).
PORCH_FLOOR = Slab(
    uid="SGS502AAAA", tag="SL-SG-PORCH",
    outline=(pt(ft(_x_in_w), ft(_y_in_arch)), pt(ft(_x_in_e), ft(_y_in_arch)),
             pt(ft(_x_in_e), ft(_y_in_n)), pt(ft(_x_in_w), ft(_y_in_n))),
    thickness=inch(SPEC.porch_deck_thickness_in),
    assembly="PORCH_DECK_COMPOSITE",
)

# ============================================================================
# Second (balcony, ~10'): 6x6 pillars, three 2x10 beams, aluminum deck.
# ============================================================================
# Six pillars: front (south) row on the arch railing, rear (north) row — outer two on the
# side-wall railings, center on the porch decking. All bear on the porch deck (their bases
# embed in the CMU grout fill of the railing they pass through) so they are anchored at the
# porch floor and stand UP to the balcony-beam soffit — not hung from the deck above.
# The rear (north, house-side) row is 2" taller so the deck crowns at the rear and drains
# south, away from the house.  Beam soffit = balcony level less the 2x10 beam depth (9.25").
# `supported_by` puts the base on SL-SG-PORCH's *top*, i.e. the composite walking surface
# laid over the porch joists, so the authored height is the exposed pillar above the boards.
_balcony_beam_depth_ft = 9.25 / 12.0
_front_h = (ft(SPEC.balcony_level_ft - _balcony_beam_depth_ft)
            - inch(SPEC.porch_deck_thickness_in))
_rear_h = _front_h + inch(SPEC.rear_pillar_rise_in)
_PILLAR_X = (_x_ax_w, _cx, _x_ax_e)
PILLARS = []
for _i, _x in enumerate(_PILLAR_X, start=1):
    PILLARS.append(Post(uid=f"SGPB{_i}0AAAA", tag=f"PT-SG-BR{_i}",
                        position=pt(ft(_x), ft(_y_in_n)), size=SPEC.pillar_size,
                        height=_rear_h, supported_by="SL-SG-PORCH",
                        assembly="POST_WHITE_PAINT"))  # rear (north) row
    PILLARS.append(Post(uid=f"SGPB{_i}1AAAA", tag=f"PT-SG-BF{_i}",
                        position=pt(ft(_x), ft(_y_ax_arch)), size=SPEC.pillar_size,
                        height=_front_h, supported_by="SL-SG-PORCH",
                        assembly="POST_WHITE_PAINT"))  # front (south) row

SECOND_NODES = [
    Node(uid="SGNB01AAAA", tag="N-SGB-NW", position=pt(ft(_x_ax_w), ft(_y_in_n))),
    Node(uid="SGNB02AAAA", tag="N-SGB-SW", position=pt(ft(_x_ax_w), ft(_y_ax_arch))),
    Node(uid="SGNB03AAAA", tag="N-SGB-NC", position=pt(ft(_cx), ft(_y_in_n))),
    Node(uid="SGNB04AAAA", tag="N-SGB-SC", position=pt(ft(_cx), ft(_y_ax_arch))),
    Node(uid="SGNB05AAAA", tag="N-SGB-NE", position=pt(ft(_x_ax_e), ft(_y_in_n))),
    Node(uid="SGNB06AAAA", tag="N-SGB-SE", position=pt(ft(_x_ax_e), ft(_y_ax_arch))),
]

# Three N-S double-2x10 beams over the west / center / east pillar lines.
BALCONY_BEAMS = [
    Beam(uid="SGBB01AAAA", tag="BM-SG-BLW", start_node="N-SGB-NW", end_node="N-SGB-SW",
         size=SPEC.balcony_beam, bearing_refs=("PT-SG-BR1", "PT-SG-BF1")),
    Beam(uid="SGBB02AAAA", tag="BM-SG-BLC", start_node="N-SGB-NC", end_node="N-SGB-SC",
         size=SPEC.balcony_beam, bearing_refs=("PT-SG-BR2", "PT-SG-BF2")),
    Beam(uid="SGBB03AAAA", tag="BM-SG-BLE", start_node="N-SGB-NE", end_node="N-SGB-SE",
         size=SPEC.balcony_beam, bearing_refs=("PT-SG-BR3", "PT-SG-BF3")),
]

# Aluminum decking walking surface (framing = 2x8 joists, E-W @ 16" o.c., on the 3 beams).
# The joists cantilever 6" past the outer (west/east) beam axes, so the decking reaches to
# those tips (beam axis ± cantilever), not just to the inner-face line the beams sit inboard of.
_cant_ft = SPEC.joist_cantilever_in / 12.0
_deck_x_w = _x_ax_w - _cant_ft
_deck_x_e = _x_ax_e + _cant_ft
DECK_FLOOR = Slab(
    uid="SGS503AAAA", tag="SL-SG-DECK",
    outline=(pt(ft(_deck_x_w), ft(_y_ax_arch)), pt(ft(_deck_x_e), ft(_y_ax_arch)),
             pt(ft(_deck_x_e), ft(_y_in_n)), pt(ft(_deck_x_w), ft(_y_in_n))),
    thickness=inch(SPEC.balcony_deck_thickness_in),
    assembly="BALCONY_DECK_ALUMINUM",
)

# --- joist framing under the two decks (rendered members beneath the surface slabs) ---
# Porch: PT 2x8 @ 16" o.c. running N-S from the arched front-wall sill to the two back
# beams on the sonotube column.
PORCH_JOISTS = FloorSystem(
    uid="SGFS01AAAA", tag="FS-SG-PORCH",
    joists=JoistSpec(member=SPEC.porch_joist, spacing=inch(SPEC.porch_joist_oc_in),
                     direction="y", cantilever=inch(SPEC.joist_cantilever_in),
                     bearing_refs=("W-SG-ARCH", "BM-SG-BKW", "BM-SG-BKE")),
    outline=PORCH_FLOOR.outline,
    source="porch floor — PT 2x8 joists, front sill -> back beams",
)

# Balcony: 2x8 @ 16" o.c. running E-W across the three N-S double-2x10 beams.
BALCONY_JOISTS = FloorSystem(
    uid="SGFS02AAAA", tag="FS-SG-DECK",
    joists=JoistSpec(member=SPEC.balcony_joist, spacing=inch(SPEC.balcony_joist_oc_in),
                     direction="x", cantilever=inch(SPEC.joist_cantilever_in),
                     bearing_refs=("BM-SG-BLW", "BM-SG-BLC", "BM-SG-BLE")),
    outline=DECK_FLOOR.outline,
    source="balcony — 2x8 joists on three double-2x10 beams",
)

# ============================================================================
# Fiberglass (GFRP) rebar dowels + 40 psi XPS foam thermal break between the shared
# house/garden footings. The three house-adjacent footings (two porch side walls + the
# sonotube column, along the north edge) pin to the house footing across a 2" XPS block so
# the joint transfers shear without a thermal bridge. Bars at mid-footing (-9.25').
# ============================================================================
_dowel_z = ft(-(SPEC.basement_depth_ft + 0.75) + SPEC.footing_thickness_in / 24.0)  # -9.25'
_DOWEL_AT = (("W1", _x_ax_w), ("E1", _x_ax_e), ("COL", _cx))
DOWELS = [
    Dowel(uid=f"SGDW0{i}AAAA", tag=f"DW-SG-{name}", position=pt(ft(x), ft(_y_in_n)),
          axis="y", length=inch(24), diameter=inch(0.625), elevation=_dowel_z,
          count=3, spacing=inch(8),
          connects=(f"FT-SG-{name}", "FT-B-S2"),
          foam_thickness=inch(2), foam_height=inch(SPEC.footing_thickness_in), foam_psi=40.0)
    for i, (name, x) in enumerate(_DOWEL_AT, start=1)
]

# ============================================================================
# Connector hardware as modeled geometry (was text/notes only). Standoff post bases under
# the six 6x6 balcony pillars, APVKB knee braces at the pillar tops, plus joist hangers /
# hurricane ties at the porch back-beam pockets.
# ============================================================================
_kb_z = ft(SPEC.balcony_level_ft - _balcony_beam_depth_ft - 0.25)  # just under the beam soffit
CONNECTORS = []
for _i, _x in enumerate(_PILLAR_X, start=1):
    for _row, _y in (("R", _y_in_n), ("F", _y_ax_arch)):
        CONNECTORS.append(Connector(
            uid=f"SGCB{_i}{_row}AAAA", tag=f"CN-SG-BASE-{_row}{_i}",
            kind=ConnectorKind.POST_BASE, position=pt(ft(_x), ft(_y)), elevation=_porch_top,
            size="ABU66", connects=(f"PT-SG-B{_row}{_i}", "SL-SG-PORCH")))
        CONNECTORS.append(Connector(
            uid=f"SGCK{_i}{_row}AAAA", tag=f"CN-SG-KB-{_row}{_i}",
            kind=ConnectorKind.KNEEBRACE, position=pt(ft(_x), ft(_y)), elevation=_kb_z,
            size="APVKB", axis="y", connects=(f"PT-SG-B{_row}{_i}",)))
# Porch back-beam pockets: joist hanger into the side wall + hurricane tie over the column.
CONNECTORS += [
    Connector(uid="SGCH01AAAA", tag="CN-SG-HGR-W", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_w), ft(_y_in_n)), elevation=_porch_top, size="LUS210",
              connects=("BM-SG-BKW", "W-SG-W1")),
    Connector(uid="SGCH02AAAA", tag="CN-SG-HGR-E", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_e), ft(_y_in_n)), elevation=_porch_top, size="LUS210",
              connects=("BM-SG-BKE", "W-SG-E1")),
    Connector(uid="SGCT01AAAA", tag="CN-SG-TIE-COL", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_cx), ft(_y_in_n)), elevation=_porch_top, size="H2.5A",
              connects=("BM-SG-BKW", "BM-SG-BKE", "PT-SG-COL")),
]
# Split by storey the hardware sits at: knee braces ride at the balcony beam soffit
# (second), everything else at the porch deck (main).
_TOP_CONNECTORS = [c for c in CONNECTORS if c.kind is ConnectorKind.KNEEBRACE]
_BASE_CONNECTORS = [c for c in CONNECTORS if c.kind is not ConnectorKind.KNEEBRACE]

# ============================================================================
# Balcony guard + edge trim. The metal fascia-mounted guardrail is a first-class Railing
# (not a parapet). PVC fascia closes the joist ends; a front gutter catches the south-
# draining deck via a front-edge drip flashing; the rear (house) edge gets a counter-
# flashing tucked up into the house WRB. Deck drains SOUTH (rear pillars 2" taller).
# ============================================================================
_deck_top = ft(SPEC.balcony_level_ft)  # 10'
# Guard the three open edges (west, front/south, east); the north edge abuts the house.
_GUARD_PATH = (pt(ft(_deck_x_w), ft(_y_in_n)), pt(ft(_deck_x_w), ft(_y_ax_arch)),
               pt(ft(_deck_x_e), ft(_y_ax_arch)), pt(ft(_deck_x_e), ft(_y_in_n)))
BALCONY_GUARD = Railing(
    uid="SGRA01AAAA", tag="RL-SG-BALCONY", path=_GUARD_PATH,
    kind=RailingKind.METAL_FASCIA_MOUNT, height=ft(3.5), base_elevation=_deck_top,
    post_spacing=inch(60), post_size="2x2", rail_count=2, mount="fascia",
    assembly="POST_WHITE_PAINT")

BALCONY_FASCIA = Fascia(
    uid="SGFC01AAAA", tag="TR-SG-FASCIA", kind=TrimKind.FASCIA, path=_GUARD_PATH,
    top_elevation=_deck_top, depth=inch(9), thickness=inch(1), material="PVC",
    host_ref="SL-SG-DECK")
# Front (south, low) edge only.
_FRONT_PATH = (pt(ft(_deck_x_w), ft(_y_ax_arch)), pt(ft(_deck_x_e), ft(_y_ax_arch)))
BALCONY_GUTTER = Gutter(
    uid="SGGT01AAAA", tag="TR-SG-GUTTER", kind=TrimKind.GUTTER, path=_FRONT_PATH,
    top_elevation=_deck_top - inch(9), depth=inch(4), thickness=inch(5), material="aluminum",
    host_ref="TR-SG-FASCIA", slope="1/16 in/ft to SE downspout")
BALCONY_DRIP = Flashing(
    uid="SGFF01AAAA", tag="TR-SG-DRIP", kind=TrimKind.DRIP_FLASHING, path=_FRONT_PATH,
    top_elevation=_deck_top, depth=inch(3), thickness=inch(3), material="aluminum",
    host_ref="TR-SG-GUTTER")
# Rear (north, house-side) counter-flashing tucked up into the house WRB.
_REAR_PATH = (pt(ft(_deck_x_w), ft(_y_in_n)), pt(ft(_deck_x_e), ft(_y_in_n)))
BALCONY_REAR_FLASH = Flashing(
    uid="SGFF02AAAA", tag="TR-SG-WRB-FLASH", kind=TrimKind.WRB_COUNTERFLASHING,
    path=_REAR_PATH, top_elevation=_deck_top + inch(6), depth=inch(8), thickness=inch(2),
    material="aluminum", host_ref="SL-SG-DECK")

# ============================================================================
# Per-storey exports (spliced into plan/manifest.py).
# ============================================================================
BASEMENT_ELEMENTS = [*NODES, *WALLS, *RAILING_WALLS, COLUMN, *FOOTINGS,
                     *FOOTING_BEDDING, *ARCH_OPENINGS, GARDEN_SLAB, *DOWELS]
MAIN_ELEMENTS = [*MAIN_NODES, *BACK_BEAMS, PORCH_FLOOR, PORCH_JOISTS, *_BASE_CONNECTORS]
SECOND_ELEMENTS = [*SECOND_NODES, *BALCONY_BEAMS, *PILLARS, DECK_FLOOR, BALCONY_JOISTS,
                   *_TOP_CONNECTORS, BALCONY_GUARD, BALCONY_FASCIA, BALCONY_GUTTER,
                   BALCONY_DRIP, BALCONY_REAR_FLASH]
