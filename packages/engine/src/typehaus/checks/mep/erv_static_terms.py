"""The component terms ``mep.erv_static_budget`` adds to friction: products, terminals, hoods.

Split out of ``erv_static.py`` for size. Everything here is a READ of authored product data —
a duct row by its key, a register's or a hood's ``static_loss_pa_at_cfm`` — and none of it is
physics; the friction arithmetic stays in ``resolve/duct_sizing.py``.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, passed
from typehaus.checks.registry import CheckContext
from typehaus.findings import Finding
from typehaus.model.enums import EquipmentKind


def product_for(ctx: CheckContext, material: str | None,
                diameter_m: float | None) -> object | None:
    """The ROUND ``DuctProductType`` matching a run's (material, nominal diameter) pair.

    The same pair ``prices.toml``'s ``[ducts]`` qualifies on, matched the same way — one
    join, so a run that prices as 4" galvanized cannot resist as something else. A
    rectangular row (``section="rectangular"``) never answers a round run.
    """
    if material is None or diameter_m is None:
        return None
    for row in getattr(ctx.plan.library, "duct_product_types", ()):
        if row.material != material or getattr(row, "section", "round") != "round":
            continue
        if row.nominal_diameter is not None and abs(
                row.nominal_diameter.meters - diameter_m) <= 1e-6:
            return row
    return None


def interpolate(curve: tuple[tuple[float, float], ...], cfm: float) -> float:
    """Linear interpolation of a component loss curve keyed on flow. Pa."""
    if cfm <= curve[0][0]:
        return curve[0][1]
    if cfm >= curve[-1][0]:
        return curve[-1][1]
    for (q0, p0), (q1, p1) in zip(curve, curve[1:], strict=False):
        if q0 <= cfm <= q1:
            return p0 + (p1 - p0) * (cfm - q0) / (q1 - q0)
    return curve[-1][1]


def type_for(ctx: CheckContext, type_ref: str | None, collection: str) -> object | None:
    if not type_ref:
        return None
    return next((row for row in getattr(ctx.plan.library, collection, ())
                 if row.tag == type_ref), None)


def terminal_loss(ctx: CheckContext, duct) -> float | None:
    """The loss of the terminal on this run, Pa at the run's design flow, or None."""
    best: float | None = None
    for element in ctx.plan.all_elements():
        if element.element_kind != "Register" or element.duct_ref != duct.tag:
            continue
        product = type_for(ctx, element.type_ref, "register_types")
        curve = tuple(getattr(product, "static_loss_pa_at_cfm", ()) or ())
        if not curve or duct.design_cfm is None:
            continue
        loss = interpolate(curve, duct.design_cfm)
        # A two-headed radial carries two terminals; the worse one is on the worst path.
        best = loss if best is None else max(best, loss)
    return best


def hood_losses(ctx: CheckContext, duct, plenums: dict[str, object],
                kinds: dict[str, str]) -> list[tuple[str, float]]:
    """``[(hood tag, Pa)]`` for the outdoor hood(s) a trunk ends in, at the trunk's flow.

    A hood is a one-collar ``DUCT_MANIFOLD`` that distributes nothing (``_manifolds``
    leaves it out of ``plenums``). Its loss is the whole side's air, so it rides with the
    trunk chain, not with a branch. A hood whose type states no curve adds nothing and says
    so in the note, not here: the static budget reports only what was read.
    """
    from typehaus.checks.mep.duct_connectivity import equipment_at_end

    if duct.design_cfm is None or not duct.path:
        return []
    out: list[tuple[str, float]] = []
    for index in (0, -1):
        z = duct.z_m[index] if duct.z_m and len(duct.z_m) == len(duct.path) else None
        host = equipment_at_end(ctx, z, duct.path[index])
        if host is None or host in plenums or kinds.get(host) != (
                EquipmentKind.DUCT_MANIFOLD.value):
            continue
        obj = next((o for o in ctx.model.canvas_objects if o.tag == host), None)
        product = type_for(ctx, getattr(obj, "type_ref", None), "equipment_types")
        curve = tuple(getattr(product, "static_loss_pa_at_cfm", ()) or ())
        if curve:
            out.append((host, interpolate(curve, duct.design_cfm)))
    return out


def machine_trunk_flows(ctx: CheckContext, trunks, machine_tag: str,
                        plenums: dict[str, object]) -> dict[str, float]:
    """``{plenum: cfm}`` for each plenum a trunk joins straight to the machine.

    Everything the box gathers or hands on (a riser's air too) passes that trunk's collar,
    which is the flow its curve is keyed on, not the sum of its own radials.
    """
    from typehaus.checks.mep.duct_connectivity import equipment_at_end

    out: dict[str, float] = {}
    for duct in trunks:
        if duct.design_cfm is None or not duct.path:
            continue
        ends = set()
        for index in (0, -1):
            z = duct.z_m[index] if duct.z_m and len(duct.z_m) == len(duct.path) else None
            ends.add(equipment_at_end(ctx, z, duct.path[index]))
        if machine_tag in ends:
            for host in ends & plenums.keys():
                out[host] = max(out.get(host, 0.0), duct.design_cfm)
    return out


def radial_capacity(ctx: CheckContext, landings: dict[str, str]) -> list[Finding]:
    """One finding per radial: its design flow against what its product is used for."""
    cid = "mep.erv_static_budget"
    out: list[Finding] = []
    for duct in sorted(ctx.model.ducts, key=lambda item: item.tag):
        if duct.tag not in landings or duct.design_cfm is None:
            continue
        product = product_for(ctx, duct.material, getattr(duct, "diameter_m", None))
        if product is None or product.max_cfm is None:
            continue
        if duct.design_cfm > product.max_cfm + 1e-9:
            out.append(failed(
                cid, f"{duct.tag} carries {duct.design_cfm:.0f} cfm in {product.tag}, which "
                     f"this house uses to {product.max_cfm:.0f} cfm",
                (duct.tag,),
                fix="split the terminal onto a second port, or take this run up a size"))
        else:
            out.append(passed(
                cid, f"{duct.tag} carries {duct.design_cfm:.0f} cfm in {product.tag} "
                     f"(<= {product.max_cfm:.0f} cfm)", ()))
    return out
