"""The +19'-0" BBD75 band: one Transition Trim per N/S wall segment, at the joint."""

from typehaus.quantities import M_PER_IN


def test_every_bbd75_wall_carries_a_transition_trim_at_the_band(catlin_model):
    bands = [s for s in catlin_model.solids
             if s.category == "cladding_trim" and s.product == "BBD_TRANSITION"]
    assert bands
    assert {s.host_ref[:3] for s in bands} == {"W-S"}
    for s in bands:
        assert s.z0_m / M_PER_IN < 228 < s.z1_m / M_PER_IN
        assert 0 < s.trim_length_m <= s.trim_stock_length_in * M_PER_IN + 1e-9


def _stations(face, solid):
    """(along, out of the back plane) for every vertex of ``solid`` in ``face``'s frame."""
    pts = solid.body_mesh.positions
    return ([x * face.d[0] + y * face.d[1] for x, y, _ in pts],
            [(x * face.n[0] + y * face.n[1]) - face.back for x, y, _ in pts])


def test_band_stops_under_the_corner_leg_short_of_the_c_closure(catlin_model_ro):
    """BBD75 p. 30: the corner's leg rides a C-Closure; the band ends under it, 1/16" short."""
    from typehaus.resolve.cladding_trim.corner_closures import corner_closures
    from typehaus.resolve.cladding_trim.runs import cladding_face

    model = catlin_model_ro
    solids = [s for s in model.solids if s.category == "cladding_trim"]
    walls = {w.uid: w for w in model.walls}
    checked = set()
    for closure in corner_closures(model):
        wall = walls[closure.wall_uid]
        layer = next(ly for ly in wall.layers if ly.name == closure.layer_name)
        face = cladding_face(wall, layer)
        ends = [s for s in solids if s.product == "BBD_TRANSITION" and s.host_ref == wall.tag]
        if not ends:
            continue
        cs = [s for s in solids if s.tag.startswith(f"TRIM-{closure.node_tag}-C-CLOSURE-")]
        # Lapped sticks, continuous through the band.
        assert all(any(c.z0_m < z < c.z1_m for c in cs) for e in ends for z in (e.z0_m, e.z1_m))
        legs = [s for s in solids if s.tag.startswith(f"TRIM-{closure.node_tag}-WIDE-CORNER-")]
        # The leg on this face: the vertices inboard of the web (the other leg is at the fold).
        leg_inner = min(o for s in legs for a, o in zip(*_stations(face, s), strict=True)
                        if (a - closure.web_station) * closure.inward > 0)
        for band in ends:
            along, out = _stations(face, band)
            end = min(along) if closure.inward > 0 else max(along)
            if abs(end - closure.lip_station) > 2 * M_PER_IN:
                continue  # the band's other end
            assert max(out) <= leg_inner + 1e-9
            assert (end - closure.lip_station) * closure.inward >= M_PER_IN / 16 - 1e-9
            leg_tip = closure.web_station + closure.inward * 5.5 * M_PER_IN
            assert (leg_tip - end) * closure.inward >= 2 * M_PER_IN
            checked.add(closure.node_tag)
    assert checked == {"N-M-NE", "N-M-NW", "N-M-SE", "N-M-SW"}
