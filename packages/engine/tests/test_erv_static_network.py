"""Splitting a header at diameter transitions must not erase its remote friction."""

from dataclasses import replace
from uuid import UUID

import pytest
from _helpers import check_context

from typehaus import (
    DuctProductType,
    Equipment,
    EquipmentKind,
    EquipmentType,
    Library,
    PlanModel,
    Project,
    Site,
    inch,
    m,
    pt,
)
from typehaus.checks.mep.erv_manifold_ports import erv_manifold_ports
from typehaus.checks.mep.erv_static import _network, erv_static_budget, radial_landings
from typehaus.findings import Result
from typehaus.model.enums import Service
from typehaus.model.placeables import PortCertainty, ServicePort
from typehaus.resolve.duct_sizing import leg_drop_in_wg
from typehaus.resolve.model import ResolvedCanvasObject, ResolvedDuct, ResolvedModel


def _duct(tag, start, end, diameter=6, system="supply", material="galvanized", z=1):
    length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
    return ResolvedDuct(uid=tag, tag=tag, storey="basement", system=system,
        path=[start, end], width_m=diameter * 0.0254, depth_m=diameter * 0.0254,
        diameter_m=diameter * 0.0254, material=material, design_cfm=25 if diameter == 4 else 210,
        routing="exposed", floor_ref=None, crossings=(), conflicts=(), depth_ok=True,
        z_m=(z, z), length_m=length)


def _body(tag, x, type_ref):
    return ResolvedCanvasObject(uid=tag, tag=tag, storey="basement", domain="mechanical",
        kind="Equipment", type_ref=type_ref, room=None, position=(x, 0), z_m=1,
        rotation_degrees=0, footprint=[(x - 0.01, -0.2), (x + 0.01, -0.2),
                                    (x + 0.01, 0.2), (x - 0.01, 0.2)])


@pytest.fixture
def ctx():
    machine_type = EquipmentType(tag="ERV-T", name="fan", footprint=(m(0.02), m(0.4)),
        height=m(0.2), ventilation_cfm=210, fan_curve=((0, 220), (1, 100)))
    plenum_type = EquipmentType(tag="PLENUM-T", name="distribution",
        footprint=(m(0.02), m(0.4)), height=m(0.2), duct_ports=2, port_diameter=inch(4))
    products = tuple(DuctProductType(tag=f"D-{diameter}", name=f"{diameter} inch rigid",
        material="galvanized", nominal_diameter=inch(diameter), bore_diameter=inch(diameter),
        roughness_m=0.00009) for diameter in (4, 6, 8))
    elements = (Equipment(uid="ERV", tag="ERV", kind=EquipmentKind.ERV,
        footprint=(m(0.02), m(0.4)), position=pt(m(0), m(0)), type_ref="ERV-T"),
        Equipment(uid="PLENUM", tag="PLENUM", kind=EquipmentKind.DUCT_MANIFOLD,
        footprint=(m(0.02), m(0.4)), position=pt(m(22), m(0)), type_ref="PLENUM-T"))
    plan = PlanModel(project=Project(name="split header", project_uuid=UUID(int=1),
        site=Site(lat=0, lon=0, elevation=m(0))), elements={"basement": elements},
        library=Library(equipment_types=(machine_type, plenum_type), duct_product_types=products))
    model = ResolvedModel(plan=plan,
        canvas_objects=[_body("ERV", 0, "ERV-T"), _body("PLENUM", 22, "PLENUM-T")],
        ducts=[_duct("MACHINE-6", (0, 0), (1, 0)),
               _duct("REMOTE-8", (1, 0), (11, 0), diameter=8),
               _duct("UPPER-6", (11, 0), (21, 0)),
               _duct("PLENUM-FEED-6", (21, 0), (22, 0)),
               _duct("RADIAL-4", (22, 0), (23, 0), diameter=4)])
    return check_context(model=model)


def test_remote_reducers_keep_every_segment_in_the_actual_friction_budget(ctx):
    # Neither REMOTE-8 nor UPPER-6 touches a machine or box. The old one-hop collection
    # omitted both, making longer routes look cheaper as soon as they were split.
    network = _network(ctx, "ERV", radial_landings(ctx))
    assert {duct.tag for duct in network} == {duct.tag for duct in ctx.model.ducts}
    pressure = sum(leg_drop_in_wg(duct.design_cfm, duct.diameter_m, 0.00009, duct.length_m)
                   for duct in ctx.model.ducts)
    assert pressure > 0.1
    finding = next(f for f in erv_static_budget(ctx) if "worst path" in f.message)
    assert f"at {pressure:.3f} in. w.g." in finding.message


