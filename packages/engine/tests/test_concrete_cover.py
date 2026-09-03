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
