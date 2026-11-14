"""The autorouter scorecard against its checked-in baseline (``haus route --scorecard``).

Opt-in (``--autorouter``): it runs every scorecard search on catlin and grades each with
``--evaluate``, one forked worker per row (~7 min on 4; ``HAUS_SCORECARD_JOBS`` sets it).
Re-bless with ``--autorouter --bless`` and say in the commit which numbers moved and why.
"""

from __future__ import annotations

import json
import pathlib

import pytest
from _helpers import CATLIN

_BASELINE = pathlib.Path(__file__).resolve().parent / "data" / "route_scorecard.json"


@pytest.mark.autorouter
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


@pytest.mark.parametrize("refused, coverage, bad", [(None, [], False), ("no resolve", [], True),
                                                    (None, ["gap"], True)])
def test_refused_evaluation_is_a_regression(monkeypatch, refused, coverage, bad) -> None:
    from types import SimpleNamespace as NS

    from typehaus.cli import route_scorecard as sc

    monkeypatch.setattr(sc, "bores", lambda *_: {})
    monkeypatch.setattr(sc, "_exterior_ft", lambda *_: 0.0)
    proposal = NS(system="drain", points=[], tag="t", fittings=lambda: [],
                  developed_ft=lambda: 1.0, cleanouts=())
    monkeypatch.setattr("typehaus.resolve.mep_fitting_direction.forbidden_turns",
                        lambda *a: [])
    monkeypatch.setattr("typehaus.routing.rack.rack_shared", lambda *a, **k: 0)
    found = NS(proposals=[proposal], refused=0, relaid=0, relay_refused=0, lifts=0,
               ft_tag=None)
    row = sc._metrics(None, found, 0.0, [], NS(rack_spacing_in=48), refused=refused,
                      coverage=coverage)
    assert (row["eval_refused"], row["eval_coverage_gaps"]) == (int(bool(refused)),
                                                                len(coverage))
    baseline = {"targets": {"r": {"proposals": 1, "developed_ft": 1.0}}}  # old golden: no keys
    assert bool(sc.regressions(baseline, {"targets": {"r": row}})) is bad
    # A refusal is a regression even when the baseline recorded one.
    assert refused is None or sc.regressions({"targets": {"r": row}}, {"targets": {"r": row}})
