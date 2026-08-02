"""2D detail components — the drawn context a junction needs but the model does not carry.

A grade line, a soil hatch, a box gutter, a flashing profile and a sill gasket are drawing
conventions, not building elements: Revit calls them detail components and they live in the
view, not the model. TypeHaus derives them the way it derives joint treatments — from the
live cut and the resolved planes around it — so they track a geometry edit instead of
freezing authored coordinates.

They are emitted as ordinary ``Polyline``/``Hatch`` nodes carrying a
``detail-component:<name>`` tag, deliberately **not** as new ``Symbol`` names: the writers
already render polylines and hatches correctly and keep them hit-testable, whereas an unknown
``Symbol`` degrades to a bare circle in ``DetailCanvas.tsx`` and to a marker in
``pdf_writer.py``.

Module map — one junction (or one concern) per file:

* ``config``      — every dimension, named and traced to the reference param that fixes it.
* ``geometry``    — shared emitters and the resolvers that read the live cut.
* ``dispatch``    — ``Transition.overlay`` recipe id → vocabulary. The wiring point.
* ``below_grade`` — grade line, soil body, perimeter drain.
* ``eave``        — box gutter, drip edge, apron, screened vent path.
* ``wall_base``   — flashings, sill gasket, slab thermal break, foam protection.
* ``stack``       — rim-band air seal, stepped-wall shelf flashing.
* ``opening``     — head flashing, sill pan, concrete bucks, sauna liner returns.
* ``ridge``       — the LVL ridge's face-mount hanger vocabulary.
* ``sauna``       — liner base plus the room-scale fit-out.
* ``shower``      — recess, tile over backer, glass panel, HRV takeoff.
* ``breezeway``   — the glazing enclosure: drainage wedges, weeping channels, glazing
                    bar, gasketed fastener, breather tape.
* ``chrome``      — material legend and derived dimension strings.

Section coordinates throughout: ``u`` is the in-section axis, ``z`` is world z, both in model
inches at the point these nodes are built (the cutter's convention).
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.below_grade import (
    build_below_grade_components,
    faces_soil,
    french_drain,
    grade_line,
    soil_body,
)
from typehaus.emit.draw.detail_components.breezeway import (
    breather_tape,
    breezeway_components,
    breezeway_overlay_for_slice,
    crown_glazing_bar,
    drainage_wedges,
    gasketed_fastener,
    shared_h_channel,
    weeping_u_channel,
)
from typehaus.emit.draw.detail_components.chrome import dimension_strings, material_legend
from typehaus.emit.draw.detail_components.config import (
    BASEMENT_TO_FRAMED_WALL,
    BREEZEWAY_GLAZING,
    FOUNDATION_FACE,
    INTERIOR_SLAB_DRIP,
    LAYER,
    M_TO_IN,
    OPENING_DETAIL,
    PERIMETER_DRAIN,
    RIDGE_HANGER,
    RIM_BAND,
    SAUNA_BASEBOARD_IN,
    SAUNA_BENCH_DEPTH_IN,
    SAUNA_BENCH_LOWER_TOP_IN,
    SAUNA_BENCH_THK_IN,
    SAUNA_BENCH_UPPER_TOP_IN,
    SAUNA_FLASH_IN,
    SAUNA_HEATER_H_IN,
    SAUNA_HEATER_W_IN,
    SAUNA_MEMBRANE_IN,
    SHEET_METAL,
    SHOWER_BACKER_IN,
    SHOWER_GLASS_GAP_IN,
    SHOWER_GLASS_IN,
    SHOWER_HRV_DUCT_IN,
    SHOWER_RECESS_IN,
    SHOWER_TILE_IN,
    SLAB_EDGE,
    STACK_WIDTH_SHELF,
)
from typehaus.emit.draw.detail_components.dispatch import (
    OVERLAY_RECIPES,
    UNDRAWN_RECIPES,
    build_overlay_components,
)
from typehaus.emit.draw.detail_components.eave import (
    box_gutter,
    eave_vent_screen,
    zero_overhang_eave,
)
from typehaus.emit.draw.detail_components.geometry import (
    condition_opening,
    condition_walls,
    flashing_nodes,
    path_from_steps,
    thicken_polyline,
)
from typehaus.emit.draw.detail_components.opening import (
    concrete_opening_bucks,
    sauna_liner_opening_return,
    window_head_jamb_sill,
)
from typehaus.emit.draw.detail_components.ridge import (
    lvl_ridge_hanger,
    ridge_overlay_for_slice,
)
from typehaus.emit.draw.detail_components.sauna import (
    build_sauna_room_components,
    sauna_benches,
    sauna_components,
    sauna_drop_ceiling,
    sauna_floor_slope,
    sauna_heater_clearance,
    sauna_liner_base,
    sauna_overlay_for_slice,
)
from typehaus.emit.draw.detail_components.shower import (
    shower_components,
    shower_glass,
    shower_hrv_duct,
    shower_overlay_for_slice,
    shower_recess,
    shower_wall_lining,
)
from typehaus.emit.draw.detail_components.stack import (
    rim_band_air_seal,
    stack_width_shelf,
)
from typehaus.emit.draw.detail_components.wall_base import (
    basement_framed_wall,
    foam_protection_board,
    interior_slab_drip_flashing,
    slab_is_on_grade,
    slab_thermal_break,
)

__all__ = [
    "BASEMENT_TO_FRAMED_WALL",
    "BREEZEWAY_GLAZING",
    "FOUNDATION_FACE",
    "INTERIOR_SLAB_DRIP",
    "LAYER",
    "M_TO_IN",
    "OPENING_DETAIL",
    "OVERLAY_RECIPES",
    "PERIMETER_DRAIN",
    "RIDGE_HANGER",
    "RIM_BAND",
    "SAUNA_BASEBOARD_IN",
    "SAUNA_BENCH_DEPTH_IN",
    "SAUNA_BENCH_LOWER_TOP_IN",
    "SAUNA_BENCH_THK_IN",
    "SAUNA_BENCH_UPPER_TOP_IN",
    "SAUNA_FLASH_IN",
    "SAUNA_HEATER_H_IN",
    "SAUNA_HEATER_W_IN",
    "SAUNA_MEMBRANE_IN",
    "SHEET_METAL",
    "SHOWER_BACKER_IN",
    "SHOWER_GLASS_GAP_IN",
    "SHOWER_GLASS_IN",
    "SHOWER_HRV_DUCT_IN",
    "SHOWER_RECESS_IN",
    "SHOWER_TILE_IN",
    "SLAB_EDGE",
    "STACK_WIDTH_SHELF",
    "UNDRAWN_RECIPES",
    "basement_framed_wall",
    "box_gutter",
    "breather_tape",
    "breezeway_components",
    "breezeway_overlay_for_slice",
    "crown_glazing_bar",
    "drainage_wedges",
    "gasketed_fastener",
    "shared_h_channel",
    "weeping_u_channel",
    "build_below_grade_components",
    "build_overlay_components",
    "build_sauna_room_components",
    "concrete_opening_bucks",
    "condition_opening",
    "condition_walls",
    "dimension_strings",
    "eave_vent_screen",
    "faces_soil",
    "flashing_nodes",
    "foam_protection_board",
    "french_drain",
    "grade_line",
    "interior_slab_drip_flashing",
    "lvl_ridge_hanger",
    "material_legend",
    "path_from_steps",
    "ridge_overlay_for_slice",
    "rim_band_air_seal",
    "sauna_benches",
    "sauna_components",
    "sauna_drop_ceiling",
    "sauna_floor_slope",
    "sauna_heater_clearance",
    "sauna_liner_base",
    "sauna_liner_opening_return",
    "sauna_overlay_for_slice",
    "shower_components",
    "shower_glass",
    "shower_hrv_duct",
    "shower_overlay_for_slice",
    "shower_recess",
    "shower_wall_lining",
    "slab_is_on_grade",
    "slab_thermal_break",
    "soil_body",
    "stack_width_shelf",
    "thicken_polyline",
    "window_head_jamb_sill",
    "zero_overhang_eave",
]
