"""Door product finish colors, sharing the catalog palette with millwork."""
from typehaus.library.wood_appearance import NATURAL_WOOD_COLORS


def door_part_color(part, authored, *, linear_paint_defaults=False):
    from typehaus.emit.gltf.palette import _color, _material_finish_color

    ref = part.catalog.material_ref if part.catalog else None
    if not ref:
        color = _color(part.material_key)
        if not linear_paint_defaults or part.material_key not in ("door_frame", "door_leaf"):
            return color
        # The generated viewer vocabulary encodes this palette as 8-bit display RGB.
        color = (*(round(channel * 255) / 255 for channel in color[:3]), color[3])
    else:
        color = _material_finish_color(ref, "millwork", authored)
    material = authored.get(ref) if authored else None
    # Existing wood colors are already linear. Other catalog colors still use the legacy
    # sRGB path elsewhere; convert here without recoloring unrelated building surfaces.
    if material is not None and getattr(material, "species", None) in NATURAL_WOOD_COLORS:
        return color
    def linear(channel):
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
    return (*map(linear, color[:3]), color[3])


def door_part_surface(part):
    if part.material_key == "door_hardware":
        return (0.35, 0.8)
    if part.material_key in ("door_frame", "door_leaf") or part.catalog:
        return (0.45, 0.0)
    return (0.9, 0.0)
