"""WP3.7 — migration equivalence: the new-engine catlin model preserves the old
catlin-house semantics (element counts / dimensions / placements by category),
generalizing the old repo's ``tests/test_catlin_house_ifc.py``.

The old builder's constants are inlined here as the contract (the old repo is being
archived): 36' house at sheathing, 16" o.c., 18' grid, 4:12 hot roof with knee 5' /
ridge 11' over the attic floor, 12" basement walls + 2x2" XPS, 24' ICF garage 12'
north, and the freestanding arched sunken-garden structure.
"""

from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.quantities import ft, inch
from typehaus.resolve import resolve
from typehaus.resolve.framing.profiles import RIDGE_BEAM_DEFAULT, cross_section
from typehaus.source import load_plan
from typehaus.checks import run
from typehaus.findings import Result

# Old CatlinHouseSpec contract values.
HOUSE_SIZE_FT = 36.0
FRAMING_SPACING_IN = 16.0
GRID_FT = 18.0
KNEE_FT = 5.0
RIDGE_OVER_ATTIC_FT = 11.0
ATTIC_ELEV_FT = 20.0
GARAGE_SIZE_FT = 24.0
GARAGE_GAP_FT = 12.0
GARAGE_OVERHANG_IN = 16.0

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    assert result.plan is not None, [f.message for f in result.findings]
    errors = [f for f in result.findings if f.severity.value == "error"]
    assert not errors, [f.message for f in errors]
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, [f.message for f in errors]
    return model


def test_floor_joist_counts_match_old_model(catlin_model):
    """Old: positions = size/spacing + 1 (both ends), two 18' spans per floor."""
    expected_positions = int(round(HOUSE_SIZE_FT * 12.0 / FRAMING_SPACING_IN)) + 1
    expected_pair_count = expected_positions * 2
    for tag in ("FS-SECOND", "FS-ATTIC"):
        floor = next(f for f in catlin_model.floors if f.tag == tag)
        joists = [m for m in floor.members if m.category == "joist"]
        assert len(joists) == expected_pair_count, tag
        # Most joists retain the 18' bearing span; lines crossing a stair opening are
        # clipped at its framed edge rather than running through the stairwell.
        spans = {round(m.length_m / ft(1).meters, 3) for m in joists}
        assert GRID_FT in spans
        if tag == "FS-SECOND":
            assert 11.0 in spans


def test_catlin_i_joists_and_frost_supports_pass_the_declared_structural_tables():
    report = run(load_plan(CATLIN_DIR).plan, CATLIN_DIR, tier=None)
    findings = [finding for finding in report.findings
                if finding.check_id in {"structural.ijoist_span", "structural.frost_depth"}]
    assert findings
    assert all(finding.result is Result.PASS for finding in findings)


def test_catlin_permit_checklist_passes_declared_minnesota_subset():
    from typehaus.checks import evaluate_permit_checklist

    report = run(load_plan(CATLIN_DIR).plan, CATLIN_DIR, tier=None)
    checklist = evaluate_permit_checklist(report, "mn-2024")
    # code.energy_prescriptive (→ Permit-ready plan set Phase 7) honestly reports UNKNOWN
    # for SL-B-FLOOR/SL-M-DECK — neither concrete slab has an authored assembly with an
    # R-value yet. That is the intended behavior (never a silent pass on missing thermal
    # data, not a regression) — every other declared item still passes.
    energy_label = "Energy prescriptive envelope"
    non_energy_items = [item for item in checklist.items if item.label != energy_label]
    assert all(item.result is Result.PASS for item in non_energy_items)
    energy_item = next(item for item in checklist.items if item.label == energy_label)
    assert energy_item.result is Result.UNKNOWN


def test_site_plan_keeps_freestanding_roofs_and_foundation_supports_visible(catlin_model):
    from typehaus.emit.draw import build_site_plan

    scene = build_site_plan(catlin_model)
    tags = {node.tag for node in scene.nodes if getattr(node, "tag", None)}
    assert {"RF-HOUSE", "RF-GARAGE"} <= tags
    assert any(getattr(node, "layer", None) == "A-SITE-FOUND" for node in scene.nodes)


