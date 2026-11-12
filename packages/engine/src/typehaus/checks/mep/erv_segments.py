"""A trunk charged only over the stretch a path's air travels, at that stretch's flow (§9).

``erv_routes`` decides WHICH trunks a path crosses; this decides HOW MUCH of each. A path
that leaves a trunk at a tap (the next trunk on its route ends on this one's interior) pays
from where it entered to that tap. Beyond each tap it passes, the trunk carries its
``design_cfm`` less that tap's, so a path that runs a trunk end to end pays each stretch at
its own flow. Where the entry or exit cannot be placed, the caller keeps the whole run at
its ``design_cfm``: the conservative rule, never a silent saving.
"""

from __future__ import annotations

import math

from typehaus.checks.mep.erv_landings import _end_host
from typehaus.checks.registry import CheckContext
from typehaus.resolve.mep_soffit import DUCT_JOINT_TOLERANCE_M


def _points(duct) -> list[tuple[float, float, float]]:
    zs = duct.z_m if duct.z_m and len(duct.z_m) == len(duct.path) else [0.0] * len(duct.path)
    return [(x, y, z) for (x, y), z in zip(duct.path, zs, strict=True)]


def station(duct, point) -> tuple[float, float]:
    """``(distance along the run to point's foot, distance off it)``, both metres."""
    pts, run, best = _points(duct), 0.0, (0.0, math.inf)
    for a, b in zip(pts, pts[1:], strict=False):
        ab = [b[i] - a[i] for i in range(3)]
        length = math.sqrt(sum(c * c for c in ab))
        t = 0.0 if length == 0 else max(0.0, min(1.0, sum(
            ab[i] * (point[i] - a[i]) for i in range(3)) / (length * length)))
        off = math.dist(point, [a[i] + t * ab[i] for i in range(3)])
        if off < best[1]:
            best = (run + t * length, off)
        run += length
    return best


def run_length(duct) -> float:
    pts = _points(duct)
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:], strict=False))


def _ends(duct):
    pts = _points(duct)
    return pts[0], pts[-1]


def _tap_on(trunk, other) -> float | None:
    """Station on ``trunk`` where an end of ``other`` lands on its interior, else None."""
    total = run_length(trunk)
    for end in _ends(other):
        at, off = station(trunk, end)
        if off <= DUCT_JOINT_TOLERANCE_M and DUCT_JOINT_TOLERANCE_M < at < total \
                - DUCT_JOINT_TOLERANCE_M:
            return at
    return None


def _end_at(ctx: CheckContext, duct, node, by_tag) -> float | None:
    """Station (0 or length) of the end of ``duct`` that meets ``node``, else None."""
    total = run_length(duct)
    for index, at in ((0, 0.0), (-1, total)):
        if node[0] == "E" and _end_host(ctx, duct, index)[0] == node[1]:
            return at
        if node[0] == "T" and node[1] in by_tag:
            end = _ends(duct)[0 if index == 0 else 1]
            if station(by_tag[node[1]], end)[1] <= DUCT_JOINT_TOLERANCE_M:
                return at
    return None


def stretches(ctx: CheckContext, duct, nodes: list, k: int, trunks: list
              ) -> list[tuple[float, float, float]] | None:
    """``[(from m, to m, cfm)]`` the path ``nodes`` charges ``duct`` (its node is ``nodes[k]``).

    None when nothing is saved over the whole run at ``design_cfm``, or when an end
    cannot be placed: the caller then charges the run whole.
    """
    by_tag = {t.tag: t for t in trunks}
    total, cfm = run_length(duct), duct.design_cfm
    if cfm is None or k == 0:
        return None
    entry = _end_at(ctx, duct, nodes[k - 1], by_tag)
    if entry is None:
        return None
    nxt = nodes[k + 1] if k + 1 < len(nodes) else None
    exit_at = None
    if nxt is not None and nxt[0] == "T" and nxt[1] in by_tag:
        exit_at = _tap_on(duct, by_tag[nxt[1]])
    if exit_at is None:
        exit_at = (_end_at(ctx, duct, nxt, by_tag) if nxt is not None else None)
        if exit_at is None or exit_at == entry:
            exit_at = total - entry  # the far end
    lo, hi = sorted((entry, exit_at))
    # Taps between entry and exit take their flow off every stretch beyond them.
    taps = sorted((abs(at - entry), other.design_cfm) for other in trunks
                  if other is not duct and other.design_cfm
                  and (at := _tap_on(duct, other)) is not None and lo < at < hi)
    out, start, flow = [], 0.0, cfm
    for distance, taken in taps:
        out.append((start, distance, flow))
        start, flow = distance, flow - taken
        if flow <= 0:
            return None  # the authored flows do not add up: charge it whole
    out.append((start, hi - lo, flow))
    if len(out) == 1 and hi - lo >= total - DUCT_JOINT_TOLERANCE_M:
        return None
    # Back to stations from the run's start, for the elbows' positions.
    return [(entry + a, entry + b, q) if entry <= exit_at else (entry - b, entry - a, q)
            for a, b, q in out]
