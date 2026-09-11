"""``engineering/spread_footing.py``'s SECTION states against §5 of the hand-worked note.

The oracle is ``houses/catlin/notes/sunken_garden_piers.md`` §5, worked by hand in a separate
pass — the discipline every calc in ``engineering/`` is held to. §3's bearing states live in
``test_pier_calcs.py``; these are deliberately a separate module because they arrived in a
separate change and the two were being edited concurrently.

The three assertions doing unusual work:

* :func:`test_the_effective_thickness_gives_up_two_inches` pins ACI 318-19 §14.5.1.7, the
  provision this derivation is most likely to lose. Flexural capacity goes as ``h**2``, so
  grading a 12" bell on 12" instead of 10" overstates the section by 44% — silently, in the
  unconservative direction, and with every other term still correct.
* :func:`test_one_way_shear_reports_a_section_that_does_not_exist` pins a state whose critical
  section falls OUTSIDE the footing. The temptation is to omit it; a limit state silently
  absent reads as one nobody thought of, where a published zero says the question was asked.
* :func:`test_the_bell_carries_none_of_its_own_weight_into_these_states` pins the one place
  this module deliberately disagrees with the bearing check three lines above it. Bearing
  includes the bell's self-weight because that is exactly what the soil feels; punching and
  flexure exclude it, because a footing does not punch itself.
"""

from __future__ import annotations

import math

import pytest

# §5b-§5e of the note, worked by hand. Demands in lb (shear) and lb-in (flexure).
#
# REVISED 2026-09-05: `_pier_bell_bottom_ft` is derived from the 42"-below-the-court rule
# again rather than pinned where the flood step left it, so both shafts are 7 1/4" shorter,
# each sheds 71 lb of its own concrete, and P_u falls 0.8%. Every DEMAND here is a net soil
# pressure times a geometry that did not move, so all four fall by that same 0.8% and no
# capacity changes at all. If one of them ever moves on its own, the geometry moved too.
_ORACLE = {
    # ** BOTH BELLS ARE 36" SINCE 2026-09-10 AND THESE TWO ROWS ARE NOW TWINS. **
    # PT-SG-COL's was 30", which was not set by anything — 36" was a fossil from a 20"
    # column and 30" was simply the other one. Standardising removes a width, an
    # under-reamer setting and a schedule row for ~0.09 cy of concrete, and takes the
    # tightest pier in the house from 0.83 to 0.60 on bearing.
    #
    # The two rows differ only in the fourth significant figure of the demands, and that
    # residue is real rather than noise: PT-SG-COL carries 1.2 lb more dead load than
    # PT-SG-FCOL (a beam-weighted tributary share, §2). Keeping both rows rather than
    # collapsing them to one is deliberate — if they ever diverge further, something moved.
    "PT-SG-COL": {
        "bell_in": 36.0,
        "pressure_psi": 10.585,
        "punching_demand": 6267.0,
        "punching_capacity": 93150.0,
        "one_way_demand": 364.0,
        "one_way_capacity": 10696.0,
        "flexure_demand": 17856.0,
        "flexure_capacity": 121599.0,
    },
    "PT-SG-FCOL": {
        "bell_in": 36.0,
        "pressure_psi": 10.583,
        "punching_demand": 6266.0,
        "punching_capacity": 93150.0,
        "one_way_demand": 364.0,
        "one_way_capacity": 10696.0,
        "flexure_demand": 17854.0,
        "flexure_capacity": 121599.0,
    },
}

# REVISED 2026-09-03 (later the same day) for the beam-weighted tributary. Every DEMAND here
# rose 2.8%, and by exactly the same factor on both piers, because every one of them is a net
# soil pressure times a geometry that did not move: the tributary went 116.97 -> 120.83 ft²
# when a deck beam's share stopped being "the deck area over its post count". No capacity
# changed. See notes/sunken_garden_piers.md §2.
#
# §5a: both bells name PIER_BASE_12 -> BURIED_MIX as of 2026-09-03. Every
# capacity in §5c-§5e goes as sqrt(f'c), so all of them are 29.1% larger than the figures this
# oracle carried while the bells named no assembly and the engine substituted 3,000 psi. The
# demands are unchanged: soil pressure does not care what the concrete is.
_ROOT_FC = math.sqrt(5000.0)


@pytest.fixture(scope="module")
def records(catlin_plan):
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.engineering.spread_footing import compute
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    ctx = EngineeringContext(plan=catlin_plan, model=model, soil_class="GM")
    return {record.key: record for record in compute(ctx)}


def _state(record, name):
    found = [s for s in record.limit_states if s.name == name]
    assert found, f"{record.key} publishes no {name!r} state; it has " \
                  f"{[s.name for s in record.limit_states]}"
    return found[0]


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_punching_shear_reproduces_the_note(tag, records) -> None:
    """§5c, term by term. Two errors can cancel inside a d/c ratio."""
    want = _ORACLE[tag]
    state = _state(records[tag], "two-way (punching) shear")
    assert state.demand == pytest.approx(want["punching_demand"], rel=0.001)
    assert state.capacity == pytest.approx(want["punching_capacity"], rel=0.001)
    assert state.ok


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_flexure_reproduces_the_note(tag, records) -> None:
    """§5e — the segment area, its centroid ABOUT THE CUT, and ``S_m = b h**2 / 6``.

    The arm is the term to watch: the segment centroid comes out measured from the circle's
    centre and the moment is taken about the column face, so a derivation that forgets to
    subtract the half-side is 30% high on ``PT-SG-COL`` and still looks plausible.
    """
    want = _ORACLE[tag]
    state = _state(records[tag], "flexure at the column face")
    assert state.demand == pytest.approx(want["flexure_demand"], rel=0.001)
    assert state.capacity == pytest.approx(want["flexure_capacity"], rel=0.001)
    assert state.ok


