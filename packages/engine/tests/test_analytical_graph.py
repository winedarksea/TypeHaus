"""``build_analytical_model`` on the reference house.

The graph is a set of structural CLAIMS — which node a beam lands on, what a column base
restrains, what pushes on it and in which case — so what is asserted here is the claims,
not the shape of the dataclasses. Three of them are load-bearing enough to name:

* the balcony's fixed-base columns, which are catlin's whole lateral system: a pinned base
  there reverses the answer (``notes/balcony_moment_columns.md``);
* a load that disagrees with the record it came from, which would make the handover
  self-contradicting rather than merely incomplete;
* byte-determinism, without which ``haus handoff``'s manifest of sha256s proves nothing.

Loaded once at module scope: resolving catlin and running every calculation is the
expensive part, and this module asks the same model a dozen questions.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from typehaus.analytical.build import build_analytical_model
from typehaus.analytical.graph import NODE_SNAP_M, Fixity, LoadCaseKind
from typehaus.analytical.loads import PLF_TO_N_M
from typehaus.engineering.pier_basis import cast_piers

_HOUSE = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_engineering():
    from typehaus.cli.engineering_load import load_engineering

    return load_engineering(_HOUSE)


@pytest.fixture(scope="module")
def analytical(catlin_engineering):
    return build_analytical_model(catlin_engineering.ctx)


def _items_of(model, kind: str) -> set[str]:
    return {item for item in model.scope if item.startswith(f"{kind}/")}


def test_every_graded_member_item_reaches_a_member(analytical) -> None:
    """A deck post and a roof beam both have a curve member to their name.

    ** ``post_bearing`` WAS THE THIRD KIND HERE UNTIL 2026-09-14. ** It left because catlin
    stopped posing the question: both centre balcony pillars came off ``FS-SG-PORCH`` and
    onto the cast column tops, and ``engineering/post_bearing.py`` enumerates a post whose
    ``supported_by`` names a ``FloorSystem`` and nothing else. The register has no
    ``post_bearing/*`` item, so ``_items_of`` returns an empty set and the "fixture has
    drifted" guard below would fire on a house that is simply built differently.

    It is not replaced by a fourth kind, and that is deliberate: the two kinds left are the
    two SHAPES this test is about — a column member and a beam member — and adding a third
    that happens to exist today would pin the register rather than the graph. What catches
    a genuinely missing member is the subset assertion, which runs on every kind the scope
    names via ``test_the_scope_is_covered_or_gapped``.
    """
    carried = {item for member in analytical.members for item in member.item_ids}
    for kind in ("deck_post", "roof_beam"):
        expected = _items_of(analytical, kind)
        assert expected, f"catlin has no {kind} item — the fixture has drifted"
        assert expected <= carried, f"{kind} items with no member: {sorted(expected - carried)}"
    assert _items_of(analytical, "post_bearing") == set(), (
        "catlin has a post_bearing item again — a post stands on a deck, and this test "
        "should go back to asserting that item reaches a member")


def test_lateral_system_columns_are_fixed_and_say_why(analytical, catlin_engineering) -> None:
    piers = {pier.tag for pier in cast_piers(catlin_engineering.ctx) if pier.lateral_system}
    assert piers, "catlin has no lateral-system column — the fixture has drifted"
    by_tag = {support.element_tag: support for support in analytical.supports}
    for tag in sorted(piers):
        support = by_tag.get(tag)
        assert support is not None, f"{tag} has no support node"
        assert support.fixity is Fixity.FIXED, f"{tag} is the lateral system and is not fixed"
        assert "wind" in support.basis.lower(), f"{tag}'s fixity does not say what fixed it"


def test_every_other_post_base_is_pinned(analytical, catlin_engineering) -> None:
    """A base connector that transfers no moment must not be modelled as if it did."""
    lateral = {pier.tag for pier in cast_piers(catlin_engineering.ctx) if pier.lateral_system}
    columns = {member.tag for member in analytical.members if member.category == "column"}
    for support in analytical.supports:
        if support.element_tag in columns and support.element_tag not in lateral:
            assert support.fixity is Fixity.PINNED, (
                f"{support.element_tag} is not the lateral system and must not be fixed")
            assert support.basis, f"{support.element_tag}'s fixity carries no basis"


def test_a_roof_beam_carries_its_records_own_uniform_load(analytical, catlin_engineering) -> None:
    """The line load IS the record's ``uniform_load``, split by its own two pressures."""
    items = _items_of(analytical, "roof_beam")
    assert items, "catlin has no roof_beam item — the fixture has drifted"
    for item in sorted(items):
        record = catlin_engineering.ctx.engineering[item]
        expected = next(q.value for q in record.inputs if q.name == "uniform_load")
        members = {member.id for member in analytical.members if item in member.item_ids}
        by_member: dict[str, float] = {}
        for load in analytical.member_loads:
            if load.member in members and load.direction == "GZ":
                by_member[load.member] = by_member.get(load.member, 0.0) + load.w0_n_m
        assert by_member, f"{item} put no load on its beam"
        for member, total in sorted(by_member.items()):
            assert total == pytest.approx(-expected * PLF_TO_N_M, rel=1e-9), (
                f"{member} carries {total} N/m, not {item}'s {expected} plf")
        cases = {load.case for load in analytical.member_loads if load.member in members}
        assert cases == {LoadCaseKind.DEAD, LoadCaseKind.SNOW}


def test_a_fixed_column_carries_the_shear_that_makes_its_record_s_base_moment(
        analytical, catlin_engineering) -> None:
    """``V x h`` at the top must reproduce the ``wind_base_moment`` the record graded."""
    tops = {support.element_tag: support for support in analytical.supports}
    for pier in cast_piers(catlin_engineering.ctx):
        if not pier.lateral_system or not pier.wind_base_moment_lb_ft:
            continue
        assert pier.tag in tops
        item = f"deck_post/{pier.tag} "
        load = next((load for load in analytical.node_loads
                     if load.case is LoadCaseKind.WIND and load.source.startswith(item)),
                    None)
        assert load is not None, f"{pier.tag} carries no wind load at its top"
        # The load must land on the column's OWN top, not on some other node of the graph.
        column = [member for member in analytical.members if member.tag == pier.tag]
        assert any(load.node in (member.n0, member.n1) for member in column)
        shear_lb = (abs(load.fx_n) + abs(load.fy_n)) / 4.4482216152605
        moment = shear_lb * pier.height_in / 12.0
        assert moment == pytest.approx(pier.wind_base_moment_lb_ft, rel=1e-6)


def test_every_member_reaches_two_real_nodes_and_has_length(analytical) -> None:
    ids = {node.id for node in analytical.nodes}
    assert len(ids) == len(analytical.nodes), "two nodes share an id"
    for member in analytical.members:
        assert member.n0 in ids and member.n1 in ids, f"{member.id} names a missing node"
        assert member.n0 != member.n1, f"{member.id} starts and ends at one node"
        assert analytical.length_m(member) > NODE_SNAP_M, f"{member.id} has no length"


def test_no_two_nodes_are_the_same_point(analytical) -> None:
    """Two nodes inside the snap distance are one node that failed to merge — and a solver
    reading them as two finds a mechanism where the building has a bearing."""
    points = [node.xyz for node in analytical.nodes]
    for index, first in enumerate(points):
        for second in points[index + 1:]:
            distance = sum((a - b) ** 2 for a, b in zip(first, second, strict=True)) ** 0.5
            assert distance > NODE_SNAP_M, f"{first} and {second} are the same node"


def test_the_surface_items_are_named_as_gaps(analytical) -> None:
    """A surface this version cannot draw is listed in words, never left silent."""
    surface = {item for item in analytical.scope
               if item.split("/", 1)[0] in ("retaining_system", "girt_screw")}
    assert surface, "catlin has no surface-member item — the fixture has drifted"
    for item in sorted(surface):
        assert any(line.startswith(f"{item}:") for line in analytical.gaps), (
            f"{item} has no member and no gap line")


def test_a_retaining_wall_is_spoken_for_by_the_shell_stage_and_only_once(analytical) -> None:
    """``shells.py`` meshes it or refuses, and either way it owns the line.

    It used to be listed as "no analytical representation in v1: surface members are a
    follow-on" — a sentence that stopped being true the day the shell stage landed. Two
    lines about one wall, one of them false, is worse than either alone.
    """
    walls = {item for item in analytical.scope if item.startswith("retaining_wall/")}
    assert walls, "catlin has no retaining wall — the fixture has drifted"
    assert not [line for line in analytical.gaps
                if any(line.startswith(f"{item}:") for item in walls)]
    spoken = [line for line in analytical.gaps if "subgrade reaction" in line]
    assert len(spoken) == 1, analytical.gaps
    for item in sorted(walls):
        assert item in spoken[0]


def test_two_builds_are_identical(catlin_engineering) -> None:
    """Byte-determinism, or ``haus handoff``'s manifest of sha256s proves nothing."""
    first = build_analytical_model(catlin_engineering.ctx)
    second = build_analytical_model(catlin_engineering.ctx)
    assert dataclasses.asdict(first) == dataclasses.asdict(second)
    assert repr(first) == repr(second)


def test_every_connected_piece_of_the_frame_reaches_a_support(analytical) -> None:
    """A component with no support is a free body, and a solver reports it as an
    instability at whatever node it happens to eliminate last — nowhere near the seat that
    was never split. Checked here, on the graph, where the answer names the members."""
    parent = {node.id: node.id for node in analytical.nodes}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for member in analytical.members:
        a, b = find(member.n0), find(member.n1)
        if a != b:
            parent[a] = b
    held = {find(support.node) for support in analytical.supports}
    attached = {find(member.n0) for member in analytical.members}
    assert attached <= held, "a run of members hangs on no support"


def test_a_bearing_node_splits_the_member_it_sits_on(analytical) -> None:
    """A node on a member's interior that did not split it is a node the member cannot
    feel — the seat slides along the beam it is set on."""
    inside: list[str] = []
    for member in analytical.members:
        a, b = analytical.node(member.n0), analytical.node(member.n1)
        span = analytical.length_m(member)
        for node in analytical.nodes:
            if node.id in (member.n0, member.n1) or span <= 0:
                continue
            t = sum((node.xyz[i] - a.xyz[i]) * (b.xyz[i] - a.xyz[i])
                    for i in range(3)) / span ** 2
            if not 0.0 < t < 1.0:
                continue
            on = tuple(a.xyz[i] + (b.xyz[i] - a.xyz[i]) * t for i in range(3))
            if sum((on[i] - node.xyz[i]) ** 2 for i in range(3)) ** 0.5 <= NODE_SNAP_M:
                inside.append(f"{node.id} lies inside {member.id}")
    assert not inside, "\n".join(inside)
