"""Finite reservations grade physical envelopes and constrain routes above a real floor."""

from dataclasses import replace
from types import SimpleNamespace
from uuid import UUID

import pytest
from pydantic import ValidationError

from typehaus import ClearZone, Library, PlanModel, Project, Site, Storey, m, pt
from typehaus.checks.integrity.clear_zones import CHECK_ID, clear_zone_intrusion
from typehaus.checks.registry import CheckReport, Tier, registered
from typehaus.findings import Result, Severity, by_result, fold_results
from typehaus.resolve.clear_zones import resolve_clear_zones
from typehaus.resolve.model import (
    ResolvedCanvasObject,
    ResolvedDuct,
    ResolvedLayer,
    ResolvedModel,
    ResolvedOpening,
    ResolvedRoom,
    ResolvedSolid,
    ResolvedWall,
)
from typehaus.routing.diagnostics import Mobility, mobility_of
from typehaus.routing.obstacles import hard_prisms


@pytest.fixture
def model():
    zone = ClearZone(uid="ZONE", tag="CZ", outline=(pt(m(0), m(0)), pt(m(2), m(0)),
                    pt(m(2), m(10)), pt(m(0), m(10))),
                    bottom=m(0), top=m(2), purpose="reserved access")
    plan = PlanModel(project=Project(name="clear volume", project_uuid=UUID(int=1),
                     site=Site(lat=0, lon=0, elevation=m(0))), library=Library(),
                     storeys=(Storey(tag="basement", elevation=m(0),
                                     default_ceiling_height=m(3)),),
                     elements={"basement": (zone,)})
    resolved = ResolvedModel(plan=plan)
    assert not resolve_clear_zones(resolved)
    return resolved


def _findings(model):
    return clear_zone_intrusion(SimpleNamespace(model=model))


def _duct(tag, path, z, insulation=None):
    return ResolvedDuct(uid=tag, tag=tag, storey="basement", system="supply", path=path,
                        width_m=0.2, depth_m=0.2, diameter_m=0.2, routing="exposed",
                        floor_ref=None, crossings=(), conflicts=(), depth_ok=True,
                        z_m=tuple(z), insulation=insulation)


def _wall():
    return ResolvedWall(uid="W", tag="W", storey="basement", assembly="EXT",
                        axis=((0, 0), (4, 0)), z0_m=0, z1_m=3,
                        layers=(ResolvedLayer(name="structure", material_ref="spf",
                            thickness_m=0.14, function="structure",
                            polygon=((0, -0.07), (4, -0.07), (4, 0.07), (0, 0.07))),))


def test_registered_and_required_intrusion_fails_once_per_element(model):
    assert CHECK_ID in {cid for cid, _ in registered(Tier.INTEGRITY)}
    model.ducts.append(_duct("DU", [(-1, 2), (1, 2), (1, 4)], [1, 1, 1]))
    findings = _findings(model)
    assert len(findings) == 1
    assert findings[0].element_tags == ("CZ", "DU")
    assert findings[0].result is Result.FAIL
    assert findings[0].severity is Severity.ERROR


def test_recommended_is_advisory_and_has_its_own_tally(model):
    model.clear_zones[0] = replace(model.clear_zones[0], policy="recommended")
    model.ducts.append(_duct("DU", [(-1, 2), (3, 2)], [1, 1]))
    findings = _findings(model)
    assert findings[0].result is Result.ADVISORY
    report = CheckReport(findings)
    assert report.ok and report.counts().failed == 0
    assert report.counts().advisory == report.counts().total == 1


@pytest.mark.parametrize("policy, expected, gate_ok", [
    ("recommended", Result.ADVISORY, True), ("required", Result.FAIL, False)])
def test_checklist_preserves_recommendations_and_required_failures(
        model, policy, expected, gate_ok):
    from typehaus.checks.permit import PermitChecklist, PermitChecklistItem

    model.clear_zones[0] = replace(model.clear_zones[0], policy=policy)
    model.ducts.append(_duct("DU", [(-1, 2), (3, 2)], [1, 1]))
    result, detail = fold_results(_findings(model))
    assert result is expected
    checklist = PermitChecklist(profile_name="test", items=(PermitChecklistItem(
        label="Activity lane", result=result, detail=detail, check_ids=(CHECK_ID,)),))
    assert checklist.ok is gate_ok
    assert by_result(CHECK_ID, result, detail).result is expected


