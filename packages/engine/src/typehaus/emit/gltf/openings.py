"""The door/window *product* inside a wall's opening void: frame, panel, swing leaves, glazing.

Kept in its own module because it is one half of a cross-language mirrored pair with
ui/src/components/Panel3D.tsx ``buildOpening`` — see the constants block below.
"""

from __future__ import annotations

import math

from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _color
from typehaus.emit.gltf.walls import _wall_top_at
from typehaus.resolve.model import ResolvedWall


# --- door/window product dimensions -------------------------------------------------------
# ``_add_opening_filling`` below and ui/src/components/Panel3D.tsx ``buildOpening`` are a
# mirrored pair: the live viewer and the static .glb have to draw the same door and window or
# a user sees the model change shape when the whole-house glb becomes the primary scene. Every
# constant here has a twin literal there — change the two together.
_OPENING_FRAME_FACE_WIDTH_M = 0.075          # visible face width of a jamb / head / sill piece
_OPENING_FRAME_SPAN_DIVISOR = 4.0            # ...but never more than a quarter of the opening
_OPENING_FRAME_DEPTH_M = 0.08                # frame thickness across the wall (wall-normal)
_DOOR_LEAF_THICKNESS_M = 0.045               # door panel / swing leaf slab thickness
_WINDOW_GLAZING_THICKNESS_M = 0.015          # glass pane thickness
_OPENING_MIN_PANEL_DIMENSION_M = 0.01        # a degenerate opening still ships a visible sliver
_DOUBLE_SWING_MULLION_CLEAR_WIDTH_DIVISOR = 6.0  # center mullion ≤ 1/6 of the clear width
_DOUBLE_SWING_LEAF_COUNT = 2


def _add_opening_filling(mb: _MeshBuilder, wall: ResolvedWall, opening,
                         is_double_swing: bool) -> None:
    """Draw the door/window product itself — frame + panel/leaf/glass — as boxes.

    A straight port of ui/src/components/Panel3D.tsx ``buildOpening`` into the plan frame:
    a four-piece frame, then either a single door panel, two leaves split at a center
    mullion (``double_swing``), or a translucent glass pane (window). Rough openings are a
    bare void with no product, so they draw nothing. Emitted regardless of LOD so the leaf
    geometry shows for both the core wall prism and the framed stud model.
    """
    if opening.kind == "rough_opening":
        return
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0)
    if length < 1e-9:
        return
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    nx, ny = -uy, ux  # right-hand wall normal (across the wall depth)
    posx, posy = x0 + ux * opening.center_along_m, y0 + uy * opening.center_along_m
    z0, sill = wall.z0_m, opening.sill_m
    width = opening.width_m
    # A gable/ToRoof wall's top slopes, so the product is clipped by the rake over *both* jambs
    # (the lower one wins), not by the flat bounding z1 — otherwise a door under a rake pokes
    # its head through the roof plane. ``_wall_top_at`` returns z1_m for an unraked wall, so
    # this reduces to the plain wall height in the common case.
    jamb_tops = [_wall_top_at(wall, posx + ux * along, posy + uy * along)
                 for along in (-width / 2.0, width / 2.0)]
    available_height = max(0.0, min(opening.height_m,
                                    *(top - z0 - sill for top in jamb_tops)))
    if available_height <= 1e-9:
        return
    frame_width = min(_OPENING_FRAME_FACE_WIDTH_M,
                      width / _OPENING_FRAME_SPAN_DIVISOR,
                      available_height / _OPENING_FRAME_SPAN_DIVISOR)
    depth = _OPENING_FRAME_DEPTH_M
    frame_color = _color("opening_frame")

    def add_box(box_w: float, box_h: float, box_t: float, along: float,
                elevation: float, color) -> None:
        cx, cy = posx + ux * along, posy + uy * along
        hw, ht = box_w / 2.0, box_t / 2.0
        ring = [
            (cx + ux * hw + nx * ht, cy + uy * hw + ny * ht),
            (cx + ux * hw - nx * ht, cy + uy * hw - ny * ht),
            (cx - ux * hw - nx * ht, cy - uy * hw - ny * ht),
            (cx - ux * hw + nx * ht, cy - uy * hw + ny * ht),
        ]
        mb.add_prism(ring, elevation - box_h / 2.0, elevation + box_h / 2.0, color)

    mid_elev = z0 + sill + available_height / 2.0
    add_box(frame_width, available_height, depth, -width / 2.0 + frame_width / 2.0, mid_elev, frame_color)
    add_box(frame_width, available_height, depth, width / 2.0 - frame_width / 2.0, mid_elev, frame_color)
    add_box(width, frame_width, depth, 0.0, z0 + sill + available_height - frame_width / 2.0, frame_color)
    add_box(width, frame_width, depth, 0.0, z0 + sill + frame_width / 2.0, frame_color)
    panel_height = max(_OPENING_MIN_PANEL_DIMENSION_M, available_height - 2.0 * frame_width)
    panel_elev = z0 + sill + frame_width + panel_height / 2.0
    clear_width = width - 2.0 * frame_width  # between the two jamb faces
    if opening.kind == "door" and is_double_swing:
        # Two leaves meeting at a center mullion, matching the 2D French-door symbol.
        mullion_width = min(frame_width,
                            clear_width / _DOUBLE_SWING_MULLION_CLEAR_WIDTH_DIVISOR)
        leaf_width = max(_OPENING_MIN_PANEL_DIMENSION_M,
                         (clear_width - mullion_width) / _DOUBLE_SWING_LEAF_COUNT)
        leaf_offset = mullion_width / 2.0 + leaf_width / 2.0
        add_box(mullion_width, available_height, depth, 0.0, mid_elev, frame_color)
        add_box(leaf_width, panel_height, _DOOR_LEAF_THICKNESS_M, -leaf_offset, panel_elev,
                frame_color)
        add_box(leaf_width, panel_height, _DOOR_LEAF_THICKNESS_M, leaf_offset, panel_elev,
                frame_color)
    elif opening.kind == "door":
        add_box(max(_OPENING_MIN_PANEL_DIMENSION_M, clear_width), panel_height,
                _DOOR_LEAF_THICKNESS_M, 0.0, panel_elev, frame_color)
    else:
        add_box(max(_OPENING_MIN_PANEL_DIMENSION_M, clear_width), panel_height,
                _WINDOW_GLAZING_THICKNESS_M, 0.0, panel_elev, _color("glass"))
