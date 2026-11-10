"""A valve in series with another that isolates exactly the same fixtures.

A preference, not code (``notes/supply_isolation_basis.md`` §3): two valves with no tee
between them close off the same set, so one is a second leak point for nothing. A valved
manifold outlet counts as the upstream valve. The main shutoff is never flagged.
"""

from __future__ import annotations

from typehaus.checks._authoring import Result, advisory, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.resolve.supply_valves import supply_tree, walk_up

CID = "advisory.redundant_isolation"


@check(Tier.ADVISORY, CID)
def redundant_isolation(ctx: CheckContext) -> list[Finding]:
    tree = supply_tree(ctx.model)
    valves = [(run, station, accessory) for run, items in tree.valves.items()
              for station, accessory in items if accessory.kind == "shutoff"]
    if not valves:
        return [not_applicable(CID, "no supply shutoffs to compare", ())]
    valved = {t.tag for t in ctx.plan.library.equipment_types if t.valved_outlets}
    types = {e.tag: getattr(e, "type_ref", None) for e in ctx.plan.all_elements()
             if e.element_kind == "Equipment"}
    out: list[Finding] = []
    for run, station, accessory in sorted(valves, key=lambda v: v[2].tag):
        found = walk_up(tree, run, station, skip_valve=accessory.tag)
        upstream = found.valve
        if upstream is None and found.port and types.get(found.port.split(".")[0]) in valved:
            upstream = found.port
        if upstream is None:
            continue
        if any(a.tag == upstream and a.kind == "main_shutoff" for a in ctx.model.pipe_accessories):
            continue
        out.append(advisory(
            CID, f"ADVISORY — {accessory.tag} on {run} isolates the same fixtures as "
                 f"{upstream} upstream, with no tee between them", (accessory.tag, upstream),
            Result.ADVISORY, fix="keep one of the two"))
    if not out:
        out.append(passed(CID, f"{len(valves)} shutoffs, none in series with another over "
                               "the same fixtures", ()))
    return out
