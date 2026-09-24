"""2024 IRC R403.5 crushed stone footings — ``code.R403_5_crushed_stone_footings``.

The rule has four independent ways to say no and they are answered by four different
people, so each is exercised on its own: the SCOPE (the jurisdiction's seismic category and
the designer's ``unbalanced_fill``), the STONE (a supplier's ticket), the CONSOLIDATION (the
excavator's method) and the SIZE (Table R403.4, against the wall the footing carries).

The catlin fixture at the end is where a real change to the building has to show. Everything
above it is synthetic, for the same reason ``test_foundation_unbalanced`` builds its own
wall: a table test should name the row it is testing, and the house's numbers move.
"""

from __future__ import annotations

import pytest

from typehaus.checks.code.mn_residential.crushed_stone_footings import crushed_stone_footings
from typehaus.checks.code.mn_residential.profile import MN_2020
from typehaus.findings import Result
from typehaus.model import CrushedStoneSpec
from typehaus.quantities import inch


def _findings(ctx):
    return crushed_stone_footings(ctx)


def _one(ctx):
    found = _findings(ctx)
    assert len(found) == 1, [f.message for f in found]
    return found[0]


# ------------------------------------------------------------------ catlin, the real one
def test_catlins_eight_garage_footings_pass_on_stone(catlin_ctx) -> None:
    """The landed verdict, and the arithmetic that earns it.

    Eight 20" x 8" strips under the garage's ICF stem runs. Table R403.4's one-storey
    conventional light-frame row wants D = 4" at every soil bearing value it publishes, and
    W = 13"/15"/17" for an 8"/10"/12" wall. Both authored dimensions clear the widest of
    those, which is what the check requires here — see the sub-8" note below.
    """
    found = _findings(catlin_ctx)
    assert {f.result for f in found} == {Result.PASS}, [
        f.message for f in found if f.result is not Result.PASS]
    tags = sorted(t for f in found for t in f.element_tags)
    assert len(tags) == 8, tags  # nine until FT-GF-N-DR retired, 2026-09-23
    assert all(t.startswith("FT-GF-") for t in tags), tags
    assert all("Seismic Design Category A" in f.message for f in found)


def test_the_six_inch_icf_core_is_below_table_r403_4s_first_column(catlin_ctx) -> None:
    """The one subtlety in catlin's numbers, asserted so it cannot be quietly "simplified".

    Table R403.4 is indexed on the WALL's width and its columns start at 8". GARAGE_ICF_6 is
    a 6" poured core between two 2 1/2" EPS faces — 11" overall, 6" of concrete — so there is
    no column to read. Footnote a permits interpolating DEPTH between wall widths; it says
    nothing about extrapolating WIDTH below the table, so the check requires the WIDEST
    published W (17") rather than inventing a narrower one. 20" clears it.

    Reading the ASSEMBLY thickness instead of the structure layer would have put this wall in
    the 12" column — the right ANSWER by luck, on the wrong row, and wrong the moment the EPS
    changes thickness.
    """
    from typehaus.checks.code.mn_residential.crushed_stone_footings import (
        _structure_width_in,
    )

    assert _structure_width_in(catlin_ctx, "W-GF-S1") == pytest.approx(6.0, abs=1e-6)
    assert all('17" W' in f.message for f in _findings(catlin_ctx))


def test_minnesota_states_a_seismic_design_category_at_last() -> None:
    """It existed nowhere in the engine until 2026-09-15, and the notes sheet said so.

    R403.5 is scoped on it, so without the field the rule could not be answered at all. It is
    a JURISDICTION fact — IRC Table R301.2.2.1 assigns it from the site's mapped spectral
    response — which is why it lives on the profile beside the frost depth and not on a wall.
    """
    assert MN_2020.seismic_design_category == "A"


# ------------------------------------------------------------------------- the scope gates
def test_a_profile_that_states_no_category_reports_unknown(catlin_ctx) -> None:
    """Never a silent pass on the friendliest row.

    R403.5 runs out at Seismic Design Category C. A profile that declares none cannot answer
    whether these footings are permitted, and the finding says where a jurisdiction reads it
    rather than assuming A because most places are A.
    """
    import dataclasses

    ctx = dataclasses.replace(
        catlin_ctx, profile=dataclasses.replace(MN_2020, seismic_design_category=None))
    found = _one(ctx)
    assert found.result is Result.UNKNOWN
    assert "R301.2.2.1" in found.message
    assert len(found.element_tags) == 8, "the UNKNOWN names every footing it could not grade"


