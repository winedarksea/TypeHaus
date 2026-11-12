"""Does a distribution manifold have a run arriving at its inlet?

``mep.erv_manifold_ports`` counts the branches that leave a plenum; nothing asked whether any
air gets in. ``EQ-M-ERV-MAN-SUP`` had two radials on its collars and no trunk, and the port
census passed it.

An outlet is a run ending in the case on a branch port, an inlet any other run ending in it
(``lands_on_branch_port``, the census's own role test, and ``equipment_at_end``'s "lands
in"). Graded: a ``DUCT_MANIFOLD`` that distributes (``erv_landings.manifolds``: two ports or a
dimensioned collar, so a hood is out) and a ``PLENUM`` that dimensions collars. A PLENUM with
no collars has no outlet role to tell apart from its inlet, so it is not graded.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.resolve.duct_sizing import effective_diameter_m

_CID = "mep.manifold_feed"


def _distributors(ctx: CheckContext) -> dict[str, object]:
    from typehaus.checks.mep.erv_landings import equipment_kinds, manifolds
    from typehaus.checks.mep.erv_manifold_ports import plenum_air_ports
    from typehaus.model.enums import EquipmentKind

    out = dict(manifolds(ctx))
    plenum = getattr(EquipmentKind, "PLENUM", None)  # E2 adds it; absent -> nothing to add
    if plenum is not None:
        ports = plenum_air_ports(ctx.model)
        for tag, kind in equipment_kinds(ctx).items():
            if kind == plenum.value and any(p.collar for p in ports.get(tag, ())):
                obj = next((o for o in ctx.model.canvas_objects if o.tag == tag), None)
                product = next((t for t in ctx.plan.library.equipment_types
                                if obj is not None and t.tag == obj.type_ref), None)
                if product is not None:
                    out[tag] = product
    return out


@check(Tier.INTEGRITY, _CID)
def manifold_feed(ctx: CheckContext) -> list[Finding]:
    """A distributor with outlet runs and no run arriving at its inlet is unfed."""
    from typehaus.checks.mep.duct_connectivity import equipment_at_end
    from typehaus.checks.mep.erv_manifold_ports import lands_on_branch_port, plenum_air_ports

    distributors = _distributors(ctx)
    if not distributors:
        return [not_applicable(_CID, "this plan holds no distribution manifold or collared "
                                     "plenum, so no inlet needs a feed", ())]
    air_ports = plenum_air_ports(ctx.model)
    out: list[Finding] = []
    for tag, product in sorted(distributors.items()):
        outlets: list[str] = []
        inlets: list[str] = []
        for duct in ctx.model.ducts:
            if not duct.path or effective_diameter_m(duct) is None:
                continue
            for index in (0, -1):
                z = (duct.z_m[index]
                     if duct.z_m and len(duct.z_m) == len(duct.path) else None)
                if equipment_at_end(ctx, z, duct.path[index]) != tag:
                    continue
                on_branch = lands_on_branch_port(product, air_ports.get(tag, ()), duct,
                                                 (duct.path[index], z))
                (outlets if on_branch else inlets).append(duct.tag)
                break
        if not outlets:
            continue  # nothing leaves it: not an unfed distributor
        if inlets:
            out.append(passed(_CID, f"{tag}: {', '.join(sorted(inlets))} arrives at its inlet "
                                    f"and {len(outlets)} outlet run(s) leave", (tag,)))
        else:
            out.append(failed(
                _CID, f"{tag} is unfed: {len(outlets)} outlet run(s) leave it "
                      f"({', '.join(sorted(outlets))}) and no run ends in its case on the "
                      "inlet", (tag, *sorted(outlets)),
                fix="draw the feed (trunk or riser) to the manifold's inlet port"))
    return out