def test_catlin_legacy_floorplans_are_dim_view_only_underlays():
    from typehaus.checks import load_preferences

    underlays = load_preferences(CATLIN_DIR).underlays
    assert {item.storey for item in underlays} == {"basement", "main", "second", "attic"}
    assert all(item.path.startswith("../../catlin_floorplan/") for item in underlays)
    assert all(0.0 < item.opacity <= 0.25 for item in underlays)


def test_configured_reference_underlay_is_served_through_the_sandboxed_route():
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    from typehaus.server.app import create_app

    with fastapi_testclient.TestClient(create_app(CATLIN_DIR)) as client:
        url = client.get("/model").json()["underlays"][0]["url"]
        response = client.get(url)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")


def test_centerline_bearing_wall_runs_full_length_on_both_framed_storeys(catlin_model):
    center_x = ft(GRID_FT).meters
    for storey in ("main", "second"):
        segments = [
            w for w in catlin_model.walls
            if w.storey == storey and w.assembly == "CATLIN_INT_2X6_BRG"
            and abs(w.axis[0][0] - center_x) < 1e-6 and abs(w.axis[1][0] - center_x) < 1e-6
        ]
        assert segments, storey
        length = sum(
            abs(w.axis[1][1] - w.axis[0][1]) + abs(w.axis[1][0] - w.axis[0][0])
            for w in segments
        )
        assert length == pytest.approx(ft(HOUSE_SIZE_FT).meters, abs=1e-6)
        # The centerline is the old 5.5" (2x6) wall on every framed storey.
        for wall in segments:
            structure = next(l for l in wall.layers if l.function == "structure")
            assert structure.thickness_m == pytest.approx(inch(5.5).meters)


def _cladding_lap(model) -> float:
    """The attic bearing wall's depth — bounds how far its cladding can lap the roof.

    The axis is not centred in the stack (``Wall.alignment``), so the exact lap is an
    alignment detail; the wall depth is the honest upper bound.
    """
    wall = next(w for w in model.walls if w.tag == "W-A-S1")
    return wall.thickness_m


def test_roof_matches_old_pitch_knee_and_ridge(catlin_model):
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    eave_ft = roof.eave_z_m / ft(1).meters
    ridge_ft = roof.ridge_z_m / ft(1).meters
    assert eave_ft == pytest.approx(ATTIC_ELEV_FT + KNEE_FT)
    # The old builder set the roof out from the bearing-wall axes, giving an 11' ridge over
    # a 36' run. A zero-overhang roof that stops at the axis leaves the cladding standing
    # proud of its own edge, so the footprint now laps the outermost wall layer — the run,
    # and with it the ridge, grows by that lap on each side. The 4:12 pitch is unchanged.
    lap = _cladding_lap(catlin_model)
    assert ATTIC_ELEV_FT + RIDGE_OVER_ATTIC_FT < ridge_ft <= \
        ATTIC_ELEV_FT + RIDGE_OVER_ATTIC_FT + (lap / 3.0) / ft(1).meters + 1e-6
    assert roof.ridge_direction == "y"
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    for span in (max(xs) - min(xs), max(ys) - min(ys)):
        assert ft(HOUSE_SIZE_FT).meters < span <= ft(HOUSE_SIZE_FT).meters + 2 * lap + 1e-6
    rise_over_run = (roof.ridge_z_m - roof.eave_z_m) / ((max(xs) - min(xs)) / 2)
    assert rise_over_run == pytest.approx(4.0 / 12.0)
    rafters = [member for member in roof.members if member.category == "rafter"]
    # 29 lines at 16" o.c. over two gable planes — one line more than the old builder's
    # 28, because the footprint now laps the cladding at each rake.
    assert len(rafters) == 58
    # WP4: rafter ridge ends are trimmed back to bear on the ridge beam rather than
    # crossing to the exact ridge centerline — z1_end drops by half the beam width
    # times the roof slope, staying on the roof plane.
    beam_width_m = cross_section(RIDGE_BEAM_DEFAULT).width_m
    expected_z1_end = roof.ridge_z_m - (4.0 / 12.0) * (beam_width_m / 2.0)
    assert all(member.z1_end_m == pytest.approx(expected_z1_end) for member in rafters)
    assert all(member.connection == "ridge:adjustable-slope-hanger;eave:birdsmouth-1.17in"
              for member in rafters)


