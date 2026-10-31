"""Dropped-ceiling boundaries and physical board, distinct from the service envelope."""

from __future__ import annotations

import math

from shapely.geometry import LineString, Point, Polygon

from typehaus.findings import Finding, element_error
from typehaus.quantities import inch
from typehaus.resolve.geometry import LIGHT_STRIP_WIDTH_M, rect_between
from typehaus.resolve.geometry_ir import GPrism
from typehaus.resolve.model import (
    ResolvedModel,
    SoffitFinishPanel,
    SoffitWallContact,
)
from typehaus.resolve.overlay import union_all

SOFFIT_LINING_THICKNESS = inch(0.625)
CONTACT_TOLERANCE_M = 1e-6


def fit_soffit_outline(model: ResolvedModel, element) -> list[tuple[float, float]]:
    """Fit an authored rectangle across the inside faces of two opposing walls."""
    outline = [point.xy_m for point in element.outline]
    if element.width_between_walls is None:
        return outline
    polygon = Polygon(outline)
    bounds = polygon.bounds
    if (not polygon.is_valid or polygon.area <= CONTACT_TOLERANCE_M ** 2
            or abs(polygon.area - (bounds[2] - bounds[0]) * (bounds[3] - bounds[1]))
            > CONTACT_TOLERANCE_M ** 2):
        raise ValueError("wall-fitted soffits need an axis-aligned rectangle")
    across = 0 if bounds[2] - bounds[0] < bounds[3] - bounds[1] else 1
    walls = {wall.tag: wall for wall in model.walls}
    faces = []
    for index, tag in enumerate(element.width_between_walls):
        wall = walls[tag]
        coordinates = [point[across] for layer in wall.body_layers()
                       for point in layer.polygon]
        faces.append(max(coordinates) if index == 0 else min(coordinates))
    if faces[1] <= faces[0]:
        raise ValueError("opposing wall finishes leave no soffit width")
    return [(faces[0 if point[across] < (bounds[across] + bounds[across + 2]) / 2 else 1],
             point[1]) if across == 0 else
            (point[0], faces[0 if point[1] < (bounds[1] + bounds[3]) / 2 else 1])
            for point in outline]


def wall_footprint(wall) -> Polygon:
    return union_all([Polygon(layer.polygon) for layer in wall.body_layers()
                        if len(layer.polygon) >= 3])


def resolve_soffit_contacts(model: ResolvedModel) -> None:
    """Contact intervals also identify which ladder portions can attach to wall studs."""
    for soffit in model.soffits:
        contacts = []
        for index, start in enumerate(soffit.outline):
            end = soffit.outline[(index + 1) % len(soffit.outline)]
            edge = LineString((start, end))
            for wall in model.walls:
                if (wall.storey != soffit.storey or wall.z0_m > soffit.z0_m
                        or wall.z1_m < soffit.z1_m - SOFFIT_LINING_THICKNESS.meters):
                    continue
                intersection = edge.intersection(wall_footprint(wall).buffer(
                    CONTACT_TOLERANCE_M, join_style=2))
                pieces = getattr(intersection, "geoms", (intersection,))
                for piece in pieces:
                    if piece.geom_type != "LineString" or piece.length <= 4 * CONTACT_TOLERANCE_M:
                        continue
                    stations = [edge.project(Point(point)) for point in piece.coords]
                    # Undo the roundoff buffer along the run, so adjacent walls do not
                    # manufacture micrometre-long ledger pieces at a shared endpoint.
                    start_station = min(stations) + CONTACT_TOLERANCE_M
                    end_station = max(stations) - CONTACT_TOLERANCE_M
                    if start_station <= 2 * CONTACT_TOLERANCE_M:
                        start_station = 0.0
                    if edge.length - end_station <= 2 * CONTACT_TOLERANCE_M:
                        end_station = edge.length
                    contacts.append(SoffitWallContact(index, start_station, end_station,
                                                      wall.tag))
        soffit.wall_contacts = tuple(contacts)


def _polygons(shape):
    if shape.geom_type == "Polygon":
        if shape.area > CONTACT_TOLERANCE_M ** 2:
            yield shape
    else:
        for part in getattr(shape, "geoms", ()):
            yield from _polygons(part)


def _panels(shape, key: str, bottom: float, top: float):
    thickness = SOFFIT_LINING_THICKNESS.meters
    for index, polygon in enumerate(_polygons(shape)):
        prism = GPrism(tuple(polygon.exterior.coords[:-1]), bottom, top,
                       voids=tuple(tuple(ring.coords[:-1]) for ring in polygon.interiors))
        yield SoffitFinishPanel(f"{key}-{index}", prism,
                               polygon.area * (top - bottom) / thickness)


