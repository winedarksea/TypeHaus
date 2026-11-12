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

**A rectangular run is graded only when anchored on a distributing plenum** (or chained
end-to-end to such a run): Huebscher equivalent diameter and its gauge row's ε, turns by the
row's ``bend_equivalent_length`` (no rectangular elbow C table exists), a missing number a gap.
``erv_landings.network`` is the membership rule; System 1's rectangular trunks stay out of it.

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

from typehaus.checks._authoring import advisory, not_applicable, passed, unknown
from typehaus.checks.mep.erv_landings import (
    direct_landings,
    equipment_kinds,
    landing_ancestors,
    manifolds,
    network,
    radial_landings,
)
from typehaus.checks.mep.erv_routes import trunk_routes
from typehaus.checks.mep.erv_static_terms import (
    damper_drop_in_wg,
    elbow_loss_sum,
    interpolate,
    machine_trunk_flows,
    product_for,
    radial_capacity,
    terminal_loss,
    trunk_terms,
    turn_points,
    type_for,
    velocity_pressure_in_wg,
)
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

# Old private names, kept for the oracle test and the network test.
_equipment_kinds = equipment_kinds
_manifolds = manifolds
_network = network
_direct = direct_landings
_interpolate = interpolate
_product_for = product_for
_type_for = type_for
_M_TO_FT = 3.280839895013123


class _Leg:
    """One run's contribution: its pressure drop, or the reason there isn't one."""

    __slots__ = ("tag", "drop_in_wg", "gap")

    def __init__(self, tag: str, drop_in_wg: float | None, gap: str | None) -> None:
        self.tag, self.drop_in_wg, self.gap = tag, drop_in_wg, gap


def _rect_drop(ctx: CheckContext, duct, elbows: int) -> _Leg:
    """A rectangular run at its Huebscher equivalent diameter and its gauge row's ε.

    The row is ``duct_sizing.rectangular_row`` (material, smallest ``max_side`` covering the
    larger side). A row with no ``roughness_m`` is a gap by the (material, W x D) pair. No
    rectangular elbow C table exists, so turns take the row's ``bend_equivalent_length``, and
    a turn with none authored is a gap, not a free bend.
    """
    width, depth = duct.width_m, duct.depth_m
    pair = (f"{duct.material or 'no material'}, "
            f"{(width or 0.0) / _M_PER_IN:.1f}x{(depth or 0.0) / _M_PER_IN:.1f}\"")
    row = (duct_sizing.rectangular_row(ctx.plan.library, duct.material, width, depth)
           if width and depth else None)
    if row is None or row.roughness_m is None:
        return _Leg(duct.tag, None, f"no rectangular DuctProductType with a roughness_m for "
                                    f"({pair})")
    if duct.design_cfm is None:
        return _Leg(duct.tag, None, "the run states no design_cfm")
    if elbows and row.bend_equivalent_length is None:
        return _Leg(duct.tag, None, f"{elbows} turn(s) on a rectangular run: no rectangular "
                    f"elbow C table exists and {row.tag} states no bend_equivalent_length")
    bend_m = row.bend_equivalent_length.meters if row.bend_equivalent_length else 0.0
    return _Leg(duct.tag, duct_sizing.leg_drop_in_wg(
        duct.design_cfm, duct_sizing.equivalent_diameter_m(width, depth), row.roughness_m,
        duct.length_m + elbows * bend_m), None)


def _duct_drop(ctx: CheckContext, duct, elbows: int) -> _Leg:
    """The run's friction and turns, plus its in-line dampers fully open."""
    leg = _run_drop(ctx, duct, elbows)
    if leg.drop_in_wg is None:
        return leg
    damper, gaps = damper_drop_in_wg(ctx, duct, duct.design_cfm)
    if gaps:
        return _Leg(duct.tag, None, "; ".join(gaps))
    return _Leg(duct.tag, leg.drop_in_wg + damper, None)


