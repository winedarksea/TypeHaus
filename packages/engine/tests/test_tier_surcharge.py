"""``engineering/tier_surcharge.py`` against ``sunken_garden_court_free_body.md`` §4c/§4d.

The raised-garden apron stands on its pad inside the soil the court walls retain; §4c works
its bearing, by hand, as a rigid-wall Boussinesq strip (closed form, Jarquio). The engine
integrates the pressure numerically — two routes to one number.
"""

from __future__ import annotations

import pytest
from test_retaining_court import (
    _NOTE_APRON_ARM_FT,
    _NOTE_APRON_GROSS_LATERAL_PLF,
    _NOTE_APRON_LATERAL_PLF,
    _NOTE_APRON_NET_PSF,
    _NOTE_APRON_SOURCE,
    _NOTE_APRON_STEM_MOMENT,
)

from typehaus.engineering.item import Status


def _ctx(plan):
    from typehaus.engineering import EngineeringContext
    from typehaus.resolve import resolve

    model, _ = resolve(plan)
    return EngineeringContext(plan=plan, model=model, soil_class="GM")


def test_the_strip_integral_reproduces_the_closed_form() -> None:
    """§4c's two planes, from its own table: virtual back (a 0) and stem face (a 3.0')."""
    from typehaus.engineering.tier_surcharge import strip_load

    force, arm = strip_load(109.37, 0.0, 1.0, 6.1198)
    assert force == pytest.approx(0.63105 * 109.37, rel=1e-4)
    assert arm == pytest.approx(5.4362, abs=1e-3)
    stem, stem_arm = strip_load(109.37, 3.0, 1.0, 5.1198)
    assert stem == pytest.approx(0.43411 * 109.37, rel=1e-4)
    assert stem_arm == pytest.approx(2.5346, abs=1e-3)
    assert strip_load(520.0, 0.0, 1.0, 6.1198)[0] == pytest.approx(
        _NOTE_APRON_GROSS_LATERAL_PLF, abs=0.1)
    # An infinite strip against the wall is q over the depth: the rigid-wall doubling.
    assert strip_load(100.0, 0.0, 1e6, 5.0)[0] == pytest.approx(500.0, rel=1e-3)
    assert strip_load(0.0, 0.0, 1.0, 5.0) == (0.0, 0.0)


def test_a_lateral_surcharge_enters_thrust_and_overturning_exactly() -> None:
    """The algebra, on the frozen screening geometry — a column-free Surcharge adds ``P`` to
    the thrust and ``P x arm`` to the overturning, and nothing else."""
    from typehaus.engineering.retaining_basis import Surcharge, _Geometry, analyse
    from typehaus.engineering.soil import presumptive

    geometry = _Geometry(tag="X", stem_thickness_ft=1.0, stem_height_ft=9.0,
                         footing_width_ft=7.0, footing_depth_ft=1.0, toe_ft=3.0, heel_ft=3.0,
                         retained_height_ft=10.0)
    soil = presumptive("GM")
    bare = analyse(geometry, soil, at_rest=True)
    loaded = analyse(geometry, soil, at_rest=True, surcharge=Surcharge(
        axial_plf=0.0, moment_plf=0.0, arm_ft=0.0, lateral_plf=100.0, lateral_arm_ft=4.0))
    assert loaded.thrust_plf == pytest.approx(bare.thrust_plf + 100.0)
    assert loaded.overturning_moment == pytest.approx(bare.overturning_moment + 400.0)
    assert loaded.weight_plf == bare.weight_plf
    assert loaded.resisting_moment == bare.resisting_moment


@pytest.mark.parametrize("pcf", [110.0, 130.0])
def test_each_court_wall_carries_its_own_apron(catlin_plan, pcf) -> None:
    """§4c: one parallel apron per court wall, NET of displaced soil, both band ends."""
    from typehaus.engineering.tier_surcharge import court_surcharges

    loads, missing = court_surcharges(_ctx(catlin_plan), pcf)
    assert not missing, missing
    # The two balcony returns meet the court end-on and load no length of it.
    assert set(loads) == set(_NOTE_APRON_SOURCE)
    for wall, apron in _NOTE_APRON_SOURCE.items():
        load = loads[wall]
        assert load.surcharge.source == f"tiered_retaining/{apron}"
        assert "BALCONY" not in load.surcharge.source
        assert load.surcharge.lateral_plf == pytest.approx(_NOTE_APRON_LATERAL_PLF[pcf], abs=0.02)
        if _NOTE_APRON_NET_PSF[pcf] > 0.0:
            assert load.surcharge.lateral_arm_ft == pytest.approx(_NOTE_APRON_ARM_FT, abs=1e-3)
        else:   # §4d: no net load at 130 pcf, and the relief is not credited
            assert any("relief and is not credited" in n for n in load.notes)
        assert load.surcharge.stem_moment_plf == pytest.approx(
            _NOTE_APRON_STEM_MOMENT[pcf], abs=0.1)
        q_net = {q.name: q.value for q in load.inputs}[f"surcharge_{apron}_q_net"]
        assert q_net == pytest.approx(_NOTE_APRON_NET_PSF[pcf], abs=0.01)


def test_the_wall_records_restate_section_4d(catlin_plan) -> None:
    """Overturning 2.35, e 0.851', q 1,341 psf, stem Mu 12,277 — and the citation.

    W-SG-S reads §12a's row instead: its 4'-4" toe gives 3.044, 0.3022', 822.2 psf and a
    toe Mu of 11,587; the stem is the same wall and does not move.
    """
    from typehaus.engineering import EngineeringResults

    rows = {"overturning": 2.35, "e": 0.8511, "q": 1_341.0, "toe": 8_491.0}
    south = {"overturning": 3.044, "e": 0.3022, "q": 822.2, "toe": 11_587.0}
    results = EngineeringResults(_ctx(catlin_plan))
    for wall, apron in _NOTE_APRON_SOURCE.items():
        record = results[f"retaining_wall/{wall}"]
        assert record.status is Status.OK, record.summary
        states = {s.name: s for s in record.limit_states}
        row = south if wall == "W-SG-S" else rows
        assert states["overturning"].capacity == pytest.approx(row["overturning"], abs=0.005)
        assert states["eccentricity"].demand == pytest.approx(row["e"], abs=1e-3)
        assert states["bearing"].demand == pytest.approx(row["q"], abs=0.5)
        assert states["stem flexure"].demand == pytest.approx(12_277.0, abs=2.0)
        assert states["toe flexure"].demand == pytest.approx(row["toe"], abs=2.0)
        note = next(n for n in record.notes if n.startswith("APRON SURCHARGE"))
        assert f"via tiered_retaining/{apron}" in note
        assert "328 plf" in note          # the gross sensitivity is printed, not hidden
        assert any(q.name == f"surcharge_{apron}_lateral" for q in record.inputs)
