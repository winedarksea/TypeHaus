"""R310.1 follows an escape door to the floor it opens on (code.R310_1_storey_egress)."""

from dataclasses import replace

from typehaus.checks.code.mn_residential.egress import basement_storey_egress
from typehaus.findings import Result


def test_sunken_door_escapes_by_the_ladder_and_stair(catlin_ctx):
    (finding,) = basement_storey_egress(catlin_ctx)
    assert finding.result is Result.PASS
    assert "LAD-SG-ESCAPE" in finding.message and "ST-SG-PORCH" in finding.message


def test_deep_court_with_no_ladder_fails(catlin_ctx):
    model = replace(catlin_ctx.model, canvas_objects=[
        o for o in catlin_ctx.model.canvas_objects if o.tag != "LAD-SG-ESCAPE"])
    (finding,) = basement_storey_egress(replace(catlin_ctx, model=model))
    assert finding.result is Result.FAIL
    assert "no stair or ladder" in finding.message


def test_catlin_ladder_meets_the_rung_rules(catlin_plan):
    spec = next(t.ladder for t in catlin_plan.library.furniture_types
                if t.tag == "FT-COURT-LADDER-WLA6SS")
    assert spec.rung_inside_width.inches >= 12 and spec.rung_projection.inches >= 3
    assert spec.rung_spacing.inches <= 18 and spec.first_rung_height.inches <= 18
    # Court floor to plank 110 3/8": the top rung stands 2 3/8" under it.
    assert abs(110.375 - spec.top_rung_height.inches - 2.375) < 0.01