def test_category_d_fails_them_all_at_once(catlin_ctx) -> None:
    """One finding, not nine: the category is a property of the jurisdiction.

    Reporting it per footing would be nine copies of one sentence about a decision no footing
    participates in — the same reasoning ``foundation_unbalanced_fill`` gives for grouping.
    """
    import dataclasses

    ctx = dataclasses.replace(
        catlin_ctx, profile=dataclasses.replace(MN_2020, seismic_design_category="D1"))
    found = _one(ctx)
    assert found.result is Result.FAIL
    assert "A, B and C" in found.message


def test_a_house_with_no_stone_footing_earns_not_applicable(catlin_ctx) -> None:
    """N/A from positive evidence of absence (decision #32), never an empty list.

    "This building's footings are all cast concrete" is a fact about the building and a real
    verdict. Returning ``[]`` would make the rule invisible in the report and indistinguishable
    from one that crashed.
    """
    import dataclasses

    from typehaus.model.structure import Footing

    plan = catlin_ctx.plan
    patched = []
    for el in plan.all_elements():
        if isinstance(el, Footing) and el.material == "crushed_stone":
            patched.append(el.tag)
    assert patched, "the fixture must actually carry stone footings for this to mean anything"

    concrete_only = plan.model_copy(deep=True)
    for el in concrete_only.all_elements():
        if isinstance(el, Footing) and el.material == "crushed_stone":
            object.__setattr__(el, "material", "concrete")
    found = _one(dataclasses.replace(catlin_ctx, plan=concrete_only))
    assert found.result is Result.NOT_APPLICABLE
    assert "every one is cast concrete" in found.message


def test_a_wall_that_retains_refuses_the_section(catlin_ctx) -> None:
    """R403.5's first condition, and the reason B1 had to land before this could.

    The section is for NONRETAINING foundations. `unbalanced_fill=ft(0)` is authored on the
    garage stem because SL-G-FLOOR's top is at grade and fill stands level on both faces;
    without that authored zero the derived proxy reports 3'-6" and this check would have to
    refuse. So the same field that makes the claim TRUE is the one that makes it TESTABLE.
    """
    import dataclasses

    from typehaus.model.structure import FoundationWall
    from typehaus.quantities import ft

    plan = catlin_ctx.plan.model_copy(deep=True)
    for el in plan.all_elements():
        if isinstance(el, FoundationWall) and el.tag == "W-GF-S1":
            object.__setattr__(el, "unbalanced_fill", ft(3.5))
    found = [f for f in _findings(dataclasses.replace(catlin_ctx, plan=plan))
             if f.result is Result.FAIL]
    assert len(found) == 1, [f.message for f in found]
    assert "NONRETAINING" in found[0].message
    assert set(found[0].element_tags) == {"FT-GF-S1", "W-GF-S1"}


def test_a_wall_that_states_nothing_is_unknown_not_a_pass(catlin_ctx) -> None:
    """The derived proxy is not evidence, and the check says which field would settle it."""
    import dataclasses

    from typehaus.model.structure import FoundationWall

    plan = catlin_ctx.plan.model_copy(deep=True)
    for el in plan.all_elements():
        if isinstance(el, FoundationWall) and el.tag == "W-GF-S1":
            object.__setattr__(el, "unbalanced_fill", None)
    found = [f for f in _findings(dataclasses.replace(catlin_ctx, plan=plan))
             if f.result is Result.UNKNOWN]
    assert len(found) == 1, [f.message for f in found]
    assert "conservative proxy" in found[0].message