def _run_drop(ctx: CheckContext, duct, elbows: int) -> _Leg:
    """Darcy-Weisbach over developed length plus the elbows' equivalent length."""
    diameter_m = getattr(duct, "diameter_m", None)
    if diameter_m is None and duct.material is not None:
        return _rect_drop(ctx, duct, elbows)
    product = _product_for(ctx, duct.material, diameter_m)
    if product is None:
        return _Leg(duct.tag, None,
                    f"no DuctProductType for ({duct.material or 'no material'}, "
                    f"{(diameter_m or 0.0) / _M_PER_IN:.1f}\")")
    if duct.design_cfm is None:
        return _Leg(duct.tag, None, "the run states no design_cfm")
    bend_m = (product.bend_equivalent_length.meters
              if product.bend_equivalent_length is not None else 0.0)
    # The house's bought elbows' C x K (#114) replaces the row's equivalent length.
    c = elbow_loss_sum(ctx, duct)
    effective_m = duct.length_m + (0.0 if c is not None else elbows * bend_m)
    bore = product.bore_diameter.meters
    return _Leg(duct.tag, duct_sizing.leg_drop_in_wg(
        duct.design_cfm, bore, product.roughness_m, effective_m) + (c or 0.0)
        * velocity_pressure_in_wg(duct.design_cfm, bore), None)


def _stretch_drop(ctx: CheckContext, duct, nodes: list, trunks: list
                  ) -> tuple[float, float, str] | None:
    """``(drop over the stretches walked, drop of the whole run, label)``, or None.

    The whole-run figure is recomputed by the same per-turn sum, so the swap is like for
    like; None (charge it whole) wherever a number is missing (``erv_segments``).
    """
    from typehaus.checks.mep.erv_segments import run_length, station, stretches

    spans = stretches(ctx, duct, nodes, nodes.index(("T", duct.tag)), trunks)
    if not spans:
        return None
    diameter_m = getattr(duct, "diameter_m", None)
    if diameter_m is not None:
        product = _product_for(ctx, duct.material, diameter_m)
        if product is None or product.roughness_m is None:
            return None
        bore, rough, bend = (product.bore_diameter.meters, product.roughness_m,
                             product.bend_equivalent_length)
    else:
        row = (duct_sizing.rectangular_row(ctx.plan.library, duct.material, duct.width_m,
                                           duct.depth_m) if duct.width_m else None)
        if row is None or row.roughness_m is None:
            return None
        bore = duct_sizing.equivalent_diameter_m(duct.width_m, duct.depth_m)
        rough, bend = row.roughness_m, row.bend_equivalent_length
    turns = [station(duct, p)[0] for p in turn_points(ctx, duct)]
    length = run_length(duct)

    def drop(lo: float, hi: float, cfm: float) -> float | None:
        def keep(point, lo=lo, hi=hi) -> bool:
            return lo <= station(duct, point)[0] < hi
        inside = sum(1 for at in turns if lo <= at < hi)
        c = elbow_loss_sum(ctx, duct, keep) if diameter_m is not None else None
        if c is None and inside and bend is None:
            return None
        bends = 0.0 if c is not None or not inside else inside * bend.meters
        effective = min(hi, length) - max(lo, 0.0) + bends
        damper, gaps = damper_drop_in_wg(ctx, duct, cfm, keep)
        if gaps:
            return None
        return duct_sizing.leg_drop_in_wg(cfm, bore, rough, effective) + (c or 0.0) \
            * velocity_pressure_in_wg(cfm, bore) + damper

    walked = [drop(lo, hi, q) for lo, hi, q in spans]
    whole = drop(-1.0, length + 1.0, duct.design_cfm)  # every turn, ends included
    if whole is None or any(d is None for d in walked):
        return None
    label = ", ".join(f"{(hi - lo) / _M_PER_IN / 12:.1f} ft at {q:.0f} cfm"
                      for lo, hi, q in spans)
    return sum(walked), whole, label


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


def _elbow_counts(ctx: CheckContext) -> dict[str, int]:
    """Per-run elbow count, from the same walk ``takeoff/mep.py`` bills fittings with.

    Imported at function scope: ``checks`` may read ``takeoff`` (``checks/mep/hvac.py``
    does the same), and counting turns a second way here would put two elbow counts in one
    house — the one the estimate buys and the one the pressure calculation pays for.
    """
    from typehaus.takeoff.runs import run_schedule

    return {str(row["tag"]): int(row["elbows"])
            for row in run_schedule(ctx.model) if row["kind"] == "duct"}


