"""Does the ventilator still move its design air once the duct system is attached?

A balanced ventilator's cfm is not a property of the machine. It is a property of the
machine *and* the duct it was given, and the spec sheet says so by publishing a curve rather
than a number. Until the curve is typed data, every verdict downstream of the machine rests
on whichever point of it somebody quoted: the Catlin file argued for months about whether
the Broan B210E75RT is "210 cfm at 0.2 in. w.g." or "206 at 0.4", which is not a
disagreement at all — they are two stations on one curve — and the whole argument existed
because the curve was prose.

So this check computes the static the authored duct system actually makes and reads the
authored curve at it. What comes back is a *delivered* flow, which is the number every
ventilation verdict in the house should have been resting on.

**Three things are the house's and one is the engine's.** Darcy-Weisbach with a Colebrook
friction factor is public physics and lives here. The absolute roughness of a duct product,
the equivalent length of a bend, and the pressure drop of a plenum, a damper or a grille are
readings off ASHRAE tables or a manufacturer's sheet: they live on ``DuctProductType`` and
``AirHandlingProductFacts`` where whoever read them owns them. A run whose (material,
nominal diameter) pair names no product row is reported UNKNOWN **by that pair**, never given
a house-average roughness — a plausible number computed from an invented epsilon is worse
than no number, because nobody can tell it is invented.

**The verdict is deliberately not a FAIL when the flow falls short of the design rate**, and
the reason is scope. Whether a delivered flow is *enough* is a code question with a code
answer — MN 1322 R403.5 in this house, graded by ``code.N1103_6_whole_house_ventilation`` —
and it is asked against the rate the building requires, not against the rate the designer
hoped for. ``ventilation_cfm`` is that hope: on the Broan it is 210, which is the curve's
value at 0.2 in. w.g., and no real duct system lands under 0.2 in. w.g. A check that FAILed
on that comparison would FAIL on every correctly-built house. So a shortfall is UNKNOWN with
both numbers named, and the FAIL is kept for the one case that is unambiguous whatever the
building needs: static past ``fan_curve_max_static_in_wg``, where the manufacturer says the
machine must not be run at all.

Oracled by ``houses/catlin/notes/erv_static_budget.md``, reproduced by
``tests/test_erv_static_oracle.py``. The note carries the arithmetic term by term, the
rigid-versus-flex comparison the material choice rests on, the 8"-trunk fallback priced, and
the two places the graded figure is deliberately conservative.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory, failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import DuctSystem, EquipmentKind
from typehaus.resolve import duct_sizing

#: Pascals per inch of water gauge. The two units in play, each the one its own source
#: publishes in: a fan curve is in. w.g., a component loss is Pa.
PA_PER_IN_WG = 249.089

#: The friction arithmetic itself — Colebrook across all three flow regimes, and
#: Darcy-Weisbach over a length — now lives in ``resolve/duct_sizing.py``, which a router
#: may import and this may not be. Re-exported under their old private names so the oracle
#: note's terms and ``tests/test_erv_static_oracle.py`` read unchanged.
_NU_FT2_S = duct_sizing.NU_FT2_S
_LAMINAR_RE = duct_sizing.LAMINAR_RE
_MIN_TURBULENT_RE = duct_sizing.MIN_TURBULENT_RE
_friction_factor = duct_sizing.friction_factor

#: Systems on the fresh-air side and on the stale-air side of a balanced ventilator. The
#: curve is an external static PER SIDE, so the governing figure is the worse of the two and
#: never their sum.
_SUPPLY_SIDE = frozenset({DuctSystem.SUPPLY.value, DuctSystem.OUTDOOR_AIR.value})
_EXTRACT_SIDE = frozenset({DuctSystem.RETURN.value, DuctSystem.EXHAUST.value})

_M_PER_IN = 0.0254
_M_TO_FT = 3.280839895013123


def _equipment_kinds(ctx: CheckContext) -> dict[str, str]:
    """``{tag: EquipmentKind value}`` from the authored elements.

    ``ResolvedCanvasObject.kind`` is the ELEMENT kind ("Equipment"), not the equipment
    kind — the resolved object carries geometry and the authored one carries what the
    machine is — so the two have to be joined by tag.
    """
    return {element.tag: element.kind.value
            for element in ctx.plan.all_elements()
            if element.element_kind == "Equipment"}


class _Leg:
    """One run's contribution: its pressure drop, or the reason there isn't one."""

    __slots__ = ("tag", "drop_in_wg", "gap")

    def __init__(self, tag: str, drop_in_wg: float | None, gap: str | None) -> None:
        self.tag, self.drop_in_wg, self.gap = tag, drop_in_wg, gap


def _product_for(ctx: CheckContext, material: str | None,
                 diameter_m: float | None) -> object | None:
    """The ``DuctProductType`` matching a run's (material, nominal diameter) pair.

    The same pair ``prices.toml``'s ``[ducts]`` qualifies on, matched the same way — one
    join, so a run that prices as 4" galvanized cannot resist as something else.
    """
    if material is None or diameter_m is None:
        return None
    for row in getattr(ctx.plan.library, "duct_product_types", ()):
        if row.material != material:
            continue
        if abs(row.nominal_diameter.meters - diameter_m) <= 1e-6:
            return row
    return None


def _duct_drop(ctx: CheckContext, duct, elbows: int) -> _Leg:
    """Darcy-Weisbach over developed length plus the elbows' equivalent length."""
    diameter_m = getattr(duct, "diameter_m", None)
    product = _product_for(ctx, duct.material, diameter_m)
    if product is None:
        return _Leg(duct.tag, None,
                    f"no DuctProductType for ({duct.material or 'no material'}, "
                    f"{(diameter_m or 0.0) / _M_PER_IN:.1f}\")")
    if duct.design_cfm is None:
        return _Leg(duct.tag, None, "the run states no design_cfm")
    bend_m = (product.bend_equivalent_length.meters
              if product.bend_equivalent_length is not None else 0.0)
    effective_m = duct.length_m + elbows * bend_m
    return _Leg(duct.tag, duct_sizing.leg_drop_in_wg(
        duct.design_cfm, product.bore_diameter.meters, product.roughness_m, effective_m),
        None)


