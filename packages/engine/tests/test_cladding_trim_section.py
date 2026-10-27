"""Folded trim geometry retains its real section in each run orientation."""

from collections import Counter

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.section import folded_section_mesh


@pytest.mark.parametrize(
    "first,second,run",
    [
        ((1, 0, 0), (0, 0, 1), (0, 2, 0)),
        ((1, 0, 0), (0, 1, 0), (0, 0, 2)),
        ((1, 0, 0), (0, 1, 0), (0, 0, -2)),
    ],
)
def test_folded_section_is_a_closed_sheet(first, second, run):
    mesh = folded_section_mesh(((0, 0), (0.1, 0), (0.1, 0.2)), (0, 0, 0), first, second, run, 0.001)
    edges = Counter(
        tuple(sorted(edge))
        for tri in mesh.triangles
        for edge in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0]))
    )
    assert all(count == 2 for count in edges.values())
    count = len(mesh.positions) // 2
    for start, end in zip(mesh.positions[:count], mesh.positions[count:], strict=True):
        assert tuple(end[i] - start[i] for i in range(3)) == pytest.approx(run)


def test_rejects_nonperpendicular_run():
    with pytest.raises(ValueError, match="perpendicular"):
        folded_section_mesh(((0, 0), (1, 0)), (0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 0, 1), 0.001)


def test_garage_corners_land_on_both_cladding_faces(catlin_model_ro):
    corners = [solid for solid in catlin_model_ro.solids
               if solid.product == "CORRUGATED_OUTSIDE_CORNER"]
    assert {piece.host_ref for piece in corners} == {
        "N-G-NE", "N-G-NW", "N-G-SE", "N-G-SW"}
    assert len(corners) == 4
    for corner in corners:
        junction = next(j for j in catlin_model_ro.junctions if j.node_tag == corner.host_ref)
        assert corner.trim_length_m == pytest.approx(100 * M_PER_IN)
        assert corner.trim_stock_length_in == 122
        assert corner.z0_m == pytest.approx(-12 * M_PER_IN)
        assert corner.z1_m == pytest.approx(88 * M_PER_IN)
        for incident in junction.incidents:
            wall = catlin_model_ro.wall(incident.wall_tag)
            layer = next(layer for layer in wall.layers if layer.function == "cladding")
            direction = incident.direction
            normal = (-direction[1], direction[0])
            projected = [x * normal[0] + y * normal[1] for x, y in layer.polygon]
            points = [x * normal[0] + y * normal[1] for x, y, _ in corner.body_mesh.positions]
            assert any(abs(p - q) < 1e-8 for p in points for q in (min(projected), max(projected)))


def test_house_corner_stock_and_overlap(catlin_model_ro):
    corners = [solid for solid in catlin_model_ro.solids
               if solid.product == "WIDE_OUTSIDE_CORNER"]
    assert len(corners) == 8
    for node in ("N-M-NE", "N-M-NW", "N-M-SE", "N-M-SW"):
        lower, upper = sorted((piece for piece in corners if piece.host_ref == node),
                              key=lambda piece: piece.z0_m)
        assert (lower.trim_stock_length_in, upper.trim_stock_length_in) == (243, 122)
        assert lower.z0_m == pytest.approx(-13.4375 * M_PER_IN)
        assert upper.z1_m == pytest.approx(255 * M_PER_IN)
        assert lower.z1_m - upper.z0_m == pytest.approx(3 * M_PER_IN)
    assert not any(s.tag.startswith("TR-H-CORNER-") for s in catlin_model_ro.solids)
