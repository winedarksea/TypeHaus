"""Steady-state Glaser condensation analysis for an assembly (M5 WP5.1).

The calculation is deliberately a screening tool: it applies fixed design-day boundary
conditions, walks the authored interior-to-exterior layer order, and reports its missing
inputs instead of inventing material properties. It is not a hygrothermal simulation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.checks.registry import CheckContext, Preferences, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.assembly import Assembly, Layer
from typehaus.model.enums import LayerFunction, Occupancy
from typehaus.model.plan import Library

# Layers whose vapor role is "moisture source/store", interior of any rainscreen cavity.
_WETTABLE = {
    LayerFunction.STRUCTURE, LayerFunction.SHEATHING, LayerFunction.INSULATION,
}
_VENTED = {LayerFunction.AIRGAP, LayerFunction.FURRING}


def _glaser_layers(layers: list[Layer]) -> list[Layer]:
    """Truncate the stack at an exterior ventilated rainscreen cavity.

    A furring/airgap layer that sits outboard of the structure/sheathing/insulation is a
    drained-and-back-vented cavity open to outdoor air: everything from that plane outward
    (the vent and its cladding) is pressure-equalised with the exterior, so it carries no
    part of the interior-to-exterior vapor drive. Standard Glaser practice terminates the
    analysis there rather than modeling the cladding as a cold-side vapor trap. Assemblies
    with no such cavity (concrete, direct-applied finishes) walk their full depth.
    """
    for index, layer in enumerate(layers):
        if layer.function in _VENTED and any(
            inner.function in _WETTABLE for inner in layers[:index]
        ):
            return layers[:index]
    return layers


@dataclass(frozen=True)
class CondensationPoint:
    """One point in the graph, measured from the interior face of the stack."""

    position: float
    temperature_c: float
    vapor_pressure_pa: float
    saturation_pressure_pa: float


@dataclass(frozen=True)
class CondensationAnalysis:
    assembly_tag: str
    points: tuple[CondensationPoint, ...]
    crossing_layer: str | None = None
    crossing_fraction: float | None = None
    unknown_materials: tuple[str, ...] = ()

    @property
    def known(self) -> bool:
        return not self.unknown_materials

    @property
    def has_risk(self) -> bool:
        return self.crossing_layer is not None

    def as_dict(self) -> dict[str, object]:
        return {
            "assembly": self.assembly_tag,
            "status": "unknown" if not self.known else "risk" if self.has_risk else "safe",
            "crossing_layer": self.crossing_layer,
            "crossing_fraction": self.crossing_fraction,
            "unknown_materials": list(self.unknown_materials),
            "points": [
                {"position": p.position, "temperature_c": p.temperature_c,
                 "vapor_pressure_pa": p.vapor_pressure_pa,
                 "saturation_pressure_pa": p.saturation_pressure_pa}
                for p in self.points
            ],
        }


def _saturation_pressure_pa(temperature_c: float) -> float:
    """Magnus saturation curve, accurate enough for a design-day screening plot."""
    return 610.94 * math.exp(17.625 * temperature_c / (temperature_c + 243.04))


def _f_to_c(temperature_f: float) -> float:
    return (temperature_f - 32.0) * 5.0 / 9.0


def analyze_assembly(
    assembly: Assembly, library: Library, *, heating_design_temp_f: float | None,
    preferences: Preferences,
) -> CondensationAnalysis:
    """Return the Glaser profile for ``assembly`` or a named UNKNOWN result.

    ``perm_rating`` is treated as permeability in US perm-in units, so a layer's vapor
    resistance is thickness-inches / perm. This is the dimensional relationship the
    authored material scalar was introduced to support.
    """
    layers = _glaser_layers(list(assembly.default_lining) + list(assembly.layers))
    missing: list[str] = []
    thermal_resistances: list[float] = []
    vapor_resistances: list[float] = []
    for layer in layers:
        material = library.material(layer.material_ref)
        if material is None or material.perm_rating is None or material.perm_rating <= 0:
            name = material.name if material else layer.material_ref
            missing.append(name)
        if material is None or material.r_per_inch is None or material.r_per_inch < 0:
            name = material.name if material else layer.material_ref
            missing.append(name)
            thermal_resistances.append(0.0)
        else:
            thermal_resistances.append(material.r_per_inch * layer.thickness.inches)
        vapor_resistances.append(
            layer.thickness.inches / material.perm_rating
            if material is not None and material.perm_rating and material.perm_rating > 0 else 0.0
        )
    if heating_design_temp_f is None:
        missing.append("Site.design_temp_heating")
    if missing:
        return CondensationAnalysis(
            assembly.tag, (), unknown_materials=tuple(dict.fromkeys(missing))
        )

    total_r = sum(thermal_resistances)
    total_vapor_r = sum(vapor_resistances)
    if total_r <= 0 or total_vapor_r <= 0:
        return CondensationAnalysis(assembly.tag, (), unknown_materials=("zero-resistance stack",))

    interior_c = _f_to_c(preferences.interior_setpoint_f)
    exterior_c = _f_to_c(heating_design_temp_f)
    interior_pressure = _saturation_pressure_pa(interior_c) * preferences.interior_relative_humidity
    exterior_pressure = _saturation_pressure_pa(exterior_c) * preferences.exterior_relative_humidity
    points: list[CondensationPoint] = [CondensationPoint(
        0.0, interior_c, interior_pressure, _saturation_pressure_pa(interior_c)
    )]
    r_used = vapor_used = 0.0
    for r_value, vapor_r in zip(thermal_resistances, vapor_resistances):
        r_used += r_value
        vapor_used += vapor_r
        fraction = r_used / total_r
        temperature = interior_c + (exterior_c - interior_c) * fraction
        vapor_fraction = vapor_used / total_vapor_r
        pressure = interior_pressure + (exterior_pressure - interior_pressure) * vapor_fraction
        points.append(CondensationPoint(
            vapor_fraction, temperature, pressure, _saturation_pressure_pa(temperature)
        ))

    for index, layer in enumerate(layers):
        start, end = points[index], points[index + 1]
        start_delta = start.vapor_pressure_pa - start.saturation_pressure_pa
        end_delta = end.vapor_pressure_pa - end.saturation_pressure_pa
        if start_delta <= 0 < end_delta:
            denominator = end_delta - start_delta
            fraction = -start_delta / denominator if denominator else 0.0
            return CondensationAnalysis(
                assembly.tag, tuple(points), crossing_layer=layer.name,
                crossing_fraction=fraction,
            )
    return CondensationAnalysis(assembly.tag, tuple(points))


# Occupancies that are not part of the conditioned (heated/humidified) building volume, so
# the fixed interior design conditions this screening tool assumes do not apply to them.
_UNCONDITIONED = {Occupancy.GARAGE, Occupancy.UNCONDITIONED}


def conditioned_envelope_assemblies(ctx: CheckContext) -> list[str]:
    """Assembly tags on the conditioned exterior envelope, in first-seen order.

    Glaser screening with an outdoor-air boundary only means something across an assembly
    that actually separates the conditioned interior (70 F / design RH) from the exterior
    at the heating design temperature. It excludes:

    * interior partitions and interior concrete/bearing walls — no cross-envelope gradient;
    * an unconditioned detached garage and freestanding site structures — the interior side
      is not conditioned, so the fixed interior conditions do not apply;
    * below-grade foundation walls — these are ground-coupled (soil near +10 C, not the
      -15 F design air), so an outdoor-air Glaser walk would invent a risk that does not run.

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
        if tag and tag not in seen:
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


@check(Tier.BUILDING_SCIENCE, "building_science.condensation")
def condensation_risk(ctx: CheckContext) -> list[Finding]:
    heating = ctx.plan.project.site.design_temp_heating
    temperature_f = heating.fahrenheit if heating is not None else None
    findings: list[Finding] = []
    for tag in conditioned_envelope_assemblies(ctx):
        assembly = ctx.plan.library.resolve_assembly(tag)
        if assembly is None:
            continue
        analysis = analyze_assembly(
            assembly, ctx.plan.library, heating_design_temp_f=temperature_f,
            preferences=ctx.preferences,
        )
        if not analysis.known:
            findings.append(Finding(
                severity=Severity.WARN, check_id="building_science.condensation",
                message=("UNKNOWN — missing Glaser inputs: "
                         + ", ".join(analysis.unknown_materials)),
                element_tags=(assembly.tag,), result=Result.UNKNOWN,
            ))
        elif analysis.has_risk:
            findings.append(Finding(
                severity=Severity.WARN, check_id="building_science.condensation",
                message=(f"dew point reached at {analysis.crossing_layer} "
                         f"({analysis.crossing_fraction:.0%} through layer)"),
                element_tags=(assembly.tag,), result=Result.FAIL,
            ))
    return findings
