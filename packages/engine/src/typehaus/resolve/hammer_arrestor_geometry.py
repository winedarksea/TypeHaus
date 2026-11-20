"""Representative in-line piston arrestor geometry for the viewer and exports."""

from dataclasses import dataclass

from shapely.geometry import MultiPoint

from typehaus.model.placeable_symbols._round_hardware import round_cylinder
from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import combine_meshes, transform_mesh
from typehaus.resolve.geometry_ir import GMesh, Vec3
from typehaus.resolve.isolation_valve_geometry import host_pipe_frame
from typehaus.resolve.model import ResolvedPipeRun, ResolvedSolid


@dataclass(frozen=True)
class ArrestorDimensions:
    # Sioux Chief 660-GT MiniRester spec sheet. Connection details below are illustrative
    # and sized around the modeled host pipe so the tee fits other nominal bores as well.
    height_in: float = 4.0
    trunk_width_in: float = 2.0
    chamber_diameter_in: float = 7 / 8
    chamber_base_in: float = 5 / 8
    neck_diameter_in: float = 5 / 8
    neck_chamber_overlap_in: float = 1 / 8
    tee_wall_in: float = 1 / 16
    collar_wall_in: float = 1 / 8
    collar_length_in: float = 3 / 8


_DIMENSIONS = ArrestorDimensions()


def _cylinder(axis: int, low: float, high: float, radius: float) -> GMesh:
    center = tuple((low + high) / 2 if index == axis else 0.0 for index in range(3))
    mesh = round_cylinder(center, radius, high - low, axis=axis)["mesh"]
    return GMesh(mesh["positions"], mesh["triangles"], mesh["normals"])


def hammer_arrestor_solid(*, uid: str, tag: str, storey: str, category: str,
                         center: Vec3, host: ResolvedPipeRun) -> ResolvedSolid | None:
    """Put the tee along the local pipe and the chamber on the frame's raised axis."""
    try:
        frame = host_pipe_frame(host, center)
    except ValueError:
        # A degenerate host has no direction. Leave its accessory visible as a marker.
        return None

    dimensions = _DIMENSIONS
    half_width = dimensions.trunk_width_in * M_PER_IN / 2
    collar_length = dimensions.collar_length_in * M_PER_IN
    pipe_radius = host.diameter_m / 2
    tee_radius = pipe_radius + dimensions.tee_wall_in * M_PER_IN
    collar_radius = pipe_radius + dimensions.collar_wall_in * M_PER_IN
    nominal_base = dimensions.chamber_base_in * M_PER_IN
    chamber_base = max(nominal_base, collar_radius)
    chamber_top = (dimensions.height_in * M_PER_IN - min(collar_radius, nominal_base)
                   + chamber_base - nominal_base)
    # The collars cover the tee ends with a short lap to avoid coincident end faces.
    tee_end = half_width - collar_length / 2
    pieces = (
        _cylinder(0, -tee_end, tee_end, tee_radius),
        _cylinder(0, -half_width, -half_width + collar_length, collar_radius),
        _cylinder(0, half_width - collar_length, half_width, collar_radius),
        _cylinder(2, 0.0, chamber_base + dimensions.neck_chamber_overlap_in * M_PER_IN,
                  dimensions.neck_diameter_in * M_PER_IN / 2),
        _cylinder(2, chamber_base, chamber_top,
                  dimensions.chamber_diameter_in * M_PER_IN / 2),
    )
    combined = combine_meshes(*pieces)
    mesh = transform_mesh(GMesh(
        combined.positions, combined.triangles,
        tuple(normal for piece in pieces for normal in piece.normals),
        curved_vertices=frozenset(range(len(combined.positions))),
    ), center, *frame)
    outline = tuple(MultiPoint([point[:2] for point in mesh.positions]).convex_hull
                    .exterior.coords)[:-1]
    elevations = [point[2] for point in mesh.positions]
    return ResolvedSolid(uid=uid, tag=tag, storey=storey, category=category, outline=outline,
                         z0_m=min(elevations), z1_m=max(elevations), body_mesh=mesh)
