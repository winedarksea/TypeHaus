"""Condensation-risk check: scope the Glaser walk to the envelope and report it (M5 WP5.1).

The profile maths live in :mod:`typehaus.checks.building_science.glaser`; this module
decides *which* assemblies the screening applies to and turns each result into a
`Finding`. A safe assembly still reports — its margin is the answer the M5 acceptance
asks for — so the tier is never silent about an envelope it did evaluate.
"""

from __future__ import annotations

from typehaus.checks.building_science.glaser import (  # re-exported: card/CLI/server import here
    CondensationAnalysis,
    CondensationPoint,
    MonthlyAssessment,
    analyze_assembly,
    analyze_assembly_monthly,
    analyze_layers,
    analyze_layers_monthly,
    glaser_layers,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.assembly import Assembly
from typehaus.model.enums import ControlLayer, LayerFunction, Occupancy

__all__ = [
    "CondensationAnalysis", "CondensationPoint", "MonthlyAssessment", "analyze_assembly",
    "analyze_assembly_monthly", "analyze_layers", "analyze_layers_monthly",
    "glaser_layers", "conditioned_envelope_assemblies", "condensation_risk",
]

# The monthly (ISO 13788-style) worst-month reduction is the pass/fail GATE; the
# 99%-design-hour walk stays as a cold-snap SCREEN under its own finding id.
CHECK_ID = "building_science.condensation"
SCREEN_CHECK_ID = "building_science.condensation.cold_snap"

# Occupancies that are not part of the conditioned (heated/humidified) building volume, so
# the fixed interior design conditions this screening tool assumes do not apply to them.
_UNCONDITIONED = {Occupancy.GARAGE, Occupancy.UNCONDITIONED}


def _carries_thermal_control(assembly: Assembly) -> bool:
    """Does this assembly insulate — i.e. can it plausibly bound conditioned space?

    An exterior wall with no insulation layer and no THERMAL control layer is not part of
    the thermal envelope in a climate-zone-6 house: it is a guard, a screen wall, or a
    site structure that happens to carry cladding. Running an indoor-to-outdoor vapour
    drive across one reports a margin for a gradient that does not exist there.
    """
    layers = list(assembly.default_lining) + list(assembly.layers)
    return any(layer.function == LayerFunction.INSULATION
               or ControlLayer.THERMAL in layer.control
               or layer.cavity is not None  # a filled stud/joist bay is the insulation
               for layer in layers)


def conditioned_envelope_assemblies(ctx: CheckContext) -> list[str]:
    """Assembly tags on the conditioned exterior envelope, in first-seen order.

    Glaser screening with an outdoor-air boundary only means something across an assembly
    that actually separates the conditioned interior (70 F / design RH) from the exterior
    at the heating design temperature. It excludes:

    * interior partitions and interior concrete/bearing walls — no cross-envelope gradient;
    * an unconditioned detached garage and freestanding site structures — the interior side
      is not conditioned, so the fixed interior conditions do not apply;
    * below-grade foundation walls — these are ground-coupled (soil near +10 C, not the
      -15 F design air), so an outdoor-air Glaser walk would invent a risk that does not run;
    * clad-but-uninsulated walls (masonry guards, screen walls) — see
      :func:`_carries_thermal_control`.

    An above-grade exterior wall is identified by its outermost cladding layer; the analysis
    is scoped to those walls and to roofs, on storeys that hold conditioned rooms.
    """
    conditioned: set[str] = set()
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            occ = getattr(element, "occupancy", None)
            if element.element_kind == "Room" and occ not in _UNCONDITIONED:
                conditioned.add(storey.tag)
                break

    tags: list[str] = []
    seen: set[str] = set()

    def _add(tag: str | None) -> None:
        if tag is None or tag in seen:
            return
        assembly = ctx.plan.library.resolve_assembly(tag)
        if assembly is None or not _carries_thermal_control(assembly):
            return
        seen.add(tag)
        tags.append(tag)

    for wall in ctx.model.walls:
        if wall.storey not in conditioned:
            continue
        if any(layer.function == "cladding" for layer in wall.layers):
            _add(wall.assembly)
    for roof in ctx.model.roofs:
        if getattr(roof, "storey", None) in conditioned:
            _add(roof.assembly)
    return tags


def _unknown_finding(analysis: CondensationAnalysis, label: str, check_id: str) -> Finding:
    return Finding(
        severity=Severity.WARN, check_id=check_id,
        message=(f"{label}: UNKNOWN — missing Glaser inputs: "
                 + ", ".join(analysis.unknown_materials)),
        element_tags=(analysis.assembly_tag,), result=Result.UNKNOWN,
        fix_hint="author perm_rating (perm-in) or vapor_permeance_perms (perms) with "
                 "its ASTM E96 / manufacturer source on the named material",
    )


def _gate_finding(assessment: MonthlyAssessment | None, assembly_tag: str) -> Finding:
    """The monthly (ISO 13788-style) gate finding — the pass/fail verdict."""
    if assessment is None:
        return Finding(
            severity=Severity.WARN, check_id=CHECK_ID,
            message="monthly gate (ISO 13788-style): UNKNOWN — Site.monthly_normals is "
                    "not authored (needs 12 MonthlyNormal entries, January..December)",
            element_tags=(assembly_tag,), result=Result.UNKNOWN,
            fix_hint="author Site.monthly_normals from published station normals (e.g. "
                     "NOAA NCEI 1991-2020) so the seasonal gate can run; until then only "
                     "the cold-snap screen is evaluated",
        )
    analysis = assessment.analysis
    if not analysis.known:
        return _unknown_finding(analysis, "monthly gate (ISO 13788-style)", CHECK_ID)
    if analysis.has_risk:
        return Finding(
            severity=Severity.WARN, check_id=CHECK_ID,
            message=(f"monthly gate (ISO 13788-style): dew point reached at "
                     f"{analysis.crossing_layer} ({analysis.crossing_fraction:.0%} through "
                     f"layer) at {assessment.boundary}"),
            element_tags=(analysis.assembly_tag,), result=Result.FAIL,
            fix_hint="this is the gate: a crossing against a monthly *mean* means the "
                     "plane runs wet for weeks, not hours — add exterior insulation, a "
                     "warm-side vapour retarder, or a vented cavity so the plane can dry",
        )
    tightest = analysis.tightest_plane
    assert tightest is not None  # a known analysis always carries its profile
    return Finding(
        severity=Severity.WARN, check_id=CHECK_ID,
        message=(f"monthly gate (ISO 13788-style): no dew-point crossing in any month — "
                 f"worst month {assessment.month} at {assessment.boundary}, tightest plane "
                 f"{analysis.tightest_plane_name} at "
                 f"{tightest.local_relative_humidity:.0%} RH, "
                 f"{tightest.margin_pa:.0f} Pa below saturation"),
        element_tags=(analysis.assembly_tag,), result=Result.PASS,
    )


def _screen_finding(analysis: CondensationAnalysis, boundary: str) -> Finding:
    """The 99%-design-hour walk, relabeled as the cold-snap screen (not the gate)."""
    if analysis.has_risk:
        return Finding(
            severity=Severity.WARN, check_id=SCREEN_CHECK_ID,
            message=(f"cold-snap screen: dew point reached at {analysis.crossing_layer} "
                     f"({analysis.crossing_fraction:.0%} through layer) at {boundary}"),
            element_tags=(analysis.assembly_tag,), result=Result.FAIL,
            fix_hint="screen only — the monthly (ISO 13788-style) gate is the pass/fail "
                     "verdict; this is the 99% design hour, not a seasonal mean, so a "
                     "crossing here means the plane runs wet during a cold snap and must "
                     "be able to dry, not that the wall fails the gate",
        )
    tightest = analysis.tightest_plane
    assert tightest is not None  # a known analysis always carries its profile
    return Finding(
        severity=Severity.WARN, check_id=SCREEN_CHECK_ID,
        message=(f"cold-snap screen: no dew-point crossing at {boundary} — tightest plane "
                 f"{analysis.tightest_plane_name} at "
                 f"{tightest.local_relative_humidity:.0%} RH, "
                 f"{tightest.margin_pa:.0f} Pa below saturation"),
        element_tags=(analysis.assembly_tag,), result=Result.PASS,
    )


@check(Tier.BUILDING_SCIENCE, CHECK_ID)
def condensation_risk(ctx: CheckContext) -> list[Finding]:
    """Per envelope assembly: the monthly gate (pass/fail) plus the cold-snap screen.

    The gate runs :func:`analyze_layers` twelve times over ``Site.monthly_normals`` and
    keeps the worst month — a seasonal mean is what an assembly actually has to dry
    against. The 99%-design-hour walk stays, relabeled as a screen: informative about a
    cold snap, never the verdict. When the Glaser inputs themselves are missing, one
    UNKNOWN finding (the gate's) names them instead of repeating itself per surface.
    """
    site = ctx.plan.project.site
    heating = site.design_temp_heating
    temperature_f = heating.fahrenheit if heating is not None else None
    # Every finding states its boundary condition: a Glaser crossing is only meaningful
    # against the design temperature and interior humidity that produced it.
    boundary = (f"{temperature_f:.0f} F design / "
                f"{ctx.preferences.interior_relative_humidity:.0%} interior RH"
                if temperature_f is not None else "the design heating temperature")
    findings: list[Finding] = []
    for tag in conditioned_envelope_assemblies(ctx):
        assembly = ctx.plan.library.resolve_assembly(tag)
        if assembly is None:
            continue
        assessment = analyze_assembly_monthly(
            assembly, ctx.plan.library, monthly_normals=site.monthly_normals,
            preferences=ctx.preferences,
        )
        findings.append(_gate_finding(assessment, assembly.tag))
        screen = analyze_assembly(
            assembly, ctx.plan.library, heating_design_temp_f=temperature_f,
            preferences=ctx.preferences,
        )
        if not screen.known:
            # The gate already named these inputs unless it ran on complete data (or was
            # itself missing its normals while the screen misses the design temperature).
            if assessment is None or assessment.analysis.known:
                findings.append(_unknown_finding(screen, "cold-snap screen",
                                                 SCREEN_CHECK_ID))
            continue
        findings.append(_screen_finding(screen, boundary))
    return findings
