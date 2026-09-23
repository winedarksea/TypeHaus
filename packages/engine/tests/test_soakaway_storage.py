"""``drainage.soakaway_storage``: voids + a slow melt's infiltration against the design melt.

Synthetic, on ``_soakaway_plan`` + ``test_area_drain``'s slab and grate: a 4'x4' course 12"
deep at 0.40 voids is 6.40 cf; 0.06 in/hr for 48 h over 16 sf is 3.84 cf; 10.24 cf in all.
Catlin's 50 psf ground snow over a 12 sf catchment is 50 / 62.4 x 12 = 9.62 cf.
The catlin reproduction of ``notes/court_soakaway_storage.md`` is ``test_catlin_court_drainage``.
"""

from __future__ import annotations

import pytest
from _soakaway_plan import PAD_BOTTOM_FT, soak_bed, soak_plan
from test_area_drain import _drain, _slab

from typehaus.checks.mep.soakaway_storage import soakaway_storage
from typehaus.findings import Result
from typehaus.quantities import ft, inch, pt
from typehaus.resolve import resolve

_CATCHMENT = (pt(ft(70), ft(10)), pt(ft(74), ft(10)), pt(ft(74), ft(13)), pt(ft(70), ft(13)))


def _findings(catlin_plan, **soak):
    from _helpers import check_context

    bed = soak_bed(inlet_refs=("FB-TEST-PLAIN", "FD-TEST-SOAK", "AD-TEST"), **soak)
    plan = soak_plan(catlin_plan, soak=bed,
                     extra=(_slab(), _drain(catchment=_CATCHMENT)))
    model, found = resolve(plan)
    assert not [f for f in found if f.severity.value == "error"]
    return [f for f in soakaway_storage(check_context(model=model))
            if "FB-TEST-SOAK" in f.element_tags]


@pytest.fixture(scope="module")
def graded(catlin_plan):
    return _findings(catlin_plan)


def test_the_course_holds_the_melt(graded):
    storage, lip = graded
    assert storage.result is Result.PASS, storage.message
    for term in ("6 cf of voids", "(16 sf)", "4 cf infiltrated", "10 cf", "10 cf of melt",
                 "presumed", "12 sf of catchment via AD-TEST"):
        assert term in storage.message, (term, storage.message)


def test_a_shallower_course_fails(catlin_plan):
    storage = _findings(catlin_plan, soakaway_depth=inch(6))[0]
    assert storage.result is Result.FAIL, storage.message   # 3.20 + 3.84 < 9.62


@pytest.mark.parametrize("unstated", ["void_ratio", "infiltration_in_per_hr"])
def test_an_unstated_term_is_unknown(catlin_plan, unstated):
    storage = _findings(catlin_plan, **{unstated: None})[0]
    assert storage.result is Result.UNKNOWN and unstated in storage.message


def test_a_lip_inside_the_drained_section_is_named(graded, catlin_plan):
    """The lip 6" under the pad sits 18" above the 24" drained section's bottom."""
    lip = graded[1]
    assert lip.result is Result.UNKNOWN
    assert "18\" above" in lip.message and "floods before relief" in lip.message
    low = _findings(catlin_plan, overflow_invert=ft(PAD_BOTTOM_FT) - inch(30))[1]
    assert low.result is Result.PASS
