"""One geometric definition for track plans, models, bounds, and aiming targets."""

from __future__ import annotations

import math

from shapely.geometry import MultiPoint

from typehaus.model.placeable_symbols._frame import Part, Stroke, box, rect
from typehaus.model.placeable_symbols._mesh import mesh_part
from typehaus.model.track_lighting import TrackHeadSpec, TrackLightingSpec

ROUND_SEGMENTS = 32
LENS_RADIUS_SHARE = 0.82
LENS_THICKNESS_M = 0.002
YOKE_WIDTH_SHARE = 0.12


def head_direction(head: TrackHeadSpec) -> tuple[float, float, float]:
    azimuth, tilt = map(math.radians, (head.azimuth_degrees, head.tilt_degrees))
    return (math.sin(tilt) * math.cos(azimuth), math.sin(tilt) * math.sin(azimuth),
            -math.cos(tilt))


def head_pivot(spec: TrackLightingSpec, head: TrackHeadSpec) -> tuple[float, float, float]:
    """Rail-top frame: the ceiling is z=0 and everything hangs below it."""
    return (head.offset.meters, 0.0,
            -spec.rail_height.meters - head.product.pivot_drop.meters)


def head_lens(spec: TrackLightingSpec, head: TrackHeadSpec) -> tuple[float, float, float]:
    pivot, direction = head_pivot(spec, head), head_direction(head)
    reach = head.product.body_length.meters / 2 + LENS_THICKNESS_M
    return tuple(pivot[i] + direction[i] * reach for i in range(3))


def _cylinder(center, direction, radius, length, color) -> Part:
    """Closed cylinder in an arbitrary orientation, with explicit end-face normals."""
    azimuth = math.atan2(direction[1], direction[0])
    side = (-math.sin(azimuth), math.cos(azimuth), 0.0)
    cross = (direction[1] * side[2] - direction[2] * side[1],
             direction[2] * side[0] - direction[0] * side[2],
             direction[0] * side[1] - direction[1] * side[0])
    vertices, triangles = [], []
    for sign in (-1, 1):
        for segment in range(ROUND_SEGMENTS):
            angle = math.tau * segment / ROUND_SEGMENTS
            vertices.append(tuple(center[i] + sign * length / 2 * direction[i]
                                  + radius * (math.cos(angle) * side[i]
                                              + math.sin(angle) * cross[i])
                                  for i in range(3)))
    vertices.extend(tuple(center[i] + sign * length / 2 * direction[i]
                          for i in range(3)) for sign in (-1, 1))
    for segment in range(ROUND_SEGMENTS):
        following = (segment + 1) % ROUND_SEGMENTS
        a, b, c, d = segment, following, segment + ROUND_SEGMENTS, following + ROUND_SEGMENTS
        triangles.extend(((a, b, c), (b, d, c), (2 * ROUND_SEGMENTS, b, a),
                          (2 * ROUND_SEGMENTS + 1, c, d)))
    return mesh_part(vertices, triangles, color)


def _ceiling_frame_parts(spec: TrackLightingSpec) -> tuple[Part, ...]:
    housing = "appliance-white" if spec.finish == "white" else "metal-black"
    rail_height = spec.rail_height.meters
    parts = [box(0, 0, -rail_height, 0, spec.rail_length.meters,
                 spec.rail_width.meters, housing)]
    feed_sign = -1 if spec.feed_end == "west" else 1
    # The canopy/feed occupies the rail end; its inner half overlaps the rail.
    feed_center = feed_sign * spec.rail_length.meters / 2
    parts.append(box(feed_center, 0, -spec.feed_height.meters, 0,
                     spec.feed_length.meters, spec.feed_width.meters, housing))
    for head in spec.heads:
        product, pivot, direction = head.product, head_pivot(spec, head), head_direction(head)
        adapter_bottom = -rail_height - product.adapter_height.meters
        parts.append(box(head.offset.meters, 0, adapter_bottom, -rail_height,
                         product.adapter_length.meters, product.adapter_width.meters, housing))
        yoke_width = product.body_diameter.meters * YOKE_WIDTH_SHARE
        parts.append(box(head.offset.meters, 0, pivot[2], adapter_bottom,
                         yoke_width, yoke_width, housing))
        # The hinge is visible even when a head points straight down.
        parts.append(_cylinder(pivot, (1.0, 0.0, 0.0), yoke_width,
                               product.body_diameter.meters, housing))
        parts.append(_cylinder(pivot, direction, product.body_diameter.meters / 2,
                               product.body_length.meters, housing))
        lens_center = tuple(pivot[i] + direction[i]
                            * (product.body_length.meters / 2 + LENS_THICKNESS_M / 2)
                            for i in range(3))
        parts.append(_cylinder(lens_center, direction,
                               product.body_diameter.meters / 2 * LENS_RADIUS_SHARE,
                               LENS_THICKNESS_M, "lamp"))
    return tuple(parts)


def _part_vertices(part: Part):
    if "mesh" in part:
        return part["mesh"]["positions"]
    center, size = part["center"], part["size"]
    return tuple((center[0] + x * size[0] / 2, center[1] + y * size[1] / 2,
                  center[2] + z * size[2] / 2)
                 for x in (-1, 1) for y in (-1, 1) for z in (-1, 1))


def track_bounds(spec: TrackLightingSpec) -> tuple[float, float, float, float, float, float]:
    vertices = [v for part in _ceiling_frame_parts(spec) for v in _part_vertices(part)]
    return (*tuple(min(v[i] for v in vertices) for i in range(3)),
            *tuple(max(v[i] for v in vertices) for i in range(3)))


def track_dimensions(spec: TrackLightingSpec) -> tuple[float, float, float]:
    bounds = track_bounds(spec)
    return tuple(bounds[i + 3] - bounds[i] for i in range(3))


def track_geometry(spec: TrackLightingSpec) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    parts = _ceiling_frame_parts(spec)
    height = -min(v[2] for part in parts for v in _part_vertices(part))
    strokes, lifted = [], []
    for part in parts:
        outline = MultiPoint([(v[0], v[1]) for v in _part_vertices(part)]).convex_hull
        strokes.append({"points": tuple(outline.exterior.coords)[:-1], "closed": True,
                        "fill": part["color"], "weight": 0.18})
        translated = {**part, "center": (part["center"][0], part["center"][1],
                                         part["center"][2] + height)}
        if "mesh" in part:
            translated["mesh"] = {**part["mesh"], "positions": tuple(
                (x, y, z + height) for x, y, z in part["mesh"]["positions"])}
        lifted.append(translated)
    return tuple(strokes), tuple(lifted)


def track_light(width: float, depth: float, height: float):
    """Vocabulary glyph; configured catalog types use track_geometry instead."""
    housing = "appliance-white"
    strokes = [rect(0, 0, width, depth * 0.15, fill=housing)]
    parts = [box(0, 0, height * 0.9, height, width, depth * 0.15, housing)]
    for x in (-width * 0.3, width * 0.3):
        strokes.append(rect(x, 0, width * 0.12, depth, fill=housing))
        parts.append(box(x, 0, height * 0.1, height * 0.9, width * 0.12, depth, housing))
        parts.append(box(x, 0, 0, height * 0.1, width * 0.1, depth * 0.8, "lamp"))
    return tuple(strokes), tuple(parts)
