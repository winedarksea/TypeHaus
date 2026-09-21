"""The ties holding a deck to another structure — ``deck_tie/<FloorSystem tag>``.

A deck tied to a wall is braced by it: ``pier_basis`` stops treating its cast columns as the
lateral system (``deck_tie_basis.wall_ties``). That is a claim that REMOVES demand from the
columns, so the tie that makes it is graded here, the ``lateral_system`` doctrine.

**The tie joints are a bolt group, not a shared total.** Every load on the deck
(``deck_tie_basis.loads_on``) is resolved to a force and a moment about the joints'
centroid and distributed by the elastic method at equal joint stiffness:
``X_i = Fx/n - M dy_i / J``, ``Y_i = Fy/n + M dx_i / J``, ``J = sum(dx^2 + dy^2)``. One joint
and any moment is a mechanism; the record says so rather than grading it.

**Capacity per joint, off the part's published row** (``hardware/catalog``), by role:

* a masonry gusset (HGAM): F1 along the wall, one part; F2 across it, every part.
* a heavy angle (HL): read by its HEEL (``Connector.axis``). Along the heel is F1, one part
  (C-C-2024 fn 6: lateral may not be doubled). Perpendicular to the heel is the published
  UPLIFT case — for a horizontal heel, mirrored into the other leg (equal legs, equal
  bolting); for a vertical heel, the force in the tied member's leg plane, which fn 6 lets a
  pair double, and the force across it, one part. Published dry at C_D 1.6: x NDS C_M 0.70,
  or 1.0 where the parts author dry service (``Connector.service``) — a judgement the
  record names for the engineer of record.

Where two directions act at once the linear interaction governs: FL11473 §9 item 4 for the
gusset, Simpson's General Notes for the angle — ``F_along/allow + F_across/allow <= 1``.
A joint on concrete also grades its anchors (``deck_tie_anchor``, ACI 318-19 Ch. 17).

**Wind at the published value, a guard at it over the C_D inside it** (NDS Table 2.3.2:
occupancy live is 1.0). Wind and guard are not combined (ASCE 7-16 §2.4.1).

Oracle: ``houses/catlin/notes/north_entry_piers.md`` §10.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typehaus.engineering import deck_tie_anchor as anchor
from typehaus.engineering.deck_tie_basis import (
    DeckWind,
    Load,
    TieJoint,
    deck_wind,
    loads_on,
    wall_ties,
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

KIND = "deck_tie"
BASIS = ("the tie part's published allowables with the linear interaction its document "
         "states (FL11473 §9 item 4; Simpson C-C-2024 General Notes); NDS 2018 §11.3.3 / "
         "Table 11.3.3 C_M per joint; ACI 318-19 Ch. 17 on concrete anchors; elastic "
         "distribution over the tie joints; ASCE 7-16 §29.3 and §2.4.1; IRC R301.5")
#: 1: the kind as introduced, 2026-09-21. 2: capacity per joint by role and heel, C_M on a
#: dry-published bolted part, ACI 318 Ch. 17 on concrete anchors, ties to framed walls.
#: 3: C_M per joint off the parts' authored service condition; the anchor layout (near and
#: far edge, one anchor per concrete leg) read off the angle's own hole pattern.
BASIS_VERSION = "3"
#: ESR-2713 §1.0 / FL11473 fn 8: the least f'c the concrete anchors are published for.
MIN_FC_PSI = 2_500.0
#: NDS 2018 Table 11.3.3, dowel-type fasteners, in-service moisture > 19 %: an exterior tie.
WET_SERVICE_CM = 0.70
#: The same table at <= 19 %: only where the joint's parts AUTHOR dry service, with a basis.
DRY_SERVICE_CM = 1.0
#: ASCE 7-16 §2.3 / §2.4: strength wind is ASD wind / 0.6; a guard (live) takes 1.6.
STRENGTH_FROM_ASD_WIND = 1.0 / 0.6
STRENGTH_FROM_GUARD = 1.6

oracled_by(KIND, Oracle(note="north_entry_piers.md", section="§10",
                        test="tests/test_deck_tie.py"))


def _tied_decks(ctx: EngineeringContext) -> list[Any]:
    """Decks the tie is what braces: tied, on no wall, and over cast columns it relieves.

    A deck whose beams already land in a wall was never a column question (the porch), and
    one on no cast column had no base moment to take away (catlin's interior landing, which
    rides the same two carriers): neither makes the claim this item grades.
    """
    from typehaus.model.elements import Wall
    from typehaus.model.floors import FloorSystem
    from typehaus.model.structure import Beam, Post
    from typehaus.resolve.assembly_material import assembly_structure_material

    def relieves(deck: Any) -> bool:
        beams = [b for b in (ctx.plan.by_tag(t) for t in deck.joists.bearing_refs or ())
                 if isinstance(b, Beam)]
        under = [ctx.plan.by_tag(t) for b in beams for t in b.bearing_refs or ()]
        return (not any(isinstance(e, Wall) for e in under)
                and any(isinstance(e, Post) and assembly_structure_material(
                    ctx.plan, e.assembly) == "concrete" for e in under))

    return sorted((e for e in ctx.plan.all_elements()
                   if isinstance(e, FloorSystem) and e.service == "deck"
                   and wall_ties(ctx, e) and relieves(e)), key=lambda d: d.tag)


@keys(KIND)
def enumerate_deck_ties(ctx: EngineeringContext) -> list[str]:
    return [deck.tag for deck in _tied_decks(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, deck) for deck in _tied_decks(ctx)]


def distribute(joints: list[TieJoint], loads: list[Load], sign: float = 1.0
               ) -> list[tuple[float, float]]:
    """``(X_i, Y_i)`` per joint under ``sign`` times ``loads``; ``[]`` for a mechanism."""
    n = len(joints)
    xb = sum(j.x_ft for j in joints) / n
    yb = sum(j.y_ft for j in joints) / n
    fx = sign * sum(load.fx for load in loads)
    fy = sign * sum(load.fy for load in loads)
    moment = sign * sum((load.x_ft - xb) * load.fy - (load.y_ft - yb) * load.fx
                        for load in loads)
    polar = sum((j.x_ft - xb) ** 2 + (j.y_ft - yb) ** 2 for j in joints)
    if polar <= 1e-9:
        return [] if abs(moment) > 1e-6 else [(fx / n, fy / n)] * n
    return [(fx / n - moment * (j.y_ft - yb) / polar, fy / n + moment * (j.x_ft - xb) / polar)
            for j in joints]


@dataclass(frozen=True)
class Capacity:
    """One joint's allowables along and across its wall, at the part's own C_D."""

    along_lb: float
    across_lb: float
    duration: float
    how: str
    cite: str
    angle: bool


def capacity(joint: TieJoint) -> Capacity | str:
    """The joint's capacity, or the reason there is none."""
    from typehaus.hardware.catalog import (
        ROLE_HEAVY_ANGLE,
        ROLE_MASONRY_GUSSET_ANGLE,
        allowable_for_model,
        hardware_by_model,
    )

    item, allow = hardware_by_model(joint.model), allowable_for_model(joint.model)
    if item is None or allow is None:
        return f"published allowables for `{joint.model}` at {joint.member}/{joint.wall}"
    n, cd = len(joint.parts), allow.load_duration_factor or 1.0
    cite = allow.citation.split(", read")[0]
    if item.role == ROLE_MASONRY_GUSSET_ANGLE and allow.lateral_f1_lb and allow.lateral_f2_lb:
        return Capacity(allow.lateral_f1_lb, allow.lateral_f2_lb * n, cd,
                        f"F1 one part / F2 x {n}", cite, False)
    if item.role != ROLE_HEAVY_ANGLE or not allow.lateral_f1_lb or not allow.uplift_lb:
        return f"a reading of `{joint.model}` ({item.role}) as a tie joint"
    if joint.heel_axis == "mixed":
        return f"one heel direction for the parts at {joint.member}/{joint.wall}"
    if joint.service_condition == "mixed":
        return f"one service condition for the parts at {joint.member}/{joint.wall}"
    c_m = service_cm(joint)
    f1, up = allow.lateral_f1_lb * c_m, allow.uplift_lb * c_m
    wet = "dry, authored" if joint.service_condition == "dry" else "wet"
    if joint.heel_axis is None:
        return Capacity(up * n, up, cd, f"heel vertical: uplift x {n} in the member's leg "
                        f"plane (fn 6), uplift x 1 across, C_M {c_m:g} ({wet})", cite, True)
    along_heel = joint.heel_axis == joint.wall_axis
    return Capacity(f1 if along_heel else up, up if along_heel else f1, cd,
                    f"heel {joint.heel_axis}: F1 along it, uplift (mirrored) across, one "
                    f"part each (fn 6), C_M {c_m:g} ({wet})", cite, True)


