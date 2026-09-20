"""``FixtureType.basin`` and ``DoorType.function`` — two declared facts a name used to guess.

``basin`` decides who E3901.6 / NEC 210.52(D) is about; the plan symbol is only the fallback
for a type that states nothing, and a symbol in neither vocabulary is an UNKNOWN naming the
type rather than a silent exclusion. ``function`` is what a door's hardware is bought as —
stated where the product decides it, left None where only a house can.
"""

from __future__ import annotations

import pytest

from typehaus.checks.mep.electrical_receptacles import (
    _NOT_BASIN_SYMBOLS,
    _is_basin,
    bathroom_basin_receptacle,
)
from typehaus.findings import Result
from typehaus.library.doors import ALL_DOOR_TYPES
from typehaus.library.placeables.fixtures import (
    LAVATORY,
    SHOWER,
    STARTER_FIXTURE_TYPES,
    TOILET,
    VANITY,
)
from typehaus.model.types import DoorType, FixtureType
from typehaus.quantities import ft


def _type(**kwargs) -> FixtureType:
    return FixtureType(tag="FX-T", name="t", footprint=(ft(1), ft(1)), height=ft(1), **kwargs)


def test_basin_defaults_to_none_so_no_existing_house_changes_shape():
    assert _type().basin is None
    assert DoorType(tag="DT-T", width=ft(3), height=ft(6, 8)).function is None


def test_the_stated_field_outranks_the_plan_symbol_in_both_directions():
    assert _is_basin(_type(plan_symbol="toilet", basin=True)) is True
    assert _is_basin(_type(plan_symbol="vanity", basin=False)) is False


def test_the_symbol_is_the_fallback_and_an_unlisted_one_answers_neither_way():
    assert _is_basin(_type(plan_symbol="lavatory")) is True
    assert _is_basin(_type(plan_symbol="shower")) is False
    # A symbol nobody listed — the case that used to leave the rule's scope in silence.
    assert _is_basin(_type(plan_symbol="trough-basin")) is None
    assert _is_basin(_type()) is None


def test_the_reviewed_catalog_states_basin_on_every_plumbing_fixture():
    unstated = [t.tag for t in STARTER_FIXTURE_TYPES if t.basin is None]
    assert unstated == []
    assert (LAVATORY.basin, VANITY.basin) == (True, True)
    assert (TOILET.basin, SHOWER.basin) == (False, False)


def test_the_two_symbol_vocabularies_do_not_overlap():
    assert not ({"lavatory", "vanity"} & _NOT_BASIN_SYMBOLS)


def test_a_derived_type_inherits_the_flag_rather_than_its_new_symbol():
    """``model_copy`` is how catlin builds its products, and a new symbol must not re-decide."""
    neo = SHOWER.model_copy(update={"tag": "FX-X", "plan_symbol": "shower-neo-angle"})
    assert _is_basin(neo) is False


def test_catlin_grades_every_basin_and_leaves_nothing_unclassified(catlin_ctx):
    findings = bathroom_basin_receptacle(catlin_ctx)
    assert findings
    assert all(f.result is Result.PASS for f in findings), [
        f.message for f in findings if f.result is not Result.PASS]
    # The UNKNOWN branch fires on a type that states nothing; catlin states them all.
    assert not [f for f in findings if "is in neither vocabulary" in f.message]


@pytest.mark.parametrize(("tag", "function"), [
    ("DT-EXT-SWING36", "entry"),
    ("DT-EXT-FRENCH60", "entry"),
    ("DT-EXT-OVERHEAD192", "overhead"),
    ("DT-INT-BIFOLD56", "closet"),
    ("DT-INT-BYPASS48", "closet"),
    ("DT-INT-BYPASS60", "closet"),
])
def test_the_catalog_states_function_where_the_product_decides_it(tag, function):
    by_tag = {t.tag: t for t in ALL_DOOR_TYPES}
    assert by_tag[tag].function == function


def test_a_commodity_interior_swing_states_nothing_because_it_cannot():
    """One leaf, two locksets: passage at a study, privacy at a bath. The house decides."""
    by_tag = {t.tag: t for t in ALL_DOOR_TYPES}
    assert by_tag["DT-INT-SWING32"].function is None
    assert by_tag["DT-POCKET-INT-36"].function is None


def test_function_is_a_closed_vocabulary():
    with pytest.raises(ValueError):
        DoorType(tag="DT-T", width=ft(3), height=ft(6, 8), function="lockset")
