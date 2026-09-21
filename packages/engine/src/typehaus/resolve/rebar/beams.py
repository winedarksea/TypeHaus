"""Linear sections: a cast ``Beam``, or a wall acting as one (W-SG-BRKBM).

Frame (decision D7): ``s`` along the member, ``t`` across it in plan, ``z`` up. ``top-y`` and
``bottom-y`` are ``count`` bars along the member inside the hoops; ``ties``/``stirrups`` are
closed hoops at a spacing (the D3 fencepost over the length less cover, limited to ``zone``
of each end when authored); ``horizontal`` authored as ``count`` is that many side bars per
face between the top and bottom bars (torsion longitudinal steel).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.model.rebar import BARS, BarSpec
from typehaus.resolve.rebar.records import Vec3
from typehaus.resolve.rebar.stock import Sink

_IN = 0.0254
BEAM_ROLES = frozenset({"top-y", "bottom-y", "ties", "stirrups"})


@dataclass(frozen=True)
class LinearFrame:
    origin: tuple[float, float]
    u: tuple[float, float]
    n: tuple[float, float]
    s0: float
    s1: float
    t0: float
    t1: float
    z0: float
    z1: float

    def world(self, s: float, t: float, z: float) -> Vec3:
        return (self.origin[0] + self.u[0] * s + self.n[0] * t,
                self.origin[1] + self.u[1] * s + self.n[1] * t, z)

    @property
    def dir3(self) -> Vec3:
        return (self.u[0], self.u[1], 0.0)


def frame_of_ring(ring, z0: float, z1: float) -> LinearFrame:
    """A frame along the longest edge of a plan ring (a cast beam's outline)."""
    pts = list(ring)
    best = max(range(len(pts)), key=lambda i: math.dist(pts[i], pts[(i + 1) % len(pts)]))
    a, b = pts[best], pts[(best + 1) % len(pts)]
    d = math.dist(a, b) or 1.0
    u = ((b[0] - a[0]) / d, (b[1] - a[1]) / d)
    n = (-u[1], u[0])
    ss = [(p[0] - a[0]) * u[0] + (p[1] - a[1]) * u[1] for p in pts]
    ts = [(p[0] - a[0]) * n[0] + (p[1] - a[1]) * n[1] for p in pts]
    return LinearFrame(a, u, n, min(ss), max(ss), min(ts), max(ts), z0, z1)


def fence(a: float, b: float, spacing: float) -> list[float]:
    """D3: ``n = ceil(L / s) + 1`` positions evenly from ``a`` to ``b`` inclusive."""
    span = b - a
    if span < -1e-9:
        return []
    if span <= 1e-6 or spacing <= 0.0:
        return [(a + b) / 2.0]
    n = math.ceil(span / spacing - 1e-9) + 1
    return [a + span * i / (n - 1) for i in range(n)]


def _spread(a: float, b: float, count: int) -> list[float]:
    if count <= 1:
        return [(a + b) / 2.0]
    return [a + (b - a) * i / (count - 1) for i in range(count)]


def lay_beam(sink: Sink, entries, frame: LinearFrame, cover: float,
             ends: dict[str, tuple[float | None, float | None]] | None = None) -> None:
    """``ends``: per ``top-y``/``bottom-y``, the ``s`` a row stops at instead of cover — a top
    row reaching into the support it hooks in, a bottom row stopping at a cold joint whose
    dowels take over (``build._beam_row_ends``)."""
    ends = ends or {}
    hoop = next((e for e in entries if e.role in ("ties", "stirrups")), None)
    dt = BARS[hoop.bar].diameter_in * _IN if hoop else 0.0
    inner = cover + dt
    for entry in entries:
        db = BARS[entry.bar].diameter_in * _IN
        if entry.role in ("ties", "stirrups") and entry.spacing is not None:
            a, b = frame.s0 + cover, frame.s1 - cover
            positions = fence(a, b, entry.spacing.meters)
            if entry.zone is not None:
                zone = entry.zone.meters
                positions = [p for p in positions if p - a <= zone + 1e-6 or b - p <= zone + 1e-6]
            tl, tr = frame.t0 + cover + db / 2, frame.t1 - cover - db / 2
            zb, zt = frame.z0 + cover + db / 2, frame.z1 - cover - db / 2
            for s in positions:
                sink.loop(entry, [frame.world(s, tl, zb), frame.world(s, tr, zb),
                                  frame.world(s, tr, zt), frame.world(s, tl, zt)])
        elif entry.role in ("top-y", "bottom-y") and entry.count:
            top = entry.role == "top-y"
            z = frame.z1 - inner - db / 2 if top else frame.z0 + inner + db / 2
            ts = _spread(frame.t0 + inner + db / 2, frame.t1 - inner - db / 2, entry.count)
            sa, sb = _row_ends(entry, frame, cover, ends)
            for _layer in range(max(1, entry.layers)):
                for t in ts:
                    sink.straight(entry, frame.world(sa, t, z), frame.world(sb, t, z),
                                  hook_dirs=_hooks(entry, frame, down=top),
                                  lap_offset=(frame.n[0], frame.n[1], 0.0),
                                  top_cast=top and z - frame.z0 > 12 * _IN)
                z += -db if top else db
        elif entry.role == "horizontal" and entry.count:
            zs = _spread(frame.z0 + inner, frame.z1 - inner, entry.count + 2)[1:-1]
            faces = (frame.t0 + inner + db / 2, frame.t1 - inner - db / 2)
            for t in faces[: max(1, min(2, entry.layers))]:
                for z in zs:
                    sink.straight(entry, frame.world(frame.s0 + cover, t, z),
                                  frame.world(frame.s1 - cover, t, z),
                                  lap_offset=(0.0, 0.0, 1.0),
                                  top_cast=z - frame.z0 > 12 * _IN)
    for entry in entries:
        if entry.role in ("top-y", "bottom-y") and entry.hooks and entry.hook_ties:
            _lay_hook_ties(sink, entry, frame, cover, ends.get(entry.role, (None, None)))


def _row_ends(entry, frame: LinearFrame, cover: float, ends) -> tuple[float, float]:
    a, b = ends.get(entry.role, (None, None))
    return (frame.s0 + cover if a is None else a, frame.s1 - cover if b is None else b)


def _lay_hook_ties(sink: Sink, entry, frame: LinearFrame, cover: float, reach) -> None:
    """``BarSpec.hook_ties``: closed ties at each hooked end, along ℓdh in the support the hook
    anchors in (ACI 318-19 §25.4.3.3) — stepping OUT from a bar ending at the beam's cover, or
    back toward the span from one already ``reach``ing into the support."""
    conf = entry.hook_ties
    tie = BarSpec(role="ties", bar=conf.bar, spacing=conf.spacing,
                  note=f"encloses the {entry.role} hooks, ACI 318-19 §25.4.3.3")
    db = BARS[conf.bar].diameter_in * _IN
    tl, tr = frame.t0 + cover + db / 2, frame.t1 - cover - db / 2
    zb, zt = frame.z0 + cover + db / 2, frame.z1 - cover - db / 2
    sa, sb = _row_ends(entry, frame, cover, {entry.role: reach})
    ends = [(sa, 1.0 if reach[0] is not None else -1.0) if "start" in entry.hooks else None,
            (sb, -1.0 if reach[1] is not None else 1.0) if "end" in entry.hooks else None]
    for s_end, step in (e for e in ends if e is not None):
        for i in range(conf.count):
            s = s_end + step * i * conf.spacing.meters
            sink.loop(tie, [frame.world(s, tl, zb), frame.world(s, tr, zb),
                            frame.world(s, tr, zt), frame.world(s, tl, zt)])


def _hooks(entry, frame: LinearFrame, *, down: bool) -> tuple:
    if not entry.hooks:
        return (None, None)
    if entry.hook_turn is not None:
        down = entry.hook_turn == "down"
    turn = (0.0, 0.0, -1.0 if down else 1.0)
    return (turn if "start" in entry.hooks else None, turn if "end" in entry.hooks else None)
