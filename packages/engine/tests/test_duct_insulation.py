"""``mep.duct_insulation`` against ``houses/catlin/notes/duct_insulation.md``'s hand grades."""

from __future__ import annotations

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.findings import Result


def test_catlin_verdicts_match_the_hand_grades(catlin_model_ro) -> None:
    found = [f for f in run_from_model(catlin_model_ro, [], tier=Tier.CODE,
                                       only="mep.duct_insulation").findings
             if f.check_id == "mep.duct_insulation"]
    by_result: dict[Result, set[str]] = {}
    for f in found:
        by_result.setdefault(f.result, set()).update(f.element_tags)
    assert by_result.get(Result.PASS) == {"DU-ERV-OA", "DU-ERV-EA"}, [f.message for f in found]
    assert Result.FAIL not in by_result and Result.UNKNOWN not in by_result
    assert {"DU-ERV-RISER-SUP", "DU-ERV-RISER-EXH", "DU-B-WH-IN", "DU-B-WH-OUT"} <= \
        by_result[Result.NOT_APPLICABLE]
    for f in found:
        if f.result is Result.PASS:  # note a: the 3 ft inside the north wall, ~2" steps
            assert "R-3.3 + V" in f.message
            length = float(f.message.split("meets ")[1].split(" ft")[0])
            assert 2.8 <= length <= 3.0, f.message
