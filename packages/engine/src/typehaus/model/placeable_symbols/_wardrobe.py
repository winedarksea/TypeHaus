"""PAX interiors, corner set, sliding pair and closet boards for browser and glTF consumers.

Heights are representative layouts, not a KOMPLEMENT drilling schedule. They are inches
above the frame's bottom and scale with the frame's height.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.model.placeable_symbols._families import Builder, Geometry, shelving
from typehaus.model.placeable_symbols._frame import (
    DETAIL_WEIGHT,
    Part,
    Point,
    box,
    line,
    polygon,
    rect,
)

FRAME_HEIGHT_INCHES = 92.875
PANEL_THICKNESS_M = 0.01905
BACK_THICKNESS_M = 0.003175
DRAWER_REVEAL_M = 0.003175
ROD_RADIUS_M = 0.016669
ROD_CROSS_SECTION_BANDS = 16
WOOD = "wood"
WHITE = "appliance-white"
PAX_DEPTH_M = 0.581025  # 22 7/8"
PAX_FRAME_WIDTH_M = 1.000125  # 39 3/8"
DOOR_THICKNESS_M = 0.0191
SLIDER_PANEL_THICKNESS_M = 0.022225  # 7/8"
SLIDER_RAIL_HEIGHT_M = 0.0254


@dataclass(frozen=True)
class WardrobeInterior:
    drawer_bottom_inches: float
    drawer_top_inches: float
    drawer_count: int
    glass_drawer_indices: tuple[int, ...]
    shelf_heights_inches: tuple[float, ...]
    rod_heights_inches: tuple[float, ...] = ()


SHOW_INTERIOR = WardrobeInterior(2, 44, 5, (3, 4), (46, 66, 80))
# Dress length: ~61" clear under the rod, three shelves above it. No drawers.
DRESS_INTERIOR = WardrobeInterior(0, 0, 0, (), (64, 73.5, 83), rod_heights_inches=(61.5,))
# Double hang on the custom bay's rod lines (79"/39" off the floor), one shelf on top.
DOUBLE_HANG_INTERIOR = WardrobeInterior(0, 0, 0, (), (81.5,),
                                        rod_heights_inches=(38.75, 78.75))
# Six shelves, evenly pitched: the doorless 19 5/8" unit and the 39 3/8" behind sliders.
SHELVES_INTERIOR = WardrobeInterior(0, 0, 0, (), (13.25, 26.5, 39.75, 53, 66.25, 79.5))
# The add-on corner unit's four shelves.
CORNER_UNIT_INTERIOR = WardrobeInterior(0, 0, 0, (), (18.5, 37, 55.5, 74))


def closet_board(width: float, depth: float, height: float) -> Geometry:
    """Keep the valance/plinth massing box but match the wardrobe's wood palette role."""
    return (rect(0, 0, width, depth),), (box(0, 0, 0, height, width, depth, WOOD),)


def wardrobe(interior: WardrobeInterior) -> Builder:
    """Wood-colored open carcass with separate drawer boxes, fronts, shelves, and rods."""

    def build(width: float, depth: float, height: float) -> Geometry:
        panel = min(PANEL_THICKNESS_M, width * 0.04, depth * 0.08, height * 0.008)
        back = min(BACK_THICKNESS_M, depth * 0.01, panel)
        reveal = min(DRAWER_REVEAL_M, height * 0.001)
        opening_width = width - 2 * panel
        shelf_depth = depth - back
        front_y = -depth / 2
        back_y = depth / 2

        def elevation(inches: float) -> float:
            return height * inches / FRAME_HEIGHT_INCHES

        # Keep the existing bookcase plan glyph: its outline describes the same footprint.
        strokes = shelving()(width, depth, 1.0)[0]
        parts = [
            box(-width / 2 + panel / 2, 0, 0, height, panel, depth, WOOD),
            box(width / 2 - panel / 2, 0, 0, height, panel, depth, WOOD),
            box(0, back_y - back / 2, 0, height, opening_width, back, WOOD),
            box(0, -back / 2, 0, panel, opening_width, shelf_depth, WOOD),
            box(0, -back / 2, height - panel, height, opening_width, shelf_depth, WOOD),
        ]
        for shelf_height in interior.shelf_heights_inches:
            z = elevation(shelf_height)
            parts.append(box(0, -back / 2, z, z + panel,
                             opening_width, shelf_depth, WOOD))

        drawer_pitch = elevation(interior.drawer_top_inches - interior.drawer_bottom_inches)
        drawer_pitch /= max(interior.drawer_count, 1)
        drawer_width = opening_width - 2 * reveal
        drawer_depth = shelf_depth - 2 * panel
        drawer_center_y = front_y + panel + drawer_depth / 2
        for index in range(interior.drawer_count):
            z0 = elevation(interior.drawer_bottom_inches) + index * drawer_pitch + reveal
            z1 = z0 + drawer_pitch - 2 * reveal
            # A hollow drawer is essential behind a glass front: a solid box masks the glass.
            parts.extend([
                box(0, drawer_center_y, z0, z0 + panel,
                    drawer_width, drawer_depth, WOOD),
                box(-drawer_width / 2 + panel / 2, drawer_center_y, z0, z1,
                    panel, drawer_depth, WOOD),
                box(drawer_width / 2 - panel / 2, drawer_center_y, z0, z1,
                    panel, drawer_depth, WOOD),
                box(0, drawer_center_y + drawer_depth / 2 - panel / 2, z0, z1,
                    drawer_width, panel, WOOD),
            ])
            face_y = front_y + panel / 2
            if index in interior.glass_drawer_indices:
                parts.extend([
                    box(0, face_y, z0, z0 + panel, drawer_width, panel, WOOD),
                    box(0, face_y, z1 - panel, z1, drawer_width, panel, WOOD),
                    box(-drawer_width / 2 + panel / 2, face_y, z0 + panel, z1 - panel,
                        panel, panel, WOOD),
                    box(drawer_width / 2 - panel / 2, face_y, z0 + panel, z1 - panel,
                        panel, panel, WOOD),
                    box(0, face_y, z0 + panel, z1 - panel,
                        drawer_width - 2 * panel, back, "glass"),
                ])
            else:
                parts.append(box(0, face_y, z0, z1, drawer_width, panel, WOOD))

        radius = min(ROD_RADIUS_M, depth * 0.03, height * 0.008)
        for rod_height in interior.rod_heights_inches:
            rod_z = elevation(rod_height)
            # Width-axis cylinders are represented by narrow bands of ordinary boxes so
            # every existing consumer can render the round profile without a new primitive.
            for band in range(ROD_CROSS_SECTION_BANDS):
                lower = -radius + 2 * radius * band / ROD_CROSS_SECTION_BANDS
                upper = lower + 2 * radius / ROD_CROSS_SECTION_BANDS
                half_depth = math.sqrt(radius**2 - ((lower + upper) / 2)**2)
                parts.append(box(0, 0, rod_z + lower, rod_z + upper,
                                 opening_width, 2 * half_depth, "metal"))
        return strokes, tuple(parts)

    return build


