"""The steel east posts, against ``notes/canopy_garage_diaphragm.md`` §5.

The pure functions are exercised on the note's own inputs, so an arithmetic regression and a
geometry change do not look the same; the landed assertions at the foot read the house.
"""

from __future__ import annotations

import pytest

from typehaus.engineering.item import Status
from typehaus.engineering.steel_post import (
    PUBLISHED,
    bolt_double_shear_lb,
    flexural_buckling_ksi,
    slender_limit,
)


def test_e3_flexural_buckling_matches_the_note() -> None:
    """KL/r 49.18 -> F_e 118.35, F_cr 41.90 ksi, P_n 141.19, P_n/Ω 84.54 kip."""
    section = PUBLISHED["HSS4x4x0.25"]
    klr = 74.75 / section.radius_in
    assert klr == pytest.approx(49.18, abs=0.01)
    fe, fcr = flexural_buckling_ksi(50.0, klr)
    assert fe == pytest.approx(118.35, abs=0.02)
    assert fcr == pytest.approx(41.90, abs=0.01)
    assert fcr * section.area_in2 / 1.67 == pytest.approx(84.54, abs=0.02)


def test_e3_takes_the_elastic_branch_past_the_transition() -> None:
    """E3-3: F_cr = 0.877 F_e once F_y/F_e passes 2.25 — the branch the note never reaches."""
    fe, fcr = flexural_buckling_ksi(50.0, 200.0)
    assert 50.0 / fe > 2.25
    assert fcr == pytest.approx(0.877 * fe)


def test_e7_the_wall_is_nonslender() -> None:
    """Table B4.1a case 6: 1.40 sqrt(29,000/50) = 33.72 against b/t 14.2."""
    assert slender_limit("hss", 50.0) == pytest.approx(33.72, abs=0.01)
    assert PUBLISHED["HSS4x4x0.25"].slender_ratio < slender_limit("hss", 50.0)
    assert slender_limit("hss_round", 46.0) == pytest.approx(0.11 * 29000.0 / 46.0)


def test_the_saddle_bolt_yield_modes_match_the_note() -> None:
    """NDS §12.3.1 double shear, steel side plates, perpendicular to grain: III_s governs."""
    z, modes = bolt_double_shear_lb(0.625, 4.5, 0.25, 0.55, perpendicular=True)
    assert modes["I_m"] == pytest.approx(1824.1, abs=0.5)
    assert modes["I_s"] == pytest.approx(5437.5, abs=0.5)
    assert modes["III_s"] == pytest.approx(1513.4, abs=0.5)
    assert modes["IV"] == pytest.approx(1891.5, abs=0.5)
    assert z == modes["III_s"]
    assert 2 * z * 1.6 * 0.7 == pytest.approx(3390.0, abs=1.0)


@pytest.fixture(scope="module")
def record(catlin_ctx):
    return catlin_ctx.engineering["steel_post/PT-BW-RE"]


def test_the_landed_record_reproduces_section_5(record) -> None:
    assert record.status is Status.OK, record.summary
    states = {s.name: s for s in record.limit_states}
    rows = {
        "slenderness KL/r, §E2": (49.18, 200.0),
        "axial, flexural buckling §E3": (3424.1, 84544.9),
        "combined axial and drag, §H1.1": (0.0226, 1.0),
        "saddle bolts, uplift": (433.26, 3390.0),
        "PT-BW-RE base anchor tension (breakout / pullout / steel)": (722.1, 4528.2),
    }
    for name, (demand, capacity) in rows.items():
        assert states[name].demand == pytest.approx(demand, rel=2e-3), name
        assert states[name].capacity == pytest.approx(capacity, rel=2e-3), name


def test_both_east_posts_are_graded_and_nothing_else_is_steel(catlin_ctx) -> None:
    keys = {k for k in catlin_ctx.engineering if k.startswith("steel_post/")}
    assert keys == {"steel_post/PT-BW-RE", "steel_post/PT-BW-RNE"}


def test_an_unpublished_section_is_incomplete_not_guessed(catlin_ctx) -> None:
    from dataclasses import replace

    from typehaus.engineering.roof_lateral import roof_winds
    from typehaus.engineering.steel_post import _one

    ctx = catlin_ctx.engineering.context
    post = next(p for p in roof_winds(ctx)["RF-BW-CANOPY"].pinned if p.tag == "PT-BW-RE")
    wind = roof_winds(ctx)["RF-BW-CANOPY"]
    element = ctx.plan.by_tag("PT-BW-RE").model_copy(update={"size": "HSS5x5x0.3125"})

    class _Plan:
        def by_tag(self, tag):
            return element if tag == "PT-BW-RE" else ctx.plan.by_tag(tag)

        def __getattr__(self, name):
            return getattr(ctx.plan, name)

    result = _one(replace(ctx, plan=_Plan()), post, wind)
    assert result.status is Status.INCOMPLETE
    assert any("HSS5x5x0.3125" in text for text in result.missing)
