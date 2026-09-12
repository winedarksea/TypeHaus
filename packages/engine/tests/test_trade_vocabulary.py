"""The trade vocabulary is one table, and every consumer keys on it.

``emit/trades.py`` names the trades and their groups; ``emit/trade_rules.py`` classifies
materials, layers, solids and members onto them; ``takeoff/cost_codes.py``, the schedule
package and the MN inspection specs key on the names. Each of these used to carry a private
copy of the 13-name list. This file pins that they cannot drift again, and that on the
reference house the fact rules actually fire — no envelope, wall-structure, placeable or
edge-trim row may reach the BOM by section default alone.
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from _helpers import CATLIN

from typehaus.emit import trade_rules
from typehaus.emit.trades import (
    CONSTRUCTION_SEQUENCE,
    TRADE_GROUP,
    TRADE_GROUPS,
    TRADE_LABELS,
    TRADES,
)
from typehaus.model.enums import LayerFunction


def test_every_trade_is_in_exactly_one_group_and_every_group_is_used() -> None:
    listed = [t for _g, _l, ts in TRADE_GROUPS for t in ts]
    assert sorted(listed) == sorted(TRADES)
    assert len(listed) == len(set(listed))
    assert all(ts for _g, _l, ts in TRADE_GROUPS)
    assert set(TRADE_GROUP.values()) == {g for g, _l, _ts in TRADE_GROUPS}
    assert set(TRADE_LABELS) == TRADES
    assert list(dict.fromkeys(CONSTRUCTION_SEQUENCE)) == list(CONSTRUCTION_SEQUENCE)


def test_every_canvas_domain_and_layer_function_is_handled() -> None:
    from typehaus.model.canvas import _TYPE_COLLECTIONS

    domains = {domain for _c, domain, _k, _s in _TYPE_COLLECTIONS}
    assert domains <= set(trade_rules.CANVAS_DOMAIN_TRADE)
    for function in LayerFunction:
        assert function.value in trade_rules.LAYER_FUNCTION_TRADE
        assert trade_rules.layer_trade(function.value) in TRADES


def test_cost_codes_and_the_vocabulary_agree() -> None:
    from typehaus.takeoff import cost_codes as cc

    named = {code.trade for code in cc.SECTION_CODES.values()}
    named |= {code.trade for _s, _p, code in cc.KEY_PATTERNS}
    named |= {code.trade for code in cc._SOLID_TRADE_CODES.values()}
    named |= {code.trade for code in cc._SECTION_TRADE_CODES.values()}
    assert named <= TRADES
    assert set(cc.TRADE_CODES) == TRADES
    assert named | set(cc.TRADE_CODES) >= TRADES


def test_schedule_consumers_key_on_real_trades() -> None:
    from typehaus.checks.code.mn_residential.inspections import MN_INSPECTIONS
    from typehaus.schedule.handoff import _BY_TRADE
    from typehaus.schedule.milestones import MILESTONE_OF_TRADE
    from typehaus.schedule.propose import DEFAULT_CONSTRAINTS, FAMILY_ORDER
    from typehaus.takeoff.task_state import LICENSED_TRADES

    assert set(DEFAULT_CONSTRAINTS) == TRADES
    assert set(FAMILY_ORDER) == TRADES
    assert set(_BY_TRADE) <= TRADES
    assert set(MILESTONE_OF_TRADE) == TRADES
    assert set(LICENSED_TRADES) <= TRADES
    assert {t for spec in MN_INSPECTIONS for t in spec.gates} <= TRADES


@pytest.mark.parametrize("section", ["envelope_layers", "wall_structure", "placeables",
                                     "edge_trim"])
def test_no_catlin_row_in_a_fact_section_files_by_default_alone(catlin_model_ro, section) -> None:
    """The rule that classifies these sections must answer for every row the reference
    house produces; a row falling to the section default is a fact nobody read."""
    from typehaus.cli.prices import ESTIMATE_PLANS
    from typehaus.takeoff.bom import bill_of_materials
    from typehaus.takeoff.cost_codes import _fact_code

    bom = bill_of_materials(catlin_model_ro)
    bom_key = next(plan[1] for plan in ESTIMATE_PLANS if plan[0] == section)
    rows = bom[bom_key]
    assert rows
    silent = [row for row in rows if _fact_code(section, row) is None]
    assert not silent, [(section, row) for row in silent[:5]]


def test_catlin_site_files_validate_clean() -> None:
    result = subprocess.run([sys.executable, "-m", "typehaus.cli.app", "site", "validate",
                             str(CATLIN)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
