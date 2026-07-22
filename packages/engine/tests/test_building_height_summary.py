"""Finished roof-height statistics stay aligned with rendered roof geometry."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from typehaus.server.building_height_summary import build_building_height_summary


def test_catlin_height_summary_uses_site_grade_and_finished_gable_miter(catlin_model):
    summary = build_building_height_summary(catlin_model)
    house = next(row for row in summary["roofs"] if row["roof_tag"] == "RF-HOUSE")
    roof = next(item for item in catlin_model.roofs if item.tag == "RF-HOUSE")
    assembly = catlin_model.plan.library.resolve_assembly(roof.assembly)
    assert assembly is not None
    thickness = sum(layer.thickness.meters for layer in assembly.layers[1:])
    span = max(point[0] for point in roof.footprint) - min(point[0] for point in roof.footprint)
    slope = (roof.ridge_z_m - roof.eave_z_m) / (span / 2)
    expected_peak = roof.ridge_z_m + thickness * math.sqrt(1 + slope * slope)
    expected_eave = roof.eave_z_m + thickness / math.sqrt(1 + slope * slope)
    grade = catlin_model.plan.project.site.grade
    assert grade is not None
    assert (sum(spot.elevation.meters for spot in catlin_model.plan.project.site.spot_elevations)
            / len(catlin_model.plan.project.site.spot_elevations)) != pytest.approx(grade.meters)
    assert summary["average_ground_grade_m"] == pytest.approx(grade.meters)
    assert house["peak_above_grade_m"] == pytest.approx(expected_peak - grade.meters, abs=1e-4)
    assert house["midpoint_above_grade_m"] == pytest.approx(
        ((expected_eave + expected_peak) / 2) - grade.meters, abs=1e-4
    )


def test_shed_peak_uses_single_plane_finish_offset_and_zero_grade_fallback(catlin_model):
    gable = next(item for item in catlin_model.roofs if item.tag == "RF-HOUSE")
    shed = replace(gable, tag="RF-SHED", form="shed")
    model = replace(
        catlin_model,
        roofs=[shed],
        plan=catlin_model.plan.model_copy(update={
            "project": catlin_model.plan.project.model_copy(update={
                "site": catlin_model.plan.project.site.model_copy(update={"grade": None})
            })
        }),
    )
    summary = build_building_height_summary(model)
    assembly = model.plan.library.resolve_assembly(shed.assembly)
    assert assembly is not None
    thickness = sum(layer.thickness.meters for layer in assembly.layers[1:])
    span = max(point[0] for point in shed.footprint) - min(point[0] for point in shed.footprint)
    slope = (shed.ridge_z_m - shed.eave_z_m) / span
    expected_peak = shed.ridge_z_m + thickness / math.sqrt(1 + slope * slope)
    assert summary["average_ground_grade_m"] == 0.0
    assert summary["roofs"] == [{
        "roof_tag": "RF-SHED",
        "midpoint_above_grade_m": pytest.approx(
            (shed.eave_z_m + thickness / math.sqrt(1 + slope * slope) + expected_peak) / 2,
            abs=1e-4,
        ),
        "peak_above_grade_m": pytest.approx(expected_peak, abs=1e-4),
    }]
