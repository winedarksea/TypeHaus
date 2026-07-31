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
  PT 2x12 back beams hung into the side walls; column and beam line sit a SPEC south-offset
  inside the edge (so the tube and its bell footing clear the house), and the deck edge
  cantilevers over them. PT 2x8 joists span N-S from the front-wall sill to the back
  beams; composite decking is the walking surface. Porch floor = main (0').
- A masonry "railing" (white brick / air gap / grouted CMU / stucco) rides the front + side
  walls as the porch guard; its grouted CMU cores receive the balcony post bases.
- The *balcony* one storey up (second, ~9-10') rides six 6x6 pillars (10' o.c. E-W, 8'
  o.c. N-S; rear row 2" taller for drainage slope) carrying three N-S double-2x10 beams,
  2x8 joists @ 16" o.c., and aluminum (Wahoo AridDeck-style) decking.

Everything here is generated — these elements carry no editable-source location. The porch
floor is a FloorSystem outright (FS-SG-PORCH: joists, and the composite plank as its deck
sheet) — it used to be a Slab standing in for the framing beside it, which meant two
elements claiming one floor. The balcony's aluminum boards are still a walking-surface Slab
over FS-SG-DECK.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus import (
    Arch,
    Beam,
    Connector,
    ConnectorKind,
    DeckLayer,
    Dowel,
    Fascia,
    Flashing,
    FloorSystem,
    Footing,
    FootingBedding,
    FoundationWall,
    Gutter,
    JoistSpec,
    KneeBrace,
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

from typehaus.resolve.framing.profiles import cross_section

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
    # Sonotube centre set south of the deck's north-edge line. Centred *on* that line the
    # 12" tube pokes 6" north — through the 5" insulation gap and into the house cladding —
    # and its 30" bell footing reaches 15" toward the house footing.
    #
    # The offset cannot shrink: the *house* footing FT-B-S2 is what the bell runs into, and
    # its south face already lands on the north-edge line (the 20"-wide strip footing under
    # the y=0 basement wall reaches y = -10" = -0'-10", which is exactly this structure's
    # north edge). The bell's north face therefore has to stop 2" short of that line to
    # leave room for the 40 psi XPS thermal-break block the dowels cross — 15" put the two
    # footings in hard contact with the foam nowhere to go. 15 + 2 = 17".
    column_south_offset_in: float = 17.0
    porch_joist: str = "2x8"
    porch_joist_oc_in: float = 16.0
    # Two-ply treated LVL, 11 1/4" deep so the depth constant below and every elevation
    # derived from it are unchanged from the 2-2x12 this replaced (2026-07-31). The sawn
    # built-up beam was 1'-9" past IRC Table R507.5(1)'s 8'-3" limit on this 10'-0" span at
    # the 8' joist-span row; the fix is the member, not the geometry, because the column and
    # the two side-wall hangers are the only bearings this line can have. Being engineered it
    # leaves the prescriptive table's scope, so `structural.deck_beam_span` now reports it
    # UNKNOWN rather than PASS — the manufacturer's span table is the authority instead.
    # (A 3-ply sawn 2x12 would also have cleared it, at 10'-3", and would have stayed
    # checkable; the engineered member was the decision.)
    back_beam: str = "2-1.75x11.25 LVL"
    porch_deck_thickness_in: float = 1.0  # composite plank
    # The porch's two joist ends are not alike, so it cannot share the balcony's symmetric
    # cantilever: the south end bears on the arched front wall's sill (flush — nothing may
    # oversail 16" of concrete) and the north end runs the column's south-offset out to the
    # deck edge. This is the *south* value; the north one is that offset (see PORCH_JOISTS).
    porch_joist_cantilever_in: float = 0.0
    # balcony framing
    pillar_size: str = "6x6"
    rear_pillar_rise_in: float = 2.0  # rear row taller for drainage slope
    # Three N-S beams over the pillar lines. Two-ply treated LVL at the 2x10's own 9 1/4"
    # depth (2026-07-31), so `_balcony_beam_depth_ft` and the soffit plane it sets are
    # unchanged. The 2-2x10 was nearly 3'-0" past R507.5(1)'s 5'-9" on this 8'-8" span: the
    # balcony's joists span 10'-6", which reads the table's 12' row, and no built-up sawn
    # size in that table reaches 8'-8" there (3-2x12, the largest row, stops at 8'-4"). So
    # unlike the porch this line had no prescriptive answer at all short of re-framing.
    balcony_beam: str = "2-1.75x9.25 LVL"
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
_y_in_n = _y_out_n  # porch deck north edge (back beams + column sit a SPEC offset south)
_y_in_arch = _y_in_n - SPEC.porch_clear_depth_ft  # north (inner) face of the 16" front wall
# The 16" front wall is a 12.5" arch/pier section plus a 3.5" joist-bearing ledge on its
# north face. A PT 2x4 sill lies flat on that ledge (top at the joist soffit, -7.25"), a PT
# 2x8 rim stands on the plate's south 1.5" (south face -9.125', north face -9.0'), and the
# joists butt that rim bearing 2" on the plate. So the porch *floor system* runs to the
# ledge's south edge and nothing overhangs the wall's north 3.5" — see PORCH_JOISTS.
_ledge_ft = 3.5 / 12.0
_y_porch_s = _y_in_arch - _ledge_ft  # -9.125' — floor-system south edge
_y_ax_arch = _y_in_arch - _arch_half  # front-wall axis (arch nodes + arch railing + front pillars)
_y_in_s = _y_in_n - SPEC.clear_length_ft
_y_ax_s = _y_in_s - _half

_wall_bottom = ft(-(SPEC.basement_depth_ft + 0.75))
_porch_top = ft(SPEC.porch_top_ft)  # storey datum = top of joist; the masonry bears here
_ret_top = ft(SPEC.retaining_top_ft)
# The guard's 42" is measured from the surface underfoot — the composite boards over the
# porch joists — while the masonry itself still bears on the structure below them. Topping
# out at porch_top + 42" would leave only 41" of guard above the deck.
_railing_top = (ft(SPEC.porch_top_ft + SPEC.railing_height_ft)
                + inch(SPEC.porch_deck_thickness_in))
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

# --- public geometry for structures that build on this one ------------------------------
# The raised garden bears on the south retaining wall's top, so it needs that wall's axis,
# span and section. Publish them rather than let a second module re-derive the same
# arithmetic off SPEC — two derivations silently diverge the next time a dimension moves.
SOUTH_RETAINING_WALL_TAG = "W-SG-S"
SOUTH_RETAINING_WALL_AXIS_Y_FT = _y_ax_s
SOUTH_RETAINING_WALL_NODES = ("N-SG-SW", "N-SG-SE")
RETAINING_WALL_SPAN_X_FT = (_x_ax_w, _x_ax_e)
RETAINING_WALL_TOP_FT = SPEC.retaining_top_ft
RETAINING_WALL_THICKNESS_IN = SPEC.wall_thickness_in
# The arched front wall's axis — the plane W-SG-RAIL-F and RL-SG-BALCONY both sit on, and
# the north limit anything wrapping this structure runs up to. Published for the raised
# garden's legs, which stop here rather than continuing past the balcony.
ARCH_WALL_AXIS_Y_FT = _y_ax_arch

# Sonotube column (12" round) at midspan, a SPEC south-offset inside the porch rather than
# on the deck's north-edge line (see ``column_south_offset_in`` — on the line, the tube and
# its bell footing both poked north into the house). The whole back-beam line re-anchors to
# the same offset — nodes, hangers, and tie all at ``_y_col`` — so the two beams stay
# collinear and the deck's north edge cantilevers over them to the house gap.
# Its top lands on the 2x12 back-beam soffit (one beam depth below the 0' porch deck), so
# the beams seat directly on the column and it reads "slightly shorter than the arched
# front wall". Base at the column footing top (basement elevation, -9').
_back_beam_depth_ft = 11.25 / 12.0  # 2x12 actual depth
_y_col = _y_in_n - SPEC.column_south_offset_in / 12.0
_col_footing_width_in = 30.0  # spread footing (bell) under the sonotube
COLUMN = Post(uid="SGP001AAAA", tag="PT-SG-COL",
              position=pt(ft(_cx), ft(_y_col)), size="12 round",
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
            width=inch(_col_footing_width_in), depth=inch(12))
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
# The back-beam line rides at the column's south-offset (``_y_col``), not on the deck's
# north-edge line: the beams stay collinear through the column and the deck edge
# cantilevers the offset over them toward the house gap.
MAIN_NODES = [
    Node(uid="SGNM01AAAA", tag="N-SGM-NW", position=pt(ft(_x_ax_w), ft(_y_col)),
         open_end=True),
    Node(uid="SGNM02AAAA", tag="N-SGM-NE", position=pt(ft(_x_ax_e), ft(_y_col)),
         open_end=True),
    Node(uid="SGNM03AAAA", tag="N-SGM-COL", position=pt(ft(_cx), ft(_y_col))),
]

# Two PT 2x12 back beams: sonotube column -> side-wall hangers (two ~9'6" spans).
BACK_BEAMS = [
    Beam(uid="SGBM01AAAA", tag="BM-SG-BKW", start_node="N-SGM-COL", end_node="N-SGM-NW",
         size=SPEC.back_beam, bearing_refs=("PT-SG-COL", "W-SG-W1")),
    Beam(uid="SGBM02AAAA", tag="BM-SG-BKE", start_node="N-SGM-COL", end_node="N-SGM-NE",
         size=SPEC.back_beam, bearing_refs=("PT-SG-COL", "W-SG-E1")),
]

# The porch floor's footprint. It used to be authored on a ``SL-SG-PORCH`` Slab that stood
# in for the framing (a "walking_surface" slab of composite plank) while FS-SG-PORCH drew
# the joists under it — two elements claiming one floor, and the slab was the one every
# consumer reached for. The floor system is the floor now; the outline lives here so the
# joists, the pillar bearings and anything else that wants the porch's extent share one.
_PORCH_OUTLINE = (pt(ft(_x_in_w), ft(_y_porch_s)), pt(ft(_x_in_e), ft(_y_porch_s)),
                  pt(ft(_x_in_e), ft(_y_in_n)), pt(ft(_x_in_w), ft(_y_in_n)))

# ============================================================================
# Second (balcony, ~10'): 6x6 pillars, three 2x10 beams, aluminum deck.
# ============================================================================
# Six pillars: front (south) row on the arch railing, rear (north) row — outer two on the
# side-wall railings, center on the porch decking. The five that land on masonry are
# *embedded in the CMU*: an ABU66SS standoff base is anchored into the grouted cores, so the
# exposed 6x6 starts at the top of the railing wall, not 42" lower at the porch deck. Their
# authored height is therefore measured from the railing top. The rear-center pillar is the
# one exception — the north edge is open (no railing wall), so it still stands off the
# composite decking over FS-SG-PORCH, and is that much taller.
# The rear (north, house-side) row is 2" taller so the deck crowns at the rear and drains
# south, away from the house.  Beam soffit = balcony level less the 2x10 beam depth (9.25").
_balcony_beam_depth_ft = 9.25 / 12.0
_balcony_joist_depth_ft = 7.25 / 12.0  # 2x8 deck joist
# Pillar-height *input* only. The resolver drops both the beam and the post carrying it by
# the deck joist depth (resolve/envelope.py::_bearing_stack_drops), so the wood does not
# land here — see _balcony_beam_soffit below for where it actually ends up. Subtracting the
# joist depth here as well would double-count it and shorten every pillar by 7.25".
_beam_soffit = ft(SPEC.balcony_level_ft - _balcony_beam_depth_ft)
# The *resolved* soffit: the pillar-top plane the beams and E-W girts sit on, and the
# plane both brace families rise to.
_balcony_beam_soffit = ft(SPEC.balcony_level_ft - _balcony_joist_depth_ft
                          - _balcony_beam_depth_ft)  # 8.625'
_girt_depth_ft = 9.25 / 12.0  # 2x10 — same depth as the double-2x10 beams, so tops finish flush
# The girts ride ON the pillar tops now (not bolted to the faces a girt-depth lower), so
# their soffit IS the resolved pillar-top / beam-soffit plane and the E-W knee braces land
# at the same soffit the N-S braces do.
_girt_soffit = _balcony_beam_soffit  # 8.625'
_girt_top = _balcony_beam_soffit + ft(_girt_depth_ft)  # 9.396' — flush with the beam tops
# Top of the composite boards laid over FS-SG-PORCH: the joist tops are the 0' storey
# datum, and the plank sits on them. (The boards were the deleted SL-SG-PORCH slab; the
# surface they make is still real and still what a person stands on.)
_porch_walking_surface = inch(SPEC.porch_deck_thickness_in)
_PILLAR_X = (_x_ax_w, _cx, _x_ax_e)
# (row, x index) -> the railing wall whose grouted cores hold that pillar's base.
_RAILING_UNDER_PILLAR = {
    ("R", 1): "W-SG-RAIL-W", ("R", 3): "W-SG-RAIL-E",
    ("F", 1): "W-SG-RAIL-F", ("F", 2): "W-SG-RAIL-F", ("F", 3): "W-SG-RAIL-F",
}
_PILLAR_ROWS = (("R", _y_in_n, inch(SPEC.rear_pillar_rise_in)), ("F", _y_ax_arch, ft(0)))
PILLARS = []
PILLAR_BEARINGS = {}  # pillar tag -> (bearing tag, base elevation) — reused by the bases
for _i, _x in enumerate(_PILLAR_X, start=1):
    for _row_index, (_row, _y, _rise) in enumerate(_PILLAR_ROWS):
        _railing = _RAILING_UNDER_PILLAR.get((_row, _i))
        _base = _railing_top if _railing is not None else _porch_walking_surface
        _tag = f"PT-SG-B{_row}{_i}"
        PILLAR_BEARINGS[_tag] = (_railing or "FS-SG-PORCH", _base)
        PILLARS.append(Post(uid=f"SGPB{_i}{_row_index}AAAA", tag=_tag,
                            position=pt(ft(_x), ft(_y)), size=SPEC.pillar_size,
                            height=_beam_soffit - _base + _rise,
                            supported_by=_railing or "FS-SG-PORCH",
                            assembly="POST_WHITE_PAINT"))

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

# E-W girts, one pair of segments per pillar row, up ON the pillar tops in the same
# horizontal band as the N-S beams (soffit at the resolved pillar-top plane, tops flush
# with the beam tops one joist depth under the deck datum). They carry no joists — the deck
# spans E-W onto the beams beside them — and exist so the balcony has a load path in its
# second principal direction at all. Without an E-W member at the pillar tops there is
# nothing for an E-W knee brace to reach, and a freestanding deck on standoff post bases
# (pinned top and bottom) has no other lateral resistance that way.
#
# A girt sharing the beams' band cannot run the full 20' — it would pass *through* the
# three N-S beams — so each row is two segments meeting the beams cleanly:
# - Front row: segment ends at the beam faces. The end laps onto the pillar-top strip
#   beside the N-S beam and butts the beam side.
# - Rear row: the rear pillars run 2" proud of the shared soffit (the drainage rise), so
#   the segments stop at the pillar faces (±2.75") and butt that proud pillar top instead;
#   the rest of the way back to the beam face is the hanger's saddle at each end.
#
# The front-row half-width is read off ``SPEC.balcony_beam`` rather than written down.
# It was the literal 1.5" that suited the old 3"-wide double-2x10, and the 2026-07-31 swap
# to a 3 1/2"-wide two-ply LVL drove the girts 1/4" into every beam they butt —
# `structural.member_interference` caught it, which is the number's whole job.
_beam_face_ft = cross_section(SPEC.balcony_beam).width_m / 2 / 0.3048
_pillar_face_ft = 2.75 / 12.0  # half the 5.5" actual 6x6
GIRT_NODES = [
    Node(uid="SGNG01AAAA", tag="N-SGG-RW1", position=pt(ft(_x_ax_w + _pillar_face_ft), ft(_y_in_n))),
    Node(uid="SGNG02AAAA", tag="N-SGG-RW2", position=pt(ft(_cx - _pillar_face_ft), ft(_y_in_n))),
    Node(uid="SGNG03AAAA", tag="N-SGG-RE1", position=pt(ft(_cx + _pillar_face_ft), ft(_y_in_n))),
    Node(uid="SGNG04AAAA", tag="N-SGG-RE2", position=pt(ft(_x_ax_e - _pillar_face_ft), ft(_y_in_n))),
    Node(uid="SGNG05AAAA", tag="N-SGG-FW1", position=pt(ft(_x_ax_w + _beam_face_ft), ft(_y_ax_arch))),
    Node(uid="SGNG06AAAA", tag="N-SGG-FW2", position=pt(ft(_cx - _beam_face_ft), ft(_y_ax_arch))),
    Node(uid="SGNG07AAAA", tag="N-SGG-FE1", position=pt(ft(_cx + _beam_face_ft), ft(_y_ax_arch))),
    Node(uid="SGNG08AAAA", tag="N-SGG-FE2", position=pt(ft(_x_ax_e - _beam_face_ft), ft(_y_ax_arch))),
]
BALCONY_GIRTS = [
    Beam(uid="SGBG01AAAA", tag="BM-SG-GIRT-RW", start_node="N-SGG-RW1", end_node="N-SGG-RW2",
         size="2x10", top_elevation=_girt_top,
         bearing_refs=("PT-SG-BR1", "PT-SG-BR2")),
    Beam(uid="SGBG03AAAA", tag="BM-SG-GIRT-RE", start_node="N-SGG-RE1", end_node="N-SGG-RE2",
         size="2x10", top_elevation=_girt_top,
         bearing_refs=("PT-SG-BR2", "PT-SG-BR3")),
    Beam(uid="SGBG02AAAA", tag="BM-SG-GIRT-FW", start_node="N-SGG-FW1", end_node="N-SGG-FW2",
         size="2x10", top_elevation=_girt_top,
         bearing_refs=("PT-SG-BF1", "PT-SG-BF2")),
    Beam(uid="SGBG04AAAA", tag="BM-SG-GIRT-FE", start_node="N-SGG-FE1", end_node="N-SGG-FE2",
         size="2x10", top_elevation=_girt_top,
         bearing_refs=("PT-SG-BF2", "PT-SG-BF3")),
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
    datum="walking_surface",  # boards laid over FS-SG-DECK, not the structure itself
)

# --- joist framing under the two decks (rendered members beneath the surface slabs) ---
# Porch: PT 2x8 @ 16" o.c. running N-S from the arched front-wall sill to the two back
# beams on the sonotube column.
PORCH_JOISTS = FloorSystem(
    uid="SGFS01AAAA", tag="FS-SG-PORCH",
    joists=JoistSpec(member=SPEC.porch_joist, spacing=inch(SPEC.porch_joist_oc_in),
                     direction="y",
                     # South (start) end: flush at the front wall — the sill/rim detail on
                     # the 3.5" ledge is the bearing, and a cantilever here would push
                     # joist tips out over 16" of concrete. North (end): the joists run the
                     # column's south-offset past the back-beam line to the deck edge, which
                     # is the porch's real overhang. One symmetric value cannot say both.
                     cantilever=inch(SPEC.porch_joist_cantilever_in),
                     cantilever_end=inch(SPEC.column_south_offset_in),
                     bearing_refs=("W-SG-ARCH", "BM-SG-BKW", "BM-SG-BKE")),
    outline=_PORCH_OUTLINE,
    # The composite plank *is* this deck's sheet: with SL-SG-PORCH gone the boards are the
    # floor system's own surface layer, which is both what a person stands on (the balcony
    # pillar that misses the masonry railing bears here) and what the sheet-goods take-off
    # bills. This is the deleted slab's one-inch PORCH_DECK_COMPOSITE layer, in place.
    subfloor=DeckLayer(material_ref="composite-deck",
                       thickness=inch(SPEC.porch_deck_thickness_in)),
    # ``service="deck"`` is what puts this under IRC R507 / AWC DCA6 instead of the interior
    # 40-psf floor table — see checks/structural/deck.py.
    service="deck",
    source="porch floor — PT 2x8 joists, front sill -> back beams",
)

# Balcony: 2x8 @ 16" o.c. running E-W across the three N-S double-2x10 beams.
BALCONY_JOISTS = FloorSystem(
    uid="SGFS02AAAA", tag="FS-SG-DECK",
    joists=JoistSpec(member=SPEC.balcony_joist, spacing=inch(SPEC.balcony_joist_oc_in),
                     direction="x", cantilever=inch(SPEC.joist_cantilever_in),
                     bearing_refs=("BM-SG-BLW", "BM-SG-BLC", "BM-SG-BLE")),
    outline=DECK_FLOOR.outline,
    # ``service="deck"`` is what puts this under IRC R507 / AWC DCA6 instead of the interior
    # 40-psf floor table — see checks/structural/deck.py.
    service="deck",
    source="balcony — 2x8 joists on three double-2x10 beams",
)

# ============================================================================
# Fiberglass (GFRP) rebar dowels + 40 psi XPS foam thermal break between the shared
# house/garden footings. The three house-adjacent footings (two porch side walls + the
# sonotube column, along the north edge) pin to the house footing across a 2" XPS block so
# the joint transfers shear without a thermal bridge. Bars at mid-footing (-9.25').
# ============================================================================
_dowel_z = ft(-(SPEC.basement_depth_ft + 0.75) + SPEC.footing_thickness_in / 24.0)  # -9.25'
# The side-wall dowels sit on the north-edge line; the column's follow the column to its
# bell footing's *north face* — the plane that actually abuts the house footing now that
# the column stands a south-offset inside the porch. FT-B-S2's south face sits *on* the
# north-edge line, so at the 17" offset the bell's north face lands 2" south of it and the
# bars cross exactly the 2" XPS block — which is the joint this detail is about. (At the
# old 15" the two footings met with nowhere to put the foam.)
_col_joint_y = _y_col + _col_footing_width_in / 24.0
_DOWEL_AT = (("W1", _x_ax_w, _y_in_n), ("E1", _x_ax_e, _y_in_n), ("COL", _cx, _col_joint_y))
DOWELS = [
    Dowel(uid=f"SGDW0{i}AAAA", tag=f"DW-SG-{name}", position=pt(ft(x), ft(y)),
          axis="y", length=inch(24), diameter=inch(0.625), elevation=_dowel_z,
          count=3, spacing=inch(8),
          connects=(f"FT-SG-{name}", "FT-B-S2"),
          foam_thickness=inch(2), foam_height=inch(SPEC.footing_thickness_in), foam_psi=40.0)
    for i, (name, x, y) in enumerate(_DOWEL_AT, start=1)
]

# ============================================================================
# Connector hardware as modeled geometry (was text/notes only). Standoff post bases under
# the six 6x6 balcony pillars, plus joist hangers / hurricane ties at the porch back-beam
# pockets. The knee braces are their own elements — see KNEE_BRACES below.
# ============================================================================
CONNECTORS = []
for _i, _x in enumerate(_PILLAR_X, start=1):
    for _row, _y, _rise in _PILLAR_ROWS:
        # ABU66SS: the stainless ABU66 standoff base, set into the grouted CMU core of the
        # railing the pillar is embedded in. It rides at that pillar's own bearing top, so
        # the base draws where the post actually starts rather than down at the deck.
        _bearing_tag, _bearing_top = PILLAR_BEARINGS[f"PT-SG-B{_row}{_i}"]
        CONNECTORS.append(Connector(
            uid=f"SGCB{_i}{_row}AAAA", tag=f"CN-SG-BASE-{_row}{_i}",
            kind=ConnectorKind.POST_BASE, position=pt(ft(_x), ft(_y)), elevation=_bearing_top,
            size="ABU66SS", connects=(f"PT-SG-B{_row}{_i}", _bearing_tag)))
# Porch back-beam pockets: joist hanger into the side wall + hurricane tie over the column.
CONNECTORS += [
    Connector(uid="SGCH01AAAA", tag="CN-SG-HGR-W", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_w), ft(_y_col)), elevation=_porch_top, size="LUS210",
              connects=("BM-SG-BKW", "W-SG-W1")),
    Connector(uid="SGCH02AAAA", tag="CN-SG-HGR-E", kind=ConnectorKind.JOIST_HANGER,
              position=pt(ft(_x_ax_e), ft(_y_col)), elevation=_porch_top, size="LUS210",
              connects=("BM-SG-BKE", "W-SG-E1")),
    Connector(uid="SGCT01AAAA", tag="CN-SG-TIE-COL", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(_cx), ft(_y_col)), elevation=_porch_top, size="H2.5A",
              connects=("BM-SG-BKW", "BM-SG-BKE", "PT-SG-COL")),
]

