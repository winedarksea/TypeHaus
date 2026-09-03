"""``structural.concrete_mix_matches_exposure`` — does the mix buy the class it claims?

Claiming F3 is free; buying F3 is not. A pour that says "class F3" over a 0.50 w/cm mix is a
specification a ready-mix plant will batch as written and that will not be F3 concrete, and
before this rule nothing in the repo compared the two halves.

The two assertions doing unusual work:

* :func:`test_a_class_with_no_air_is_not_a_freeze_thaw_class` pins the failure mode that
  looks most like success — an F3 mix at 5,000 psi and w/cm 0.40 with no air entrainment
  gets both headline numbers right and is not freeze-thaw concrete at any strength.
* :func:`test_not_applicable_is_earned` pins decision-doctrine: N/A needs positive evidence
  of absence. A model with concrete and no ``ConcreteSpec`` is UNKNOWN, because that is a gap
  in the model rather than an exposure the building does not have.
"""

from __future__ import annotations

import pytest

from typehaus.checks.structural.concrete_durability import _mix_problems
from typehaus.findings import Result
from typehaus.model.assembly import ConcreteSpec
from typehaus.quantities import inch


def _spec(**kwargs):
    base = dict(fc_psi=5000.0, w_cm_max=0.40, air_content_pct=6.0, air_tolerance_pct=1.5,
                max_aggregate=inch(0.75))
    return ConcreteSpec(**{**base, **kwargs})


def test_a_mix_that_delivers_its_class_is_silent() -> None:
    assert _mix_problems(_spec(exposure_f="F3", exposure_c="C2")) == []
    assert _mix_problems(_spec(fc_psi=4000.0, w_cm_max=0.45, air_content_pct=None,
                               air_tolerance_pct=None, exposure_f="F0",
                               exposure_w="W1", exposure_c="C1")) == []


def test_an_under_strength_mix_is_caught() -> None:
    problems = _mix_problems(_spec(fc_psi=4000.0, exposure_f="F3"))
    assert len(problems) == 1
    assert "4,000 psi against the 5,000 psi" in problems[0]


def test_an_over_wet_mix_is_caught() -> None:
    problems = _mix_problems(_spec(w_cm_max=0.50, exposure_c="C2"))
    assert len(problems) == 1 and "0.50 against the 0.40 cap" in problems[0]


def test_an_unstated_w_cm_is_not_a_low_one() -> None:
    """The quiet one. A class that caps w/cm and a spec that states none is not compliant by
    default — a plant batches to whatever it likes within the strength it was given."""
    problems = _mix_problems(_spec(w_cm_max=None, exposure_f="F3"))
    assert len(problems) == 1 and "states none" in problems[0]


def test_a_class_with_no_air_is_not_a_freeze_thaw_class() -> None:
    """5,000 psi and w/cm 0.40 with no entrained air gets both headline numbers right and is
    still not F3 concrete. Entrained air IS the freeze-thaw mechanism; strength is not a
    substitute for it at any value."""
    problems = _mix_problems(_spec(air_content_pct=None, air_tolerance_pct=None,
                                   exposure_f="F3"))
    assert len(problems) == 1
    assert "air entrainment is its mechanism" in problems[0]


def test_too_little_air_is_caught_only_at_a_known_aggregate() -> None:
    """Table 19.3.3.1's target moves with the nominal maximum aggregate, so a house that
    specifies a different size is left alone rather than graded against the wrong row."""
    assert _mix_problems(_spec(air_content_pct=4.0, air_tolerance_pct=0.5,
                               exposure_f="F3"))
    assert _mix_problems(_spec(air_content_pct=4.0, air_tolerance_pct=0.5,
                               max_aggregate=inch(1.5), exposure_f="F3")) == []


def test_the_strictest_of_several_classes_governs() -> None:
    """A pour is simultaneously some F, some S, some W and some C — that is why they are four
    fields and not one. The mix has to satisfy all of them, so the tightest cap wins."""
    # C2 wants 5,000/0.40; W1 alone would be happy at 4,000/0.50.
    problems = _mix_problems(_spec(fc_psi=4000.0, w_cm_max=0.50,
                                   exposure_w="W1", exposure_c="C2"))
    assert len(problems) == 2
    assert any("5,000 psi" in p for p in problems)
    assert any("0.40 cap" in p for p in problems)


def test_every_problem_is_reported_not_just_the_first() -> None:
    """An under-strength, over-wet, unentrained F3 mix has three things wrong with it, and
    fixing one at a time across three runs of the checker is how the other two get lost."""
    problems = _mix_problems(_spec(fc_psi=3000.0, w_cm_max=0.55, air_content_pct=None,
                                   air_tolerance_pct=None, exposure_f="F3"))
    assert len(problems) == 3


def test_claiming_no_class_at_all_is_silence() -> None:
    """The engine has no honest way to decide what class a pour SHOULD be — see the module
    docstring on the geometric version of this rule, which fired 45 times on correct pours
    before it was cut. So an unstated class is neither a pass nor a failure here."""
    assert _mix_problems(_spec()) == []


def test_catlin_is_clean(catlin_plan) -> None:
    from typehaus.checks.structural.concrete_durability import concrete_mix_matches_exposure

    class _Ctx:
        plan = catlin_plan

    findings = concrete_mix_matches_exposure(_Ctx())
    assert not [f for f in findings if f.result is Result.FAIL], \
        [f.message for f in findings if f.result is Result.FAIL]
    assert any(f.result is Result.PASS for f in findings)


def test_not_applicable_is_earned(catlin_plan) -> None:
    """N/A needs positive evidence of absence (decision #66 doctrine).

    A model with concrete pours but no ``ConcreteSpec`` on any of them is UNKNOWN — that is a
    gap in the model, not an exposure the building does not have. Only a model with no pour
    in scope at all earns N/A.
    """
    from typehaus.checks.structural.concrete_durability import concrete_mix_matches_exposure

    class _Empty:
        class plan:
            @staticmethod
            def all_elements():
                return []
    findings = concrete_mix_matches_exposure(_Empty())
    assert len(findings) == 1 and findings[0].result is Result.NOT_APPLICABLE

    pours = [el for el in catlin_plan.all_elements()
             if el.element_kind in ("Footing", "Slab") and getattr(el, "assembly", None)]
    assert pours, "catlin has assembly-bearing pours; this test proves nothing if not"

    class _NoSpecs:
        class plan:
            library = catlin_plan.library

            @staticmethod
            def all_elements():
                return [p.model_copy(update={"assembly": "GARAGE_WALL_2X6"}) for p in pours]

    findings = concrete_mix_matches_exposure(_NoSpecs())
    assert len(findings) == 1 and findings[0].result is Result.UNKNOWN
    assert "gap in the model" in findings[0].message


def test_the_table_is_aci_318_19_table_19_3_2_1() -> None:
    """Spot-checked against the published table rather than against itself."""
    from typehaus.checks.structural.concrete_durability import _TABLE_19_3_2_1

    assert _TABLE_19_3_2_1["F3"] == (0.40, 5000.0)
    assert _TABLE_19_3_2_1["C2"] == (0.40, 5000.0)
    assert _TABLE_19_3_2_1["W1"] == (0.50, 4000.0)
    assert _TABLE_19_3_2_1["S1"] == (0.50, 4000.0)
    # The four "0" classes impose no w/cm cap and only §19.2.1.1's 2,500 psi floor.
    for cls in ("F0", "S0", "W0", "C0"):
        assert _TABLE_19_3_2_1[cls] == (None, 2500.0)
    assert pytest.approx(_TABLE_19_3_2_1["C1"][1]) == 2500.0