def test_required_failures_and_unknown_measurements_outrank_recommendations():
    recommendation = by_result(CHECK_ID, Result.ADVISORY, "unmet recommendation")
    for result in (Result.FAIL, Result.UNKNOWN):
        verdict, _detail = fold_results([recommendation,
                                        by_result(CHECK_ID, result, "outstanding")])
        assert verdict is result


def test_insulation_and_repeated_plan_point_risers_are_physical_obstructions(model):
    # Bare underside is 2.01 m; one inch of lagging puts it below the 2 m ceiling.
    model.ducts.append(_duct("WRAPPED", [(-1, 2), (3, 2)], [2.11, 2.11], "1in wrap"))
    model.ducts.append(_duct("RISER", [(1, 4), (1, 4)], [1, 3]))
    assert {f.element_tags[-1] for f in _findings(model)} == {"WRAPPED", "RISER"}


def test_segment_heights_do_not_project_a_remote_drop_along_the_whole_run(model):
    model.ducts.append(_duct("HIGH", [(-1, 2), (3, 2), (3, 4)], [3, 3, 1]))
    # Derived rendering solids deliberately bound the whole run; they must not be graded
    # again as a full-height prism after the segment envelopes have cleared the zone.
    model.solids.append(ResolvedSolid(uid="HIGH-run", tag="HIGH-RUN", storey="basement",
        category="duct_supply", outline=[(-1, 1.9), (3.1, 1.9), (3.1, 4.1), (-1, 4.1)],
        z0_m=0.9, z1_m=3.1))
    assert [f.result for f in _findings(model)] == [Result.PASS]


def test_only_explicit_tags_pardon_bodies_and_accessories(model):
    model.canvas_objects.append(ResolvedCanvasObject(
        uid="EQ", tag="EQ", storey="basement", domain="mechanical", kind="Equipment",
        type_ref=None, room=None, position=(1, 2), z_m=1, rotation_degrees=0,
        footprint=[(0.5, 1), (1.5, 1), (1.5, 3), (0.5, 3)],
        body_z0_m=0.8, body_z1_m=1.8))
    model.solids.append(ResolvedSolid(uid="BFP", tag="BFP", storey="garage",
        category="backflow_preventer", outline=[(0.5, 1), (1.5, 1), (1.5, 2), (0.5, 2)],
        z0_m=1, z1_m=1.2))
    model.clear_zones[0] = replace(model.clear_zones[0], except_tags=("EQ-*",))
    assert {f.element_tags[-1] for f in _findings(model)} == {"EQ", "BFP"}
    model.clear_zones[0] = replace(model.clear_zones[0], except_tags=("EQ", "BFP"))
    assert [f.result for f in _findings(model)] == [Result.PASS]


def test_leaf_at_rest_is_checked_without_treating_the_whole_swing_as_a_body(model):
    model.walls.append(_wall())
    model.openings.append(ResolvedOpening(uid="D", tag="D", host_wall="W", type_ref=None,
        width_m=0.9, height_m=2, sill_m=0, center_along_m=1, kind="door", is_door=True,
        swing_clearance=[(0, 0), (2, 0), (2, 2), (0, 2)]))
    assert _findings(model)[0].element_tags == ("CZ", "D")
    model.clear_zones[0] = replace(model.clear_zones[0],
        outline=((0, 0.2), (2, 0.2), (2, 10), (0, 10)))
    assert [f.result for f in _findings(model)] == [Result.PASS]


def test_missing_body_dimensions_report_unknown_instead_of_clear(model):
    model.canvas_objects.append(ResolvedCanvasObject(
        uid="F", tag="F", storey="basement", domain="furniture", kind="Furniture",
        type_ref=None, room=None, position=(1, 2), z_m=0, rotation_degrees=0,
        footprint=[(0.5, 1), (1.5, 1), (1.5, 2), (0.5, 2)]))
    assert [f.result for f in _findings(model)] == [Result.UNKNOWN]


def test_schematic_run_gaps_only_affect_zones_the_known_plan_path_could_enter(model):
    model.ducts.append(_duct("UNPLACED-ELSEWHERE", [(4, 1), (4, 4)], []))
    assert [f.result for f in _findings(model)] == [Result.PASS]
    model.ducts.append(_duct("UNPLACED-HERE", [(1, 1), (1, 4)], []))
    findings = _findings(model)
    assert len(findings) == 1 and findings[0].result is Result.UNKNOWN
    assert "UNPLACED-HERE" in findings[0].message


