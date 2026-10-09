"""A truss attic's loose fill, cut to the roof it lies under.

The blow is level across the field and tapers at each eave, where the roof plane comes down
to the heel. A flat prism at the fill's settled depth ignores that and, under a standard
heel, pokes through the top chords. Here the section is the fill's depth capped by the deck
plane less the vent space IRC R806.3 keeps open over the baffle, swept along the ridge.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedModel, Ring, SolidSweep
from typehaus.resolve.roof_geometry import (
    roof_height_at,
    roof_ridge_coordinate,
    roof_slope_factor,
)
from typehaus.resolve.sweep import leg_frame

#: IRC R806.3: at least 1" of air between the insulation and the deck at the vent, square
#: to the deck.
VENT_SPACE_M = inch(1).meters
#: Below this a section point is no fill at all; keep the ring non-degenerate.
_MIN_DEPTH_M = 0.005


def attic_fill_sweep(model: ResolvedModel, roof_tag: str, outline: Ring, base_m: float,
                     depth_m: float) -> SolidSweep | None:
    """The fill as one sweep along the ridge, or ``None`` where it cannot be read.

    ``base_m`` is where the fill sits (the ceiling top), ``depth_m`` its settled depth.
    Only a gable over a rectangular ceiling qualifies: anything else keeps the flat prism,
    which over-reads rather than inventing a shape.
    """
    roof = next((r for r in model.roofs if r.tag == roof_tag), None)
    if roof is None or roof.ridge_direction not in ("x", "y"):
        return None
    ridge = roof_ridge_coordinate(roof)
    if ridge is None:
        return None
    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    box = (min(xs), min(ys), max(xs), max(ys))
    area = (box[2] - box[0]) * (box[3] - box[1])
    if area <= 0 or abs(Polygon(outline).area - area) > 1e-3 * area:
        return None
    along = 1 if roof.ridge_direction == "y" else 0
    across = 1 - along
    lo, hi = box[across], box[across + 2]
    centre = (lo + hi) / 2.0

    def point(s: float, t: float) -> tuple[float, float]:
        p = [0.0, 0.0]
        p[across], p[along] = s, t
        return (p[0], p[1])

    mid_t = (box[along] + box[along + 2]) / 2.0

    gap_m = VENT_SPACE_M * roof_slope_factor(roof)

    def room_for_fill(s: float) -> float:
        return roof_height_at(roof, point(s, mid_t)) - gap_m - base_m

    # Stations across the span: both edges, where each slope meets the full depth, the ridge.
    stations = {lo, hi}
    if lo < ridge < hi:
        stations.add(ridge)
    for edge in (lo, hi):
        end = ridge if lo < ridge < hi else (hi if edge == lo else lo)
        h0, h1 = room_for_fill(edge), room_for_fill(end)
        if h0 < depth_m < h1:
            stations.add(edge + (end - edge) * (depth_m - h0) / (h1 - h0))
    section = [(s, max(_MIN_DEPTH_M, min(depth_m, room_for_fill(s)))) for s in sorted(stations)]

    start = (*point(centre, box[along]), base_m)
    end = (*point(centre, box[along + 2]), base_m)
    right, _up = leg_frame((end[0] - start[0], end[1] - start[1], 0.0))
    sign = 1.0 if right[across] > 0 else -1.0
    top = sorted((sign * (s - centre), h) for s, h in section)
    # Counter-clockwise in (u, v), which is how the sweep kernel faces its sides outward.
    ring = [(top[0][0], 0.0), (top[-1][0], 0.0), *reversed(top)]
    return SolidSweep(path=(start, end), profile=tuple(ring))