def test_ridge_beam_member_and_condition(catlin_model):
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    beams = [member for member in roof.members if member.category == "ridge_beam"]
    assert len(beams) == 1
    beam = beams[0]
    assert beam.profile == RIDGE_BEAM_DEFAULT
    assert beam.z1_m == pytest.approx(roof.ridge_z_m)
    section = cross_section(beam.profile)
    assert beam.z0_m == pytest.approx(roof.ridge_z_m - section.depth_m)
    assert any(c.kind.value == "roof_ridge" for c in catlin_model.conditions)


def test_garage_gable_roof_with_no_ridge_beam_warns_not_errors(catlin_model):
    garage_roof = next(r for r in catlin_model.roofs if r.tag == "RF-GARAGE")
    assert not [m for m in garage_roof.members if m.category == "ridge_beam"]
    _, resolve_findings = resolve(load_plan(CATLIN_DIR).plan)
    ridge_warnings = [f for f in resolve_findings if f.check_id == "structural.ridge_support"]
    assert any(f.element_tags == ("RF-GARAGE",) and f.severity.value == "warn"
              for f in ridge_warnings)
    assert not [f for f in ridge_warnings if f.severity.value == "error"]


def test_attic_to_roof_walls_frame_with_raked_studs_and_plates(catlin_model):
    """The gable ends are true raked walls, not 11' rectangular placeholders."""
    gable = next(w for w in catlin_model.walls if w.tag == "W-A-S1")
    # Knee height above the attic floor, plus the roof plane's cladding lap (see
    # test_roof_matches_old_pitch_knee_and_ridge).
    knee = ft(5).meters + ft(ATTIC_ELEV_FT).meters
    assert knee < gable.top_z0_m <= knee + _cladding_lap(catlin_model) / 3.0 + 1e-6
    assert gable.top_z1_m > gable.top_z0_m
    studs = [member for member in gable.members if member.category == "stud"]
    assert len(studs) >= 2
    assert max(member.z1_m for member in studs) > min(member.z1_m for member in studs)
    assert any(member.category == "raked_plate" for member in gable.members)


def test_floors_get_two_rim_boards_at_the_outer_bearing_lines(catlin_model):
    """WP3: rim (band) joists cap the deck ends, one per outermost bearing line."""
    for tag in ("FS-SECOND", "FS-ATTIC"):
        floor = next(f for f in catlin_model.floors if f.tag == tag)
        rims = [m for m in floor.members if m.category == "rim"]
        assert len(rims) == 2, tag
        assert all(m.profile.endswith(" rim") for m in rims)


def test_exterior_wall_spans_floor_to_floor_across_the_rim(catlin_model):
    """Revit convention: one wall from its base level to the next, no band proxy object.

    The wall's own layers carry the envelope across the joist band; its *framing* still
    stops at the double top plate, so the band is rim board and joists, not studs.
    """
    lower = catlin_model.wall("W-M-S1")
    upper = catlin_model.wall("W-S-S1")
    assert lower.z1_m == pytest.approx(upper.z0_m), "no void left at the storey line"
    assert lower.plate_top_z_m is not None
    assert lower.z1_m - lower.plate_top_z_m == pytest.approx(ft(1).meters)

    plate_tops = [m.z1_m for m in lower.members if m.category == "plate"]
    assert max(plate_tops) == pytest.approx(lower.plate_top_z_m, abs=1e-6), \
        "studs and plates must not run up into the joist band"
    studs = [m for m in lower.members if m.category == "stud"]
    assert studs and max(m.z1_m for m in studs) < lower.plate_top_z_m + 1e-6


def test_raked_gable_king_studs_match_roof_plane_at_own_station(catlin_model):
    """WP0: king-stud tops on a raked wall follow the roof line at their own plan
    position. A prior bug reused the last regular stud's leftover top for every
    king on the wall, regardless of the opening's actual station."""
    wall = next(w for w in catlin_model.walls if w.tag == "W-A-S3")  # two windows
    assert wall.top_z0_m is not None and wall.top_z1_m is not None
    (x0, y0), (x1, y1) = wall.axis
    axis_len = math.hypot(x1 - x0, y1 - y0)
    dx, dy = (x1 - x0) / axis_len, (y1 - y0) / axis_len
    plate_h = inch(1.5).meters
    top_plates = 2  # CATLIN_EXT_2X4 double top plate, not advanced framing

    kings = [m for m in wall.members if m.category == "king"]
    assert len(kings) >= 4  # two windows, at least one king per side each

    for king in kings:
        px, py = king.p0
        # Project onto the wall axis direction (king.p0 sits on the structure-layer
        # centerline, offset perpendicular from the datum axis — hypot would pick up
        # that perpendicular offset and skew the station).
        s = (px - x0) * dx + (py - y0) * dy
        fraction = s / axis_len
        expected = (wall.top_z0_m + (wall.top_z1_m - wall.top_z0_m) * fraction
                    - plate_h * top_plates)
        assert king.z1_m == pytest.approx(expected, abs=1e-6)

    # Kings on the two different windows sit at different stations, so their
    # tops must differ — exactly what the leftover-loop-variable bug broke.
    tops = {round(k.z1_m, 6) for k in kings}
    assert len(tops) > 1