def test_split_headers_use_their_authored_branch_flows_without_reducing_the_machine_rate(ctx):
    # The upper tee carries 150 cfm after the basement's 60 cfm takeoff; the machine
    # still carries the full 210. Network expansion must not replace these with one rate.
    ctx.model.ducts = [replace(duct, design_cfm=150)
                      if duct.tag in {"REMOTE-8", "UPPER-6", "PLENUM-FEED-6"} else duct
                      for duct in ctx.model.ducts]
    pressure = sum(leg_drop_in_wg(duct.design_cfm, duct.diameter_m, 0.00009, duct.length_m)
                   for duct in ctx.model.ducts)
    all_at_machine_rate = sum(leg_drop_in_wg(210, duct.diameter_m, 0.00009, duct.length_m)
                             for duct in ctx.model.ducts)
    assert pressure < all_at_machine_rate
    finding = next(f for f in erv_static_budget(ctx) if "worst path" in f.message)
    assert f"at {pressure:.3f} in. w.g." in finding.message
    assert "210 cfm design rate" in finding.message


@pytest.mark.parametrize("extra", [
    _duct("WRONG-SYSTEM", (11, 0), (11, 2), system="return"),
    _duct("MIDSPAN-CROSSING", (6, -1), (6, 1)),
    _duct("OTHER-LEVEL", (11, 0), (11, 2), z=3),
    _duct("UNTYPED-HEAT-PUMP", (11, 0), (11, 2), material=None),
])
def test_only_compatible_physical_joints_extend_the_distribution(ctx, extra):
    ctx.model.ducts.append(extra)
    network = _network(ctx, "ERV", radial_landings(ctx))
    assert extra.tag not in {duct.tag for duct in network}
    assert len(network) == 5


def test_a_remote_material_without_a_catalog_row_stays_in_the_network_and_reports_its_gap(ctx):
    ctx.model.ducts[1] = replace(ctx.model.ducts[1], material="unpublished-metal")
    assert "REMOTE-8" in {duct.tag for duct in _network(ctx, "ERV", radial_landings(ctx))}
    findings = erv_static_budget(ctx)
    assert any("REMOTE-8" in f.message and "unpublished-metal" in f.message for f in findings)


def test_return_and_exhaust_share_the_extract_network_without_pulling_in_supply(ctx):
    ctx.model.ducts = [replace(duct, system="return") for duct in ctx.model.ducts]
    ctx.model.ducts[1] = replace(ctx.model.ducts[1], system="exhaust")
    extra = _duct("FRESH-AIR", (11, 0), (11, 2), system="supply")
    ctx.model.ducts.append(extra)
    network = _network(ctx, "ERV", radial_landings(ctx))
    assert {duct.tag for duct in network} == {duct.tag for duct in ctx.model.ducts[:-1]}


@pytest.mark.parametrize(("system", "offset_in", "landed", "verdict"), [
    ("supply", 0.0, True, Result.PASS),    # reduced onto its collar: a radial
    ("supply", 3.0, True, Result.FAIL),    # drawn off it: still a branch, stranded by name
    ("return", 3.0, False, Result.PASS),   # the trunk port's system and no collar's: trunk
])
def test_a_reduced_run_is_classified_by_the_port_it_lands_on(ctx, system, offset_in,
                                                             landed, verdict):
    collar = ServicePort(tag="collar", service=Service.SUPPLY_AIR,
                         position=(m(0), m(0), m(0)), connection_size=inch(4),
                         certainty=PortCertainty.EXACT)
    trunk = ServicePort(tag="trunk", service=Service.RETURN_AIR, position=(m(0), m(0.1), m(0)))
    lib = ctx.plan.library
    plenum = lib.equipment_types[1].model_copy(update={"duct_ports": 1, "ports": (collar, trunk)})
    plan = ctx.plan.model_copy(update={"library": lib.model_copy(
        update={"equipment_types": (lib.equipment_types[0], plenum)})})
    y = offset_in * 0.0254
    reduced = replace(_duct("RADIAL-3", (22, y), (23, y), diameter=4, system=system),
                      diameter_m=3 * 0.0254)
    ducts = [*ctx.model.ducts[:-1], reduced]
    reduced_ctx = check_context(model=replace(ctx.model, plan=plan, ducts=ducts))
    assert ("RADIAL-3" in radial_landings(reduced_ctx)) is landed
    census = next(f for f in erv_manifold_ports(reduced_ctx) if "PLENUM" in f.message)
    assert census.result is verdict
    assert ("RADIAL-3" in census.message) is (verdict is Result.FAIL)


