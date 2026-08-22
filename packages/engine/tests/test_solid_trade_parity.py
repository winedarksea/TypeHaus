"""Solid-trade parity between the engine table and the three.js viewer.

``SOLID_CATEGORY_TRADE`` in ``emit/trades.py`` used to be mirrored by a second, hand-authored
table inlined in ``ui/src/three/solidMaterials.ts``, linked only by a test reading the
TypeScript as text — the same arrangement ``test_palette_parity.py`` used for the colour
tables. That second table is gone: ``solidMaterials.ts`` now imports
``ui/src/generated/vocabulary.json`` (generated from ``SOLID_CATEGORY_TRADE`` by
``emit/vocabulary_manifest.py``) directly, so a TypeScript-only entry or a disagreement
between the two is no longer possible — there is nothing left on the TypeScript side to
disagree. What remains possible is the checked-in JSON going stale relative to
``SOLID_CATEGORY_TRADE``, which ``test_the_checked_in_manifest_matches_a_fresh_build`` below
catches.

The bug behind the table: every ``ResolvedSolid`` was handed to the ``concrete`` trade whatever
its category, which filed the standalone ``Beam``/``Post`` solids away from the studs and rafters
they carry (while an authored *ridge* beam appeared under framing, because the resolver re-types
that one as a ``FramedMember``), and put all 791 routed pipe solids behind the Concrete toggle
instead of Plumbing.
"""

from __future__ import annotations

import json

import pytest

from typehaus.emit.trades import (
    DRAINAGE_CATEGORIES, FALLBACK_TRADE, SOLID_CATEGORY_TRADE, TRADES, solid_trade)
from typehaus.emit.vocabulary_manifest import build_vocabulary_manifest
from _helpers import REPO_ROOT

VOCABULARY_JSON = REPO_ROOT / "ui" / "src" / "generated" / "vocabulary.json"

# Categories that ride the fallback on purpose, so "unclassified" stays a meaningful signal.
# Keep the reasons in emit/trades.py, next to the table.
#
# Empty as of 2026-08-15. ``railing`` and ``connector`` were the last two, and both were
# escapes rather than answers: a guard rode the concrete toggle and so did 49 PV rail clamps.
# Guards went to ``stairs`` (with the plan viewer's gate moving in the same change) and
# connection hardware split by kind — structural hardware to framing, snow rails and seam
# clamps to roof. What is left on the concrete fallback is pours and what is cast into them.
DELIBERATELY_UNCLASSIFIED: set[str] = set()


@pytest.fixture(scope="module")
def catlin_solid_categories(catlin_model) -> set[str]:
    return {solid.category.lower() for solid in catlin_model.solids}


def test_every_trade_in_the_table_is_one_the_ui_honours() -> None:
    unknown = sorted(set(SOLID_CATEGORY_TRADE.values()) - TRADES)
    assert not unknown, f"SOLID_CATEGORY_TRADE names trades the UI has no group for: {unknown}"
    assert FALLBACK_TRADE in TRADES


def test_the_checked_in_manifest_matches_a_fresh_build() -> None:
    """ui/src/generated/vocabulary.json is checked into git and is what
    ui/src/three/solidMaterials.ts actually imports for ``SOLID_CATEGORY_TRADE`` — there is
    no longer a second, independently authored TypeScript table to compare against.
    Regenerate the manifest in memory and diff it against the file on disk, to catch the
    checked-in copy going stale relative to ``SOLID_CATEGORY_TRADE``."""
    fresh = build_vocabulary_manifest()["solidTrades"]
    checked_in = json.loads(VOCABULARY_JSON.read_text())["solidTrades"]
    assert fresh == checked_in, (
        "ui/src/generated/vocabulary.json is stale — regenerate it "
        "(typehaus.emit.vocabulary_manifest.write_vocabulary_manifest) after this change to "
        "emit/trades.py")


def test_every_emitted_solid_category_is_classified(catlin_solid_categories) -> None:
    """A new solid category must be routed on purpose, not silently poured into concrete."""
    unclassified = sorted(catlin_solid_categories
                          - set(SOLID_CATEGORY_TRADE)
                          - DELIBERATELY_UNCLASSIFIED)
    assert not unclassified, (
        "these categories fall through to the concrete fallback; route them in "
        f"emit/trades.py or add them to DELIBERATELY_UNCLASSIFIED: {unclassified}")


def test_standalone_beams_and_posts_are_framing(catlin_model) -> None:
    """The regression this table was written for: BM-M-HALL and BM-S-HALL rendered under
    Concrete while RB-HOUSE — the same authored element kind — rendered under Framing."""
    by_tag = {solid.tag: solid for solid in catlin_model.solids}
    for tag in ("BM-M-HALL", "BM-S-HALL", "BM-SG-BKW"):
        assert tag in by_tag, f"fixture regression: the Catlin house lost {tag}"
        assert solid_trade(by_tag[tag].category) == "framing"
    posts = [s for s in catlin_model.solids if s.category == "column"]
    assert posts, "fixture regression: the Catlin house lost its posts"
    assert all(solid_trade(s.category) == "framing" for s in posts)


def test_routed_pipe_runs_are_plumbing(catlin_model) -> None:
    pipes = [s for s in catlin_model.solids if s.category.startswith("pipe_")]
    assert pipes, "fixture regression: the Catlin house lost its routed plumbing"
    assert {solid_trade(s.category) for s in pipes} == {"plumbing"}


def test_the_whole_stormwater_run_is_one_trade(catlin_model) -> None:
    """Drainage used to be split: the gutter under Roof, the leader with it (it carried the
    gutter category outright), and the sump pit on the concrete fallback. One run, one toggle."""
    for category in ("gutter", "downspout", "sump"):
        assert solid_trade(category) == "drainage"
    assert DRAINAGE_CATEGORIES == {"gutter", "downspout", "sump",
                                   "drain_tile", "french_drain", "drywell"}
    leaders = [s for s in catlin_model.solids if s.category == "downspout"]
    assert leaders, "fixture regression: the Catlin house lost its downspouts"


def test_solid_trade_falls_back_rather_than_raising() -> None:
    assert solid_trade("no_such_category") == FALLBACK_TRADE
    assert solid_trade(None) == FALLBACK_TRADE
    assert solid_trade("") == FALLBACK_TRADE
    assert solid_trade("  BEAM  ") == "framing"
