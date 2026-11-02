"""Authored detail sheets — A-501+ (→ Permit-ready plan set Phase 6).

They were A-401+ until the set took NCS numbering. NCS sheet-type 4 is LARGE-SCALE
VIEWS — an enlarged plan at 1/2" = 1'-0" — and a junction cut at 1-1/2" is a DETAIL,
type 5. See ``emit/draw/sheets.build_sheet_index``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from _helpers import CATLIN as CATLIN_DIR

from typehaus.checks import load_preferences
from typehaus.emit.draw import build_sheet_index
from typehaus.emit.draw.scene import Hatch
from typehaus.emit.draw.schedules.architectural import SYMBOLS
from typehaus.resolve import resolve
from typehaus.source import load_plan


def test_catlin_emits_authored_then_derived_detail_sheets(catlin_sheet_index):
    sheets = catlin_sheet_index()
    # Enlarged head/sill sub-sheets (A-512.1) ride their parent and are not numbered.
    detail_numbers = [s.number for s in sheets
                      if s.number.startswith("A-5") and "." not in s.number]
    # The four authored details keep A-501..A-504, in order, ahead of derived details.
    assert detail_numbers[:4] == ["A-501", "A-502", "A-503", "A-504"]
    titles = {s.number: s.title for s in sheets}
    assert titles["A-501"] == "Foundation detail"
    assert titles["A-502"] == "Floor truss bearing detail"
    # Derived transition details continue the A-5xx block (catlin binds many conditions).
    assert len(detail_numbers) > 4
    # numbering is contiguous
    nums = [int(n.split("-")[1]) for n in detail_numbers]
    assert nums == list(range(501, 501 + len(nums)))


def test_deckbrg_scene_seats_the_truss_on_the_pour(catlin_model_ro, catlin_sheet_index):
    """FS-M-NE's trusses on W-B-E1 (decision #112): pour to the -13 7/16" seat, the 1/16"
    gasket and 1 1/2" PT mudsill on it, and the 11 7/8" truss from there to the datum."""
    sheets = {s.number: s for s in catlin_sheet_index()}
    scene = sheets["A-502"].scene(catlin_model_ro)
    bands = {}
    for hatch in (n for n in scene.nodes if isinstance(n, Hatch)):
        zs = [p[1] for p in hatch.boundary]
        bands.setdefault(hatch.pattern, []).append((min(zs), max(zs)))
    assert any(top == pytest.approx(-13.4375, abs=1e-3) for _lo, top in bands["concrete"])
    assert (-13.4375, -13.375) in [pytest.approx(b, abs=1e-3) for b in bands["sill-seal"]]
    assert (-13.375, -11.875) in [pytest.approx(b, abs=1e-3) for b in bands["pt-syp"]]
    assert (-11.875, 0.0) in [pytest.approx(b, abs=1e-3) for b in bands["lumber"]]


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

    assert full_by_number["A-502"] == "Floor truss bearing detail"
    assert full_by_number["A-507"] == "Hall bath shower section"
    assert permit_by_number["A-506"] == "Sauna window-side reading recliner"
    assert {"A-502", "A-507"}.isdisjoint(permit_by_number)

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
