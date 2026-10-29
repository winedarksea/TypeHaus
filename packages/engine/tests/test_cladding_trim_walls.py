"""Wall base, door, screen-end and small-opening trim: the inventory the note works by hand."""

from collections import Counter
from copy import copy
from dataclasses import replace

import pytest

from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.takeoff.cladding_trim import cladding_trim_takeoff


def _pieces(model):
    return [s for s in model.solids if s.category == "cladding_trim"]


def test_trim_inventory_by_profile(catlin_model_ro):
    counts = Counter(s.product for s in _pieces(catlin_model_ro))
    assert counts == {
        "PBR_WINDOW_JAMB": 36, "WINDOW_JAMB_CUSTOM": 48, "WINDOW_SILL_CUSTOM": 42,
        "OPENING_HEAD": 42,
        "PBR_BASE": 11, "BBD_BASE": 10, "CORRUGATED_BASE": 12, "BBD_TRANSITION": 10,
        "BBD_PANEL_STARTER": 6, "CORRUGATED_JAMB": 8, "DOOR_HEAD_CUSTOM": 5,
        "WIDE_OUTSIDE_CORNER": 8, "CORRUGATED_OUTSIDE_CORNER": 4,
        "RAINSCREEN_BASE_Z": 21, "EPDM_BASE_ISOLATION": 14,
        "OPENING_HEAD_CAP": 38,
        # 6411499: the four gable corner stubs inside the eave skins are gone.
        "6460800": 9, "6411499": 6, "CORRUGATED_SILL_TO_SOFFIT": 6,
        "corrugated-outside-closure": 6,
    }


def test_base_run_splits_at_stock_with_a_lap():
    # W-M-W4: a 164.8 in run takes one 122 in stick and a second to cover the 2 in lap.
    assert len(split_stock_run(164.8, (122.0,), 2.0)) == 2


def test_screen_ends_close_both_edges_of_the_screen_and_its_skirt(catlin_model_ro):
    ends = {s.tag: s for s in _pieces(catlin_model_ro) if "-END-" in s.tag}
    assert sorted(ends) == [
        "TRIM-W-BW-SCREEN-END-HI-1", "TRIM-W-BW-SCREEN-END-LO-1",
        "TRIM-W-BW-SCREEN-SKIRT-END-HI-1", "TRIM-W-BW-SCREEN-SKIRT-END-LO-1"]
    assert ends["TRIM-W-BW-SCREEN-END-HI-1"].trim_length_m / M_PER_IN == pytest.approx(48.9, 0.01)


def test_catalog_door_takes_jambs_but_its_head_is_the_band(catlin_model_ro):
    pieces = _pieces(catlin_model_ro)
    deck = [s for s in pieces if s.host_ref == "D-S-DECK-E"]
    assert sorted(s.product for s in deck) == ["BBD_PANEL_STARTER", "BBD_PANEL_STARTER"]
    assert all("-TRIM-HEAD-" not in s.tag for s in deck)
    bands = [s for s in pieces if s.product == "BBD_TRANSITION"]
    assert any(s.z0_m / M_PER_IN < 208 < s.z1_m / M_PER_IN for s in bands)


def test_penetrations_under_six_inches_take_no_trim(catlin_model_ro):
    hosts = {s.host_ref for s in _pieces(catlin_model_ro)}
    assert {"AO-M-ERV-OA", "AO-S-ERV-EA"} <= hosts
    assert not hosts & {"AO-M-FIRE-NICHE", "AO-M-PORCH-HYD", "AO-S-BALC-HYD"}


def test_interior_fireplace_niche_has_no_exterior_trim_or_trim_findings(catlin_model_ro):
    from typehaus.checks.integrity.cladding_trim_coverage import _window_like
    from typehaus.checks.integrity.cladding_trim_fit import _opening_runs, _site_brake
    from typehaus.checks.registry import CheckContext

    model = catlin_model_ro
    niche = "AO-M-FIRE-NICHE"
    assert not any(s.host_ref == niche and s.category in {"cladding_trim", "opening_flashing"}
                   for s in model.solids)
    assert not any(niche in tag for row in cladding_trim_takeoff(model) for tag in row["tags"])
    ctx = CheckContext(plan=model.plan, model=model, preferences=None, profile=None)
    pieces = _pieces(model)
    findings = [*_window_like(ctx, pieces), *_opening_runs(ctx, pieces), *_site_brake(ctx, pieces)]
    assert not any(niche in f.element_tags for f in findings)

    missing_erv_trim = [piece for piece in pieces if piece.host_ref != "AO-M-ERV-OA"]
    assert any(f.result.name == "FAIL" and "AO-M-ERV-OA" in f.element_tags
               for f in _window_like(ctx, missing_erv_trim))


def test_roof_edges_bill_as_image_ii_pieces(catlin_model_ro):
    rows = {r["part"]: r for r in cladding_trim_takeoff(catlin_model_ro) if r["kind"] == "roof"}
    assert rows["52124XX"]["count"] == 16        # extended eave: six eave runs, three roofs
    assert rows["52131XX"]["count"] == 5         # closed ridge cover: house and canopy
    # Every exposed rake: the house's four runs, the garage's north gable and the canopy's
    # south gable. The garage south and canopy north are one plane (abutted_run_keys), no piece.
    assert rows["52126XX"]["count"] == 16
    assert rows["52132XX"]["count"] == 16        # one rake cleat per rake stick
    assert rows["5806199"]["count"] == 40        # flat cleats on barge boards only (the fascias)
    assert "IMAGE_II_RAKE_4IN_CUSTOM" not in rows  # the house rake is the stock 2-5/8 in leg


