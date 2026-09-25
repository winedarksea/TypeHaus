"""Every LayerFunction has one metadata row, and the consumers read it."""

from __future__ import annotations

from typehaus.model.enums import LayerFunction
from typehaus.model.layer_functions import LAYER_FUNCTIONS


def test_every_layer_function_has_a_row() -> None:
    assert set(LAYER_FUNCTIONS) == set(LayerFunction)


def test_consumers_cover_every_member() -> None:
    from typehaus.emit.draw.palette import aia_layer
    from typehaus.emit.finishes import layer_visibility_group
    from typehaus.emit.trade_rules import LAYER_FUNCTION_TRADE
    from typehaus.takeoff.envelope import _BILLABLE

    for function, row in LAYER_FUNCTIONS.items():
        assert LAYER_FUNCTION_TRADE[function.value] == row.trade
        assert (function in _BILLABLE) is row.billable
        assert aia_layer(function.value) == row.aia
        assert layer_visibility_group(function.value) == row.visibility_group


def test_hardware_fastened_set_matches_the_table() -> None:
    """``hardware`` is a leaf and cannot import ``model``, so its copy is pinned here."""
    from typehaus.hardware.config import ExteriorInsulationFastenerRules
    from typehaus.model.layer_functions import values_where

    rules = ExteriorInsulationFastenerRules()
    assert rules.fastened_layer_functions == values_where(fastened=True)
    assert rules.structure_layer_functions == {LayerFunction.STRUCTURE.value}
    assert rules.insulation_layer_functions == {LayerFunction.INSULATION.value}
