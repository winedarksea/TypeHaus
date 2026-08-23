"""``structural.frost_depth`` measures from the lowest adjacent grade, not from the datum.

The datum and the grade coincide only while ``Site.grade`` is 0'-0", which is the only case
the check was ever exercised against. Once grade moves — as it does when a house is lifted
out of the ground by dropping grade under it — a footing that has not moved is that much
*less* deep, and the rule has to say so.

Since 2026-08-22 there is a second way for the two to diverge, and it does not move
``Site.grade`` at all: an *excavation*. A footing beside an open sunken court is measured
from that court's floor (IRC R403.1.4.1), and no single grade plane can express it — see
``test_frost_depth_excavation.py`` for that half. These pin the plane half, which the
excavation-aware derivation is a strict refinement of: away from a hole, the plane is still
the answer, and moving it still moves every verdict that depends on it.
"""

from __future__ import annotations

import copy

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.quantities import ft

# The footings the sunken-garden excavation reaches. Their grade is the garden floor, so
# moving the site plane up or down does not move them, and they are excluded wherever
# these tests make a claim about *the plane*.
_BESIDE_THE_EXCAVATION = {"FT-B-BRICK", "FT-B-S1", "FT-B-S2", "FT-B-S3",
                          "FT-SG-COL", "FT-SG-FCOL", "FT-SG-E1", "FT-SG-E2",
                          "FT-SG-S", "FT-SG-W1", "FT-SG-W2"}


def _model_at_grade(catlin_model, grade):
    model = copy.copy(catlin_model)
    site = catlin_model.plan.project.site.model_copy(update={"grade": grade})
    project = catlin_model.plan.project.model_copy(update={"site": site})
    model.plan = catlin_model.plan.model_copy(update={"project": project})
    return model


def _frost(model):
    report = run_from_model(model, [], tier=Tier.STRUCTURAL)
    return [f for f in report.findings if f.check_id == "structural.frost_depth"]


def _on_the_plane(findings):
    """Findings about footings the excavation does not reach."""
    return [f for f in findings
            if not (set(f.element_tags) & _BESIDE_THE_EXCAVATION)]


def test_frost_depth_passes_at_the_authored_grade(catlin_model):
    """Every footing the excavation does not reach clears 42" under the authored plane."""
    matched = _on_the_plane(_frost(catlin_model))
    assert matched and all(f.result.value == "pass" for f in matched)


def test_dropping_grade_makes_unmoved_footings_shallow(catlin_model):
    # Grade 3'-0" below the datum leaves catlin's 42"-deep footings only 6" under soil.
    matched = _on_the_plane(_frost(_model_at_grade(catlin_model, ft(-3))))
    assert matched and any(f.result.value == "fail" for f in matched)
    failures = [f for f in matched if f.result.value == "fail"]
    # The reported depth is measured to grade, so it must be shallower than the frost
    # minimum the message quotes — never the datum-relative depth, which would still pass.
    for finding in failures:
        assert "below grade" in finding.message


def test_raising_grade_buries_footings_deeper(catlin_model):
    # Grade 3'-0" above the datum buries everything the plane governs; nothing is shallow.
    matched = _on_the_plane(_frost(_model_at_grade(catlin_model, ft(3))))
    assert matched and all(f.result.value == "pass" for f in matched)


def test_raising_the_plane_does_not_bury_a_footing_beside_an_open_excavation(catlin_model):
    """The claim the old single-plane reading got backwards.

    Piling 3' more soil onto the site does nothing for the strip along the sunken garden:
    the ground beside it is still the garden floor, 6'-6" down, and the court does not fill
    in because the survey says the lawn got higher.
    """
    matched = _frost(_model_at_grade(catlin_model, ft(3)))
    south = next(f for f in matched if "FT-B-S2" in f.element_tags)
    # It passes — but on the R403.3 wing insulation beside it, and still measured against
    # the garden floor. The single-plane reading would have it 10'-2" deep and would say so.
    assert south.result.value == "pass"
    assert "SL-SG-FLOOR" in south.message and "R403.3" in south.message
    assert '8"' in south.message
