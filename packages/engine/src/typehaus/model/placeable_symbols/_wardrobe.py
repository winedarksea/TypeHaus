"""Open PAX interiors and matching closet boards shared by browser and glTF consumers.

Heights are representative layouts, not a KOMPLEMENT drilling schedule. They are inches
above the frame's bottom and scale with the frame's height.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.model.placeable_symbols._families import Builder, Geometry, shelving
from typehaus.model.placeable_symbols._frame import box, rect

FRAME_HEIGHT_INCHES = 92.875
PANEL_THICKNESS_M = 0.01905
BACK_THICKNESS_M = 0.003175
DRAWER_REVEAL_M = 0.003175
ROD_RADIUS_M = 0.016669
ROD_CROSS_SECTION_BANDS = 16
WOOD = "wood"


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
