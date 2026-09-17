"""The resolved bar: one record per physical piece a fabricator cuts (decision D1)."""

from __future__ import annotations

from dataclasses import dataclass

Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class ResolvedBar:
    """One cut piece of bar, as placed.

    ``path`` is the bar centreline in project metres — two points for a straight bar, a
    polyline for a hooked bar, a hoop or an L-dowel; ``closed`` joins its last point to its
    first. Lengths split the cut length into what it is FOR: ``placed`` is the run the bar
    covers once, ``lap`` the overlap it shares with its next piece, ``hook`` the bends and
    tails. ``piece`` is 1-based of ``pieces`` along one run. A bar hooked into the pour below
    carries ``embedment_m`` (top of that pour to the outside of the hook) beside the
    ``development_m`` (ldh) it needs; ``integrity.reinforcement_layout`` compares them.
    """

    key: str
    role: str
    bar: int
    coating: str
    spacing_in: float | None
    path: tuple[Vec3, ...]
    closed: bool
    diameter_m: float
    placed_length_m: float
    lap_length_m: float = 0.0
    hook_length_m: float = 0.0
    hook_kinds: tuple[str, ...] = ()
    piece: int = 1
    pieces: int = 1
    note: str | None = None
    embedment_m: float | None = None
    development_m: float | None = None

    @property
    def cut_length_m(self) -> float:
        return self.placed_length_m + self.lap_length_m + self.hook_length_m


@dataclass(frozen=True)
class ResolvedRebarSet:
    """Every bar one host element carries. ``scope`` is the BOM's member family."""

    host_uid: str
    host_tag: str
    host_kind: str
    storey: str
    scope: str
    bars: tuple[ResolvedBar, ...]
