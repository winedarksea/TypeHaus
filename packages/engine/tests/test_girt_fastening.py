"""``checks/structural/girt_fastening.py`` against a hand-worked note.

The oracle is ``houses/catlin/notes/catlin_truss_engineering.md`` §2 (h above the lowest
ground) and §3 (the screw, read off ICC-ES ESR-1078 Tables 1A/2/3), hand-worked 2026-11-22.

Since 2026-11-22 the girt screw is a **published read**, not an engineering item
(``girt_screw/W-A-N1`` is retired, owner decision 21). The ablations assert UNKNOWN, not a
FAIL: a row that stops describing the wall is silent about it rather than damning, while a
measured shortfall (thread standing in the stack, demand past the row) is a FAIL.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.findings import Result

#: §2 and §3.5 of the note, worked by hand before the check reproduced them.
_ORACLE = {
    "mean_roof_height_ft": 34.7626,
    "q_h_psf": 21.0282,
    "asd_zone5_psf": 19.9348,
    "tributary_ft2": 5.3333,
    "simple_lb": 106.32,
    "demand_lb": 146.19,
    "withdrawal_lb": 255.0,
    "withdrawal_ratio": 0.5733,
    "pull_through_lb": 200.0,
    "pull_through_ratio": 0.7309,
    "tension_ratio": 0.11245,
    "wet_pull_through_ratio": 1.0442,
}

_CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"
#: Every wall whose outer band is a block-standoff girt: 34 EXT_2X6 plus the plant room's two.
_GIRT_WALL_COUNT = 36


def _girt(ctx):
    from typehaus.checks.structural.girt_fastening import girt_fastening
    return girt_fastening(ctx)


@pytest.fixture(scope="module")
def findings(catlin_ctx):
    return _girt(catlin_ctx)


def _variant(tmp_path, edit):
    """catlin with one edit to ``plan/assemblies/envelope_walls.py``, as a check context."""
    from _helpers import copy_house

    from typehaus.checks.run import build_context
    from typehaus.source import load_plan

    house = copy_house(_CATLIN, tmp_path / "house")
    source = house / "plan" / "assemblies" / "envelope_walls.py"
    text = source.read_text()
    source.write_text(edit(text))
    loaded = load_plan(house)
    assert loaded.plan is not None, [f.message for f in loaded.findings]
    return build_context(loaded.plan, house)[0]


def _replace(old: str, new: str):
    def edit(text: str) -> str:
        assert old in text, old
        return text.replace(old, new, 1)
    return edit


# --- scope, and the retirement ------------------------------------------------------------

def test_every_girt_wall_is_one_read(findings):
    assert len(findings) == 1
    finding = findings[0]
    assert finding.result is Result.PASS
    assert len(finding.element_tags) == _GIRT_WALL_COUNT
    assert finding.engineering_item is None
    for tag in ("W-A-N1", "W-M-S1", "W-M-E1", "W-M-W1B", "W-S-W4"):
        assert tag in finding.element_tags


def test_the_item_left_the_register(catlin_ctx):
    from typehaus.engineering import registered_kinds

    assert "girt_screw" not in registered_kinds()
    assert not any(item.startswith("girt_screw/") for item in catlin_ctx.engineering)


# --- the demand, against the note ---------------------------------------------------------

def test_the_demand_is_the_panels_suction_times_continuity(catlin_model_ro):
    from typehaus import wind
    from typehaus.checks.structural import girt_fastening_table as table

    height = wind.mean_roof_height_ft(catlin_model_ro)
    assert height == pytest.approx(_ORACLE["mean_roof_height_ft"], abs=1e-3)
    q_h = wind.velocity_pressure_psf(wind.WindBasis(115.0, "B", "II"), height)
    assert q_h == pytest.approx(_ORACLE["q_h_psf"], abs=1e-3)
    _, asd = wind.cladding_pressure_asd_psf(q_h, wind.effective_wind_area_ft2(24.0), "5")
    assert asd == pytest.approx(_ORACLE["asd_zone5_psf"], abs=1e-3)
    assert table.tributary_area_ft2(32.0, 24.0) == pytest.approx(_ORACLE["tributary_ft2"],
                                                                 abs=1e-3)
    simple = asd * table.tributary_area_ft2(32.0, 24.0)
    assert simple == pytest.approx(_ORACLE["simple_lb"], abs=0.01)
    assert table.crossing_demand_lb(asd, 32.0, 24.0) == pytest.approx(
        _ORACLE["demand_lb"], abs=0.01)
    # Statics: 5wL/4 over two equal spans, 11wL/10 over three or more.
    assert table.GIRT_CONTINUITY == 1.25 and table.PANEL_CONTINUITY == 1.10


def test_the_finding_prints_the_ratios_and_the_wet_sensitivity(findings):
    text = findings[0].message
    assert f"{_ORACLE['demand_lb']:.1f} lb ASD" in text
    assert f"d/c {_ORACLE['withdrawal_ratio']:.3f}" in text
    assert f"d/c {_ORACLE['pull_through_ratio']:.3f}" in text
    assert f"d/c {_ORACLE['tension_ratio']:.3f}" in text
    assert "Governing: head pull-through" in text
    # The wet allowable is printed beside the dry pass and never applied to it.
    assert f"d/c {_ORACLE['wet_pull_through_ratio']:.2f}" in text
    assert "ACQ-D girt stock at retention <= 0.40 pcf" in text
    assert "LSL studs are outside ESR-1078" in text


# --- the thread bookkeeping and the rows ---------------------------------------------------

def test_thread_bookkeeping_matches_the_note():
    from typehaus.checks.structural import girt_fastening_table as table

    assert table.plain_shank_in(8.0, 2.0) == pytest.approx(6.0)
    assert table.thread_in_side_member(8.0, 2.0, 6.0) == pytest.approx(0.0)
    assert table.thread_in_main_member(8.0, 2.0, 6.5) == pytest.approx(1.5)
    # SDWS22800DB, 8" with a 3" thread (ER-192 Table 7): 1" of it inside the 6" stack.
    assert table.thread_in_side_member(8.0, 3.0, 6.0) == pytest.approx(1.0)
    assert table.plain_shank_in(8.0, 3.0) < 6.0


def test_the_rows_are_the_reports(findings):
    from typehaus.checks.structural import girt_fastening_table as table

    assert table.row_at(table.WITHDRAWAL_LB_PER_IN, 0.42) == 170.0
    assert table.row_at(table.PULL_THROUGH_LB, 0.55) == 200.0
    # Between rows the lower row governs; below the lowest there is no row.
    assert table.row_at(table.PULL_THROUGH_LB, 0.52) == 160.0
    assert table.row_at(table.PULL_THROUGH_LB, 0.40) is None
    assert table.TENSILE_LB == 1300.0
    assert table.TIMBERLOK_1A["TLOK08"] == (8.0, 2.0)


# --- the refusals ---------------------------------------------------------------------------

def _all_unknown(ctx, fragment):
    """The edit reaches EXT_2X6 only; the plant room's own band (``interior_wet.py``) still
    reads, so the edited design is the one UNKNOWN among the findings."""
    out = _girt(ctx)
    bad = [f for f in out if f.result is Result.UNKNOWN]
    assert len(bad) == 1, [f.message for f in out]
    assert fragment in bad[0].message, bad[0].message


def test_a_screw_whose_thread_stands_in_the_stack_fails(tmp_path):
    """The SDWS's own 3" thread: 5" of plain shank against a 6" stack, 1" of thread in it.

    A measured fact about the building, graded before the report rows are compared.
    """
    ctx = _variant(tmp_path, _replace("standoff_fastener_thread_in=2.0,",
                                      "standoff_fastener_thread_in=3.0,"))
    bad = [f for f in _girt(ctx) if f.result is Result.FAIL]
    assert len(bad) == 1
    assert "1\" of thread stands inside it" in bad[0].message


def test_a_longer_authored_pull_through_than_the_row_drifts(tmp_path):
    ctx = _variant(tmp_path, _replace("standoff_fastener_pull_through_lb=200.0,",
                                      "standoff_fastener_pull_through_lb=260.0,"))
    _all_unknown(ctx, "exceeds Table 3's 200")


def test_a_higher_withdrawal_than_the_row_drifts(tmp_path):
    ctx = _variant(tmp_path, _replace("standoff_fastener_withdrawal_lb_per_in=170.0,",
                                      "standoff_fastener_withdrawal_lb_per_in=220.0,"))
    _all_unknown(ctx, "exceeds Table 2's 170")


def test_a_girt_in_spf_is_refused_not_read_at_the_pine_row(tmp_path):
    """Table 3 at SG 0.42 is 110 lb; the authored 200 is the SG 0.55 row."""
    def edit(text: str) -> str:
        old = 'Layer(name="outer-girt", material_ref="kdat"'
        assert old in text
        return text.replace(old, 'Layer(name="outer-girt", material_ref="spf"', 1)
    _all_unknown(_variant(tmp_path, edit), "exceeds Table 3's 110")


def test_another_part_drifts(tmp_path):
    ctx = _variant(tmp_path, _replace('standoff_fastener_part="TLOK08"',
                                      'standoff_fastener_part="HLGM8"'))
    _all_unknown(ctx, "not a TimberLOK")


def test_a_source_that_is_not_esr_1078_drifts(tmp_path):
    ctx = _variant(tmp_path, _replace('standoff_fastener_source="ICC-ES ESR-1078',
                                      'standoff_fastener_source="IAPMO UES ER-192'))
    _all_unknown(ctx, "does not name ICC-ES ESR-1078")


def test_a_shorter_timberlok_cannot_clamp_the_stack(tmp_path):
    """TLOK06 is a real TimberLOK (Table 1A) but 6" less its 2" thread is 4" of shank against
    a 6" stack: 2" of thread stands in it. A fact, so FAIL, whatever the rows say."""
    def edit(text: str) -> str:
        text = text.replace('standoff_fastener_part="TLOK08"', 'standoff_fastener_part="TLOK06"')
        return text.replace("standoff_fastener_length_in=8.0,", "standoff_fastener_length_in=6.0,")
    bad = [f for f in _girt(_variant(tmp_path, edit)) if f.result is Result.FAIL]
    assert len(bad) == 1 and "jacks the girt off the block" in bad[0].message


def test_a_girt_band_with_no_screw_authored_is_unknown_and_names_every_field(tmp_path):
    def edit(text: str) -> str:
        assert 'standoff="block",' in text
        text = text.replace('standoff="block",', 'standoff="block")),', 1)
        return "".join(line for line in text.splitlines(keepends=True)
                       if "standoff_fastener" not in line)
    out = _girt(_variant(tmp_path, edit))
    assert out[0].result is Result.UNKNOWN
    assert "standoff_fastener_withdrawal_lb_per_in" in out[0].message


def test_a_tighter_block_module_still_passes_and_a_wider_course_fails(tmp_path):
    """Demand is computed each run: widen the course to 48" and pull-through is past 200 lb."""
    ctx = _variant(tmp_path, _replace('spacing=inch(24), layout_origin="line"',
                                      'spacing=inch(48), layout_origin="line"'))
    bad = [f for f in _girt(ctx) if f.result is Result.FAIL]
    assert bad and "past its published row" in bad[0].message
