"""``FloorSystem.strongbacks``: a 2x on edge across an open-web field's bottom chords.

TRIFORCE Detail 5 Option #1: the strongback runs perpendicular to the trusses through one
web opening, on the bottom chords and against the web, nailed at every truss. One piece per
run of consecutive kept bays, line centre to line centre; an ``omit_bays`` station cuts its
bay ("can be cut between two joists for ducts or pipes"). Refused, with an
``integrity.floor_strongback`` ERROR, off an open-web field with no authored panel layout,
on a web, or longer than one stick of stock. "Inside one web opening" is read on every truss
the piece crosses, against its derived ``OpenWebShape`` (``resolve/open_web.py``).
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.model.floors import FloorSystem
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.resolve.open_web import _contains_point, open_web_shape, run_of

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
        row = spec.web_openings
        if chord.shape != "floor_truss" or row is None:
            why = "the field is not an open-web truss field with an authored web row"
        else:
            why = _outside_opening(row, chord, section, members, at, half, along_x)
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


def _outside_opening(row, chord, section, members, at: float, half: float,
                     along_x: bool) -> str | None:
    """Why the piece is not inside one web opening of every truss it crosses, or None."""
    z_lo = chord.flange_thickness_m
    z_hi = z_lo + section.depth_m
    shapes: dict[float, object] = {}
    for member in members:
        if member.category != "joist":
            continue
        run = run_of(member, at, along_x)
        if not 0.0 <= run <= member.length_m:
            continue
        shape = shapes.setdefault(round(member.length_m, 6),
                                  open_web_shape(row, chord, member.length_m))
        corners = [(run + du, z) for du in (-half, half) for z in (z_lo, z_hi)]
        if not any(o.kind == "D" and all(_in(o.ring, u, z) for u, z in corners)
                   for o in shape.openings):
            return (f"its {section.depth_m / inch(1).meters:.1f}\" face is not inside one web "
                    f"opening of truss {member.child_key} at {run / inch(1).meters:.2f}\" "
                    "from its start")
    return None


def _in(ring, u: float, z: float) -> bool:
    return _contains_point(ring, u, z, tol=_TOL_M)
