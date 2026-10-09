"""One winder layout: clear boundaries, cut panels, and concentric walkline measurements."""

from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from typehaus.model.stair_winders import WinderTurnSpec
from typehaus.quantities import inch, m, pt

Point2 = tuple[float, float]
Segment = tuple[Point2, Point2]
WALKLINE_OFFSET_M = inch(12).meters
DESIGN_NARROW_DEPTH_M = inch(6.25).meters
LAYOUT_INCREMENT_M = inch(0.25).meters
GEOMETRY_TOLERANCE_M = 1e-7


def ascent_normal(line: Segment, probe: Point2) -> Point2:
    (ax, ay), (bx, by) = line
    length = math.hypot(bx - ax, by - ay)
    if length <= GEOMETRY_TOLERANCE_M:
        raise ValueError("a winder riser segment has zero length")
    nx, ny = (by - ay) / length, -(bx - ax) / length
    if nx * (probe[0] - ax) + ny * (probe[1] - ay) < 0:
        nx, ny = -nx, -ny
    return nx, ny


def shifted_line(line: Segment, normal: Point2, distance_m: float) -> Segment:
    return tuple((x + normal[0] * distance_m, y + normal[1] * distance_m)
                 for x, y in line)


def clip_half_plane(polygon: Polygon, line: Segment, normal: Point2,
                    distance_m: float = 0.0, ahead: bool = True) -> Polygon:
    """Clip without arbitrary world-sized cutters; the reach follows this polygon's bounds."""
    a, b = shifted_line(line, normal, distance_m)
    ux, uy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(ux, uy)
    ux, uy = ux / length, uy / length
    reach = max(polygon.length, length) * 2
    nx, ny = normal if ahead else (-normal[0], -normal[1])
    p = (a[0] - ux * reach, a[1] - uy * reach)
    q = (a[0] + ux * reach, a[1] + uy * reach)
    cut = polygon.intersection(Polygon((p, q, (q[0] + nx * reach, q[1] + ny * reach),
                                       (p[0] + nx * reach, p[1] + ny * reach))))
    if not isinstance(cut, Polygon) or cut.area <= GEOMETRY_TOLERANCE_M ** 2:
        raise ValueError("winder boundaries produce an empty or disconnected panel")
    return cut


def polygon_ring(polygon: Polygon) -> list[Point2]:
    # GEOS may keep redundant clipping vertices. They form zero-area mesh faces on export.
    return list(polygon.simplify(GEOMETRY_TOLERANCE_M).exterior.coords)[:-1]


def physical_nosing_line(polygon: Polygon, normal: Point2) -> Segment:
    """The foremost physical panel edge in the direction opposite ascent."""
    ring = polygon_ring(polygon)
    foremost = min(x * normal[0] + y * normal[1] for x, y in ring)
    vertices = [p for p in ring if abs(p[0] * normal[0] + p[1] * normal[1]
                                      - foremost) <= GEOMETRY_TOLERANCE_M]
    vertices.sort(key=lambda p: -p[0] * normal[1] + p[1] * normal[0])
    if len(vertices) < 2 or math.dist(vertices[0], vertices[-1]) <= GEOMETRY_TOLERANCE_M:
        raise ValueError("physical winder panel has no single nosing edge")
    edge = (vertices[0], vertices[-1])
    if not polygon.boundary.buffer(GEOMETRY_TOLERANCE_M).covers(LineString(edge)):
        raise ValueError("physical winder nosing must be a connected straight edge")
    return edge


def line_intersection(first: Segment, second: Segment) -> Point2:
    a, b = first
    c, d = second
    ux, uy, vx, vy = b[0] - a[0], b[1] - a[1], d[0] - c[0], d[1] - c[1]
    determinant = ux * vy - uy * vx
    if abs(determinant) <= GEOMETRY_TOLERANCE_M ** 2:
        raise ValueError("entering and departing winder risers must define a turn")
    t = ((c[0] - a[0]) * vy - (c[1] - a[1]) * vx) / determinant
    return a[0] + ux * t, a[1] + uy * t


@dataclass(frozen=True)
class WinderLayout:
    footprint: tuple[Point2, ...]
    inner_boundary: tuple[Point2, ...]
    riser_lines: tuple[Segment, ...]
    normals: tuple[Point2, ...]

    @property
    def polygon(self) -> Polygon:
        return Polygon(self.footprint)

    @property
    def centre(self) -> Point2:
        return line_intersection(self.riser_lines[0], self.riser_lines[-1])

    def panel(self, index: int, nosing_m: float, rear_fit_m: float) -> Polygon:
        entering = self.riser_lines[0]
        # Only the entering edge projects beyond the turn. The remaining noses overlap
        # the preceding panel, while the exterior wall and clear well edges remain fixed.
        strip = Polygon((*entering, *reversed(shifted_line(
            entering, self.normals[0], -nosing_m))))
        extended = self.polygon.union(strip) if nosing_m > 0 else self.polygon
        cut = clip_half_plane(extended, self.riser_lines[index], self.normals[index], -nosing_m)
        return clip_half_plane(cut, self.riser_lines[index + 1], self.normals[index + 1],
                               rear_fit_m, ahead=False)

    def subdeck(self, index: int, riser_thickness_m: float) -> Polygon:
        return clip_half_plane(self.polygon, self.riser_lines[index], self.normals[index],
                               riser_thickness_m)


