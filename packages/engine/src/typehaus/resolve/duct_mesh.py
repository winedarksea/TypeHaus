"""Mesh primitives for duct part solids: sections, rings, prisms, lofts and boxes.

Split out of ``duct_part_solids`` so ``boot_solids`` and other part drawers share them.
Sections parse from the record text (``4in`` round, ``18x8`` width x depth, inches).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_ir import GMesh, Vec3, signed_volume
from typehaus.resolve.sweep import leg_frame

_FACETS = 16


@dataclass(frozen=True)
class Section:
    """A duct section in metres: ``width`` across the run, ``depth`` through it."""

    is_round: bool
    width: float
    depth: float

    @property
    def larger(self) -> float:
        return max(self.width, self.depth)


def parse_section(text: str | None) -> Section | None:
    """``4in`` -> round, ``18x8`` -> rectangular; anything else (``none``, None) -> None."""
    if not text:
        return None
    try:
        if text.endswith("in"):
            d = float(text[:-2]) * M_PER_IN
            return Section(True, d, d) if d > 0 else None
        w, _, h = text.partition("x")
        w, h = float(w) * M_PER_IN, float(h) * M_PER_IN
        return Section(False, w, h) if w > 0 and h > 0 else None
    except ValueError:
        return None


def _add(a: Vec3, b: Vec3, k: float = 1.0) -> Vec3:
    return (a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k)


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _unit(v: Vec3) -> Vec3 | None:
    n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return None if n < 1e-9 else (v[0] / n, v[1] / n, v[2] / n)


def _ring(section: Section, centre: Vec3, right: Vec3, up: Vec3, count: int) -> list[Vec3]:
    """The section's outline at ``centre``: ``count`` 4 (rectangle) or ``_FACETS`` points."""
    hw, hd = section.width / 2.0, section.depth / 2.0
    if section.is_round:
        pts = [(hw * math.cos(2 * math.pi * i / count), hd * math.sin(2 * math.pi * i / count))
               for i in range(count)]
    elif count == 4:
        pts = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
    else:  # a rectangle lofted to a round: sampled on the same angles, never collinear in uv
        pts = []
        for i in range(count):
            c, s = math.cos(2 * math.pi * i / count), math.sin(2 * math.pi * i / count)
            t = min(hw / abs(c) if abs(c) > 1e-9 else math.inf,
                    hd / abs(s) if abs(s) > 1e-9 else math.inf)
            pts.append((t * c, t * s))
    return [_add(_add(centre, right, u), up, v) for u, v in pts]


def prism(a: list[Vec3], b: list[Vec3]) -> GMesh:
    """A closed solid between two convex rings of equal length, capped from their centres."""
    n = len(a)
    ca = tuple(sum(p[i] for p in a) / n for i in range(3))
    cb = tuple(sum(p[i] for p in b) / n for i in range(3))
    positions = (*a, *b, ca, cb)
    tris: list[tuple[int, int, int]] = []
    for i in range(n):
        j = (i + 1) % n
        tris += [(i, j, n + j), (i, n + j, n + i), (2 * n, j, i), (2 * n + 1, n + i, n + j)]
    if signed_volume(positions, tris) < 0:
        tris = [(x, z, y) for x, y, z in tris]
    return GMesh(positions=positions, triangles=tuple(tris))


def loft(origin: Vec3, axis: Vec3, start: Section, end: Section, length: float,
         far: Vec3 | None = None) -> GMesh:
    """``start`` at ``origin`` to ``end`` ``length`` along ``axis`` (or centred on ``far``,
    an eccentric fitting: each ring on its own run's centreline)."""
    right, up = leg_frame(axis)
    count = 4 if not start.is_round and not end.is_round else _FACETS
    far = far if far is not None else _add(origin, axis, length)
    return prism(_ring(start, origin, right, up, count), _ring(end, far, right, up, count))


def _box(centre: Vec3, axes: tuple[Vec3, Vec3, Vec3], dims: tuple[float, float, float]) -> GMesh:
    def corner(sx: float, sy: float, sz: float) -> Vec3:
        p = centre
        for sign, axis, dim in zip((sx, sy, sz), axes, dims, strict=True):
            p = _add(p, axis, sign * dim / 2.0)
        return p

    return prism([corner(-1, -1, -1), corner(1, -1, -1), corner(1, 1, -1), corner(-1, 1, -1)],
                 [corner(-1, -1, 1), corner(1, -1, 1), corner(1, 1, 1), corner(-1, 1, 1)])
