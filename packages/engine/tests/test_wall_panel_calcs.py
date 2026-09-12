"""``engineering/wall_panel.py`` against a hand-worked note.

The oracle is ``houses/catlin/notes/board_batten_girt_span.md``, worked by hand from ASCE
7-16 and NDS 2018 in a separate pass before the module was written — the discipline every
calc module in this package is held to.

Four of these assertions are doing unusual work and are worth reading before changing:

* :func:`test_the_twenty_walls_are_one_item` pins the grouping. Twenty walls clad in one
  product over one girt course are one design and one seal; twenty identical sheets are
  twenty chances for a reviewer to stamp nineteen and miss one.
* :func:`test_withdrawal_is_computed_from_the_standard` pins the reason this item became
  stampable. Nobody publishes a pull-out value for a concealed leg into wood; NDS §12.2 is
  the rational design IAPMO UES ER-309 expressly authorises, and the arithmetic is checked
  term by term against the note rather than against itself.
* :func:`test_the_east_and_west_pbr_walls_are_not_items` pins the *scope*. PBR's wall
  capacity is published in the manufacturers' own wall span tables (144-168 psf at 3'-0"),
  so it stays prescriptive; an item enumerated for it would be this engine claiming an
  engineer is needed where a table already answers.
* :func:`test_a_span_the_allowable_was_not_read_at_is_not_interpolated` pins a refusal.
  Reading 58 psf off a 24" row and applying it to some other spacing is exactly the silent
  wrong answer this module exists to avoid.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.engineering.item import Status

#: §2-§6 of the note, hand-worked from ASCE 7-16 and NDS 2018 before the module existed.
_ORACLE = {
    "mean_roof_height_ft": 25.5990,
    "k_z": 0.669544,
    "q_h_psf": 19.2679,
    "effective_wind_area_ft2": 1.3333,
    "gcp_zone5": -1.4,
    "gcp_zone4": -1.1,
    "gcpi": 0.18,
    "strength_zone5_psf": 30.4432,
    "asd_zone5_psf": 18.2659,
    "asd_zone4_psf": 14.7977,
    "allowable_psf": 58.0,
    "bending_ratio": 0.3149,
    # NDS 2018 §12.2, note §6: G 0.55 (Table 12.3.3A southern pine), D 0.190", C_D 1.6,
    # C_M 0.7, a 2" screw through a 24 ga flange taking the full 1-1/2" girt.
    "w": 163.80,
    "w_adjusted": 183.46,
    "thread_penetration_in": 1.50,
    "capacity_lb": 275.19,
    "tributary_ft2": 1.8333,
    "demand_lb": 33.49,
    "withdrawal_ratio": 0.1217,
    # The 1" screw the panel order ships with, printed as an alternate — and the reason the
    # house specifies 2".
    "one_inch_ratio": 0.306,
}

#: The twenty north/south walls the board & batten override lands on (§1 of the note).
_BOARD_BATTEN_WALLS = {
    "W-M-S1", "W-M-S2", "W-M-N1", "W-M-N2", "W-M-N3", "W-M-N1B", "W-M-N3B",
    "W-S-N1", "W-S-S1", "W-S-S2", "W-S-N2", "W-S-N3", "W-S-N1B", "W-S-N3B",
    "W-A-N1", "W-A-N2", "W-A-N2B", "W-A-S1", "W-A-S2", "W-A-S3",
}

#: The group's key: the lowest member tag, which is what a person types.
_ITEM = "wall_panel/W-A-N1"

_CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def results(catlin_plan):
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    return EngineeringResults(EngineeringContext(plan=catlin_plan, model=model))


@pytest.fixture(scope="module")
def record(results):
    return results[_ITEM]


def _variant(tmp_path, edit):
    """catlin with one edit to ``plan/assemblies.py``, resolved — the ablation harness."""
    from _helpers import copy_house

    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    house = copy_house(_CATLIN, tmp_path / "house")
    source = house / "plan" / "assemblies.py"
    source.write_text(edit(source.read_text()))
    loaded = load_plan(house)
    assert loaded.plan is not None, [f.message for f in loaded.findings]
    model, _ = resolve(loaded.plan)
    return EngineeringResults(EngineeringContext(plan=loaded.plan, model=model))


def _replace(old: str, new: str):
    def edit(text: str) -> str:
        assert old in text, old
        return text.replace(old, new, 1)
    return edit


# --- scope and grouping ------------------------------------------------------------------

def test_the_twenty_walls_are_one_item(results, record):
    ids = {key for key in results if key.startswith("wall_panel/")}
    assert ids == {_ITEM}
    assert set(record.element_tags) == _BOARD_BATTEN_WALLS
    assert len(record.element_tags) == 20


def test_any_member_resolves_to_the_group(results):
    # `haus engineering --item wall_panel/W-M-S1` has to reach the design that grades it.
    # `in` stays strict: the register lists group keys, not their members.
    assert results["wall_panel/W-M-S1"].item_id == _ITEM
    assert "wall_panel/W-M-S1" not in results


def test_membership_is_in_the_fingerprint(record):
    # `element_tags` is not hashed, so without this input a wall could join or leave the
    # group and a stamp pinned to the old set would still read FRESH.
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["panel_count"] == 20.0


def test_the_east_and_west_pbr_walls_are_not_items(record):
    for tag in ("W-M-E1", "W-M-W1B", "W-S-E1", "W-S-W4"):
        assert tag not in record.element_tags


# --- the wind demand ---------------------------------------------------------------------

def test_the_velocity_pressure_matches_the_hand_worked_note(record):
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["mean_roof_height"] == pytest.approx(_ORACLE["mean_roof_height_ft"], abs=1e-3)
    assert inputs["velocity_pressure"] == pytest.approx(_ORACLE["q_h_psf"], abs=1e-3)
    assert inputs["design_wind_speed"] == 115.0


def test_the_cladding_pressure_matches_the_hand_worked_note(record):
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["support_spacing"] == pytest.approx(24.0, abs=1e-6)
    assert inputs["effective_wind_area"] == pytest.approx(
        _ORACLE["effective_wind_area_ft2"], abs=1e-3)
    assert inputs["GCp_zone5"] == pytest.approx(_ORACLE["gcp_zone5"])
    assert inputs["GCpi"] == pytest.approx(_ORACLE["gcpi"])
    assert inputs["suction_asd"] == pytest.approx(_ORACLE["asd_zone5_psf"], abs=1e-3)


def test_the_demand_is_asd_not_strength(record):
    # 0.6W. Setting a published allowable against the strength-level 30.4 psf would report a
    # margin a third of the real one, and is the mistake the note's §4 is written against.
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["suction_asd"] == pytest.approx(0.6 * _ORACLE["strength_zone5_psf"], abs=1e-3)
    assert any(f"{_ORACLE['strength_zone5_psf']:.1f} psf" in note for note in record.notes)


def test_zone_four_is_reported_but_zone_five_governs(record):
    assert any(f"{_ORACLE['asd_zone4_psf']:.1f} psf" in note for note in record.notes)


# --- the two limit states ----------------------------------------------------------------

def _state(record, fragment):
    return next(s for s in record.limit_states if fragment in s.name)


def test_bending_is_graded_against_the_declared_allowable(record):
    state = _state(record, "bending")
    assert state.capacity == pytest.approx(_ORACLE["allowable_psf"])
    assert state.ratio == pytest.approx(_ORACLE["bending_ratio"], abs=1e-3)
    assert state.ok


def test_withdrawal_is_computed_from_the_standard(record):
    """NDS 2018 §12.2, term by term against §6 of the note."""
    from typehaus.engineering.wall_panel_withdrawal import withdrawal_allowable_lb

    hand = withdrawal_allowable_lb(0.55, 0.190, 2.0, 1.5, 0.0239)
    assert hand.w_per_in == pytest.approx(_ORACLE["w"], abs=0.01)
    assert hand.w_adjusted_per_in == pytest.approx(_ORACLE["w_adjusted"], abs=0.01)
    assert hand.thread_penetration_in == pytest.approx(_ORACLE["thread_penetration_in"], abs=1e-3)
    assert hand.capacity_lb == pytest.approx(_ORACLE["capacity_lb"], abs=0.01)

    state = _state(record, "withdrawal")
    assert state.capacity == pytest.approx(_ORACLE["capacity_lb"], abs=0.01)
    assert state.demand == pytest.approx(_ORACLE["demand_lb"], abs=0.01)
    assert state.ratio == pytest.approx(_ORACLE["withdrawal_ratio"], abs=1e-3)
    assert state.ok
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["tributary_area"] == pytest.approx(_ORACLE["tributary_ft2"], abs=1e-3)
    assert inputs["fastener_demand"] == pytest.approx(_ORACLE["demand_lb"], abs=0.01)
    assert inputs["thread_penetration"] == pytest.approx(1.50, abs=1e-3)


def test_the_shorter_screws_are_printed_as_alternates(record):
    """The 1" screw a panel order ships with is 0.31 — passing, and not what is specified."""
    from typehaus.engineering.wall_panel_withdrawal import (
        fastener_demand_lb, withdrawal_allowable_lb)

    short = withdrawal_allowable_lb(0.55, 0.190, 1.0, 1.5, 0.0239)
    demand = fastener_demand_lb(_ORACLE["asd_zone5_psf"], 24.0, 11.0)
    assert demand / short.capacity_lb == pytest.approx(_ORACLE["one_inch_ratio"], abs=1e-3)
    assert any('1" -> 0.596" pen' in note for note in record.notes)