# --- rectangular trunks: graded only when anchored on a plenum ------------------------------

def _rect(tag, start, end, width_in, depth_in, system="supply", cfm=210, z=1):
    length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
    return replace(_duct(tag, start, end, system=system, z=z), width_m=width_in * 0.0254,
                   depth_m=depth_in * 0.0254, diameter_m=None, design_cfm=cfm, length_m=length)


def _rect_ctx(ctx, ducts, roughness=0.0000914, extra=()):
    """The fixture with an 8" plenum collar and a rectangular galvanized row."""
    lib = ctx.plan.library
    plenum = lib.equipment_types[1].model_copy(update={"port_diameter": inch(8)})
    row = DuctProductType(tag="R-10", name="rect to 10in", material="galvanized",
                          section="rectangular", max_side=inch(10), gauge=30,
                          thickness=inch(0.013), roughness_m=roughness)
    plan = ctx.plan.model_copy(update={"library": lib.model_copy(update={
        "equipment_types": (lib.equipment_types[0], plenum, *extra),
        "duct_product_types": (*lib.duct_product_types, row)})})
    return check_context(model=replace(ctx.model, plan=plan, ducts=ducts))


def test_the_equivalent_diameter_and_one_rectangular_drop_are_the_hand_values() -> None:
    # De = 1.30 (a b)^0.625 / (a + b)^0.25: 8x4 -> 1.30 x 32^0.625 / 12^0.25 = 6.0935 in.
    from typehaus.resolve.duct_sizing import equivalent_diameter_m
    assert equivalent_diameter_m(8 * 0.0254, 4 * 0.0254) / 0.0254 == pytest.approx(6.0935, abs=1e-3)
    assert equivalent_diameter_m(6 * 0.0254, 4 * 0.0254) / 0.0254 == pytest.approx(5.3281, abs=1e-3)
    # 100 cfm, 10 ft, eps 0.0003 ft: D 0.50779 ft, V 493.8 fpm, Re 25,640, eps/D 5.908e-4,
    # Colebrook f 0.02578, VP (V/4005)^2 0.01520 -> f (L/D) VP = 0.02578 x 19.693 x 0.01520.
    drop = leg_drop_in_wg(100, equivalent_diameter_m(8 * 0.0254, 4 * 0.0254), 0.0000914, 3.048)
    assert drop == pytest.approx(0.007718, abs=2e-6)


@pytest.mark.parametrize("neck", [False, True])
def test_a_rectangular_trunk_off_a_plenum_is_graded_with_its_round_branches(ctx, neck):
    trunk_start = (20, 0) if neck else (22, 0)
    ducts = [_rect("TRUNK-8X4", trunk_start, (10, 0), 8, 4),
             _duct("BRANCH-4", (15, 0), (15, 3), diameter=4)]
    if neck:
        ducts.insert(0, _rect("NECK-6X4", (22, 0), (20, 0), 6, 4))
    rect_ctx = _rect_ctx(ctx, ducts)
    landings = radial_landings(rect_ctx)
    assert set(landings) == {d.tag for d in ducts}
    assert {d.tag for d in _network(rect_ctx, "ERV", landings)} == set(landings)

    def de(w, d):
        return 1.30 * (w * d) ** 0.625 / (w + d) ** 0.25 * 0.0254

    expected = leg_drop_in_wg(210, de(8, 4), 0.0000914, ducts[-2].length_m)
    expected += leg_drop_in_wg(25, 4 * 0.0254, 0.00009, 3)
    if neck:
        expected += leg_drop_in_wg(210, de(6, 4), 0.0000914, 2)
    finding = next(f for f in erv_static_budget(rect_ctx) if "worst path" in f.message)
    assert "via BRANCH-4" in finding.message
    assert f"at {expected:.3f} in. w.g." in finding.message


