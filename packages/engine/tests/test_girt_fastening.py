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
    "demand_lb": 151.88,          # x 1.25 x 8/7
    "weight_lb": 11.237,          # panel 6.400 + girt 3.642 + block 1.195
    "moment_in_lb": 64.21,        # at panel profile 1.25"
    "pry_lb": 36.69,              # / 1.75"
    "tension_lb": 188.57,
    "withdrawal_lb": 408.0,       # 170 x 1.5 x C_D 1.6, stud dry
    "withdrawal_ratio": 0.462,
    "pull_through_lb": 224.0,      # 200 x C_M 0.7 x C_D 1.6
    "pull_through_ratio": 0.842,
    "tension_ratio": 0.145,
    "z_prime_lb": 201.6,          # 180 x 1.6 x 0.7
    "z_alpha_lb": 406.53,
    "combined_ratio": 0.465,
    "dead_ratio": 0.291,
    "nds_w_per_in": 95.02,        # 2850 x 0.42^2 x 0.189
    "lsl_withdrawal_lb": 228.05,  # 95.02 x 1.5 x 1.6
    "lsl_withdrawal_ratio": 0.827,
    "lsl_z_alpha_lb": 228.0,      # 228.05 x 201.6 / (228.05 cos^2 + 201.6 sin^2) at 86.59 deg
    "lsl_combined_ratio": 0.829,
}

_CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"
#: Every wall whose outer band is a block-standoff girt: 22 on SPF studs (second storey, attic)
#: and 14 on the main storey's LSL, which ESR-1078 §3.2 leaves out.
_SPF_WALLS, _LSL_WALLS = 22, 14


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

def _group(findings, tag):
    [read] = [f for f in findings if tag in f.element_tags]
    return read


def _spf(findings):
    return _group(findings, "W-A-N1")          # attic: SPF studs


def test_the_spf_and_lsl_walls_are_two_reads(findings):
    """SPF studs read ESR-1078 Table 2; the main storey's LSL, outside §3.2, reads NDS 12.2.2.1
    at ESR-1387's equivalent SG (below). Neither is UNKNOWN, neither is an engineering item."""
    assert len(findings) == 2
    spf, lsl = _spf(findings), _group(findings, "W-M-S1")
    assert spf.result is Result.PASS and lsl.result is Result.PASS
    assert spf.engineering_item is None and lsl.engineering_item is None
    assert len(spf.element_tags) == _SPF_WALLS and len(lsl.element_tags) == _LSL_WALLS


def test_lsl_withdrawal_is_the_nds_equation_at_esr_1387s_edge_sg(findings):
    """ESR-1387 Table 2: TimberStrand LSL nails and screws, withdrawal, installed in edge 0.42.
    NDS 12.2.2.1 W = 2850 G^2 D = 2850 x 0.42^2 x 0.189 = 95.02 lb/in; x 1.5" x C_D 1.6 = 228.05."""
    from typehaus.checks.structural import girt_fastening_table as table

    assert table.LSL_WITHDRAWAL_EDGE_SG == 0.42
    assert table.nds_wood_screw_withdrawal_per_in(0.42, 0.189) == pytest.approx(
        _ORACLE["nds_w_per_in"], abs=0.01)
    text = _group(findings, "W-M-S1").message
    assert "NDS 12.2.2.1" in text and "ESR-1387" in text and "installed in edge" in text
    wd = f"= {_ORACLE['lsl_withdrawal_lb']:.0f} lb (d/c {_ORACLE['lsl_withdrawal_ratio']:.3f})"
    assert wd in text
    assert f"Z'a {_ORACLE['lsl_z_alpha_lb']:.0f} lb" in text
    assert f"(d/c {_ORACLE['lsl_combined_ratio']:.3f})" in text
    # The girt's pull-through (in scope) still governs both groups.
    assert "Governing: head pull-through" in text


def test_another_engineered_wood_has_no_published_route_and_is_unknown(catlin_ctx):
    """LVL and PSL are not in ESR-1078 §3.2 and nothing here reads them: refused, not passed."""
    import dataclasses

    from typehaus.checks.structural.girt_fastening import _crossings, _drift

    crossing = next(c for c in _crossings(catlin_ctx) if c.stud_material == "lsl")
    for tag in ("lvl", "psl"):
        reason = _drift(dataclasses.replace(crossing, stud_material=tag), 1.5)
        assert reason is not None and "engineered wood product" in reason and "§3.2" in reason
    assert _drift(crossing, 1.5) is None


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
    assert asd * table.tributary_area_ft2(32.0, 24.0) == pytest.approx(
        _ORACLE["simple_lb"], abs=0.01)
    assert table.crossing_demand_lb(asd, 32.0, 24.0) == pytest.approx(
        _ORACLE["demand_lb"], abs=0.01)
    # Statics: 5wL/4 over two equal spans; the panel's worst interior reaction over 3+ spans
    # is the 4-span 8/7 (3 spans 1.10, 5 spans 1.132).
    assert table.GIRT_CONTINUITY == 1.25
    assert abs(table.PANEL_CONTINUITY - 8 / 7) < 1e-12


