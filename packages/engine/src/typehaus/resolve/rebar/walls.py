"""Wall steel: verticals and horizontals in the plane of the concrete STRUCTURE layer.

Frame: ``s`` along the axis from its start, ``t`` along the left normal, ``z`` absolute.
Bars stay inside the concrete layer's own polygon (so a mitred corner is honoured), inside
its band (``Layer.extent``) and under a raked top. Openings split the bars that cross them
at cover; no trim bars are added — the schema carries none. Horizontals sit inboard of
the verticals on the same face; where both are centred they straddle the centreline.
Horizontals stop straight at cover: ``junctions.py`` laps them across a node with separate
corner and splice bars. A vertical authored ``hooks=("start",)`` runs continuous from the
pour below — its foot on that pour's bottom mat, turned across the wall — instead of a
lapped dowel. Faces follow the assembly's layer order — layer 0 is the interior, which is
the side ``resolve/orientation.wall_outward_sign`` already put there.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from typehaus.model.enums import LayerFunction
from typehaus.model.rebar import BARS
from typehaus.resolve.rebar import detailing as det
from typehaus.resolve.rebar.beams import BEAM_ROLES, LinearFrame, fence, lay_beam
from typehaus.resolve.rebar.stock import Sink

_IN = 0.0254
_MIN_BAR_M = 3 * _IN
_ROW_FROM_EDGE_M = 6 * _IN


@dataclass(frozen=True)
class WallBase:
    """The pour a wall stands on: its top, and where a foot rests (atop its bottom mat)."""

    top: float
    rest: float


@dataclass
class WallSteel:
    """What ``junctions.py`` needs of a laid wall: its frame and each horizontal line."""

    frame: LinearFrame
    layer: object
    top_at: object
    cover: float
    lines: list = field(default_factory=list)  # (entry, t, zs)


def structure_layer(wall):
    return next((ly for ly in wall.layers
                 if ly.function == LayerFunction.STRUCTURE.value and not ly.is_cavity), None)


def wall_frame(wall, layer) -> tuple[LinearFrame, float]:
    """The layer's frame, and the sign of ``t`` that points to the EXTERIOR face."""
    (ax, ay), (bx, by) = wall.axis
    d = math.hypot(bx - ax, by - ay) or 1.0
    u = ((bx - ax) / d, (by - ay) / d)
    n = (-u[1], u[0])

    def tc(ly) -> float:
        pts = list(ly.polygon)
        return sum((p[0] - ax) * n[0] + (p[1] - ay) * n[1] for p in pts) / max(1, len(pts))

    pts = list(layer.polygon)
    ss = [(p[0] - ax) * u[0] + (p[1] - ay) * u[1] for p in pts]
    ts = [(p[0] - ax) * n[0] + (p[1] - ay) * n[1] for p in pts]
    z0, z1 = layer.band(wall)
    tops = [z for z in (wall.top_z0_m, wall.top_z1_m) if z is not None]
    if tops:
        z1 = min(z1, max(tops))
    frame = LinearFrame((ax, ay), u, n, min(ss), max(ss), min(ts), max(ts), z0, z1)
    depth = list(wall.depth_layers())
    i = depth.index(layer) if layer in depth else 0
    sign = 1.0
    if i + 1 < len(depth):
        sign = 1.0 if tc(depth[i + 1]) >= tc(layer) else -1.0
    elif i > 0:
        sign = -1.0 if tc(depth[i - 1]) >= tc(layer) else 1.0
    return frame, sign


def _s_range_at(layer_ring, frame: LinearFrame, t: float) -> tuple[float, float] | None:
    """Where the line at offset ``t`` crosses the (convex) layer polygon, in ``s``."""
    pts = [((p[0] - frame.origin[0]) * frame.u[0] + (p[1] - frame.origin[1]) * frame.u[1],
            (p[0] - frame.origin[0]) * frame.n[0] + (p[1] - frame.origin[1]) * frame.n[1])
           for p in layer_ring]
    hits: list[float] = []
    for i, (s0, t0) in enumerate(pts):
        s1, t1 = pts[(i + 1) % len(pts)]
        if (t0 - t) * (t1 - t) <= 0.0 and abs(t1 - t0) > 1e-12:
            hits.append(s0 + (s1 - s0) * (t - t0) / (t1 - t0))
    return (min(hits), max(hits)) if hits else None


