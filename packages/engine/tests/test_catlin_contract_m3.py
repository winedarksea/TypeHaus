"""WP3.7 — the catlin **design contract**: the constants the port committed to.

These are *declared* facts, not a comparison: 36' house at sheathing, 16" o.c., 18' grid,
4:12 hot roof with knee 5' / ridge 11' over the attic floor, 12" basement walls + 2x2" XPS,
24' ICF garage 4'-6 3/8" north at the wall lines (4'-0 1/2" of clear slot once both
skins are on),
the freestanding arched sunken-garden structure — plus the views,
checks and emitters those numbers feed. They are inlined here because the old repo is being
archived, and they guard the design against silent drift.

The *equivalence* claim they used to stand in for — "the rebuilt model still means what the
old catlin-house IFC meant" — is now made by a real semantic comparison against that IFC in
``test_catlin_equivalence_m3.py``. Contract facts live here; equivalence lives there.
"""

from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.quantities import ft, inch
from typehaus.resolve import resolve
from typehaus.resolve.framing.profiles import RIDGE_BEAM_DEFAULT, cross_section
from typehaus.resolve.geometry_members import member_solid
from typehaus.source import load_plan
from typehaus.checks import run
from typehaus.findings import Result
from _helpers import CATLIN as CATLIN_DIR, frames_structure

# Old CatlinHouseSpec contract values.
HOUSE_SIZE_FT = 36.0
FRAMING_SPACING_IN = 16.0
GRID_FT = 18.0
KNEE_FT = 5.0
RIDGE_OVER_ATTIC_FT = 11.0
ATTIC_ELEV_FT = 20.0
GARAGE_SIZE_FT = 24.0
# House sheathing plane to garage wall line. The finished gap is tighter: the house's 7 1/4"
# of outsulation + cladding and the garage's own 1/2" of cladding leave 4'-0 1/2" of clear
# slot, which is what the breezeway's 4'-0" polycarbonate panels are sized to.
#
# 4.57292' (4'-6 7/8"), not the 5'-0" it was until 2026-08-15. The garage's ICF stem used to
# straddle the wall line and stand 5 5/8" proud of the cladding — a rain shelf right round
# the building. Aligning the stem's exterior EPS face onto the wall line fixed that, and the
# wall lines moved 5 5/8" south with it so the clear slot, and the uncut 4'-0" panel in it,
# are exactly what they were. The *cladding* is the controlling face now, where the stem
# used to be.
#
# It grew 1/2" on 2026-08-23, another 1" on 2026-08-26, and 3/8" more the same day, for the
# identical reason every time. The Swinburne truss put the HOUSE's cladding 1/2" further
# north (5.02" -> 5.5" proud of y=36'); the catlin truss's four flat girt layers put it 1"
# further again (5.5" -> 6.5"); then the 1 1/4" exposed-fastener PBR panel replaced the 1/2"
# snap-lock seam and took it to 7.25". Any of those alone would have closed the breezeway's
# clear slot to 4'-0" or less and left an uncut 4'-0" panel with nowhere to go, so the garage
# moved with it and the slot — and the panel's 1/2" reveal — are again exactly what they
# were. Both wall lines moved each time; the garage is still 24'-0" square.
#
# The last move is only 3/8" against the house's 3/4", and the difference is a CORRECTION:
# ``params/breezeway.py`` carried a 3/8" rainscreen furring on the garage face that
# ``GARAGE_WALL_2X6`` dropped on 2026-08-20, so the modelled garage face had been 3/8" south
# of where it stands for six days. Fixing that gave back exactly half the move.
GARAGE_GAP_FT = 4.6875
GARAGE_OVERHANG_IN = 16.0
# eave_z_m is the rafter-top (deck) plane: the 11.875" I-joist rises above the knee-wall
# plate by its depth less the seat drop across the stud (5.5" 2x6 depth x 4:12 pitch =
# 1.8333" — the knee walls went 2x6 with the rest of the envelope), per the golden eave
# detail (roof_wall_eave_detail_ifc.py). The birdsmouth notch itself stays 1.17" deep.
DECK_RISE_FT = (11.875 - 5.5 / 3.0) / 12.0


def test_floor_joist_counts_match_old_model(catlin_model):
    """Old: positions = size/spacing + 1 (both ends), two 18' spans per floor."""
    expected_positions = int(round(HOUSE_SIZE_FT * 12.0 / FRAMING_SPACING_IN)) + 1
    expected_pair_count = expected_positions * 2
    for tag in ("FS-ATTIC",):
        floor = next(f for f in catlin_model.floors if f.tag == tag)
        joists = [m for m in floor.members if m.category == "joist"]
        assert len(joists) == expected_pair_count, tag
        # Most joists retain the 18' bearing span; lines crossing a stair opening are
        # clipped at its framed edge rather than running through the stairwell.
        spans = {round(m.length_m / ft(1).meters, 3) for m in joists}
        assert GRID_FT in spans

    # Since 2026-08-21 the second floor is FS-S-WEST/FS-S-EAST, not one whole-floor
    # FS-SECOND: each half spans only 18' (one bearing pair, not two), so each has
    # ``expected_positions`` joists rather than ``expected_pair_count`` of them.
    west = next(f for f in catlin_model.floors if f.tag == "FS-S-WEST")
    east = next(f for f in catlin_model.floors if f.tag == "FS-S-EAST")
    west_joists = [m for m in west.members if m.category == "joist"]
    east_joists = [m for m in east.members if m.category == "joist"]
    assert len(west_joists) == expected_positions
    assert len(east_joists) == expected_positions
    east_spans = {round(m.length_m / ft(1).meters, 3) for m in east_joists}
    assert east_spans == {GRID_FT}
    west_spans = {round(m.length_m / ft(1).meters, 3) for m in west_joists}
    assert GRID_FT in west_spans
    # FO-S-STAIR is drawn to the finished well, so the clip lands on W-M-STRW's
    # stair-side face at x=10'-3 3/8" rather than on its centreline. 8 lines clip here,
    # not the 7 that only cross the opening's own y-range: the doubled trimmer pair
    # along the opening's long edge (a floor truss's 3 1/2" chord is wider than an
    # I-joist's 2 1/2" flange at this depth) reaches past the opening into the next
    # regular joist line's own footprint, so that line is clipped too rather than left
    # to interpenetrate the trimmer (structural.member_interference).
    assert 10.281 in west_spans
    assert sum(1 for s in (round(m.length_m / ft(1).meters, 3) for m in west_joists)
              if s == 10.281) == 8


def test_catlin_i_joists_and_frost_supports_pass_the_declared_structural_tables():
    report = run(load_plan(CATLIN_DIR).plan, CATLIN_DIR, tier=None)
    findings = [finding for finding in report.findings
                if finding.check_id in {"structural.ijoist_span", "structural.frost_depth"}]
    assert findings
    # Nothing FAILS. The seven sunken-garden footings report UNKNOWN — they retain the
    # excavation they stand in, which IRC R404.4 sends to an engineered design rather than to
    # any prescriptive table — and the four house footings the garden reaches PASS through
    # IRC R403.3's frost-protected path on the wing insulation under the garden slab. Every
    # one of the eleven read a comfortable 7'-2" and passed until 2026-08-22, because the
    # rule measured them against a grade plane six and a half feet over their heads.
    assert not [f for f in findings if f.result is Result.FAIL]
    unknown = [f for f in findings if f.result is Result.UNKNOWN]
    assert {tag for f in unknown for tag in f.element_tags if tag.startswith("FT-")} == {
        "FT-SG-W1", "FT-SG-W2", "FT-SG-E1", "FT-SG-E2", "FT-SG-S",
        "FT-SG-COL", "FT-SG-FCOL"}


def test_catlin_sunken_garden_decks_are_graded_and_the_guard_rule_resolves():
    """Both freestanding sunken-garden walking surfaces carry ``service="deck"`` (IRC R507 /
    AWC DCA6 scope, like the breezeway's FS-BW-FLOOR) and ``structural.deck_guard`` reaches a
    real verdict for each: the balcony is guarded by RL-SG-BALCONY at 42" over its 120" drop,
    and the porch surface sits at the site grade datum, under the 30" R312.1 threshold.
    (The check measures against site grade — the -9' garden floor beside the porch is a
    condition it deliberately does not model.)"""
    from typehaus.model.floors import FloorSystem

    plan = load_plan(CATLIN_DIR).plan
    decks = {e.tag: e for e in plan.all_elements()
             if isinstance(e, FloorSystem) and e.service == "deck"}
    assert {"FS-SG-PORCH", "FS-SG-DECK"} <= set(decks)
    report = run(plan, CATLIN_DIR, tier=None)
    guard = {tag: [f for f in report.findings if f.check_id == "structural.deck_guard"
                   and tag in f.element_tags]
             for tag in ("FS-SG-PORCH", "FS-SG-DECK")}
    for tag, findings in guard.items():
        assert findings, f"{tag} produced no deck_guard finding"
        assert all(f.result is Result.PASS for f in findings), \
            [f.message for f in findings if f.result is not Result.PASS]
    balcony = guard["FS-SG-DECK"][0]
    assert "RL-SG-BALCONY" in balcony.element_tags


def test_catlin_fixtures_do_not_overlap_and_required_clearances_hold():
    """The ensuite de-overlap pass and the BATH2 wet-wall move leave every room's fixture
    footprints pairwise disjoint with each WC's REQUIRED clearance zone empty."""
    report = run(load_plan(CATLIN_DIR).plan, CATLIN_DIR, tier=None)
    findings = [f for f in report.findings if f.check_id == "advisory.fixture_overlap"]
    assert not findings, [f.message for f in findings]


def test_catlin_permit_checklist_passes_declared_minnesota_subset():
    from typehaus.checks import evaluate_permit_checklist

    report = run(load_plan(CATLIN_DIR).plan, CATLIN_DIR, tier=None)
    checklist = evaluate_permit_checklist(report, "mn-2024")
    # code.energy_prescriptive used to report UNKNOWN here because SL-B-FLOOR/SL-M-DECK had
    # no authored assembly. Every slab now either carries one or is scoped out of the
    # prescriptive table for a stated reason (the main-floor deck has conditioned space on
    # both faces; the garage slab floors an unheated detached structure), so the gate is
    # fully evaluated. It must stay that way: an UNKNOWN reappearing means a component lost
    # its thermal input again, which is exactly what this item exists to catch.
    #
    # The plumbing pass (2026-07-29) put eight more checks on this checklist. Two of the
    # resulting items sat UNKNOWN for a day on one open design decision — FX-1, the
    # mechanical-room utility sink, had no routed drain, and could not have one by gravity
    # while the basement main hung at the ceiling 6'-6" above the slab it stands on. That is
    # settled: the sewer connection is below the slab (Minnesota buries them under frost), so
    # the main now drops through SP-B-SLAB-MAIN and runs under the slab out beneath FT-B-S1,
    # and FX-1 drains and vents. Every declared item is evaluated and passes again.
    #
    # Scoped to the *gating* items: the code-coverage expansion added a staging lane of
    # encoded-but-not-yet-gating rules (PermitItemSpec.blocking), and those are allowed to
    # sit UNKNOWN against a house authored before they existed. What must never regress is
    # the gate itself — an item that gates today and stops passing tomorrow.
    # tests/test_permit_gate_catlin.py pins the size of that lane so it cannot grow.
    #
    # ONE gating item is UNKNOWN and is pinned rather than waived. "Foundation frost depth"
    # became evaluable-against-the-real-condition on 2026-08-22, when `structural.frost_depth`
    # stopped comparing every footing to a single global grade plane and started deriving a
    # local one. It found four house footings with 8" of cover — and one with 2" of NEGATIVE
    # cover — below the sunken garden's floor; those are answered, by the R403.3 wings under
    # the garden slab, and they pass. It also found the garden's OWN seven footings 12"-21"
    # below the floor of the court they retain. Those are not a table's business: a structure
    # holding up the hole it stands in is an engineered design under IRC R404.4, which is
    # where `structural.foundation_unbalanced_fill` already sends the same five walls. The
    # honest checklist entry for a permit set is therefore "engineered — see the consultant's
    # drawings", not a green tick.
    #
    # Pinned tightly on purpose: any OTHER gating item regressing still fails this test, and
    # so does this one changing shape.
    gating = [item for item in checklist.items if item.blocking]
    unresolved = [item for item in gating if item.result is not Result.PASS]
    assert [item.label for item in unresolved] == ["Foundation frost depth"], \
        [(item.label, item.result, item.detail) for item in unresolved]
    assert unresolved[0].result is Result.UNKNOWN
    assert "R404.4" in unresolved[0].detail


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
    # Dim enough to stay obviously reference-only, dark enough to read at 110 dpi. 0.16 was
    # invisible in a `haus render` snapshot, which is the one place the underlay has a job.
    assert all(0.0 < item.opacity <= 0.35 for item in underlays)


