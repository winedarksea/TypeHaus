"""Markdown and schematic SVG deliverables for the reproducible courtyard study."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from typehaus.engineering.sunken_garden.comparison import (
    COURTYARD_LAYOUTS,
    CostRange,
    LayoutResult,
    compare_layouts,
    sizing_study,
)
from typehaus.engineering.sunken_garden.inputs import default_design_input
from typehaus.engineering.sunken_garden.veneer_beam import check_veneer_beam

BASIS_VERSION = "sunken-garden-study-1.0"


def _money(value: CostRange) -> str:
    return f"${value.low:,.0f}-${value.high:,.0f}"


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(BASIS_VERSION.encode() + b":" + encoded).hexdigest()[:16]


def _layout_table(results: tuple[LayoutResult, ...]) -> list[str]:
    lines = [
        "| Alternative | Material | Labor | Installed | Governing service check | Status |",
        "|---|---:|---:|---:|---|---|",
    ]
    for result in results:
        material = CostRange(0.0, 0.0)
        labor = CostRange(0.0, 0.0)
        for line in result.costs:
            material += line.material
            labor += line.labor
        governing = max(
            result.cases,
            key=lambda item: max(1.5 / item.sliding_fs, 1.5 / item.overturning_fs,
                                 item.bearing_max_psf / 3000.0),
        )
        ratio = max(1.5 / governing.sliding_fs, 1.5 / governing.overturning_fs,
                    governing.bearing_max_psf / 3000.0)
        status = ("screening pass" if all(case.passes_screening for case in result.cases)
                  else "revise")
        lines.append(
            f"| {result.name} | {_money(material)} | {_money(labor)} | "
            f"{_money(result.installed_cost)} | {governing.case} ({ratio:.2f}) | {status} |"
        )
    return lines


def _cost_detail(result: LayoutResult) -> list[str]:
    lines = [f"### {result.name}", "",
             "| Item | Quantity | Material | Labor | Installed |",
             "|---|---:|---:|---:|---:|"]
    for item in result.costs:
        lines.append(f"| {item.item} | {item.quantity:.1f} {item.unit} | "
                     f"{_money(item.material)} | {_money(item.labor)} | "
                     f"{_money(item.installed)} |")
    return lines + [""]


def _sizing_lines() -> list[str]:
    lines = [
        "| Layout | Stem | Footing | Toe / heel | Concrete | Governing | Status |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for layout in COURTYARD_LAYOUTS:
        candidates = sizing_study(layout)
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
        '<text x="340" y="203">collector to drywell/overflow</text>',
        "</svg>",
    ))


def write_study(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    design = default_design_input()
    results = compare_layouts(design)
    beam = check_veneer_beam()
    for layout in COURTYARD_LAYOUTS:
        name = ("yard-grade" if not layout.clear_width_ft else
                f"{layout.layout}-{layout.clear_width_ft * 12:.0f}")
        (output_dir / f"{name}.svg").write_text(
            _svg(name, layout.raised_height_ft * 12, layout.clear_width_ft * 12,
                 layout.setback_ft * 12), encoding="utf-8")

    lines = [
        "# Sunken courtyard engineering and cost comparison", "",
        f"Basis version: `{BASIS_VERSION}`  ",
        f"Engineering fingerprint: `{_fingerprint(asdict(design))}`", "",
        "The existing plan remains the default. All proposed layouts are comparison variants; "
        "none is selected for construction by this report.", "",
        "## Common-structure comparison", "", *_layout_table(results), "",
        "Costs are planning ranges. Concrete stays rebar-inclusive and no separate steel cost "
        "is added. Shared mobilization and the existing whole-site excavation allowance are "
        "excluded from deltas until bidder scope is reconciled.", "",
        "## Itemized variable work", "",
    ]
    for result in results:
        lines.extend(_cost_detail(result))
    lines.extend([
        "## Conditional structural optimization", "", *_sizing_lines(), "",
        "The bounded sweep covers 10- and 12-inch stems, 4- through 7-foot footings in "
        "6-inch steps, and 6-inch toe allocations with at least 12 inches at toe and heel. "
        "A screening pass is not a construction size: development, local balcony zones, soil "
        "stiffness, settlement, frost and global stability remain open.", "",
        "## Corrected veneer beam", "",
        f"Effective span {beam.effective_span_ft:.2f} ft; factored load "
        f"{beam.factored_load_plf:.0f} plf; Mu {beam.factored_moment_ftlb / 1000:.1f} kip-ft; "
        f"Vu {beam.factored_shear_lb / 1000:.1f} kip. Required steel by demand is "
        f"{beam.required_steel_in2:.2f} in² and ACI minimum is {beam.minimum_steel_in2:.2f} "
        f"in². Three #5 ({beam.provided_steel_in2:.2f} in²) is the study section; the old "
        "two-#5 conclusion is superseded. Torsion restraint and development remain open.", "",
        "## Drainage and water envelope", "",
        "| Scenario | Model action | Required disposition |", "|---|---|---|",
        "| Normal infiltration | Wall drain to drywell and overflow | Survey every invert |",
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
        "## Unresolved requirements", "",
    ])
    lines.extend(f"- {item}" for item in design.unresolved_requirements())
    lines.extend([
        "- site stratigraphy, strength, settlement, interface resistance and global stability",
        "- drain/overflow invert survey and drywell infiltration test",
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
