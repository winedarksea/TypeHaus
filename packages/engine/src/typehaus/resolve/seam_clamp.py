"""Open-throat S-5-N bodies shared by roof attachments and ColorGard."""

import math

from typehaus.hardware import snow_retention as dimensions
from typehaus.resolve.geometry_ir import GBox, GMesh
from typehaus.resolve.geometry_slice_box import outward_box_mesh
from typehaus.resolve.roof_geometry import roof_plane_z, roof_slope_coordinate


def clamp_body_boxes(station, seam_top, length=dimensions.CLAMP_LENGTH_IN):
    """Inches in the (across seam, downhill, normal) frame; not fabrication CAD."""
    bottom = seam_top - dimensions.CLAMP_TOE_BELOW_SEAM_TOP_IN
    throat_top = bottom + dimensions.CLAMP_THROAT_HEIGHT_IN
    top = bottom + dimensions.CLAMP_HEIGHT_IN
    half_width = dimensions.CLAMP_WIDTH_IN / 2
    throat = dimensions.CLAMP_THROAT_WIDTH_IN / 2
    half_length = length / 2
    return [
        (station - half_width, station - throat, -half_length, half_length,
         bottom, throat_top),
        (station + throat, station + half_width, -half_length, half_length,
         bottom, throat_top),
        (station - half_width, station + half_width, -half_length, half_length,
         throat_top, top),
    ]


def roof_seam_clamp_mesh(model, connector):
    """Seat a dimensioned nail-strip clamp on its resolved roof pan and seam."""
    from typehaus.resolve.roof_panel_skin import profiled_roof_layers, seam_stations

    if connector.roof_mount is not None:
        raise ValueError("roof_mount is for flat straps; use connects for the clamp roof")
    roofs = [r for r in model.roofs if r.tag in connector.connects]
    if len(roofs) != 1 or roofs[0].form not in ("gable", "shed"):
        raise ValueError("roof clamp requires exactly one gable or shed roof")
    roof = roofs[0]
    layers = list(profiled_roof_layers(roof, model))
    if len(layers) != 1 or layers[0][3].key != "standing-seam":
        raise ValueError("S-5-N roof clamp requires one Image II standing-seam layer")
    _, base, rect, profile = layers[0]
    along_index = 0 if roof.ridge_direction == "x" else 1
    cross_index = 1 - along_index
    position = connector.position.xy_m
    if not (rect[0] < position[0] < rect[1] and rect[2] < position[1] < rect[3]):
        raise ValueError("roof clamp must lie inside the field panel footprint")
    if not any(abs(position[along_index] - station) < dimensions.GEOMETRY_TOLERANCE_M
               for station in seam_stations(roof, model)):
        raise ValueError("roof clamp must align with a standing seam")
    across = [point[cross_index] for point in roof.footprint]
    low, high = min(across), max(across)
    cross = connector.position.xy_m[cross_index]
    run = high - low if roof.form == "shed" else (high - low) / 2
    if run <= dimensions.GEOMETRY_TOLERANCE_M:
        raise ValueError("roof clamp requires a nonzero roof slope span")
    if roof.form == "gable" and abs(cross - (low + high) / 2) < dimensions.GEOMETRY_TOLERANCE_M:
        raise ValueError("roof clamp must lie on a slope clear of the ridge")
    slope = (roof.ridge_z_m - roof.eave_z_m) / run
    factor = math.hypot(1, slope)
    direction = -1 if roof.form == "shed" or cross < (low + high) / 2 else 1
    downhill = tuple(direction / factor if i == cross_index else
                     (-slope / factor if i == 2 else 0.0) for i in range(3))
    normal = tuple(direction * slope / factor if i == cross_index else
                   (1 / factor if i == 2 else 0.0) for i in range(3))
    x, y = connector.position.xy_m
    z = roof_plane_z(roof, roof_slope_coordinate(roof, (x, y))) + base * factor
    origin = (x, y, z)
    inch = dimensions.INCH_M

    def world(u, v, w):
        return tuple(origin[i] + inch * (u * (i == along_index)
                     + v * downhill[i] + w * normal[i]) for i in range(3))

    length = (dimensions.CLAMP_MINI_LENGTH_IN if connector.size == "S-5-N Mini"
              else dimensions.CLAMP_LENGTH_IN)
    positions, triangles = [], []
    for u0, u1, v0, v1, w0, w1 in clamp_body_boxes(0, profile.depth_m / inch, length):
        corners = ((u0, v0), (u1, v0), (u1, v1), (u0, v1))
        mesh = outward_box_mesh(GBox(tuple(world(u, v, w0) for u, v in corners),
                                    tuple(world(u, v, w1) for u, v in corners)))
        offset = len(positions)
        positions.extend(mesh.positions)
        triangles.extend(tuple(i + offset for i in triangle) for triangle in mesh.triangles)
    return GMesh(tuple(positions), tuple(triangles))


def resolve_roof_seam_clamp(model, connector, storey):
    from typehaus.findings import element_error
    from typehaus.resolve.geometry_slice_box import _hull
    from typehaus.resolve.model import ResolvedSolid

    try:
        body = roof_seam_clamp_mesh(model, connector)
    except ValueError as error:
        return [element_error("integrity.roof_seam_clamp", f"{connector.tag}: {error}",
                              connector.tag)]
    model.solids.append(ResolvedSolid(
        uid=connector.uid or f"{connector.tag}-conn", tag=connector.tag, storey=storey,
        category="seam_clamp", product=connector.size, material=dimensions.ALUMINUM_MATERIAL,
        outline=_hull([(p[0], p[1]) for p in body.positions]),
        z0_m=min(p[2] for p in body.positions), z1_m=max(p[2] for p in body.positions),
        body_mesh=body))
    return []
