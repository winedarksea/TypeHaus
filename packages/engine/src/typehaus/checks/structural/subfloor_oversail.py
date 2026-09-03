"""How far a subfloor sheet may reach past the framing it is nailed to (→ 12 §checks).

``FloorSystem.subfloor_outline`` lets an authored sheet win over the derived joist field —
the breezeway's composite plank runs past its rim onto two door thresholds, which is what a
deck board does. The field is one line in ``resolve/floors.py`` and touches nothing else, so
nothing else pushes back on it: the sheet can be authored any size at all, and the model
stays green while the plank floats over air.

**The bound is not arbitrary and is not this check's own number.** It is
``preferences.toml [framing] bearing_plan_tolerance_in`` (8" by default), the same allowance
``takeoff/uplift.py`` uses to decide whether a member's end lands on a support. That
matters because of a failure this house has already had once:
``params/sunken_garden.py`` records that a sheet oversailing past that tolerance makes the
uplift pass find neither a derived tie nor a hanger, and FAIL **every member under the
deck** — a cascade whose cause is nowhere near where it is reported. Bounding the oversail
here is what turns that into one finding naming one deck.

The measure is the largest distance from any sheet corner to the framing's own plan
bounding box, so a sheet that oversails on one edge only is graded on that edge. A sheet
INSIDE the framing is not an oversail and is not this check's business — a plank narrower
than its joists is a design choice, and the joists it leaves bare are visible in the
framing plan.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity, not_applicable
from typehaus.quantities import M_PER_IN
from typehaus.takeoff.hardware_config import DEFAULT_HARDWARE_TAKEOFF_CONFIG

_CHECK_ID = "structural.subfloor_oversail"
_LIMIT_IN = DEFAULT_HARDWARE_TAKEOFF_CONFIG.uplift.bearing_plan_tolerance_in


def _framing_box(floor) -> tuple[float, float, float, float] | None:
    points = [point for member in floor.members for point in (member.p0, member.p1)]
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), max(xs), min(ys), max(ys)


@check(Tier.STRUCTURAL, _CHECK_ID)
def subfloor_oversail(ctx: CheckContext) -> list[Finding]:
    """An authored subfloor sheet must stay within a bearing tolerance of its framing."""
    from typehaus.model.floors import FloorSystem

    authored = [system for system in ctx.plan.all_elements()
                if isinstance(system, FloorSystem) and system.subfloor_outline]
    if not authored:
        return [not_applicable(
            _CHECK_ID,
            "no deck in this building authors a FloorSystem.subfloor_outline — every "
            "subfloor here is its own joist field, which cannot oversail anything")]

    floors = {floor.tag: floor for floor in ctx.model.floors}
    out: list[Finding] = []
    for system in sorted(authored, key=lambda item: item.tag):
        floor = floors.get(system.tag)
        box = _framing_box(floor) if floor is not None else None
        if box is None:
            out.append(Finding(
                severity=Severity.WARN, check_id=_CHECK_ID,
                message=(f"UNKNOWN — deck {system.tag} authors a subfloor_outline but "
                         f"resolves no framing to measure it against"),
                element_tags=(system.tag,), result=Result.UNKNOWN,
                fix_hint="check the deck's joist bearing_refs resolve"))
            continue
        x0, x1, y0, y1 = box
        worst_in, edge = 0.0, ""
        for point in system.subfloor_outline:
            px, py = point.xy_m
            for over, name in ((x0 - px, "west"), (px - x1, "east"),
                               (y0 - py, "south"), (py - y1, "north")):
                if over / M_PER_IN > worst_in:
                    worst_in, edge = over / M_PER_IN, name
        if worst_in > _LIMIT_IN + 1e-9:
            out.append(Finding(
                severity=Severity.WARN, check_id=_CHECK_ID,
                message=(f"[advisory, not engineering] deck {system.tag}'s authored subfloor "
                         f"sheet oversails its framing by {worst_in:.2f}\" on the {edge} "
                         f"edge, past the {_LIMIT_IN:.0f}\" bearing plan tolerance. Past that "
                         f"the uplift pass finds neither a derived tie nor a hanger for the "
                         f"members under it and FAILs all of them, reported nowhere near "
                         f"here"),
                element_tags=(system.tag,), result=Result.FAIL,
                fix_hint=("bring the sheet back inside the tolerance, or extend the framing "
                          "under it — a plank with nothing to nail to is not a walking "
                          "surface")))
        else:
            out.append(Finding(
                severity=Severity.WARN, check_id=_CHECK_ID,
                message=(f"[advisory, not engineering] deck {system.tag}'s authored subfloor "
                         f"sheet oversails its framing by at most {worst_in:.2f}\""
                         + (f" on the {edge} edge" if edge else "")
                         + f", within the {_LIMIT_IN:.0f}\" bearing plan tolerance"),
                element_tags=(system.tag,), result=Result.PASS))
    return out
