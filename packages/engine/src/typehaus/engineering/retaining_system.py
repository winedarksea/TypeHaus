"""A closed loop of retaining walls, graded as ONE body on two planes.

``retaining_system/<the cross-member's tag>``. ``retaining_wall`` grades each wall as an
isolated cantilever; what is built at the sunken garden is a court whose walls are cast into a
closed loop. ``W-SG-W2`` and ``W-SG-E2`` face each other across it and **their thrusts cancel
through the concrete between them**; only the south wall is unopposed. The sum is over the
whole group as one rigid body, so the cancellation falls out of equilibrium rather than out of
pairing walls.

What the record grades (free body §15, the 2026-11-22 case set):

* sliding on the footing plane and on the deep plane, dry and wet
  (:mod:`retaining_system_cases`, bodies read off the resolved solids in
  :mod:`retaining_system_body`);
* the load path that earns the cancellation — the strut, the side footings in plan and the
  south footing's corner delivery (:mod:`retaining_system_rows`);
* the backfill sequence the completed body depends on (:mod:`retaining_system_staged`).

**Oracle.** ``houses/catlin/notes/sunken_garden_court_free_body.md``, hand-worked in a
separate pass; ``tests/test_retaining_court.py`` reproduces it and breaks each condition in
:func:`_verify` in turn to confirm the answer is INCOMPLETE and never OK.

**At-rest governs** (:data:`AT_REST_IS_THE_GRADED_CASE`): a permanent base restraint and an
active wedge are not both available.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.engineering import owner_bases, retaining_sheet
from typehaus.engineering import retaining_system_cases as cases
from typehaus.engineering import retaining_system_rows as rows
from typehaus.engineering import retaining_system_staged as staged
from typehaus.engineering import retaining_system_working as W
from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Status,
    declare_sheet,
    item_id,
)
from typehaus.engineering.registry import (
    EngineeringContext,
    calc,
    keys,
    oracled_by,
)
from typehaus.engineering.retaining_basis import (
    BASIS,
    REQUIRED_FS,
    _base_interface,
    _geometry,
    analyse,
)
from typehaus.engineering.retaining_system_fallback import fallback_states
from typehaus.engineering.retaining_system_loop import (
    _foundation_walls,
    _verify,
)
from typehaus.engineering.soil import (
    SOIL_UNIT_WEIGHT_BAND_PCF,
    presumptive,
    soil_is_presumed,
    soil_provenance_note,
)
from typehaus.engineering.tier_surcharge import court_surcharges

KIND = "retaining_system"
declare_sheet(KIND, **retaining_sheet.SYSTEM_SHEET)

#: Bumped whenever the arithmetic moves; it rides in the fingerprint. "2" derived strut
#: reaction (2026-09-14); "3" apron surcharge (2026-09-20); "4" one body, the case set, plan
#: bending, strut at its f'c, staged backfill (2026-11-22); "5" soil basis fingerprinted;
#: "6" the plan rows' toe-edge ties (As, centroid) fingerprinted (2026-11-23).
BASIS_VERSION = "6"

#: At-rest, not active: a permanent base restraint concedes the walls cannot move enough to
#: mobilise the active wedge (a 12" stem moves ~0.0013H, the bottom of 0.001H-0.004H).
AT_REST_IS_THE_GRADED_CASE = True

_M_PER_FT = 0.3048


@dataclass(frozen=True)
class _Member:
    """One wall in the loop, with the vector its thrust acts along."""

    tag: str
    length_ft: float
    thrust_plf: float
    weight_plf: float
    friction: float
    #: Unit vector the retained soil pushes this wall along, in plan. The exterior face is
    #: at ``+outward_sign * normal(start->end)`` (``resolve/orientation``), so the soil
    #: pushes the other way.
    push: tuple[float, float]
    #: The stem's own section, feet — what the wall has to pass in-plane shear THROUGH when
    #: its base cannot hold its own thrust. Zero where the model does not say, which
    #: :func:`_corner_transfer` reports rather than defaults around.
    stem_thickness_ft: float = 0.0
    stem_height_ft: float = 0.0

    @property
    def demand_lb(self) -> float:
        return self.thrust_plf * self.length_ft

    @property
    def capacity_lb(self) -> float:
        return self.friction * self.weight_plf * self.length_ft

    @property
    def unassisted_shortfall_lb(self) -> float:
        """What this member's OWN base cannot hold of its OWN thrust (unit section): the
        force that has to reach the loop. ``thermal_break`` reads it; the court's own load
        path is graded by the plan-bending and corner-delivery rows."""
        return max(0.0, self.demand_lb - self.capacity_lb)


def _loops(ctx: EngineeringContext) -> dict[str, list]:
    """Groups of walls that name the same ``base_restraint_ref``, keyed by that ref.

    The key is the **cross-member's tag** and not an invented group name. That is what makes
    the item id ``retaining_system/W-SG-ARCH`` name a thing the model actually contains — the
    element whose presence closes the loop and whose removal breaks it, which is exactly the
    edit that should stale the seal. ``retaining_system/SG-COURT`` would name nothing, and
    ``EngineeringRecord``'s identity rule is that an item is per element.
    """
    groups: dict[str, list] = {}
    for wall in _foundation_walls(ctx):
        ref = getattr(wall, "base_restraint_ref", None)
        if ref and getattr(wall, "lateral_support", None) == "base":
            groups.setdefault(ref, []).append(wall)
    return {ref: sorted(walls, key=lambda w: w.tag) for ref, walls in groups.items()}


def _members(ctx: EngineeringContext, walls: list, *, soil, soil_pcf: float
             ) -> tuple[list[_Member], list[str]]:
    """Each wall's thrust, weight and push direction, on one soil unit weight."""
    from typehaus.resolve.orientation import resolve_storey_windings, wall_outward_sign

    out: list[_Member] = []
    missing: list[str] = []
    # The apron founded in the retained soil pushes too (``tier_surcharge``), and the loop
    # carries that thrust as it carries the earth's.
    tiers, tier_missing = court_surcharges(ctx, soil_pcf)
    for wall in walls:
        geometry, geometry_missing = _geometry(ctx, wall)
        if geometry is None:
            missing.extend(geometry_missing)
            continue
        missing.extend(tier_missing.get(wall.tag, ()))
        base = _base_interface(ctx, wall) or soil
        tier = tiers.get(wall.tag)
        case = analyse(geometry, soil, at_rest=AT_REST_IS_THE_GRADED_CASE,
                       soil_pcf=soil_pcf, base=base,
                       surcharge=tier.surcharge if tier is not None else None)
        resolved = next((w for w in ctx.model.walls if w.tag == wall.tag), None)
        if resolved is None:
            missing.append(f"a resolved {wall.tag} to take its length and direction from")
            continue
        (x0, y0), (x1, y1) = resolved.axis
        dx, dy = x1 - x0, y1 - y0
        length_m = (dx * dx + dy * dy) ** 0.5
        if not length_m:
            missing.append(f"a non-zero length on {wall.tag}")
            continue
        windings = resolve_storey_windings(ctx.plan, resolved.storey)
        sign = wall_outward_sign(ctx.plan, wall, resolved.storey,
                                 windings.sign_for_wall(wall))
        # Left-hand normal of start->end, per ``resolve/geometry.normal``. The exterior face
        # is at +sign along it, so the retained soil pushes along -sign.
        nx, ny = -dy / length_m, dx / length_m
        out.append(_Member(
            tag=wall.tag, length_ft=length_m / _M_PER_FT, thrust_plf=case.thrust_plf,
            weight_plf=case.weight_plf, friction=base.friction_coefficient,
            push=(-sign * nx, -sign * ny),
            stem_thickness_ft=geometry.stem_thickness_ft,
            stem_height_ft=geometry.stem_height_ft))
    return out, missing


