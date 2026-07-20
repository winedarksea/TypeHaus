"""
Basement concrete wall transitioning to wood-framed exterior wall above, driven by IFC parameters.

Run:
  python catlin_house/build_catlin_house_ifc.py
  python catlin_house/basement_to_framed_wall_detail_ifc.py

Output:
  catlin_house/out/basement_to_framed_wall_detail_ifc.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch, Polygon

import ifcopenshell
import ifcopenshell.util.element

from ifcplot.catlin_house import build_catlin_house_ifc
from ifcplot.detail_utils import (
    COLORS,
    HATCHES,
    BasementConcreteWallAssembly,
    ExteriorWoodWallAssembly,
    _dim_h,
    _flashing,
    _french_drain,
    _leader,
    _lumber,
    _path_from_steps,
    _rect,
    _slab_assembly,
    load_markdown_notes,
    _wrap_notes,
)


def _ensure_ifc_has_house_psets(ifc_path: Path, *, required: list[str]) -> None:
    """
    Ensure `ifc_path` exists and contains the required JSON psets on building 'House'.

    This keeps the detail scripts resilient when the IFC on disk is stale (e.g. built before
    new psets were added).
    """

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


def _get_house_pset_params(ifc_path: Path, *, pset_name: str) -> dict:
    f = ifcopenshell.open(str(ifc_path))
    house = next(b for b in f.by_type("IfcBuilding") if b.Name == "House")
    psets = ifcopenshell.util.element.get_psets(house)
    raw = psets.get(pset_name, {}).get("ParamsJSON")
    if not raw:
        raise RuntimeError(f"Missing `{pset_name}.ParamsJSON` on building 'House'.")
    return json.loads(raw)


def main() -> None:
    ifc_path = Path("catlin_house/out/catlin_house.ifc")
    _ensure_ifc_has_house_psets(
        ifc_path,
        required=[
            "Pset_ifcPlot_BasementConstruction",
            "Pset_ifcPlot_BasementToFramedWallDetail",
        ],
    )

    basement_p = _get_house_pset_params(ifc_path, pset_name="Pset_ifcPlot_BasementConstruction")
    detail_p = _get_house_pset_params(ifc_path, pset_name="Pset_ifcPlot_BasementToFramedWallDetail")

    foundation_p = basement_p["foundation"]
    slab_p = basement_p["slab"]

    wall_p = detail_p["wall"]
    basement_ext_p = detail_p["basement_exterior"]
    sill_p = detail_p["sill"]
    view_p = detail_p["detail_view"]

    fig = plt.figure(figsize=(20, 10))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.85, 1.15], wspace=0.06)
    ax = fig.add_subplot(gs[0, 0])
    ax_notes = fig.add_subplot(gs[0, 1])

    # Units: inches (schematic)
    grade_y = float(view_p.get("grade_offset_in", 12.0))  # raised to reduce figure height
    basement_above_grade = float(view_p.get("basement_above_grade_in", 24.0))
    basement_wall_height = float(view_p.get("basement_wall_show_height_in", 48.0))

    y_conc_top = grade_y + basement_above_grade
    y_conc_bot = y_conc_top - basement_wall_height

    # Wall assemblies (x: interior negative, exterior positive)
    drywall = float(wall_p["drywall_in"])
    stud_depth = float(wall_p["stud_depth_in"])
    sheathing = float(wall_p["sheathing_in"])
    membrane_thk = float(wall_p.get("membrane_in", 0.0))
    polyiso_wall = float(wall_p["polyiso_in"])
    eps_wall = float(wall_p["eps_in"])
    furring = float(wall_p["furring_in"])
    cladding = float(wall_p["cladding_in"])

    conc_wall_thk = float(foundation_p["wall_thickness_in"])

    wall_layers = ExteriorWoodWallAssembly(
        drywall=drywall,
        stud_depth=stud_depth,
        sheathing=sheathing,
        membrane=membrane_thk,
        polyiso=polyiso_wall,
        eps=eps_wall,
        furring=furring,
        cladding=cladding,
        x_clad1=1.0,
    ).coords()
    x_dry0, _x_dry1 = wall_layers["drywall"]
    x_stud0, _x_stud1 = wall_layers["stud"]
    x_sheath0, _x_sheath1 = wall_layers["sheathing"]
    x_mem0, x_mem1 = wall_layers["membrane"]
    x_poly0, _x_poly1 = wall_layers["polyiso"]
    x_eps0, x_eps1 = wall_layers["eps"]
    x_fur0, x_fur1 = wall_layers["furring"]
    x_clad0, x_clad1 = wall_layers["cladding"]
    x_foam_outer = x_eps1

    conc_layers = BasementConcreteWallAssembly(
        conc_thk=conc_wall_thk,
        membrane=membrane_thk,
        polyiso=polyiso_wall,
        eps=eps_wall,
        furring=furring,
        cladding=cladding,
        x_clad1=x_clad1,
    ).coords()
    x_conc_int, x_conc_ext = conc_layers["concrete"]

    # Interior slab assembly (at basement floor level)
    slab_thk = float(slab_p["slab_thickness_in"])
    xps_under_thk = float(slab_p["xps_under_in"])
    poly_sheet_thk = float(slab_p["vapor_barrier_in"])
    stone_under_slab = float(slab_p["stone_under_in"])
    thermal_break_thk = float(slab_p["thermal_break_in"])
    sealant_thk = float(slab_p["sealant_in"])
    slab_width = float(view_p.get("slab_show_width_in", 18.0))

    # Footing / base (schematic)
    footing_w = float(foundation_p["footing_width_in"])
    footing_d = float(foundation_p["footing_thickness_in"])
    stone_base_thk = float(foundation_p["stone_base_thickness_in"])
    stone_base_extra = float(foundation_p["stone_base_extra_in"])
    drain_diam = float(foundation_p["french_drain_diameter_in"])

    # Sill assembly (schematic)
    sill_gasket = float(sill_p["gasket_in"])
    sill_plate = float(sill_p["plate_in"])
    y_sill0 = y_conc_top
    y_gasket1 = y_sill0 + sill_gasket
    y_sill1 = y_gasket1 + sill_plate

    # How much of the framed wall to show above the sill
    wall_show_h = 46.0
    y_wall_top = y_sill1 + wall_show_h

    # Colors
    COL = COLORS
    COL_WOOD = COL.wood
    COL_CONC = COL.concrete
    COL_SHEATH = COL.sheathing
    COL_MEM = COL.membrane
    COL_XPS = COL.xps
    COL_EPS = COL.eps
    COL_POLYISO = COL.polyiso
    COL_SOIL = COL.soil
    COL_METAL = COL.metal_dark
    COL_FLASH = COL.metal
    COL_SPRAY = COL.spray_foam
    COL_INSUL = COL.insulation
    COL_RIVER_ROCK = COL.river_rock

    # -----------------------
    # Exterior grade / soil
    # -----------------------
    grade_line = np.array([[x_clad1 + 0.2, grade_y], [x_clad1 + 32.0, grade_y]])
    soil_poly = np.vstack(
        [
            grade_line,
            [x_clad1 + 32.0, y_conc_bot - 18.0],
            [x_clad1 + 0.2, y_conc_bot - 18.0],
        ]
    )
    ax.add_patch(Polygon(soil_poly, closed=True, facecolor=COL_SOIL, edgecolor="none", alpha=0.55, zorder=0))
    ax.plot(grade_line[:, 0], grade_line[:, 1], color="black", linewidth=1.2, zorder=5)
    ax.text(x_clad1 + 18.0, grade_y + 0.2, "Grade (typ.)", fontsize=9, ha="center", va="bottom")
    ax.text(x_clad1 + 18.0, grade_y - 1.8, 'Slope: 6" per 10\' away from foundation', fontsize=9, ha="center", va="top", style="italic")

    # -----------------------
    # Interior slab assembly (basement floor)
    # -----------------------
    slab_x0 = x_conc_int - slab_width
    slab_x1 = x_conc_int

    # Footing starts at bottom of concrete wall
    y_foot0 = y_conc_bot
    y_foot1 = y_foot0 - footing_d
    y_stone0 = y_foot1
    y_stone1 = y_stone0 - stone_base_thk

    # Place slab so XPS bottom sits slightly above the footing top (schematic consistency across details).
    slab_xps_bot = y_foot0 + 2.0
    basement_floor_y = slab_xps_bot + xps_under_thk + poly_sheet_thk + slab_thk

    _slab_assembly(
        ax,
        slab_x0,
        slab_x1,
        basement_floor_y,
        slab_thk=slab_thk,
        xps_thk=xps_under_thk,
        vapor_thk=poly_sheet_thk,
        stone_thk=stone_under_slab,
        thermal_break_thk=thermal_break_thk,
        sealant_thk=sealant_thk,
        thermal_break_side="right",
        thermal_break_x=x_conc_int - thermal_break_thk,
        show_stone=True,
    )

    # Single consistent aggregate base (wider than footing for french drain)
    footing_center_x = x_conc_int + conc_wall_thk / 2.0
    x_foot0 = footing_center_x - footing_w / 2.0
    x_foot1 = x_foot0 + footing_w
    x_stone0 = x_foot0 - stone_base_extra
    x_stone1 = x_foot1 + stone_base_extra

    _rect(ax, x_conc_int, y_conc_bot, conc_wall_thk, y_conc_top - y_conc_bot, fc=COL_CONC, lw=1.2, z=2)
    _rect(ax, x_foot0, y_foot1, footing_w, footing_d, fc=COL_CONC, lw=1.2, hatch=HATCHES.compacted, z=2)
    _rect(ax, x_stone0, y_stone1, x_stone1 - x_stone0, stone_base_thk, fc=COL.aggregate, lw=1.0, hatch=HATCHES.gravel, z=1)

    # French drain (in wider stone area, not under footing)
    drain_x = x_stone0 + drain_diam * 0.8
    drain_y = y_stone1 + stone_base_thk / 2
    _french_drain(ax, drain_x, drain_y, drain_diam, fc=COL_METAL, z=3)

    # -----------------------
    # Air/water barrier continuity (liquid membrane) + basement exterior insulation
    # -----------------------
    _rect(ax, x_mem0, y_conc_bot, membrane_thk, y_wall_top - y_conc_bot, fc=COL_MEM, ec="black", lw=0.9, z=6)

    xps_layer = float(basement_ext_p["xps_layer_in"])
    xps_layers = int(basement_ext_p["xps_layers"])
    xps_total = xps_layer * xps_layers

    x_xps_in0 = x_mem1
    x_xps_out1 = x_xps_in0 + xps_total
    for i in range(xps_layers):
        _rect(ax, x_xps_in0 + i * xps_layer, y_conc_bot, xps_layer, y_conc_top - y_conc_bot, fc=COL_XPS, lw=1.0, z=4)

    # Above-grade XPS protection (coating or rigid trim), only on the exposed portion
    protect_thk = float(basement_ext_p["xps_protect_in"])
    _rect(ax, x_xps_out1, grade_y, protect_thk, y_conc_top - grade_y, fc=COL_METAL, lw=1.0, z=7, alpha=0.85)

    # River rock trench (top 8" of soil, against foundation for drainage)
    river_rock_depth = float(foundation_p.get("river_rock_depth_in", 8.0))
    river_rock_width = float(foundation_p.get("river_rock_width_in", 10.0))
    river_rock_x0 = x_xps_out1 + protect_thk
    _rect(
        ax,
        river_rock_x0,
        grade_y - river_rock_depth,
        river_rock_width,
        river_rock_depth,
        fc=COL_RIVER_ROCK,
        ec="black",
        lw=1.0,
        hatch=HATCHES.gravel,
        z=2,
    )

    # -----------------------
    # Sill gasket + sill plate (mudsill)
    # -----------------------
    _rect(ax, x_stud0, y_sill0, stud_depth, sill_gasket, fc=COL.rubber, ec="black", lw=0.9, z=7)
    _lumber(ax, x_stud0, y_gasket1, stud_depth, sill_plate, fc=COL_WOOD, lw=1.2, z=10)

    # -----------------------
    # Above-grade wood wall (portion)
    # -----------------------
    _rect(ax, x_dry0, y_sill1, drywall, y_wall_top - y_sill1, fc=COL.drywall, lw=1.0, z=3)
    _rect(ax, x_stud0, y_sill1, stud_depth, y_wall_top - y_sill1, fc=COL_INSUL, lw=0.9, hatch=HATCHES.compacted, z=1)
    _rect(ax, x_stud0, y_sill1, stud_depth, y_wall_top - y_sill1, fc="none", lw=1.2, z=5)
    _rect(ax, x_sheath0, y_sill1, sheathing, y_wall_top - y_sill1, fc=COL_SHEATH, lw=1.1, z=4)
    _rect(ax, x_poly0, y_sill0, polyiso_wall, y_wall_top - y_sill0, fc=COL_POLYISO, lw=1.0, z=3)
    _rect(ax, x_eps0, y_sill0, eps_wall, y_wall_top - y_sill0, fc=COL_EPS, lw=1.0, z=3)

    # Furring + cladding start at the basement/first-floor transition (y_conc_top)
    _rect(ax, x_fur0, y_conc_top, furring, y_wall_top - y_conc_top, fc=COL_WOOD, lw=1.0, hatch=HATCHES.diagonal, z=6)
    _rect(ax, x_clad0, y_conc_top, cladding, y_wall_top - y_conc_top, fc=COL_METAL, lw=1.1, z=7)

    # -----------------------
    # Flashings + insect screen at the transition
    # -----------------------
    l_flash_thk = 0.45
    l_flash_x = x_mem1 + 0.15
    l_flash_y = y_conc_top + 0.12
    l_flash_pts = np.array([[l_flash_x, y_sill1 + 0.15], [l_flash_x, l_flash_y], [x_foam_outer - 0.7, l_flash_y]])
    _flashing(ax, l_flash_pts, l_flash_thk, fc=COL_FLASH, lw=0.9, z=12, alpha=0.9)

    spray_h = 0.9
    _rect(ax, x_foam_outer - 0.75, y_conc_top, 0.75, spray_h, fc=COL_SPRAY, ec="black", lw=0.8, z=11)

    # Z-flashing w/ drip edge at bottom of furring strips; add insect screen above.
    z_thk = 0.5
    z_start = (x_fur0 + 0.06, y_conc_top + 2.4)
    z_steps = [
        (0.0, -2.15),
        (x_fur1 - x_fur0 + 0.18, 0.0),
        (0.55, 0.0),
        (0.0, -4.2),
        (0.7, -0.25),
    ]
    _flashing(ax, _path_from_steps(z_start, z_steps), z_thk, fc=COL_FLASH, lw=0.9, z=13, alpha=0.9)

    screen_h = 0.5
    _rect(ax, x_fur0 + 0.02, y_conc_top + 2.65, x_clad1 - x_fur0 - 0.04, screen_h, fc="white", ec="black", lw=0.8, hatch=HATCHES.cross, z=14, alpha=0.9)

    # -----------------------
    # Callouts / dimensions
    # -----------------------
    _dim_h(ax, x_xps_in0, x_xps_out1, y_conc_bot + 24.0, f'{xps_total:.0f}" XPS ({xps_layers} layers)')
    _dim_h(ax, x_poly0, x_eps1, y_conc_top + 28.0, f'{(polyiso_wall + eps_wall):.0f}" CI above ({polyiso_wall:.0f}\" + {eps_wall:.0f}\")')

    _leader(
        ax,
        xy=(x_conc_ext + 0.35, (y_conc_top + y_conc_bot) / 2),
        text_xy=(x_clad1 + 5.0, y_conc_bot + 28.0),
        text="Liquid-applied waterproofing / air barrier\n(thickness exaggerated; continuous)",
        ha="left",
    )
    _leader(
        ax,
        xy=(x_xps_in0 + xps_total * 0.7, y_conc_top - 14.0),
        text_xy=(x_clad1 + 5.0, y_conc_top - 10.0),
        text=f'{xps_total:.0f}" XPS ({xps_layers} layers, staggered seams;\nouter layer taped; low water absorption)',
        ha="left",
    )
    _leader(
        ax,
        xy=(x_xps_out1 + protect_thk / 2, grade_y + 10.0),
        text_xy=(x_clad1 + 5.0, grade_y + 8.0),
        text="Exposed XPS protection above grade:\ncoating or rigid metal/PVC trim",
        ha="left",
    )
    _leader(
        ax,
        xy=(river_rock_x0 + river_rock_width / 2, grade_y - river_rock_depth / 2),
        text_xy=(x_clad1 + 5.0, grade_y - 6.0),
        text=f'{river_rock_width:.0f}"×{river_rock_depth:.0f}" river rock trench (geotextile-lined)\n(top of soil, drainage against foundation)',
        ha="left",
    )
    _leader(
        ax,
        xy=(drain_x, drain_y),
        text_xy=(x_clad1 + 5.0, y_foot1 - 6.0),
        text=f'{drain_diam:.0f}" perforated french drain\nin washed stone (wider area,\nnot under footing)',
        ha="left",
    )
    _leader(
        ax,
        xy=((x_foot0 + x_foot1) / 2, (y_foot0 + y_foot1) / 2),
        text_xy=(x_dry0 - 12.0, y_foot1 + 2.0),
        text=f'{footing_w:.0f}"×{footing_d:.0f}" footing (5000 psi)\non {stone_base_thk:.0f}" compacted aggregate\n(geotextile-lined)',
        ha="right",
        va="center",
    )
    _leader(
        ax,
        xy=((slab_x0 + slab_x1) / 2, basement_floor_y - slab_thk / 2),
        text_xy=(x_dry0 - 12.0, y_conc_bot - 12.0),
        text=f'Interior basement slab:\n{slab_thk:.0f}" concrete over R-{xps_under_thk * 5:.0f} XPS,\nvapor barrier, {stone_under_slab:.0f}" gravel base\n{thermal_break_thk:.0f}" thermal break at foundation wall',
        ha="right",
        va="center",
    )
    _leader(
        ax,
        xy=(x_stud0 + 0.6, y_gasket1 + sill_plate / 2),
        text_xy=(x_dry0 - 12.0, y_conc_top + 18.0),
        text="Sill gasket + treated mudsill\n(air seal at sill; anchors such as MASAP not shown)",
        ha="right",
    )
    _leader(
        ax,
        xy=(x_fur0 + 0.3, y_conc_top + 1.2),
        text_xy=(x_clad1 + 5.0, y_conc_top + 5.5),
        text="Stainless / thick aluminum Z-flashing\nw/ drip edge at bottom of rainscreen furring",
        ha="left",
    )
    _leader(
        ax,
        xy=(x_fur0 + 0.2, y_conc_top + 2.9),
        text_xy=(x_clad1 + 5.0, y_conc_top + 12.0),
        text="Insect screen (Cor-A-Vent or SS mesh)\njust above flashing",
        ha="left",
    )
    _leader(
        ax,
        xy=(x_foam_outer - 0.55, y_conc_top + 0.4),
        text_xy=(x_dry0 - 12.0, y_conc_top + 2.0),
        text="L-flashing from sheathing down onto\nbasement foam; terminate within foam\nand seal outer end with spray foam",
        ha="right",
    )

    ax.set_title("Basement to Wood-Framed Wall Transition Detail (IFC-driven)", fontsize=13, fontweight="bold", loc="center", pad=12)
    ax.text(x_conc_int + 30.0, y_stone1 - 8.0, "Colin Catlin, 2026", ha="center", va="top", fontsize=7)

    ax.set_xlim(x_conc_int - 14.0, x_clad1 + 38.0)
    ax.set_ylim(y_stone1 - 6.0, y_wall_top + 12.0)
    ax.set_aspect("equal")
    ax.axis("off")

    legend_patches = [
        Patch(facecolor=COL_CONC, edgecolor="black", label="Concrete"),
        Patch(facecolor=COL_WOOD, edgecolor="black", label="Wood framing / plates / furring"),
        Patch(facecolor=COL_SHEATH, edgecolor="black", label=f'Sheathing ({sheathing:.3g}\")'),
        Patch(facecolor=COL_MEM, edgecolor="black", label="Liquid-applied membrane"),
        Patch(facecolor=COL_XPS, edgecolor="black", label=f'XPS ({xps_total:.0f}\")'),
        Patch(facecolor=COL_POLYISO, edgecolor="black", label=f'Polyiso ({polyiso_wall:.0f}\")'),
        Patch(facecolor=COL_EPS, edgecolor="black", label=f'EPS ({eps_wall:.0f}\")'),
        Patch(facecolor=COL.aggregate, edgecolor="black", label="Aggregate / washed stone"),
        Patch(facecolor=COL_RIVER_ROCK, edgecolor="black", label="River rock (drainage)"),
        Patch(facecolor=COL_FLASH, edgecolor="black", label="Metal flashing"),
        Patch(facecolor=COL_SPRAY, edgecolor="black", label="Spray foam (seal gaps)"),
    ]
    ax.legend(
        handles=legend_patches,
        loc="lower left",
        bbox_to_anchor=(0.01, 0.01),
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
    raw_notes = load_markdown_notes(repo_root / "notes/basement_to_framed_wall_detail.md")
    ax_notes.text(3, 146, _wrap_notes(raw_notes), fontsize=9, va="top", ha="left", family="monospace")

    out_path = Path("catlin_house/out/basement_to_framed_wall_detail_ifc.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight", pad_inches=0.02)
    print(out_path)


if __name__ == "__main__":
    main()