def test_bending_governs_and_the_item_is_finished(record):
    """Both states graded, both under 1, nothing missing — the item is stampable.

    Until 2026-09-11 this record was hard-wired INCOMPLETE because withdrawal was
    unpublished. Computing it from NDS is what closed it; the status is now earned by
    every state being graded, not asserted by the module.
    """
    assert record.status is Status.OK
    assert record.missing == ()
    assert len(record.limit_states) == 2
    assert record.governing is not None
    assert "bending" in record.governing.name
    assert record.governing.ratio == pytest.approx(_ORACLE["bending_ratio"], abs=1e-3)


def test_the_open_framing_permission_is_quoted_not_summarised(record):
    assert any("open framing" in note and "Metal Sales" in note for note in record.notes)


# --- the refusals ------------------------------------------------------------------------

def test_a_span_the_allowable_was_not_read_at_is_not_interpolated(tmp_path):
    results = _variant(tmp_path, _replace(
        "panel_allowable_psf=58.0, panel_allowable_span_in=24.0,",
        "panel_allowable_psf=58.0, panel_allowable_span_in=32.0,"))
    record = results[_ITEM]
    assert record.status is Status.INCOMPLETE
    assert not any("bending" in s.name for s in record.limit_states)
    assert any('read at this wall\'s own 24" support spacing' in name
               for name in record.missing)


