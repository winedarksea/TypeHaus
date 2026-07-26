"""Circuit model + ``electrical.circuit_refs`` + service-entrance device kinds (WS1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.model import (Building, Circuit, DeviceKind, ElectricalDevice, ElectricalDeviceType,
                            Library, PlanModel, Project, Service, ServicePort, Site, Storey, m, pt)
from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def _plan(circuits=(), devices=(), types=()):
    return PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000002",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(circuits=tuple(circuits), electrical_device_types=tuple(types)),
        elements={"main": tuple(devices)},
    )


def _findings(plan, check_id):
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    report = run_from_model(model, [], tier=Tier.ADVISORY)
    return [f for f in report.findings if f.check_id == check_id]


_PANEL = ElectricalDevice(tag="ED-M-PANEL", kind=DeviceKind.PANEL, position=pt(m(0), m(0)))
_PORT_120 = ServicePort(tag="power", service=Service.POWER_120, position=(m(0), m(0), m(0)))
_PORT_240 = ServicePort(tag="power240", service=Service.POWER_240, position=(m(0), m(0), m(0)))


def test_circuit_refs_unknown_without_circuits():
    findings = _findings(_plan(devices=(_PANEL,)), "electrical.circuit_refs")
    assert [f.result.value for f in findings] == ["unknown"]


def test_circuit_refs_pass_when_everything_reconciles():
    plan = _plan(
        circuits=(Circuit(tag="CKT-01", panel_ref="ED-M-PANEL", breaker_amps=20),),
        types=(ElectricalDeviceType(tag="ED-T", name="Outlet", footprint=(m(.1), m(.1)),
                                    height=m(.05), ports=(_PORT_120,)),),
        devices=(_PANEL, ElectricalDevice(tag="ED-M-RC1", kind=DeviceKind.RECEPTACLE,
                                          position=pt(m(1), m(0)), type_ref="ED-T",
                                          circuit="CKT-01")),
    )
    findings = _findings(plan, "electrical.circuit_refs")
    assert [f.result.value for f in findings] == ["pass"]


def test_circuit_refs_flags_dangling_reference_and_missing_panel():
    plan = _plan(
        circuits=(Circuit(tag="CKT-01", panel_ref="ED-M-NOPE", breaker_amps=20),),
        devices=(_PANEL, ElectricalDevice(tag="ED-M-RC1", kind=DeviceKind.RECEPTACLE,
                                          position=pt(m(1), m(0)), circuit="CKT-99")),
    )
    findings = _findings(plan, "electrical.circuit_refs")
    messages = " | ".join(f.message for f in findings if f.result.value == "fail")
    assert "missing panel ED-M-NOPE" in messages
    assert "unknown circuit CKT-99" in messages


def test_circuit_refs_flags_pole_port_mismatch():
    plan = _plan(
        circuits=(Circuit(tag="CKT-EV", panel_ref="ED-M-PANEL", breaker_amps=50, poles=2),),
        types=(ElectricalDeviceType(tag="ED-T-120", name="Outlet", footprint=(m(.1), m(.1)),
                                    height=m(.05), ports=(_PORT_120,)),),
        devices=(_PANEL, ElectricalDevice(tag="ED-M-RC1", kind=DeviceKind.RECEPTACLE,
                                          position=pt(m(1), m(0)), type_ref="ED-T-120",
                                          circuit="CKT-EV")),
    )
    findings = _findings(plan, "electrical.circuit_refs")
    fails = [f for f in findings if f.result.value == "fail"]
    assert fails and "no power_240 port" in fails[0].message


def test_dual_port_type_satisfies_either_pole_count():
    """The two-gang 5-20R/6-20R precedent: a type with both ports passes on any circuit."""
    dual = ElectricalDeviceType(tag="ED-T-DUAL", name="Kettle outlet", footprint=(m(.1), m(.1)),
                                height=m(.05), ports=(_PORT_120, _PORT_240))
    plan = _plan(
        circuits=(Circuit(tag="CKT-A", panel_ref="ED-M-PANEL", breaker_amps=20, poles=2),),
        types=(dual,),
        devices=(_PANEL, ElectricalDevice(tag="ED-M-KET", kind=DeviceKind.RECEPTACLE_240,
                                          position=pt(m(1), m(0)), type_ref="ED-T-DUAL",
                                          circuit="CKT-A")),
    )
    findings = _findings(plan, "electrical.circuit_refs")
    assert [f.result.value for f in findings] == ["pass"]


def test_service_entrance_device_kinds_get_dedicated_ifc_classes(tmp_path: Path):
    """junction_box/meter/disconnect must not fall through to IfcBuildingElementProxy —
    and the diff adapter must read the same classes back (clean round-trip)."""
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.diff import build_report
    from typehaus.diff.ifc_adapter import baseline_elems, external_elems
    from typehaus.emit.ifc.emitter import emit_ifc

    plan = _plan(devices=(
        ElectricalDevice(uid="TESTJB0001", tag="ED-M-JB", kind=DeviceKind.JUNCTION_BOX,
                         position=pt(m(0), m(0))),
        ElectricalDevice(uid="TESTMT0001", tag="ED-M-METER", kind=DeviceKind.METER,
                         position=pt(m(1), m(0))),
        ElectricalDevice(uid="TESTDS0001", tag="ED-M-DISC", kind=DeviceKind.DISCONNECT,
                         position=pt(m(2), m(0))),
    ))
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    f = ifcopenshell.open(str(emit_ifc(model, tmp_path / "kinds.ifc")))
    assert {p.Name for p in f.by_type("IfcJunctionBox")} == {"ED-M-JB"}
    assert {p.Name for p in f.by_type("IfcFlowMeter")} == {"ED-M-METER"}
    assert {p.Name for p in f.by_type("IfcSwitchingDevice")} == {"ED-M-DISC"}
    report = build_report(baseline_elems(model), external_elems(tmp_path / "kinds.ifc"))
    assert not report.substantive(), [
        (change.kind, change.tag) for change in report.substantive()]


def _room_plan(project, devices=()):
    """A 20'x14' LIVING room with four walls — the receptacle-spacing fixture."""
    from typehaus.model import (Assembly, FramingSpec, Layer, LayerFunction, Material, Node,
                                Occupancy, Room, Wall, ft, inch)

    lib = Library(
        materials=(Material(tag="spf", name="SPF", r_per_inch=1.25),
                   Material(tag="gwb", name="GWB", r_per_inch=0.9)),
        assemblies=(Assembly(tag="EXT", layers=(
            Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                  function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),),
            default_lining=(Layer(name="gwb", material_ref="gwb", thickness=inch(0.625),
                                  function=LayerFunction.FINISH),)),),
    )
    storey = Storey(uid="ST00000001", tag="s1", elevation=ft(0), default_ceiling_height=ft(9))
    nodes = [Node(uid=f"N{i:09d}", tag=f"N-{i}", position=p) for i, p in enumerate(
        [pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14))], 1)]
    walls = [Wall(uid=f"W{i:09d}", tag=f"W-{i}", start_node=f"N-{a}", end_node=f"N-{b}",
                  assembly="EXT", top=ft(9))
             for i, (a, b) in enumerate([(1, 2), (2, 3), (3, 4), (4, 1)], 1)]
    room = Room(uid="RM00000001", tag="RM-1", seed=pt(ft(10), ft(7)),
                occupancy=Occupancy.LIVING)
    return (PlanModel(project=project, library=lib, storeys=(storey,))
            .with_elements("s1", [*nodes, *walls, room, *devices]))


def _spacing_findings(plan):
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    report = run_from_model(model, [], tier=Tier.ADVISORY)
    return [f for f in report.findings
            if f.check_id == "electrical.receptacle_spacing" and "RM-1" in f.element_tags]


def test_receptacle_spacing_fails_a_bare_room(project):
    from typehaus.model import ft as _ft

    plan = _room_plan(project, devices=(
        ElectricalDevice(uid="TESTRC0000", tag="ED-S1-SW", kind=DeviceKind.SWITCH,
                         position=pt(_ft(1), _ft(1))),))
    findings = _spacing_findings(plan)
    assert [f.result.value for f in findings] == ["fail"]


def test_receptacle_spacing_passes_with_even_coverage(project):
    from typehaus.model import ft as _ft

    spots = [(5, 0), (15, 0), (20, 4), (20, 10), (15, 14), (5, 14), (0, 10), (0, 4)]
    devices = [
        ElectricalDevice(uid=f"TESTRC{i:04d}", tag=f"ED-S1-RC{i}", kind=DeviceKind.RECEPTACLE,
                         position=pt(_ft(x), _ft(y)))
        for i, (x, y) in enumerate(spots, 1)]
    findings = _spacing_findings(_room_plan(project, devices=devices))
    assert [f.result.value for f in findings] == ["pass"]


def test_receptacle_spacing_flags_a_single_far_receptacle(project):
    """One receptacle in a door-free 68' perimeter leaves arcs far over the 12' limit."""
    from typehaus.model import ft as _ft

    devices = (ElectricalDevice(uid="TESTRC0001", tag="ED-S1-RC1",
                                kind=DeviceKind.RECEPTACLE, position=pt(_ft(5), _ft(0))),)
    findings = _spacing_findings(_room_plan(project, devices=devices))
    assert [f.result.value for f in findings] == ["fail"]


# --- catlin: the authored schedule reconciles and the derived numbers fired -----------

def test_catlin_panel_schedule_is_derived(catlin_model):
    from typehaus.takeoff import backup_component_rows, panel_schedule, service_load_summary

    rows = {row["circuit"]: row for row in panel_schedule(catlin_model)}
    assert len(rows) == 31
    # The radiant floor is a heating circuit in an all-electric house, so it is on the
    # schedule with breaker-level GFCI (NEC 424.44(G) — heating cable in a bathroom floor).
    assert rows["CKT-FH-SAUNA"]["gfci"] and rows["CKT-FH-SAUNA"]["volts"] == 120
    assert rows["CKT-FH-SAUNA"]["devices"] == ["ED-B-SAUNA-FH-STAT"]
    # Derived from the device type's load_va, not authored on the circuit.
    assert rows["CKT-EV-1450"]["connected_va"] == 9600
    assert rows["CKT-EV-1450"]["devices"] == ["ED-G-EV-1450"]
    assert rows["CKT-DRYER"]["connected_va"] == 5000
    # The notes' backup set is flagged.
    backup = {tag for tag, row in rows.items() if row["backup"]}
    assert backup == {"CKT-WH-HP", "CKT-SUMP", "CKT-FRIDGE", "CKT-HA",
                      "CKT-LT-BACKUP", "CKT-MINI-2"}
    # ceil(6 backup circuits / 4 channels) = 2 relays, one PSU, one UPS, and a contactor
    # for each backup circuit a 16A relay channel can't switch directly (sump 20A,
    # fridge 20A, the 2-pole minisplit).
    components = {row["component"]: row["count"] for row in backup_component_rows(catlin_model)}
    assert components["Shelly Pro 4PM 4-channel DIN relay"] == 2
    assert components["DIN contactor (relay-driven)"] == 3
    load = service_load_summary(catlin_model)
    assert load["floor_area_ft2"] > 4000
    assert load["demand_amps"] > 100  # a real number, not a stub
    assert load["panel_rating_amps"] == 225 and load["service_amps"] == 200


def test_catlin_receptacle_spacing_passes_after_fill(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    findings = [f for f in report.findings if f.check_id == "electrical.receptacle_spacing"]
    fails = [f for f in findings if f.result.value == "fail"]
    assert not fails, [f.message for f in fails]
    passes = [f for f in findings if f.result.value == "pass"]
    assert len(passes) == 12  # every habitable room
    # The kitchen-counter rule stays visibly unevaluated.
    assert any(f.result.value == "unknown" for f in findings)


def test_catlin_circuit_refs_reconcile(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    findings = [f for f in report.findings if f.check_id == "electrical.circuit_refs"]
    assert [f.result.value for f in findings] == ["pass"]


def test_panel_schedule_sheet_is_in_the_permit_set(catlin_model):
    from typehaus.emit.draw.sheets import build_sheet_index

    numbers = {sheet.number for sheet in build_sheet_index(catlin_model)}
    assert "E-601" in numbers
    assert {"E-101", "E-102", "E-103", "E-104", "E-105"} <= numbers  # all five storeys


def test_conduit_run_developed_length(project):
    """Length = plan polyline + the vertical rise between the absolute end elevations."""
    from typehaus.model import ConduitRun, ft, inch

    plan = _plan(devices=()).with_elements("main", (
        ConduitRun(uid="TESTCD0001", tag="CD-1", trade_size=inch(1),
                   path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))),
                   start_elevation=ft(0), end_elevation=ft(10)),))
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    run = model.conduits[0]
    assert abs(run.length_m - 20 * 0.3048) < 1e-6
    from typehaus.takeoff import conduit_takeoff
    rows = conduit_takeoff(model)
    assert rows == [{"trade_size_in": 1.0, "runs": 1, "length_ft": 20.0, "tags": ["CD-1"]}]


def test_conduit_emits_cable_carrier_segments(project, tmp_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc.emitter import emit_ifc
    from typehaus.model import ConduitRun, ft, inch

    plan = _plan(devices=()).with_elements("main", (
        ConduitRun(uid="TESTCD0002", tag="CD-2", trade_size=inch(1),
                   path=(pt(ft(0), ft(0)), pt(ft(10), ft(0)), pt(ft(10), ft(8))),
                   start_elevation=ft(0), end_elevation=ft(9)),))
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    f = ifcopenshell.open(str(emit_ifc(model, tmp_path / "conduit.ifc")))
    segments = f.by_type("IfcCableCarrierSegment")
    # Two plan legs + one riser (9' rise), each a CONDUITSEGMENT with a stable guid.
    assert len(segments) == 3
    assert all(s.PredefinedType == "CONDUITSEGMENT" and s.GlobalId for s in segments)


def test_catlin_conduit_trunks(catlin_model):
    from typehaus.takeoff import conduit_takeoff

    assert len(catlin_model.conduits) == 4
    assert all(run.from_ref == "ED-B-PANEL" for run in catlin_model.conduits)
    rows = conduit_takeoff(catlin_model)
    assert {row["trade_size_in"] for row in rows} == {0.75, 1.0, 1.25, 1.5}
    assert all(20 < row["length_ft"] < 60 for row in rows)
    # The PV riser reaches the attic junction box.
    riser = next(run for run in catlin_model.conduits if run.tag == "CD-B-ATTIC-RISER")
    assert riser.to_ref == "ED-A-PV-JB" and riser.z_end_m > 7.0


def test_bill_of_materials_carries_the_electrical_sections(catlin_model):
    """The BOM is one payload, nothing dropped — the WS6 sections ride along and every
    number is the same derived value the standalone takeoffs report."""
    from typehaus.takeoff import bill_of_materials, panel_schedule

    bom = bill_of_materials(catlin_model)
    for section in ("electrical_devices", "panel_schedule", "service_load", "conduit",
                    "solar", "backup_components"):
        assert section in bom, section
    assert bom["panel_schedule"] == panel_schedule(catlin_model)
    assert bom["solar"]["total_watts"] == 5280
    assert bom["solar"]["panels"] == 12
    devices = {(row["kind"], row["type"]): row["count"] for row in bom["electrical_devices"]}
    assert devices[("meter", "ED-T-METER")] == 1
    assert devices[("receptacle_240", "ED-T-EV-1450")] == 1
    assert sum(row["count"] for row in bom["electrical_devices"]) == sum(
        1 for storey in catlin_model.plan.storeys
        for element in catlin_model.plan.storey_elements(storey.tag)
        if element.element_kind == "ElectricalDevice")
    assert len(bom["conduit"]) == 4
    assert bom["backup_components"][0]["count"] == 2  # ceil(6/4) relays


def test_circuit_is_schedule_data_not_geometry():
    """A Circuit never enters storey element lists; it lives in Library.circuits."""
    circuit = Circuit(tag="CKT-01", panel_ref="ED-B-PANEL", breaker_amps=20, backup=True)
    assert circuit.poles == 1 and circuit.backup and not circuit.gfci
    library = Library(circuits=(circuit,))
    assert library.circuits[0].tag == "CKT-01"


# --- model.json: the circuits reader's contract ---------------------------------------

def test_model_json_carries_the_electrical_takeoff(catlin_model):
    """The browser reads the *same* derivation the E-601 sheet prints, never its own.

    A UI that re-summed the schedule could disagree with the drawing stamped for permit,
    so model.json carries takeoff/electrical.py's output verbatim.
    """
    from typehaus.server.model_json import model_to_dict
    from typehaus.takeoff import (conduit_takeoff, electrical_device_takeoff, panel_schedule,
                                  service_load_summary, solar_takeoff)

    payload = model_to_dict(catlin_model)["electrical"]
    assert set(payload) == {"panel_schedule", "service_load", "conduit", "devices", "solar",
                            "backup_components"}
    assert payload["panel_schedule"] == panel_schedule(catlin_model)
    assert payload["service_load"] == service_load_summary(catlin_model)
    assert payload["conduit"] == conduit_takeoff(catlin_model)
    assert payload["devices"] == electrical_device_takeoff(catlin_model)
    assert payload["solar"] == solar_takeoff(catlin_model)
    assert len(payload["panel_schedule"]) == 31


def test_model_json_canvas_objects_carry_their_circuit(catlin_model):
    """The device end of the circuit edge — what the inspector reads off a selection."""
    from typehaus.server.model_json import model_to_dict

    objects = {item["tag"]: item for item in model_to_dict(catlin_model)["canvas_objects"]}
    assert objects["ED-G-EV-1450"]["circuit"] == "CKT-EV-1450"
    # Equipment consumes power too; a placeable that doesn't reports None rather than
    # omitting the key, so the UI can tell "no circuit" from "old model.json".
    assert objects["EQ-B-WH"]["circuit"] == "CKT-WH-HP"
    assert all("circuit" in item for item in objects.values() if item["domain"] != "opening")
    # Every tag the schedule names is addressable in the canvas-object index — this is the
    # edge the reader's device tags zoom through.
    for row in model_to_dict(catlin_model)["electrical"]["panel_schedule"]:
        for tag in row["devices"]:
            assert tag in objects, tag


def test_service_load_is_null_without_circuits():
    """A house that authors no circuits gets no estimate — the summary would be over nothing."""
    from typehaus.server.model_json import model_to_dict

    model, _findings = resolve(_plan())
    payload = model_to_dict(model)["electrical"]
    assert payload["service_load"] is None
    assert payload["panel_schedule"] == [] and payload["conduit"] == []
