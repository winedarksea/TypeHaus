"""The ``duct_fabrication`` stage: each duct run drawn as the pieces a crew hangs (#136).

``resolve/mep.py`` gives a run one ``{uid}-run`` sweep along its whole path. Here it is
split, in place, into straight stretches and elbows:

* an elbow (``elbow_geometry``) at every turn whose ``FittingRecord`` names a part with a
  radius; a gap keeps the butt inside its stretch;
* the stretches are what is left once every occupied interval is taken out: the elbows,
  a branch's take-off collar (``takeoff_solids.takeoff_branch_start``), collar and in-line
  dampers, and an end boot's tip past ``boot_solids.boot_inlet_point``. Those parts draw
  themselves (``duct_part_solids``), so nothing draws twice. An integral part, a side boot
  or a boot the register's neck draws trims nothing.

Pieces keep the run's category, tag (``{tag}-RUN``) and storey; ``host_ref`` is the run's
tag, as is ``group``; the first stretch, ``{uid}-run``, stays at the run solid's index and
so leads the pick group. Stretches are ``{uid}-run``, ``{uid}-run-2``, ... and elbows
``{uid}-elbow-01``, ... — run body like the stretches, so not ``derived`` (a section cuts
it; the bill stays on the run and its fitting records). A piece with a
vertical leg carries ``vertical_up`` (``sweep.carried_up``: an elbow its own, a riser the
level leg below it), so a section neither rolls at a riser nor twists inside an elbow.
``ResolvedDuct.path`` and ``length_m`` are untouched, so the bill does not move.
"""

from __future__ import annotations

import bisect
import math
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from typehaus.resolve.elbow_geometry import ElbowArc, elbow_arcs, elbow_radius_m
from typehaus.resolve.sweep import (
    carried_up,
    clean_path,
    sweep_plan_silhouette,
    sweep_z_extent,
)

Vec3 = tuple[float, float, float]

#: A stretch shorter than this is not drawn (an elbow meeting a boot, say).
MIN_STRETCH_M = 1e-3
#: A fitting record's point within this of a path vertex is that vertex.
_VERTEX_MATCH_M = 1e-4
_TRIMS_BRANCH = ("takeoff", "tee")
_TRIMS_OWN = ("collar_damper", "damper", "boot")


@dataclass(frozen=True)
class Occupied:
    """A stretch of a run's path, by station from its first vertex, a fitting fills."""

    start_m: float
    end_m: float
    kind: str


def _stations(pts: Sequence[Vec3]) -> list[float]:
    out = [0.0]
    for a, b in zip(pts, pts[1:], strict=False):
        out.append(out[-1] + math.dist(a, b))
    return out


def station_of(pts: Sequence[Vec3], cum: Sequence[float], point: Sequence[float]) -> float:
    """The station of the path point nearest ``point``."""
    best = (math.inf, 0.0)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        n2 = ab[0] ** 2 + ab[1] ** 2 + ab[2] ** 2
        if n2 < 1e-18:
            continue
        t = max(0.0, min(1.0, sum((point[k] - a[k]) * ab[k] for k in range(3)) / n2))
        gap = math.dist(point, (a[0] + ab[0] * t, a[1] + ab[1] * t, a[2] + ab[2] * t))
        if gap < best[0]:
            best = (gap, cum[i] + t * (cum[i + 1] - cum[i]))
    return best[1]


def point_at(pts: Sequence[Vec3], cum: Sequence[float], s: float) -> Vec3:
    i = max(0, min(len(pts) - 2, bisect.bisect_right(cum, s) - 1))
    span = cum[i + 1] - cum[i]
    t = 0.0 if span <= 0.0 else max(0.0, min(1.0, (s - cum[i]) / span))
    a, b = pts[i], pts[i + 1]
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def sub_path(pts: Sequence[Vec3], cum: Sequence[float], a: float, b: float) -> tuple:
    inner = [pts[i] for i in range(len(pts)) if a < cum[i] < b]
    return clean_path([point_at(pts, cum, a), *inner, point_at(pts, cum, b)])


def _duct_path(duct: Any) -> tuple[Vec3, ...]:
    z = duct.z_m or ()
    if len(z) != len(duct.path):
        return ()
    return clean_path([(x, y, zz) for (x, y), zz in zip(duct.path, z, strict=True)])


def _arcs(pts: Sequence[Vec3], records: Sequence[Any], standard: Any) -> list[ElbowArc]:
    radii: dict[int, float] = {}
    for record in records:
        if record.kind != "elbow" or record.index is None:
            continue
        index = next((i for i, p in enumerate(pts)
                      if math.dist(p, record.point) < _VERTEX_MATCH_M), record.index)
        radius = elbow_radius_m(record, standard)
        if radius is not None:
            radii[index] = radius
    return elbow_arcs(pts, radii)