def test_catlin_underlays_are_calibrated_to_the_source_svg_grid():
    """All four pages are 1280x1920 on the vector twins' own 74.7029 px/m grid.

    The extent is therefore identical on every page and only the origin differs; a table
    that disagrees is a mis-calibration, which makes the underlay useless as a ruler.
    """
    from typehaus.checks import load_preferences

    px_per_m = 74.7029
    for item in load_preferences(CATLIN_DIR).underlays:
        assert item.width_m == pytest.approx(1280 / px_per_m, abs=0.001)
        assert item.height_m == pytest.approx(1920 / px_per_m, abs=0.001)
        assert item.rotation_deg == 0.0
    by_storey = {item.storey: item for item in load_preferences(CATLIN_DIR).underlays}
    # SW corner of each page's wall-fill polygon, measured off the .svg (see preferences.toml).
    for storey, origin in (("basement", (-3.1807, -12.3580)), ("main", (-2.9769, -4.7410)),
                           ("second", (-3.0595, -9.0316)), ("attic", (-3.0382, -8.0507))):
        assert (by_storey[storey].origin_x_m,
                by_storey[storey].origin_y_m) == pytest.approx(origin, abs=0.001)


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
            # PLANT_INT_2X6_BRG_HUMID is the same 2x6 bearing line with the plant room's
            # humid liner on its west face (2026-08-18) — a finish decision on one segment,
            # not a break in the stack, so it counts toward the run like any other segment.
            if w.storey == storey
            and w.assembly in ("CATLIN_INT_2X6_BRG", "PLANT_INT_2X6_BRG_HUMID")
            and abs(w.axis[0][0] - center_x) < 1e-6 and abs(w.axis[1][0] - center_x) < 1e-6
        ]
        assert segments, storey
        length = sum(
            abs(w.axis[1][1] - w.axis[0][1]) + abs(w.axis[1][0] - w.axis[0][0])
            for w in segments
        )
        # The second storey carries 8'-6" of that line as BM-S-HALL — three plies of
        # 11-7/8" LVL over the open hall/landing/stair — rather than as studs. The stack
        # is still continuous gable to gable; part of it is just a beam.
        for solid in catlin_model.solids:
            if solid.category != "beam" or solid.storey != storey:
                continue
            xs = [x for x, _ in solid.outline]
            # On the line means straddling it *and* running along it (a beam that merely
            # crosses x=18' contributes none of its length to this run).
            if not min(xs) - 1e-6 <= center_x <= max(xs) + 1e-6:
                continue
            if max(xs) - min(xs) > ft(1).meters:
                continue
            ys = [y for _, y in solid.outline]
            # ...and inside the house: the sunken garden's balcony beams share this storey
            # and this x, but they are a separate structure south of the south wall.
            if min(ys) < -1e-6 or max(ys) > ft(HOUSE_SIZE_FT).meters + 1e-6:
                continue
            length += max(ys) - min(ys)
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
    # eave_z_m is the deck plane: knee-wall plate top + the I-joist's rise above it.
    assert eave_ft == pytest.approx(ATTIC_ELEV_FT + KNEE_FT + DECK_RISE_FT)
    # The old builder set the roof out from the bearing-wall axes, giving an 11' ridge over
    # a 36' run. A zero-overhang roof that stops at the axis leaves the cladding standing
    # proud of its own edge, so the footprint now laps the outermost wall layer — the run,
    # and with it the ridge, grows by that lap on each side. The whole plane also rides
    # DECK_RISE_FT higher now that the eave is the deck. The 4:12 pitch is unchanged.
    lap = _cladding_lap(catlin_model)
    assert ATTIC_ELEV_FT + RIDGE_OVER_ATTIC_FT + DECK_RISE_FT < ridge_ft <= \
        ATTIC_ELEV_FT + RIDGE_OVER_ATTIC_FT + DECK_RISE_FT + (lap / 3.0) / ft(1).meters + 1e-6
    assert roof.ridge_direction == "y"
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    for span in (max(xs) - min(xs), max(ys) - min(ys)):
        assert ft(HOUSE_SIZE_FT).meters < span <= ft(HOUSE_SIZE_FT).meters + 2 * lap + 1e-6
    rise_over_run = (roof.ridge_z_m - roof.eave_z_m) / ((max(xs) - min(xs)) / 2)
    assert rise_over_run == pytest.approx(4.0 / 12.0)
    rafters = [member for member in roof.members if member.category == "rafter"]
    # 28 station lines at 16" o.c. over two gable planes: stations span the bearing walls'
    # 36' extent (not the cladding-lapped footprint), with the end stations inset half a
    # member width so end rafters sit fully inside the gable wall planes.
    assert len(rafters) == 56
    flange_half = cross_section("11.875 I-joist").width_m / 2.0
    stations = sorted({round(member.p0[1], 6) for member in rafters})
    assert stations[0] == pytest.approx(flange_half, abs=1e-6)
    assert stations[-1] == pytest.approx(ft(HOUSE_SIZE_FT).meters - flange_half, abs=1e-6)
    # The rafter sinks only the birdsmouth below the plate top — never its full depth.
    plate_top = ft(ATTIC_ELEV_FT + KNEE_FT).meters
    birdsmouth = inch(3.5 / 3.0).meters
    assert all(member.z0_m >= plate_top - birdsmouth - 1e-6 for member in rafters)
    # WP4: rafter ridge ends are trimmed back to bear on the ridge beam rather than
    # crossing to the exact ridge centerline — z1_end drops by half the beam width
    # times the roof slope, staying on the roof plane.
    beam_width_m = cross_section(RIDGE_BEAM_DEFAULT).width_m
    expected_z1_end = roof.ridge_z_m - (4.0 / 12.0) * (beam_width_m / 2.0)
    assert all(member.z1_end_m == pytest.approx(expected_z1_end) for member in rafters)
    assert all(member.connection == "ridge:adjustable-slope-hanger;eave:birdsmouth"
              for member in rafters)
    # The depth is no longer spelled into the connection string: it is the seat's run times
    # the rafter's slope, and the notch is part of the rafter's own solid.
    assert all(member.seat is not None for member in rafters)


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


def test_house_roof_bearing_datum_seat_cuts_and_layer_setbacks(catlin_model):
    """Step 1/3 acceptance (golden eave detail): bearing_z_m is the plate top, the rafter is
    notched at the bearing (not above the deck), and every above-structure roof layer carries
    a per-edge setback stepping deck >= foam >= batten >= metal."""
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    authored = catlin_model.plan.by_tag("RF-HOUSE")
    plate_top = max(catlin_model.wall(tag).z1_m for tag in authored.bearing_refs)
    assert roof.bearing_z_m == pytest.approx(plate_top)
    # eave rides the deck plane, ~10.04" (0.2551 m) above the plate.
    assert roof.eave_z_m - roof.bearing_z_m == pytest.approx(ft(DECK_RISE_FT).meters)

    # 1.917" = the 4:12 rise over the horizontal distance from the footprint edge to the
    # heel. It has deepened three times, every time by the same arithmetic: the zero-overhang
    # roof laps the CLADDING, so the rafter tail and the deck plane above it follow the
    # cladding face out and the notch deepens by the move times 4/12. 1.17" under the
    # rigid-CI stack; 1.333" from 2026-08-23, when the Swinburne truss moved the face 0.48";
    # 1.667" when the catlin truss moved it a further 1.0"; 1.917" since the exposed-fastener
    # PBR panel moved it 0.75" more (2026-08-26, 0.75 x 4/12 = 0.25").
    birdsmouth = inch(1.917).meters
    rafters = [m for m in roof.members if m.category == "rafter"]
    assert not [m for m in roof.members if m.category == "seat_cut"], \
        "the seat is part of the rafter's own solid now, not a block beside it"
    bearing_x = sorted({catlin_model.wall(tag).axis[0][0] for tag in authored.bearing_refs})
    for rafter in rafters:
        seat = rafter.seat
        assert seat is not None
        assert seat.plate_top_z_m == pytest.approx(plate_top)
        # Anchored at the rafter's plumb-cut tail — the bearing wall's stud exterior face,
        # one sheathing thickness inboard of the sheathing-ext axis (the reference seat spans
        # exactly the stud depth from there) — not out in the cladding lap. The heel sits one
        # seat run inboard of that.
        heel_offset = min(abs(seat.heel[0] - x) for x in bearing_x)
        assert abs(heel_offset - inch(0.5).meters) <= seat.seat_run_m + 1e-6

        # The notch: the rafter's solid has a flat seat at the plate top over the run, and a
        # plumb heel rising to the underside — one birdsmouth's worth, once.
        solid = member_solid(rafter)
        zs = sorted(round(z, 9) for (_x, _y, z) in solid.profile)
        assert zs[0] == pytest.approx(plate_top)
        assert zs[1] == pytest.approx(plate_top)
        heel_height = zs[2] - plate_top
        assert heel_height == pytest.approx(birdsmouth, abs=1e-3)

    setbacks = {entry["layer"]: entry for entry in roof.layer_edge_setbacks}
    assert set(setbacks) == {"zip", "deck-vb", "polyiso-1", "polyiso-2",
                             "top-deck", "underlayment", "vent-mat", "roofing"}
    for edge in ("west", "east", "south", "north"):
        deck, foam = setbacks["zip"][edge], setbacks["polyiso-1"][edge]
        batten, metal = setbacks["top-deck"][edge], setbacks["roofing"][edge]
        assert deck >= foam >= batten >= metal
        # Wall stack per the reference: the deck clips at the wall-sheathing face (the whole
        # catlin-truss stand-off plus the cladding), metal runs 0.6" proud of the mount
        # plane. 0.02 + 2 + 2 + 0.5 + 0.5 = 5.02" for the rigid-CI stack, 5.5" for the
        # Swinburne truss, 6.5" when the catlin truss laid four flat layers where the
        # outrigger band was, and 7.25" since the 1 1/4" exposed-fastener PBR panel replaced
        # the 1/2" snap-lock seam (2026-08-26).
        assert deck == pytest.approx(inch(1.5 + 1.5 + 1.0 + 0.5 + 1.5 + 1.25).meters)
        # The cladding + the 2" vented cavity the roof's foam clears. It was 1/2" + 1/2" of
        # furring under the rigid-CI stack, and 1/2" + a 1" vent under the Swinburne truss
        # (whose 3-1/2" band was 2-1/2" packed with foam). The catlin truss's cavity is the
        # 1/2" gap PLUS the 1-1/2" between girt courses — ``accessories.rainscreen_band``
        # reads both, and this is the number that follows it. The cladding term grew 3/4"
        # with the panel, and the cavity behind it did not move.
        assert foam == pytest.approx(inch(3.25).meters)
        # The batten/top-deck plane clips at the CLADDING face, so it is the cladding
        # thickness and nothing else — 1/2" while the wall wore a snap-lock pan, 1-1/4"
        # since the PBR panel (2026-08-26). It moves with the panel and never with the
        # stand-off behind it.
        assert batten == pytest.approx(inch(1.25).meters)
        assert metal == pytest.approx(inch(-0.1).meters)
        # The nailbase deck is the case that made _layer_group position-aware (2026-08-20).
        # It is a SHEATHING layer like the ZIP below the foam, but it stands where a vented
        # roof's battens stood, so it must clip with the battens and not inherit the deck's
        # 5.02" — which would leave the top deck standing proud of its own roofing.
        assert setbacks["top-deck"][edge] == setbacks["vent-mat"][edge]
        assert setbacks["top-deck"][edge] < setbacks["zip"][edge]
        # Both foam courses are one plane: they are two layers to say the seams stagger,
        # not two positions.
        assert setbacks["polyiso-1"][edge] == setbacks["polyiso-2"][edge]
        # The deck vapour barrier is under the foam, so it rides the ZIP, not the top deck.
        assert setbacks["deck-vb"][edge] == setbacks["zip"][edge]
    # The garage/truss roof is deferred: no setbacks, geometry unchanged.
    garage = next(r for r in catlin_model.roofs if r.tag == "RF-GARAGE")
    assert garage.layer_edge_setbacks == ()


def test_catlin_roof_passes_the_monthly_condensation_gate_with_margin():
    """The hot roof must clear the monthly (ISO 13788-style) condensation gate — the
    pass/fail verdict, not just the cold-snap screen — and carry a whole-assembly
    R >= 50, both read off the resolved model rather than pinned to authored numbers."""
    from typehaus.analysis import assembly_r_value
    from typehaus.checks.building_science.condensation import CHECK_ID

    plan = load_plan(CATLIN_DIR).plan
    report = run(plan, CATLIN_DIR, tier=None)
    gate = [f for f in report.findings
            if f.check_id == CHECK_ID and "CATLIN_ROOF" in f.element_tags]
    assert gate, "the condensation gate never evaluated CATLIN_ROOF"
    assert all(f.result is Result.PASS for f in gate), [f.message for f in gate]

    r = assembly_r_value(plan.library.resolve_assembly("CATLIN_ROOF"), plan.library)
    assert r.value is not None and not r.unknown_materials
    assert r.value.r_us >= 50.0


