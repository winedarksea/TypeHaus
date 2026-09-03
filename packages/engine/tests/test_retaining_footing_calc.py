"""``retaining_basis.footing_states`` against §7 of the hand-worked free-body note.

The oracle is ``houses/catlin/notes/sunken_garden_court_free_body.md`` §7, worked by hand in
a separate pass. §4's stability and §6's stem live in ``test_retaining_court.py`` and
``test_retaining_wall_calc.py``; this is a separate module because it grades a different
member — the footing STRIP, not the wall standing on it.

The assertions worth reading before changing any of them:

* :func:`test_a_footing_with_no_mat_is_five_times_over_as_plain_concrete` is the finding that
  produced this whole calculation, pinned as a regression on the CALCULATION rather than on
  the house. A 4'-0" toe under 1,275 psf is a real flexural cantilever, and a 12" plain strip
  carries a fifth of it. If a future change makes that pass without steel, the change is
  wrong.
* :func:`test_the_plain_branch_gives_up_two_inches_of_its_thickness` pins ACI 318-19
  §14.5.1.7 — a plain footing cast against soil is graded on ``h - 2``.
* :func:`test_the_toe_takes_no_credit_for_the_footings_own_weight` and
  :func:`test_the_heel_takes_no_credit_for_the_pressure_under_it` pin the two deliberate
  conservatisms. Each exists to avoid a load-factor argument, not to win one, and "improving"
  either of them moves the design.
"""

from __future__ import annotations

import pytest

# §7a-§7e, worked by hand against §4's governing at-rest / 110 pcf case.
_TOE_FT, _HEEL_FT, _WIDTH_FT, _DEPTH_FT = 4.0, 3.0, 8.0, 1.0
_Q_TOE, _Q_HEEL = 1275.2, 269.2

_ORACLE = {
    "toe flexure": (14176.0, 19264.0),        # Mu, phi*Mn  ft-lb/ft, with #6 @ 10"
    "heel flexure": (9293.0, 19264.0),
    "footing one-way shear": (5612.0, 8503.0),  # lb/ft, reinforced branch at d
}
#: §7b/§7c/§7d as the PLAIN section the house had before 2026-09-03.
_PLAIN_CAPACITY = 2739.0
_PLAIN_SHEAR = (5452.0, 5258.0)

_WALLS = ("W-SG-W2", "W-SG-E2", "W-SG-S")


@pytest.fixture(scope="module")
def geometry_and_case(catlin_plan):
    """``W-SG-W2``'s geometry and the governing case, straight out of the module."""
    from typehaus.engineering import retaining_basis as rb
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.engineering.soil import presumptive
    from typehaus.model.structure import FoundationWall
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    ctx = EngineeringContext(plan=catlin_plan, model=model, soil_class="GM")
    wall = next(e for e in catlin_plan.all_elements()
                if isinstance(e, FoundationWall) and e.tag == "W-SG-W2")
    geometry, missing = rb._geometry(ctx, wall)
    assert geometry is not None, missing
    case = rb.analyse(geometry, presumptive("GM"), at_rest=True, soil_pcf=110.0,
                      base=rb._base_interface(ctx, wall))
    return geometry, case


def _state(states, name):
    found = [s for s in states if s.name == name]
    assert found, f"no {name!r} state; got {[s.name for s in states]}"
    return found[0]


def test_the_geometry_is_the_one_the_note_worked(geometry_and_case) -> None:
    """A 4'-0" toe and a 3'-0" heel on an 8'-0" base. Everything in §7 rests on these."""
    geometry, _case = geometry_and_case
    assert geometry.toe_ft == pytest.approx(_TOE_FT, abs=0.01)
    assert geometry.heel_ft == pytest.approx(_HEEL_FT, abs=0.01)
    assert geometry.footing_width_ft == pytest.approx(_WIDTH_FT, abs=0.01)
    assert geometry.footing_depth_ft == pytest.approx(_DEPTH_FT, abs=0.01)


def test_the_pressure_diagram_reproduces_the_note(geometry_and_case) -> None:
    """§7a — the trapezoid the toe and heel are both read off."""
    geometry, case = geometry_and_case
    assert case.bearing_psf == pytest.approx(_Q_TOE, rel=0.001)
    q_heel = (case.weight_plf / geometry.footing_width_ft
              * (1.0 - 6.0 * case.eccentricity_ft / geometry.footing_width_ft))
    assert q_heel == pytest.approx(_Q_HEEL, rel=0.002)


