"""
Basement detail for combined sauna + shower, driven by IFC parameters.

Run:
  python catlin_house/build_catlin_house_ifc.py
  python catlin_house/sauna_shower_basement_detail_ifc.py

Output:
  catlin_house/out/sauna_shower_basement_detail_ifc.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Patch

import ifcopenshell
import ifcopenshell.util.element

from ifcplot.catlin_house import build_catlin_house_ifc
from ifcplot.detail_utils import COLORS, HATCHES, _dim_h, _dim_v, _leader, _poly, _rect, load_markdown_notes, _wrap_notes
from ifcplot.units import m_to_in


def _sloped_layer(x0: float, x1: float, y0: float, y1: float, thickness: float) -> np.ndarray:
    return np.array([[x0, y0], [x1, y1], [x1, y1 - thickness], [x0, y0 - thickness]], dtype=float)


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

    slab_p = basement_p["slab"]
    finish_p = sauna_p["finish"]
    structure_p = sauna_p["structure"]
    shower_p = sauna_p["shower"]
    benches_p = sauna_p["benches"]
    heater_p = sauna_p["heater"]

    fig = plt.figure(figsize=(20, 10))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.9, 1.1], wspace=0.06)
    ax = fig.add_subplot(gs[0, 0])
    ax_notes = fig.add_subplot(gs[0, 1])

    # -----------------------
    # Geometry (inches, schematic)
    # -----------------------
    total_L = m_to_in(float(plan_p["sauna_rect_m"]["w_m"]))  # 12'
    sauna_L = total_L - m_to_in(float(plan_p["shower_rect_m"]["w_m"]))  # 8'
    shower_L = total_L - sauna_L  # 4'

    total_h = float(structure_p["clear_height_in"])
    ceiling_slab_thk = float(structure_p["ceiling_slab_in"])

    slab_thk = float(slab_p["slab_thickness_in"])
    underfoam_thk = float(slab_p["xps_under_in"])
    poly_sheet_thk = float(slab_p["vapor_barrier_in"])
    stone_under_thk = float(slab_p["stone_under_in"])

    thermal_break_thk = float(slab_p["thermal_break_in"])
    sealant_thk = float(slab_p["sealant_in"])

    sauna_rise_far_end = float(sauna_p["sauna_floor_slope"]["rise_in"])  # total rise over sauna length
    shower_recess = m_to_in(float(plan_p["shower_rect_m"]["recess_m"])) if "recess_m" in plan_p["shower_rect_m"] else float(shower_p["recess_in"])

    # Shower finish build-up (schematic)
    shower_buildup_nom = 4.0
    tile_thk = float(shower_p["tile_in"])

    polyiso_thk = float(finish_p["polyiso_in"])
    furring_thk = float(finish_p["furring_in"])
    tg_thk = float(finish_p["tg_in"])
    baseboard_h = float(finish_p["baseboard_height_in"])
    baseboard_thk = furring_thk + tg_thk
    mem_thk = float(finish_p["membrane_in"])

    drywall_thk = 0.625
    shower_wall_backer_thk = float(shower_p["wall_backer_in"])

    glass_thk = float(shower_p["glass_in"])
    glass_gap_bot = float(shower_p["glass_gap_in"])

    hrv_diam = float(shower_p["hrv_duct_in"])

    # Reference levels
    y_main_ff = 0.0
    y_ceiling_bot = total_h
    y_ceiling_top = y_ceiling_bot + ceiling_slab_thk

    drop_depth = float(structure_p["drop_ceiling_depth_in"])
    y_drop_top = y_ceiling_bot - float(structure_p["drop_ceiling_gap_in"])
    y_drop_bot = y_drop_top - drop_depth
    glass_h = y_drop_bot - (y_main_ff + glass_gap_bot)

    y_ceil_poly0 = y_drop_bot - polyiso_thk
    y_ceil_fur0 = y_ceil_poly0 - furring_thk
    y_ceil_tg0 = y_ceil_fur0 - tg_thk

    # x reference
    x0 = 0.0
    x_part = sauna_L
    x1 = total_L

    # Sauna slab top is sloped: +rise at far end -> 0 at partition
    y_sauna_top_0 = y_main_ff + sauna_rise_far_end
    y_sauna_top_1 = y_main_ff

    # Shower slab (recessed)
    y_shower_slab_top = y_main_ff - shower_recess

    # Under-slab elevations
    y_sauna_slab_bot_0 = y_sauna_top_0 - slab_thk
    y_sauna_slab_bot_1 = y_sauna_top_1 - slab_thk
    y_shower_slab_bot = y_shower_slab_top - slab_thk

    y_sauna_poly_bot_0 = y_sauna_slab_bot_0 - poly_sheet_thk
    y_sauna_poly_bot_1 = y_sauna_slab_bot_1 - poly_sheet_thk
    y_shower_poly_bot = y_shower_slab_bot - poly_sheet_thk

    y_sauna_foam_bot_0 = y_sauna_poly_bot_0 - underfoam_thk
    y_sauna_foam_bot_1 = y_sauna_poly_bot_1 - underfoam_thk
    y_shower_foam_bot = y_shower_poly_bot - underfoam_thk

    y_sauna_stone_bot_0 = y_sauna_foam_bot_0 - stone_under_thk
    y_sauna_stone_bot_1 = y_sauna_foam_bot_1 - stone_under_thk
    y_shower_stone_bot = y_shower_foam_bot - stone_under_thk

    # -----------------------
    # Slab + under-slab assemblies
    # -----------------------
    _poly(ax, _sloped_layer(x0, x_part, y_sauna_top_0, y_sauna_top_1, slab_thk), fc=COLORS.concrete, z=4)
    _poly(ax, _sloped_layer(x0, x_part, y_sauna_slab_bot_0, y_sauna_slab_bot_1, poly_sheet_thk), fc=COLORS.glass, lw=0.7, z=3)
    _poly(ax, _sloped_layer(x0, x_part, y_sauna_poly_bot_0, y_sauna_poly_bot_1, underfoam_thk), fc=COLORS.xps, lw=1.0, z=2)
    _poly(ax, _sloped_layer(x0, x_part, y_sauna_foam_bot_0, y_sauna_foam_bot_1, stone_under_thk), fc=COLORS.aggregate, lw=0.9, hatch=HATCHES.gravel, z=1)

    _rect(ax, x_part, y_shower_slab_top - slab_thk, shower_L, slab_thk, fc=COLORS.concrete, z=4)
    _rect(ax, x_part, y_shower_slab_bot - poly_sheet_thk, shower_L, poly_sheet_thk, fc=COLORS.glass, lw=0.7, z=3)
    _rect(ax, x_part, y_shower_poly_bot - underfoam_thk, shower_L, underfoam_thk, fc=COLORS.xps, lw=1.0, z=2)
    _rect(ax, x_part, y_shower_foam_bot - stone_under_thk, shower_L, stone_under_thk, fc=COLORS.aggregate, lw=0.9, hatch=HATCHES.gravel, z=1)

    # Thermal break / isolation joint around perimeter (left + right shown)
    _rect(ax, x0 - thermal_break_thk, y_sauna_top_0 - slab_thk, thermal_break_thk, slab_thk, fc=COLORS.xps, lw=1.0, z=5)
    _rect(ax, x0 - thermal_break_thk, y_sauna_top_0, thermal_break_thk, sealant_thk, fc=COLORS.sealant, ec="black", lw=0.9, z=6)
    _rect(ax, x1, y_shower_slab_top - slab_thk, thermal_break_thk, slab_thk, fc=COLORS.xps, lw=1.0, z=5)
    _rect(ax, x1, y_main_ff, thermal_break_thk, sealant_thk, fc=COLORS.sealant, ec="black", lw=0.9, z=6)

    # Suggested adjacent main basement slab (dashed, flat)
    main_slab_w = 36.0
    main_x0 = x1 + thermal_break_thk
    y_main_slab_bot = y_main_ff - slab_thk
    y_main_poly_bot = y_main_slab_bot - poly_sheet_thk
    y_main_foam_bot = y_main_poly_bot - underfoam_thk
    y_main_stone_bot = y_main_foam_bot - stone_under_thk
    _rect(ax, main_x0, y_main_slab_bot, main_slab_w, slab_thk, fc=COLORS.concrete, lw=1.1, z=4)
    _rect(ax, main_x0, y_main_poly_bot, main_slab_w, poly_sheet_thk, fc=COLORS.glass, lw=0.7, z=3)
    _rect(ax, main_x0, y_main_foam_bot, main_slab_w, underfoam_thk, fc=COLORS.xps, lw=1.0, z=2)
    _rect(ax, main_x0, y_main_stone_bot, main_slab_w, stone_under_thk, fc=COLORS.aggregate, lw=0.9, hatch=HATCHES.gravel, z=1)

    # Concrete step face at sauna/shower transition (recess)
    _rect(ax, x_part - 2.0, y_shower_slab_top, 2.0, (y_sauna_top_1 - y_shower_slab_top), fc=COLORS.concrete, lw=1.2, z=5)
    _rect(ax, x_part - 2.0, y_shower_slab_bot, 2.0, (y_shower_slab_top - y_shower_slab_bot), fc=COLORS.concrete, lw=1.2, z=5)

    # -----------------------
    # Sauna finishes (schematic)
    # -----------------------
    _poly(ax, _sloped_layer(x0 + 2.0, x_part - 2.0, y_sauna_top_0, y_sauna_top_1, mem_thk), fc=COLORS.membrane, lw=0.8, z=10)

    duck_thk = 1.0
    foot_h = 0.5
    duck_x0 = x0 + 4.0
    duck_x1 = x_part - 4.0
    duck_y0_0 = y_sauna_top_0 + mem_thk + foot_h
    duck_y0_1 = y_sauna_top_1 + mem_thk + foot_h
    _poly(ax, _sloped_layer(duck_x0, duck_x1, duck_y0_0, duck_y0_1, duck_thk), fc=COLORS.wood, lw=1.0, hatch=HATCHES.compacted, z=11)
    for fx in [duck_x0 + 6.0, duck_x1 - 6.0]:
        fy0 = y_sauna_top_0 + (fx - x0) * (y_sauna_top_1 - y_sauna_top_0) / (x_part - x0) + mem_thk
        _rect(ax, fx, fy0, 1.2, foot_h, fc=COLORS.rubber, ec="black", lw=0.8, z=12)

    # -----------------------
    # Sauna benches (schematic, two-tier along length)
    # -----------------------
    bench_thk = float(benches_p["thickness_in"])
    lower_bench_top = float(benches_p["lower_top_in"])
    upper_bench_top = float(benches_p["upper_top_in"])
    bench_setback = 2.0
    bench_x0 = x0 + bench_setback
    bench_x1 = x_part - bench_setback - 4.0
    bench_length = bench_x1 - bench_x0

    lower_bench_y = y_main_ff + lower_bench_top - bench_thk
    _rect(ax, bench_x0, lower_bench_y, bench_length, bench_thk, fc=COLORS.wood, lw=1.0, z=12)
    upper_bench_y = y_main_ff + upper_bench_top - bench_thk
    _rect(ax, bench_x0, upper_bench_y, bench_length * 0.7, bench_thk, fc=COLORS.wood, lw=1.0, z=12)

    # -----------------------
    # Sauna heater (schematic)
    # -----------------------
    heater_w = float(heater_p["width_in"])
    heater_h = float(heater_p["height_in"])
    heater_x0 = x0 + 6.0
    heater_y0 = y_main_ff + mem_thk
    _rect(ax, heater_x0, heater_y0, heater_w, heater_h, fc=COLORS.equipment, ec="black", lw=1.0, hatch=HATCHES.dense_plus, z=12)

    # HRV exhaust above heater (pipe in wall)
    hrv_exhaust_x = x0 - 0.5
    hrv_exhaust_y = heater_y0 + heater_h + 4.0
    _rect(ax, hrv_exhaust_x, hrv_exhaust_y, hrv_diam, hrv_diam, fc="white", ec="black", lw=1.0, z=13)
    ax.add_patch(Circle((hrv_exhaust_x + hrv_diam / 2, hrv_exhaust_y + hrv_diam / 2), radius=hrv_diam / 2 - 0.2, facecolor=COLORS.metal_dark, edgecolor="none", alpha=0.6, zorder=13))

    # -----------------------
    # Shower finishes (schematic)
    # -----------------------
    _rect(ax, x_part, y_shower_slab_top, shower_wall_backer_thk, shower_recess, fc=COLORS.polyiso, lw=1.2, z=15)
    _rect(ax, x_part - tile_thk, y_shower_slab_top, tile_thk, shower_recess, fc=COLORS.tile, lw=1.2, z=15)

    shower_fill_thk = max(shower_buildup_nom - shower_wall_backer_thk - tile_thk, 0)
    _rect(ax, x_part, y_shower_slab_top, shower_L, shower_wall_backer_thk, fc=COLORS.polyiso, lw=1.0, hatch=HATCHES.compacted, z=9)
    if shower_fill_thk > 0:
        _rect(ax, x_part, y_shower_slab_top + shower_wall_backer_thk, shower_L, shower_fill_thk, fc=COLORS.polyiso, lw=1.0, hatch=HATCHES.compacted, z=9)
    _rect(ax, x_part, y_shower_slab_top + shower_buildup_nom - tile_thk, shower_L, tile_thk, fc=COLORS.tile, lw=1.0, z=10)

    # Shower entry door (shown in section, dotted)
    door_width = 36.0
    door_height = 80.0
    door_x0 = x_part + (shower_L - door_width) / 2
    _rect(ax, door_x0, y_main_ff, door_width, door_height, fc="none", ec="black", lw=1.0, ls=":", z=15)

    # Glass partition (enclosure wall + door; schematic in section)
    glass_x0 = x_part - glass_thk / 2
    glass_y0 = y_main_ff + glass_gap_bot
    _rect(ax, glass_x0, glass_y0, glass_thk, glass_h, fc=COLORS.glass, lw=1.1, z=20, alpha=0.55)

    # Door handle
    handle_w = 0.65
    handle_h = 12.0
    handle_y0 = y_main_ff + 40.0
    _rect(ax, x_part + 1.0, handle_y0, handle_w, handle_h, fc=COLORS.metal, lw=0.9, z=21)
    ax.plot([x_part + glass_thk / 2, x_part + 1.0], [handle_y0 + handle_h / 2, handle_y0 + handle_h / 2], color="black", lw=0.9, zorder=21)

    # -----------------------
    # Suggestive end walls (schematic)
    # -----------------------
    wall_y0 = y_main_ff
    wall_y1 = y_ceiling_bot

    # HRV intake on shower wall (halfway up)
    hrv_intake_x = x1 - shower_wall_backer_thk - tile_thk + 0.5
    hrv_intake_y = y_main_ff + (y_ceiling_bot - y_main_ff) / 2 - hrv_diam / 2
    _rect(ax, hrv_intake_x, hrv_intake_y, hrv_diam, hrv_diam, fc="white", ec="black", lw=1.0, z=13)
    ax.add_patch(Circle((hrv_intake_x + hrv_diam / 2, hrv_intake_y + hrv_diam / 2), radius=hrv_diam / 2 - 0.2, facecolor=COLORS.metal_dark, edgecolor="none", alpha=0.6, zorder=13))

    # Sauna end wall (left)
    x_sauna_tg0 = x0 - tg_thk
    x_sauna_fur0 = x_sauna_tg0 - furring_thk
    x_sauna_poly0 = x_sauna_fur0 - polyiso_thk
    wall_thk = 6.0
    _rect(ax, x0 - wall_thk, wall_y0, (x_sauna_poly0 - (x0 - wall_thk)), wall_y1 - wall_y0, fc=COLORS.insulation, lw=1.0, hatch=HATCHES.compacted, z=0)
    _rect(ax, x_sauna_poly0, wall_y0, polyiso_thk, y_drop_bot - wall_y0, fc=COLORS.polyiso, lw=1.0, z=2)
    _rect(ax, x_sauna_fur0, baseboard_h, furring_thk, y_ceil_tg0 - baseboard_h, fc=COLORS.wood, lw=1.0, hatch=HATCHES.diagonal, z=3)
    _rect(ax, x_sauna_tg0, baseboard_h, tg_thk, y_ceil_tg0 - baseboard_h, fc=COLORS.wood, lw=1.1, z=4)
    _rect(ax, x_sauna_fur0, wall_y0, baseboard_thk, baseboard_h, fc=COLORS.fiber_cement, lw=1.1, z=5)

    # Shower end wall (right) with foam tile backer to ceiling
    stud_depth = 3.5
    _rect(ax, x1, wall_y0 - shower_recess, stud_depth, wall_y1 - (wall_y0 - shower_recess), fc=COLORS.insulation, lw=1.0, hatch=HATCHES.compacted, z=0)
    _rect(ax, x1, wall_y0 - shower_recess, shower_wall_backer_thk, wall_y1 - (wall_y0 - shower_recess), fc=COLORS.polyiso, lw=1.0, z=2)
    _rect(ax, x1 - shower_wall_backer_thk, wall_y0 - shower_recess, tile_thk, wall_y1 - (wall_y0 - shower_recess), fc=COLORS.tile, lw=1.0, z=3)
    _rect(ax, x1 + stud_depth, wall_y0 - shower_recess, drywall_thk, wall_y1 - (wall_y0 - shower_recess), fc=COLORS.drywall, lw=1.0, z=1)

    # Ceiling slab above (Catlin House: concrete slab at main floor)
    _rect(ax, x0 - 10.0, y_ceiling_bot, (x1 - x0) + 20.0, ceiling_slab_thk, fc=COLORS.concrete, lw=1.2, z=2)

    # Dropped ceiling framing below ceiling slab
    drop_frame_x0 = x0 - wall_thk
    drop_frame_w = (x1 - x0) + wall_thk + stud_depth + drywall_thk
    _rect(ax, drop_frame_x0, y_drop_bot, drop_frame_w, drop_depth, fc=COLORS.wood, lw=1.1, hatch=HATCHES.cross, z=4, alpha=0.9)
    poly_extend_left = 2.0
    _rect(ax, x0 - poly_extend_left, y_ceil_poly0, (x1 - x0) + poly_extend_left, polyiso_thk, fc=COLORS.polyiso, lw=1.0, z=5)
    _rect(ax, x0, y_ceil_fur0, (x1 - x0), furring_thk, fc=COLORS.wood, lw=1.0, hatch=HATCHES.diagonal, z=6)
    _rect(ax, x0, y_ceil_tg0, (x1 - x0), tg_thk, fc=COLORS.wood, lw=1.1, z=7)

    # -----------------------
    # Inset: shower transverse slope to drain (8' width)
    # -----------------------
    ax_in = ax.inset_axes([0.03, -0.06, 0.24, 0.18])
    ax_in.axis("off")
    ax_in.set_facecolor("white")
    ax_in.patch.set_alpha(0.97)
    for spine in ax_in.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.8)
        spine.set_edgecolor(COLORS.metal)

    sh_w = 96.0
    y_ff = 0.0
    y_slab_top = -shower_recess
    y_slab_bot = y_slab_top - slab_thk

    slope = 0.25 / 12.0  # 1/4" per foot
    drop = slope * sh_w
    y_tile_at_door = y_ff
    y_tile_at_drain = y_ff - drop

    _rect(ax_in, 0.0, y_slab_bot, sh_w, slab_thk, fc=COLORS.concrete, lw=1.0, z=2)
    _rect(ax_in, 0.0, y_slab_bot - poly_sheet_thk, sh_w, poly_sheet_thk, fc=COLORS.glass, lw=0.6, z=1)
    _rect(ax_in, 0.0, y_slab_bot - poly_sheet_thk - underfoam_thk, sh_w, underfoam_thk, fc=COLORS.xps, lw=0.8, z=1)

    buildup0 = y_tile_at_door - y_slab_top - tile_thk
    buildup1 = y_tile_at_drain - y_slab_top - tile_thk
    _poly(
        ax_in,
        np.array([[0.0, y_tile_at_door - tile_thk], [sh_w, y_tile_at_drain - tile_thk], [sh_w, y_slab_top], [0.0, y_slab_top]]),
        fc=COLORS.polyiso,
        ec="black",
        lw=0.9,
        z=3,
        alpha=0.55,
    )
    _poly(
        ax_in,
        np.array([[0.0, y_tile_at_door], [sh_w, y_tile_at_drain], [sh_w, y_tile_at_drain - tile_thk], [0.0, y_tile_at_door - tile_thk]]),
        fc=COLORS.tile,
        ec="black",
        lw=0.9,
        z=4,
    )
    drain_r = 2.2
    ax_in.add_patch(Circle((sh_w - 2.0, y_tile_at_drain - tile_thk / 2), radius=drain_r, facecolor="white", edgecolor="black", lw=1.0, zorder=6))
    ax_in.add_patch(Circle((sh_w - 2.0, y_tile_at_drain - tile_thk / 2), radius=drain_r - 0.3, facecolor=COLORS.metal_dark, edgecolor="none", alpha=0.75, zorder=6))
    ax_in.set_xlim(-6.0, sh_w + 10.0)
    ax_in.set_ylim(-12.0, 12.0)
    ax_in.text(sh_w / 2, -11.5, "Shower floor slope (transverse section)", fontsize=9, ha="center", va="top")

    # -----------------------
    # Drain + pipe (schematic, in main section)
    # -----------------------
    drain_x = x_part + shower_L / 2
    pipe_diam = 2.0
    pipe_x0 = drain_x - pipe_diam / 2
    pipe_y_top = y_main_ff - tile_thk
    pipe_y_bot = y_shower_stone_bot + 0.5
    _rect(ax, pipe_x0, pipe_y_bot, pipe_diam, pipe_y_top - pipe_y_bot, fc=COLORS.metal, lw=0.9, z=25, alpha=0.85)

    # -----------------------
    # Leaders / callouts
    # -----------------------
    _leader(ax, (x_part + 18.0, y_main_ff - 1.0), (x_part + 18.0, 18.0), f"Shower area ({shower_L / 12:.0f}'-0\") recessed slab\n(-{shower_recess:.0f}\" to top of concrete)", ha="left")
    _leader(ax, (x0 + 18.0, (y_sauna_top_0 + y_sauna_top_1) / 2), (x0 + 10.0, 42.0), 'Sauna floor slopes 1/8" per ft\n(1" over 8\') toward shower', ha="left")
    _leader(ax, (x_part, glass_y0 + 12.0), (x_part - 36.0, 84.0), 'Glass partition wall + 36" door\n1/2" tempered glass\nhandle shown; base spigots not shown', ha="right")
    _leader(ax, (x_part, y_main_ff + glass_gap_bot / 2), (x_part - 34.0, 14.0), '1" gap under partition wall\n(air + water flow; maintain cleanable edge)', ha="right")
    _leader(ax, (x1 - 1.0, 66.0), (x1 + 28.0, 80.0), "Shower walls: foam tile backer\n(GoBoard/polyiso preferred)\nup to ceiling", ha="left")
    _leader(ax, (drain_x, pipe_y_top - 0.2), (x1 + 26.0, 44.0), "Shower drain pipe (schematic)\nroute to trap/vent per plumbing", ha="left")
    _leader(ax, (bench_x0 + 18.0, upper_bench_y + bench_thk / 2), (x0 + 48.0, 52.0), "Two-tier benches (Law of Löyly):\nupper ≈36\", lower ≈18\"", ha="left")
    _leader(ax, (heater_x0 + heater_w / 2, heater_y0 + heater_h / 2), (x0 + 32.0, 32.0), "Sauna heater (electric)\nplace near airflow path", ha="left")
    _leader(ax, (hrv_exhaust_x + hrv_diam / 2, hrv_exhaust_y + hrv_diam / 2), (x0 + 32.0, 42.0), "HRV exhaust\n(low, above heater)", ha="left")
    _leader(ax, (hrv_intake_x + hrv_diam / 2, hrv_intake_y + hrv_diam / 2), (x1 + 26.0, 60.0), "HRV intake\n(mid-height)", ha="left")
    _leader(ax, (x0 - thermal_break_thk / 2, y_sauna_top_0 + 0.2), (x0 + 22.0, 96.0), f'Thermal break: {thermal_break_thk:.0f}" XPS + sealant\naround shower/sauna perimeter', ha="left")

    # Key dimensions
    _dim_h(ax, x0, x_part, -28.0, '8\'-0" sauna length')
    _dim_h(ax, x_part, x1, -28.0, '4\'-0" shower length')
    _dim_h(ax, x0, x1, -38.0, '12\'-0" overall length')
    _dim_v(ax, y_main_ff - shower_recess, y_main_ff, x1 + 10.0, f'{shower_recess:.0f}" shower recess')

    ax.set_title("Sauna + Shower Basement Detail (IFC-driven)", fontsize=13, fontweight="bold", loc="center", pad=12)
    ax.text(x0 + total_L / 2, y_shower_stone_bot - 10.0, "Colin Catlin, 2026", ha="center", va="top", fontsize=7)

    ax.set_xlim(x0 - 28.0, x1 + 44.0)
    ax.set_ylim(y_shower_stone_bot - 16.0, y_ceiling_top + 22.0)
    ax.set_aspect("equal")
    ax.axis("off")

    legend_patches = [
        Patch(facecolor=COLORS.concrete, edgecolor="black", label="Concrete"),
        Patch(facecolor=COLORS.xps, edgecolor="black", label=f'Foam under slab / XPS ({underfoam_thk:.0f}\")'),
        Patch(facecolor=COLORS.glass, edgecolor="black", label="Vapor barrier (schematic)"),
        Patch(facecolor=COLORS.aggregate, edgecolor="black", label="Washed stone / aggregate"),
        Patch(facecolor=COLORS.membrane, edgecolor="black", label="Liquid membrane"),
        Patch(facecolor=COLORS.polyiso, edgecolor="black", label="Foam board / wedges / backer"),
        Patch(facecolor=COLORS.tile, edgecolor="black", label="Tile / finish layer"),
        Patch(facecolor=COLORS.glass, edgecolor="black", label="Glass (partition)"),
    ]
    ax.legend(
        handles=legend_patches,
        loc="lower right",
        bbox_to_anchor=(0.92, 0.01),
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
    ax_notes.set_ylim(0, 165)
    ax_notes.axis("off")

    repo_root = Path(__file__).resolve().parents[1]
    raw_notes = load_markdown_notes(repo_root / "notes/sauna_shower_basement_detail.md")
    ax_notes.text(2, 162, _wrap_notes(raw_notes), fontsize=9, va="top", ha="left", family="monospace")

    out_path = Path("catlin_house/out/sauna_shower_basement_detail_ifc.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight", pad_inches=0.02)
    print(out_path)


if __name__ == "__main__":
    main()