def test_garage_gable_roof_frames_raised_heel_trusses(catlin_model):
    """The garage roof is framed as raised-heel trusses: top + bottom chords, web members,
    and a raised heel at each eave bearing. A truss carries its own ridge, so it needs no
    authored ridge Beam and must not raise the ridge_support advisory."""
    garage_roof = next(r for r in catlin_model.roofs if r.tag == "RF-GARAGE")
    categories = {m.category for m in garage_roof.members}
    assert {"top_chord", "bottom_chord", "truss_web", "truss_heel"} <= categories
    assert "ridge_beam" not in categories
    # The raised heel lifts the top chord above the plate at the bearing.
    heels = [m for m in garage_roof.members if m.category == "truss_heel"]
    assert heels and all(m.z1_m - m.z0_m > 0.2 for m in heels)  # ~9.25" energy heel
    _, resolve_findings = resolve(load_plan(CATLIN_DIR).plan)
    ridge = [f for f in resolve_findings if f.check_id == "structural.ridge_support"]
    assert not [f for f in ridge if f.element_tags == ("RF-GARAGE",)]
    assert not [f for f in ridge if f.severity.value == "error"]


def test_attic_to_roof_walls_frame_with_raked_studs_and_plates(catlin_model):
    """The gable ends are true raked walls, not 11' rectangular placeholders."""
    gable = next(w for w in catlin_model.walls if w.tag == "W-A-S1")
    # Knee height above the attic floor plus the deck rise (eave_z_m is the deck plane),
    # plus the roof plane's cladding lap (see test_roof_matches_old_pitch_knee_and_ridge).
    knee = ft(5 + DECK_RISE_FT).meters + ft(ATTIC_ELEV_FT).meters
    assert knee < gable.top_z0_m <= knee + _cladding_lap(catlin_model) / 3.0 + 1e-6
    assert gable.top_z1_m > gable.top_z0_m
    studs = [member for member in gable.members if member.category == "stud"]
    assert len(studs) >= 2
    assert max(member.z1_m for member in studs) > min(member.z1_m for member in studs)
    assert any(member.category == "raked_plate" for member in gable.members)


def test_floors_get_two_rim_boards_at_the_outer_bearing_lines(catlin_model):
    """WP3: rim (band) joists cap the deck ends, one per outermost bearing line.

    Since 2026-08-21 the second floor is two systems (FS-S-WEST/FS-S-EAST), so it
    carries four rims across the storey rather than FS-SECOND's two.
    """
    for tag in ("FS-S-WEST", "FS-S-EAST", "FS-ATTIC"):
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


def test_opening_framing_registers_with_the_opening_it_frames(catlin_model):
    """Every rough sill's top face and every header's underside land ON the hole.

    The framing solver hands ``frame_opening`` the stud bearing line — the top of the
    bottom plate — and until 2026-08-25 that value was used for two different jobs: where
    a jack bears (right) and what a ``sill_m`` is measured from (wrong). ``base_ref_z_m``
    is the sill datum, and every other consumer already read it — the wall body's cut, the
    buck, the ladder blocking, the furring cuts, the IFC void, the elevations — so the
    stud wall alone framed 1 1/2" high. The rough sill was flipped on top of that: emitted
    upward from the sill line instead of hanging under it, which put it 3" into the
    opening and left a plank of 2x6 lying across the glass of every window in the house.

    Nothing checked the two against each other, which is why it shipped. This does.
    """
    plate_h = inch(1.5).meters
    checked = 0
    for wall in catlin_model.walls:
        members = [m for m in catlin_model.all_members() if m.parent_uid == wall.uid]
        if not any(m.category in ("plate", "stud") for m in members):
            continue  # concrete, brick, strapping-only: no stud pack to register
        openings = [o for o in catlin_model.openings if o.host_wall == wall.tag]
        heads = sorted(wall.base_ref_z_m + o.sill_m + o.height_m for o in openings)
        # A rough sill only exists where the opening leaves room for one under it: a cased
        # opening running to the floor has the bottom plate as its sill and gets no member.
        sills = sorted(wall.base_ref_z_m + o.sill_m for o in openings
                       if not o.is_door
                       and wall.base_ref_z_m + o.sill_m - plate_h
                       > wall.base_ref_z_m + plate_h + 1e-9)
        got_sills = sorted(m.z1_m for m in members if m.category == "sill")
        got_heads = sorted(m.z0_m for m in members
                           if m.category == "header" or m.child_key.startswith("roughhead-"))
        assert got_sills == pytest.approx(sills, abs=1e-9), \
            f"{wall.tag}: rough sill tops do not land on their openings' sill lines"
        for head in got_heads:
            assert any(head == pytest.approx(h, abs=1e-9) for h in heads), \
                f"{wall.tag}: a header/head nailer at {head} sits on no opening's head"
        # The sill hangs *below* the line it carries, one plate deep.
        for member in members:
            if member.category != "sill":
                continue
            assert member.z1_m - member.z0_m == pytest.approx(plate_h, abs=1e-9)
        checked += len(openings)
    assert checked > 75, "the whole plan's openings, not a handful"


def test_raked_gable_king_studs_match_roof_plane_at_own_station(catlin_model):
    """WP0: king-stud tops on a raked wall follow the roof line at their own plan
    position. A prior bug reused the last regular stud's leftover top for every
    king on the wall, regardless of the opening's actual station."""
    # The two raked north gables: W-A-N1 (WIN-A-N2) and W-A-N2 (WIN-A-N1), each a 30" RO
    # that breaks a stud and so pulls in a header, jacks and kings. The south gables used
    # to be the subject here, but the 2026-07-30 facade pass moved them to the 14" family
    # — a 14" RO fits a stud bay unbroken and frames with no header and no kings at all,
    # leaving nothing on those walls for this rule to bite on. The north gables rake
    # 6'-0" over their 18', so a single window's two kings land at clearly different
    # heights, which is all this regression needs.
    plate_h = inch(1.5).meters
    top_plates = 2  # CATLIN_EXT_2X6 double top plate, not advanced framing
    checked = 0

    for tag in ("W-A-N1", "W-A-N2"):
        wall = next(w for w in catlin_model.walls if w.tag == tag)
        assert wall.top_z0_m is not None and wall.top_z1_m is not None
        (x0, y0), (x1, y1) = wall.axis
        axis_len = math.hypot(x1 - x0, y1 - y0)
        dx, dy = (x1 - x0) / axis_len, (y1 - y0) / axis_len

        kings = [m for m in wall.members if m.category == "king"]
        assert len(kings) >= 2, tag  # one window, at least one king per side

        for king in kings:
            px, py = king.p0
            # Project onto the wall axis direction (king.p0 sits on the structure-layer
            # centerline, offset perpendicular from the datum axis — hypot would pick up
            # that perpendicular offset and skew the station).
            s = (px - x0) * dx + (py - y0) * dy
            fraction = s / axis_len
            expected = (wall.top_z0_m + (wall.top_z1_m - wall.top_z0_m) * fraction
                        - plate_h * top_plates)
            assert king.z1_m == pytest.approx(expected, abs=1e-6), tag

        # Kings flanking the opening sit at different stations, so their tops must
        # differ — exactly what the leftover-loop-variable bug broke.
        tops = {round(k.z1_m, 6) for k in kings}
        assert len(tops) > 1, tag
        checked += 1

    assert checked == 2


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
    # W-M-W1B carries the actual NW corner now (2026-07-28, RM-M-MECH's shaft closet split
    # W-M-W1 at N-M-MECH1, well south of N-M-NW).
    for tag in ("W-M-S1", "W-M-E1", "W-M-N1", "W-M-W1B"):
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
    # **No exceptions, and that is the point of the assertion (2026-08-25).** This list
    # carried three until the exterior assembly took its stud module from the layout line
    # instead of from each wall's own start node: WIN-S-BATH-N, whose 7'-8" segment could
    # not put the RO on a bay centre and still clear `integrity.opening_fits`'s 2" edge
    # minimum, and the attic juliet pair, 3" off since the 2026-08-24 one-sided widening.
    # Every one of the three was the same defect wearing a different hat — a wall segment
    # laying out from a node that happens to sit off 16" — so unifying the grid dissolved
    # all three rather than fixing them one at a time. 20 windows moved 3"-8" to get here;
    # `houses/catlin/plan/assemblies.py` (LAYOUT_ORIGIN) has the ledger.
    #
    # Keep this empty. An exception here is now evidence of a genuinely constrained wall,
    # not of an accident of authoring order, and deserves the argument written out.
    assert not findings, [finding.message for finding in findings]


def test_the_attic_south_juliet_pair_straddles_the_ridge_at_full_unclipped_height(catlin_model):
    """The gable peak's composition: two 24x64 casements symmetric about the x=18' ridge.

    Every number here is load-bearing on the design. The rake is what makes this worth
    pinning: ``resolve/geometry_openings.py`` *shortens* an opening that runs into the roof
    underside rather than erroring, so "the head still lands at 8'-0"" is a claim that has
    to be asserted rather than assumed from the authored type height.
    """
    west = next(item for item in catlin_model.openings if item.tag == "WIN-A-S-JUL-W")
    east = next(item for item in catlin_model.openings if item.tag == "WIN-A-S-JUL-E")

    # W-A-S2 starts at N-A-S1 (x 10'), W-A-S3 at N-A-S2 (x 18'), and since 2026-08-25 both
    # take their module from the layout line rather than from those nodes, so the stud lines
    # here are the house grid itself: x 16'-0", 17'-4", 18'-8", 20'-0".
    #
    # The centres sat on 16'-8"/19'-4" until the 2026-08-24 widening 18" -> 24" pushed them
    # OUTWARD ONLY to 16'-5"/19'-7" — the inboard jambs being held by the bearing pier — and
    # left both 3" off a stud line, the house's one knowingly-off-module pair. The line
    # origin retired that exception: 16'-0"/20'-0" are stud lines on the unified grid, 5"
    # further out, so each RO breaks exactly one stud again and the pair is back on module
    # with no width change. What never moved through any of it is the mirror about the
    # ridge, which is the gable rule that governs this composition.
    assert west.host_wall == "W-A-S2"
    assert east.host_wall == "W-A-S3"
    assert west.center_along_m == pytest.approx(ft(6).meters, abs=1e-6)
    assert east.center_along_m == pytest.approx(ft(2).meters, abs=1e-6)
    west_x = ft(10).meters + west.center_along_m
    east_x = ft(18).meters + east.center_along_m
    assert west_x == pytest.approx(ft(16).meters, abs=1e-6)
    assert east_x == pytest.approx(ft(20).meters, abs=1e-6)
    assert ft(18).meters - west_x == pytest.approx(east_x - ft(18).meters, abs=1e-9)
    # Each RO now sits centred on its own stud line with a full clear bay to the next one
    # out (17'-4" west, 18'-8"... east reads 21'-4"), so one stud breaks and no jamb crowds
    # a neighbour — the 1/4" squeeze the outward-only widening had left is gone.
    assert west_x - inch(12).meters == pytest.approx(ft(15).meters, abs=1e-6)
    assert east_x + inch(12).meters == pytest.approx(ft(21).meters, abs=1e-6)

    for opening in (west, east):
        # The storey-wide south sill line, held here deliberately — and 8" above the 24"
        # R312.2 fall-protection trigger, which is why this pair reads as a juliet balcony
        # while needing no guard.
        assert opening.sill_m == pytest.approx(ft(2, 8).meters, abs=1e-6)
        assert opening.sill_m > inch(24).meters
        # Unclipped: the rake did not silently eat the head.
        assert opening.height_m == pytest.approx(inch(64).meters, abs=1e-6)
        assert opening.sill_m + opening.height_m == pytest.approx(ft(8).meters, abs=1e-6)
        assert opening.width_m == pytest.approx(inch(24).meters, abs=1e-6)

    # The clear pier between the two ROs, centred on W-A-C1 / the RB-HOUSE south bearing
    # point: W-A-C1's 5-1/2" stud body plus a jack and king each side is 11-1/2", so 14"
    # carries the bearing with 2-1/2" to spare. It is also the composition's mullion, and
    # between the two it is what forbids the pair from growing INWARD — which is why the
    # 2026-08-24 widening is one-sided. Unchanged by that widening, and asserted here so a
    # future "just make them a bit wider" cannot quietly spend it.
    pier = (east_x - inch(12).meters) - (west_x + inch(12).meters)
    assert pier == pytest.approx(inch(24).meters, abs=1e-6)
    # 14" is the requirement — W-A-C1's 5-1/2" stud body plus a jack and king each side is
    # 11-1/2". The pair moving back onto the grid spent its 5" of outward travel here, so
    # the clear pier is 24" and the bearing has 12-1/2" to spare rather than 2-1/2".
    assert pier >= inch(14).meters

    report = run(load_plan(CATLIN_DIR).plan, CATLIN_DIR, tier=None)
    # `integrity.opening_fits` is a hard gate and stays clean. `window_framing_module` is an
    # ADVISORY, and between 2026-08-24 and 2026-08-25 the pair failed it by the 3" the
    # one-sided widening cost — the house's one accepted off-module window. The line-based
    # stud module retired that exception rather than the pair moving: on a grid shared by the
    # whole south line, 16'-0"/20'-0" ARE stud lines. Both checks are clean now, and the
    # advisory is asserted clean so a future re-phase cannot quietly reintroduce the debt.
    offenders = [finding for finding in report.findings
                 if finding.check_id == "integrity.opening_fits"
                 and finding.result is Result.FAIL
                 and ("WIN-A-S-JUL-W" in finding.message or "WIN-A-S-JUL-E" in finding.message)]
    assert not offenders, [finding.message for finding in offenders]
    advisories = [finding for finding in report.findings
                  if finding.check_id == "structural.window_framing_module"
                  and finding.result is Result.FAIL
                  and ("WIN-A-S-JUL-W" in finding.message or "WIN-A-S-JUL-E" in finding.message)]
    assert not advisories, [finding.message for finding in advisories]


