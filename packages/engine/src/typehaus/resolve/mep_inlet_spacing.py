"""How close two branch fittings may stack on one drain, read off the catalog's stations.

Shared by ``mep.drain_inlet_spacing`` (two inlets on a vertical barrel) and the router (a
new branch tied onto a main keeps that pitch from every inlet already on it). The pitch of a
pair is the lower fitting's branch-to-top plus the upper's branch-to-bottom, plus a nipple of
two socket depths unless the upper is a street pattern whose spigot seats in the lower's hub
(Charlotte Pipe SUB-PAC-PVC-DWV, ``library/fittings.py``).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from typehaus.hardware.fittings import SERVICE_DRAIN, FittingSpec, fitting_catalog
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_fitting_direction import WYE_KINDS, approach_kinds

#: A plan offset under this is "on the same point": the 1/16" grid.
SAME_POINT_M = 0.0015875


def nominal_in(diameter_m: float) -> float:
    """A nominal size in inches, to the sixteenth the catalog is keyed on."""
    return round(diameter_m / M_PER_IN * 16) / 16


def stack_candidates(kinds: Sequence[str], size_in: float) -> list[FittingSpec]:
    """Catalogued full-size patterns of these kinds that publish their stack stations."""
    return [f for f in fitting_catalog()
            if f.service == SERVICE_DRAIN and f.kind in kinds and f.nominal_in == size_in
            and f.branch_in == size_in and f.branch_to_top_in is not None
            and f.branch_to_bottom_in is not None
            and (f.spigot_bottom or f.socket_depth_in is not None)]


def tightest_pair(lowers: Sequence[FittingSpec], uppers: Sequence[FittingSpec]
                  ) -> tuple[float, FittingSpec, FittingSpec] | None:
    """``(pitch in, lower, upper)`` for the closest catalogued stack of the two sets."""
    best = None
    for lower in lowers:
        for upper in uppers:
            nipple = 0.0 if upper.spigot_bottom else 2 * upper.socket_depth_in
            pitch = lower.branch_to_top_in + upper.branch_to_bottom_in + nipple
            if best is None or pitch < best[0]:
                best = (pitch, lower, upper)
    return best


def approach_deg(run: Any, point: tuple[float, float]) -> float | None:
    """Degrees off level of the segment by which ``run`` arrives at ``point``."""
    for end, prev in ((0, 1), (-1, -2)):
        x, y = run.path[end]
        if abs(x - point[0]) > SAME_POINT_M or abs(y - point[1]) > SAME_POINT_M:
            continue
        px, py = run.path[prev]
        rise = abs(run.z_m[prev] - run.z_m[end])
        return math.degrees(math.atan2(rise, math.hypot(px - x, py - y)))
    return None


def inlet_candidates(run: Any, point: tuple[float, float], size_in: float
                     ) -> list[FittingSpec]:
    """The catalogued full-size patterns an inlet may be, by how it arrives."""
    slope = approach_deg(run, point)
    if slope is None:
        return []
    return stack_candidates(approach_kinds(slope), size_in)


def tightest_stack(barrel: Any, low: Any, high: Any, point: tuple[float, float]
                   ) -> tuple[float, FittingSpec, FittingSpec] | None:
    """``(pitch in, lower, upper)`` for two inlets on one barrel, or None."""
    size = nominal_in(barrel.diameter_m)
    if nominal_in(low.diameter_m) != size or nominal_in(high.diameter_m) != size:
        return None
    return tightest_pair(inlet_candidates(low, point, size),
                         inlet_candidates(high, point, size))


def main_inlet_pitch_m(main_diameter_m: float) -> float | None:
    """The tightest pitch two wye branches keep along a horizontal main, or None.

    A branch onto a horizontal main enters by a wye or combo (UPC 706); None where the
    catalog dimensions no wye at this size — the caller then keeps the check's screen.
    """
    wyes = stack_candidates(WYE_KINDS, nominal_in(main_diameter_m))
    found = tightest_pair(wyes, wyes)
    return None if found is None else found[0] * M_PER_IN


def level_inlets(pipe_runs: Sequence[Any], exclude: frozenset[str] = frozenset()
                 ) -> list[tuple[float, float, float, str]]:
    """``(x, y, z, main)`` of every drain branch tied onto a LEVEL leg of its main.

    ``exclude`` names runs a proposal replaces: their own inlets are about to go.
    """
    from typehaus.resolve.mep_tie_ins import drain_tie_ins

    by_tag = {run.tag: run for run in pipe_runs}
    out = []
    for child_tag, main_tag in sorted(drain_tie_ins(pipe_runs).items()):
        child, main = by_tag.get(child_tag), by_tag.get(main_tag)
        if child_tag in exclude or child is None or main is None or not child.path:
            continue
        if child.z_m is None or main.z_m is None:
            continue
        (x, y), z = child.path[-1], child.z_m[-1]
        if _on_level_leg(main, (x, y)):
            out.append((x, y, z, main_tag))
    return out


def _on_level_leg(run: Any, point: tuple[float, float]) -> bool:
    for i in range(len(run.path) - 1):
        (ax, ay), (bx, by) = run.path[i], run.path[i + 1]
        length = math.hypot(bx - ax, by - ay)
        if length < SAME_POINT_M:
            continue
        t = ((point[0] - ax) * (bx - ax) + (point[1] - ay) * (by - ay)) / length ** 2
        if -1e-9 <= t <= 1 + 1e-9 and math.hypot(ax + t * (bx - ax) - point[0],
                                                  ay + t * (by - ay) - point[1]) < SAME_POINT_M:
            return True
    return False