def service_cm(joint: TieJoint) -> float:
    """NDS 2018 Table 11.3.3: 1.0 where the parts author dry service, else 0.70."""
    return DRY_SERVICE_CM if joint.service_condition == "dry" else WET_SERVICE_CM


def _split(joint: TieJoint, force: tuple[float, float]) -> tuple[float, float]:
    """``(along the wall, across it)``, signed."""
    return force if joint.wall_axis == "x" else (force[1], force[0])


def _worst(joints: list[TieJoint], caps: list[Capacity], cases: list[list[Load]],
           divisor: float, factor: float, demands: dict[str, list[anchor.Demand]]
           ) -> tuple[float, str] | None:
    """The worst joint ratio over every case and both senses; strength demands collected."""
    best: tuple[float, str] | None = None
    for loads in cases:
        for sign in (1.0, -1.0):
            forces = distribute(joints, loads, sign)
            if not forces:
                return None
            label = " + ".join(load.label for load in loads)
            for joint, cap, force in zip(joints, caps, forces, strict=True):
                along, across = (abs(v) for v in _split(joint, force))
                ratio = along * divisor / cap.along_lb + across * divisor / cap.across_lb
                if joint.on_concrete and cap.angle:
                    heel_is_along = joint.heel_axis == joint.wall_axis
                    demands.setdefault(joint.member, []).append(anchor.Demand(
                        label, factor * (along if heel_is_along else across),
                        factor * (across if heel_is_along else along), heel_is_along))
                if best is None or ratio > best[0]:
                    best = (ratio, (
                        f"{joint.member} at {joint.wall} ({len(joint.parts)} x "
                        f"{joint.model}, {cap.how}): {along:,.1f} lb along the wall / "
                        f"{cap.along_lb / divisor:,.1f} + {across:,.1f} lb across it / "
                        f"{cap.across_lb / divisor:,.1f}, under {label}"))
    return best


