"""``engineering/base_rotation.py`` against ``notes/column_base_rotation.md``.

The note is hand-worked in a separate pass; this module reproduces its arithmetic — §3a's
pole solve term by term, §4's wall-top spring, and §0's table of verdicts at both band ends.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

from typehaus.checks.structural._engineering import engineering_context
from typehaus.engineering import base_spring as spring
from typehaus.engineering.base_rotation import KIND, _Column, _Point, compute
from typehaus.engineering.base_supports import PoleBase, WallBase
from typehaus.engineering.item import Status
from typehaus.engineering.pier_basis import cast_piers
from typehaus.model import Site, SubgradeModulus
from typehaus.model.registry import constructor_names

#: §0: ``(δ at δ_ref 0.25", δ at 1.0" or None for a mechanism, status)``.
_ORACLE = {
    "PT-BW-RE": (1.305, 1.953, Status.INCOMPLETE),
    "PT-BW-RNE": (1.295, 1.868, Status.INCOMPLETE),
    "PT-BW-W": (1.110, 1.442, Status.INCOMPLETE),
    "PT-BW-E": (1.034, 1.106, Status.OK),
    "PT-BW-GW": (1.456, None, Status.OVER),
    "PT-BW-GE": (1.099, 1.538, Status.INCOMPLETE),
    "PT-SG-BF1": (1.0438, 1.0447, Status.OK),
    "PT-SG-BF3": (1.0438, 1.0447, Status.OK),
    "PT-SG-BR1": (1.0454, 1.0463, Status.OK),
    "PT-SG-BR3": (1.0454, 1.0463, Status.OK),
}


@pytest.fixture(scope="module")
def ectx(catlin_ctx):
    return engineering_context(catlin_ctx)


def _points(ectx, tag):
    pier = next(p for p in cast_piers(ectx) if p.tag == tag)
    base = (WallBase if pier.base_kind == "wall" else PoleBase).build(ectx, pier)
    column = _Column.of(pier)
    return pier, column, [_Point.at("", column, base.k_theta(ectx, d, column))
                          for d in (0.25, 1.0)]


def test_the_pole_solve_reproduces_section_3a() -> None:
    """§3a, per pound at the head of PT-BW-RE, δ_ref 1.0" (n_h 3,600 lb/ft⁴)."""
    profile = ((0.0, 7.3333, 1.0), (7.3333, 8.3333, 1.5))
    pole = spring.winkler_pole(3_600.0, profile, 1.0, 9.2292)
    assert 12.0 * pole.u0_ft == pytest.approx(0.001983, rel=2e-3)
    assert pole.theta_rad == pytest.approx(2.731e-5, rel=2e-3)
    tip_in = 12.0 * pole.at_height_ft(9.2292)
    assert tip_in == pytest.approx(0.005008, rel=2e-3)
    assert 198.75 ** 2 / tip_in == pytest.approx(7.887e6, rel=2e-3)


def test_a_constant_width_pole_is_the_textbook_rigid_pile() -> None:
    """``b`` constant: a rigid pile in a linearly increasing modulus, by hand —
    ``u0 = 18H/(n_h D²) + 24M/(n_h D³)``, ``θ = 24H/(n_h D³) + 36M/(n_h D⁴)``. Pure moment:
    ΣH = 0 gives ``u0 = 2θD/3``, then ``ΣM`` gives ``n_h θ D⁴/36 = M``. The two cross terms
    are equal, as Maxwell's reciprocity requires."""
    n_h, depth, shear, height = 1_000.0, 4.0, 100.0, 2.0
    pole = spring.winkler_pole(n_h, ((0.0, depth, 1.0),), shear, height)
    moment = shear * height
    assert pole.u0_ft == pytest.approx(18 * shear / (n_h * depth ** 2)
                                       + 24 * moment / (n_h * depth ** 3))
    assert pole.theta_rad == pytest.approx(24 * shear / (n_h * depth ** 3)
                                           + 36 * moment / (n_h * depth ** 4))


def test_a_rigid_spring_returns_the_fixed_base_k_and_the_series_form_is_conservative() -> None:
    assert spring.spring_cantilever_k(1e9) == pytest.approx(2.0, abs=1e-4)
    for r in (0.03, 0.3, 1.3, 5.0, 50.0):
        exact = (math.pi / spring.spring_cantilever_k(r)) ** 2      # Pc L²/EI
        graded = math.pi ** 2 / 2.1 ** 2 * spring.series_ratio(r)
        assert graded < exact