def test_garage_vented_ridge_bills_by_part_and_its_closure(catlin_model_ro):
    garage = [r for r in cladding_trim_takeoff(catlin_model_ro)
              if "RF-GARAGE:ridge-vent-cap" in r["tags"]]
    by_part = {r["part"]: r for r in garage}
    vented = by_part["IMAGE_II_VENTED_STEP_RIDGE"]
    assert vented["count"] == 3                  # 25.7 LF in 10'-2" sticks, 2 in laps
    # The closure runs the ridge once; the cover's laps are its own extra cut.
    assert by_part["cobra-vented-closure"]["length_ft"] == pytest.approx(25.41, abs=0.01)
    assert vented["cut_length_ft"] > by_part["cobra-vented-closure"]["length_ft"]
    # Rivets are one row for the whole house; the garage's share is its tag on that row.
    assert "RF-GARAGE:ridge-vent-cap" in by_part["trim-pop-rivet"]["tags"]
    assert "58603XX" not in by_part, "the vented ridge takes no Z-closure"


def test_wall_top_edges_use_developed_length_without_stacked_duplicates(catlin_model_ro):
    from typehaus.resolve.cladding_trim.wall_tops import exposed_wall_top_edges

    totals = Counter()
    for edge in exposed_wall_top_edges(catlin_model_ro):
        totals[edge.product] += edge.length_m / 0.3048
    assert totals["6460800"] == pytest.approx(74.25, abs=0.02)
    assert totals["6411499"] == pytest.approx(82.7345, abs=0.02)
    assert totals["CORRUGATED_SILL_TO_SOFFIT"] == pytest.approx(48.2917, abs=0.02)
    assert totals["corrugated-outside-closure"] == pytest.approx(99.0418, abs=0.02)


def test_garage_soffit_trim_meets_the_soffit_not_the_higher_panel_top(catlin_model_ro):
    from typehaus.checks.integrity.cladding_trim_fit import _soffit_panel_joint
    from typehaus.checks.registry import CheckContext
    from typehaus.resolve.cladding_trim.wall_tops import exposed_wall_top_edges

    edges = exposed_wall_top_edges(catlin_model_ro)
    sill = next(e for e in edges if e.wall.tag == "W-G-W"
                and e.product == "CORRUGATED_SILL_TO_SOFFIT")
    top = next(e for e in edges if e.wall.tag == "W-G-W"
               and e.product == "corrugated-outside-closure")
    assert sill.z_start / M_PER_IN == pytest.approx(84.1667, abs=0.01)
    assert top.z_start / M_PER_IN == pytest.approx(91.5, abs=0.01)
    ctx = CheckContext(plan=catlin_model_ro.plan, model=catlin_model_ro,
                       preferences=None, profile=None)
    assert any(f.result.name == "UNKNOWN" for f in _soffit_panel_joint(ctx))


@pytest.mark.parametrize("product", ["6460800", "6411499", "CORRUGATED_SILL_TO_SOFFIT"])
def test_wall_top_check_detects_missing_or_displaced_termination(catlin_model_ro, product):
    from typehaus.checks.integrity.cladding_trim_coverage import _wall_tops
    from typehaus.checks.registry import CheckContext

    model = copy(catlin_model_ro)
    piece = next(s for s in model.solids if s.product == product)
    # Remove a whole run, including every stock piece at that wall.
    model.solids = [s for s in model.solids if not (s.host_ref == piece.host_ref
                                                     and s.product == product)]
    ctx = CheckContext(plan=model.plan, model=model, preferences=None, profile=None)
    assert any(f.result.name == "FAIL" for f in _wall_tops(ctx, model.solids))

    shifted = replace(piece, body_mesh=replace(
        piece.body_mesh, positions=tuple((x, y, z + inch(6).meters)
                                         for x, y, z in piece.body_mesh.positions)))
    model.solids = [s for s in catlin_model_ro.solids if s is not piece] + [shifted]
    assert any(f.result.name == "FAIL" and piece.host_ref in f.message
               for f in _wall_tops(ctx, model.solids))


def test_wall_top_check_does_not_hide_a_missing_kit_mapping(catlin_model_ro):
    from typehaus.checks.integrity.cladding_trim_coverage import _wall_tops
    from typehaus.checks.registry import CheckContext
    from typehaus.model.cladding_trim import TrimCondition

    model = copy(catlin_model_ro)
    materials = tuple(
        material.model_copy(update={"trim_kit": {
            key: value for key, value in material.trim_kit.items()
            if key != TrimCondition.EAVE_TOP}})
        if material.tag == "pbr-panel-24" else material
        for material in model.plan.library.materials)
    library = model.plan.library.model_copy(update={"materials": materials})
    model.plan = model.plan.model_copy(update={"library": library})
    ctx = CheckContext(plan=model.plan, model=model, preferences=None, profile=None)
    assert any(f.result.name == "FAIL" and "W-S-E" in f.message
               for f in _wall_tops(ctx, model.solids))


def test_the_vented_ridge_is_the_coverage_checks_one_supplier_question(catlin_check_report):
    from typehaus.findings import Result

    report = catlin_check_report()
    open_items = [f for f in report.findings if f.check_id == "integrity.cladding_trim_coverage"
                  and f.result is Result.UNKNOWN]
    assert len(open_items) == 1
    assert "step ridge" in open_items[0].message and "Cobra" in open_items[0].message