def _one(ctx: EngineeringContext, deck: Any) -> EngineeringRecord:
    joints = wall_ties(ctx, deck)
    tags = (deck.tag, *sorted({j.member for j in joints}), *sorted({j.wall for j in joints}))
    ident = item_id(KIND, deck.tag)
    missing: list[str] = []
    states: list[LimitState] = []
    inputs: list[Quantity] = []
    caps = [capacity(j) for j in joints]
    missing += [c for c in caps if isinstance(c, str)]

    anchors = [ctx.plan.by_tag(t) for t in sorted(_bearing_posts(ctx, deck))]
    wind: DeckWind | None = deck_wind(ctx, deck, anchors) if anchors else None
    if wind is None:
        missing.append(f"a guard on {deck.tag} and a site wind basis: the deck's own "
                       "storey shear starts there")
    if missing or wind is None:
        return _record(ident, deck.tag, tags, Status.INCOMPLETE, states, inputs, missing,
                       f"{deck.tag}: the tie cannot be graded")
    good = [c for c in caps if isinstance(c, Capacity)]

    wind_cases, guard_loads = loads_on(ctx, deck, wind)
    for axis, loads in wind_cases.items():
        for load in loads:
            inputs.append(Quantity(f"{axis}:{load.label}", load.fx + load.fy, "lb", 0.1))
    demands: dict[str, list[anchor.Demand]] = {}
    for axis, name in (("y", "N-S wind"), ("x", "E-W wind")):
        worst = _worst(joints, good, [wind_cases[axis]], 1.0, STRENGTH_FROM_ASD_WIND, demands)
        if worst is None:
            missing.append("a second tie joint: one joint cannot resist the plan torsion "
                           "of a load off its own line")
            break
        states.append(LimitState(
            f"tie interaction, {name}", worst[0], 1.0, "",
            f"{'; '.join(sorted({c.cite for c in good}))}, published at C_D "
            f"{good[0].duration:g}; {worst[1]}",
            combination="ASCE 7-16 §2.4.1(5) 0.6W", combination_factors=(("W", 0.6),)))
    if guard_loads and not missing:
        worst = _worst(joints, good, [[load] for load in guard_loads], good[0].duration,
                       STRENGTH_FROM_GUARD, demands)
        if worst is not None:
            states.append(LimitState(
                "tie interaction, guard", worst[0], 1.0, "",
                f"IRC R301.5's 200 lb at C_D 1.0 against the row over its C_D "
                f"{good[0].duration:g}; {worst[1]}"))
    states += _concrete_states(ctx, joints, good, demands, missing)

    notes = [
        "NOT GRADED — the concrete member under the anchors (out-of-plane bending of the "
        "wall top) and the tie block's own screws into the tied member are named in the "
        "oracle note with a hand bound; the framed wall a tie lands on is graded as that "
        "structure's bracing, not here.",
        "The wood path from each load to the tied member is assumed to deliver it; the "
        "distribution treats the deck as rigid in plan and every joint as equally stiff.",
    ]
    notes += [f"DRY SERVICE at {j.member}/{j.wall} (C_M {DRY_SERVICE_CM:g}, NDS 2018 "
              f"§11.3.3 / Table 11.3.3): a service-condition judgement the engineer of "
              f"record confirms. Basis: {j.service_basis}"
              for j in joints if j.service_condition == "dry"]
    notes += anchor.layout_notes(joints)
    status = (Status.INCOMPLETE if missing
              else Status.OVER if any(not s.ok for s in states) else Status.OK)
    graded = [s for s in states if not s.is_detailing]
    worst_state = max(graded, key=lambda s: s.ratio) if graded else None
    summary = (f"{deck.tag}: {len(joints)} tie joint(s) to "
               f"{', '.join(sorted({j.wall for j in joints}))}"
               + (f" — {worst_state.name} governs at {worst_state.ratio:.2f}"
                  if worst_state else ""))
    return _record(ident, deck.tag, tags, status, states, inputs, missing, summary, notes)


