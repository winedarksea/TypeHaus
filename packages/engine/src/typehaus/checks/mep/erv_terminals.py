"""Where a balanced ventilator's outdoor-side hoods may be.

An ERV with no intake and no discharge is not modeled, and until ``Service`` learned to
spell ``OUTDOOR_AIR``/``EXHAUST_AIR`` the Catlin ERV had neither — the plan said so in a
comment. Once the two runs exist, they are the pieces of the ventilation system most easily
got wrong, because every failure is a *relationship* rather than a property of the run:

* an intake within ten feet of a discharge short-circuits the machine — it recovers heat
  from air it just threw away, and it re-inhales whatever it just exhausted
  (IRC M1602.2, ASHRAE 62.2-2019 §6.8);
* an intake within three feet of a plumbing vent or a dryer exhaust draws sewer gas and
  lint into every room the supply side feeds;
* a hood set low on a rim band spends February under a drift, and a blocked intake stops
  the whole balanced system rather than half of it.

Each is a distance the model can measure and nobody can eyeball off a plan. What the model
cannot do is *place* them — that is a facade decision (see ``houses/catlin/CLAUDE.md``) —
so this grades a placement rather than proposing one.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import advisory, failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import DuctSystem, EquipmentKind

#: IRC M1602.2 / ASHRAE 62.2-2019 §6.8: an outdoor-air intake stands at least 10 ft from
#: any exhaust outlet. A manufacturer's manual may allow less for its own balanced pair —
#: Broan's does — but the manual governs only the pair it ships, and the code figure is
#: what an inspector reads, so the code figure is the one graded here.
_INTAKE_TO_EXHAUST_FT = 10.0
#: The same sections' separation from a plumbing vent terminal or a dryer exhaust. Shorter
#: than the exhaust figure because those are point sources rather than a continuous plume.
_INTAKE_TO_CONTAMINANT_FT = 3.0
#: Height above finished grade an intake hood needs to stay clear of drifted snow. Judgment
#: with a stated basis, in the same spirit as ``structural.snow``'s slide reach: there is no
#: authored snow depth in the model and none is published as a design value the way ground
#: *load* is, so this is the 24" the manufacturers' cold-climate literature asks for on top
#: of a foot of drift. An intake below it is graded advisory, never a hard FAIL — the number
#: is a rule of thumb and says so.
_HOOD_ABOVE_GRADE_FT = 3.0


def _outdoor_end(duct) -> tuple[float, float, float] | None:
    """The run's outdoor end as ``(x, y, z)``, or None if it has no elevations to read.

    The *last* vertex by authoring order: an outdoor-air run is authored inward from its
    hood and an exhaust run outward to it, which is the direction the air goes and the
    direction a plan reader traces. The pairing is made explicit by the caller, which asks
    each system for the end it cares about rather than guessing from geometry.
    """
    if not duct.z_m or len(duct.z_m) != len(duct.path):
        return None
    return (duct.path[-1][0], duct.path[-1][1], duct.z_m[-1])


def _first_end(duct) -> tuple[float, float, float] | None:
    if not duct.z_m or len(duct.z_m) != len(duct.path):
        return None
    return (duct.path[0][0], duct.path[0][1], duct.z_m[0])


def _feet(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.dist(a, b) / 0.3048


def _plumbing_vent_terminals(ctx: CheckContext) -> list[tuple[str, tuple[float, float, float]]]:
    """Every plumbing/radon vent terminal, as ``(tag, point)`` in the project frame."""
    from typehaus.model.mep import VentRun
    from typehaus.resolve.vent_termination import (
        derived_termination_elevation,
        exterior_riser_point,
    )

    out: list[tuple[str, tuple[float, float, float]]] = []
    for element in ctx.plan.all_elements():
        if not isinstance(element, VentRun):
            continue
        x, y = exterior_riser_point(element)
        z = derived_termination_elevation(ctx.model, element)
        if z is None:
            stated = element.roof_termination_elevation
            if stated is None:
                continue
            z = stated.meters
        out.append((element.tag, (x, y, z)))
    return out


def _ends_outdoors(ctx: CheckContext, duct) -> bool:
    """Whether the run's last vertex lands outside every resolved room's clear face.

    This is what separates the ERV's discharge from the house's other EXHAUST runs, and it
    is a fact about the geometry rather than a naming convention: a bath extract ends at the
    machine, in a room; the stale-air leg ends in the open air. The same probe
    ``code.M1502_dryer_exhaust`` uses for M1502.3, for the same reason.
    """
    from shapely.geometry import Point, Polygon

    if not duct.path:
        return False
    probe = Point(duct.path[-1])
    for room in ctx.model.rooms:
        if len(room.clear_face) >= 3 and Polygon(room.clear_face).covers(probe):
            return False
    return True


def _dryer_terminations(ctx: CheckContext) -> list[tuple[str, tuple[float, float, float]]]:
    out: list[tuple[str, tuple[float, float, float]]] = []
    for duct in ctx.model.ducts:
        if duct.system != DuctSystem.DRYER.value:
            continue
        end = _outdoor_end(duct)
        if end is not None:
            out.append((duct.tag, end))
    return out


@check(Tier.CODE, "mep.erv_outdoor_terminals")
def erv_outdoor_terminals(ctx: CheckContext) -> list[Finding]:
    """Intake/exhaust separation, contaminant separation and snow clearance for the hoods."""
    cid = "mep.erv_outdoor_terminals"
    intakes = [d for d in ctx.model.ducts if d.system == DuctSystem.OUTDOOR_AIR.value]
    if not intakes:
        # Two different sentences hide behind "no outdoor-air run". A house that places no
        # balanced ventilator at all has nothing for M1602.2 to govern — N/A, and the
        # permit line can gate on it. A house that places an ERV and then models no intake
        # duct has a real hole in its model, and that stays UNKNOWN.
        ventilators = [element for element in ctx.plan.all_elements()
                       if element.element_kind == "Equipment"
                       and getattr(element, "kind", None) is EquipmentKind.ERV]
        if not ventilators:
            return [not_applicable(cid, "this house places no balanced ventilator, so "
                                        "there is no ERV intake or exhaust hood for "
                                        "M1602.2 to locate", (), code="M1602.2")]
        return [unknown(cid, f"{ventilators[0].tag} is placed but no DuctSystem.OUTDOOR_AIR "
                             f"run is modeled, so there is no intake hood to locate",
                        tuple(v.tag for v in ventilators), code="M1602.2")]
    out: list[Finding] = []
    grade = ctx.plan.project.site.grade
    grade_m = grade.meters if grade is not None else None
    discharges = [d for d in ctx.model.ducts
                  if d.system == DuctSystem.EXHAUST.value and _ends_outdoors(ctx, d)]
    contaminants = _plumbing_vent_terminals(ctx) + _dryer_terminations(ctx)

    for intake in intakes:
        # An outdoor-air run is authored from its hood inward, so the hood is vertex 0.
        hood = _first_end(intake)
        if hood is None:
            out.append(unknown(cid, f"outdoor-air run {intake.tag} carries no elevations, "
                                    "so its hood cannot be located", (intake.tag,),
                               code="M1602.2"))
            continue
        for discharge in discharges:
            other = _outdoor_end(discharge)
            if other is None:
                continue
            separation = _feet(hood, other)
            if separation < _INTAKE_TO_EXHAUST_FT - 1e-6:
                out.append(failed(
                    cid, f"{intake.tag}'s intake hood stands {separation:.1f}' from "
                         f"{discharge.tag}'s discharge; IRC M1602.2 / ASHRAE 62.2 §6.8 "
                         f"want {_INTAKE_TO_EXHAUST_FT:.0f}' — the machine re-inhales what "
                         "it just threw away",
                    (intake.tag, discharge.tag), code="M1602.2",
                    fix="move one hood along the facade, or carry both to the gable where "
                        "the separation is trivially made"))
            else:
                out.append(passed(
                    cid, f"{intake.tag}'s intake stands {separation:.1f}' from "
                         f"{discharge.tag}'s discharge (>= {_INTAKE_TO_EXHAUST_FT:.0f}')",
                    (), code="M1602.2"))
        for tag, point in contaminants:
            separation = _feet(hood, point)
            if separation < _INTAKE_TO_CONTAMINANT_FT - 1e-6:
                out.append(failed(
                    cid, f"{intake.tag}'s intake hood stands {separation:.1f}' from {tag}; "
                         f"{_INTAKE_TO_CONTAMINANT_FT:.0f}' is the minimum from a plumbing "
                         "vent or a dryer exhaust",
                    (intake.tag, tag), code="M1602.2"))
        if grade_m is None:
            out.append(unknown(cid, f"the site states no grade, so {intake.tag}'s hood "
                                    "height above it cannot be graded", (intake.tag,),
                               code="M1602.2"))
            continue
        above_ft = (hood[2] - grade_m) / 0.3048
        if above_ft < _HOOD_ABOVE_GRADE_FT - 1e-6:
            out.append(advisory(
                cid, f"{intake.tag}'s intake hood sits {above_ft * 12:.0f}\" above grade; "
                     f"{_HOOD_ABOVE_GRADE_FT * 12:.0f}\" is the cold-climate rule of thumb "
                     "for clearing drifted snow, and a blocked intake stops the whole "
                     "balanced system",
                (intake.tag,), Result.FAIL, code="M1602.2",
                fix="raise the hood to the storey above, or carry the run to a gable"))
        else:
            out.append(passed(
                cid, f"{intake.tag}'s intake hood sits {above_ft * 12:.0f}\" above grade "
                     f"(>= {_HOOD_ABOVE_GRADE_FT * 12:.0f}\")", (), code="M1602.2"))
    return out