def test_attic_follow_roof_rooms_pass_r305(catlin_model):
    report = run(catlin_model.plan, CATLIN_DIR, tier=None)
    findings = [finding for finding in report.findings
                if finding.check_id == "code.R305_ceiling_height"
                and "follows RF-HOUSE" in finding.message]
    assert findings
    assert all(finding.result is Result.PASS for finding in findings)


def test_center_section_cuts_the_raked_attic_walls(catlin_model):
    from typehaus.emit.draw.section import build_center_section

    scene = build_center_section(catlin_model)
    assert any(getattr(node, "tag", "").startswith("W-A-") for node in scene.nodes)


def test_exterior_elevations_include_resolved_openings_and_roof_profiles(catlin_model):
    from typehaus.emit.draw.elevation import build_elevation

    scene = build_elevation(catlin_model, "south")
    tags = {getattr(node, "tag", None) for node in scene.nodes}
    assert "RF-HOUSE" in tags
    assert "WIN-M-BED-S1" in tags


def test_roof_plan_uses_resolved_plane_footprints_and_ridges(catlin_model):
    from typehaus.emit.draw.roofplan import build_roof_plan

    scene = build_roof_plan(catlin_model)
    tags = {getattr(node, "tag", None) for node in scene.nodes}
    assert {"RF-HOUSE", "RF-HOUSE-ridge", "RF-GARAGE", "RF-GARAGE-ridge"} <= tags


def test_exterior_corners_include_strength_first_third_stud(catlin_model):
    """A third stud supplements the two intersecting endpoint studs at true corners."""
    for tag in ("W-M-S1", "W-M-E1", "W-M-N1", "W-M-W1"):
        wall = next(item for item in catlin_model.walls if item.tag == tag)
        assert any(member.category == "corner" for member in wall.members), tag


def test_bedroom_egress_is_associated_with_its_own_bounding_wall():
    report = run(load_plan(CATLIN_DIR).plan, CATLIN_DIR, tier=None)
    findings = [finding for finding in report.findings if finding.check_id == "code.R310_egress"]
    assert len(findings) == 5
    assert all(finding.result is Result.PASS for finding in findings)
    assert all("WIN-B-SAUNA" not in finding.message for finding in findings)


def test_catlin_window_openings_follow_the_sixteen_inch_framing_module():
    report = run(load_plan(CATLIN_DIR).plan, CATLIN_DIR, tier=None)
    findings = [finding for finding in report.findings
                if finding.check_id == "structural.window_framing_module"]
    assert not findings, [finding.message for finding in findings]


def test_every_catlin_boundary_condition_has_a_transition_binding():
    report = run(load_plan(CATLIN_DIR).plan, CATLIN_DIR, tier=None)
    findings = [finding for finding in report.findings
                if finding.check_id == "integrity.condition_coverage"]
    assert not findings, [finding.message for finding in findings]


