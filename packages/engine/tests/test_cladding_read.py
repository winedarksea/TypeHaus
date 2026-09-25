"""``checks/structural/cladding.py`` against a hand-worked note.

The oracle is ``houses/catlin/notes/board_batten_girt_span.md`` — §2-§6.2 worked by hand
from ASCE 7-16, NDS 2018 and AISI S100, and §5b (the inward pressure) worked by hand on
2026-09-22 before this file reproduced it.

Since 2026-09-22 the board & batten is a **manufacturer read**, not an engineering item:
``structural.cladding_wind`` grades the zone-5 demand against the BBD75 guide's own row in
both directions, and ``wall_panel/W-A-N1`` is retired (note §8). What was the item's
withdrawal and pull-through arithmetic is the ``structural.cladding_fastener`` advisory.

The ablations here assert UNKNOWN, not INCOMPLETE: a row that stops describing the wall is
silent about it rather than damning (``published._cladding_drift``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.findings import Result, Severity

#: §2-§6.2 and §5b of the note, hand-worked before the code.
_ORACLE = {
    "mean_roof_height_ft": 25.5990,
    "q_h_psf": 19.2679,
    "effective_wind_area_ft2": 1.3333,
    "gcp_zone5": -1.4,
    "gcp_positive": 1.0,
    "gcpi": 0.18,
    "strength_zone5_psf": 30.4432,
    "asd_zone5_psf": 18.2659,
    "asd_zone4_psf": 14.7977,
    "outward_ratio": 0.3149,
    # §5b: q_h (1.0 + 0.18) = 22.7361 strength, 13.6417 ASD, against 43 inward.
    "strength_inward_psf": 22.7361,
    "asd_inward_psf": 13.6417,
    "inward_ratio": 0.3172,
    # §6: NDS 2018 §12.2 at G 0.55, D 0.190", C_D 1.6, C_M 0.7, the 1-1/2" screw (D3).
    "w": 163.80,
    "w_adjusted": 183.46,
    "thread_penetration_in": 1.0961,
    "capacity_lb": 201.09,
    "demand_lb": 36.5318,
    "withdrawal_ratio": 0.1817,
    # §6.2: AISI S100 Pnov = 1.5 t d'w Fu / 3.0.
    "pull_through_capacity_lb": 310.7,
    "pull_through_ratio": 0.1176,
}

#: The twenty north/south walls the board & batten lands on (§1 of the note).
_BOARD_BATTEN_WALLS = {
    "W-M-S1", "W-M-S2", "W-M-N1", "W-M-N2", "W-M-N3", "W-M-N1B", "W-M-N3B",
    "W-S-N1", "W-S-S1", "W-S-S2", "W-S-N2", "W-S-N3", "W-S-N1B", "W-S-N3B",
    "W-A-N1", "W-A-N2", "W-A-N2B", "W-A-S1", "W-A-S2", "W-A-S3",
}
_FOOTNOTE = "does not address web crippling, fasteners, support material or load testing"

_CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"


def _wind(ctx):
    from typehaus.checks.structural.cladding import cladding_wind
    return cladding_wind(ctx)


def _fastener(ctx):
    from typehaus.checks.structural.cladding import cladding_fastener
    return cladding_fastener(ctx)


@pytest.fixture(scope="module")
def wind_findings(catlin_ctx):
    return _wind(catlin_ctx)


def _variant(tmp_path, edit):
    """catlin with one edit to ``plan/assemblies/materials_metal.py`` — the ablation harness."""
    from _helpers import copy_house

    from typehaus.checks.run import build_context
    from typehaus.source import load_plan

    house = copy_house(_CATLIN, tmp_path / "house")
    source = house / "plan" / "assemblies" / "materials_metal.py"
    source.write_text(edit(source.read_text()))
    loaded = load_plan(house)
    assert loaded.plan is not None, [f.message for f in loaded.findings]
    return build_context(loaded.plan, house)[0]


def _replace(old: str, new: str):
    def edit(text: str) -> str:
        assert old in text, old
        return text.replace(old, new, 1)
    return edit


def _direction(findings, word):
    return next(f for f in findings if f" ASD {word}" in f.message)


# --- scope ---------------------------------------------------------------------------------

def test_the_twenty_walls_are_one_read_in_both_directions(wind_findings):
    assert len(wind_findings) == 2
    for finding in wind_findings:
        assert set(finding.element_tags) == _BOARD_BATTEN_WALLS
        assert finding.result is Result.PASS
        assert finding.engineering_item is None


def test_the_east_and_west_pbr_walls_are_out_of_scope(wind_findings):
    for tag in ("W-M-E1", "W-M-W1B", "W-S-E1", "W-S-W4"):
        assert all(tag not in f.element_tags for f in wind_findings)


def test_the_item_left_the_register(catlin_ctx):
    from typehaus.engineering import registered_kinds

    assert "wall_panel" not in registered_kinds()
    assert not any(item.startswith("wall_panel/") for item in catlin_ctx.engineering)
    assert "girt_screw/W-A-N1" in catlin_ctx.engineering


# --- the demand, against the note ------------------------------------------------------------

def test_the_shared_wind_leaf_reproduces_the_note(catlin_model_ro):
    from typehaus import wind

    height = wind.mean_roof_height_ft(catlin_model_ro)
    assert height == pytest.approx(_ORACLE["mean_roof_height_ft"], abs=1e-3)
    basis = wind.WindBasis(115.0, "B", "II")
    q_h = wind.velocity_pressure_psf(basis, height)
    assert q_h == pytest.approx(_ORACLE["q_h_psf"], abs=1e-3)
    area = wind.effective_wind_area_ft2(24.0)
    assert area == pytest.approx(_ORACLE["effective_wind_area_ft2"], abs=1e-3)
    assert wind.external_pressure_coefficient(area, "5") == _ORACLE["gcp_zone5"]
    assert wind.external_pressure_coefficient(area, "5", sign="positive") == \
        _ORACLE["gcp_positive"]

    strength, asd = wind.cladding_pressure_asd_psf(q_h, area, "5")
    assert strength == pytest.approx(_ORACLE["strength_zone5_psf"], abs=1e-3)
    assert asd == pytest.approx(_ORACLE["asd_zone5_psf"], abs=1e-3)
    assert wind.cladding_pressure_asd_psf(q_h, area, "4")[1] == pytest.approx(
        _ORACLE["asd_zone4_psf"], abs=1e-3)
    strength, asd = wind.cladding_pressure_asd_psf(q_h, area, "5", sign="positive")
    assert strength == pytest.approx(_ORACLE["strength_inward_psf"], abs=1e-3)
    assert asd == pytest.approx(_ORACLE["asd_inward_psf"], abs=1e-3)


def test_the_positive_curve_steps_down_on_the_log_axis():
    from typehaus import wind

    assert wind.external_pressure_coefficient(500.0, "5", sign="positive") == 0.7
    mid = wind.external_pressure_coefficient(70.7107, "4", sign="positive")
    assert mid == pytest.approx(0.85, abs=1e-3)


def test_outward_is_graded_against_58(wind_findings):
    finding = _direction(wind_findings, "outward")
    assert f"d/c {_ORACLE['outward_ratio']:.3f}" in finding.message
    assert "<= 58 psf" in finding.message


def test_inward_is_graded_against_43_and_governs(wind_findings):
    """§5b: a lower demand against a lower allowable, and the ratios cross."""
    finding = _direction(wind_findings, "inward")
    assert f"{_ORACLE['asd_inward_psf']:.1f} psf ASD inward" in finding.message
    assert f"d/c {_ORACLE['inward_ratio']:.3f}" in finding.message
    assert "<= 43 psf" in finding.message
    assert _ORACLE["inward_ratio"] > _ORACLE["outward_ratio"]


def test_the_footnote_is_on_every_finding(wind_findings):
    for finding in wind_findings:
        assert _FOOTNOTE in finding.message
        assert "graded here as a condition" in finding.message


# --- drift: a row that stops describing the wall is UNKNOWN -----------------------------------

def _all_unknown(ctx, fragment):
    findings = _wind(ctx)
    assert len(findings) == 2
    for finding in findings:
        assert finding.result is Result.UNKNOWN, finding.message
        assert fragment in finding.message, finding.message
        assert _FOOTNOTE in finding.message


def test_a_wider_girt_spacing_than_the_row_drifts(tmp_path):
    """Increase-only: a row read at 18" says nothing about 24" girts (the table publishes
    MORE at tighter spacing), while one read at 36" covers them (next test)."""
    ctx = _variant(tmp_path, _replace("fastener_spacing=inch(24),", "fastener_spacing=inch(18),"))
    _all_unknown(ctx, "indexed at 18\" fastener spacing")


