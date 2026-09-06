"""Authored detail sheets — A-501+ (→ Permit-ready plan set Phase 6).

They were A-401+ until the set took NCS numbering. NCS sheet-type 4 is LARGE-SCALE
VIEWS — an enlarged plan at 1/2" = 1'-0" — and a junction cut at 1-1/2" is a DETAIL,
type 5. See ``emit/draw/sheets.build_sheet_index``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw import build_sheet_index
from typehaus.emit.draw.scene import Hatch, Text
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR



def test_catlin_emits_authored_then_derived_detail_sheets(catlin_model):
    sheets = build_sheet_index(catlin_model)
    detail_numbers = [s.number for s in sheets if s.number.startswith("A-5")]
    # The four authored details keep A-501..A-504, in order, ahead of derived details.
    assert detail_numbers[:4] == ["A-501", "A-502", "A-503", "A-504"]
    titles = {s.number: s.title for s in sheets}
    assert titles["A-501"] == "Foundation detail"
    assert titles["A-502"] == "Deck bearing detail"
    # Derived transition details continue the A-5xx block (catlin binds many conditions).
    assert len(detail_numbers) > 4
    # numbering is contiguous
    nums = [int(n.split("-")[1]) for n in detail_numbers]
    assert nums == list(range(501, 501 + len(nums)))


def test_deckbrg_scene_contains_deck_hatch_spanning_its_thickness(catlin_model):
    sheets = {s.number: s for s in build_sheet_index(catlin_model)}
    scene = sheets["A-502"].scene(catlin_model)
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
    a = sheets["A-501"].scene(catlin_model)
    b = sheets["A-501"].scene(catlin_model)
    assert a.to_json() == b.to_json()


def test_starter_emits_one_detail_sheet(starter_dir: Path):
    result = load_plan(starter_dir)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    sheets = build_sheet_index(model)
    detail_numbers = [s.number for s in sheets if s.number.startswith("A-50")]
    assert detail_numbers == ["A-501"]


def test_ridge_detail_scene_is_nonempty(catlin_model):
    sheets = {s.number: s for s in build_sheet_index(catlin_model)}
    scene = sheets["A-504"].scene(catlin_model)
    assert scene.nodes
