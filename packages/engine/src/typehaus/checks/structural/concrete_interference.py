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

#: Solid categories that are a *pour*. ``column`` is excluded: a concrete pier standing on
#: its own pad shares that pad's whole footprint by design.
CONCRETE_CATEGORIES = ("pad", "footing", "slab")

# Minimum shared plan area (m²). A face abutment intersects in a zero-area line; this clears
# it with margin. Same constant, same reasoning, as interference.py's.
_TOL_AREA = 1e-4


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
    for solid in model.solids:
        if solid.category not in CONCRETE_CATEGORIES:
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

    out: list[Finding] = []
    reported: set[frozenset[str]] = set()
    clashed: set[str] = set()
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
    # A check that says nothing has graded nothing. Every isolated pour that came through
    # clean says so by name, so the report shows the four breezeway pads standing clear
    # rather than showing an absence.
    clear = sorted(tag for tag, _l, _p, _z0, _z1 in subjects if tag not in clashed)
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
