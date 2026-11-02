"""The plant terminal is an actual assembly and inlet, rather than a nearby generic box."""

from dataclasses import replace

import pytest
from _helpers import check_context

from typehaus import TerminalNeck, TerminalNeckComponent, TerminalNeckInlet, inch
from typehaus.checks.integrity.catalog_tags import unknown_product_ref
from typehaus.checks.mep.duct_connectivity import duct_connectivity
from typehaus.checks.mep.terminal_necks import terminal_neck_fit
from typehaus.findings import Result
from typehaus.resolve.terminal_connections import inlet_connection_error
from typehaus.resolve.terminal_necks import component_box, terminal_inlet
from typehaus.takeoff.placeables import placeables_takeoff

REGISTER = "REG-S-HP-PLANT"
DUCT = "DU-S-HP-SOUTH"


def test_assembly_has_named_parts_and_one_priced_purchase(catlin_model_ro):
    model = catlin_model_ro
    obj = next(o for o in model.canvas_objects if o.tag == REGISTER)
    assert obj.position == pytest.approx((inch(176).meters, inch(39).meters))
    parts = [s for s in model.solids if s.group == REGISTER]
    assert len(parts) == 5
    assert {s.host_ref for s in parts} == {REGISTER}
    assert all(model.plan.library.product(s.product) is not None for s in parts)
    assert any(s.tag == REGISTER + "-NECK" for s in parts)
    assert not unknown_product_ref(check_context(model=model))
    rows = [r for r in placeables_takeoff(model) if REGISTER in r["tags"]]
    assert len(rows) == 1 and rows[0]["count"] == 1
    included = rows[0]["included_products"]
    assert len(included) == 4  # actuator belongs to the damper, not a fifth purchase
    assert all(p["quantity_per_assembly"] == 1 for p in included)


def test_inlet_and_parts_fit_the_real_ceiling_cavity(catlin_model_ro):
    model = catlin_model_ro
    assert inlet_connection_error(model, REGISTER) is None
    inlet, _, width, height = terminal_inlet(model, REGISTER)
    obj = next(o for o in model.canvas_objects if o.tag == REGISTER)
    duct = next(d for d in model.ducts if d.tag == DUCT)
    assert (*duct.path[-1], duct.z_m[-1]) == pytest.approx(inlet)
    assert width == pytest.approx(duct.width_m)
    assert height == pytest.approx(duct.depth_m)
    assert duct.path[1][0] == pytest.approx(inch(210).meters)
    assert duct.z_m[0] == duct.z_m[1] < duct.z_m[-1]
    assert duct.z_m[-2] == duct.z_m[-1]  # square inlet mouth after the rise
    assert duct.path[-2][0] - duct.path[-1][0] == pytest.approx(inch(6).meters)
    assert duct.z_m[-1] - duct.depth_m / 2 > obj.body_z0_m
    findings = [f for f in terminal_neck_fit(check_context(model=model))
                if REGISTER in f.element_tags]
    assert findings and all(f.result is Result.PASS for f in findings), [
        f.message for f in findings]


@pytest.mark.parametrize("change", ["plan", "height", "section", "direction"])
def test_disconnected_inlet_cannot_use_the_implicit_boot_allowance(catlin_model_ro, change):
    model = replace(catlin_model_ro)
    duct = next(d for d in model.ducts if d.tag == DUCT)
    path, z = list(duct.path), list(duct.z_m)
    updates = {}
    if change == "plan":
        path[-1] = (path[-1][0] + inch(2).meters, path[-1][1])
    elif change == "height":
        z[-1] += inch(2).meters
    elif change == "section":
        updates["width_m"] = inch(8).meters
    else:
        path[-2] = (path[-1][0] - inch(12).meters, path[-1][1])
    changed = replace(duct, path=path, z_m=tuple(z), **updates)
    model.ducts = [changed if d.tag == DUCT else d for d in model.ducts]
    assert inlet_connection_error(model, REGISTER)
    findings = duct_connectivity(check_context(model=model))
    assert any(f.result is Result.FAIL and DUCT in f.element_tags for f in findings)


def test_ceiling_shift_moves_the_inlet_and_component_geometry_together(catlin_model_ro):
    model = catlin_model_ro
    obj = next(o for o in model.canvas_objects if o.tag == REGISTER)
    catalog = next(t for t in model.plan.library.register_types if t.tag == obj.type_ref)
    shifted = replace(obj, body_z0_m=obj.body_z0_m + inch(1).meters)
    component = catalog.neck.components[0]
    before, after = component_box(obj, component), component_box(shifted, component)
    assert after[1] - before[1] == pytest.approx(inch(1).meters)