def resolve_soffit_finishes(model: ResolvedModel) -> list[Finding]:
    """No top board; walls, neighboring boxes, hatches and channels cut physical board."""
    thickness = SOFFIT_LINING_THICKNESS.meters
    findings = []
    wall_shapes = [(wall, wall_footprint(wall)) for wall in model.walls]
    for soffit in model.soffits:
        envelope = Polygon(soffit.outline)
        walls = [(wall, shape) for wall, shape in wall_shapes
                 if wall.storey == soffit.storey and shape.intersects(envelope)]
        neighbors = [other for other in model.soffits
                     if other.uid != soffit.uid and other.storey == soffit.storey
                     and Polygon(other.outline).distance(envelope) < CONTACT_TOLERANCE_M]
        bottom_shape = envelope
        for wall, shape in walls:
            if wall.z0_m < soffit.z0_m + thickness and wall.z1_m > soffit.z0_m:
                bottom_shape = bottom_shape.difference(shape)
        for _tag, outline in soffit.openings:
            bottom_shape = bottom_shape.difference(Polygon(outline))
        for run in model.light_runs:
            if run.soffit_ref != soffit.tag:
                continue
            # A shadow gap's reveal was set on this face (→ resolve/drywall_led.py).
            width = run.aperture_m or LIGHT_STRIP_WIDTH_M
            if run.profile != "shadow_gap" and not (
                    soffit.z0_m <= run.z_m - LIGHT_STRIP_WIDTH_M
                    and run.z_m <= soffit.z0_m + thickness):
                findings.append(element_error("integrity.soffit_channel",
                    f"channel {run.tag} must fit within {soffit.tag}'s underside board",
                    run.tag))
                continue
            # The recess is cut before framing; its inner edge lands on the bottom rail.
            slot = LineString(run.path).buffer(width / 2,
                                               cap_style=2, join_style=2)
            bottom_shape = bottom_shape.difference(slot)
        panels = list(_panels(bottom_shape, "underside", soffit.z0_m,
                              soffit.z0_m + thickness))
        # Vertical bands retain the step below a shallower neighboring soffit. Subtracting
        # a neighbor's entire edge would erase that visible riser along with the hidden cap.
        elevations = sorted({soffit.z0_m + thickness, soffit.z1_m} | {
            z for other in neighbors for z in (other.z0_m, other.z1_m)
            if soffit.z0_m + thickness < z < soffit.z1_m} | {
            z for wall, _ in walls for z in (wall.z0_m, wall.z1_m)
            if soffit.z0_m + thickness < z < soffit.z1_m})
        claimed_returns = Polygon()
        for edge_index, start in enumerate(soffit.outline):
            end = soffit.outline[(edge_index + 1) % len(soffit.outline)]
            # Ring winding is irrelevant: intersect the inward half of a full-width strip.
            strip = Polygon(rect_between(start, end, -thickness, thickness)).intersection(
                envelope).difference(claimed_returns)
            claimed_returns = claimed_returns.union(strip)
            bands = zip(elevations, elevations[1:], strict=False)
            for band_index, (bottom, top) in enumerate(bands):
                exposed = strip
                for wall, shape in walls:
                    if wall.z0_m < top and wall.z1_m > bottom:
                        exposed = exposed.difference(shape.buffer(CONTACT_TOLERANCE_M,
                                                                 join_style=2))
                for other in neighbors:
                    if other.z0_m < top and other.z1_m > bottom:
                        exposed = exposed.difference(Polygon(other.outline).buffer(
                            thickness + CONTACT_TOLERANCE_M, join_style=2))
                # A wall touching the edge covers the return's thickness inside the box.
                for contact in soffit.wall_contacts:
                    if contact.edge_index != edge_index:
                        continue
                    length = math.dist(start, end)
                    direction = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
                    endpoints = [tuple(start[i] + station * direction[i] for i in (0, 1))
                                 for station in (contact.start_m, contact.end_m)]
                    exposed = exposed.difference(Polygon(rect_between(
                        *endpoints, -thickness - CONTACT_TOLERANCE_M,
                        thickness + CONTACT_TOLERANCE_M)))
                panels.extend(_panels(exposed, f"return-{edge_index}-{band_index}", bottom, top))
        soffit.finish_panels = tuple(panels)
    return findings
