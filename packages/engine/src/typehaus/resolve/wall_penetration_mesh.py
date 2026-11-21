"""Drawn bodies for decision #142's derived parts, built in a wall-face frame.

Local coordinates are (``s`` along the wall, ``n`` out of the cladding face, ``z`` up).
Every piece is a closed convex prism (``duct_mesh.prism``): no booleans, light enough for
Pyodide. Sizes come from the records (the standard's rows); the shape detail below is the
product's look:

* sleeve: only its white PVC lip proud of the panel, an annulus round the run;
* EPDM boot (Dektite class): a thin round aluminium-bonded base and a stepped cone cut to
  the pipe;
* lineset wall inlet (DiversiTech 230-WC4 class): a flange and a hood tapering outward;
* mount block: cellular PVC with eased edges and two screw heads, a raked top when cut;
* strut: 1-5/8" C-channel (web on the crowns, lipped flanges), with a spring-nut clamp per
  held device top and bottom;
* lineset cover: a rounded-square duct swept along each set's outdoor leg.
"""

from __future__ import annotations

import math

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import combine_meshes
from typehaus.resolve.duct_mesh import prism
from typehaus.resolve.geometry_ir import GMesh

Vec3 = tuple[float, float, float]
_FACETS = 20
_BOOT_BASE_M = 0.1875 * M_PER_IN  # Dektite base thickness
_STRUT_GAUGE_M = 0.105 * M_PER_IN  # 12 ga channel
_STRUT_LIP_M = 0.375 * M_PER_IN
_EASE_M = 0.125 * M_PER_IN
_SCREW_R_M = 0.25 * M_PER_IN
_SCREW_H_M = 0.125 * M_PER_IN
_SHEET_M = 0.125 * M_PER_IN


class Frame:
    def __init__(self, origin: tuple[float, float], tangent: tuple[float, float],
                 normal: tuple[float, float]) -> None:
        self.o, self.t, self.n = origin, tangent, normal

    def at(self, s: float, n: float, z: float) -> Vec3:
        return (self.o[0] + self.t[0] * s + self.n[0] * n,
                self.o[1] + self.t[1] * s + self.n[1] * n, z)

    def slab(self, ring_sz: list[tuple[float, float]], n0: float, n1: float) -> GMesh:
        """A convex (s, z) ring extruded from ``n0`` to ``n1`` off the face."""
        return prism([self.at(s, n0, z) for s, z in ring_sz],
                     [self.at(s, n1, z) for s, z in ring_sz])

    def frustum(self, s: float, z: float, r0: float, r1: float, n0: float,
                n1: float) -> GMesh:
        """A round piece on the face normal, radius ``r0`` at ``n0`` to ``r1`` at ``n1``."""
        return prism(_circle(s, z, r0, self, n0), _circle(s, z, r1, self, n1))


def _circle(s: float, z: float, r: float, frame: Frame, n: float) -> list[Vec3]:
    return [frame.at(s + r * math.cos(a), n, z + r * math.sin(a))
            for a in (2 * math.pi * i / _FACETS for i in range(_FACETS))]


def _annulus(frame: Frame, s: float, z: float, r_in: float, r_out: float, n0: float,
             n1: float) -> GMesh:
    pieces = []
    for i in range(_FACETS):
        a0, a1 = (2 * math.pi * k / _FACETS for k in (i, i + 1))
        ring = [(s + r * math.cos(a), z + r * math.sin(a))
                for r, a in ((r_in, a0), (r_out, a0), (r_out, a1), (r_in, a1))]
        pieces.append(frame.slab(ring, n0, n1))
    return combine_meshes(*pieces)


def _eased(lo: float, hi: float, z0: float, z1: float, ease: float = _EASE_M
           ) -> list[tuple[float, float]]:
    e = min(ease, (hi - lo) / 4, (z1 - z0) / 4)
    return [(lo + e, z0), (hi - e, z0), (hi, z0 + e), (hi, z1 - e), (hi - e, z1),
            (lo + e, z1), (lo, z1 - e), (lo, z0 + e)]