def _part_intervals(model: Any, duct: Any, pts: Sequence[Vec3], cum: Sequence[float],
                    parts: Sequence[Any], necked: set[str]) -> list[Occupied]:
    from typehaus.resolve.boot_solids import boot_inlet_point
    from typehaus.resolve.duct_mesh import _add, _unit, parse_section

    out: list[Occupied] = []
    total = cum[-1]
    for part in parts:
        if part.integral:
            continue
        axis = _unit(part.axis)
        if axis is None:
            continue
        s0 = station_of(pts, cum, part.point)
        if part.kind in _TRIMS_BRANCH and part.other == duct.tag:
            s1 = station_of(pts, cum, _add(part.point, axis, _branch_start(model, part, axis)))
        elif part.run_tag != duct.tag:
            continue
        elif part.kind == "collar_damper":
            from typehaus.resolve.boot_solids import COLLAR_LENGTH_M

            s1 = station_of(pts, cum, _add(part.point, axis, COLLAR_LENGTH_M))
        elif part.kind == "damper":
            size = parse_section(part.size)
            half = (part.length_m or (size.larger if size else 0.0)) / 2.0
            s0 = station_of(pts, cum, _add(part.point, axis, -half))
            s1 = station_of(pts, cum, _add(part.point, axis, half))
        elif part.kind == "boot" and part.joint != "side" and part.other not in necked:
            s1 = station_of(pts, cum, boot_inlet_point(part))
            s0 = total if s0 > total / 2.0 else 0.0  # from the run's end it stands at
        else:
            continue
        lo, hi = min(s0, s1), max(s0, s1)
        if hi - lo > 1e-6:
            out.append(Occupied(lo, hi, part.kind))
    return out


def _branch_start(model: Any, part: Any, axis: Vec3) -> float:
    try:
        from typehaus.resolve.takeoff_solids import takeoff_branch_start
    except ImportError:  # pragma: no cover - the P2-E contract's fallback
        from typehaus.quantities import M_PER_IN
        from typehaus.resolve.duct_mesh import parse_section

        size = parse_section(part.size)
        return (size.width / 2.0 if size else 0.0) + 2.0 * M_PER_IN
    return takeoff_branch_start(model, part)


def _run_plan(model: Any, duct: Any, pts: Sequence[Vec3], records: Sequence[Any],
              standard: Any, parts: Sequence[Any], necked: set[str]
              ) -> tuple[list[ElbowArc], list[Occupied], list[float]]:
    cum = _stations(pts)
    fittings = _part_intervals(model, duct, pts, cum, parts, necked)
    # An elbow inside a boot or collar is that part's own turn: drawn once, by the part.
    arcs = [a for a in _arcs(pts, records, standard)
            if not any(f.start_m - 1e-6 <= cum[a.index] - a.setback_m
                       and cum[a.index] + a.setback_m <= f.end_m + 1e-6 for f in fittings)]
    occupied = [Occupied(cum[a.index] - a.setback_m, cum[a.index] + a.setback_m, "elbow")
                for a in arcs]
    occupied += fittings
    return arcs, sorted(occupied, key=lambda o: (o.start_m, o.end_m)), cum


def _context(model: Any) -> tuple[dict[str, list], Any, dict[str, list], set[str]]:
    from typehaus.resolve.duct_part_solids import neck_drawn
    from typehaus.resolve.duct_standard import duct_standard
    from typehaus.resolve.mep_fittings import FAMILY_DUCT, fitting_records

    records: dict[str, list] = {}
    for record in fitting_records(model):
        if record.family == FAMILY_DUCT:
            records.setdefault(record.run_tag, []).append(record)
    parts: dict[str, list] = {}
    for part in model.duct_parts:
        for tag in {part.run_tag, part.other}:
            if tag is not None:
                parts.setdefault(tag, []).append(part)
    standard = duct_standard(getattr(model, "plan", None))[0]
    return records, standard, parts, neck_drawn(model) if model.duct_parts else set()


def occupied_intervals(model: Any, duct: Any) -> list[Occupied]:
    """Where along ``duct`` (stations on its cleaned 3D path) a fitting is drawn instead of
    the straight duct, sorted. Elbows, take-off collar, dampers and end boots."""
    pts = _duct_path(duct)
    if len(pts) < 2:
        return []
    records, standard, parts, necked = _context(model)
    return _run_plan(model, duct, pts, records.get(duct.tag, ()), standard,
                     parts.get(duct.tag, ()), necked)[1]


