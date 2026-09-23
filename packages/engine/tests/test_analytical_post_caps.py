"""A column top under a CONTINUOUS beam is a post cap: hinged in the beam's plane only.

The bent, on paper: two fixed-base 12" round columns 3 m tall at y = 1 and y = 5, under one
beam running along Y from y = 0 to y = 7 (1 m and 2 m cantilevers), 2,000 N/m dead. With
the tops hinged about X the beam is statically determinate on two vertical supports:
R1 = 14,000 x (5 - 3.5) / 4 = 5,250 N, R2 = 8,750 N, and no base moment. A 1,000 N push in
+Y at one top is shared by two pin-topped cantilevers through the beam's axial stiffness,
so the pair's base moments sum to 1,000 x 3 = 3,000 N.m.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from analytical_fixtures import BEAM, COLUMN

from typehaus.analytical.graph import (
    AnalyticalModel,
    Fixity,
    LoadCase,
    LoadCaseKind,
    Member,
    MemberLoad,
    Node,
    NodeLoad,
    Support,
)
from typehaus.analytical.post_caps import apply_post_caps
from typehaus.analytical.pynite_map import build_inputs
from typehaus.analytical.solve import solve

H = 3.0
W = 2000.0


def _column(tag: str) -> Member:
    return Member(id=tag, tag=tag, category="column", n0=f"{tag}:base", n1=f"{tag}:top",
                  section=COLUMN, material="concrete f'c 4000 psi", e_pa=2.48e10,
                  e_basis="fixture")


def _beam(member_id: str, n0: str, n1: str, tag: str = "BM") -> Member:
    return Member(id=member_id, tag=tag, category="beam", n0=n0, n1=n1, section=BEAM,
                  material="glulam", e_pa=1.24e10, e_basis="fixture")


def _bent(fixity: Fixity = Fixity.FIXED):
    nodes = (Node("BM:i", 0, 0, H), Node("A:top", 0, 1, H), Node("B:top", 0, 5, H),
             Node("BM:j", 0, 7, H), Node("A:base", 0, 1, 0), Node("B:base", 0, 5, 0))
    members = (_column("A"), _column("B"), _beam("BM#1", "BM:i", "A:top"),
               _beam("BM#2", "A:top", "B:top"), _beam("BM#3", "B:top", "BM:j"))
    rotations = None if fixity is Fixity.FIXED else (False, True, True)
    supports = tuple(Support(f"{t}:base", fixity, "fixture", rotations=rotations)
                     for t in ("A", "B"))
    graph = SimpleNamespace(nodes=nodes, members=members, assumptions=(),
                            post_top={"A": "A:top", "B": "B:top"},
                            post_base={"A": "A:base", "B": "B:base"},
                            beam_axis_xy={"BM": (0.0, 1.0)})
    return graph, supports


def _model(graph, supports) -> AnalyticalModel:
    return AnalyticalModel(
        nodes=graph.nodes, members=graph.members, supports=supports,
        cases=(LoadCase(LoadCaseKind.DEAD, "fixture"), LoadCase(LoadCaseKind.WIND, "fx")),
        member_loads=tuple(MemberLoad(LoadCaseKind.DEAD, m, "GZ", -W, -W)
                           for m in ("BM#1", "BM#2", "BM#3")),
        node_loads=(NodeLoad(LoadCaseKind.WIND, "A:top", fy_n=1000.0),),
        assumptions=graph.assumptions)


def test_a_continuous_beam_hinges_the_column_tops_about_the_axis_across_it():
    graph, supports = _bent()
    assert apply_post_caps(graph, supports) == ()
    columns = {m.id: m for m in graph.members if m.is_vertical}
    for member in columns.values():
        assert member.releases.j_hinge == "X" and not member.releases.j_moment
        assert "held against its roll" in member.releases.basis
    assert any(a.startswith("post cap:") for a in graph.assumptions)
    # X on a Z-vertical member is PyNite's local z: Rz free, Ry held.
    flags = dict(build_inputs(_model(graph, supports)).releases)["A"]
    assert flags == (False,) * 10 + (False, True)


def test_the_hinged_bent_solves_to_statics_and_carries_no_gravity_base_moment():
    graph, supports = _bent()
    apply_post_caps(graph, supports)
    result = solve(_model(graph, supports))
    assert result.stable, result.warnings
    dead_a, dead_b = (result.reactions[(f"{t}:base", "dead")] for t in "AB")
    assert dead_a.fz_n == pytest.approx(5250.0, rel=1e-3)
    assert dead_b.fz_n == pytest.approx(8750.0, rel=1e-3)
    for reaction in (dead_a, dead_b):
        assert abs(reaction.mx_nm) < 1e-3 and abs(reaction.fy_n) < 1e-3
    wind = [result.reactions[(f"{t}:base", "wind")] for t in "AB"]
    assert sum(r.fy_n for r in wind) == pytest.approx(-1000.0, rel=1e-6)
    assert sum(abs(r.mx_nm) for r in wind) == pytest.approx(1000.0 * H, rel=1e-3)


def test_a_rigid_knee_is_what_the_hinge_replaces():
    """Without the cap pass the same bent is a portal: a gravity base moment appears."""
    graph, supports = _bent()
    result = solve(_model(graph, supports))
    assert abs(result.reactions[("B:base", "dead")].mx_nm) > 100.0


def test_a_pinned_base_leaves_the_knee_rigid_and_says_so():
    graph, supports = _bent(Fixity.PINNED)
    gaps = apply_post_caps(graph, supports)
    assert len(gaps) == 2 and all("RIGID knee" in g and "free about global X" in g
                                  for g in gaps)
    assert not any(m.releases.any for m in graph.members)


def test_two_crossing_continuous_beams_leave_the_knee_rigid_and_say_so():
    graph, supports = _bent()
    graph.nodes += (Node("X:i", -1, 1, H), Node("X:j", 1, 1, H))
    graph.members += (_beam("X#1", "X:i", "A:top", "X"), _beam("X#2", "A:top", "X:j", "X"))
    graph.beam_axis_xy["X"] = (1.0, 0.0)
    gaps = apply_post_caps(graph, supports)
    assert gaps == (next(g for g in gaps if g.startswith("A: the post cap is left a RIGID")
                         and "different directions" in g),)
    assert {m.id for m in graph.members if m.releases.any} == {"B"}


def test_the_ifc_states_the_hinge_in_the_members_local_frame():
    """IFC local z is the Axis (global X on a column), y = z x x = -Y: X frees Rz only."""
    from typehaus.emit.ifc.analytical import _end_rotations, _release_text

    graph, supports = _bent()
    apply_post_caps(graph, supports)
    column = next(m for m in graph.members if m.id == "A")
    assert _end_rotations(column, "j") == (True, True, False)
    assert _end_rotations(column, "i") is None
    assert _release_text(column).startswith("j: hinge about global X (post cap under BM")
