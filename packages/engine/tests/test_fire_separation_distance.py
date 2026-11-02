"""R302.1 / Table R302.1(1): exterior walls, openings and projections vs the lot lines."""

from __future__ import annotations

import copy

from typehaus.checks import run_from_model
from typehaus.quantities import m, pt

_CID = "code.R302_1_exterior_walls"


def _results(model) -> list[tuple[str, tuple[str, ...]]]:
    return [(f.result.value, f.element_tags)
            for f in run_from_model(model, [], only=[_CID]).findings if f.check_id == _CID]


def test_catlin_clears_5_ft_and_a_tight_west_line_does_not(catlin_model_ro):
    assert {result for result, _ in _results(catlin_model_ro)} == {"pass"}
    site = catlin_model_ro.plan.project.site
    ring = [p.xy_m for p in site.parcel]
    # Pull the west lot line (x = -2.13 m) to 1 ft off the house's west face.
    tight = tuple(pt(m(-0.5 if x < 0 else x), m(y)) for x, y in ring)
    model = copy.copy(catlin_model_ro)
    project = model.plan.project.model_copy(
        update={"site": site.model_copy(update={"parcel": tight})})
    model.plan = model.plan.model_copy(update={"project": project})
    found = _results(model)
    assert ("fail", ("RF-HOUSE",)) in found  # eave inside 2 ft
    assert any(result == "unknown" for result, _ in found)  # an unrated wall under 5 ft
    assert sum(result == "fail" for result, _ in found) > 1  # and its windows