# ============================================================================
# Knee braces at the balcony pillar tops: 2x6 wood diagonals with a 3' leg, through-bolted,
# with a Simpson Outdoor Accents APVKB45-6 at each joint.
#
# The four *corner* pillars are braced in both plan directions; the two centre pillars
# (PT-SG-BR2 / PT-SG-BF2) are deliberately left as leaning columns. Reasoning:
# - This is a freestanding deck with no ledger into the house, on ABU66SS standoff bases.
#   Both the base and the beam bearing are pins, so every bit of lateral resistance the
#   balcony has comes from these braces. It needs them in *both* principal directions, which
#   is why the E-W girts exist for the "x" braces to reach.
# - Bracing both ends of the outer bays in each direction is enough with the deck acting as
#   a diaphragm; the centre pillars then just carry gravity. Bracing them too would push
#   thrust into PT-SG-BR2, which is the one pillar bearing on the porch decking rather than
#   on grouted masonry — the worst place in the frame to load laterally.
# - One brace per element. Each pillar is a beam *end*, so only one brace fits in the beam's
#   own plane; the second brace at a corner is the E-W one, against the girt segment in its
#   row — now at the same soffit as the beams, since the girts ride the pillar tops. The
#   old "matched pair per joint" rule billed 12 braces that could not be built.
# ============================================================================
# (row, pillar index, N-S lean, E-W lean). Rear posts brace south toward the beam's midspan
# and front posts brace north; the west pillar of each row braces east, the east one west.
_BRACED_CORNERS = (("R", 1, -1, +1), ("R", 3, -1, -1),
                   ("F", 1, +1, +1), ("F", 3, +1, -1))
