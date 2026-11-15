"""Hollow sump basin and bolted cover in the shared viewer/IFC geometry.

Wall, lid and fastener sizes are representative visualization dimensions, not a
manufacturer's basin specification. The authored diameter remains the clear inside size.
"""

from dataclasses import dataclass, replace
from math import cos, pi, sin

from shapely.geometry import Polygon

from typehaus.model.mep import Sump
from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import combine_meshes
from typehaus.resolve.geometry import circle_outline
from typehaus.resolve.geometry_panel import panel
from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.solid_categories import in_slab_family


@dataclass(frozen=True)
class SumpVisualization:
    wall_m: float = 0.1875 * M_PER_IN
    bottom_m: float = 0.25 * M_PER_IN
    cover_m: float = 0.25 * M_PER_IN
    gasket_m: float = 0.0625 * M_PER_IN
    bolt_radius_m: float = 0.1875 * M_PER_IN
    bolt_height_m: float = 0.125 * M_PER_IN
    bolt_recess_m: float = 0.03125 * M_PER_IN
    bolt_clearance_m: float = 0.0625 * M_PER_IN
    bolt_inset_m: float = 0.5 * M_PER_IN
    bolt_count: int = 6
    penetration_clearance_m: float = 0.0625 * M_PER_IN
    facets: int = 64
    bolt_facets: int = 6


VISUALIZATION = SumpVisualization()


def cover_penetrations(model, storey_tag, cover_z_m, inside):
    """Locate actual pipe crossings; a nearby pipe above the lid makes no hole."""
    holes = []
    for run in model.pipe_runs:
        if run.storey != storey_tag or run.system not in {"radon", "sump_discharge"}:
            continue
        if run.z_m is None:
            continue
        for index, (a, b) in enumerate(zip(run.path[:-1], run.path[1:], strict=True)):
            za, zb = run.z_m[index:index + 2]
            if za == zb or not min(za, zb) <= cover_z_m <= max(za, zb):
                continue
            fraction = (cover_z_m - za) / (zb - za)
            centre = tuple(a[i] + fraction * (b[i] - a[i]) for i in range(2))
            radius = run.diameter_m / 2 + VISUALIZATION.penetration_clearance_m
            ring = circle_outline(centre, radius, VISUALIZATION.facets)
            # No invented notch where a route misses the basin or clips its rim.
            if inside.contains(Polygon(ring)) and ring not in holes:
                holes.append(ring)
    return holes


def resolve_sump(model: ResolvedModel, sump: Sump, storey) -> None:
    dimensions = VISUALIZATION
    host_index = next((i for i, solid in enumerate(model.solids)
                       if solid.tag == sump.host_ref and in_slab_family(solid.category)), None)
    host = model.solids[host_index] if host_index is not None else None
    rim_z = host.z1_m if host is not None else storey.elevation.meters
    bottom_z = (host.z0_m if host is not None else rim_z) - sump.depth.meters
    centre = sump.position.xy_m
    radius = sump.diameter.meters / 2
    outer = tuple(circle_outline(centre, radius + dimensions.wall_m, dimensions.facets))
    inner = tuple(circle_outline(centre, radius, dimensions.facets))
    # A flush cover preserves the floor's working-space datum beside electrical equipment.
    cover_top = rim_z
    cover_bottom = cover_top - dimensions.cover_m
    gasket_bottom = cover_bottom - (dimensions.gasket_m if sump.sealed_cover else 0)
    # One selectable/billable basin; disconnected fastener meshes do not create extra pits.
    meshes = [panel(outer, (), bottom_z, bottom_z + dimensions.bottom_m),
              panel(outer, (inner,), bottom_z + dimensions.bottom_m, gasket_bottom)]
    if sump.sealed_cover:
        meshes.append(panel(outer, (inner,), gasket_bottom, cover_bottom))
    holes = cover_penetrations(model, storey.tag, rim_z, Polygon(inner))
    bolt_pockets = []
    bolt_bottom = cover_top - dimensions.bolt_recess_m - dimensions.bolt_height_m
    for index in range(dimensions.bolt_count):
        angle = 2 * pi * index / dimensions.bolt_count
        bolt_radius = radius - dimensions.bolt_inset_m
        bolt_centre = (centre[0] + bolt_radius * cos(angle),
                       centre[1] + bolt_radius * sin(angle))
        outline = circle_outline(bolt_centre, dimensions.bolt_radius_m, dimensions.bolt_facets)
        pocket = circle_outline(bolt_centre, dimensions.bolt_radius_m
                                + dimensions.bolt_clearance_m, dimensions.facets)
        if any(Polygon(pocket).intersects(Polygon(hole)) for hole in holes):
            continue
        bolt_pockets.append(pocket)
        meshes.append(panel(outline, (), bolt_bottom, cover_top - dimensions.bolt_recess_m))
    meshes.extend((panel(outer, holes, cover_bottom, bolt_bottom),
                   panel(outer, (*holes, *bolt_pockets), bolt_bottom, cover_top)))
    mesh = combine_meshes(*meshes)
    model.solids.append(ResolvedSolid(
        uid=sump.uid or f"{sump.tag}-sump", tag=sump.tag, storey=storey.tag,
        category="sump", outline=outer, z0_m=bottom_z,
        z1_m=max(point[2] for point in mesh.positions), material="polyethylene",
        body_mesh=mesh))
    if host is not None:
        model.solids[host_index] = replace(host, voids=(*host.voids, outer))
