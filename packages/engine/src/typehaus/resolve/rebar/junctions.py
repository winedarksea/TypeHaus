"""Horizontal continuity across a wall node: corner L bars and splice bars.

Every wall's horizontals stop straight at cover (``walls.py``); this lays the bars that
carry them through the node, one rule for every kind:

* **collinear** (one run modelled as two walls): a straight splice bar per row and face,
  lapping each wall's bars by a full lap.
* **L corner**: an L bar per row on each face — outer with outer, inner with inner — whose
  legs run a lap past each wall's own bar end.
* **T**: the stem's rows, per face, turn along the through wall's FAR face and run a lap
  along it; the through wall's own bars are continuous and need nothing.

The bars sit one bar diameter above the row they lap (a contact lap) — or below it, or a
further diameter out, where a bar from the node at the wall's other end already lies there
(a short wall between two nodes). They belong to the first wall by tag, or to the stem.
Rows are kept only where the other wall's concrete is.
Laps are the wall lap (``detailing.wall_lap_in``).
"""

from __future__ import annotations

import math

from typehaus.model.rebar import BARS
from typehaus.resolve.rebar.walls import _s_range_at

_IN = 0.0254
_PARALLEL = 0.95


def lay_junction_bars(junctions, steel: dict, sinks: dict) -> None:
    """``steel``: wall tag → ``WallSteel``; ``sinks``: wall tag → ``Sink``."""
    placed: list = []
    for j in junctions:
        incs = sorted((i for i in j.incidents if i.wall_tag in steel and steel[i.wall_tag].lines),
                      key=lambda i: i.wall_tag)
        for ia in range(len(incs)):
            for ib in range(ia + 1, len(incs)):
                a, b = incs[ia], incs[ib]
                if a.z1_m <= b.z0_m or b.z1_m <= a.z0_m:
                    continue
                dot = a.direction[0] * b.direction[0] + a.direction[1] * b.direction[1]
                if dot < -_PARALLEL:
                    _splice(j, a, b, steel, sinks, placed)
                elif abs(dot) < _PARALLEL:
                    stem, through = _stem_of(j, a, b)
                    if through is None:
                        _corner(j, a, b, steel, sinks, placed)
                    else:
                        _tee(j, stem, through, steel, sinks, placed)


def _stem_of(j, a, b):
    if a.wall_tag in j.through_walls and b.wall_tag not in j.through_walls:
        return b, a
    if b.wall_tag in j.through_walls and a.wall_tag not in j.through_walls:
        return a, b
    return a, None


def _line_geom(ws, t: float):
    f = ws.frame
    return f.world(0.0, t, 0.0)[:2], f.u


def _intersect(p, u, q, v):
    den = u[0] * v[1] - u[1] * v[0]
    if abs(den) < 1e-9:
        return None
    k = ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / den
    return (p[0] + u[0] * k, p[1] + u[1] * k)


def _bar_end(ws, t: float, node, direction=None):
    """The wall's own bar end on line ``t`` nearest the node, in plan."""
    rng = _s_range_at(ws.layer.polygon, ws.frame, t)
    if rng is None:
        return None
    ends = [ws.frame.world(rng[0] + ws.cover, t, 0.0)[:2],
            ws.frame.world(rng[1] - ws.cover, t, 0.0)[:2]]
    return min(ends, key=lambda p: math.dist(p, node))


def _mid_and_half(ws):
    return (ws.frame.t0 + ws.frame.t1) / 2.0, (ws.frame.t1 - ws.frame.t0) / 2.0


def _side_normal(ws, t: float):
    """The plan normal pointing from the wall's centre toward line ``t``'s face."""
    mid, _ = _mid_and_half(ws)
    k = 1.0 if t >= mid else -1.0
    return (ws.frame.n[0] * k, ws.frame.n[1] * k)


def _matching_t(ws, inset: float, normal) -> float:
    """``t`` on the face of ``ws`` whose outward normal is ``normal``, ``inset`` inside it."""
    mid, half = _mid_and_half(ws)
    k = 1.0 if normal[0] * ws.frame.n[0] + normal[1] * ws.frame.n[1] >= 0 else -1.0
    return mid + k * (half - inset)


def _inset(ws, t: float) -> float:
    mid, half = _mid_and_half(ws)
    return half - abs(t - mid)


def _rows_inside(zs, other, at, cover: float):
    lo = other.frame.z0 + cover
    top = other.top_at(at) - cover
    return [z for z in zs if lo <= z <= top]


def _s_of(ws, p) -> float:
    f = ws.frame
    return (p[0] - f.origin[0]) * f.u[0] + (p[1] - f.origin[1]) * f.u[1]


def _seg_dist(p1, q1, p2, q2) -> float:
    """Closest distance between segments ``p1q1`` and ``p2q2`` (3-D)."""
    d1 = [q1[i] - p1[i] for i in range(3)]
    d2 = [q2[i] - p2[i] for i in range(3)]
    r = [p1[i] - p2[i] for i in range(3)]
    a, e, f = (sum(x * x for x in d1), sum(x * x for x in d2), sum(d2[i] * r[i] for i in range(3)))
    c, b = sum(d1[i] * r[i] for i in range(3)), sum(d1[i] * d2[i] for i in range(3))
    den = a * e - b * b
    s = min(1.0, max(0.0, (b * f - c * e) / den)) if den > 1e-12 and a > 1e-12 else 0.0
    t = (b * s + f) / e if e > 1e-12 else 0.0
    if t < 0.0 or t > 1.0:
        t = min(1.0, max(0.0, t))
        s = min(1.0, max(0.0, (b * t - c) / a)) if a > 1e-12 else 0.0
    return math.dist([p1[i] + d1[i] * s for i in range(3)], [p2[i] + d2[i] * t for i in range(3)])