def lay_wall(sink: Sink, spec, wall, cover: float, openings,
             base: WallBase | None = None) -> WallSteel | None:
    layer = structure_layer(wall)
    if layer is None:
        return None
    frame, ext = wall_frame(wall, layer)
    top_at = _top_fn(wall, frame)
    steel = WallSteel(frame, layer, top_at, cover)
    beam_entries = [e for e in spec.bars if e.role in BEAM_ROLES]
    if beam_entries:
        side = [e for e in spec.bars if e.role == "horizontal"]
        lay_beam(sink, beam_entries + side, frame, cover)
        return steel
    vert = next((e for e in spec.bars if e.role == "vertical"), None)
    horiz = next((e for e in spec.bars if e.role == "horizontal"), None)
    dv = BARS[vert.bar].diameter_in * _IN if vert else 0.0
    dh = BARS[horiz.bar].diameter_in * _IN if horiz else 0.0
    vert_faces = set(_face_names(vert)) if vert else set()
    horiz_faces = set(_face_names(horiz)) if horiz else set()
    holes = [_hole(o, wall) for o in openings]
    inward = 1.0 if ext > 0 else -1.0
    for entry in spec.bars:
        if entry.role not in ("vertical", "horizontal"):
            continue
        db = BARS[entry.bar].diameter_in * _IN
        if entry.role == "vertical":
            behind, centre = 0.0, (dv / 2 if "center" in horiz_faces else 0.0)
        else:
            behind, centre = dv, (-dh / 2 if "center" in vert_faces else 0.0)
        for t, face in _faces(entry, frame, ext, cover, db, behind, vert_faces, centre):
            rng = _s_range_at(layer.polygon, frame, t)
            if rng is None:
                continue
            a, b = rng[0] + cover, rng[1] - cover
            if entry.role == "vertical" and entry.spacing is not None:
                hooked = base is not None and bool(entry.hooks) and "start" in entry.hooks
                z_start = base.rest + db / 2 if hooked else frame.z0 + cover
                foot = _d3(_scale(frame.n, -inward if face == "exterior" else inward)) \
                    if hooked else None
                anchor = _anchorage(sink, entry, base, z_start, db) if hooked else None
                for s in fence(a + db / 2, b - db / 2, entry.spacing.meters):
                    zt = top_at(s) - cover
                    runs = _cut(z_start, zt, s, holes, cover, vertical=True)
                    for k, (z_lo, z_hi) in enumerate(runs):
                        first = k == 0 and abs(z_lo - z_start) < 1e-6
                        sink.straight(entry, frame.world(s, t, z_lo), frame.world(s, t, z_hi),
                                      hook_dirs=(foot if first else None, None),
                                      lap_offset=frame.dir3,
                                      anchorage=anchor if first else None)
            elif entry.role == "horizontal":
                zs = _rows(entry, frame, cover, db, top_at)
                steel.lines.append((entry, t, zs))
                for z in zs:
                    lo, hi = _under_rake(a, b, z + cover, top_at)
                    for s_lo, s_hi in _cut(lo, hi, z, holes, cover, vertical=False):
                        sink.straight(entry, frame.world(s_lo, t, z), frame.world(s_hi, t, z),
                                      lap_offset=(0.0, 0.0, 1.0),
                                      top_cast=z - frame.z0 > 12 * _IN)
    return steel


def _scale(v, k: float) -> tuple[float, float]:
    return (v[0] * k, v[1] * k)


def _anchorage(sink: Sink, entry, base: WallBase, z_foot: float, db: float):
    """``(embedment, ldh)``: top of the pour below to the outside of the foot, against §25.4.3."""
    need = det.hooked_development_in(
        entry.bar, sink.fc_psi, confined_spacing=entry.spacing.meters >= 6 * db,
        side_cover_ok=True) * _IN
    return base.top - (z_foot - db / 2), need


def _d3(d):
    return None if d is None else (d[0], d[1], 0.0)


def _face_names(entry) -> list[str]:
    face = entry.face or ("center" if entry.layers <= 1 else None)
    if face is None:
        return ["interior", "exterior"]
    return [face] * max(1, entry.layers)


