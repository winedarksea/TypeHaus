"""Bounded layout and initial structural-sizing comparison for the courtyard."""

from __future__ import annotations

from dataclasses import dataclass, replace

from typehaus.engineering.sunken_garden.inputs import (
    PlantingProfile,
    SunkenGardenDesignInput,
    default_design_input,
)
from typehaus.engineering.sunken_garden.stability import StabilityResult, analyse_stability

COURTYARD_LAYOUTS = (
    PlantingProfile("yard-grade", 0.0, 0.0, 0.0),
    PlantingProfile("against-wall", 2.5, 2.0, 0.0),
    PlantingProfile("against-wall", 2.5, 3.0, 0.0),
    PlantingProfile("setback", 2.5, 2.0, 3.0),
    PlantingProfile("setback", 2.5, 3.0, 3.0),
)
REFERENCE_LAYOUT = PlantingProfile("reference", 40.0 / 12.0, 3.0, 0.0)


@dataclass(frozen=True)
class CostRange:
    low: float
    high: float

    def __add__(self, other: CostRange) -> CostRange:
        return CostRange(self.low + other.low, self.high + other.high)


@dataclass(frozen=True)
class UnitCost:
    material: CostRange
    labor: CostRange


@dataclass(frozen=True)
class CostLine:
    item: str
    quantity: float
    unit: str
    unit_cost: UnitCost

    @property
    def material(self) -> CostRange:
        return CostRange(self.quantity * self.unit_cost.material.low,
                         self.quantity * self.unit_cost.material.high)

    @property
    def labor(self) -> CostRange:
        return CostRange(self.quantity * self.unit_cost.labor.low,
                         self.quantity * self.unit_cost.labor.high)

    @property
    def installed(self) -> CostRange:
        return self.material + self.labor


@dataclass(frozen=True)
class LayoutResult:
    name: str
    planting: PlantingProfile
    cladding: str
    cases: tuple[StabilityResult, ...]
    costs: tuple[CostLine, ...]
    unresolved: tuple[str, ...]

    @property
    def installed_cost(self) -> CostRange:
        total = CostRange(0.0, 0.0)
        for line in self.costs:
            total += line.installed
        return total


@dataclass(frozen=True)
class SizingCandidate:
    stem_in: float
    footing_width_ft: float
    toe_ft: float
    heel_ft: float
    governing_case: str
    governing_ratio: float
    stem_flexure_ratio: float
    footing_flexure_ratio: float
    passes_screening: bool
    requires_deeper_footing: bool
    development_resolved: bool
    concrete_cy: float


_UNIT_COST = {
    "excavation": UnitCost(CostRange(0.0, 0.0), CostRange(38.0, 75.0)),
    "replacement stone": UnitCost(CostRange(50.0, 75.0), CostRange(25.0, 50.0)),
    # Concrete remains rebar-inclusive; no separate reinforcing-dollar line is emitted.
    "concrete": UnitCost(CostRange(450.0, 650.0), CostRange(400.0, 600.0)),
    "formwork": UnitCost(CostRange(5.0, 8.0), CostRange(13.0, 24.0)),
    "planter block": UnitCost(CostRange(35.0, 55.0), CostRange(55.0, 95.0)),
    "metal guard": UnitCost(CostRange(170.0, 270.0), CostRange(90.0, 160.0)),
    "brick": UnitCost(CostRange(13.0, 19.0), CostRange(21.0, 33.0)),
    "fiber-cement": UnitCost(CostRange(11.0, 18.0), CostRange(13.0, 22.0)),
    "drainage": UnitCost(CostRange(18.0, 30.0), CostRange(37.0, 65.0)),
    "waterproofing": UnitCost(CostRange(3.0, 6.0), CostRange(5.0, 9.0)),
}


def _court_length_ft(design: SunkenGardenDesignInput) -> float:
    return 2.0 * design.geometry.retained_side_length_ft + design.geometry.clear_width_ft + 1.0


