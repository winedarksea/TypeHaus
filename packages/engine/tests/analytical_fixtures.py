"""A hand-solvable portal frame every analytical emitter and the solver test against.

Two 12" round cast columns 3 m tall, fixed at the base, 4 m apart along X; a 3.5 x 11.875
glulam beam between their tops with both moments released (it bears on them). One dead line
load and one wind push. Because the beam ends are released, each column is a cantilever and
the frame is solvable on paper:

* dead  — 2,000 N/m over 4 m = 8,000 N, split 4,000 N onto each base; zero base moment.
* wind  — 1,000 N at each column top in +X: base shear 1,000 N and base moment
          1,000 N x 3 m = 3,000 N.m at each base, both columns alike.

Any reader that cannot reproduce those two numbers has mis-read the graph, not the frame.
"""

from __future__ import annotations

from typehaus.analytical.graph import (
    AnalyticalModel,
    Fixity,
    LoadCase,
    LoadCaseKind,
    Member,
    MemberLoad,
    Node,
    NodeLoad,
    Releases,
    Support,
)
from typehaus.resolve.framing.profiles import CrossSection

_IN = 0.0254
COLUMN = CrossSection(shape="round", width_m=12 * _IN, depth_m=12 * _IN)
BEAM = CrossSection(shape="rect", width_m=3.5 * _IN, depth_m=11.875 * _IN)

SPAN_M = 4.0
HEIGHT_M = 3.0
DEAD_N_M = 2000.0
WIND_N = 1000.0

EXPECTED_BASE_VERTICAL_N = DEAD_N_M * SPAN_M / 2      # 4,000 N per base, dead case
EXPECTED_BASE_MOMENT_NM = WIND_N * HEIGHT_M             # 3,000 N.m per base, wind case
EXPECTED_BASE_SHEAR_N = WIND_N                          # 1,000 N per base, wind case


def portal_frame() -> AnalyticalModel:
    nodes = (
        Node("N-W-BASE", 0.0, 0.0, 0.0),
        Node("N-W-TOP", 0.0, 0.0, HEIGHT_M),
        Node("N-E-BASE", SPAN_M, 0.0, 0.0),
        Node("N-E-TOP", SPAN_M, 0.0, HEIGHT_M),
    )
    members = (
        Member(id="PT-W", tag="PT-W", category="column", n0="N-W-BASE", n1="N-W-TOP",
               section=COLUMN, material="concrete f'c 4000 psi", e_pa=2.48e10,
               e_basis="assumed: ACI 318-19 19.2.2.1, 57000*sqrt(f'c) psi",
               item_ids=("deck_post/PT-W",), physical_uid="uid-pt-w"),
        Member(id="PT-E", tag="PT-E", category="column", n0="N-E-BASE", n1="N-E-TOP",
               section=COLUMN, material="concrete f'c 4000 psi", e_pa=2.48e10,
               e_basis="assumed: ACI 318-19 19.2.2.1, 57000*sqrt(f'c) psi",
               item_ids=("deck_post/PT-E",), physical_uid="uid-pt-e"),
        Member(id="BM-1", tag="BM-1", category="beam", n0="N-W-TOP", n1="N-E-TOP",
               section=BEAM, material="glulam", e_pa=1.24e10,
               e_basis="assumed: 24F-V4 glulam, 1.8e6 psi",
               releases=Releases(i_moment=True, j_moment=True),
               item_ids=(), physical_uid="uid-bm-1"),
    )
    supports = (
        Support("N-W-BASE", Fixity.FIXED, "fixture: cast column doweled to its pad",
                item_id="deck_post/PT-W", element_tag="PT-W"),
        Support("N-E-BASE", Fixity.FIXED, "fixture: cast column doweled to its pad",
                item_id="deck_post/PT-E", element_tag="PT-E"),
    )
    cases = (
        LoadCase(LoadCaseKind.DEAD, "fixture dead load"),
        LoadCase(LoadCaseKind.WIND, "fixture wind push, +X"),
    )
    member_loads = (
        MemberLoad(LoadCaseKind.DEAD, "BM-1", "GZ", -DEAD_N_M, -DEAD_N_M,
                   source="fixture"),
    )
    node_loads = (
        NodeLoad(LoadCaseKind.WIND, "N-W-TOP", fx_n=WIND_N, source="fixture"),
        NodeLoad(LoadCaseKind.WIND, "N-E-TOP", fx_n=WIND_N, source="fixture"),
    )
    return AnalyticalModel(
        nodes=nodes, members=members, supports=supports, cases=cases,
        member_loads=member_loads, node_loads=node_loads,
        scope=("deck_post/PT-E", "deck_post/PT-W"),
        assumptions=("fixture: beam bears on the column tops, both moments released",),
        gaps=(),
    )
