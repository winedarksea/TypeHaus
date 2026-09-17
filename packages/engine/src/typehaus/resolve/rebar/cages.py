"""Column cages and L-dowels.

A round column (a many-sided outline) takes its ``count`` verticals on a circle of radius
``R − cover − d_tie − d_v/2`` and circular ties of radius ``R − cover − d_tie/2``, each closed
with two 135° seismic hooks and a 6" overlap (decision D5). A rectangular column takes
rectangular ties and verticals shared out around the tie's inside corners. Ties sit at
``s/2 … H − s/2`` by the D3 fencepost.

A dowel (decision D6) is an L: a standard 90° foot resting on the base pour's bottom steel,
up through the base, and a lap above its top — at every vertical the host lays out. The base
is the footing under a wall, or the pad, footing or wall a post is ``supported_by``. No base,
no dowel; ``integrity.reinforcement_layout`` reports the role that placed nothing.
"""

from __future__ import annotations

import math

from typehaus.model.rebar import BARS
from typehaus.resolve.rebar import detailing as det
from typehaus.resolve.rebar.beams import fence
from typehaus.resolve.rebar.stock import Sink

_IN = 0.0254
_TIE_FACETS = 24


def is_round(outline) -> bool:
    return len(outline) > 8


def lay_column(sink: Sink, spec, solid, cover: float) -> list[tuple[float, float, float]]:
    """Lays the cage; returns the verticals' ``(x, y, z_bottom)`` for any dowels."""
    xs = [p[0] for p in solid.outline]
    ys = [p[1] for p in solid.outline]
    cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
    hx, hy = (max(xs) - min(xs)) / 2.0, (max(ys) - min(ys)) / 2.0
    tie = next((e for e in spec.bars if e.role == "ties"), None)
    dt = BARS[tie.bar].diameter_in * _IN if tie else 0.0
    z0, z1 = solid.z0_m, solid.z1_m
    feet: list[tuple[float, float, float]] = []
    round_ = is_round(solid.outline)
    for entry in spec.bars:
        db = BARS[entry.bar].diameter_in * _IN
        if entry.role == "vertical" and entry.count:
            for x, y in _vertical_positions(entry.count, cx, cy, hx, hy, cover + dt + db / 2,
                                            round_):
                feet.append((x, y, z0 + cover))
                sink.straight(entry, (x, y, z0 + cover), (x, y, z1 - cover),
                              lap_offset=(1.0, 0.0, 0.0))
        elif entry.role == "ties" and entry.spacing is not None:
            s = entry.spacing.meters
            for z in fence(z0 + s / 2, z1 - s / 2, s):
                if round_:
                    r = min(hx, hy) - cover - db / 2
                    pts = [(cx + r * math.cos(2 * math.pi * k / _TIE_FACETS),
                            cy + r * math.sin(2 * math.pi * k / _TIE_FACETS), z)
                           for k in range(_TIE_FACETS)]
                    sink.loop(entry, pts, overlap_in=det.CIRCULAR_TIE_OVERLAP_IN,
                              perimeter_m=2 * math.pi * r)
                else:
                    ix, iy = hx - cover - db / 2, hy - cover - db / 2
                    sink.loop(entry, [(cx - ix, cy - iy, z), (cx + ix, cy - iy, z),
                                      (cx + ix, cy + iy, z), (cx - ix, cy + iy, z)])
    return feet


def _vertical_positions(count: int, cx: float, cy: float, hx: float, hy: float,
                        inset: float, round_: bool) -> list[tuple[float, float]]:
    if round_:
        r = min(hx, hy) - inset
        return [(cx + r * math.cos(math.pi / 4 + 2 * math.pi * k / count),
                 cy + r * math.sin(math.pi / 4 + 2 * math.pi * k / count))
                for k in range(count)]
    ix, iy = hx - inset, hy - inset
    corners = [(cx - ix, cy - iy), (cx + ix, cy - iy), (cx + ix, cy + iy), (cx - ix, cy + iy)]
    if count <= 4:
        return corners[:count]
    # The rest round the perimeter, evenly by arc length between the corners.
    perimeter = [(corners[i], corners[(i + 1) % 4]) for i in range(4)]
    total = 4 * (ix + iy)
    out = list(corners)
    for k in range(count - 4):
        d = total * (k + 0.5) / (count - 4)
        for a, b in perimeter:
            seg = math.dist(a, b)
            if d <= seg:
                f = d / seg if seg else 0.0
                out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
                break
            d -= seg
    return out


def lay_dowels(sink: Sink, entry, points: list[tuple[float, float]],
               base_bottom: float, base_top: float, cover: float,
               foot_dir: tuple[float, float], *, compression: bool = False) -> None:
    """One L per plan point: foot at the base's bottom steel, lap above ``base_top``."""
    db = BARS[entry.bar].diameter_in * _IN
    lap = sink.lap_m(entry.bar, compression=compression)
    z_foot = base_bottom + cover + db / 2
    if base_top - z_foot < 3 * _IN:
        return
    _, bend, extension = det.hook_geometry_in(entry.bar, "std90")
    leg = (bend / 2.0 + BARS[entry.bar].diameter_in + extension) * _IN
    hook = det.hook_allowance_in(entry.bar, "std90") * _IN
    for x, y in points:
        foot = (x + foot_dir[0] * leg, y + foot_dir[1] * leg, z_foot)
        sink.polyline(entry, [foot, (x, y, z_foot), (x, y, base_top + lap)],
                      placed_m=base_top - z_foot, lap_m=lap, hook_m=hook,
                      hook_kinds=("std90",))
