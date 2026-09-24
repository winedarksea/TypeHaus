"""The campaign end to end through ``haus route --house``: a full 30-target supply run.

Split from ``test_routing_campaign.py`` and marked slow: it is ~13% of the fast suite's CPU
on its own, and the rest of that module pins the campaign's policy without a search.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.slow


def test_the_supply_slot_in_trade_order_is_no_longer_decorative() -> None:
    """`TRADE_ORDER` has always named supply fourth and a supply target has never been
    layable: `_pipe_run_endpoints` sent every one of them to `_vent_siblings`, which asks
    an endpoint question about a tee that sits on a segment. `haus route --house --trades
    supply` refused 16 of 20 targets; it now lays 23 of 30. The 30th is the plant room's
    watering stub (PR-M-CW-PLANT-STUB), refused like the cold-store stub: its feeding riser
    is not modelled.

    Driven through the CLI rather than `run_campaign`, because the campaign runs no search
    of its own — what was broken was the ENDPOINTS, which is the parameter."""
    import pathlib

    from typer.testing import CliRunner

    from typehaus.cli.app import app

    catlin = pathlib.Path(__file__).resolve().parents[3] / "houses" / "catlin"
    result = CliRunner().invoke(
        app, ["route", str(catlin), "--house", "--trades", "supply"])
    # Exit 1: seven runs are still honestly parentless, which is the campaign reporting a
    # fact about the model rather than failing.
    assert result.exit_code in (0, 1), result.output
    printed = " ".join(result.output.split())
    assert "of 30 targets laid" in printed
    laid = int(printed.split(" of 30 targets laid")[0].split()[-1])
    assert laid >= 20, printed
    # And the refusals that remain say which cause applies, not a sentence about a chase.
    assert "chase" not in printed
