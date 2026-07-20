"""
Roof-to-wall eave detail driven by the generated IFC parameters.

Run:
  python catlin_house/build_catlin_house_ifc.py
  python catlin_house/roof_wall_eave_detail_ifc.py

Output:
  catlin_house/out/roof_wall_eave_detail_ifc.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch, Polygon, Rectangle

import ifcopenshell
import ifcopenshell.util.element

from ifcplot.detail_utils import (
    COLORS,
    HATCHES,
    ExteriorWoodWallAssembly,
    _flashing,
    _leader,
    _lumber,
    _offset_segment,
    _quad_from_segment,
    _rect,
    load_markdown_notes,
    _wrap_notes,
)


def _pt_at_x(seg0, seg1, x):
    """Helper to find point along a segment at a given x coordinate."""
    t = (x - seg0[0]) / (seg1[0] - seg0[0] + 1e-9)
    return seg0 + t * (seg1 - seg0)


def _layer_poly(mid0, mid1, center_offset, thickness, x0, x1):
    """Create a polygon for a layer offset from a centerline segment."""
    upper0, upper1 = _offset_segment(mid0, mid1, center_offset + thickness / 2)
    lower0, lower1 = _offset_segment(mid0, mid1, center_offset - thickness / 2)
    p0u = _pt_at_x(upper0, upper1, x0)
    p1u = _pt_at_x(upper0, upper1, x1)
    p1l = _pt_at_x(lower0, lower1, x1)
    p0l = _pt_at_x(lower0, lower1, x0)
    return np.vstack([p0u, p1u, p1l, p0l])


def _load_house_roof_params(ifc_path: Path) -> dict:
    f = ifcopenshell.open(str(ifc_path))
    roof = next(r for r in f.by_type("IfcRoof") if r.Name and r.Name.startswith("House Roof"))
    psets = ifcopenshell.util.element.get_psets(roof)
    raw = psets.get("Pset_ifcPlot_DetailParams", {}).get("ParamsJSON")
    if not raw:
        raise RuntimeError("Missing `Pset_ifcPlot_DetailParams.ParamsJSON` on House roof.")
    return json.loads(raw)


def main() -> None:
    ifc_path = Path("catlin_house/out/catlin_house.ifc")
    params = _load_house_roof_params(ifc_path)

    wall_p = params["wall"]
    roof_p = params["roof"]

    # Units: inches (schematic)
    drywall = float(wall_p["drywall_in"])
    stud_depth = float(wall_p["stud_depth_in"])
    sheathing = float(wall_p["sheathing_in"])
    polyiso_wall = float(wall_p["polyiso_in"])
    eps_wall = float(wall_p["eps_in"])
    furring_wall = float(wall_p["furring_in"])
    cladding = float(wall_p["cladding_in"])

    pitch = float(roof_p["pitch_rise_over_run"])
    roof_pitch = -abs(pitch)  # x increases to exterior
    depth_ijoist = float(roof_p["ijoist_depth_in"])
    roof_sheathing = float(roof_p["sheathing_in"])
    polyiso_roof = float(roof_p["polyiso_in"])
    eps_roof = float(roof_p["eps_in"])
    roof_mem = float(roof_p["membrane_in"])
    furring_roof = float(roof_p["furring_in"])
    metal_roof = float(roof_p["metal_roof_in"])
    overhang = float(roof_p["overhang_in"])

    fig = plt.figure(figsize=(20, 10))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.9, 1.1], wspace=0.06)
    ax = fig.add_subplot(gs[0, 0])
    ax_notes = fig.add_subplot(gs[0, 1])

    COL = COLORS

    wall_layers = ExteriorWoodWallAssembly(
        drywall=drywall,
        stud_depth=stud_depth,
        sheathing=sheathing,
        membrane=0.0,
        polyiso=polyiso_wall,
        eps=eps_wall,
        furring=furring_wall,
        cladding=cladding,
        x_clad1=1.0,
    ).coords()
    x_dry0, x_dry1 = wall_layers["drywall"]
    x_stud0, x_stud1 = wall_layers["stud"]
    x_sheath0, x_sheath1 = wall_layers["sheathing"]
    x_poly0, x_poly1 = wall_layers["polyiso"]
    x_eps0, x_eps1 = wall_layers["eps"]
    x_fur0, x_fur1 = wall_layers["furring"]
    x_clad0, x_clad1 = wall_layers["cladding"]

    # Wall elevation layout
    plate_thk = 1.5
    y_top_plate_top = 0.0
    y_top_plate_mid = y_top_plate_top - plate_thk
    y_top_plate_bot = y_top_plate_mid - plate_thk
    wall_show_h = 36.0
    y_wall_bot = y_top_plate_bot - wall_show_h
    
    # Compute wall foam top extent (where it meets roof foam)
    flange_thk = 1.375  # I-joist flange thickness
    membrane_thk = 0.25
    
    # Roof geometry setup for wall foam calculation
    x_bearing = x_stud1
    eave_x = x_bearing
    eave_outer_x = eave_x + overhang

    birdsmouth_depth = 1.17
    y_joist_bot = y_top_plate_top - birdsmouth_depth
    y_joist_center = y_joist_bot + depth_ijoist / 2

    x_inside = -34.0
    mid0 = np.array([x_inside, y_joist_center + roof_pitch * (x_inside - x_bearing)], dtype=float)
    mid1 = np.array([eave_x, y_joist_center], dtype=float)
    mid1_ext = np.array([eave_outer_x, y_joist_center + roof_pitch * (eave_outer_x - x_bearing)], dtype=float)
    
    # Wall foam extends up to just below underside of roof foam
    foam_base_offset = depth_ijoist / 2 + roof_sheathing + membrane_thk
    foam_base_seg0, foam_base_seg1 = _offset_segment(mid0, mid1_ext, foam_base_offset)
    y_roof_foam_under_at_eps = _pt_at_x(foam_base_seg0, foam_base_seg1, x_eps1)[1]
    y_wall_ext = min(y_roof_foam_under_at_eps - 0.4, y_top_plate_top + depth_ijoist - 0.25)
    
    # Furring bot offset for wall furring top calculation
    offset_furring_bot = depth_ijoist / 2 + roof_sheathing + membrane_thk + polyiso_roof + eps_roof + roof_mem
    fur_bot_seg0, fur_bot_seg1 = _offset_segment(mid0, mid1_ext, offset_furring_bot)
    wall_fur_top_y = _pt_at_x(fur_bot_seg0, fur_bot_seg1, x_fur1)[1]

    # Wall layers
    _rect(ax, x_dry0, y_wall_bot, drywall, y_top_plate_top - y_wall_bot, fc=COL.drywall, lw=1.0, z=4)
    
    # Ceiling drywall under I-joist (sloped)
    ceiling_offset = -depth_ijoist / 2 - drywall / 2
    ceiling_dry_poly = _layer_poly(mid0, mid1, ceiling_offset, drywall, x_inside, x_stud1)
    ax.add_patch(Polygon(ceiling_dry_poly, closed=True, facecolor=COL.drywall, edgecolor="black", linewidth=1.1, zorder=2))
    
    _rect(ax, x_stud0, y_wall_bot, stud_depth, y_top_plate_bot - y_wall_bot, fc=COL.insulation, lw=0.9, hatch=HATCHES.compacted, z=1)
    _lumber(ax, x_stud0, y_top_plate_bot, stud_depth, plate_thk, fc=COL.wood, lw=1.2, z=10)
    _lumber(ax, x_stud0, y_top_plate_mid, stud_depth, plate_thk, fc=COL.wood, lw=1.2, z=10)
    _rect(ax, x_stud0, y_wall_bot, stud_depth, y_top_plate_bot - y_wall_bot, fc="none", lw=1.2, z=5)
    
    # Wall sheathing extends up to meet roof deck
    _rect(ax, x_sheath0, y_wall_bot, sheathing, (y_top_plate_top + depth_ijoist) - y_wall_bot, fc=COL.sheathing, lw=1.0, z=4)
    _rect(ax, x_sheath1, y_wall_bot, membrane_thk, (y_top_plate_top + depth_ijoist) - y_wall_bot, fc=COL.membrane, ec="black", lw=0.8, z=7)
    
    # Wall foam layers extend up to meet roof
    _rect(ax, x_poly0, y_wall_bot, polyiso_wall, y_wall_ext - y_wall_bot, fc=COL.polyiso, lw=1.0, z=4)
    _rect(ax, x_eps0, y_wall_bot, eps_wall, y_wall_ext - y_wall_bot, fc=COL.eps, lw=1.0, z=4)
    
    # Wall furring extends up to meet roof furring
    _rect(ax, x_fur0, y_wall_bot, furring_wall, wall_fur_top_y - y_wall_bot, fc=COL.wood, lw=1.0, hatch=HATCHES.diagonal, z=5)
    _rect(ax, x_clad0, y_wall_bot, cladding, y_wall_ext - y_wall_bot, fc=COL.metal_dark, lw=1.0, z=6)

    # I-joist with birdsmouth cut
    seat_x0 = x_stud0
    seat_y = y_top_plate_top - 0.1
    
    top_offset = depth_ijoist / 2
    bot_offset = -depth_ijoist / 2
    top0, top1 = _offset_segment(mid0, mid1, top_offset)
    bot0, bot1 = _offset_segment(mid0, mid1, bot_offset)
    
    p_top_start = _pt_at_x(top0, top1, x_inside)
    p_top_end = _pt_at_x(top0, top1, eave_x)
    p_bot_end = np.array([eave_x, seat_y], dtype=float)
    p_seat0 = np.array([seat_x0, seat_y], dtype=float)
    p_bot_seat0_uncut = _pt_at_x(bot0, bot1, seat_x0)
    p_bot_start = _pt_at_x(bot0, bot1, x_inside)
    
    joist_poly = np.vstack([p_top_start, p_top_end, p_bot_end, p_seat0, p_bot_seat0_uncut, p_bot_start])
    ax.add_patch(Polygon(joist_poly, closed=True, facecolor=COL.wood, edgecolor="black", linewidth=1.2, zorder=3))
    
    # Flange lines (schematic)
    top_flange_offset = depth_ijoist / 2 - flange_thk
    bot_flange_offset = -(depth_ijoist / 2 - flange_thk)
    top_flange_seg0, top_flange_seg1 = _offset_segment(mid0, mid1, top_flange_offset)
    bot_flange_seg0, bot_flange_seg1 = _offset_segment(mid0, mid1, bot_flange_offset)
    ax.plot([_pt_at_x(top_flange_seg0, top_flange_seg1, x_inside)[0], _pt_at_x(top_flange_seg0, top_flange_seg1, eave_x)[0]],
            [_pt_at_x(top_flange_seg0, top_flange_seg1, x_inside)[1], _pt_at_x(top_flange_seg0, top_flange_seg1, eave_x)[1]],
            color="black", linewidth=0.9, linestyle=(0, (2.5, 2.5)), alpha=0.8)
    ax.plot([_pt_at_x(bot_flange_seg0, bot_flange_seg1, x_inside)[0], _pt_at_x(bot_flange_seg0, bot_flange_seg1, seat_x0)[0]],
            [_pt_at_x(bot_flange_seg0, bot_flange_seg1, x_inside)[1], _pt_at_x(bot_flange_seg0, bot_flange_seg1, seat_x0)[1]],
            color="black", linewidth=0.9, linestyle=(0, (2.5, 2.5)), alpha=0.8)
    
    # Bearing stiffener
    stiff_w = stud_depth
    stiff_x0_pos = eave_x - stiff_w
    stiff_bot0 = _pt_at_x(bot_flange_seg0, bot_flange_seg1, stiff_x0_pos)
    stiff_bot1 = _pt_at_x(bot_flange_seg0, bot_flange_seg1, eave_x)
    stiff_top0 = _pt_at_x(top_flange_seg0, top_flange_seg1, stiff_x0_pos)
    stiff_top1 = _pt_at_x(top_flange_seg0, top_flange_seg1, eave_x)
    stiff_poly = np.array([stiff_bot0, stiff_bot1, stiff_top1, stiff_top0])
    ax.add_patch(Polygon(stiff_poly, closed=True, facecolor=COL.wood, edgecolor="black", linewidth=1.0, hatch=HATCHES.cross, zorder=4))

    # Roof layers
    offset_sheath = depth_ijoist / 2 + roof_sheathing / 2
    sheath_poly = _layer_poly(mid0, mid1_ext, offset_sheath, roof_sheathing, x_inside, eave_x + sheathing)
    ax.add_patch(Polygon(sheath_poly, closed=True, facecolor=COL.sheathing, edgecolor="black", linewidth=1.0, zorder=5))
    
    offset_roof_mem = depth_ijoist / 2 + roof_sheathing + membrane_thk / 2
    roof_mem_poly = _layer_poly(mid0, mid1_ext, offset_roof_mem, membrane_thk, x_inside, eave_x + sheathing)
    ax.add_patch(Polygon(roof_mem_poly, closed=True, facecolor=COL.membrane, edgecolor="black", linewidth=0.8, zorder=7))
    
    offset_polyiso = depth_ijoist / 2 + roof_sheathing + membrane_thk + polyiso_roof / 2
    poly_poly = _layer_poly(mid0, mid1_ext, offset_polyiso, polyiso_roof, x_inside, x_fur0)
    ax.add_patch(Polygon(poly_poly, closed=True, facecolor=COL.polyiso, edgecolor="black", linewidth=1.0, zorder=5))
    
    offset_eps = depth_ijoist / 2 + roof_sheathing + membrane_thk + polyiso_roof + eps_roof / 2
    eps_poly = _layer_poly(mid0, mid1_ext, offset_eps, eps_roof, x_inside, x_fur0)
    ax.add_patch(Polygon(eps_poly, closed=True, facecolor=COL.eps, edgecolor="black", linewidth=1.0, zorder=5))
    
    offset_roof_mem2 = depth_ijoist / 2 + roof_sheathing + membrane_thk + polyiso_roof + eps_roof + roof_mem / 2
    mem_poly = _layer_poly(mid0, mid1_ext, offset_roof_mem2, roof_mem, x_inside, x_fur0)
    ax.add_patch(Polygon(mem_poly, closed=True, facecolor=COL.membrane, edgecolor="black", linewidth=0.8, zorder=6))
    
    offset_furring = depth_ijoist / 2 + roof_sheathing + membrane_thk + polyiso_roof + eps_roof + roof_mem + furring_roof / 2
    fur_poly = _layer_poly(mid0, mid1_ext, offset_furring, furring_roof, x_inside, x_fur1)
    ax.add_patch(Polygon(fur_poly, closed=True, facecolor=COL.wood, edgecolor="black", linewidth=1.0, hatch=HATCHES.diagonal, zorder=7))
    
    offset_metal = offset_furring + furring_roof / 2 + metal_roof / 2
    metal_poly = _layer_poly(mid0, mid1_ext, offset_metal, metal_roof, x_inside, x_fur1 + 0.6)
    ax.add_patch(Polygon(metal_poly, closed=True, facecolor=COL.metal_dark, edgecolor="black", linewidth=1.0, zorder=8))
    
    # Spray foam wedge at roof/wall foam interface
    roof_foam_bot_at_sheath = _pt_at_x(foam_base_seg0, foam_base_seg1, x_sheath1)
    roof_foam_bot_at_eps = _pt_at_x(foam_base_seg0, foam_base_seg1, x_eps1)
    spray_poly = np.array([
        (x_eps1, y_wall_ext),
        roof_foam_bot_at_eps,
        roof_foam_bot_at_sheath,
        (x_sheath1, y_wall_ext),
    ])
    ax.add_patch(Polygon(spray_poly, closed=True, facecolor=COL.spray_foam, edgecolor="black", linewidth=0.8, zorder=6))
    
    # Gutter at eave
    gutter_h = 5.0
    gutter_depth = 5.0
    gutter_back_x = x_fur1 + furring_wall - 0.2
    gutter_front_x = gutter_back_x + gutter_depth
    roof_fur_top_at_eave = _pt_at_x(*_offset_segment(mid0, mid1_ext, offset_furring + furring_roof / 2), x_fur1)
    gutter_top_y = _pt_at_x(fur_bot_seg0, fur_bot_seg1, x_fur1)[1] - 1.2
    
    gutter = np.array([
        [gutter_back_x, gutter_top_y],
        [gutter_back_x, gutter_top_y - gutter_h],
        [gutter_front_x, gutter_top_y - gutter_h],
        [gutter_front_x + 1.0, gutter_top_y - gutter_h + 2.5],
        [gutter_front_x + 1.0, gutter_top_y + 0.5],
        [gutter_back_x + 0.5, gutter_top_y + 0.5],
    ])
    ax.add_patch(Polygon(gutter, closed=True, facecolor=COL.gutter, edgecolor="black", linewidth=1.0, zorder=7))

    # Leaders/annotations
    _leader(ax, (eave_x - 0.6, y_top_plate_top + 0.15), (x_dry0 - 18.0, y_joist_center - 6.0), "I-joist bearing on top plate\nwith birdsmouth cut")
    
    sheath_seg0, sheath_seg1 = _offset_segment(mid0, mid1_ext, offset_sheath)
    _leader(ax, _pt_at_x(sheath_seg0, sheath_seg1, -6.0), (x_clad1 + 14.0, y_joist_center + 14.0),
            '3/4" Struct 1 roof sheathing\nLiquid membrane = roof air barrier')
    
    eps_seg0, eps_seg1 = _offset_segment(mid0, mid1_ext, offset_eps)
    _leader(ax, _pt_at_x(eps_seg0, eps_seg1, -2.0), (x_clad1 + 14.0, y_joist_center + 22.0),
            'Roof CI: 2" polyiso (inner, seams staggered)\n+ 4" EPS (outer, seams taped)')
    
    fur_seg0, fur_seg1 = _offset_segment(mid0, mid1_ext, offset_furring)
    _leader(ax, _pt_at_x(fur_seg0, fur_seg1, -12.0), (-22.0, y_joist_center + 22.0),
            '3/4" plywood roof furring, 3.5" wide\nVent channel continuous wall→eave→ridge')
    
    _leader(ax, ((x_sheath1 + x_eps1) / 2, stiff_top1[1] + 1.0), (x_clad1 + 10.0, y_top_plate_top - 1.0),
            "Fill gap between roof & wall foam\nwith closed-cell spray foam")
    
    _leader(ax, (gutter_back_x + gutter_depth / 2, gutter_top_y - gutter_h / 2), (x_clad1 + 16.0, y_top_plate_top + 8.0),
            '6" box gutter (fascia style)')
    
    _leader(ax, (x_stud0 + stud_depth / 2, y_top_plate_bot - 12), (x_dry0 - 1.5, y_top_plate_bot - 9.0),
            "2x4 wall w/ R-13 batt fill", ha="right")
    
    _leader(ax, (x_eps0 + eps_wall / 2, y_top_plate_bot - 12.0), (x_poly1 + 12.0, y_top_plate_bot - 16.0),
            '2" polyiso (inner) + 2" EPS (outer)\nStagger seams, tape outer layer')

    # Vent arrows
    ax.annotate("", xy=_pt_at_x(fur_seg0, fur_seg1, x_fur1 - 2.0), xytext=_pt_at_x(fur_seg0, fur_seg1, -8.0),
                arrowprops=dict(arrowstyle="->", linewidth=1.0))
    ax.annotate("", xy=(x_fur1 + 0.05, y_top_plate_top - 2.0), xytext=(x_fur1 + 0.05, y_wall_bot + 6.0),
                arrowprops=dict(arrowstyle="->", linewidth=1.0))
    ax.text(x_fur1 + 0.9, y_top_plate_top - 1.0, "Vent path\nroof→wall", fontsize=8, ha="left", va="top")

    ax.set_title("Roof–Wall Eave Detail with Exterior CI, Box Gutter (4:12 Slope, IFC-driven)", fontsize=13, fontweight="bold", loc="left", pad=12)
    ax.text(x_dry0 - 1.0, y_wall_bot - 10.0, "Colin Catlin, 2026", ha="left", va="top", fontsize=7)
    ax.set_xlim(x_dry0 - 4.0, gutter_front_x + 12.0)
    ax.set_ylim(y_wall_bot - 8.0, y_joist_center + 24.0)
    ax.set_aspect("equal")
    ax.axis("off")

    legend_patches = [
        Patch(facecolor=COL.wood, edgecolor="black", label="Wood framing / furring"),
        Patch(facecolor=COL.drywall, edgecolor="black", label="Drywall (5/8\")"),
        Patch(facecolor=COL.sheathing, edgecolor="black", label="Struct 1 plywood"),
        Patch(facecolor=COL.membrane, edgecolor="black", label="Liquid / roofing membrane"),
        Patch(facecolor=COL.polyiso, edgecolor="black", label="Polyiso foam"),
        Patch(facecolor=COL.eps, edgecolor="black", label="EPS foam"),
        Patch(facecolor=COL.spray_foam, edgecolor="black", label="Spray foam infill"),
        Patch(facecolor=COL.metal_dark, edgecolor="black", label="Metal roofing / siding"),
    ]
    ax.legend(handles=legend_patches, loc="lower left", bbox_to_anchor=(0.01, 0.01), bbox_transform=ax.transAxes,
              frameon=True, fontsize=8.5, ncol=2, borderaxespad=0.0, handlelength=1.6, columnspacing=1.0)

    # Notes panel
    ax_notes.set_xlim(0, 100)
    ax_notes.set_ylim(0, 150)
    ax_notes.axis("off")

    repo_root = Path(__file__).resolve().parents[1]
    raw_notes = load_markdown_notes(repo_root / "notes/roof_wall_eave_detail.md")
    raw_notes.extend(["", f'IFC PARAMETERS: Pitch {pitch:.4g}, Overhang {overhang:g}", I-joist {depth_ijoist:g}"'])
    ax_notes.text(4, 146, _wrap_notes(raw_notes), fontsize=9, va="top", ha="left", family="monospace")

    out_path = Path("catlin_house/out/roof_wall_eave_detail_ifc.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight", pad_inches=0.02)
    print(out_path)


if __name__ == "__main__":
    main()
