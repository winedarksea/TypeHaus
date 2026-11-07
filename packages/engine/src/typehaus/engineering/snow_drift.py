"""Where the house's authored roof-step drift lands, roof by roof.

One reading for every reader: ``structural.truss_reactions`` grades a truss row by it, and
S-001 / S-102 print it. The drift itself is authored (``preferences.toml [structural]
roof_beam_snow_psf`` / ``roof_beam_drift_width_ft``); this module only places it.
Oracle: ``notes/north_entry_piers.md`` §3a.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from typehaus.engineering.item import EngineeringRecord

#: Two roof footprints this close (ft) across an edge are one drift surface.
_ADJACENT_FT = 0.5
_FT = 0.3048


@dataclass(frozen=True)
class DriftReach:
    """The truss keys of one roof inside the drift, and where the drift comes from."""

    trusses: frozenset[str]
    #: The roof's own beams are graded at the authored design snow.
    whole: bool
    #: The drifted roof it runs in from; ``None`` when ``whole``.
    source: str | None
    why: str


def drift_reach(model, preferences: object, records: Mapping[str, EngineeringRecord],
                roof) -> DriftReach | None:
    """The drift on ``roof``, or ``None``.

    A roof whose beams ``roof_beam`` grades at the authored design snow (``records``) is
    drifted WHOLE. A trussed roof abutting one is drifted where the drift outruns it: the
    width (``roof_beam_drift_width_ft``) is laid from the drifted roof's FAR edge —
    conservative, the step face is at or beyond it — so the truss lines inside that width
    carry it too. With no width authored the neighbour is held to it whole.
    """
    trusses = [m for m in roof.members if m.category == "roof_truss"]
    beams = [r for r in records.values() if r.kind == "roof_beam"]
    if any(roof.tag in r.element_tags for r in beams):
        return DriftReach(frozenset(_key(m.child_key) for m in trusses), True, None,
                          f"the house grades {roof.tag}'s beams at it")
    drifted = {tag for r in beams for tag in r.element_tags}
    width = getattr(getattr(preferences, "structural", None), "roof_beam_drift_width_ft", None)
    for other in sorted(model.roofs, key=lambda r: r.tag):
        if other.tag not in drifted or other.tag == roof.tag:
            continue
        axis = abutting(other.footprint, roof.footprint)
        if axis is None:
            continue
        if width is None:
            return DriftReach(frozenset(_key(m.child_key) for m in trusses), False, other.tag,
                              f"it abuts the drifted {other.tag} and no "
                              f"roof_beam_drift_width_ft says how far the drift runs")
        i, sign = axis
        far = min(sign * p[i] for p in other.footprint) / _FT
        near = max(sign * p[i] for p in other.footprint) / _FT
        limit = far + width
        inside = frozenset(_key(m.child_key) for m in trusses
                           if min(sign * m.p0[i], sign * m.p1[i]) / _FT <= limit + 1e-6)
        if inside:
            return DriftReach(inside, False, other.tag,
                              f"the {other.tag} drift, {width:g} ft from its far edge "
                              f"(preferences.toml [structural] roof_beam_drift_width_ft), "
                              f"runs {limit - near:.2f} ft past it into {roof.tag}")
    return None


def abutting(first, second) -> tuple[int, float] | None:
    """``(axis, sign)`` pointing from ``first`` to ``second`` where their plan boxes share an
    edge (within ``_ADJACENT_FT``) and overlap along it, else ``None``."""
    tol = _ADJACENT_FT * _FT
    lo1 = [min(p[i] for p in first) for i in (0, 1)]
    hi1 = [max(p[i] for p in first) for i in (0, 1)]
    lo2 = [min(p[i] for p in second) for i in (0, 1)]
    hi2 = [max(p[i] for p in second) for i in (0, 1)]
    for i in (0, 1):
        j = 1 - i
        if min(hi1[j], hi2[j]) - max(lo1[j], lo2[j]) <= tol:
            continue
        if abs(lo2[i] - hi1[i]) <= tol:
            return i, 1.0
        if abs(lo1[i] - hi2[i]) <= tol:
            return i, -1.0
    return None


def _key(name: str | None) -> str:
    return (name or "").strip().lower()