_BRACE_LEG = ft(3.0)
# The N-S brace uid is the one the retired Connector carried at this same pillar, so the
# brace keeps its IFC GlobalId across this change.
_NS_BRACE_UID = {("R", 1): "SGCK1RAAAA", ("R", 3): "SGCK3RAAAA",
                 ("F", 1): "SGCK1FAAAA", ("F", 3): "SGCK3FAAAA"}
_EW_BRACE_UID = {("R", 1): "SGKX1RAAAA", ("R", 3): "SGKX3RAAAA",
                 ("F", 1): "SGKX1FAAAA", ("F", 3): "SGKX3FAAAA"}
_ROW_Y = {"R": _y_in_n, "F": _y_ax_arch}
_NS_BEAM = {1: "BM-SG-BLW", 3: "BM-SG-BLE"}
# The west pillar of each row braces east into its row's west girt segment; the east
# pillar braces west into the east segment.
_EW_GIRT = {("R", 1): "BM-SG-GIRT-RW", ("R", 3): "BM-SG-GIRT-RE",
            ("F", 1): "BM-SG-GIRT-FW", ("F", 3): "BM-SG-GIRT-FE"}
KNEE_BRACES = []
for _row, _i, _ns, _ew in _BRACED_CORNERS:
    _post = f"PT-SG-B{_row}{_i}"
    _at = pt(ft(_PILLAR_X[_i - 1]), ft(_ROW_Y[_row]))
    KNEE_BRACES.append(KneeBrace(
        uid=_NS_BRACE_UID[(_row, _i)], tag=f"KB-SG-{_row}{_i}-NS", position=_at,
        soffit_elevation=_balcony_beam_soffit, leg=_BRACE_LEG, axis="y", direction=_ns,
        member="2x6", post_size=SPEC.pillar_size, assembly="POST_WHITE_PAINT",
        connects=(_post, _NS_BEAM[_i])))
    KNEE_BRACES.append(KneeBrace(
        uid=_EW_BRACE_UID[(_row, _i)], tag=f"KB-SG-{_row}{_i}-EW", position=_at,
        soffit_elevation=_girt_soffit, leg=_BRACE_LEG, axis="x", direction=_ew,
        member="2x6", post_size=SPEC.pillar_size, assembly="POST_WHITE_PAINT",
        connects=(_post, _EW_GIRT[(_row, _i)])))

