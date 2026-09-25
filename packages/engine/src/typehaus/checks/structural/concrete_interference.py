"""An isolated pour in someone else's hole (→ 12 §checks/structural).

The sibling of ``structural.member_interference``, and deliberately **not** part of it.
That check excludes ``slab``/``footing``/``pad`` solids at
:mod:`~typehaus.checks.structural.interference` (:func:`member_interference`), and the
exclusion is correct for what it is about — a beam legitimately bears *into* concrete, and a
joist frames under a deck slab. The consequence was that nothing in the repo graded concrete
against concrete: a FoundationWall contributes no framed members, so a pier pad hosted in
the middle of a foundation wall's own assembly band was invisible at 0 FAIL. The breezeway's
four pads were exactly that — ``PD-BW-1/2`` 6 1/16" into the house wall, ``PD-BW-3/4``
8 3/8" into the garage ICF stem — for as long as they existed.

**Scope: an ISOLATED pour against anything.** An isolated pour is a ``Pad``, or a
``Footing`` that carries no wall (``Footing.under`` empty) — a body whose whole premise is
that it stands alone in the soil with its own bearing area under its own column. Anything it
shares volume with is a collision, because nothing was ever going to be poured with it.

Continuous foundation work — strip footing to strip footing, wall to wall, a slab over the
footing ledge it bears on — is **out of scope, and said so rather than silently cleared**.
Those bodies lap by design at every corner and every junction: two strip footings meeting at
a building corner share 0.06 m² and 8" of height because they are one pour, and a basement
slab crosses every footing in the house because it is cast onto their ledges. Grading them
here would report ~80 findings of correct construction, which is worse than reporting none.
Wall-to-wall junctions already have a grader of their own (``integrity.junction_*`` and the
assembly interface rules). Widening this check to continuous work needs a junction model for
concrete, not a bigger candidate list.

WARN severity with a FAIL result, matching the STRUCTURAL "advisory, not engineering"
convention its sibling set: this is a geometry regression guard, not a bearing calculation.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity, not_applicable
from typehaus.model.plan import PlanModel
from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.solid_categories import categories_where

#: Solid categories that are a *pour*. ``column`` is excluded: a concrete pier standing on
#: its own pad shares that pad's whole footprint by design.
CONCRETE_CATEGORIES = categories_where(is_pour=True)

# Minimum shared plan area (m²). A face abutment intersects in a zero-area line; this clears
# it with margin. Same constant, same reasoning, as interference.py's.
_TOL_AREA = 1e-4


def _non_concrete_footings(plan: PlanModel) -> set[str]:
    """Tags of footings that are not a pour at all — IRC R403.5 consolidated crushed stone.

    A stone footing still draws a ``footing`` solid, so category alone would read it as
    concrete. Nothing is formed and nothing is cast: a pad that laps one displaces stone
    instead of sharing a form, which is not the defect this check is looking for.
    """
    from typehaus.model.structure import Footing

    return {el.tag for el in plan.all_elements()
            if isinstance(el, Footing) and el.material != "concrete"}


def _declared_pours(plan: PlanModel) -> set[frozenset[str]]:
    """The pairs a house has DECLARED are one pour — ``Pad.cast_with``, both ways round.

    ** A LAP IS NOT ALWAYS A DEFECT, AND THE MODEL HAD NO WAY TO SAY WHICH. ** A pier base
    placed in the same excavation as the building's strip footing, on the same plane, at the
    same time, laps it — and that lap IS the joint. Until a house could say so, the only way
    to model such a base was as a ``Footing`` with an ``under``, which took it out of this
    check's scope by pretending it carried a wall, and took its bearing out of
    ``structural.deck_footing_size``'s prescriptive reach along with it.

    Symmetric by construction: a declaration on either body covers the pair, because "these
    two are one pour" is a fact about the joint and not about the element that happened to
    author it.
    """
    from typehaus.model.structure import Pad

    declared: set[frozenset[str]] = set()
    for element in plan.all_elements():
        if isinstance(element, Pad):
            for other in element.cast_with:
                declared.add(frozenset({element.tag, other}))
    return declared


def _cast_with_non_concrete(plan: PlanModel) -> list[tuple[str, str]]:
    """``(pad, target)`` for every ``cast_with`` naming something that is not a concrete pour.

    Nothing is cast monolithically with stone, or with a tag that is not a footing or pad.
    """
    from typehaus.model.structure import Footing, Pad

    pours = {el.tag for el in plan.all_elements()
             if isinstance(el, Pad) or (isinstance(el, Footing) and el.material == "concrete")}
    return sorted((el.tag, other) for el in plan.all_elements() if isinstance(el, Pad)
                  for other in el.cast_with if other not in pours)


def _isolated_tags(plan: PlanModel) -> set[str]:
    """Tags of the pours that stand alone: every ``Pad``, and every wall-less ``Footing``."""
    from typehaus.model.structure import Footing, Pad

    return {
        element.tag for element in plan.all_elements()
        if isinstance(element, Pad)
        or (isinstance(element, Footing) and not element.under)
    }


def _wall_bands(model: ResolvedModel) -> Iterator[tuple[str, str, object, float, float]]:
    """Every foundation wall's non-cavity layer bands as ``(wall_tag, layer, ring, z0, z1)``.

    A cavity layer shares its host's polygon and adds no wall depth, so including it would
    report one clash twice.
    """
    for wall in model.walls:
        if not wall.is_foundation:
            continue
        for layer in wall.layers:
            if layer.is_cavity or len(layer.polygon) < 3:
                continue
            z0, z1 = layer.band(wall)
            yield wall.tag, layer.name, layer.polygon, z0, z1


@check(Tier.STRUCTURAL, "structural.concrete_interference")
def concrete_interference(ctx: CheckContext) -> list[Finding]:
    """An isolated pad or footing must not share volume with any other concrete."""
    from shapely.geometry import Polygon

    model = ctx.model
    tol_z = inch(ctx.preferences.framing.interference_tolerance_in).meters
    isolated = _isolated_tags(model.plan)

    _Body = tuple[str, str, Any, float, float]
    subjects: list[_Body] = []
    others: list[_Body] = []
    non_concrete = _non_concrete_footings(model.plan)
    for solid in model.solids:
        if solid.category not in CONCRETE_CATEGORIES or solid.tag in non_concrete:
            continue
        poly = Polygon(solid.outline)
        if not poly.is_valid or poly.area <= _TOL_AREA:
            continue
        entry = (solid.tag, solid.tag, poly, solid.z0_m, solid.z1_m)
        (subjects if solid.tag in isolated else others).append(entry)

    if not subjects:
        return [not_applicable(
            "structural.concrete_interference",
            "no isolated pour in this building — every Pad and every wall-less Footing is "
            "what this grades, and the model holds none")]

    for wall_tag, layer_name, ring, z0, z1 in _wall_bands(model):
        poly = Polygon(ring)
        if poly.is_valid and poly.area > _TOL_AREA:
            others.append((wall_tag, f"{wall_tag}/{layer_name}", poly, z0, z1))

    out: list[Finding] = [
        Finding(
            severity=Severity.ERROR,
            check_id="structural.concrete_interference",
            message=(f"{pad} declares it is CAST WITH {other}, which is not a concrete pour "
                     f"— the declaration is stale or wrong and credits nothing"),
            element_tags=(pad,),
            fix_hint=f"delete {other!r} from {pad}.cast_with",
            result=Result.FAIL,
        )
        for pad, other in _cast_with_non_concrete(model.plan)
    ]
    declared = _declared_pours(model.plan)
    reported: set[frozenset[str]] = set()
    clashed: set[str] = set()
    monolithic: list[tuple[str, str, str, float, float]] = []
    for tag, label, poly, z0, z1 in sorted(subjects):
        # One finding per (pad, other element), not per layer band: a pad buried in a wall
        # hits every one of that wall's five layers, and that is one defect.
        worst: dict[str, tuple[float, float, str]] = {}
        for other_tag, other_label, other_poly, oz0, oz1 in [*subjects, *others]:
            if other_tag == tag:
                continue
            overlap = min(z1, oz1) - max(z0, oz0)
            if overlap <= tol_z:
                continue  # stacked: one bears on the other
            area = poly.intersection(other_poly).area
            if area <= _TOL_AREA:
                continue  # abutting faces
            if area > worst.get(other_tag, (0.0, 0.0, ""))[0]:
                worst[other_tag] = (area, overlap, other_label)
        for other_tag, (area, overlap, other_label) in sorted(worst.items()):
            # Two isolated pours in each other are one defect, reported once.
            key = frozenset({tag, other_tag})
            if key in reported:
                continue
            reported.add(key)
            # ** A DECLARED MONOLITHIC POUR IS A JOINT, NOT A COLLISION. ** It is still
            # reported, by name and with its numbers — a lap this check passed over in
            # silence would be indistinguishable from one it never looked at, and the
            # declaration carries a detailing obligation somebody has to see.
            if key in declared:
                monolithic.append((tag, label, other_label, area, overlap))
                continue
            clashed.add(tag)
            out.append(Finding(
                severity=Severity.WARN,
                check_id="structural.concrete_interference",
                message=(f"[advisory, not engineering] isolated pour {label} shares volume "
                         f"with {other_label}: {area:.4f} m² in plan, {overlap:.3f} m "
                         f"vertically — there is no hole to form it in"),
                element_tags=(tag, other_tag),
                fix_hint=("move the pad clear and cantilever what it carried, or make the "
                          "two one pour by hosting it on the wall/footing it lands in"),
                result=Result.FAIL,
            ))
    for tag, label, other_label, area, overlap in sorted(monolithic):
        out.append(Finding(
            severity=Severity.WARN,
            check_id="structural.concrete_interference",
            message=(f"[advisory, not engineering] {label} shares {area:.4f} m² in plan and "
                     f"{overlap:.3f} m vertically with {other_label}, and declares it is "
                     f"CAST WITH it — one pour placed in one excavation on one plane, which "
                     f"is the joint rather than a clash. **Its bearing area takes no credit "
                     f"from what it laps**: IRC R403.1.1 sizes a pier footing on its own "
                     f"tributary load over the allowable soil pressure, and claiming the "
                     f"union would make this a COMBINED footing under ACI 318-19 §13.3.4 — "
                     f"an engineered design, not a lookup. NOT graded by this or any other "
                     f"rule: that the pour really is placed monolithically (ACI 318-19 Table "
                     f"22.9.4.2 credits 1.4λ for that and 0.6λ for an unroughened cold "
                     f"joint), and that reinforcement runs continuous through the "
                     f"intersection where there is any (§14.1.4(a))"),
            element_tags=(tag, *[t for t in (other_label.split("/")[0],) if t != tag]),
            result=Result.PASS,
        ))
    # A check that says nothing has graded nothing. Every isolated pour that came through
    # clean says so by name, so the report shows the four breezeway pads standing clear
    # rather than showing an absence.
    declared_tags = {tag for tag, _label, _other, _a, _o in monolithic}
    clear = sorted(tag for tag, _l, _p, _z0, _z1 in subjects
                   if tag not in clashed and tag not in declared_tags)
    if clear:
        out.append(Finding(
            severity=Severity.WARN,
            check_id="structural.concrete_interference",
            message=(f"[advisory, not engineering] {len(clear)} isolated pour(s) stand clear "
                     f"of every other pad, footing, slab and foundation-wall band"),
            element_tags=tuple(clear),
            result=Result.PASS,
        ))
    return out
