"""The door/window *product* in a wall's opening void: frame, mullion, leaf, glazing.

Moved out of ``emit/gltf/openings.py``, which was one half of a documented cross-language
mirrored pair with ``ui/src/three/builders/walls.ts::buildOpening`` — two hand-maintained
copies of the same eleven constants, which is exactly the drift this IR exists to end. The
constants live here now; the glTF emitter re-exports them so the pair's Python side keeps its
public names. The TS copy stays — the viewer's own render path is not being retired (see
``WHOLE_HOUSE_GLB_PRIMARY``) — so `tests/test_gltf_opening_fillings.py` is what keeps the two
in step, and a change here still has to be made there.

The product is a stack of boxes laid out in the wall's own frame: a four-piece frame, then a
single panel, French leaves, slider panels, bifold leaves, or glazing. Box order is preserved
exactly as the emitter drew it, so the switch-over is a byte-for-byte diff rather than a
re-blessing.
"""

from __future__ import annotations

import math

from typehaus.model.enums import DoorOperation
from typehaus.resolve.geometry_ir import GPart, GPrism
from typehaus.resolve.geometry_walls import is_raked, wall_top_at
from typehaus.resolve.model import ResolvedWall

# --- door/window product dimensions -------------------------------------------------------
_OPENING_FRAME_FACE_WIDTH_M = 0.075          # visible face width of a jamb / head / sill piece
_OPENING_FRAME_SPAN_DIVISOR = 4.0            # ...but never more than a quarter of the opening
_OPENING_FRAME_DEPTH_M = 0.08                # frame thickness across the wall (wall-normal)
_DOOR_LEAF_THICKNESS_M = 0.045               # door panel / swing leaf slab thickness
_WINDOW_GLAZING_THICKNESS_M = 0.015          # glass pane thickness
_OPENING_MIN_PANEL_DIMENSION_M = 0.01        # a degenerate opening still ships a visible sliver
_DOUBLE_SWING_MULLION_CLEAR_WIDTH_DIVISOR = 6.0  # center mullion <= 1/6 of the clear width
_DOUBLE_SWING_LEAF_COUNT = 2
_BIFOLD_LEAF_COUNT = 4
_SLIDING_PANEL_COUNT = 2
_SLIDING_TRACK_HEIGHT_M = 0.02

_FRAME_KEY = "opening_frame"
_GLASS_KEY = "glass"


