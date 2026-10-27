"""RL-SG-BALCONY's fascia brackets and TR-SG-GUTTER share the same few inches of TR-SG-FASCIA.

The guard is through-bolted to the PVC fascia and rim blocking; the gutter's back sheet lies
flush on the same fascia face, 3" below the deck top, so the board ends drain into it. The
brackets are drawn (``RailingType.fascia_bracket_*``) so the clash is visible in 3D.
"""

from __future__ import annotations

import pytest

from typehaus.quantities import inch

IN = inch(1).meters


def _box(solid):
    xs = [p[0] for p in solid.outline]
    ys = [p[1] for p in solid.outline]
    return min(xs), max(xs), min(ys), max(ys), solid.z0_m, solid.z1_m


def _overlap(a, b) -> bool:
    return all(a[i] < b[i + 1] and b[i] < a[i + 1] for i in (0, 2, 4))


def test_the_guard_draws_a_bracket_at_each_post_station(catlin_model):
    brackets = [s for s in catlin_model.solids if "RL-SG-BALCONY-FASCIA-BRACKET" in s.tag]
    posts = [s for s in catlin_model.solids
             if s.tag.startswith("RL-SG-BALCONY-POST") and s.category == "railing"]
    assert len(brackets) == len(posts)
    fascia_top = max(s.z1_m for s in catlin_model.solids if s.tag.startswith("TR-SG-FASCIA"))
    for b in brackets:
        assert b.z1_m == pytest.approx(fascia_top - 0.5 * IN)  # 1/2" below the rim top
        assert b.z1_m - b.z0_m == pytest.approx(5.0 * IN)      # Ultralox flat cut


@pytest.mark.xfail(strict=True, reason=(
    "OPEN: the gutter back sheet lies flush on the fascia where the brackets stand; the "
    "fix (notch, stand-off or relocated bracket) waits on the bracket drawing."))
def test_the_gutter_clears_the_guard_brackets(catlin_model):
    gutter = [_box(s) for s in catlin_model.solids
              if s.tag.startswith("TR-SG-GUTTER-") and s.category == "gutter"]
    clashes = [s.tag for s in catlin_model.solids
               if "RL-SG-BALCONY-FASCIA-BRACKET" in s.tag
               and any(_overlap(_box(s), g) for g in gutter)]
    assert not clashes, f"gutter intersects {clashes}"
