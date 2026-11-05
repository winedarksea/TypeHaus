"""A fixture's arm tied onto another bathroom-group drain, graded as a UPC 908 wet vent.

The router's question, asked of the check's own walk: if this arm ended on that drain, would
``developed_arm`` close it at a legal wet vent within Table 1002.2? The arm is inserted as a
synthetic run and walked with EVERY vent's ends, since a proposal may lean on a dry vent that
does not yet name the fixture — those vents are returned, because the check walks only the
vents whose ``serves`` names it. A size failure is re-graded at the size 908.2.2 asks, and the
runs to upsize are returned with it. ``houses/catlin/notes/mep_drain_routing_basis.md`` §14.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_trap_arm import (
    TEE_TOL_M,
    Point3,
    WetVentData,
    _on_run,
    developed_arm,
    drain_parent,
)

_NEED = re.compile(r'^(\S+) rejected as a wet vent \(.*under the ([\d.]+)" ')


@dataclass(frozen=True)
class WetTie:
    """Where the arm ends, what vents it, and what pasting it obliges."""

    parent: str
    join: Point3
    arm_in: float
    what: str
    #: ``(run, Ø in)``: wet-vent runs 908.2.2 wants larger, the whole length (PB0225).
    upsize: tuple[tuple[str, float], ...] = ()
    #: Vents the walk leaned on whose ``serves`` does not name the fixture yet.
    name_on_vent: tuple[str, ...] = ()


def grade_hypothetical_tie(model, data: WetVentData, fixture: str, arm: list[Point3],
                           arm_radius_m: float, limit_in: float
                           ) -> tuple[WetTie | None, list[str]]:
    """``(tie, wet vents rejected)`` for ``arm`` (trap to join, 3D) graded as if authored;
    the tie is None unless a legal vent ends the arm within ``limit_in``."""
    if fixture not in data.fx or len(arm) < 2:
        return None, []
    run = f"{fixture}-PROPOSED"
    drains = {**{t: p for t, p in data.drains.items() if t != data.fx[fixture][0]},
              run: list(arm)}
    radii = {**data.radii, run: arm_radius_m}
    joined = drain_parent(arm[-1], run, drains, radii)
    if joined is None:
        return None, []
    fx = {**data.fx, fixture: (run, *data.fx[fixture][1:])}
    arm_m, what, _gap, notes = developed_arm(run, drains, radii, data.all_vent_ends, (fx, fixture))
    upsize: dict[str, float] = {}
    if arm_m is None:
        for note in notes:
            m = _NEED.match(note)
            if m is None:
                continue
            child, need = m.group(1), float(m.group(2))
            parent = drain_parent(drains[child][-1], child, drains, radii)
            for tag in (child, *(() if parent is None else (parent[0],))):
                if 2.0 * radii[tag] / M_PER_IN < need - 1e-6:
                    upsize[tag] = need
        if not upsize:
            return None, notes
        radii = {**radii, **{t: d * M_PER_IN / 2.0 for t, d in upsize.items()}}
        arm_m, what, _gap, notes = developed_arm(run, drains, radii, data.all_vent_ends,
                                                 (fx, fixture))
    if arm_m is None or arm_m / M_PER_IN > limit_in + 1e-6:
        return None, notes
    return WetTie(parent=joined[0], join=arm[-1], arm_in=arm_m / M_PER_IN, what=what,
                  upsize=tuple(sorted(upsize.items())),
                  name_on_vent=_vents_leaned_on(model, fixture, what, joined[0], drains,
                                                radii)), []


def _vents_leaned_on(model, fixture: str, what: str, parent: str,
                     drains: dict[str, list[Point3]], radii: dict[str, float]
                     ) -> tuple[str, ...]:
    """Vents ending on the wet vent (or, for a true tee, on the run joined) not naming it."""
    host = what.split(",", 1)[0] if "wet-vented" in what else parent
    if host not in drains:
        return ()
    from typehaus.resolve.mep_trap_arm import run_points

    out = []
    for r in model.pipe_runs:
        pts = run_points(r) if r.system == "vent" and fixture not in r.serves else None
        if pts and any(_on_run(p, drains[host], radii[host] + TEE_TOL_M)
                       for p in (pts[0], pts[-1])):
            out.append(r.tag)
    return tuple(sorted(out))