def _opening_plan_y(model, tag):
    """World y of an opening's RO centre, walked along its host wall's axis.

    ``center_along_m`` is measured from the host's *start* node, which is the whole point
    of these two tests: a segment lays its studs from that node, so where a window can
    legally sit is a property of the node, not of the facade.
    """
    opening = next(item for item in model.openings if item.tag == tag)
    wall = model.wall(opening.host_wall)
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0)
    return y0 + (y1 - y0) * (opening.center_along_m / length), opening


def _framing_offenders(tags):
    """Re-run opening/module/safety gates and keep only failures naming one of ``tags``."""
    report = run(load_plan(CATLIN_DIR).plan, CATLIN_DIR, tier=None)
    return [finding.message for finding in report.findings
            if finding.check_id in ("structural.window_framing_module",
                                    "integrity.opening_fits",
                                    "code.R308_4_safety_glazing")
            and finding.result is Result.FAIL
            and any(tag in finding.message for tag in tags)]


def test_the_west_facade_stacks_five_two_storey_window_columns(catlin_model):
    """Five exact lower columns and mirrored attic caps.

    Four until 2026-08-25, when the assembly took its stud module from the layout line.
    The fifth was the face's one broken column: W-S-W1's grid had re-phased out from under
    WIN-S-BATH-W on 2026-08-21 when the mechanical chase moved N-S-CH3, and the window rode
    3 1/8" south to the bay centre that move created rather than break a stud. With one grid
    for the whole line there is no per-segment phase left to drift, so it returns to 31'-4"
    under WIN-M-MUD. The other four shifted 4" together, which is the whole face re-hanging
    on the house grid — same rhythm, same pairs, one datum.
    """
    columns = {
        ft(5, 4).meters: ("WIN-M-BED-W1", "WIN-S-PLANT3"),
        ft(10, 8).meters: ("WIN-M-BED-W2", "WIN-S-SUITE1"),
        ft(20).meters: ("WIN-M-BATH2", "WIN-S-SUITE2"),
        ft(24, 8).meters: ("WIN-M-BATH1-W", "WIN-S-VANITY-W"),
        ft(31, 4).meters: ("WIN-M-MUD", "WIN-S-BATH-W"),
    }
    for expected_y, (main_tag, second_tag) in columns.items():
        main_y, main = _opening_plan_y(catlin_model, main_tag)
        second_y, second = _opening_plan_y(catlin_model, second_tag)
        assert main_y == pytest.approx(expected_y, abs=1e-6), main_tag
        assert second_y == pytest.approx(expected_y, abs=1e-6), second_tag
        # A column is only a column if the units match, not just their centrelines.
        assert main.width_m == pytest.approx(second.width_m, abs=1e-6), (main_tag, second_tag)
        # One 6'-0" head line carries the whole face — the 27" units off a 3'-0" sill and
        # the 14" units off 4'-0" (CLAUDE.md, Facade rules / Head lines).
        for opening in (main, second):
            assert opening.sill_m + opening.height_m == pytest.approx(ft(6).meters, abs=1e-6), \
                opening.tag

    vanity_y, vanity = _opening_plan_y(catlin_model, "WIN-S-VANITY-W")
    bath_y, bath = _opening_plan_y(catlin_model, "WIN-M-BATH1-W")
    assert vanity_y == pytest.approx(ft(24, 8).meters, abs=1e-6)
    assert bath_y == pytest.approx(ft(24, 8).meters, abs=1e-6)
    assert vanity.host_wall == "W-S-W2" and vanity.type_ref == "WT-1424-T"
    assert bath.host_wall == "W-M-W2" and bath.type_ref == "WT-1424-T"

    attic_south_y, attic_south = _opening_plan_y(catlin_model, "WIN-A-W-S")
    attic_north_y, attic_north = _opening_plan_y(catlin_model, "WIN-A-W-N")
    assert attic_south_y == pytest.approx(ft(4, 8).meters, abs=1e-6)
    assert attic_north_y == pytest.approx(ft(31, 4).meters, abs=1e-6)
    assert attic_south_y + attic_north_y == pytest.approx(ft(36).meters, abs=1e-6)
    assert attic_south.width_m == pytest.approx(attic_north.width_m, abs=1e-6)

    # The recovered column, asserted as a pair rather than as two separate stations: the
    # 3 1/8" that used to sit between them was the per-segment phase drift, and there is no
    # longer a mechanism that could reopen it without moving both.
    mud_y, _mud = _opening_plan_y(catlin_model, "WIN-M-MUD")
    second_bath_y, _second_bath = _opening_plan_y(catlin_model, "WIN-S-BATH-W")
    assert mud_y == pytest.approx(ft(31, 4).meters, abs=1e-6)
    assert second_bath_y == pytest.approx(mud_y, abs=1e-6)

    # The ladder backing at W-S-W3's tee is COMPLETE again (2026-08-25). WIN-S-SUITE1's
    # header used to cross the top rung, and opening framing owns that volume, so the solver
    # dropped the one nonstructural block and this test pinned the hole. The 4" the window
    # moved to reach the line's grid took the header off the rung, and the rung came back —
    # a second-order win worth asserting, because a future window move could re-open it.
    suite_wall = catlin_model.wall("W-S-W3")
    suite_wall_member_keys = {member.child_key for member in suite_wall.members}
    assert "header-0" in suite_wall_member_keys
    assert {"tee-N-S-W3-block-00", "tee-N-S-W3-block-01",
            "tee-N-S-W3-block-02", "tee-N-S-W3-block-03"} <= suite_wall_member_keys

    column_tags = [tag for pair in columns.values() for tag in pair]
    assert not _framing_offenders(column_tags)


def test_the_east_second_storey_window_row_mirrors_about_the_house_centreline(catlin_model):
    """4'-0" / 13'-4" / 22'-8" / 32'-0" — 4+32 = 13'-4"+22'-8" = 36'-0", exactly.

    The row it replaced ran a perfectly even 9'-0" beat that sat 10" north of centre: 5'-4"
    of wall at the south end against 3'-8" at the north. An even beat is invisible; a 20"
    asymmetry on a 36'-0" face is not. Width and head mirror too, on one 3'-0" sill, so the
    two halves are the same picture — that is the claim, and it is pinned in all three
    dimensions because holding only the stations would let a retype break it silently.

    The inner pair moved 4" outward on 2026-08-25 with the line-based stud module, and the
    row got *more* regular for it: the beat is now 9'-4" three times over, even and centred
    at once, where 4/13/23/32 was centred with a 9'-0"/10'-0"/9'-0" beat.

    Later the same day the inner pair went 30x48 -> 27x54 (WT-2754): the east wall is
    BEARING, so it takes the 27" rung of the RO ladder, and R303.1's area had to be bought
    back in height. Every claim above survived it unchanged — same stations, same mirror,
    same 3'-0" sill, same equal widths and equal heads within the pair — because the width
    came off both jambs symmetrically (``from_node`` is the NEAR jamb, so both authored
    offsets moved +1 1/2", half of the 3" lost). Only the inner head reads 7'-6" now
    instead of 7'-0". That is the test earning its keep: it let the narrowing through and
    caught the one thing the narrowing actually moved.
    """
    house = ft(36).meters
    pairs = (("WIN-S-STUDY3", "WIN-S-BED3", ft(4).meters),
             ("WIN-S-BED1", "WIN-S-BED2", ft(13, 4).meters))
    tags = []
    for south_tag, north_tag, expected_south_y in pairs:
        south_y, south = _opening_plan_y(catlin_model, south_tag)
        north_y, north = _opening_plan_y(catlin_model, north_tag)
        tags += [south_tag, north_tag]
        assert south_y == pytest.approx(expected_south_y, abs=1e-6), south_tag
        assert south_y + north_y == pytest.approx(house, abs=1e-6), (south_tag, north_tag)
        assert south.width_m == pytest.approx(north.width_m, abs=1e-6)
        assert south.sill_m == pytest.approx(ft(3).meters, abs=1e-6)
        assert north.sill_m == pytest.approx(ft(3).meters, abs=1e-6)
        assert (south.sill_m + south.height_m
                == pytest.approx(north.sill_m + north.height_m, abs=1e-6))

    # And the row really is a row: the outer pair reads 6'-0" at the head, the inner 7'-6",
    # so the composition steps up toward the middle rather than wandering.
    #
    # The inner head was 7'-0" until 2026-08-25 and moved with the 27" bearing cap, not for
    # a compositional reason: W-S-E2/E3 are BEARING, the bearing rung of the RO ladder is
    # 27", and BED1/BED2 are single-window rooms where R303.1 binds on AREA — so the 3" of
    # width had to come back as 6" of height (30x48 -> 27x54) or the rooms fail R303.1:
    # 27x48 is 9.00 sf against BED2's 9.945 sf requirement, 27x54 is 10.125 sf.
    # The step-up this pins is therefore still the claim; only its size changed. Pinned
    # exactly, because the whole point of this test is that a retype cannot move the
    # picture silently.
    heads = {tag: _opening_plan_y(catlin_model, tag)[1].sill_m
                  + _opening_plan_y(catlin_model, tag)[1].height_m
             for tag in tags}
    assert heads["WIN-S-STUDY3"] == pytest.approx(ft(6).meters, abs=1e-6)
    assert heads["WIN-S-BED1"] == pytest.approx(ft(7, 6).meters, abs=1e-6)

    assert not _framing_offenders(tags)


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
        layer.model_copy(update={"thickness": inch(3)}) if layer.name == "spray-foam" else layer
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
                if finding.check_id in ("code.R314_R315_alarms", "code.R315_garage_alarms")
                and finding.result is Result.FAIL]
    model, _ = resolve(plan)
    alarms = model_to_dict(model)["alarms"]
    assert {alarm["tag"] for alarm in alarms} >= {"AL-M-BED", "AL-M-HALL", "AL-S-HALL",
                                                  "AL-G-HEAT"}
    # The garage detector is a heat head, not a smoke alarm — a smoke head there would
    # nuisance-trip on exhaust, dust and outdoor temperature.
    garage = next(alarm for alarm in alarms if alarm["tag"] == "AL-G-HEAT")
    assert garage["kind"] == "heat"


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


def test_deck_slabs_render_on_their_storey_plans(catlin_model):
    """A deck that encloses no walls has to draw its own outline, or the plan slice shows
    empty air where a walking surface is.

    Two of the three exterior decks are FloorSystems — the porch (3bf2f48) and the balcony
    (2026-08-22) — so neither is a Slab any more and neither would be drawn by reading
    ``model.solids`` alone. ``_emit_slabs`` reads ``model.floors`` too, and the tag on the
    polyline is the floor system's. The breezeway is the third and stays a Slab, for the
    reason params/breezeway.py gives: its plank oversails its joist field onto two door
    thresholds, and a floor system's sheet cannot. It draws from ``model.solids``, so this
    covers both paths."""
    from typehaus.emit.draw.floorplan import build_floorplan
    from typehaus.emit.draw.scene import Polyline

    for storey, tag in (("second", "FS-SG-DECK"), ("main", "FS-SG-PORCH"),
                        ("main", "SL-BW-DECK")):
        outlines = [node for node in build_floorplan(catlin_model, storey).nodes
                    if isinstance(node, Polyline) and getattr(node, "tag", None) == tag]
        assert len(outlines) == 1, (storey, tag)
        assert outlines[0].layer == "A-SLAB" and outlines[0].closed

    # And an interior floor still does NOT draw one: its subfloor covers the whole storey,
    # so its rectangle would sit over every room on the plan.
    interior = [node for node in build_floorplan(catlin_model, "second").nodes
                if isinstance(node, Polyline)
                and str(getattr(node, "tag", "")).startswith("FS-S-")]
    assert not interior, [node.tag for node in interior]


