"""Backing sits inside its selected stud face in every wall direction."""

from __future__ import annotations

import pytest

from typehaus.quantities import inch
from typehaus.resolve.framing.backing_panels import BackingBand, append_backing_members
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.model import ResolvedLayer, ResolvedWall


@pytest.mark.parametrize("direction", ((1, 0), (0, 1), (-1, 0), (0, -1)))
@pytest.mark.parametrize("face", ("left", "right"))
def test_backing_is_flush_with_the_authored_stud_face(direction, face):
    normal = (-direction[1], direction[0])
    half_depth = inch(2.75).meters
    polygon = [(direction[0] * station + normal[0] * offset,
                direction[1] * station + normal[1] * offset)
               for station, offset in ((0, -half_depth), (4, -half_depth),
                                       (4, half_depth), (0, half_depth))]
    wall = ResolvedWall(
        uid="W1", tag="W-TEST", storey="MAIN", assembly="TEST",
        axis=((0, 0), (direction[0] * 4, direction[1] * 4)), z0_m=0, z1_m=3,
        layers=(ResolvedLayer(name="stud", material_ref="spf", function="structure",
                              thickness_m=half_depth * 2, polygon=polygon),),
    )
    band = BackingBand(tag="BK-TEST", wall_ref=wall.tag, face=face,
                       start_m=1, length_m=1, elevation_m=1, height_m=inch(7.25).meters,
                       profile="2x8", material_ref="spf", purpose="bracket")
    members = []
    append_backing_members(members, wall, [band], direction, (0, 0), 0, 4,
                           lambda _: 3, [])
    assert len(members) == 1
    footprint, _, _ = member_footprint(members[0])
    offsets = [point[0] * normal[0] + point[1] * normal[1] for point in footprint]
    expected = ((half_depth - inch(1.5).meters, half_depth) if face == "left"
                else (-half_depth, -half_depth + inch(1.5).meters))
    assert (min(offsets), max(offsets)) == pytest.approx(expected)
    assert members[0].length_m == pytest.approx(1)
    assert members[0].z0_m == pytest.approx(1)
