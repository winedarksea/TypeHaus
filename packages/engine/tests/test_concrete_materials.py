"""``checks/structural/concrete_materials.py``: chloride, SCM caps, sulfate cement, ASR, chromate.

The tables are pinned against the published values (ACI 318-19 Tables 19.3.2.1 and
26.4.2.2(b), ASTM C1778 Tables 2 and 3), not against themselves. Every unauthored input
must grade UNKNOWN.
"""

from __future__ import annotations

import pytest

from typehaus.checks.structural import concrete_materials as cm
from typehaus.findings import Result
from typehaus.model import AsrSpec, CementSpec, ConcreteSpec, ScmFractions


def _spec(**kwargs):
    base = dict(fc_psi=5000.0, w_cm_max=0.40, exposure_f="F3", exposure_w="W1",
                exposure_c="C2")
    return ConcreteSpec(**{**base, **kwargs})


def _scm(fly=0.0, slag=0.0, fume=0.0, blended=False):
    return ScmFractions(fly_ash_pct=fly, slag_pct=slag, silica_fume_pct=fume,
                        includes_blended_cement=blended)


_C150 = CementSpec(standard="ASTM C150", designation="I/II")


def test_the_tables_are_the_published_ones() -> None:
    assert cm.CHLORIDE_LIMIT_PCT == {"C0": 1.00, "C1": 0.30, "C2": 0.15}
    assert (cm.F3_FLY_ASH_MAX, cm.F3_SLAG_MAX, cm.F3_SILICA_FUME_MAX) == (25.0, 50.0, 10.0)
    assert (cm.F3_FLY_ASH_PLUS_SF_MAX, cm.F3_TOTAL_MAX) == (35.0, 50.0)
    assert cm.ASR_RISK["humid_or_buried"] == (1, 3, 4, 5)
    assert cm.ASR_RISK["alkalis_in_service"] == (1, 4, 5, 6)
    assert cm.ASR_PREVENTION[3] == ("V", "W", "X", "Y")
    assert cm.ASR_PREVENTION[6] == ("Y", "Z", "ZZ", None)


def test_the_w_rows_are_318_19s_not_318_14s() -> None:
    from typehaus.checks.structural.concrete_durability import _TABLE_19_3_2_1
    assert _TABLE_19_3_2_1["W1"] == (None, 2500.0)
    assert _TABLE_19_3_2_1["W2"] == (0.50, 4000.0)


@pytest.mark.parametrize("pct,result", [(None, Result.UNKNOWN), (0.15, Result.PASS),
                                        (0.20, Result.FAIL)])
def test_chloride_against_c2(pct, result) -> None:
    assert cm._chloride(_spec(chloride_ion_max_pct=pct))[0] is result


def test_chloride_limit_follows_the_class() -> None:
    assert cm._chloride(_spec(exposure_c="C1", chloride_ion_max_pct=0.20))[0] is Result.PASS


def test_scm_caps() -> None:
    assert cm._scm(_spec())[0] is Result.UNKNOWN
    assert cm._scm(_spec(scm_fractions=_scm(fly=25.0), cement=_C150))[0] is Result.PASS
    over = cm._scm(_spec(scm_fractions=_scm(fly=30.0), cement=_C150))
    assert over[0] is Result.FAIL and "25% cap" in over[1]
    assert cm.scm_problems(_scm(fly=20.0, fume=10.0)) == []       # pair 30, under 35
    assert cm.scm_problems(_scm(fly=25.0, fume=10.0)) == []       # pair 35 is AT the cap
    assert cm.scm_problems(_scm(fly=20.0, slag=35.0))              # total 55, over 50


def test_scm_needs_the_cement_because_a_blend_carries_its_own() -> None:
    """Fractions within the caps still grade UNKNOWN until the cement is named, and a
    blended cement must say its own SCM is counted."""
    assert cm._scm(_spec(scm_fractions=_scm(fly=20.0)))[0] is Result.UNKNOWN
    ip = CementSpec(standard="ASTM C595", designation="IP(MS)")
    assert cm._scm(_spec(scm_fractions=_scm(fly=20.0), cement=ip))[0] is Result.UNKNOWN
    assert cm._scm(_spec(scm_fractions=_scm(fly=20.0, blended=True),
                         cement=ip))[0] is Result.PASS
    il = CementSpec(standard="ASTM C595", designation="IL")
    assert cm._scm(_spec(scm_fractions=_scm(fly=20.0), cement=il))[0] is Result.PASS


