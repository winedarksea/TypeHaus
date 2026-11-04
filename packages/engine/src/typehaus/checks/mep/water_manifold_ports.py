"""Does each outlet of a water manifold carry exactly one supply run?

The water-side sibling of ``mep.erv_manifold_ports``. A branch's source is read off
``resolve/mep_tie_ins``: a run whose first vertex stands on an exact outlet port is fed by
it. Two runs on one outlet cannot be built (FAIL); an outlet nothing leaves is named, so a
spare that needs a plug is never silent. The inlet is where the feed ENDS, so it is not an
outlet and is never counted.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import EquipmentKind
from typehaus.resolve.mep_ports import placed_ports
from typehaus.resolve.mep_tie_ins import supply_tie_in_records


@check(Tier.INTEGRITY, "mep.water_manifold_ports")
def water_manifold_ports(ctx: CheckContext) -> list[Finding]:
    """One run per outlet, per water manifold."""
    cid = "mep.water_manifold_ports"
    manifolds = sorted(element.tag for element in ctx.plan.all_elements()
                       if element.element_kind == "Equipment"
                       and element.kind is EquipmentKind.WATER_MANIFOLD)
    if not manifolds:
        return [not_applicable(cid, "this plan holds no water manifold, so there are no "
                                    "outlets to account for", ())]
    ports = placed_ports(ctx.model)
    users: dict[str, list[str]] = {}
    for record in supply_tie_in_records(ctx.model.pipe_runs, ports):
        if record.reason == "equipment_port" and record.port:
            users.setdefault(record.port, []).append(record.child)

    out: list[Finding] = []
    for tag in manifolds:
        # An outlet is every exact port no run ENDS on: the feed lands on the inlet.
        outlets = sorted((p for p in ports if p.equipment_tag == tag and p.exact
                          and not any(_ends_on(run, p) for run in ctx.model.pipe_runs)),
                         key=lambda p: p.port_tag)
        names = [f"{tag}.{p.port_tag}" for p in outlets]
        contested = {name: sorted(users[name]) for name in names if len(users.get(name, ())) > 1}
        spare = [name.split(".", 1)[1] for name in names if name not in users]
        if contested:
            name, runs = sorted(contested.items())[0]
            out.append(failed(
                cid, f"{name} feeds {len(runs)} runs ({', '.join(runs)}); an outlet is one "
                     "ProPEX connection and takes one tube", (tag, *runs),
                fix="start one run on a free outlet, or tee it off a branch downstream"))
            continue
        used = len(names) - len(spare)
        out.append(passed(
            cid, f"{tag}: {used} of {len(names)} outlets used, one run each"
                 + (f"; spare {', '.join(spare)} (plug it)" if spare else ", full"),
            (tag,)))
    return out


def _ends_on(run, port) -> bool:
    """Whether ``run``'s last vertex stands on ``port`` (1/2" in plan and height)."""
    if not run.path or not run.z_m:
        return False
    (x, y), z = run.path[-1][:2], run.z_m[-1]
    return max(abs(x - port.x_m), abs(y - port.y_m), abs(z - port.z_m)) <= 0.0127