def _planter_length_ft(design: SunkenGardenDesignInput,
                       planting: PlantingProfile) -> float:
    if planting.layout == "yard-grade":
        return 0.0
    base_u = _court_length_ft(design)
    if planting.layout in {"against-wall", "reference"}:
        return base_u + 4.0 * planting.clear_width_ft
    inner_u = base_u + 4.0 * planting.setback_ft
    outer_u = inner_u + 4.0 * planting.clear_width_ft + 4.0
    return inner_u + outer_u + 2.0 * planting.clear_width_ft


def _cost_lines(design: SunkenGardenDesignInput, planting: PlantingProfile,
                cladding: str) -> tuple[CostLine, ...]:
    length = _court_length_ft(design)
    face_sf = length * design.geometry.concrete_stem_height_ft
    planter_length = _planter_length_ft(design, planting)
    guard_length = length if planting.layout == "against-wall" else 0.0
    cladding_sf = 129.0
    concrete_cy = _concrete_volume_cy(design)
    replacement_stone_cy = 89.82  # current resolved Catlin takeoff
    excavation_cy = replacement_stone_cy + concrete_cy
    # Common structural dimensions are intentionally held fixed here. The sizing study
    # reports structural deltas separately, conditional on the missing site inputs.
    return (
        CostLine("court excavation", excavation_cy, "cy", _UNIT_COST["excavation"]),
        CostLine("washed replacement stone", replacement_stone_cy, "cy",
                 _UNIT_COST["replacement stone"]),
        CostLine("court reinforced concrete", concrete_cy, "cy", _UNIT_COST["concrete"]),
        CostLine("planter construction", planter_length * 3.0, "face sf",
                 _UNIT_COST["planter block"]),
        CostLine("planter drainage", planter_length, "lf", _UNIT_COST["drainage"]),
        CostLine("court metal guard", guard_length, "lf", _UNIT_COST["metal guard"]),
        CostLine(f"{cladding} walkout finish", cladding_sf, "sf", _UNIT_COST[cladding]),
        CostLine("retained-face drainage", length, "lf", _UNIT_COST["drainage"]),
        CostLine("retained-face waterproofing",
                 length * design.soil.ordinary_retained_height_ft.value,
                 "sf", _UNIT_COST["waterproofing"]),
        CostLine("court wall formwork", face_sf * 2.0, "sf", _UNIT_COST["formwork"]),
    )


def _cases(design: SunkenGardenDesignInput,
           planting: PlantingProfile) -> tuple[StabilityResult, ...]:
    return (
        analyse_stability(design, planting, case="symmetric-service"),
        analyse_stability(design, planting, case="one-side-only"),
        analyse_stability(design, planting, case="staged-backfill"),
        analyse_stability(design, planting, case="construction-compaction",
                          compaction_surcharge_psf=250.0),
        analyse_stability(design, planting, case="blocked-drain-wet", wet=True),
        analyse_stability(design, planting, case="historical-full-height",
                          full_height_comparison=True),
    )


def compare_layouts(design: SunkenGardenDesignInput | None = None) -> tuple[LayoutResult, ...]:
    design = design or default_design_input()
    out: list[LayoutResult] = []
    for planting in (REFERENCE_LAYOUT, *COURTYARD_LAYOUTS):
        width = int(planting.clear_width_ft * 12) if planting.clear_width_ft else 0
        base_name = ("reference" if planting.layout == "reference" else
                     "yard-grade" if not width else f"{planting.layout}-{width}")
        claddings = ("brick",) if planting.layout == "reference" else ("brick", "fiber-cement")
        for cladding in claddings:
            conflicts = ()
            if planting.layout == "setback":
                conflicts = ("verify 36-inch strip plus planter against utilities and circulation",)
            out.append(LayoutResult(
                name=f"{base_name}-{cladding}", planting=planting, cladding=cladding,
                cases=_cases(design, planting), costs=_cost_lines(design, planting, cladding),
                unresolved=design.unresolved_requirements() + conflicts,
            ))
    return tuple(out)