def _free_body(members: list[_Member]) -> tuple[float, float, float]:
    """``(demand_lb, capacity_lb, cancelled_lb)`` for the group as one rigid body.

    The demand is the **2-D resultant** of the members' thrusts, not their scalar sum: two
    walls facing each other across a court push in opposite directions and equilibrium is
    where the cancellation belongs. Friction is isotropic, so every member's base resists
    the resultant whichever way it points.
    """
    rx = sum(m.demand_lb * m.push[0] for m in members)
    ry = sum(m.demand_lb * m.push[1] for m in members)
    demand = (rx * rx + ry * ry) ** 0.5
    scalar = sum(m.demand_lb for m in members)
    return demand, sum(m.capacity_lb for m in members), scalar - demand


#: The independent hand pass this module is checked against — see ``Oracle``.
#: The closed-loop court free body is hand-worked start to finish in the first note; the
#: isolated free cantilever the loop is compared against is §4 of the second.
oracled_by(
    KIND,
    Oracle(note="sunken_garden_court_free_body.md", test="tests/test_retaining_court.py"),
    Oracle(note="sunken_garden_retaining_screening.md", section="§4",
           test="tests/test_retaining_wall_calc.py"),
)


@keys(KIND)
def enumerate_systems(ctx: EngineeringContext) -> list[str]:
    return sorted(_loops(ctx))


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, ref, members) for ref, members in sorted(_loops(ctx).items())]