def test_a_rectangular_row_without_roughness_is_a_gap_by_its_pair(ctx):
    rect_ctx = _rect_ctx(ctx, [_rect("TRUNK-8X4", (22, 0), (10, 0), 8, 4)], roughness=None)
    gaps = [f for f in erv_static_budget(rect_ctx) if "no rectangular DuctProductType" in f.message]
    assert gaps and all(f.result is Result.UNKNOWN for f in gaps)
    assert 'galvanized, 8.0x4.0"' in gaps[0].message


def test_a_rectangle_is_never_anchored_by_a_mixing_box_or_pulled_in_by_a_round_joint(ctx):
    mix_type = EquipmentType(tag="MIX-T", name="mixing box", footprint=(m(0.02), m(0.4)),
                             height=m(0.2))
    mix = Equipment(uid="MIX", tag="MIX", kind=EquipmentKind.MIXING_BOX,
                    footprint=(m(0.02), m(0.4)), position=pt(m(40), m(0)), type_ref="MIX-T")
    stray = [_rect("RECT-MIX", (40, 0), (30, 0), 8, 4),          # ends in the mixing box
             _rect("RECT-OFF-ROUND", (11, 0), (11, 2), 8, 4)]    # tees off REMOTE-8's end
    rect_ctx = _rect_ctx(ctx, [*ctx.model.ducts, *stray], extra=(mix_type,))
    plan = rect_ctx.plan.model_copy(update={"elements": {
        "basement": (*rect_ctx.plan.elements["basement"], mix)}})
    objects = [*rect_ctx.model.canvas_objects, _body("MIX", 40, "MIX-T")]
    rect_ctx = check_context(model=replace(rect_ctx.model, plan=plan, canvas_objects=objects))
    network = {d.tag for d in _network(rect_ctx, "ERV", radial_landings(rect_ctx))}
    assert network == {d.tag for d in ctx.model.ducts}
    assert not any("RECT-" in f.message for f in erv_static_budget(rect_ctx))


def test_a_one_port_plenum_with_a_rectangular_collar_distributes_and_counts_its_neck(ctx):
    collar = ServicePort(tag="collar", service=Service.SUPPLY_AIR, position=(m(0), m(0), m(0)),
                         width=inch(6), depth=inch(4), certainty=PortCertainty.EXACT)
    rect_ctx = _rect_ctx(ctx, [_rect("NECK-6X4", (22, 0), (10, 0), 6, 4),
                               _duct("BRANCH-4", (15, 0), (15, 3), diameter=4)])
    lib = rect_ctx.plan.library
    plenum = lib.equipment_types[1].model_copy(update={
        "duct_ports": 1, "port_diameter": inch(6), "ports": (collar,)})
    plan = rect_ctx.plan.model_copy(update={"library": lib.model_copy(
        update={"equipment_types": (lib.equipment_types[0], plenum)})})
    rect_ctx = check_context(model=replace(rect_ctx.model, plan=plan))
    assert set(radial_landings(rect_ctx)) == {"NECK-6X4", "BRANCH-4"}
    census = next(f for f in erv_manifold_ports(rect_ctx) if "PLENUM" in f.message)
    assert census.result is Result.PASS and "1 of 1" in census.message


# --- per-path trunk chains and same-size tees (2026-11-11, note §9) -------------------------

def test_a_same_size_tee_is_a_branch_and_carries_its_parent_leg(ctx):
    # A 4" off a 4": the old size rule never hopped it, so its terminal went ungraded.
    ducts = [*ctx.model.ducts[:-1], _duct("RADIAL-4", (22, 0), (30, 0), diameter=4),
             _duct("TEE-4", (26, 0), (26, 3), diameter=4)]
    tee_ctx = check_context(model=replace(ctx.model, ducts=ducts))
    assert radial_landings(tee_ctx)["TEE-4"] == "PLENUM"
    pressure = sum(leg_drop_in_wg(d.design_cfm, d.diameter_m, 0.00009, d.length_m)
                   for d in ducts)
    finding = next(f for f in erv_static_budget(tee_ctx) if "worst path" in f.message)
    assert "via TEE-4" in finding.message and "RADIAL-4" in finding.message
    assert f"at {pressure:.3f} in. w.g." in finding.message


