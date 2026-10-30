"""`haus countertops`: fillet math, the peninsula's edges, and a DXF that reads back."""

from __future__ import annotations

import math

import pytest

from typehaus.resolve.fillet import corner_fillets, filleted_ring

INCH = 0.0254


def test_fillet_on_a_square_corner_and_a_notch():
    # Counter-clockwise L: (2,1) is the one concave corner.
    ring = [(0.0, 0.0), (4.0, 0.0), (4.0, 1.0), (2.0, 1.0), (2.0, 3.0), (0.0, 3.0)]
    radii = [0.0, 0.5, 0.0, 0.25, 0.0, 0.0]
    convex, concave = corner_fillets(ring, radii)
    assert convex.start == pytest.approx((3.5, 0.0)) and convex.end == pytest.approx((4.0, 0.5))
    assert convex.center == pytest.approx((3.5, 0.5))
    # 90 degrees of sweep: tan(90/4), positive (counter-clockwise) on a left turn.
    assert convex.bulge == pytest.approx(math.tan(math.pi / 8)) and convex.convex
    assert concave.start == pytest.approx((2.25, 1.0)) and concave.end == pytest.approx((2.0, 1.25))
    assert concave.bulge == pytest.approx(-math.tan(math.pi / 8)) and not concave.convex
    # A concave fillet adds stone in the corner; a convex one removes it.
    from shapely.geometry import Polygon

    area = Polygon(filleted_ring(ring, radii, segments=64)).area
    assert area == pytest.approx(8.0 - (1 - math.pi / 4) * 0.25 + (1 - math.pi / 4) * 0.0625,
                                 abs=1e-3)
    # A radius bigger than its edges allow is clamped, and says so.
    (clamped,) = corner_fillets([(0, 0), (1, 0), (1, 1), (0, 1)], [0, 2.0, 0, 0])
    assert clamped.clamped and clamped.radius_m == pytest.approx(1.0)


def test_the_peninsula_is_eased_where_it_is_seen(catlin_model_ro):
    top = next(item for item in catlin_model_ro.countertops
               if item.tag == "CT-M-KIT-PENINSULA")
    by_vertex = {(round(x / INCH, 3), round(y / INCH, 3)): (kind, radius / INCH)
                 for (x, y), kind, radius in zip(top.outline, top.edge_kinds,
                                                 top.corner_radii_m, strict=True)}
    # The edge leaving each vertex, and that vertex's radius.
    assert by_vertex == {
        (376.375, 304.375): ("finished", pytest.approx(1.0)),     # seating edge's east end
        (376.375, 319.375): ("finished", pytest.approx(0.375)),   # the cantilever notch
        (387.375, 319.375): ("seam", pytest.approx(0.0)),         # x=32'-3 3/8" to CT-M-KIT-E
        (387.375, 344.375): ("finished", pytest.approx(0.0)),     # drawer side, from the seam
        (302.875, 344.375): ("finished", pytest.approx(1.0)),     # west end
        (302.875, 304.375): ("finished", pytest.approx(1.0)),     # seating edge
    }
    corner = next(item for item in catlin_model_ro.countertops if item.tag == "CT-M-KIT-E")
    assert "abutment" in corner.edge_kinds  # the tall pantry, not a finished edge


def test_a_piece_dxf_reads_back_with_true_arcs(catlin_model_ro, tmp_path):
    import ezdxf

    from typehaus.emit.fabrication.stone_dxf import write_piece_dxf
    from typehaus.takeoff.stone_pieces import fabricated_pieces

    piece = next(p for p in fabricated_pieces(catlin_model_ro, "quartz-counter")
                 if p.tag == "CT-M-KIT-N")
    doc = ezdxf.readfile(write_piece_dxf(piece, tmp_path / "piece.dxf"))
    assert not doc.audit().has_errors
    assert doc.header["$INSUNITS"] == 1
    (cut,) = doc.modelspace().query('LWPOLYLINE[layer=="CUT"]')
    assert cut.closed
    assert cut.get_xdata("TYPEHAUS")[0][1] == f"uid={piece.uid}"
    (hole,) = doc.modelspace().query('CIRCLE[layer=="HOLE"]')
    assert 2 * hole.dxf.radius == pytest.approx(1.375)
    # The faucet sits at the note's (352, 423.5): 54.625" from the west end, 1.875" off
    # the back of a 25" top.
    assert (hole.dxf.center.x, hole.dxf.center.y) == pytest.approx((54.625, 23.125), abs=1e-3)
    peninsula = next(p for p in fabricated_pieces(catlin_model_ro, "quartz-counter")
                     if p.tag == "CT-M-KIT-PENINSULA")
    doc = ezdxf.readfile(write_piece_dxf(peninsula, tmp_path / "pen.dxf"))
    (cut,) = doc.modelspace().query('LWPOLYLINE[layer=="CUT"]')
    assert sum(1 for *_xy, bulge in cut.get_points("xyb") if bulge) == 4
