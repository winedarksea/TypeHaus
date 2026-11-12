"""``mep.condensate_overflow`` — IMC 2018 307.2.3, the four overflow guards.

Cases re-author catlin's real air handler in a stand-in plan view, over the real resolved
model, so the refs resolve against real runs and units.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.checks.mep.condensate_overflow import condensate_overflow
from typehaus.checks.registry import CheckContext
from typehaus.findings import Result
from typehaus.model.enums import EquipmentKind

_AH = "EQ-S-HP1-AH"


def _grade(model, **update):
    """The finding for the air handler with ``update`` applied (``kind`` re-kinds EQ-B-WH)."""
    target = "EQ-B-WH" if "kind" in update else _AH
    elements = [e.model_copy(update=update) if e.tag == target else e
                for e in model.plan.all_elements()]
    plan = SimpleNamespace(all_elements=lambda: elements)
    ctx = CheckContext(plan=plan, model=model, preferences=None, profile=None)
    return {f.element_tags[0]: f for f in condensate_overflow(ctx)}[target]


def test_catlin_air_handler_is_unknown_until_authored(catlin_model_ro) -> None:
    assert _grade(catlin_model_ro).result is Result.UNKNOWN


@pytest.mark.parametrize(("update", "result", "words"), [
    ({"float_switch_ref": "EQ-M-HP1-OD"}, Result.PASS, "item 4"),
    ({"secondary_drain_pan": True, "float_switch_ref": _AH}, Result.PASS, "item 3"),
    ({"secondary_drain_pan": True, "overflow_drain_ref": "PR-M-COND-HP3"}, Result.PASS,
     "item 1"),
    ({"overflow_drain_ref": "PR-M-COND-HP3"}, Result.PASS, "item 2"),
    ({"overflow_drain_ref": "PR-A-COND-HP1", "pan_drain_ref": "PR-A-COND-HP1"}, Result.FAIL,
     "primary"),
    ({"float_switch_ref": "EQ-NOPE"}, Result.FAIL, "no equipment"),
    ({"float_switch_ref": "EQ-B-WH"}, Result.FAIL, "neither"),
    ({"overflow_drain_ref": "PR-NOPE"}, Result.FAIL, "no pipe run"),
    ({"secondary_drain_pan": True}, Result.FAIL, "item 3 needs"),
    # A floor-standing unit on the bare basement slab: nothing below to damage.
    ({"kind": EquipmentKind.AIR_HANDLER}, Result.NOT_APPLICABLE, "SL-B-FLOOR"),
])
def test_each_option_and_each_dangling_ref(catlin_model_ro, update, result, words) -> None:
    finding = _grade(catlin_model_ro, **update)
    assert finding.result is result and words in finding.message, finding.message