def sleeve_lip_mesh(frame: Frame, s: float, z: float, sleeve_d: float, run_d: float,
                    lip: float) -> GMesh:
    wall = max(0.0625 * M_PER_IN, min(0.25 * M_PER_IN, (sleeve_d - run_d) / 2))
    return _annulus(frame, s, z, sleeve_d / 2 - wall, sleeve_d / 2, -_SHEET_M, lip)


def boot_mesh(frame: Frame, s: float, z: float, base_d: float, run_d: float,
              height: float, pan_n: float) -> GMesh:
    """Base on the pan plane (``pan_n``, behind the crowns), a three-step cone to the pipe."""
    r_pipe = run_d / 2 + 0.0625 * M_PER_IN
    r_cone = max(r_pipe + 0.25 * M_PER_IN, base_d * 0.36)
    parts = [frame.frustum(s, z, base_d / 2, base_d / 2, pan_n, pan_n + _BOOT_BASE_M)]
    steps = 3
    for i in range(steps):
        r0 = r_cone - (r_cone - r_pipe) * i / steps
        r1 = r_cone - (r_cone - r_pipe) * (i + 1) / steps
        n0 = pan_n + _BOOT_BASE_M + height * i / steps
        n1 = pan_n + _BOOT_BASE_M + height * (i + 1) / steps
        parts.append(frame.frustum(s, z, r0, r1 + (r0 - r1) * 0.25, n0, n1))
    return combine_meshes(*parts)


def inlet_mesh(frame: Frame, s: float, z: float, width: float, height: float,
               projection: float, run_d: float) -> GMesh:
    hw, hh = width / 2, height / 2
    flange = frame.slab(_eased(s - hw, s + hw, z - hh, z + hh), 0.0, _SHEET_M)
    bw = max(run_d / 2 + 0.25 * M_PER_IN, hw - 0.5 * M_PER_IN)
    near = _eased(s - bw, s + bw, z - hh + 0.5 * M_PER_IN, z + hh - 0.5 * M_PER_IN)
    # The hood narrows outward and opens downward: drawn as its tapering shell.
    far = _eased(s - bw * 0.8, s + bw * 0.8, z - hh + 0.5 * M_PER_IN, z + hh * 0.35)
    hood = prism([frame.at(a, _SHEET_M, b) for a, b in near],
                 [frame.at(a, projection, b) for a, b in far])
    return combine_meshes(flange, hood)


def block_mesh(frame: Frame, lo: float, hi: float, z0: float, z1: float, depth: float,
               top_z: tuple[float, float] | None = None, back: float = 0.0) -> GMesh:
    if top_z is not None:
        e = min(_EASE_M, (hi - lo) / 4)
        ring = [(lo + e, z0), (hi - e, z0), (hi, z0 + e), (hi, top_z[1]), (lo, top_z[0]),
                (lo, z0 + e)]
    else:
        ring = _eased(lo, hi, z0, z1)
    face = back + depth
    parts = [frame.slab(ring, back, face)]
    mid = (z0 + (min(top_z) if top_z else z1)) / 2
    for sx in (lo + (hi - lo) * 0.3, lo + (hi - lo) * 0.7):
        parts.append(frame.frustum(sx, mid, _SCREW_R_M, _SCREW_R_M * 0.8, face,
                                   face + _SCREW_H_M))
    return combine_meshes(*parts)


def strut_mesh(frame: Frame, channels: tuple[float, ...], width: float, depth: float,
               z0: float, z1: float, clamps: tuple[float, ...]) -> GMesh:
    """C-channels open outward; a clamp (spring nut + strap) at each ``clamps`` z."""
    parts = []
    g = _STRUT_GAUGE_M
    for c in channels:
        lo, hi = c - width / 2, c + width / 2
        parts.append(frame.slab(_rect(lo, hi, z0, z1), 0.0, g))  # web on the crowns
        for a, b in ((lo, lo + g), (hi - g, hi)):
            parts.append(frame.slab(_rect(a, b, z0, z1), g, depth))
        for a, b in ((lo + g, lo + g + _STRUT_LIP_M), (hi - g - _STRUT_LIP_M, hi - g)):
            parts.append(frame.slab(_rect(a, b, z0, z1), depth - g, depth))
        for zc in clamps:
            parts.append(frame.slab(_rect(lo - 0.0625 * M_PER_IN, hi + 0.0625 * M_PER_IN,
                                          zc - 0.375 * M_PER_IN, zc + 0.375 * M_PER_IN),
                                    depth, depth + 0.1875 * M_PER_IN))
    return combine_meshes(*parts)


