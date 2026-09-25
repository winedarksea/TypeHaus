"""A transparent block-load estimate, not a replacement for Manual J (M5 WP5.3).

The arithmetic only: exposed UA by component, orientation-weighted window solar gain, and
the two air-side terms (blower-door infiltration, ERV ventilation air). What counts as
envelope is answered in ``envelope_geometry``, how much of a plane a zone owns in
``energy_scope``, and what a below-grade surface's conductance and ΔT are in ``ground`` —
this module takes those answers and sums them.

Every area comes from the resolved IR. A missing U-factor or R-value is named in
``EnergyReport.unknown_inputs`` and dropped from the sum, never replaced by a rule of
thumb: a load that silently invented an input is a load nobody can size equipment against.

**The heating total used to be right only by cancellation.** Every component line was wrong,
in both directions, by 0.5-2.0 kBtu/h, and the sum survived review while none of its parts
would have. What moved, and where the derivation for each lives:

* Envelope scope is derived, not read off this house's tag prefixes → ``envelope_geometry``.
* A raked gable wall is a trapezoid, not a prism. ``length x (z1 - z0)`` ignored
  ``top_z0_m``/``top_z1_m`` and billed catlin's attic gables 657.6 sf against 414.0 sf real.
* A below-grade wall's conductance rises with depth and its ΔT is to the ground SURFACE at
  its design-hour minimum, not to the annual mean → ``ground``.
* A wall is split at its LOCAL grade, not at the global ``Site.grade`` plane, which buried
  1.73 m of open-air walkout wall in soil ΔT → ``resolve.site_earth.strip_grade_elevation_m``.
* Cooling ΔT is to a 75 °F cooling setpoint, not to the 70 °F heating one.
* The air side carries the LBL table's N (not its two-storey cell as a flat default), the
  heating design-hour uplift over Sherman's annual-average N, and an altitude correction.

Solar is deliberately NOT touched here: the orientation weights are wrong, but the term is
71% of the cooling load and a partial fix moves it the WRONG way — raising E/W without
adding shading or fixing the all-orientations-peak-at-once error makes the number worse.
It changes exactly once, with the hourly method, in ``solar``.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.analysis import assembly_r_value
from typehaus.checks.building_science.energy_scope import (
    _M2_TO_FT2,
    _conditioned_rooms,
    _opening_in_scope,
    _polygon_scope_fraction,
    _room_scope,
    _storey_is_conditioned,
    _volume_ft3,
    _wall_scope_fraction,
)
from typehaus.checks.building_science.ground import (
    basement_floor_u,
    basement_wall_u_avg,
    ground_design_temp_f,
    ground_summer_temp_f,
    slab_on_grade_f_factor,
    slab_on_grade_q,
)
from typehaus.checks.building_science.solar import (
    fenestration_gain,
    horizontal_surface_irradiance,
    internal_gains,
    roof_absorptance,
    sol_air_temperature_f,
)
from typehaus.checks.building_science.wwr import _wall_length
from typehaus.checks.registry import Preferences
from typehaus.resolve.envelope_geometry import envelope_geometry
from typehaus.resolve.geometry import polygon_area
from typehaus.resolve.model import ResolvedModel, ResolvedWall
from typehaus.resolve.site_earth import (
    heated_floor_footprint,
    local_grade_elevation_m,
    open_excavation_floors,
    strip_grade_elevation_m,
)
from typehaus.resolve.solid_categories import is_pour_slab

# Component kinds whose exterior boundary is the ground, not the outdoor design air.
# ``foundation_walls_above_grade`` is deliberately NOT here: the band of a foundation wall
# that stands proud of its local grade sees weather, and on catlin's walkout that band is
# 251 sf of it.
_GROUND_COUPLED_KINDS = ("foundation_walls", "slab")

# Sensible heat of air at sea level: 0.075 lb/ft3 × 0.24 Btu/lb·°F × 60 min/h.
_AIR_SENSIBLE_BTU_PER_CFM_F = 1.08

# Sherman's N yields an ANNUAL AVERAGE infiltration rate; a design-hour load wants the
# design-hour rate. ACCA Manual J Table 5 / ASHRAE: below four storeys the heating design
# rate is about 1.5× the annual average (the design hour is the coldest and windiest of the
# year, which is what drives stack and wind pressure) and the cooling design rate is about
# 0.84× it (a summer design hour is nearly still). Applied to infiltration only — an ERV's
# airflow is a machine setting and does not move with the weather.
_HEATING_DESIGN_INFILTRATION_UPLIFT = 1.5
_COOLING_DESIGN_INFILTRATION_UPLIFT = 0.84

# LBL N-factor table (Sherman & Grimsrud), as ``base × height × shielding``. The flat 18.0
# this replaced is the two-storey / normal-shelter cell — one entry read as the whole table.
_LBL_N_BASE = 18.5
_LBL_N_HEIGHT = {1.0: 1.0, 1.5: 0.9, 2.0: 0.8, 3.0: 0.7}
# Shielding is read off ``Site.wind_exposure``, which a house already authors for wind:
# ASCE 7 §26.7.3's B (suburban/wooded), C (open terrain) and D (open water) are the same
# three surroundings the LBL shielding classes name, so there is nothing new to keep in sync.
_LBL_N_SHIELDING = {"B": 1.2, "C": 1.0, "D": 0.9}


def altitude_correction_factor(elevation_ft: float) -> float:
    """Air-density correction on the 1.08 sensible factor (barometric, standard atmosphere).

    ``(1 - 6.8754e-6 · z)^5.2559``. 0.97 at catlin's 830 ft: thinner air carries 3% less
    heat per CFM, which is a 3% error on both air-side terms that nothing corrected.
    """
    return max(0.0, 1.0 - 6.8754e-6 * elevation_ft) ** 5.2559


def _n_factor(
    preferences: Preferences, wind_exposure: str | None, unknown: list[str],
) -> float | None:
    """The LBL divisor: authored if the house states one, else read off the table."""
    if preferences.infiltration_n_factor is not None:
        if preferences.infiltration_n_factor <= 0:
            unknown.append("Preferences infiltration_n_factor (must be > 0)")
            return None
        return preferences.infiltration_n_factor
    storeys = preferences.infiltration_storeys
    height = _LBL_N_HEIGHT.get(storeys) if storeys is not None else None
    if height is None:
        unknown.append("Preferences infiltration_storeys (LBL height correction; "
                       f"one of {sorted(_LBL_N_HEIGHT)})")
        return None
    # Shielding defaults to the table's own REFERENCE condition (1.0, "normal"), which is
    # declining to apply a correction rather than inventing a value — unlike the height
    # correction above, where 1.0 would be the positive claim "one storey".
    shielding = _LBL_N_SHIELDING.get(wind_exposure or "", 1.0)
    return _LBL_N_BASE * height * shielding


def _infiltration_cfm(
    preferences: Preferences, volume_ft3: float, unknown: list[str],
    n_factor: float | None = None,
) -> float:
    """Natural-condition infiltration airflow from the authored blower-door result.

    ``cfm50`` is the measurement; ``ach50`` is the same fact normalized by volume, so it
    only becomes a CFM once there is a conditioned volume to multiply. Neither authored
    means the term is *unknown*, not zero — it is named and dropped, never guessed at from
    a leakage rule of thumb.
    """
    cfm50 = preferences.cfm50
    if cfm50 is None and preferences.ach50 is not None:
        if volume_ft3 <= 0:
            unknown.append("conditioned volume (no resolved conditioned rooms) — "
                           "ach50 cannot be converted to CFM50")
            return 0.0
        cfm50 = preferences.ach50 * volume_ft3 / 60.0
    if cfm50 is None:
        unknown.append("Preferences ach50/cfm50 (infiltration term omitted)")
        return 0.0
    if n_factor is None or n_factor <= 0:
        return 0.0  # the gap is already named by ``_n_factor``
    return cfm50 / n_factor


def _ventilation_cfm(model: ResolvedModel, unknown: list[str]) -> float:
    """Continuous ventilation air that still has to be tempered, net of sensible recovery.

    Summed over the authored ERV/HRV ``Equipment`` — a house with none authored moves no
    mechanical ventilation air, which is a fact read off the model rather than a missing
    input, so it stays silent. An ERV that *is* authored but whose type states no airflow or
    no recovery effectiveness is a real gap and is named.
    """
    types = {item.tag: item for item in model.plan.library.equipment_types}
    net_cfm = 0.0
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "Equipment" or element.kind.value != "erv":
                continue
            product = types.get(element.type_ref)
            cfm = getattr(product, "ventilation_cfm", None)
            effectiveness = getattr(product, "sensible_recovery_effectiveness", None)
            if cfm is None or effectiveness is None:
                unknown.append(f"{element.tag} ventilation_cfm / "
                               "sensible_recovery_effectiveness")
                continue
            net_cfm += cfm * (1.0 - effectiveness)
    return net_cfm


@dataclass(frozen=True)
class LoadComponent:
    kind: str
    area_ft2: float
    ua_btu_per_hour_f: float
    solar_gain_btu_per_hour: float = 0.0
    # The heating ΔT this component's UA was multiplied by: below-grade components
    # (foundation walls, slabs) see the soil temperature, not the 99% design air.
    heating_delta_f: float | None = None

    def as_dict(self) -> dict[str, float | str | None]:
        return {"kind": self.kind, "area_ft2": self.area_ft2,
                "ua_btu_per_hour_f": self.ua_btu_per_hour_f,
                "solar_gain_btu_per_hour": self.solar_gain_btu_per_hour,
                "heating_delta_f": self.heating_delta_f}


@dataclass(frozen=True)
class EnergyReport:
    heating_load_btu_per_hour: float
    cooling_load_btu_per_hour: float
    cooling_tons: float
    components: tuple[LoadComponent, ...]
    wall_comparison: dict[str, float | str] | None = None
    unknown_inputs: tuple[str, ...] = ()
    # The two air-side heating terms, reported separately because they are not UA against an
    # area and so cannot be carried as ``LoadComponent``s. Both are already included in
    # ``heating_load_btu_per_hour``.
    infiltration_btu_per_hour: float = 0.0
    ventilation_btu_per_hour: float = 0.0
    # The cooling side's own three terms, reported apart from the components for the same
    # reason: none of them is a UA against an area.
    #
    # ``cooling_load_btu_per_hour`` is SENSIBLE and stays sensible — that is the quantity a
    # unit's ``cooling_capacity_btuh`` is rated against. ``latent_btu_per_hour`` is the
    # moisture side, and ``cooling_tons`` is the TOTAL (sensible + latent) over 12,000,
    # because a ton of refrigeration is a total, not a sensible.
    latent_btu_per_hour: float = 0.0
    #: Fenestration gain at the house's own peak solar hour (→ ``solar``), and that hour.
    #: Already inside ``cooling_load_btu_per_hour``; carried so the sheet can print WHEN.
    solar_btu_per_hour: float = 0.0
    solar_peak_hour: float | None = None
    #: The AED excursion (ACCA TRB 2003-001a), also already inside the cooling load.
    solar_excursion_btu_per_hour: float = 0.0
    #: Internal gains, cooling only — Manual J credits none against heating and nor does
    #: this. Both already inside their respective totals.
    internal_sensible_btu_per_hour: float = 0.0
    #: Caveats a reader must see beside the number, distinct from ``unknown_inputs``: these
    #: are terms the method knowingly does not carry, not inputs it is missing. The sizing
    #: checks print them, so the number never travels without them.
    cooling_caveats: tuple[str, ...] = ()

    @property
    def sensible_heat_ratio(self) -> float | None:
        """``sensible / (sensible + latent)``, or ``None`` with no cooling load at all."""
        total = self.cooling_load_btu_per_hour + self.latent_btu_per_hour
        return None if total <= 0 else self.cooling_load_btu_per_hour / total

    def as_dict(self) -> dict[str, object]:
        return {"heating_load_btu_per_hour": self.heating_load_btu_per_hour,
                "cooling_load_btu_per_hour": self.cooling_load_btu_per_hour,
                "latent_btu_per_hour": self.latent_btu_per_hour,
                "sensible_heat_ratio": self.sensible_heat_ratio,
                "cooling_tons": self.cooling_tons,
                "components": [component.as_dict() for component in self.components],
                "infiltration_btu_per_hour": self.infiltration_btu_per_hour,
                "ventilation_btu_per_hour": self.ventilation_btu_per_hour,
                "solar_btu_per_hour": self.solar_btu_per_hour,
                "solar_peak_hour": self.solar_peak_hour,
                "solar_excursion_btu_per_hour": self.solar_excursion_btu_per_hour,
                "internal_sensible_btu_per_hour": self.internal_sensible_btu_per_hour,
                "cooling_caveats": list(self.cooling_caveats),
                "wall_comparison": self.wall_comparison,
                "unknown_inputs": list(self.unknown_inputs),
                "scope": "resolved walls, foundations, roof, slabs, windows, and doors, "
                         "plus blower-door infiltration and ERV ventilation air, hourly "
                         "fenestration gain at the house's peak solar hour with its AED "
                         "excursion, the roof's sol-air excess where an absorptance is "
                         "stated, and Manual J occupant/appliance internal gains"}


def estimate_block_load(
    model: ResolvedModel, preferences: Preferences,
    storeys: frozenset[str] | None = None,
    rooms: frozenset[str] | None = None,
) -> EnergyReport:
    """Sum exposed resolved wall/opening UA plus orientation-weighted window solar gain,
    then the two air-side terms: blower-door infiltration and ERV ventilation air.

    Every area comes from the resolved IR.  Missing geometry or thermal data remains named
    UNKNOWN rather than being replaced by a rule-of-thumb area or U-factor.

    ``storeys`` restricts the sum to a subset of the conditioned storeys; ``rooms``
    restricts it to a set of room tags (an ``Equipment.zone_rooms`` zone, per
    ``checks.mep.hvac.heating_capacity``); ``None``/``None`` keeps the whole-house behavior.
    Zone loads ignore floors between zones at the same setpoint, so per-zone results sum
    (up to the shared ``wall_comparison``) to the whole-house block load.

    **Room-scoped results are approximate by design.** Envelope planes are attributed by
    plan overlap — the fraction of a wall's run that bounds the zone's rooms, the fraction
    of a roof/slab outline over them — and the air-side terms are apportioned by the zone's
    share of conditioned volume. That is a zone load good enough to size a head against, not
    a Manual J room-by-room calculation: it carries no room-level internal gains, no duct
    losses, and no per-room ceiling planes.
    """
    site = model.plan.project.site
    if site.design_temp_heating is None or site.design_temp_cooling is None:
        return EnergyReport(0.0, 0.0, 0.0, (), unknown_inputs=("Site design temperatures",))
    components: list[LoadComponent] = []
    unknown: list[str] = []
    # Terms the method knowingly does not carry, as opposed to inputs it is missing. The
    # sizing checks print these beside the number so it never travels without them.
    cooling_caveats: list[str] = []
    heating_delta = preferences.interior_setpoint_f - site.design_temp_heating.fahrenheit
    # Manual J's cooling indoor design condition is 75 °F, not the heating setpoint. One
    # ``interior_setpoint_f`` for both seasons made catlin's cooling ΔT 20 where it is 15.
    cooling_delta = site.design_temp_cooling.fahrenheit - preferences.cooling_setpoint_f
    # Below-grade components are ground-coupled, and the boundary is the ground SURFACE at
    # the bottom of its annual swing, not the annual mean (→ ``ground``). With the swing
    # unauthored the air ΔT stands in and the gap is named, which is conservative: the air
    # is colder than the ground at the design hour, so the term oversizes rather than under.
    ground_design_f, ground_gap = ground_design_temp_f(
        site.monthly_normals, site.ground_surface_amplitude_f)
    ground_summer_f, _ = ground_summer_temp_f(
        site.monthly_normals, site.ground_surface_amplitude_f)
    ground_temperature_gap: str | None = None
    if ground_design_f is None or ground_summer_f is None:
        # Named only if a ground-coupled component actually turns up (below), the way
        # ``Site.soil_temp_f`` was: a single-storey slab-less house has no below-grade
        # surface for the gap to be a gap ABOUT, and reporting one there is noise.
        ground_heating_delta, ground_cooling_delta = heating_delta, cooling_delta
        if ground_gap is not None:
            ground_temperature_gap = (
                f"{ground_gap} — below-grade surfaces use outdoor design air ΔT")
    else:
        ground_heating_delta = preferences.interior_setpoint_f - ground_design_f
        ground_cooling_delta = max(0.0, ground_summer_f - preferences.cooling_setpoint_f)
        # A free self-check, and it is free because the house authored the answer already:
        # ``soil_temp_f`` IS the annual mean the swing is taken about, and a house whose
        # hand-computed figure disagrees with its own twelve normals has one of the two
        # wrong. Named, not silently overridden — the engine does not know which.
        derived_mean = ground_design_f + (site.ground_surface_amplitude_f or 0.0)
        if (site.soil_temp_f is not None
                and abs(site.soil_temp_f - derived_mean) > _SOIL_TEMP_AGREEMENT_F):
            unknown.append(
                f"Site.soil_temp_f {site.soil_temp_f:.1f} °F disagrees with the annual mean "
                f"of Site.monthly_normals ({derived_mean:.2f} °F)")

    def _deltas_for(kind: str) -> tuple[float, float]:
        if kind in _GROUND_COUPLED_KINDS:
            return ground_heating_delta, ground_cooling_delta
        return heating_delta, cooling_delta

    conditioned_storeys = {storey.tag for storey in model.plan.storeys
                           if _storey_is_conditioned(model.plan, storey.tag)}
    if storeys is not None:
        conditioned_storeys &= storeys
    # A room zone implies its storeys: a zone spanning two levels is scoped by its rooms,
    # and no envelope on a storey it does not reach can belong to it.
    scope = None
    if rooms is not None:
        scope = _room_scope(model, rooms)
        conditioned_storeys &= set(scope)
    geometry = envelope_geometry(model)
    envelope_walls = [wall for wall in model.walls
                      if wall.storey in conditioned_storeys
                      and geometry.is_envelope_wall(wall)]
    wall_fraction = {wall.tag: _wall_scope_fraction(wall, scope) for wall in envelope_walls}
    envelope_walls = [wall for wall in envelope_walls if wall_fraction[wall.tag] > 0.0]
    wall_by_tag = {wall.tag: wall for wall in envelope_walls}
    # An opening is discrete: it belongs wholly to the zone its own plan point stands in,
    # never split by a fraction, so a window is never counted twice across zones.
    # ``not is_blind``: a blind recess has no area in the envelope and no U-factor to give
    # it. Counted here it would be deducted from its wall's opaque area and billed back at
    # ``preferences.window_u``, which is the opposite of what a pocket behind brick does —
    # the exterior foam runs continuous past it.
    envelope_openings = [opening for opening in model.openings
                         if opening.host_wall in wall_by_tag and not opening.is_blind
                         and _opening_in_scope(wall_by_tag[opening.host_wall], opening, scope)]
    opening_area_ft2: dict[str, float] = {wall.tag: 0.0 for wall in envelope_walls}
    for opening in envelope_openings:
        opening_area_ft2[opening.host_wall] = opening_area_ft2.get(opening.host_wall, 0.0) + (
            opening.width_m * opening.height_m * _M2_TO_FT2
        )
    # Fenestration gain is an HOURLY walk with ONE peak hour for the whole house (→
    # ``solar``), and it is taken here rather than in the opening loop below because the
    # roof's sol-air term is evaluated at the same hour: the peak cooling condition is one
    # instant, and charging the glass its peak and the roof its own separate peak is the
    # every-orientation-peaks-at-once error in a different dress.
    solar = fenestration_gain(model, wall_by_tag, envelope_openings)
    solar_peak_hour = solar.peak_hour
    unknown.extend(solar.unknown_inputs)

    # The excavation floors and the heated footprint are whole-model facts; derived once
    # here rather than per wall, because ``open_excavation_floors`` walks every solid.
    floors = open_excavation_floors(model)
    sheltered = heated_floor_footprint(model)
    above_area = above_ua = below_area = below_ua = 0.0
    foundation_above_area = foundation_above_ua = 0.0
    for wall in envelope_walls:
        assembly = model.plan.library.resolve_assembly(wall.assembly)
        if assembly is None:
            unknown.append(f"assembly {wall.assembly}")
            continue
        r_value = assembly_r_value(assembly, model.plan.library)
        if r_value.value is None or r_value.value.r_us <= 0:
            unknown.extend(r_value.unknown_materials or (f"R-value {assembly.tag}",))
            continue
        r_us = r_value.value.r_us
        buffer_room = geometry.buffer_adjacent(wall)
        if buffer_room is not None:
            unknown.append(
                f"buffer temperature for {buffer_room} ({wall.tag} bounds it) — charged the "
                "full outdoor design ΔT, which oversizes rather than undersizes")
        # Grade is read off a strip swept from THIS wall's exterior face, never off the
        # global plane: catlin's W-B-S2-FR/W-B-S3-FR span to -2.596 m with the sunken court
        # floor at -2.869, and the global -0.864 buries 1.73 m of open-air walkout wall in
        # soil ΔT — a 3.7x understatement on the very walls the scope fix has just added.
        strip = geometry.exterior_grade_strip(wall)
        grade_z = (strip_grade_elevation_m(model, strip, floors)[0] if strip is not None
                   else local_grade_elevation_m(model, [], floors=floors,
                                                sheltered_by=sheltered)[0])
        length_m = _wall_length(wall)
        top_z = _wall_top_z_m(wall)
        gross_ft2 = max(0.0, length_m * (top_z - wall.z0_m)) * _M2_TO_FT2
        split_z = min(max(grade_z, wall.z0_m), top_z)
        below_ft2 = max(0.0, length_m * (split_z - wall.z0_m)) * _M2_TO_FT2
        above_ft2 = max(0.0, gross_ft2 - below_ft2)
        # Openings come off the ABOVE-grade band first: a window is in the part of the wall
        # that is out of the ground. Only the remainder spills below, which is the honest
        # answer for a walkout whose door head is above its own local grade.
        holes = opening_area_ft2.get(wall.tag, 0.0)
        above_net = max(0.0, above_ft2 - holes)
        below_net = max(0.0, below_ft2 - max(0.0, holes - above_ft2))
        fraction = wall_fraction[wall.tag]
        above_net *= fraction
        below_net *= fraction
        if below_net > 0:
            # Latta: the soil path lengthens with depth, so the conductance is a depth
            # average over the buried band, not ``1 / r_us``.
            depth_ft = (split_z - wall.z0_m) / 0.3048
            below_area += below_net
            below_ua += below_net * basement_wall_u_avg(r_us, depth_ft)
        if above_net > 0:
            if wall.is_foundation:
                foundation_above_area += above_net
                foundation_above_ua += above_net / r_us
            else:
                above_area += above_net
                above_ua += above_net / r_us

    def _component(kind: str, area: float, ua: float,
                   solar: float = 0.0) -> LoadComponent:
        return LoadComponent(kind, area, ua, solar, heating_delta_f=_deltas_for(kind)[0])

    components.append(_component("walls", above_area, above_ua))
    if below_area:
        components.append(_component("foundation_walls", below_area, below_ua))
    if foundation_above_area:
        # A third wall component, not a line folded into ``walls``: the band of a foundation
        # wall standing proud of its own local grade sees air, and keeping it separate also
        # keeps the ``walls.area_ft2 <= clad_wall_area_ft2`` bound the energy-sheet test
        # asserts honest — a bare concrete band carries no cladding.
        components.append(_component("foundation_walls_above_grade",
                                     foundation_above_area, foundation_above_ua))

    roof_area = roof_ua = slab_area = slab_ua = 0.0
    slab_on_grade_heating = slab_on_grade_cooling = slab_on_grade_perimeter = 0.0
    roofs = [roof for roof in model.roofs if roof.storey in conditioned_storeys
             and geometry.is_envelope_roof(roof)[0]]
    slabs = [solid for solid in model.solids
             if is_pour_slab(solid.category) and solid.storey in conditioned_storeys
             and geometry.is_envelope_slab(solid)[0]]
    roof_fraction = {roof.tag: _polygon_scope_fraction(roof.footprint, roof.storey, scope)
                     for roof in roofs}
    slab_fraction = {slab.tag: _polygon_scope_fraction(slab.outline, slab.storey, scope)
                     for slab in slabs}
    roofs = [roof for roof in roofs if roof_fraction[roof.tag] > 0.0]
    slabs = [slab for slab in slabs if slab_fraction[slab.tag] > 0.0]
    has_roofs = bool(roofs)
    has_slabs = bool(slabs)
    # A *zone* legitimately lacks a roof or a slab when that boundary is an interior floor
    # against another conditioned zone at the same setpoint, so the missing-geometry
    # diagnostics only apply to the whole-house sum.
    whole_house = storeys is None and rooms is None
    if whole_house:
        if not has_roofs and not has_slabs:
            # Keep the original combined diagnostic stable for existing consumers while
            # still reporting the missing side precisely when only one is absent.
            unknown.append("roof/slab resolved geometry")
        elif not has_roofs:
            unknown.append("roof resolved geometry")
    for roof in roofs:
        r_value = _assembly_r_value(model, roof.assembly, unknown)
        if r_value is not None:
            area = roof.surface_area_m2 * _M2_TO_FT2 * roof_fraction[roof.tag]
            roof_area += area
            roof_ua += area / r_value
        under = geometry.is_envelope_roof(roof)[1]
        if "buffer" in under:
            unknown.append(f"buffer temperature under {roof.tag} ({under}) — charged the "
                           "full outdoor design ΔT")
    # A roof is solar-dominated and nearly ΔT-independent, so its cooling term is a SOL-AIR
    # excess over the air ΔT, not the air ΔT. Gated on an authored ``solar_absorptance``,
    # which is a published optical property nobody has stated for catlin's roofing: with
    # none the roof carries the plain air ΔT (the behaviour this replaced) and the caveat
    # is CARRIED IN THE MESSAGE rather than in ``unknown_inputs``, because an omitted
    # refinement is not a missing required input and must not take the sizing verdict to
    # UNKNOWN over it.
    roof_sol_air_cooling = 0.0
    if roof_area:
        components.append(_component("roof", roof_area, roof_ua))
        absorptances = {roof.tag: roof_absorptance(model, roof.assembly) for roof in roofs}
        unstated = sorted(tag for tag, value in absorptances.items() if value is None)
        if unstated:
            cooling_caveats.append(
                "the roof carries no sol-air term — no solar_absorptance is authored on "
                f"the outermost layer of {', '.join(unstated)}, so it is charged the plain "
                "air ΔT and its cooling contribution is understated several-fold")
        for roof in roofs:
            absorptance = absorptances.get(roof.tag)
            if absorptance is None:
                continue
            irradiance = horizontal_surface_irradiance(site.lat, solar_peak_hour)
            sol_air = sol_air_temperature_f(
                site.design_temp_cooling.fahrenheit, absorptance, irradiance)
            area = roof.surface_area_m2 * _M2_TO_FT2 * roof_fraction[roof.tag]
            roof_r = _assembly_r_value(model, roof.assembly, unknown)
            if roof_r is None:
                continue
            excess = max(0.0, (sol_air - preferences.cooling_setpoint_f) - cooling_delta)
            roof_sol_air_cooling += (area / roof_r) * excess
    if not slabs and has_roofs and whole_house:
        unknown.append("slab resolved geometry")
    for slab in slabs:
        if slab.assembly is None:
            unknown.append(f"slab {slab.tag} assembly")
            continue
        slab_r = _assembly_r_value(model, slab.assembly, unknown)
        if slab_r is None:
            continue
        area = (abs(polygon_area(slab.outline)) * _M2_TO_FT2 * slab_fraction[slab.tag])
        grade_z = local_grade_elevation_m(model, slab.outline, floors=floors,
                                          sheltered_by=sheltered)[0]
        depth_ft = (grade_z - slab.z1_m) / 0.3048
        if depth_ft > _SLAB_BELOW_GRADE_MIN_FT:
            # A below-grade floor: the soil is most of the resistance, and how much depends
            # on the floor's shortest plan dimension and its depth (→ ``ground``). Billing
            # ``A / r_assembly`` against a soil ΔT overstated catlin's basement floor ~2x.
            short_ft = _short_plan_dimension_ft(slab.outline)
            slab_area += area
            slab_ua += area * basement_floor_u(slab_r, short_ft, depth_ft)
        else:
            # A slab on grade loses heat around its EDGE, which is why every standard
            # publishes it as an F-factor per linear foot against outdoor design air — not
            # as an area against soil. Nothing in this model carries slab-edge insulation
            # as a number, so the F-factor is a named gap rather than an invented row.
            # catlin has no slab on grade inside its envelope; this is here so the first
            # house that does gets a gap instead of a ~2-10x understatement.
            perimeter_ft = _plan_perimeter_ft(slab.outline) * slab_fraction[slab.tag]
            f_factor, gap = slab_on_grade_f_factor(_slab_edge_r(model, slab))
            if f_factor is None:
                unknown.append(f"slab {slab.tag}: {gap}")
                continue
            slab_on_grade_perimeter += perimeter_ft
            slab_on_grade_heating += slab_on_grade_q(perimeter_ft, f_factor, heating_delta)
            slab_on_grade_cooling += slab_on_grade_q(perimeter_ft, f_factor, cooling_delta)
        buffered = geometry.is_envelope_slab(slab)[1]
        if "buffer" in buffered:
            unknown.append(f"buffer temperature across {slab.tag} ({buffered}) — charged "
                           "the full outdoor design ΔT")
    if slab_area:
        components.append(_component("slab", slab_area, slab_ua))
    if ground_temperature_gap is not None and (below_area or slab_area):
        unknown.append(ground_temperature_gap)
    if slab_on_grade_perimeter:
        # An F-factor is Btu/h per LINEAR FOOT per °F, so it cannot ride in
        # ``ua_btu_per_hour_f`` beside an area conductance without lying about what the
        # column means. It is carried as its own component with the perimeter in
        # ``area_ft2`` and the loss already multiplied out, and ``heating_delta_f`` states
        # the air ΔT it was taken at so the sheet still reads term by term.
        components.append(LoadComponent(
            "slab_on_grade_edge", slab_on_grade_perimeter, 0.0,
            solar_gain_btu_per_hour=0.0, heating_delta_f=heating_delta))

    window_area = window_ua = door_area = door_ua = 0.0
    for opening in envelope_openings:
        if opening.penetration_for:
            # A duct/pipe penetration is not fenestration: the hole is filled by the run and
            # its exterior hood, so there is no glass to state an SHGC about and no leaf to
            # give a U-factor. Billing it as a window at ``preferences.window_u`` would be
            # inventing a product, and demanding an SHGC takes the whole block load to
            # UNKNOWN over a 0.34 sf hole. Its real UA belongs to the duct and the hood,
            # which this model does not carry — so it is DROPPED here, deliberately, and the
            # envelope is understated by that much.
            continue
        area = opening.width_m * opening.height_m * _M2_TO_FT2
        if opening.is_door:
            kind, product = "doors", next((d for d in model.plan.library.door_types
                                             if d.tag == opening.type_ref), None)
        else:
            kind, product = "windows", next((w for w in model.plan.library.window_types
                                               if w.tag == opening.type_ref), None)
        u_factor = (
            product.u_factor.u_us
            if product is not None and product.u_factor is not None else None
        )
        if u_factor is None and kind == "windows":
            u_factor = preferences.window_u
        if u_factor is None:
            unknown.append(f"{kind} {opening.tag} U-factor")
            continue
        if kind == "doors":
            door_area += area
            door_ua += area * u_factor
        else:
            window_area += area
            window_ua += area * u_factor
    # No per-component ``solar_gain_btu_per_hour`` any more: the answer is not separable
    # per facade at a single hour the way a weighted sum pretended — the east glass's
    # contribution AT THE HOUSE'S PEAK HOUR is not the east glass's own peak — so it is one
    # house-level term (``EnergyReport.solar_btu_per_hour``) taken above.
    components.extend((_component("windows", window_area, window_ua),
                       _component("doors", door_area, door_ua)))
    # Air-side terms. Both the blower-door result and the ERV's airflow are whole-house
    # facts, so a zone gets its share of each by conditioned volume — the quantity the air
    # in a zone actually scales with.
    whole_volume_ft3 = _volume_ft3(model, _conditioned_rooms(model, None, None))
    zone_volume_ft3 = (whole_volume_ft3 if whole_house else
                       _volume_ft3(model, _conditioned_rooms(model, storeys, rooms)))
    share = 1.0 if whole_house else (
        zone_volume_ft3 / whole_volume_ft3 if whole_volume_ft3 > 0 else 0.0)
    n_factor = _n_factor(preferences, site.wind_exposure, unknown)
    infiltration_cfm = _infiltration_cfm(
        preferences, whole_volume_ft3, unknown, n_factor) * share
    ventilation_cfm = _ventilation_cfm(model, unknown) * share
    # Thinner air carries less heat per CFM. 0.97 at catlin's 830 ft — a 3% error on both
    # air-side terms that the flat 1.08 could not express.
    air_sensible = _AIR_SENSIBLE_BTU_PER_CFM_F * altitude_correction_factor(
        site.elevation.feet)
    # Sherman's N is an annual average; the design hour is the year's coldest and windiest.
    infiltration_heating = (air_sensible * infiltration_cfm
                            * _HEATING_DESIGN_INFILTRATION_UPLIFT * heating_delta)
    ventilation_heating = air_sensible * ventilation_cfm * heating_delta
    air_cooling = air_sensible * cooling_delta * (
        infiltration_cfm * _COOLING_DESIGN_INFILTRATION_UPLIFT + ventilation_cfm)

    heating = (sum(component.ua_btu_per_hour_f * _deltas_for(component.kind)[0]
                   for component in components)
               + slab_on_grade_heating + infiltration_heating + ventilation_heating)
    # Internal gains are COOLING ONLY. Manual J credits none against a heating load and
    # neither does this: a design heating hour is 4 a.m. in January with the house asleep
    # and the appliances off, and crediting people against it is how a system ends up unable
    # to recover from a setback. Apportioned to a zone by conditioned-volume share, the same
    # way the air-side terms are — the alternative is a per-room occupant census the model
    # does not carry.
    gains = internal_gains(model)
    internal_sensible = gains.sensible_btu_per_hour * share
    internal_latent = gains.latent_btu_per_hour * share
    # Latent is OCCUPANTS ONLY, and the two air-side latent terms are named rather than
    # guessed: an infiltration or ventilation latent load needs the cooling design
    # outdoor HUMIDITY RATIO, and nothing on ``Site`` carries one — ``monthly_normals``'
    # RH is a monthly mean, not a 1% design coincident wet bulb. An ERV's latent recovery
    # is a second gap: ``sensible_recovery_effectiveness`` is the only field there is.
    latent = internal_latent
    cooling_caveats.append(
        "latent load is occupant-only: no design outdoor humidity ratio is authored on "
        "Site, so the infiltration and ventilation latent terms are omitted (understated)")
    if ventilation_cfm > 0:
        cooling_caveats.append(
            "the ERV's LATENT recovery is unstated (only sensible_recovery_effectiveness "
            "exists), so its moisture load is not carried either")
    cooling = (air_cooling + slab_on_grade_cooling + roof_sol_air_cooling
               + solar.design_btu_per_hour * share + internal_sensible
               + sum(component.ua_btu_per_hour_f * _deltas_for(component.kind)[1]
                     for component in components))
    # A ton of refrigeration is a TOTAL, not a sensible. ``cooling_load_btu_per_hour`` stays
    # sensible because that is what a unit's ``cooling_capacity_btuh`` is rated against.
    return EnergyReport(heating, cooling, (cooling + latent) / 12000.0, tuple(components),
                        wall_comparison=_two_by_four_vs_six(model, heating_delta),
                        unknown_inputs=tuple(dict.fromkeys(unknown)),
                        infiltration_btu_per_hour=infiltration_heating,
                        ventilation_btu_per_hour=ventilation_heating,
                        latent_btu_per_hour=latent,
                        solar_btu_per_hour=solar.peak_btu_per_hour * share,
                        solar_peak_hour=solar.peak_hour,
                        solar_excursion_btu_per_hour=solar.excursion_btu_per_hour * share,
                        internal_sensible_btu_per_hour=internal_sensible,
                        cooling_caveats=tuple(dict.fromkeys(cooling_caveats)))


# How far apart the authored annual mean and the one derived from the twelve monthly
# normals may sit before it is worth saying so. A tenth of a degree is rounding; a degree is
# a different number.
_SOIL_TEMP_AGREEMENT_F = 1.0
# How far a slab's top must sit under its local grade to be a below-grade floor rather than
# a slab on grade. 6": ``EARTH_PLANE_SLAB_TOP_TOLERANCE_M`` is the at-grade band and this is
# past it, so a slab-on-grade whose top rounds either side of the plane stays one.
_SLAB_BELOW_GRADE_MIN_FT = 0.5


def _wall_top_z_m(wall: ResolvedWall) -> float:
    """The wall's mean top elevation — **rake-aware**.

    ``z1_m`` is the wall's bounding height, and for a ``ToRoof`` wall that is the RIDGE:
    billing ``length × (z1 - z0)`` makes a gable a rectangle. ``top_z0_m``/``top_z1_m`` are
    the real top at the two ends, and a straight rake between them makes the face a
    trapezoid, whose area is the mean of the two heights. catlin's attic gables billed
    657.6 sf against 414.0 sf real — 243.6 sf of invented wall, about 470 Btu/h of heating,
    and a bigger error than the screen-wall phantom the scope fix removed.
    """
    if wall.top_z0_m is not None and wall.top_z1_m is not None:
        return (wall.top_z0_m + wall.top_z1_m) / 2
    return wall.z1_m


def _short_plan_dimension_ft(outline) -> float:
    """The shorter side of the outline's bounding box, in feet.

    The quantity the below-grade floor method reads: heat leaves a basement floor sideways
    to the nearest exterior wall, so it is the NARROW way across that sets the path length.
    The bounding box rather than a minimum-width polygon measure because the method's own
    charts are drawn for rectangular floors, and a bounding box is the reading that stays
    honest for an L-shaped one — it never claims a shorter path than the floor has.
    """
    xs = [x for x, _ in outline]
    ys = [y for _, y in outline]
    return min(max(xs) - min(xs), max(ys) - min(ys)) / 0.3048


def _plan_perimeter_ft(outline) -> float:
    """Outline perimeter in feet — the length an F-factor multiplies."""
    total = 0.0
    for index, (x0, y0) in enumerate(outline):
        x1, y1 = outline[(index + 1) % len(outline)]
        total += ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    return total / 0.3048


def _slab_edge_r(model: ResolvedModel, slab) -> float | None:
    """R-value of the slab's EDGE insulation, or ``None`` where the model does not say.

    Nothing in the IR carries a slab edge as its own surface: a ``Layer`` with
    ``extent`` measured from ``GRADE`` is the closest thing, and it is a vertical band in
    the *wall*, not a property of the slab. So this answers ``None`` today, deliberately —
    the F-factor branch then names the gap rather than reading the slab's own R-value, which
    is a horizontal resistance and answers a different question.
    """
    return None


def _assembly_r_value(model: ResolvedModel, tag: str, unknown: list[str]) -> float | None:
    assembly = model.plan.library.resolve_assembly(tag)
    if assembly is None:
        unknown.append(f"assembly {tag}")
        return None
    r_value = assembly_r_value(assembly, model.plan.library)
    if r_value.value is None or r_value.value.r_us <= 0:
        unknown.extend(r_value.unknown_materials or (f"R-value {assembly.tag}",))
        return None
    return r_value.value.r_us


def _two_by_four_vs_six(
    model: ResolvedModel, heating_delta_f: float,
) -> dict[str, float | str] | None:
    """Compare the authored 2x4/2x6 *wall* assemblies on an equal 100-sf wall area.

    Scoped to assemblies a resolved above-grade wall actually uses, and resolved through
    ``resolve_assembly`` so a variant (#35) — which stores no layers of its own — is seen
    at its full depth. Scanning the raw library instead pairs whatever 2x4-framed item
    comes first (a garage roof, a partition) against an exterior wall, which answers a
    question nobody asked: the M5 acceptance is a *wall* assembly swap on the same run.

    **Which 2x4 and which 2x6, when a house builds several of each: the one it builds the
    MOST of, by resolved wall area.** Sorting by tag alone is arbitrary — a one-off piece
    of millwork could outrank the house's real interior partition simply by starting with
    an earlier letter, which is not what a reader of an energy sheet means by "the 2x4
    wall". Area is the honest tiebreak and it is stable; the tag breaks a genuine tie, so
    the result is still deterministic.
    """
    areas: dict[str, float] = {}
    for wall in model.walls:
        if wall.is_foundation:
            continue
        (ax, ay), (bx, by) = wall.axis
        length = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
        areas[wall.assembly] = areas.get(wall.assembly, 0.0) + length * max(
            0.0, wall.z1_m - wall.z0_m)
    candidates: dict[str, tuple[float, str, float]] = {}
    for tag in sorted(areas):
        assembly = model.plan.library.resolve_assembly(tag)
        if assembly is None:
            continue
        member = next((
            layer.framing.member for layer in assembly.layers
            if layer.framing is not None and layer.framing.member in ("2x4", "2x6")
        ), None)
        if member is None:
            continue
        r_value = assembly_r_value(assembly, model.plan.library)
        if r_value.value is None or r_value.value.r_us <= 0:
            continue
        contender = (areas[tag], assembly.tag, r_value.value.r_us)
        best = candidates.get(member)
        # Most area wins; on a true tie the lexically-first tag does, so the answer never
        # depends on iteration order.
        if best is None or (contender[0], [-ord(c) for c in contender[1]]) > (
                best[0], [-ord(c) for c in best[1]]):
            candidates[member] = contender
    if set(candidates) != {"2x4", "2x6"}:
        return None
    _area_4, tag_4, r_4 = candidates["2x4"]
    _area_6, tag_6, r_6 = candidates["2x6"]
    return {"baseline_assembly": tag_4, "upgrade_assembly": tag_6,
            "area_ft2": 100.0,
            "heating_savings_btu_per_hour": (1 / r_4 - 1 / r_6) * 100 * heating_delta_f}
