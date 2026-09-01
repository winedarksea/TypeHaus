"""``engineering/wall_panel.py`` against a hand-worked note.

The oracle is ``houses/catlin/notes/board_batten_girt_span.md``, worked by hand from ASCE
7-16 in a separate pass before the module was written — the discipline every calc module in
this package is held to.

Three of these assertions are doing unusual work and are worth reading before changing:

* :func:`test_the_record_is_incomplete_even_though_bending_passes` pins the point of the
  whole item. A d/c of 0.36 is not a pass here: the limit state that governs a concealed
  panel is screw withdrawal and nobody publishes it, so a green ratio against the only table
  anybody printed must never open the gate.
* :func:`test_the_east_and_west_pbr_walls_are_not_items` pins the *scope*. PBR is covered by
  ICC-ES ESR-4729 and stays prescriptive; an item enumerated for it would be this engine
  claiming an engineer is needed where a report already answers.
* :func:`test_a_span_the_allowable_was_not_read_at_is_not_interpolated` pins a refusal.
  Reading 51 psf off a 32" row and applying it to some other spacing is exactly the silent
  wrong answer this module exists to avoid.
"""

from __future__ import annotations

import pytest

from typehaus.engineering.item import Status

#: §2-§5 of the note, hand-worked from ASCE 7-16 before the module existed.
_ORACLE = {
    "mean_roof_height_ft": 25.5990,
    "k_z": 0.669544,
    "q_h_psf": 19.2679,
    "effective_wind_area_ft2": 2.3704,
    "gcp_zone5": -1.4,
    "gcp_zone4": -1.1,
    "gcpi": 0.18,
    "strength_zone5_psf": 30.4432,
    "asd_zone5_psf": 18.2659,
    "asd_zone4_psf": 14.7977,
    "allowable_psf": 51.0,
    "ratio": 0.3582,
}

#: The twenty north/south walls the board & batten override lands on (§1 of the note).
_BOARD_BATTEN_WALLS = {
    "W-M-S1", "W-M-S2", "W-M-N1", "W-M-N2", "W-M-N3", "W-M-N1B", "W-M-N3B",
    "W-S-N1", "W-S-S1", "W-S-S2", "W-S-N2", "W-S-N3", "W-S-N1B", "W-S-N3B",
    "W-A-N1", "W-A-N2", "W-A-N2B", "W-A-S1", "W-A-S2", "W-A-S3",
}


@pytest.fixture(scope="module")
def results(catlin_plan):
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    return EngineeringResults(EngineeringContext(plan=catlin_plan, model=model))


def test_every_board_batten_wall_is_an_item_and_only_those(results):
    ids = {key for key in results if key.startswith("wall_panel/")}
    assert ids == {f"wall_panel/{tag}" for tag in _BOARD_BATTEN_WALLS}


def test_the_east_and_west_pbr_walls_are_not_items(results):
    # ESR-4729 covers PBR at these spacings, so the question stays prescriptive. An item
    # here would be the engine asking for a seal a published report already supplies.
    for tag in ("W-M-E1", "W-M-W1B", "W-S-E1", "W-S-W4"):
        assert f"wall_panel/{tag}" not in results


def test_the_velocity_pressure_matches_the_hand_worked_note(results):
    record = results["wall_panel/W-M-S1"]
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["mean_roof_height"] == pytest.approx(_ORACLE["mean_roof_height_ft"], abs=1e-3)
    assert inputs["velocity_pressure"] == pytest.approx(_ORACLE["q_h_psf"], abs=1e-3)
    assert inputs["design_wind_speed"] == 115.0


def test_the_cladding_pressure_matches_the_hand_worked_note(results):
    record = results["wall_panel/W-M-S1"]
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["support_spacing"] == 32.0
    assert inputs["effective_wind_area"] == pytest.approx(
        _ORACLE["effective_wind_area_ft2"], abs=1e-3)
    assert inputs["GCp_zone5"] == pytest.approx(_ORACLE["gcp_zone5"])
    assert inputs["GCpi"] == pytest.approx(_ORACLE["gcpi"])
    assert inputs["suction_asd"] == pytest.approx(_ORACLE["asd_zone5_psf"], abs=1e-3)


def test_the_demand_is_asd_not_strength(results):
    # 0.6W. Setting a published allowable against the strength-level 30.4 psf would report a
    # margin a third of the real one, and is the mistake the note's §4 is written against.
    record = results["wall_panel/W-M-S1"]
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["suction_asd"] == pytest.approx(0.6 * _ORACLE["strength_zone5_psf"], abs=1e-3)
    assert any(f"{_ORACLE['strength_zone5_psf']:.1f} psf" in note for note in record.notes)


def test_zone_four_is_reported_but_zone_five_governs(results):
    record = results["wall_panel/W-M-S1"]
    assert any(f"{_ORACLE['asd_zone4_psf']:.1f} psf" in note for note in record.notes)
    assert record.governing is not None
    assert record.governing.demand == pytest.approx(_ORACLE["asd_zone5_psf"], abs=1e-3)


def test_bending_is_graded_against_the_declared_allowable(results):
    record = results["wall_panel/W-M-S1"]
    state = record.governing
    assert state is not None
    assert state.capacity == pytest.approx(_ORACLE["allowable_psf"])
    assert state.ratio == pytest.approx(_ORACLE["ratio"], abs=1e-3)
    assert state.ok


def test_the_record_is_incomplete_even_though_bending_passes(results):
    # THE POINT OF THE ITEM. Withdrawal of the concealed leg's screws is what governs a
    # panel like this and is published by nobody, so the only ratio anybody can compute
    # passing must not read as a design.
    record = results["wall_panel/W-M-S1"]
    assert record.status is Status.INCOMPLETE
    assert record.governing is not None and record.governing.ok
    assert any("WITHDRAWAL" in name for name in record.missing)


def test_a_span_the_allowable_was_not_read_at_is_not_interpolated(tmp_path):
    from pathlib import Path

    from _helpers import copy_house

    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    catlin = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    house = copy_house(catlin, tmp_path / "house")
    source = house / "plan" / "assemblies.py"
    text = source.read_text()
    old = "panel_allowable_psf=51.0, panel_allowable_span_in=32.0,"
    assert old in text
    source.write_text(text.replace(old, "panel_allowable_psf=51.0, panel_allowable_span_in=24.0,"))
    loaded = load_plan(house)
    assert loaded.plan is not None, [f.message for f in loaded.findings]
    model, _ = resolve(loaded.plan)
    results = EngineeringResults(EngineeringContext(plan=loaded.plan, model=model))
    record = results["wall_panel/W-M-S1"]
    assert record.limit_states == ()
    assert record.status is Status.INCOMPLETE
    assert any('read at this wall\'s own 32" support spacing' in name
               for name in record.missing)
