"""One feet-and-inches formatter for the MEP checks.

A station a builder can find with a tape, not a float in metres. It was private to
``routing_members.py`` until ``run_interference`` started reporting stations too, and two
copies of a dimension formatter is how two findings about the same crossing come to spell
it differently.

**Metres in.** ``routing_ceiling.py`` keeps its own one-liner because it takes FEET and
rounds to the whole inch — a headroom line, not a station — and folding the two would make
the unit a footgun rather than removing one.
"""

from __future__ import annotations

from typehaus.quantities import M_PER_IN


def feet_inches(meters: float) -> str:
    """``5.2`` m -> ``17'-0.8"``. Signed, one decimal inch."""
    total_in = meters / M_PER_IN
    sign = "-" if total_in < 0 else ""
    total_in = abs(total_in)
    feet, inches = divmod(total_in, 12.0)
    return f"{sign}{int(feet)}'-{inches:.1f}\""
