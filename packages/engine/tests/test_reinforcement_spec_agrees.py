"""``integrity.reinforcement_spec_agrees`` — the rule that makes two spellings safe.

A concrete pour may state its steel twice: as free text for the drawing
(``vertical_reinforcement``) and as a structured ``ReinforcementSpec`` the engineering suite
grades. Keeping both is what let catlin migrate pour by pour instead of in one sweep. The
cost of keeping both is that they can drift apart silently — the calc reads the struct and
passes, the drawing prints the string, and the two go to site together. This rule is the
thing that stops that, so it is an ERROR and not an advisory.

The subtle half is what is NOT a disagreement: an unreadable string means "no steel stated
here", which is the conservative contract both parsers already keep. Reporting that as a
conflict would punish a house for writing prose.
"""

from __future__ import annotations

import pytest

from typehaus.checks.integrity.checks import reinforcement_spec_agrees
from typehaus.findings import Result, Severity
from typehaus.model.rebar import BarSpec, ReinforcementSpec
from typehaus.quantities import inch


class _Element:
    """The three attributes the rule reads. A real Post/FoundationWall is frozen and needs a
    node graph; this rule touches neither."""

    def __init__(self, kind, tag, text=None, spec=None):
        self.element_kind, self.tag = kind, tag
        self.vertical_reinforcement, self.reinforcement = text, spec


class _Ctx:
    def __init__(self, *elements):
        self.plan = self
        self._elements = elements

    def all_elements(self):
        return self._elements


def _wall(text, spec):
    return _Element("FoundationWall", "W-TEST", text, spec)


def _mat(role, bar, spacing_in=None, count=None):
    spacing = inch(spacing_in) if spacing_in is not None else None
    return ReinforcementSpec(bars=(BarSpec(role=role, bar=bar, spacing=spacing,
                                           count=count),))


def test_agreement_is_silent() -> None:
    ctx = _Ctx(_wall('#6 @ 10" o.c.', _mat("vertical", 6, spacing_in=10.0)))
    assert reinforcement_spec_agrees(ctx) == []


@pytest.mark.parametrize("text,spec", [
    ('#6 @ 10" o.c.', _mat("vertical", 5, spacing_in=10.0)),   # wrong bar
    ('#6 @ 10" o.c.', _mat("vertical", 6, spacing_in=12.0)),   # wrong spacing
])
def test_a_disagreement_is_an_ERROR(text, spec) -> None:
    """Severity matters: this is a drawing that contradicts a calculation, and the only
    thing standing between it and site is this rule."""
    findings = reinforcement_spec_agrees(_Ctx(_wall(text, spec)))
    assert len(findings) == 1
    assert findings[0].severity is Severity.ERROR
    assert findings[0].result is Result.FAIL
    assert "disagree" in findings[0].message


def test_prose_the_parser_cannot_read_is_not_a_disagreement() -> None:
    """"No steel stated" is the conservative reading both parsers already keep.

    The string exists to hold what the struct cannot — a hook, a stagger, a galvanizing
    callout. A house that writes one must not be reported as contradicting itself.
    """
    spec = _mat("vertical", 6, spacing_in=10.0)
    for prose in ("galvanized per ASTM A767 cl. 1, hook the top",
                  "see structural drawings", ""):
        assert reinforcement_spec_agrees(_Ctx(_wall(prose, spec))) == []


def test_a_struct_with_no_comparable_role_is_not_a_disagreement() -> None:
    """A footing mat states ``bottom-x``/``top-x``; a wall string states vertical steel.
    Those are different bars in different members and comparing them is a category error."""
    ctx = _Ctx(_wall('#6 @ 10" o.c.', _mat("bottom-x", 5, spacing_in=18.0)))
    assert reinforcement_spec_agrees(ctx) == []


def test_a_post_is_compared_on_its_COUNT_not_a_spacing() -> None:
    """A column cage either has four bars in it or does not; a spacing says nothing about it.

    ``Post.vertical_reinforcement``'s own docstring argues this distinction, and the rule has
    to honour it or every migrated column reports a false conflict.
    """
    agree = _Element("Post", "PT-TEST", '(4) #5 vertical, #3 ties @ 10" o.c.',
                     _mat("vertical", 5, count=4))
    assert reinforcement_spec_agrees(_Ctx(agree)) == []

    disagree = _Element("Post", "PT-TEST", '(4) #5 vertical, #3 ties @ 10" o.c.',
                        _mat("vertical", 6, count=4))
    findings = reinforcement_spec_agrees(_Ctx(disagree))
    assert len(findings) == 1 and findings[0].severity is Severity.ERROR


def test_either_side_missing_is_silent() -> None:
    """The rule is about CONTRADICTION. One spelling alone is the ordinary state of the
    world — most pours have only the string, and the migrated ones will have only the
    struct."""
    spec = _mat("vertical", 6, spacing_in=10.0)
    assert reinforcement_spec_agrees(_Ctx(_wall('#6 @ 10" o.c.', None))) == []
    assert reinforcement_spec_agrees(_Ctx(_wall(None, spec))) == []


def test_it_runs_over_the_real_house(catlin_plan) -> None:
    """catlin authors both spellings on its retaining walls (string) and its retaining
    footings (struct) and must be clean."""
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)

    class _Real:
        plan = catlin_plan

    assert reinforcement_spec_agrees(_Real()) == []
    assert model is not None
