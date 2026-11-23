"""The balcony corner columns' P-M point at 2", 2 1/2" and 3" cover.

Oracle: ``houses/catlin/notes/balcony_moment_columns.md`` §14, re-worked in §26. 2" is what is
built; 3" is the owner's aim and 2 1/2" the middle, both refused by the north-entry pad dowels'
hooked development (§14), not by anything graded here.
"""

from __future__ import annotations

import dataclasses

import pytest

#: note §26 (§14 at the final loads, 2026-11-23), P_u 4,440.9 (front row, no planter, beam
#: statics): (cover, c, phi, phi*Mn lb-ft). Re-worked by the review's independent
#: strain-compatibility script, which the engine matches to 0.1 lb-ft.
_AT_PU = ((2.0, 2.742, 0.900, 24_570.0), (2.5, 2.859, 0.900, 24_555.8),
          (3.0, 2.973, 0.870, 23_893.6))
#: §26's envelope: (cover, phi*Mn at the governing pair). 2" and 2 1/2" govern at
#: 1.2D + 1.0W + L_guard, floor live absent (P_u 1,718.2); 3" at 1.2D + 1.0W + L (P_u 3,419.8).
_ENVELOPE = ((2.0, 23_856.6), (2.5, 23_889.9), (3.0, 23_776.7))
#: §26's joint, PT-SG-BR1, the worst case of each state (bearing at 1.2D + 1.0W + L, tension at
#: the floor-empty guard pair), flexible-base delta: (cover, bearing C, φBn, T per bar). The
#: dowel ring shrinks with the cage, so T rises 14% at 3" (still under φAs fy 16,740, §28). §27's
#: couple is on the block the dowel force itself produces.
_JOINT = ((2.0, 13_128.0, 38_943.0, 9_162.0), (2.5, 13_602.0, 41_363.0, 9_774.0),
          (3.0, 14_131.0, 43_748.0, 10_476.0))


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
    """3" puts the section into Table 21.2.2's transition band (phi 0.870); 2 1/2" does not."""
    from typehaus.engineering.deck_post import _one

    pier, _cage = corner
    record = _one(dataclasses.replace(pier, specified_cover_in=cover))
    envelope = next(s for s in record.limit_states if s.name.startswith("P-M envelope"))
    assert envelope.capacity == pytest.approx(phi_mn, rel=5e-4)
    assert envelope.demand / envelope.capacity < 0.35     # wind + guard, §26/§28


@pytest.mark.parametrize("cover,comp,phi_bn,pull", _JOINT)
def test_the_wall_top_joint_at_each_cover(catlin_plan, cover, comp, phi_bn, pull) -> None:
    from typehaus.engineering import column_support
    from typehaus.engineering.pier_basis import cast_piers
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    ctx = EngineeringContext(plan=catlin_plan, model=model, soil_class="GM")
    pier = next(p for p in cast_piers(ctx) if p.tag == "PT-SG-BR1")
    states = {s.name: s for s in column_support._column_states(
        ctx, dataclasses.replace(pier, specified_cover_in=cover), "W-SG-W1", [], [], {})}
    bearing = states["PT-SG-BR1: bearing on the wall top"]
    tension = states["PT-SG-BR1: dowel tension across the joint"]
    assert bearing.demand == pytest.approx(comp, rel=0.003)
    assert bearing.capacity == pytest.approx(phi_bn, rel=0.003)
    assert tension.demand == pytest.approx(pull, rel=0.003)