def _interpolate(curve: tuple[tuple[float, float], ...], cfm: float) -> float:
    """Linear interpolation of a component loss curve keyed on flow. Pa."""
    if cfm <= curve[0][0]:
        return curve[0][1]
    if cfm >= curve[-1][0]:
        return curve[-1][1]
    for (q0, p0), (q1, p1) in zip(curve, curve[1:], strict=False):
        if q0 <= cfm <= q1:
            return p0 + (p1 - p0) * (cfm - q0) / (q1 - q0)
    return curve[-1][1]


def _delivered(curve: tuple[tuple[float, float], ...], static: float) -> float | None:
    """Net cfm off the fan curve at this static, or None past its last point.

    **Refuses to extrapolate.** A curve stops where the manufacturer stopped measuring, and
    a straight-line continuation past the last point is the check's invention, not the
    machine's behaviour.
    """
    if static <= curve[0][0]:
        return curve[0][1]
    if static > curve[-1][0]:
        return None
    for (s0, c0), (s1, c1) in zip(curve, curve[1:], strict=False):
        if s0 <= static <= s1:
            return c0 + (c1 - c0) * (static - s0) / (s1 - s0)
    return None


def _type_for(ctx: CheckContext, type_ref: str | None, collection: str) -> object | None:
    if not type_ref:
        return None
    return next((row for row in getattr(ctx.plan.library, collection, ())
                 if row.tag == type_ref), None)


