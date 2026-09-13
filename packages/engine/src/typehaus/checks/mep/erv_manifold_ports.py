"""Are there more branches on a distribution plenum than it was fabricated with ports?

This grades a sentence. ``houses/catlin/plan/mep_erv.py`` has said in prose since the
level-2 layout was drawn that ``EQ-M-ERV-MAN-EXH`` is "full at 10 of 10", and every argument
about where a new terminal could go leans on it — the plant room's extract is where it is
because that manifold has no eleventh port. A comment is not a guard. Add a twelfth radial
and the prose goes on saying ten while the model says twelve, and nothing anywhere notices.

The census is earned rather than counted off a naming convention. A branch is a run whose
end lands *inside the plenum's case* — the same ``duct_connectivity.equipment_at_end`` test
that decides a duct is plumbed into a machine anywhere else in the engine — and whose
diameter matches the plenum's own ``port_diameter``. The second half is what keeps the trunk
out of the count: a 6" riser landing in the same box is the inlet collar, not a branch, and a
census that counted it would report every plenum one over.

**This one does FAIL, and blocks.** Unlike the static budget beside it, there is nothing
approximate here and nothing that depends on what the building needs: a box with six collars
cannot take seven pipes. It is an INTEGRITY finding for the same reason a duplicate tag is —
the model is asserting something that cannot be built.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import EquipmentKind

_M_PER_IN = 0.0254


@check(Tier.INTEGRITY, "mep.erv_manifold_ports")
def erv_manifold_ports(ctx: CheckContext) -> list[Finding]:
    """Branch count against the fabricated port count, per distribution plenum."""
    from typehaus.checks.mep.duct_connectivity import equipment_at_end

    cid = "mep.erv_manifold_ports"
    kinds = {element.tag: element.kind.value for element in ctx.plan.all_elements()
             if element.element_kind == "Equipment"}
    plenums = [obj for obj in ctx.model.canvas_objects
               if kinds.get(obj.tag) == EquipmentKind.DUCT_MANIFOLD.value]
    if not plenums:
        return [not_applicable(cid, "this plan holds no duct manifold, so there is no port "
                                    "census to take", ())]

    types = {row.tag: row for row in ctx.plan.library.equipment_types}
    stated = [obj for obj in plenums
              if getattr(types.get(obj.type_ref or ""), "duct_ports", None) is not None]
    if not stated:
        # Earned: every manifold in the plan was inspected and not one type states a port
        # count, so there is no number in this model to grade a census against. Distinct
        # from "a plenum is missing one", which is the UNKNOWN below.
        return [not_applicable(
            cid, f"none of the {len(plenums)} duct manifolds in this plan names a type "
                 "stating duct_ports, so no port census is expressible", ())]

    out: list[Finding] = []
    for obj in sorted(plenums, key=lambda item: item.tag):
        product = types.get(obj.type_ref or "")
        ports = getattr(product, "duct_ports", None)
        if ports is None:
            out.append(unknown(
                cid, f"{obj.tag} is a duct manifold but its type "
                     f"({obj.type_ref or 'none'}) states no duct_ports, so the runs landing "
                     "in it cannot be counted against anything", (obj.tag,)))
            continue
        port_diameter = getattr(product, "port_diameter", None)
        if port_diameter is None:
            out.append(unknown(
                cid, f"{obj.tag}'s type states {ports} ports but no port_diameter, so a "
                     "branch cannot be told from the trunk collar", (obj.tag,)))
            continue

        branches: list[str] = []
        trunks: list[str] = []
        for duct in ctx.model.ducts:
            if not duct.path or duct.diameter_m is None:
                continue
            for index in (0, -1):
                z = (duct.z_m[index]
                     if duct.z_m and len(duct.z_m) == len(duct.path) else None)
                if equipment_at_end(ctx, z, duct.path[index]) != obj.tag:
                    continue
                if abs(port_diameter.meters - duct.diameter_m) <= 1e-6:
                    branches.append(duct.tag)
                else:
                    trunks.append(duct.tag)
                break

        size = f"{port_diameter.meters / _M_PER_IN:.0f}\""
        if len(branches) > ports:
            out.append(failed(
                cid, f"{obj.tag} ({obj.type_ref}) is fabricated with {ports} x {size} ports "
                     f"and {len(branches)} runs land on them: "
                     f"{', '.join(sorted(branches))}",
                (obj.tag, *sorted(branches)),
                fix="add a port to the plenum's spec, split the load onto a second plenum, "
                    "or give one radial two heads at a grille plenum"))
        else:
            spare = ports - len(branches)
            out.append(passed(
                cid, f"{obj.tag} ({obj.type_ref}): {len(branches)} of {ports} x {size} "
                     f"ports used"
                     + (f", {spare} spare" if spare else ", full")
                     + (f"; trunk collar {', '.join(sorted(trunks))}" if trunks else ""),
                (obj.tag,)))
    return out
