"""Circuit model + ``electrical.circuit_refs`` + service-entrance device kinds (WS1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.model import (BackupTier, Building, Circuit, DeviceKind, ElectricalDevice, ElectricalDeviceType,
                            Library, PlanModel, Project, Service, ServicePort, Site, Storey, m, pt)
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR


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
    # 36: 36 after the 2026-08-02 microgrid refactor retired CKT-BACKUP-FEED, plus
    # CKT-DISPOSAL (2026-08-07), minus CKT-WH-HP folded into CKT-WH-240 (2026-08-15) when
    # the two-tank water heater became one.
    assert len(rows) == 36
    # Each radiant floor zone is its own 120V circuit with breaker-level GFCI, controlled
    # by one thermostat (NEC 424.44(G) — heating cable in a bathroom or kitchen floor; the
    # dining zone takes the same protection because every mat maker asks for it).
    for circuit, stat in (("CKT-FH-BATH2", "ED-M-BATH2-FH-STAT"),
                          ("CKT-FH-DINING", "ED-M-DINING-FH-STAT"),
                          ("CKT-FH-BATH1", "ED-S-BATH1-FH-STAT")):
        assert rows[circuit]["gfci"] and rows[circuit]["volts"] == 120
        assert rows[circuit]["breaker_amps"] == 15
        assert rows[circuit]["devices"] == [stat]
    # The two 1.5 kW resistance heaters: 20A because 12.5A x 1.25 continuous needs 16A, and
    # no GFCI because both are hard-wired equipment rather than receptacles (210.8(A)).
    for circuit, equipment in (("CKT-FIREPLACE", "EQ-M-FIREPLACE"),
                               ("CKT-GAR-HEAT", "EQ-G-HEATER")):
        assert rows[circuit]["connected_va"] == 1500
        assert rows[circuit]["breaker_amps"] == 20 and not rows[circuit]["gfci"]
        assert rows[circuit]["devices"] == [equipment]
    # The EV circuits author load_va so LM-EV can read the managed group off the circuits;
    # the figure is the same 240x40 the receptacle type carries, so the row is unchanged.
    assert rows["CKT-EV-1450"]["connected_va"] == 9600
    assert rows["CKT-EV-1450"]["devices"] == ["ED-G-EV-1450"]
    # 830 W, not the 5,000 VA the 14-30R receptacle type carries: the dryer is a ventless
    # heat-pump machine and CKT-DRYER authors its nameplate (2026-08-15). The 30A branch and
    # the 14-30R stay — a provision for a future vented dryer — which is exactly why the
    # receptacle-derived figure was the wrong one to let stand on a service with no room.
    assert rows["CKT-DRYER"]["connected_va"] == 830
    # The notes' backup set is tiered, and every one of them is on the subpanel. CKT-WH-240
    # joined the SHED tier 2026-08-15 in place of CKT-WH-HP, when the two-tank water heater
    # became one ProTerra on one (governed) circuit.
    backup = {tag for tag, row in rows.items() if row["backup"]}
    assert backup == {"CKT-WH-240", "CKT-SUMP", "CKT-FRIDGE", "CKT-HA",
                      "CKT-LT-BACKUP", "CKT-HP3"}
    assert {tag for tag, row in rows.items() if row["backup_tier"] == "always_on"} == {
        "CKT-FRIDGE", "CKT-HA", "CKT-LT-BACKUP"}
    assert {tag for tag, row in rows.items() if row["backup_tier"] == "shed"} == {
        "CKT-WH-240", "CKT-SUMP", "CKT-HP3"}
    assert all(rows[tag]["panel"] == "ED-B-BACKUP-PANEL" for tag in backup)
    # Only the SHED tier buys switching gear — that is what the tier means. Every shed
    # circuit is now 2-pole or over the 16A relay-channel limit (CKT-WH-240 joined CKT-SUMP
    # at 20A and the 2-pole CKT-HP3), so no circuit switches through a direct relay channel
    # any more — but the relay itself is still bought, to drive the three contactor coils.
    # The always-on tier contributes none, where the old flat `backup` flag bought three.
    components = {row["component"]: row["count"] for row in backup_component_rows(catlin_model)}
    assert components["Shelly Pro 4PM 4-channel DIN relay"] == 1
    assert components["DIN contactor (relay-driven)"] == 3
    # The source circuit is a source, and the schedule says so rather than leaving a reader
    # to infer it from a zero.
    assert rows["CKT-ESS-GRID"]["source"] and not rows["CKT-ESS-GRID"]["backup"]
    load = service_load_summary(catlin_model)
    assert load["floor_area_ft2"] > 4000
    assert load["demand_amps"] > 100  # a real number, not a stub
    assert load["panel_rating_amps"] == 225 and load["service_amps"] == 200
    # 220.82(C) selects, it does not sum: six separately controlled resistance heaters
    # (three mats, the fireplace, the garage heater, and since 2026-08-15 EQ-S-HP1-STRIP's
    # 2 kW supply-plenum duct heater) are taken at 40% and lose to the three heat-pump
    # systems at 100%, so the heating term is the heat pumps' and the resistance heat costs
    # the service nothing. The heat-pump circuits are identified by the typed Equipment on
    # them, not by a word in the description (takeoff/electrical._is_heat_pump).
    assert load["resistance_heat_units"] == 6 and load["resistance_heat_factor"] == 0.40
    assert load["hvac_va"] == load["heat_pump_va"] > load["resistance_heat_va"] * 0.40


def test_catlin_receptacle_spacing_passes_after_fill(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    findings = [f for f in report.findings if f.check_id == "electrical.receptacle_spacing"]
    fails = [f for f in findings if f.result.value == "fail"]
    assert not fails, [f.message for f in fails]
    passes = [f for f in findings if f.result.value == "pass"]
    assert len(passes) == 11  # every habitable room (RM-A-EAST-UNFIN is storage, not living)
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

    # 4 power trunks + the 3 ESS microgrid runs + the 8 structured-cabling runs. The last
    # three arrived 2026-08-22 with the workshop, study and media-room drops — and one of
    # them, CD-B-DATA-SHOP, is the answer to "can it share the spa conduit": it runs 6" east
    # of CD-B-SPA and parallel to it the whole way, because NEC 800.133/725 forbids comms
    # sharing a RACEWAY with power and `ConduitRun.service` is one value, never a set.
    assert len(catlin_model.conduits) == 15
    # Not all from the panel any more: the three 2026-08-02 microgrid runs start at the PV
    # junction box and at the inverter, and every data run starts at the patch enclosure.
    assert {run.from_ref for run in catlin_model.conduits} == {
        "ED-B-PANEL", "ED-A-PV-JB", "EQ-B-ESS-INV", "ED-B-NET-PATCH"}
    rows = conduit_takeoff(catlin_model)
    # Power only — data and the capped spare are billed by takeoff/data.py, because comms
    # and power are separate orders pulled by separate trades and may not share a raceway.
    assert {row["trade_size_in"] for row in rows} == {0.75, 1.0, 1.25, 1.5}
    # A loose sanity band, not a contract: no trunk group is a stub and none crosses the
    # house twice. The 1" group sits at 60 ft because it is four runs, not one.
    assert all(20 < row["length_ft"] < 70 for row in rows)
    assert not [run.tag for row in rows for run in catlin_model.conduits
                if run.tag in row["tags"] and run.service in ("data", None)]
    # The PV riser reaches the attic junction box.
    riser = next(run for run in catlin_model.conduits if run.tag == "CD-B-ATTIC-RISER")
    assert riser.to_ref == "ED-A-PV-JB" and riser.z_end_m > 7.0


def test_bill_of_materials_carries_the_electrical_sections(catlin_model):
    """The BOM is one payload, nothing dropped — the WS6 sections ride along and every
    number is the same derived value the standalone takeoffs report."""
    from typehaus.takeoff import bill_of_materials, panel_schedule

    bom = bill_of_materials(catlin_model)
    for section in ("electrical_devices", "panel_schedule", "service_load", "conduit",
                    "solar", "backup_power"):
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
    # Rows are trade-size groups, not runs: the three 1" microgrid runs join the group the
    # 1" trunk already made.
    assert len(bom["conduit"]) == 4
    # The microgrid section is derived twice over: the placed ESS hardware, then the
    # shed-tier switching gear. The first row is the inverter because equipment leads.
    components = bom["backup_power"]["components"]
    assert components[0]["component"].startswith("EG4 12kPV")
    assert any(row["component"].startswith("EG4 PowerPro") for row in components)
    relays = next(row for row in components if "Pro 4PM" in row["component"])
    assert relays["count"] == 1  # drives the shed-tier contactor coils
    contactors = next(row for row in components if "contactor" in row["component"])
    assert contactors["count"] == 3  # CKT-HP3 (2-pole), CKT-SUMP (20A), CKT-WH-240 (2-pole)
    assert bom["backup_power"]["runtime"]["modeled"] is True


# --- panel spaces + slot map ----------------------------------------------------------

def _panel_with_spaces(spaces):
    """A synthetic panel whose type declares the enclosure size."""
    panel_type = ElectricalDeviceType(tag="ED-T-PNL", name="Panel", footprint=(m(.5), m(.1)),
                                      height=m(1), spaces=spaces, ports=(_PORT_240,))
    panel = ElectricalDevice(tag="ED-M-PANEL", kind=DeviceKind.PANEL,
                             position=pt(m(0), m(0)), type_ref="ED-T-PNL")
    return panel_type, panel


def _spaces_findings(spaces, circuits):
    panel_type, panel = _panel_with_spaces(spaces)
    plan = _plan(circuits=circuits, devices=(panel,), types=(panel_type,))
    return _findings(plan, "electrical.panel_spaces")


def test_panel_spaces_pass_and_fail_on_capacity():
    circuits = tuple(
        Circuit(tag=f"CKT-{i}", panel_ref="ED-M-PANEL", breaker_amps=20, poles=2,
                slot=1 + 4 * i)
        for i in range(3))  # 6 spaces at slots 1/3, 5/7, 9/11
    results = [f.result.value for f in _spaces_findings(12, circuits)]
    assert results == ["pass"]
    results = [f.result.value for f in _spaces_findings(4, circuits)]
    assert "fail" in results  # 6 required > 4, and slots run past the enclosure


def test_panel_spaces_flags_overlapping_slots():
    circuits = (
        Circuit(tag="CKT-A", panel_ref="ED-M-PANEL", breaker_amps=30, poles=2, slot=1),
        Circuit(tag="CKT-B", panel_ref="ED-M-PANEL", breaker_amps=20, poles=1, slot=3),
    )  # 2-pole at 1 occupies 1 and 3; CKT-B collides at 3
    findings = _spaces_findings(12, circuits)
    fails = [f for f in findings if f.result.value == "fail"]
    assert fails and "slot 3" in fails[0].message


def test_panel_spaces_unknown_without_declared_spaces():
    circuits = (Circuit(tag="CKT-A", panel_ref="ED-M-PANEL", breaker_amps=20),)
    findings = _spaces_findings(None, circuits)
    assert [f.result.value for f in findings] == ["unknown"]


def test_catlin_slot_map_is_complete_and_unique(catlin_model):
    """Every authored circuit holds a slot; positions never collide *within a panel*;
    columns are honest (2-pole pairs share a column because slot and slot+2 have the same
    parity).

    Per panel since 2026-08-02: the house has two enclosures now, and slot 2 of the backup
    subpanel is a different piece of metal from slot 2 of the service panel. Collapsing
    them into one map made the second panel's first circuit look like a double-tap.
    """
    circuits = catlin_model.plan.library.circuits
    assert all(circuit.slot is not None for circuit in circuits)
    assert len({c.panel_ref for c in circuits}) == 2
    occupied: dict = {}
    for circuit in circuits:
        positions = (circuit.slot,) if circuit.poles == 1 else (circuit.slot,
                                                                circuit.slot + 2)
        for position in positions:
            key = (circuit.panel_ref, position)
            assert key not in occupied, (key, circuit.tag, occupied[key])
            occupied[key] = circuit.tag
    assert len(occupied) == sum(circuit.poles for circuit in circuits)


def test_catlin_panel_spaces_fits_the_54_space_enclosure(catlin_model):
    """ED-T-PANEL was a 42-space enclosure carrying a 52-space schedule, so this check
    used to FAIL by design and the last ten circuits sat past the bus. The panel was
    swapped for a 54-space unit (plan/mep.py), and the check now PASSES.

    Since 2026-08-02 the check reconciles *both* enclosures, and the service panel is far
    less crowded: moving the six backup circuits and retiring CKT-BACKUP-FEED took it from
    52 spaces of 54 down to 44 (2026-08-07's CKT-DISPOSAL and 2026-08-15's CKT-WH-240 move
    to the backup subpanel land it at 43), with the subpanel carrying 8 of its 12. All four
    numbers are measured off the model, never pinned."""
    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    findings = [f for f in report.findings if f.check_id == "electrical.panel_spaces"]
    assert findings
    assert all(f.result.value == "pass" for f in findings), [f.message for f in findings]
    circuits = catlin_model.plan.library.circuits
    types = {t.tag: t for t in catlin_model.plan.library.electrical_device_types}

    def spaces(panel_ref: str, type_ref: str) -> tuple:
        return (sum(c.poles for c in circuits if c.panel_ref == panel_ref),
                types[type_ref].spaces)

    main = spaces("ED-B-PANEL", "ED-T-PANEL")
    backup = spaces("ED-B-BACKUP-PANEL", "ED-T-BACKUP-PANEL")
    assert main[0] <= main[1] and backup[0] <= backup[1]
    assert main == (43, 54)  # CKT-DISPOSAL spent one, CKT-WH-240's move to backup freed two
    assert backup == (8, 12)
    required = sum(circuit.poles for circuit in circuits)
    declared = main[1]
    # And the enclosure it replaced still would not have held the schedule — which is why
    # it was replaced, and what keeps this from passing for the wrong reason.
    retagged = tuple(c.model_copy(update={"panel_ref": "ED-M-PANEL"}) for c in circuits)
    assert any(f.result.value == "fail" for f in _spaces_findings(42, retagged))


# --- service load + load management ---------------------------------------------------

def test_catlin_service_load_finding_reflects_the_ems_decision(catlin_model):
    """Catlin settled the open service-load decision with an EMS (LM-EV, plan/circuits.py)
    rather than a service upgrade, so the raw 220.82 demand is still over the 200A service
    while the *managed* demand fits. The amps come off the takeoff, never pinned here.

    Both branches are live: if the house ever slims under the service on its own, or if
    the credit ever stops covering the overage, the check has to agree either way."""
    from typehaus.takeoff import service_load_summary

    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    findings = [f for f in report.findings if f.check_id == "electrical.service_load"]
    summary = service_load_summary(catlin_model)
    assert findings

    managements = catlin_model.plan.library.load_managements
    circuits = {c.tag: c for c in catlin_model.plan.library.circuits}
    assert managements, "the EMS decision is authored, not open"
    credit_va = 0.0
    for management in managements:
        group_va = sum(circuits[tag].load_va or 0.0 for tag in management.managed_circuits)
        credit_va += max(0.0, group_va - management.max_simultaneous_va)
    assert credit_va > 0, "an EMS that credits nothing is not managing anything"
    managed_amps = float(summary["demand_va"]) / 240.0 - credit_va / 240.0

    if managed_amps > float(summary["service_amps"]):
        fails = [f for f in findings if f.result.value == "fail"]
        assert fails, [f.message for f in findings]
        assert "625.42" in fails[0].message and "interlock" in fails[0].message
        assert "service upgrade" in fails[0].message
        assert f"{summary['service_amps']:.0f}A" in fails[0].message
    else:
        assert all(f.result.value == "pass" for f in findings), [
            f.message for f in findings]
        assert any("load-management credit" in f.message for f in findings)


def test_load_management_credits_the_managed_excess():
    """A synthetic EMS over a big managed group flips service_load from fail to pass."""
    from typehaus.model import LoadManagement

    big = Circuit(tag="CKT-KILN", panel_ref="ED-M-PANEL", breaker_amps=100, poles=2,
                  load_va=150000, description="Kiln bank")
    base = _plan(circuits=(big,), devices=(_PANEL,))

    def _run(library):
        model, findings = resolve(base.model_copy(update={"library": library}))
        assert not [f for f in findings if f.severity.value == "error"]
        report = run_from_model(model, [], tier=Tier.ADVISORY)
        return [f for f in report.findings if f.check_id == "electrical.service_load"]

    unmanaged = _run(Library(circuits=(big,)))
    assert any(f.result.value == "fail" for f in unmanaged)

    ems = LoadManagement(tag="LM-KILN", managed_circuits=("CKT-KILN",),
                         max_simultaneous_va=10000, strategy="ems",
                         source="synthetic test EMS")
    managed = _run(Library(circuits=(big,), load_managements=(ems,)))
    assert managed and all(f.result.value == "pass" for f in managed), [
        f.message for f in managed]


def test_load_management_flags_unknown_circuits():
    from typehaus.model import LoadManagement

    lm = LoadManagement(tag="LM-X", managed_circuits=("CKT-NOPE",),
                        max_simultaneous_va=1000, strategy="interlock")
    circuit = Circuit(tag="CKT-01", panel_ref="ED-M-PANEL", breaker_amps=20)
    plan = _plan(circuits=(circuit,), devices=(_PANEL,)).model_copy(
        update={"library": Library(circuits=(circuit,), load_managements=(lm,))})
    findings = _findings(plan, "electrical.service_load")
    assert any(f.result.value == "fail" and "CKT-NOPE" in f.message for f in findings)


def test_circuit_is_schedule_data_not_geometry():
    """A Circuit never enters storey element lists; it lives in Library.circuits."""
    circuit = Circuit(tag="CKT-01", panel_ref="ED-B-PANEL", breaker_amps=20,
                      backup_tier=BackupTier.ALWAYS_ON)
    assert circuit.poles == 1 and not circuit.gfci
    # Never inferred, never defaulted: no tier, no source, no duty cycle unless authored.
    assert circuit.backup_tier is BackupTier.ALWAYS_ON
    assert circuit.source is False and circuit.duty_cycle is None
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
                            "data",
                            "backup_components", "backup_runtime", "lighting"}
    assert set(payload["lighting"]) == {"schedule", "controls", "runs", "connected_va"}
    assert payload["panel_schedule"] == panel_schedule(catlin_model)
    assert payload["service_load"] == service_load_summary(catlin_model)
    assert payload["conduit"] == conduit_takeoff(catlin_model)
    assert payload["devices"] == electrical_device_takeoff(catlin_model)
    assert payload["solar"] == solar_takeoff(catlin_model)
    # 36: the 36 that survived the 2026-08-02 microgrid refactor plus CKT-DISPOSAL
    # (2026-08-07), minus CKT-WH-HP folded into CKT-WH-240 (2026-08-15).
    assert len(payload["panel_schedule"]) == 36


def test_model_json_canvas_objects_carry_their_circuit(catlin_model):
    """The device end of the circuit edge — what the inspector reads off a selection."""
    from typehaus.server.model_json import model_to_dict

    objects = {item["tag"]: item for item in model_to_dict(catlin_model)["canvas_objects"]}
    assert objects["ED-G-EV-1450"]["circuit"] == "CKT-EV-1450"
    # Equipment consumes power too; a placeable that doesn't reports None rather than
    # omitting the key, so the UI can tell "no circuit" from "old model.json".
    assert objects["EQ-B-WH"]["circuit"] == "CKT-WH-240"
    assert all("circuit" in item for item in objects.values() if item["domain"] != "opening")
    # Every tag the schedule names has to be addressable — this is the edge the reader's
    # device tags zoom through, and a row naming something the UI cannot reach is a dead end.
    #
    # Most consumers are canvas objects, which carry their own position. Alarms are the
    # exception and deliberately so: they are life-safety symbols keyed to a room, not
    # movable placeables (an Alarm has no position at all — it draws at the room seed), so
    # they are never canvas objects. They are still consumers — R314.4 puts them on a branch
    # circuit and the schedule has to say which — so they zoom through their room instead.
    payload = model_to_dict(catlin_model)
    alarms = {item["tag"]: item for item in payload["alarms"]}
    rooms = {item["tag"] for item in payload["rooms"]}
    for row in payload["electrical"]["panel_schedule"]:
        for tag in row["devices"]:
            if tag in alarms:
                assert alarms[tag]["room"] in rooms, tag
                continue
            assert tag in objects, tag


def test_service_load_is_null_without_circuits():
    """A house that authors no circuits gets no estimate — the summary would be over nothing."""
    from typehaus.server.model_json import model_to_dict

    model, _findings = resolve(_plan())
    payload = model_to_dict(model)["electrical"]
    assert payload["service_load"] is None
    assert payload["panel_schedule"] == [] and payload["conduit"] == []


def _room_result(model, room_tag: str) -> str:
    report = run_from_model(model, [], tier=Tier.ADVISORY)
    finding = next(f for f in report.findings
                   if f.check_id == "electrical.receptacle_spacing"
                   and f.element_tags == (room_tag,))
    return finding.result.value


def test_wall_space_is_not_traced_across_a_stair_well():
    """210.52(A)(2) measures "along the floor line", and a stair well is where the floor line
    stops. The only way to satisfy the 6' rule on the strip of wall a well runs up against is
    to hang a box over the drop, so the well breaks the measurement the way a doorway does —
    and, once it does, a receptacle already sitting on that strip stops counting.

    FO-A-STAIR takes the north 3'-0" of RM-A-STUDY, leaving 6 5/8" of deck against the east
    wall. ED-A-STUDY-RC2 was authored on exactly that strip; moved south of the well it both
    becomes reachable and is what closes the run from RC3 round the southeast corner, so
    putting it back is the room's only failure.
    """
    plan = load_plan(CATLIN_DIR).plan
    model, _ = resolve(plan)
    assert _room_result(model, "RM-A-STUDY") == "pass"

    ledge = pt(m(35.83 * 0.3048), m(8.28 * 0.3048))  # where RC2 used to sit
    stranded = tuple(
        element.model_copy(update={"position": ledge})
        if getattr(element, "tag", None) == "ED-A-STUDY-RC2" else element
        for element in plan.storey_elements("attic"))
    plan = plan.model_copy(update={"elements": {**plan.elements, "attic": stranded}})
    model, _ = resolve(plan)

    assert _room_result(model, "RM-A-STUDY") == "fail"


def test_a_combination_receptacle_counts_by_its_125v_half():
    """ED-M-LIVING-KET1 is a ``RECEPTACLE_240`` kind, but its type is a 5-20R/6-20R duplex:
    one box holding a 240V outlet for the kettle and an ordinary 125V outlet beside it. The
    125V half is a 210.52 receptacle like any other, so the kind alone cannot decide this —
    the type's ports do (the DeviceKind precedent: the kind stays flat, the type
    differentiates). Drop the 120V port and the north kitchen counter loses its coverage.
    """
    plan = load_plan(CATLIN_DIR).plan
    model, _ = resolve(plan)
    assert _room_result(model, "RM-M-LIVING") == "pass"

    # ED-M-LIVING-KDS1 and ED-M-LIVING-KDW1 come out with it — the disposer outlet and the
    # dishwasher cord, both inside the sink base at 18" up. Neither is anybody's idea of
    # kitchen-counter coverage, but this check grades 210.52(A)'s *wall* rule, where a 125V
    # receptacle below the 5'-6" cut-off counts wherever it stands, and both happen to sit
    # in the stretch this test empties. Leaving either would hold the north wall covered
    # for a reason that has nothing to do with the kettle outlet under test.
    #
    # KDW1 joined the list on 2026-08-27: it did not move house, the SINK did. The base run
    # was re-composed on 2026-08-26 to centre the bowl under WIN-M-KITCH, the dishwasher
    # went to the sink base's west side with it, and its cord outlet landed 3'-0" from the
    # wall space's start — inside the 6' this test needs empty. Nothing about the check or
    # the kettle changed; a piece of casework moved 15" and quietly took over the coverage
    # the assertion was reading.
    #
    # Removing the devices, not demoting their types: a plain RECEPTACLE kind counts on the
    # kind alone, and only the combination kind consults ports — which is the asymmetry this
    # test exists to pin.
    without_appliance_outlets = tuple(
        element for element in plan.storey_elements("main")
        if getattr(element, "tag", None) not in ("ED-M-LIVING-KDS1", "ED-M-LIVING-KDW1"))
    plan = plan.model_copy(update={
        "elements": {**plan.elements, "main": without_appliance_outlets}})

    library = plan.library
    demoted = tuple(
        device_type.model_copy(update={
            "ports": tuple(p for p in device_type.ports if p.service is not Service.POWER_120)})
        if device_type.tag == "ED-T-RECEPTACLE-620" else device_type
        for device_type in library.electrical_device_types)
    plan = plan.model_copy(update={"library": library.model_copy(
        update={"electrical_device_types": demoted})})
    model, _ = resolve(plan)

    assert _room_result(model, "RM-M-LIVING") == "fail"


def test_wall_space_stops_at_a_run_of_counterless_fixed_cabinet():
    """210.52(A)(2)(1) lists "fixed cabinets that do not have countertops or similar work
    surfaces" alongside doorways as things wall space is unbroken by.

    ** RE-ANCHORED 2026-08-24, AND THE REASON MATTERS MORE THAN THE EDIT. ** This used to
    name 7'-1" of catlin's north wall — FURN-M-KIT-PANTRY-E plus the tall pull-outs at the
    head of the west run — and prove the rule by giving every counterless type a countertop
    and watching RM-M-LIVING flip pass -> fail. All three of those cabinets are gone: the
    pantry became a framed room (RM-M-PANTRY) and the pull-outs stood where its south
    partition now runs. The room's counterless fixed cabinets are the east tall bank
    (FURN-M-KIT-PANTRY-S1/S2) and the mixer garage, and RM-M-LIVING now has enough
    receptacles that it passes WITH OR WITHOUT their break — so the old mutation asserts
    'fail' on a house that no longer fails, and no other room in the house depends on the
    break either (RM-S-BATH1's closet is in a bathroom, which is not habitable and is not
    graded).

    So the mutation is pointed at the RULE instead of at one room's incidental dependence
    on it: the break intervals themselves have to appear for a counterless cabinet and have
    to vanish when the same cabinet is given a work surface. That is the behaviour
    210.52(A)(2)(1) describes, and unlike a room verdict it cannot be made vacuous by adding
    a receptacle somewhere else.
    """
    from typehaus.checks.code.mn_residential.profile import MN_2024
    from typehaus.checks.mep.electrical import _fixed_cabinet_intervals
    from typehaus.checks.registry import CheckContext, Preferences

    plan = load_plan(CATLIN_DIR).plan
    model, _ = resolve(plan)
    assert _room_result(model, "RM-M-LIVING") == "pass"

    living = next(room for room in model.rooms if room.tag == "RM-M-LIVING")
    ring = [tuple(point) for point in living.clear_face]
    ctx = CheckContext(plan=plan, model=model, preferences=Preferences(), profile=MN_2024)
    breaks = _fixed_cabinet_intervals(ctx, ring, "main")
    # The east tall bank is 4'-0" of floor-to-ceiling carcass on the living room's boundary,
    # so it has to produce a break, and one long enough to be that bank.
    assert breaks, "counterless fixed cabinets should break the wall line"
    assert max(hi - lo for lo, hi in breaks) >= 3.5 * 0.3048

    library = plan.library
    countertopped = tuple(
        furniture_type.model_copy(update={"work_surface": True})
        if furniture_type.work_surface is False else furniture_type
        for furniture_type in library.furniture_types)
    plan = plan.model_copy(update={"library": library.model_copy(
        update={"furniture_types": countertopped})})
    model, _ = resolve(plan)
    living = next(room for room in model.rooms if room.tag == "RM-M-LIVING")
    ring = [tuple(point) for point in living.clear_face]
    ctx = CheckContext(plan=plan, model=model, preferences=Preferences(), profile=MN_2024)

    # Give every one of them a countertop and the wall line is unbroken by cabinets: the
    # same carcasses are now work surfaces, which 210.52(A)(2)(1) does not exempt.
    assert _fixed_cabinet_intervals(ctx, ring, "main") == []
