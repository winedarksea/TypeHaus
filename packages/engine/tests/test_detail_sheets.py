"""Authored detail sheets — A-401+ (→ Permit-ready plan set Phase 6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw import build_sheet_index
from typehaus.emit.draw.scene import Hatch, Text
from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


def test_catlin_emits_authored_then_derived_detail_sheets(catlin_model):
    sheets = build_sheet_index(catlin_model)
    detail_numbers = [s.number for s in sheets if s.number.startswith("A-4")]
    # The four authored details keep A-401..A-404, in order, ahead of derived details.
    assert detail_numbers[:4] == ["A-401", "A-402", "A-403", "A-404"]
    titles = {s.number: s.title for s in sheets}
    assert titles["A-401"] == "Foundation detail"
    assert titles["A-402"] == "Deck bearing detail"
    # Derived transition details continue the A-4xx block (catlin binds many conditions).
    assert len(detail_numbers) > 4
    # numbering is contiguous
    nums = [int(n.split("-")[1]) for n in detail_numbers]
    assert nums == list(range(401, 401 + len(nums)))


def test_deckbrg_scene_contains_deck_hatch_spanning_its_thickness(catlin_model):
    sheets = {s.number: s for s in build_sheet_index(catlin_model)}
    scene = sheets["A-402"].scene(catlin_model)
    slab_hatches = [n for n in scene.nodes if isinstance(n, Hatch) and n.pattern == "concrete"]
    assert slab_hatches
    # the 9" deck spans z in [-0.2286m, 0] — some hatch boundary must cover that band
    m_to_in = 39.37007874015748
    covers_deck = any(
        min(p[1] for p in hatch.boundary) <= -0.2286 * m_to_in + 1e-3
        and max(p[1] for p in hatch.boundary) >= 0.0 - 1e-3
        for hatch in slab_hatches
    )
    assert covers_deck


def test_detail_sheets_snapshot_deterministic(catlin_model):
    sheets = {s.number: s for s in build_sheet_index(catlin_model)}
    a = sheets["A-401"].scene(catlin_model)
    b = sheets["A-401"].scene(catlin_model)
    assert a.to_json() == b.to_json()


def test_starter_emits_one_detail_sheet(starter_dir: Path):
    result = load_plan(starter_dir)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    sheets = build_sheet_index(model)
    detail_numbers = [s.number for s in sheets if s.number.startswith("A-40")]
    assert detail_numbers == ["A-401"]


def test_ridge_detail_scene_is_nonempty(catlin_model):
    sheets = {s.number: s for s in build_sheet_index(catlin_model)}
    scene = sheets["A-404"].scene(catlin_model)
    assert scene.nodes
