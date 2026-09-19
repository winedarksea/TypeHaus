"""Cost sections of the courtyard study, written from each variant's priced BOM lines.

No rate lives here. A layout with no lines is printed as unpriced, never as $0.
"""

from __future__ import annotations

import math

from typehaus.engineering.sunken_garden.comparison import CostRange, LayoutResult
from typehaus.engineering.sunken_garden.inputs import SunkenGardenDesignInput

ZERO = CostRange(0.0, 0.0)


def money(value: CostRange) -> str:
    return f"${value.low:,.0f}-${value.high:,.0f}"


def _delta(reference: CostRange, cost: CostRange) -> str:
    if reference == cost:
        return "—"
    low, high = sorted((reference.low - cost.low, reference.high - cost.high))
    if high < 0.0:
        return f"premium ${abs(high):,.0f}-${abs(low):,.0f}"
    if low < 0.0:
        return f"${low:,.0f} to +${high:,.0f} (within the range)"
    return f"saving ${low:,.0f}-${high:,.0f}"


def _sum(result: LayoutResult, part: str) -> CostRange:
    total = ZERO
    for line in result.costs:
        total += getattr(line, part)
    return total


def _ratio(case, allowable_psf: float | None) -> float:
    """**A max-of-three proxy for which case presses hardest — not a utilization.**

    It ranks three unlike quantities on one scale so the table can name a governing case:
    the shortfall against the 1.5 sliding and overturning factors, and bearing against the
    site's own allowable. A value of 1.0 is the screening threshold on each of the three,
    and a value above it says *which* of them is short, not by how much anything is
    overstressed. Nothing downstream may read it as a demand/capacity.

    Until 2026-09-18 the bearing term divided by a hard-coded **3,000 psf**, a number that
    is in no input and which `analyse_stability` does not use — so the printed ratio and
    `passes_screening` could disagree about the same case on the same soil. It now divides
    by the allowable the screening itself applied.

    ``contact_loss`` had no term at all, so a case whose heel had lifted off the soil
    entirely printed a benign number and looked like the mildest thing on the page. Every
    catlin case loses contact, and none of them said so. :func:`_rank` now sorts a case
    that has lost contact above every case that has not, and :func:`_ratio_cell` says it in
    words — because once the heel is off the soil, `bearing_max_psf` is a number about a
    triangular distribution the screening no longer has, and dividing it by an allowable
    would be arithmetic about a mechanism that is not there.
    """

    bearing = math.inf if allowable_psf is None else case.bearing_max_psf / allowable_psf
    return max(1.5 / case.sliding_fs, 1.5 / case.overturning_fs, bearing)


def _rank(case, allowable_psf: float | None) -> tuple[bool, float]:
    """Contact loss outranks every finite ratio; within either group the ratio orders."""

    return (case.contact_loss, _ratio(case, allowable_psf))


def _ratio_cell(case, allowable_psf: float | None) -> str:
    ratio = ("no declared allowable bearing" if allowable_psf is None
             else f"{_ratio(case, allowable_psf):.2f}")
    return f"{ratio}, heel contact lost" if case.contact_loss else ratio


def layout_table(results: tuple[LayoutResult, ...], priced: bool,
                 design: SunkenGardenDesignInput | None = None) -> list[str]:
    allowable_psf = None if design is None else design.soil.allowable_bearing_psf.value
    reference = results[0].installed_cost
    lines = ["| Alternative | Material | Labor | Merged installed | Installed | Direct result | "
             "Governing check | Status |", "|---|---:|---:|---:|---:|---:|---|---|"]
    for result in results:
        governing = max(result.cases, key=lambda case: _rank(case, allowable_psf))
        status = ("screening pass" if all(case.passes_screening for case in result.cases)
                  else "revise")
        if priced and result.costs:
            money_cells = (f"{money(_sum(result, 'material'))} | {money(_sum(result, 'labor'))} | "
                           f"{money(_sum(result, 'merged'))} | {money(result.installed_cost)} | "
                           f"{_delta(reference, result.installed_cost)}")
        else:
            money_cells = "unpriced | unpriced | unpriced | unpriced | —"
        lines.append(f"| {result.name} | {money_cells} | "
                     f"{governing.case} ({_ratio_cell(governing, allowable_psf)}) | "
                     f"{status} |")
    lines += ["", "The parenthesised number beside the governing case is a **ranking proxy**: "
              "the worst of 1.5/FS-sliding, 1.5/FS-overturning and bearing over the site's "
              "allowable. It says which of the three governs, not how far anything is "
              "overstressed, and it is not a demand/capacity ratio."]
    if allowable_psf is not None:
        lines[-1] += f" Bearing is taken against {allowable_psf:,.0f} psf."
    return lines


