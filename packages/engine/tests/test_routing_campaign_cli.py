"""The campaign end to end through ``haus route --house``: a small real supply run.

Opt-in (``--autorouter``): it runs a real search, so it only earns its minute when
``typehaus/routing/`` changes. The rest of ``test_routing_campaign.py`` pins the campaign's
policy without a search and always runs.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.autorouter

# The PR-A tees, plus one riser-gap refusal so the refusal wording stays graded.
_REFUSED = "PR-M-CW-PLANT-STUB"


def test_the_supply_slot_in_trade_order_is_no_longer_decorative(request) -> None:
    """`TRADE_ORDER` has always named supply fourth and a supply target has never been
    layable: `_pipe_run_endpoints` sent every one of them to `_vent_siblings`, which asks
    an endpoint question about a tee that sits on a segment.

    The main storey's PR-A tees run as one campaign, every other main supply run locked in
    place as an obstacle (~1 min; the whole storey is ~7). Driven through the CLI rather
    than `run_campaign`, because the campaign runs no search of its own — what was broken
    was the ENDPOINTS, which is the parameter."""
    import pathlib

    from typer.testing import CliRunner

    from typehaus.cli.app import app
    from typehaus.routing.campaign import order_targets

    model = request.getfixturevalue("catlin_model_ro")
    scope = order_targets(model, trades=["supply"], storey="main")
    tees = [t.tag for t in scope if t.tag.startswith("PR-A-")]
    locked = [t.tag for t in scope if t.tag not in tees and t.tag != _REFUSED]
    assert tees and _REFUSED in {t.tag for t in scope}

    catlin = pathlib.Path(__file__).resolve().parents[3] / "houses" / "catlin"
    result = CliRunner().invoke(app, [
        "route", str(catlin), "--house", "--trades", "supply", "--storey", "main",
        *(arg for tag in locked for arg in ("--locked", tag))])
    # Exit 1: the stub is honestly parentless, a fact about the model, not a failure.
    assert result.exit_code in (0, 1), result.output
    printed = " ".join(result.output.split())
    total = len(tees) + 1
    assert f"of {total} targets laid" in printed, printed
    laid = int(printed.split(f" of {total} targets laid")[0].split()[-1])
    assert laid >= len(tees), printed
    # And the refusals that remain say which cause applies, not a sentence about a chase.
    assert f"refused {_REFUSED}" in printed and "is not modelled" in printed
    assert "chase" not in printed
