"""The portal frame, solved. If PyNite disagrees with the hand pass, the export is wrong.

``analytical_fixtures.portal_frame`` states the two numbers on paper: 4,000 N per base under
dead, and 1,000 N shear with 3,000 N.m of moment per base under wind. Nothing here recomputes
them — they come from the fixture's own module constants, so the note and the test cannot
drift apart.
"""

from __future__ import annotations

import pytest
from analytical_fixtures import (
    BEAM,
    EXPECTED_BASE_MOMENT_NM,
    EXPECTED_BASE_SHEAR_N,
    EXPECTED_BASE_VERTICAL_N,
    portal_frame,
)

from typehaus.analytical.graph import (
    AnalyticalModel,
    Fixity,
    LoadCase,
    LoadCaseKind,
    Member,
    MemberLoad,
    Node,
    Releases,
    Support,
)
from typehaus.analytical.pynite_map import build_inputs, section_properties, support_label
from typehaus.analytical.solve import solve

_TOL = 0.005          # 0.5%
_BASES = ("N-W-BASE", "N-E-BASE")


@pytest.fixture(scope="module")
def result():
    return solve(portal_frame())


def test_frame_is_stable(result):
    assert result.stable, result.warnings
    assert result.warnings == ()


@pytest.mark.parametrize("node", _BASES)
def test_dead_case_lands_half_the_beam_on_each_base(result, node):
    reaction = result.reactions[(node, "dead")]
    assert reaction.fz_n == pytest.approx(EXPECTED_BASE_VERTICAL_N, rel=_TOL)
    # The beam ends are moment-released, so a symmetric gravity load raises no base moment.
    assert abs(reaction.my_nm) < 1e-6
    assert abs(reaction.fx_n) < 1e-6


@pytest.mark.parametrize("node", _BASES)
def test_wind_case_is_a_cantilever_at_each_base(result, node):
    reaction = result.reactions[(node, "wind")]
    # The frame is in the XZ plane, so it bends about global Y. A reaction opposes the push:
    # +X at the top gives a negative base FX.
    assert reaction.fx_n == pytest.approx(-EXPECTED_BASE_SHEAR_N, rel=_TOL)
    assert abs(reaction.my_nm) == pytest.approx(EXPECTED_BASE_MOMENT_NM, rel=_TOL)
    assert abs(reaction.fz_n) < 1e-6
    assert abs(reaction.mz_nm) < 1e-6


def test_beam_carries_wl2_over_8(result):
    # 2,000 N/m over 4 m = 4,000 N.m, and it must land on the STRONG axis: the whole point
    # of putting the depth-axis inertia in Iy under a Z-up mapping.
    extremes = result.member_extremes[("BM-1", "dead")]
    assert extremes.max_abs_moment_nm == pytest.approx(4000.0, rel=_TOL)
    assert extremes.max_abs_shear_n == pytest.approx(4000.0, rel=_TOL)


def test_columns_take_the_wind_moment(result):
    for member in ("PT-W", "PT-E"):
        extremes = result.member_extremes[(member, "wind")]
        assert extremes.max_abs_moment_nm == pytest.approx(EXPECTED_BASE_MOMENT_NM, rel=_TOL)
        assert result.member_extremes[(member, "dead")].max_axial_n == pytest.approx(
            EXPECTED_BASE_VERTICAL_N, rel=_TOL, abs=1.0
        )


def test_section_properties_put_the_depth_inertia_in_iy():
    frame = portal_frame()
    beam = frame.member("BM-1")
    area, iy, iz, j = section_properties(beam.section)
    assert area == pytest.approx(3.5 * 11.875)
    assert iy == pytest.approx(3.5 * 11.875**3 / 12.0)
    assert iz == pytest.approx(11.875 * 3.5**3 / 12.0)
    # Saint-Venant J for a thin rectangle is ~0.29*h*b^3, i.e. a few times Iz (h*b^3/12)
    # and far below the strong-axis Iy.
    assert iz < j < iy

    column = frame.member("PT-W")
    c_area, c_iy, c_iz, c_j = section_properties(column.section)
    assert c_area == pytest.approx(3.14159265 * 144.0 / 4.0, rel=1e-6)
    assert c_iy == pytest.approx(c_iz)
    assert c_j == pytest.approx(2.0 * c_iy)