def _concrete_states(ctx: EngineeringContext, joints: list[TieJoint], caps: list[Capacity],
                     demands: dict[str, list[anchor.Demand]], missing: list[str]
                     ) -> list[LimitState]:
    """f'c detailing on every concrete wall, and ACI 318 Ch. 17 on angle anchors."""
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi

    out: list[LimitState] = []
    fcs: dict[str, float] = {}
    for wall_tag in sorted({j.wall for j in joints if j.on_concrete}):
        fc = fc_psi(concrete_spec_for(ctx.plan, ctx.plan.by_tag(wall_tag)))
        if fc is None:
            missing.append(f"a specified f'c on {wall_tag} (the anchors want >= "
                           f"{MIN_FC_PSI:,.0f})")
            continue
        fcs[wall_tag] = fc
        out.append(LimitState(f"{wall_tag} f'c for the tie's concrete anchors", MIN_FC_PSI,
                              fc, "psi", "ESR-2713 §1.0 / FL11473 fn 8: min f'c 2,500 psi",
                              is_detailing=True))
    groups = []
    for joint, cap in zip(joints, caps, strict=True):
        if not (joint.on_concrete and cap.angle and joint.wall in fcs):
            continue
        group = anchor.group_for(ctx, joint, fcs[joint.wall])
        if group is None:
            missing.append(f"the anchor layout of {joint.model} on {joint.wall} (its hole "
                           "pattern, or the wall's core)")
        else:
            groups.append(group)
    worst: dict[str, tuple[float, str]] = {}
    for group in groups:
        for demand in demands.get(group.joint, []):
            t, v, both, how = anchor.grade(group, demand)
            for key, ratio in (("tension", t), ("shear", v), ("both", both)):
                if key not in worst or ratio > worst[key][0]:
                    worst[key] = (ratio, how)
    return out + anchor.states(worst, groups) if worst else out


def _bearing_posts(ctx: EngineeringContext, deck: Any) -> set[str]:
    from typehaus.model.structure import Beam, Post

    out: set[str] = set()
    for ref in deck.joists.bearing_refs or ():
        beam = ctx.plan.by_tag(ref)
        if isinstance(beam, Beam):
            out |= {t for t in beam.bearing_refs or () if isinstance(ctx.plan.by_tag(t), Post)}
    return out


def _record(ident: str, key: str, tags: tuple[str, ...], status: Status,
            states: list[LimitState], inputs: list[Quantity], missing: list[str],
            summary: str, notes: list[str] | None = None) -> EngineeringRecord:
    return EngineeringRecord(
        item_id=ident, kind=KIND, key=key, basis_version=BASIS_VERSION, basis=BASIS,
        status=status, summary=summary, inputs=tuple(inputs), limit_states=tuple(states),
        missing=tuple(missing), notes=tuple(notes or ()), element_tags=tags)
