"""Joist-bay edges with the along-axis interval each one reaches.

A bay edge is a joist line only over the stretch its member exists: a sister ply or a joist
that stops short bounds a bay over its own extent, not over the whole floor (the pattern
``blocking_parts.bay_edges_at`` already takes for blocks). Members end to end on one
station merge into one interval. ``mep_queries`` builds these from ``bay_edge_members``;
routing and the bay checks read them through it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from typehaus.resolve.framing.profiles import cross_section

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import FramedMember, ResolvedFloor

#: A sixteenth of an inch: two ends this close are one end.
TOL_M = 0.0015875


@dataclass(frozen=True)
class BayEdge:
    """One continuous stretch of a joist line: ``station`` across, ``lo_m..hi_m`` along."""

    station: float
    lo_m: float
    hi_m: float
    width_m: float

    def reaches(self, lo: float, hi: float, tol: float = TOL_M) -> bool:
        return self.lo_m - tol <= max(lo, hi) and min(lo, hi) <= self.hi_m + tol

    def faces(self) -> tuple[float, float]:
        return self.station - self.width_m / 2.0, self.station + self.width_m / 2.0


@dataclass(frozen=True)
class BayPiece:
    """A bay between two adjacent edges, over the along interval both reach."""

    lo_m: float
    hi_m: float
    near: tuple[float, float]  # the lower edge's (low, high) faces
    far: tuple[float, float]  # the upper edge's


def bay_edges(floor: ResolvedFloor, members: Sequence[FramedMember]) -> list[BayEdge]:
    """Merged edges of ``members``, sorted by (station, lo)."""
    along, across = (0, 1) if floor.direction == "x" else (1, 0)
    groups: dict[float, list[tuple[float, float, float, float]]] = {}
    for m in members:
        lo, hi = sorted((m.p0[along], m.p1[along]))
        groups.setdefault(round(m.p0[across], 6), []).append(
            (lo, hi, cross_section(m.profile).width_m, m.p0[across]))
    out: list[BayEdge] = []
    for key in sorted(groups):
        runs: list[list[float]] = []
        for lo, hi, width, station in sorted(groups[key]):
            if runs and lo <= runs[-1][1] + TOL_M:
                runs[-1][1] = max(runs[-1][1], hi)
                runs[-1][2] = max(runs[-1][2], width)
            else:
                runs.append([lo, hi, width, station])
        out.extend(BayEdge(station, lo, hi, width) for lo, hi, width, station in runs)
    return out


def edges_over(edges: Sequence[BayEdge], span: tuple[float, float] | None,
               tol: float = TOL_M) -> list[BayEdge]:
    """The edges that reach ``span`` along the joists (all of them for None)."""
    return list(edges) if span is None else [e for e in edges if e.reaches(*span, tol)]


def stations(edges: Sequence[BayEdge]) -> list[float]:
    return sorted({e.station for e in edges})


def faces(edges: Sequence[BayEdge]) -> list[tuple[float, float]]:
    """Each station's (low, high) faces, the widest edge setting them, sorted."""
    widths: dict[float, float] = {}
    for e in edges:
        widths[e.station] = max(widths.get(e.station, 0.0), e.width_m)
    return [(s - w / 2.0, s + w / 2.0) for s, w in sorted(widths.items())]


def bay_pieces(edges: Sequence[BayEdge]) -> list[BayPiece]:
    """Every bay between adjacent edges, one piece per along stretch it keeps its two faces.

    Elementary intervals between edge ends are read at their midpoint; adjacent ones with
    the same pair of faces coalesce, so a bay a short ply interrupts comes out as the
    stretches either side of it plus the narrower bays beside the ply.
    """
    marks = sorted({round(v, 6) for e in edges for v in (e.lo_m, e.hi_m)})
    pieces: list[BayPiece] = []
    for lo, hi in zip(marks, marks[1:], strict=False):
        if hi - lo < TOL_M:
            continue
        fs = faces(edges_over(edges, ((lo + hi) / 2.0, (lo + hi) / 2.0), 0.0))
        for near, far in zip(fs, fs[1:], strict=False):
            last = next((i for i in range(len(pieces) - 1, -1, -1)
                         if pieces[i].near == near and pieces[i].far == far), None)
            if last is not None and lo <= pieces[last].hi_m + TOL_M:
                pieces[last] = BayPiece(pieces[last].lo_m, hi, near, far)
            else:
                pieces.append(BayPiece(lo, hi, near, far))
    return pieces
