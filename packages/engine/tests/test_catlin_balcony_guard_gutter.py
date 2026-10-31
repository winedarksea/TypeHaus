"""RL-SG-BALCONY's fascia brackets and TR-SG-GUTTER share the same few inches of TR-SG-FASCIA.

The guard is through-bolted to the PVC fascia and rim blocking; the gutter's back sheet lies
flush on the same fascia face, 3" below the deck top, so the board ends drain into it. The
brackets are drawn (``RailingType.fascia_bracket_*``) so the clash is visible in 3D, and each
3" post stands in its bracket's pocket, 1.518" outboard of the fascia face (ESR-3485 Fig. 10),
down to the bracket's bottom.
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


def test_each_post_stands_in_its_brackets_pocket(catlin_model):
    """The post adds no clash of its own: below the deck it is inside its bracket's box."""
    brackets = {s.tag.rsplit("BRACKET", 1)[1]: _box(s) for s in catlin_model.solids
                if "RL-SG-BALCONY-FASCIA-BRACKET" in s.tag}
    posts = [s for s in catlin_model.solids
             if s.tag.startswith("RL-SG-BALCONY-POST") and s.category == "railing"]
    assert posts and len(posts) == len(brackets)
    for post in posts:
        p, b = _box(post), brackets[post.tag.rsplit("POST", 1)[1]]
        assert b[0] - 1e-9 <= p[0] and p[1] <= b[1] + 1e-9, post.tag
        assert b[2] - 1e-9 <= p[2] and p[3] <= b[3] + 1e-9, post.tag
        assert p[4] == pytest.approx(b[4]), post.tag


@pytest.mark.xfail(strict=True, reason=(
    "OPEN: the gutter back sheet lies flush on the fascia where the brackets (and the posts "
    "in them) stand. Drawing read (5.64\" x 3.29\", ESR-3485 Fig. 10); the clash is real."))
def test_the_gutter_clears_the_guard_brackets(catlin_model):
    gutter = [_box(s) for s in catlin_model.solids
              if s.tag.startswith("TR-SG-GUTTER-") and s.category == "gutter"]
    clashes = [s.tag for s in catlin_model.solids
               if s.tag.startswith(("RL-SG-BALCONY-FASCIA-BRACKET", "RL-SG-BALCONY-POST"))
               and any(_overlap(_box(s), g) for g in gutter)]
    assert not clashes, f"gutter intersects {clashes}"