def _built(ctx: EngineeringContext, members: list, soil) -> tuple[dict, list[str]]:
    by_pcf, missing = {}, []
    for pcf in SOIL_UNIT_WEIGHT_BAND_PCF:
        built, gap = _members(ctx, members, soil=soil, soil_pcf=pcf)
        missing.extend(gap)
        by_pcf[pcf] = built
    return by_pcf, missing


def system_factors(ctx: EngineeringContext, ref: str, members: list
                   ) -> dict[str, tuple[float, float]] | None:
    """``{soil_pcf: (dry resultant lb, dry base friction lb)}`` of the footing-plane body —
    what a per-wall record quotes back and ``thermal_break`` pushes the court against.

    Both records read the SAME body; each picks the end of the band adverse to it (110 pcf
    for sliding, 130 for the break's restraint rows), and each says which.
    """
    soil = presumptive(getattr(ctx, "soil_class", None),
                       basis=getattr(ctx, "soil_basis", None))
    if soil is None or _verify(ctx, ref, members):
        return None
    built, missing = _built(ctx, members, soil)
    if missing:
        return None
    graded, gap = cases.grade(ctx, ref, members, built, soil)
    if graded is None or gap:
        return None
    return {f"{pcf:.0f}": value for pcf, value in graded.dry.items()}


def _graded_loops(ctx: EngineeringContext) -> dict:
    soil = presumptive(getattr(ctx, "soil_class", None))
    out = {}
    for ref, members in _loops(ctx).items():
        if soil is None or _verify(ctx, ref, members):
            continue
        built, missing = _built(ctx, members, soil)
        graded, gap = (None, True) if missing else cases.grade(ctx, ref, members, built, soil)
        if graded is not None and not gap:
            out[ref] = graded
    return out


def loop_mobilisation(ctx: EngineeringContext) -> dict[str, dict[float, tuple[float, float]]]:
    """``{loop ref: Graded.mobilised}`` for every verified loop (the joint row reads it)."""
    return {ref: g.mobilised for ref, g in _graded_loops(ctx).items()}


def loop_free_bodies(ctx: EngineeringContext, *, restraint: bool = False
                     ) -> dict[str, dict[str, tuple[float, float]]]:
    """``{loop ref: {soil_pcf: (soil resultant, base friction)}}`` at the design friction, or
    the 5-tuple ``Graded.restraint`` at the upper friction (the winter rows read it)."""
    return {ref: {f"{pcf:.0f}": v for pcf, v in (g.restraint if restraint else g.dry).items()}
            for ref, g in _graded_loops(ctx).items()}


def footing_shortfalls(ctx: EngineeringContext
                       ) -> dict[str, dict[float, dict[str, float]]]:
    """``{loop ref: {soil_pcf: {member tag: own thrust less own friction}}}``."""
    soil = presumptive(getattr(ctx, "soil_class", None),
                       basis=getattr(ctx, "soil_basis", None))
    if soil is None:
        return {}
    out: dict[str, dict[float, dict[str, float]]] = {}
    for ref, members in _loops(ctx).items():
        if _verify(ctx, ref, members):
            continue
        by_pcf: dict[float, dict[str, float]] = {}
        for pcf in SOIL_UNIT_WEIGHT_BAND_PCF:
            built, missing = _members(ctx, members, soil=soil, soil_pcf=pcf)
            if missing:
                break
            by_pcf[pcf] = {m.tag: m.unassisted_shortfall_lb for m in built}
        else:
            out[ref] = by_pcf
    return out


