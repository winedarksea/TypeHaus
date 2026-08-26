"""Finished roof height above the project's average-grade datum, plus exterior footprint."""

from __future__ import annotations

import math

from typehaus.model.enums import LayerFunction
from typehaus.resolve.model import ResolvedModel, ResolvedRoof


def build_building_height_summary(model: ResolvedModel) -> dict[str, object]:
    """Return finished midpoint/peak roof heights and per-storey exterior footprint dims.

    ``Site.grade`` is the authored project-wide average-grade datum.  The established
    elevation convention uses the main-floor zero datum when it is omitted, so this
    summary does the same rather than inferring a terrain surface from sparse spots.

    ``footprint`` rides along here rather than in its own summary because it answers the
    same "what does this building measure, from the outside" question the roof heights do —
    cladding-to-cladding, not the framer's axis-to-axis grid.
    """
    from typehaus.server.space_summary import exterior_footprint_dimensions_m

    site_grade_m = (model.plan.project.site.grade.meters
                    if model.plan.project.site.grade is not None else 0.0)
    return {
        "average_ground_grade_m": round(site_grade_m, 4),
        "roofs": [
            _roof_height_row(model, roof, site_grade_m)
            for roof in sorted(model.roofs, key=lambda item: item.tag)
        ],
        "footprint": exterior_footprint_dimensions_m(model),
    }


def _roof_height_row(
    model: ResolvedModel, roof: ResolvedRoof, site_grade_m: float
) -> dict[str, float | str]:
    finished_eave_m, finished_peak_m = _finished_roof_elevations(model, roof)
    return {
        "roof_tag": roof.tag,
        "midpoint_above_grade_m": round(
            ((finished_eave_m + finished_peak_m) / 2) - site_grade_m, 4
        ),
        "peak_above_grade_m": round(finished_peak_m - site_grade_m, 4),
    }


def _finished_roof_elevations(model: ResolvedModel, roof: ResolvedRoof) -> tuple[float, float]:
    """Return exterior finished eave and high-point elevations in meters.

    The resolved roof plane ends at the rafter top.  Every layer following the final
    structural layer sits normal to that plane, matching ``roofOffsetter`` in the UI.
    At a gable ridge the two roof planes meet in a miter, so its vertical offset is
    greater than a single plane's normal vertical component.
    """
    assembly = model.plan.library.resolve_assembly(roof.assembly)
    exterior_thickness_m = 0.0
    if assembly is not None:
        final_structure_index = max(
            (index for index, layer in enumerate(assembly.layers)
             if layer.function is LayerFunction.STRUCTURE),
            default=-1,
        )
        exterior_thickness_m = sum(
            layer.thickness.meters for layer in assembly.layers[final_structure_index + 1:]
        )

    roof_run_m = _roof_run_m(roof)
    slope = ((roof.ridge_z_m - roof.eave_z_m) / roof_run_m
             if roof_run_m > 1e-9 else 0.0)
    plane_normal_vertical = 1 / math.sqrt(1 + slope * slope)
    finished_eave_m = roof.eave_z_m + exterior_thickness_m * plane_normal_vertical
    ridge_offset = (exterior_thickness_m / plane_normal_vertical
                    if roof.form == "gable"
                    else exterior_thickness_m * plane_normal_vertical)
    return finished_eave_m, roof.ridge_z_m + ridge_offset


def _roof_run_m(roof: ResolvedRoof) -> float:
    coordinates = [point[1 if roof.ridge_direction == "x" else 0] for point in roof.footprint]
    span_m = max(coordinates) - min(coordinates)
    return span_m / 2 if roof.form == "gable" else span_m
