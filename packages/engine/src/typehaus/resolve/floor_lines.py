"""A deck's joist stations off the module: moved regular lines and authored extra lines.

Both are refused under 6" from another line, since ``joints/bearing.py`` would fold the two
lines' ties into one.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.model.floors import FloorSystem
from typehaus.quantities import inch

#: An extra line closer than this to a regular one would share its derived tie.
_EXTRA_LINE_MIN_M = inch(6).meters


def move_lines(system: FloorSystem, positions: list[float], perp0: float,
                perp1: float) -> list[Finding]:
    """Apply ``JoistSpec.line_overrides`` to ``positions`` in place; refusals are findings."""
    findings: list[Finding] = []
    for old, new in system.joists.line_overrides:
        at, to = old.meters, new.meters
        index = next((i for i, p in enumerate(positions) if abs(p - at) < 1e-4), None)
        others = [p for i, p in enumerate(positions) if i != index]
        nearest = min((abs(to - p) for p in others), default=float("inf"))
        why = ("matches no laid joist line" if index is None
               else "moves it outside the joist field" if not perp0 < to < perp1
               else f"puts it {nearest / inch(1).meters:.2f}\" from another line, under the "
                    f"6\" that keeps its own tie" if nearest < _EXTRA_LINE_MIN_M - 1e-9
               else None)
        if why is None and index is not None:
            positions[index] = to
            continue
        findings.append(Finding(
            severity=Severity.ERROR, check_id="integrity.floor_line_move",
            message=f"floor {system.tag}: moving the joist line at {at / inch(1).meters:.2f}\" "
                    f"to {to / inch(1).meters:.2f}\" {why}; it is not moved",
            element_tags=(system.tag,), result=Result.FAIL))
    return findings


def extra_lines(system: FloorSystem, positions: list[float], perp0: float,
                 perp1: float) -> tuple[list[float], list[Finding]]:
    """``JoistSpec.extra_lines`` inside the field and clear of every regular line."""
    kept: list[float] = []
    findings: list[Finding] = []
    for length in system.joists.extra_lines:
        perp = length.meters
        nearest = min((abs(perp - p) for p in positions), default=float("inf"))
        # Against the extra lines already laid too: two that coincide share one tie.
        sibling = min((abs(perp - p) for p in kept), default=float("inf"))
        why = ("lies outside the joist field" if not perp0 < perp < perp1
               else f"is {nearest / inch(1).meters:.2f}\" from a regular joist line, under "
                    f"the 6\" that keeps its own tie" if nearest < _EXTRA_LINE_MIN_M - 1e-9
               else f"is {sibling / inch(1).meters:.2f}\" from another extra line, under "
                    f"the 6\" that keeps its own tie" if sibling < _EXTRA_LINE_MIN_M - 1e-9
               else None)
        if why is None:
            kept.append(perp)
            continue
        findings.append(Finding(
            severity=Severity.ERROR, check_id="integrity.floor_extra_line",
            message=f"floor {system.tag}: extra joist line at "
                    f"{perp / inch(12).meters:.3f}' {why}; it is not laid",
            element_tags=(system.tag,), result=Result.FAIL))
    return sorted(kept), findings
