"""The eave heel is foamed solid: heel to plate inside face, down to the block and plate."""

IN = 0.0254


def _bay(solid, y_lo=99.0, y_hi=125.0, x_hi=10.0):
    return [p for p in solid.body_mesh.positions
            if y_lo * IN < p[1] < y_hi * IN and p[0] < x_hi * IN]


def test_west_eave_heel_is_foamed_over_the_block(catlin_model_ro):
    solids = {s.tag: s for s in catlin_model_ro.solids if s.tag.startswith("INSUL-RF-HOUSE")}
    foam = _bay(solids["INSUL-RF-HOUSE-2"])
    batt = _bay(solids["INSUL-RF-HOUSE-1"])
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-HOUSE")
    block = next(m for m in roof.members if m.category == "blocking"
                 and m.p0[0] < 10 * IN and 99 * IN < m.p0[1] < 125 * IN)
    bx0, bx1 = 0.5 * IN, 2.0 * IN

    # reaches the heel plane, stands on the block top over it and the plate top inboard
    assert min(p[0] for p in foam) < 0.51 * IN
    over_block = [p[2] for p in foam if bx0 - 1e-6 <= p[0] <= bx1 - 1e-4]
    inboard = [p[2] for p in foam if bx1 + 1e-4 <= p[0] <= 6.01 * IN]
    assert abs(min(over_block) - block.z1_m) < 1e-4
    assert abs(min(inboard) - 243.75 * IN) < 1e-4
    # nothing strictly inside the block
    assert not [p for p in foam if bx0 + 1e-4 < p[0] < bx1 - 1e-4
                and block.z0_m + 1e-4 < p[2] < block.z1_m - 1e-4]
    # the batt starts at the plate's inside face
    assert abs(min(p[0] for p in batt) - 6.0 * IN) < 1e-3
