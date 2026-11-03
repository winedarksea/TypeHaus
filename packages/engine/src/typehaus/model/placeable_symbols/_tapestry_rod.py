"""Tapestry-specific rod hardware, including fourteen rings and fabric clips."""

import math

from typehaus.model.placeable_symbols._curtain_rod import curtain_rod
from typehaus.model.placeable_symbols._frame import Part, box

INCH_M = 0.0254
CLIP_COUNT = 14
FABRIC_WIDTH_M = 80 * INCH_M
FABRIC_EDGE_INSET_M = INCH_M
BARE_ROD_HEIGHT_M = 2 * INCH_M
RING_RADIUS_M = 0.6875 * INCH_M
RING_WIRE_RADIUS_M = 0.0625 * INCH_M
RING_SEGMENTS = 24
WIRE_SEGMENTS = 8
CLIP_WIDTH_M = 0.375 * INCH_M
CLIP_DEPTH_M = 0.125 * INCH_M
CLIP_BOTTOM_M = 0.375 * INCH_M
HARDWARE_COLOR = "metal-black"


def _clip_ring(x: float, y: float, z: float) -> Part:
    positions, normals, triangles = [], [], []
    for course in range(RING_SEGMENTS):
        angle = math.tau * course / RING_SEGMENTS
        for wire in range(WIRE_SEGMENTS):
            wire_angle = math.tau * wire / WIRE_SEGMENTS
            axial, radial = math.sin(wire_angle), math.cos(wire_angle)
            radius = RING_RADIUS_M + RING_WIRE_RADIUS_M * radial
            positions.append((x + RING_WIRE_RADIUS_M * axial,
                              y + radius * math.cos(angle), z + radius * math.sin(angle)))
            normals.append((axial, radial * math.cos(angle), radial * math.sin(angle)))
            a = course * WIRE_SEGMENTS + wire
            b = course * WIRE_SEGMENTS + (wire + 1) % WIRE_SEGMENTS
            c = ((course + 1) % RING_SEGMENTS) * WIRE_SEGMENTS + wire
            d = ((course + 1) % RING_SEGMENTS) * WIRE_SEGMENTS + (wire + 1) % WIRE_SEGMENTS
            triangles.extend(((a, c, b), (b, c, d)))
    diameter = 2 * (RING_RADIUS_M + RING_WIRE_RADIUS_M)
    return {"center": (x, y, z), "size": (2 * RING_WIRE_RADIUS_M, diameter, diameter),
            "color": HARDWARE_COLOR, "points": (), "shape": "mesh",
            "mesh": {"positions": tuple(positions), "normals": tuple(normals),
                     "triangles": tuple(triangles)}}


def _tapestry_rod_clips(width: float, depth: float, height: float):
    """The four-inch envelope keeps the shaft at 74½ inches and clips on the 72-inch hem."""
    strokes, bare_parts = curtain_rod(width, depth, BARE_ROD_HEIGHT_M)
    rod_lift = height - BARE_ROD_HEIGHT_M
    parts = []
    for part in bare_parts:
        x, y, z = part["center"]
        shifted = {**part, "center": (x, y, z + rod_lift)}
        if "mesh" in part:
            shifted["mesh"] = {**part["mesh"], "positions": tuple(
                (px, py, pz + rod_lift) for px, py, pz in part["mesh"]["positions"])}
        parts.append(shifted)
    rod_y, rod_z = bare_parts[0]["center"][1], bare_parts[0]["center"][2] + rod_lift
    clip_span = min(FABRIC_WIDTH_M, width) - 2 * FABRIC_EDGE_INSET_M
    for index in range(CLIP_COUNT):
        x = -clip_span / 2 + clip_span * index / (CLIP_COUNT - 1)
        parts.append(_clip_ring(x, rod_y, rod_z))
        parts.append(box(x, rod_y, CLIP_BOTTOM_M, rod_z - RING_RADIUS_M,
                         CLIP_WIDTH_M, CLIP_DEPTH_M, HARDWARE_COLOR))
    return strokes, tuple(parts)


def tapestry_rod_clips(width: float, depth: float, height: float):
    # Symbol previews can request tiny envelopes; shrink the hardware together to keep it closed.
    scale = min(1.0, width / (96 * INCH_M), depth / (4 * INCH_M), height / (4 * INCH_M))
    strokes, parts = _tapestry_rod_clips(width / scale, depth / scale, height / scale)
    if scale == 1:
        return strokes, parts
    scaled_parts = []
    for part in parts:
        scaled = {**part, "center": tuple(value * scale for value in part["center"]),
                  "size": tuple(value * scale for value in part["size"])}
        if "mesh" in part:
            scaled["mesh"] = {**part["mesh"], "positions": tuple(
                tuple(value * scale for value in vertex) for vertex in part["mesh"]["positions"])}
        scaled_parts.append(scaled)
    return tuple({**stroke, "points": tuple((x * scale, y * scale)
                                            for x, y in stroke["points"])}
                 for stroke in strokes), tuple(scaled_parts)
