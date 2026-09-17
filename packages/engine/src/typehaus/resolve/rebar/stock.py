"""Runs into cut pieces: stock-length splits, laps, hooks — the sink every layout writes to.

A straight run longer than stock is split into ``n = ceil((L_dev − lap) / (stock − lap))``
pieces of EQUAL cut length ``(L_dev + (n−1)·lap) / n`` (decision D2), where ``L_dev`` includes
the hooks — which never exceeds stock and never leaves a stub that is all lap. Every piece
but the last carries the lap it shares with the next, so Σ placed is the run and Σ cut is
``L + (n−1)·lap + hooks``. Lapping pieces are drawn one bar diameter apart, alternately, so
both are visible and pickable.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field

from typehaus.model.rebar import BARS
from typehaus.resolve.rebar import detailing as det
from typehaus.resolve.rebar.records import ResolvedBar, Vec3

_IN = 0.0254


def _add(a: Vec3, b: Vec3, k: float = 1.0) -> Vec3:
    return (a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k)


def _dist(a: Vec3, b: Vec3) -> float:
    return math.dist(a, b)


def _unit(a: Vec3, b: Vec3) -> Vec3:
    d = _dist(a, b) or 1.0
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d, (b[2] - a[2]) / d)


@dataclass
class Sink:
    """Collects one host's bars. ``fc_psi`` and ``lap_class`` govern its laps."""

    host_tag: str
    pour_coating: str
    fc_psi: float
    lap_class: str | None
    stock_m: float
    bars: list[ResolvedBar] = field(default_factory=list)
    _runs: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def _key(self, role: str) -> str:
        self._runs[role] += 1
        return f"{self.host_tag}/{role}/{self._runs[role]:03d}"

    def _common(self, entry) -> dict:
        return {"role": entry.role, "bar": entry.bar,
                "coating": entry.coating or self.pour_coating or "",
                "spacing_in": float(entry.spacing.inches) if entry.spacing else None,
                "diameter_m": BARS[entry.bar].diameter_in * _IN, "note": entry.note}

    def lap_m(self, bar: int, *, top_cast: bool = False, compression: bool = False) -> float:
        if compression:
            return det.compression_lap_in(bar) * _IN
        return det.tension_lap_in(bar, self.fc_psi, self.lap_class, top_cast=top_cast) * _IN

    def straight(self, entry, p0: Vec3, p1: Vec3, *, hook_dirs: tuple = (None, None),
                 lap_offset: Vec3 = (0.0, 0.0, 1.0), top_cast: bool = False,
                 compression: bool = False, hook_kind: det.HookKind = "std90") -> None:
        """One straight run ``p0 → p1``; a hook turns along ``hook_dirs[i]`` at that end."""
        length = _dist(p0, p1)
        if length <= 1e-4:
            return
        bar = entry.bar
        hooks = [det.hook_allowance_in(bar, hook_kind) * _IN if d is not None else 0.0
                 for d in hook_dirs]
        lap = self.lap_m(bar, top_cast=top_cast, compression=compression)
        developed = length + hooks[0] + hooks[1]
        n = 1 if developed <= self.stock_m + 1e-6 else math.ceil(
            (developed - lap) / (self.stock_m - lap) - 1e-9)
        key = self._key(entry.role)
        u = _unit(p0, p1)
        db = BARS[bar].diameter_in * _IN
        cut = (developed + (n - 1) * lap) / n
        start = 0.0
        for i in range(n):
            last = i == n - 1
            end = length if last else start + cut - (hooks[0] if i == 0 else 0.0)
            off = db if i % 2 else 0.0
            a = _add(_add(p0, u, start), lap_offset, off)
            b = _add(_add(p0, u, end), lap_offset, off)
            path: list[Vec3] = [a, b]
            kinds: list[str] = []
            hook = 0.0
            if i == 0 and hook_dirs[0] is not None:
                path.insert(0, _add(a, hook_dirs[0], self._leg_m(bar, hook_kind)))
                kinds.append(hook_kind)
                hook += hooks[0]
            if last and hook_dirs[1] is not None:
                path.append(_add(b, hook_dirs[1], self._leg_m(bar, hook_kind)))
                kinds.append(hook_kind)
                hook += hooks[1]
            lap_here = 0.0 if last else lap
            self.bars.append(ResolvedBar(
                key=key if n == 1 else f"{key}-{i + 1}", path=tuple(path), closed=False,
                placed_length_m=(end - start) - lap_here, lap_length_m=lap_here,
                hook_length_m=hook, hook_kinds=tuple(kinds), piece=i + 1, pieces=n,
                **self._common(entry)))
            start = end - lap

    @staticmethod
    def _leg_m(bar: int, kind: det.HookKind) -> float:
        _, bend, extension = det.hook_geometry_in(bar, kind)
        return (bend / 2.0 + BARS[bar].diameter_in + extension) * _IN

    def loop(self, entry, points: list[Vec3], *, hook_kind: det.HookKind = "tie135",
             overlap_in: float = 0.0, perimeter_m: float | None = None) -> None:
        """A closed tie, hoop or stirrup: perimeter placed, two hooks (+ overlap) extra.

        ``perimeter_m`` overrides the drawn polygon's — a circular tie bills ``2πr``.
        """
        if len(points) < 3:
            return
        perimeter = perimeter_m if perimeter_m is not None else sum(
            _dist(points[i], points[(i + 1) % len(points)]) for i in range(len(points)))
        hook = (2.0 * det.hook_allowance_in(entry.bar, hook_kind) + overlap_in) * _IN
        self.bars.append(ResolvedBar(
            key=self._key(entry.role), path=tuple(points), closed=True,
            placed_length_m=perimeter, hook_length_m=hook,
            hook_kinds=(hook_kind, hook_kind), **self._common(entry)))

    def polyline(self, entry, points: list[Vec3], *, placed_m: float, hook_m: float,
                 hook_kinds: tuple[str, ...], lap_m: float = 0.0) -> None:
        """An already-bent single piece (an L dowel) whose lengths the caller states."""
        self.bars.append(ResolvedBar(
            key=self._key(entry.role), path=tuple(points), closed=False,
            placed_length_m=placed_m, lap_length_m=lap_m, hook_length_m=hook_m,
            hook_kinds=hook_kinds, **self._common(entry)))
