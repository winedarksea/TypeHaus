"""A cast beam carrying a masonry wythe between two walls — ``veneer_beam/<beam tag>``.

Promoted 2026-09-20 from the report-only screening in ``sunken_garden/veneer_beam.py`` to a
registered kind that reads the plan: the section off the beam's own STRUCTURE layer (the
concrete only — ``SG_VENEER_BEAM_14``'s 2" ``xps-break`` is not section), the supports off
the walls whose pour it overlaps, the load off the wythe it carries, and the steel off its
``ReinforcementSpec`` (counts, through ``retaining_basis.bar_count_for_roles``).

Graded at U = 1.4D: flexure, minimum steel, shear, torsion in EQUILIBRIUM (no §22.7.3.2
redistribution is relied on), the §9.6.4/§9.7 torsion detailing, deflection after the wythe
is attached (TMS 402-22 §13.1.2.3's ℓ/600 and ACI Table 24.2.2's ℓ/480), and end anchorage of
each longitudinal row
(``veneer_beam_anchorage``): hooked into the supporting wall, or through dowels cast in the
footing where the row sits below the wall. A row with no authored hook, tie credit or dowel is
INCOMPLETE naming it — never assumed. ``Scope.SCREENING``.

An authored ``FoundationWall.end_restraint`` credits partial fixity at the monolithic end
joints — for SERVICEABILITY only, so midspan flexure stays graded at α = 0 and a softer joint
can never buy strength. What the fixity adds is ``veneer_beam_joint``. Unauthored, the beam
is a simple span and the ℓ/600 row says so.

Oracle: ``houses/catlin/notes/sunken_garden_veneer_beam.md`` §6, reproduced by
``tests/test_veneer_beam_calc.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Scope,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by
from typehaus.engineering.retaining_basis import (
    REINFORCEMENT_FY_PSI,
    bar_count_for_roles,
    bar_for_roles,
)
from typehaus.engineering.soil import CONCRETE_UNIT_WEIGHT_PCF
from typehaus.engineering.sunken_garden.veneer_beam import (
    DEAD_LOAD_FACTOR,
    TORSION_THRESHOLD_COEFFICIENT,
    check_veneer_beam,
    deflection_after_attachment,
    torsion_design,
)
from typehaus.engineering.veneer_beam_anchorage import anchor_rows
from typehaus.engineering.veneer_beam_joint import joint_states
from typehaus.model.rebar import BARS

KIND = "veneer_beam"
BASIS_VERSION = "3"
BASIS = "ACI 318-19 (strength design at U = 1.4D, Eq. 5.3.1a); §22.7 torsion; §24.2 deflection"
_COMBO = "ACI 318-19 Eq. (5.3.1a) U = 1.4D"
_M_PER_IN = 0.0254
_TOL_M = 1e-4
_Vec = tuple[float, float]


def _footingless_walls(ctx: EngineeringContext) -> list[Any]:
    from typehaus.model.structure import Footing, FoundationWall

    hosted = {f.under for f in ctx.plan.all_elements() if isinstance(f, Footing)}
    return [w for w in ctx.plan.all_elements()
            if isinstance(w, FoundationWall) and w.tag not in hosted]


def _resolved(ctx: EngineeringContext, tag: str) -> Any:
    return next((w for w in ctx.model.walls if w.tag == tag), None)


def _extent(ctx: EngineeringContext, tag: str) -> tuple[float, float, float, float] | None:
    wall = _resolved(ctx, tag)
    if wall is None:
        return None
    (ax, ay), (bx, by) = wall.axis
    return min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)


def _near(first: Any, second: Any, tol: float = 0.3048) -> bool:
    """Axis boxes within 1 ft — a wall bearing on a beam is within its own thickness of it."""
    if first is None or second is None:
        return False
    return bool(first[0] - tol <= second[2] and second[0] - tol <= first[2]
                and first[1] - tol <= second[3] and second[1] - tol <= first[3])


def veneer_beams(ctx: EngineeringContext) -> list[tuple[Any, tuple[Any, ...]]]:
    """``(beam, walls it carries)``: a footingless wall whose TOP is the BOTTOM of another
    footingless wall that declares no lateral support, the two overlapping in plan.

    The relation, not a tag. A screening predicate stated as one: a beam carrying a slab
    edge or a stair is not found here, and a house that builds one should widen this.
    """
    walls = _footingless_walls(ctx)
    boxes = {w.tag: _extent(ctx, w.tag) for w in walls}
    out = []
    for beam in sorted(walls, key=lambda w: w.tag):
        if beam.top_elevation is None:
            continue
        carried = tuple(
            w for w in sorted(walls, key=lambda w: w.tag)
            if w.tag != beam.tag and w.bottom_elevation is not None
            and getattr(w, "lateral_support", None) is None
            and abs(w.bottom_elevation.meters - beam.top_elevation.meters) <= 1e-6
            and _near(boxes.get(beam.tag), boxes.get(w.tag)))
        if carried:
            out.append((beam, carried))
    return out


@keys(KIND)
def enumerate_veneer_beams(ctx: EngineeringContext) -> list[str]:
    return [beam.tag for beam, _carried in veneer_beams(ctx)]


def carried_wythes(ctx: EngineeringContext) -> list[str]:
    """Every wall a veneer beam carries — ``veneer_anchor``'s keys, off the same relation."""
    return sorted({w.tag for _beam, carried in veneer_beams(ctx) for w in carried})