def test_the_wall_top_spring_reproduces_section_4() -> None:
    ei = 0.35 * 57_000.0 * math.sqrt(5_000.0) * 12.0 * 12.0 ** 3 / 12.0
    assert ei == pytest.approx(2.4377e9, rel=1e-3)
    footing = 12.0 * 24_000.0 * 1.0 * 7.0 ** 3 / 12.0
    assert footing == pytest.approx(8.232e6, rel=1e-4)
    assert spring.wall_top_stiffness(ei, 109.4375, footing) == pytest.approx(6.8707e7, rel=1e-3)
    assert spring.wall_top_stiffness(ei, 109.4375, 0.0) == pytest.approx(3 * ei / 109.4375)


def test_the_rigid_bound_is_deck_posts_own_magnifier(ectx) -> None:
    """R → ∞ must return deck_post's δ, or this record is not citing deck_post's bound."""
    from typehaus.engineering.deck_post import _sway_magnifier

    for tag in _ORACLE:
        pier, column, _points_ = _points(ectx, tag)
        rigid = spring.magnifier(column.pu_lb, column.pc_rigid_lb)
        assert rigid == pytest.approx(_sway_magnifier(pier, pier.factored_lb)[1], rel=1e-9)
        assert _Point.at("", column, 1e15).delta == pytest.approx(rigid, rel=1e-6)


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_both_band_ends_reproduce_the_note(tag, ectx) -> None:
    stiff, soft, _status = _ORACLE[tag]
    _pier, _column, (at_stiff, at_soft) = _points(ectx, tag)
    assert at_stiff.delta == pytest.approx(stiff, abs=0.002)
    if soft is None:
        assert at_soft.delta is None
    else:
        assert at_soft.delta == pytest.approx(soft, abs=0.002)


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_the_record_reproduces_the_notes_verdict(tag, catlin_ctx) -> None:
    record = catlin_ctx.engineering[f"{KIND}/{tag}"]
    assert record.status is _ORACLE[tag][2], (record.summary, record.missing)
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["subgrade_modulus_measured"] == 0.0
    assert any("NOT GRADED" in n for n in record.notes)
    if record.status is Status.INCOMPLETE:
        assert "Site.lateral_subgrade_modulus" in record.missing[0]


def test_the_keys_are_column_bases_plus_the_wall_borne_columns(catlin_ctx, ectx) -> None:
    from typehaus.engineering import keys_of

    assert set(keys_of(KIND, ectx)) == set(_ORACLE)
    assert set(keys_of("column_base", ectx)) < set(keys_of(KIND, ectx))


def test_the_pole_residue_names_the_shaft_pad_split(catlin_ctx) -> None:
    """Plan rule 12: the deferral's residue must not vanish with it."""
    notes = " ".join(catlin_ctx.engineering[f"{KIND}/PT-BW-RE"].notes)
    assert "HOW THE BASE MOMENT SPLITS" in notes
    assert "W-BW-SCREEN" in notes and "§1604.4" in notes


def test_a_measured_modulus_governs_and_moves_the_fingerprint(ectx) -> None:
    from typehaus.engineering import fingerprint

    site = ectx.plan.project.site
    report = SubgradeModulus(n_h_pci=20.0, source="GEO-1 (test)", basis="pressuremeter")
    project = ectx.plan.project.model_copy(
        update={"site": site.model_copy(update={"lateral_subgrade_modulus": report})})
    measured = dataclasses.replace(
        ectx, plan=ectx.plan.model_copy(update={"project": project}))
    before = {r.key: r for r in compute(ectx)}
    after = {r.key: r for r in compute(measured)}
    re = after["PT-BW-RE"]
    assert re.status is Status.OK, re.missing
    inputs = {q.name: q.value for q in re.inputs}
    assert inputs["subgrade_modulus_measured"] == 1.0
    assert inputs["subgrade_modulus_pci"] == pytest.approx(20.0)
    assert any("A measured modulus governs" in n for n in re.notes)
    assert fingerprint(after["PT-BW-E"]) != fingerprint(before["PT-BW-E"])


def test_the_subgrade_modulus_round_trips_on_the_site() -> None:
    site = Site(lat=45.0, lon=-93.0, elevation=0.0,  # type: ignore[arg-type]
                lateral_subgrade_modulus=SubgradeModulus(
                    n_h_pci=12.5, source="report", basis="correlated", k_v_pci=80.0))
    assert Site.model_validate_json(site.model_dump_json()) == site
    assert "SubgradeModulus" in constructor_names()
    assert Site.model_fields["lateral_subgrade_modulus"].default is None