def test_known_elevations_scope_envelope_spec_gaps_to_the_zone(model):
    model.ducts.append(_duct("HIGH-UNKNOWN-WRAP", [(1, 1), (1, 4)], [4, 4], "R-8"))
    assert [f.result for f in _findings(model)] == [Result.PASS]
    model.ducts.append(_duct("LOW-UNKNOWN-WRAP", [(1, 1), (1, 4)], [1, 1], "R-8"))
    findings = _findings(model)
    assert {f.result for f in findings} == {Result.FAIL, Result.UNKNOWN}
    assert all("HIGH-UNKNOWN-WRAP" not in f.message for f in findings)


def test_clear_zone_is_an_authored_reservation_without_a_ui_move_operation(model):
    from typehaus.source.loader import _UI_EDITABLE_KINDS
    from typehaus.source.macros_common import _PLACEABLE_KINDS

    assert not {base.__name__ for base in ClearZone.__mro__} & _UI_EDITABLE_KINDS
    assert "ClearZone" not in _PLACEABLE_KINDS


def test_invalid_nearby_physical_geometry_is_unknown_and_distant_geometry_does_not_crash(model):
    invalid = ResolvedSolid(uid="BAD", tag="BAD", storey="basement", category="slab",
        outline=[(0.5, 1), (1.5, 2), (0.5, 2), (1.5, 1)], z0_m=0.5, z1_m=0.7)
    model.solids.append(invalid)
    assert [f.result for f in _findings(model)] == [Result.UNKNOWN]
    model.solids[0] = replace(invalid, outline=[(x + 10, y) for x, y in invalid.outline])
    assert [f.result for f in _findings(model)] == [Result.PASS]


@pytest.mark.parametrize("avoid", [frozenset(), frozenset({"CZ"})])
def test_routing_prism_has_a_finite_band_and_counts_radius_and_clearance(model, avoid):
    prism, = [p for p in hard_prisms(model, 0.1, clearance_m=0.02, avoid=avoid)
              if p.tag == "CZ"]
    assert prism.kind == "clear_zone"
    assert mobility_of(prism.kind) is Mobility.FIXED
    assert prism.z0_m == pytest.approx(-0.12)
    assert prism.z1_m == pytest.approx(2.12)
    assert prism.blocks((1, 2), 2.1)
    assert not prism.blocks((1, 2), 2.13)


def test_floor_reference_is_the_actual_slab_not_the_storey_datum(model):
    model.clear_zones.clear()
    model.walls.append(_wall())
    model.rooms.append(ResolvedRoom(uid="R", tag="R", storey="basement",
        occupancy="storage", conditioned=False, clear_face=[(0, 0), (2, 0), (2, 10), (0, 10)],
        area_m2=20, floor_finish=None))
    model.solids.append(ResolvedSolid(uid="SL", tag="SL", storey="basement",
        category="slab", outline=[(-1, -1), (3, -1), (3, 11), (-1, 11)], z0_m=-0.6, z1_m=-0.5))
    assert not resolve_clear_zones(model)
    assert model.clear_zones[0].z0_m == pytest.approx(-0.5)
    assert model.clear_zones[0].z1_m == pytest.approx(1.5)


@pytest.mark.parametrize("changes", [{"bottom": m(-1)}, {"top": m(0)},
    {"outline": (pt(m(0), m(0)),)}, {"policy": "optional"}])
def test_invalid_clear_zone_contracts_are_rejected(model, changes):
    values = {**model.plan.by_tag("CZ").__dict__, **changes}
    with pytest.raises(ValidationError):
        ClearZone(**values)


def test_catlin_full_lane_is_required_and_clear(catlin_model_ro):
    # The owner's minimum is 10 m by 6'; the ERV moved east of the lane on 2026-10-17.
    zone = next(z for z in catlin_model_ro.clear_zones if z.tag == "CZ-B-DRYFIRE")
    length_m = max(y for _, y in zone.outline) - min(y for _, y in zone.outline)
    assert length_m == pytest.approx(10.2504875)
    assert length_m >= 10.0
    assert zone.z1_m - zone.z0_m == pytest.approx(72 * 0.0254)
    assert zone.policy == "required"
    findings = _findings(catlin_model_ro)
    assert findings and all(f.check_id == CHECK_ID for f in findings)
    assert all(f.element_tags[0] == zone.tag for f in findings)
    assert {f.result for f in findings} == {Result.PASS}