def test_catlin_drain_fixtures_use_six_inch_wet_walls():
    report = run(load_plan(CATLIN_DIR).plan, CATLIN_DIR, tier=None)
    findings = [finding for finding in report.findings if finding.check_id == "advisory.wet_wall_depth"]
    assert not findings, [finding.message for finding in findings]


def test_catlin_floor_heat_has_no_fixture_keepout_conflict():
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


def test_catlin_floor_heat_zones_are_the_three_supplemental_ones(catlin_model):
    """Radiant floor is a comfort layer, not the heating system, and RM-B-SAUNA has none.

    The sauna floor was deleted 2026-07-25 (a heated floor in a 190 F room has nowhere to
    put its heat); what is left is the main bath, the patch under the dining table and the
    NW bathroom upstairs. All three are electric mat with a resolvable zone and wire run.
    """
    zones = {item.tag: item for item in catlin_model.floor_heat}
    assert set(zones) == {"FH-M-BATH2", "FH-M-DINING", "FH-S-BATH1"}
    for zone in zones.values():
        assert zone.system == "electric"
        assert zone.wire_length_m > 0
        assert len(zone.zone) >= 3
    assert {zone.storey for zone in zones.values()} == {"main", "second"}


def test_catlin_is_all_electric_with_no_gas_appliance(catlin_model):
    """No furnace, no gas: heat is the minisplits plus the radiant floor zones.

    The air side that survives is ventilation only — EQ-B-ERV's fresh-air supply — so a
    SUPPLY_AIR port here must trace back to the ERV and not to a reintroduced air handler.
    """
    plan = catlin_model.plan
    equipment = [element for storey in plan.storeys
                 for element in plan.storey_elements(storey.tag)
                 if element.element_kind == "Equipment"]
    assert not [item for item in equipment
                if item.kind.value in {"furnace", "air_handler"}]
    assert not [line for line in plan.project.site.utilities if line.kind.value == "gas"]
    for product in plan.library.equipment_types:
        assert "gas" not in {port.service.value for port in product.ports}, product.tag
    # Two air-side products now, and neither burns anything: the ERV (ventilation air) and
    # System 1's concealed ducted air handler (conditioned air off a heat pump). What the
    # all-electric contract forbids is a *combustion* appliance, not a duct.
    air = {product.tag for product in plan.library.equipment_types
           if "supply_air" in {port.service.value for port in product.ports}}
    # The ventilator became a named product on 2026-08-25 (EQ-T-BROAN-B210E75RT), and the
    # radial pass added two more boxes its FRESH air passes through — the 6-port supply
    # manifold and the mixing box where the ERV leg joins System 1's return. (The 10-port
    # manifold and the gable hoods carry stale and outdoor air, so they declare RETURN_AIR
    # and OUTDOOR_AIR instead and are not in this set.) None of the five burns anything,
    # which is what this assertion is actually about.
    assert air == {"EQ-T-BROAN-B210E75RT", "EQ-T-GREE-SLIM24", "EQ-T-ERV-MANIFOLD-6",
                   "EQ-T-ERV-MIXING-BOX"}


_PERIMETER_ASSEMBLIES = ("CATLIN_BASEMENT_12", "CATLIN_BASEMENT_8",
                         "CATLIN_BASEMENT_8_GARDEN", "SAUNA_LINER_ON_BASEMENT_8_GARDEN")


def test_basement_walls_carry_two_exterior_xps_layers(catlin_model):
    """Old: 4 perimeter segments x 2 XPS layers; new: every perimeter segment
    carries both 2" XPS layers in its resolved stack.

    Eleven segments across four assemblies since 2026-08-23: eight on N/E/W with an
    above-grade protection band, three on the south with a full-height parge into the sunken
    garden — of which W-B-S2 also carries the sauna's liner inboard of the pour. The foam is
    identical on all of them and so is the 4.05" it puts outboard of the pour; the splits are
    about what covers the foam outside, what (if anything) lines the room inside, and — since
    the thinning — how thick the pour behind it is.

    It was ten until the ESS closet moved to the furnace room's NE corner and W-B-N3 split at
    x=6'-0" into W-B-N3 + W-B-N4. That is a node, not a construction change: both halves carry
    the same assembly, and the assertion below still runs over every one of them.
    """
    perimeter = [w for w in catlin_model.walls
                 if w.storey == "basement" and w.assembly in _PERIMETER_ASSEMBLIES]
    assert len(perimeter) == 11  # same wall line, split at grid/tee nodes
    garden = [w for w in perimeter if w.assembly.endswith("BASEMENT_8_GARDEN")]
    assert len(garden) == 2 + 1  # W-B-S1/W-B-S3 bare + W-B-S2 on the liner variant
    for wall in perimeter:
        xps = [l for l in wall.layers if l.name.startswith("xps")]
        assert len(xps) == 2
        for layer in xps:
            assert layer.thickness_m == pytest.approx(inch(2.0).meters)


def test_only_the_deck_bearing_perimeter_stays_twelve_inches(catlin_model):
    """12" is earned where a *cast* deck lands on the wall top beside the sill, and nowhere
    else (2026-08-21). SL-M-DECK spans east-west onto the east wall and the centre line, so
    W-B-E1/E2 keep the 12" pour and the other eight segments are 8" — which IRC Table
    R404.1.2(8) allows at 45 psf/ft on the 10' x 7' row only with vertical steel, so each of
    the eight must declare it or ``structural.foundation_unbalanced_fill`` FAILs."""
    from typehaus.model.structure import FoundationWall

    perimeter = {w.tag: w for w in catlin_model.walls
                 if w.storey == "basement" and w.assembly in _PERIMETER_ASSEMBLIES}
    thick = {tag for tag, w in perimeter.items()
             if next(l for l in w.layers if l.name == "concrete").thickness_m
             == pytest.approx(inch(12.0).meters)}
    assert thick == {"W-B-E1", "W-B-E2"}
    for tag, wall in perimeter.items():
        if tag in thick:
            continue
        concrete = next(l for l in wall.layers if l.name == "concrete")
        assert concrete.thickness_m == pytest.approx(inch(8.0).meters)
        source = next(w for w in catlin_model.plan.all_elements()
                      if isinstance(w, FoundationWall) and w.tag == tag)
        assert source.vertical_reinforcement == '#5 @ 41" o.c.', tag


def test_the_brick_standoff_is_independent_of_the_pour(catlin_model):
    """N-B-BRICK-W/-E stand off ``inch(-4.55)`` from the concrete face. That number is the
    library core's tail (0.05" damp-proofing + 2 x 2" XPS = 4.05") plus a 1/2" house skin,
    and it must survive a change of pour thickness — the veneer, the excavation, the XPS
    plane and the drain tile are all measured off the *exterior* face, which is the datum
    the walls align on, so only the inside face moved on 2026-08-21."""
    for tag in _PERIMETER_ASSEMBLIES:
        asm = catlin_model.plan.library.resolve_assembly(tag)
        after_pour = [l for l in asm.layers
                      if l.name in ("damp-proof", "xps-a", "xps-b", "parge",
                                    "protection-panel")]
        outboard = sum(l.thickness.inches for l in after_pour)
        assert outboard == pytest.approx(4.55), tag


def test_garage_is_freestanding_north_of_the_house_with_icf_stem(catlin_model):
    stem = [w for w in catlin_model.walls if w.tag.startswith("W-GF-")]
    # 8, not 4: both stems that carry a door gap at it rather than running a continuous 22"
    # band across it — the east at the overhead door (W-GF-E1/W-GF-E-DR/W-GF-E2) and, since
    # 2026-08-01, the south at the service door (W-GF-S1/W-GF-S-DR/W-GF-S2). A person will
    # not climb a 22" curb any more happily than a car will.
    assert len(stem) == 8
    ys = [p[1] for w in stem for p in w.axis]
    assert min(ys) == pytest.approx(ft(HOUSE_SIZE_FT + GARAGE_GAP_FT).meters)
    assert max(ys) == pytest.approx(ft(HOUSE_SIZE_FT + GARAGE_GAP_FT + GARAGE_SIZE_FT).meters)
    # Stem runs 42" below grade to 22" above it — absolute elevations, walkout-style —
    # except under the overhead door, where it becomes a grade beam topping out *flush with
    # the slab* rather than at any reveal at all: a low curb across a 16' vehicle door is
    # still a curb the car has to climb.
    #
    # Every one of those numbers is measured from **grade**, not from the project datum. The
    # two were the same thing until 2026-08-18, when grade went to -2'-6" to lift the house
    # out of the ground and the garage — driven into at grade, and staying there — went down
    # with the soil. Reading them off ``site.grade`` is the assertion: the reveal, the bury
    # and the slab are properties of the ground, and the house datum is not the ground.
    grade_m = catlin_model.plan.project.site.grade.meters
    grade_beams = {w.tag for w in stem if w.tag in ("W-GF-E-DR", "W-GF-S-DR")}
    assert grade_beams == {"W-GF-E-DR", "W-GF-S-DR"}
    slab = next(s for s in catlin_model.solids if s.tag == "SL-G-FLOOR")
    assert slab.z1_m == pytest.approx(grade_m)
    for wall in stem:
        assert wall.z0_m == pytest.approx(grade_m - inch(42.0).meters)
        expected_top = slab.z1_m if wall.tag in grade_beams else grade_m + inch(22.0).meters
        assert wall.z1_m == pytest.approx(expected_top)
    # Garage roof: ridge E-W (rotated 90° vs the house), 16" overhangs.
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-GARAGE")
    assert roof.ridge_direction == "x"
    xs = [p[0] for p in roof.footprint]
    assert max(xs) - min(xs) == pytest.approx(
        ft(GARAGE_SIZE_FT).meters + 2 * inch(GARAGE_OVERHANG_IN).meters)


def test_garage_overhead_door_opens_from_the_slab_at_grade(catlin_model):
    """The one negative sill in the plan, and the thing that makes the garage drivable.

    W-G-E bears on the ICF stem, 22" above the slab poured inside it, so a door sitting on
    its host wall's own base would open 22" up in the air. D-G-OVERHEAD instead drops that
    exact reveal to land on SL-G-FLOOR. This is the assertion that holds ``sill_height``
    tied to ``GARAGE_STEM_REVEAL``: the editable-plan dialect bans arithmetic, so the two
    numbers cannot be spelled as one expression in plan/storeys/garage.py.
    """
    wall = catlin_model.wall("W-G-E")
    door = next(o for o in catlin_model.openings if o.tag == "D-G-OVERHEAD")
    slab = next(s for s in catlin_model.solids if s.tag == "SL-G-FLOOR")

    threshold = wall.z0_m + door.sill_m
    assert threshold == pytest.approx(slab.z1_m)
    assert door.sill_m == pytest.approx(-(wall.z0_m - slab.z1_m))
    # A 7' door is 7' of clear opening wherever its threshold lands, so the head comes down
    # with it — and stays inside the 8' wall, leaving room for the LVL and its cripples.
    head = threshold + door.height_m
    assert head == pytest.approx(slab.z1_m + ft(7.0).meters)
    assert head < wall.z1_m

    # The framed header follows the head down too. It used to be pinned to the host wall's
    # base regardless of sill, which left the LVL 22" above the hole every other emitter cut.
    # And it sits ON the head, not a plate above it: until 2026-08-25 the opening pack was
    # framed off the stud bearing line rather than the wall's framing base, so every header
    # in the house stood 1 1/2" clear of the hole it carries — see
    # test_opening_framing_registers_with_the_opening_it_frames.
    header = next(m for m in catlin_model.all_members()
                  if m.parent_uid == wall.uid and m.category == "header")
    assert header.z0_m == pytest.approx(head)

    # …and the cripples the docstring promises are actually there. Until 2026-08-23 they
    # were not: the head family was emitted from inside the window-only branch that carries
    # the rough sill, so this door — the widest opening in the house — had 18" of empty
    # wall and 16 ft of unbacked double top plate above its header. They bear on the flat
    # track nailer, not on the LVL through it.
    backing = next(m for m in catlin_model.all_members()
                   if m.parent_uid == wall.uid and m.child_key.startswith("trackbacking-"))
    cripples = [m for m in catlin_model.all_members()
                if m.parent_uid == wall.uid and m.child_key.startswith("cripple-head-")]
    assert len(cripples) > 8, "16'-9\" of header at 16\" o.c. is a dozen stations"
    for cripple in cripples:
        assert cripple.z0_m == pytest.approx(backing.z1_m)


