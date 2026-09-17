"""Runs into cut pieces: stock-length splits, laps, hooks — the sink every layout writes to.

A straight run whose developed length ``D`` (hooks included) exceeds stock is split into
``n = ceil((D − lap) / (stock − lap))`` pieces of EQUAL cut length ``c = (D + (n−1)·lap) / n``
(decision D2) — never over stock, never a stub that is all lap. Laps are STAGGERED: every
other run of a role shifts its splices by half a pitch ``(c − lap)/2``, which costs it one
more piece (both end pieces ``(c − lap)/2 + lap``) and keeps neighbouring laps apart. Every
piece but the last carries the lap it shares with the next, so Σ placed is the run and
Σ cut is ``L + (pieces−1)·lap + hooks``. Lapping pieces are drawn one bar diameter apart.

A wall's laps are the greater of ACI class B and IRC Table R608.5.4(1)
(``Sink.wall``); an A767 bar's hooks bend at A767's diameters.
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


def _unit(a: Vec3, b: Vec3) -> Vec3:
    d = math.dist(a, b) or 1.0
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d, (b[2] - a[2]) / d)


def split_pieces(developed: float, lap: float, stock: float,
                 stagger: bool) -> list[tuple[float, float]]:
    """``[(d0, d1)]`` along the developed length: equal pieces, or staggered by half a pitch."""
    if developed <= stock + 1e-6:
        return [(0.0, developed)]
    n = math.ceil((developed - lap) / (stock - lap) - 1e-9)
    pitch = (developed - lap) / n
    starts = [i * pitch for i in range(n)]
    if stagger:
        starts = [0.0] + [(i + 0.5) * pitch for i in range(n)]
    ends = [s + lap for s in starts[1:]] + [developed]
    return list(zip(starts, ends, strict=True))


@dataclass
class Sink:
    """Collects one host's bars. ``fc_psi`` and ``lap_class`` govern its laps."""

    host_tag: str
    pour_coating: str
    fc_psi: float
    lap_class: str | None
    stock_m: float
    wall: bool = False
    bars: list[ResolvedBar] = field(default_factory=list)
    _runs: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def _key(self, role: str) -> str:
        self._runs[role] += 1
        return f"{self.host_tag}/{role}/{self._runs[role]:03d}"

    def coating(self, entry) -> str:
        return entry.coating or self.pour_coating or ""

    def galvanized(self, entry) -> bool:
        return det.bent_before_galvanizing(self.coating(entry))

    def _common(self, entry, note: str | None = None) -> dict:
        return {"role": entry.role, "bar": entry.bar, "coating": self.coating(entry),
                "spacing_in": float(entry.spacing.inches) if entry.spacing else None,
                "diameter_m": BARS[entry.bar].diameter_in * _IN,
                "note": note if note is not None else entry.note}

    def lap_m(self, bar: int, *, top_cast: bool = False, compression: bool = False) -> float:
        if compression:
            return det.compression_lap_in(bar) * _IN
        if self.wall:
            return det.wall_lap_in(bar, self.fc_psi, self.lap_class, top_cast=top_cast) * _IN
        return det.tension_lap_in(bar, self.fc_psi, self.lap_class, top_cast=top_cast) * _IN

    def straight(self, entry, p0: Vec3, p1: Vec3, *, hook_dirs: tuple = (None, None),
                 lap_offset: Vec3 = (0.0, 0.0, 1.0), top_cast: bool = False,
                 compression: bool = False, hook_kind: det.HookKind = "std90",
                 anchorage: tuple[float, float] | None = None) -> None:
        """One straight run ``p0 → p1``; a hook turns along ``hook_dirs[i]`` at that end.

        ``anchorage`` is ``(embedment_m, development_m)`` of a start hook into the pour below.
        """
        length = math.dist(p0, p1)
        if length <= 1e-4:
            return
        bar = entry.bar
        galv = self.galvanized(entry)
        hooks = [det.hook_allowance_in(bar, hook_kind, galvanized=galv) * _IN
                 if d is not None else 0.0 for d in hook_dirs]
        lap = self.lap_m(bar, top_cast=top_cast, compression=compression)
        developed = length + hooks[0] + hooks[1]
        key = self._key(entry.role)
        pieces = split_pieces(developed, lap, self.stock_m, self._runs[entry.role] % 2 == 0)
        u = _unit(p0, p1)
        db = BARS[bar].diameter_in * _IN
        n = len(pieces)
        for i, (d0, d1) in enumerate(pieces):
            last = i == n - 1
            start = max(0.0, d0 - hooks[0])
            end = length if last else d1 - hooks[0]
            off = db if i % 2 else 0.0
            a = _add(_add(p0, u, start), lap_offset, off)
            b = _add(_add(p0, u, end), lap_offset, off)
            path: list[Vec3] = [a, b]
            kinds: list[str] = []
            hook = 0.0
            if i == 0 and hook_dirs[0] is not None:
                path.insert(0, _add(a, hook_dirs[0], self._leg_m(bar, hook_kind, galv)))
                kinds.append(hook_kind)
                hook += hooks[0]
            if last and hook_dirs[1] is not None:
                path.append(_add(b, hook_dirs[1], self._leg_m(bar, hook_kind, galv)))
                kinds.append(hook_kind)
                hook += hooks[1]
            lap_here = 0.0 if last else lap
            anchor = anchorage if i == 0 and anchorage is not None else (None, None)
            self.bars.append(ResolvedBar(
                key=key if n == 1 else f"{key}-{i + 1}", path=tuple(path), closed=False,
                placed_length_m=(end - start) - lap_here, lap_length_m=lap_here,
                hook_length_m=hook, hook_kinds=tuple(kinds), piece=i + 1, pieces=n,
                embedment_m=anchor[0], development_m=anchor[1], **self._common(entry)))

    @staticmethod
    def _leg_m(bar: int, kind: det.HookKind, galvanized: bool = False) -> float:
        _, bend, extension = det.hook_geometry_in(bar, kind, galvanized=galvanized)
        return (bend / 2.0 + BARS[bar].diameter_in + extension) * _IN

    def loop(self, entry, points: list[Vec3], *, hook_kind: det.HookKind = "tie135",
             overlap_in: float = 0.0, perimeter_m: float | None = None) -> None:
        """A closed tie, hoop or stirrup: perimeter placed, two hooks (+ overlap) extra.

        ``perimeter_m`` overrides the drawn polygon's — a circular tie bills ``2πr``.
        """
        if len(points) < 3:
            return
        perimeter = perimeter_m if perimeter_m is not None else sum(
            math.dist(points[i], points[(i + 1) % len(points)]) for i in range(len(points)))
        allowance = det.hook_allowance_in(entry.bar, hook_kind, galvanized=self.galvanized(entry))
        hook = (2.0 * allowance + overlap_in) * _IN
        self.bars.append(ResolvedBar(
            key=self._key(entry.role), path=tuple(points), closed=True,
            placed_length_m=perimeter, hook_length_m=hook,
            hook_kinds=(hook_kind, hook_kind), **self._common(entry)))

    def polyline(self, entry, points: list[Vec3], *, placed_m: float, hook_m: float,
                 hook_kinds: tuple[str, ...], lap_m: float = 0.0, note: str | None = None,
                 anchorage: tuple[float, float] | None = None) -> None:
        """An already-bent piece (an L dowel, a corner bar) whose lengths the caller states."""
        embed, need = anchorage if anchorage is not None else (None, None)
        self.bars.append(ResolvedBar(
            key=self._key(entry.role), path=tuple(points), closed=False,
            placed_length_m=placed_m, lap_length_m=lap_m, hook_length_m=hook_m,
            hook_kinds=hook_kinds, embedment_m=embed, development_m=need,
            **self._common(entry, note)))
