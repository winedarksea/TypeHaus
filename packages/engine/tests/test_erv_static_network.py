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
from typehaus.checks.mep.erv_static import _network, erv_static_budget, radial_landings
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
