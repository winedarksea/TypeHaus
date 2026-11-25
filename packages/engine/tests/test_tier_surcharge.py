"""``engineering/tier_surcharge.py`` against ``sunken_garden_court_free_body.md`` §4c/§4d.

The raised-garden apron stands on its pad inside the soil the court walls retain; §4c works
its bearing, by hand, as a rigid-wall Boussinesq strip (closed form, Jarquio). The engine
integrates the pressure numerically — two routes to one number.
"""

from __future__ import annotations

import pytest

from typehaus.engineering.item import Status

#: Since 2026-11-23 every apron leg is the 52" chart section (six 8" courses + a 4" capstone) on
#: a base 4" lower (raised_garden_srw.md §10): the court sees W = 130 pcf x 0.97' x 52"/12 on
#: its pad. The three parallel aprons are identical; the two returns meet the court end-on.
_CAPPED_FT = 52.0 / 12.0
_COURT_RETAINED_FT = 10.1198       # the court's retained height, 6.1198' + the old 4'-0" drop
_NOTE_APRON_SOURCE = {"W-SG-S": "W-RG-BLOCK", "W-SG-W2": "W-RG-WEST", "W-SG-E2": "W-RG-EAST"}
#: Pad width pushing on each wall's virtual back. FT-SG-S's heel +6" (free body §15n) puts its
#: virtual back mid-pad, so only the outer 6" pushes on S (27.52 plf, was 54.63).
_BACK_STRIP_FT = {"W-SG-S": 0.5, "W-SG-W2": 1.0, "W-SG-E2": 1.0}
#: Gross strip thrust on the same plane, the sensitivity the record prints (520 psf: 328 plf
#: on the old 4'-0" apron; 563.3 psf here).


def _rigid_strip(q, a, b, h):
    """The note's rigid-wall strip by Gauss-Legendre, not Simpson: a second route."""
    import numpy as np

    x, w = np.polynomial.legendre.leggauss(80)
    z = 0.5 * h * (x + 1.0)
    a1, a2 = np.arctan(a / z), np.arctan((a + b) / z)
    beta = a2 - a1
    sigma = 2.0 * q / np.pi * (beta - np.sin(beta) * np.cos(a1 + a2))
    force = float(0.5 * h * np.sum(w * sigma))
    moment = float(0.5 * h * np.sum(w * sigma * (h - z)))
    return force, moment / force


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
    assert strip_load(520.0, 0.0, 1.0, 6.1198)[0] == pytest.approx(328.1, abs=0.1)
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
        assert load.surcharge.source == f"SRW apron {apron}"
        assert "BALCONY" not in load.surcharge.source
        q_net = max((130.0 - pcf) * _CAPPED_FT, 0.0)       # net of the displaced soil
        q_key = {q.name: q.value for q in load.inputs}[f"surcharge_{apron}_q_net"]
        assert q_key == pytest.approx(q_net, abs=0.01)
        if q_net > 0.0:
            drop = _CAPPED_FT
            lateral, arm = _rigid_strip(q_net, 0.0, _BACK_STRIP_FT[wall],
                                        _COURT_RETAINED_FT - drop)
            sp, sarm = _rigid_strip(q_net, 3.0, 1.0, _COURT_RETAINED_FT - 1.0 - drop)
            assert load.surcharge.lateral_plf == pytest.approx(lateral, abs=0.02)
            assert load.surcharge.lateral_arm_ft == pytest.approx(arm, abs=1e-3)
            assert load.surcharge.stem_moment_plf == pytest.approx(sp * sarm, abs=0.1)
        else:   # no net load at 130 pcf, and the relief is not credited
            assert load.surcharge.lateral_plf == 0.0
            assert any("relief and is not credited" in n for n in load.notes)


def test_the_wall_records_carry_the_apron_surcharge(catlin_plan) -> None:
    """Each court wall's record quotes its apron by name, with the gross sensitivity and the
    capped section's moved rows (re-pinned 2026-11-23 from the engine: overturning, e, q,
    stem and toe Mu on the three identical 52" aprons; W-SG-S has its own 4'-4" toe, and since
    §15n its heel +6": overturning 3.55, e 0.093', q 746.9, toe 11,002)."""
    from typehaus.engineering import EngineeringResults

    rows = {
        "W-SG-E2": {"overturning": 2.3504, "e": 0.8519, "q": 1_341.5, "toe": 8_494.3},
        "W-SG-W2": {"overturning": 2.3504, "e": 0.8519, "q": 1_341.5, "toe": 8_494.3},
        "W-SG-S": {"overturning": 3.5513, "e": 0.0935, "q": 746.94, "toe": 11_001.7},
    }
    results = EngineeringResults(_ctx(catlin_plan))
    for wall, apron in _NOTE_APRON_SOURCE.items():
        gross = _rigid_strip(130.0 * _CAPPED_FT, 0.0, _BACK_STRIP_FT[wall],
                             _COURT_RETAINED_FT - _CAPPED_FT)[0]
        record = results[f"retaining_wall/{wall}"]
        assert record.status is Status.OK, record.summary
        states = {s.name: s for s in record.limit_states}
        row = rows[wall]
        assert states["overturning"].capacity == pytest.approx(row["overturning"], abs=0.005)
        assert states["eccentricity"].demand == pytest.approx(row["e"], abs=1e-3)
        assert states["bearing"].demand == pytest.approx(row["q"], abs=0.5)
        assert states["stem flexure"].demand == pytest.approx(12_268.9, abs=2.0)
        assert states["toe flexure"].demand == pytest.approx(row["toe"], abs=2.0)
        note = next(n for n in record.notes if n.startswith("APRON SURCHARGE"))
        assert f"via SRW apron {apron}" in note
        assert f"{gross:,.0f} plf" in note     # the gross sensitivity is printed, not hidden
        assert any(q.name == f"surcharge_{apron}_lateral" for q in record.inputs)
