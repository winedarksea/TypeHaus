"""Formed cap sheets cut around existing bearing wood and connector steel."""

from __future__ import annotations

import math

from shapely.geometry import MultiPoint, box

from typehaus.resolve.flashing_config import FLASHING
from typehaus.resolve.flashing_solids import flashing_solid
from typehaus.resolve.geometry_ir import GBox, GMesh, GSweep
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.geometry_slice import _box_mesh, sweep_mesh
from typehaus.resolve.overlay import difference, union_all
from typehaus.resolve.sheet_geometry import combine_sheets, polygon_sheet, sheet_between

_EPS = 1e-10


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b, strict=True))


def clipped_sheet(a, b, run, thickness, obstacles, clearance=0.0, *, normal_hint=None) -> GMesh:
    """Cut a planar sheet around the actual intersection of each obstruction's mesh.

    A slat's plan bounding box runs all the way up the diagonal and would erase most of
    the cap. Intersecting its faces with the sheet plane keeps just its bearing footprint.
    Steel is treated the same way, with a small installation clearance around each cut.
    """
    width = math.sqrt(_dot(run, run))
    across = _sub(b, a)
    depth = math.sqrt(_dot(across, across))
    u, v = tuple(x / width for x in run), tuple(x / depth for x in across)
    normal = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
              u[0] * v[1] - u[1] * v[0])
    if normal_hint is not None and _dot(normal, normal_hint) < 0:
        normal = tuple(-value for value in normal)
    cuts = []
    for mesh in obstacles:
        # Each vertex participates in the face clipping below as well as the initial
        # containment check. Project once so large connector meshes do not repeat the same
        # three dot products for every incident triangle.
        projected = []
        for vertex in mesh.positions:
            delta = _sub(vertex, a)
            projected.append((_dot(delta, u), _dot(delta, v), _dot(delta, normal)))
        points = [(s, t) for s, t, distance in projected
                  if -_EPS <= distance <= thickness + _EPS]
        # The finite sheet occupies the interval [0, thickness] normal to its plane.
        for offset in (0.0, thickness):
            for triangle in mesh.triangles:
                indices = list(triangle)
                ring = [projected[i] for i in indices]
                next_indices = (*indices[1:], indices[0])
                for index_p, index_q, p, q in zip(
                    indices, next_indices, ring, (*ring[1:], ring[0]), strict=True
                ):
                    dp, dq = p[2] - offset, q[2] - offset
                    if abs(dp) < _EPS:
                        points.append((p[0], p[1]))
                    if dp * dq < 0:
                        t = dp / (dp - dq)
                        # Keep the original 3D interpolation and projection order here.
                        # Shapely's hull can distinguish sub-ulp changes at a cut edge,
                        # which needlessly changes the emitted mesh's triangulation.
                        start, end = mesh.positions[index_p], mesh.positions[index_q]
                        intersection = tuple(
                            start[axis] + t * (end[axis] - start[axis])
                            for axis in range(3)
                        )
                        delta = _sub(intersection, a)
                        points.append((_dot(delta, u), _dot(delta, v)))
        if points:
            # Convex hull is conservative for punched hardware: never fill a fastener hole
            # with cap metal and imply the cap can be installed through the connector.
            cuts.append(MultiPoint(points).convex_hull.buffer(clearance, join_style=2))
    sheet = box(0, 0, width, depth)
    if cuts:
        sheet = difference(sheet, union_all(cuts))
    parts = list(sheet.geoms) if hasattr(sheet, "geoms") else [sheet]

    def place(s, t):
        return tuple(a[i] + u[i] * s + v[i] * t for i in range(3))

    return combine_sheets([polygon_sheet(
        [list(part.exterior.coords)[:-1], *[list(r.coords)[:-1] for r in part.interiors]],
        place, tuple(n * thickness for n in normal))
        for part in parts if part.geom_type == "Polygon" and part.area > _EPS])


