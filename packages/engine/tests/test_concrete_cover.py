"""Clear cover: who states it, who wins, and what the minimum is.

``resolve/concrete.cover_for`` is the one reduction from an element to the cover its bar
actually gets. The precedence it fixes was a live defect: every calc read
``ConcreteSpec.cover`` and **nothing read ``ReinforcementSpec.cover``**, so the 2" authored
on catlin's three retaining stems was inert. It went unnoticed because the ACI table
fallback returns 2" for a #6 as well — the number was right and the reason was not, which is
the failure mode a calc that only agrees with itself is built to hide.

:func:`test_the_schedule_outranks_the_mix` is the one that matters: cover is a property of a
FACE, a mix is one ticket serving many faces, and a footing cast against soil and the formed
stem standing on it do not want the same figure.
"""

from __future__ import annotations

import pytest

from typehaus.model.assembly import ConcreteSpec
from typehaus.model.rebar import BarSpec, ReinforcementSpec
from typehaus.quantities import inch
from typehaus.resolve.concrete import cover_for


class _Plan:
    """A plan whose library resolves exactly one assembly, to whatever spec is handed in."""

    def __init__(self, spec: ConcreteSpec | None) -> None:
        outer = self

        class _Library:
            @staticmethod
            def resolve_assembly(tag: str):
                if tag != "MIX" or outer.spec is None:
                    return None
                return _Assembly(outer.spec)

        self.spec = spec
        self.library = _Library()


class _Assembly:
    def __init__(self, spec: ConcreteSpec) -> None:
        from typehaus.model.assembly import Layer, LayerFunction
        self.layers = (Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
                             function=LayerFunction.STRUCTURE, concrete=spec),)

    def structure_index(self) -> int:
        return 0


class _Element:
    def __init__(self, assembly: str | None, reinforcement=None) -> None:
        self.assembly = assembly
        self.reinforcement = reinforcement


def _schedule(cover_inches: float) -> ReinforcementSpec:
    return ReinforcementSpec(
        bars=(BarSpec(role="vertical", bar=6, spacing=inch(10.0)),),
        cover=inch(cover_inches))


_MIX = ConcreteSpec(fc_psi=5000.0, cover=inch(3.0))


def test_the_schedule_outranks_the_mix() -> None:
    """The defect this function exists to fix, stated as an assertion.

    A basement wall on the buried mix used to take that mix's cast-against-earth 3" onto a
    FORMED face. The wall's own schedule says 2" and is the only place a per-face figure can
    be written at all, so it governs.
    """
    plan = _Plan(_MIX)
    got, why = cover_for(plan, _Element("MIX", _schedule(2.0)))
    assert got == pytest.approx(2.0)
    assert why == "its reinforcement schedule"


def test_the_mix_is_the_fallback_not_the_authority() -> None:
    plan = _Plan(_MIX)
    got, why = cover_for(plan, _Element("MIX"))
    assert got == pytest.approx(3.0) and why == "its mix"


def test_neither_stated_is_None_and_not_a_default() -> None:
    """``None`` is "this model does not say", which the caller reports as the ACI table
    minimum *and names as such* in its citation. Collapsing it to a number here would erase
    the difference between a cover somebody chose and one nobody did."""
    assert cover_for(_Plan(None), _Element(None)) == (None, None)
    assert cover_for(_Plan(ConcreteSpec(fc_psi=4000.0)), _Element("MIX")) == (None, None)


def test_catlins_retaining_stems_now_read_their_own_schedule(catlin_plan, catlin_model) -> None:
    """End to end on the real house: the 2" that used to be inert.

    Asserted through the calc's own citation rather than through ``cover_for`` again, because
    the bug was never in the reduction — it was that the calc did not call one.
    """
    from typehaus.engineering import EngineeringContext, EngineeringResults

    results = EngineeringResults(EngineeringContext(
        plan=catlin_plan, model=catlin_model, soil_class="GM"))
    stem = next(s for s in results["retaining_wall/W-SG-E2"].limit_states
                if s.name == "stem flexure")
    assert "none specified" not in stem.citation, (
        "the stem is still falling back to the ACI table: _RET_STEM_STEEL.cover is inert "
        "again. See resolve/concrete.cover_for.")


# ---------------------------------------------------------------------------------------
# structural.concrete_cover_meets_minimum — ACI 318-19 Table 20.5.1.3.1
# ---------------------------------------------------------------------------------------

from typehaus.checks.structural.concrete_cover import (  # noqa: E402
    _is_exposed,
    _required_cover_in,
    concrete_cover_meets_minimum,
)
from typehaus.findings import Result  # noqa: E402


