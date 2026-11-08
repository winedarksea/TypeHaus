"""Pipe risers stand in cover; a fixture end in a door swing moves along its wall or is named."""

from __future__ import annotations

from types import SimpleNamespace

from shapely.geometry import box

from typehaus.resolve.riser_cover import RiserCover, _Zone, riser_row
from typehaus.routing.cost import RouteCost
from typehaus.routing.graph import build_graph
from typehaus.routing.members import _Floor, _riser_on_member
from typehaus.routing.obstacles import HardPrism
from typehaus.routing.space import RoutingSpace
from typehaus.routing.terminal_block import resolve_ends

M = 0.0254


def test_riser_in_open_air_is_the_checks_predicate() -> None:
    """The router's zone and the check's ``riser_row`` read one function."""
    room = box(0, 0, 4, 4)
    cover = box(0, 0, 0.2, 4)
    zone = _Zone(room.difference(cover), floor=0.0, ceiling_z=2.4)
    rc = RiserCover(zones=[zone])
    assert rc.exposed(2.0, 2.0, 0.3, 1.2, 0.02)
    assert not rc.exposed(0.1, 2.0, 0.3, 1.2, 0.02)          # in wall cover
    assert not rc.exposed(2.0, 2.0, 2.45, 2.9, 0.02)         # above the ceiling plane
    # A route's own end excuses the leg in the room it stands in, not one passing through it.
    here = RiserCover(zones=[zone], exempt=[(2.0, 2.0, 1.0)])
    assert not here.exposed(2.0, 2.0, 0.3, 1.2, 0.02)
    assert RiserCover(zones=[zone], exempt=[(2.0, 2.0, 5.0)]).exposed(2.0, 2.0, 0.3, 1.2, 0.02)
    assert riser_row((2.0, 2.0), 0.3, 1.2, 0.02, room, cover, None, 0.0, 2.4, 3 * M)
    assert not riser_row((0.1, 2.0), 0.3, 1.2, 0.02, room, cover, None, 0.0, 2.4, 3 * M)


def test_a_riser_may_not_pass_through_an_lvl_trimmer() -> None:
    floor = _Floor(tag="F", across="y", kind="open_web", window=(0.0, 0.3))
    floor.blocks = [(1.0, 1.0, 1.0 + 3.5 * M, 2.0, 0.0, 0.3)]  # an LVL opening edge
    assert _riser_on_member(floor, (1.0, 1.5, 0.0), 0.0, 0.3, 0.02)
    assert not _riser_on_member(floor, (2.0, 1.5, 0.0), 0.0, 0.3, 0.02)


class _Wall:
    tag, axis, along, perp = "W", "x", (0.0, 6.0), (1.9, 2.1)


def test_a_fixture_end_in_a_door_swing_moves_along_its_wall_or_is_named() -> None:
    swing = HardPrism(tag="D-1", kind="opening", footprint=box(1.0, 1.5, 2.0, 2.5),
                      z0_m=0.0, z1_m=2.0)
    space = RoutingSpace(radius_m=0.0, clearance_m=0.0, cost=RouteCost(), hard=[swing], soft=[],
                         corridors=[], bbox=(-1.0, -1.0, 8.0, 8.0), storeys=("main",))
    space.members = SimpleNamespace(
        _walls_at=lambda axis, station: [_Wall()] if axis == "x" else [],
        cuts=lambda *a, **k: {})
    end = (1.5, 2.0, 1.0)
    moved, blocks = resolve_ends(space, [end])
    (block,) = blocks
    assert block.cause == "door" and block.prisms == ("D-1",) and block.wall == "W"
    assert block.moved_to is not None and block.moved_to[0] > 2.0   # out of the sector, same wall
    assert block.moved_to[1] == 2.0 and moved[end][:2] == block.moved_to
    graph = build_graph(space, [end, (6.0, 2.0, 1.0)], None, ends=(end,))
    assert graph.terminal_blocks == [block]
    # No wall, no legal point: named, the end keeps its own node (the caller refuses).
    space.members = None
    _, blocks = resolve_ends(space, [end])
    assert blocks[0].moved_to is None and "house move" in blocks[0].render()
