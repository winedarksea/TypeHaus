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
from typehaus.model.site import MonthlyNormal
from typehaus.quantities import rsi

if TYPE_CHECKING:  # only for the annotation; the physics needs no check-registry import
    from typehaus.checks.registry import Preferences

MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December")

# Layers whose vapor role is "moisture source/store", interior of any rainscreen cavity.
_WETTABLE = {
    LayerFunction.STRUCTURE, LayerFunction.SHEATHING, LayerFunction.INSULATION,
}
_VENTED = {LayerFunction.AIRGAP, LayerFunction.FURRING}
# The wall/roof core: the plane a warm-side vapour retarder must sit inboard of.
_CORE_PLANES = {LayerFunction.STRUCTURE, LayerFunction.SHEATHING}

# IRC R702.7.1 vapour-retarder classes, by ASTM E96 desiccant/dry-cup permeance of the
# material *as installed*. Upper bound of each class, tightest first; anything looser than
# Class III is vapour-permeable and is not a retarder at all.
#   Class I   <= 0.1 perm   (sheet polyethylene, unperforated foil)
#   Class II  0.1 - 1.0     (kraft-faced batt, "vapour-barrier" latex primer)
#   Class III 1.0 - 10.0    (latex or enamel paint over gypsum board)
VAPOR_RETARDER_CLASS_LIMITS_PERMS: tuple[tuple[float, str], ...] = (
    (0.1, "I"), (1.0, "II"), (10.0, "III"),
)


def vapor_retarder_class(permeance_perms: float | None) -> str | None:
    """The IRC R702.7.1 class of a layer at ``permeance_perms``, or None.

    None means "not a vapour retarder": either the permeance is unknown, or the layer is
    looser than 10 perm and the code does not rate it. Bare 5/8" gypsum board runs about
    30 perm and lands here — which is the point of modelling the paint over it, since
    R702.7 counts that film as the assembly's warm-side retarder.
    """
    if permeance_perms is None or permeance_perms < 0.0:
        return None
    for limit, name in VAPOR_RETARDER_CLASS_LIMITS_PERMS:
        if permeance_perms <= limit:
            return name
    return None

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


def _c_to_f(temperature_c: float) -> float:
    return temperature_c * _FAHRENHEIT_PER_CELSIUS + _FAHRENHEIT_FREEZING


def dew_point_f(temperature_f: float, relative_humidity: float) -> float:
    """Dew point of air at ``temperature_f`` and ``relative_humidity`` (0..1), in F.

    The Magnus curve above, inverted. This is the number every wet-room decision turns on:
    at 75 F / 70% RH it is 64.4 F, and every surface in the room colder than that is wet.
    """
    gamma = math.log(max(relative_humidity, 1e-6)) + (
        _MAGNUS_BETA * _f_to_c(temperature_f) / (_f_to_c(temperature_f) + _MAGNUS_LAMBDA_C)
    )
    return _c_to_f(_MAGNUS_LAMBDA_C * gamma / (_MAGNUS_BETA - gamma))


