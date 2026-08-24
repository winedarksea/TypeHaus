"""Pre-framing ConstructionRule application pass (#45, → 10 §Element model).

``ConstructionRule`` objects are typed, pre-resolve declarations of the physical *returns*
the junction solver leaves for framing/take-off — the membrane / foam / liner / masonry lap
that actually closes a resolved junction (a PT sill where framed walls — or a joisted deck —
land on concrete, the sauna liner wrapping onto the centre concrete wall, the exterior
foundation foam turning a corner for thermal continuity, the masonry guard's corner
return) — or, where a rule names no junction at all, a *field* of material a resolved
element leaves for the trades (the resilient channel one room's ceiling membrane hangs
on). They are *authored* on
``PlanModel.construction_rules`` and, until this pass existed, emitted nothing.

This pass runs once, after the envelope is resolved and **before final framing** (so the
returns are construction geometry, not documentation), and for each rule:

* records a :class:`ResolvedConstructionReturn` carrying the return's geometry (outline, z
  range, thickness, length), the take-off quantity and the overlay metadata (element tags,
  lap / sealant / flashing / thermal-continuity) a detail recipe binds to.

The record is documentation + take-off, **not** render geometry: a correctly-placed return
duplicates the mitred ``ResolvedLayer.polygon`` the host wall already draws, so no
``ResolvedSolid`` is emitted (that only ever produced z-fighting prisms in 3D and phantom
concrete rectangles in the sections). ``model.construction_returns`` is serialized to
``model.json`` and emitted as an ``IfcCovering`` directly.

It is declarative: a ``ConstructionRule.applies_to`` predicate selects *where* the return
lands via the finders registered in ``_FINDERS``. It never mutates a resolved wall polygon
or a framing member — a Transition documents the return post-resolve (``documents_rules``),
keyed to the ordinary boundary condition the return names in ``condition_key``.

The finders themselves live one module out — ``construction_sills`` (plate returns),
``construction_corners`` (layers turning a corner) and ``construction_ceiling`` (the
channel field), over the shared readings in ``construction_assemblies`` and
``construction_geometry``. What stays here is the registry and the dispatcher: the whole
pass is "look up ``applies_to``, run the finder, record what it yields".
"""

from __future__ import annotations

from typehaus.findings import Finding
from typehaus.model.plan import PlanModel
from typehaus.resolve.construction_ceiling import _find_ceiling_channel
from typehaus.resolve.construction_corners import (
    _find_foundation_foam_return,
    _find_porch_masonry_return,
    _find_sauna_liner_return,
)
from typehaus.resolve.construction_rim import _find_rim_cavity_foam
from typehaus.resolve.construction_sills import (
    _find_framed_on_concrete,
)
from typehaus.resolve.model import ResolvedModel

# Registry: applies_to predicate -> finder. Adding a rule/finder here is all that a new
# declarative return needs; unknown predicates simply emit nothing (and are flagged once).
_FINDERS = {
    "wall:framed_on_concrete": _find_framed_on_concrete,
    "wall:foundation_foam_return": _find_foundation_foam_return,
    "wall:porch_masonry_return": _find_porch_masonry_return,
    "wall:sauna_liner_return": _find_sauna_liner_return,
    "floor:ceiling_channel": _find_ceiling_channel,
    "wall:rim_cavity_foam": _find_rim_cavity_foam,
}


def apply_construction_rules(model: ResolvedModel) -> list[Finding]:
    """Apply ``PlanModel.construction_rules`` to the resolved model, pre-framing.

    Appends each matched return's record to ``model.construction_returns``. Records only —
    never fails a build, never mutates a resolved wall or framing member, and never emits a
    ``ResolvedSolid`` (see the module docstring).
    """
    plan: PlanModel = model.plan
    for rule in plan.library.construction_rules:
        finder = _FINDERS.get(rule.applies_to)
        if finder is None:
            continue
        for ret in finder(model, rule):
            model.construction_returns.append(ret)
    return []


__all__ = [
    "apply_construction_rules",
    # Re-exported so the finder registry and its entries stay addressable from the module
    # every caller and test already imports.
    "_FINDERS",
    "_find_ceiling_channel",
    "_find_foundation_foam_return",
    "_find_framed_on_concrete",
    "_find_porch_masonry_return",
    "_find_rim_cavity_foam",
    "_find_sauna_liner_return",
]
