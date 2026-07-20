"""
Basement floor plan derived from the generated IFC (placeholder plan geometry).

Run:
  python catlin_house/build_catlin_house_ifc.py
  python catlin_house/basement_floor_plan_ifc.py

Output:
  catlin_house/out/basement_floor_plan_ifc.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
import numpy as np

import ifcopenshell
import ifcopenshell.util.element

from ifcplot.units import M_PER_FT

# Colors consistent with other details
COL_CONC = "#BFBFBF"
COL_SAUNA = "#DDECC8"
COL_SHOWER = "#BEE3F8"
COL_STAIR = "#F5F5F5"


def _get_house_plan_params(ifc_path: Path) -> dict:
    f = ifcopenshell.open(str(ifc_path))
    house = next(b for b in f.by_type("IfcBuilding") if b.Name == "House")
    psets = ifcopenshell.util.element.get_psets(house)
    raw = psets.get("Pset_ifcPlot_BasementPlan", {}).get("ParamsJSON")
    if not raw:
        raise RuntimeError("Missing `Pset_ifcPlot_BasementPlan.ParamsJSON` on building 'House'.")
    return json.loads(raw)


def main() -> None:
    ifc_path = Path("catlin_house/out/catlin_house.ifc")
    params = _get_house_plan_params(ifc_path)

    size_m = float(params["house_size_m"])
    wall_thk_m = float(params["basement_wall_thickness_m"])
    grid_m = float(params["basement_grid_m"])

    stair = params["stair_opening_rect_m"]
    sauna = params["sauna_rect_m"]
    shower = params["shower_rect_m"]

    size_ft = size_m / M_PER_FT
    wall_thk_ft = wall_thk_m / M_PER_FT
    grid_ft = grid_m / M_PER_FT

    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect("equal")

    # Perimeter walls (filled concrete)
    # South wall
    ax.add_patch(Rectangle((0, 0), size_ft, wall_thk_ft, facecolor=COL_CONC, edgecolor="black", lw=1.5))
    # North wall
    ax.add_patch(Rectangle((0, size_ft - wall_thk_ft), size_ft, wall_thk_ft, facecolor=COL_CONC, edgecolor="black", lw=1.5))
    # West wall
    ax.add_patch(Rectangle((0, wall_thk_ft), wall_thk_ft, size_ft - 2 * wall_thk_ft, facecolor=COL_CONC, edgecolor="black", lw=1.5))
    # East wall
    ax.add_patch(Rectangle((size_ft - wall_thk_ft, wall_thk_ft), wall_thk_ft, size_ft - 2 * wall_thk_ft, facecolor=COL_CONC, edgecolor="black", lw=1.5))

    # Center concrete cross walls at 18' OC
    # N-S wall (vertical on plan)
    ax.add_patch(Rectangle((grid_ft - wall_thk_ft / 2, wall_thk_ft), wall_thk_ft, size_ft - 2 * wall_thk_ft, facecolor=COL_CONC, edgecolor="black", lw=1.0))
    # E-W wall (horizontal on plan)
    ax.add_patch(Rectangle((wall_thk_ft, grid_ft - wall_thk_ft / 2), size_ft - 2 * wall_thk_ft, wall_thk_ft, facecolor=COL_CONC, edgecolor="black", lw=1.0))

    # Quadrant labels
    for qx, qy, label in [
        (grid_ft / 2, grid_ft / 2, "SW"),
        (grid_ft + (size_ft - grid_ft) / 2, grid_ft / 2, "SE"),
        (grid_ft / 2, grid_ft + (size_ft - grid_ft) / 2, "NW"),
        (grid_ft + (size_ft - grid_ft) / 2, grid_ft + (size_ft - grid_ft) / 2, "NE"),
    ]:
        ax.text(qx, qy, label, ha="center", va="center", fontsize=14, color="#888888", fontweight="bold", alpha=0.5)

    # Stair opening (dashed)
    stair_x0 = float(stair["x0_m"]) / M_PER_FT
    stair_y0 = float(stair["y0_m"]) / M_PER_FT
    stair_w = float(stair["w_m"]) / M_PER_FT
    stair_h = float(stair["h_m"]) / M_PER_FT
    ax.add_patch(Rectangle((stair_x0, stair_y0), stair_w, stair_h, facecolor=COL_STAIR, edgecolor="black", lw=1.4, linestyle=(0, (6, 4))))
    ax.text(stair_x0 + stair_w / 2, stair_y0 + stair_h / 2, "Stairs\n(opening above)", ha="center", va="center", fontsize=10)
    # Stair arrow (direction of travel up)
    ax.annotate("", xy=(stair_x0 + stair_w / 2, stair_y0 + stair_h - 0.5), xytext=(stair_x0 + stair_w / 2, stair_y0 + 0.5),
                arrowprops=dict(arrowstyle="-|>", lw=1.2, color="black"))
    ax.text(stair_x0 + stair_w / 2, stair_y0 + 0.8, "UP", ha="center", va="bottom", fontsize=8)

    # Stair side wall (8") west of opening
    side_wall_thk_ft = (8.0 * 0.0254) / M_PER_FT
    ax.add_patch(Rectangle((stair_x0 - side_wall_thk_ft, stair_y0), side_wall_thk_ft, stair_h, facecolor=COL_CONC, edgecolor="black", lw=1.0))

    # Sauna + shower zone
    sauna_x0 = float(sauna["x0_m"]) / M_PER_FT
    sauna_y0 = float(sauna["y0_m"]) / M_PER_FT
    sauna_w = float(sauna["w_m"]) / M_PER_FT
    sauna_h = float(sauna["h_m"]) / M_PER_FT
    ax.add_patch(Rectangle((sauna_x0, sauna_y0), sauna_w, sauna_h, facecolor=COL_SAUNA, edgecolor="black", lw=1.0, alpha=0.5))
    ax.text(sauna_x0 + sauna_w / 2, sauna_y0 + sauna_h / 2, "Sauna + Shower\n(placeholder)", ha="center", va="center", fontsize=10)

    # Shower recess (4" lower)
    sh_x0 = float(shower["x0_m"]) / M_PER_FT
    sh_y0 = float(shower["y0_m"]) / M_PER_FT
    sh_w = float(shower["w_m"]) / M_PER_FT
    sh_h = float(shower["h_m"]) / M_PER_FT
    ax.add_patch(Rectangle((sh_x0, sh_y0), sh_w, sh_h, facecolor=COL_SHOWER, edgecolor="black", lw=1.0, alpha=0.7))
    ax.text(sh_x0 + sh_w / 2, sh_y0 + sh_h / 2, 'Shower\nrecess\n(-4")', ha="center", va="center", fontsize=9)

    # Dimension annotations
    # Overall size
    ax.annotate("", xy=(0, -1.5), xytext=(size_ft, -1.5), arrowprops=dict(arrowstyle="<->", lw=1.0))
    ax.text(size_ft / 2, -2.0, f"{size_ft:.0f}'", ha="center", va="top", fontsize=10)
    ax.annotate("", xy=(-1.5, 0), xytext=(-1.5, size_ft), arrowprops=dict(arrowstyle="<->", lw=1.0))
    ax.text(-2.0, size_ft / 2, f"{size_ft:.0f}'", ha="right", va="center", fontsize=10, rotation=90)
    
    # Grid dimension
    ax.annotate("", xy=(wall_thk_ft, size_ft + 1.0), xytext=(grid_ft, size_ft + 1.0), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text((wall_thk_ft + grid_ft) / 2, size_ft + 1.3, f"{grid_ft - wall_thk_ft:.0f}'", ha="center", va="bottom", fontsize=9)

    # Title and legend
    ax.set_title("House Basement Floor Plan (IFC-driven)", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Feet (east →)")
    ax.set_ylabel("Feet (north ↑)")
    ax.set_xlim(-4, size_ft + 4)
    ax.set_ylim(-4, size_ft + 4)
    ax.grid(True, lw=0.5, alpha=0.25)

    # North arrow
    ax.annotate("N", xy=(size_ft + 2.0, size_ft - 2.0), xytext=(size_ft + 2.0, size_ft - 8.0),
                fontsize=12, fontweight="bold", ha="center", va="bottom",
                arrowprops=dict(arrowstyle="-|>", lw=1.5))

    # Legend
    legend_patches = [
        Patch(facecolor=COL_CONC, edgecolor="black", label=f'Concrete wall ({wall_thk_ft:.0f}")'),
        Patch(facecolor=COL_STAIR, edgecolor="black", linestyle="--", label="Stair opening"),
        Patch(facecolor=COL_SAUNA, edgecolor="black", alpha=0.5, label="Sauna zone"),
        Patch(facecolor=COL_SHOWER, edgecolor="black", alpha=0.7, label="Shower recess"),
    ]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=9, frameon=True)
    
    ax.text(0, -3.5, "Colin Catlin, 2026", ha="left", va="top", fontsize=7)

    out_path = Path("catlin_house/out/basement_floor_plan_ifc.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight", pad_inches=0.05)
    print(out_path)


if __name__ == "__main__":
    main()
