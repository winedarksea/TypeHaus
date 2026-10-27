"""RL-SG-BALCONY's fascia brackets and TR-SG-GUTTER share the same few inches of TR-SG-FASCIA.

The guard is through-bolted to the PVC fascia and rim blocking. The gutter's back sheet rides
the same fascia, 3" below the deck top. Nothing in the model draws the brackets, so this reads
them off the authored rule instead: top 1/2" below the rim top, Ultralox's published height.
"""

from __future__ import annotations

import pytest

from typehaus.quantities import inch

IN = inch(1).meters
#: Ultralox fascia-mount bracket: 5" at the mounting face ("flat cut"; a "high cut" style is 6"
#: at the outside). The type carries no bracket field, so the number lives here.
BRACKET_HEIGHT_IN = 5.0
#: sunken_garden.py: "bracket top 1/2" below the rim top".
BRACKET_BELOW_RIM_IN = 0.5
#: Aluminium plank on the joists; the fascia top is the plank top, the rim top is below it.
PLANK_IN = 1.5


def _bands(model):
    fascia = next(s for s in model.solids if s.tag == "TR-SG-FASCIA-1")
    gutter = [s for s in model.solids
              if s.tag.startswith("TR-SG-GUTTER-") and s.category == "gutter"]
    rim_top = fascia.z1_m - PLANK_IN * IN
    bracket = (rim_top - (BRACKET_BELOW_RIM_IN + BRACKET_HEIGHT_IN) * IN,
               rim_top - BRACKET_BELOW_RIM_IN * IN)
    return bracket, (min(g.z0_m for g in gutter), max(g.z1_m for g in gutter))


@pytest.mark.xfail(strict=True, reason=(
    "OPEN: gutter 110-114\" and bracket 110-115\" overlap 4\" on the fascia. Resolution "
    "(lower the gutter or raise the brackets) waits on the bracket plan projection."))
def test_the_gutter_clears_the_guard_brackets(catlin_model):
    bracket, gutter = _bands(catlin_model)
    assert gutter[1] <= bracket[0] or gutter[0] >= bracket[1], (
        f"gutter z {gutter[0] / IN:.2f}..{gutter[1] / IN:.2f}\" shares the fascia with "
        f"brackets z {bracket[0] / IN:.2f}..{bracket[1] / IN:.2f}\"")