def cost_detail(results: tuple[LayoutResult, ...]) -> list[str]:
    reference = {line.item: line for line in results[0].costs}
    lines: list[str] = []
    for result in results:
        lines += [f"### {result.name}", "",
                  "| Price section | Quantity | Material | Labor | Merged | Installed | "
                  "vs reference |", "|---|---:|---:|---:|---:|---:|---:|"]
        for item in result.costs:
            base = reference.get(item.item)
            moved = ("—" if base is not None and base.installed == item.installed
                     else _delta(base.installed if base else ZERO, item.installed))
            lines.append(f"| {item.item} | {item.quantity} | {money(item.material)} | "
                         f"{money(item.labor)} | {money(item.merged)} | "
                         f"{money(item.installed)} | {moved} |")
        lines.append("")
    return lines


def cost_basis(source: str | None, allowances: tuple[tuple[str, CostRange], ...]) -> list[str]:
    if source is None:
        return ["The house supplies no `prices.toml`, so no layout is priced (decision #28: "
                "quantities are the product, dollars are opt-in).", ""]
    lines = [
        f"Every line is the variant's own resolved model — the declared `variants.toml` entry, "
        f"ablated to the court (`-SG-`), terrace (`-RG-`), comparison planter (`-RGV-`) and "
        f"walkout-finish walls — billed and priced from `{source}`, before waste, contingency, "
        "markup and tax. \"Merged\" is installed money with no declared split and is never "
        "divided. Concrete stays rebar-inclusive where the house says so.", "",
    ]
    if allowances:
        lines += ["Fixed allowances touching the court are **held outside** every delta until "
                  "bidder scope is reconciled with the modelled work:", ""]
        lines += [f"- `{key}`: {money(value)}" for key, value in allowances]
        lines.append("")
    return lines


def recommendation_lines(results: tuple[LayoutResult, ...]) -> list[str]:
    by_name = {result.name: result for result in results}
    reference = by_name["reference"].installed_cost

    def delta(name: str) -> str:
        result = by_name[name]
        return _delta(reference, result.installed_cost) if result.costs else "unpriced"

    return [
        "## Pragmatic shortlist", "",
        "1. **Yard-grade planting with fiber-cement is the pragmatic cost and engineering "
        "choice.** It removes the planter surcharge; directly compared scope: "
        f"{delta('yard-grade-fiber-cement')}. It also removes masonry gravity support from "
        "the veneer beam, subject to a smaller transverse tie being confirmed by the coupled "
        "model.",
        "2. **Yard-grade planting with brick is the pragmatic appearance-first alternate.** "
        f"It retains the full-depth masonry expression; {delta('yard-grade-brick')}. "
        "It requires the corrected veneer beam, three-#5 study reinforcement, masonry-anchor "
        "design and verified pocket development.",
        "3. **If a raised bed is essential, use the separate 24-inch bed with fiber-cement as "
        "the engineering-led fallback** "
        f"({delta('setback-24-fiber-cement')}). The 36-inch clear strip sharply reduces "
        "surcharge at the court, but the second planter ring and its bedding make this the "
        "most expensive family and require a utility/circulation check.",
        "",
        "The against-wall variants are not shortlisted. They retain most of the lateral load "
        f"and add a 42-inch metal guard ({delta('against-wall-24-brick')} for the 24-inch "
        "brick case). The 36-inch setback bed is dominated by the 24-inch setback bed unless "
        "the extra planting width has owner value.", "",
    ]