def _box(pts, pad: float):
    return (min(p[0] for p in pts) - pad, min(p[1] for p in pts) - pad,
            min(p[2] for p in pts) - pad, max(p[0] for p in pts) + pad,
            max(p[1] for p in pts) + pad, max(p[2] for p in pts) + pad)


def _clear(pts, db: float, placed) -> bool:
    box = _box(pts, db)
    for other, odb, obox in placed:
        if any(box[i] > obox[i + 3] or obox[i] > box[i + 3] for i in range(3)):
            continue
        for i in range(len(pts) - 1):
            for k in range(len(other) - 1):
                if _seg_dist(pts[i], pts[i + 1], other[k], other[k + 1]) < (db + odb) / 2 - 1e-4:
                    return False
    return True


def _emit(sink, entry, plan_pts, z: float, lap: float, note: str, placed) -> None:
    db = BARS[entry.bar].diameter_in * _IN
    pts = [(x, y, z + db) for x, y in plan_pts]
    for k in (1, -1, 2, -2):
        trial = [(x, y, z + k * db) for x, y in plan_pts]
        if _clear(trial, db, placed):
            pts = trial
            break
    placed.append((pts, db, _box(pts, db)))
    total = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    sink.polyline(entry, pts, placed_m=max(0.0, total - 2 * lap), hook_m=0.0, hook_kinds=(),
                  lap_m=min(total, 2 * lap), note=note)


def _splice(j, a, b, steel, sinks, placed) -> None:
    wa, wb = steel[a.wall_tag], steel[b.wall_tag]
    sink = sinks[a.wall_tag]
    for entry, t, zs in wa.lines:
        pa = _bar_end(wa, t, j.point, a.direction)
        if pa is None:
            continue
        # b's line on the same side: the parallel line through the same plan offset.
        normal = _side_normal(wa, t)
        tb = _matching_t(wb, _inset(wa, t), normal)
        pb = _bar_end(wb, tb, j.point, b.direction)
        if pb is None:
            continue
        for z in _rows_inside(zs, wb, _s_of(wb, j.point), wb.cover):
            lap = sink.lap_m(entry.bar, top_cast=z - wa.frame.z0 > 12 * _IN)
            ea = (pa[0] + a.direction[0] * lap, pa[1] + a.direction[1] * lap)
            eb = (pb[0] + b.direction[0] * lap, pb[1] + b.direction[1] * lap)
            _emit(sink, entry, [ea, eb], z, lap, f"splice bar across {j.node_tag}", placed)


def _leg_end(corner, direction, own_end, lap):
    reach = max(0.0, (own_end[0] - corner[0]) * direction[0]
                + (own_end[1] - corner[1]) * direction[1])
    return (corner[0] + direction[0] * (reach + lap), corner[1] + direction[1] * (reach + lap))


def _corner(j, a, b, steel, sinks, placed) -> None:
    wa, wb = steel[a.wall_tag], steel[b.wall_tag]
    sink = sinks[a.wall_tag]
    for entry, t, zs in wa.lines:
        normal = _side_normal(wa, t)
        # Outer pairs with outer: a's face points away from b's interior, and b's face must
        # point away from a's.
        outer = normal[0] * b.direction[0] + normal[1] * b.direction[1] < 0
        nb = (-a.direction[0], -a.direction[1]) if outer else a.direction
        tb = _matching_t(wb, _inset(wa, t), nb)
        corner = _intersect(*_line_geom(wa, t), *_line_geom(wb, tb))
        pa, pb = _bar_end(wa, t, j.point, a.direction), _bar_end(wb, tb, j.point, b.direction)
        if corner is None or pa is None or pb is None:
            continue
        for z in _rows_inside(zs, wb, _s_of(wb, j.point), wb.cover):
            lap = sink.lap_m(entry.bar, top_cast=z - wa.frame.z0 > 12 * _IN)
            pts = [_leg_end(corner, a.direction, pa, lap), corner,
                   _leg_end(corner, b.direction, pb, lap)]
            _emit(sink, entry, pts, z, lap, f"corner bar at {j.node_tag}", placed)


def _tee(j, stem, through, steel, sinks, placed) -> None:
    ws, wt = steel[stem.wall_tag], steel[through.wall_tag]
    sink = sinks[stem.wall_tag]
    far = (-stem.direction[0], -stem.direction[1])
    for entry, t, zs in ws.lines:
        tt = _matching_t(wt, _inset(ws, t), far)
        corner = _intersect(*_line_geom(ws, t), *_line_geom(wt, tt))
        ps = _bar_end(ws, t, j.point, stem.direction)
        if corner is None or ps is None:
            continue
        side = _side_normal(ws, t)
        u = wt.frame.u
        along = u if side[0] * u[0] + side[1] * u[1] >= 0 else (-u[0], -u[1])
        for z in _rows_inside(zs, wt, _s_of(wt, j.point), wt.cover):
            lap = sink.lap_m(entry.bar, top_cast=z - ws.frame.z0 > 12 * _IN)
            pts = [_leg_end(corner, stem.direction, ps, lap), corner,
                   (corner[0] + along[0] * lap, corner[1] + along[1] * lap)]
            _emit(sink, entry, pts, z, lap,
                  f"corner bar into {through.wall_tag} at {j.node_tag}", placed)