def test_a_tighter_girt_spacing_is_still_covered(tmp_path):
    ctx = _variant(tmp_path, _replace("fastener_spacing=inch(24),", "fastener_spacing=inch(36),"))
    assert all(f.result is Result.PASS for f in _wind(ctx))


def test_another_screw_drifts(tmp_path):
    ctx = _variant(tmp_path, _replace(
        'panel_fastener="#10-12 x 1-1/2\\" pancake head wood screw,',
        'panel_fastener="#12-14 x 1-1/2\\" hex washer head screw,'))
    _all_unknown(ctx, "the maker names")


def test_a_screw_shorter_than_the_named_one_drifts(tmp_path):
    """Length is increase-only: the named 1" is a floor (D3 takes the 1-1/2")."""
    ctx = _variant(tmp_path, _replace(
        'panel_fastener="#10-12 x 1-1/2\\" pancake',
        'panel_fastener="#10-12 x 3/4\\" pancake'))
    _all_unknown(ctx, 'a shorter 3/4" screw')


def test_another_coverage_drifts(tmp_path):
    ctx = _variant(tmp_path, _replace("fastener_coverage_in=12.0,", "fastener_coverage_in=10.0,"))
    _all_unknown(ctx, "coverage")


def test_a_higher_judged_demand_is_required(tmp_path):
    ctx = _variant(tmp_path, _replace("demand_psf=18.27,", "demand_psf=15.0,"))
    _all_unknown(ctx, "judged against 15.00 psf")