@pytest.mark.parametrize("name", sorted(_ORACLE))
def test_the_footing_states_reproduce_the_note(name, geometry_and_case) -> None:
    """§7b, §7c and §7e term by term. Two errors can cancel inside a d/c ratio."""
    from typehaus.engineering.retaining_basis import footing_states

    geometry, case = geometry_and_case
    demand, capacity = _ORACLE[name]
    state = _state(footing_states(geometry, case), name)
    assert state.demand == pytest.approx(demand, rel=0.002)
    assert state.capacity == pytest.approx(capacity, rel=0.002)
    assert state.ok


def test_a_footing_with_no_mat_is_five_times_over_as_plain_concrete(
        geometry_and_case) -> None:
    """§7b — the finding that produced this calculation, pinned on the CALCULATION.

    This must never come out passing. If a future change lets an unreinforced 4'-0" toe under
    1,275 psf report OK, that change has broken the check rather than fixed the footing —
    and the house would silently lose the mat it is now designed with.
    """
    from typehaus.engineering.retaining_basis import _Geometry, footing_states

    geometry, case = geometry_and_case
    bare = _Geometry(**{**geometry.__dict__, "footing_reinforcement": None})
    toe = _state(footing_states(bare, case), "toe flexure")
    assert toe.capacity == pytest.approx(_PLAIN_CAPACITY, rel=0.002)
    assert toe.demand / toe.capacity == pytest.approx(5.18, rel=0.01)
    assert not toe.ok

    heel = _state(footing_states(bare, case), "heel flexure")
    assert heel.demand / heel.capacity == pytest.approx(3.39, rel=0.01)
    assert not heel.ok

    shear = _state(footing_states(bare, case), "footing one-way shear")
    assert (shear.demand, shear.capacity) == (
        pytest.approx(_PLAIN_SHEAR[0], rel=0.002), pytest.approx(_PLAIN_SHEAR[1], rel=0.002))
    assert not shear.ok


def test_the_plain_branch_gives_up_two_inches_of_its_thickness(geometry_and_case) -> None:
    """ACI 318-19 §14.5.1.7. Capacity goes as ``h**2``, so this is a 44% error if lost."""
    from typehaus.engineering.retaining_basis import (
        _PLAIN_SOIL_CAST_DEDUCTION_IN,
        PRESUMPTIVE_FC_PSI,
        _Geometry,
        footing_states,
    )

    assert _PLAIN_SOIL_CAST_DEDUCTION_IN == 2.0
    geometry, case = geometry_and_case
    bare = _Geometry(**{**geometry.__dict__, "footing_reinforcement": None})
    toe = _state(footing_states(bare, case), "toe flexure")
    on_ten = 0.60 * 5.0 * PRESUMPTIVE_FC_PSI ** 0.5 * (12.0 * 10.0 ** 2 / 6.0) / 12.0
    on_twelve = 0.60 * 5.0 * PRESUMPTIVE_FC_PSI ** 0.5 * (12.0 * 12.0 ** 2 / 6.0) / 12.0
    assert toe.capacity == pytest.approx(on_ten, rel=0.001)
    assert on_twelve / on_ten == pytest.approx(1.44, rel=0.01)


