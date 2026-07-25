"""WP2.14 — declared house variants, their overrides, and the compare surfaces (→ 21b).

``test_variant_compare.py`` covers the compare *engine* on ad-hoc selections; this module
covers the declared side: ``variants.toml`` parsing, the override vocabulary, the envelope /
check deltas the compare view shows, the assembly delta compare (#53), and the CLI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from typehaus.analysis import assembly_metrics
from typehaus.diff.assembly_compare import compare_assemblies
from typehaus.diff.compare import VariantSelection, compare_variants, variant_plan
from typehaus.diff.variants import (
    LayerThicknessOverride,
    apply_layer_thickness,
    find_variant,
    load_variants,
)
from typehaus.source import load_plan

_ZIPR = "HOUSE_WALL_2X6_WITH_ZIPR"
_CI_2X4 = "HOUSE_WALL_2X4_WITH_CI"
_ZIPR_LAYER = "zip-r"


@pytest.fixture(scope="module")
def starter_variants(starter_dir: Path):
    return load_variants(starter_dir)


def test_starter_declares_a_baseline_and_two_overrides(starter_variants):
    names = [spec.name for spec in starter_variants]
    assert names == ["as-authored", "2x4-ci", "thicker-zip-r"]
    baseline = find_variant(starter_variants, "as-authored")
    assert baseline.override_count == 0
    swap = find_variant(starter_variants, "2x4-ci")
    assert swap.assembly_swaps == {_ZIPR: _CI_2X4}
    thicker = find_variant(starter_variants, "thicker-zip-r")
    assert [(item.assembly, item.layer, item.thickness_in) for item in thicker.layer_thickness] \
        == [(_ZIPR, _ZIPR_LAYER, 2.5)]


def test_a_house_without_the_file_declares_no_variants(tmp_path: Path):
    assert load_variants(tmp_path) == ()


def test_an_unknown_variant_name_names_the_ones_that_exist(starter_variants):
    with pytest.raises(ValueError) as error:
        find_variant(starter_variants, "nope")
    assert "2x4-ci" in str(error.value)


def test_layer_thickness_override_rewrites_the_authored_assembly(starter_dir: Path):
    plan = load_plan(starter_dir).plan
    original = next(layer for layer in plan.library.assembly(_ZIPR).layers
                    if layer.name == _ZIPR_LAYER)
    assert original.thickness.inches == pytest.approx(1.5)

    bumped = apply_layer_thickness(
        plan, (LayerThicknessOverride(assembly=_ZIPR, layer=_ZIPR_LAYER, thickness_in=2.5),))
    layer = next(item for item in bumped.library.assembly(_ZIPR).layers
                 if item.name == _ZIPR_LAYER)
    assert layer.thickness.inches == pytest.approx(2.5)
    # The base plan is untouched: a variant never mutates what it was derived from.
    assert next(item for item in plan.library.assembly(_ZIPR).layers
                if item.name == _ZIPR_LAYER).thickness.inches == pytest.approx(1.5)
    # ...and the wall it thickens gets the R-value the extra insulation buys.
    before = assembly_metrics(plan.library.resolve_assembly(_ZIPR), plan.library)
    after = assembly_metrics(bumped.library.resolve_assembly(_ZIPR), bumped.library)
    assert after.r_value.value.r_us > before.r_value.value.r_us
    assert after.thickness_in == pytest.approx(before.thickness_in + 1.0)


@pytest.mark.parametrize("override, message", [
    (LayerThicknessOverride(assembly="NO_SUCH", layer="x", thickness_in=1.0), "NO_SUCH"),
    (LayerThicknessOverride(assembly=_ZIPR, layer="no-such-layer", thickness_in=1.0),
     "no-such-layer"),
])
def test_an_override_that_matches_nothing_is_an_error_not_a_no_op(starter_dir: Path,
                                                                 override, message):
    plan = load_plan(starter_dir).plan
    with pytest.raises(ValueError) as error:
        apply_layer_thickness(plan, (override,))
    assert message in str(error.value)


def test_a_swap_to_an_assembly_the_plan_cannot_resolve_is_rejected(starter_dir: Path):
    """The failure mode this guards: the walls silently vanish and compare reads as deletion."""
    with pytest.raises(ValueError) as error:
        variant_plan(VariantSelection(house=starter_dir, swaps={_ZIPR: "NOT_IN_LIBRARY"}))
    assert "NOT_IN_LIBRARY" in str(error.value)


def test_declared_variants_build_and_compare_with_envelope_and_check_deltas(
        starter_dir: Path, starter_variants):
    baseline = find_variant(starter_variants, "as-authored").selection(starter_dir)
    swapped = find_variant(starter_variants, "2x4-ci").selection(starter_dir)
    report = compare_variants(baseline, swapped)

    assert report.label_a == "as-authored" and report.label_b == "2x4-ci"
    assert report.diff.substantive(), "a thinner exterior wall must move geometry"
    assert report.quantity_deltas, "2x6 studs become 2x4 studs in the takeoff"
    # The envelope roll-up names both walls: one leaves the design, the other enters it.
    assemblies = {item.assembly for item in report.envelope_deltas}
    assert assemblies == {_ZIPR, _CI_2X4}
    assert all(item.note for item in report.envelope_deltas if item.delta is None)
    # Losing R-value moves a code check — the answer the compare view exists to give.
    assert any(item.check_id == "code.energy_prescriptive" for item in report.check_deltas)


def test_layer_thickness_variant_thickens_walls_without_changing_the_takeoff(
        starter_dir: Path, starter_variants):
    baseline = find_variant(starter_variants, "as-authored").selection(starter_dir)
    thicker = find_variant(starter_variants, "thicker-zip-r").selection(starter_dir)
    report = compare_variants(baseline, thicker, include_checks=False)
    assert [change.kind.value for change in report.diff.substantive()] == \
        ["resized"] * len(report.diff.substantive())
    envelope = {(item.assembly, item.metric): item for item in report.envelope_deltas}
    assert envelope[(_ZIPR, "thickness_in")].delta == pytest.approx(1.0)
    assert envelope[(_ZIPR, "r_value")].delta > 0
    # Sheathing thickness is not a framing member: the stud takeoff must not move.
    assert report.quantity_deltas == []


def test_assembly_delta_compare_reads_r_thickness_layers_and_stc(starter_dir: Path):
    library = load_plan(starter_dir).plan.library
    comparison = compare_assemblies(library, [_ZIPR, _CI_2X4, "INT_2X4_PARTITION"])
    assert comparison.baseline_tag == _ZIPR
    assert [item.tag for item in comparison.metrics] == [_ZIPR, _CI_2X4, "INT_2X4_PARTITION"]

    deltas = {item.metric: item for item in comparison.deltas[_CI_2X4]}
    assert deltas["r_value"].delta < 0        # the 2x4 CI wall is the weaker envelope
    assert deltas["thickness_in"].delta == pytest.approx(-1.98, abs=0.01)
    # STC is a lab test, never computed: unknown on both sides stays an unknown delta.
    assert deltas["stc"].delta is None
    partition = {item.metric: item for item in comparison.deltas["INT_2X4_PARTITION"]}
    assert partition["stc"].candidate == 36.0

    payload = comparison.as_dict()
    assert set(payload) == {"baseline", "assemblies", "deltas"}
    assert json.loads(comparison.to_json()) == payload


def test_assembly_compare_needs_two_real_assemblies(starter_dir: Path):
    library = load_plan(starter_dir).plan.library
    with pytest.raises(ValueError):
        compare_assemblies(library, [_ZIPR])
    with pytest.raises(ValueError):
        compare_assemblies(library, [_ZIPR, "NOT_AN_ASSEMBLY"])


def _run(*args: str):
    from typehaus.cli.app import app

    return CliRunner().invoke(app, list(args))


def test_cli_lists_variants_and_writes_the_catalog(starter_dir: Path):
    result = _run("variants", "list", str(starter_dir), "--json")
    assert result.exit_code == 0, result.output
    catalog = json.loads((starter_dir / "out" / "variants.json").read_text())
    assert {item["name"] for item in catalog} == {"as-authored", "2x4-ci", "thicker-zip-r"}


def test_cli_assembly_compare_renders_the_delta_row(starter_dir: Path):
    result = _run("variants", "assemblies", _ZIPR, _CI_2X4, "--house", str(starter_dir))
    assert result.exit_code == 0, result.output
    assert "r_value" in result.output
    written = json.loads((starter_dir / "out" / "assembly_compare.json").read_text())
    assert written["baseline"] == _ZIPR


def test_cli_compare_writes_compare_json(starter_dir: Path):
    result = _run("variants", "compare", "as-authored", "thicker-zip-r",
                  "--house", str(starter_dir), "--no-checks")
    assert result.exit_code == 0, result.output
    payload = json.loads((starter_dir / "out" / "compare.json").read_text())
    assert payload["variants"] == {"a": "as-authored", "b": "thicker-zip-r"}
    assert payload["envelope_deltas"]


def test_cli_rejects_an_undeclared_variant(starter_dir: Path):
    result = _run("variants", "compare", "as-authored", "nope", "--house", str(starter_dir))
    assert result.exit_code == 1
    assert "nope" in result.output