def test_garage_brick_wainscot_piers_are_the_door_jambs_and_cap_at_four_feet(catlin_model):
    """The two things about the east brick wainscot a future edit could silently break.

    **The piers are not a free choice.** W-G-BRICK-S/N stand on the two stem segments that
    exist only because the stem drops to a grade beam under the overhead door, so their
    4'-0" width IS ``OVERHEAD_DOOR_OFFSET`` and their inboard ends ARE the door jambs. The
    editable-plan dialect bans arithmetic, so plan/storeys/garage.py spells the four node y
    values as literals and nothing but this test ties them back to the door.

    **Top of cap is 4'-0" above grade on the nose**, and every course below it is a whole
    2 2/3" module: shelf at grade + 1 course, 15 courses of field brick, a 4" rowlock, then
    1 1/3" of cap flashing. Read off ``site.grade`` for the same reason the stem test does —
    the wainscot is a property of the ground, and the house datum is not the ground.

    Neither fact has a check behind it. A veneer wall whose node fails to resolve comes back
    ``None`` silently — no geometry and no finding — so the first assertion here is simply
    that the two walls exist at all.
    """
    grade_m = catlin_model.plan.project.site.grade.meters
    south = catlin_model.wall("W-G-BRICK-S")
    north = catlin_model.wall("W-G-BRICK-N")
    assert south is not None and north is not None

    # W-G-E runs south -> north, so ``center_along_m`` is measured from its south end and
    # the two jambs are absolute y values on the same line the piers stand on.
    door = next(o for o in catlin_model.openings if o.tag == "D-G-OVERHEAD")
    host = catlin_model.wall("W-G-E")
    (_, ya), (_, yb) = host.axis[0], host.axis[-1]
    assert yb > ya, "W-G-E is authored south -> north; the jamb maths below assumes it"
    jamb_lo = ya + door.center_along_m - door.width_m / 2.0
    jamb_hi = ya + door.center_along_m + door.width_m / 2.0

    for wall, jamb, end in ((south, jamb_lo, "north"), (north, jamb_hi, "south")):
        ys = sorted(p[1] for p in wall.axis)
        assert ys[1] - ys[0] == pytest.approx(ft(4.0).meters), "pier is the door offset"
        # The pier's inboard end lands on the jamb it flanks.
        inboard = ys[1] if end == "north" else ys[0]
        assert inboard == pytest.approx(jamb)

    # Whole modules all the way up, and the cap 4'-0" over grade.
    course = inch(2.0 + 2.0 / 3.0).meters
    for wall in (south, north):
        assert wall.z0_m == pytest.approx(grade_m + course), "base course one module up"
        assert wall.z1_m - wall.z0_m == pytest.approx(inch(44.0).meters)  # 15 courses + rowlock
    caps = [s for s in catlin_model.solids if str(s.tag).startswith("TR-G-BRICK-CAP-")]
    assert caps, "the cap flashing is a modelled element, not just a note"
    assert max(c.z1_m for c in caps) == pytest.approx(grade_m + ft(4.0).meters)


def test_garage_service_door_opens_onto_the_breezeway_deck_not_the_slab(catlin_model):
    """D-G-SERVICE follows the *deck*, and D-G-OVERHEAD follows the *slab*. That split is
    the whole shape of the 2026-08-18 lift at the garage.

    Both doors carried the same negative sill from 2026-08-01, when the service door was
    dropped to the slab to meet a breezeway deck that also sat at 0'-0". Then grade went to
    -2'-6" and the garage went down with it while the breezeway deck — a bridge between two
    doors, not a thing standing on soil — stayed. The deck is still this door's landing
    (code.R311_3_exterior_landing, and houses/catlin/CLAUDE.md's rule that both breezeway
    doors open onto it at one level), so the threshold stays at 0'-0" and the sill turns
    positive. Grade went down another 4" on 2026-08-21 for the basement-ceiling overhaul,
    so it is now +1'-0" over a garage storey at -1'-0", and the 2'-10" is taken inside
    instead — by the SL-G-STEP-0 landing and the ST-G-SERVICE flight below it.
    """
    wall = catlin_model.wall("W-G-S")
    door = next(o for o in catlin_model.openings if o.tag == "D-G-SERVICE")
    slab = next(s for s in catlin_model.solids if s.tag == "SL-G-FLOOR")
    # The breezeway plank is FS-BW-FLOOR's `subfloor` since 2026-08-22, not the SL-BW-DECK
    # Slab it used to be, so the landing height is the resolved deck sheet's top.
    deck_top = next(f for f in catlin_model.floors if f.tag == "FS-BW-FLOOR").deck_z1_m

    threshold = wall.z0_m + door.sill_m
    # The landing outside, not the floor inside: within R311.3.1's 1 1/2" of the deck, and a
    # full 2'-10" above the slab.
    assert abs(deck_top - threshold) <= inch(1.5).meters
    assert threshold - slab.z1_m == pytest.approx(inch(34.0).meters)

    # Five 6.8" risers inside close that 2'-10": a 3'-0" concrete landing level with the
    # threshold, and four pressure-treated treads below it. (Six-inch risers while grade was
    # -2'-6"; five concrete slabs until 2026-08-22, when `Stair` gained the optional
    # `floor_opening` and the explicit elevations a step-down within one storey needs.)
    landing = next(s for s in catlin_model.solids if s.tag == "SL-G-STEP-0")
    assert landing.z1_m == pytest.approx(threshold)
    assert [s.tag for s in catlin_model.solids if s.tag.startswith("SL-G-STEP-")] == \
        ["SL-G-STEP-0"]

    stair = next(s for s in catlin_model.stairs if s.tag == "ST-G-SERVICE")
    assert stair.riser_count == 5
    assert stair.riser_height_m == pytest.approx(inch(34.0 / 5).meters)
    assert stair.base_elevation_m == pytest.approx(slab.z1_m)
    assert stair.arrival_elevation_m == pytest.approx(threshold)
    treads = sorted((m for m in stair.members if m.category == "tread"), key=lambda m: m.z1_m)
    assert len(treads) == 4
    assert treads[0].z1_m - slab.z1_m == pytest.approx(inch(34.0 / 5).meters)
    assert treads[-1].z1_m == pytest.approx(threshold - inch(34.0 / 5).meters)
    # Pressure-treated, not the generic lumber every stair in the house rendered as before
    # `Stair` had a material at all.
    assert {m.material for m in stair.members} == {"kdat"}


def test_garage_wood_framing_uses_its_structure_layer_centerline(catlin_model):
    """Wood members must follow studs rather than the exterior ZIP-R datum axis."""
    # The east side's stem splits into 3 segments at the overhead door (W-GF-E1/
    # W-GF-E-DR/W-GF-E2), so it no longer matches the (unsplit) wood wall 1:1 — group by
    # side and check the wood wall's endpoints are among the group's stem corners instead.
    stem_groups: dict[str, list] = {}
    for wall in catlin_model.walls:
        if not wall.tag.startswith("W-GF-"):
            continue
        side = wall.tag.removeprefix("W-GF-").split("-")[0].rstrip("12")
        stem_groups.setdefault(side, []).append(wall)
    garage_walls = [wall for wall in catlin_model.walls if wall.tag.startswith("W-G-")]
    assert len(garage_walls) == 4

    for wall in garage_walls:
        group = stem_groups[wall.tag.removeprefix("W-G-")]
        stem_points = [p for stem in group for p in stem.axis]
        for point in wall.axis:  # both systems share the intended garage footprint
            assert any(point == pytest.approx(stem_point, abs=1e-9)
                       for stem_point in stem_points)
        start, end = wall.axis
        dx, dy = end[0] - start[0], end[1] - start[1]
        span = (dx * dx + dy * dy) ** 0.5
        normal_x, normal_y = -dy / span, dx / span

        def band_offset(function: str) -> float:
            layer = next(ly for ly in wall.layers if ly.function == function)
            return sum(
                (point[0] - start[0]) * normal_x + (point[1] - start[1]) * normal_y
                for point in layer.polygon
            ) / len(layer.polygon)

        # Every member is on the centreline of the band it belongs to — the studs on the
        # structure layer's, and the rainscreen strapping, where there is any, on the FURRING
        # layer's, outboard of it (resolve/framing/furring.py). Asserting one offset for all
        # of them would put the battens inside the ZIP-R they are fastened over.
        #
        # GARAGE_WALL_2X6 has had NO furring layer since 2026-08-20 (nail strip face-fastens
        # straight to the Zip-R), so on this house the strapping branch is currently dead. It
        # stays coded rather than deleted because the offset rule is what the test is about,
        # and the furring comes straight back if the garage ever re-clads.
        has_furring = any(ly.function == "furring" for ly in wall.layers)
        expected = {"strapping": band_offset("furring")} if has_furring else {}
        default_offset = band_offset("structure")

        assert wall.members
        assert has_furring == any(member.category == "strapping" for member in wall.members)
        for member in wall.members:
            center_offset = expected.get(member.category, default_offset)
            for point in (member.p0, member.p1):
                offset = (point[0] - start[0]) * normal_x + (point[1] - start[1]) * normal_y
                assert offset == pytest.approx(center_offset, abs=1e-9)


def test_sunken_garden_structure_matches_redesign_spec(catlin_model):
    """Freestanding porch/balcony redesign: no north or front wall, two 12" side walls, a
    column + two beams on each open porch edge, a metal porch guard, six 6x6 pillars +
    three balcony beams, and a 19x28 garden.

    The porch's south edge was a 16" arched cross-wall under a 42" masonry parapet until
    2026-08-18. It is a 16" square cast column and two flush LVL beams now — the same
    detail the north edge has carried all along — with RL-SG-PORCH in place of the parapet.
    """
    walls = [w for w in catlin_model.walls if w.tag.startswith("W-SG-")]
    # 5 concrete: two porch side walls (W1/E1) + the retaining U (W2/E2/S). No north wall,
    # no front wall, and no masonry railing over any of them.
    assert {w.tag for w in walls} == {"W-SG-W1", "W-SG-E1", "W-SG-W2", "W-SG-E2", "W-SG-S"}
    assert all(w.is_foundation for w in walls)
    assert all(w.assembly == "SUNKEN_GARDEN_WALL" for w in walls)
    assert not any(w.tag.startswith("W-SG-RAIL-") for w in walls)

    # Both open porch edges are a column at midspan carrying two beams into the side walls.
    front = next(s for s in catlin_model.solids if s.tag == "PT-SG-FCOL")
    assert front.category == "column" and front.assembly == "SUNKEN_GARDEN_COLUMN_16"
    xs = [p[0] for p in front.outline]
    ys = [p[1] for p in front.outline]
    assert max(xs) - min(xs) == pytest.approx(inch(16).meters)   # a true 16" square:
    assert max(ys) - min(ys) == pytest.approx(inch(16).meters)   # "16x16" would read 1.5x5.5
    front_beams = {b.tag: b for b in catlin_model.solids
                   if b.tag in ("BM-SG-FRW", "BM-SG-FRE")}
    assert len(front_beams) == 2
    # Flush-framed: the beams top out at the 0' joist datum and the column stops at their
    # soffit, which is what keeps the pour clear of the 16"-o.c. joist band above it.
    assert all(b.z1_m == pytest.approx(0.0) for b in front_beams.values())
    assert front.z1_m == pytest.approx(min(b.z0_m for b in front_beams.values()))

    # The porch guard is a Railing now, matching RL-SG-BALCONY one storey up.
    guard = catlin_model.plan.by_tag("RL-SG-PORCH")
    assert guard.type_ref == "RAILING-EXT-ALUMINUM-FASCIA"
    assert guard.height.inches == pytest.approx(42.0)
    assert len(guard.path) == 4  # west / south / east; the north edge is the house gap

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
    assert {"PT-SG-COL", "PT-SG-FCOL"} <= posts  # sonotube + front square column
    assert len([t for t in posts if t.startswith("PT-SG-B")]) == 6  # 6x6 pillars
    # 2 LVL back beams + 2 LVL front beams + 3 double-2x10 N-S balcony beams + 4 E-W girt
    # segments (two per pillar row, butting the beams; the girts give the freestanding
    # balcony a member to brace against in its second principal direction).
    assert len(beams) == 11
    assert {"BM-SG-BKW", "BM-SG-BKE", "BM-SG-FRW", "BM-SG-FRE"} <= beams
    assert {"BM-SG-GIRT-RW", "BM-SG-GIRT-RE",
            "BM-SG-GIRT-FW", "BM-SG-GIRT-FE"} <= beams

    # Both exterior decks carry their walking surface, and both do it the same way now: the
    # plank is the floor system's own deck sheet, so the surface follows the framing instead
    # of floating beside it as a second element. The balcony's SL-SG-DECK slab was the last
    # of the three to go (2026-08-22); no Slab is left over either deck.
    for tag, material in (("FS-SG-PORCH", "composite-deck"), ("FS-SG-DECK", "aluminum-deck")):
        system = catlin_model.plan.by_tag(tag)
        assert system.subfloor is not None and system.subfloor.material_ref == material
    assert not [s for s in catlin_model.solids
                if s.category == "slab" and s.tag.startswith("SL-SG-DECK")]


