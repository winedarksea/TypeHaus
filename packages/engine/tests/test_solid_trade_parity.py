"""Solid-trade parity between the engine table and the three.js viewer.

Two tables name the same thing: ``SOLID_CATEGORY_TRADE`` in ``emit/trades.py`` and the mirror in
``ui/src/three/solidMaterials.ts``. The viewer's render path is deliberately not on the geometry
IR (→ ``WHOLE_HOUSE_GLB_PRIMARY``), so nothing but a test can hold the two in agreement — the
same arrangement ``test_palette_parity.py`` makes for the two colour tables, and it reads the
TypeScript as text for the same reason: the point is to fail in the suite that runs on every
engine change rather than only in the browser.

The bug behind the table: every ``ResolvedSolid`` was handed to the ``concrete`` trade whatever
its category, which filed the standalone ``Beam``/``Post`` solids away from the studs and rafters
they carry (while an authored *ridge* beam appeared under framing, because the resolver re-types
that one as a ``FramedMember``), and put all 791 routed pipe solids behind the Concrete toggle
instead of Plumbing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from typehaus.emit.trades import FALLBACK_TRADE, SOLID_CATEGORY_TRADE, TRADES, solid_trade
from typehaus.resolve import resolve
from typehaus.source import load_plan

REPO_ROOT = Path(__file__).resolve().parents[3]
CATLIN_DIR = REPO_ROOT / "houses" / "catlin"
SOLID_MATERIALS_TS = REPO_ROOT / "ui" / "src" / "three" / "solidMaterials.ts"

# Categories that ride the fallback on purpose, so "unclassified" stays a meaningful signal.
# Keep the reasons in emit/trades.py, next to the table.
DELIBERATELY_UNCLASSIFIED = {"sump", "railing", "connector"}


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    assert not [f for f in findings if f.severity.value == "error"]
    return model


@pytest.fixture(scope="module")
def catlin_solid_categories(catlin_model) -> set[str]:
    return {solid.category.lower() for solid in catlin_model.solids}


def _viewer_trades() -> dict[str, str]:
    """The ``SOLID_CATEGORY_TRADE`` literal in solidMaterials.ts, read out of the source."""
    source = SOLID_MATERIALS_TS.read_text()
    block = re.search(
        r"export const SOLID_CATEGORY_TRADE: Record<string, Trade> = \{(.*?)\n\};",
        source, re.S)
    assert block is not None, "SOLID_CATEGORY_TRADE literal not found in solidMaterials.ts"
    return dict(re.findall(r'^\s{2}([A-Za-z_][A-Za-z0-9_]*):\s*"([a-z]+)"',
                           block.group(1), re.M))


def test_every_trade_in_the_table_is_one_the_ui_honours() -> None:
    unknown = sorted(set(SOLID_CATEGORY_TRADE.values()) - TRADES)
    assert not unknown, f"SOLID_CATEGORY_TRADE names trades the UI has no group for: {unknown}"
    assert FALLBACK_TRADE in TRADES


def test_the_two_tables_agree(catlin_solid_categories) -> None:
    viewer = _viewer_trades()
    disagreements = sorted(
        (category, engine, viewer[category])
        for category, engine in SOLID_CATEGORY_TRADE.items()
        if category in viewer and viewer[category] != engine)
    assert not disagreements, (
        "engine/viewer trade disagreement (category, engine, viewer): "
        f"{disagreements}")
    missing = sorted(set(SOLID_CATEGORY_TRADE) - set(viewer))
    assert not missing, f"solidMaterials.ts SOLID_CATEGORY_TRADE has no entry for: {missing}"
    extra = sorted(set(viewer) - set(SOLID_CATEGORY_TRADE))
    assert not extra, f"viewer table keys with no engine counterpart: {extra}"


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


def test_solid_trade_falls_back_rather_than_raising() -> None:
    assert solid_trade("no_such_category") == FALLBACK_TRADE
    assert solid_trade(None) == FALLBACK_TRADE
    assert solid_trade("") == FALLBACK_TRADE
    assert solid_trade("  BEAM  ") == "framing"
