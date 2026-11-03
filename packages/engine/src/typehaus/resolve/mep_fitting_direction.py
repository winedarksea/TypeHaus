"""Which DWV patterns a change of direction may be, read from how the flow turns (UPC 706).

Shared by ``mep.drain_inlet_spacing`` (which patterns an inlet on a barrel may be) and the
router (what a turn costs, and which turns it may not make). Minnesota is UPC-based: UPC 706
lets a sanitary tee or a short 1/4 bend take flow from horizontal to vertical and nowhere
else; vertical-to-horizontal and horizontal-to-horizontal take a wye, a combination wye and
1/8 bend, or a fitting of equivalent sweep (a long-sweep 1/4 bend, two 1/8 bends). Section
706 governs drainage fittings, so every vent turn may be a plain bend.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from typehaus.hardware.fittings import (
    KIND_COMBO,
    KIND_STREET_TEE,
    KIND_STREET_WYE,
    KIND_TEE,
    KIND_WYE,
)

#: An approach within this of level takes a sanitary pattern; up to WYE_MAX_DEG a wye.
LEVEL_MAX_DEG = 22.5
WYE_MAX_DEG = 67.5

#: Inlet patterns by approach (the stack fittings ``library/fittings.py`` dimensions).
SANITARY_KINDS = (KIND_TEE, KIND_COMBO, KIND_STREET_TEE)
WYE_KINDS = (KIND_WYE, KIND_STREET_WYE)

#: A segment's direction class in the direction of flow.
LEVEL, DOWN, UP = "level", "down", "up"

#: Turn patterns, as a proposal names them.
QUARTER_BEND = "quarter_bend"  # short 1/4 bend, or a sanitary tee on a branch
LONG_SWEEP = "long_sweep"      # long-sweep 1/4 bend, combo, or wye + 1/8 bend
EIGHTH_PAIR = "eighth_pair"    # two 1/8 bends
EIGHTH_BEND = "eighth_bend"    # one 1/8 bend (a 45 degree turn)

#: UPC 706: the patterns each drainage transition may be, in flow order.
ALLOWED: dict[tuple[str, str], tuple[str, ...]] = {
    (LEVEL, DOWN): (QUARTER_BEND, LONG_SWEEP, EIGHTH_PAIR, EIGHTH_BEND),
    (DOWN, LEVEL): (LONG_SWEEP, EIGHTH_PAIR, EIGHTH_BEND),
    (LEVEL, LEVEL): (LONG_SWEEP, EIGHTH_PAIR, EIGHTH_BEND),
    (DOWN, DOWN): (LONG_SWEEP, EIGHTH_PAIR, EIGHTH_BEND),
}

#: Off level, in degrees, past which a pitched drain leg counts as vertical.
_VERTICAL_DEG = 45.0


def approach_kinds(slope_deg: float) -> tuple[str, ...]:
    """The inlet patterns a branch arriving ``slope_deg`` off level may be."""
    if slope_deg <= LEVEL_MAX_DEG:
        return SANITARY_KINDS
    if slope_deg <= WYE_MAX_DEG:
        return WYE_KINDS
    return ()


def segment_class(a: Sequence[float], b: Sequence[float]) -> str:
    """``level`` | ``down`` | ``up`` for flow from ``a`` to ``b``."""
    plan = math.hypot(b[0] - a[0], b[1] - a[1])
    rise = b[2] - a[2]
    if math.degrees(math.atan2(abs(rise), plan)) < _VERTICAL_DEG:
        return LEVEL
    return DOWN if rise < 0 else UP


def allowed_patterns(service: str, before: str, after: str) -> tuple[str, ...]:
    """The patterns a turn from ``before`` to ``after`` may be; empty means none is legal."""
    if service != "drain":
        return (QUARTER_BEND, LONG_SWEEP, EIGHTH_PAIR, EIGHTH_BEND)
    if UP in (before, after):
        return ()
    return ALLOWED[(before, after)]


def pattern_for_angle(angle_deg: float) -> str:
    """The stock bend a measured turn reads as when nobody named a pattern."""
    return EIGHTH_BEND if angle_deg < 67.5 else QUARTER_BEND


def forbidden_turns(service: str, points: Sequence[Sequence[float]],
                    patterns: dict[int, str] | None = None) -> list[tuple[int, str, str]]:
    """``(vertex, pattern, transition)`` for each turn its flow direction forbids.

    ``points`` run in the direction of flow. ``patterns`` names a vertex's pattern where the
    caller chose one; otherwise the turn reads as the stock bend its angle makes.
    """
    out: list[tuple[int, str, str]] = []
    named = patterns or {}
    for i in range(1, len(points) - 1):
        a, b, c = points[i - 1], points[i], points[i + 1]
        if _plan_or_z_length(a, b) < 1e-6 or _plan_or_z_length(b, c) < 1e-6:
            continue
        angle = _turn_deg(a, b, c)
        if angle < 10.0:
            continue
        before, after = segment_class(a, b), segment_class(b, c)
        pattern = named.get(i, pattern_for_angle(angle))
        if pattern not in allowed_patterns(service, before, after):
            out.append((i, pattern, f"{before}->{after}"))
    return out


def _plan_or_z_length(a: Sequence[float], b: Sequence[float]) -> float:
    return math.dist(a[:3], b[:3])


def _turn_deg(a: Sequence[float], b: Sequence[float], c: Sequence[float]) -> float:
    u = [b[k] - a[k] for k in range(3)]
    v = [c[k] - b[k] for k in range(3)]
    nu, nv = math.hypot(*u), math.hypot(*v)
    cosine = max(-1.0, min(1.0, sum(p * q for p, q in zip(u, v, strict=True)) / (nu * nv)))
    return math.degrees(math.acos(cosine))
