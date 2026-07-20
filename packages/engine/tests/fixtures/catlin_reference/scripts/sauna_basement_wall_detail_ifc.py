"""
Sauna basement wall detail driven by IFC parameters.

Run:
  python catlin_house/build_catlin_house_ifc.py
  python catlin_house/sauna_basement_wall_detail_ifc.py

Output:
  catlin_house/out/sauna_basement_wall_detail_ifc.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Patch, Polygon

import ifcopenshell
import ifcopenshell.util.element

from ifcplot.catlin_house import build_catlin_house_ifc
from ifcplot.detail_utils import (
    COLORS,
    HATCHES,
    _french_drain,
    _leader,
    _lumber,
    _rect,
    _slab_assembly,
    load_markdown_notes,
    _wrap_notes,
)
from ifcplot.units import m_to_in


def _ensure_ifc_has_house_psets(ifc_path: Path, *, required: list[str]) -> None:
    def has_psets() -> bool:
        if not ifc_path.exists():
            return False
        f = ifcopenshell.open(str(ifc_path))
        house = next((b for b in f.by_type("IfcBuilding") if b.Name == "House"), None)
        if house is None:
            return False
        psets = ifcopenshell.util.element.get_psets(house)
        return all(pset in psets and psets[pset].get("ParamsJSON") for pset in required)

    if has_psets():
        return

    ifc_path.parent.mkdir(parents=True, exist_ok=True)
    build_catlin_house_ifc(out_path=ifc_path)


def _load_house_params(ifc_path: Path) -> dict[str, dict]:
    f = ifcopenshell.open(str(ifc_path))
    house = next(b for b in f.by_type("IfcBuilding") if b.Name == "House")
    psets = ifcopenshell.util.element.get_psets(house)

    def read(pset_name: str) -> dict:
        raw = psets.get(pset_name, {}).get("ParamsJSON")
        if not raw:
            raise RuntimeError(f"Missing `{pset_name}.ParamsJSON` on building 'House'.")
        return json.loads(raw)

    return {
        "plan": read("Pset_ifcPlot_BasementPlan"),
        "basement": read("Pset_ifcPlot_BasementConstruction"),
        "sauna": read("Pset_ifcPlot_SaunaShowerDetail"),
    }


def main() -> None:
    ifc_path = Path("catlin_house/out/catlin_house.ifc")
    _ensure_ifc_has_house_psets(
        ifc_path,
        required=[
            "Pset_ifcPlot_BasementPlan",
            "Pset_ifcPlot_BasementConstruction",
            "Pset_ifcPlot_SaunaShowerDetail",
        ],
    )
    params = _load_house_params(ifc_path)

    plan_p = params["plan"]
    basement_p = params["basement"]
    sauna_p = params["sauna"]

    foundation_p = basement_p["foundation"]
    slab_p = basement_p["slab"]

    finish_p = sauna_p["finish"]
    structure_p = sauna_p["structure"]
    adjacent_p = sauna_p["adjacent_wall"]
    benches_p = sauna_p["benches"]
    heater_p = sauna_p["heater"]

    fig = plt.figure(figsize=(20, 10))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.8, 1.15], wspace=0.06)
    ax = fig.add_subplot(gs[0, 0])
    ax_notes = fig.add_subplot(gs[0, 1])

    COL = COLORS

    # -----------------------
    # Geometry (inches, schematic)
    # -----------------------
    sauna_clear_w = m_to_in(float(plan_p["sauna_rect_m"]["h_m"]))  # 8'
    total_h = float(structure_p["clear_height_in"])  # clear height to underside of ceiling slab

    conc_wall_thk = float(foundation_p["wall_thickness_in"])
    footing_w = float(foundation_p["footing_width_in"])
    footing_d = float(foundation_p["footing_thickness_in"])
    stone_base_thk = float(foundation_p["stone_base_thickness_in"])
    stone_base_extra = float(foundation_p["stone_base_extra_in"])
    drain_diam = float(foundation_p["french_drain_diameter_in"])

    slab_thk = float(slab_p["slab_thickness_in"])
    xps_under_thk = float(slab_p["xps_under_in"])
    vapor_sheet_thk = float(slab_p["vapor_barrier_in"])
    stone_under_slab = float(slab_p["stone_under_in"])

    thermal_break_thk = float(slab_p["thermal_break_in"])
    sealant_thk = float(slab_p["sealant_in"])

    polyiso_thk = float(finish_p["polyiso_in"])
    furring_thk = float(finish_p["furring_in"])
    tg_thk = float(finish_p["tg_in"])
    baseboard_h = float(finish_p["baseboard_height_in"])
    baseboard_thk = furring_thk + tg_thk

    mem_thk = float(finish_p["membrane_in"])
    flash_thk = float(finish_p["flashing_in"])

    stud_depth = float(adjacent_p["stud_depth_in"])
    drywall = float(adjacent_p["drywall_in"])
    gap_to_conc = float(adjacent_p["gap_to_concrete_in"])

    ceiling_slab_thk = float(structure_p["ceiling_slab_in"])
    drop_gap = float(structure_p["drop_ceiling_gap_in"])
    drop_depth = float(structure_p["drop_ceiling_depth_in"])

    # Define footing position first (independent reference point)
    footing_center_x = 0.0

    # Calculate concrete wall position (centered over footing)
    x_conc_center = footing_center_x
    x_conc_ext = x_conc_center - conc_wall_thk / 2
    x_conc_int = x_conc_ext + conc_wall_thk

    # Left wall framing against concrete (supports drop ceiling)
    x_studL0 = x_conc_int + gap_to_conc
    x_studL1 = x_studL0 + stud_depth

    # Left wall layers (toward sauna interior, +x)
    x_polyL0 = x_studL1
    x_polyL1 = x_polyL0 + polyiso_thk
    x_furL0 = x_polyL1
    x_furL1 = x_furL0 + furring_thk
    x_tgL0 = x_furL1
    x_tgL1 = x_tgL0 + tg_thk
    x_sauna_left = x_tgL1
    x_sauna_right = x_sauna_left + sauna_clear_w

    # Right wall layers (away from sauna interior, +x)
    x_tgR0 = x_sauna_right
    x_tgR1 = x_tgR0 + tg_thk
    x_furR0 = x_tgR1
    x_furR1 = x_furR0 + furring_thk
    x_polyR0 = x_furR1
    x_polyR1 = x_polyR0 + polyiso_thk
    x_stud0 = x_polyR1
    x_stud1 = x_stud0 + stud_depth
    x_dry0 = x_stud1
    x_dry1 = x_dry0 + drywall

    # Ceiling build-up (inside sauna)
    y_slab_top = 0.0
    y_ceiling_bot = total_h
    y_ceiling_top = y_ceiling_bot + ceiling_slab_thk
    y_drop_top = y_ceiling_bot - drop_gap
    y_drop_bot = y_drop_top - drop_depth
    y_ceil_poly0 = y_drop_bot - polyiso_thk
    y_ceil_fur0 = y_ceil_poly0 - furring_thk
    y_ceil_tg0 = y_ceil_fur0 - tg_thk

    # -----------------------
    # Sauna slab assembly (interior)
    # -----------------------
    y_slab_bot = y_slab_top - slab_thk
    y_vapor_bot = y_slab_bot - vapor_sheet_thk
    y_xps_bot = y_vapor_bot - xps_under_thk
    y_stone_under_bot = y_xps_bot - stone_under_slab

    x_foot0 = footing_center_x - footing_w / 2
    x_foot1 = x_foot0 + footing_w
    x_stone0 = x_foot0 - stone_base_extra
    x_stone1 = x_foot1 + stone_base_extra
    y_foot0 = y_xps_bot - 2.0
    y_foot1 = y_foot0 - footing_d
    y_stone0 = y_foot1
    y_stone1 = y_stone0 - stone_base_thk

    # -----------------------
    # Concrete wall + footing
    # -----------------------
    _rect(ax, x_conc_ext, y_foot0, conc_wall_thk, (y_ceiling_top - y_foot0), fc=COL.concrete, lw=1.2, z=2)
    _rect(ax, x_foot0, y_foot1, footing_w, footing_d, fc=COL.concrete, lw=1.2, hatch=HATCHES.compacted, z=2)
    _rect(ax, x_stone0, y_stone1, (x_stone1 - x_stone0), stone_base_thk, fc=COL.aggregate, lw=1.0, hatch=HATCHES.gravel, z=1)

    # French drain in wider stone (not under footing)
    drain_x = x_stone0 + drain_diam * 0.8
    drain_y = y_stone1 + stone_base_thk / 2
    _french_drain(ax, drain_x, drain_y, drain_diam, fc=COL.metal_dark, z=3)

    # Sauna slab assembly with thermal breaks on both sides
    slab_break_x0 = x_conc_int
    _rect(ax, slab_break_x0, y_slab_bot, thermal_break_thk, slab_thk, fc=COL.xps, lw=1.0, z=3)
    _rect(ax, slab_break_x0, y_slab_top, thermal_break_thk, sealant_thk, fc=COL.sealant, ec="black", lw=0.9, z=5)

    slab_x0 = slab_break_x0 + thermal_break_thk
    slab_x1 = x_polyR0
    _slab_assembly(
        ax,
        slab_x0,
        slab_x1,
        y_slab_top,
        slab_thk=slab_thk,
        xps_thk=xps_under_thk,
        vapor_thk=vapor_sheet_thk,
        stone_thk=stone_under_slab,
        thermal_break_side="none",
        show_stone=True,
    )

    slab_break2_x0 = slab_x1
    _rect(ax, slab_break2_x0, y_slab_bot, thermal_break_thk, slab_thk, fc=COL.xps, lw=1.0, z=3)
    _rect(ax, slab_break2_x0, y_slab_top, thermal_break_thk, sealant_thk, fc=COL.sealant, ec="black", lw=0.9, z=5)
    _rect(ax, slab_break2_x0 + thermal_break_thk, y_slab_bot, 18.0, slab_thk, fc=COL.concrete, lw=1.0, ls="--", z=1)

    # -----------------------
    # Right wall framing (2x4 with optional R-13)
    # -----------------------
    plate_thk = 1.5
    _lumber(ax, x_stud0, y_slab_top, stud_depth, plate_thk, fc=COL.wood, lw=1.2, z=6)
    _rect(ax, x_stud0, y_slab_top + plate_thk, stud_depth, (y_ceiling_bot - (y_slab_top + plate_thk)), fc=COL.insulation, lw=1.0, hatch=HATCHES.compacted, z=1)
    _rect(ax, x_dry0, y_slab_top, drywall, (y_ceiling_bot - y_slab_top), fc=COL.drywall, lw=1.0, z=0)

    # Left wall framing against concrete (supports drop ceiling)
    _lumber(ax, x_studL0, y_slab_top, stud_depth, plate_thk, fc=COL.wood, lw=1.2, z=6)
    _rect(ax, x_studL0, y_slab_top + plate_thk, stud_depth, (y_drop_bot - (y_slab_top + plate_thk)), fc=COL.insulation, lw=1.0, hatch=HATCHES.compacted, z=1)

    # -----------------------
    # Sauna interior wall & ceiling finishes
    # -----------------------
    _rect(ax, x_polyL0, y_slab_top, polyiso_thk, (y_drop_bot - y_slab_top), fc=COL.polyiso, lw=1.0, z=4)
    _rect(ax, x_polyR0, y_slab_top, polyiso_thk, (y_drop_bot - y_slab_top), fc=COL.polyiso, lw=1.0, z=4)
    _rect(ax, x_polyL1, y_ceil_poly0, (x_polyR0 - x_polyL1), polyiso_thk, fc=COL.polyiso, lw=1.0, z=4)

    _rect(ax, x_furL0, baseboard_h, furring_thk, (y_ceil_tg0 - baseboard_h), fc=COL.wood, lw=1.0, hatch=HATCHES.diagonal, z=6)
    _rect(ax, x_tgL0, baseboard_h, tg_thk, (y_ceil_tg0 - baseboard_h), fc=COL.wood, lw=1.1, z=7)
    _rect(ax, x_furR0, baseboard_h, furring_thk, (y_ceil_tg0 - baseboard_h), fc=COL.wood, lw=1.0, hatch=HATCHES.diagonal, z=6)
    _rect(ax, x_tgR0, baseboard_h, tg_thk, (y_ceil_tg0 - baseboard_h), fc=COL.wood, lw=1.1, z=7)

    _rect(ax, x_furL1, y_ceil_fur0, (x_furR0 - x_furL1), furring_thk, fc=COL.wood, lw=1.0, hatch=HATCHES.diagonal, z=6)
    _rect(ax, x_sauna_left, y_ceil_tg0, (x_sauna_right - x_sauna_left), tg_thk, fc=COL.wood, lw=1.1, z=7)

    # Fiber cement baseboard (replaces furring + T&G at bottom 6")
    _rect(ax, x_furL0, y_slab_top, baseboard_thk, baseboard_h, fc=COL.fiber_cement, lw=1.1, z=8)
    _rect(ax, x_sauna_right, y_slab_top, baseboard_thk, baseboard_h, fc=COL.fiber_cement, lw=1.1, z=8)

    # Flashing from polyiso over baseboard (both sides)
    left_flash = np.array(
        [
            [x_polyL1, baseboard_h + flash_thk],
            [x_sauna_left, baseboard_h + flash_thk],
            [x_sauna_left, baseboard_h],
            [x_polyL1 + 0.15, baseboard_h],
            [x_polyL1 + 0.15, baseboard_h + 3.0],
            [x_polyL1, baseboard_h + 3.0],
        ]
    )
    ax.add_patch(Polygon(left_flash, closed=True, facecolor=COL.metal, edgecolor="black", linewidth=0.9, zorder=9))

    right_flash = np.array(
        [
            [x_polyR0, baseboard_h + flash_thk],
            [x_sauna_right, baseboard_h + flash_thk],
            [x_sauna_right, baseboard_h],
            [x_polyR0 - 0.15, baseboard_h],
            [x_polyR0 - 0.15, baseboard_h + 3.0],
            [x_polyR0, baseboard_h + 3.0],
        ]
    )
    ax.add_patch(Polygon(right_flash, closed=True, facecolor=COL.metal, edgecolor="black", linewidth=0.9, zorder=9))

    # Liquid floor membrane + up baseboard
    _rect(ax, x_sauna_left, y_slab_top, (x_sauna_right - x_sauna_left), mem_thk, fc=COL.membrane, lw=0.8, z=10)
    _rect(ax, x_sauna_left, y_slab_top, mem_thk, baseboard_h, fc=COL.membrane, lw=0.8, z=10)
    _rect(ax, x_sauna_right - mem_thk, y_slab_top, mem_thk, baseboard_h, fc=COL.membrane, lw=0.8, z=10)

    # Dropped ceiling framing (2x4s below primary structure)
    _rect(ax, x_studL0, y_drop_bot, (x_stud0 + stud_depth - x_studL0), drop_depth, fc=COL.wood, lw=1.1, hatch=HATCHES.cross, z=5)

    # Duckboards on rubber feet (schematic)
    duck_thk = 1.0
    foot_h = 0.5
    duck_y0 = y_slab_top + mem_thk + foot_h
    duck_x0 = x_sauna_left + 4.0
    duck_x1 = x_sauna_right - 4.0
    _rect(ax, duck_x0, duck_y0, duck_x1 - duck_x0, duck_thk, fc=COL.wood, lw=1.0, hatch=HATCHES.compacted, z=11)
    for fx in [duck_x0 + 6.0, duck_x1 - 6.0]:
        _rect(ax, fx, y_slab_top + mem_thk, 1.2, foot_h, fc=COL.rubber, ec="black", lw=0.8, z=12)

    # Benches and heater (schematic)
    bench_depth = float(benches_p["depth_in"])
    bench_thk = float(benches_p["thickness_in"])
    lower_bench_top = float(benches_p["lower_top_in"])
    upper_bench_top = float(benches_p["upper_top_in"])
    bench_x0 = x_sauna_right - bench_depth - 2.0
    bench_x1 = x_sauna_right - 2.0
    lower_bench_x0 = x_sauna_right - bench_depth * 2 - 2.0
    _rect(ax, lower_bench_x0, y_slab_top + lower_bench_top - bench_thk, bench_depth * 2, bench_thk, fc=COL.wood, lw=1.0, z=12)
    _rect(ax, bench_x0, y_slab_top + upper_bench_top - bench_thk, bench_depth, bench_thk, fc=COL.wood, lw=1.0, z=12)

    heater_w = float(heater_p["width_in"])
    heater_h = float(heater_p["height_in"])
    heater_x0 = x_sauna_left + 6.0
    heater_y0 = y_slab_top + mem_thk
    _rect(ax, heater_x0, heater_y0, heater_w, heater_h, fc=COL.equipment, ec="black", lw=1.0, hatch=HATCHES.dense_plus, z=12)

    # Ceiling slab above (Catlin House uses a concrete ceiling slab at the main floor)
    _rect(ax, x_conc_ext - 6.0, y_ceiling_bot, (x_dry1 - (x_conc_ext - 6.0)) + 8.0, ceiling_slab_thk, fc=COL.concrete, lw=1.2, z=3)

    # -----------------------
    # Labels / leaders (key callouts)
    # -----------------------
    _leader(ax, (x_conc_ext + conc_wall_thk / 2, 54.0), (x_conc_ext - 40.0, 82.0), "Concrete wall\n(basement foundation)", ha="right")
    _leader(ax, ((x_foot0 + x_foot1) / 2, (y_foot0 + y_foot1) / 2), (x_conc_ext - 26.0, -26.0), f'{footing_w:.0f}"×{footing_d:.0f}" footing\n(5000 psi concrete)', ha="right")
    _leader(ax, (drain_x, drain_y), (x_conc_ext - 26.0, -54.0), "French drain in washed stone\n(wider area, not under footing)", ha="right")
    _leader(ax, (x_polyL1 - 0.6, 62.0), (x_sauna_left + 18.0, 68.0), f'{polyiso_thk:.0f}" foil-faced polyiso (taped)\n(walls + ceiling)')
    _leader(ax, ((x_furL0 + x_furL1) / 2, 76.0), (x_conc_ext - 26.0, 92.0), f'{furring_thk:.1f}" plywood furring strips\n(fasteners per IRC Table R703.15.2)', ha="right")
    _leader(ax, ((x_tgL0 + x_tgL1) / 2, 86.0), (x_sauna_left + 18.0, 92.0), f'5/4 T&G boards ({tg_thk:.0f}" actual)\n(low-k species: basswood/poplar/aspen)')
    _leader(ax, (x_studL0 + (x_stud0 + stud_depth - x_studL0) / 2, y_drop_bot + drop_depth / 2), (x_sauna_left + 34.0, y_drop_top + 10.0), "2x4 dropped ceiling framing\nbelow primary structure")
    _leader(ax, (x_sauna_left + 0.4, 3.0), (x_sauna_left - 80.0, 18.0), f'{baseboard_h:.0f}" fiber cement baseboard\n(replaces furring + T&G)')
    _leader(ax, ((x_sauna_left + x_sauna_right) / 2, y_slab_top + mem_thk / 2), (x_sauna_left + 20.0, 12.0), "Liquid membrane on slab\nextends up baseboard")
    _leader(ax, ((duck_x0 + duck_x1) / 2, duck_y0 + duck_thk / 2), (x_sauna_left + 55.0, 24.0), "Duckboards on rubber feet\n(SS fasteners)")
    _leader(ax, ((x_polyR1 + x_stud0) / 2, 62.0), (x_dry1 + 16.0, 80.0), '2×4 framing\nR-13 batt optional')
    _leader(ax, (slab_x0 + 30.0, y_xps_bot + xps_under_thk / 2), (x_dry1 + 16.0, -24.0), f'R-10 XPS under slab\n(≥25 psi)')
    _leader(ax, (slab_x0 + 30.0, y_vapor_bot + vapor_sheet_thk / 2), (x_dry1 + 16.0, -44.0), "10 mil (min) polyethylene\nradon / vapor barrier")
    _leader(ax, (x_conc_int + thermal_break_thk / 2, y_slab_bot + slab_thk / 2), (x_sauna_left + 4.0, -14.0), f'Perimeter thermal break:\n{thermal_break_thk:.0f}" XPS + {sealant_thk:.1f}" polyurethane sealant')
    _leader(ax, (bench_x0 + bench_depth / 2, y_slab_top + upper_bench_top), (x_sauna_left + 30.0, 50.0), "Two-tier benches (Law of Löyly):\nupper ≈36\", lower ≈18\"")
    _leader(ax, (heater_x0 + heater_w / 2, heater_y0 + heater_h / 2), (x_sauna_left + 15.0, 32.0), "Electric sauna heater (shown)\nplace near airflow path")

    ax.set_title("Sauna Detail (IFC-driven)", fontsize=13, fontweight="bold", loc="center", pad=12)
    ax.text(x_conc_ext + 54.0, y_stone1 - 20.0, "Colin Catlin, 2026", ha="center", va="top", fontsize=7)

    ax.set_xlim(x_conc_ext - 34.0, x_dry1 + 30.0)
    ax.set_ylim(y_stone1 - 18.0, y_ceiling_top + 24.0)
    ax.set_aspect("equal")
    ax.axis("off")

    legend_patches = [
        Patch(facecolor=COL.concrete, edgecolor="black", label="Concrete"),
        Patch(facecolor=COL.wood, edgecolor="black", label="Wood framing / T&G / furring"),
        Patch(facecolor=COL.polyiso, edgecolor="black", label=f'Foil-faced polyiso ({polyiso_thk:.0f}\")'),
        Patch(facecolor=COL.xps, edgecolor="black", label="XPS (under slab / thermal break)"),
        Patch(facecolor=COL.membrane, edgecolor="black", label="Liquid membrane"),
        Patch(facecolor=COL.fiber_cement, edgecolor="black", label=f'Fiber cement baseboard ({baseboard_h:.0f}\")'),
        Patch(facecolor=COL.insulation, edgecolor="black", label="Cavity insulation (optional)"),
        Patch(facecolor=COL.aggregate, edgecolor="black", label="Washed stone / aggregate"),
    ]
    ax.legend(
        handles=legend_patches,
        loc="lower right",
        bbox_to_anchor=(0.8, 0.01),
        bbox_transform=ax.transAxes,
        frameon=True,
        fontsize=8.5,
        ncol=2,
        borderaxespad=0.0,
        handlelength=1.6,
        columnspacing=1.0,
    )

    # -----------------------
    # Notes panel
    # -----------------------
    ax_notes.set_xlim(0, 100)
    ax_notes.set_ylim(0, 150)
    ax_notes.axis("off")

    repo_root = Path(__file__).resolve().parents[1]
    raw_notes = load_markdown_notes(repo_root / "notes/sauna_basement_wall_detail.md")
    ax_notes.text(2, 146, _wrap_notes(raw_notes), fontsize=9, va="top", ha="left", family="monospace")

    out_path = Path("catlin_house/out/sauna_basement_wall_detail_ifc.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight", pad_inches=0.02)
    print(out_path)


if __name__ == "__main__":
    main()
