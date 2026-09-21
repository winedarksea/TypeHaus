"""``engineering/tier_surcharge.py`` against ``sunken_garden_court_free_body.md`` §4c.

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
    assert strip_load(549.37, 0.0, 1.0, 6.1198)[0] == pytest.approx(
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
        assert load.surcharge.lateral_arm_ft == pytest.approx(_NOTE_APRON_ARM_FT, abs=1e-3)
        assert load.surcharge.stem_moment_plf == pytest.approx(
            _NOTE_APRON_STEM_MOMENT[pcf], abs=0.1)
        q_net = {q.name: q.value for q in load.inputs}[f"surcharge_{apron}_q_net"]
        assert q_net == pytest.approx(_NOTE_APRON_NET_PSF[pcf], abs=0.01)


def test_the_wall_records_restate_section_4c(catlin_plan) -> None:
    """Overturning 2.33, e 0.870', q 1,353 psf, stem Mu 12,329 — and the citation."""
    from typehaus.engineering import EngineeringResults

    results = EngineeringResults(_ctx(catlin_plan))
    for wall, apron in _NOTE_APRON_SOURCE.items():
        record = results[f"retaining_wall/{wall}"]
        assert record.status is Status.OK, record.summary
        states = {s.name: s for s in record.limit_states}
        assert states["overturning"].capacity == pytest.approx(2.33, abs=0.005)
        assert states["eccentricity"].demand == pytest.approx(0.8696, abs=1e-3)
        assert states["bearing"].demand == pytest.approx(1_353.3, abs=0.5)
        assert states["stem flexure"].demand == pytest.approx(12_329.0, abs=2.0)
        assert states["toe flexure"].demand == pytest.approx(8_555.0, abs=2.0)
        note = next(n for n in record.notes if n.startswith("APRON SURCHARGE"))
        assert f"via tiered_retaining/{apron}" in note
        assert "347 plf" in note          # the gross sensitivity is printed, not hidden
        assert any(q.name == f"surcharge_{apron}_lateral" for q in record.inputs)
