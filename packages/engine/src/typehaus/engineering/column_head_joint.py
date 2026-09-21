"""The joint at a lateral-system column's head — ``column_head_joint/<Post tag>``.

``deck_post`` and ``column_base`` grade the column and its base; the head, where the beam
hands the column its load, was deferred to a seal until 2026-09-20. It is computed here, six
limit states per column:

* **Head moment transfer** — a detailing row. ``deck_post`` sways every lateral column at
  ``k = 2.1`` (ACI 318-19 Table R6.2.5, fixed base / free top), so the adopted model asks the
  joint for no moment. Graded as ``2.0 / k_adopted``, which goes over the day somebody adopts
  a ``k`` that assumes the head restrains rotation.
* **Connector lateral** against ``Post.head_connector.lateral_lb`` — the lower directional
  figure, never doubled for a pair (a ``set_rated`` pair's value is already the set's). The
  published value carries C_D = 1.6, so wind grades against it as printed and a guard load
  (C_D 1.0) against it divided by 1.6.
* **Connector uplift** at 0.6D + 0.6W, where the column carries roof.
* **Column shear**, ACI 318-19 §22.5.5.1 with §22.5.2.2's circular ``b_w``/``d``.
* **Column torsion** against ``φT_th`` (§22.7.4.1). The torque is a HORIZONTAL force at a
  plan lever — never a vertical reaction, which makes bending — bounded by
  ``|r x F| <= |r||F|`` over the points it can enter: each beam face at the head and each
  authored tie. A lever that does not resolve is INCOMPLETE, never zero.
* **Bearing at the seat**, §22.8.3.2, the authored pack on the column top.

The pack's seat eccentricity is printed as the bending moment it is.

**Oracle.** ``houses/catlin/notes/north_entry_piers.md`` §9, hand-worked first;
``tests/test_column_head_joint.py`` reproduces it.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.engineering.column_head_geometry import (
    BeamFrame,
    beam_frame,
    confinement_ratio,
    lever_in,
    relative_in,
    seat_centroid,
)
from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by

KIND = "column_head_joint"
BASIS = ("ACI 318-19 §22.5, §22.7.4, §22.8.3, Table R6.2.5; the head connector's published "
         "allowables (Post.head_connector)")
#: 1: the kind as introduced, 2026-09-20.
BASIS_VERSION = "1"

oracled_by(KIND, Oracle(note="north_entry_piers.md", section="§9",
                        test="tests/test_column_head_joint.py"))

#: IRC R301.5 / Table R301.5 note f — the guard's concentrated load, the same 200 lb
#: ``pier_basis._base_moments`` puts on the base.
GUARD_LOAD_LB = 200.0
#: ACI 318-19 Table 21.2.1: shear and torsion; bearing.
PHI_SHEAR_TORSION = 0.75
PHI_BEARING = 0.65
#: §22.8.3.2's cap on sqrt(A2/A1).
BEARING_CONFINEMENT_CAP = 2.0
#: The ideal fixed-base / free-top effective length factor (Table R6.2.5).
FREE_HEAD_K = 2.0

#: The deliverable of the retired deferral, kept (plan rule 12): what is still a seal's.
_NOT_GRADED = (
    "NOT GRADED — what the retired deferral asked for and this record does not compute: a "
    "sealed connection detail at each cast column head, meaning the FASTENER schedule "
    "through the standoff pack and the gusset's anchor edge distance on the round (only the "
    "published part allowables are graded here), and whether the shim stack and gussets "
    "deliver the free head this analysis assumes rather than a partial fixity it does not. "
    "Wood crushing on the pack (NDS F_c-perp) belongs to the beam, not to this joint.")


@keys(KIND)
def enumerate_heads(ctx: EngineeringContext) -> list[str]:
    """Every cast column that IS a lateral system — the head of each one ``deck_post``
    grades in bending, whether it stands on a pad, a footing or a wall."""
    from typehaus.engineering.pier_basis import cast_piers

    return sorted(pier.tag for pier in cast_piers(ctx) if pier.lateral_system)


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    from typehaus.engineering.lateral_system import column_head_reactions
    from typehaus.engineering.pier_basis import cast_piers

    piers = [pier for pier in cast_piers(ctx) if pier.lateral_system]
    heads = column_head_reactions(ctx)
    return [_one(ctx, pier, heads.get(pier.tag)) for pier in piers]


def _one(ctx: EngineeringContext, pier: Any, frame_forces: dict[str, float] | None
         ) -> EngineeringRecord:
    from typehaus.engineering.deck_post import (
        CANTILEVER_EFFECTIVE_LENGTH_FACTOR,
        GUARD_LOAD_FACTOR,
        STRENGTH_FROM_ASD_WIND,
    )

    post = ctx.plan.by_tag(pier.tag)
    connector = getattr(post, "head_connector", None)
    states: list[LimitState] = []
    missing: list[str] = []
    notes: list[str] = []
    inputs: list[Quantity] = []
    height_ft = pier.height_in / 12.0

    states.append(LimitState(
        "head moment transfer (none asked of the joint)", FREE_HEAD_K,
        CANTILEVER_EFFECTIVE_LENGTH_FACTOR, "",
        f"ACI 318-19 Table R6.2.5: deck_post sways this column at k = "
        f"{CANTILEVER_EFFECTIVE_LENGTH_FACTOR:g}, fixed base and FREE top, so the adopted "
        f"model restrains no rotation at the head; over 1.0 would mean a k assuming it does",
        is_detailing=True))

    # ── what the beam hands the head, ASD ──
    guard = GUARD_LOAD_LB if pier.guard_base_moment_lb_ft > 0.0 else 0.0
    if frame_forces:
        wind_by_axis = dict(frame_forces)
        wind_how = ("the column's share of the diaphragm shear "
                    "(lateral_system.column_head_reactions), not netted against its own drag")
    else:
        wind_by_axis = {"any": pier.wind_base_moment_lb_ft / height_ft} if height_ft else {}
        wind_how = ("the storey shear at the head, M_wind / H — exact for a deck column, an "
                    "upper bound on a free-headed roof column")
    wind = max(wind_by_axis.values(), default=0.0)
    inputs += [Quantity("head_lateral_wind", wind, "lb", 1.0),
               Quantity("head_lateral_guard", guard, "lb", 1.0)]

    if connector is None:
        missing.append(f"Post.head_connector on {pier.tag}: the published allowables of the "
                       "part tying the head to its beam")
    else:
        _connector_states(ctx, pier, connector, wind, wind_how, guard, states, missing,
                          notes, inputs)

    fc = pier.specified_fc_psi or _presumptive_fc()
    _shear_state(pier, fc, wind, guard, states, missing, inputs,
                 STRENGTH_FROM_ASD_WIND, GUARD_LOAD_FACTOR)
    frames = _frames(ctx, pier)
    if not frames:
        missing.append(f"a Beam bearing on {pier.tag} (Beam.bearing_refs), to place the "
                       "head's load")
    else:
        _torsion_state(ctx, pier, frames, fc, wind_by_axis, guard, states, inputs,
                       STRENGTH_FROM_ASD_WIND, GUARD_LOAD_FACTOR)
        if connector is not None:
            _seat_states(ctx, pier, frames, connector, fc, states, missing, notes, inputs)
    inputs.append(Quantity("fc", fc, "psi", 1.0))
    notes += [_NOT_GRADED,
              "The guard's lever above the deck: deck_post charges the base with 200 lb x "
              "(H + guard height). A free head cannot pass that couple; it returns through "
              "the deck's bearings as an axial pair, which is not graded here.",
              "SCREENING, not a stamped design."]

    ident = item_id(KIND, pier.tag)
    if missing:
        return EngineeringRecord(
            item_id=ident, kind=KIND, key=pier.tag, basis_version=BASIS_VERSION,
            basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{pier.tag}: the head joint could not be graded to the end",
            inputs=tuple(inputs), limit_states=tuple(states), missing=tuple(missing),
            notes=tuple(notes), element_tags=(pier.tag,))
    record = EngineeringRecord(
        item_id=ident, kind=KIND, key=pier.tag, basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if any(not s.ok for s in states) else Status.OK,
        inputs=tuple(inputs), limit_states=tuple(states), notes=tuple(notes),
        element_tags=(pier.tag,))
    governing = record.governing
    summary = (f"{pier.tag}: head joint — {governing.name} governs at {governing.ratio:.2f}"
               if governing is not None else f"{pier.tag}: head joint")
    from dataclasses import replace

    return replace(record, summary=summary)


def _presumptive_fc() -> float:
    from typehaus.engineering.retaining_basis import PRESUMPTIVE_FC_PSI

    return PRESUMPTIVE_FC_PSI


def _connector_states(ctx: EngineeringContext, pier: Any, connector: Any, wind: float,
                      wind_how: str, guard: float, states: list[LimitState],
                      missing: list[str], notes: list[str], inputs: list[Quantity]) -> None:
    cd = connector.load_duration_factor
    lateral = connector.lateral_lb
    if lateral is None:
        missing.append(
            f"a published lateral capacity for {pier.tag}'s head: {connector.tie} publishes "
            f"none ({connector.source}) — an ACI 318 Ch. 17 anchor-shear design or a "
            f"different tie")
    else:
        if wind > 0.0:
            states.append(LimitState(
                "connector lateral, wind", wind, lateral, "lb",
                f"{connector.tie} {lateral:,.0f} lb as published (C_D {cd:g} already in it; "
                f"{_credit(connector)}); {wind_how}; 0.6W"))
        if guard > 0.0:
            states.append(LimitState(
                "connector lateral, guard", guard, lateral / cd, "lb",
                f"{connector.tie} {lateral:,.0f} lb / C_D {cd:g} = {lateral / cd:,.1f} lb for "
                f"an occupancy live load (NDS Table 2.3.2, C_D 1.0); IRC R301.5's 200 lb"))

    uplift = _net_uplift(ctx, pier, notes)
    if uplift is None:
        return
    inputs.append(Quantity("net_uplift", uplift, "lb", 1.0))
    if connector.uplift_lb is None:
        missing.append(f"a published uplift capacity for {connector.tie}")
        return
    states.append(LimitState(
        "connector uplift", uplift, connector.uplift_lb, "lb",
        f"{connector.tie} {connector.uplift_lb:,.0f} lb, "
        f"{'the rated set' if connector.set_rated else 'ONE part'} credited; ASCE 7-16 "
        f"§2.4.1(7) 0.6D + 0.6W on {pier.roof_tributary_ft2:.1f} ft2 of roof"))
    if lateral is not None and wind > 0.0:
        share = 1 if connector.set_rated else connector.tie_count
        unity = (max(uplift, 0.0) / share) / connector.uplift_lb + wind / lateral
        inputs.append(Quantity("combined_unity_unverified", unity, "", 0.001))
        notes.append(
            f"COMBINED LOADING IS NOT GRADED: the document's recorded footnotes state no "
            f"interaction rule. A linear one would read (uplift / {share}) / "
            f"{connector.uplift_lb:,.0f} + lateral / {lateral:,.0f} = {unity:.3f}, on two "
            f"stacked surrogate bounds — a reviewer should settle whether the rule applies.")


def _credit(connector: Any) -> str:
    if connector.set_rated:
        return f"the published value of the {connector.tie_count}-part set"
    return f"not raised for {connector.tie_count} parts"


def _net_uplift(ctx: EngineeringContext, pier: Any, notes: list[str]) -> float | None:
    """0.6D + 0.6W on the roof this column carries, ASD lb up; ``None`` with no roof."""
    from typehaus.engineering.pier_basis import DECK_DEAD_LOAD_PSF
    from typehaus.wind import ASD_WIND_FACTOR
    from typehaus.wind_tables import GUST_EFFECT_RIGID, MAX_VERIFIED_CASE_AB

    if pier.roof_tributary_ft2 <= 0.0:
        notes.append(
            "NO UPLIFT ROW: this column carries no roof (roof tributary 0 ft2, computed), and "
            "ASCE 7-16 assigns an open-jointed walking surface no uplift coefficient.")
        return None
    q_h = _roof_q_h(ctx, pier.tag)
    if q_h is None:
        return None
    up = ASD_WIND_FACTOR * q_h * GUST_EFFECT_RIGID * MAX_VERIFIED_CASE_AB
    notes.append(
        f"UPLIFT is the roof_moment surrogate spent on plan area: 0.6 x {q_h:.3f} x "
        f"{GUST_EFFECT_RIGID} x {MAX_VERIFIED_CASE_AB} = {up:.3f} psf, a bound on any "
        f"published free-roof C_N, less 0.6 x {DECK_DEAD_LOAD_PSF:g} psf of roof dead.")
    return (up - 0.6 * DECK_DEAD_LOAD_PSF) * pier.roof_tributary_ft2


def _roof_q_h(ctx: EngineeringContext, tag: str) -> float | None:
    """q_h at the ridge of the roof(s) this column carries, the ``roof_moment`` datum."""
    from typehaus.engineering.balcony_wind import ground_below_ft
    from typehaus.model.spatial import Roof
    from typehaus.model.structure import Beam, Post
    from typehaus.wind import velocity_pressure_psf, wind_basis

    basis = wind_basis(ctx.plan.project.site)
    if basis is None:
        return None
    standing = {e.tag for e in ctx.plan.all_elements()
                if isinstance(e, Post) and e.supported_by == tag}
    ground = ground_below_ft(ctx.plan)
    best = None
    for roof in ctx.model.roofs:
        element = ctx.plan.by_tag(roof.tag)
        if not isinstance(element, Roof):
            continue
        beams = [b for b in (ctx.plan.by_tag(r) for r in element.bearing_refs)
                 if isinstance(b, Beam)]
        if any({tag, *standing} & set(b.bearing_refs or ()) for b in beams):
            q_h = velocity_pressure_psf(basis, roof.ridge_z_m / 0.3048 - ground)
            best = q_h if best is None else max(best, q_h)
    return best


def _shear_state(pier: Any, fc: float, wind: float, guard: float, states: list[LimitState],
                 missing: list[str], inputs: list[Quantity], wind_factor: float,
                 guard_factor: float) -> None:
    from typehaus.engineering.deck_post import cage_for
    from typehaus.engineering.retaining_basis import _BAR, REINFORCEMENT_FY_PSI
    from typehaus.engineering.roof_moment import base_shear_of

    recorded = base_shear_of(pier.tag)
    base_wind = wind
    if recorded is not None and guard == 0.0:
        base_wind = max(base_wind, recorded[0])
    v_u = max(base_wind * wind_factor, guard * guard_factor)
    b_w, d = _shear_section(pier)
    root = math.sqrt(fc)
    v_c = 2.0 * root * b_w * d
    inputs.append(Quantity("shear_u", v_u, "lb", 1.0))
    states.append(LimitState(
        "column shear", v_u, PHI_SHEAR_TORSION * v_c, "lb",
        f"ACI 318-19 Table 22.5.5.1(a) with N_u = 0, b_w {b_w:g}\" and d {d:g}\" "
        f"(§22.5.2.2); V_u the larger of base wind / 0.6 and 1.6 x the guard"))
    cage = cage_for(pier)
    if cage is None:
        missing.append(f"a tied cage on {pier.tag} (Post.reinforcement) for A_v,min")
        return
    a_v = 2.0 * _BAR[cage.tie_bar][0]
    a_v_min = max(0.75 * root, 50.0) * b_w * cage.tie_spacing_in / REINFORCEMENT_FY_PSI
    states.append(LimitState(
        "A_v,min for Table 22.5.5.1(a)", a_v_min, a_v, "in2",
        f"§9.6.3.4 at s {cage.tie_spacing_in:g}\"; a circular tie counts twice "
        f"(§22.5.10.5.3), #{cage.tie_bar}", is_detailing=True))


def _shear_section(pier: Any) -> tuple[float, float]:
    if pier.round_section:
        return pier.diameter_in, 0.8 * pier.diameter_in
    cover = pier.specified_cover_in if pier.specified_cover_in is not None else 1.5
    return pier.diameter_in, pier.diameter_in - cover - 0.375 - 0.3125


def _frames(ctx: EngineeringContext, pier: Any) -> list[BeamFrame]:
    from typehaus.model.structure import Beam

    axis = ctx.plan.by_tag(pier.tag).position.xy_m
    out = []
    for element in ctx.plan.all_elements():
        if isinstance(element, Beam) and pier.tag in (element.bearing_refs or ()):
            frame = beam_frame(ctx.plan, element, axis)
            if frame is not None:
                out.append(frame)
    return out


def _parts(ctx: EngineeringContext, tag: str, *, standoff: bool) -> list[Any]:
    from typehaus.model.enums import ConnectorKind
    from typehaus.model.structure import Connector

    return [c for c in ctx.plan.all_elements()
            if isinstance(c, Connector) and tag in c.connects
            and (c.kind == ConnectorKind.BEARING_STANDOFF) == standoff]


def _torsion_state(ctx: EngineeringContext, pier: Any, frames: list[BeamFrame], fc: float,
                   wind_by_axis: dict[str, float], guard: float, states: list[LimitState],
                   inputs: list[Quantity], wind_factor: float, guard_factor: float) -> None:
    axis = ctx.plan.by_tag(pier.tag).position.xy_m
    points = [p for frame in frames for p in frame.faces_at_axis()]
    points += [relative_in(c.position.xy_m, axis) for c in _parts(ctx, pier.tag, standoff=False)]
    directions = {"x": (1.0, 0.0), "y": (0.0, 1.0)}
    candidates = [(force * wind_factor, lever_in(points, directions.get(key)), key)
                  for key, force in wind_by_axis.items()]
    if guard > 0.0:
        candidates.append((guard * guard_factor, lever_in(points, None), "guard"))
    t_u, force, lever, case = max(((f * arm / 12.0, f, arm, k) for f, arm, k in candidates),
                                  default=(0.0, 0.0, 0.0, ""))
    area = pier.gross_area_in2
    perimeter = (math.pi * pier.diameter_in if pier.round_section else 4.0 * pier.diameter_in)
    t_th = math.sqrt(fc) * area ** 2 / perimeter / 12.0
    inputs += [Quantity("torsion_u", t_u, "lb-ft", 0.1),
               Quantity("torsion_lever", lever, "in", 0.01)]
    states.append(LimitState(
        "column torsion vs threshold", t_u, PHI_SHEAR_TORSION * t_th, "lb-ft",
        f"ACI 318-19 §22.7.4.1(a), T_th = sqrt(f'c) A_cp^2 / p_cp = {t_th:,.1f} lb-ft, N_u "
        f"= 0; T_u = {force:,.1f} lb ({case}) x {lever:.3f}\" — the bound |r x F| over each "
        f"beam face and tie at the head. Under it, §22.7.1.1 permits torsion to be "
        f"neglected and §9.6.4's closed hoops are not owed"))


def _seat_states(ctx: EngineeringContext, pier: Any, frames: list[BeamFrame], connector: Any,
                 fc: float, states: list[LimitState], missing: list[str], notes: list[str],
                 inputs: list[Quantity]) -> None:
    from typehaus.engineering.pier_basis import DEAD_LOAD_FACTOR, LIVE_LOAD_FACTOR

    width, length = connector.bearing_width_in, connector.bearing_length_in
    packs = _parts(ctx, pier.tag, standoff=True)
    if width is None or not packs:
        missing.append(f"the seat on {pier.tag}: a BEARING_STANDOFF Connector joining a beam "
                       "to it, and HeadConnector.bearing_width_in / _length_in")
        return
    axis = ctx.plan.by_tag(pier.tag).position.xy_m
    pack = packs[0]
    centre = relative_in(pack.position.xy_m, axis)
    frame = next((f for f in frames if f.tag in pack.connects), frames[0])
    seat = seat_centroid(frame, centre, length, width)
    if seat is None:
        missing.append(f"a seat: {pack.tag} does not lie under {frame.tag}'s footprint")
        return
    k = confinement_ratio(frame, centre, length, width, pier.diameter_in / 2.0)
    if k < 1.0:
        missing.append(f"a seat on the concrete: {pack.tag} overhangs {pier.tag}'s top")
        return
    p_u = (DEAD_LOAD_FACTOR * (pier.dead_lb - pier.self_weight_lb)
           + LIVE_LOAD_FACTOR * pier.live_lb)
    a_1 = width * length
    capacity = PHI_BEARING * 0.85 * fc * a_1 * min(k, BEARING_CONFINEMENT_CAP)
    ecc = math.hypot(*seat)
    inputs += [Quantity("seat_pu", p_u, "lb", 1.0),
               Quantity("seat_eccentricity", ecc, "in", 0.01),
               Quantity("seat_bending", p_u * ecc / 12.0, "lb-ft", 0.1)]
    states.append(LimitState(
        "bearing at the seat", p_u, capacity, "lb",
        f"ACI 318-19 §22.8.3.2, {connector.bearing} {width:g}\" x {length:g}\" = "
        f"{a_1:g} in2, sqrt(A2/A1) = {k:.3f} capped at {BEARING_CONFINEMENT_CAP:g} (A2 the "
        f"largest similar concentric area inside the column top); P_u = 1.2(D - shaft) + "
        f"1.6(L or S)"))
    notes.append(
        f"SEAT ECCENTRICITY {ecc:.3f}\": the pack's centroid under {frame.tag} stands that "
        f"far off the axis, so the head takes P_u x e = {p_u * ecc / 12.0:,.1f} lb-ft of "
        f"BENDING (not torsion) that deck_post's base-moment demand does not include.")
