"""``integrity.reinforcement_layout`` — a schedule the layout can honour, and one it did.

Catlin is clean. Each red case mutates one authored spec on a copy of the loaded plan and
re-resolves, so the finding comes from the real layout rather than a hand-built model.
"""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus import BarSpec, ReinforcementSpec, inch
from typehaus.checks.integrity.reinforcement_layout import reinforcement_layout
from typehaus.findings import Result, Severity

_ID = "integrity.reinforcement_layout"
#: A cast-concrete Post with a cage: a balcony corner column. PT-SG-COL was the subject until
#: it retired with the court's centre line (2026-09-22).
_COLUMN = "PT-SG-BR1"


def _with_spec(plan, tag: str, spec):
    for storey, items in plan.elements.items():
        for el in items:
            if el.tag == tag:
                swapped = [e.model_copy(update={"reinforcement": spec}) if e.tag == tag else e
                           for e in items]
                return plan.with_elements(storey, swapped)
    raise KeyError(tag)


def _findings(plan, tag):
    ctx = check_context(plan)
    return [f for f in reinforcement_layout(ctx) if tag in f.element_tags]


def test_catlin_is_clean(catlin_model_ro) -> None:
    ctx = check_context(model=catlin_model_ro)
    found = reinforcement_layout(ctx)
    assert found
    assert all(f.result is Result.PASS for f in found), [f.message for f in found
                                                          if f.result is not Result.PASS]


@pytest.mark.parametrize(("bars", "needle"), [
    ((BarSpec(role="vertical", bar=5, count=4, spacing=inch(10)),), "exactly one of"),
    ((BarSpec(role="vertical", bar=5),), "exactly one of"),
    ((BarSpec(role="top-x", bar=5, count=4),), "does not belong on a Post"),
    ((BarSpec(role="vertical", bar=5, count=4, zone=inch(48)),), "cannot take a zone"),
])
def test_a_schedule_the_layout_cannot_honour_is_an_error(catlin_plan, bars, needle) -> None:
    plan = _with_spec(catlin_plan, _COLUMN, ReinforcementSpec(bars=bars, cover=inch(2)))
    found = _findings(plan, _COLUMN)
    errors = [f for f in found if f.severity is Severity.ERROR]
    assert errors and any(needle in f.message for f in errors), [f.message for f in found]


def test_a_rib_role_without_ribs_is_an_error(catlin_plan) -> None:
    spec = ReinforcementSpec(bars=(BarSpec(role="rib", bar=5, count=2),))
    found = _findings(_with_spec(catlin_plan, "SL-M-DECK", spec), "SL-M-DECK")
    assert any("needs ReinforcementSpec.ribs" in f.message for f in found)


def test_a_role_that_places_nothing_warns(catlin_plan) -> None:
    """A corner column stands on its wall top — but a pier with no ``supported_by`` has no
    base."""
    spec = ReinforcementSpec(bars=(BarSpec(role="vertical", bar=5, count=4),
                                   BarSpec(role="dowels", bar=5)), cover=inch(2))
    plan = _with_spec(catlin_plan, _COLUMN, spec)
    storey, items = next((s, i) for s, i in plan.elements.items()
                         if any(e.tag == _COLUMN for e in i))
    plan = plan.with_elements(storey, [e.model_copy(update={"supported_by": None})
                                       if e.tag == _COLUMN else e for e in items])
    found = _findings(plan, _COLUMN)
    warn = [f for f in found if f.result is Result.FAIL and f.severity is Severity.WARN]
    assert warn and "dowels" in warn[0].message


def test_a_section_too_thin_for_its_cover_warns(catlin_plan) -> None:
    spec = ReinforcementSpec(bars=(BarSpec(role="vertical", bar=6, spacing=inch(10)),
                                   BarSpec(role="horizontal", bar=6, spacing=inch(10))),
                             cover=inch(4))
    found = _findings(_with_spec(catlin_plan, "W-B-S1", spec), "W-B-S1")
    assert any("cannot hold" in f.message for f in found), [f.message for f in found]
