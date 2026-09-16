"""Authored detail sheets — A-501+ (→ Permit-ready plan set Phase 6).

They were A-401+ until the set took NCS numbering. NCS sheet-type 4 is LARGE-SCALE
VIEWS — an enlarged plan at 1/2" = 1'-0" — and a junction cut at 1-1/2" is a DETAIL,
type 5. See ``emit/draw/sheets.build_sheet_index``.
"""

from __future__ import annotations

import re
from pathlib import Path

from _helpers import CATLIN as CATLIN_DIR

from typehaus.checks import load_preferences
from typehaus.emit.draw import build_sheet_index
from typehaus.emit.draw.scene import Hatch
from typehaus.emit.draw.schedules.architectural import SYMBOLS
from typehaus.resolve import resolve
from typehaus.source import load_plan


def test_catlin_emits_authored_then_derived_detail_sheets(catlin_sheet_index):
    sheets = catlin_sheet_index()
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


def test_deckbrg_scene_contains_deck_hatch_spanning_its_thickness(catlin_model_ro,
                                                                  catlin_sheet_index):
    sheets = {s.number: s for s in catlin_sheet_index()}
    scene = sheets["A-502"].scene(catlin_model_ro)
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


def test_detail_sheets_snapshot_deterministic(catlin_model_ro, catlin_sheet_index):
    sheets = {s.number: s for s in catlin_sheet_index()}
    a = sheets["A-501"].scene(catlin_model_ro)
    b = sheets["A-501"].scene(catlin_model_ro)
    assert a.to_json() == b.to_json()


def test_starter_emits_one_detail_sheet(starter_dir: Path):
    result = load_plan(starter_dir)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    sheets = build_sheet_index(model)
    detail_numbers = [s.number for s in sheets if s.number.startswith("A-50")]
    assert detail_numbers == ["A-501"]


def test_ridge_detail_scene_is_nonempty(catlin_model_ro, catlin_sheet_index):
    sheets = {s.number: s for s in catlin_sheet_index()}
    scene = sheets["A-504"].scene(catlin_model_ro)
    assert scene.nodes


def test_catlin_omits_low_value_details_only_from_its_permit_set(catlin_model_ro,
                                                                 catlin_model_report):
    preferences = load_preferences(CATLIN_DIR)
    full = build_sheet_index(catlin_model_ro, preferences, sets="full",
                             report=catlin_model_report)
    permit = build_sheet_index(catlin_model_ro, preferences, sets="permit",
                               report=catlin_model_report)
    full_by_number = {sheet.number: sheet.title for sheet in full}
    permit_by_number = {sheet.number: sheet.title for sheet in permit}

    assert full_by_number["A-502"] == "Deck bearing detail"
    assert full_by_number["A-506"] == "Hall bath shower section"
    assert {"A-502", "A-506"}.isdisjoint(permit_by_number)

    # Filtering never renumbers or retitles the retained sheets.
    assert all(full_by_number[number] == title
               for number, title in permit_by_number.items())


def test_symbols_legend_uses_a_detail_retained_in_catlin_permit_set(catlin_model_ro,
                                                                    catlin_model_report):
    preferences = load_preferences(CATLIN_DIR)
    permit_numbers = {sheet.number for sheet in build_sheet_index(
        catlin_model_ro, preferences, sets="permit", report=catlin_model_report)}
    legend = " ".join(f"{symbol} {meaning}" for symbol, meaning in SYMBOLS)
    referenced_sheets = set(re.findall(r"\b[A-Z]-\d{3}(?:\.\d+)?\b", legend))

    assert "A-501" in referenced_sheets
    assert referenced_sheets <= permit_numbers
    assert "A-502" not in legend