def _elbow_counts(ctx: CheckContext) -> dict[str, int]:
    """Per-run elbow count, from the same walk ``takeoff/mep.py`` bills fittings with.

    Imported at function scope: ``checks`` may read ``takeoff`` (``checks/mep/hvac.py``
    does the same), and counting turns a second way here would put two elbow counts in one
    house — the one the estimate buys and the one the pressure calculation pays for.
    """
    from typehaus.takeoff.runs import run_schedule

    return {str(row["tag"]): int(row["elbows"])
            for row in run_schedule(ctx.model) if row["kind"] == "duct"}


def _manifolds(ctx: CheckContext) -> dict[str, object]:
    """Distribution plenums by tag: a ``DUCT_MANIFOLD`` whose type states TWO OR MORE ports.

    **Two, not one, and the exterior hoods are why.** A hood carries ``DUCT_MANIFOLD``
    because the enum has no HOOD kind, and it states one 6" port so the port census can
    grade it. One port does not distribute anything: counted here, the exhaust hood would
    make ``DU-ERV-EA`` — a 6" trunk carrying the whole house's stale air — read as a radial
    off it, and the worst path would be a trunk landing on a hood rather than the branch it
    actually is. ``mep.erv_manifold_ports`` still grades every one of them.
    """
    out: dict[str, object] = {}
    kinds = _equipment_kinds(ctx)
    for obj in ctx.model.canvas_objects:
        if kinds.get(obj.tag) != EquipmentKind.DUCT_MANIFOLD.value:
            continue
        product = _type_for(ctx, obj.type_ref, "equipment_types")
        if product is not None and (getattr(product, "duct_ports", None) or 0) >= 2:
            out[obj.tag] = product
    return out


def radial_landings(ctx: CheckContext) -> dict[str, str]:
    """``{run tag: manifold tag}`` for every run that lands in a fabricated plenum.

    A run is a *radial* when one of its ends is inside a ``DUCT_MANIFOLD``'s case and its
    diameter matches that plenum's ``port_diameter``. A larger run landing in the same box
    is the trunk collar, not a branch — which is what keeps a 6" riser out of the port
    census in :mod:`typehaus.checks.mep.erv_manifold_ports`.

    "Lands in" is ``duct_connectivity.equipment_at_end``, the one definition of it in the
    engine, rather than a second footprint test that could drift from the first.
    """
    from typehaus.checks.mep.duct_connectivity import equipment_at_end

    plenums = _manifolds(ctx)
    out: dict[str, str] = {}
    for duct in ctx.model.ducts:
        if not duct.path or duct.diameter_m is None:
            continue
        for index in (0, -1):
            z = duct.z_m[index] if duct.z_m and len(duct.z_m) == len(duct.path) else None
            host = equipment_at_end(ctx, z, duct.path[index])
            if host is None or host not in plenums:
                continue
            port = getattr(plenums[host], "port_diameter", None)
            if port is not None and abs(port.meters - duct.diameter_m) <= 1e-6:
                out[duct.tag] = host
                break
    return out


def _network(ctx: CheckContext, machine_tag: str, landings: dict[str, str]) -> list[object]:
    """The runs that belong to this ventilator's own distribution, and nothing else.

    A run is in the network when it is a radial off one of the plenums, or when one of its
    ends lands in the machine, a plenum, or the mixing box the fresh leg discharges into.

    **A run that states no ``material`` is not in it, and that exclusion is the point.**
    Catlin's System 1 shares the mixing box with this machine and its trunks are fabricated
    rectangular sheet metal, which is not a typed round product and has no roughness anybody
    read: pulling those five runs into an ERV pressure budget would report a gap in a system
    this check has no business grading. A run that DOES state a material but matches no
    ``DuctProductType`` is a different thing entirely and stays in, reported as a gap by its
    own pair — that is a house that forgot to author a row.
    """
    from typehaus.checks.mep.duct_connectivity import equipment_at_end

    kinds = _equipment_kinds(ctx)
    anchors = {machine_tag, *landings.values()}
    anchors |= {tag for tag, kind in kinds.items()
                if kind == EquipmentKind.MIXING_BOX.value}
    out: list[object] = []
    for duct in ctx.model.ducts:
        if duct.material is None or not duct.path:
            continue
        if duct.tag in landings:
            out.append(duct)
            continue
        for index in (0, -1):
            z = duct.z_m[index] if duct.z_m and len(duct.z_m) == len(duct.path) else None
            if equipment_at_end(ctx, z, duct.path[index]) in anchors:
                out.append(duct)
                break
    return out


