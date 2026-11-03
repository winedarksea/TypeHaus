"""The autorouter scorecard against its checked-in baseline (``haus route --scorecard``).

Opt-in (``--autorouter``): it runs every scorecard search on catlin and grades each with
``--evaluate`` (~5 min). Re-bless with ``--autorouter --bless`` and say in the commit which
numbers moved and why.
"""

from __future__ import annotations

import json
import pathlib

import pytest
from _helpers import CATLIN

pytestmark = pytest.mark.autorouter

_BASELINE = pathlib.Path(__file__).resolve().parent / "data" / "route_scorecard.json"


def test_no_scorecard_metric_regresses(request, catlin_model_ro) -> None:
    from typehaus.checks import load_preferences
    from typehaus.cli.route_scorecard import markdown, regressions, run_scorecard
    from typehaus.routing.cost import cost_from_preferences

    cost = cost_from_preferences(load_preferences(CATLIN).mep.routing)
    card = run_scorecard(CATLIN, catlin_model_ro, cost)
    if request.config.getoption("--bless"):
        _BASELINE.write_text(json.dumps(card, indent=1, sort_keys=True) + "\n")
        pytest.skip("blessed:\n" + markdown(card))
    baseline = json.loads(_BASELINE.read_text())
    worse = regressions(baseline, card)
    assert not worse, "\n".join(worse) + "\n\n" + markdown(card)
