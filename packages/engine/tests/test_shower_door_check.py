"""``code.MN_4714_0408_shower_door``: the free-angle boundary and the no-swing verdicts (#152)."""

from types import SimpleNamespace

import pytest
from shapely.geometry import Polygon, box

from typehaus.checks.mep.shower_door import shower_door_opening
from typehaus.findings import Result
from typehaus.model import FixtureType, ShowerEnclosure, inch
from typehaus.model.placeable_symbols import symbol_geometry
from typehaus.resolve.shower_enclosures import ResolvedShowerEnclosure, free_opening_angle

LEAF = inch(22.875)
REACH = LEAF.meters + 0.025


def _flex(**changes):
    spec = dict(kind="hinged", entry_edge="+y", hinge="right", clear_opening=LEAF,
                leaf_width=LEAF, swing_radius=inch(23.875))
    return ShowerEnclosure(**{**spec, **changes})


def _verdicts(spec, free=None):
    """Result of the check on one shower whose leaf opens ``free`` degrees."""
    product = FixtureType(tag="T", name="t", footprint=(inch(36), inch(36)), height=inch(80),
                          shower_enclosure=spec)
    record = ResolvedShowerEnclosure(
        tag="SH", storey="s", room="R", type_ref="T", kind=spec.kind, entry=((0, 0), (1, 0)),
        entry_normal=(0, 1), clear_opening_m=spec.clear_opening.meters,
        free_angle_degrees=free, blocker="a wall")
    ctx = SimpleNamespace(
        plan=SimpleNamespace(library=SimpleNamespace(fixture_types=[product]),
                             elements_of_kind=lambda _: [SimpleNamespace(tag="SH", type_ref="T")]),
        model=SimpleNamespace(shower_enclosures=[record]))
    return [f.result for f in shower_door_opening(ctx)]


@pytest.mark.parametrize(("wall_gap", "passes"), [(REACH * 0.95, False), (REACH * 1.05, True)])
def test_leaf_free_angle_decides_the_verdict(wall_gap, passes):
    room = box(-2, -2, 2, wall_gap)  # the room's face stands ``wall_gap`` off the entry
    free, blocker = free_opening_angle((0, 0), (1, 0), (0, 1), REACH, 90.0, room, [])
    assert (blocker is None) == passes
    assert [Result.PASS if passes else Result.FAIL] == _verdicts(_flex(), free)


def test_a_body_below_the_head_stops_the_leaf_and_boundary_is_exact():
    cabinet = box(-1, 0.30, 1, 1)
    free, blocker = free_opening_angle((0, 0), (1, 0), (0, 1), 0.6, 90.0,
                                       Polygon(box(-2, -2, 2, 2)), [("CAB", cabinet)])
    assert blocker == "CAB" and free == pytest.approx(30.0, abs=0.1)  # asin(0.30 / 0.6)


def test_no_swing_and_no_spec():
    assert _verdicts(_flex(kind="curtain", hinge=None, swing_radius=None, leaf_width=None)) \
        == [Result.NOT_APPLICABLE]
    assert _verdicts(_flex(kind="sliding", hinge=None, swing_radius=None)) == [Result.PASS]
    assert _verdicts(_flex(clear_opening=inch(20))) == [Result.FAIL]
    with pytest.raises(ValueError, match="no hinge"):
        _flex(kind="sliding", hinge="left", swing_radius=None)


def test_generic_glyph_glazes_the_entry_and_fixed_edges_not_the_walls():
    # Entry +y, fixed glass +x: walls are -x and -y, where the old glyph drew its glass.
    _, parts = symbol_geometry("shower", 0.9144, 0.9144, 2.0,
                               shower_enclosure=_flex(fixed_glass_edges=("+x",)))
    glass = [p["center"] for p in parts if p["color"] == "glass"]
    assert len(glass) == 2 and all(x > 0.3 or y > 0.3 for x, y, _ in glass)
    assert not any(x < -0.3 or y < -0.3 for x, y, _ in glass)