@check(Tier.ADVISORY, "mep.erv_static_budget")
def erv_static_budget(ctx: CheckContext) -> list[Finding]:
    """Static of the worst air path against the ventilator's own published fan curve."""
    cid = "mep.erv_static_budget"
    kinds = _equipment_kinds(ctx)
    machines = [obj for obj in ctx.model.canvas_objects
                if kinds.get(obj.tag) == EquipmentKind.ERV.value]
    if not machines:
        # Earned from positive evidence: every canvas object was inspected and none is a
        # balanced ventilator, so there is no fan curve in this building to grade against.
        return [not_applicable(cid, "this plan holds no ERV, so there is no fan curve and "
                                    "no distribution static to read against one", ())]

    elbows = _elbow_counts(ctx)
    landings = radial_landings(ctx)
    plenums = _manifolds(ctx)
    out: list[Finding] = []

    for machine in machines:
        product = _type_for(ctx, machine.type_ref, "equipment_types")
        curve = tuple(getattr(product, "fan_curve", ()) or ())
        design_cfm = getattr(product, "ventilation_cfm", None)
        if not curve:
            out.append(unknown(
                cid, f"{machine.tag}'s type states no fan_curve, so the static this duct "
                     "system makes cannot be turned into a delivered flow — author the "
                     "curve off the spec sheet", (machine.tag,)))
            continue

        worst: tuple[float, str, list[str]] | None = None
        gaps: list[str] = []
        network = _network(ctx, machine.tag, landings)
        for side, name in ((_SUPPLY_SIDE, "supply"), (_EXTRACT_SIDE, "extract")):
            runs = [duct for duct in network if duct.system in side]
            if not runs:
                continue
            radials = [duct for duct in runs if duct.tag in landings]
            trunks = [duct for duct in runs if duct.tag not in landings]
            # The trunk chain is summed WHOLE. A branch that parallels the path rather than
            # lying on it — Catlin's mixing-box feed — is counted, which over-states that
            # side. Conservative, named in the note's §9, and the alternative is a graph
            # walk over joints the model does not author.
            trunk_total = 0.0
            terms: list[str] = []
            for duct in trunks:
                leg = _duct_drop(ctx, duct, elbows.get(duct.tag, 0))
                if leg.drop_in_wg is None:
                    gaps.append(f"{leg.tag}: {leg.gap}")
                    continue
                trunk_total += leg.drop_in_wg
                terms.append(f"{leg.tag} {leg.drop_in_wg:.3f}\"")

            # Each plenum's flow is the sum of the radials landing in it.
            plenum_cfm: dict[str, float] = {}
            for duct in radials:
                if duct.design_cfm is not None:
                    plenum_cfm[landings[duct.tag]] = (
                        plenum_cfm.get(landings[duct.tag], 0.0) + duct.design_cfm)

            for duct in radials:
                leg = _duct_drop(ctx, duct, elbows.get(duct.tag, 0))
                if leg.drop_in_wg is None:
                    gaps.append(f"{leg.tag}: {leg.gap}")
                    continue
                branch = leg.drop_in_wg
                detail = [f"{leg.tag} {leg.drop_in_wg:.3f}\""]
                terminal = _terminal_loss(ctx, duct)
                if terminal is not None:
                    branch += terminal / PA_PER_IN_WG
                    detail.append(f"terminal {terminal:.1f} Pa")
                host = landings[duct.tag]
                curve_pa = tuple(getattr(plenums[host], "static_loss_pa_at_cfm", ()) or ())
                if curve_pa:
                    loss = _interpolate(curve_pa, plenum_cfm.get(host, 0.0))
                    branch += loss / PA_PER_IN_WG
                    detail.append(f"{host} {loss:.1f} Pa at "
                                  f"{plenum_cfm.get(host, 0.0):.0f} cfm")
                total = branch + trunk_total
                if worst is None or total > worst[0]:
                    worst = (total, f"{name} side via {duct.tag}", detail + terms)

        if worst is None:
            out.append(unknown(
                cid, f"{machine.tag}: no duct run on either side resolved a pressure drop, "
                     "so there is no path to grade"
                     + (" — " + "; ".join(sorted(set(gaps))) if gaps else ""),
                (machine.tag,)))
            continue

        static, path, detail = worst
        ceiling = getattr(product, "fan_curve_max_static_in_wg", None)
        note = (f"{machine.tag}: worst path is the {path} at {static:.3f} in. w.g. "
                f"({'; '.join(detail[:4])}" + (", ..." if len(detail) > 4 else "") + ")")
        if ceiling is not None and static > ceiling:
            out.append(advisory(
                cid, note + f" — past the {ceiling} in. w.g. the manufacturer will run this "
                            "machine at, so it is outside its operating envelope, not merely "
                            "off the bottom of its curve",
                (machine.tag,), Result.FAIL,
                fix="take the trunk up a size, or shorten the outdoor legs"))
            continue
        flow = _delivered(curve, static)
        if flow is None:
            out.append(unknown(
                cid, note + f" — past the last point on the fan curve ({curve[-1][0]} in. "
                            "w.g.), and this refuses to extrapolate one: a curve stops where "
                            "the manufacturer stopped measuring",
                (machine.tag,)))
            continue
        if design_cfm is None:
            out.append(unknown(
                cid, note + f", delivering {flow:.0f} cfm — the type states no "
                            "ventilation_cfm to read that against", (machine.tag,)))
        elif flow + 1e-9 >= design_cfm:
            out.append(passed(
                cid, note + f", delivering {flow:.0f} cfm against a {design_cfm:.0f} cfm "
                            "design rate", ()))
        else:
            out.append(unknown(
                cid, note + f", delivering {flow:.0f} cfm against a {design_cfm:.0f} cfm "
                            f"design rate — {design_cfm - flow:.0f} cfm short. Whether that "
                            "is enough is the code's question, not this one: "
                            "code.N1103_6_whole_house_ventilation grades the provided rate "
                            "against what the building requires. This is UNKNOWN and not a "
                            "FAIL because a design rate is a hope and a curve is a "
                            "measurement",
                (machine.tag,),
                fix="measure it at commissioning with a low-flow hood, and take the trunk "
                    "up a size if it comes in under the code rate"))
        for gap in sorted(set(gaps)):
            out.append(unknown(cid, f"{machine.tag}: {gap}", (machine.tag,)))

    out.extend(_radial_capacity(ctx, landings))
    return out


def _terminal_loss(ctx: CheckContext, duct) -> float | None:
    """The loss of the terminal on this run, Pa at the run's design flow, or None."""
    best: float | None = None
    for element in ctx.plan.all_elements():
        if element.element_kind != "Register" or element.duct_ref != duct.tag:
            continue
        product = _type_for(ctx, element.type_ref, "register_types")
        curve = tuple(getattr(product, "static_loss_pa_at_cfm", ()) or ())
        if not curve or duct.design_cfm is None:
            continue
        loss = _interpolate(curve, duct.design_cfm)
        # A two-headed radial carries two terminals; the worse one is on the worst path.
        best = loss if best is None else max(best, loss)
    return best


def _radial_capacity(ctx: CheckContext, landings: dict[str, str]) -> list[Finding]:
    """One finding per radial: its design flow against what its product is used for."""
    cid = "mep.erv_static_budget"
    out: list[Finding] = []
    for duct in sorted(ctx.model.ducts, key=lambda item: item.tag):
        if duct.tag not in landings or duct.design_cfm is None:
            continue
        product = _product_for(ctx, duct.material, getattr(duct, "diameter_m", None))
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