def test_ci_thickness_bump_reflows_resolved_envelope_without_losing_transition_coverage():
    """M3's details must follow layer geometry rather than preserve a hand-drawn offset."""
    from typehaus.emit.draw import build_center_section

    plan = load_plan(CATLIN_DIR).plan
    baseline, baseline_findings = resolve(plan)
    assert not [finding for finding in baseline_findings if finding.severity.value == "error"]
    base_assembly = next(item for item in plan.library.assemblies if item.tag == "CATLIN_EXT_2X6")
    thicker_layers = tuple(
        layer.model_copy(update={"thickness": inch(3)}) if layer.name == "polyiso" else layer
        for layer in base_assembly.layers
    )
    thicker_assembly = base_assembly.model_copy(update={"layers": thicker_layers})
    updated_library = plan.library.model_copy(update={
        "assemblies": tuple(thicker_assembly if item.tag == thicker_assembly.tag else item
                            for item in plan.library.assemblies),
    })
    bumped_plan = plan.model_copy(update={"library": updated_library})
    bumped, bumped_findings = resolve(bumped_plan)
    assert not [finding for finding in bumped_findings if finding.severity.value == "error"]
    base_wall = next(item for item in baseline.walls if item.tag == "W-M-E1")
    bumped_wall = next(item for item in bumped.walls if item.tag == "W-M-E1")
    assert bumped_wall.layers[-1].polygon != base_wall.layers[-1].polygon
    assert build_center_section(bumped).nodes
    report = run(bumped_plan, CATLIN_DIR, tier=None)
    assert not [finding for finding in report.findings
                if finding.check_id == "integrity.condition_coverage"], [
                    finding.message for finding in report.findings
                    if finding.check_id == "integrity.condition_coverage"]


def test_catlin_has_required_smoke_co_alarm_coverage_and_json_symbols(tmp_path):
    from typehaus.server.model_json import model_to_dict

    plan = load_plan(CATLIN_DIR).plan
    report = run(plan, CATLIN_DIR, tier=None)
    assert not [finding for finding in report.findings
                if finding.check_id == "code.R314_R315_alarms" and finding.result is Result.FAIL]
    model, _ = resolve(plan)
    alarms = model_to_dict(model)["alarms"]
    assert {alarm["tag"] for alarm in alarms} >= {"AL-M-BED", "AL-M-HALL", "AL-S-HALL"}


def test_catlin_fixtures_render_as_footprints_and_serialize_services(catlin_model):
    from typehaus.emit.draw.floorplan import build_floorplan
    from typehaus.server.model_json import model_to_dict

    fixture_tags = {getattr(node, "tag", None) for node in build_floorplan(catlin_model, "main").nodes}
    assert "FX-M-BATH1-WC" in fixture_tags
    fixtures = model_to_dict(catlin_model)["fixtures"]
    washer = next(item for item in fixtures if item["tag"] == "FX-M-LAUNDRY")
    assert {"water_hot", "water_cold", "drain", "power_240"} <= set(washer["needs"])


def test_stairs_render_on_both_connected_storey_plans(catlin_model):
    from typehaus.emit.draw.floorplan import build_floorplan

    expected_uids = {
        "basement": {"CST701AAAA"},
        # ST-B2M and ST-M2S have the same footprint here; the departing main flight wins.
        "main": {"CST702AAAA"},
        "second": {"CST702AAAA", "CST703AAAA"},
        "attic": {"CST703AAAA"},
    }
    for storey, expected in expected_uids.items():
        seen = {getattr(node, "uid", None) for node in build_floorplan(catlin_model, storey).nodes
                if getattr(node, "uid", None) in expected}
        assert seen == expected


def test_catlin_drain_fixtures_use_six_inch_wet_walls():
    report = run(load_plan(CATLIN_DIR).plan, CATLIN_DIR, tier=None)
    findings = [finding for finding in report.findings if finding.check_id == "advisory.wet_wall_depth"]
    assert not findings, [finding.message for finding in findings]


def test_catlin_sauna_floor_heat_has_no_fixture_keepout_conflict():
    report = run(load_plan(CATLIN_DIR).plan, CATLIN_DIR, tier=None)
    findings = [finding for finding in report.findings
                if finding.check_id == "advisory.floor_heat_fixture_keepout"]
    assert not findings, [finding.message for finding in findings]


