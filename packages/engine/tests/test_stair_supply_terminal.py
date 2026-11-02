"""A named stair register box and a physically connected round branch."""

from dataclasses import replace

import pytest
from _helpers import check_context

from typehaus import inch
from typehaus.checks.mep.duct_connectivity import duct_connectivity
from typehaus.checks.mep.terminal_necks import terminal_neck_fit
from typehaus.findings import Result
from typehaus.resolve.terminal_connections import inlet_connection_error
from typehaus.resolve.terminal_necks import terminal_inlet
from typehaus.takeoff.placeables import placeables_takeoff

REGISTER = "REG-S-HP-STAIR"
BRANCH = "DU-S-HP-STAIR"


def test_named_box_and_explicit_branch_clear_framing(catlin_model_ro):
    model = catlin_model_ro
    neck = next(s for s in model.solids if s.tag == REGISTER + "-NECK")
    product = model.plan.library.product(neck.product)
    assert product.model == "TH-HP-STAIR-BOX-01"
    assert neck.host_ref == REGISTER
    assert max(x for x, y in neck.outline) == pytest.approx(inch(223.26).meters)
    branch = next(d for d in model.ducts if d.tag == BRANCH)
    assert branch.diameter_m == pytest.approx(inch(4).meters)
    assert branch.design_cfm == 50
    inlet, _, _, _ = terminal_inlet(model, REGISTER)
    assert (*branch.path[-1], branch.z_m[-1]) == pytest.approx(inlet)
    assert inlet_connection_error(model, REGISTER) is None
    trunk = next(d for d in model.ducts if d.tag == "DU-S-HP-SUP")
    assert branch.z_m[0] - branch.diameter_m / 2 >= trunk.z_m[0] - trunk.depth_m / 2
    assert branch.z_m[0] + branch.diameter_m / 2 <= trunk.z_m[0] + trunk.depth_m / 2
    findings = [f for f in terminal_neck_fit(check_context(model=model))
                if REGISTER in f.element_tags]
    assert findings and all(f.result is Result.PASS for f in findings), findings
    findings = [f for f in duct_connectivity(check_context(model=model))
                if BRANCH in f.element_tags]
    assert findings and all(f.result is Result.PASS for f in findings), findings
    rows = [r for r in placeables_takeoff(model) if REGISTER in r["tags"]]
    assert len(rows) == 1 and rows[0]["included_products"] == [
        {"product_ref": "PROD-AIR-STAIR-REGISTER-BOX", "quantity_per_assembly": 1}]


def test_short_branch_is_not_excused_as_an_implicit_boot(catlin_model_ro):
    model = replace(catlin_model_ro)
    branch = next(d for d in model.ducts if d.tag == BRANCH)
    short = replace(branch, path=[branch.path[0], (inch(225).meters, branch.path[-1][1])])
    model.ducts = [short if d.tag == BRANCH else d for d in model.ducts]
    assert inlet_connection_error(model, REGISTER)
    findings = duct_connectivity(check_context(model=model))
    assert any(f.result is Result.FAIL and BRANCH in f.element_tags for f in findings)
