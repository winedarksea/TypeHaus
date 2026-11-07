"""``routing/supply_tree`` against ``mep_supply_trunk_basis.md`` (PR-B-CW-TRUNK by hand).

§1's 19 trunk vertices give 84.028 ft over 18 legs and §2's tee stations; §4's keys give the
laying order; §5's two windows give the z gate [-9.6875", -2.1875"]. Synthetic graphs only."""

from __future__ import annotations

import numpy as np
import pytest
from _helpers import CATLIN

from typehaus.quantities import M_PER_IN
from typehaus.routing import supply_tree as st

IN = M_PER_IN
FT = 12 * IN
#: §1.1, project-frame inches.
TRUNK_IN = [(136, 420, -107.4375), (136, 420, -61.4375), (136, 420, -14.8), (136, 418, -14.8),
            (114, 418, -14.8), (114, 418, -8.8), (57, 418, -8.8), (57, 418, -16.0),
            (57, 386.5, -16.0), (57, 386.5, -8.8), (57, 192, -8.8), (96, 192, -8.8),
            (200, 192, -8.8), (200, 180, -8.8), (357.6, 180, -8.8), (357.6, 424.2, -8.8),
            (357.6, 424.2, 10.56), (357.6, 421.5, 10.56), (357.6, 421.5, 20.0)]
TRUNK = [(x * IN, y * IN, z * IN) for x, y, z in TRUNK_IN]


def test_the_authored_trunk_is_84_ft_over_18_legs() -> None:
    assert len(TRUNK) - 1 == 18
    assert abs(st.developed_m(TRUNK) / (12 * IN) - 84.028) < 0.05


def test_tees_land_at_the_note_s_stations() -> None:
    """§2's ``s`` column, from each tee point's position on the trunk."""
    tees = {  # (x, y, z) inches -> s in ft
        (136, 420, -61.44): 3.83, (57, 192, -8.8): 35.00, (71.25, 192, -8.8): 36.19,
        (72, 192, -8.8): 36.25, (84, 192, -8.8): 37.25, (100, 192, -8.8): 38.59,
        (110, 192, -8.8): 39.42, (139.5, 192, -8.8): 41.88, (206.5, 180, -8.8): 48.46,
        (357.6, 421.5, 20.0): 84.03}
    for point, expected in tees.items():
        s = st.station_m(TRUNK, tuple(v * IN for v in point))
        assert s is not None and abs(s / FT - expected) < 0.05, (point, s)
    assert st.station_m(TRUNK, (0.0, 0.0, 0.0)) is None


def test_farthest_first_is_the_note_s_order_and_ties_break_on_tag() -> None:
    keys = {"SBATH": 95.44, "SUITE": 92.60, "HYD": 77.65, "WH": 69.24, "SAUNA": 62.19,
            "BATH-WC": 59.42, "BATH2": 57.13, "WASH": 53.24, "BATH1": 47.80,
            "BATH2-SH": 44.89, "FILLER": 39.27, "HYDRANT": 27.39}
    assert st.farthest_first(keys) == list(keys)
    assert st.farthest_first({"B": 1.0, "A": 1.0, "C": 2.0}) == ["C", "A", "B"]


def test_the_gate_is_the_two_windows_less_the_pipe_radius() -> None:
    """§5: I-joist -10.500..-1.375 and truss -10.375..-1.500, 1 1/4" PEX (r 0.6875")."""
    radius = 0.6875 * IN
    gate = st.gate_for([(-10.5 * IN, -1.375 * IN), (-10.375 * IN, -1.5 * IN)],
                       member_low_m=-11.875 * IN, radius_m=radius)
    assert gate is not None
    assert abs(gate.hi_m / IN - (-2.1875)) < 1e-9
    assert abs(gate.planes[1] / IN - (-5.9375)) < 1e-9  # mid of [-9.6875, -2.1875]
    assert gate.lo_m < gate.planes[0] < gate.planes[1] < gate.hi_m
    assert st.gate_for([(-3 * IN, -2 * IN)], -11.875 * IN, radius) is None  # narrower than pipe
    assert st.gate_for([], -11.875 * IN, radius) is None


def test_the_gate_blocks_level_flight_outside_it_except_in_the_riser_holes() -> None:
    gate = st.Gate(lo_m=-0.5, hi_m=-0.1, planes=(-0.4, -0.2))
    under, over = st.gate_prisms((0.0, 0.0, 10.0, 10.0), gate, [(2.0, 2.0)])
    assert over.blocks((5.0, 5.0), 0.3) and under.blocks((5.0, 5.0), -0.9)
    assert not over.blocks((5.0, 5.0), -0.3) and not under.blocks((5.0, 5.0), -0.3)
    assert not over.blocks((2.0, 2.0), 0.3) and not under.blocks((2.5, 2.0), -0.9)
    assert over.blocks((2.0 + 1.1 * st.HOLE_M, 2.0), 0.3)


