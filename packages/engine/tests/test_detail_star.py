"""Transition.star — authored curation of the primary detail set (2026-07-31).

`star` marks the derived details a builder actually opens: `detail_index` serves it to
the UI, `build_sheet_index(details="primary")` composes only starred (plus authored)
detail sheets, and the flag round-trips to `houses/<house>/plan/transitions.py` through
the ordinary PatchOp writeback — which is why that file is `# haus: editable` now.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from typehaus.emit.draw.details import detail_index
from typehaus.emit.draw.sheets import build_sheet_index
from typehaus.resolve import resolve
from typehaus.source import load_plan
from typehaus.source.coordinator import ProjectCoordinator
from typehaus.source.ops import PatchOp

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"
_DETAIL_NUMBER = re.compile(r"A-4\d\d$")


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    assert result.plan is not None
    model, _ = resolve(result.plan)
    return model


def test_star_reaches_the_detail_index(catlin_model):
    rows = detail_index(catlin_model)
    starred = {r["key"] for r in rows if r["star"]}
    unstarred = {r["key"] for r in rows if not r["star"]}
    # The eave transition is authored star=True; the interior-opening one is not.
    assert any(k.startswith("wall_roof:") for k in starred)
    assert any("INT_" in k for k in unstarred)


def test_primary_sheet_set_keeps_only_starred_derived_details(catlin_model):
    everything = build_sheet_index(catlin_model)
    primary = build_sheet_index(catlin_model, details="primary")
    det_all = [s for s in everything if _DETAIL_NUMBER.match(s.number)]
    det_primary = [s for s in primary if _DETAIL_NUMBER.match(s.number)]
    # The filter drops exactly the unstarred derived sheets; everything it keeps is
    # flagged primary, and non-detail sheets are untouched.
    assert len(det_primary) < len(det_all)
    assert all(s.primary for s in det_primary)
    assert len(det_all) - len(det_primary) == sum(1 for s in det_all if not s.primary)
    non_detail = lambda sheets: [s.number for s in sheets  # noqa: E731
                                 if not _DETAIL_NUMBER.match(s.number)]
    assert non_detail(everything) == non_detail(primary)


def test_star_writes_back_to_the_real_transitions_source(tmp_path):
    house = tmp_path / "catlin"
    shutil.copytree(CATLIN_DIR, house,
                    ignore=shutil.ignore_patterns("out", "__pycache__", ".claude"))
    source = house / "plan" / "transitions.py"
    assert 'tag="TR-CATLIN-EAVE"' in source.read_text()
    coordinator = ProjectCoordinator(house)
    coordinator.apply_patch(
        [PatchOp("update", "Transition", "TR-CATLIN-EAVE", {"star": False})],
        coordinator.revision())
    text = source.read_text()
    block = text[text.index('tag="TR-CATLIN-EAVE"'):text.index("TR-CATLIN-FOUNDATION")]
    assert "star=False" in block
    result = load_plan(house)
    assert result.plan is not None, [f.message for f in result.findings]
    eave = next(t for t in result.plan.library.transitions if t.tag == "TR-CATLIN-EAVE")
    assert eave.star is False