def test_house_local_furniture_import_creates_a_type_and_placed_instance(tmp_path, monkeypatch):
    """The M3 mesh importer never touches shared library source or a manifest."""
    from typehaus.cli.furniture_import import import_furniture_mesh
    from typehaus.source.imported_furniture import load_imported_furniture

    source = tmp_path / "warehouse-chair.glb"
    source.write_bytes(b"mesh")

    class FakeScene:
        class Vector(list):
            def __sub__(self, other):
                return FakeScene.Vector(a - b for a, b in zip(self, other))

        bounds = (Vector((0.0, 0.0, 0.0)), Vector((0.6, 0.7, 1.1)))

        def export(self, path, file_type):
            assert file_type == "glb"
            Path(path).write_bytes(b"converted-glb")

    monkeypatch.setitem(__import__("sys").modules, "trimesh",
                        SimpleNamespace(load=lambda *_args, **_kwargs: FakeScene()))
    import_furniture_mesh(source, tmp_path, tag="reading-chair", room="RM-M-LIVING",
                          position_m=(7.0, 4.0), storage=True)
    plan = load_plan(CATLIN_DIR).plan
    assert plan is not None
    findings = []
    augmented = load_imported_furniture(tmp_path, plan, findings)
    assert not findings
    furniture_type = next(item for item in augmented.library.furniture_types
                          if item.tag == "FURN-READING-CHAIR")
    assert furniture_type.mesh is not None
    instance = next(item for item in augmented.storey_elements("main")
                    if item.tag == "F-READING-CHAIR")
    assert instance.element_kind == "Furniture"
    model, resolve_findings = resolve(augmented)
    assert not [finding for finding in resolve_findings if finding.severity.value == "error"]
    from typehaus.emit.gltf import emit_glb
    from typehaus.server.model_json import model_to_dict

    glb = emit_glb(model, tmp_path / "furniture.glb")
    assert glb.exists() and glb.stat().st_size > 0
    assert any(item["tag"] == "F-READING-CHAIR" for item in model_to_dict(model)["furniture"])
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc import emit_ifc

    ifc = emit_ifc(model, tmp_path / "furniture.ifc", lod="core")
    assert any(item.Name == "F-READING-CHAIR"
               for item in ifcopenshell.open(ifc).by_type("IfcFurnishingElement"))


def test_catlin_model_json_has_derived_space_dashboard_metrics(catlin_model):
    from typehaus.server.model_json import model_to_dict

    summary = model_to_dict(catlin_model)["space_summary"]
    assert summary["overall"]["conditioned_sf"] > 0
    assert summary["overall"]["storage_ratio"] > 0
    assert {row["storey"] for row in summary["storeys"]} >= {"basement", "main", "second"}


def test_catlin_bearing_view_has_continuous_house_load_path(catlin_model):
    bearing_tags = {wall.tag for wall in catlin_model.walls
                    if getattr(catlin_model.plan.by_tag(wall.tag), "structural_role", None)
                    and catlin_model.plan.by_tag(wall.tag).structural_role.value == "bearing"}
    stacked = {edge.lower_wall for edge in catlin_model.stack_edges} | {
        edge.upper_wall for edge in catlin_model.stack_edges
    }
    assert {"W-M-C1", "W-S-C1"} <= bearing_tags
    assert {"W-M-C1", "W-S-C1"} <= stacked


def test_catlin_sauna_floor_heat_has_a_plan_zone_and_wire_takeoff(catlin_model):
    zone = next(item for item in catlin_model.floor_heat if item.tag == "FH-B-SAUNA")
    assert zone.system == "electric"
    assert zone.wire_length_m > 0
    assert len(zone.zone) >= 3


def test_basement_walls_carry_two_exterior_xps_layers(catlin_model):
    """Old: 4 perimeter segments x 2 XPS layers; new: every perimeter segment
    carries both 2" XPS layers in its resolved stack."""
    perimeter = [w for w in catlin_model.walls
                 if w.storey == "basement" and w.assembly == "CATLIN_BASEMENT_12"]
    assert len(perimeter) == 10  # same wall line, split at grid/tee nodes
    for wall in perimeter:
        xps = [l for l in wall.layers if l.name.startswith("xps")]
        assert len(xps) == 2
        for layer in xps:
            assert layer.thickness_m == pytest.approx(inch(2.0).meters)
        concrete = next(l for l in wall.layers if l.name == "concrete")
        assert concrete.thickness_m == pytest.approx(inch(12.0).meters)


def test_garage_is_freestanding_12ft_north_with_icf_stem(catlin_model):
    stem = [w for w in catlin_model.walls if w.tag.startswith("W-GF-")]
    assert len(stem) == 4
    ys = [p[1] for w in stem for p in w.axis]
    assert min(ys) == pytest.approx(ft(HOUSE_SIZE_FT + GARAGE_GAP_FT).meters)
    assert max(ys) == pytest.approx(ft(HOUSE_SIZE_FT + GARAGE_GAP_FT + GARAGE_SIZE_FT).meters)
    # Stem runs frost depth (-42") to +22" — absolute elevations, walkout-style.
    for wall in stem:
        assert wall.z0_m == pytest.approx(-inch(42.0).meters)
        assert wall.z1_m == pytest.approx(inch(22.0).meters)
    # Garage roof: ridge E-W (rotated 90° vs the house), 16" overhangs.
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-GARAGE")
    assert roof.ridge_direction == "x"
    xs = [p[0] for p in roof.footprint]
    assert max(xs) - min(xs) == pytest.approx(
        ft(GARAGE_SIZE_FT).meters + 2 * inch(GARAGE_OVERHANG_IN).meters)


