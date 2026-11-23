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
#:
#: RE/RNE straddle the band and CLOSE on catlin's presumed n_h (§10), hence OK.
_WORKED = {
    # Every north-entry column cast one 3/4" pack low, 2026-10-31 (addendum 2026-10-31b): the
    # head 3/4" nearer grade, the shafts 3/4" shorter. GW's soft end closes at 1/δ 0.0076.
    "PT-BW-RE": (1.2988, 1.9309, Status.OK),
    "PT-BW-RNE": (1.2892, 1.8486, Status.OK),
    # The four landing rows (W, E, GW, GE) went 2026-11-22: decision 16 pins and props
    # those piers as footing piers, so a fixed-base sway reading of them describes nothing.
    # The balcony, re-worked 2026-11-23 (note balcony_moment_columns.md §26): each column on its
    # beam's STATICS reaction plus the planter, P_u 5,196.3 (front) / 6,095.4 (rear). The hand
    # script (scratchpad hand_delta.py, from §4's wall-top spring, Pc = Pc_rigid/(1 + 3/R)
    # with the exact-spring root as the cap) reads R 6.838 / 6.450 front, 6.763 / 6.379 rear.
    "PT-SG-BF1": (1.0456, 1.0465, Status.OK),
    "PT-SG-BF3": (1.0456, 1.0465, Status.OK),
    "PT-SG-BR1": (1.0545, 1.0556, Status.OK),
    "PT-SG-BR3": (1.0545, 1.0556, Status.OK),
}
_LANDING = ("PT-BW-W", "PT-BW-E", "PT-BW-GW", "PT-BW-GE")
_ORACLE = {tag: row for tag, row in _WORKED.items() if tag not in _LANDING}


@pytest.fixture(scope="module")
def ectx(catlin_cast_ctx):
    return engineering_context(catlin_cast_ctx)


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

    for tag in _WORKED:
        pier, column, _points_ = _points(ectx, tag)
        rigid = spring.magnifier(column.pu_lb, column.pc_rigid_lb)
        assert rigid == pytest.approx(_sway_magnifier(pier, pier.factored_lb)[1], rel=1e-9)
        assert _Point.at("", column, 1e15).delta == pytest.approx(rigid, rel=1e-6)


@pytest.mark.parametrize("tag", sorted(_WORKED))
def test_both_band_ends_reproduce_the_note(tag, ectx) -> None:
    stiff, soft, _status = _WORKED[tag]
    _pier, _column, (at_stiff, at_soft) = _points(ectx, tag)
    assert at_stiff.delta == pytest.approx(stiff, abs=0.002)
    if soft is None:
        assert at_soft.delta is None
    elif soft > 10.0:
        # Near-singular: 0.1 lb of P_u moves δ ~0.5%. Pin 1/δ = 1 - P_u/(0.75 Pc), which is
        # what the note works, to ~0.7 lb of P_u.
        assert 1.0 / at_soft.delta == pytest.approx(1.0 / soft, abs=1e-4)
    else:
        assert at_soft.delta == pytest.approx(soft, abs=0.002, rel=1e-3)


@pytest.mark.parametrize("tag", sorted(_ORACLE))
def test_the_record_reproduces_the_notes_verdict(tag, catlin_cast_ctx) -> None:
    record = catlin_cast_ctx.engineering[f"{KIND}/{tag}"]
    assert record.status is _ORACLE[tag][2], (record.summary, record.missing)
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["subgrade_modulus_measured"] == 0.0
    assert inputs["n_h_presumed"] == 1.0
    assert any("NOT GRADED" in n for n in record.notes)
    if record.status is Status.INCOMPLETE:
        assert "Site.lateral_subgrade_modulus" in record.missing[0]


#: §10: Terzaghi's loose dry sand, 7 tons/ft³ = 8.10 pci, the pole at unit width.
_PRESUMED = {"PT-BW-RE": (2.7792e7, 4.5893, 41_523.0, 1.3185),
             "PT-BW-RNE": (2.7792e7, 4.5893, 41_523.0, 1.3185)}


