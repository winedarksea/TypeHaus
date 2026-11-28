"""Solids for the wall-penetration stage's records (decision #142), billed off the records.

Each is ``derived``: drawn, never measured. An authored sleeve (``sleeve_ref``) keeps its own
solid, so the record draws none. Colours come from each part's ``Material``.
"""

from __future__ import annotations

from typing import Any

from typehaus.resolve.duct_part_solids import _solid
from typehaus.resolve.wall_penetration_mesh import (
    Frame,
    block_mesh,
    boot_mesh,
    cover_mesh,
    inlet_mesh,
    sleeve_lip_mesh,
    strut_mesh,
)


def penetration_solids(model: Any, standard: Any) -> None:
    from dataclasses import replace

    from typehaus.resolve.panel_flats import panel_profile

    def add(uid, tag, storey, category, mesh, product, host, material):
        if mesh is not None and mesh.positions:
            model.solids.append(replace(_solid(uid, tag, storey, category, mesh, product,
                                               host), material=material))

    lip = standard.sleeve_lip.meters
    for pen in model.wall_penetrations:
        frame = Frame(pen.origin, pen.tangent, pen.normal)
        wall = model.wall(pen.wall_tag)
        profile = panel_profile(model, wall) if wall is not None else None
        pan = -(profile.depth_m - profile.sheet_thickness_m) if profile is not None else 0.0
        if pen.sleeve_d_m and pen.sleeve_ref is None and pen.closure not in ("block",):
            add(f"{pen.uid}-sleeve", f"{pen.tag}-SLEEVE", pen.storey, "wall_sleeve",
                sleeve_lip_mesh(frame, pen.station_m, pen.z_m, pen.sleeve_d_m,
                                pen.outside_d_m, lip),
                pen.sleeve_product, pen.wall_tag, standard.sleeve_material_ref)
        if pen.closure in ("boot", "strut_boot") and pen.boot_base_m:
            add(f"{pen.uid}-boot", f"{pen.tag}-BOOT", pen.storey, "penetration_boot",
                boot_mesh(frame, pen.station_m, pen.z_m, pen.boot_base_m[0],
                          pen.outside_d_m, pen.boot_height_m, pan),
                pen.closure_product, pen.wall_tag, standard.boot_material_ref)
        elif pen.closure == "inlet" and standard.lineset_inlet is not None:
            row = standard.lineset_inlet
            add(f"{pen.uid}-inlet", f"{pen.tag}-INLET", pen.storey, "lineset_inlet",
                inlet_mesh(frame, pen.station_m, pen.z_m, row.flange_width.meters,
                           row.flange_height.meters, row.projection.meters,
                           pen.outside_d_m), pen.closure_product, pen.wall_tag,
                row.material_ref)
    for mount in model.mount_blocks:
        if mount.kind == "flat":
            continue  # the device itself stands on the pan: no solid of its own
        frame = Frame(mount.origin, mount.tangent, mount.normal)
        if mount.kind == "strut":
            clamps = tuple(z for obj in model.canvas_objects if obj.tag in mount.holds
                           for z in (obj.body_z0_m + 0.0254, (obj.body_z1_m or 0) - 0.0254))
            mesh = strut_mesh(frame, mount.channels, mount.channel_width_m, mount.depth_m,
                              mount.z0_m, mount.z1_m, clamps)
            category = "mount_strut"
        else:
            mesh = block_mesh(frame, mount.station_lo_m, mount.station_hi_m, mount.z0_m,
                              mount.z1_m, mount.depth_m, mount.top_z, back=mount.back_n_m)
            category = "mount_block"
        add(mount.uid, mount.tag, mount.storey, category, mesh, mount.product,
            mount.wall_tag, mount.material)
    _cover_solids(model, standard, add)
    _strap_bodies(model)


def _strap_bodies(model: Any) -> None:
    """Each through-panel strap drawn as its strap on its block, not a marker box."""
    from dataclasses import replace

    from typehaus.resolve.strap_blocks import held_radius
    from typehaus.resolve.wall_penetration_mesh import strap_mesh

    blocks = {m.holds[0]: m for m in model.mount_blocks if m.kind == "strap_block"}
    els = {el.tag: el for el in model.plan.all_elements() if el.tag in blocks}
    for i, solid in enumerate(model.solids):
        block = blocks.get(solid.tag) if solid.category == "panel_strap" else None
        el = els.get(solid.tag)
        if block is None or el is None:
            continue
        xy = el.position.xy_m
        radius = held_radius(model, el, block.normal)
        if radius is None:
            continue
        frame = Frame(block.origin, block.tangent, block.normal)
        n_centre = ((xy[0] - block.origin[0]) * block.normal[0]
                    + (xy[1] - block.origin[1]) * block.normal[1])
        station = ((xy[0] - block.origin[0]) * block.tangent[0]
                   + (xy[1] - block.origin[1]) * block.tangent[1])
        mesh = strap_mesh(frame, station, n_centre, el.elevation.meters, radius,
                          block.back_n_m + block.depth_m)
        zs = [p[2] for p in mesh.positions]
        model.solids[i] = replace(solid, body_mesh=mesh, z0_m=min(zs), z1_m=max(zs))