# --- geometry off the resolved model ------------------------------------------------------

@dataclass(frozen=True)
class _Band:
    """A STRUCTURE layer projected onto the beam's frame: ``u`` along it, ``n`` across, m."""

    tag: str
    u0: float
    u1: float
    n0: float
    n1: float
    z0: float
    z1: float


def _structure(wall: Any) -> Any:
    return next((ly for ly in wall.layers
                 if ly.function == "structure" and not ly.is_cavity), None)


def _band(wall: Any, origin: _Vec, u: _Vec, n: _Vec) -> _Band | None:
    layer = _structure(wall)
    if layer is None or not layer.polygon:
        return None
    us = [(p[0] - origin[0]) * u[0] + (p[1] - origin[1]) * u[1] for p in layer.polygon]
    ns = [(p[0] - origin[0]) * n[0] + (p[1] - origin[1]) * n[1] for p in layer.polygon]
    return _Band(wall.tag, min(us), max(us), min(ns), max(ns), wall.z0_m, wall.z1_m)


def _frame(beam: Any) -> tuple[_Vec, _Vec, _Vec]:
    (ax, ay), (bx, by) = beam.axis
    length = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
    u = ((bx - ax) / length, (by - ay) / length)
    return (ax, ay), u, (-u[1], u[0])


def _supports(ctx: EngineeringContext, own: _Band, skip: set[str], origin: _Vec, u: _Vec,
              n: _Vec) -> tuple[list[_Band], list[_Band]]:
    """The walls whose pour the beam's own pour overlaps, split by which end they hold."""
    start: list[_Band] = []
    end: list[_Band] = []
    for wall in ctx.model.walls:
        if wall.tag in skip:
            continue
        band = _band(wall, origin, u, n)
        if band is None:
            continue
        if (min(band.u1, own.u1) - max(band.u0, own.u0) <= _TOL_M
                or min(band.n1, own.n1) - max(band.n0, own.n0) <= _TOL_M
                or min(band.z1, own.z1) - max(band.z0, own.z0) <= _TOL_M):
            continue
        (start if (band.u0 + band.u1) < (own.u0 + own.u1) else end).append(band)
    return start, end


def _end_gaps(wythes: list[_Band], west: _Band, east: _Band) -> str:
    """How far each end of the carried wythe(s) stands off the supporting wall's face."""
    lo, hi = min(b.u0 for b in wythes), max(b.u1 for b in wythes)
    return (f"{(lo - west.u1) / _M_PER_IN:.2f}\" clear of {west.tag} and "
            f"{(east.u0 - hi) / _M_PER_IN:.2f}\" clear of {east.tag}")


# --- the record ---------------------------------------------------------------------------

def _state(name: str, demand: float, capacity: float, unit: str, citation: str, *,
           detailing: bool = False) -> LimitState:
    return LimitState(name, demand, capacity, unit, citation, is_detailing=detailing,
                      combination=_COMBO, combination_factors=(("D", DEAD_LOAD_FACTOR),))