def test_inputs_are_sorted_and_carry_one_combo_per_case():
    inputs = build_inputs(portal_frame())
    assert [n[0] for n in inputs.nodes] == sorted(n[0] for n in inputs.nodes)
    assert inputs.combos == (("dead", (("dead", 1.0),)), ("wind", (("wind", 1.0),)))
    # A moment release frees Ry and Rz at that end and nothing else.
    (name, flags), = inputs.releases
    assert name == "BM-1"
    assert flags == (False, False, False, False, True, True,
                     False, False, False, False, True, True)
    # Self weight is deliberately absent: every rho is zero.
    assert all(material[4] == 0.0 for material in inputs.materials)


def test_supports_pin_translations_and_fix_rotations_only_when_fixed():
    inputs = build_inputs(portal_frame())
    for _node, dx, dy, dz, rx, ry, rz in inputs.supports:
        assert (dx, dy, dz) == (True, True, True)
        assert (rx, ry, rz) == (True, True, True)   # the fixture's bases are FIXED


def _beam_on_two_walls(rotations):
    """A beam bearing on two walls: pinned both ends, both moments released.

    The case ``Support.rotations`` exists for. With no rotational restraint the node has no
    rotational stiffness at all and PyNite calls it what it is: a mechanism.
    """
    return AnalyticalModel(
        nodes=(Node("A", 0.0, 0.0, 3.0), Node("B", 4.0, 0.0, 3.0)),
        members=(Member(id="BM", tag="BM", category="beam", n0="A", n1="B", section=BEAM,
                        material="glulam", e_pa=1.24e10, e_basis="fixture",
                        releases=Releases(i_moment=True, j_moment=True)),),
        supports=tuple(Support(node, Fixity.PINNED, "bears on a wall", rotations=rotations)
                       for node in ("A", "B")),
        cases=(LoadCase(LoadCaseKind.DEAD, "fixture"),),
        member_loads=(MemberLoad(LoadCaseKind.DEAD, "BM", "GZ", -2000.0, -2000.0),),
    )


def test_support_rotations_reach_def_support_verbatim():
    inputs = build_inputs(_beam_on_two_walls((True, False, False)))
    assert inputs.supports == (("A", True, True, True, True, False, False),
                               ("B", True, True, True, True, False, False))
    # A support with no `rotations` still follows its fixity.
    assert all(row[4:] == (True, True, True) for row in build_inputs(portal_frame()).supports)


def test_an_unrestrained_released_beam_end_is_reported_not_raised():
    result = solve(_beam_on_two_walls(None))
    assert result.stable is False
    assert result.reactions == {}
    # PyNite PRINTS the diagnosis and then raises; both have to survive into `warnings`.
    joined = " ".join(result.warnings)
    assert "Nodal instability" in joined
    assert "node A" in joined


def test_restraining_the_node_rotations_costs_the_released_beam_nothing():
    result = solve(_beam_on_two_walls((True, True, True)))
    assert result.stable, result.warnings
    reaction = result.reactions[("A", "dead")]
    assert reaction.fz_n == pytest.approx(4000.0, rel=_TOL)
    # Restraining a node whose only member end is moment-released raises NO reaction moment,
    # which is why it is the right cure for the mechanism rather than a hidden fixed base.
    assert abs(reaction.mx_nm) < 1e-6
    assert abs(reaction.my_nm) < 1e-6
    assert result.member_extremes[("BM", "dead")].max_abs_moment_nm == pytest.approx(
        4000.0, rel=_TOL)


def test_support_label_names_the_extra_rotations():
    assert support_label(Support("A", Fixity.PINNED, "w")) == "pinned"
    assert support_label(Support("A", Fixity.FIXED, "w")) == "fixed"
    assert support_label(Support("A", Fixity.PINNED, "w", rotations=(True, False, False))) == (
        "pinned+RX")
    assert support_label(
        Support("A", Fixity.PINNED, "w", rotations=(True, True, True)), " "
    ) == "pinned RX RY RZ"
    # A FIXED support that releases a rotation is named too, not silently downgraded.
    assert support_label(
        Support("A", Fixity.FIXED, "w", rotations=(True, True, False))) == "fixed+RX+RY"