def test_invalid_assembly_dimensions_and_duplicate_parts_are_rejected():
    with pytest.raises(ValueError, match="positive"):
        TerminalNeckComponent(tag="X", width=inch(0), height=inch(6), depth=inch(4),
                              offset=(inch(0),) * 3, part="invalid")
    with pytest.raises(ValueError, match="unit vector"):
        TerminalNeckInlet(position=(inch(0),) * 3, width=inch(10), height=inch(6), normal=(0, 0))
    part = TerminalNeckComponent(tag="X", width=inch(12), height=inch(6), depth=inch(4),
                                 offset=(inch(0),) * 3, part="damper")
    with pytest.raises(ValueError, match="unique"):
        TerminalNeck(width=inch(12), height=inch(6), depth=inch(4), part="assembly",
                     components=(part, part))


def test_actuator_extraction_fits_the_service_opening(catlin_plan):
    neck = next(t.neck for t in catlin_plan.library.register_types
                if t.tag == "REG-T-HP-CEIL-DAMPERED")
    parts = {p.tag: p for p in neck.components}
    hatch = parts["SERVICE-HATCH"]
    removal = parts["ACTUATOR-REMOVAL"]
    # The 12x8 cover conceals a 10x6 clear opening. The entire detached motor passes it.
    for axis, opening in ((0, inch(10).meters), (1, inch(6).meters)):
        extent = (removal.width if axis == 0 else removal.height).meters
        offset = abs(removal.offset[axis].meters - hatch.offset[axis].meters)
        assert offset + extent / 2 < opening / 2
    assert parts["ACTUATOR-WITHDRAWAL"].clearance_only
    assert parts["DAMPER-REMOVAL"].clearance_only
    collar, damper, boot = (parts[tag] for tag in ("COLLAR", "DAMPER", "BOOT"))
    assert collar.offset[2].meters == 0
    assert collar.depth.meters == damper.offset[2].meters
    assert damper.offset[2].meters + damper.depth.meters == boot.offset[2].meters


def test_rectangular_feed_below_attic_deck_is_not_attic_headroom_obstruction(catlin_model_ro):
    from typehaus.checks.mep.routing_ceiling import run_in_finished_volume

    model = replace(catlin_model_ro)
    findings = run_in_finished_volume(check_context(model=model))
    assert not [f for f in findings if f.result is Result.FAIL and DUCT in f.element_tags]
    duct = next(d for d in model.ducts if d.tag == DUCT)
    # A real intrusion above the deck must still fail, even though width exceeds depth.
    changed = replace(duct, z_m=tuple(z + inch(2).meters for z in duct.z_m))
    model.ducts = [changed if d.tag == DUCT else d for d in model.ducts]
    findings = run_in_finished_volume(check_context(model=model))
    assert [f for f in findings if f.result is Result.FAIL and DUCT in f.element_tags]


def test_feed_endpoint_is_resolved_from_the_changed_terminal_face(catlin_model_ro):
    from typehaus.resolve.mep import _resolve_duct_run

    original = catlin_model_ro
    obj = next(o for o in original.canvas_objects if o.tag == REGISTER)
    shifted = replace(obj, body_z0_m=obj.body_z0_m + inch(1).meters)
    model = replace(original,
                    canvas_objects=[shifted if o.tag == REGISTER else o
                                    for o in original.canvas_objects],
                    ducts=[d for d in original.ducts if d.tag != DUCT],
                    solids=list(original.solids))
    authored = original.plan.by_tag(DUCT)
    storey = next(s for s in original.plan.storeys if s.tag == "second")
    findings = _resolve_duct_run(model, authored, storey)
    assert not findings
    before = next(d for d in original.ducts if d.tag == DUCT)
    after = next(d for d in model.ducts if d.tag == DUCT)
    assert after.z_m[-1] - before.z_m[-1] == pytest.approx(inch(1).meters)
    assert after.z_m[0] == before.z_m[0]
    assert inlet_connection_error(model, REGISTER) is None


def test_invalid_terminal_anchor_reports_an_error(catlin_model_ro):
    from typehaus.resolve.mep import _resolve_duct_run

    model = replace(catlin_model_ro, solids=list(catlin_model_ro.solids),
                    ducts=list(catlin_model_ro.ducts))
    authored = model.plan.by_tag(DUCT).model_copy(update={"end_terminal_ref": "MISSING"})
    storey = next(s for s in model.plan.storeys if s.tag == "second")
    findings = _resolve_duct_run(model, authored, storey)
    assert [f for f in findings if f.check_id == "integrity.duct_terminal_ref"
            and f.result is Result.FAIL]
