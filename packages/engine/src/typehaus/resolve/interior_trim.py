"""Resolve interior trim: derived base runs and door casings (→ model/millwork.TrimStandard).

Declare once, derive everywhere — the stool precedent. A house's ``TrimStandard`` names the
stock and its sizes; every qualifying room gets base along its finish face
(``interior_trim_base.py``) and every cased door a picture frame on each finished face
(``interior_trim_casing.py``). A room qualifies when it is conditioned, has a
``floor_finish`` and is not in ``excluded_rooms``; what kind of base it takes is its floor
material's ``base_detail``.

Records, not solids: ``geometry_millwork`` draws them for the viewer, the GLB and the IFC,
and ``takeoff/interior_trim.py`` bills them by the LF.
"""

from __future__ import annotations

from typehaus.findings import Finding
from typehaus.model.plan import PlanModel
from typehaus.resolve.interior_trim_base import resolve_base_runs
from typehaus.resolve.interior_trim_casing import resolve_door_casings
from typehaus.resolve.interior_trim_scope import trim_scope
from typehaus.resolve.model import ResolvedModel


def resolve_interior_trim(plan: PlanModel, model: ResolvedModel) -> list[Finding]:
    """Populate ``model.base_runs`` and ``model.door_casings``."""
    scope, findings = trim_scope(plan, model)
    if scope is None:
        return findings
    resolve_door_casings(plan, model, scope)
    resolve_base_runs(plan, model, scope)
    return findings
