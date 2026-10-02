"""Generated geometry for the closet's SEKTION / MAXIMERA drawer base."""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import Builder, Geometry
from typehaus.model.placeable_symbols._frame import DETAIL_WEIGHT, box, line, rect
from typehaus.quantities import inch

# Published product dimensions and the closet's countertop spec. The top's front oversail is
# part of the furniture footprint; its carcass depth remains the IKEA cabinet's 15 1/2".
SEKTION_LEG_HEIGHT_M = inch(4.5).meters
SEKTION_LEG_WIDTH_M = inch(1.5).meters
SEKTION_LEG_EDGE_INSET_M = inch(1).meters
SEKTION_COUNTERTOP_THICKNESS_M = inch(1.181).meters
SEKTION_COUNTERTOP_FRONT_OVERSAIL_M = inch(1).meters
SEKTION_DRAWER_COUNT = 3
SEKTION_DRAWER_REVEAL_M = inch(0.125).meters
SEKTION_DRAWER_FRAME_BORDER_M = inch(0.75).meters
SEKTION_DRAWER_FRONT_DEPTH_M = inch(0.75).meters
SEKTION_DRAWER_PANEL_RECESS_M = inch(0.125).meters
SEKTION_DRAWER_PULL_WIDTH_M = inch(6).meters
SEKTION_DRAWER_PULL_HEIGHT_M = inch(0.25).meters
SEKTION_DRAWER_PULL_PROJECTION_M = inch(0.25).meters
SEKTION_DRAWER_PULL_MOUNT_SPACING_M = inch(5).meters
SEKTION_DRAWER_PULL_END_MARGIN_M = inch(0.5).meters
SEKTION_DRAWER_PULL_MOUNT_SIZE_M = inch(0.125).meters
SEKTION_REVEAL_BACKING_DEPTH_M = inch(0.08).meters


