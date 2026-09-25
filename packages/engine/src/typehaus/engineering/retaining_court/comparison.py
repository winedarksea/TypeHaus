"""Bounded layout and initial structural-sizing comparison for the courtyard."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from typehaus.engineering.retaining_court.inputs import (
    CourtDesignInput,
    PlantingProfile,
    default_design_input,
)
from typehaus.engineering.retaining_court.stability import StabilityResult, analyse_stability

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
class CostLine:
    """One priced section of one variant's courtyard scope, from its resolved BOM.

    ``merged`` is installed money with no declared split; it is never divided.
    """

    item: str
    quantity: str
    material: CostRange
    labor: CostRange
    merged: CostRange

    @property
    def installed(self) -> CostRange:
        return self.material + self.labor + self.merged


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


def _court_length_ft(design: CourtDesignInput) -> float:
    return 2.0 * design.geometry.retained_side_length_ft + design.geometry.clear_width_ft + 1.0


#: Why the two asymmetric cases are **not** in :func:`_cases`, said once so the next reader
#: does not put them back. ``"one-side-only"`` and ``"staged-backfill"`` were listed here
#: until 2026-09-14 and passed **no differentiating argument**: both called
#: :func:`analyse_stability` exactly as ``"symmetric-service"`` did, so all three returned
#: byte-identical results and ``max(...)`` printed whichever the tie landed on as
#: "governing". A case that cannot differ is worse than a missing one — it reads as coverage.
#:
#: They cannot differ *here* because this free body is **one lineal foot of one wall**.
#: Backfilling one leg before the other, or in unequal lifts, changes nothing about that
#: foot: it changes how the legs share thrust through the cross-member and the corners,
#: which is a question about the whole U. ``analytical/retaining_court_coupled.py`` is where
#: it is asked — it already runs with and without the veneer tie and with unequal east/west
#: load — and ``engineering/retaining_system.py`` is where the closed loop is summed.
ASYMMETRIC_CASES_ARE_SYSTEM_LEVEL = (
    "one-side-only and staged-backfill are system cases, not per-foot ones: see "
    "analytical/retaining_court_coupled.py and engineering/retaining_system.py"
)


def _cases(design: CourtDesignInput,
           planting: PlantingProfile) -> tuple[StabilityResult, ...]:
    return (
        analyse_stability(design, planting, case="symmetric-service"),
        analyse_stability(design, planting, case="construction-compaction",
                          compaction_surcharge_psf=250.0),
        analyse_stability(design, planting, case="blocked-drain-wet", wet=True),
        analyse_stability(design, planting, case="historical-full-height",
                          full_height_comparison=True),
    )


def compare_layouts(design: CourtDesignInput | None = None,
                    costs: Mapping[str, tuple[CostLine, ...]] | None = None,
                    ) -> tuple[LayoutResult, ...]:
    """``costs`` maps a ``variants.toml`` name to its priced lines; absent means unpriced."""

    design = design or default_design_input()
    costs = costs or {}
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
            name = "reference" if planting.layout == "reference" else f"{base_name}-{cladding}"
            out.append(LayoutResult(
                name=name, planting=planting, cladding=cladding,
                cases=_cases(design, planting), costs=costs.get(name, ()),
                unresolved=design.unresolved_requirements() + conflicts,
            ))
    return tuple(out)


def _concrete_volume_cy(design: CourtDesignInput) -> float:
    length = _court_length_ft(design)
    stem_t = design.geometry.stem_thickness_in / 12.0
    # U-shaped runs overlap at two monolithic corners; subtract those squares once.
    stem = (length * stem_t - 2.0 * stem_t ** 2) * design.geometry.concrete_stem_height_ft
    footing = ((length * design.geometry.footing_width_ft
                - 2.0 * design.geometry.footing_width_ft ** 2)
               * design.geometry.footing_depth_ft)
    return (stem + footing) / 27.0


def sizing_study(planting: PlantingProfile,
                 design: CourtDesignInput | None = None) -> tuple[SizingCandidate, ...]:
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