def test_garage_wood_framing_uses_its_structure_layer_centerline(catlin_model):
    """Wood members must follow studs rather than the exterior ZIP-R datum axis."""
    stems = {wall.tag.removeprefix("W-GF-"): wall for wall in catlin_model.walls
             if wall.tag.startswith("W-GF-")}
    garage_walls = [wall for wall in catlin_model.walls if wall.tag.startswith("W-G-")]
    assert len(garage_walls) == 4

    for wall in garage_walls:
        stem = stems[wall.tag.removeprefix("W-G-")]
        assert wall.axis == stem.axis  # both systems share the intended garage footprint
        structure = next(layer for layer in wall.layers if layer.function == "structure")
        start, end = wall.axis
        dx, dy = end[0] - start[0], end[1] - start[1]
        span = (dx * dx + dy * dy) ** 0.5
        normal_x, normal_y = -dy / span, dx / span
        center_offset = sum(
            (point[0] - start[0]) * normal_x + (point[1] - start[1]) * normal_y
            for point in structure.polygon
        ) / len(structure.polygon)

        assert wall.members
        for member in wall.members:
            for point in (member.p0, member.p1):
                offset = (point[0] - start[0]) * normal_x + (point[1] - start[1]) * normal_y
                assert offset == pytest.approx(center_offset, abs=1e-9)


def test_sunken_garden_structure_matches_redesign_spec(catlin_model):
    """Freestanding porch/balcony redesign: no north wall, single 16" arched front wall
    with two arches, a masonry railing, a sonotube column + PT back beams, six 6x6 pillars
    + three balcony beams, and a 19x28 garden."""
    walls = [w for w in catlin_model.walls if w.tag.startswith("W-SG-")]
    # 6 concrete (ARCH + W1/E1/W2/E2/S) + 3 masonry railing (RAIL-F/W/E); no north wall.
    assert len(walls) == 9
    assert all(w.is_foundation for w in walls)
    assert not any(w.tag == "W-SG-N" for w in walls)
    arch_wall = next(w for w in walls if w.tag == "W-SG-ARCH")
    assert arch_wall.assembly == "SUNKEN_GARDEN_ARCH_16"
    railings = [w for w in walls if w.tag.startswith("W-SG-RAIL-")]
    assert len(railings) == 3
    assert all(w.assembly == "PORCH_RAILING_MASONRY" for w in railings)

    # A single garden-level tier of two 8'-wide arches across the front wall.
    arches = [o for o in catlin_model.openings if o.tag.startswith("AO-")]
    assert len(arches) == 2
    assert all(o.width_m == pytest.approx(ft(8).meters) for o in arches)
    assert all(o.host_wall == "W-SG-ARCH" for o in arches)

    garden = next(s for s in catlin_model.solids if s.tag == "SL-SG-FLOOR")
    xs = [p[0] for p in garden.outline]
    ys = [p[1] for p in garden.outline]
    assert max(xs) - min(xs) == pytest.approx(ft(19).meters)
    assert max(ys) - min(ys) == pytest.approx(ft(28).meters)

    # The porch/balcony framing members are authored (their 3D resolution is Phase 2).
    elements = [el for tag in ("basement", "main", "second")
                for el in catlin_model.plan.storey_elements(tag)]
    posts = {el.tag for el in elements if el.element_kind == "Post" and el.tag.startswith("PT-SG-")}
    beams = {el.tag for el in elements if el.element_kind == "Beam" and el.tag.startswith("BM-SG-")}
    assert "PT-SG-COL" in posts  # sonotube column
    assert len([t for t in posts if t.startswith("PT-SG-B")]) == 6  # 6x6 pillars
    assert len(beams) == 5  # 2 PT 2x12 back beams + 3 double-2x10 balcony beams

    # Both exterior decks carry a decking assembly.
    porch = next(s for s in catlin_model.solids if s.tag == "SL-SG-PORCH")
    deck = next(s for s in catlin_model.solids if s.tag == "SL-SG-DECK")
    assert porch.assembly == "PORCH_DECK_COMPOSITE"
    assert deck.assembly == "BALCONY_DECK_ALUMINUM"


