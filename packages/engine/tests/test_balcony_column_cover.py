"""The balcony corner columns' P-M point at 2", 2 1/2" and 3" cover.

Oracle: ``houses/catlin/notes/balcony_moment_columns.md`` §14, worked by hand. 2" is what is
built; the other two are the alternatives the durability question keeps asking about.
"""

from __future__ import annotations

import dataclasses

import pytest

#: note §14 at P_u 4,855.3 (front row): (cover, c, phi, phi*Mn lb-ft).
_AT_PU = ((2.0, 2.750, 0.900, 24_678.0), (2.5, 2.867, 0.900, 24_657.0),
          (3.0, 2.981, 0.868, 23_941.0))
#: note §14's envelope, 1.2D + 1.0W + L at P_u 3,724: (cover, phi*Mn).
_ENVELOPE = ((2.0, 24_382.0), (2.5, 24_381.0), (3.0, 23_812.0))


@pytest.fixture(scope="module")
def corner(catlin_plan):
    from typehaus.engineering import deck_post
    from typehaus.engineering.pier_basis import cast_piers
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    ctx = EngineeringContext(plan=catlin_plan, model=model, soil_class="GM")
    pier = next(p for p in cast_piers(ctx) if p.tag == "PT-SG-BF1")
    return pier, deck_post.cage_for(pier)


def test_the_built_cover_is_two_inches(corner) -> None:
    pier, _cage = corner
    assert pier.specified_cover_in == pytest.approx(2.0)


@pytest.mark.parametrize("cover,c,phi,phi_mn", _AT_PU)
def test_the_pm_point_reproduces_the_hand_pass(corner, cover, c, phi, phi_mn) -> None:
    from typehaus.engineering.deck_post import _pm_point

    pier, cage = corner
    got_mn, got_phi, got_c = _pm_point(pier, cage, cover, pier.factored_lb)
    assert got_c == pytest.approx(c, abs=0.002)
    assert got_phi == pytest.approx(phi, abs=0.001)
    assert got_mn == pytest.approx(phi_mn, rel=5e-4)


@pytest.mark.parametrize("cover,phi_mn", _ENVELOPE)
def test_the_envelope_at_each_cover(corner, cover, phi_mn) -> None:
    """3" puts the section into Table 21.2.2's transition band (phi 0.868); 2 1/2" does not."""
    from typehaus.engineering.deck_post import _one

    pier, _cage = corner
    record = _one(dataclasses.replace(pier, specified_cover_in=cover))
    envelope = next(s for s in record.limit_states if s.name.startswith("P-M envelope"))
    assert envelope.capacity == pytest.approx(phi_mn, rel=5e-4)
    assert envelope.demand / envelope.capacity < 0.20