def glaser_layers(layers: list[Layer]) -> list[Layer]:
    """Truncate the stack at an exterior ventilated rainscreen cavity.

    A furring/airgap layer that sits outboard of the structure/sheathing/insulation is a
    drained-and-back-vented cavity open to outdoor air: everything from that plane outward
    (the vent and its cladding) is pressure-equalised with the exterior, so it carries no
    part of the interior-to-exterior vapor drive. Standard Glaser practice terminates the
    analysis there rather than modeling the cladding as a cold-side vapor trap. Assemblies
    with no such cavity (concrete, direct-applied finishes) walk their full depth.

    An *interior* service cavity — a furring/airgap layer with no wettable layer inboard of
    it — is deliberately NOT truncated, and the plant room's PVC liner gap is the case that
    tests the rule. It is tempting to call that gap "at room conditions" and start the walk
    at the membrane behind it, which would let the walk run without a permeance for the PVC
    panel. But a gap behind a tongue-and-groove liner is a closed cavity, not a vented one:
    nothing declares where it is open to, and the difference between "drains to the floor
    tray" and "communicates freely with room air" is the whole question. So the walk keeps
    the panel, and reports UNKNOWN naming it — which is the honest answer while no
    manufacturer in that product class publishes an ASTM E96 number.

    A furring band PACKED WITH INSULATION is not a vented cavity either, and a truss wall is
    the case that tests that rule. Its outrigger band is 3-1/2" deep with 2-1/2" of
    closed-cell foam behind the stick; only the outer 1" vents. Truncating at the band's
    inner face would drop most of the wall's exterior insulation out of the walk and read a
    4"-of-foam wall as a 1-1/2"-of-foam wall — which is a dew point at the stud that the
    real assembly does not have. So a band carrying a ``CavityFill`` is walked (parallel-
    pathed across its fill, like any other layer with one) and the vent plane is the *next*
    layer out. The same reasoning ``resolve/accessories.rainscreen_cavity_m`` applies to the
    insect closure at the bottom of that cavity: what vents is the unfilled remainder.
    """
    for index, layer in enumerate(layers):
        if layer.function not in _VENTED or not any(
            inner.function in _WETTABLE for inner in layers[:index]
        ):
            continue
        # An empty band vents over its whole depth, so the walk stops at its inner face. A
        # PARTLY filled band vents only the unfilled remainder in front of the fill, so the
        # walk keeps the band — parallel-pathed across its fill like any other layer with
        # one — and stops at its OUTER face. Stopping short of it would drop most of a truss
        # wall's exterior insulation; running past it would put the standing-seam cladding, a
        # perfect vapour barrier, on the cold side of a wall that is in fact back-vented to
        # outdoor air, and read a trap that is not there.
        #
        # A band filled SOLID is neither: nothing vents, so it is not a vent plane at all and
        # the walk must carry on past it to whatever really is. ``CavityFill.thickness``
        # defaults to the host layer's own depth, so "packed solid" is the *default* spelling
        # of a fill — without this guard a service chase stuffed with batt would truncate the
        # walk at its own outer face and hide every layer beyond it, which is the exact trap
        # the paragraph above claims to avoid.
        if layer.cavity is None:
            return layers[:index]
        if (layer.cavity.thickness or layer.thickness).meters < layer.thickness.meters - 1e-9:
            return layers[:index + 1]
        continue
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
    # The warm-side vapour retarder (IRC R702.7.1) this stack carries, if any: the layer's
    # name and its class. ``None`` means the interior face of the assembly is vapour-open —
    # nothing inboard of the structure is rated at 10 perm or tighter.
    interior_retarder_layer: str | None = None
    interior_retarder_class: str | None = None

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

    @property
    def interior_retarder_note(self) -> str:
        """One clause describing the warm-side retarder, for a finding message."""
        if self.interior_retarder_class is None:
            return "no rated warm-side vapour retarder (interior face vapour-open)"
        return (f"warm-side vapour retarder {self.interior_retarder_layer} is Class "
                f"{self.interior_retarder_class} (IRC R702.7.1)")

    def as_dict(self) -> dict[str, object]:
        tightest = self.tightest_plane
        return {
            "assembly": self.assembly_tag,
            "status": "unknown" if not self.known else "risk" if self.has_risk else "safe",
            "interior_retarder_layer": self.interior_retarder_layer,
            "interior_retarder_class": self.interior_retarder_class,
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


def layer_permeance_perms(layer: Layer, library: Library) -> float | None:
    """Installed permeance of one layer, in perms — or None when an input is missing.

    The public face of the same parallel-path walk :func:`_layer_path` does for the Glaser
    profile, so a rule about "is there a Class I layer here" and the profile that crosses
    it can never disagree about what a layer's permeance is. ``0.0`` means a sourced vapour
    barrier (infinite resistance); ``inf`` means a layer with no vapour resistance at all.
    """
    path, missing = _layer_path(layer, library)
    if path is None or missing:
        return None
    if math.isinf(path.vapor_resistance_rep):
        return 0.0
    if path.vapor_resistance_rep <= 0.0:
        return math.inf
    return 1.0 / path.vapor_resistance_rep


def _interior_retarder(layers: list[Layer],
                       paths: list[_LayerPath]) -> tuple[str | None, str | None]:
    """The warm-side vapour retarder of an interior→exterior stack: (layer name, class).

    "Warm-side" is the whole qualifier: a tight layer on the *cold* side is a vapour trap,
    not a retarder, and reporting it as one would read a hazard as a credit. The warm-side
    span therefore ends at the wall/roof core — the first STRUCTURE or SHEATHING layer —
    which keeps interior continuous insulation inside the span (foil-faced polyiso applied
    to the room side of a stud wall is the textbook Class I retarder, e.g. the sauna liner)
    while leaving exterior sheathing and exterior CI outside it. A stack with no core at all
    falls back to the first wettable layer, which credits nothing it cannot place.

    Within that span the tightest layer is the retarder, since it is the one the vapour
    drive actually has to cross. Bare gypsum (~30 perm at 5/8") is not rated by R702.7.1 and
    yields ``(None, None)`` — the paint over it is what earns the Class III.
    """
    warm_side = next((index for index, layer in enumerate(layers)
                      if layer.function in _CORE_PLANES), None)
    if warm_side is None:
        warm_side = next((index for index, layer in enumerate(layers)
                          if layer.function in _WETTABLE), len(layers))

    best_name: str | None = None
    best_class: str | None = None
    best_permeance = math.inf
    for layer, path in zip(layers[:warm_side], paths[:warm_side]):
        permeance = 0.0 if math.isinf(path.vapor_resistance_rep) else (
            1.0 / path.vapor_resistance_rep if path.vapor_resistance_rep > 0.0 else math.inf
        )
        rated = vapor_retarder_class(permeance)
        if rated is not None and permeance < best_permeance:
            best_name, best_class, best_permeance = layer.name, rated, permeance
    return best_name, best_class


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
    retarder_layer, retarder_class = _interior_retarder(layers, paths)
    return CondensationAnalysis(
        assembly_tag, tuple(points), crossing_layer=crossing_layer,
        crossing_fraction=crossing_fraction, plane_names=plane_names,
        interior_retarder_layer=retarder_layer, interior_retarder_class=retarder_class,
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


@dataclass(frozen=True)
class MonthlyAssessment:
    """The worst month of twelve steady-state walks — the ISO 13788-style gate result.

    ``analysis`` is the full :class:`CondensationAnalysis` for ``month`` (the month whose
    tightest plane runs closest to — or past — saturation). The design-hour walk stays a
    cold-snap *screen*; this monthly reduction over published climate normals is the
    pass/fail *gate*, because a seasonal mean is the condition an assembly actually has to
    dry against, not a 99%-percentile snap.
    """

    month: str
    normal: MonthlyNormal
    analysis: CondensationAnalysis

    @property
    def boundary(self) -> str:
        """The exterior boundary condition the worst-month profile was run against."""
        return f"{self.normal.temp_f:.1f} F / {self.normal.rh:.0f}% RH ({self.month} normals)"


def analyze_layers_monthly(
    assembly_tag: str, layers: list[Layer], library: Library, *,
    monthly_normals: tuple[MonthlyNormal, ...], interior_setpoint_f: float,
    interior_relative_humidity: float,
) -> MonthlyAssessment | None:
    """Run :func:`analyze_layers` once per month and keep the worst month.

    Pure reducer over the pure profile walk: each month's normals (mean outdoor dry-bulb +
    mean RH, January..December) are one steady-state boundary condition; the worst month is
    the one whose tightest plane carries the highest local relative humidity, which ranks a
    crossing (local RH >= 1) above every safe month automatically. Returns ``None`` when
    ``monthly_normals`` does not hold twelve months — the gate is then not evaluable and
    the caller reports the missing input by name rather than gating on partial data.
    """
    if len(monthly_normals) != 12:
        return None
    worst: MonthlyAssessment | None = None
    worst_rh = -1.0
    for month_name, normal in zip(MONTH_NAMES, monthly_normals):
        analysis = analyze_layers(
            assembly_tag, layers, library, heating_design_temp_f=normal.temp_f,
            interior_setpoint_f=interior_setpoint_f,
            interior_relative_humidity=interior_relative_humidity,
            exterior_relative_humidity=normal.rh / 100.0,
        )
        if not analysis.known:  # same layers every month — missing inputs are identical
            return MonthlyAssessment(month_name, normal, analysis)
        tightest = analysis.tightest_plane
        local_rh = tightest.local_relative_humidity if tightest is not None else 0.0
        if local_rh > worst_rh:
            worst, worst_rh = MonthlyAssessment(month_name, normal, analysis), local_rh
    return worst


def analyze_assembly_monthly(
    assembly: Assembly, library: Library, *,
    monthly_normals: tuple[MonthlyNormal, ...], preferences: Preferences,
) -> MonthlyAssessment | None:
    """Worst-month Glaser assessment for ``assembly`` (the monthly condensation gate)."""
    layers = glaser_layers(list(assembly.default_lining) + list(assembly.layers))
    return analyze_layers_monthly(
        assembly.tag, layers, library, monthly_normals=monthly_normals,
        interior_setpoint_f=preferences.interior_setpoint_f,
        interior_relative_humidity=preferences.monthly_interior_relative_humidity,
    )