class _Pour:
    def __init__(self, kind: str, tag: str, bars: tuple[int, ...], cover: float | None,
                 assembly: str | None = "MIX") -> None:
        self.element_kind, self.tag, self.assembly = kind, tag, assembly
        self.reinforcement = ReinforcementSpec(
            bars=tuple(BarSpec(role="vertical", bar=b, spacing=inch(12.0)) for b in bars),
            cover=None if cover is None else inch(cover))


_WET = ConcreteSpec(fc_psi=5000.0, exposure_f="F3", exposure_w="W1", exposure_c="C2")
_DRY = ConcreteSpec(fc_psi=4000.0, exposure_f="F0", exposure_w="W0", exposure_c="C0")


def test_the_table_is_aci_318_19_table_20_5_1_3_1() -> None:
    """The four rows, spot-checked against the published table rather than against itself."""
    assert _required_cover_in(_Pour("Footing", "F", (6,), 3.0), _WET, _Pour(
        "Footing", "F", (6,), 3.0).reinforcement)[0] == pytest.approx(3.0)
    wall6 = _Pour("FoundationWall", "W", (6,), 2.0)
    wall5 = _Pour("FoundationWall", "W", (5,), 1.5)
    assert _required_cover_in(wall6, _WET, wall6.reinforcement)[0] == pytest.approx(2.0)
    assert _required_cover_in(wall5, _WET, wall5.reinforcement)[0] == pytest.approx(1.5)
    assert _required_cover_in(wall6, _DRY, wall6.reinforcement)[0] == pytest.approx(0.75)
    col = _Pour("Post", "P", (5,), 1.5)
    assert _required_cover_in(col, _DRY, col.reinforcement)[0] == pytest.approx(1.5)


def test_the_largest_bar_governs_row_two() -> None:
    """Row 2's threshold moves at #6. A schedule graded on its smallest bar is graded on the
    one that does not govern — #4 ties around #6 verticals still want 2"."""
    mixed = _Pour("FoundationWall", "W", (4, 6), 2.0)
    assert _required_cover_in(mixed, _WET, mixed.reinforcement)[0] == pytest.approx(2.0)


def test_an_unset_exposure_is_not_a_zero_class() -> None:
    """The quiet one, and it is catlin's real case: all three of its mixes leave
    ``exposure_s`` unset on purpose, because nobody has run a soil sulfate test. Reading an
    unset field as S0 would turn "nobody measured" into "measured and clean"."""
    assert _is_exposed(ConcreteSpec(fc_psi=4000.0, exposure_w="W1")) is True
    assert _is_exposed(_DRY) is False
    # Nothing declared at all is not evidence of a dry pour either — but it is also not
    # evidence of a wet one, and row 3 is the lenient row, so this cannot produce a false FAIL.
    assert _is_exposed(ConcreteSpec(fc_psi=4000.0)) is False


def _findings(pours, spec=_WET):
    class _Ctx:
        class plan:
            library = _Plan(spec).library

            @staticmethod
            def all_elements():
                return pours
    return concrete_cover_meets_minimum(_Ctx())


def test_short_cover_is_a_fail_that_names_both_numbers() -> None:
    findings = _findings([_Pour("FoundationWall", "W-X", (6,), 1.5)])
    fails = [f for f in findings if f.result is Result.FAIL]
    assert len(fails) == 1
    assert '1.50"' in fails[0].message and '2.00"' in fails[0].message


def test_an_unstated_cover_fails_rather_than_defaulting() -> None:
    """The failure mode with no symptom. A reinforced pour that names no cover is not a pour
    at the minimum — it is the one dimension a placer sets by eye if nobody writes it down."""
    fails = [f for f in _findings([_Pour("FoundationWall", "W-X", (6,), None)])
             if f.result is Result.FAIL]
    assert len(fails) == 1 and "states no clear cover anywhere" in fails[0].message


def test_a_pour_with_no_mix_is_left_to_the_other_two_rules() -> None:
    """Not graded here, and deliberately: an unclassifiable pour is
    ``integrity.element_assembly``'s and ``concrete_mix_matches_exposure``'s subject, and two
    rules reporting one gap is how a fix gets counted twice. A Footing is the exception —
    its row does not depend on a declared exposure."""
    findings = _findings([_Pour("FoundationWall", "W-X", (6,), 0.5, assembly=None)],
                         spec=None)
    assert not [f for f in findings if f.result is Result.FAIL]
    assert [f for f in findings if f.result is Result.NOT_APPLICABLE]


def test_not_applicable_is_earned() -> None:
    findings = _findings([])
    assert len(findings) == 1 and findings[0].result is Result.NOT_APPLICABLE


def test_catlin_is_clean(catlin_plan) -> None:
    class _Ctx:
        plan = catlin_plan

    findings = concrete_cover_meets_minimum(_Ctx())
    assert not [f for f in findings if f.result is Result.FAIL], \
        [f.message for f in findings if f.result is Result.FAIL]
    assert any(f.result is Result.PASS for f in findings)