def test_stack_width_change_resolves_on_the_side_wall_line(catlin_model):
    """M3 acceptance: 2x6 -> 2x4 -> 2x4 stack with a width-change edge (#43)."""
    width_changes = [e for e in catlin_model.stack_edges if e.width_change]
    main_to_second = [
        e for e in width_changes
        if e.lower_wall.startswith("W-M-") and e.upper_wall.startswith("W-S-")
    ]
    assert main_to_second, width_changes
    keys = {c.key for c in catlin_model.conditions}
    assert any("stack_width_change" in k for k in keys)
    assert any("storey_stack" in k for k in keys)


def test_wall_and_room_counts_by_storey(catlin_model):
    """Coarse census — the port carries the whole program, not a subset."""
    by_storey: dict[str, int] = {}
    for wall in catlin_model.walls:
        by_storey[wall.storey] = by_storey.get(wall.storey, 0) + 1
    assert by_storey["basement"] >= 25  # house concrete + garden + garage stem
    assert by_storey["main"] >= 25
    assert by_storey["second"] >= 30
    assert by_storey["attic"] >= 12
    assert by_storey["garage"] == 4
    rooms = {r.tag for r in catlin_model.rooms}
    assert {"RM-B-SAUNA", "RM-M-LIVING", "RM-S-PLANT", "RM-A-WEST",
            "RM-GARAGE"} <= rooms


def test_stairs_resolve_with_code_risers(catlin_model):
    stairs = {s.tag: s for s in catlin_model.stairs}
    assert set(stairs) == {"ST-B2M", "ST-M2S", "ST-S2A"}
    for stair in stairs.values():
        assert stair.riser_count in {14, 16}
        assert stair.riser_height_m <= inch(7.75).meters + 1e-9
        assert stair.tread_depth_m >= inch(10.0).meters - 1e-9
    attic = stairs["ST-S2A"]
    assert attic.winder_count == 3
    assert attic.run_reversed is True
    winders = [member for member in attic.members if member.category == "winder"]
    assert len(winders) == 3
    # All three radial tread edges share the inside turn, never opposed diagonals.
    assert len({member.p0 for member in winders}) == 1
    for tag in ("ST-B2M", "ST-M2S"):
        stair = stairs[tag]
        assert stair.layout == "u_split_landing"
        assert {member.child_key for member in stair.members} >= {
            "landing-lower", "step-between-landings", "landing-upper",
        }


def test_stair_designer_contract_exposes_catlin_authored_inputs(catlin_model):
    """The editor receives editable inputs alongside resolver-owned stair geometry."""
    from typehaus.server.model_json import model_to_dict

    stairs = {item["tag"]: item for item in model_to_dict(catlin_model)["stairs"]}
    assert set(stairs) == {"ST-B2M", "ST-M2S", "ST-S2A"}
    assert stairs["ST-B2M"]["width_m"] == pytest.approx(ft(3, 6).meters, abs=1e-9)
    assert stairs["ST-B2M"]["floor_opening"] == "FO-M-STAIR"
    assert stairs["ST-B2M"]["run_direction"] == "y"
    assert stairs["ST-B2M"]["layout"] == "u_split_landing"
    assert stairs["ST-B2M"]["start"] == pytest.approx([ft(11).meters, ft(25).meters])
    assert stairs["ST-M2S"]["layout"] == "u_split_landing"
    assert stairs["ST-S2A"]["layout"] == "right_angle_winder"
    assert stairs["ST-S2A"]["turn_direction"] == "left"
    assert stairs["ST-S2A"]["winder_count"] == 3
    assert stairs["ST-S2A"]["run_reversed"] is True


def test_ifc_emission_when_available(catlin_model, tmp_path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    import ifcopenshell.validate
    from typehaus.emit.ifc import emit_ifc

    path = emit_ifc(catlin_model, tmp_path / "catlin.ifc", lod="framed")
    assert path.exists() and path.stat().st_size > 0
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(str(path), logger, express_rules=True)
    assert not logger.statements, logger.statements