def _concrete_volume_cy(design: SunkenGardenDesignInput) -> float:
    length = _court_length_ft(design)
    stem_t = design.geometry.stem_thickness_in / 12.0
    # U-shaped runs overlap at two monolithic corners; subtract those squares once.
    stem = (length * stem_t - 2.0 * stem_t ** 2) * design.geometry.concrete_stem_height_ft
    footing = ((length * design.geometry.footing_width_ft
                - 2.0 * design.geometry.footing_width_ft ** 2)
               * design.geometry.footing_depth_ft)
    return (stem + footing) / 27.0


def sizing_study(planting: PlantingProfile,
                 design: SunkenGardenDesignInput | None = None) -> tuple[SizingCandidate, ...]:
    """The requested bounded 10/12-inch, 4-7 foot, 6-inch toe/heel sweep."""

    base = design or default_design_input()
    candidates: list[SizingCandidate] = []
    for stem in (10.0, 12.0):
        for width_in in range(48, 85, 6):
            for toe_in in range(12, width_in - int(stem) - 11, 6):
                heel_in = width_in - stem - toe_in
                if heel_in < 12.0:
                    continue
                geometry = replace(base.geometry, stem_thickness_in=stem,
                                   footing_width_ft=width_in / 12.0, toe_ft=toe_in / 12.0)
                candidate = replace(base, geometry=geometry)
                cases = _cases(candidate, planting)
                ratios = [
                    max(1.5 / case.sliding_fs, 1.5 / case.overturning_fs,
                        case.bearing_max_psf / candidate.soil.allowable_bearing_psf.value,
                        1.01 if case.contact_loss else 0.0)
                    for case in cases
                ]
                stem_as_in2 = 0.44 * 12.0 / 10.0  # authored #6 at 10 inches
                stem_d_in = stem - 3.0 - 0.375
                stem_a_in = stem_as_in2 * 60000.0 / (0.85 * 5000.0 * 12.0)
                stem_capacity_ftlb = (0.9 * stem_as_in2 * 60000.0
                                      * (stem_d_in - stem_a_in / 2.0) / 12.0)
                stem_ratio = max(1.6 * case.pressure.moment_at_footing_top_ftlb_per_ft
                                 / stem_capacity_ftlb for case in cases)
                footing_as_in2 = 0.31  # authored #5 at 12 inches, top and bottom
                footing_d_in = 12.0 - 3.0 - 0.3125
                footing_a_in = footing_as_in2 * 60000.0 / (0.85 * 5000.0 * 12.0)
                footing_capacity_ftlb = (0.9 * footing_as_in2 * 60000.0
                                         * (footing_d_in - footing_a_in / 2.0) / 12.0)
                footing_ratio = max(
                    1.6 * max(
                        case.bearing_max_psf * geometry.toe_ft ** 2 / 2.0,
                        candidate.soil.unit_weight_pcf.value
                        * candidate.soil.ordinary_retained_height_ft.value
                        * geometry.heel_ft ** 2 / 2.0,
                    ) / footing_capacity_ftlb
                    for case in cases
                )
                governing_index = max(range(len(cases)), key=ratios.__getitem__)
                ratio = max(ratios[governing_index], stem_ratio, footing_ratio)
                governing_case = cases[governing_index].case
                if ratio == stem_ratio:
                    governing_case = "stem flexure"
                elif ratio == footing_ratio:
                    governing_case = "footing flexure"
                candidates.append(SizingCandidate(
                    stem_in=stem, footing_width_ft=width_in / 12.0,
                    toe_ft=toe_in / 12.0, heel_ft=heel_in / 12.0,
                    governing_case=governing_case,
                    governing_ratio=ratio, passes_screening=ratio <= 1.0,
                    stem_flexure_ratio=stem_ratio, footing_flexure_ratio=footing_ratio,
                    requires_deeper_footing=footing_ratio > 1.0,
                    development_resolved=False,
                    concrete_cy=_concrete_volume_cy(candidate),
                ))
    return tuple(candidates)