# ============================================================================
# Balcony guard + edge trim. The metal fascia-mounted guardrail is a first-class Railing
# (not a parapet). PVC fascia closes the joist ends; a front gutter catches the south-
# draining deck via a front-edge drip flashing; the rear (house) edge gets a counter-
# flashing tucked up into the house WRB. Deck drains SOUTH (rear pillars 2" taller).
# ============================================================================
_deck_top = ft(SPEC.balcony_level_ft)  # 10' — storey datum = top of joist
# Guard height is measured from the surface a person stands on, which is the top of the
# aluminum boards, not the joists they sit on. Basing the guard on _deck_top instead would
# make the authored 42" measure 40.5" in the field and fail the guard-height rule.
_deck_walking_surface = _deck_top + inch(SPEC.balcony_deck_thickness_in)
# Guard the three open edges (west, front/south, east); the north edge abuts the house.
_GUARD_PATH = (pt(ft(_deck_x_w), ft(_y_in_n)), pt(ft(_deck_x_w), ft(_y_ax_arch)),
               pt(ft(_deck_x_e), ft(_y_ax_arch)), pt(ft(_deck_x_e), ft(_y_in_n)))
BALCONY_GUARD = Railing(
    uid="SGRA01AAAA", tag="RL-SG-BALCONY", type_ref="RAILING-EXT-ALUMINUM-FASCIA",
    path=_GUARD_PATH,
    kind=RailingKind.METAL_FASCIA_MOUNT, height=ft(3.5),
    base_elevation=_deck_walking_surface,
    post_spacing=inch(60), post_size="2x2", rail_count=2, mount="fascia",
    assembly="POST_WHITE_PAINT")