def test_a_retyped_member_drifts(tmp_path):
    ctx = _variant(tmp_path, _replace('member="BBD75-1212",', 'member="BBD75-1010",'))
    _all_unknown(ctx, "the row is for 'BBD75-1010'")


def test_an_unauthored_row_is_unknown_with_the_hint(tmp_path):
    def strip(text: str) -> str:
        start = text.index("             published_cladding=PublishedCladdingLoad(")
        end = text.index('exposure="B"),\n', start) + len('exposure="B"),\n')
        return text[:start] + text[end:]
    findings = _wind(_variant(tmp_path, strip))
    assert len(findings) == 2
    assert all(f.result is Result.UNKNOWN for f in findings)
    assert all("no published cladding load row" in f.message for f in findings)


def test_an_unquoted_open_framing_permission_is_unknown(tmp_path):
    """A panel nobody's literature puts on girts is the wrong product, not a table to read."""
    def strip(text: str) -> str:
        lines = [line for line in text.splitlines(keepends=True)
                 if not line.lstrip().startswith("open_framing_source=")]
        assert len(lines) < len(text.splitlines()), "the field moved; fix this test"
        return "".join(lines)
    findings = _wind(_variant(tmp_path, strip))
    assert len(findings) == 1
    assert findings[0].result is Result.UNKNOWN
    assert "open_framing_source" in findings[0].message


# --- the fastener advisory --------------------------------------------------------------------

def test_withdrawal_is_computed_from_the_standard(catlin_ctx):
    """NDS 2018 §12.2, term by term against §6 of the note."""
    from typehaus.checks.structural.cladding_fastener import withdrawal_allowable_lb

    hand = withdrawal_allowable_lb(0.55, 0.190, 1.5, 1.5, 0.0239)
    assert hand.w_per_in == pytest.approx(_ORACLE["w"], abs=0.01)
    assert hand.w_adjusted_per_in == pytest.approx(_ORACLE["w_adjusted"], abs=0.01)
    assert hand.thread_penetration_in == pytest.approx(_ORACLE["thread_penetration_in"], abs=1e-3)
    assert hand.capacity_lb == pytest.approx(_ORACLE["capacity_lb"], abs=0.01)

    [finding] = _fastener(catlin_ctx)
    assert finding.result is Result.PASS
    assert finding.severity is Severity.WARN
    assert finding.engineering_item is None
    assert f"{_ORACLE['demand_lb']:.1f} lb per screw" in finding.message
    assert f"d/c {_ORACLE['withdrawal_ratio']:.3f}" in finding.message


def test_head_pull_through_is_graded_the_third_mode_the_code_names(catlin_ctx):
    from typehaus.checks.structural.cladding_fastener import pull_through_allowable_lb

    assert pull_through_allowable_lb(0.40) == pytest.approx(
        _ORACLE["pull_through_capacity_lb"], abs=0.1)
    [finding] = _fastener(catlin_ctx)
    assert f"d/c {_ORACLE['pull_through_ratio']:.3f}" in finding.message


def test_the_whole_screw_ladder_is_printed_once_each(catlin_ctx):
    [finding] = _fastener(catlin_ctx)
    for rung in ('1" -> 0.596" pen', '1.5" -> 1.096" pen', '2" -> 1.500" pen'):
        assert finding.message.count(rung) == 1, rung


def test_the_stocked_1in_screw_moves_withdrawal_and_nothing_else(tmp_path):
    """The pre-D3 spec: the maker's own named 1" still reads, at the note's history 0.334."""
    ctx = _variant(tmp_path, lambda text: _replace(
        "panel_fastener_length_in=1.5,", "panel_fastener_length_in=1.0,")(_replace(
            'panel_fastener="#10-12 x 1-1/2\\"', 'panel_fastener="#10-12 x 1\\"')(text)))
    [finding] = _fastener(ctx)
    assert "d/c 0.334" in finding.message
    assert f"d/c {_ORACLE['pull_through_ratio']:.3f}" in finding.message
    assert all(f.result is Result.PASS for f in _wind(ctx))


def test_an_absent_head_diameter_is_unknown_and_names_itself(tmp_path):
    ctx = _variant(tmp_path, _replace("panel_fastener_head_dia_in=0.40,", ""))
    [finding] = _fastener(ctx)
    assert finding.result is Result.UNKNOWN
    assert "panel_fastener_head_dia_in" in finding.message
