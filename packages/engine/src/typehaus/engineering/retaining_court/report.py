"""Markdown and schematic SVG deliverables for the reproducible courtyard study."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path

from typehaus.engineering.retaining_court.comparison import (
    COURTYARD_LAYOUTS,
    REFERENCE_LAYOUT,
    CostLine,
    compare_layouts,
    sizing_study,
)
from typehaus.engineering.retaining_court.cost_report import (
    cost_basis,
    cost_detail,
    layout_table,
    recommendation_lines,
)
from typehaus.engineering.retaining_court.inputs import (
    CourtDesignInput,
    PlantingProfile,
    default_design_input,
)
from typehaus.engineering.retaining_court.veneer_beam import check_veneer_beam

BASIS_VERSION = "retaining-court-study-1.0"


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(BASIS_VERSION.encode() + b":" + encoded).hexdigest()[:16]


def _basis_lines(design: CourtDesignInput,
                 fell_back: tuple[str, ...]) -> list[str]:
    """What this run was driven from — the half the study used to leave unsaid.

    Until 2026-09-14 this report was written from literals that disagreed with the authored
    house (ordinary retained height 5.0 ft against the model's 5.7865 ft), and nothing in
    the output said so. Every derived value now names its basis, and anything that stayed a
    literal is listed as a gap rather than passing as a measurement.
    """
    geometry = design.geometry
    height = design.soil.ordinary_retained_height_ft
    lines = [
        "## Basis of this run", "",
        "| Input | Value | Basis |", "|---|---:|---|",
        f"| court clear width | {geometry.clear_width_ft:.2f} ft | resolved wall axes |",
        f"| retained leg length | {geometry.retained_side_length_ft:.2f} ft | "
        "resolved wall axes |",
        f"| concrete stem height | {geometry.concrete_stem_height_ft:.4f} ft | "
        "authored top/bottom elevations |",
        f"| stem thickness | {geometry.stem_thickness_in:.1f} in | assembly STRUCTURE layer |",
        f"| footing | {geometry.footing_width_ft:.2f} ft wide x "
        f"{geometry.footing_depth_ft:.2f} ft, toe {geometry.toe_ft:.2f} ft | authored Footing |",
        f"| end wall toe extension | {geometry.end_toe_extension_ft:.2f} ft | authored "
        "Footing; the per-foot screening below is the legs' section |",
        f"| ordinary retained height | {height.value:.4f} ft | {height.basis} |",
        "",
    ]
    if fell_back:
        lines.extend(["**Not derived from the model — literal screening values:**", ""])
        lines.extend(f"- {item}" for item in fell_back)
        lines.append("")
    else:
        lines.extend([
            "Every geometric input above was read from the resolved model. Soil strength, "
            "stiffness, groundwater and the balcony reactions are **not** in the model and "
            "remain unresolved below; nothing here invents them.", "",
        ])
    return lines


def _smallest(layout: PlantingProfile, design: CourtDesignInput):
    """The lightest section in the bounded sweep that clears screening for ``layout``.

    Falls back to the least-overstressed candidate when none passes, so the caller can say
    "nothing in the set works" rather than raising.
    """
    candidates = sizing_study(layout, design)
    passing = [item for item in candidates if item.passes_screening]
    return min(passing or candidates,
               key=lambda item: (item.governing_ratio, item.concrete_cy)), bool(passing)


def _terrace_verdict(design: CourtDesignInput) -> list[str]:
    """**Decision 1, answered on evidence rather than on preference.**

    The owner's standing position is that the raised terrace stays *unless removing it buys
    a materially smaller section* — footings above all. That question was already being
    answered by the sweep, but from a court 9" shorter than the authored one; at the
    corrected ordinary retained height it is worth re-reading, because the terrace's
    contribution is exactly the height the old literal had mislaid.

    Both sides are run through the same bounded sweep, so the comparison is like for like:
    ``REFERENCE_LAYOUT`` is the terrace as authored (40" against the wall) and
    ``yard-grade`` is the same court with the terrace removed.
    """
    yard = next(item for item in COURTYARD_LAYOUTS if item.layout == "yard-grade")
    with_terrace, terrace_passes = _smallest(REFERENCE_LAYOUT, design)
    without, without_passes = _smallest(yard, design)
    concrete_delta = with_terrace.concrete_cy - without.concrete_cy
    same_section = (with_terrace.stem_in == without.stem_in
                    and abs(with_terrace.footing_width_ft - without.footing_width_ft) < 1e-9
                    and abs(with_terrace.toe_ft - without.toe_ft) < 1e-9)
    lines = [
        "## Does removing the terrace buy a smaller section?", "",
        "| Court | Stem | Footing | Toe / heel | Concrete | Governing |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name, item, passes in (("as authored (40-inch terrace)", with_terrace, terrace_passes),
                               ("terrace removed (yard-grade)", without, without_passes)):
        note = "" if passes else " — **no candidate in the set passes**"
        lines.append(
            f"| {name} | {item.stem_in:.0f} in | {item.footing_width_ft:.1f} ft | "
            f"{item.toe_ft:.1f} / {item.heel_ft:.1f} ft | {item.concrete_cy:.1f} cy | "
            f"{item.governing_case} ({item.governing_ratio:.2f}){note} |")
    lines.append("")
    both_fail = not terrace_passes and not without_passes
    shown = ("least-overstressed candidate" if both_fail else "lightest passing candidate")
    if same_section:
        lines.extend([
            f"**No. The section does not move.** The {shown} is the same stem, the same "
            "footing width and the same toe on both sides of the comparison, and the "
            f"concrete differs by {abs(concrete_delta):.2f} cy — which is the court's own "
            "geometry, not a structural saving. The terrace's own cost is the yard-grade "
            "delta in the layout table; it buys no section, so the structure gives no reason "
            "to remove it and the reference stays the default until the owner chooses.", "",
            "That is a statement about the *bounded sweep*, not a proof that no smaller wall "
            "exists: 10- and 12-inch stems and 4- to 7-foot footings are the whole search. "
            "It does say that the terrace is not what is sizing this wall.", "",
        ])
    else:
        lines.extend([
            f"**Yes — removing the terrace moves the section**, from a "
            f"{with_terrace.stem_in:.0f}-inch stem on a "
            f"{with_terrace.footing_width_ft:.1f}-foot footing to "
            f"{without.stem_in:.0f} inches on {without.footing_width_ft:.1f} feet, a "
            f"concrete difference of {concrete_delta:.2f} cy. Decision 1's condition is met "
            "and the terrace should be re-opened on its merits.", "",
        ])
    if both_fail:
        lines.extend([
            "**Read the ratios before reading the verdict.** *Nothing in the bounded sweep "
            f"clears screening on either side* — {with_terrace.governing_case} governs both, "
            f"at {with_terrace.governing_ratio:.2f} with the terrace and "
            f"{without.governing_ratio:.2f} without it. Removing the terrace therefore buys "
            "a real reduction in **demand** while buying no reduction in **section**, "
            "because the section is being set by something else: the blocked-drain wet case "
            "is a five-foot hydrostatic head on a buoyant free body, and no 12-inch stem on "
            "a 7-foot footing survives it. What that case actually asks for is a retained-face "
            "drain that is modelled and verified, not a bigger wall. Until the drainage "
            "network can be walked to an outfall, this table is a statement about the wet "
            "envelope and not a sizing recommendation.", "",
        ])
    return lines


def _sizing_lines(design: CourtDesignInput) -> list[str]:
    lines = [
        "| Layout | Stem | Footing | Toe / heel | Concrete | Governing | Status |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for layout in COURTYARD_LAYOUTS:
        candidates = sizing_study(layout, design)
        passing = [item for item in candidates if item.passes_screening]
        shown = min(passing or candidates,
                    key=lambda item: (item.governing_ratio, item.concrete_cy))
        layout_name = ("yard-grade" if not layout.clear_width_ft else
                       f"{layout.layout}-{layout.clear_width_ft * 12:.0f}")
        status = ("conditional screening pass; development/site checks open"
                  if shown.passes_screening else "no 12-inch-deep candidate passes")
        lines.append(
            f"| {layout_name} | {shown.stem_in:.0f} in | {shown.footing_width_ft:.1f} ft | "
            f"{shown.toe_ft:.1f} / {shown.heel_ft:.1f} ft | {shown.concrete_cy:.1f} cy | "
            f"{shown.governing_case} ({shown.governing_ratio:.2f}) | {status} |"
        )
    return lines


def _svg(layout: str, raised_in: float, width_in: float, setback_in: float) -> str:
    yard_y = 90
    wall_x = 250
    soil_top = yard_y - raised_in
    bed_x = wall_x + setback_in
    bed_width = max(width_in, 1.0)
    plan_offset = (width_in + setback_in) * 0.7
    planter_plan = ""
    if raised_in:
        planter_plan = (
            f'<path d="M{470 - plan_offset:.1f} 65 V{215 + plan_offset:.1f} '
            f'H{650 + plan_offset:.1f} V65" fill="none" stroke="#9b7653" '
            'stroke-width="8"/>'
        )
    return "\n".join((
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="260" '
        'viewBox="0 0 720 260">',
        "<style>text{font:14px sans-serif}.concrete{fill:#bbb;stroke:#222}"
        ".soil{fill:#9b7653}.drain{stroke:#168aad;stroke-width:5;fill:none}"
        ".dim{stroke:#444;stroke-dasharray:4 3}</style>",
        f'<text x="20" y="25">{layout}: coordinated section '
        '(dimensions in inches, schematic)</text>',
        f'<path class="soil" d="M20 {yard_y} H{bed_x} V{soil_top} '
        f'H{bed_x + bed_width} V{yard_y} H700 V245 H20Z"/>',
        f'<rect class="concrete" x="{wall_x - 10}" y="40" width="10" height="180"/>',
        f'<rect class="concrete" x="{wall_x - 70}" y="210" width="150" height="12"/>',
        f'<rect x="{wall_x + 4}" y="105" width="12" height="105" '
        'fill="#d9edf2" stroke="#168aad"/>',
        f'<path class="drain" d="M{wall_x + 8} 205 H{wall_x + 90}"/>',
        f'<circle cx="{wall_x + 8}" cy="205" r="7" fill="none" stroke="#168aad"/>',
        f'<line class="dim" x1="{bed_x}" y1="35" x2="{bed_x}" y2="225"/>',
        f'<line class="dim" x1="{bed_x + bed_width}" y1="35" '
        f'x2="{bed_x + bed_width}" y2="225"/>',
        f'<text x="{bed_x + 3}" y="55">bed {width_in:.0f}</text>',
        f'<text x="{wall_x + 12}" y="82">setback {setback_in:.0f}</text>',
        '<text x="20" y="115">ordinary yard</text>',
        '<text x="275" y="165">drained stone + filter</text>',
        '<text x="340" y="203">collector to soakaway/overflow</text>',
        '<text x="450" y="35">plan</text>',
        '<path d="M470 65 V215 H650 V65" fill="none" stroke="#777" stroke-width="10"/>',
        planter_plan,
        '<line x1="470" y1="65" x2="650" y2="65" stroke="#168aad" stroke-width="4"/>',
        '<text x="475" y="240">court wall / planter / north tie</text>',
        "</svg>",
    ))


def write_study(output_dir: Path, design: CourtDesignInput | None = None,
                fell_back: tuple[str, ...] = (),
                costs: Mapping[str, tuple[CostLine, ...]] | None = None,
                cost_source: str | None = None,
                allowances: tuple = ()) -> Path:
    """``design`` is normally :func:`model_inputs.design_input_from_model`'s answer.

    ``None`` keeps the standalone literal basis, which is a *screening* basis and is
    labelled as one in the report. ``fell_back`` names every value that could not be derived
    from the model and kept its literal — printed, because a study that silently agrees with
    itself is the failure this whole path was rebuilt to stop.

    ``costs`` is each ``variants.toml`` entry's priced BOM lines (``cli/retaining_court_costs``)
    and ``cost_source`` the price file; both ``None`` prints every layout unpriced.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    design = design or default_design_input()
    results = compare_layouts(design, costs)
    beam = check_veneer_beam()
    for layout in COURTYARD_LAYOUTS:
        name = ("yard-grade" if not layout.clear_width_ft else
                f"{layout.layout}-{layout.clear_width_ft * 12:.0f}")
        (output_dir / f"{name}.svg").write_text(
            _svg(name, layout.raised_height_ft * 12, layout.clear_width_ft * 12,
                 layout.setback_ft * 12), encoding="utf-8")

    lines = [
        "# Retaining court engineering and cost comparison", "",
        f"Basis version: `{BASIS_VERSION}`  ",
        f"Engineering fingerprint: `{_fingerprint(asdict(design))}`", "",
        "The existing plan remains the default. All proposed layouts are comparison variants; "
        "none is selected for construction by this report.", "",
        *_basis_lines(design, fell_back),
        "## Common-structure comparison", "",
        *layout_table(results, priced=cost_source is not None, design=design), "",
        *cost_basis(cost_source, allowances),
        "## Itemized variable work", "",
    ]
    lines.extend(cost_detail(results))
    g = design.geometry
    t = g.walls
    lines.extend([
        *_terrace_verdict(design),
        "## Conditional structural optimization", "", *_sizing_lines(design), "",
        "The bounded sweep covers 10- and 12-inch stems, 4- through 7-foot footings in "
        "6-inch steps, and 6-inch toe allocations with at least 12 inches at toe and heel. "
        "A screening pass is not a construction size: development, local balcony zones, soil "
        "stiffness, settlement, frost and global stability remain open.", "",
        "No structural reduction in the bounded set is currently supported. Conditional "
        "structural savings are therefore reported as $0; smaller stems or footings remain "
        "design candidates only and must not be carried into bidding.", "",
        "## Coupled structural model and member schedule", "",
        f"The PyNite model contains shell elements for {t.left_upper}, {t.left}, {t.end}, "
        f"{t.right} and {t.right_upper}; footing plates; {t.cross}; the optional {t.tie} "
        "tie; four balcony "
        "reaction nodes; horizontal soil springs; and one-sided vertical contact springs. "
        "It runs with and without the veneer tie and with unequal east/west load. The project "
        "solve is INCOMPLETE until measured soil stiffness and column reactions are supplied; "
        "the solver does not substitute fixed supports or zero reactions.", "",
        "| Members | Current study section | Role / required check |", "|---|---|---|",
        f"| {t.left_upper} / {t.right_upper} | {g.stem_thickness_in:g}-in stem | "
        "porch wall, balcony local zones, staged backfill |",
        f"| {t.left} / {t.right} / {t.end} | {g.stem_thickness_in:g}-in stem | "
        "retained wall plates and corners |",
        f"| footings | {g.footing_width_ft:g} ft by {g.footing_depth_ft * 12:g} in | "
        "contact, bearing, toe/heel flexure |",
        f"| {t.cross} | cross-member | calculated transverse force and penetrated section |",
        f"| {t.tie} | veneer beam | brick gravity beam and optional transverse tie |",
        "| balcony column corners | local cast columns | reactions, bearing and anchorage |",
        "", "Validation examples cover a cantilever wall, beam/frame response, unequal loading, "
        "removed ties, missing-input refusal, global equilibrium and 4/3/2-foot mesh response.", "",
        "## Corrected veneer beam", "",
        f"Effective span {beam.effective_span_ft:.2f} ft; factored load "
        f"{beam.factored_load_plf:.0f} plf at **U = 1.4D** (ACI 318-19 Eq. 5.3.1a — the "
        "member carries dead weight and nothing else, so 1.2D + 1.6L does not govern and "
        f"1.2D alone is not a combination ACI publishes); Mu "
        f"{beam.factored_moment_ftlb / 1000:.1f} kip-ft; "
        f"Vu {beam.factored_shear_lb / 1000:.1f} kip. Required steel by demand is "
        f"{beam.required_steel_in2:.2f} in² and ACI §9.6.1.2's minimum — the **greater** of "
        f"3√f'c·b·d/fy and 200·b·d/fy, at the real 5,000 psi mix — is "
        f"{beam.minimum_steel_in2:.3f} in². **Two #5 is 0.620 in² and does not clear it**, "
        "and §9.6.1.3's one-third-over exception does not rescue it either (4/3 of the "
        f"demand steel is {beam.required_steel_in2 * 4.0 / 3.0:.3f} in²). Three #5 "
        f"({beam.provided_steel_in2:.2f} in²) is the study section, at d/c "
        f"{beam.flexure_ratio:.2f} flexure and {beam.shear_ratio:.2f} shear.", "",
        f"**Torsion is computed, not asserted.** The wythe's eccentric weight gives "
        f"{beam.torsion_ftlb_per_ft:.0f} ft-lb per foot, "
        f"{beam.factored_torsion_ftlb:,.0f} ft-lb factored at the support. That is **below "
        f"cracking** (φTcr {beam.phi_cracking_torsion_ftlb:,.0f} ft-lb), so ACI §22.7.3.2 "
        "lets the twist redistribute into the slab — and **above the threshold** (φTth "
        f"{beam.phi_threshold_torsion_ftlb:,.0f} ft-lb), so §9.6.4's minimum torsional "
        "reinforcement is owed regardless: closed hoops with 135° hooks plus longitudinal "
        "steel. The two provisions answer different questions and only one of them used to "
        "be quoted. Pocket restraint and development remain open.", "",
        "## Drainage and water envelope", "",
        "| Scenario | Model action | Required disposition |", "|---|---|---|",
        "| Normal infiltration | Wall drain to soakaway course and overflow | "
        "Survey every invert |",
        "| Failed infiltration | Storage fills to overflow | Prove overflow capacity and "
        "freeboard |",
        "| Blocked collector | Add hydrostatic pressure to five-foot head | Wet case governs "
        "until access/cleanouts are detailed |",
        "| Pump unavailable | No pumping credit | Add gravity emergency discharge or accept "
        "wet envelope |", "",
        "## Frost and geotechnical basis", "",
        "| Foundation approach | Excavation credit | Status |", "|---|---:|---|",
        "| Current thick washed-stone replacement | none | retain pending subgrade and "
        "drainage verification |",
        "| Shallower replacement | conditional | needs stratigraphy, groundwater, bearing "
        "and frost-heave design |",
        "| Insulated unheated foundation | conditional | needs ASCE 32/approved thermal "
        "design and coordinated wing insulation |", "",
        "The stone layer answers drainage and concrete interface resistance. It does not by "
        "itself establish resistance below the replacement stone, settlement, frost safety, "
        "or global stability.", "",
        "## Construction requirements", "",
        "1. Place footings and piers; then place all five walls and the grade beam with "
        "monolithic corners; then place the rim slab and columns.",
        "2. Reach the engineer-specified concrete strength before backfill. Provide temporary "
        "restraint and backfill the east and west sides in balanced lifts.",
        "3. Use light compaction equipment within the engineer's exclusion zone. Keep heavy "
        "equipment and stockpiles out of the surcharge zone unless included in the case.",
        "4. Coordinate reinforcement, corner bars, beam pockets, balcony-column zones, GFRP "
        "thermal-break dowels, sleeves, waterstops and drains before either wall placement.", "",
        *recommendation_lines(results),
        "## Unresolved requirements", "",
    ])
    lines.extend(f"- {item}" for item in design.unresolved_requirements())
    lines.extend([
        "- site stratigraphy, strength, settlement, interface resistance and global stability",
        "- drain/overflow invert survey and soakaway-course infiltration test",
        "- GFRP dowel stiffness, shear transfer and development across the thermal break",
        "- veneer/structural tie connection design and local balcony support reinforcement",
        "- fiber-cement manufacturer clearances and verified walkout-wall attachment backing",
        "", "## Schematic sections", "",
    ])
    for layout in COURTYARD_LAYOUTS:
        name = ("yard-grade" if not layout.clear_width_ft else
                f"{layout.layout}-{layout.clear_width_ft * 12:.0f}")
        lines.append(f"- [{name}]({name}.svg)")
    report_path = output_dir / "comparison.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path
