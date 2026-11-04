"""RL-SG-BALCONY's fascia brackets and TR-SG-GUTTER share the same few inches of TR-SG-FASCIA.

The guard is through-bolted to the PVC fascia and rim blocking. Each 3" post stands in its
bracket's pocket, 1.518" outboard of the fascia face (ESR-3485 Fig. 10), down to the
bracket's bottom. Since 2026-10-31 the gutter's back sheet lies on the fascia 1" BELOW the
bracket bottoms, and TR-SG-APRON carries the drip's water down to it.
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
    from typehaus.resolve.railings.guard_line import guard_line_offset_m
    from typehaus.resolve.railings.spans import deck_surface
    deck = next(f for f in catlin_model.floors if f.tag == "FS-SG-DECK")
    guard = catlin_model.plan.by_tag("RL-SG-BALCONY")
    surface = deck_surface(deck, [p.xy_m for p in guard.path],
                           guard_line_offset_m(catlin_model.plan.library, guard))
    for bracket, post in zip(brackets, posts, strict=True):
        point = tuple(sum(p[i] for p in post.outline)/len(post.outline) for i in range(2))
        assert bracket.z1_m == pytest.approx(surface.height_at(point)-2*IN)
        assert bracket.z1_m-bracket.z0_m == pytest.approx(6*IN)



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
        assert p[4] == pytest.approx(b[4] + 0.125*IN), post.tag


def test_the_gutter_clears_the_guard_brackets(catlin_model):
    gutter = [_box(s) for s in catlin_model.solids
              if s.tag.startswith("TR-SG-GUTTER-") and s.category == "gutter"]
    clashes = [s.tag for s in catlin_model.solids
               if s.tag.startswith(("RL-SG-BALCONY-FASCIA-BRACKET", "RL-SG-BALCONY-POST"))
               and any(_overlap(_box(s), g) for g in gutter)]
    assert not clashes, f"gutter intersects {clashes}"