def test_one_way_shear_reproduces_the_note(records) -> None:
    """§5d, on BOTH bells since 2026-09-10.

    It used to run on PT-SG-FCOL alone, because at 30" PT-SG-COL's critical section at
    ``h`` from the column face landed 15.32" out on a 15" radius and there was no section
    to check. Standardising both bells at 36" gives that pier a real one.
    """
    for tag in ("PT-SG-FCOL", "PT-SG-COL"):
        want = _ORACLE[tag]
        state = _state(records[tag], "one-way shear")
        assert state.demand == pytest.approx(want["one_way_demand"], rel=0.02), tag
        assert state.capacity == pytest.approx(want["one_way_capacity"], rel=0.001), tag
        assert state.ok, tag


def test_a_degenerate_one_way_section_is_published_and_not_omitted(catlin_plan) -> None:
    """A state that vanishes when its geometry degenerates is indistinguishable from one
    nobody wrote, which is precisely the failure an engineering register exists to prevent.

    **There is no degenerate bell in this house any more**, and that is why this test now
    drives the calculation directly instead of reading PT-SG-COL's record. At 30" its
    critical section at ``h`` from the column face fell 15.32" out on a 15" radius and the
    engine published a zero-demand state citing OUTSIDE; at 36" it has a real section.
    Deleting the test with the geometry would have retired the behaviour it guards, which
    is exactly the kind of silent loss it exists to catch — the next 30" bell on any house
    must still get a published state rather than a missing one.
    """
    import dataclasses

    from typehaus.engineering.registry import EngineeringContext
    from typehaus.engineering.spread_footing import _piers_on_their_own_footing, _section_states
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    ctx = EngineeringContext(plan=catlin_plan, model=model, soil_class="GM")
    pier = next(p for p in _piers_on_their_own_footing(ctx) if p.tag == "PT-SG-COL")
    assert pier.footing_width_in == 36.0, "the live bell is 36\"; this test narrows a copy"
    narrow = dataclasses.replace(pier, footing_width_in=30.0)

    states, _notes = _section_states(ctx, narrow)
    shear = [state for state in states if state.name == "one-way shear"]
    assert shear, 'a 30" bell must still PUBLISH a one-way shear state'
    assert shear[0].demand == 0.0
    assert "OUTSIDE" in shear[0].citation
    assert shear[0].ok


def test_the_effective_thickness_gives_up_two_inches(records) -> None:
    """ACI 318-19 §14.5.1.7 — a plain footing cast against soil is graded on ``h - 2``.

    Checked through the flexural capacity rather than by reading a constant, because that is
    where the error would actually show: ``S_m`` goes as ``h**2``, so a 12" bell graded on 12"
    reports 44% more capacity than it has.
    """
    from typehaus.engineering.spread_footing import (
        PHI_PLAIN,
        PLAIN_SOIL_CAST_DEDUCTION_IN,
    )

    assert PLAIN_SOIL_CAST_DEDUCTION_IN == 2.0
    state = _state(records["PT-SG-COL"], "flexure at the column face")
    # §5e: the chord across the bell at the column face, and the 10" the deduction leaves
    # of a 12" bell. 34.39" on the 36" bell both piers have carried since 2026-09-10 (it
    # was 28.05" while PT-SG-COL's was 30"): the critical section stands half a 12" round's
    # equivalent square out, 5.317", so the chord is 2*sqrt(18^2 - 5.317^2).
    expected = PHI_PLAIN * 5.0 * _ROOT_FC * 34.394 * 10.0 ** 2 / 6.0
    assert state.capacity == pytest.approx(expected, rel=0.001)
    ungraded = PHI_PLAIN * 5.0 * _ROOT_FC * 34.394 * 12.0 ** 2 / 6.0
    assert ungraded / expected == pytest.approx(1.44, rel=0.01)


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_the_bell_carries_none_of_its_own_weight_into_these_states(tag, records) -> None:
    """The net pressure is ``P_u / A_bell`` — the bell's own weight is NOT in it.

    The bearing state one line above deliberately DOES include it. Both are right: bearing
    asks what the soil feels, and these ask what crosses a critical section inside the
    concrete. Reconciling them by "fixing" one to match the other is the regression here, and
    it moves every demand in this module by about a tenth.
    """
    record = records[tag]
    want = _ORACLE[tag]
    area_in2 = math.pi * (want["bell_in"] / 2.0) ** 2
    # The critical square at h/2 from a 12" round's equivalent-square face (§5c).
    inside_in2 = (2.0 * (math.sqrt(math.pi * 12.0 ** 2 / 4.0) / 2.0 + 5.0)) ** 2

    # The published demand back-solves to P_u / A, not to (P_u + bell weight) / A.
    state = _state(record, "two-way (punching) shear")
    assert state.demand / (area_in2 - inside_in2) == pytest.approx(
        want["pressure_psi"], rel=0.001)
    assert any("does not punch itself" in note for note in record.notes)

    # And the bearing state on the same record still DOES include it, which is the whole
    # point. Back-solve it: bearing x area must return the service load PLUS the bell's own
    # 150 pcf, and must exceed the service load alone by exactly that.
    inputs = {q.name: q.value for q in record.inputs}
    service_lb = inputs["dead_load"] + inputs["live_load"]
    area_ft2 = area_in2 / 144.0
    bell_weight_lb = area_ft2 * 1.0 * 150.0            # a 12"-thick bell at 150 pcf
    bearing = _state(record, "bearing")
    assert bearing.demand == pytest.approx(
        (service_lb + bell_weight_lb) / area_ft2, rel=0.001)
    assert bearing.demand - service_lb / area_ft2 == pytest.approx(150.0, rel=0.001)