def test_a_shorter_screw_moves_the_ratio_and_nothing_else(tmp_path):
    results = _variant(tmp_path, _replace(
        "panel_fastener_length_in=2.0,", "panel_fastener_length_in=1.0,"))
    state = _state(results[_ITEM], "withdrawal")
    assert state.ratio == pytest.approx(_ORACLE["one_inch_ratio"], abs=1e-3)
    assert results[_ITEM].status is Status.OK


def test_an_absent_diameter_is_incomplete_and_names_itself(tmp_path):
    results = _variant(tmp_path, _replace(
        "panel_fastener_diameter_in=0.190,", ""))
    record = results[_ITEM]
    assert record.status is Status.INCOMPLETE
    assert any("panel_fastener_diameter_in" in name for name in record.missing)
    assert not any("withdrawal" in s.name for s in record.limit_states)


def test_an_unquoted_open_framing_permission_is_incomplete(tmp_path):
    """A panel nobody's literature puts on girts is the wrong product, not a maths problem."""
    results = _variant(tmp_path, lambda text: _strip_open_framing(text))
    record = results[_ITEM]
    assert record.status is Status.INCOMPLETE
    assert any("open_framing_source" in name for name in record.missing)


def _strip_open_framing(text: str) -> str:
    lines = [line for line in text.splitlines(keepends=True)
             if not line.lstrip().startswith("open_framing_source=")]
    assert len(lines) < len(text.splitlines()), "the field moved; fix this test"
    return "".join(lines)
