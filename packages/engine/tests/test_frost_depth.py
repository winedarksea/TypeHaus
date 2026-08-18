"""``structural.frost_depth`` measures from finished grade, not from the project datum.

The two coincide only while ``Site.grade`` is 0'-0", which is the only case the check was
ever exercised against. Once grade moves — as it does when a house is lifted out of the
ground by dropping grade under it — a footing that has not moved is that much *less* deep,
and the rule has to say so.
"""

from __future__ import annotations

import copy

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.quantities import ft


def _model_at_grade(catlin_model, grade):
    model = copy.copy(catlin_model)
    site = catlin_model.plan.project.site.model_copy(update={"grade": grade})
    project = catlin_model.plan.project.model_copy(update={"site": site})
    model.plan = catlin_model.plan.model_copy(update={"project": project})
    return model


def _frost(model):
    report = run_from_model(model, [], tier=Tier.STRUCTURAL)
    return [f for f in report.findings if f.check_id == "structural.frost_depth"]


def test_frost_depth_passes_at_the_authored_grade(catlin_model):
    matched = _frost(catlin_model)
    assert matched and all(f.result.value == "pass" for f in matched)


def test_dropping_grade_makes_unmoved_footings_shallow(catlin_model):
    # Grade 3'-0" below the datum leaves catlin's 42"-deep footings only 6" under soil.
    matched = _frost(_model_at_grade(catlin_model, ft(-3)))
    assert matched and any(f.result.value == "fail" for f in matched)
    failures = [f for f in matched if f.result.value == "fail"]
    # The reported depth is measured to grade, so it must be shallower than the frost
    # minimum the message quotes — never the datum-relative depth, which would still pass.
    for finding in failures:
        assert "below grade" in finding.message


def test_raising_grade_buries_footings_deeper(catlin_model):
    # Grade 3'-0" above the datum buries everything; nothing can be shallow.
    matched = _frost(_model_at_grade(catlin_model, ft(3)))
    assert matched and all(f.result.value == "pass" for f in matched)
