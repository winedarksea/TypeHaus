"""Leviton 5980-UCL envelope with a shallow GFCI behind a clear closed hood.

Overall dimensions follow the 5980 drawing; shell thickness and adapter relief are
schematic. Local +Y is the mounting plane, matching the other wiring-device symbols.
"""

from dataclasses import dataclass

from typehaus.model.placeable_symbols._frame import box, rect
from typehaus.model.placeable_symbols.receptacles import _face


@dataclass(frozen=True)
class InUseCoverGeometryConfig:
    width_in: float = 3.63
    depth_in: float = 3.08
    height_in: float = 6.69
    shell_thickness_in: float = 0.08
    adapter_depth_in: float = 0.25
    face_width_in: float = 1.29
    face_height_in: float = 2.70
    face_projection_20a_in: float = 0.10
    face_projection_15a_in: float = 0.03


IN_USE_COVER_GEOMETRY = InUseCoverGeometryConfig()


def gfci_in_use_cover(width, depth, height, *, amperage=20):
    cfg = IN_USE_COVER_GEOMETRY
    # Uniform scaling preserves the device proportions even in registry size sweeps.
    unit = min(width / cfg.width_in, depth / cfg.depth_in, height / cfg.height_in)
    thickness = cfg.shell_thickness_in * unit
    adapter_depth = cfg.adapter_depth_in * unit
    back = depth / 2
    adapter_front = back - adapter_depth
    hood_front = -depth / 2
    hood_depth = adapter_front - hood_front
    parts = [box(0, back - adapter_depth / 2, 0, height, width, adapter_depth, "device-face")]
    face_depth = (cfg.face_projection_20a_in if amperage == 20
                  else cfg.face_projection_15a_in) * unit
    face_height = cfg.face_height_in * unit
    _, face_parts = _face(cfg.face_width_in * unit, face_depth, face_height,
                          (("120-20", "120-20") if amperage == 20 else ("120", "120"),),
                          band="gfci")
    offset_y = adapter_front - face_depth / 2
    offset_z = (height - face_height) / 2
    for part in face_parts:
        x, y, z = part["center"]
        shifted = {**part, "center": (x, y + offset_y, z + offset_z)}
        if "mesh" in part:
            shifted["mesh"] = {**part["mesh"], "positions": tuple(
                (x, y + offset_y, z + offset_z) for x, y, z in part["mesh"]["positions"])}
        parts.append(shifted)
    # Separate thin panels leave the sockets visible through an empty plug cavity.
    parts.append(box(0, hood_front + thickness / 2, 0, height, width, thickness,
                     "clear-glass"))
    for x in (-(width - thickness) / 2, (width - thickness) / 2):
        parts.append(box(x, (hood_front + adapter_front) / 2, 0, height,
                         thickness, hood_depth, "clear-glass"))
    for z in (0, height - thickness):
        parts.append(box(0, (hood_front + adapter_front) / 2, z, z + thickness,
                         width - 2 * thickness, hood_depth, "clear-glass"))
    return (rect(0, 0, width, depth),), tuple(parts)


def gfci_in_use_cover_15a(width, depth, height):
    return gfci_in_use_cover(width, depth, height, amperage=15)