BALCONY_FASCIA = Fascia(
    uid="SGFC01AAAA", tag="TR-SG-FASCIA", kind=TrimKind.FASCIA, path=_GUARD_PATH,
    top_elevation=_deck_top, depth=inch(9), thickness=inch(1), material="PVC",
    host_ref="SL-SG-DECK")
# Front (south, low) edge only.
_FRONT_PATH = (pt(ft(_deck_x_w), ft(_y_ax_arch)), pt(ft(_deck_x_e), ft(_y_ax_arch)))
# The gutter's rim meets the drip flashing's lower edge (drip top = deck top, its depth
# below that), so water shedding off the drip lands straight in the trough. Hung 9" down
# it cleared the drip by 6" and the sheet overshot the trough entirely.
_drip_depth_in = 3.0
BALCONY_GUTTER = Gutter(
    uid="SGGT01AAAA", tag="TR-SG-GUTTER", kind=TrimKind.GUTTER, path=_FRONT_PATH,
    top_elevation=_deck_top - inch(_drip_depth_in), depth=inch(4), thickness=inch(5),
    material="aluminum", host_ref="TR-SG-FASCIA", slope="1/16 in/ft to SE downspout",
    # The run goes west→east, so its left-hand normal (resolve/geometry.py::normal) points
    # north (+y) — the porch/house side. The channel's back sheet rides the fascia there.
    back_side="left")
BALCONY_DRIP = Flashing(
    uid="SGFF01AAAA", tag="TR-SG-DRIP", kind=TrimKind.DRIP_FLASHING, path=_FRONT_PATH,
    top_elevation=_deck_top, depth=inch(_drip_depth_in), thickness=inch(3),
    material="aluminum", host_ref="TR-SG-GUTTER")
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
# Every remaining connector is porch hardware at the deck (post bases, hangers, the column
# tie), so main takes them whole; the knee braces are the only second-storey hardware.
MAIN_ELEMENTS = [*MAIN_NODES, *BACK_BEAMS, PORCH_JOISTS, *CONNECTORS]
SECOND_ELEMENTS = [*SECOND_NODES, *GIRT_NODES, *BALCONY_BEAMS, *BALCONY_GIRTS, *PILLARS, DECK_FLOOR,
                   BALCONY_JOISTS, *KNEE_BRACES, BALCONY_GUARD, BALCONY_FASCIA,
                   BALCONY_GUTTER, BALCONY_DRIP, BALCONY_REAR_FLASH]
