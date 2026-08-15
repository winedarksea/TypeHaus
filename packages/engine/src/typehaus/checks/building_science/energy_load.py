"""A transparent block-load estimate, not a replacement for Manual J (M5 WP5.3).

The arithmetic only: exposed UA by component, orientation-weighted window solar gain, and
the two air-side terms (blower-door infiltration, ERV ventilation air). What counts as
envelope, and how much of a plane a zone owns, is answered next door in ``energy_scope`` —
this module takes those answers and sums them.

Every area comes from the resolved IR. A missing U-factor or R-value is named in
``EnergyReport.unknown_inputs`` and dropped from the sum, never replaced by a rule of
thumb: a load that silently invented an input is a load nobody can size equipment against.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.analysis import assembly_r_value
from typehaus.checks.building_science.energy_scope import (
    _FREESTANDING_SLAB_PREFIXES,
    _FREESTANDING_WALL_PREFIXES,
    _M2_TO_FT2,
    _conditioned_rooms,
    _is_envelope_wall,
    _opening_in_scope,
    _polygon_scope_fraction,
    _room_scope,
    _storey_is_conditioned,
    _volume_ft3,
    _wall_scope_fraction,
)
from typehaus.checks.building_science.wwr import _facade_for_wall, _wall_length
from typehaus.checks.registry import Preferences
from typehaus.resolve.geometry import polygon_area
from typehaus.resolve.model import ResolvedModel

# Component kinds whose exterior boundary is the ground, not the outdoor design air.
_GROUND_COUPLED_KINDS = ("foundation_walls", "slab")

# Sensible heat of air at sea level: 0.075 lb/ft3 × 0.24 Btu/lb·°F × 60 min/h.
_AIR_SENSIBLE_BTU_PER_CFM_F = 1.08


def _infiltration_cfm(
    preferences: Preferences, volume_ft3: float, unknown: list[str],
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
    n_factor = preferences.infiltration_n_factor
    if not n_factor or n_factor <= 0:
        unknown.append("Preferences infiltration_n_factor (must be > 0)")
        return 0.0
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

    def as_dict(self) -> dict[str, object]:
        return {"heating_load_btu_per_hour": self.heating_load_btu_per_hour,
                "cooling_load_btu_per_hour": self.cooling_load_btu_per_hour,
                "cooling_tons": self.cooling_tons,
                "components": [component.as_dict() for component in self.components],
                "infiltration_btu_per_hour": self.infiltration_btu_per_hour,
                "ventilation_btu_per_hour": self.ventilation_btu_per_hour,
                "wall_comparison": self.wall_comparison,
                "unknown_inputs": list(self.unknown_inputs),
                "scope": "resolved walls, foundations, roof, slabs, windows, and doors, "
                         "plus blower-door infiltration and ERV ventilation air"}


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
    heating_delta = preferences.interior_setpoint_f - site.design_temp_heating.fahrenheit
    cooling_delta = site.design_temp_cooling.fahrenheit - preferences.interior_setpoint_f
    # Below-grade components are ground-coupled: their exterior boundary is the soil (near
    # its annual-mean temperature), not the 99% design air. With no authored soil
    # temperature the air ΔT stands in and the gap is named in ``unknown_inputs``.
    soil_temp_f = site.soil_temp_f
    if soil_temp_f is not None:
        ground_heating_delta = preferences.interior_setpoint_f - soil_temp_f
        ground_cooling_delta = max(0.0, soil_temp_f - preferences.interior_setpoint_f)
    else:
        ground_heating_delta, ground_cooling_delta = heating_delta, cooling_delta

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
    envelope_walls = [wall for wall in model.walls
                      if wall.storey in conditioned_storeys and _is_envelope_wall(wall, model)
                      and not wall.tag.startswith(_FREESTANDING_WALL_PREFIXES)]
    wall_fraction = {wall.tag: _wall_scope_fraction(wall, scope) for wall in envelope_walls}
    envelope_walls = [wall for wall in envelope_walls if wall_fraction[wall.tag] > 0.0]
    wall_by_tag = {wall.tag: wall for wall in envelope_walls}
    wall_gross_ft2 = {
        wall.tag: (_wall_length(wall) * (wall.z1_m - wall.z0_m) * _M2_TO_FT2
                   * wall_fraction[wall.tag])
        for wall in envelope_walls
    }
    # An opening is discrete: it belongs wholly to the zone its own plan point stands in,
    # never split by a fraction, so a window is never counted twice across zones.
    envelope_openings = [opening for opening in model.openings
                         if opening.host_wall in wall_by_tag
                         and _opening_in_scope(wall_by_tag[opening.host_wall], opening, scope)]
    opening_area_ft2: dict[str, float] = {tag: 0.0 for tag in wall_gross_ft2}
    components: list[LoadComponent] = []
    unknown: list[str] = []

    for opening in envelope_openings:
        opening_area_ft2[opening.host_wall] = opening_area_ft2.get(opening.host_wall, 0.0) + (
            opening.width_m * opening.height_m * _M2_TO_FT2
        )
    walls_area = walls_ua = foundation_area = foundation_ua = 0.0
    for wall in envelope_walls:
        area = max(0.0, wall_gross_ft2[wall.tag] - opening_area_ft2.get(wall.tag, 0.0))
        assembly = model.plan.library.resolve_assembly(wall.assembly)
        if assembly is None:
            unknown.append(f"assembly {wall.assembly}")
            continue
        r_value = assembly_r_value(assembly, model.plan.library)
        if r_value.value is None or r_value.value.r_us <= 0:
            unknown.extend(r_value.unknown_materials or (f"R-value {assembly.tag}",))
            continue
        if wall.is_foundation:
            foundation_area += area
            foundation_ua += area / r_value.value.r_us
        else:
            walls_area += area
            walls_ua += area / r_value.value.r_us
    def _component(kind: str, area: float, ua: float,
                   solar: float = 0.0) -> LoadComponent:
        return LoadComponent(kind, area, ua, solar, heating_delta_f=_deltas_for(kind)[0])

    components.append(_component("walls", walls_area, walls_ua))
    if foundation_area:
        components.append(_component("foundation_walls", foundation_area, foundation_ua))

    roof_area = roof_ua = slab_area = slab_ua = 0.0
    roofs = [roof for roof in model.roofs if roof.storey in conditioned_storeys]
    slabs = [solid for solid in model.solids
             if solid.category == "slab" and solid.storey in conditioned_storeys
             and not solid.tag.startswith(_FREESTANDING_SLAB_PREFIXES)]
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
    if roof_area:
        components.append(_component("roof", roof_area, roof_ua))
    if not slabs and has_roofs and whole_house:
        unknown.append("slab resolved geometry")
    for slab in slabs:
        if slab.assembly is None:
            unknown.append(f"slab {slab.tag} assembly")
            continue
        r_value = _assembly_r_value(model, slab.assembly, unknown)
        if r_value is not None:
            area = (abs(polygon_area(slab.outline)) * _M2_TO_FT2
                    * slab_fraction[slab.tag])
            slab_area += area
            slab_ua += area / r_value
    if slab_area:
        components.append(_component("slab", slab_area, slab_ua))
    if soil_temp_f is None and (foundation_area or slab_area):
        unknown.append("Site.soil_temp_f (below-grade components use outdoor design air ΔT)")

    window_area = window_ua = window_solar = door_area = door_ua = 0.0
    solar_orientation = {"N": 0.25, "E": 0.70, "S": 1.0, "W": 0.85}
    for opening in envelope_openings:
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
            wall = wall_by_tag.get(opening.host_wall)
            if product is None or product.shgc is None:
                unknown.append(f"window {opening.tag} SHGC")
            elif wall is not None:
                window_solar += (
                    area * product.shgc * solar_orientation[_facade_for_wall(wall, model)]
                    * preferences.cooling_solar_gain_btu_per_hour_ft2
                )
    components.extend((_component("windows", window_area, window_ua, window_solar),
                       _component("doors", door_area, door_ua)))
    # Air-side terms. Both the blower-door result and the ERV's airflow are whole-house
    # facts, so a zone gets its share of each by conditioned volume — the quantity the air
    # in a zone actually scales with.
    whole_volume_ft3 = _volume_ft3(model, _conditioned_rooms(model, None, None))
    zone_volume_ft3 = (whole_volume_ft3 if whole_house else
                       _volume_ft3(model, _conditioned_rooms(model, storeys, rooms)))
    share = 1.0 if whole_house else (
        zone_volume_ft3 / whole_volume_ft3 if whole_volume_ft3 > 0 else 0.0)
    infiltration_cfm = _infiltration_cfm(preferences, whole_volume_ft3, unknown) * share
    ventilation_cfm = _ventilation_cfm(model, unknown) * share
    infiltration_heating = _AIR_SENSIBLE_BTU_PER_CFM_F * infiltration_cfm * heating_delta
    ventilation_heating = _AIR_SENSIBLE_BTU_PER_CFM_F * ventilation_cfm * heating_delta
    air_cooling = (_AIR_SENSIBLE_BTU_PER_CFM_F * (infiltration_cfm + ventilation_cfm)
                   * cooling_delta)

    heating = sum(component.ua_btu_per_hour_f * _deltas_for(component.kind)[0]
                  for component in components) + infiltration_heating + ventilation_heating
    cooling = window_solar + air_cooling + sum(
        component.ua_btu_per_hour_f * _deltas_for(component.kind)[1]
        for component in components
    )
    return EnergyReport(heating, cooling, cooling / 12000.0, tuple(components),
                        wall_comparison=_two_by_four_vs_six(model, heating_delta),
                        unknown_inputs=tuple(dict.fromkeys(unknown)),
                        infiltration_btu_per_hour=infiltration_heating,
                        ventilation_btu_per_hour=ventilation_heating)


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
    """
    wall_tags = sorted({wall.assembly for wall in model.walls if not wall.is_foundation})
    candidates: dict[str, tuple[str, float]] = {}
    for tag in wall_tags:
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
        if r_value.value is not None and r_value.value.r_us > 0:
            candidates.setdefault(member, (assembly.tag, r_value.value.r_us))
    if set(candidates) != {"2x4", "2x6"}:
        return None
    tag_4, r_4 = candidates["2x4"]
    tag_6, r_6 = candidates["2x6"]
    return {"baseline_assembly": tag_4, "upgrade_assembly": tag_6,
            "area_ft2": 100.0,
            "heating_savings_btu_per_hour": (1 / r_4 - 1 / r_6) * 100 * heating_delta_f}
