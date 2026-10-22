"""Discrete fixings cross authored wall tees only on a continuous mounting face."""

from dataclasses import replace

import pytest
from shapely.geometry import box

from typehaus.checks.advisory.backing_fixings import fixing_support, fixing_wall_faces
from typehaus.quantities import M_PER_IN as IN
from typehaus.resolve.model import FramedMember, ResolvedLayer, ResolvedWall


def _wall(tag, start, end, *, shifted=0, finish=0.5 * IN):
    low, high = sorted((start, end))
    return ResolvedWall(
        uid=tag, tag=tag, storey="main", assembly="TEST",
        axis=((start, shifted), (end, shifted)), z0_m=0, z1_m=3,
        layers=(
            ResolvedLayer(name="stud", material_ref="spf", function="structure",
                          thickness_m=6 * IN,
                          polygon=tuple(box(low, shifted - 3 * IN,
                                            high, shifted + 3 * IN).exterior.coords)),
            ResolvedLayer(name="finish", material_ref="gyp", function="finish",
                          thickness_m=finish,
                          polygon=tuple(box(low, shifted + 3 * IN,
                                            high, shifted + 3 * IN + finish).exterior.coords)),
        ),
    )


@pytest.mark.parametrize("reverse", [False, True])
def test_post_can_land_on_connected_wall_even_with_reversed_axis(reverse):
    host = _wall("HOST", 0, 1)
    peer = _wall("PEER", 2 if reverse else 1, 1 if reverse else 2)
    block = FramedMember(parent_uid=peer.uid, child_key="backing-0", category="blocking",
                         profile="2x6", p0=(1.1, 2.25 * IN), p1=(1.9, 2.25 * IN),
                         z0_m=23.25 * IN, z1_m=28.75 * IN, length_m=0.8)
    peer = replace(peer, members=(block,))
    xy, z = (1.5, 3.5 * IN), 26 * IN
    candidates = list(fixing_wall_faces(host, "left", xy, z, [host, peer]))
    assert [(wall.tag, face) for wall, face in candidates] == [
        ("HOST", "left"), ("PEER", "right" if reverse else "left")]
    assert [member for wall, face in candidates
            for member in fixing_support(wall, face, xy, z)] == [block]
    # Wood in the opposite row cannot satisfy a post on the selected physical face.
    opposite = replace(block, p0=(1.1, -2.25 * IN), p1=(1.9, -2.25 * IN))
    assert not fixing_support(replace(peer, members=(opposite,)), candidates[1][1], xy, z)
    assert not fixing_support(replace(peer, members=()), candidates[1][1], xy, z)


@pytest.mark.parametrize("condition", ["gap", "parallel", "finish", "storey", "height"])
def test_disconnected_or_different_face_is_not_a_continuation(condition):
    host = _wall("HOST", 0, 1)
    peer = _wall("PEER", 1, 2)
    if condition == "gap":
        peer = _wall("PEER", 1.0001, 2)
    elif condition == "parallel":
        peer = _wall("PEER", 1, 2, shifted=0.0001)
    elif condition == "finish":
        peer = _wall("PEER", 1, 2, finish=IN)
    elif condition == "storey":
        peer = replace(peer, storey="upper")
    else:
        peer = replace(peer, z1_m=0.5)
    assert list(fixing_wall_faces(host, "left", (1.5, 3.5 * IN), 26 * IN,
                                  [host, peer])) == [(host, "left")]


def test_a_missed_post_inside_host_does_not_borrow_an_overlapping_walls_wood():
    host = _wall("HOST", 0, 2)
    peer = _wall("PEER", 0, 2)
    assert list(fixing_wall_faces(host, "left", (1.5, 3.5 * IN), 26 * IN,
                                  [host, peer])) == [(host, "left")]
