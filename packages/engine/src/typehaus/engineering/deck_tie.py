"""The tie holding a deck to a concrete wall — ``deck_tie/<FloorSystem tag>``.

A deck tied to a wall is braced by it: ``pier_basis`` stops treating its cast columns as the
lateral system (``deck_tie_basis.wall_ties``). That is a claim that REMOVES demand from the
columns, so the tie that makes it is graded here, the ``lateral_system`` doctrine.

**The tie line is a bolt group, not a shared total.** Every load on the deck
(``deck_tie_basis.loads_on``) is resolved to a force and a moment about the joints'
centroid and distributed by the elastic method at equal joint stiffness:
``X_i = Fx/n - M dy_i / J``, ``Y_i = Fy/n + M dx_i / J``, ``J = sum(dx^2 + dy^2)``. A tie
line on one wall has all its joints on one line, so a load off that line is taken by a
COUPLE between the joints, and on a narrow line that couple is the demand that governs.
One joint and any moment is a mechanism; the record says so rather than grading it.

**Capacity per joint, off the part's published row** (``hardware/catalog``, the
``lateral_system`` excuse): F1 is the force ALONG the wall, F2 the force across it — along
the tied member. F2 counts every part at the joint, because parts on the two faces of one
member are mirror images across the plane F2 lies in and share it as they share uplift
(``HeadConnector.tie_count``). F1 counts ONE part: across the member, one face pushes and
the other pulls, and which takes the load is not something the model can say
(``library/hardware.py``, HGAM10). Where two directions act at once the row's evaluation
report governs: FL11473 §9 item 4, ``F1/F1_allow + F2/F2_allow <= 1``.

**Wind at the published value, a guard at it over the C_D inside it** (NDS Table 2.3.2:
occupancy live is 1.0). Wind and guard are not combined (ASCE 7-16 §2.4.1 pairs W with L
at 0.75, and a guard load is not a storey live load).

Oracle: ``houses/catlin/notes/north_entry_piers.md`` §10.
"""

from __future__ import annotations

from typing import Any

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
BASIS = ("the tie part's published allowables with its evaluation report's linear "
         "interaction (FL11473 §9 item 4); elastic distribution over the tie line; ASCE 7-16 "
         "§29.3 and §2.4.1; IRC R301.5")
#: 1: the kind as introduced, 2026-09-21.
BASIS_VERSION = "1"
#: FL11473 fn 8 and the Titen 2 row it governs: minimum f'c of the concrete tied into.
MIN_FC_PSI = 2_500.0

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


def _interaction(joint: TieJoint, force: tuple[float, float], f1: float, f2: float
                 ) -> tuple[float, float, float]:
    """``(F1 lb, F2 lb, ratio)`` — along the wall, across it, and FL11473's sum."""
    along, across = (abs(force[0]), abs(force[1])) if joint.wall_axis == "x" \
        else (abs(force[1]), abs(force[0]))
    f2_joint = f2 * len(joint.parts)
    return along, across, along / f1 + across / f2_joint


def _worst(joints: list[TieJoint], cases: list[list[Load]], f1: float, f2: float
           ) -> tuple[float, str] | None:
    """The worst joint ratio over every case and both senses, and how it arose."""
    best: tuple[float, str] | None = None
    for loads in cases:
        for sign in (1.0, -1.0):
            forces = distribute(joints, loads, sign)
            if not forces:
                return None
            for joint, force in zip(joints, forces, strict=True):
                along, across, ratio = _interaction(joint, force, f1, f2)
                if best is None or ratio > best[0]:
                    best = (ratio, (
                        f"{joint.member} at {joint.wall} ({len(joint.parts)} x "
                        f"{joint.model}): {along:,.1f} lb along the wall / {f1:,.1f} + "
                        f"{across:,.1f} lb across it / {f2 * len(joint.parts):,.1f}, under "
                        + " + ".join(load.label for load in loads)))
    return best


