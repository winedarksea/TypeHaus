"""WP3.7 — migration equivalence: the new-engine catlin model preserves the old
catlin-house semantics (element counts / dimensions / placements by category),
generalizing the old repo's ``tests/test_catlin_house_ifc.py``.

The old builder's constants are inlined here as the contract (the old repo is being
archived): 36' house at sheathing, 16" o.c., 18' grid, 4:12 hot roof with knee 5' /
ridge 11' over the attic floor, 12" basement walls + 2x2" XPS, 24' ICF garage 12'
north, and the freestanding arched sunken-garden structure.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.quantities import ft, inch
from typehaus.resolve import resolve
from typehaus.source import load_plan

# Old CatlinHouseSpec contract values.
HOUSE_SIZE_FT = 36.0
FRAMING_SPACING_IN = 16.0
GRID_FT = 18.0
KNEE_FT = 5.0
RIDGE_OVER_ATTIC_FT = 11.0
ATTIC_ELEV_FT = 18.0
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
        # 18' clear-span pairs bearing on the west / center / east lines.
        spans = {round(m.length_m / ft(1).meters, 3) for m in joists}
        assert spans == {GRID_FT}


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


def test_roof_matches_old_pitch_knee_and_ridge(catlin_model):
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    eave_ft = roof.eave_z_m / ft(1).meters
    ridge_ft = roof.ridge_z_m / ft(1).meters
    assert eave_ft == pytest.approx(ATTIC_ELEV_FT + KNEE_FT)
    assert ridge_ft == pytest.approx(ATTIC_ELEV_FT + RIDGE_OVER_ATTIC_FT)
    # 4:12 over the 18' half-run; ridge runs N-S; zero overhang (footprint == house).
    assert roof.ridge_direction == "y"
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    assert max(xs) - min(xs) == pytest.approx(ft(HOUSE_SIZE_FT).meters)
    assert max(ys) - min(ys) == pytest.approx(ft(HOUSE_SIZE_FT).meters)
    rise_over_run = (roof.ridge_z_m - roof.eave_z_m) / (ft(HOUSE_SIZE_FT / 2).meters)
    assert rise_over_run == pytest.approx(4.0 / 12.0)


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


def test_sunken_garden_structure_matches_old_spec(catlin_model):
    """One freestanding structure: 7 wall segments, two-tier arches, 18x28 garden."""
    walls = [w for w in catlin_model.walls if w.tag.startswith("W-SG-")]
    assert len(walls) == 7
    assert all(w.is_foundation for w in walls)
    # Two arched walls x two levels x two arches + two side doorways = 10 openings.
    arches = [o for o in catlin_model.openings if o.tag.startswith("AO-")]
    assert len(arches) == 10
    eight_ft_arches = [o for o in arches if o.width_m == pytest.approx(ft(8).meters)]
    assert len(eight_ft_arches) == 8
    garden = next(s for s in catlin_model.solids if s.tag == "SL-SG-FLOOR")
    xs = [p[0] for p in garden.outline]
    ys = [p[1] for p in garden.outline]
    assert max(xs) - min(xs) == pytest.approx(ft(18).meters)
    assert max(ys) - min(ys) == pytest.approx(ft(28).meters)


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
        assert stair.riser_count == 14
        assert stair.riser_height_m <= inch(7.75).meters + 1e-9
        assert stair.tread_depth_m >= inch(10.0).meters - 1e-9


def test_ifc_emission_when_available(catlin_model, tmp_path):
    pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc import emit_ifc

    path = emit_ifc(catlin_model, tmp_path / "catlin.ifc", lod="framed")
    assert path.exists() and path.stat().st_size > 0
