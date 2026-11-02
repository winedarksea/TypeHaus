"""``FloorSystem.strongbacks``: a 2x on edge across an open-web field's bottom chords.

TRIFORCE Detail 5 Option #1: the strongback runs perpendicular to the trusses through one
web opening, on the bottom chords and against the web, nailed at every truss. One piece per
run of consecutive kept bays, line centre to line centre; an ``omit_bays`` station cuts its
bay ("can be cut between two joists for ducts or pipes"). Refused, with an
``integrity.floor_strongback`` ERROR, off an open-web field with no authored panel layout,
on a web, or longer than one stick of stock.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.model.floors import FloorSystem
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.mep_crossings import WebPanels
from typehaus.resolve.model import FramedMember

#: The longest stock a piece is cut from.
STOCK_M = inch(240).meters
_TOL_M = inch(1 / 32).meters


def strongback_members(system: FloorSystem, lines: list[float], along_x: bool, z0: float,
                       members: list[FramedMember]) -> list[Finding]:
    """Append ``system``'s strongback pieces across its sorted joist ``lines`` to ``members``."""
    findings: list[Finding] = []
    spec = system.joists
    chord = cross_section(spec.member)
    for index, strongback in enumerate(system.strongbacks):
        at = strongback.at.meters
        section = cross_section(strongback.member)
        half = section.width_m / 2.0
        why = None
        if (chord.shape != "floor_truss" or spec.web_panel_pitch is None
                or spec.web_opening_width is None or spec.web_panel_offset is None):
            why = "the field is not an open-web truss field with an authored panel layout"
        else:
            panels = WebPanels(spec.web_panel_pitch.meters, spec.web_opening_width.meters,
                               spec.web_panel_offset.meters)
            low, high = panels.opening_at(at)
            if at - half < low - _TOL_M or at + half > high + _TOL_M:
                why = (f"its {strongback.member} is not inside one web opening "
                       f"({low / inch(1).meters:.2f}\"..{high / inch(1).meters:.2f}\")")
        omitted = set()
        for station in strongback.omit_bays:
            s = station.meters
            bay = next((i for i in range(len(lines) - 1) if lines[i] < s < lines[i + 1]), None)
            if bay is None:
                why = why or f"omit station {s / inch(1).meters:.2f}\" is in no bay"
            omitted.add(bay)
        pieces: list[tuple[float, float]] = []
        start = None
        for bay in range(len(lines)):
            if bay < len(lines) - 1 and bay not in omitted:
                start = lines[bay] if start is None else start
            elif start is not None:
                pieces.append((start, lines[bay]))
                start = None
        long = [b - a for a, b in pieces if b - a > STOCK_M + _TOL_M]
        if why is None and long:
            why = f"a piece is {max(long) / inch(12).meters:.2f}', over 20' stock"
        if why is not None:
            findings.append(Finding(
                severity=Severity.ERROR, check_id="integrity.floor_strongback",
                message=f"floor {system.tag}: strongback at "
                        f"{at / inch(1).meters:.2f}\": {why}; it is not laid",
                element_tags=(system.tag,), result=Result.FAIL))
            continue
        bottom = z0 + (chord.flange_thickness_m or 0.0)
        for n, (a, b) in enumerate(pieces):
            p0, p1 = ((at, a), (at, b)) if along_x else ((a, at), (b, at))
            members.append(FramedMember(
                system.uid, f"strongback-{index}-{n}", "strongback", strongback.member,
                p0, p1, bottom, bottom + section.depth_m, b - a))
    return findings