def _faces(entry, frame: LinearFrame, ext: float, cover: float, db: float, behind: float,
           vert_faces: set[str], centre: float = 0.0) -> list[tuple[float, str]]:
    """``(t, face)`` of each layer of ``entry``. A horizontal sits ``behind`` (the vertical's
    diameter) inboard only on a face the verticals actually occupy; repeats of one face
    stack a bar diameter further in. ``centre`` shifts a centred bar toward the exterior
    (negative: the interior), so a centred vertical and horizontal touch rather than cross."""
    t_int = frame.t0 if ext > 0 else frame.t1
    t_ext = frame.t1 if ext > 0 else frame.t0
    inward = 1.0 if ext > 0 else -1.0  # interior face -> exterior face
    out: list[tuple[float, str]] = []
    seen: dict[str, int] = {}
    for name in _face_names(entry):
        k = seen.get(name, 0)
        seen[name] = k + 1
        extra = (behind if name in vert_faces else 0.0) + k * db
        if name == "center":
            step = k * db if centre >= 0 else -k * db
            out.append(((frame.t0 + frame.t1) / 2.0 + inward * (centre + step), name))
        elif name == "interior":
            out.append((t_int + inward * (cover + extra + db / 2), name))
        else:
            out.append((t_ext - inward * (cover + extra + db / 2), name))
    return out


def _rows(entry, frame: LinearFrame, cover: float, db: float, top_at) -> list[float]:
    top = min(top_at(frame.s0), top_at(frame.s1))
    if entry.count:
        # D8 / IRC Table R404.1.2(1): rows at top − 6", evenly down to 6" off the base.
        hi, lo = top - _ROW_FROM_EDGE_M, frame.z0 + _ROW_FROM_EDGE_M
        if entry.count == 1:
            return [hi]
        return [lo + (hi - lo) * i / (entry.count - 1) for i in range(entry.count)]
    if entry.spacing is None:
        return []
    return fence(frame.z0 + cover + db / 2, max(top_at(frame.s0), top_at(frame.s1))
                 - cover - db / 2, entry.spacing.meters)


def _top_fn(wall, frame: LinearFrame):
    """Concrete top at ``s``: the raked line where the wall has one, capped by the band."""
    if wall.top_z0_m is None and wall.top_z1_m is None:
        return lambda s: frame.z1
    length = math.dist(*wall.axis) or 1.0
    z_a = wall.top_z0_m if wall.top_z0_m is not None else wall.z1_m
    z_b = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
    return lambda s: min(frame.z1, z_a + (z_b - z_a) * max(0.0, min(1.0, s / length)))


def _under_rake(a: float, b: float, z_need: float, top_at) -> tuple[float, float]:
    """Trim ``[a, b]`` to where the top clears ``z_need`` — linear, so check both ends."""
    fa, fb = top_at(a) - z_need, top_at(b) - z_need
    if fa >= 0 and fb >= 0:
        return a, b
    if fa < 0 and fb < 0:
        return b, a
    cross = a + (b - a) * fa / (fa - fb)
    return (cross, b) if fa < 0 else (a, cross)


def _hole(opening, wall) -> tuple[float, float, float, float]:
    half = opening.width_m / 2.0
    z = wall.base_ref_z_m + opening.sill_m
    return (opening.center_along_m - half, opening.center_along_m + half, z,
            z + opening.height_m)


def _cut(lo: float, hi: float, at: float, holes, cover: float, *,
         vertical: bool) -> list[tuple[float, float]]:
    """``[lo, hi]`` less every opening the bar at ``at`` crosses, at cover each side."""
    runs = [(lo, hi)] if hi - lo > _MIN_BAR_M else []
    for s0, s1, z0, z1 in holes:
        across = (s0 - cover <= at <= s1 + cover) if vertical else (z0 - cover <= at <= z1 + cover)
        if not across:
            continue
        g0, g1 = (z0 - cover, z1 + cover) if vertical else (s0 - cover, s1 + cover)
        nxt: list[tuple[float, float]] = []
        for r0, r1 in runs:
            for c0, c1 in ((r0, min(r1, g0)), (max(r0, g1), r1)):
                if c1 - c0 > _MIN_BAR_M:
                    nxt.append((c0, c1))
        runs = nxt
    return runs
