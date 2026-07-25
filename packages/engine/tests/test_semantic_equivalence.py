"""The semantic-equivalence primitives, without ifcopenshell (→ 30 WP3.7).

``test_catlin_equivalence_m3.py`` exercises these against the real archived IFC, which is
slow and needs ifcopenshell. The normalization rules that make two modelling conventions
comparable — storey-key aliasing, layer-per-wall vs layerset-per-wall run merging, corner
walls staying apart — are pure geometry and are pinned here on synthetic entities.
"""

from __future__ import annotations

import pytest

from typehaus.diff.equivalence import (
    STATUS_DIVERGENT,
    STATUS_EQUIVALENT,
    STATUS_ONLY_CURRENT,
    STATUS_ONLY_REFERENCE,
    EquivalenceTolerance,
    compare_semantic_models,
)
from typehaus.diff.semantic import (
    SemanticEntity,
    SemanticModel,
    SemanticStorey,
    merge_runs,
    normalize_storey_key,
)

WALL_HEIGHT_M = 2.7432          # 9', both models' framed storey height
WALL_LENGTH_M = 10.9728         # 36'
LAYER_THICKNESS_M = 0.05


def _wall(name: str, *, x: float, y: float, z: float = WALL_HEIGHT_M / 2,
          size: tuple[float, float, float], storey: str = "main",
          layers: tuple[str, ...] = (), members: int = 0) -> SemanticEntity:
    return SemanticEntity(guid=name, name=name, category="wall", storey_key=storey,
                          centroid_m=(x, y, z), size_m=size, layer_names=layers,
                          framing_member_count=members)


def _layer_stack(count: int, storey: str = "main") -> list[SemanticEntity]:
    """One wall line drawn the reference's way: one wall per layer, stacked outward."""
    return [
        _wall(f"layer-{index}", x=WALL_LENGTH_M / 2,
              y=index * LAYER_THICKNESS_M + LAYER_THICKNESS_M / 2,
              size=(WALL_LENGTH_M, LAYER_THICKNESS_M, WALL_HEIGHT_M), storey=storey)
        for index in range(count)
    ]


def test_storey_keys_normalize_and_honour_aliases():
    assert normalize_storey_key("Main Floor") == "main"
    assert normalize_storey_key("Attic Floor") == "attic"
    assert normalize_storey_key("Garage Level") == "garage"
    assert normalize_storey_key("Sunken Garden Floor", {"Sunken Garden Floor": "basement"}) \
        == "basement"


def test_layer_walls_merge_into_one_run_carrying_its_layer_count():
    runs = merge_runs(_layer_stack(7))
    assert len(runs) == 1
    run = runs[0]
    assert run.layer_count == 7          # seven bands across the run's thickness
    assert run.plan_length_m == pytest.approx(WALL_LENGTH_M)
    assert run.plan_thickness_m == pytest.approx(7 * LAYER_THICKNESS_M)
    assert len(run.merged_from) == 7


def test_collinear_segments_merge_but_a_corner_does_not():
    half = WALL_LENGTH_M / 2
    south_west = _wall("W-S1", x=half / 2, y=0.15,
                       size=(half, 0.3, WALL_HEIGHT_M))
    south_east = _wall("W-S2", x=half + half / 2, y=0.15,
                       size=(half, 0.3, WALL_HEIGHT_M))
    east = _wall("W-E1", x=WALL_LENGTH_M - 0.15, y=WALL_LENGTH_M / 2,
                 size=(0.3, WALL_LENGTH_M, WALL_HEIGHT_M))
    runs = merge_runs([south_west, south_east, east])
    assert len(runs) == 2, [run.merged_from or run.name for run in runs]
    merged = next(run for run in runs if run.merged_from)
    assert merged.plan_length_m == pytest.approx(WALL_LENGTH_M)
    assert merged.layer_count == 1       # one band: a continuation, not a layer


def test_stacked_storeys_never_merge_across_the_storey_line():
    lower = _wall("W-M-S1", x=1.0, y=0.15, z=WALL_HEIGHT_M / 2,
                  size=(2.0, 0.3, WALL_HEIGHT_M), storey="main")
    upper = _wall("W-S-S1", x=1.0, y=0.15, z=WALL_HEIGHT_M * 1.5,
                  size=(2.0, 0.3, WALL_HEIGHT_M), storey="second")
    assert len(merge_runs([lower, upper])) == 2