def _cover_solids(model: Any, standard: Any, add) -> None:
    """The lineset cover channel, swept along each set's outdoor leg."""
    from shapely.geometry import Point

    from typehaus.resolve.linesets import _interior_sets

    row = standard.lineset_inlet
    runs = [r for r in model.pipe_runs if r.system == "refrigerant" and r.z_m]
    if row is None or not runs:
        return
    interior = _interior_sets(model)

    def outside(p) -> bool:
        return not any(z0 <= p[2] <= z1 and shape.covers(Point(p[0], p[1]))
                       for z0, z1, shape in interior)

    walls = _wall_shapes(model)
    for run in runs:
        pts = [(*p, z) for p, z in zip(run.path, run.z_m, strict=True)]
        chains, chain = [], []
        for a, b in zip(pts, pts[1:], strict=False):
            mid = tuple((a[i] + b[i]) / 2 for i in range(3))
            if not outside(mid):
                if chain:
                    chains.append(chain)
                    chain = []
                continue
            a2, b2 = _clear_of_walls(a, b, walls)
            if a2 != a and chain:  # the leg leaves a wall: a new piece from its face
                chains.append(chain)
                chain = []
            chain = chain or [a2]
            chain.append(b2)
            if b2 != b:
                chains.append(chain)
                chain = []
        if chain:
            chains.append(chain)
        for i, points in enumerate(chains):
            add(f"{run.uid}-cover-{i}", f"{run.tag}-COVER-{i + 1}", run.storey,
                "lineset_cover", cover_mesh(points, row.cover_size.meters),
                None, run.tag, standard.cover_material_ref)  # billed in [linesets]

def _wall_shapes(model: Any) -> list[tuple[float, float, Any]]:
    """``(z0, z1, plan body)`` per wall: a cover stops at the face it meets."""
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all

    out = []
    for wall in model.walls:
        rings = [Polygon(ly.polygon) for ly in wall.layers
                 if not ly.is_cavity and len(ly.polygon) >= 3]
        if rings:
            out.append((wall.z0_m, max(wall.z1_m, wall.top_z0_m or 0.0, wall.top_z1_m or 0.0),
                        union_all(rings)))
    return out


def _clear_of_walls(a: tuple, b: tuple, walls: list) -> tuple[tuple, tuple]:
    """The leg ``a``-``b`` cut back to the face of any wall it starts in or runs into."""
    from shapely.geometry import LineString, Point

    seg = LineString([a[:2], b[:2]])
    if seg.length < 1e-6:
        return a, b
    t0, t1 = 0.0, 1.0
    for z0, z1, shape in walls:
        if not (min(a[2], b[2]) <= z1 and max(a[2], b[2]) >= z0) or not seg.intersects(shape):
            continue
        hit = seg.intersection(shape)
        parts = getattr(hit, "geoms", [hit])
        ts = [seg.project(Point(c)) / seg.length for g in parts for c in g.coords]
        if not ts:
            continue
        lo, hi = min(ts), max(ts)
        if lo <= 1e-6:  # starts in the wall: begin at its face
            t0 = max(t0, hi)
        else:  # meets the wall: stop at its face
            t1 = min(t1, lo)

    def at(t: float) -> tuple:
        return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

    return (a if t0 == 0.0 else at(t0)), (b if t1 == 1.0 else at(t1))


def gasket_solid(el: Any, storey: str, centre: tuple[float, float, float],
                 host: Any) -> Any | None:
    """A penetration seal drawn as the gasket ring on its run, where the run is level there."""
    import math

    from typehaus.resolve.model import ResolvedSolid
    from typehaus.resolve.pipe_sections import pipe_run_outside_diameter_m
    from typehaus.resolve.wall_penetration_mesh import gasket_mesh

    path = list(host.path)
    if len(path) < 2:
        return None
    a, b = min(zip(path, path[1:], strict=False),
               key=lambda seg: _point_segment_m(centre[:2], seg[0], seg[1]))
    if math.dist(a, b) < 1e-4:
        return None  # a riser: no level axis to ring
    mesh = gasket_mesh(centre, (b[0] - a[0], b[1] - a[1]), pipe_run_outside_diameter_m(host))
    xs, ys, zs = zip(*mesh.positions, strict=True)
    return ResolvedSolid(
        uid=el.uid or f"{el.tag}-acc", tag=el.tag, storey=storey,
        category=el.kind.value,
        outline=((min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))),
        z0_m=min(zs), z1_m=max(zs), body_mesh=mesh)


def _point_segment_m(p: tuple[float, float], a: tuple[float, float],
                     b: tuple[float, float]) -> float:
    import math

    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy)
                                             / length2))
    return math.dist(p, (a[0] + dx * t, a[1] + dy * t))
