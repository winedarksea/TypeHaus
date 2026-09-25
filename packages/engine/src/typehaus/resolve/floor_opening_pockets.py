"""Resolve the deliberately narrow wall-enclosed pockets beside stair openings.

The record here is not a room, obstacle, or general walkability feature.  It is proof that
one named stretch of a stair-well edge is enclosed by named walls.  R312 edge coverage is
the sole consumer; every other spatial rule continues to see the ordinary deck and walls.
"""

from __future__ import annotations

from shapely.geometry import LineString, Point, Polygon

from typehaus.findings import Finding, element_error
from typehaus.model.elements import Door, RoughOpening, Wall, Window
from typehaus.model.floors import (
    FloorOpening,
    FloorOpeningPocketClosure,
    FloorSystem,
)
from typehaus.model.spatial import Room
from typehaus.resolve.floor_openings import _rectangular_opening_box
from typehaus.resolve.model import ResolvedFloorOpeningPocketClosure, ResolvedModel
from typehaus.resolve.overlay import union_all

_CHECK_ID = "resolve.floor_opening_pocket_closure"
_TOUCH_TOL_M = 0.04  # joins are construction geometry, not a permissive proximity search
_GUARD_HEIGHT_M = 36.0 * 0.0254


def _wall_or_roof_closes_locally(model: ResolvedModel, wall, surface: float) -> bool:
    """Check a raked wall at local stations, allowing the roof only where it is low.

    ``ResolvedWall.z1_m`` is the rake's bounding height. Conversely, comparing only the
    low endpoint rejects a valid wall whose short end is inside the existing roof closure.
    Sampling makes the two physical barriers complement each other at each station.
    """
    import math

    from typehaus.resolve.roof_geometry import roof_bearing_footprint, roof_underside_at

    p0, p1 = wall.axis
    run = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    steps = max(2, int(run / 0.05) + 1)
    top0 = wall.top_z0_m if wall.top_z0_m is not None else wall.z1_m
    top1 = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
    for index in range(steps + 1):
        t = index / steps
        point = (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
        wall_top = top0 + (top1 - top0) * t
        if wall.z0_m <= surface + 0.1 and wall_top >= surface + _GUARD_HEIGHT_M - 0.02:
            continue
        roof_clearances = []
        for roof in model.roofs:
            footprint = roof_bearing_footprint(model, roof)
            if footprint is None:
                continue
            xs, ys = zip(*footprint, strict=True)
            if min(xs) <= point[0] <= max(xs) and min(ys) <= point[1] <= max(ys):
                roof_clearances.append(roof_underside_at(model, roof, point) - surface)
        if not roof_clearances or min(roof_clearances) >= _GUARD_HEIGHT_M:
            return False
    return True


def _failure(closure: FloorOpeningPocketClosure, message: str) -> Finding:
    return element_error(_CHECK_ID, f"{closure.tag}: {message}", closure.tag)


def _storey_of(plan, element) -> str | None:
    for storey, elements in plan.elements.items():
        if element in elements:
            return storey
    return None


def _edge(box, edge: str) -> tuple[tuple[float, float], tuple[float, float], float]:
    minx, maxx, miny, maxy = box
    if edge == "west":
        return (minx, miny), (minx, maxy), maxy - miny
    if edge == "east":
        return (maxx, miny), (maxx, maxy), maxy - miny
    if edge == "south":
        return (minx, miny), (maxx, miny), maxx - minx
    return (minx, maxy), (maxx, maxy), maxx - minx


def _wall_polygon(wall) -> Polygon | None:
    points = [point for layer in wall.layers for point in layer.polygon]
    if len(points) < 3:
        return None
    polygon = Polygon(points).convex_hull
    return polygon if polygon.is_valid and polygon.area > 1e-8 else None


def _boundary_is_walled(pocket: Polygon, edge_line: LineString, walls) -> bool:
    """Every pocket boundary except its admitted well edge must meet a named wall."""
    wall_area = union_all(walls).buffer(_TOUCH_TOL_M)
    boundary = pocket.boundary.difference(edge_line.buffer(_TOUCH_TOL_M))
    # A buffer turns the line subtraction into short rounded endpoint caps.  Sampling the
    # residual segments catches a missing return without pretending a furniture footprint
    # can cover it.
    parts = getattr(boundary, "geoms", (boundary,))
    for part in parts:
        if getattr(part, "length", 0.0) <= _TOUCH_TOL_M:
            continue
        midpoint = part.interpolate(0.5, normalized=True)
        if not wall_area.covers(midpoint):
            return False
    return True


def resolve_floor_opening_pockets(plan, model: ResolvedModel) -> list[Finding]:
    """Validate authored pocket closures and retain only trustworthy ones in the IR."""
    closures = [
        element for element in plan.all_elements() if isinstance(element, FloorOpeningPocketClosure)
    ]
    if not closures:
        return []

    authored = {element.tag: element for element in plan.all_elements()}
    floors = {
        element.tag: element for element in plan.all_elements() if isinstance(element, FloorSystem)
    }
    hosts = {opening: floor.tag for floor in floors.values() for opening in floor.openings}
    resolved_floors = {floor.tag: floor for floor in model.floors}
    resolved_walls = {wall.tag: wall for wall in model.walls}
    findings: list[Finding] = []

    for closure in closures:
        opening = authored.get(closure.opening_ref)
        if not isinstance(opening, FloorOpening):
            findings.append(
                _failure(closure, f"opening_ref {closure.opening_ref!r} is not a FloorOpening")
            )
            continue
        host_tag = hosts.get(opening.tag)
        floor = resolved_floors.get(host_tag or "")
        closure_storey = _storey_of(plan, closure)
        opening_storey = _storey_of(plan, opening)
        if (
            host_tag is None
            or floor is None
            or not floor.deck_outline
            or closure_storey is None
            or closure_storey != opening_storey
        ):
            findings.append(
                _failure(closure, "must share its STAIR opening's resolved FloorSystem storey")
            )
            continue
        box = _rectangular_opening_box(opening)
        if box is None:
            findings.append(_failure(closure, "requires an axis-aligned rectangular FloorOpening"))
            continue
        p0, p1, edge_length = _edge(box, closure.edge_interval.edge)
        start, end = closure.edge_interval.start.meters, closure.edge_interval.end.meters
        if start < -1e-9 or end > edge_length + 1e-9 or end - start <= _TOUCH_TOL_M:
            findings.append(
                _failure(
                    closure,
                    "edge interval must be a non-empty low-to-high span within its opening edge",
                )
            )
            continue
        if len(set(closure.wall_refs)) < 3:
            findings.append(
                _failure(closure, "requires the rear wall and both return-wall references")
            )
            continue
        if not closure.source.strip():
            findings.append(_failure(closure, "requires a non-empty construction source"))
            continue

        walls = []
        invalid_wall = None
        for tag in closure.wall_refs:
            authored_wall, wall = authored.get(tag), resolved_walls.get(tag)
            if (
                not isinstance(authored_wall, Wall)
                or wall is None
                or _storey_of(plan, authored_wall) != closure_storey
            ):
                invalid_wall = tag
                break
            polygon = _wall_polygon(wall)
            if polygon is None:
                invalid_wall = tag
                break
            walls.append((tag, wall, polygon))
        if invalid_wall is not None:
            findings.append(
                _failure(
                    closure, f"wall_refs must resolve to walls on {closure_storey}: {invalid_wall}"
                )
            )
            continue

        pocket = Polygon([point.xy_m for point in closure.pocket_outline])
        if len(closure.pocket_outline) < 3 or not pocket.is_valid or pocket.area <= 1e-6:
            findings.append(
                _failure(closure, "pocket_outline must be one valid non-zero-area polygon")
            )
            continue
        edge_start = (
            p0[0] + (p1[0] - p0[0]) * start / edge_length,
            p0[1] + (p1[1] - p0[1]) * start / edge_length,
        )
        edge_end = (
            p0[0] + (p1[0] - p0[0]) * end / edge_length,
            p0[1] + (p1[1] - p0[1]) * end / edge_length,
        )
        edge_line = LineString([edge_start, edge_end])
        opening_polygon = Polygon([point.xy_m for point in opening.outline])
        if (
            pocket.intersection(opening_polygon).area > 1e-6
            or pocket.boundary.distance(edge_line) > _TOUCH_TOL_M
        ):
            findings.append(
                _failure(
                    closure, "pocket must abut, but not overlap, its named opening edge interval"
                )
            )
            continue
        deck = Polygon(floor.deck_outline)
        if not deck.covers(pocket):
            findings.append(
                _failure(closure, "pocket must lie on the opening host's adjacent deck")
            )
            continue

        wall_polygons = [polygon for _tag, _wall, polygon in walls]
        wall_union = union_all(wall_polygons)
        if any(
            a.intersection(b).area > _TOUCH_TOL_M**2
            for index, a in enumerate(wall_polygons)
            for b in wall_polygons[index + 1 :]
        ):
            findings.append(
                _failure(
                    closure, "named walls overlap or cross instead of meeting at pocket returns"
                )
            )
            continue
        joined = wall_union.buffer(_TOUCH_TOL_M)
        if len(getattr(joined, "geoms", (joined,))) != 1:
            findings.append(
                _failure(closure, "named wall footprints do not form one connected pocket barrier")
            )
            continue
        if (
            joined.distance(Point(edge_start)) > _TOUCH_TOL_M
            or joined.distance(Point(edge_end)) > _TOUCH_TOL_M
            or not _boundary_is_walled(pocket, edge_line, wall_polygons)
        ):
            findings.append(
                _failure(
                    closure, "named walls must connect at both edge endpoints and bound the pocket"
                )
            )
            continue
        if any(polygon.intersection(opening_polygon).area > 1e-6 for polygon in wall_polygons):
            findings.append(_failure(closure, "named walls may not cross the stair opening"))
            continue
        openings = [
            element.tag
            for element in plan.all_elements()
            if isinstance(element, (Door, Window, RoughOpening))
            and element.host in closure.wall_refs
        ]
        if openings:
            findings.append(
                _failure(closure, f"named pocket walls contain opening(s): {', '.join(openings)}")
            )
            continue
        surface = floor.deck_top_range()[1]  # a tilted deck's high edge governs
        if any(not _wall_or_roof_closes_locally(model, wall, surface)
               for _tag, wall, _polygon in walls):
            findings.append(
                _failure(
                    closure,
                    "named walls must stand 36 inches above the deck (or the existing roof "
                    "exception must close the interval)",
                )
            )
            continue
        if any(
            pocket.covers(Point(room.seed.xy_m))
            for room in plan.all_elements()
            if isinstance(room, Room) and _storey_of(plan, room) == closure_storey
        ):
            findings.append(_failure(closure, "pocket contains a room seed"))
            continue
        if any(
            pocket.intersection(Polygon(stair.outline)).area > 1e-6
            for stair in model.stairs
            if stair.to_storey == closure_storey or stair.storey == closure_storey
        ):
            findings.append(_failure(closure, "pocket overlaps a stair or its arrival"))
            continue
        if any(
            pocket.intersects(Polygon(other.pocket_outline))
            for other in model.floor_opening_pocket_closures
            if other.storey == closure_storey
        ):
            findings.append(_failure(closure, "pocket overlaps an already valid pocket closure"))
            continue

        model.floor_opening_pocket_closures.append(
            ResolvedFloorOpeningPocketClosure(
                uid=closure.uid,
                tag=closure.tag,
                storey=closure_storey,
                opening_ref=opening.tag,
                edge=closure.edge_interval.edge,
                start_m=start,
                end_m=end,
                wall_refs=closure.wall_refs,
                pocket_outline=tuple(point.xy_m for point in closure.pocket_outline),
                source=closure.source,
            )
        )
    return findings


def pocket_closure_intervals(
    model: ResolvedModel, opening_ref: str, edge: str, edge_length_m: float
) -> tuple[tuple[float, float, str], ...]:
    """Validated closure spans for one opening edge, clipped to the measured segment."""
    return tuple(
        (max(0.0, closure.start_m), min(edge_length_m, closure.end_m), closure.tag)
        for closure in getattr(model, "floor_opening_pocket_closures", ())
        if closure.opening_ref == opening_ref
        and closure.edge == edge
        and closure.end_m > 0.0
        and closure.start_m < edge_length_m
    )
