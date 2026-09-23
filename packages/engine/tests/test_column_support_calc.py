"""``engineering/column_support.py`` against ``notes/balcony_moment_columns.md`` §11 / §13c.

The note is hand-worked in a separate pass; the numbers below are ITS, and the engine is what
is being checked. Two refusals are pinned too, because a limit state nobody can break on
purpose is not being tested: an embedment past the stem, and a joint with no roughening.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.engineering.item import Status

CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"

#: §11a-§11d as re-worked in §13c (2026-09-23, each edge beam on its own 9.75' strip):
#: (bearing C, φBn), (T per bar, φAs fy), (Vu, φVn), (ld, embedment). P_u fell, so the
#: couple needs MORE dowel and the block is a little shallower.
_ORACLE = {
    "PT-SG-BR1": {"bearing": (9_378, 38_825), "tension": (5_032, 16_740),
                  "shear": (410.9, 50_168), "development": (21.2, 24.0)},
    "PT-SG-BF1": {"bearing": (9_247, 38_817), "tension": (4_935, 16_740),
                  "shear": (410.9, 50_277), "development": (21.2, 24.0)},
}
_LABELS = {"bearing": "bearing on the wall top", "tension": "dowel tension across the joint",
           "shear": "shear friction across the cold joint",
           "development": "dowel development into the stem"}


def _results(plan):
    from typehaus.engineering import EngineeringContext, EngineeringResults
    from typehaus.resolve import resolve

    model, _ = resolve(plan)
    return EngineeringResults(EngineeringContext(plan=plan, model=model, soil_class="GM"))


@pytest.fixture(scope="module")
def results(catlin_plan):
    return _results(catlin_plan)


def _state(record, column, key):
    return next(s for s in record.limit_states if s.name == f"{column}: {_LABELS[key]}")


@pytest.mark.parametrize("column", sorted(_ORACLE))
@pytest.mark.parametrize("key", sorted(_LABELS))
def test_the_joint_reproduces_the_note(results, column, key) -> None:
    record = results["column_support/W-SG-W1"]
    state = _state(record, column, key)
    demand, capacity = _ORACLE[column][key]
    assert state.demand == pytest.approx(demand, rel=0.003)
    assert state.capacity == pytest.approx(capacity, rel=0.003)


def test_both_walls_are_computed_and_pass(results) -> None:
    for wall in ("W-SG-W1", "W-SG-E1"):
        record = results[f"column_support/{wall}"]
        assert record.status is Status.OK, record.missing
        assert record.governing.name.endswith("dowel development into the stem")
        assert any("base_rotation/<column>" in note for note in record.notes)


def test_a_flush_round_takes_no_confinement_credit(results) -> None:
    """§11a: the 12" round on a 12" stem — √(A2/A1) is 1.0, read off the wall, not assumed."""
    record = results["column_support/W-SG-W1"]
    root = next(q for q in record.inputs if q.name == "PT-SG-BR1.sqrt_A2_A1")
    assert root.value == pytest.approx(1.0)
    footprint = _state_named(record, "PT-SG-BR1: footprint on the wall top")
    assert footprint.ok and footprint.is_detailing


def _state_named(record, name):
    return next(s for s in record.limit_states if s.name == name)


def test_deck_post_grades_the_same_development(results) -> None:
    """One arithmetic, two records: the column's own anchorage state is the joint's."""
    state = next(s for s in results["deck_post/PT-SG-BR1"].limit_states
                 if s.name == "dowel anchorage into the base")
    assert (state.demand, state.capacity) == pytest.approx((21.21, 24.0), abs=0.01)


def _mutated(tmp_path, old, new):
    from _helpers import copy_house

    from typehaus.source import load_plan

    house = copy_house(CATLIN, tmp_path / "house")
    source = house / "params" / "sunken_garden.py"
    text = source.read_text()
    assert old in text
    source.write_text(text.replace(old, new))
    loaded = load_plan(house)
    assert loaded.plan is not None
    return loaded.plan


_DOWEL = 'embedment=inch(24.0), joint_surface="roughened"'


def test_an_embedment_past_the_stem_is_refused(tmp_path) -> None:
    plan = _mutated(tmp_path, _DOWEL, 'embedment=inch(200.0), joint_surface="roughened"')
    state = _state(_results(plan)["column_support/W-SG-W1"], "PT-SG-BR1", "development")
    assert state.capacity == pytest.approx(109.4375 - 3.0, abs=0.01)
    assert "REFUSED" in state.citation


def test_no_roughening_is_graded_at_0_6(tmp_path) -> None:
    plan = _mutated(tmp_path, _DOWEL, "embedment=inch(24.0)")
    record = _results(plan)["column_support/W-SG-W1"]
    mu = next(q for q in record.inputs if q.name == "PT-SG-BR1.shear_friction_mu")
    assert mu.value == 0.6
    state = _state(record, "PT-SG-BR1", "shear")
    assert state.capacity == pytest.approx(0.6 * 50_168, rel=0.003)


def test_no_embedment_is_incomplete_naming_the_field(tmp_path) -> None:
    plan = _mutated(tmp_path, _DOWEL, 'joint_surface="roughened"')
    record = _results(plan)["column_support/W-SG-W1"]
    assert record.status is Status.INCOMPLETE
    assert any("BarSpec.embedment" in m for m in record.missing)