def _free(occupied: Sequence[Occupied], total: float) -> list[tuple[float, float]]:
    """``[0, total]`` less the union of ``occupied``."""
    out, cursor = [], 0.0
    for o in occupied:
        if o.start_m > cursor + MIN_STRETCH_M:
            out.append((cursor, min(o.start_m, total)))
        cursor = max(cursor, o.end_m)
    if total > cursor + MIN_STRETCH_M:
        out.append((cursor, total))
    return [(a, b) for a, b in out if b - a > MIN_STRETCH_M]


def _vertical(a: Sequence[float], b: Sequence[float]) -> bool:
    return math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-9


def _stretch_up(pts: Sequence[Vec3], cum: Sequence[float], start_m: float,
                piece: Sequence[Vec3]) -> Vec3 | None:
    """``carried_up`` for a stretch: its own level leg's, else the run's nearest level leg
    before (else after) it, so a riser between two elbows holds the frame of the one below."""
    if not any(_vertical(a, b) for a, b in zip(piece, piece[1:], strict=False)):
        return None
    own = carried_up(piece)
    if own is not None:
        return own
    legs = list(zip(pts, pts[1:], strict=False))
    at = max(0, min(len(legs) - 1, bisect.bisect_right(cum, start_m + 1e-9) - 1))
    level = [i for i in range(at, -1, -1) if not _vertical(*legs[i])]
    level += [i for i in range(at, len(legs)) if not _vertical(*legs[i])]
    if not level:
        return None
    a, b = legs[level[0]]
    h = math.hypot(b[0] - a[0], b[1] - a[1])
    return (-(b[0] - a[0]) / h, -(b[1] - a[1]) / h, 0.0)


def _piece(base: Any, uid: str, path: tuple, vertical_up: Vec3 | None, host: str,
           group: str) -> Any:
    from typehaus.resolve.model import SolidSweep

    sweep = SolidSweep(path=path, profile=base.sweep.profile, vertical_up=vertical_up)
    z0, z1 = sweep_z_extent(sweep)
    return replace(base, uid=uid, outline=sweep_plan_silhouette(sweep), z0_m=z0, z1_m=z1,
                   sweep=sweep, host_ref=host, group=group)


def fabricate_run(model: Any, duct: Any, solid: Any, records: Sequence[Any], standard: Any,
                  parts: Sequence[Any], necked: set[str]) -> list[Any]:
    """The pieces replacing ``solid`` (``{uid}-run``), the leader first then along the run.
    ``[solid]`` re-hosted where nothing splits it or nothing straight survives."""
    base_uid = solid.uid
    group = duct.tag  # like a railing's pieces: group == host_ref
    pts = clean_path(solid.sweep.path)
    rehosted = replace(solid, host_ref=duct.tag, group=group)
    if len(pts) < 2:
        return [rehosted]
    arcs, occupied, cum = _run_plan(model, duct, pts, records, standard, parts, necked)
    free = _free(occupied, cum[-1])
    if not free:
        return [rehosted]
    stretches = []
    for n, (a, b) in enumerate(free, start=1):
        path = sub_path(pts, cum, a, b)
        uid = base_uid if n == 1 else f"{base_uid}-{n}"
        up = _stretch_up(pts, cum, a, path)
        stretches.append((a, _piece(solid, uid, path, up, duct.tag, group)))
    stem = base_uid.removesuffix("-run")
    elbows = [(cum[arc.index] - arc.setback_m,
               _piece(solid, f"{stem}-elbow-{n:02d}", arc.path, carried_up(arc.path),
                      duct.tag, group))
              for n, arc in enumerate(arcs, start=1)]
    rest = sorted(stretches[1:] + elbows, key=lambda item: item[0])
    return [stretches[0][1], *(piece for _, piece in rest)]


def fabricate_runs(model: Any) -> None:
    """Replace every duct's ``{uid}-run`` solid in place with its pieces (module docstring)."""
    if not model.ducts:
        return
    records, standard, parts, necked = _context(model)
    index = {s.uid: i for i, s in enumerate(model.solids)}
    replacements: list[tuple[int, list[Any]]] = []
    for duct in model.ducts:
        at = index.get(f"{duct.uid or duct.tag}-run")
        solid = model.solids[at] if at is not None else None
        if solid is None or solid.sweep is None:
            continue
        replacements.append((at, fabricate_run(model, duct, solid, records.get(duct.tag, ()),
                                               standard, parts.get(duct.tag, ()), necked)))
    for at, pieces in sorted(replacements, key=lambda item: -item[0]):
        model.solids[at:at + 1] = pieces
