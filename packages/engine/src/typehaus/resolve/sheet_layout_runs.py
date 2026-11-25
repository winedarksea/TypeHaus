"""Collinear sheathing or panel-cladding faces joined into one run (decision #146).

A wall split at a tee is two walls but one sheathed face: the crew hangs the sheets across
the tee, so laying each piece apart would rip a sheet at every split. Faces join when they
lie on one line, abut, and share material, thickness, sheet length and band (a raked
head may differ: each face keeps its own top). Stations in a
run are measured from its first wall's axis start along that wall's direction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.quantities import M_PER_IN
from typehaus.resolve.face_extent import face_span, framing_side_span

_LINE_TOL_M = 0.125 * M_PER_IN
_ABUT_TOL_M = 1.0 * M_PER_IN
_PARALLEL = 0.999


@dataclass
class Face:
    """One wall's laid layer on a run: ``base`` is the run station of the wall's axis
    start and ``sign`` +1 where the wall runs with the run, -1 against it. ``structure``
    is the framed layer behind it; ``nailer`` a cladding's joint-nailer stock, if any."""

    wall: object
    layer: object
    structure: object | None
    sheet_l: float
    z0: float
    top: float
    base: float = 0.0
    sign: float = 1.0
    lo: float = 0.0
    hi: float = 0.0
    nailer: object | None = None

    def run_station(self, local: float) -> float:
        return self.base + self.sign * local


@dataclass
class Run:
    origin: tuple[float, float]
    d: tuple[float, float]
    faces: list[Face]

    @property
    def lo(self) -> float:
        return min(f.lo for f in self.faces)

    @property
    def hi(self) -> float:
        return max(f.hi for f in self.faces)

    def face_at(self, s: float) -> Face:
        return min(self.faces, key=lambda f: 0.0 if f.lo <= s <= f.hi
                   else min(abs(s - f.lo), abs(s - f.hi)))


def direction(wall) -> tuple[float, float]:
    (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
    run = max(math.hypot(bx - ax, by - ay), 1e-9)
    return (bx - ax) / run, (by - ay) / run


def _place(face: Face, origin, d) -> bool:
    """Set ``face``'s run stations; False where it has no extent along its wall."""
    wall, layer = face.wall, face.layer
    wd = direction(wall)
    face.sign = 1.0 if wd[0] * d[0] + wd[1] * d[1] > 0 else -1.0
    face.base = (wall.axis[0][0] - origin[0]) * d[0] + (wall.axis[0][1] - origin[1]) * d[1]
    span = (framing_side_span(wall, layer, face.structure.polygon)
            if face.structure is not None else None)
    if span is None:
        absolute = face_span(wall, layer)
        if absolute is None:
            return False
        start = wall.axis[0][0] * wd[0] + wall.axis[0][1] * wd[1]
        span = (absolute[0] - start, absolute[1] - start)
    lo, hi = span
    if layer.run_span_m is not None:
        lo, hi = max(lo, layer.run_span_m[0]), min(hi, layer.run_span_m[1])
    ends = sorted((face.run_station(lo), face.run_station(hi)))
    face.lo, face.hi = ends
    return face.hi - face.lo > _LINE_TOL_M and face.top - face.z0 > _LINE_TOL_M


def _offsets(layer, origin, n) -> tuple[float, float]:
    values = [(x - origin[0]) * n[0] + (y - origin[1]) * n[1] for x, y in layer.polygon]
    return min(values), max(values)


def _joinable(a: Face, b: Face) -> bool:
    if (a.layer.material_ref, round(a.layer.thickness_m, 5), round(a.sheet_l, 5)) != (
            b.layer.material_ref, round(b.layer.thickness_m, 5), round(b.sheet_l, 5)):
        return False
    raked = any(f.wall.top_z0_m is not None or f.wall.top_z1_m is not None for f in (a, b))
    if abs(a.z0 - b.z0) > _LINE_TOL_M or (not raked and abs(a.top - b.top) > _LINE_TOL_M):
        return False
    da, db = direction(a.wall), direction(b.wall)
    if abs(da[0] * db[0] + da[1] * db[1]) < _PARALLEL:
        return False
    origin, n = a.wall.axis[0], (-da[1], da[0])
    if any(abs(p - q) > _LINE_TOL_M for p, q in zip(
            _offsets(a.layer, origin, n), _offsets(b.layer, origin, n), strict=True)):
        return False
    _place(a, origin, da)
    _place(b, origin, da)
    return b.lo <= a.hi + _ABUT_TOL_M and a.lo <= b.hi + _ABUT_TOL_M


def build_runs(faces: list[Face]) -> list[Run]:
    """Faces grouped into runs, each placed on its first wall's frame."""
    parent = list(range(len(faces)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(faces)):
        for j in range(i + 1, len(faces)):
            if root(i) != root(j) and _joinable(faces[i], faces[j]):
                parent[root(j)] = root(i)
    groups: dict[int, list[Face]] = {}
    for i, face in enumerate(faces):
        groups.setdefault(root(i), []).append(face)
    runs = []
    for group in groups.values():
        first = group[0]
        origin, d = first.wall.axis[0], direction(first.wall)
        placed = [f for f in group if _place(f, origin, d)]
        if placed:
            runs.append(Run(origin, d, sorted(placed, key=lambda f: f.lo)))
    return runs
