"""Board-and-batten layout across contiguous collinear paneling records.

A model wall split is not a joinery decision. Lay out the connected finish run first,
then assign its cut boards to one backing record so exports and takeoff count each once.
"""
from __future__ import annotations

import math
from dataclasses import replace

from shapely.geometry import box

from typehaus.findings import failed
from typehaus.resolve.model import ResolvedPanelingTrim
from typehaus.resolve.overlay import union_all

_GEOMETRY_TOLERANCE_M = 1e-6


def resolve_paneling_trim(plan, model) -> list:
    findings = []
    for element in plan.elements_of_kind("WallPaneling"):
        spec = element.board_and_batten
        if spec is None:
            continue
        bands = [band for band in model.panelings if band.uid == element.uid]
        error = _spec_error(plan, element, bands)
        if error:
            findings.append(failed("integrity.paneling_ref", error, (element.tag,)))
            continue
        pending = list(bands)
        while pending:
            first = pending.pop(0)
            origin, direction, outward = _frame(first)
            group = [first]
            # Grow only through touching runs on the same face and elevation. A corner
            # starts another layout; disconnected spans never acquire phantom trim.
            changed = True
            while changed:
                changed = False
                for band in list(pending):
                    if _joins(band, group, origin, direction, outward):
                        group.append(band)
                        pending.remove(band)
                        changed = True
            extents = [_interval(band, origin, direction) for band in group]
            run = max(hi for _, hi in extents) - min(lo for lo, _ in extents)
            if run <= spec.batten_width.meters:
                findings.append(failed("integrity.paneling_ref",
                                       "Board-and-batten run is narrower than an end stile",
                                       (element.tag,)))
                continue
            trim = _layout(group, spec, origin, direction, outward)
            for band in group:
                index = model.panelings.index(band)
                model.panelings[index] = replace(
                    band, retains_baseboard=True,
                    trim_pieces=tuple(trim) if band is first else ())
    return findings


def _spec_error(plan, element, bands):
    spec = element.board_and_batten
    dimensions = (spec.thickness, spec.batten_width, spec.rail_width,
                  spec.target_spacing, spec.base_height)
    if any(value.meters <= 0 for value in dimensions):
        return "Board-and-batten dimensions must be positive"
    if spec.target_spacing.meters <= spec.batten_width.meters:
        return "Board-and-batten spacing must exceed batten width"
    if (not element.room or element.replaces_wall_finish
            or (element.offset is not None and element.offset.meters != 0)):
        return "Board-and-batten requires an applied room band starting at the floor"
    if element.thickness is None or element.thickness.meters <= 0:
        return "Board-and-batten requires an explicit positive backing thickness"
    if plan.library.material(spec.material_ref) is None:
        return f"Board-and-batten names no material {spec.material_ref!r}"
    standards = list(plan.elements_of_kind("TrimStandard"))
    if len(standards) != 1 or not math.isclose(
            standards[0].base_height.meters, spec.base_height.meters, abs_tol=1e-9):
        return "Board-and-batten base height must match the existing TrimStandard"
    if not math.isclose(standards[0].thickness.meters, spec.thickness.meters, abs_tol=1e-9):
        return "Board-and-batten thickness must match the retained baseboard"
    if not bands or any(not b.outline or b.z0_m is None or b.z1_m is None for b in bands):
        return "Board-and-batten requires drawable room-side backing geometry"
    if any(b.z1_m - b.z0_m <= spec.base_height.meters + spec.rail_width.meters for b in bands):
        return "Board-and-batten band is too small for its base, rail and battens"
    return None


def _frame(band):
    origin, end, _, back = band.outline
    run = math.dist(origin, end)
    depth = math.dist(origin, back)
    return (origin, tuple((end[i] - origin[i]) / run for i in (0, 1)),
            tuple((back[i] - origin[i]) / depth for i in (0, 1)))


def _project(point, origin, direction):
    return sum((point[i] - origin[i]) * direction[i] for i in (0, 1))


def _interval(band, origin, direction):
    values = [_project(point, origin, direction) for point in band.outline]
    return min(values), max(values)


def _joins(band, group, origin, direction, outward):
    if not math.isclose(band.z0_m, group[0].z0_m, abs_tol=_GEOMETRY_TOLERANCE_M) \
            or not math.isclose(band.z1_m, group[0].z1_m, abs_tol=_GEOMETRY_TOLERANCE_M):
        return False
    _, tangent, normal = _frame(band)
    if sum(normal[i] * outward[i] for i in (0, 1)) < 1 - _GEOMETRY_TOLERANCE_M \
            or abs(sum(tangent[i] * direction[i] for i in (0, 1))) < 1 - _GEOMETRY_TOLERANCE_M:
        return False
    if abs(_project(band.outline[0], origin, outward)) > _GEOMETRY_TOLERANCE_M:
        return False
    lo, hi = _interval(band, origin, direction)
    return any(min(hi, b) >= max(lo, a) - _GEOMETRY_TOLERANCE_M
               for a, b in (_interval(other, origin, direction) for other in group))


def _rectangles(shape):
    if shape.is_empty:
        return []
    if shape.geom_type != "Polygon":
        return [part for geom in getattr(shape, "geoms", ()) for part in _rectangles(geom)]
    if math.isclose(shape.area, box(*shape.bounds).area, abs_tol=1e-10):
        return [shape.bounds]
    # Notched boards are separate rectangular cuts around the opening. Using the net
    # backing domain keeps trim out of doors without subtracting its area twice.
    cuts = sorted({x for ring in (shape.exterior, *shape.interiors) for x, _ in ring.coords})
    return [part for a, b in zip(cuts, cuts[1:], strict=False)
            for part in _rectangles(
                shape.intersection(box(a, shape.bounds[1], b, shape.bounds[3])))]


def _layout(group, spec, origin, direction, outward):
    backing = group[0].thickness_m
    domain = union_all([
        box(min(_project(p, origin, direction) for p in ring), z0,
            max(_project(p, origin, direction) for p in ring), z1)
        for band in group for ring, z0, z1 in band.pieces])
    lo, z0, hi, z1 = domain.bounds
    width = spec.batten_width.meters
    rail = spec.rail_width.meters
    bottom = z0 + spec.base_height.meters
    upper = z1 - rail
    intervals = max(1, math.ceil((hi - lo - width) / spec.target_spacing.meters))
    pitch = (hi - lo - width) / intervals
    boards = [("paneling top rail", lo, hi, upper, z1)]
    boards.extend(("paneling batten", lo + i * pitch, lo + i * pitch + width,
                   bottom, upper) for i in range(intervals + 1))
    result = []
    for kind, a, b, low, high in boards:
        for x0, y0, x1, y1 in _rectangles(domain.intersection(box(a, low, b, high))):
            if min(x1 - x0, y1 - y0) <= _GEOMETRY_TOLERANCE_M:
                continue
            outline = tuple(
                tuple(origin[i] + x * direction[i] + depth * outward[i] for i in (0, 1))
                for x, depth in ((x0, backing), (x1, backing),
                                 (x1, backing + spec.thickness.meters),
                                 (x0, backing + spec.thickness.meters)))
            length, face_width = ((x1 - x0, y1 - y0) if kind == "paneling top rail"
                                  else (y1 - y0, x1 - x0))
            result.append(ResolvedPanelingTrim(
                kind=kind, material_ref=spec.material_ref, outline=outline,
                z0_m=y0, z1_m=y1, length_m=length, width_m=face_width,
                thickness_m=spec.thickness.meters))
    return result
