"""R806.2 attic ventilation: the nested roof eave trim is walked, and the ratio is graded.

The garage's vented eave is ``Roof.eave_trim`` (``RF-GARAGE``), not a top-level element.
Its intake and ridge ratings are not authored yet, so the honest answer is UNKNOWN; the grade
tests supply test ratings through a plan wrapper, which keeps the house source untouched.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.checks.code.mn_residential.attic_ventilation import attic_ventilation
from typehaus.findings import Result
from typehaus.model.spatial import Roof


class _PlanWithEaveRatings:
    """The catlin plan with the named roofs' eave trims swapped for rated copies."""

    def __init__(self, plan, trims_by_tag):
        self._plan = plan
        self._trims = trims_by_tag

    def __getattr__(self, name):
        return getattr(self._plan, name)

    def all_elements(self):
        return (self._swap(element) for element in self._plan.all_elements())

    def by_tag(self, tag):
        return self._swap(self._plan.by_tag(tag))

    def _swap(self, element):
        if isinstance(element, Roof) and element.tag in self._trims:
            return element.model_copy(update={"eave_trim": self._trims[element.tag]})
        return element


def _rated_garage_ctx(catlin_plan, catlin_ctx, *, soffit, ridge):
    garage = catlin_plan.by_tag("RF-GARAGE")
    rated = garage.eave_trim.model_copy(update={
        "soffit_nfva_in2_per_ft": soffit,
        "ridge_vent_nfva_in2_per_ft": ridge,
    })
    plan = _PlanWithEaveRatings(catlin_plan, {"RF-GARAGE": rated})
    return SimpleNamespace(model=catlin_ctx.model, plan=plan)


def test_nested_vented_eave_is_graded_not_passed_as_unvented(catlin_ctx):
    """RF-GARAGE is vented through its nested trim: the old top-level read said PASS."""
    findings = attic_ventilation(catlin_ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert "no vented eave" not in finding.message
    assert finding.result is Result.UNKNOWN
    assert finding.element_tags == ("RF-GARAGE",)
    assert "RF-GARAGE soffit net free area" in finding.message
    assert "RF-GARAGE ridge vent net free area" in finding.message


@pytest.mark.parametrize("soffit, ridge", [(10.0, 12.5), (10.0, None)])
def test_intake_at_one_fifty_passes_and_unrated_ridge_cannot_fail_it(
        catlin_plan, catlin_ctx, soffit, ridge):
    """Ratings clear 1/150 (553 in²) on intake alone: unrated runs can only add."""
    ctx = _rated_garage_ctx(catlin_plan, catlin_ctx, soffit=soffit, ridge=ridge)
    (finding,) = attic_ventilation(ctx)
    assert finding.result is Result.PASS
    assert "in² net free area" in finding.message


def test_short_intake_with_unrated_ridge_is_unknown_not_fail(catlin_plan, catlin_ctx):
    ctx = _rated_garage_ctx(catlin_plan, catlin_ctx, soffit=2.0, ridge=None)
    (finding,) = attic_ventilation(ctx)
    assert finding.result is Result.UNKNOWN
    assert "RF-GARAGE ridge vent net free area" in finding.message
    assert "RF-GARAGE soffit" not in finding.message


def test_known_short_ratings_fail(catlin_plan, catlin_ctx):
    """2 in²/ft intake and ridge is about 200 in² over ~576 sf: short of 1/150 and 1/300."""
    ctx = _rated_garage_ctx(catlin_plan, catlin_ctx, soffit=2.0, ridge=2.0)
    (finding,) = attic_ventilation(ctx)
    assert finding.result is Result.FAIL
    assert "1/150" in finding.message and "1/300" in finding.message


def test_balanced_exhaust_clears_the_one_three_hundredth_exception(catlin_plan, catlin_ctx):
    """281 in² with 47% up high clears 1/300 (~277 in²) though it misses 1/150 (553 in²)."""
    ctx = _rated_garage_ctx(catlin_plan, catlin_ctx, soffit=2.0, ridge=5.2)
    (finding,) = attic_ventilation(ctx)
    assert finding.result is Result.PASS
    assert "exception 2" in finding.message


def test_the_house_roof_is_still_graded_beside_the_vented_garage(catlin_ctx):
    """R806.5 partitions the roofs with R806.2: the vented garage leaves the house graded."""
    from typehaus.checks.code.unvented_roof import _vented_roof_tags, unvented_roof_insulation

    assert _vented_roof_tags(catlin_ctx) == {"RF-GARAGE"}
    findings = unvented_roof_insulation(catlin_ctx)
    assert findings and all(f.result is not Result.NOT_APPLICABLE for f in findings)
    assert any("ROOF" in f.message and f.result is Result.PASS for f in findings)