def test_stack_width_change_resolves_on_the_side_wall_line(catlin_model):
    """M3 acceptance: a main->second stack edge with a width change still resolves.

    The exterior stack is 2x6 on every storey now, so the surviving width-change
    edges are interior — the 2x4 storage partitions (W-M-STOS/STOS2) under the
    second floor's 2x6 plumbing wall (W-S-BD-N)."""
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
    # ST-G-SERVICE joined them on 2026-08-22: five risers from the garage slab to the
    # service-door threshold, a step-down WITHIN one storey, which `Stair` could not express
    # until `floor_opening` became optional and `base_elevation`/`top_elevation` were added.
    # It was five concrete `Slab`s before that, and invisible to every stair rule there is.
    assert set(stairs) == {"ST-B2M", "ST-M2S", "ST-S2A", "ST-G-SERVICE"}
    for stair in stairs.values():
        assert stair.riser_height_m <= inch(7.75).meters + 1e-9
        assert stair.tread_depth_m >= inch(10.0).meters - 1e-9
    # ST-B2M gained a riser (14 -> 15) on 2026-08-21: the basement storey went down 4" so the
    # house could carry a 12 5/8" deck over it and keep its headroom. The three storey-to-
    # storey flights are all in that band; ST-G-SERVICE is a 2'-10" step-down and has five.
    assert {stairs[tag].riser_count for tag in ("ST-B2M", "ST-M2S", "ST-S2A")} <= {14, 15, 16}
    assert stairs["ST-G-SERVICE"].riser_count == 5
    # Ordinary stairs stay compact by default: 11" boards with a 1" nose yield the 10"
    # code-minimum going, leaving any extra shaft length beyond the arrival platform.
    assert stairs["ST-M2S"].tread_depth_m == pytest.approx(inch(11.0).meters, abs=1e-9)
    assert stairs["ST-B2M"].tread_depth_m == pytest.approx(inch(11.0).meters, abs=1e-9)
    assert all(stair.going_depth_m == pytest.approx(inch(10).meters, abs=1e-9)
               for tag, stair in stairs.items() if tag != "ST-G-SERVICE")
    # The garage stair takes the opposite trade: 11" boards with NO nose, so its going is the
    # full 11" and its run stays the 3'-8" the four concrete treads it replaced occupied. A
    # nose would have shortened the run and bought nothing — there is no shaft to fit into.
    assert stairs["ST-G-SERVICE"].going_depth_m == pytest.approx(inch(11).meters, abs=1e-9)
    assert stairs["ST-G-SERVICE"].nosing_depth_m == 0.0
    attic = stairs["ST-S2A"]
    assert attic.winder_count == 3
    assert attic.run_reversed is True
    winders = [member for member in attic.members if member.category == "winder"]
    assert len(winders) == 3
    # The three raised tapered panels have independent code-sized narrow ends; they no
    # longer converge on a newel point or leave a fourth floor-level wedge at the turn.
    # Three distinct corners is the floor: the first and last wedges are honest triangles
    # once degenerate (coincident/collinear) ring vertices are stripped.
    assert len({member.p0 for member in winders}) == len(winders)
    assert all(member.plan_outline and len(member.plan_outline) >= 3 for member in winders)
    source = catlin_model.plan.storey(attic.storey)
    assert source is not None
    assert [member.z1_m for member in winders] == pytest.approx(
        [source.elevation.meters + attic.riser_height_m * step for step in (1, 2, 3)])
    for tag in ("ST-B2M", "ST-M2S"):
        stair = stairs[tag]
        assert stair.layout == "u_split_landing"
        keys = {member.child_key for member in stair.members}
        # Split-landing semantics: the riser between the two half-width landing
        # platforms IS the step, so there is no separate step-between-landings member
        # (it used to be a byte-identical duplicate of landing-upper).
        assert keys >= {"landing-lower", "landing-upper"}
        assert "step-between-landings" not in keys


def test_stair_designer_contract_exposes_catlin_authored_inputs(catlin_model):
    """The editor receives editable inputs alongside resolver-owned stair geometry."""
    from typehaus.server.model_json import model_to_dict

    stairs = {item["tag"]: item for item in model_to_dict(catlin_model)["stairs"]}
    # ST-G-SERVICE joined them on 2026-08-22: five risers from the garage slab to the
    # service-door threshold, a step-down WITHIN one storey, which `Stair` could not express
    # until `floor_opening` became optional and `base_elevation`/`top_elevation` were added.
    # It was five concrete `Slab`s before that, and invisible to every stair rule there is.
    assert set(stairs) == {"ST-B2M", "ST-M2S", "ST-S2A", "ST-G-SERVICE"}
    # 3'-5 1/16" is the flight the basement's 7'-2 5/8" well leaves either side of the
    # 4 1/2" well partition. It was 3'-3 3/4" in a 7'-0" well until 2026-08-24, when
    # W-B-STR/W-B-STR3 were framed and the shaft's west face came down from x=10'-6" to the
    # stud line's plywood at 10'-3 3/8"; the 2 5/8" went into the two flights rather than
    # being left as a slot beside the wall.
    assert stairs["ST-B2M"]["width_m"] == pytest.approx(ft(3, 5.0625).meters, abs=1e-9)
    assert stairs["ST-B2M"]["floor_opening"] == "FO-M-STAIR"
    assert stairs["ST-B2M"]["run_direction"] == "y"
    assert stairs["ST-B2M"]["layout"] == "u_split_landing"
    # x=10'-3 3/8" since 2026-08-24 — the framed stair wall's plywood face, which is where
    # FO-M-STAIR's west edge is now and where FO-S-STAIR's already was.
    assert stairs["ST-B2M"]["start"] == pytest.approx(
        [ft(10, 3.375).meters, ft(26, 0.375).meters])
    assert stairs["ST-M2S"]["layout"] == "u_split_landing"
    # Both U-stairs turn left, so each springs from the east lane and arrives in the west
    # one — on main, the lane D-M-STAIR stood in until the wall came out (2026-08-24).
    for tag in ("ST-B2M", "ST-M2S"):
        assert stairs[tag]["turn_direction"] == "left"
    assert stairs["ST-S2A"]["layout"] == "right_angle_winder"
    assert stairs["ST-S2A"]["turn_direction"] == "left"
    assert stairs["ST-S2A"]["winder_count"] == 3
    assert stairs["ST-S2A"]["run_reversed"] is True


# Two devices are wall-*mounted* but not wall-*hosted*, and both say so in their own
# comments: the island GFCI is let into FURN-M-KIT-ISLAND's east end, and the porch flood
# is strapped to pillar PT-SG-BR2. Neither is a Wall, and `wall_ref` only names Walls.
# Devices that are deliberately not on a wall face — one, and it should stay one.
#
# ED-M-LIVING-KGF4 was here from 2026-08-02 (the island's end-mounted GFCI) until
# 2026-08-24, and for two days of that it had three companions: KGF5/KGF6, flush
# counter-top pop-ups, and KMX1 inside a base-cabinet mixer lift. All four went when the
# mixer moved into FURN-M-KIT-MIXER-GARAGE, a counter-to-ceiling cabinet whose back IS the
# east wall — so KGF4 and KMX1 are ordinary wall-hosted boxes at 42" now and are graded like
# every other receptacle in the house. ** Shrinking this set is the direction it should
# move; adding to it is how a device ends up floating in a room and nobody notices. **
_NOT_WALL_HOSTED = {"ED-M-PORCH-FLOOD"}


def test_wall_mounted_devices_resolve_against_a_wall_face(catlin_model):
    """A switch or receptacle lands on the finish plane, not on the wall's centreline.

    Authored device positions are plain plan points — nothing in the resolver pulls them
    onto a wall — so a box authored at the wall's axis resolves *inside* the framing, and
    one authored a few feet off resolves in mid-air. Both were widespread until the
    2026-08-03 pass; this is what says they stay fixed. The test grades the resolved body,
    not the authored point: its back edge sits on a wall face (a recessed box the other
    way), it does not reach through into the studs, and it is not floating in a room.
    """
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    walls: dict[str, list] = {}
    for wall in catlin_model.walls:
        parts = [Polygon(layer.polygon) for layer in wall.layers if len(layer.polygon) >= 3]
        parts = [p for p in parts if p.is_valid and p.area > 1e-9]
        if parts:
            walls.setdefault(wall.storey, []).append((unary_union(parts), wall.z0_m, wall.z1_m))

    offenders = []
    for item in catlin_model.canvas_objects:
        if item.kind != "ElectricalDevice" or item.tag in _NOT_WALL_HOSTED:
            continue
        mount = item.mount
        if mount is None or mount.kind.value != "wall":
            continue
        body = Polygon(item.footprint)
        best = None
        for solid, z0, z1 in walls.get(item.storey, []):
            if z1 <= item.z_m + 1e-6 or z0 >= item.z_m + 1e-6:
                continue  # this wall is not there at the height the device hangs
            overlap = solid.intersection(body).area
            gap = solid.distance(body)
            if best is None or (overlap, -gap) > (best[0], -best[1]):
                best = (overlap, gap)
        if best is None:
            offenders.append((item.tag, "no wall at its mounting height"))
            continue
        overlap, gap = best
        # Positions are authored to 1/8", so grade how far the body reaches past the face
        # rather than whether it touches it at all.
        reach = overlap / math.sqrt(body.area)
        if reach > inch(0.25).meters and not mount.recessed_into_host_surface:
            offenders.append((item.tag, "buried %.2f\" into the wall" % (reach / inch(1).meters)))
        elif overlap <= 1e-9 and gap > inch(0.25).meters:
            offenders.append((item.tag, "floating %.1f\" off the wall" % (gap / inch(1).meters)))
    assert not offenders, offenders


