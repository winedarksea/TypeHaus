"""Electrical plan builder — E-101+ (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.electricalplan import build_electrical_plan, has_electrical_content
from typehaus.emit.draw.scene import Symbol
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


@pytest.fixture(scope="module")
def starter_model(starter_dir: Path):
    result = load_plan(starter_dir)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def test_starter_has_no_electrical_content(starter_model):
    assert not any(has_electrical_content(starter_model, s.tag) for s in starter_model.plan.storeys)


def test_main_plan_symbol_census(catlin_model):
    scene = build_electrical_plan(catlin_model, "main")
    symbols = [n for n in scene.nodes if isinstance(n, Symbol)]
    kinds = {n.name for n in symbols}
    assert {"light", "switch"} <= kinds


def test_basement_plan_has_panel(catlin_model):
    scene = build_electrical_plan(catlin_model, "basement")
    symbols = [n for n in scene.nodes if isinstance(n, Symbol) and n.name == "panel"]
    assert symbols


def test_legend_reflects_present_device_kinds(catlin_model):
    from typehaus.emit.draw.scene import Text

    scene = build_electrical_plan(catlin_model, "second")
    texts = {n.content for n in scene.nodes if isinstance(n, Text)}
    assert "LEGEND" in texts
    assert "LIGHT" in texts and "SWITCH" in texts


def test_every_habitable_room_has_a_light_and_a_switch(catlin_model):
    """``electrical.room_lighting`` matches devices to rooms by tag suffix, so a room that
    gains a light also needs its tag to line up — the two ways this regresses (no device at
    all, device tagged for the wrong room) both surface as the same FAIL."""
    from typehaus.checks import run_from_model
    from typehaus.checks.registry import Tier

    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    findings = [f for f in report.findings if f.check_id == "electrical.room_lighting"]
    assert findings
    assert all(f.result.value == "pass" for f in findings), \
        [f.message for f in findings if f.result.value != "pass"]


def test_the_previously_dark_habitable_rooms_are_covered(catlin_model):
    """The three rooms that had no lighting at all: the basement gym and both habitable
    attic rooms. Named explicitly so deleting a device from one of them fails here instead
    of quietly shrinking the census in the test above."""
    tags = {element.tag for storey in catlin_model.plan.storeys
            for element in catlin_model.plan.storey_elements(storey.tag)
            if element.element_kind == "ElectricalDevice"}
    for room_suffix in ("B-GYM", "A-EAST", "A-STUDY"):
        assert f"ED-{room_suffix}-LT" in tags
        assert f"ED-{room_suffix}-SW" in tags


def test_service_upgrade_devices_are_present(catlin_model):
    """The electrical_notes.md program (WS2): meter, backup enclosure, EV receptacles,
    hot tub disconnect in the sunken garden, minisplit disconnects, PV junction box."""
    devices = {element.tag: element for storey in catlin_model.plan.storeys
               for element in catlin_model.plan.storey_elements(storey.tag)
               if element.element_kind == "ElectricalDevice"}
    assert devices["ED-M-METER"].kind.value == "meter"
    assert devices["ED-B-BACKUP-ENCL"].kind.value == "panel"
    assert devices["ED-G-EV-620"].type_ref == "ED-T-EV-620"
    assert devices["ED-G-EV-1450"].type_ref == "ED-T-EV-1450"
    assert devices["ED-B-SPA-DISC"].kind.value == "disconnect"
    # One 440.14 disconnect per outdoor unit — three systems now, not two minisplits.
    assert devices["ED-M-HP1-DISC"].kind.value == "disconnect"
    assert devices["ED-M-HP2-DISC"].kind.value == "disconnect"
    assert devices["ED-M-HP3-DISC"].kind.value == "disconnect"
    assert devices["ED-A-PV-JB"].kind.value == "junction_box"
    # Typed NEMA data replaces name parsing (WS1 schema).
    types = {t.tag: t for t in catlin_model.plan.library.electrical_device_types}
    assert types["ED-T-EV-1450"].nema == "14-50R"
    assert types["ED-T-EV-1450"].load_va == 9600


def test_garage_now_has_an_electrical_sheet(catlin_model):
    assert has_electrical_content(catlin_model, "garage")
    scene = build_electrical_plan(catlin_model, "garage")
    symbols = {n.name for n in scene.nodes if isinstance(n, Symbol)}
    assert "receptacle_240" in symbols


def test_meter_and_disconnect_render_with_dedicated_symbols(catlin_model):
    scene = build_electrical_plan(catlin_model, "main")
    symbols = {n.name for n in scene.nodes if isinstance(n, Symbol)}
    assert {"meter", "disconnect"} <= symbols


def test_both_water_heaters_are_modeled(catlin_model):
    equipment_with_storey = [(storey.tag, element) for storey in catlin_model.plan.storeys
                             for element in catlin_model.plan.storey_elements(storey.tag)
                             if element.element_kind == "Equipment"]
    equipment = {element.tag: element for _, element in equipment_with_storey}
    equipment_storeys = {element.tag: storey for storey, element in equipment_with_storey}
    assert equipment["EQ-B-WH"].type_ref == "EQ-T-WATER-HEATER"  # 120V Rheem HPWH
    assert equipment["EQ-B-WH2"].type_ref == "EQ-T-WATER-HEATER-240"
    # The three Gree outdoor units, and the indoor halves that name them.
    for tag in ("EQ-M-HP1-OD", "EQ-M-HP2-OD", "EQ-M-HP3-OD"):
        assert equipment[tag].kind.value == "heat_pump"
    # Systems 1 and 2 are intentionally paired on the upper balcony (second-storey datum),
    # rather than leaving the ducted system's outdoor half invisible at ground level.
    assert equipment_storeys["EQ-M-HP1-OD"] == "second"
    assert equipment_storeys["EQ-M-HP2-OD"] == "second"
    assert equipment["EQ-S-HP1-AH"].kind.value == "ducted_air_handler"
    assert equipment["EQ-S-HP1-AH"].outdoor_ref == "EQ-M-HP1-OD"
    for tag in ("EQ-B-HP2-GYM", "EQ-M-HP2-BED", "EQ-M-HP2-LIVING"):
        assert equipment[tag].kind.value == "indoor_head"
        assert equipment[tag].outdoor_ref == "EQ-M-HP2-OD"
    assert equipment["EQ-M-HP3-STAIR"].outdoor_ref == "EQ-M-HP3-OD"


def test_outdoor_heat_pumps_have_distinct_3d_symbol_geometry(catlin_model):
    """The outdoor halves are visible condensers, not anonymous massing boxes."""
    from typehaus.model.placeable_symbols import model_parts

    types = {product.tag: product for product in catlin_model.plan.library.equipment_types}
    for type_tag in ("EQ-T-GREE-VIREO-GEN3", "EQ-T-GREE-MULTI-U30",
                     "EQ-T-GREE-SAPPHIRE-9-OD"):
        product = types[type_tag]
        assert product.plan_symbol == "heat-pump-outdoor"
        width, depth = (dimension.meters for dimension in product.footprint)
        assert len(model_parts(product.plan_symbol, width, depth, product.height.meters)) >= 3


def test_electrical_plan_dxf_round_trips(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_electrical_plan(catlin_model, "main")
    path = write_dxf(scene, tmp_path / "electrical.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"E-POWR-DEVC", "E-LITE"} <= names


def test_the_three_lighting_checks_pass_on_the_catlin_house(catlin_model):
    """``lighting_controls`` / ``wet_location`` / ``light_run_psu`` (→ checks/mep/lighting).

    All three are advisory and all three pass, so any regression here is a real one: a
    fixture nobody can switch, one not listed for a bathroom, or a 24V run whose driver
    cannot carry it.
    """
    from typehaus.checks import run_from_model
    from typehaus.checks.registry import Tier

    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    for check_id in ("electrical.lighting_controls", "electrical.wet_location",
                     "electrical.light_run_psu"):
        findings = [f for f in report.findings if f.check_id == check_id]
        assert findings, check_id
        assert all(f.result.value == "pass" for f in findings), \
            [f.message for f in findings if f.result.value != "pass"]


def test_a_fixture_with_no_switch_is_reported(catlin_model):
    """The check has to actually fire — one that only ever passes proves nothing."""
    from typehaus.checks.mep.lighting import lighting_controls
    from typehaus.checks.code.mn_residential.profile import MN_2024
    from typehaus.checks.registry import CheckContext, Preferences

    def context(plan):
        return CheckContext(plan=plan, model=catlin_model, preferences=Preferences(),
                            profile=MN_2024)

    # Point one fixture at a switch that does not exist: it fails, naming that fixture.
    device = catlin_model.plan.by_tag("ED-M-BED-CAN2")
    broken = device.model_copy(update={"controlled_by": ("ED-NOT-A-SWITCH",)})
    patched = catlin_model.plan.with_elements(
        "main", [broken if element.tag == device.tag else element
                 for element in catlin_model.plan.storey_elements("main")])
    failures = [f for f in lighting_controls(context(patched)) if f.result.value == "fail"]
    assert [f.element_tags for f in failures] == [("ED-M-BED-CAN2",)]
