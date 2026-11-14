"""``electrical.outdoor_branch_wiring`` -- 2026 NEC 225.10 on circuits that leave their building.

A branch circuit with a consumer in a building other than its panel's runs outside between
them, and 225.10 lists the wiring methods it may use on a building. The circuit is graded on
what the model draws: a ``ConduitRun`` naming it in ``circuits``, or running from its panel to
one of its consumers there. EMT and PVC are on the list; ENT was not on the list as read (the
transcription trailed off), so an ENT route stays UNKNOWN. An undrawn circuit is UNKNOWN, one
finding per building. N/A only when every circuit's consumers stand in its panel's building.
``mep.raceway_use`` grades the drawn exterior runs themselves.
"""

from __future__ import annotations

from typehaus.checks._authoring import not_applicable, passed, unknown
from typehaus.checks.mep.electrical_grounding import building_of_tag, storey_of
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.nec import NEC, cite

_CID = "electrical.outdoor_branch_wiring"
_CODE = cite(NEC.EXTERIOR_WIRING_METHODS)
#: 225.10 methods the model can draw (RacewayMaterial values), as read 2026-11-14.
LISTED_METHODS = frozenset({"emt", "pvc"})


def _remote_consumers(ctx: CheckContext, storeys: dict[str, str]) -> dict[str, list]:
    """Circuit -> (building, consumer tags) for consumers away from the panel's building."""
    panel_bldg = {c.tag: building_of_tag(ctx, c.panel_ref, storeys)
                  for c in ctx.plan.library.circuits}
    out: dict[str, list] = {}
    for storey in ctx.plan.storeys:
        here = ctx.plan.building_of(storey.tag)
        for element in ctx.plan.storey_elements(storey.tag):
            ref = getattr(element, "circuit", None)
            if ref in panel_bldg and panel_bldg[ref] is not None and panel_bldg[ref] != here:
                out.setdefault(ref, []).append((here or "site", element.tag))
    return out


def _material(run) -> str:
    return getattr(run.material, "value", run.material)


@check(Tier.ADVISORY, _CID)
def outdoor_branch_wiring(ctx: CheckContext) -> list[Finding]:
    """Each circuit leaving its building: a drawn 225.10 method, or UNKNOWN."""
    storeys = storey_of(ctx)
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    unplaced = sorted(tag for tag, c in circuits.items()
                      if building_of_tag(ctx, c.panel_ref, storeys) is None)
    remote = _remote_consumers(ctx, storeys)
    if not remote:
        if unplaced:
            return [unknown(_CID, f"{len(unplaced)} circuit(s) name a panel in no building "
                                  f"({', '.join(unplaced[:5])}), so whether they leave it is "
                                  "unknown", code=_CODE)]
        return [not_applicable(_CID, "every circuit's consumers stand in its panel's building",
                               code=_CODE)]
    runs = [r for r in ctx.model.conduits if r.derived is None]
    out: list[Finding] = []
    undrawn: dict[str, list[str]] = {}
    for tag in sorted(remote):
        building = remote[tag][0][0]
        ends = {t for _b, t in remote[tag]}
        panel = circuits[tag].panel_ref
        drawn = [r for r in runs if tag in r.circuits
                 or (r.to_ref in ends and r.from_ref in (panel, None))]
        if not drawn:
            undrawn.setdefault(building, []).append(tag)
            continue
        names = ", ".join(sorted(f"{r.tag} ({_material(r)})" for r in drawn))
        off = [r for r in drawn if _material(r) not in LISTED_METHODS]
        if off:
            out.append(unknown(_CID, f"{tag} to {building} runs in {names}; ENT was not on the "
                                     "225.10 list as read, so the method is unconfirmed",
                               (tag, *(r.tag for r in off)), code=_CODE,
                               fix="read 225.10 in print, or route it in EMT or PVC"))
        else:
            out.append(passed(_CID, f"{tag} to {building} runs in {names}, a 225.10 method",
                              (tag, *(r.tag for r in drawn)), code=_CODE))
    for building, tags in sorted(undrawn.items()):
        out.append(unknown(_CID, f"{len(tags)} circuit(s) to {building} have no drawn route "
                                 f"({', '.join(tags)}), so the wiring method outside cannot "
                                 "be read", tuple(tags), code=_CODE,
                           fix="draw each circuit's raceway (ConduitRun.circuits) or feed the "
                               "building from one feeder"))
    return out