@pytest.mark.parametrize("cls,standard,designation,result", [
    ("S0", None, None, Result.PASS),
    ("S1", None, None, Result.UNKNOWN),
    ("S1", "ASTM C150", "II", Result.PASS),
    ("S1", "ASTM C150", "I", Result.UNKNOWN),       # only below 8% C3A, not modelled
    ("S2", "ASTM C150", "II", Result.FAIL),
    ("S2", "ASTM C150", "II/V", Result.PASS),
    ("S1", "ASTM C595", "IL(MS)", Result.PASS),
    ("S2", "ASTM C595", "IL(MS)", Result.FAIL),
    ("S2", "ASTM C1157", "HS", Result.PASS),
    ("S2", "ASTM C1157", "GU", Result.FAIL),
])
def test_sulfate_cement(cls, standard, designation, result) -> None:
    cement = CementSpec(standard=standard, designation=designation) if standard else None
    assert cm._sulfate(_spec(exposure_s=cls, cement=cement))[0] is result


def test_s3_needs_option_2_or_a_pozzolan() -> None:
    hs = CementSpec(standard="ASTM C1157", designation="HS")
    assert cm._sulfate(_spec(exposure_s="S3", cement=hs))[0] is Result.PASS  # 0.40 / 5,000
    weaker = dict(w_cm_max=0.45, fc_psi=4500.0, exposure_s="S3", cement=hs)
    assert cm._sulfate(_spec(**weaker))[0] is Result.UNKNOWN
    assert cm._sulfate(_spec(**weaker, scm_fractions=_scm(fly=20.0)))[0] is Result.PASS


def test_asr() -> None:
    assert cm._asr(_spec())[0] is Result.UNKNOWN
    assert cm._asr(_spec(asr=AsrSpec(aggregate_class="R0")))[0] is Result.PASS
    assert cm._asr(_spec(asr=AsrSpec(aggregate_class="R1")))[0] is Result.UNKNOWN
    # C2 is deicing salt: the "alkalis in service" row. R1 -> risk 4; S2 -> X.
    r1 = AsrSpec(aggregate_class="R1", structure_class="S2", prevention_level="W")
    graded = cm._asr(_spec(asr=r1))
    assert graded[0] is Result.FAIL and "risk level 4 needs prevention X" in graded[1]
    # The same aggregate under C1 is the humid row: risk 3 -> W on S2.
    assert cm._asr(_spec(exposure_c="C1", asr=r1))[0] is Result.PASS
    r3 = AsrSpec(aggregate_class="R3", structure_class="S4", prevention_level="ZZ")
    assert cm._asr(_spec(asr=r3))[0] is Result.FAIL        # risk 6 on S4: not permitted


def test_chromate() -> None:
    assert cm._chromate(_spec(bar_coating="hdg-a767"))[0] is Result.UNKNOWN
    for treatment in ("passivated", "waived"):
        spec = _spec(bar_coating="hdg-a1094", chromate_treatment=treatment)
        assert cm._chromate(spec)[0] is Result.PASS


def test_not_applicable_is_earned() -> None:
    """Every mix states its C/F/W class and bar coating and none triggers: N/A. A mix that
    states none of them is silence, and silence everywhere is UNKNOWN."""
    class _Pour:
        tag, element_kind, assembly = "SL-X", "Slab", "A"

    def ctx(spec):
        class _Library:
            @staticmethod
            def resolve_assembly(_tag):
                from typehaus.model import Assembly, Layer
                from typehaus.model.enums import LayerFunction
                from typehaus.quantities import inch
                return Assembly(tag="A", layers=(Layer(
                    name="c", material_ref="concrete", thickness=inch(4.0),
                    function=LayerFunction.STRUCTURE, concrete=spec),))

        class _Plan:
            library = _Library()

            @staticmethod
            def all_elements():
                return [_Pour()]

        class _Ctx:
            plan = _Plan()
        return _Ctx()

    dry = ConcreteSpec(fc_psi=4000.0, exposure_f="F0", exposure_w="W0", bar_coating="black")
    for rule in (cm.concrete_scm_caps, cm.concrete_asr, cm.galvanized_bar_chromate):
        (finding,) = rule(ctx(dry))
        assert finding.result is Result.NOT_APPLICABLE, finding.message
    bare = ConcreteSpec(fc_psi=4000.0)
    for rule in (cm.concrete_scm_caps, cm.concrete_asr, cm.galvanized_bar_chromate,
                 cm.concrete_chloride_limit, cm.concrete_sulfate_cement):
        (finding,) = rule(ctx(bare))
        assert finding.result is Result.UNKNOWN, finding.message


def test_catlin(catlin_plan) -> None:
    """Catlin authors chromate (passivated) and its SCM fractions; the cement, chloride,
    sulfate class and aggregate reactivity are unsourced and stay UNKNOWN."""
    class _Ctx:
        plan = catlin_plan

    assert all(f.result is Result.PASS for f in cm.galvanized_bar_chromate(_Ctx()))
    for rule in (cm.concrete_chloride_limit, cm.concrete_scm_caps, cm.concrete_asr,
                 cm.concrete_sulfate_cement):
        findings = rule(_Ctx())
        assert findings and all(f.result is Result.UNKNOWN for f in findings)
    (scm,) = cm.concrete_scm_caps(_Ctx())
    assert "cement is not named" in scm.message