def test_a_trunk_off_the_path_is_not_charged_to_it_and_grades_on_its_own(ctx):
    mix_type = EquipmentType(tag="MIX-T", name="mixing box", footprint=(m(0.4), m(0.02)),
                             height=m(0.2))
    mix = Equipment(uid="MIX", tag="MIX", kind=EquipmentKind.MIXING_BOX,
                    footprint=(m(0.4), m(0.02)), position=pt(m(11), m(5)), type_ref="MIX-T")
    body = ResolvedCanvasObject(uid="MIX", tag="MIX", storey="basement", domain="mechanical",
        kind="Equipment", type_ref="MIX-T", room=None, position=(11, 5), z_m=1,
        rotation_degrees=0, footprint=[(10.8, 4.99), (11.2, 4.99), (11.2, 5.01), (10.8, 5.01)])
    side = _duct("SIDE-6", (11, 0), (11, 5))
    lib = ctx.plan.library
    plan = ctx.plan.model_copy(update={
        "elements": {"basement": (*ctx.plan.elements["basement"], mix)},
        "library": lib.model_copy(update={"equipment_types": (*lib.equipment_types, mix_type)})})
    side_ctx = check_context(model=replace(ctx.model, plan=plan, ducts=[*ctx.model.ducts, side],
                                           canvas_objects=[*ctx.model.canvas_objects, body]))
    on_path = sum(leg_drop_in_wg(d.design_cfm, d.diameter_m, 0.00009, d.length_m)
                  for d in ctx.model.ducts)
    finding = next(f for f in erv_static_budget(side_ctx) if "worst path" in f.message)
    assert "via RADIAL-4" in finding.message
    assert f"at {on_path:.3f} in. w.g." in finding.message
    # Lengthen the side trunk past the radial's route and it governs, into its own box.
    long_side = replace(side, length_m=40.0)
    side_ctx.model.ducts = [*ctx.model.ducts, long_side]
    finding = next(f for f in erv_static_budget(side_ctx) if "worst path" in f.message)
    assert "via SIDE-6 into MIX" in finding.message


def test_a_tapped_trunk_is_charged_per_stretch_and_only_to_the_tap(ctx):
    # SIDE-4 (60 cfm) taps REMOTE-8 half way. The radial pays REMOTE-8's far half at 150 cfm;
    # SIDE-4's own path pays only the near half (note §9, ``erv_segments``).
    mix_type = EquipmentType(tag="MIX-T", name="mixing box", footprint=(m(0.4), m(0.02)),
                             height=m(0.2))
    mix = Equipment(uid="MIX", tag="MIX", kind=EquipmentKind.MIXING_BOX,
                    footprint=(m(0.4), m(0.02)), position=pt(m(6), m(30)), type_ref="MIX-T")
    body = ResolvedCanvasObject(uid="MIX", tag="MIX", storey="basement", domain="mechanical",
        kind="Equipment", type_ref="MIX-T", room=None, position=(6, 30), z_m=1,
        rotation_degrees=0, footprint=[(5.8, 29.99), (6.2, 29.99), (6.2, 30.01), (5.8, 30.01)])
    side = replace(_duct("SIDE-4", (6, 0), (6, 30), diameter=4), design_cfm=60)
    lib = ctx.plan.library
    plan = ctx.plan.model_copy(update={
        "elements": {"basement": (*ctx.plan.elements["basement"], mix)},
        "library": lib.model_copy(update={"equipment_types": (*lib.equipment_types, mix_type)})})
    tap_ctx = check_context(model=replace(ctx.model, plan=plan, ducts=[*ctx.model.ducts, side],
                                          canvas_objects=[*ctx.model.canvas_objects, body]))
    eight, six, four = 8 * 0.0254, 6 * 0.0254, 4 * 0.0254

    def drop(cfm, bore, length):
        return leg_drop_in_wg(cfm, bore, 0.00009, length)

    rest = sum(drop(d.design_cfm, d.diameter_m, d.length_m) for d in ctx.model.ducts
               if d.tag != "REMOTE-8")
    radial = rest + drop(210, eight, 5) + drop(150, eight, 5)
    via_side = drop(210, six, 1) + drop(210, eight, 5) + drop(60, four, 30)
    finding = next(f for f in erv_static_budget(tap_ctx) if "worst path" in f.message)
    assert via_side > radial and "via SIDE-4 into MIX" in finding.message
    assert f"at {via_side:.3f} in. w.g." in finding.message
    side_ctx = check_context(model=replace(tap_ctx.model, ducts=[
        *ctx.model.ducts, replace(side, path=[(6, 0), (6, 1)], length_m=1.0)]))
    finding = next(f for f in erv_static_budget(side_ctx) if "worst path" in f.message)
    assert "via RADIAL-4" in finding.message and f"at {radial:.3f} in. w.g." in finding.message