def _worst_path(ctx: CheckContext, machine_tag: str, elbows: dict[str, int],
                landings: dict[str, str], plenums: dict, kinds: dict[str, str]
                ) -> tuple[tuple[float, str, list[str]] | None, list[str]]:
    """The worse side's (static in. w.g., path, terms), and the runs that resolved no drop."""
    worst: tuple[float, str, list[str]] | None = None
    gaps: list[str] = []
    members = network(ctx, machine_tag, landings)
    ancestors = landing_ancestors(ctx, landings)
    for side, name in ((_SUPPLY_SIDE, "supply"), (_EXTRACT_SIDE, "extract")):
        runs = [duct for duct in members if duct.system in side]
        if not runs:
            continue
        radials = [duct for duct in runs if duct.tag in landings]
        trunks = [duct for duct in runs if duct.tag not in landings]
        # Each trunk's drop (with the hood and port kit riding on it) is worked once and
        # charged only to the paths that cross it (``erv_routes``, note §9).
        trunk_legs: dict[str, tuple[float, list[str]]] = {}
        trunk_by_tag = {duct.tag: duct for duct in trunks}
        for duct in trunks:
            leg = _duct_drop(ctx, duct, elbows.get(duct.tag, 0))
            if leg.drop_in_wg is None:
                gaps.append(f"{leg.tag}: {leg.gap}")
                continue
            extra, missing = trunk_terms(ctx, duct, plenums, kinds)
            trunk_legs[duct.tag] = (
                leg.drop_in_wg + sum(loss for _, loss in extra) / PA_PER_IN_WG,
                [f"{leg.tag} {leg.drop_in_wg:.3f}\""]
                + [f"{term} {loss:.1f} Pa" for term, loss in extra])
            gaps.extend(missing)
        routes = trunk_routes(ctx, machine_tag, trunks, plenums, kinds,
                              {landings[duct.tag] for duct in radials})

        def chain(tags: list[str], key: str | None = None, legs=trunk_legs,
                  routes=routes, trunks=trunks, by_tag=trunk_by_tag
                  ) -> tuple[float, list[str]]:
            """The trunks' drops; one on ``key``'s walk only over the stretch it travels."""
            nodes = routes.nodes.get(key, []) if key else []
            total, terms = 0.0, []
            for tag in tags:
                if tag not in legs:
                    continue
                drop, detail = legs[tag]
                part = (_stretch_drop(ctx, by_tag[tag], nodes, trunks)
                        if ("T", tag) in nodes else None)
                if part is not None:
                    drop += part[0] - part[1]
                    detail = [f"{tag} {part[0]:.3f}\" over {part[2]}"] + detail[1:]
                total += drop
                terms += detail
            return total, terms

        # A plenum's curve is keyed on its trunk-collar flow (note §4). A trunk-and-branch
        # tree counts its trunk once, never the trunk plus the branches it carries; and a
        # box whose trunk runs to the machine passes that trunk's flow, riser air included.
        plenum_cfm: dict[str, float] = {}
        direct = direct_landings(ctx, landings)
        for duct in radials:
            if duct.design_cfm is not None and duct.tag in direct:
                plenum_cfm[landings[duct.tag]] = (
                    plenum_cfm.get(landings[duct.tag], 0.0) + duct.design_cfm)
        for host, cfm in machine_trunk_flows(ctx, trunks, machine_tag, plenums).items():
            plenum_cfm[host] = max(plenum_cfm.get(host, 0.0), cfm)

        def boxes_on(hosts: list[str], cfm=plenum_cfm) -> tuple[float, list[str]]:
            total, terms = 0.0, []
            for host in hosts:
                curve_pa = tuple(getattr(plenums[host], "static_loss_pa_at_cfm", ()) or ())
                if curve_pa:
                    loss = _interpolate(curve_pa, cfm.get(host, 0.0))
                    total += loss / PA_PER_IN_WG
                    terms.append(f"{host} {loss:.1f} Pa at {cfm.get(host, 0.0):.0f} cfm")
            return total, terms

        legs = {duct.tag: _duct_drop(ctx, duct, elbows.get(duct.tag, 0)) for duct in radials}
        for duct in radials:
            leg = legs[duct.tag]
            if leg.drop_in_wg is None:
                gaps.append(f"{leg.tag}: {leg.gap}")
                continue
            branch = leg.drop_in_wg
            detail = [f"{leg.tag} {leg.drop_in_wg:.3f}\""]
            # The trunk (and neck) a through-branch's air also crosses rides on its path.
            for up in ancestors.get(duct.tag, ()):
                if up in legs and legs[up].drop_in_wg is not None:
                    branch += legs[up].drop_in_wg
                    detail.append(f"{up} {legs[up].drop_in_wg:.3f}\"")
            terminal = terminal_loss(ctx, duct)
            if terminal is not None:
                branch += terminal / PA_PER_IN_WG
                detail.append(f"terminal {terminal:.1f} Pa")
            host = landings[duct.tag]
            # Its own plenum, then every plenum its air passed through to get there.
            box_total, boxes = boxes_on([host, *routes.through.get(host, [])])
            trunk_total, terms = chain(routes.for_plenum(host), host)
            total = branch + box_total + trunk_total
            if worst is None or total > worst[0]:
                worst = (total, f"{name} side via {duct.tag}", detail + boxes + terms)
        # A trunk landing in other equipment (the System 1 mixing box) is a path of its own.
        for equipment, route in routes.to_equipment:
            box_total, boxes = boxes_on(routes.through.get(equipment, []))
            total, terms = chain(routes.for_route(route), equipment)
            if worst is None or total + box_total > worst[0]:
                worst = (total + box_total, f"{name} side via {route[-1]} into {equipment}",
                         boxes + terms)

    return worst, gaps