def test_two_floor_systems_leave_only_their_bands_open() -> None:
    a, b = st.Gate(-0.5, -0.1, (-0.4,)), st.Gate(2.5, 2.9, (2.6,))
    prisms = st.gate_prisms((0.0, 0.0, 10.0, 10.0), [b, a], [])
    assert len(prisms) == 3
    free = [z for z in (-0.3, 2.7)]
    blocked = [-0.9, 1.0, 3.5]
    assert not any(p.blocks((5.0, 5.0), z) for p in prisms for z in free)
    assert all(any(p.blocks((5.0, 5.0), z) for p in prisms) for z in blocked)


def test_a_run_carries_what_the_sizing_table_says() -> None:
    table = ((0.5, 4.0), (0.75, 14.0), (1.0, 32.0), (1.25, 64.0))
    assert [st.capacity_wsfu(d * IN, table) for d in (0.375, 0.5, 0.75, 1.25)] == [
        0.0, 4.0, 14.0, 64.0]


def test_groups_follow_the_tie_chain_and_serves_flow_up_the_tees() -> None:
    parent = {"A": "T", "A1": "A", "A2": "A1", "B": "T", "T": None}
    assert [st.group_of(parent, "T", t) for t in ("A", "A1", "A2", "B", "T")] == [
        "A", "A", "A", "B", ""]
    own = {"trunk": ("K",), "br": (), "x": ("F1",), "y": ("F2",)}
    tee = {"br": None, "x": "br", "y": "x"}
    got = st.downstream_serves(own, tee, ("K", "F1", "F2"))
    assert got["br"] == ("F1", "F2") and got["x"] == ("F1", "F2") and got["y"] == ("F2",)
    assert got["trunk"] == ("K",)


def test_terminals_are_fixture_ends_ports_and_stubs_not_distribution_runs() -> None:
    kids = {"T": ["D", "W"], "D": ["F1", "F2"], "W": ["C"]}
    own = {"T": ("K",), "D": (), "F1": ("a",), "F2": ("b",), "W": (), "C": ("c",)}
    got = st.terminal_tags(["T", "D", "F1", "F2", "W", "C", "S"], {**own, "S": ()},
                           {**kids}, frozenset({"W"}))
    assert got == ["T", "F1", "F2", "W", "C", "S"]  # D distributes; W feeds a heater; S is a stub


def test_clip_keeps_the_stretch_in_a_box_with_z_interpolated() -> None:
    line = [(0.0, 0.0, 0.0), (10.0, 0.0, 10.0), (10.0, 10.0, 10.0)]
    (piece,) = st.clip_polyline(line, (2.0, -1.0, 12.0, 4.0))
    assert piece[0] == (2.0, 0.0, 2.0) and piece[-1] == (10.0, 4.0, 10.0)
    assert st.clip_polyline(line, (20.0, 20.0, 30.0, 30.0)) == []


def test_nodes_on_a_line_honour_its_elevation_and_a_riser_holds_every_z() -> None:
    xyz = np.array([(0, 0, 0), (1, 0, 0), (1, 0, 5), (1, 0.5, 0), (2, 0, 1)], dtype=float)
    level = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
    assert st.nodes_on(xyz, level, tol_m=0.01, z_tol_m=0.01) == {0, 1}
    riser = [(1.0, 0.0, -1.0), (1.0, 0.0, 6.0)]
    assert st.nodes_on(xyz, riser, tol_m=0.01, z_tol_m=0.01) == {1, 2}


@pytest.mark.autorouter
def test_catlin_cold_trunk_lays_inside_the_gate_with_no_refusal(request) -> None:
    """``--tree PR-B-CW-TRUNK --topology trunk``, for real (opt-in, minutes): the trunk is no
    longer than 1.1x the authored 84.028 ft (§3 S1), the whole tree no longer than 1.1x S3'
    (449.779 ft), nothing refused, and every level trunk leg rides the §5 gate."""
    from typehaus.cli.cmd_route import _route_cost
    from typehaus.cli.cmd_route_supply_tree import propose_supply_tree
    from typehaus.cli.route_options import RouteOptions

    model = request.getfixturevalue("catlin_model_ro")
    opts = RouteOptions(
        directory=CATLIN, cost=_route_cost(CATLIN), out_dir=None, as_json=False,
        summary=False, explain=False, details=False, evaluate=False, margin_ft=8.0,
        level=None, band=None, avoid=frozenset(), via=(), slope=None, alternatives=1,
        timing=None)
    made, problems, _notices, refusals = propose_supply_tree(
        model, "PR-B-CW-TRUNK", "trunk", opts)
    assert not refusals and not problems, problems
    trunk = made[0][0]
    assert trunk.tag == "PR-B-CW-TRUNK-PROPOSED"
    assert st.developed_m(trunk.points) / FT <= 1.1 * 84.028
    assert sum(st.developed_m(p.points) for p, _s in made) / FT <= 1.1 * 449.779
    gate = (-23.19 * IN, -2.1875 * IN)
    for a, b in zip(trunk.points, trunk.points[1:], strict=False):
        if abs(a[2] - b[2]) < 1e-6:  # a level leg: the gate (a riser stands in a hole)
            assert gate[0] - 1e-3 <= a[2] <= gate[1] + 1e-3
