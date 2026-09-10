"""Every plumbing symbol has a fixture-unit row, or is exempt on the record.

The defect this closes: ``plan_symbol`` is the join key for the DFU and WSFU tables, so
naming a NEW symbol on a type — ``"shower-neo-angle"``, when the attic guest shower stopped
being a square pan — silently dropped that fixture out of both tables. Nothing raised: the
run serving it simply reported "carries no fixture-unit table row" as an UNKNOWN, and the
permit gate (which blocks on UNKNOWN) went red one storey away from the edit.

A symbol may legitimately be missing from one table — a hose bibb has no drain, a floor
drain has no supply — so the exemptions are listed here by name rather than inferred. That
makes "not in the table" a reviewable statement instead of an omission.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols import SYMBOL_NAMES
from typehaus.model.placeable_symbols.plumbing import PLUMBING_SYMBOLS
from typehaus.takeoff.plumbing_calc import DFU_BY_SYMBOL, WSFU_BY_SYMBOL

# A hose bibb discharges to grade, so it is a demand with no drainage fixture unit.
_NO_DRAIN = {"hydrant"}
# A floor drain is the opening itself — it receives, it is never supplied.
_NO_SUPPLY = {"floor-drain"}


def test_every_plumbing_symbol_carries_a_drainage_fixture_unit() -> None:
    missing = sorted(set(PLUMBING_SYMBOLS) - set(DFU_BY_SYMBOL) - _NO_DRAIN)
    assert not missing, f"no MN Table 702.1 row for {missing}"


def test_every_plumbing_symbol_carries_a_water_supply_fixture_unit() -> None:
    missing = sorted(set(PLUMBING_SYMBOLS) - set(WSFU_BY_SYMBOL) - _NO_SUPPLY)
    assert not missing, f"no MN Table 610.3 row for {missing}"


def test_the_tables_name_no_symbol_that_is_not_in_the_registry() -> None:
    """The other direction: a row for a symbol nobody draws is a typo, not a spare.

    Checked against the WHOLE vocabulary, not just the plumbing family: a clothes washer and
    a dishwasher are appliance glyphs that nonetheless discharge, and they carry DFU rows."""
    for table, name in ((DFU_BY_SYMBOL, "702.1"), (WSFU_BY_SYMBOL, "610.3")):
        strays = sorted(set(table) - SYMBOL_NAMES)
        assert not strays, f"Table {name} rows for unknown symbols {strays}"


def test_a_neo_angle_pan_is_valued_exactly_as_a_shower() -> None:
    """The cut corner is a plan outline, not a drainage or demand fact."""
    assert DFU_BY_SYMBOL["shower-neo-angle"] == DFU_BY_SYMBOL["shower"]
    assert WSFU_BY_SYMBOL["shower-neo-angle"] == WSFU_BY_SYMBOL["shower"]
