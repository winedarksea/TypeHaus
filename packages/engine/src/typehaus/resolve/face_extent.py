"""A wall layer's own extent along its wall: stations, framing-side span and billed run.

One reader for every consumer that used to take the node axis: the cladding trim frame,
the sheet layout and the envelope takeoff all measure a layer off its resolved polygon,
so a through corner panel is longer than the axis and a branch's board stops short.
"""

from __future__ import annotations

import math

from shapely.geometry import Polygon

from typehaus.resolve.framing.course_ends import band_extent
from typehaus.resolve.sheathing_corner import layer_run_m

_FACE_INSET = 0.45  # of thickness: read a face just inside the band, clear of its edge


def axis_direction(wall) -> tuple[float, float] | None:
    """Unit vector from the wall's first axis point to its last (None for a point)."""
    (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
    run = math.hypot(bx - ax, by - ay)
    return None if run < 1e-6 else ((bx - ax) / run, (by - ay) / run)


def face_span(wall, layer) -> tuple[float, float] | None:
    """``(lo, hi)`` absolute stations (``x*dx + y*dy``) of ``layer``'s polygon on its axis."""
    d = axis_direction(wall)
    if d is None or not layer.polygon:
        return None
    along = [x * d[0] + y * d[1] for x, y in layer.polygon]
    return min(along), max(along)


def framing_side_span(wall, layer, toward) -> tuple[float, float] | None:
    """``(lo, hi)`` along-stations from the axis start of ``layer``'s face toward ``toward``.

    ``toward`` is the layer polygon (or any ring) the face looks at — the framing for a
    sheathing layer. A mitred band is shorter on that face than its outer one, and a panel
    is laid on the framing, so the layout reads this face, not the polygon's bounding span.
    """
    d = axis_direction(wall)
    if d is None or len(layer.polygon) < 3 or len(toward) < 3:
        return None
    n = (-d[1], d[0])
    p0 = wall.axis[0]

    def offset(ring) -> float:
        return sum((x - p0[0]) * n[0] + (y - p0[1]) * n[1] for x, y in ring) / len(ring)

    centre = offset(layer.polygon)
    side = 1.0 if offset(toward) > centre else -1.0
    shift = centre + side * layer.thickness_m * _FACE_INSET
    start = (p0[0] + n[0] * shift, p0[1] + n[1] * shift)
    axis_len = math.hypot(wall.axis[-1][0] - p0[0], wall.axis[-1][1] - p0[1])
    return band_extent(layer.polygon, start, d, axis_len, clamp=False)


def face_run_m(layer, axis_run: float, wall=None) -> float:
    """A layer's billed run: a board by area / thickness, a coating by half its ring.

    A cavity fill shares its host's polygon but not its depth, so it reads the host's run.
    """
    if getattr(layer, "is_cavity", False) and wall is not None:
        layer = next((h for h in wall.layers if h.name == layer.cavity_host), layer)
        if layer.is_cavity:
            return axis_run
    if layer.thickness_m > 0.0:
        return layer_run_m(layer, axis_run)
    half = Polygon(layer.polygon).length / 2.0 if len(layer.polygon) >= 3 else 0.0
    return half if half > 0.0 else axis_run
