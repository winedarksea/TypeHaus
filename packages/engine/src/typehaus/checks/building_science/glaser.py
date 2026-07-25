"""Steady-state Glaser temperature + vapour-pressure profile through a layer stack (WP5.1).

This is the physics half of WP5.1; :mod:`typehaus.checks.building_science.condensation`
owns the envelope scoping and the `Finding` surface. It is a *screening* calculation —
fixed design-day boundary conditions, one authored interior→exterior layer order, no
storage, no air leakage — and it reports its missing inputs by name instead of
substituting a default for a material property nobody authored (#32).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from typehaus.model.assembly import Assembly, Layer
from typehaus.model.enums import LayerFunction
from typehaus.model.plan import Library
from typehaus.quantities import rsi

if TYPE_CHECKING:  # only for the annotation; the physics needs no check-registry import
    from typehaus.checks.registry import Preferences

# Layers whose vapor role is "moisture source/store", interior of any rainscreen cavity.
_WETTABLE = {
    LayerFunction.STRUCTURE, LayerFunction.SHEATHING, LayerFunction.INSULATION,
}
_VENTED = {LayerFunction.AIRGAP, LayerFunction.FURRING}

# ISO 13788 §6 fixes the surface resistances for an interstitial-condensation assessment:
# Rsi 0.25, Rse 0.04 m²·K/W. They are deliberately not the ASHRAE winter films the R-value
# rollup uses (0.12/0.03): the method that defines the crossing test also defines the
# boundary layers it is calibrated against, and omitting them entirely (as this walk used
# to) puts the whole indoor-to-outdoor ΔT across the solid layers and reads every plane
# colder than it runs.
INTERIOR_SURFACE_R_US = rsi(0.25).r_us
EXTERIOR_SURFACE_R_US = rsi(0.04).r_us

# Magnus/Tetens saturation curve over water, WMO CIMO Guide form. Accurate to well under
# 1% across the -30..+30 C design-day band, which is finer than the perm data feeding it.
_MAGNUS_SCALE_PA = 610.94
_MAGNUS_BETA = 17.625
_MAGNUS_LAMBDA_C = 243.04

_FAHRENHEIT_FREEZING = 32.0
_FAHRENHEIT_PER_CELSIUS = 9.0 / 5.0


def saturation_pressure_pa(temperature_c: float) -> float:
    """Saturation vapour pressure over water at ``temperature_c``."""
    return _MAGNUS_SCALE_PA * math.exp(
        _MAGNUS_BETA * temperature_c / (temperature_c + _MAGNUS_LAMBDA_C)
    )


def _f_to_c(temperature_f: float) -> float:
    return (temperature_f - _FAHRENHEIT_FREEZING) / _FAHRENHEIT_PER_CELSIUS


def glaser_layers(layers: list[Layer]) -> list[Layer]:
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

    @property
    def local_relative_humidity(self) -> float:
        """Vapour pressure as a fraction of saturation at this plane. >= 1 is condensing."""
        if self.saturation_pressure_pa <= 0.0:
            return 0.0
        return self.vapor_pressure_pa / self.saturation_pressure_pa

    @property
    def margin_pa(self) -> float:
        """How far below saturation this plane sits. Negative means condensing."""
        return self.saturation_pressure_pa - self.vapor_pressure_pa


@dataclass(frozen=True)
class CondensationAnalysis:
    assembly_tag: str
    points: tuple[CondensationPoint, ...]
    crossing_layer: str | None = None
    crossing_fraction: float | None = None
    unknown_materials: tuple[str, ...] = ()
    # Layer names matching ``points[1:]``; ``points[0]`` is the interior surface.
    plane_names: tuple[str, ...] = ()

    @property
    def known(self) -> bool:
        return not self.unknown_materials

    @property
    def has_risk(self) -> bool:
        return self.crossing_layer is not None

    @property
    def tightest_plane(self) -> CondensationPoint | None:
        """The plane running closest to saturation — the assembly's condensation margin.

        Ranked by local RH, not by the Pa margin: saturation pressure collapses with
        temperature, so the smallest absolute gap is always the outermost, coldest plane
        no matter how safe the wall is. RH is the quantity the crossing test is about.
        """
        return max(self.points, key=lambda point: point.local_relative_humidity,
                   default=None)

    @property
    def tightest_plane_name(self) -> str | None:
        tightest = self.tightest_plane
        if tightest is None:
            return None
        index = self.points.index(tightest)
        if index == 0:
            return "interior surface"
        return self.plane_names[index - 1] if index - 1 < len(self.plane_names) else None

    def as_dict(self) -> dict[str, object]:
        tightest = self.tightest_plane
        return {
            "assembly": self.assembly_tag,
            "status": "unknown" if not self.known else "risk" if self.has_risk else "safe",
            "crossing_layer": self.crossing_layer,
            "crossing_fraction": self.crossing_fraction,
            "unknown_materials": list(self.unknown_materials),
            "margin_pa": tightest.margin_pa if tightest else None,
            "margin_layer": self.tightest_plane_name,
            "points": [
                {"position": p.position, "temperature_c": p.temperature_c,
                 "vapor_pressure_pa": p.vapor_pressure_pa,
                 "saturation_pressure_pa": p.saturation_pressure_pa}
                for p in self.points
            ],
        }


@dataclass(frozen=True)
class _LayerPath:
    """One layer reduced to the two resistances the Glaser walk needs."""

    thermal_r_us: float
    # Vapour resistance in US rep (1/perm). ``inf`` is a sourced vapour barrier.
    vapor_resistance_rep: float


@dataclass(frozen=True)
class _MaterialPath:
    """R-value and permeance of one *material* over a stated depth."""

    r_us: float
    permeance_perms: float


def _material_path(material_ref: str, thickness_inches: float,
                   library: Library, missing: list[str]) -> _MaterialPath | None:
    """R + permeance for ``thickness_inches`` of ``material_ref``, or None with a note."""
    material = library.material(material_ref)
    if material is None:
        missing.append(material_ref)
        return None
    permeance = material.vapor_permeance_at(thickness_inches)
    if material.r_per_inch is None or material.r_per_inch < 0 or permeance is None:
        missing.append(material.name)
        return None
    return _MaterialPath(material.r_per_inch * thickness_inches, permeance)


def _layer_path(layer: Layer, library: Library) -> tuple[_LayerPath | None, list[str]]:
    """Resistances of ``layer``, parallel-pathed across its cavity fill, plus missing inputs.

    This is the same layer walk the R-value rollup does (``analysis._layer_rsi``) — the
    plan's point is that condensation is one more consumer of that data, so the two must
    not disagree about what a 2x6 wall's stud layer is worth. A batt between studs is the
    *other* path through the same depth, not a layer in series: U and permeance are both
    conductances, so both area-weight the same way, ``ff·framing + (1-ff)·fill``.
    """
    missing: list[str] = []
    framing = _material_path(layer.material_ref, layer.thickness.inches, library, missing)
    fill_spec = layer.cavity
    fill = None
    if fill_spec is not None:
        fill_thickness = (fill_spec.thickness or layer.thickness).inches
        fill = _material_path(fill_spec.material_ref, fill_thickness, library, missing)
    if missing or framing is None:
        return None, missing

    r_us, permeance = framing.r_us, framing.permeance_perms
    if fill is not None:
        framing_factor = min(max(fill_spec.framing_factor, 0.0), 1.0)
        permeance = (framing_factor * framing.permeance_perms
                     + (1.0 - framing_factor) * fill.permeance_perms)
        # A zero-R layer has infinite conductance, which would swamp the weighting; the
        # insulated bay is the meaningful path in that (unphysical) case.
        r_us = (fill.r_us if framing.r_us <= 0.0 or fill.r_us <= 0.0 else 1.0 / (
            framing_factor / framing.r_us + (1.0 - framing_factor) / fill.r_us))

    resistance = math.inf if permeance <= 0.0 else 1.0 / permeance
    return _LayerPath(r_us, resistance), []


def _vapor_fractions(resistances: list[float]) -> list[float] | None:
    """Fraction of total vapour resistance consumed at each layer's outboard face.

    A vapour-impermeable layer (permeance 0 → infinite resistance) takes the whole drop:
    every plane inboard of it sits at the interior pressure, every plane outboard at the
    exterior. Two barriers in one stack is physically indeterminate at steady state; the
    inboard one is credited, which is the conservative reading because it leaves the cold
    layers between the two barriers at full interior vapour pressure. Returns None when
    the stack has no resolvable vapour resistance at all.
    """
    first_barrier = next(
        (index for index, value in enumerate(resistances) if math.isinf(value)), None
    )
    if first_barrier is not None:
        return [0.0 if index < first_barrier else 1.0 for index in range(len(resistances))]
    total = sum(resistances)
    if total <= 0.0:
        return None
    used = 0.0
    fractions: list[float] = []
    for value in resistances:
        used += value
        fractions.append(used / total)
    return fractions


def analyze_layers(
    assembly_tag: str, layers: list[Layer], library: Library, *,
    heating_design_temp_f: float | None, interior_setpoint_f: float,
    interior_relative_humidity: float, exterior_relative_humidity: float,
) -> CondensationAnalysis:
    """Glaser profile for an already-truncated interior→exterior ``layers`` stack."""
    missing: list[str] = []
    paths: list[_LayerPath] = []
    for layer in layers:
        path, layer_missing = _layer_path(layer, library)
        missing.extend(layer_missing)
        if path is not None:
            paths.append(path)
    if heating_design_temp_f is None:
        missing.append("Site.design_temp_heating")
    if missing:
        return CondensationAnalysis(
            assembly_tag, (), unknown_materials=tuple(dict.fromkeys(missing))
        )
    assert heating_design_temp_f is not None

    vapor_fractions = _vapor_fractions([path.vapor_resistance_rep for path in paths])
    if vapor_fractions is None:
        return CondensationAnalysis(
            assembly_tag, (), unknown_materials=("stack has no vapour resistance",)
        )

    # Surface films carry temperature but no vapour resistance, so they shift the profile
    # without moving any plane along the vapour axis.
    total_r = (INTERIOR_SURFACE_R_US + EXTERIOR_SURFACE_R_US
               + sum(path.thermal_r_us for path in paths))
    interior_c = _f_to_c(interior_setpoint_f)
    exterior_c = _f_to_c(heating_design_temp_f)
    interior_pressure = saturation_pressure_pa(interior_c) * interior_relative_humidity
    exterior_pressure = saturation_pressure_pa(exterior_c) * exterior_relative_humidity

    def _temperature_at(cumulative_r: float) -> float:
        return interior_c + (exterior_c - interior_c) * (cumulative_r / total_r)

    surface_c = _temperature_at(INTERIOR_SURFACE_R_US)
    points = [CondensationPoint(0.0, surface_c, interior_pressure,
                                saturation_pressure_pa(surface_c))]
    cumulative_r = INTERIOR_SURFACE_R_US
    for path, vapor_fraction in zip(paths, vapor_fractions):
        cumulative_r += path.thermal_r_us
        temperature = _temperature_at(cumulative_r)
        pressure = interior_pressure + (exterior_pressure - interior_pressure) * vapor_fraction
        points.append(CondensationPoint(
            vapor_fraction, temperature, pressure, saturation_pressure_pa(temperature)
        ))

    plane_names = tuple(layer.name for layer in layers)
    crossing_layer, crossing_fraction = _first_crossing(points, plane_names)
    return CondensationAnalysis(
        assembly_tag, tuple(points), crossing_layer=crossing_layer,
        crossing_fraction=crossing_fraction, plane_names=plane_names,
    )


def _first_crossing(points: list[CondensationPoint],
                    plane_names: tuple[str, ...]) -> tuple[str | None, float | None]:
    """The first layer whose outboard face is supersaturated, and where inside it."""
    for index, name in enumerate(plane_names):
        start, end = points[index], points[index + 1]
        if end.margin_pa > 0:
            continue
        span = start.margin_pa - end.margin_pa
        fraction = start.margin_pa / span if span > 0 else 0.0
        return name, min(max(fraction, 0.0), 1.0)
    return None, None


def analyze_assembly(
    assembly: Assembly, library: Library, *, heating_design_temp_f: float | None,
    preferences: Preferences,
) -> CondensationAnalysis:
    """Return the Glaser profile for ``assembly`` or a named UNKNOWN result."""
    layers = glaser_layers(list(assembly.default_lining) + list(assembly.layers))
    return analyze_layers(
        assembly.tag, layers, library, heating_design_temp_f=heating_design_temp_f,
        interior_setpoint_f=preferences.interior_setpoint_f,
        interior_relative_humidity=preferences.interior_relative_humidity,
        exterior_relative_humidity=preferences.exterior_relative_humidity,
    )
