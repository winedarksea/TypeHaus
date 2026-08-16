""" Garage wall / roof-eave side detail driven by the generated IFC parameters.

Run:
  python catlin_house/build_catlin_house_ifc.py
  python catlin_house/garage_wall_detail_side_ifc.py

Output:
  catlin_house/out/garage_wall_detail_side_ifc.png
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
    _dim_v,
    _flashing,
    _leader,
    _lumber,
    _offset_segment,
    _path_from_steps,
    _quad_from_segment,
    _rect,
    load_markdown_notes,
    _wrap_notes,
)


def _load_garage_params(ifc_path: Path) -> dict:
    f = ifcopenshell.open(str(ifc_path))
    roof = next(r for r in f.by_type("IfcRoof") if r.Name and r.Name.startswith("Garage Roof"))
    psets = ifcopenshell.util.element.get_psets(roof)
    raw = psets.get("Pset_ifcPlot_DetailParams", {}).get("ParamsJSON")
    if not raw:
        raise RuntimeError("Missing `Pset_ifcPlot_DetailParams.ParamsJSON` on Garage roof.")
    return json.loads(raw)


def main() -> None:
    ifc_path = Path("catlin_house/out/catlin_house.ifc")
    params = _load_garage_params(ifc_path)

    icf_p = params["icf"]
    wall_p = params["wall"]
    roof_p = params["roof"]
    foundation_p = params.get("foundation", {})
    slab_p = params.get("slab", {})
    framing_p = params.get("framing", {})

    def _p(d: dict, *keys: str, default: float) -> float:
        for key in keys:
            if key in d:
                return float(d[key])
        return float(default)

    # Units: inches (schematic)
    icf_core = _p(icf_p, "core_in", default=6.0)
    icf_eps = _p(icf_p, "eps_in", default=2.5)
    icf_total = _p(icf_p, "total_in", default=icf_core + 2.0 * icf_eps)
    icf_above_grade = _p(icf_p, "above_grade_in", default=22.0)
    icf_coating = _p(icf_p, "coating_in", default=0.5)

    drywall = _p(wall_p, "drywall_in", default=0.625)
    stud_depth = _p(wall_p, "stud_depth_in", default=5.5)
    zip_r = _p(wall_p, "sheathing_in", "zip_r_in", default=1.5)
    rainscreen = _p(wall_p, "furring_in", "rainscreen_in", default=0.375)
    metal_siding = _p(wall_p, "cladding_in", "metal_siding_in", default=0.5)
    wall_height = _p(wall_p, "wood_wall_height_ft", default=8.0) * 12.0

    pitch = _p(roof_p, "pitch_rise_over_run", default=4.0 / 12.0)
    overhang = _p(roof_p, "overhang_in", default=16.0)

    frost_depth = _p(foundation_p, "frost_depth_in", default=42.0)
    footing_thick = _p(foundation_p, "footing_thick_in", default=6.0)
    footing_width = _p(foundation_p, "footing_width_in", default=12.0)

    slab_thick = _p(slab_p, "thickness_in", default=3.5)
    vapor_poly = _p(slab_p, "vapor_poly_in", default=0.05)
    xps = _p(slab_p, "xps_in", default=2.0)
    gravel = _p(slab_p, "gravel_in", default=4.0)

    sill_gasket = _p(framing_p, "sill_gasket_in", default=0.25)
    sill_plate = _p(framing_p, "sill_plate_in", default=1.5)
    top_plate = _p(framing_p, "top_plate_in", default=1.5)
    raised_heel = _p(framing_p, "raised_heel_in", default=6.0)
    truss_member = _p(framing_p, "truss_member_in", default=3.5)
    overhang_length = overhang

    fig = plt.figure(figsize=(20, 10))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.9, 1.1], wspace=0.06)
    ax = fig.add_subplot(gs[0, 0])
    ax_notes = fig.add_subplot(gs[0, 1])

    COL = COLORS

    # Coordinate system: x interior negative, exterior positive. Grade at y=0.
    grade_y = 0.0
    y_footing_top = grade_y - frost_depth
    y_footing_bot = y_footing_top - footing_thick
    y_icf_bot = y_footing_top
    y_icf_top = grade_y + icf_above_grade

    # Layout: x=0 is exterior face of ICF protective coating (exposed portion).
    x_exterior = 0.0
    x_icf_eps_ext0 = x_exterior - icf_coating - icf_eps
    x_icf_eps_ext1 = x_exterior - icf_coating
    x_icf_core0 = x_icf_eps_ext0 - icf_core
    x_icf_core1 = x_icf_eps_ext0
    x_icf_eps_int0 = x_icf_core0 - icf_eps
    x_icf_eps_int1 = x_icf_core0

    # Place stud wall so the sheathing plane and the stem's exterior EPS face are
    # coplanar — the alignment the model authors (params/foundations.py). 4 1/2" of the
    # 5 1/2" sill plate still lands on the concrete core, and the rainscreen + siding
    # project past the foam and drip clear of it instead of ledging back onto it.
    x_stud_ext = x_icf_eps_ext1 - zip_r
    x_stud_int = x_stud_ext - stud_depth
    x_dry_int = x_stud_int - drywall
    x_zip_ext = x_stud_ext + zip_r
    x_rain_ext = x_zip_ext + rainscreen
    x_siding_ext = x_rain_ext + metal_siding

    y_sill0 = y_icf_top
    y_sill1 = y_sill0 + sill_gasket + sill_plate

    # Above-grade framed wall
    y_topplate_top = y_sill1 + wall_height
    y_topplate0 = y_topplate_top - top_plate
    y_raised_heel_top = y_topplate_top + raised_heel

    # ----- Draw grade + soil (schematic) --------------------------------------
    grade_line = np.array([[x_exterior + 0.2, grade_y], [x_exterior + 30.0, grade_y]])
    soil_poly = np.vstack([grade_line, [x_exterior + 30.0, y_footing_bot - 7.0], [x_exterior + 0.2, y_footing_bot - 7.0]])
    ax.add_patch(Polygon(soil_poly, closed=True, facecolor=COL.soil, edgecolor="none", alpha=0.55, zorder=0))
    ax.plot(grade_line[:, 0], grade_line[:, 1], color="black", linewidth=1.2, zorder=5)
    ax.text(x_exterior + 18.0, grade_y + 0.2, "Grade (typ.)", fontsize=9, ha="center", va="bottom")

    # River rock trench beneath overhang edge (for drainage)
    river_rock_depth = 6.0
    river_rock_width = 12.0
    river_rock_x = x_exterior + 16.0
    river_rock_x0 = river_rock_x - river_rock_width / 2
    _rect(ax, river_rock_x0, grade_y - river_rock_depth, river_rock_width, river_rock_depth, fc=COL.river_rock, ec="black", lw=1.0, hatch=HATCHES.gravel, z=2)
    _leader(ax, (river_rock_x, grade_y - river_rock_depth / 2), (x_exterior + 30.0, grade_y - 12.0), '12"×6" river rock trench\n(drainage below overhang), geotextile-lined', ha="left", va="center")

    # ----- Footing (compacted stone) ------------------------------------------
    footing_center = (x_exterior - icf_total / 2) - icf_coating / 2
    x_foot0 = footing_center - footing_width / 2
    x_foot1 = footing_center + footing_width / 2
    _rect(ax, x_foot0, y_footing_bot, x_foot1 - x_foot0, footing_thick, fc=COL.aggregate, ec="black", lw=1.2, hatch=HATCHES.compacted, z=2)
    _leader(ax, (footing_center, (y_footing_top + y_footing_bot) / 2), (x_exterior + 30.0, y_footing_bot - 2.0), '12"×6" compacted stone footing\n(IRC R403.1, R403.4.1)', ha="left", va="top")

    # ----- ICF stem wall (EPS + concrete + EPS) -------------------------------
    _rect(ax, x_icf_eps_ext0, y_icf_bot, x_icf_eps_ext1 - x_icf_eps_ext0, y_icf_top - y_icf_bot, fc=COL.eps, z=2)
    _rect(ax, x_icf_core0, y_icf_bot, x_icf_core1 - x_icf_core0, y_icf_top - y_icf_bot, fc=COL.concrete, z=2)
    _rect(ax, x_icf_eps_int0, y_icf_bot, x_icf_eps_int1 - x_icf_eps_int0, y_icf_top - y_icf_bot, fc=COL.eps, z=2)

    # Protective coating (only where EPS is exposed above grade)
    _rect(ax, x_icf_eps_ext1, grade_y, icf_coating, y_icf_top - grade_y, fc=COL.metal_dark, ec="black", lw=1.2, z=5)
    _rect(ax, x_icf_eps_int0, grade_y, icf_coating, y_icf_top - grade_y, fc=COL.drywall, ec="black", lw=1.2, z=5)
    _leader(ax, (x_icf_eps_ext1 + icf_coating / 2, (grade_y + y_icf_top) / 2), (x_exterior + 30.0, grade_y + 2.0), "Protective coating over exposed\nICF EPS (above grade, both sides)\nInterior: 15-min thermal barrier\n(IRC R316.4)", ha="left", va="bottom")
    _leader(ax, ((x_icf_core0 + x_icf_core1) / 2, y_icf_bot + 10.0), (x_exterior + 30.0, y_footing_top + 10.0), 'ICF stem wall\n6" concrete core,\n11" total width incl. EPS foam', ha="left")

    # Dimensions for ICF depth
    _dim_v(ax, y_footing_top, grade_y, x_exterior + 2.0, '42" to frost (typ.)')

    # ----- Sill, gasket, anchors (schematic) ----------------------------------
    _rect(ax, x_stud_int, y_sill0, stud_depth, sill_gasket, fc="#FFFFFF", ec="black", lw=1.0, z=4)
    _lumber(ax, x_stud_int, y_sill0 + sill_gasket, stud_depth, sill_plate, fc=COL.wood, ec="black", lw=1.2, z=4)
    _leader(ax, (x_stud_int + stud_depth / 2, y_sill0 + sill_gasket + sill_plate / 2), (x_dry_int - 10.0, y_sill1 + 6.0), "PT sill board + sill gasket", ha="right", va="bottom")

    # ----- Above-grade framed wall --------------------------------------------
    _rect(ax, x_stud_int, y_sill1, stud_depth, y_topplate0 - y_sill1, fc=COL.wood, ec="black", lw=1.2, z=3)
    _lumber(ax, x_stud_int, y_topplate0, stud_depth, top_plate, fc=COL.wood, ec="black", lw=1.2, z=5)
    _leader(ax, (x_stud_int + stud_depth / 2, (y_sill1 + y_topplate_top) / 2), (x_dry_int - 10.0, y_topplate_top - 18.0), '2×6 framed wall @ 16" o.c.\n(1 stud shown in section)', ha="right")

    # Interior drywall
    _rect(ax, x_dry_int, y_sill0, drywall, y_topplate_top - y_sill0, fc=COL.drywall, ec="black", lw=1.0, z=4)
    _leader(ax, (x_dry_int + drywall / 2, y_sill1 + 24.0), (x_dry_int - 10.0, y_sill1 + 24.0), '5/8" drywall (interior)', ha="right")

    # Zip-R sheathing (extends down over sill plate onto flashing, and up over raised heel)
    zip_r_bottom = y_sill0 - 0.5
    _rect(ax, x_stud_ext, zip_r_bottom, zip_r, y_raised_heel_top - zip_r_bottom, fc=COL.sheathing, ec="black", lw=1.0, z=4)
    _leader(ax, (x_stud_ext + zip_r, y_sill1 + 62.0), (x_exterior + 30.0, y_sill1 + 62.0), 'Zip-R (or similar) sheathing\n1.5" (R-6.6), taped\n(extends over sill & flashing,\nup over raised heel)')

    # Optional rainscreen mesh (extends over raised heel)
    _rect(ax, x_zip_ext, y_sill1, rainscreen, y_raised_heel_top - y_sill1, fc="none", ec="black", lw=1.0, ls="--", z=4)

    # Metal siding (extends down over sill plate onto flashing, and up over raised heel)
    metal_siding_bottom = y_sill0 - 0.5
    _rect(ax, x_rain_ext, metal_siding_bottom, metal_siding, y_raised_heel_top - metal_siding_bottom, fc=COL.metal_dark, ec="black", lw=1.0, z=4)
    _leader(ax, (x_rain_ext + metal_siding / 2, y_sill1 + 34.0), (x_exterior + 30.0, y_sill1 + 34.0), "Metal siding over optional rainscreen")

    # Z-flashing / drip edge at base of wall cladding (schematic)
    z_y = y_sill0 - 0.2
    z_thk = 0.2
    z_ext_start = (x_stud_ext + z_thk, z_y + 0.7)
    z_ext_steps = [(0.0, -0.8), (x_exterior + 0.2 - z_ext_start[0], 0.0), (0.0, -0.2)]
    _flashing(ax, _path_from_steps(z_ext_start, z_ext_steps), z_thk, fc=COL.flashing, ec="black", lw=0.9, z=6, alpha=0.95)
    _leader(ax, (x_exterior + 0.1, z_y + 0.2), (x_exterior + 30.0, grade_y + 24.0), "Z-flashing / drip edge (exterior)\n(liquid flashing recommended)\nDirects water outward", va="bottom")
    
    z_int_start = (x_stud_int - z_thk, z_y + 0.7)
    z_int_steps = [(0.0, -0.8), (x_dry_int - 0.2 - z_int_start[0], 0.0), (0.0, -0.2)]
    _flashing(ax, _path_from_steps(z_int_start, z_int_steps), z_thk, fc=COL.flashing, ec="black", lw=0.9, z=6, alpha=0.95)
    _leader(ax, (x_dry_int - 6.0, z_y + 0.1), (x_dry_int - 16.0, grade_y + 3.0), "Z-flashing / drip edge (interior)\nDirects water inward to sloped slab", ha="right", va="bottom")

    # ----- Slab (interior, schematic section) ---------------------------------
    x_slab0 = x_icf_eps_int0 - 28.0
    x_slab1 = x_icf_eps_int0
    _rect(ax, x_slab0, grade_y - slab_thick, x_slab1 - x_slab0, slab_thick, fc=COL.concrete, ec="black", lw=1.2, z=2)
    _leader(ax, ((x_slab0 + x_slab1) / 2, grade_y - slab_thick / 2), (x_slab0 - 10.0, grade_y - 8.0), 'Concrete slab (min. 3.5")\n≥3,500 psi (IRC R506.1)\nSlope to drain/door (into page)', ha="right", va="top")

    ax.annotate("Slope (typ.)", xy=(x_slab0 + 6.0, grade_y - 0.2), xytext=(x_slab0 + 18.0, grade_y + 5.0), ha="left", va="bottom", fontsize=9, arrowprops=dict(arrowstyle="->", linewidth=1.0))

    # Optional vapor retarder, XPS, gravel
    _rect(ax, x_slab0, grade_y - slab_thick - vapor_poly, x_slab1 - x_slab0, vapor_poly, fc=COL.membrane, ec="black", lw=0.8, ls="--", z=3)
    _rect(ax, x_slab0, grade_y - slab_thick - vapor_poly - xps, x_slab1 - x_slab0, xps, fc=COL.xps, ec="black", lw=0.8, ls="--", z=2)
    _rect(ax, x_slab0, grade_y - slab_thick - vapor_poly - xps - gravel, x_slab1 - x_slab0, gravel, fc=COL.aggregate, ec="black", lw=0.8, ls="--", hatch=HATCHES.compacted, z=1)
    _leader(ax, (x_slab1 - 2.0, grade_y - slab_thick - vapor_poly - xps / 2), (x_slab0 - 8.0, grade_y - 22.0), "Below slab:\n- Poly vapor retarder\n- 2\" XPS (≥25 psi)\n- 4\" gravel base", ha="center", va="top")

    # ----- Roof / truss at eave (schematic) -----------------------------------
    roof_pitch = pitch  # 4:12 pitch
    bottom_chord_bottom = y_topplate_top
    bottom_chord_y = bottom_chord_bottom + truss_member / 2
    bottom_chord_int = np.array([x_stud_int - 48.0, bottom_chord_y])
    bottom_chord_ext = np.array([x_stud_ext, bottom_chord_y])

    heel_y = bottom_chord_y + raised_heel
    heel_x = x_stud_ext
    top_chord_int_x = bottom_chord_int[0]
    top_chord_int_y = heel_y + (heel_x - top_chord_int_x) * roof_pitch
    top_chord_int = np.array([top_chord_int_x, top_chord_int_y])

    eave_x = heel_x + overhang_length
    eave_y = heel_y - overhang_length * roof_pitch
    eave = np.array([eave_x, eave_y])

    # Draw chords
    bottom_chord_poly = _quad_from_segment(bottom_chord_int, bottom_chord_ext, truss_member)
    ax.add_patch(Polygon(bottom_chord_poly, closed=True, facecolor=COL.wood, edgecolor="black", linewidth=1.2, zorder=5))
    top_chord_poly = _quad_from_segment(top_chord_int, eave, truss_member)
    ax.add_patch(Polygon(top_chord_poly, closed=True, facecolor=COL.wood, edgecolor="black", linewidth=1.2, zorder=5))

    # Raised heel support
    heel_support_x = x_stud_ext - 3.0
    heel_support_bottom = bottom_chord_y + truss_member / 2
    heel_support_top_y = heel_y + (heel_x - heel_support_x) * roof_pitch - truss_member / 2 + 0.5
    heel_support_poly = _quad_from_segment(np.array([heel_support_x, heel_support_bottom]), np.array([heel_support_x, heel_support_top_y]), stud_depth)
    ax.add_patch(Polygon(heel_support_poly, closed=True, facecolor=COL.wood, edgecolor="black", linewidth=1.0, zorder=4))

    # Diagonal web member
    diag_bottom = np.array([bottom_chord_int[0] + 6.0, bottom_chord_y + truss_member / 2])
    diag_top_x = (bottom_chord_int[0] + heel_x) / 2
    diag_top_y = heel_y + (heel_x - diag_top_x) * roof_pitch - truss_member / 2
    diag_top = np.array([diag_top_x, diag_top_y])
    diag_poly = _quad_from_segment(diag_bottom, diag_top, 1.5)
    ax.add_patch(Polygon(diag_poly, closed=True, facecolor=COL.wood, edgecolor="black", linewidth=0.8, zorder=4))
    _leader(ax, ((bottom_chord_int[0] + heel_x) / 2, (bottom_chord_y + top_chord_int_y) / 2), (x_dry_int - 10.0, y_topplate_top + 10.0), 'Gable roof truss @ 16" o.c.\n(~4\' shown, not to full scale)', ha="right", va="bottom")

    # Roof sheathing + underlayment + metal roofing
    roof_seg0, roof_seg1 = top_chord_int, eave
    osb_offset = truss_member / 2 + 0.3
    osb_seg0, osb_seg1 = _offset_segment(roof_seg0, roof_seg1, osb_offset)
    osb_poly = _quad_from_segment(osb_seg0, osb_seg1, 0.5)
    underlayment_seg0, underlayment_seg1 = _offset_segment(roof_seg0, roof_seg1, osb_offset + 0.5)
    underlayment_poly = _quad_from_segment(underlayment_seg0, underlayment_seg1, 0.1)
    metal_seg0, metal_seg1 = _offset_segment(roof_seg0, roof_seg1, osb_offset + 0.6)
    metal_poly = _quad_from_segment(metal_seg0, metal_seg1, 0.5)
    ax.add_patch(Polygon(osb_poly, closed=True, facecolor=COL.sheathing, edgecolor="black", linewidth=0.8, zorder=6))
    ax.add_patch(Polygon(underlayment_poly, closed=True, facecolor=COL.underlayment, edgecolor="black", linewidth=0.6, zorder=7))
    ax.add_patch(Polygon(metal_poly, closed=True, facecolor=COL.metal_dark, edgecolor="black", linewidth=0.8, zorder=8))
    _leader(ax, ((osb_seg0[0] + osb_seg1[0]) / 2, (osb_seg0[1] + osb_seg1[1]) / 2 + 1.5), (x_exterior + 30.0, y_topplate_top + 14.0), "Roof: OSB + underlayment + (optional)\nrainscreen mesh + metal roofing")

    # Fascia board
    fascia_w = 1.5
    fascia_x = eave[0] + truss_member / 2 - 2.5
    soffit_y = eave[1] - truss_member / 2 - 0.5
    fascia_top_y = metal_seg1[1] - 0.2
    fascia_bot_y = soffit_y
    fascia_h = fascia_top_y - fascia_bot_y
    _rect(ax, fascia_x, fascia_bot_y, fascia_w, fascia_h, fc=COL.wood, ec="black", lw=1.2, z=8)

    # Drip edge flashing
    drip_thickness = 0.15
    roof_dir = (metal_seg1 - metal_seg0) / (np.linalg.norm(metal_seg1 - metal_seg0) + 1e-9)
    drip_roof_in = metal_seg1 - roof_dir * 0.6
    drip_roof_out = metal_seg1 + roof_dir * 0.8
    fascia_face_x = fascia_x + fascia_w
    drip_centerline = [drip_roof_in, drip_roof_out, [fascia_face_x + drip_thickness / 2, drip_roof_out[1]], [fascia_face_x + drip_thickness / 2, fascia_bot_y - 0.3]]
    _flashing(ax, drip_centerline, drip_thickness, fc=COL.flashing, ec="black", lw=1.0, z=9, alpha=0.95)
    _leader(ax, (fascia_face_x + drip_thickness/2, (drip_roof_out[1] + fascia_bot_y) / 2), (x_exterior + 30.0, fascia_bot_y - 0.0), "Drip edge flashing wraps over\nroof edge and down fascia face")

    # Vented soffit
    soffit_x0 = x_siding_ext
    soffit_x1 = fascia_x
    _rect(ax, soffit_x0, soffit_y, soffit_x1 - soffit_x0, 0.5, fc=COL.soffit, ec="black", lw=1.0, z=7)
    ax.plot([soffit_x0 + 1.0, soffit_x1 - 1.0], [soffit_y + 0.25, soffit_y + 0.25], color="black", linewidth=0.8, zorder=8, linestyle=":")
    _leader(ax, ((soffit_x0 + soffit_x1) / 2, soffit_y + 0.25), (x_exterior + 30.0, soffit_y - 12.0), "Vented soffit (aluminum recommended)")

    # Ceiling drywall
    ceiling_drywall_y = bottom_chord_y - truss_member / 2 - 0.625
    _rect(ax, x_slab0, ceiling_drywall_y, x_dry_int - x_slab0, 0.625, fc=COL.drywall, ec="black", lw=0.9, z=4)

    # Blown insulation above ceiling
    insulation_bottom_y = bottom_chord_y + truss_member / 2
    original_height = (top_chord_int_y - truss_member / 2) - insulation_bottom_y
    insulation_top_y = insulation_bottom_y + original_height / 3.0
    ax.add_patch(Polygon(np.array([[x_slab0, insulation_bottom_y], [x_stud_int - 4.0, insulation_bottom_y], [x_stud_int - 4.0, insulation_top_y], [x_slab0, insulation_top_y]]), closed=True, facecolor=COL.insulation, edgecolor="black", linewidth=0.8, hatch=HATCHES.compacted, zorder=1))
    _leader(ax, (x_stud_int - 14.0, insulation_bottom_y + 8.0), (x_dry_int - 10.0, insulation_bottom_y + 18.0), 'Ceiling: airtight 5/8" drywall\nAttic insulation above', ha="right")

    # ----- Labels / title / formatting ----------------------------------------
    ax.set_title("Detached Garage Wall Detail (Side View) — Insulated, Unheated (Builder Reference, IFC-driven)", fontsize=13, fontweight="bold", pad=12, loc='left')
    ax.text(x_exterior - 0.0, y_footing_bot - 50.0, "Colin Catlin, 2026", ha="center", va="bottom", fontsize=7)
    ax.set_xlim(x_dry_int - 18.0, x_exterior + 45.0)
    ax.set_ylim(y_footing_bot - 44.0, y_topplate_top + 24.0)
    ax.set_aspect("equal")
    ax.axis("off")

    legend_patches = [
        Patch(facecolor=COL.concrete, edgecolor="black", label="Concrete"),
        Patch(facecolor=COL.eps, edgecolor="black", label="EPS foam"),
        Patch(facecolor=COL.xps, edgecolor="black", label="XPS foam"),
        Patch(facecolor=COL.wood, edgecolor="black", label="Wood framing / plates"),
        Patch(facecolor=COL.drywall, edgecolor="black", label="Drywall"),
        Patch(facecolor=COL.insulation, edgecolor="black", label="Attic Insulation"),
        Patch(facecolor=COL.metal_dark, edgecolor="black", label="Metal cladding / roofing"),
        Patch(facecolor=COL.aggregate, edgecolor="black", label="Stone / gravel"),
    ]
    ax.legend(handles=legend_patches, loc="lower left", bbox_to_anchor=(0.01, 0.01), bbox_transform=ax.transAxes, frameon=True, fontsize=8.5, ncol=2, borderaxespad=0.0, handlelength=1.6, columnspacing=1.2)

    # ----- Notes panel --------------------------------------------------------
    ax_notes.set_xlim(0, 100)
    ax_notes.set_ylim(0, 145)
    ax_notes.axis("off")

    repo_root = Path(__file__).resolve().parents[1]
    raw_notes = load_markdown_notes(repo_root / "notes/garage_wall_detail_side.md")
    ax_notes.text(5, 142, _wrap_notes(raw_notes, width=54), fontsize=9, va="top", ha="left", family="monospace")

    out_path = Path("catlin_house/out/garage_wall_detail_side_ifc.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight", pad_inches=0.02)
    print(out_path)


if __name__ == "__main__":
    main()