def layout_from_spec(spec: WinderTurnSpec, count: int, width_m: float) -> WinderLayout:
    footprint = tuple(p.xy_m for p in spec.footprint)
    inner = tuple(p.xy_m for p in spec.inner_boundary)
    lines = tuple(tuple(p.xy_m for p in line) for line in spec.riser_lines)
    if len(footprint) < 3:
        raise ValueError("winder footprint needs at least three vertices")
    coordinates = (*footprint, *inner, *(p for line in lines for p in line))
    if not all(math.isfinite(v) for p in coordinates for v in p):
        raise ValueError("winder coordinates must be finite")
    polygon = Polygon(footprint)
    if not polygon.is_valid or polygon.area <= GEOMETRY_TOLERANCE_M ** 2:
        raise ValueError("winder footprint must be a simple, positive-area polygon")
    if len(lines) != count + 1 or len(inner) < 2:
        raise ValueError("a winder turn needs n + 1 riser segments and a clear inner boundary")
    if count < 1 or width_m <= 0:
        raise ValueError("winder count and clear width must be positive")
    boundary = polygon.boundary
    if not boundary.buffer(GEOMETRY_TOLERANCE_M).covers(LineString(inner)):
        raise ValueError("the complete winder inner boundary must follow its footprint")
    if any(boundary.distance(Point(p)) > GEOMETRY_TOLERANCE_M for p in inner):
        raise ValueError("winder clear inner boundary must lie on its footprint")
    inner_path = LineString(inner)
    if math.dist(lines[0][0], inner[0]) > GEOMETRY_TOLERANCE_M or math.dist(
            lines[-1][0], inner[-1]) > GEOMETRY_TOLERANCE_M:
        raise ValueError("winder inner boundary must start and end at the inner riser endpoints")
    stations = [inner_path.project(Point(line[0])) for line in lines]
    if any(b <= a + GEOMETRY_TOLERANCE_M for a, b in zip(stations, stations[1:], strict=False)):
        raise ValueError("winder inner endpoints must advance along the clear inner boundary")
    for line in lines:
        if inner_path.distance(Point(line[0])) > GEOMETRY_TOLERANCE_M:
            raise ValueError("every winder riser must start on the clear inner boundary")
        if any(boundary.distance(Point(p)) > GEOMETRY_TOLERANCE_M for p in line):
            raise ValueError("winder riser endpoints must lie on the footprint")
        if not polygon.buffer(GEOMETRY_TOLERANCE_M).covers(LineString(line)):
            raise ValueError("winder riser crosses outside the footprint")
    if any(abs(math.dist(*line) - width_m) > GEOMETRY_TOLERANCE_M
           for line in (lines[0], lines[-1])):
        raise ValueError("entering and departing winder edges must match the stair width")
    if (abs(lines[0][0][1] - lines[0][1][1]) > GEOMETRY_TOLERANCE_M
            or abs(lines[-1][0][0] - lines[-1][1][0]) > GEOMETRY_TOLERANCE_M
            or lines[0][0][0] <= lines[0][1][0]
            or lines[-1][0][1] >= lines[-1][1][1]):
        raise ValueError("local winder entry must ascend +y and departure +x, "
                         "with inner endpoints first")
    normals = []
    for index, line in enumerate(lines):
        probe = lines[index + 1][1] if index < count else (
            line[0][0] + width_m, line[0][1])
        normals.append(ascent_normal(line, probe))
    layout = WinderLayout(footprint, inner, lines, tuple(normals))
    entering, departing = normals[0], normals[-1]
    if abs(entering[0] * departing[0] + entering[1] * departing[1]) > 1e-6:
        raise ValueError("winder entering and departing directions must form a right angle")
    panels = [clip_half_plane(clip_half_plane(polygon, lines[i], normals[i]),
                              lines[i + 1], normals[i + 1], ahead=False)
              for i in range(count)]
    coverage = unary_union(panels)
    if (abs(sum(p.area for p in panels) - coverage.area) > GEOMETRY_TOLERANCE_M
            or coverage.symmetric_difference(polygon).area > GEOMETRY_TOLERANCE_M):
        raise ValueError("winder riser segments must partition the complete turn in ascent order")
    return layout


