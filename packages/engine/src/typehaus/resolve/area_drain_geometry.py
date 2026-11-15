"""Hollow area-drain presentation shared by glTF and IFC.

Nominal authored envelope, not a fabrication model of NDS 1200. The 1211 grate
informs the 3/8-inch slots and 1-1/8-inch depth at a nominal 12-inch size:
https://www.ndspro.com/PDFs/Catalogs/NDS-cat-full-product-catalog-2024-2025-en.pdf
Wall thickness, slot layout and floor connection are representative. In particular,
the authored bottom drop still needs an adapter detail: stock 1200 outlets are lateral.
"""

from dataclasses import dataclass

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import combine_meshes
from typehaus.resolve.geometry import circle_outline
from typehaus.resolve.geometry_panel import panel
from typehaus.resolve.round_solids import PIPE_FACETS


@dataclass(frozen=True)
class AreaDrainVisualization:
    nominal_size_m: float = 12 * M_PER_IN
    wall_m: float = 0.1875 * M_PER_IN
    grate_depth_m: float = 1.125 * M_PER_IN
    grate_border_m: float = 0.75 * M_PER_IN
    grate_centre_bar_m: float = 0.5 * M_PER_IN
    slot_width_m: float = 0.375 * M_PER_IN
    slots_per_bank: int = 14
    nominal_riser_diameter_m: float = 4 * M_PER_IN
    riser_wall_m: float = 0.237 * M_PER_IN
    # Keep unusually shallow/small authored drains representable without inverting walls.
    maximum_wall_fraction: float = 0.1
    maximum_grate_depth_fraction: float = 0.25


VISUALIZATION = AreaDrainVisualization()


def _rectangle(x0, y0, x1, y1):
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


def basin_mesh(centre, size_m, depth_m, outlet_diameter_m, floor_m, rim_m):
    """Open grate, hollow walls and a floor bored through to the authored downpipe."""
    dimensions = VISUALIZATION
    scale = size_m / dimensions.nominal_size_m
    wall = min(dimensions.wall_m * scale, depth_m * dimensions.maximum_wall_fraction,
               (size_m - outlet_diameter_m) * dimensions.maximum_wall_fraction)
    grate_depth = min(dimensions.grate_depth_m * scale,
                      depth_m * dimensions.maximum_grate_depth_fraction)
    x, y = centre
    half = size_m / 2
    outer = _rectangle(x - half, y - half, x + half, y + half)
    inner = _rectangle(x - half + wall, y - half + wall,
                       x + half - wall, y + half - wall)
    outlet = circle_outline(centre, outlet_diameter_m / 2, PIPE_FACETS)
    border = dimensions.grate_border_m * scale
    centre_bar = dimensions.grate_centre_bar_m * scale
    slot_width = dimensions.slot_width_m * scale
    pitch = (size_m - 2 * border - slot_width) / (dimensions.slots_per_bank - 1)
    slots = []
    for index in range(dimensions.slots_per_bank):
        slot_x = x - half + border + index * pitch
        for bottom, top in ((y - half + border, y - centre_bar / 2),
                            (y + centre_bar / 2, y + half - border)):
            slots.append(_rectangle(slot_x, bottom, slot_x + slot_width, top))
    return combine_meshes(
        panel(outer, (outlet,), floor_m, floor_m + wall),
        panel(outer, (inner,), floor_m + wall, rim_m - grate_depth),
        panel(outer, slots, rim_m - grate_depth, rim_m))


def riser_geometry(centre, diameter_m, bottom_m, top_m):
    """Round open tube; nominal outlet diameter is retained as the outside envelope."""
    wall = (diameter_m * VISUALIZATION.riser_wall_m
            / VISUALIZATION.nominal_riser_diameter_m)
    outer = circle_outline(centre, diameter_m / 2, PIPE_FACETS)
    inner = circle_outline(centre, diameter_m / 2 - wall, PIPE_FACETS)
    return outer, panel(outer, (inner,), bottom_m, top_m)
