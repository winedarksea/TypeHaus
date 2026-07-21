"""Element matching: GlobalId keys, Hungarian fallback, replace detection (→ 20 §Diff)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from typehaus.diff.model import DiffElem

# Cost-matrix weights over (class mismatch, storey mismatch, centroid dist, bbox dist).
_W_CLASS = 100.0
_W_STOREY = 5.0
_W_CENTROID = 4.0
_W_BBOX = 3.0
# Above this cost a pair is not a credible match (→ replace stays delete+add).
_MATCH_THRESHOLD = 6.0


@dataclass(frozen=True)
class Match:
    baseline: DiffElem | None   # None => added (present only in the external model)
    external: DiffElem | None   # None => deleted (present only in the baseline)
    keyed: bool                 # matched by GlobalId (vs. geometric fallback)
    cost: float = 0.0


def _pair_cost(a: DiffElem, b: DiffElem) -> float:
    cost = _W_CENTROID * a.centroid_distance(b) + _W_BBOX * a.bbox_distance(b)
    if a.ifc_class != b.ifc_class:
        cost += _W_CLASS
    if a.storey != b.storey:
        cost += _W_STOREY
    return cost


def match_elements(baseline: list[DiffElem], external: list[DiffElem]) -> list[Match]:
    """Match two element sets. Order: GlobalId keys, then Hungarian over the leftovers."""
    matches: list[Match] = []
    by_gid = {e.global_id: e for e in external if e.global_id}
    baseline_guid_counts = Counter(e.global_id for e in baseline if e.global_id)
    external_guid_counts = Counter(e.global_id for e in external if e.global_id)
    used_ext: set[int] = set()

    # 1. Key by GlobalId (survives tools that preserve GUIDs; identity is the immutable uid).
    unkeyed_base: list[DiffElem] = []
    for b in baseline:
        # Empty/legacy source UIDs can derive the same GlobalId for multiple elements.
        # Treat a duplicate as unkeyed; a geometric match is safer than silently pairing
        # unrelated occurrences based on an invalid non-unique IFC identifier.
        ext = (by_gid.get(b.global_id) if b.global_id
               and baseline_guid_counts[b.global_id] == 1
               and external_guid_counts[b.global_id] == 1 else None)
        if ext is not None:
            matches.append(Match(b, ext, keyed=True, cost=_pair_cost(b, ext)))
            used_ext.add(id(ext))
        else:
            unkeyed_base.append(b)

    leftover_ext = [e for e in external if id(e) not in used_ext]

    # 2. Hungarian fallback + replace detection over the leftovers (same cost matrix).
    paired_b, paired_e = _hungarian(unkeyed_base, leftover_ext)
    for bi, ei in zip(paired_b, paired_e):
        b, e = unkeyed_base[bi], leftover_ext[ei]
        if _pair_cost(b, e) <= _MATCH_THRESHOLD:
            matches.append(Match(b, e, keyed=False, cost=_pair_cost(b, e)))
        else:  # below confidence → honest delete + add
            matches.append(Match(b, None, keyed=False))
            matches.append(Match(None, e, keyed=False))
    for bi, b in enumerate(unkeyed_base):
        if bi not in paired_b:
            matches.append(Match(b, None, keyed=False))
    for ei, e in enumerate(leftover_ext):
        if ei not in paired_e:
            matches.append(Match(None, e, keyed=False))
    return matches


def _hungarian(
    rows: list[DiffElem], cols: list[DiffElem]
) -> tuple[list[int], list[int]]:
    """Optimal assignment via scipy; returns paired (row_idx, col_idx) lists."""
    if not rows or not cols:
        return [], []
    try:
        import numpy as np
        from scipy.optimize import linear_sum_assignment
    except ImportError:  # pragma: no cover - scipy is a hard dep, but degrade safely
        return _greedy(rows, cols)
    cost = np.array([[_pair_cost(r, c) for c in cols] for r in rows], dtype=float)
    r_idx, c_idx = linear_sum_assignment(cost)
    return list(r_idx), list(c_idx)


def _greedy(rows: list[DiffElem], cols: list[DiffElem]) -> tuple[list[int], list[int]]:
    pairs = sorted(
        ((_pair_cost(r, c), i, j) for i, r in enumerate(rows) for j, c in enumerate(cols)),
    )
    used_r: set[int] = set()
    used_c: set[int] = set()
    pr: list[int] = []
    pc: list[int] = []
    for _cost, i, j in pairs:
        if i in used_r or j in used_c:
            continue
        used_r.add(i)
        used_c.add(j)
        pr.append(i)
        pc.append(j)
    return pr, pc