# -------------------------------------------------------------------- R403.4.1, term by term
@pytest.mark.parametrize("field,value,needle", [
    ("gradation", "MnDOT Class 5 aggregate base", "ASTM C33"),
    ("max_size", inch(1.0), 'exceeds the 1/2"'),
    ("min_size", inch(1.0 / 32.0), 'finer than the 1/16"'),
    ("angular", False, "angular"),
    ("free_of_fines", False, "organic, clayey or silty"),
    ("lift_thickness", inch(18), 'exceed the 8"'),
    ("consolidation", "tracked in with the excavator bucket", "vibratory plate"),
])
def test_each_r403_4_1_requirement_is_graded_by_name(catlin_ctx, field, value, needle) -> None:
    """Seven requirements, seven separate ways to fail, and each says which one.

    This is the whole reason ``CrushedStoneSpec`` is a model rather than the free-text
    ``aggregate`` string ``FootingBedding`` carries: a checker has to answer R403.4.1 term by
    term, and reading a gradation out of a substring is guessing. The parametrisation IS the
    specification — a requirement added to the section without a row here is one nothing
    grades.
    """
    import dataclasses

    from typehaus.model.structure import Footing

    plan = catlin_ctx.plan.model_copy(deep=True)
    for el in plan.all_elements():
        if isinstance(el, Footing) and el.tag == "FT-GF-S1":
            object.__setattr__(el, "stone",
                               CrushedStoneSpec(**{field: value}))
    found = [f for f in _findings(dataclasses.replace(catlin_ctx, plan=plan))
             if f.result is Result.FAIL]
    assert len(found) == 1, [f.message for f in found]
    assert needle in found[0].message
    assert found[0].element_tags == ("FT-GF-S1",)


def test_a_stone_footing_naming_no_stone_is_unknown(catlin_ctx) -> None:
    """R403.4.1 is a specification, and an unstated stone meets none of it.

    Not a FAIL: nobody has said the stone is wrong, only that nobody has said what it is. The
    finding names the constructor to author, because that is the whole remedy.
    """
    import dataclasses

    from typehaus.model.structure import Footing

    plan = catlin_ctx.plan.model_copy(deep=True)
    for el in plan.all_elements():
        if isinstance(el, Footing) and el.tag == "FT-GF-S1":
            object.__setattr__(el, "stone", None)
    found = [f for f in _findings(dataclasses.replace(catlin_ctx, plan=plan))
             if f.result is Result.UNKNOWN]
    assert len(found) == 1, [f.message for f in found]
    assert "CrushedStoneSpec" in found[0].message


# ------------------------------------------------------------------------ Table R403.4, size
def test_a_shallow_footing_fails_on_the_tables_floor(catlin_ctx) -> None:
    """D = 4" is Table R403.4's minimum at EVERY soil bearing value it publishes.

    Which is why the depth half of this rule needs no soil class at all — a fact worth
    pinning, because the width half would if the wall were ever in range of the table.
    """
    import dataclasses

    from typehaus.model.structure import Footing

    plan = catlin_ctx.plan.model_copy(deep=True)
    for el in plan.all_elements():
        if isinstance(el, Footing) and el.tag == "FT-GF-S1":
            object.__setattr__(el, "depth", inch(3))
    found = [f for f in _findings(dataclasses.replace(catlin_ctx, plan=plan))
             if f.result is Result.FAIL]
    assert len(found) == 1, [f.message for f in found]
    assert "minimum D of 4" in found[0].message


def test_a_narrow_footing_fails_against_the_widest_published_w(catlin_ctx) -> None:
    """16" under a 6" wall: under 17", so it fails — and the message says why 17".

    The reason matters more than the verdict here. A reader who sees "17 required" under a 6"
    wall and cannot find that row in the table will assume the check is broken; the finding
    has to carry the extrapolation argument with it.
    """
    import dataclasses

    from typehaus.model.structure import Footing

    plan = catlin_ctx.plan.model_copy(deep=True)
    for el in plan.all_elements():
        if isinstance(el, Footing) and el.tag == "FT-GF-S1":
            object.__setattr__(el, "width", inch(16))
    found = [f for f in _findings(dataclasses.replace(catlin_ctx, plan=plan))
             if f.result is Result.FAIL]
    assert len(found) == 1, [f.message for f in found]
    assert "NARROWER than Table R403.4's first column" in found[0].message
    assert "footnote a" in found[0].message
