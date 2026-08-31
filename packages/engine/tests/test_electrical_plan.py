"""Electrical plan builder — E-101+ (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.electricalplan import build_electrical_plan, has_electrical_content
from typehaus.emit.draw.scene import Symbol
from typehaus.resolve import resolve
from typehaus.source import load_plan


@pytest.fixture(scope="module")
def starter_model(starter_dir: Path):
    result = load_plan(starter_dir)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def test_starter_models_a_minimal_electrical_package_on_both_storeys(starter_model):
    """The template carries the smallest package a house can be wired from.

    It used to carry exactly one device — the MN 1303.2402 subp. 6 junction box beside the
    radon riser, required of every new MN dwelling — and that single mandatory box was
    enough to flip ``electrical.room_lighting`` and ``electrical.receptacle_spacing`` from
    *not modeled* to *modeled and incomplete*, so the template shipped four advisory FAILs
    that said nothing about the design. ``plan/electrical.py`` answers them: a panel, a
    light + switch in each of the two habitable rooms, and NEC 210.52 receptacles on their
    wall lines.
    """
    with_content = [s.tag for s in starter_model.plan.storeys
                    if has_electrical_content(starter_model, s.tag)]
    assert with_content == ["main", "upper"]

    def devices(storey: str) -> list[str]:
        return [e.tag for e in starter_model.plan.storey_elements(storey)
                if e.element_kind == "ElectricalDevice"]

    main = devices("main")
    assert "ED-RADON-FAN-JB" in main, "the subpart 6 box is not optional"
    assert "ED-PANEL" in main
    assert [t for t in main if t.startswith("ED-Main-RC")] == [
        f"ED-Main-RC{n}" for n in range(1, 9)]
    assert {"ED-Main-LT1", "ED-Main-SW1"} <= set(main)

    upper = devices("upper")
    assert [t for t in upper if t.startswith("ED-Upper-RC")] == [
        f"ED-Upper-RC{n}" for n in range(1, 10)]
    assert {"ED-Upper-LT1", "ED-Upper-SW1"} <= set(upper)

    # Every device joins the panel schedule, and every circuit it names exists.
    circuits = {c.tag for c in starter_model.plan.library.circuits}
    assert circuits == {"CKT-LIGHTS", "CKT-RECEPT", "CKT-ALARMS", "CKT-RADON"}
    named = {e.circuit for storey in ("main", "upper")
             for e in starter_model.plan.storey_elements(storey)
             if e.element_kind == "ElectricalDevice" and e.circuit}
    assert named <= circuits


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


def test_the_water_heater_is_modeled(catlin_model):
    """One tank, not two (2026-08-15): the house carries a single 80-gal hybrid HPWH,
    not a 120V-compressor tank beside a 240V-element tank — that split was a modelling
    artifact of one product's two internal power draws, corrected in plan/mep.py."""
    equipment_with_storey = [(storey.tag, element) for storey in catlin_model.plan.storeys
                             for element in catlin_model.plan.storey_elements(storey.tag)
                             if element.element_kind == "Equipment"]
    equipment = {element.tag: element for _, element in equipment_with_storey}
    equipment_storeys = {element.tag: storey for storey, element in equipment_with_storey}
    assert equipment["EQ-B-WH"].type_ref == "EQ-T-WATER-HEATER"  # Rheem ProTerra 80gal
    assert "EQ-B-WH2" not in equipment
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
    # EQ-T-GREE-VIREO-GEN3 -> EQ-T-GREE-FLEXX-ULTRA-24-OD on 2026-08-31 with the System 1
    # retype. A new outdoor type that forgets `plan_symbol` draws as an anonymous massing box
    # in 3D and nothing else complains, which is what this list is here to prevent.
    for type_tag in ("EQ-T-GREE-FLEXX-ULTRA-24-OD", "EQ-T-GREE-MULTI-U30",
                     "EQ-T-GREE-SAPPHIRE-9-OD"):
        product = types[type_tag]
        assert product.plan_symbol == "heat-pump-outdoor"
        width, depth = (dimension.meters for dimension in product.footprint)
        assert len(model_parts(product.plan_symbol, width, depth, product.height.meters)) >= 3


def test_plant_tubes_use_the_cable_suspension_symbol(catlin_model):
    """Only the plant-room grow tubes need a visible ceiling suspension in 3D."""
    from typehaus.model.placeable_symbols import model_parts

    types = {product.tag: product for product in catlin_model.plan.library.electrical_device_types}
    tube = types["ED-T-LT-TUBE6"]
    assert tube.plan_symbol == "suspended-linear-light"
    width, depth = (dimension.meters for dimension in tube.footprint)
    parts = model_parts(tube.plan_symbol, width, depth, tube.height.meters)
    assert [part["color"] for part in parts].count("luminaire-housing") == 3


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


def test_dark_sky_lighting_passes_on_the_catlin_house(catlin_model):
    """``advisory.dark_sky_lighting`` (→ checks/mep/lighting): the three exterior
    luminaires — the garage-door sconce, the porch flood, and the ceiling-hung porch fan
    (exempt from the cutoff grading; the deck above it is the shield) — are full cutoff
    where gradeable and all at or under the 3000K ceiling."""
    from typehaus.checks import run_from_model
    from typehaus.checks.registry import Tier

    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    findings = [f for f in report.findings if f.check_id == "advisory.dark_sky_lighting"]
    assert findings
    assert all(f.result.value == "pass" for f in findings), \
        [f.message for f in findings if f.result.value != "pass"]


