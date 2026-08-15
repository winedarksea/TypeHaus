"""Plan geometry the construction finders place their returns with.

Strips, stack overlaps and condition keys — the small vocabulary that turns "these two
walls meet" into an outline, a run length and the ``condition_key`` a Transition later
joins on. Kept apart from the finders because the *placement* rules (what counts as a
bearing overlap, how wide a strip runs off an anchor) are shared physics, while each finder
owns only which elements to run them over.
"""

from __future__ import annotations

from typehaus.resolve.geometry import add, length, normal, scale, sub, unit
from typehaus.resolve.model import ResolvedModel, ResolvedWall

# A framed wall must overlap a concrete wall below by at least this much before a sill plate
# is billed — a token clip of a passing wall is not a bearing line. Matches the stacking
# pass's minimum vertical stack overlap (2 ft) so the two agree on what "stacks" means.
_MIN_STACK_OVERLAP_M = 0.6096  # 2 ft
_EPS = 1e-6


# --- geometry helpers ---------------------------------------------------------
def _axis_dir(rw: ResolvedWall) -> tuple[float, float]:
    return unit(sub(rw.axis[1], rw.axis[0]))


def _strip(anchor: tuple[float, float], direction: tuple[float, float],
           run_m: float, near: float, far: float) -> list[tuple[float, float]]:
    """A rectangle from ``anchor`` running ``run_m`` along ``direction``, spanning the
    perpendicular offsets ``near``..``far`` (positive = left of ``direction``)."""
    tip = add(anchor, scale(direction, run_m))
    n = normal(direction)
    return [
        add(anchor, scale(n, near)),
        add(tip, scale(n, near)),
        add(tip, scale(n, far)),
        add(anchor, scale(n, far)),
    ]


def _stack_overlap(lower: ResolvedWall, upper: ResolvedWall) -> \
        tuple[tuple[float, float], tuple[float, float]] | None:
    """The collinear plan overlap of two stacked walls as a world segment, or None.

    Tolerant of the exterior-insulation datum offset (a ``face("sheathing-ext")`` framed
    wall sits outboard of the concrete centreline): the perpendicular gate is the two walls'
    combined depth, i.e. "the framed wall sits within the concrete wall's footprint band".
    """
    a0, a1 = lower.axis
    da = _axis_dir(lower)
    db = _axis_dir(upper)
    if length(da) < _EPS or length(db) < _EPS:
        return None
    if abs(da[0] * db[1] - da[1] * db[0]) > 1e-3:  # not parallel
        return None
    n = normal(da)
    perp = abs(sub(upper.axis[0], a0)[0] * n[0] + sub(upper.axis[0], a0)[1] * n[1])
    if perp > (lower.thickness_m + upper.thickness_m):
        return None

    def proj(point: tuple[float, float]) -> float:
        v = sub(point, a0)
        return v[0] * da[0] + v[1] * da[1]

    lo_a, hi_a = 0.0, length(sub(a1, a0))
    lo_b, hi_b = sorted((proj(upper.axis[0]), proj(upper.axis[1])))
    lo, hi = max(lo_a, lo_b), min(hi_a, hi_b)
    if hi - lo < _MIN_STACK_OVERLAP_M:
        return None
    return add(a0, scale(da, lo)), add(a0, scale(da, hi))


def _walls_by_storey(model: ResolvedModel) -> dict[str, list[ResolvedWall]]:
    out: dict[str, list[ResolvedWall]] = {}
    for rw in model.walls:
        out.setdefault(rw.storey, []).append(rw)
    return out


def _condition_key(prefix: str, *assemblies: str) -> str:
    return f"{prefix}:{'|'.join(sorted(set(assemblies)))}"