def balanced_winder_turn(width_m: float, count: int, nosing_m: float) -> WinderTurnSpec:
    """Smallest quarter-inch inner well in the radial family meeting the narrow target.

    Equal angular stations intersect a concentric walkline at equal chord depths, including
    the entering and departing nosings. The physical nose shifts the narrow intersections,
    so sizing the well from bare endpoint gaps would under-size it.
    """
    if count < 3 or width_m <= 0 or nosing_m < 0:
        raise ValueError("a balanced quarter turn needs at least three winders and positive width")
    angle = math.pi / (2 * count)
    loss = 2 * nosing_m * (1 / math.cos(angle / 2) - 1)
    radius = math.ceil((DESIGN_NARROW_DEPTH_M + loss) / math.sin(angle)
                       / LAYOUT_INCREMENT_M) * LAYOUT_INCREMENT_M
    while True:
        extent = width_m + radius
        inner = tuple((extent - radius * math.cos(index * angle),
                       radius * math.sin(index * angle)) for index in range(count + 1))
        outer = []
        for index in range(count + 1):
            theta = index * angle
            reach = extent / max(math.cos(theta), math.sin(theta))
            outer.append((extent - reach * math.cos(theta), reach * math.sin(theta)))
        spec = WinderTurnSpec(
            footprint=tuple(pt(m(x), m(y)) for x, y in
                            ((0.0, 0.0), (0.0, extent), (extent, extent), *reversed(inner))),
            inner_boundary=tuple(pt(m(x), m(y)) for x, y in inner),
            riser_lines=tuple((pt(m(a[0]), m(a[1])), pt(m(b[0]), m(b[1])))
                              for a, b in zip(inner, outer, strict=True)))
        layout = layout_from_spec(spec, count, width_m)
        noses = tuple(shifted_line(line, normal, -nosing_m)
                      for line, normal in zip(layout.riser_lines, layout.normals, strict=True))
        if min(measure_winders(layout.inner_boundary, layout.riser_lines, noses,
                               tuple(layout.panel(i, nosing_m, 0) for i in range(count)))
               .narrow_depths_m
               ) >= DESIGN_NARROW_DEPTH_M - GEOMETRY_TOLERANCE_M:
            return spec
        radius += LAYOUT_INCREMENT_M


@dataclass(frozen=True)
class WinderMeasurements:
    walkline_points: tuple[Point2, ...]
    walkline_depths_m: tuple[float, ...]
    narrow_depths_m: tuple[float, ...]
    centre: Point2
    radius_m: float


def _circle_point(line: Segment, centre: Point2, radius: float) -> Point2:
    a, b = line
    dx, dy = b[0] - a[0], b[1] - a[1]
    px, py = a[0] - centre[0], a[1] - centre[1]
    aa, bb = dx * dx + dy * dy, 2 * (px * dx + py * dy)
    discriminant = bb * bb - 4 * aa * (px * px + py * py - radius * radius)
    if aa <= GEOMETRY_TOLERANCE_M ** 2 or discriminant < 0:
        raise ValueError("winder nosing does not intersect the concentric walkline")
    roots = [(-bb + sign * math.sqrt(discriminant)) / (2 * aa) for sign in (-1, 1)]
    valid = [t for t in roots if -GEOMETRY_TOLERANCE_M <= t <= 1 + GEOMETRY_TOLERANCE_M]
    if len(valid) != 1:
        raise ValueError("winder nosing must cross the walkline exactly once within clear width")
    t = valid[0]
    return a[0] + dx * t, a[1] + dy * t


def measure_winders(inner: tuple[Point2, ...], risers: tuple[Segment, ...],
                    noses: tuple[Segment, ...],
                    panels: tuple[Polygon, ...]) -> WinderMeasurements:
    """Measure resolved noses, never authored goings or distance along separate fan lines."""
    if len(noses) != len(risers) or len(noses) < 2 or len(panels) != len(noses) - 1:
        raise ValueError("every winder needs its entering and departing nosing")
    centre = line_intersection(risers[0], risers[-1])
    narrow_boundary = LineString(inner)
    radius = narrow_boundary.distance(Point(centre)) + WALKLINE_OFFSET_M
    points = tuple(_circle_point(line, centre, radius) for line in noses)
    narrow = []
    for index, panel in enumerate(panels):
        # Crop rear fit beneath the next tread's foremost projection. Plane distance is
        # affine inside this region, so evaluating every vertex proves the minimum across
        # the entire clear tread, including irregular outer boundaries and interior pinches.
        trailing_normal = ascent_normal(risers[index + 1], risers[index][1])
        clear = clip_half_plane(panel, noses[index + 1], trailing_normal)
        distances = []
        for point in polygon_ring(clear):
            depth = 0.0
            for a, b in noses[index:index + 2]:
                length = math.dist(a, b)
                nx, ny = (b[1] - a[1]) / length, -(b[0] - a[0]) / length
                depth += abs((point[0] - a[0]) * nx + (point[1] - a[1]) * ny)
            distances.append(depth)
        narrow.append(min(distances))
    return WinderMeasurements(points, tuple(math.dist(a, b) for a, b in
                                            zip(points, points[1:], strict=False)),
                              tuple(narrow), centre, radius)