def test_an_unshielded_cool_exterior_luminaire_is_reported(catlin_model):
    """Retype the garage-door light to the 4000K, unshielded shop light: both dark-sky
    gradings fail on that one fixture — no cutoff, and over the CCT ceiling."""
    from typehaus.checks.code.mn_residential.profile import MN_2024
    from typehaus.checks.mep.lighting import dark_sky_lighting
    from typehaus.checks.registry import CheckContext, Preferences

    device = catlin_model.plan.by_tag("ED-G-EXT-LT")
    broken = device.model_copy(update={"type_ref": "ED-T-LT-SHOP4"})
    patched = catlin_model.plan.with_elements(
        "garage", [broken if element.tag == device.tag else element
                   for element in catlin_model.plan.storey_elements("garage")])
    context = CheckContext(plan=patched, model=catlin_model, preferences=Preferences(),
                           profile=MN_2024)
    failures = [f for f in dark_sky_lighting(context) if f.result.value == "fail"]
    assert [f.element_tags for f in failures] == [("ED-G-EXT-LT",), ("ED-G-EXT-LT",)]
    assert any("full-cutoff" in f.message for f in failures)
    assert any("4000" in f.message for f in failures)


def test_a_wall_attached_peninsula_is_not_graded_as_an_island(catlin_model):
    """``electrical.island_receptacle`` returns NOT_APPLICABLE on catlin, and that is correct.

    This test asserted a PASS on FURN-M-KIT-ISLAND until 2026-08-24, when the island became
    FURN-M-KIT-PENINSULA and landed its east end on the east wall. The check's own
    population rule is "freestanding by more than ``_NEAR_WALL_M`` from every room
    boundary" — a peninsula reads as near-wall and is deliberately not graded, because a
    carcass against a wall is ``receptacle_spacing``'s beat, not this one. With no
    freestanding work-surface carcass left in the house the check has nothing to grade and
    says so. Since 2026-08-30 it says so as N/A rather than UNKNOWN, and it earns that by
    counting: eight work-surface units were read and every one of them stands against a
    boundary, so "this house has no island" is a fact about the building. Had *no*
    work-surface casework been modeled at all the answer would still be UNKNOWN, because
    then the question would be unanswerable rather than answered.

    ** THIS IS AN HONEST REGRESSION IN COVERAGE, NOT A FIX. ** The peninsula still has
    countertop-serving receptacles — ED-M-LIVING-KGF4 and KMX1, both inside
    FURN-M-KIT-MIXER-GARAGE at 42", which is "above the counter surface" under
    210.52(C)(3) — but nothing in the engine grades 210.52(C) at all, which it reports
    UNKNOWN by design. What used to be checked here is now only reviewed.
    """
    from typehaus.checks import run_from_model
    from typehaus.checks.registry import Tier

    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    findings = [f for f in report.findings if f.check_id == "electrical.island_receptacle"]
    assert [f.result.value for f in findings] == ["not_applicable"]
    assert "no freestanding island" in findings[0].message
    tags = {item.tag for item in catlin_model.canvas_objects}
    assert "FURN-M-KIT-PENINSULA" in tags and "FURN-M-KIT-ISLAND" not in tags


def test_an_island_with_no_receptacle_is_reported(catlin_model):
    """Pull the peninsula off the wall and strip its receptacles: it fails, citing 210.52(C).

    Re-anchored 2026-08-24. It used to delete ED-M-LIVING-KGF4 and lean on the island's own
    freestanding position; there is no freestanding carcass in the house any more, so the
    fixture has to make one. Moving the peninsula's resolved footprint is what does it —
    the check populates off ``model.canvas_objects``, not off the plan — and stripping every
    receptacle on the storey is what makes the *finding* rather than a pass.
    """
    from dataclasses import replace

    from typehaus.checks.code.mn_residential.profile import MN_2024
    from typehaus.checks.mep.electrical import island_receptacle
    from typehaus.checks.registry import CheckContext, Preferences

    # Re-centred on (26'-0", 27'-0"), which is the ONE place a 10'-0" carcass stands clear
    # of every RM-M-LIVING boundary by more than `_NEAR_WALL_M` (4.07', the widest margin
    # the room offers a box this long). As built it is centred at (30'-5 3/8", 26'-9 7/8")
    # with its east end ON the wall — hence the sibling test above.
    peninsula = next(item for item in catlin_model.canvas_objects
                     if item.tag == "FURN-M-KIT-PENINSULA")
    xs = [x for x, _ in peninsula.footprint]
    ys = [y for _, y in peninsula.footprint]
    shift_x = 26 * 0.3048 - (min(xs) + max(xs)) / 2
    shift_y = 27 * 0.3048 - (min(ys) + max(ys)) / 2
    moved = [
        replace(item, footprint=[(x + shift_x, y + shift_y) for x, y in item.footprint])
        if item.tag == "FURN-M-KIT-PENINSULA" else item
        for item in catlin_model.canvas_objects
    ]
    model = replace(catlin_model, canvas_objects=moved)
    patched = model.plan.with_elements(
        "main", [element for element in model.plan.storey_elements("main")
                 if element.element_kind != "ElectricalDevice"])
    context = CheckContext(plan=patched, model=model, preferences=Preferences(),
                           profile=MN_2024)
    failures = [f for f in island_receptacle(context) if f.result.value == "fail"]
    assert [f.element_tags for f in failures] == [("FURN-M-KIT-PENINSULA",)]
    assert "210.52(C)" in failures[0].message