def test_ifc_emission_when_available(catlin_model, tmp_path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    import ifcopenshell.validate
    from typehaus.emit.ifc import emit_ifc

    path = emit_ifc(catlin_model, tmp_path / "catlin.ifc", lod="framed")
    assert path.exists() and path.stat().st_size > 0
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(str(path), logger, express_rules=True)
    assert not logger.statements, logger.statements


def test_the_main_floor_finish_follows_the_deck_boundary(tmp_path):
    """The contract that makes DERIVING the finish split worth it rather than authoring it.

    ``_BAND_Y`` in ``params/main_deck.py`` is the one place the concrete/wood boundary lives:
    the two FloorSystem outlines and the Slab outline are all cut from it. Because
    ``RM-M-LIVING``'s polished-concrete zone is intersected out of ``SL-M-DECK`` rather than
    written as a polygon on the room, moving that one line moves the finish with it. An
    authored zone would have gone stale silently — which is exactly how the three
    sealed-concrete rooms ended up over a wood deck.
    """
    from _helpers import copy_house

    house = copy_house(CATLIN_DIR, tmp_path / "catlin")
    params = house / "params" / "main_deck.py"
    source = params.read_text()
    assert "_BAND_Y = ft(13)" in source
    params.write_text(source.replace("_BAND_Y = ft(13)", "_BAND_Y = ft(20)"))

    def band_sqft(house_dir: Path) -> float:
        result = load_plan(house_dir)
        assert result.plan is not None, [f.message for f in result.findings]
        model, findings = resolve(result.plan)
        assert not [f for f in findings if f.severity.value == "error"]
        living = next(room for room in model.rooms if room.tag == "RM-M-LIVING")
        zones = [z for z in living.finish_zones if z.material_ref == "polished-concrete"]
        assert len(zones) == 1 and zones[0].source_ref == "SL-M-DECK"
        return zones[0].area_m2 * 10.7639104

    before = band_sqft(CATLIN_DIR)
    after = band_sqft(house)
    # The band lost 7' of its 23' north-south run over the 18' east half, and the zone is
    # clipped to the room, so the drop is the room's share of 7' x 18' — not the whole of it.
    # 411.3 until 2026-08-24, when RM-M-PANTRY took the living room's NW corner — the band
    # is clipped to the ROOM, so framing a room out of it shrinks this zone by that room's
    # area. Then 390.6 -> 392.7 later the same day, when W-M-PAN-S moved 4" north and handed
    # 2.1 sf back. The 7' x 18' arithmetic below is unaffected either way: the pantry is at
    # y 33'-3 3/8"..35'-5 3/8", nowhere near the _BAND_Y line this test moves.
    assert before == pytest.approx(392.7, abs=0.5)
    assert before - after == pytest.approx(7.0 * 17.9, rel=0.05)


def test_the_laundry_pocket_clears_the_bearing_corner_and_owns_its_wall(catlin_model):
    """D-M-LAUN's cavity crosses N-M-E3 into W-M-HS4, and that wall is spoken for.

    Three facts, each of which a later edit would otherwise break silently:

    1. **The closed end clears N-M-C2.** That node is where the BEARING ``W-M-C3`` corners
       in and ``BM-M-HALL`` starts, so the jamb pack that closes the cavity has to stop
       short of its corner square. 4'-0" is the widest leaf that does; a wider one walks
       the pack into the corner.
    2. **The cavity crosses the W-M-LS tee.** This is legal because a pocket occupies only
       floor to 6'-8": the band's double top plate runs unbroken above it and its bottom
       plate below, so W-M-LS ties plate to plate and only its vertical edge floats. If a
       split stud ever reaches the plate, that tie is gone.
    3. **W-M-HS4 hosts nothing, and never may again.** No pipe, no register, no
       wall-mounted device — there is no stud to fasten to and no depth to recess into.
       ``mep.pocket_occupancy`` enforces it; this pins the wall was empty to begin with.
    """
    from typehaus.resolve.framing.pockets import pocket_segments

    door = next(op for op in catlin_model.openings if op.tag == "D-M-LAUN")
    assert door.type_ref == "DT-POCKET-INT-48"
    assert door.host_wall == "W-M-HS3" and door.pocket_sign == 1

    segments, shortfall = pocket_segments(catlin_model.plan, catlin_model, door)
    assert shortfall == pytest.approx(0.0)
    assert [segment.wall_tag for segment in segments] == ["W-M-HS3", "W-M-HS4"]

    # (1) The far end of the framing, in absolute plan x, against N-M-C2 at 18'-0".
    hs4 = catlin_model.wall("W-M-HS4")
    pack = [m for m in catlin_model.wall("W-M-HS3").members
            if m.category in ("king", "jack") and m.p0 == m.p1]
    closed_x = max(m.p0[0] for m in pack)
    assert closed_x < ft(18).meters - inch(6).meters, "the pack must clear the bearing corner"

    # (2) Every split stud stops at the header, well below the 9'-0" plate line.
    splits = [m for m in catlin_model.wall("W-M-HS3").members
              if m.child_key.startswith("pocketsplit-")]
    assert splits, "the cavity must be framed"
    assert all(m.z1_m <= ft(7).meters for m in splits)
    # ...and they really do stand inside W-M-HS4, past their own host's end node.
    assert max(m.p0[0] for m in splits) > hs4.axis[0][0]

    # (3) Nothing else claims W-M-HS4.
    assert not [op for op in catlin_model.openings if op.host_wall == "W-M-HS4"]
    assert not [run for run in catlin_model.pipe_runs
                if "W-M-HS4" in (run.wall_refs or ())]


# --- one grid per facade ------------------------------------------------------------------

#: The four exterior layout lines, named by a wall on each (→ resolve/layout_lines.py).
FACADE_WALLS = ("W-M-N1", "W-M-S1", "W-M-E1", "W-M-W1")


def _facade_stations(model, wall_tag: str, category: str, child_prefix: str = ""):
    """``{storey: [station in inches]}`` for one facade line's members of ``category``.

    ``child_prefix`` narrows a category that more than one layer writes into: ``strapping``
    carries both the exterior stand-off band and the plant room's horizontal liner courses,
    and ``truss_block`` carries both girt tiers, of which only the inner one is on the stud
    module (block-2 is deliberately half a bay off it).
    """
    from typehaus.resolve.layout_lines import lines_by_wall

    line = lines_by_wall(model.layout_lines)[wall_tag]
    (ox, oy), (dx, dy) = line.origin, line.direction
    walls = {w.tag: w for w in model.walls}
    out: dict[str, set[float]] = {}
    for member in line.members:
        wall = walls.get(member.wall_tag)
        if wall is None:
            continue
        for framed in wall.members:
            if framed.category != category:
                continue
            if child_prefix and not framed.child_key.startswith(child_prefix):
                continue
            station = ((framed.p0[0] - ox) * dx + (framed.p0[1] - oy) * dy) / inch(1).meters
            out.setdefault(member.storey, set()).add(round(station, 3))
    return {storey: sorted(values) for storey, values in out.items()}


def _off_module(stations) -> list[float]:
    return [s for s in stations if min(s % 16.0, 16.0 - s % 16.0) > 0.02]


@pytest.mark.parametrize("wall_tag", FACADE_WALLS)
def test_each_facade_block_grid_is_one_grid_on_every_storey(catlin_model, wall_tag):
    """The screws that hold the cladding on, and so the line the eye reads off the street.

    The catlin truss (2026-08-26) turned the stand-off on its side: the girts are horizontal
    and it is their BLOCKS that phase-lock to the 16" stud module, one under every course at
    every stud station. So the facade's vertical grid is the block grid now, and the claim is
    the one the outrigger band used to carry — every storey of a facade lays out the identical
    module. What it rules out is the old behaviour, where each of the six or seven wall
    segments a facade is authored as framed its own end piece at the tee it was split at: a
    doubled fastening line on main that the storey above put somewhere else entirely.

    **On-module stations only**, and the exclusion is the interesting half. A girt wall
    carries three kinds of deliberately off-module block: the one at each free course end,
    the pair under every jamb post, and the ones SNAPPED onto a cripple that the opening's
    own rhythm put two inches off the wall's (``GirtFrame.snap``). All three are the
    openings' business, and the openings differ storey to storey. The module underneath them
    does not — 26 stations at 16" o.c. on every facade of every storey, unbroken.
    """
    by_storey = _facade_stations(catlin_model, wall_tag, "truss_block", "block-1-")
    assert set(by_storey) == {"main", "second", "attic"}, by_storey.keys()
    on_module = {storey: [s for s in stations if s not in _off_module(stations)]
                 for storey, stations in by_storey.items()}
    main, second, attic = (on_module["main"], on_module["second"], on_module["attic"])
    assert main == second == attic, (
        f"{wall_tag}: the block grid differs storey to storey\n"
        f"  main   {main}\n  second {second}\n  attic  {attic}")
    assert len(main) >= 20, f"{wall_tag}: only {len(main)} module blocks on a facade"
    gaps = {round(b - a, 3) for a, b in zip(main, main[1:], strict=False)}
    assert gaps <= {16.0}, f"{wall_tag}: the module breaks at {sorted(gaps)}"


@pytest.mark.parametrize("wall_tag", FACADE_WALLS)
def test_no_facade_stud_stands_off_the_module_except_at_a_corner(catlin_model, wall_tag):
    """Studs stack up a facade, and the seam studs were the last thing stopping them.

    A stud is allowed off the module in exactly one place — packed into a building corner,
    where the corner square and not the grid says where it goes, and where every storey packs
    it identically. Anywhere else an off-module stud is a wall segment that framed its own
    end at a tee. (King and jack studs are a different category and are not swept here: a
    jamb pack is deliberately off-module, sitting where its rough opening puts it.)
    """
    by_storey = _facade_stations(catlin_model, wall_tag, "stud")
    corners = (min(min(v) for v in by_storey.values()),
               max(max(v) for v in by_storey.values()))
    for storey, stations in sorted(by_storey.items()):
        strays = [s for s in _off_module(stations)
                  if min(abs(s - corners[0]), abs(s - corners[1])) > inch(6).inches]
        assert not strays, f"{wall_tag} on {storey}: studs off the facade grid at {strays}"


# --- the interior: the centreline bearing line -------------------------------------------
#: The x=18'-0" centreline, named by a wall on it. `LL-W-A-C1` carries `W-M-C1..C5B`,
#: `W-S-C1..C4B` and `W-A-C1..C2` — twelve walls on three storeys — and it is the load path
#: R602.3.3 is written about: `RB-HOUSE` bears on it continuously down to the footings.
CENTRELINE_WALL = "W-A-C1"


def _line_breaks(model, wall_tag: str) -> list[float]:
    """Every station, in inches, where a segment of the line starts or stops.

    A stud that is off the module is only defensible at one of these: it is the end stud of
    a segment whose neighbour does not continue the grid. Anywhere else it is a wall that
    laid its module out from its own start node.
    """
    from typehaus.resolve.layout_lines import lines_by_wall

    line = lines_by_wall(model.layout_lines)[wall_tag]
    walls = {w.tag: w for w in model.walls}
    out: set[float] = set()
    for member in line.members:
        wall = walls.get(member.wall_tag)
        if wall is None:
            continue
        span = math.dist(*wall.axis) / inch(1).meters
        start = member.u_offset_m / inch(1).meters
        out.update((round(start, 3), round(start + member.direction_sign * span, 3)))
    return sorted(out)


def test_the_centreline_bearing_wall_is_one_stud_grid_on_every_storey(catlin_model):
    """The interior analogue of the facade tests above, on the wall that carries the ridge.

    Three storeys used to lay this line out on three different phases, and every one of its
    twelve segments restarted the 16" module at its own start node — on the house's primary
    load path, where "studs directly over the studs below" is a bearing requirement and not
    a facade preference. `CATLIN_INT_2X6_BRG` and `PLANT_INT_2X6_BRG_HUMID` now set
    `layout_origin="line"`, so all three read off one grid.

    The line's origin lands on the house origin here — `_orient` puts it at the extreme
    member end, and this chain happens to end at y=0 — so the grid is *the* 16" grid and the
    assertion can be made in the plan frame rather than relative to the line. That is luck,
    not a property: `LL-W-B-STR` starts at y=216" and its grid will sit 8" off the house's.
    """
    by_storey = _facade_stations(catlin_model, CENTRELINE_WALL, "stud")
    assert {"main", "second", "attic"} <= set(by_storey), sorted(by_storey)

    breaks = _line_breaks(catlin_model, CENTRELINE_WALL)
    shared: set[float] | None = None
    for storey in ("main", "second", "attic"):
        stations = by_storey[storey]
        off = _off_module(stations)
        # Every off-module stud is a segment end. Not "near a corner", as on a facade: an
        # interior line breaks where a room does, so the end studs are wherever the chain
        # stops being provably continuous — 268" on main and second, 310"/370" where the
        # next segment starts somewhere the module does not reach.
        strays = [s for s in off if min(abs(s - b) for b in breaks) > inch(12).inches]
        assert not strays, f"{storey}: studs off the centreline grid at {strays}"
        module = [s for s in stations if s not in off]
        assert len(module) >= 15, f"{storey}: only {len(module)} module studs"
        shared = set(module) if shared is None else (shared & set(module))

    # Not merely "each storey is on a 16" grid" — the same stations, storey to storey. Ten
    # of them run the full height of the house; the rest are where one storey has a door or
    # a segment the others do not.
    assert shared is not None and len(shared) >= 10, sorted(shared or ())


def test_upper_storey_studs_stand_over_studs(catlin_model):
    """The house-wide metric, and the only thing that would catch a later un-stacking.

    Nothing in `checks/` measures this. Walk `model.stack_edges`, skip any lower wall that
    frames no lumber (a stud cannot stack on concrete, and 13 of the 75 edges are pours
    under framed walls), project both walls' studs onto the upper wall's own axis, and count
    the upper studs standing over nothing.

    The pinned number is a ceiling, not a target, and it is not zero and should not be: a
    module stud suppressed under a window on one storey and not the other, and jamb packs at
    different stations because the windows differ, are both correct framing. What the pin
    catches is the whole house drifting back apart — it fell from 113 to 94 when the five
    interior bearing assemblies joined the four facades on `layout_origin="line"`.
    """
    walls = {w.tag: w for w in catlin_model.walls}

    def studs(wall):
        return [m for m in wall.members if m.category == "stud"]

    carriers: dict[str, list[str]] = {}
    for edge in catlin_model.stack_edges:
        lower, upper = walls.get(edge.lower_wall), walls.get(edge.upper_wall)
        if lower is None or upper is None or not frames_structure(lower):
            continue
        carriers.setdefault(edge.upper_wall, []).append(edge.lower_wall)

    tol = inch(0.5).meters
    total, orphans = 0, []
    for upper_tag, lower_tags in sorted(carriers.items()):
        upper = walls[upper_tag]
        (ax, ay), (bx, by) = upper.axis
        span = math.dist((ax, ay), (bx, by))
        dx, dy = (bx - ax) / span, (by - ay) / span

        def station(member, ax=ax, ay=ay, dx=dx, dy=dy):
            return (member.p0[0] - ax) * dx + (member.p0[1] - ay) * dy

        below = [station(b) for tag in lower_tags for b in studs(walls[tag])]
        for stud in studs(upper):
            total += 1
            if not any(abs(station(stud) - b) <= tol for b in below):
                orphans.append(f"{upper_tag}/{stud.child_key}")

    assert total >= 230, f"fixture regression: only {total} stacked studs found"
    assert len(orphans) <= 94, (
        f"{len(orphans)}/{total} upper-storey studs stand over no stud below "
        f"(was 94/237); first offenders {orphans[:12]}")
