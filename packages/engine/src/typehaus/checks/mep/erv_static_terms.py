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


def velocity_pressure_in_wg(cfm: float, bore_m: float) -> float:
    """Standard-air velocity pressure, (V / 4005)^2 in. w.g. with V in fpm."""
    from typehaus.resolve.duct_sizing import velocity_fpm

    return (velocity_fpm(cfm, bore_m) / 4005.0) ** 2


#: ASHRAE Fitting 3-1/3-2 angle factor K_theta (Locklin 1950): C at an angle = C90 x K.
ELBOW_ANGLE_FACTOR = ((0.0, 0.0), (20.0, 0.31), (30.0, 0.45), (45.0, 0.60), (60.0, 0.78),
                      (90.0, 1.00))


def elbow_loss_sum(ctx: CheckContext, duct) -> float | None:
    """Sum of C x K over a round run's turns, off the house's bought elbows (#114).

    Each turn takes ``elbow_for_turn``'s row at its own angle; a turn no row makes (a
    reversal) is two 90s. None where the standard has no elbow at this size, so the
    caller keeps the duct row's equivalent length.
    """
    from typehaus.checks.registry import shared
    from typehaus.resolve.duct_standard import duct_standard, elbow_for_turn
    from typehaus.resolve.mep_fittings import FAMILY_DUCT, fitting_records

    standard = duct_standard(ctx.plan)[0]
    size = getattr(duct, "diameter_m", None)
    rows = [r for r in (standard.elbows if standard else ())
            if size and abs(r.diameter.meters - size) < 1e-4 and r.loss_c is not None]
    if not rows:
        return None
    turns = shared(ctx, "erv_static.duct_turns", lambda: _turns_by_run(
        [r for r in fitting_records(ctx.model) if r.family == FAMILY_DUCT]))
    total = 0.0
    for angle in turns.get(duct.tag, ()):
        hit = elbow_for_turn(standard, size, angle)
        if hit is None or hit[0].loss_c is None:
            total += 2 * max(r.loss_c for r in rows)
        else:
            total += hit[0].loss_c * interpolate(ELBOW_ANGLE_FACTOR, min(angle, 90.0))
    return total


def _turns_by_run(records) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for record in records:
        if record.index is not None:
            out.setdefault(record.run_tag, []).append(record.angle_deg)
    return out


def trunk_terms(ctx: CheckContext, duct, plenums: dict[str, object],
                kinds: dict[str, str]) -> tuple[list[tuple[str, float]], list[str]]:
    """``([(term, Pa)], gaps)`` riding with a trunk: its hoods and its port kit (#114).

    A kit's flex is friction over its length in the matching flex row; its transition is
    C x the velocity pressure at the port. An unread number is a gap, not a zero.
    """
    from typehaus.checks.mep.erv_static import PA_PER_IN_WG
    from typehaus.resolve.duct_sizing import leg_drop_in_wg
    from typehaus.resolve.duct_standard import duct_standard

    terms, gaps = hood_losses(ctx, duct, plenums, kinds), []
    standard = duct_standard(ctx.plan)[0]
    cfm = duct.design_cfm
    for part in ctx.model.duct_parts:
        if part.run_tag != duct.tag or part.kind not in ("flex", "transition") or not cfm:
            continue
        label = f"{part.kind} at {part.other}.{part.port}"
        if part.kind == "flex":
            row = product_for(ctx, "flex", duct.diameter_m)
            if row is None or not part.length_m:
                gaps.append(f"{duct.tag}: {label} has no flex row or length")
                continue
            loss = leg_drop_in_wg(cfm, row.bore_diameter.meters, row.roughness_m,
                                  part.length_m) * PA_PER_IN_WG
        else:
            kit = standard.port_kit(_type_of(ctx, part.other), part.port) if standard else None
            port_m = min(duct.diameter_m or 0.0, _diameter_in(part.branch) or 0.0) or None
            if kit is None or kit.transition_loss_c is None or port_m is None:
                gaps.append(f"{duct.tag}: {label} has no published loss coefficient")
                continue
            loss = kit.transition_loss_c * velocity_pressure_in_wg(cfm, port_m) * PA_PER_IN_WG
        terms.append((label, loss))
    return terms, gaps


def _type_of(ctx: CheckContext, tag: str | None) -> str | None:
    return next((o.type_ref for o in ctx.model.canvas_objects if o.tag == tag), None)


def _diameter_in(size: str | None) -> float | None:
    from typehaus.quantities import M_PER_IN

    return float(size[:-2]) * M_PER_IN if size and size.endswith("in") else None
