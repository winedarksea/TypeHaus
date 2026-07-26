"""A transparent block-load estimate, not a replacement for Manual J (M5 WP5.3)."""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.analysis import assembly_r_value
from typehaus.checks.building_science.wwr import _facade_for_wall, _wall_length
from typehaus.checks.registry import Preferences
from typehaus.model.plan import PlanModel
from typehaus.resolve.geometry import polygon_area
from typehaus.resolve.model import ResolvedModel, ResolvedWall

_M2_TO_FT2 = 10.7639104167
_WALL_UA_KINDS = ("walls", "windows", "doors")

# Component kinds whose exterior boundary is the ground, not the outdoor design air.
_GROUND_COUPLED_KINDS = ("foundation_walls", "slab")

# Tag prefixes of freestanding, unoccupied structures (sunken-garden porch/retaining walls,
# raised-garden planter, the detached garage's slab, breezeway decking) that are filed on
# one of the house's own storey keys because they share the plan frame, so
# ``_storey_is_conditioned`` cannot see past them. Minimal duplicate of the same scoping in
# ``checks.code.mn_energy`` (read-only to this module) — the block load and the
# prescriptive table must agree about what the conditioned envelope is.
_FREESTANDING_WALL_PREFIXES = ("W-SG-", "W-RG-")
_FREESTANDING_SLAB_PREFIXES = ("SL-SG-", "SL-G-", "SL-BW-")


def _storey_is_conditioned(plan: PlanModel, storey_tag: str) -> bool:
    """Does this storey hold any conditioned room?

    The block load sums UA against the *interior setpoint*, so a storey whose rooms are all
    unconditioned (catlin's detached garage, ``conditioned=False``) carries no such UA and
    must not be summed. This mirrors ``checks.code.mn_energy._storey_is_conditioned``
    (read-only to this module) — a storey with no rooms at all stays in scope, because an
    empty storey is a modelling gap, not a declared unconditioned space.
    """
    rooms = [el for el in plan.storey_elements(storey_tag) if el.element_kind == "Room"]
    if not rooms:
        return True
    return any(room.conditioned for room in rooms)


def _is_envelope_wall(wall: ResolvedWall) -> bool:
    """Is this wall on the thermal boundary — clad above grade, or below grade?

    Interior partitions separate two rooms at the same setpoint, so they carry no UA
    against the outdoor design temperature; summing them (and the doors hosted in them)
    inflates the block load by the entire interior wall area and fills ``unknown_inputs``
    with closet doors that have no business in an envelope report. Cladding is the same
    above-grade marker the condensation check scopes itself with.
    """
    return wall.is_foundation or any(layer.function == "cladding" for layer in wall.layers)


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

    def as_dict(self) -> dict[str, object]:
        return {"heating_load_btu_per_hour": self.heating_load_btu_per_hour,
                "cooling_load_btu_per_hour": self.cooling_load_btu_per_hour,
                "cooling_tons": self.cooling_tons,
                "components": [component.as_dict() for component in self.components],
                "wall_comparison": self.wall_comparison,
                "unknown_inputs": list(self.unknown_inputs),
                "scope": "resolved walls, foundations, roof, slabs, windows, and doors"}


def estimate_block_load(
    model: ResolvedModel, preferences: Preferences,
    storeys: frozenset[str] | None = None,
) -> EnergyReport:
    """Sum exposed resolved wall/opening UA plus orientation-weighted window solar gain.

    Every area comes from the resolved IR.  Missing geometry or thermal data remains named
    UNKNOWN rather than being replaced by a rule-of-thumb area or U-factor.

    ``storeys`` restricts the sum to a subset of the conditioned storeys (a heating zone,
    per ``checks.mep.hvac.heating_capacity``); ``None`` keeps the whole-house behavior.
    Zone loads ignore floors between zones at the same setpoint, so per-zone results sum
    (up to the shared ``wall_comparison``) to the whole-house block load.
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
    envelope_walls = [wall for wall in model.walls
                      if wall.storey in conditioned_storeys and _is_envelope_wall(wall)
                      and not wall.tag.startswith(_FREESTANDING_WALL_PREFIXES)]
    wall_by_tag = {wall.tag: wall for wall in envelope_walls}
    wall_gross_ft2 = {wall.tag: _wall_length(wall) * (wall.z1_m - wall.z0_m) * _M2_TO_FT2
                      for wall in envelope_walls}
    envelope_openings = [opening for opening in model.openings
                         if opening.host_wall in wall_by_tag]
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
    has_roofs = bool(roofs)
    has_slabs = bool(slabs)
    # A *zone* legitimately lacks a roof or a slab when that boundary is an interior floor
    # against another conditioned zone at the same setpoint, so the missing-geometry
    # diagnostics only apply to the whole-house sum.
    if storeys is None:
        if not has_roofs and not has_slabs:
            # Keep the original combined diagnostic stable for existing consumers while
            # still reporting the missing side precisely when only one is absent.
            unknown.append("roof/slab resolved geometry")
        elif not has_roofs:
            unknown.append("roof resolved geometry")
    for roof in roofs:
        r_value = _assembly_r_value(model, roof.assembly, unknown)
        if r_value is not None:
            area = roof.surface_area_m2 * _M2_TO_FT2
            roof_area += area
            roof_ua += area / r_value
    if roof_area:
        components.append(_component("roof", roof_area, roof_ua))
    if not slabs and has_roofs and storeys is None:
        unknown.append("slab resolved geometry")
    for slab in slabs:
        if slab.assembly is None:
            unknown.append(f"slab {slab.tag} assembly")
            continue
        r_value = _assembly_r_value(model, slab.assembly, unknown)
        if r_value is not None:
            area = abs(polygon_area(slab.outline)) * _M2_TO_FT2
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
    heating = sum(component.ua_btu_per_hour_f * _deltas_for(component.kind)[0]
                  for component in components)
    cooling = window_solar + sum(
        component.ua_btu_per_hour_f * _deltas_for(component.kind)[1]
        for component in components
    )
    return EnergyReport(heating, cooling, cooling / 12000.0, tuple(components),
                        wall_comparison=_two_by_four_vs_six(model, heating_delta),
                        unknown_inputs=tuple(dict.fromkeys(unknown)))


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