@pytest.mark.parametrize("tag", sorted(_PRESUMED))
def test_the_presumed_n_h_reproduces_section_10(tag, catlin_cast_ctx) -> None:
    """§10: both canopy columns close on the presumed n_h — the pad earns no width."""
    k_theta, r, pc, delta = _PRESUMED[tag]
    record = catlin_cast_ctx.engineering[f"{KIND}/{tag}"]
    inputs = {q.name: q.value for q in record.inputs}
    assert inputs["subgrade_modulus_pci"] == pytest.approx(8.10)
    assert inputs["base_spring"] == pytest.approx(k_theta, rel=2e-3)
    assert inputs["spring_ratio_R"] == pytest.approx(r, abs=2e-3)
    assert inputs["Pc_flexible"] == pytest.approx(pc, rel=1e-3)
    increment = next(s for s in record.limit_states if s.name == "second-order increment")
    assert increment.demand == pytest.approx(delta - 1.0, abs=5e-4)
    assert record.governing.name == "second-order increment"
    assert any("THE SOIL IS PRESUMED" in n for n in record.notes)


@pytest.mark.parametrize("tag,ratio", [("PT-SG-BF1", 0.4251), ("PT-SG-BR1", 0.4297)])
def test_the_flexible_delta_magnifies_every_pair_and_the_worst_governs(
        tag, ratio, catlin_cast_ctx) -> None:
    """B-04: 0.178 was the flexible delta on one non-governing pair (the guard at 1.6L). Every
    §2.3.1 pair now takes it against its own phi*Mn; the floor-empty wind + guard pair at
    the lowest axial governs, 10,142 lb-ft against 23,857."""
    record = catlin_cast_ctx.engineering[f"{KIND}/{tag}"]
    assert record.governing.name == "magnified moment (sway), flexible base"
    assert record.governing.ratio == pytest.approx(ratio, abs=0.0005)
    assert "L_guard, floor live absent" in record.governing.citation
    notes = " ".join(record.notes)
    assert "HEAD DRIFT" in notes and "SEISMIC" in notes and "SDC A" in notes
    assert "WHICH Pc IS GRADED" in notes


def test_the_keys_are_column_bases_plus_the_wall_borne_columns(catlin_cast_ctx, ectx) -> None:
    from typehaus.engineering import keys_of

    assert set(keys_of(KIND, ectx)) == set(_ORACLE)
    assert set(keys_of("column_base", ectx)) < set(keys_of(KIND, ectx))


def test_active_kdat_pinned_east_posts_need_no_cast_column_rotation(catlin_ctx) -> None:
    from typehaus.engineering import keys_of

    keys = set(keys_of(KIND, catlin_ctx.engineering.context))
    assert keys == {"PT-SG-BF1", "PT-SG-BF3", "PT-SG-BR1", "PT-SG-BR3"}
    assert not {"PT-BW-RE", "PT-BW-RNE"} & keys


def test_the_pole_residue_names_the_shaft_pad_split(catlin_cast_ctx) -> None:
    """Plan rule 12: the deferral's residue must not vanish with it."""
    notes = " ".join(catlin_cast_ctx.engineering[f"{KIND}/PT-BW-RE"].notes)
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
    assert fingerprint(after["PT-BW-RNE"]) != fingerprint(before["PT-BW-RNE"])


def test_the_subgrade_modulus_round_trips_on_the_site() -> None:
    site = Site(lat=45.0, lon=-93.0, elevation=0.0,  # type: ignore[arg-type]
                lateral_subgrade_modulus=SubgradeModulus(
                    n_h_pci=12.5, source="report", basis="correlated", k_v_pci=80.0))
    assert Site.model_validate_json(site.model_dump_json()) == site
    assert "SubgradeModulus" in constructor_names()
    assert Site.model_fields["lateral_subgrade_modulus"].default is None
