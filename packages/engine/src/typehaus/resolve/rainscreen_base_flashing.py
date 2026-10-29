"""Formed flashing under the same mitred cavity outline as the base screen, and the EPDM
isolation where the steel base trim laps the aluminium screen."""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.resolve.cladding_trim.section import folded_section_mesh
from typehaus.resolve.model import ResolvedSolid
from typehaus.resolve.rainscreen_closures import BUG_SCREEN_HEIGHT_IN, cavity_base_run


def _end_stations(run, offset):
    """Intersect an offset line with the cavity polygon, including the mitred ends."""
    points = []
    for a, b in zip(run.outline, (*run.outline[1:], run.outline[0]), strict=True):
        oa = a[0] * run.outward[0] + a[1] * run.outward[1]
        ob = b[0] * run.outward[0] + b[1] * run.outward[1]
        if abs(ob - oa) < 1e-10:
            if abs(offset - oa) < 1e-8:
                points.extend((a, b))
            continue
        t = (offset - oa) / (ob - oa)
        if -1e-8 <= t <= 1 + 1e-8:
            points.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    along = [p[0] * run.direction[0] + p[1] * run.direction[1] for p in points]
    return min(along), max(along)


def _mitre_mesh(mesh, run, start, end, total):
    positions = []
    for x, y, z in mesh.positions:
        along = x * run.direction[0] + y * run.direction[1]
        offset = x * run.outward[0] + y * run.outward[1]
        offset = min(run.outer_offset, max(run.inner_offset, offset))
        lo, hi = _end_stations(run, offset)
        shift = 0.0
        if start == 0 and abs(along - run.start) < 1e-7:
            shift = lo - run.start
        elif abs(end - total) < 1e-7 and abs(along - run.end) < 1e-7:
            shift = hi - run.end
        positions.append((x + shift * run.direction[0], y + shift * run.direction[1], z))
    return replace(mesh, positions=tuple(positions))


def resolve_rainscreen_base_flashing(model) -> None:
    for wall in model.walls:
        run = cavity_base_run(model, wall)
        assembly = model.plan.library.resolve_assembly(wall.assembly)
        spec = assembly.rainscreen_base_flashing if assembly else None
        if run is None or spec is None:
            continue
        depth = run.outer_offset - run.inner_offset
        thickness = spec.sheet_thickness.meters
        # The section's outer line is above its inset by one normal sheet thickness.
        top = wall.z0_m + thickness * math.sqrt(1 + spec.slope**2)
        section = ((0.0, spec.upstand.meters), (0.0, 0.0),
                   (depth, -depth * spec.slope),
                   (depth, -depth * spec.slope - spec.drip.meters),
                   (depth + spec.hem.meters, -depth * spec.slope - spec.drip.meters))
        total = run.end - run.start
        for index, (start, end, stock) in enumerate(split_stock_run(
                total, (spec.stock_length.meters,), spec.lap.meters)):
            station = run.start + start
            x = station * run.direction[0] + run.inner_offset * run.outward[0]
            y = station * run.direction[1] + run.inner_offset * run.outward[1]
            mesh = folded_section_mesh(section, (x, y, top), (*run.outward, 0.0),
                                       (0.0, 0.0, 1.0),
                                       (run.direction[0] * (end-start),
                                        run.direction[1] * (end-start), 0.0), thickness)
            mesh = _mitre_mesh(mesh, run, start, end, total)
            xs, ys, zs = zip(*mesh.positions, strict=True)
            model.solids.append(ResolvedSolid(
                uid=f"{wall.uid}-basez-{index}", tag=f"{wall.tag}-BASEZ-{index+1}",
                storey=wall.storey, category="cladding_trim", material=spec.material,
                product="RAINSCREEN_BASE_Z", host_ref=wall.tag, body_mesh=mesh, derived=True,
                outline=((min(xs), min(ys)), (max(xs), min(ys)),
                         (max(xs), max(ys)), (min(xs), max(ys))),
                z0_m=min(zs), z1_m=max(zs), trim_length_m=end-start,
                trim_stock_length_in=round(stock / M_PER_IN, 6)))
        # The strip isolates the steel trim's back leg from the screen's outer leg where the
        # one laps the other; the drip below it stays bare so the pan edge drains.
        station = run.start
        isolation_thickness = spec.isolation_thickness.meters
        offset = run.outer_offset
        bottom = wall.z0_m + spec.trim_rise.meters
        lap_top = top + BUG_SCREEN_HEIGHT_IN * M_PER_IN
        x = station * run.direction[0] + offset * run.outward[0]
        y = station * run.direction[1] + offset * run.outward[1]
        strip_mesh = folded_section_mesh(
            ((0.0, 0.0), (0.0, lap_top - bottom)),
            (x, y, bottom), (*run.outward, 0.0), (0.0, 0.0, 1.0),
            (run.direction[0] * total, run.direction[1] * total, 0.0),
            isolation_thickness)
        strip_mesh = _mitre_mesh(strip_mesh, run, 0, total, total)
        xs, ys, zs = zip(*strip_mesh.positions, strict=True)
        model.solids.append(ResolvedSolid(
            uid=f"{wall.uid}-basez-isolation", tag=f"{wall.tag}-BASEZ-ISOLATION",
            storey=wall.storey, category="cladding_trim", material="rubber",
            product="EPDM_BASE_ISOLATION", host_ref=wall.tag, body_mesh=strip_mesh,
            derived=True, outline=((min(xs), min(ys)), (max(xs), min(ys)),
                                   (max(xs), max(ys)), (min(xs), max(ys))),
            z0_m=min(zs), z1_m=max(zs), trim_length_m=total))
