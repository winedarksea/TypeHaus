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

#: §11a-§11d as re-worked through §13c-§19, and again in §25 (2026-11-23): beam statics and the
#: planter (off here: this context carries no preferences), the wind of §24, the floor-empty
#: guard pair, the flexible base's delta, and the general-equation development of §21.
#: (demand, capacity) of the worst §2.3.1 case of each state.
_ORACLE = {
    "PT-SG-BR1": {"bearing": (13_127.7, 38_943), "tension": (9_162, 16_740),
                  "shear": (761.6, 45_635), "development": (12.73, 48.0)},
    "PT-SG-BF1": {"bearing": (12_768.7, 38_697), "tension": (9_212.5, 16_740),
                  "shear": (761.6, 45_580), "development": (12.73, 48.0)},
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
        assert record.governing.name.endswith("stem as a cantilever under E-W wind and the "
                                              "retained soil")
        assert any("base_rotation/<column>" in note for note in record.notes)
        # B-05: nothing is handed to "the engineer of record" any more.
        assert not any("engineer of record" in note for note in record.notes)


def test_a_flush_round_takes_no_confinement_credit(results) -> None:
    """§11a: the 12" round on a 12" stem — √(A2/A1) is 1.0, read off the wall, not assumed."""
    record = results["column_support/W-SG-W1"]
    root = next(q for q in record.inputs if q.name == "PT-SG-BR1.sqrt_A2_A1")
    assert root.value == pytest.approx(1.0)
    footprint = _state_named(record, "PT-SG-BR1: footprint on the wall top")
    assert footprint.ok and footprint.is_detailing


def _state_named(record, name):
    return next(s for s in record.limit_states if s.name == name)


def test_the_development_is_graded_once_here_and_deck_post_points_to_it(results) -> None:
    """B-08: one limit state, one row. `column_support` carries the dowel development (the
    general equation, 12.73" of 48"); `deck_post` no longer prints it for a wall base."""
    state = _state_named(results["column_support/W-SG-W1"],
                         "PT-SG-BR1: dowel development into the stem")
    assert (state.demand, state.capacity) == pytest.approx((12.73, 48.0), abs=0.01)
    assert "§25.4.2.4" in state.citation and "26.0" not in state.citation
    record = results["deck_post/PT-SG-BR1"]
    assert not any(s.name == "dowel anchorage into the base" for s in record.limit_states)
    assert any("graded once" in n for n in record.notes)


@pytest.mark.parametrize("column,stem,capacity,footing", [
    ("PT-SG-BR1", 10_541.5, 32_802.0, 46.11), ("PT-SG-BF1", 10_427.5, 45_820.5, 23.69)])
def test_the_stem_and_the_footing_are_rows_with_the_spread_stopped_at_the_pour(
        results, column, stem, capacity, footing) -> None:
    """§22 / §27 (B-05, D-R3): plain concrete below the 48" dowels over a 45 deg spread, the
    moment AND its shear's lever (M_u + V_u x, x = 48") and the spread stopped at the pour's
    free end: the rear column stands 23.3" from it (spread 77", phi M_n 32,802 lb-ft), the front
    one is unclipped (108", 45,820)."""
    record = results["column_support/W-SG-W1"]
    below = _state_named(record, f"{column}: stem flexure below the dowels")
    assert below.demand == pytest.approx(stem, rel=0.003)
    assert below.capacity == pytest.approx(capacity, rel=0.002)
    assert "M_u + V_u x" in below.citation
    under = _state_named(record, f"{column}: footing bearing under the column point")
    assert under.demand == pytest.approx(footing, rel=0.01) and under.capacity == 2_000.0
    assert not any("strut" in s.name for s in record.limit_states)   # no prop to receive


def test_each_stem_is_a_cantilever_under_e_w_wind_plus_the_retained_soil(results) -> None:
    """§27 (verifier 2026-11-23): all four columns push both stems the same way, so the
    porch cannot prop one against the other; the SOIL pushes inward on both, so the porch DOES
    prop it. Per foot: the columns' M + V H over the union of their spreads (18.9') = 1,495, plus
    the PROPPED soil 1.6 x 60 psf/ft (the court's at-rest basis) x 6.29'^3 / 15 = 1,590, against
    #6 @ 38" on the earth face, d 8.625": phi M_n = 0.9 x 0.1389 x 60,000 x (8.625 - 0.0817) / 12
    = 5,340; d/c 0.58."""
    for wall in ("W-SG-W1", "W-SG-E1"):
        record = results[f"column_support/{wall}"]
        state = _state_named(record, f"{wall}: stem as a cantilever under E-W wind and the "
                                     f"retained soil")
        assert state.capacity == pytest.approx(5_340.0, rel=0.002)
        assert state.demand == pytest.approx(3_085.0, rel=0.01)
        assert "cannot prop one against the other" in state.citation
        assert "PROPPED retained soil 1.6 x 60" in state.citation
        notes = " ".join(record.notes)
        assert "WHAT CARRIES THE E-W LATERAL" in notes
        assert "OWNER-ACCEPTED" in notes


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


_DOWEL = 'embedment=inch(48.0), projection=inch(30.0),\n                joint_surface="roughened"'


def test_an_embedment_past_the_stem_is_refused(tmp_path) -> None:
    plan = _mutated(tmp_path, _DOWEL, _DOWEL.replace("48.0", "200.0"))
    state = _state(_results(plan)["column_support/W-SG-W1"], "PT-SG-BR1", "development")
    assert state.capacity == pytest.approx(109.4375 - 3.0, abs=0.01)
    assert "REFUSED" in state.citation


def test_no_roughening_is_graded_at_0_6(tmp_path) -> None:
    plan = _mutated(tmp_path, _DOWEL, "embedment=inch(48.0), projection=inch(30.0)")
    record = _results(plan)["column_support/W-SG-W1"]
    mu = next(q for q in record.inputs if q.name == "PT-SG-BR1.shear_friction_mu")
    assert mu.value == 0.6
    state = _state(record, "PT-SG-BR1", "shear")
    # mu 0.6 on the same (Avf fy - tension) the roughened 1.0 reads: 38,549 x 0.6.
    assert state.capacity == pytest.approx(0.6 * 45_635, rel=0.003)


def test_no_embedment_is_incomplete_naming_the_field(tmp_path) -> None:
    plan = _mutated(tmp_path, _DOWEL, 'projection=inch(30.0), joint_surface="roughened"')
    record = _results(plan)["column_support/W-SG-W1"]
    assert record.status is Status.INCOMPLETE
    assert any("BarSpec.embedment" in m for m in record.missing)