def _one(ctx: EngineeringContext, deck: Any) -> EngineeringRecord:
    from typehaus.hardware.catalog import allowable_for_model
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi

    joints = wall_ties(ctx, deck)
    tags = (deck.tag, *sorted({j.member for j in joints}), *sorted({j.wall for j in joints}))
    ident = item_id(KIND, deck.tag)
    missing: list[str] = []
    states: list[LimitState] = []
    notes: list[str] = []
    inputs: list[Quantity] = []

    models = {j.model for j in joints}
    allowable = allowable_for_model(next(iter(models))) if len(models) == 1 else None
    f1 = getattr(allowable, "lateral_f1_lb", None)
    f2 = getattr(allowable, "lateral_f2_lb", None)
    if len(models) != 1:
        missing.append(f"one tie part along the line (found {sorted(models)})")
    elif f1 is None or f2 is None:
        missing.append(f"published F1 and F2 allowables for `{next(iter(models))}`")

    anchors = [ctx.plan.by_tag(t) for t in sorted(_bearing_posts(ctx, deck))]
    wind: DeckWind | None = deck_wind(ctx, deck, anchors) if anchors else None
    if wind is None:
        missing.append(f"a guard on {deck.tag} and a site wind basis: the deck's own "
                       "storey shear starts there")
    if missing or wind is None or f1 is None or f2 is None or allowable is None:
        return _record(ident, deck.tag, tags, Status.INCOMPLETE, states, inputs, notes,
                       missing, f"{deck.tag}: the tie cannot be graded")

    wind_cases, guard_loads = loads_on(ctx, deck, wind)
    for axis, loads in wind_cases.items():
        for load in loads:
            inputs.append(Quantity(f"{axis}:{load.label}", load.fx + load.fy, "lb", 0.1))
    duration = allowable.load_duration_factor or 1.0
    cite = allowable.citation.split(". ")[0]
    for axis, name in (("y", "N-S wind"), ("x", "E-W wind")):
        worst = _worst(joints, [wind_cases[axis]], f1, f2)
        if worst is None:
            missing.append("a second tie joint: one joint cannot resist the plan torsion "
                           "of a load off its own line")
            break
        states.append(LimitState(
            f"tie interaction, {name}", worst[0], 1.0, "",
            f"{cite}, published at C_D {duration:g}; {worst[1]}",
            combination="ASCE 7-16 §2.4.1(5) 0.6W", combination_factors=(("W", 0.6),)))
    if guard_loads and not missing:
        worst = _worst(joints, [[load] for load in guard_loads], f1 / duration, f2 / duration)
        if worst is not None:
            states.append(LimitState(
                "tie interaction, guard", worst[0], 1.0, "",
                f"IRC R301.5's 200 lb at C_D 1.0 against the row over its C_D {duration:g}; "
                f"{worst[1]}"))
    for wall_tag in sorted({j.wall for j in joints}):
        fc = fc_psi(concrete_spec_for(ctx.plan, ctx.plan.by_tag(wall_tag)))
        if fc is None:
            missing.append(f"a specified f'c on {wall_tag} (the row wants >= {MIN_FC_PSI:,.0f})")
            continue
        states.append(LimitState(
            f"{wall_tag} f'c for the tie's concrete anchors", MIN_FC_PSI, fc, "psi",
            f"{cite}, footnote 8: min f'c 2,500 psi", is_detailing=True))

    notes += [
        "NOT GRADED — the published row covers the part, its screws into the wood and its "
        "anchors into the concrete. What it does not cover is the concrete member under "
        "them (out-of-plane bending of the wall top between the tie and whatever props it) "
        "and any filler block between the part's wood leg and the tied member; both are "
        "named in the oracle note with a hand bound.",
        "The wood path from each load to the tied member — sill hangers, seat beams in "
        "weak-axis bending, the member's bearing on them — is assumed to deliver it; the "
        "distribution treats the deck as rigid in plan, which is the assumption that puts "
        "the most torsion on the tie line.",
    ]
    status = (Status.INCOMPLETE if missing
              else Status.OVER if any(not s.ok for s in states) else Status.OK)
    graded = [s for s in states if not s.is_detailing]
    worst_state = max(graded, key=lambda s: s.ratio) if graded else None
    summary = (f"{deck.tag}: {len(joints)} tie joint(s) to "
               f"{', '.join(sorted({j.wall for j in joints}))}"
               + (f" — {worst_state.name} governs at {worst_state.ratio:.2f}"
                  if worst_state else ""))
    return _record(ident, deck.tag, tags, status, states, inputs, notes, missing, summary)


def _bearing_posts(ctx: EngineeringContext, deck: Any) -> set[str]:
    from typehaus.model.structure import Beam, Post

    out: set[str] = set()
    for ref in deck.joists.bearing_refs or ():
        beam = ctx.plan.by_tag(ref)
        if isinstance(beam, Beam):
            out |= {t for t in beam.bearing_refs or () if isinstance(ctx.plan.by_tag(t), Post)}
    return out


def _record(ident: str, key: str, tags: tuple[str, ...], status: Status,
            states: list[LimitState], inputs: list[Quantity], notes: list[str],
            missing: list[str], summary: str) -> EngineeringRecord:
    return EngineeringRecord(
        item_id=ident, kind=KIND, key=key, basis_version=BASIS_VERSION, basis=BASIS,
        status=status, summary=summary, inputs=tuple(inputs), limit_states=tuple(states),
        missing=tuple(missing), notes=tuple(notes), element_tags=tags)
