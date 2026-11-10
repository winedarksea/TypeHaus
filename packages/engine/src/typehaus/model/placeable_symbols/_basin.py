"""Shared hollow rectangular vessels for plumbing symbols."""

from typehaus.model.placeable_symbols._frame import Part, box


def rectangular_basin(cx: float, cy: float, width: float, depth: float, z0: float, z1: float,
           wall_t: float, color: str) -> list[Part]:
    """A hollow vessel as four rim walls over a floor — an opaque box would read as solid."""
    wall_t = min(wall_t, width * 0.3, depth * 0.3, (z1 - z0) * 0.5)
    return [box(cx, cy, z0, z0 + wall_t, width, depth, color),
            box(cx, cy + depth / 2 - wall_t / 2, z0, z1, width, wall_t, color),
            box(cx, cy - depth / 2 + wall_t / 2, z0, z1, width, wall_t, color),
            box(cx - width / 2 + wall_t / 2, cy, z0, z1, wall_t, depth - 2 * wall_t, color),
            box(cx + width / 2 - wall_t / 2, cy, z0, z1, wall_t, depth - 2 * wall_t, color)]
