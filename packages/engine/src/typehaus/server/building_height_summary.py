"""Finished roof height above the project's average-grade datum, plus exterior footprint."""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel, ResolvedRoof
from typehaus.resolve.roof_finished import finished_roof_elevations


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
    finished_eave_m, finished_peak_m = finished_roof_elevations(model, roof)
    return {
        "roof_tag": roof.tag,
        "midpoint_above_grade_m": round(
            ((finished_eave_m + finished_peak_m) / 2) - site_grade_m, 4
        ),
        "peak_above_grade_m": round(finished_peak_m - site_grade_m, 4),
    }