def brace_cap_mesh(model, element, section) -> GMesh:
    brace = next((b for b in model.braces if b.tag == element.host_ref), None)
    if brace is None:
        raise ValueError(f"{element.tag}: cap host must name a resolved SlatBrace")
    sill = next(m for m in brace.members if m.child_key == "plate-sill")
    a, b = sill.p0, sill.p1
    span = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / span, (b[1] - a[1]) / span
    # Positive is outboard, regardless of which direction the path was authored.
    sign = -1 if element.back_side == "left" else 1
    outward = (-uy * sign, ux * sign)
    width = element.thickness.meters
    centre = _dot(_sub(element.path[0].xy_m, a), outward)
    bottom = sill.z1_m
    top = bottom + width * section.slope

    def point(depth, z):
        return (a[0] + outward[0] * (depth - width / 2 + centre),
                a[1] + outward[1] * (depth - width / 2 + centre), z)

    obstacles = []
    for member in brace.members:
        if member is sill or member.z0_m > top + section.sheet_thickness.meters:
            continue
        solid = member_solid(member)
        if isinstance(solid, GBox):
            obstacles.append(_box_mesh(solid))
        elif isinstance(solid, GSweep):
            obstacles.append(sweep_mesh(solid))
    for solid in model.solids:
        if (solid.category.startswith("connector") and solid.body_mesh is not None
                and solid.z0_m <= top + section.sheet_thickness.meters
                and solid.z1_m >= bottom - section.drip.meters):
            obstacles.append(solid.body_mesh)
    run = (b[0] - a[0], b[1] - a[1], 0.0)
    legs = [(point(0, top), point(width, bottom)),
            (point(width, bottom), point(width, bottom - section.drip.meters)),
            (point(width, bottom - section.drip.meters),
             point(width - section.hem.meters, bottom - section.drip.meters)),
            (point(0, top), point(0, top - section.drip.meters))]
    meshes = [clipped_sheet(p, q, run, section.sheet_thickness.meters,
                            obstacles, FLASHING.obstacle_clearance_m,
                            normal_hint=(*outward, 1.0))
              for p, q in legs if math.dist(p, q) > _EPS]
    return combine_sheets(meshes)


def resolve_brace_caps(model) -> None:
    from typehaus.model.trim import Flashing

    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if not isinstance(element, Flashing) or element.section is None:
                continue
            if not element.section.fit_to_brace_sill:
                continue
            mesh = brace_cap_mesh(model, element, element.section)
            model.solids.append(flashing_solid(
                uid=f"{element.uid}-cap", tag=element.tag, storey=storey.tag,
                category="beam_cap", mesh=mesh, material=element.material,
                host_ref=element.host_ref))


def formed_run_mesh(element, a, b) -> GMesh:
    section = element.section
    half = element.thickness.meters / 2
    span = math.dist(a, b)
    if span <= _EPS:
        raise ValueError(f"{element.tag}: flashing path has a repeated point")
    ux, uy = (b[0] - a[0]) / span, (b[1] - a[1]) / span
    sign = -1 if element.back_side == "left" else 1
    nx, ny = -uy * sign, ux * sign
    top = element.top_elevation.meters
    front_z = top - 2 * half * section.slope

    def point(depth, z):
        return (a[0] + nx * (depth - half), a[1] + ny * (depth - half), z)

    legs = [(point(0, top), point(2 * half, front_z))]
    if section.profile == "counter" and section.upstand.meters > 0:
        legs.append((point(0, top + section.upstand.meters), point(0, top)))
    elif section.profile == "cap" and section.drip.meters > 0:
        legs.append((point(0, top), point(0, top - section.drip.meters)))
    if section.drip.meters > 0:
        legs.append((point(2 * half, front_z), point(2 * half, front_z - section.drip.meters)))
    if section.hem.meters > 0:
        legs.append((point(2 * half, front_z - section.drip.meters),
                     point(2 * half - section.hem.meters, front_z - section.drip.meters)))
    return combine_sheets([sheet_between(p, q, (b[0] - a[0], b[1] - a[1], 0),
                                          section.sheet_thickness.meters,
                                          normal_hint=(nx, ny, 1.0)) for p, q in legs])