def _model(label: str, entities, storeys=(("main", 0.0),)) -> SemanticModel:
    return SemanticModel(
        label=label, schema="IFC4",
        storeys=tuple(SemanticStorey(name=key, key=key, elevation_m=elevation,
                                     building="House") for key, elevation in storeys),
        entities=tuple(entities), class_census={"IfcWall": len(entities)},
        buildings=("House",))


def test_layerset_and_layer_per_wall_conventions_compare_as_equivalent():
    """The same wall, drawn seven ways on one side and once on the other, is one wall."""
    reference = _model("old", merge_runs(_layer_stack(7)))
    current = _model("new", merge_runs([
        _wall("W-M-S1", x=WALL_LENGTH_M / 2, y=7 * LAYER_THICKNESS_M / 2,
              size=(WALL_LENGTH_M, 7 * LAYER_THICKNESS_M, WALL_HEIGHT_M),
              layers=tuple(f"layer-{index}" for index in range(7)))]))
    report = compare_semantic_models(reference, current)
    assert report.status_counts() == {STATUS_EQUIVALENT: 1}
    row = report.entities[0]
    assert row.reference_layer_count == row.current_layer_count == 7
    assert report.equivalent_fraction("wall") == 1.0


def test_a_moved_wall_reports_as_divergent_with_its_reason():
    reference = _model("old", merge_runs(_layer_stack(3)))
    moved = merge_runs(_layer_stack(3))[0]
    shifted = SemanticEntity(
        guid=moved.guid, name="W-M-S1", category="wall", storey_key="main",
        centroid_m=(moved.centroid_m[0], moved.centroid_m[1] + 0.4, moved.centroid_m[2]),
        size_m=moved.size_m, layer_names=("a", "b", "c"))
    report = compare_semantic_models(reference, _model("new", [shifted]))
    row = report.entities[0]
    assert row.status == STATUS_DIVERGENT
    assert row.placement_delta_m == pytest.approx(0.4)
    assert any("placement" in reason for reason in row.reasons)


def test_unpaired_entities_are_reported_from_the_side_they_exist_on():
    reference = _model("old", merge_runs(_layer_stack(3)))
    far_away = _wall("W-X", x=100.0, y=100.0, size=(2.0, 0.3, WALL_HEIGHT_M))
    report = compare_semantic_models(reference, _model("new", [far_away]))
    statuses = {item.status for item in report.entities}
    assert statuses == {STATUS_ONLY_REFERENCE, STATUS_ONLY_CURRENT}
    assert [item.reference_name for item in report.by_status(STATUS_ONLY_REFERENCE)]
    assert [item.current_name for item in report.by_status(STATUS_ONLY_CURRENT)] == ["W-X"]


def test_framing_counts_are_compared_relatively():
    """A tenth more studs on a 100-member wall is a solver detail; twice as many is not."""
    def _framed(members: int) -> SemanticModel:
        return _model(f"framed-{members}", [
            _wall("W", x=1.0, y=0.15, size=(2.0, 0.3, WALL_HEIGHT_M), members=members)])

    tolerance = EquivalenceTolerance()
    assert compare_semantic_models(_framed(100), _framed(105),
                                   tolerance).entities[0].status == STATUS_EQUIVALENT
    assert compare_semantic_models(_framed(100), _framed(200),
                                   tolerance).entities[0].status == STATUS_DIVERGENT


def test_storeys_and_census_land_in_the_serialized_report():
    reference = _model("old", merge_runs(_layer_stack(3)), storeys=(("main", 0.0),))
    current = _model("new", merge_runs(_layer_stack(3)),
                     storeys=(("main", 0.0), ("attic", 5.4864)))
    report = compare_semantic_models(reference, current)
    payload = report.as_dict()
    assert {row["storey"] for row in payload["storeys"]} == {"main", "attic"}
    attic = next(row for row in payload["storeys"] if row["storey"] == "attic")
    assert attic["status"] == STATUS_ONLY_CURRENT
    assert payload["census"] == [{"storey": "main", "category": "wall",
                                  "reference": 1, "current": 1, "delta": 0}]
