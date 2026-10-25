"""Thin steel skins and a continuous isolation layer on the exposed wood trim faces."""
from dataclasses import replace


def wrapped_installation_boards(placement):
    specification = placement.specification
    sign = placement.outward_sign
    boards = list(placement.boards)
    for board in placement.boards:
        if not board.name.startswith("exterior-"):
            continue
        for material, thickness, offset, role in (
            (specification.wrap_isolation_material_ref,
             specification.wrap_isolation_thickness.meters, 0, "door_trim_isolation"),
            (specification.exterior_wrap_material_ref,
             specification.exterior_wrap_thickness.meters,
             specification.wrap_isolation_thickness.meters, "door_trim_wrap"),
        ):
            distance = offset + thickness / 2
            skin = replace(board, name=f"{board.name}-{role}", material_ref=material,
                           role=role, material_key="window_trim")
            if "casing" in board.name:
                skin = replace(skin, depth_m=thickness,
                    normal_m=board.normal_m + sign * (board.depth_m / 2 + distance))
            elif "jamb" in board.name:
                toward_opening = -1 if board.along_m > 0 else 1
                skin = replace(skin, width_m=thickness,
                    along_m=board.along_m + toward_opening * (board.width_m / 2 + distance))
            else:
                skin = replace(skin, height_m=thickness,
                    z_m=board.z_m - board.height_m / 2 - distance)
            boards.append(skin)
            if "casing-jamb" in board.name:
                outward_along = 1 if board.along_m > 0 else -1
                boards.append(replace(skin, name=f"{skin.name}-outer-edge",
                    width_m=thickness, depth_m=board.depth_m,
                    normal_m=board.normal_m,
                    along_m=board.along_m + outward_along * (board.width_m / 2 + distance)))
    return tuple(boards)
