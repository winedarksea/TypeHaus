"""Mats in horizontal pours: strip footings, pads, slabs — and the ribs of a ribbed slab.

Frame (decision D7): a strip footing's ``y`` runs along its wall and ``x`` across it; a pad
or slab uses plan X/Y. A ``-x`` role is a bar RUNNING in x, spaced along y by the D3 fencepost
across the region, and each bar is the part of its line inside ``outline − voids`` shrunk
by cover — so a void splits a bar and an L-shaped slab shortens one. Bottom roles stack up
from the soffit in authored order, top roles down from the top.

A ribbed slab (``ReinforcementSpec.ribs``) holds its mat in the cap: the cap is the assembly's
STRUCTURE layer at the top of the solid, and each rib hangs ``ribs.depth`` below it. ``rib``
bars are ``count`` per rib at the rib bottom; ``stirrups`` are closed loops from the rib
bottom to the cap top, within ``zone`` of each rib end.
"""

from __future__ import annotations

from shapely.geometry import LineString, Polygon

from typehaus.model.rebar import BARS
from typehaus.resolve.rebar.beams import _spread, fence
from typehaus.resolve.rebar.stock import Sink

_IN = 0.0254
MAT_ROLES = ("bottom-x", "bottom-y", "top-x", "top-y")


class _Frame:
    def __init__(self, ey: tuple[float, float]) -> None:
        self.ey = ey
        self.ex = (ey[1], -ey[0])

    def local(self, p) -> tuple[float, float]:
        return (p[0] * self.ex[0] + p[1] * self.ex[1], p[0] * self.ey[0] + p[1] * self.ey[1])

    def world(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        return (x * self.ex[0] + y * self.ey[0], x * self.ex[1] + y * self.ey[1], z)

    def along(self, runs_x: bool) -> tuple[float, float, float]:
        d = self.ex if runs_x else self.ey
        return (d[0], d[1], 0.0)


def _segments(region, runs_x: bool, q: float, lo: float, hi: float):
    line = LineString([(lo, q), (hi, q)] if runs_x else [(q, lo), (q, hi)])
    hit = region.intersection(line)
    parts = getattr(hit, "geoms", [hit])
    for part in parts:
        if part.is_empty or part.geom_type != "LineString" or part.length < 3 * _IN:
            continue
        (x0, y0), (x1, y1) = part.coords[0], part.coords[-1]
        yield (x0, y0), (x1, y1)


def lay_mat(sink: Sink, spec, solid, cover: float, *, ey=(0.0, 1.0),
            cap_thickness: float | None = None) -> None:
    frame = _Frame(ey)
    ribs = spec.ribs
    concrete = Polygon([frame.local(p) for p in solid.outline],
                       [[frame.local(p) for p in v] for v in solid.voids]).buffer(0)
    region = concrete.buffer(-cover, join_style="mitre")
    if region.is_empty:
        return
    minx, miny, maxx, maxy = region.bounds
    z_top = solid.z1_m
    z_bot = solid.z0_m if cap_thickness is None or ribs is None else z_top - cap_thickness
    acc = {"bottom": 0.0, "top": 0.0}
    for entry in spec.bars:
        if entry.role not in MAT_ROLES or entry.spacing is None:
            continue
        db = BARS[entry.bar].diameter_in * _IN
        level, axis = entry.role.split("-")
        runs_x = axis == "x"
        q_lo, q_hi = (miny, maxy) if runs_x else (minx, maxx)
        lo, hi = (minx - 1.0, maxx + 1.0) if runs_x else (miny - 1.0, maxy + 1.0)
        turn = (0.0, 0.0, 1.0) if level == "bottom" else (0.0, 0.0, -1.0)
        hooks = (turn if entry.hooks and "start" in entry.hooks else None,
                 turn if entry.hooks and "end" in entry.hooks else None)
        for _layer in range(max(1, entry.layers)):
            z = (z_bot + cover + acc["bottom"] + db / 2 if level == "bottom"
                 else z_top - cover - acc["top"] - db / 2)
            acc[level] += db
            for q in fence(q_lo + db / 2, q_hi - db / 2, entry.spacing.meters):
                for a, b in _segments(region, runs_x, q, lo, hi):
                    sink.straight(entry, frame.world(*a, z), frame.world(*b, z),
                                  hook_dirs=hooks, lap_offset=frame.along(not runs_x),
                                  top_cast=level == "top" and z - solid.z0_m > 12 * _IN)
    if ribs is not None:
        _lay_ribs(sink, spec, concrete, region, frame, cover, z_bot, z_top)


def _lay_ribs(sink: Sink, spec, concrete, region, frame: _Frame, cover: float,
              cap_bottom: float, z_top: float) -> None:
    ribs = spec.ribs
    runs_x = ribs.direction == "x"
    minx, miny, maxx, maxy = concrete.bounds
    q_min, q_max = (miny, maxy) if runs_x else (minx, maxx)
    lo, hi = (minx - 1.0, maxx + 1.0) if runs_x else (miny - 1.0, maxy + 1.0)
    rib_bottom = cap_bottom - ribs.depth.meters
    half = ribs.width.meters / 2.0
    stir = next((e for e in spec.bars if e.role == "stirrups"), None)
    dst = BARS[stir.bar].diameter_in * _IN if stir else 0.0
    centres: list[float] = []
    q = q_min + ribs.offset.meters
    while q < q_max - half:
        if q > q_min + half:
            centres.append(q)
        q += ribs.spacing.meters
    for q in centres:
        for a, b in _segments(region, runs_x, q, lo, hi):
            s_a, s_b = (a[0], b[0]) if runs_x else (a[1], b[1])
            for entry in spec.bars:
                db = BARS[entry.bar].diameter_in * _IN
                if entry.role == "rib" and entry.count:
                    z = rib_bottom + cover + dst + db / 2
                    for t in _spread(q - half + cover + dst + db / 2,
                                     q + half - cover - dst - db / 2, entry.count):
                        p0 = (s_a, t) if runs_x else (t, s_a)
                        p1 = (s_b, t) if runs_x else (t, s_b)
                        sink.straight(entry, frame.world(*p0, z), frame.world(*p1, z),
                                      lap_offset=frame.along(not runs_x))
                elif entry.role == "stirrups" and entry.spacing is not None:
                    positions = fence(s_a, s_b, entry.spacing.meters)
                    if entry.zone is not None:
                        zone = entry.zone.meters
                        positions = [p for p in positions
                                     if p - s_a <= zone + 1e-6 or s_b - p <= zone + 1e-6]
                    t0, t1 = q - half + cover + db / 2, q + half - cover - db / 2
                    zb, zt = rib_bottom + cover + db / 2, z_top - cover - db / 2
                    for s in positions:
                        corners = [(s, t0, zb), (s, t1, zb), (s, t1, zt), (s, t0, zt)]
                        sink.loop(entry, [frame.world(*((c[0], c[1]) if runs_x
                                                         else (c[1], c[0])), c[2])
                                          for c in corners])