def wardrobe_corner_points(width: float, depth: float,
                           leg: float = PAX_DEPTH_M) -> tuple[Point, ...]:
    """The L ring the corner glyph draws and its catalog ``footprint_shape`` states.

    The frame runs along the back (+y); the corner unit returns down the -x end, its back
    on the corner wall. The notch at +x/-y is the floor both doors open into.
    """
    hw, hd = width / 2, depth / 2
    leg = min(leg, width, depth)
    return ((-hw, -hd), (-hw + leg, -hd), (-hw + leg, hd - leg), (hw, hd - leg),
            (hw, hd), (-hw, hd))


def _moved(part: Part, dx: float, dy: float, quarter_turn: bool = False) -> Part:
    """A part shifted in plan, optionally turned +90 deg about the origin first."""
    (cx, cy, cz), (sx, sy, sz) = part["center"], part["size"]
    if quarter_turn:
        cx, cy, sx, sy = -cy, cx, sy, sx
    return {**part, "center": (cx + dx, cy + dy, cz), "size": (sx, sy, sz)}


def wardrobe_corner(width: float, depth: float, height: float) -> Geometry:
    """PAX/GRIMO corner set: a frame on the back wall, an add-on corner unit returning down
    the -x wall, one white door on each inner face of the L.

    The frame stands off the corner wall by whatever the run leaves over (4" at 43 3/8"); the
    corner unit reaches behind it. Doors sit inside the ring, so the carcass is a door
    thickness shallower than the leg.
    """
    hw, hd = width / 2, depth / 2
    leg = min(PAX_DEPTH_M, width * 0.75, depth * 0.75)
    carcass = leg - DOOR_THICKNESS_M
    frame_w = min(PAX_FRAME_WIDTH_M, width - leg)
    frame = wardrobe(DOUBLE_HANG_INTERIOR)(frame_w, carcass, height)[1]
    unit_w = depth - leg
    unit = wardrobe(CORNER_UNIT_INTERIOR)(unit_w, carcass, height)[1]
    parts = [_moved(p, hw - frame_w / 2, hd - carcass / 2) for p in frame]
    parts += [_moved(p, -hw + carcass / 2, -hd + unit_w / 2, quarter_turn=True)
              for p in unit]
    inner_x, inner_y = -hw + leg, hd - leg
    door_t = DOOR_THICKNESS_M
    parts.append(box((inner_x + hw) / 2, inner_y + door_t / 2, 0, height,
                     hw - inner_x, door_t, WHITE))
    parts.append(box(inner_x - door_t / 2, (inner_y - hd) / 2, 0, height,
                     door_t, inner_y + hd, WHITE))
    strokes = (polygon(wardrobe_corner_points(width, depth, leg), fill="wood"),
               line((inner_x, inner_y + door_t), (hw, inner_y + door_t)),
               line((inner_x - door_t, -hd), (inner_x - door_t, inner_y)),
               line((-hw, hd), (inner_x, inner_y), weight=DETAIL_WEIGHT))
    return strokes, tuple(parts)


def wardrobe_sliding_pair(width: float, depth: float, height: float) -> Geometry:
    """PAX sliding-door frame with two panels on two tracks: mirror on the +x half in the
    front track, white on the -x half behind it. +x is the viewer's right from the room."""
    rail = min(SLIDER_RAIL_HEIGHT_M, height * 0.05)
    panel_t = min(SLIDER_PANEL_THICKNESS_M, depth * 0.45)
    front_y, back_y = -depth / 4, depth / 4
    half = width / 2
    parts = [box(0, 0, 0, rail, width, depth, "metal"),
             box(0, 0, height - rail, height, width, depth, "metal"),
             box(half / 2, front_y, rail, height - rail, half, panel_t, "mirror"),
             box(-half / 2, back_y, rail, height - rail, half, panel_t, WHITE)]
    for x0, x1, cy in ((0.0, half, front_y), (-half, 0.0, back_y)):  # the panels' stiles
        for stile_x in (x0 + rail / 4, x1 - rail / 4):
            parts.append(box(stile_x, cy, rail, height - rail, rail / 2, panel_t * 1.1,
                             "metal"))
    strokes = (rect(0, 0, width, depth, weight=DETAIL_WEIGHT),
               rect(half / 2, front_y, half, panel_t, fill="mirror"),
               rect(-half / 2, back_y, half, panel_t, fill=WHITE))
    return strokes, tuple(parts)