def delivered_flows(ctx: CheckContext) -> dict[str, tuple[float, float] | None]:
    """``{ERV tag: (delivered cfm, worst static)}`` off each curve, as this check grades it.

    ``None`` where no honest figure exists: no curve, an unresolved run (a partial path
    would read high), or a static past the curve or its ceiling. Reads only ``ctx.model``
    and ``ctx.plan``, so a code check or a sheet may hand it any such view.
    """
    kinds = _equipment_kinds(ctx)
    machines = [obj for obj in ctx.model.canvas_objects
                if kinds.get(obj.tag) == EquipmentKind.ERV.value]
    if not machines:
        return {}
    landings, plenums, elbows = radial_landings(ctx), _manifolds(ctx), _elbow_counts(ctx)
    out: dict[str, tuple[float, float] | None] = {}
    for machine in machines:
        product = _type_for(ctx, machine.type_ref, "equipment_types")
        curve = tuple(getattr(product, "fan_curve", ()) or ())
        worst, gaps = (_worst_path(ctx, machine.tag, elbows, landings, plenums, kinds)
                       if curve else (None, []))
        ceiling = getattr(product, "fan_curve_max_static_in_wg", None)
        flow = None
        if worst is not None and not gaps and (ceiling is None or worst[0] <= ceiling):
            flow = _delivered(curve, worst[0])
        out[machine.tag] = None if flow is None else (flow, worst[0])
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

        worst, gaps = _worst_path(ctx, machine.tag, elbows, landings, plenums, kinds)

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
                            "is enough is the code's question: "
                            "code.N1103_6_whole_house_ventilation grades this delivered "
                            "figure against the code rate. This is UNKNOWN and not a FAIL "
                            "because a design rate is a hope and a curve is a measurement",
                (machine.tag,),
                fix="measure it at commissioning with a low-flow hood, and take the trunk "
                    "up a size if it comes in under the code rate"))
        for gap in sorted(set(gaps)):
            out.append(unknown(cid, f"{machine.tag}: {gap}", (machine.tag,)))

    out.extend(radial_capacity(ctx, landings))
    return out