def test_the_toe_takes_no_credit_for_the_footings_own_weight(geometry_and_case) -> None:
    """§7b's conservatism — the toe is designed for the upward pressure alone.

    Back-solved: the published demand is exactly 1.6x the trapezoid's moment about the stem
    face, with no 150 psf of concrete subtracted. Keeping that relief would mean factoring a
    *relieving* dead load, which ASCE 7 takes at 0.9 and this module cannot express.
    """
    from typehaus.engineering.retaining_basis import (
        EARTH_PRESSURE_LOAD_FACTOR,
        footing_states,
    )

    geometry, case = geometry_and_case
    q_face = _Q_TOE - (_Q_TOE - _Q_HEEL) / _WIDTH_FT * _TOE_FT
    pressure_only = (q_face * _TOE_FT ** 2 / 2.0
                     + 0.5 * (_Q_TOE - q_face) * _TOE_FT * (2.0 * _TOE_FT / 3.0))
    state = _state(footing_states(geometry, case), "toe flexure")
    assert state.demand == pytest.approx(
        EARTH_PRESSURE_LOAD_FACTOR * pressure_only, rel=0.002)

    # The size of the conservatism, stated so nobody removes it thinking it is noise: taking
    # the relief AT ITS PROPER 0.9 FACTOR (ASCE 7-16 §2.3.1 on a counteracting dead load)
    # would lighten the FACTORED demand by about 8%. Comparing service moments instead
    # overstates it at 13.5% — the factor is the whole point, so the comparison has to carry
    # it, and it is exactly the argument this conservatism exists to avoid having.
    relief_service = 150.0 * _DEPTH_FT * _TOE_FT ** 2 / 2.0
    proper = EARTH_PRESSURE_LOAD_FACTOR * pressure_only - 0.9 * relief_service
    assert proper / state.demand == pytest.approx(0.92, rel=0.02)


def test_the_heel_takes_no_credit_for_the_pressure_under_it(geometry_and_case) -> None:
    """§7c's mirror-image conservatism — the soil column and concrete alone.

    The heel's job is to hold a column of earth down, and the bearing pressure that would
    help is exactly the pressure that vanishes when the wall starts to rotate.
    """
    from typehaus.engineering.retaining_basis import (
        CONCRETE_UNIT_WEIGHT_PCF,
        EARTH_PRESSURE_LOAD_FACTOR,
        footing_states,
    )

    geometry, case = geometry_and_case
    stem_height_ft = geometry.retained_height_ft - _DEPTH_FT
    down = (_HEEL_FT * stem_height_ft * case.soil_pcf
            + _HEEL_FT * _DEPTH_FT * CONCRETE_UNIT_WEIGHT_PCF)
    state = _state(footing_states(geometry, case), "heel flexure")
    assert state.demand == pytest.approx(
        EARTH_PRESSURE_LOAD_FACTOR * down * _HEEL_FT / 2.0, rel=0.002)


def test_every_retaining_wall_in_the_court_carries_the_mat(catlin_plan) -> None:
    """All three court footings are authored alike — one bar size for the whole pour.

    ``FT-SG-W1``/``E1`` deliberately do NOT: they are braced top and bottom, IRC Table
    R404.1.2(8) answers them prescriptively, and neither has a toe worth grading.
    """
    from typehaus.model.structure import Footing

    footings = {f.tag: f for f in catlin_plan.all_elements() if isinstance(f, Footing)}
    for wall in _WALLS:
        spec = footings[f"FT-{wall[2:]}"].reinforcement
        assert spec is not None, f"FT-{wall[2:]} lost its mat"
        roles = {b.role: b for b in spec.bars}
        assert roles["bottom-x"].bar == 6
        assert roles["bottom-x"].spacing.inches == pytest.approx(10.0)
        assert roles["top-x"].bar == 6
        assert roles["top-x"].spacing.inches == pytest.approx(10.0)
        assert spec.cover.inches == pytest.approx(3.0)

    for braced in ("FT-SG-W1", "FT-SG-E1"):
        assert footings[braced].reinforcement is None


def test_a_bar_authored_as_a_count_is_not_read_as_a_spacing() -> None:
    """A strip footing is graded per foot of run, so "(4) #5" says nothing about a foot of it.

    The conservative contract ``parse_reinforcement`` keeps is kept here: anything unreadable
    is NO steel, never assumed steel.
    """
    from typehaus.engineering.retaining_basis import bar_for_roles
    from typehaus.model.rebar import BarSpec, ReinforcementSpec
    from typehaus.quantities import inch

    counted = ReinforcementSpec(bars=(BarSpec(role="bottom-x", bar=5, count=4),))
    assert bar_for_roles(counted, ("bottom-x",)) is None

    wrong_role = ReinforcementSpec(
        bars=(BarSpec(role="ties", bar=5, spacing=inch(10.0)),))
    assert bar_for_roles(wrong_role, ("bottom-x",)) is None

    assert bar_for_roles(None, ("bottom-x",)) is None
