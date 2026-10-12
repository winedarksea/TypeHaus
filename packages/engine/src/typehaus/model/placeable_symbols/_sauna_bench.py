"""Slatted sauna platform on posts: the floor remains ventilated and serviceable."""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import box, line, rect
from typehaus.quantities import M_PER_IN

DECK_THICKNESS_IN = 1.5
POST_WIDTH_IN = 2.5
POST_END_INSET_IN = 6.0
POST_DEPTH_INSET_IN = 2.5
MAXIMUM_SUPPORT_SPAN_IN = 48.0
RAIL_HEIGHT_IN = 3.5
LIGHT_RAIL_TOP_IN = 16.0
LIGHT_RAIL_THICKNESS_IN = 0.75
LIGHT_RAIL_HEIGHT_IN = 1.5
SLAT_WIDTH_IN = 3.0
SLAT_GAP_IN = 0.25


def sauna_open_bench(width: float, depth: float, height: float) -> Geometry:
    """Posts inset from the ends keep a low wall register clear; no full-depth leg panels."""
    top = min(DECK_THICKNESS_IN * M_PER_IN, height / 4)
    post = min(POST_WIDTH_IN * M_PER_IN, width / 8, depth / 8)
    end_inset = max(post / 2, min(POST_END_INSET_IN * M_PER_IN, width / 4))
    depth_inset = max(post / 2, min(POST_DEPTH_INSET_IN * M_PER_IN, depth / 4))
    support_span = width - 2 * end_inset
    count = max(2, math.ceil(support_span / (MAXIMUM_SUPPORT_SPAN_IN * M_PER_IN)) + 1)
    rail_height = min(RAIL_HEIGHT_IN * M_PER_IN, (height - top) / 2)
    parts = []
    support_stations = [-support_span / 2 + i * support_span / (count - 1)
                        for i in range(count)]
    for sign in (-1, 1):
        y = sign * (depth / 2 - depth_inset)
        parts.append(box(0, y, height - top - rail_height, height - top,
                         width, post, "sauna-wood-dark"))
        for x in support_stations:
            parts.append(box(x, y, 0, height - top, post, post, "sauna-wood-dark"))
    # Boards run along the bench: transverse bearers carry every board to the post rows.
    for x in support_stations:
        parts.append(box(x, 0, height - top - rail_height, height - top,
                         post, depth, "sauna-wood-dark"))
    # Low perimeter rails give under-bench tape a real mounting face at 16" AFF.
    light_top = min(LIGHT_RAIL_TOP_IN * M_PER_IN, height - top - rail_height)
    light_bottom = max(0, light_top - LIGHT_RAIL_HEIGHT_IN * M_PER_IN)
    light_depth = min(LIGHT_RAIL_THICKNESS_IN * M_PER_IN, post)
    for sign in (-1, 1):
        parts.append(box(0, sign * (depth / 2 - light_depth / 2), light_bottom,
                         light_top, width, light_depth, "sauna-wood-dark"))
        parts.append(box(sign * (width / 2 - light_depth / 2), 0, light_bottom,
                         light_top, light_depth, depth, "sauna-wood-dark"))
        parts.append(box(0, sign * (depth / 2 - depth_inset), light_bottom,
                         light_top, width, post, "sauna-wood-dark"))
    # Stretchers connect the perimeter mounting rails to inset posts rather than float.
    for x in support_stations:
        parts.append(box(x, 0, light_bottom, light_top, post, depth, "sauna-wood-dark"))
    slat_count = max(1, math.ceil(depth / ((SLAT_WIDTH_IN + SLAT_GAP_IN) * M_PER_IN)))
    pitch = depth / slat_count
    gap = pitch * SLAT_GAP_IN / (SLAT_WIDTH_IN + SLAT_GAP_IN)
    strokes = [rect(0, 0, width, depth, fill="sauna-wood")]
    # Panel joints land on bearers, letting the drain-side deck lift without dismantling
    # a full-length run. The ordinary slat gap also gives the joint room to drain/dry.
    panel_edges = [-width / 2, *support_stations[1:-1], width / 2]
    for index in range(slat_count):
        y = -depth / 2 + (index + 0.5) * pitch
        for panel_index, (start, end) in enumerate(zip(panel_edges, panel_edges[1:], strict=False)):
            left = start + (gap / 2 if panel_index else 0)
            right = end - (gap / 2 if panel_index < len(panel_edges) - 2 else 0)
            parts.append(box((left + right) / 2, y, height - top, height,
                             right - left, pitch - gap, "sauna-wood"))
        strokes.append(line((-width / 2, y), (width / 2, y)))
    for joint in panel_edges[1:-1]:
        strokes.append(line((joint, -depth / 2), (joint, depth / 2)))
    return tuple(strokes), tuple(parts)
