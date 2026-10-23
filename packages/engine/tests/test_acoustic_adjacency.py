"""advisory.acoustic_adjacency on synthetic rooms: bedroom | bath | bedroom in a row."""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.checks.advisory.acoustics import acoustic_adjacency
from typehaus.findings import Result


def _room(tag, occupancy, x0):
    ring = [(x0, 0.0), (x0 + 3.0, 0.0), (x0 + 3.0, 3.0), (x0, 3.0)]
    return SimpleNamespace(tag=tag, storey="s", occupancy=occupancy, axis_face=ring,
                           clear_face=ring)


def _wall(tag, x, assembly):
    return SimpleNamespace(tag=tag, storey="s", assembly=assembly, is_foundation=False,
                           axis=((x, 0.0), (x, 3.0)))


def _ctx(*, door_on=None, target=45):
    walls = [_wall("W-1", 3.0, "RATED"), _wall("W-2", 6.0, "PLAIN")]
    rooms = [_room("BED-A", "bedroom", 0.0), _room("BATH", "bathroom", 3.0),
             _room("BED-B", "bedroom", 6.0)]
    openings = [] if door_on is None else [SimpleNamespace(
        kind="door", host_wall=door_on, center_along_m=1.5)]
    model = SimpleNamespace(rooms=rooms, walls=walls, openings=openings,
                            wall={w.tag: w for w in walls}.get)
    stc = {"RATED": 48, "PLAIN": 34}
    library = SimpleNamespace(
        resolve_assembly=lambda tag: SimpleNamespace(stc=stc.get(tag)))
    return SimpleNamespace(model=model, plan=SimpleNamespace(library=library),
                           preferences=SimpleNamespace(min_partition_stc=target))


def _by_wall(findings):
    return {f.element_tags[0]: f.result for f in findings}


def test_grades_doorless_sleeping_walls_against_the_target():
    assert _by_wall(acoustic_adjacency(_ctx())) == {"W-1": Result.PASS, "W-2": Result.FAIL}


def test_a_door_between_the_pair_takes_the_wall_out():
    assert _by_wall(acoustic_adjacency(_ctx(door_on="W-2"))) == {"W-1": Result.PASS}


def test_unstated_target_is_unknown_and_no_pair_is_earned_na():
    assert set(_by_wall(acoustic_adjacency(_ctx(target=None))).values()) == {Result.UNKNOWN}
    ctx = _ctx()
    for room in ctx.model.rooms:
        room.occupancy = "storage"
    assert [f.result for f in acoustic_adjacency(ctx)] == [Result.NOT_APPLICABLE]
