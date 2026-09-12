"""Every geometry-IR part names a layer group the engine knows.

The viewer no longer toggles by layer group — it toggles by trade (2026-09-12, see
``test_trade_vocabulary.py``) — but ``GPart.layer_group`` is still stamped on every part of
the IR, and a part in a group nobody named is a band that fell through a rule.
"""

from __future__ import annotations

import pytest

from typehaus.emit.finishes import LAYER_VISIBILITY_GROUPS, layer_visibility_group
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import HOUSES


def test_an_unknown_function_buckets_to_other_on_both_sides() -> None:
    assert layer_visibility_group("no-such-function") == "other"
    assert layer_visibility_group("") == "other"
    assert layer_visibility_group(None) == "other"


@pytest.mark.parametrize("house", ["starter", "catlin"])
def test_every_emitted_layer_group_is_in_the_vocabulary(house: str) -> None:
    result = load_plan(HOUSES / house)
    assert result.plan is not None
    model, _findings = resolve(result.plan)
    assert model.geometry is not None
    groups = {part.layer_group for element in model.geometry.elements
              for part in element.parts if part.layer_group is not None}
    assert groups, "no part declared a layer group at all"
    assert groups <= set(LAYER_VISIBILITY_GROUPS), sorted(
        groups - set(LAYER_VISIBILITY_GROUPS))