def _surcharge_notes(ctx: EngineeringContext, built: list[_Member], pcf: float
                     ) -> tuple[str, ...]:
    tiers, _ = court_surcharges(ctx, pcf)
    parts = [f"{m.tag} +{tiers[m.tag].surcharge.lateral_plf:,.0f} plf via "
             f"{tiers[m.tag].surcharge.source}" for m in built if m.tag in tiers]
    if not parts:
        return ()
    return (f"APRON SURCHARGE, in every thrust above at {pcf:.0f} pcf: " + "; ".join(parts)
            + ". The raised-garden SRW apron stands on its pad inside the retained soil; its "
            "net bearing is a rigid-wall Boussinesq strip load (IBC 2018 §1610.1), worked on "
            "each wall's retaining_wall record. Equal aprons on the two side walls still "
            "cancel; the south wall's does not, so it reaches the resultant whole. The deep "
            "plane carries it too, on the court's deep-plane rows.",)


def _incomplete(ref: str, tags: tuple, summary: str, missing, **extra) -> EngineeringRecord:
    return EngineeringRecord(
        item_id=item_id(KIND, ref), kind=KIND, key=ref, basis_version=BASIS_VERSION,
        basis=BASIS, status=Status.INCOMPLETE, summary=summary,
        missing=tuple(dict.fromkeys(missing)), element_tags=tags, **extra)