def test_gravity_pries_the_screw(catlin_model_ro):
    """§3.5a by hand: 11.237 lb hung off the sheathing, 64.21 in-lb over 1.75" = 36.69 lb."""
    from typehaus.checks.structural import girt_fastening_table as table

    weight, moment, tension = table.prying(32.0, 24.0, 1.5, 4.5, 1.25, 600.0)
    assert weight == pytest.approx(_ORACLE["weight_lb"], abs=0.01)
    assert moment == pytest.approx(_ORACLE["moment_in_lb"], abs=0.05)
    assert tension == pytest.approx(_ORACLE["pry_lb"], abs=0.05)


def test_nds_12_4_1_combines_lateral_and_withdrawal():
    """Eq. 12.4-1 at the note's angle: Z'a = 408 x 201.6 / (408 cos^2 a + 201.6 sin^2 a)."""
    import math

    from typehaus.checks.structural import girt_fastening_table as table

    alpha = math.atan2(_ORACLE["tension_lb"], _ORACLE["weight_lb"])
    assert math.degrees(alpha) == pytest.approx(86.59, abs=0.01)
    z_alpha = table.combined_allowable_lb(408.0, 201.6, alpha)
    assert z_alpha == pytest.approx(_ORACLE["z_alpha_lb"], abs=0.1)
    # Pure withdrawal and pure lateral recover their own capacities.
    assert table.combined_allowable_lb(408.0, 201.6, math.pi / 2) == pytest.approx(408.0)
    assert table.combined_allowable_lb(408.0, 201.6, 0.0) == pytest.approx(201.6)


def test_the_finding_prints_the_combination_and_the_ratios(findings):
    text = _spf(findings).message
    assert f"{_ORACLE['tension_lb']:.1f} lb of screw tension" in text
    assert "D + 0.6W, ASCE 7-16 §2.4.1(5)" in text
    assert f"= {_ORACLE['withdrawal_lb']:.0f} lb (d/c {_ORACLE['withdrawal_ratio']:.3f})" in text
    pull = f"= {_ORACLE['pull_through_lb']:.0f} lb (d/c {_ORACLE['pull_through_ratio']:.3f})"
    assert pull in text
    assert f"(d/c {_ORACLE['tension_ratio']:.3f})" in text        # Table 1A tension, no factor
    assert f"Z'a {_ORACLE['z_alpha_lb']:.0f} lb" in text
    assert f"(d/c {_ORACLE['combined_ratio']:.3f})" in text
    assert f"dead alone at C_D 0.9 d/c {_ORACLE['dead_ratio']:.3f}" in text
    assert "Governing: head pull-through" in text
    assert "ACQ-D girt stock at retention <= 0.40 pcf" in text


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
    # Table 4, 2-1/2" row: Z (parallel, perpendicular) at SG 0.42 is 200 / 180.
    assert table.row_at({k: v[1] for k, v in table.LATERAL_LB.items()}, 0.42) == 180.0
    # NDS 2018 Table 2.3.2 wind 1.6 (cap 11.3.2), Table 11.3.3 wet 0.7.
    assert table.C_D_WIND == 1.6 and table.C_D_DEAD == 0.9 and table.WET_SERVICE_FACTOR == 0.70
    assert table.TIMBERLOK_1A["TLOK08"] == (8.0, 2.0)


# --- the refusals ---------------------------------------------------------------------------

def _all_unknown(ctx, fragment):
    """The edit reaches every EXT_2X6 wall, so the SPF group (W-A-N1) is among the findings
    that name the drift; the plant room's own band (``interior_wet.py``) still reads."""
    out = _girt(ctx)
    bad = [f for f in out if f.result is Result.UNKNOWN and fragment in f.message]
    assert bad, [f.message for f in out]
    assert any("W-A-N1" in f.element_tags for f in bad)


def test_a_screw_whose_thread_stands_in_the_stack_fails(tmp_path):
    """The SDWS's own 3" thread: 5" of plain shank against a 6" stack, 1" of thread in it.

    A measured fact about the building, graded before the report rows are compared.
    """
    ctx = _variant(tmp_path, _replace("standoff_fastener_thread_in=2.0,",
                                      "standoff_fastener_thread_in=3.0,"))
    bad = [f for f in _girt(ctx) if f.result is Result.FAIL]
    assert bad and "1\" of thread stands inside it" in bad[0].message


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
    assert bad and "jacks the girt off the block" in bad[0].message


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