def _rect(lo: float, hi: float, z0: float, z1: float) -> list[tuple[float, float]]:
    return [(lo, z0), (hi, z0), (hi, z1), (lo, z1)]


def cover_mesh(points: list[Vec3], size: float) -> GMesh | None:
    """A rounded-square channel swept straight along each leg, a cube at each bend."""
    parts = []
    half = size / 2
    for a, b in zip(points, points[1:], strict=False):
        d = tuple(b[i] - a[i] for i in range(3))
        length = math.sqrt(sum(v * v for v in d))
        if length < 1e-4:
            continue
        d = tuple(v / length for v in d)
        u = (0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (1.0, 0.0, 0.0)
        u = _unit(_cross(_cross(d, u), d))
        v = _cross(d, u)
        ring = _eased(-half, half, -half, half, size * 0.18)

        def place(p: Vec3, ring=ring, u=u, v=v) -> list[Vec3]:
            return [tuple(p[i] + u[i] * z + v[i] * s for i in range(3)) for s, z in ring]

        parts.append(prism(place(a), place(b)))
    return combine_meshes(*parts) if parts else None


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(a: Vec3) -> Vec3:
    m = math.sqrt(sum(v * v for v in a)) or 1.0
    return tuple(v / m for v in a)


def strap_mesh(frame: Frame, s: float, n_centre: float, z: float, radius: float,
               face_n: float, width: float = 0.75 * M_PER_IN,
               sheet: float = 0.0625 * M_PER_IN) -> GMesh:
    """A two-hole 316 strap: a band round the pipe's front, legs back to the block face and
    a screw foot each side on it, drawn in the (s, n) plane over ``width`` of z."""
    z0, z1 = z - width / 2, z + width / 2
    r0, r1 = radius, radius + sheet
    parts = []

    def piece(ring: list[tuple[float, float]]) -> None:
        parts.append(prism([frame.at(a, b, z0) for a, b in ring],
                           [frame.at(a, b, z1) for a, b in ring]))

    steps = 8
    for i in range(steps):
        a0, a1 = (-math.pi / 2 + math.pi * k / steps for k in (i, i + 1))
        piece([(s + r0 * math.sin(a0), n_centre + r0 * math.cos(a0)),
               (s + r1 * math.sin(a0), n_centre + r1 * math.cos(a0)),
               (s + r1 * math.sin(a1), n_centre + r1 * math.cos(a1)),
               (s + r0 * math.sin(a1), n_centre + r0 * math.cos(a1))])
    for sign in (-1.0, 1.0):
        inner, outer = s + sign * r0, s + sign * r1
        if n_centre > face_n + 1e-4:  # the leg from the band back to the block face
            piece(sorted([(inner, face_n), (outer, face_n)]) +
                  sorted([(outer, n_centre), (inner, n_centre)], reverse=True))
        foot = (outer, outer + sign * width)
        piece([(min(foot), face_n), (max(foot), face_n), (max(foot), face_n + sheet),
               (min(foot), face_n + sheet)])
    return combine_meshes(*parts)


def gasket_mesh(centre: Vec3, axis: tuple[float, float], bore: float,
                outside: float = 3.5 * M_PER_IN, thick: float = 0.125 * M_PER_IN) -> GMesh:
    """A flat ring gasket round a horizontal run (a hydrant escutcheon's), on its axis."""
    m = math.hypot(*axis) or 1.0
    n = (axis[0] / m, axis[1] / m)
    frame = Frame((centre[0], centre[1]), (-n[1], n[0]), n)
    return _annulus(frame, 0.0, centre[2], bore / 2, outside / 2, -thick / 2, thick / 2)