def _one(ctx: EngineeringContext, beam: Any, carried: tuple[Any, ...]) -> EngineeringRecord:
    from typehaus.resolve.assembly_weight import dead_load_plf
    from typehaus.resolve.concrete import concrete_spec_for, cover_for, fc_psi

    tags = (beam.tag, *(w.tag for w in carried))
    missing: list[str] = []
    resolved = _resolved(ctx, beam.tag)
    origin, u, n = _frame(resolved) if resolved is not None else ((0.0, 0.0), (1, 0), (0, 1))
    own = _band(resolved, origin, u, n) if resolved is not None else None
    if own is None:
        missing.append(f"a resolved concrete STRUCTURE layer on {beam.tag}")
    fc = fc_psi(concrete_spec_for(ctx.plan, beam))
    if fc is None:
        missing.append(f"a ConcreteSpec (f'c) on {beam.tag}'s assembly")
    cover, _where = cover_for(ctx.plan, beam)
    if cover is None:
        missing.append(f"a cover on {beam.tag}'s ReinforcementSpec or mix")
    spec = getattr(beam, "reinforcement", None)
    bottom = bar_count_for_roles(spec, ("bottom-y",))
    top = bar_count_for_roles(spec, ("top-y",))
    side = bar_count_for_roles(spec, ("horizontal",))
    hoop = bar_for_roles(spec, ("ties", "stirrups"))
    for got, what in ((bottom, "a `bottom-y` bar COUNT"), (top, "a `top-y` bar COUNT"),
                      (hoop, "`ties` at a spacing (the closed hoops)")):
        if got is None:
            missing.append(f"{what} in {beam.tag}'s ReinforcementSpec")

    wythe_plf, ecc_num = 0.0, 0.0
    wythe_bands: list[_Band] = []
    for wall in carried:
        rw = _resolved(ctx, wall.tag)
        plf = dead_load_plf(ctx, rw, rw.z1_m - rw.z0_m) if rw is not None else None
        band = _band(rw, origin, u, n) if rw is not None else None
        if plf is None or band is None or own is None:
            missing.append(f"a weighable STRUCTURE layer (material density) on {wall.tag}")
            continue
        wythe_plf += plf
        wythe_bands.append(band)
        ecc_num += plf * abs((band.n0 + band.n1) / 2.0 - (own.n0 + own.n1) / 2.0)

    start: list[_Band] = []
    end: list[_Band] = []
    if own is not None:
        start, end = _supports(ctx, own, set(tags), origin, u, n)
        if len(start) != 1 or len(end) != 1:
            missing.append(f"exactly one supporting wall at each end of {beam.tag} (found "
                           f"{[b.tag for b in start]} / {[b.tag for b in end]})")
    # Anything missing so far leaves nothing gradeable: every state reads the section, the
    # steel, the span and the load together.
    if missing:
        return EngineeringRecord(
            item_id=item_id(KIND, beam.tag), kind=KIND, key=beam.tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{beam.tag}: cannot be graded — {len(missing)} input(s) missing",
            missing=tuple(missing), element_tags=tags, scope=Scope.SCREENING)
    assert own is not None and fc is not None and cover is not None
    assert bottom is not None and top is not None and hoop is not None

    width = (own.n1 - own.n0) / _M_PER_IN
    depth = (own.z1 - own.z0) / _M_PER_IN
    (w_sup,), (e_sup,) = start, end
    clear_ft = (e_sup.u0 - w_sup.u1) / _M_PER_IN / 12.0
    bearing = ((w_sup.u1 - own.u0) + (own.u1 - e_sup.u0)) / 2.0 / _M_PER_IN
    self_plf = CONCRETE_UNIT_WEIGHT_PCF * width * depth / 144.0
    ecc = ecc_num / wythe_plf / _M_PER_IN
    hoop_bar, hoop_s = hoop
    hoop_d, bot_bar = BARS[hoop_bar].diameter_in, BARS[bottom[0]]
    screen = check_veneer_beam(
        clear_span_ft=clear_ft, bearing_in=bearing, width_in=width, depth_in=depth,
        fc_psi=fc, fy_psi=REINFORCEMENT_FY_PSI, clear_cover_in=cover,
        stirrup_diameter_in=hoop_d, longitudinal_bar_diameter_in=bot_bar.diameter_in,
        provided_bar_count=bottom[1], provided_bar_area_in2=bot_bar.area_in2,
        veneer_load_plf=wythe_plf, beam_load_plf=self_plf, eccentricity_in=ecc)
    d, span = screen.effective_depth_in, screen.effective_span_ft
    tors = torsion_design(
        tu_ftlb=screen.factored_torsion_ftlb, vu_lb=screen.factored_shear_lb, width_in=width,
        depth_in=depth, d_in=d, cover_in=cover, hoop_diameter_in=hoop_d,
        hoop_leg_area_in2=BARS[hoop_bar].area_in2, hoop_spacing_in=hoop_s, fc_psi=fc)
    top_area = top[1] * BARS[top[0]].area_in2
    side_area = (side[1] * side[2] * BARS[side[0]].area_in2) if side else 0.0
    restraint = getattr(beam, "end_restraint", None)
    defl = deflection_after_attachment(
        span_ft=span, service_plf=screen.service_load_plf, self_plf=self_plf, width_in=width,
        depth_in=depth, d_in=d, tension_in2=screen.provided_steel_in2,
        compression_in2=top_area, fc_psi=fc,
        end_fixity=float(restraint.fixity) if restraint is not None else 0.0)
    inset = cover + hoop_d + bot_bar.diameter_in / 2.0
    vgap = (depth - 2.0 * inset) / ((side[1] if side else 0) + 1)
    hgap = (width - 2.0 * inset) / max(bottom[1] - 1, 1)
    long_req = max(screen.required_steel_in2, screen.minimum_steel_in2) + tors.al_required_in2
    long_prov = screen.provided_steel_in2 + top_area + side_area
    phi_mn = screen.factored_moment_ftlb / screen.flexure_ratio

    states = [
        _state("flexure, simple span", screen.factored_moment_ftlb, phi_mn, "ft-lb",
               "ACI 318-19 §22.2, φ 0.90; simple span — no end fixity credited"),
        _state("minimum flexural steel", screen.minimum_steel_in2,
               screen.provided_steel_in2, "in2", "ACI 318-19 §9.6.1.2", detailing=True),
        _state("one-way shear", screen.factored_shear_lb,
               screen.factored_shear_lb / screen.shear_ratio, "lb",
               "ACI 318-19 Table 22.5.5.1(a), 2λ√f'c — Av ≥ Av,min from the hoops"),
        _state("torsion transverse steel, equilibrium (one leg)", tors.at_s_required,
               tors.at_s_provided, "in2/in",
               "ACI 318-19 §22.7.6.1, θ 45°, Ao 0.85 Aoh — no §22.7.3.2 redistribution"),
        _state("torsion section limit", tors.combined_stress_psi, tors.stress_limit_psi, "psi",
               "ACI 318-19 §22.7.7.1(a)"),
        _state("closed hoop spacing", hoop_s, tors.hoop_spacing_max_in, "in",
               "ACI 318-19 §9.7.6.3.3, min(ph/8, 12\")", detailing=True),
        _state("minimum transverse torsion steel", tors.transverse_min,
               tors.transverse_provided, "in2/in", "ACI 318-19 §9.6.4.2", detailing=True),
        _state("longitudinal steel, flexure + torsion", long_req, long_prov, "in2",
               "ACI 318-19 §9.5.4.3 with Al,min per §9.6.4.3", detailing=True),
        _state("longitudinal bar spacing around the perimeter", max(vgap, hgap), 12.0, "in",
               "ACI 318-19 §9.7.5.1", detailing=True),
        LimitState(
            "deflection after the wythe is attached, TMS ℓ/600", defl.after_attachment_in,
            defl.limit_600_in, "in",
            "TMS 402-22 §13.1.2.3 (ℓ/600), the governing limit for a horizontally spanning "
            "member supporting veneer; Ie per Table 24.2.3.5"
            + (f" averaged 0.70/0.30 per §24.2.3.6 (avg {defl.effective_inertia_in4:,.1f}, "
               f"end {defl.effective_inertia_end_in4:,.1f} in⁴) at α {defl.end_fixity:g}"
               if defl.end_fixity else " at midspan, simple span (α 0)")
            + ", λΔ per §24.2.4.1",
            combination="service D, sustained", combination_factors=(("D", 1.0),)),
        LimitState("deflection after the wythe is attached, ACI ℓ/480",
                   defl.after_attachment_in, defl.limit_480_in, "in",
                   "ACI 318-19 Table 24.2.2 (ℓ/480) — the looser of the pair, graded beside "
                   "the TMS row rather than instead of it",
                   combination="service D, sustained", combination_factors=(("D", 1.0),)),
    ]
    joint_notes: list[str] = []
    if restraint is not None:
        joint, joint_notes = joint_states(
            ctx, restraint, (w_sup, e_sup), factored_moment_ftlb=screen.factored_moment_ftlb,
            beam_phi_mn_ftlb=phi_mn, beam_width_in=width, beam_d_in=d)
        states.extend(joint)

    # End anchorage of each row: hooked into the wall, or dowelled into the footing below it.
    mix_coating = getattr(concrete_spec_for(ctx.plan, beam), "bar_coating", "") or ""
    epoxy = "epoxy" in f"{' '.join(b.coating or '' for b in spec.bars)} {mix_coating}".lower()
    ends = anchor_rows(ctx, beam, spec, {"top-y": top, "bottom-y": bottom}, (w_sup, e_sup), own,
                       (origin, u, n), (width, cover, hoop_d), epoxy)
    states.extend(ends.states)
    missing.extend(ends.missing)
    notes_ldh = ends.notes

    over = any(not s.ok for s in states)
    status = Status.OVER if over else (Status.INCOMPLETE if missing else Status.OK)
    worst = max((s for s in states if not s.is_detailing), key=lambda s: s.ratio)
    threshold = (TORSION_THRESHOLD_COEFFICIENT * fc ** 0.5 * (width * depth) ** 2
                 / (2.0 * (width + depth)) / 12.0 * 0.75)
    return EngineeringRecord(
        item_id=item_id(KIND, beam.tag), kind=KIND, key=beam.tag,
        basis_version=BASIS_VERSION, basis=BASIS, status=status,
        summary=(f"{beam.tag}: {width:.0f}\" x {depth:.2f}\" beam spanning {clear_ft:.2f}' "
                 f"between {w_sup.tag} and {e_sup.tag}, carrying {wythe_plf:.0f} plf of "
                 f"{', '.join(w.tag for w in carried)} — d/c {worst.ratio:.2f}, governed by "
                 f"{worst.name}" + (f"; {len(missing)} input(s) missing" if missing else "")),
        inputs=(
            Quantity("section_width", width, "in", 0.0625),
            Quantity("section_depth", depth, "in", 0.0625),
            Quantity("clear_span", clear_ft, "ft", 0.01),
            Quantity("bearing", bearing, "in", 0.0625),
            Quantity("wythe_load", wythe_plf, "plf", 1.0),
            Quantity("self_weight", self_plf, "plf", 1.0),
            Quantity("eccentricity", ecc, "in", 0.0625),
            Quantity("fc", fc, "psi", 1.0),
            Quantity("cover", cover, "in", 0.0625),
            Quantity("bottom_bars", float(bottom[1]), "count", None),
            Quantity("top_bars", float(top[1]), "count", None),
            Quantity("hoop_spacing", hoop_s, "in", 0.0625),
            Quantity("end_fixity", defl.end_fixity, "-", 0.01),
        ),
        limit_states=tuple(states), missing=tuple(missing),
        notes=(
            f"LOAD: {wythe_plf:.2f} plf of masonry (its assembly's density x height, openings "
            f"not deducted) + {self_plf:.2f} plf of beam at {CONCRETE_UNIT_WEIGHT_PCF:.0f} pcf, "
            f"at {DEAD_LOAD_FACTOR}D. SECTION is the concrete layer only, {width:.2f}\".",
            f"TORSION: Tu {screen.factored_torsion_ftlb:,.0f} ft-lb at e {ecc:.3f}\" is "
            f"{screen.factored_torsion_ftlb / threshold:.2f}x φT_th ({threshold:,.0f}), so "
            f"§9.6.4 detailing is owed and graded; it is designed in equilibrium, so the "
            f"garden slab bearing §22.7.3.2 would need is not relied on.",
            *notes_ldh,
            *joint_notes,
            "NOT GRADED (moved from the deferral): the stirrup form; which way each hook turns "
            "(it must stay inside the wall it anchors in); shrinkage restraint between the two "
            "side walls; the masonry "
            "anchors over the insulated standoff, which are `veneer_anchor/<wythe>`, their own "
            "deferral.",
            f"SOFT JOINTS: the wythe ends {_end_gaps(wythe_bands, w_sup, e_sup)}; each end's "
            f"seal over compressible filler is a MovementJoint, billed by the foot and graded "
            f"by structural.masonry_movement_joint (BIA Technical Note 18A; notes §6g).",
            "LITERALS: fy = fyt 60,000 psi; Es 29,000,000 psi; Ec 57,000√f'c; ξ 2.0; "
            f"{CONCRETE_UNIT_WEIGHT_PCF:.0f} pcf concrete.",
        ),
        element_tags=tags, scope=Scope.SCREENING)


oracled_by(KIND, Oracle(note="sunken_garden_veneer_beam.md", section="§6",
                        test="tests/test_veneer_beam_calc.py"))


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, beam, carried) for beam, carried in veneer_beams(ctx)]