def _one(ctx: EngineeringContext, ref: str, members: list) -> EngineeringRecord:
    tags = tuple(sorted({ref, *(w.tag for w in members)}))
    soil = presumptive(getattr(ctx, "soil_class", None),
                       basis=getattr(ctx, "soil_basis", None))
    missing: list[str] = []
    if soil is None:
        missing.append("a declared soil class (Site/profile soil_class)")
    missing.extend(_verify(ctx, ref, members))
    built_by_pcf: dict[float, list[_Member]] = {}
    if not missing:
        built_by_pcf, gap = _built(ctx, members, soil)
        missing.extend(gap)
    graded = None
    if not missing:
        graded, gap = cases.grade(ctx, ref, members, built_by_pcf, soil)
        missing.extend(gap)
    if missing or graded is None:
        return _incomplete(ref, tags, f"{ref}: the court's base restraint could not be "
                           f"verified, so the walls it is claimed to restrain have no closed "
                           f"free body", missing)

    low = SOIL_UNIT_WEIGHT_BAND_PCF[0]
    cross = ctx.plan.by_tag(ref)
    built = built_by_pcf[low]
    from typehaus.engineering.retaining_system_body import footing_plane_body

    members_low = cases.members_for(ctx, members, built, soil, low)
    body, _ = footing_plane_body(ctx, ref, members, members_low, soil_pcf=low,
                                 friction=graded_friction(ctx, members))
    braced = [w for w in ctx.plan.all_elements() if w.tag in body.spliced]
    states = list(graded.states)
    strut = rows.strut(ctx, cross, body, braced, built)
    if strut is not None:
        states.append(strut)
    else:
        missing.append(f"a resolvable section and axis on {ref} for the strut row")
    states.extend(rows.plan_bending(ctx, body, members_low, built))
    floor = max(p.z1_ft for p in body.prisms if p.label.startswith("footing:"))
    geometry, _ = _geometry(ctx, members[0])
    worst, empty, loop_only, stage = staged.staged(
        body, members_low, floor, geometry.stem_thickness_ft if geometry else 1.0)
    states.append(LimitState(
        f"staged backfill, no side more than {staged.RULE:.0%} of H above another",
        REQUIRED_FS, worst, "", (
            f"IRC R404.4 — the completed body at every stage the rule allows (grid of "
            f"twelfths of H per side, earth only, {low:.0f} pcf, spliced walls empty): worst "
            f"FS {worst:.2f} with " + ", ".join(
                f"{t[0]} at {round(f * 12)}/12" for t, f in zip(stage.thrusts, stage.fills,
                                                                 strict=True))
            + f"; one side empty and two full {empty:.2f}; the loop alone without "
            f"the spliced walls' concrete {loop_only:.2f}"), is_safety_factor=True,
        combination=W.SERVICE_BACKFILL[0], combination_factors=W.SERVICE_BACKFILL[1],
        working=W.staged_steps(body, worst, empty, loop_only, staged.RULE, stage)))

    soil_state, soil_how = cases.design_friction(ctx, soil)[2:]
    if soil_state == "specified":
        states.extend(fallback_states(ctx, ref, members, members_low, floor,
                                      geometry.stem_thickness_ft if geometry else 1.0))
    pending = list(graded.pending)
    inputs = tuple(
        item for member in built for item in (
            Quantity(f"thrust_{member.tag}", member.thrust_plf, "plf", 1.0),
            Quantity(f"weight_{member.tag}", member.weight_plf, "plf", 1.0),
            Quantity(f"length_{member.tag}", member.length_ft, "ft", 0.01),
        )
    ) + cases.soil_inputs(ctx, soil) + graded.inputs + (
        Quantity("cross_thickness", rows.cross_section_in(ctx, cross)[0], "in", 0.5),
        Quantity("cross_height", rows.cross_section_in(ctx, cross)[1], "in", 0.01),
        Quantity("cross_fc", rows.cross_fc(ctx, cross)[0], "psi", 1.0),
        Quantity("soil_presumed", 1.0 if soil_is_presumed(soil) else 0.0, "-", 0.5),
    ) + rows.tie_inputs(ctx, members_low)
    demand, capacity = graded.dry[low]
    notes = (
        f"ONE body, not {len(members)} walls: cast into a closed loop through {ref}, so the "
        f"thrusts sum as a 2-D resultant and opposed walls cancel in equilibrium. The body is "
        f"read off the resolved solids — every footing and stem in the loop, the strut, the "
        f"walls spliced to it ({', '.join(sorted(t for t in body.spliced if t.startswith('W')))}"
        f", concrete only, their own thrusts carried by their own braces) and the retained "
        f"soil on the retaining heels, corner squares included.",
        "EACH PUSH ACTS ON THE BODY'S PROJECTED WIDTH (" + ", ".join(
            f"{p.tag} {p.width_ft:.2f}'" for p in body.pushes) + "): the retained soil "
        "pushes on every soil face of the body, corner squares included, not on a wall's "
        "axis length. Favourable soil pressure on its north-facing soil faces is not "
        "credited.",
        "GRADED AT AT-REST (60 psf/ft): a permanent base restraint and an active wedge are "
        "not both available.",
        f"DRY: {capacity:,.0f} lb of base friction against {demand:,.0f} lb of resultant at "
        f"{low:.0f} pcf. The 130 pcf end is adverse to the thermal break's restraint rows "
        f"(more heel soil, more friction) and that record reads it; this one reads 110.",
        soil_provenance_note(soil),
        f"SOIL BASIS — {soil_how}. " + {
            "specified": "Stated basis, section 6; the fallback rows pre-check the printed "
                         "lean wall on the presumptions.",
            "confirmed": "Soil parameters CONFIRMED by the site report.",
            "presumptive": "No site report and no specified parameters."}[soil_state],
        "CORNERS: the footings' longitudinal bars are lap-spliced through both joints of "
        "each side footing, and the south footing runs out to out under both corners; the "
        "side footings' plan bending and the south footing's corner delivery are the rows "
        "that grade that path.",
        "Sequence: the cross-member is cast with the footings (placement 1), so the loop is "
        "closed before any backfill; the staged row grades the backfill rule the drawing "
        "prints.",
    ) + graded.notes + _surcharge_notes(ctx, built, low)

    soil_basis = cases.soil_stated_basis(ctx, soil)
    bases = (*((soil_basis,) if soil_basis else ()), *graded.bases,
             owner_bases.BACKFILL_CONDITIONS)
    governing = max(states, key=lambda state: state.ratio)
    over = [s for s in states if not s.ok]
    open_rows = [s for s in over if s.name in {name for name, _ in pending}]
    if pending and len(open_rows) == len(over):
        return _incomplete(
            ref, tags, (f"{ref}: dry sliding FS {capacity / demand:.2f}; open — "
                        + "; ".join(f"{s.name} {s.capacity:.2f}" if s.is_safety_factor
                                    else f"{s.name} d/c {s.ratio:.2f}" for s in open_rows)),
            [*missing, *(text for _, text in pending)], inputs=inputs,
            limit_states=tuple(states), notes=notes, bases=bases)
    return EngineeringRecord(
        item_id=item_id(KIND, ref), kind=KIND, key=ref,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over else (Status.INCOMPLETE if missing else Status.OK),
        summary=(f"{ref} closes a {len(members)}-wall court: {demand:,.0f} lb of resultant "
                 f"thrust against {capacity:,.0f} lb of base friction, dry FS "
                 f"{capacity / demand:.2f} against the 1.50 IRC R404.4 requires "
                 f"({governing.name} governs)"),
        inputs=inputs, limit_states=tuple(states), missing=tuple(missing), notes=notes,
        element_tags=tags, bases=bases)


def graded_friction(ctx: EngineeringContext, members: list) -> float:
    soil = presumptive(getattr(ctx, "soil_class", None))
    return cases.design_friction(ctx, soil)[0]
