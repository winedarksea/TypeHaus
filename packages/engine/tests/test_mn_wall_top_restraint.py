"""``code.MN_1309_0404_wall_top`` against catlin, pinned to the hand check in
``houses/catlin/notes/main_floor_truss_basis.md`` §4 (the oracle)."""

from __future__ import annotations

import re

from _helpers import check_context

from typehaus.checks.code.mn_residential.foundation_wall_top import foundation_wall_top
from typehaus.findings import Result


def test_catlin_wall_tops_match_the_basis_note(catlin_model_ro) -> None:
    findings = {f.element_tags[0] if f.element_tags else re.match(r"(W-B-\w+)", f.message)[1]: f
                for f in foundation_wall_top(check_context(model=catlin_model_ro))}
    assert {tag for tag, f in findings.items() if f.result is Result.PASS} == {
        "W-B-E1", "W-B-E2", "W-B-W1", "W-B-W2", "W-B-N1", "W-B-N3", "W-B-N4", "W-B-S1",
        "W-B-S4"}
    # FO-M-STAIR fills W-B-N2's first three joist spaces: a design, not a table read.
    assert findings["W-B-N2"].result is Result.UNKNOWN
    for f in findings.values():
        assert "row 8'/7.5' gives 400 plf" in f.message
    # Perpendicular: 538 lb a truss end, 563 lb a TJI end (note §4).
    assert "1 A35Z x 538 lb = 538 lb, d/c 0.74" in findings["W-B-E2"].message
    assert "14 11.875 TJI 230 ends at 16\" o.c., 533 lb each): 1 A35Z x 563 lb" \
        in findings["W-B-W2"].message
    assert "d/c 0.95" in findings["W-B-W2"].message
    # Parallel: worst station per wall.
    for tag, worst in (("W-B-N1", "0.89"), ("W-B-S1", "0.69"), ("W-B-S4", "0.71"),
                       ("W-B-N3", "0.57"), ("W-B-N4", "0.83")):
        assert f"worst d/c {worst}" in findings[tag].message, tag