def opening_parts(wall: ResolvedWall, opening, operation: DoorOperation | None,
                  is_glazed: bool = False, is_trimless: bool = False) -> tuple[GPart, ...]:
    """Every solid the product inside ``opening`` contributes, grouped into named parts.

    A rough opening is a bare void with no product and yields nothing. A ``trimless`` door
    (drywall return jamb, no applied casing) suppresses the four frame boxes but still sizes
    its leaf as if they were there, so the reveal reads the same.
    """
    if opening.kind == "rough_opening":
        return ()
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0)
    if length < 1e-9:
        return ()
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    nx, ny = -uy, ux  # right-hand wall normal (across the wall depth)
    posx, posy = x0 + ux * opening.center_along_m, y0 + uy * opening.center_along_m
    z0, sill = wall.z0_m, opening.sill_m
    width = opening.width_m
    # A gable/ToRoof wall's top slopes, so the product is clipped by the rake over *both*
    # jambs (the lower one wins), not by the flat bounding z1 — otherwise a door under a rake
    # pokes its head through the roof plane. Unraked walls reduce to the plain wall height.
    top_at = (lambda x, y: wall_top_at(wall, x, y)) if is_raked(wall) else None
    jamb_tops = [wall.z1_m if top_at is None else top_at(posx + ux * along, posy + uy * along)
                 for along in (-width / 2.0, width / 2.0)]
    available_height = max(0.0, min(opening.height_m,
                                    *(top - z0 - sill for top in jamb_tops)))
    if available_height <= 1e-9:
        return ()
    frame_width = min(_OPENING_FRAME_FACE_WIDTH_M,
                      width / _OPENING_FRAME_SPAN_DIVISOR,
                      available_height / _OPENING_FRAME_SPAN_DIVISOR)
    depth = _OPENING_FRAME_DEPTH_M

    def box(box_w: float, box_h: float, box_t: float, along: float,
            elevation: float) -> GPrism:
        cx, cy = posx + ux * along, posy + uy * along
        hw, ht = box_w / 2.0, box_t / 2.0
        ring = (
            (cx + ux * hw + nx * ht, cy + uy * hw + ny * ht),
            (cx + ux * hw - nx * ht, cy + uy * hw - ny * ht),
            (cx - ux * hw - nx * ht, cy - uy * hw - ny * ht),
            (cx - ux * hw + nx * ht, cy - uy * hw + ny * ht),
        )
        return GPrism(ring=ring, z0_m=elevation - box_h / 2.0, z1_m=elevation + box_h / 2.0)

    parts: list[GPart] = []
    mid_elev = z0 + sill + available_height / 2.0
    if not is_trimless:
        parts.append(GPart(key="frame", material_key=_FRAME_KEY, solids=(
            box(frame_width, available_height, depth, -width / 2.0 + frame_width / 2.0, mid_elev),
            box(frame_width, available_height, depth, width / 2.0 - frame_width / 2.0, mid_elev),
            box(width, frame_width, depth, 0.0,
                z0 + sill + available_height - frame_width / 2.0),
            box(width, frame_width, depth, 0.0, z0 + sill + frame_width / 2.0),
        )))
    panel_height = max(_OPENING_MIN_PANEL_DIMENSION_M, available_height - 2.0 * frame_width)
    panel_elev = z0 + sill + frame_width + panel_height / 2.0
    clear_width = width - 2.0 * frame_width  # between the two jamb faces
    if opening.kind == "door" and operation is DoorOperation.DOUBLE_SWING:
        # Two leaves meeting at a centre mullion, matching the 2D French-door symbol.
        mullion_width = min(frame_width,
                            clear_width / _DOUBLE_SWING_MULLION_CLEAR_WIDTH_DIVISOR)
        leaf_width = max(_OPENING_MIN_PANEL_DIMENSION_M,
                         (clear_width - mullion_width) / _DOUBLE_SWING_LEAF_COUNT)
        leaf_offset = mullion_width / 2.0 + leaf_width / 2.0
        leaf_thickness = _WINDOW_GLAZING_THICKNESS_M if is_glazed else _DOOR_LEAF_THICKNESS_M
        parts.append(GPart(key="mullion", material_key=_FRAME_KEY,
                           solids=(box(mullion_width, available_height, depth, 0.0, mid_elev),)))
        parts.append(GPart(
            key="leaf", material_key=_GLASS_KEY if is_glazed else _FRAME_KEY,
            solids=(box(leaf_width, panel_height, leaf_thickness, -leaf_offset, panel_elev),
                    box(leaf_width, panel_height, leaf_thickness, leaf_offset, panel_elev)),
        ))
    elif opening.kind == "door" and operation is DoorOperation.SLIDE:
        # A closed slider stays coplanar in the product view: the two glazed panels meet at
        # a narrow stile and a low track, which distinguishes it from a French pair without
        # pretending the inactive panel is currently parked over the wall.
        stile_width = min(frame_width / 2.0, clear_width / 12.0)
        panel_width = max(_OPENING_MIN_PANEL_DIMENSION_M,
                          (clear_width - stile_width) / _SLIDING_PANEL_COUNT)
        panel_offset = stile_width / 2.0 + panel_width / 2.0
        parts.append(GPart(key="sliding_stile", material_key=_FRAME_KEY,
                           solids=(box(stile_width, panel_height, depth, 0.0, panel_elev),)))
        parts.append(GPart(key="sliding_track", material_key=_FRAME_KEY, solids=(
            box(clear_width, min(_SLIDING_TRACK_HEIGHT_M, panel_height), depth, 0.0,
                z0 + sill + frame_width + min(_SLIDING_TRACK_HEIGHT_M, panel_height) / 2.0),
        )))
        panel_thickness = (_WINDOW_GLAZING_THICKNESS_M if is_glazed
                           else _DOOR_LEAF_THICKNESS_M)
        parts.append(GPart(
            key="sliding_panel", material_key=_GLASS_KEY if is_glazed else _FRAME_KEY,
            solids=(
                box(panel_width, panel_height, panel_thickness, -panel_offset, panel_elev),
                box(panel_width, panel_height, panel_thickness, panel_offset, panel_elev),
            ),
        ))
    elif opening.kind == "door" and operation is DoorOperation.BIFOLD:
        # Four leaves are the closed, coplanar form of a centre-opening bifold pair. The
        # narrow reveals preserve each fold joint without posing the leaves open in 3D.
        fold_gap = min(frame_width / 8.0, clear_width / 40.0)
        leaf_width = max(
            _OPENING_MIN_PANEL_DIMENSION_M,
            (clear_width - fold_gap * (_BIFOLD_LEAF_COUNT - 1)) / _BIFOLD_LEAF_COUNT,
        )
        first_leaf_center = -clear_width / 2.0 + leaf_width / 2.0
        parts.append(GPart(key="bifold_leaf", material_key=_FRAME_KEY, solids=tuple(
            box(leaf_width, panel_height, _DOOR_LEAF_THICKNESS_M,
                first_leaf_center + index * (leaf_width + fold_gap), panel_elev)
            for index in range(_BIFOLD_LEAF_COUNT)
        )))
    elif opening.kind == "door" and not is_glazed:
        parts.append(GPart(key="leaf", material_key=_FRAME_KEY, solids=(
            box(max(_OPENING_MIN_PANEL_DIMENSION_M, clear_width), panel_height,
                _DOOR_LEAF_THICKNESS_M, 0.0, panel_elev),)))
    else:
        parts.append(GPart(key="glass", material_key=_GLASS_KEY, solids=(
            box(max(_OPENING_MIN_PANEL_DIMENSION_M, clear_width), panel_height,
                _WINDOW_GLAZING_THICKNESS_M, 0.0, panel_elev),)))
    return tuple(parts)
