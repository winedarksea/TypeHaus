"""``mep.takeoff_collar_fit``: a take-off's collar sits on a straight face of its main.

A collar is the branch's width plus its flange or tabs. It must land wholly on one leg of
the parent: not past the run's end, not into the elbow at a turn, and not over a sibling
collar on the same face. Read off ``ResolvedModel.duct_parts`` and the parent's path.
"""

from __future__ import annotations

import math
from collections import defaultdict

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, advisory_fail, not_applicable, passed
from typehaus.quantities import M_PER_IN

_ID = "mep.takeoff_collar_fit"
#: The collar's flange or tabs beyond the branch's own section, each side.
FLANGE_ALLOWANCE_M = 0.5 * M_PER_IN
_TOL_M = M_PER_IN / 16.0
_KINDS = ("takeoff", "tee")


def _half_width(part, main) -> float:
    from typehaus.resolve.duct_part_solids import parse_section

    branch = parse_section(part.branch or part.size)
    return (branch.width / 2.0 if branch else 0.0) + FLANGE_ALLOWANCE_M


def _leg(main, point) -> tuple[int, float, float] | None:
    """(leg index, station along it, leg length) of the leg nearest ``point``."""
    pts = [(x, y, z) for (x, y), z in zip(main.path, main.z_m, strict=True)]
    best = None
    for i, (a, b) in enumerate(zip(pts, pts[1:], strict=False)):
        ab = [q - p for p, q in zip(a, b, strict=True)]
        length = math.sqrt(sum(c * c for c in ab))
        if length < 1e-9:
            continue
        s = sum((point[k] - a[k]) * ab[k] for k in range(3)) / length
        t = max(0.0, min(length, s))
        gap = math.dist(point, [a[k] + ab[k] * t / length for k in range(3)])
        if best is None or gap < best[0]:
            best = (gap, i, s, length)
    return None if best is None else best[1:]


def _corner_tee(main, point, axis) -> bool:
    """A branch at an interior vertex carrying straight on along one adjacent leg: the
    corner is itself the tee, not a collar on a face."""
    pts = [(x, y, z) for (x, y), z in zip(main.path, main.z_m, strict=True)]
    for i in range(1, len(pts) - 1):
        if math.dist(pts[i], point) > 3.0 * M_PER_IN:
            continue
        for other in (pts[i - 1], pts[i + 1]):
            leg = [b - a for a, b in zip(other, pts[i], strict=True)]
            n = math.sqrt(sum(c * c for c in leg))
            if n > 1e-9 and abs(sum(c * a for c, a in zip(leg, axis, strict=True))) / n > 0.99:
                return True
    return False


def _turn_allowance(main) -> float:
    """How far an elbow at an interior vertex eats into the straight face."""
    return (main.diameter_m or max(main.width_m, main.depth_m)) / 2.0


@check(Tier.ADVISORY, _ID)
def takeoff_collar_fit(ctx: CheckContext) -> list[Finding]:
    ducts = {d.tag: d for d in ctx.model.ducts
             if len(d.path) >= 2 and len(d.z_m) == len(d.path)}
    parts = [p for p in ctx.model.duct_parts if p.kind in _KINDS and p.run_tag in ducts]
    if not parts:
        return [not_applicable(_ID, "no take-off or tee on a run")]
    out: list[Finding] = []
    faces: dict[tuple[str, int], list[tuple[object, float, float]]] = defaultdict(list)
    for part in parts:
        main = ducts[part.run_tag]
        leg = _leg(main, part.point)
        if leg is None or _corner_tee(main, part.point, part.axis):
            continue
        index, station, length = leg
        r = _half_width(part, main)
        last = len(main.path) - 2
        lo = 0.0 if index == 0 else _turn_allowance(main)
        hi = length - (0.0 if index == last else _turn_allowance(main))
        name = f"{part.other or 'branch'}'s collar on {main.tag}"
        if station - r < lo - _TOL_M or station + r > hi + _TOL_M:
            where = ("the run's end" if (station - r < lo and index == 0)
                     or (station + r > hi and index == last) else "a turn")
            over = max(lo - (station - r), station + r - hi) / M_PER_IN
            out.append(advisory_fail(
                _ID, f"{name} runs {over:.2f}\" past {where}: a collar needs a straight face",
                (main.tag, part.other or main.tag),
                fix="move the branch along the main, or extend the main past it"))
        faces[(main.tag, index)].append((part, station, r))
    for (tag, _), entries in sorted(faces.items()):
        for i, (a, sa, ra) in enumerate(entries):
            for b, sb, rb in entries[i + 1:]:
                same_face = sum(x * y for x, y in zip(a.axis, b.axis, strict=True)) > 0.99
                if same_face and abs(sa - sb) < ra + rb - _TOL_M:
                    out.append(advisory_fail(
                        _ID, f"{a.other} and {b.other} collars overlap on {tag}'s face: "
                             f"{abs(sa - sb) / M_PER_IN:.2f}\" centre to centre, "
                             f"{(ra + rb) / M_PER_IN:.2f}\" needed",
                        (tag, a.other or tag, b.other or tag),
                        fix="space the branches along the main"))
    if not out:
        out.append(passed(_ID, f"{len(parts)} take-off/tee collar(s) each sit on a straight "
                               "face of their main"))
    return out