def sektion_drawer_base() -> Builder:
    """Draw a three-front SEKTION base on four legs with its shared quartz surface.

    The frame fronts use a shallow inset to suggest the selected ASPUDDEN thin-frame face.
    Handles are generic bar pulls because the IKEA set requires them but no SKU was chosen.
    """

    def build(width: float, depth: float, height: float) -> Geometry:
        front_oversail = min(SEKTION_COUNTERTOP_FRONT_OVERSAIL_M, depth * 0.12)
        carcass_depth = max(depth - front_oversail, depth * 0.5)
        carcass_center_y = front_oversail / 2
        carcass_front_y = carcass_center_y - carcass_depth / 2
        carcass_back_y = carcass_center_y + carcass_depth / 2

        leg_height = min(SEKTION_LEG_HEIGHT_M, height * 0.18)
        countertop_thickness = min(SEKTION_COUNTERTOP_THICKNESS_M, height * 0.1)
        frame_top = height - countertop_thickness
        frame_height = frame_top - leg_height
        leg_width = min(SEKTION_LEG_WIDTH_M, width * 0.16, carcass_depth * 0.16)
        leg_depth = leg_width
        leg_inset = min(SEKTION_LEG_EDGE_INSET_M, min(width, carcass_depth) * 0.1)
        foot_cap_height = min(inch(0.25).meters, leg_height * 0.15)

        drawer_reveal = min(SEKTION_DRAWER_REVEAL_M, frame_height * 0.025)
        face_side_margin = min(inch(0.1875).meters, width * 0.04)
        face_width = width - 2 * face_side_margin
        drawer_front_height = (
            frame_height - (SEKTION_DRAWER_COUNT + 1) * drawer_reveal
        ) / SEKTION_DRAWER_COUNT
        drawer_front_depth = min(SEKTION_DRAWER_FRONT_DEPTH_M, carcass_depth * 0.12)
        drawer_front_y = carcass_front_y - drawer_front_depth / 2
        frame_border = min(SEKTION_DRAWER_FRAME_BORDER_M,
                           face_width * 0.12, drawer_front_height * 0.18)
        inset_panel_depth = max(drawer_front_depth - SEKTION_DRAWER_PANEL_RECESS_M,
                                drawer_front_depth * 0.7)
        reveal_backing_depth = min(SEKTION_REVEAL_BACKING_DEPTH_M,
                                   carcass_depth * 0.02)
        reveal_backing_y = carcass_front_y - reveal_backing_depth / 2

        strokes = [
            rect(0, 0, width, depth, fill="counter"),
            line((-width / 2, carcass_front_y), (width / 2, carcass_front_y),
                 weight=DETAIL_WEIGHT),
        ]
        parts = [
            # The 3 cm slab aligns with the cabinet back and projects 1" past its fronts.
            box(0, 0, frame_top, height, width, depth, "counter"),
            box(0, carcass_center_y, leg_height, frame_top, width, carcass_depth,
                "appliance-white"),
            # This set-back face shows as a fine contact shadow in the 1/8" drawer reveals.
            # It sits ahead of the carcass front, behind all three removable fronts.
            box(0, reveal_backing_y, leg_height + drawer_reveal,
                frame_top - drawer_reveal, face_width, reveal_backing_depth,
                "casework-shadow"),
        ]

        leg_x = width / 2 - leg_inset - leg_width / 2
        front_leg_y = carcass_front_y + leg_inset + leg_depth / 2
        back_leg_y = carcass_back_y - leg_inset - leg_depth / 2
        foot_cap_width = min(leg_width * 1.15, width / 2 - leg_inset)
        foot_cap_depth = min(leg_depth * 1.15, carcass_depth / 2 - leg_inset)
        for x_sign in (-1, 1):
            for foot_y in (front_leg_y, back_leg_y):
                foot_x = x_sign * leg_x
                parts.append(box(foot_x, foot_y, 0, foot_cap_height,
                                 foot_cap_width, foot_cap_depth, "metal"))
                parts.append(box(foot_x, foot_y, foot_cap_height, leg_height,
                                 leg_width, leg_depth, "appliance-white"))

        for drawer_index in range(SEKTION_DRAWER_COUNT):
            front_z0 = leg_height + drawer_reveal + drawer_index * (
                drawer_front_height + drawer_reveal)
            front_z1 = front_z0 + drawer_front_height
            # Four raised rails and a recessed center form the ASPUDDEN thin frame.
            side_rail_x = face_width / 2 - frame_border / 2
            for x_sign in (-1, 1):
                parts.append(box(x_sign * side_rail_x, drawer_front_y, front_z0, front_z1,
                                 frame_border, drawer_front_depth, "appliance-white"))
            parts.append(box(0, drawer_front_y, front_z0,
                             front_z0 + frame_border, face_width, drawer_front_depth,
                             "appliance-white"))
            parts.append(box(0, drawer_front_y, front_z1 - frame_border, front_z1,
                             face_width, drawer_front_depth, "appliance-white"))
            panel_width = face_width - 2 * frame_border
            parts.append(box(0, carcass_front_y - inset_panel_depth / 2,
                             front_z0 + frame_border, front_z1 - frame_border,
                             panel_width, inset_panel_depth, "porcelain"))

            pull_width = min(SEKTION_DRAWER_PULL_WIDTH_M, face_width * 0.45)
            pull_height = min(SEKTION_DRAWER_PULL_HEIGHT_M, drawer_front_height * 0.12)
            pull_depth = min(SEKTION_DRAWER_PULL_PROJECTION_M,
                             max(0.001, front_oversail - inset_panel_depth))
            pull_z = (front_z0 + front_z1) / 2
            panel_front_y = carcass_front_y - inset_panel_depth
            mount_spacing = min(SEKTION_DRAWER_PULL_MOUNT_SPACING_M,
                                max(0.0, pull_width - 2 * SEKTION_DRAWER_PULL_END_MARGIN_M))
            mount_size = min(SEKTION_DRAWER_PULL_MOUNT_SIZE_M,
                             pull_height * 0.75, pull_depth * 0.5)
            pull_bar_depth = pull_depth - mount_size
            mount_y = panel_front_y - mount_size / 2
            pull_y = panel_front_y - mount_size - pull_bar_depth / 2
            for x_sign in (-1, 1):
                parts.append(box(x_sign * mount_spacing / 2, mount_y,
                                 pull_z - mount_size / 2, pull_z + mount_size / 2,
                                 mount_size, mount_size, "metal"))
            parts.append(box(0, pull_y, pull_z - pull_height / 2,
                             pull_z + pull_height / 2, pull_width, pull_bar_depth,
                             "metal"))

        return tuple(strokes), tuple(parts)

    return build
