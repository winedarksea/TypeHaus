"""RM-S-PLANT's supply: a sidewall grille over D-S-PLANT, a 6in take-off, no hatch."""

import pytest
from _helpers import check_context

from typehaus import inch
from typehaus.checks.integrity.catalog_tags import unknown_product_ref
from typehaus.checks.mep.terminal_necks import terminal_neck_fit
from typehaus.findings import Result

REGISTER = "REG-S-HP-PLANT"


def test_sidewall_sits_in_the_clear_cripple_bay_above_the_header(catlin_model_ro):
    model = catlin_model_ro
    obj = next(o for o in model.canvas_objects if o.tag == REGISTER)
    wall = next(w for w in model.walls if w.tag == "W-S-C1")
    header = next(m for m in wall.members if m.child_key.startswith("header-0"))
    cripples = sorted(m.p0[1] for m in wall.members if m.child_key.startswith("cripple-head-0"))
    y = obj.position[1]
    stud = inch(1.5).meters
    assert cripples[0] + stud / 2 <= y - inch(6).meters
    assert y + inch(6).meters <= cripples[1] - stud / 2
    assert obj.body_z0_m > header.z1_m  # face bottom clears the header's top
    top_plate = wall.plate_top_z_m - 2 * inch(1.5).meters
    assert obj.body_z1_m < top_plate


def test_feed_is_a_6in_round_take_off_at_75_cfm_and_the_hatch_is_gone(catlin_model_ro):
    model = catlin_model_ro
    duct = next(d for d in model.ducts if d.tag == "DU-S-HP-PLANT")
    assert duct.diameter_m == pytest.approx(inch(6).meters)
    assert duct.design_cfm == 75
    library = model.plan.library
    assert library.product("PROD-AIR-PLANT-SERVICE-HATCH") is None
    reg_type = next(t for t in library.register_types if t.tag == "REG-T-HP-PLANT-SIDE")
    assert [p.product_ref for p in reg_type.parts] == ["PROD-AIR-DAMPER-6-24V"]
    assert not unknown_product_ref(check_context(model=model))
    findings = [f for f in terminal_neck_fit(check_context(model=model))
                if REGISTER in f.element_tags]
    assert findings and all(f.result is Result.PASS for f in findings)
