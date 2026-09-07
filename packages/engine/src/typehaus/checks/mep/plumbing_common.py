"""Shared helpers for the plumbing check family.

The plumbing checks are split along their own topic bands into
``plumbing_supply``/``plumbing_dwv``/``plumbing_concrete``. These two symbols are the only
ones every band uses, so they live here rather than being copied three ways.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.findings import Finding, Result

_M_TO_FT = 3.280839895

#: Plan length, in feet, under which a drain segment is a vertical drop rather than a leg
#: with a grade. ``mep.drain_slope`` skips those (a stack holds no slope) and
#: ``mep.drain_offset_geometry`` exempts them (a stack cannot be too steep); the two rules
#: are complements of each other and must agree exactly about which segments exist, so the
#: tolerance is one constant rather than two literals.
VERTICAL_PLAN_FT = 1e-6


def _advisory_fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    # Advisory findings never carry ERROR severity — that severity is reserved for
    # hard blockers, and permit.py's integrity gate treats any ERROR as a permit-set
    # blocker regardless of check_id.
    return advisory(cid, msg, tags, Result.FAIL)
