"""A UI-movable element authored in a non-editable plan module can't be written back
(its drag POSTs a writeback op the coordinator can't apply), so the loader must fail loud
rather than let the move silently not persist. See loader._consistency_check."""

from __future__ import annotations

from pathlib import Path

from typehaus.source import load_plan
from _helpers import CATLIN, STARTER, copy_house



def _errors(result, check_id: str) -> list:
    return [f for f in result.findings
            if f.check_id == check_id and str(f.severity).lower().endswith("error")]


def test_catlin_has_no_uneditable_movable_elements() -> None:
    """Control: every movable element in the reference house lives in an editable file."""
    result = load_plan(CATLIN)
    assert not _errors(result, "loader.uneditable_movable_element"), \
        _errors(result, "loader.uneditable_movable_element")


def test_movable_element_in_noneditable_file_is_a_hard_error(tmp_path: Path) -> None:
    dst = tmp_path / "catlin"
    copy_house(CATLIN, dst)
    mep = dst / "plan" / "mep.py"
    # Strip the `# haus: editable` header → mep.py (which authors the water heater and
    # other placeables) becomes non-editable, reproducing the silent "move didn't save" bug.
    mep.write_text(mep.read_text().replace("# haus: editable\n", "", 1))

    result = load_plan(dst)
    errs = _errors(result, "loader.uneditable_movable_element")
    flagged = {t for f in errs for t in f.element_tags}
    assert "EQ-B-WH" in flagged, flagged  # the water heater the user reported


def test_catlin_has_zero_provenance_gaps() -> None:
    """Acceptance criterion: runtime authorship capture locates every element the libcst
    scan can't see (params/ math, plan/views.py Slices), so a clean reference house
    builds with no loader.provenance_gap warnings at all."""
    result = load_plan(CATLIN)
    gaps = [f for f in result.findings if f.check_id == "loader.provenance_gap"]
    assert not gaps, sorted(t for f in gaps for t in f.element_tags)


def test_starter_has_zero_provenance_gaps() -> None:
    result = load_plan(STARTER)
    gaps = [f for f in result.findings if f.check_id == "loader.provenance_gap"]
    assert not gaps, sorted(t for f in gaps for t in f.element_tags)


def test_params_generated_geometry_is_not_flagged() -> None:
    """Params/-generated walls & openings (e.g. sunken_garden) have no constructor to
    write back to — they must stay a benign warning, never the hard error."""
    result = load_plan(CATLIN)
    flagged = {t for f in _errors(result, "loader.uneditable_movable_element")
               for t in f.element_tags}
    assert not any(t.startswith("AO-ARCH") or t.startswith("W-SG-") for t in flagged), flagged
