"""The Image II roof pieces are drawn from the Residential Design Manual's own dimensions.

Each leg below is read off the manual's stretch-out labels (pp. 6-12, see
``houses/catlin/notes/metal_trim_kit.md``). Open hems are drawn as two plies with a real gap,
so a fold adds a short connector the stretch-out does not count.
"""

import dataclasses
import math
from types import SimpleNamespace

import pytest

from typehaus.library.trim._image_ii import (
    IMAGE_II_OFFSET_CLEAT,
    IMAGE_II_RAKE_CLEAT,
    IMAGE_II_RESIDENTIAL_RAKE,
    IMAGE_II_RIDGE_COVER,
    IMAGE_II_Z_CLOSURE,
    SHEET_24_GA_IN,
    eave_catalog_reach_in,
    extended_eave_section,
    hem_offset_in,
    rake_deck_flange_in,
)
from typehaus.library.trim.metal_sales import RESIDENTIAL_RAKE_FACE_IN
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.roof_edge_geometry import (
    abutted_run_keys,
    roof_edge_runs,
    roof_ridge_run,
    roof_slope,
)
from typehaus.resolve.roof_image_ii import (
    RAKE_BELOW_HEAD_M,
    wrapped_image_ii_edges,
)
from typehaus.resolve.roof_image_ii_eave import LAP_GAP_M, eave_deck_bearing
from typehaus.resolve.roof_layer_setbacks import above_structure_layers
from typehaus.takeoff.cladding_trim import cladding_trim_takeoff


def _legs(section):
    """Leg lengths, the open hems' fold connectors left out."""
    return [d for a, b in zip(section, section[1:], strict=False)
            if (d := math.dist(a, b)) > hem_offset_in() + 1e-9]


def test_extended_eave_legs_match_the_manual() -> None:
    section = extended_eave_section(6.0 / 12.0)
    hem, leg, ret, face, kick, drip = _legs(section)
    assert (hem, leg, ret, face, kick, drip) == pytest.approx((0.875, 5.0, 1.5, 1.5, 0.625, 0.5))
    assert sum(_legs(section)) == pytest.approx(10.0)       # RDM p. 11 stretch-out
    assert eave_catalog_reach_in() == pytest.approx(3.5)    # 5 in leg less the 1-1/2 lip
    assert rake_deck_flange_in() == pytest.approx(2 + 7 / 8)
    hem_tip, hem_fold, leg_top, lip_top, lip_under, corner, *_ = section
    assert corner == (0.0, 0.0)
    # Both hems lie flat under the leg (no fin), two plies a real gap apart, and the lip
    # is a hook: the leg runs 1-1/2 in past the face and returns under itself to the corner.
    slope = math.atan(0.5)
    up = (math.sin(slope), math.cos(slope))
    for under, over in ((hem_tip, leg_top), (lip_under, lip_top)):
        gap = (over[0] - under[0]) * up[0] + (over[1] - under[1]) * up[1] - 2 * SHEET_24_GA_IN
        assert gap > 0.0
    assert hem_tip[1] - hem_fold[1] == pytest.approx(-0.875 * math.sin(slope))
    assert lip_top[0] > corner[0] + 1.3 and lip_under[1] < lip_top[1]
    # The drip hem folds back inside the kick, clear of it.
    tip, turn, end = section[-3:]
    assert math.dist(tip, turn) > 2 * SHEET_24_GA_IN and math.dist(turn, end) == pytest.approx(0.5)


def test_house_eave_bears_on_the_deck_as_placed(catlin_model_ro) -> None:
    """The bearing is the leg's plan overlap inboard of the deck's top edge.

    Hand calc at 6:12 (cos 0.8944, sin 0.4472): the face's outer surface stands
    1/32 + 0.0239 + 1/32 + 0.0239 = 0.1103 in out (gap, gutter back, gap, face sheet), so the
    leg's inboard end is 0.1103 - 3.5 x 0.8944 = -3.0202 in. The 19/32 in deck is cut square
    to the pitch through its 1-1/4 in setback, so its top corner is at
    -1.25 + 0.59375 x 0.4472 = -0.9845 in. Bearing 3.0202 - 0.9845 = 2.036 in.
    """
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-HOUSE")
    face_u = 2 * LAP_GAP_M / M_PER_IN + 2 * SHEET_24_GA_IN
    sin = math.sin(math.atan(0.5))
    hand = (-1.25 + 0.59375 * sin) - (face_u - 3.5 * math.cos(math.atan(0.5)))
    assert hand == pytest.approx(2.036, abs=1e-3)
    for run in (r for r in roof_edge_runs(roof) if r.is_eave):
        bearing = eave_deck_bearing(catlin_model_ro, roof, run)
        assert bearing.bearing_m / M_PER_IN == pytest.approx(hand, abs=1e-3)


def test_residential_rake_legs_match_the_manual() -> None:
    top_return, main, kick, hem = _legs(IMAGE_II_RESIDENTIAL_RAKE.section_in)
    assert top_return == pytest.approx(1.0)   # 1 in return over the panel turn-up
    assert main == pytest.approx(RESIDENTIAL_RAKE_FACE_IN) == pytest.approx(2.625)
    assert kick == pytest.approx(0.625)
    assert hem == pytest.approx(0.5)          # 1/2 in open hem folded back inside the kick
    assert max(z for _, z in IMAGE_II_RESIDENTIAL_RAKE.section_in) == pytest.approx(2.625)


def test_rake_cleat_offset_cleat_and_z_closure_match_the_manual() -> None:
    assert sum(_legs(IMAGE_II_RAKE_CLEAT.section_in)) == pytest.approx(5.0)
    assert _legs(IMAGE_II_RAKE_CLEAT.section_in)[0] == pytest.approx(2 + 7 / 8)
    assert _legs(IMAGE_II_OFFSET_CLEAT.section_in)[::2] == pytest.approx([1.5, 1.0])
    assert sum(_legs(IMAGE_II_OFFSET_CLEAT.section_in)) == pytest.approx(3.0, abs=0.05)
    assert _legs(IMAGE_II_Z_CLOSURE.section_in) == pytest.approx([1.0, 1.0, 1.0])


def test_ridge_cover_has_seven_inch_legs_and_one_inch_hems() -> None:
    left_hem, left, peak, right, right_hem = IMAGE_II_RIDGE_COVER.section_in
    assert math.dist(left, peak) == pytest.approx(7.0)
    assert math.dist(peak, right) == pytest.approx(7.0)
    assert math.dist(left, left_hem) == pytest.approx(1.0)
    assert math.dist(right, right_hem) == pytest.approx(1.0)
    assert sum(_legs(IMAGE_II_RIDGE_COVER.section_in)) == pytest.approx(16.0)


def test_house_rake_is_the_stock_leg_and_covers_the_stack(catlin_model_ro) -> None:
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-HOUSE")
    rakes = [m for m in roof.members if m.connection == "roof:image-ii-rake"]
    assert len(rakes) == 4                    # both rakes on each of the two gable ends
    # Each stops on the eave's leg at its corner: a foot over the leg, clear of it.
    feet = [m for m in roof.members if m.connection == "roof:image-ii-rake-foot"]
    assert len(feet) == 4
    # The stock main leg, billed as the catalog piece with no custom 4 in row.
    rows = {r["part"]: r for r in cladding_trim_takeoff(catlin_model_ro) if r["kind"] == "roof"}
    assert "IMAGE_II_RAKE_4IN_CUSTOM" not in rows
    assert all(r.connection != "roof:panel-rake" for r in roof.members)
    # The face must cover the roofing above the wall head plus the lap that hides the
    # 3/4 in Universal Closure: 1 in below the head, so the leg needs roofing + 1 in.
    layers = above_structure_layers(catlin_model_ro.plan.library.resolve_assembly(roof.assembly))
    roofing = next(layer for layer in layers if layer.name == "roofing")
    factor = math.hypot(1.0, roof_slope(roof))
    stack_in = roofing.thickness.meters * factor / M_PER_IN
    assert pytest.approx(1.0) == RAKE_BELOW_HEAD_M / M_PER_IN
    required_in = stack_in + RAKE_BELOW_HEAD_M / M_PER_IN
    assert required_in == pytest.approx(2.12, abs=0.02)
    assert required_in <= RESIDENTIAL_RAKE_FACE_IN


def test_garage_vented_peak_is_the_canopy_cover_over_profile_vent(catlin_model_ro) -> None:
    """RDM p. 41 on both slopes under the 7 in cover: one cover, no step at the canopy joint."""
    roofs = {r.tag: r for r in catlin_model_ro.roofs}
    garage, canopy = roofs["RF-GARAGE"], roofs["RF-BW-CANOPY"]
    cap = next(m for m in garage.members if m.category == "ridge_cap")
    canopy_cap = next(m for m in canopy.members if m.category == "ridge_cap")
    assert cap.connection == "ridge:vented-peak" and canopy_cap.connection == "ridge:closed-cap"
    assert cap.section_ring == canopy_cap.section_ring
    assert (cap.z0_m, cap.z1_m) == pytest.approx((canopy_cap.z0_m, canopy_cap.z1_m), abs=1e-9)
    vents = [m for m in garage.members if m.connection == "ridge:profile-vent"]
    assert len(vents) == 2 and not any(m.connection == "ridge:profile-closure"
                                       for m in garage.members)
    ridge = roof_ridge_run(garage)
    half_cover = max(abs(u) for u, _ in cap.section_ring)
    for vent in vents:
        offset = abs(vent.p0[0] - ridge.p0[0])
        width = max(u for u, _ in vent.section_ring) - min(u for u, _ in vent.section_ring)
        # Under the cover's leg and clear of the 2 in deck slot.
        assert offset - width / 2 > 1.0 * M_PER_IN and offset + width / 2 < half_cover
        # A 1 in rib normal to the slope, over a 3-1/8 in clip's fall across it.
        assert vent.z1_m - vent.z0_m == pytest.approx(
            math.hypot(1, 4 / 12) * M_PER_IN + width * 4 / 12)


def test_open_ridge_ends_are_closed_and_the_canopy_joint_is_not(catlin_model_ro) -> None:
    ends = {(r.tag, m.child_key) for r in catlin_model_ro.roofs for m in r.members
            if m.connection == "ridge:end-closure"}
    assert ends == {("RF-HOUSE", "ridge-end-closure-lo"), ("RF-HOUSE", "ridge-end-closure-hi"),
                    ("RF-GARAGE", "ridge-end-closure-hi"),
                    ("RF-BW-CANOPY", "ridge-end-closure-lo")}


def _image_ii_rakes(roof):
    return [m for m in roof.members if m.connection == "roof:image-ii-rake"]


def test_the_garage_south_gable_is_a_seam_not_a_rake(catlin_model_ro) -> None:
    # The canopy's roof runs on across it in the same plane (same slope, same eave and ridge
    # heights), so the garage's south rake is interior: no Image II piece, no barge cleat.
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-GARAGE")
    assert abutted_run_keys(catlin_model_ro, roof) == {"rake-lo-0", "rake-lo-1"}
    assert _image_ii_rakes(roof) == []
    rows = [r for r in cladding_trim_takeoff(catlin_model_ro) if r["kind"] == "roof"]
    cleat = [r for r in rows if r["part"] == "5806199"]
    assert cleat and not any(f"{roof.tag}:rake-lo" in t for r in cleat for t in r["tags"])


def test_the_canopy_north_rake_is_the_same_seam(catlin_model_ro) -> None:
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-BW-CANOPY")
    assert abutted_run_keys(catlin_model_ro, roof) == {"rake-hi-0", "rake-hi-1"}
    assert _image_ii_rakes(roof) == []


def test_the_house_rakes_are_exposed(catlin_model_ro) -> None:
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-HOUSE")
    assert abutted_run_keys(catlin_model_ro, roof) == frozenset()


def test_a_gap_or_a_step_leaves_the_joint_edges_exposed(catlin_model_ro) -> None:
    """The abutment rule is geometric: separate the roofs, or lift one, and the edges return."""
    garage = next(r for r in catlin_model_ro.roofs if r.tag == "RF-GARAGE")
    canopy = next(r for r in catlin_model_ro.roofs if r.tag == "RF-BW-CANOPY")

    # A 0.625 in gap: the canopy's north edge is pulled 1.5 in south of its catalog position.
    pulled = tuple((x, y - inch(1.5).meters if y > 500 * M_PER_IN else y)
                   for x, y in canopy.footprint)
    gapped = SimpleNamespace(roofs=(garage, dataclasses.replace(canopy, footprint=pulled)))
    assert abutted_run_keys(gapped, garage) == frozenset()
    assert abutted_run_keys(gapped, gapped.roofs[1]) == frozenset()

    # A 12 in step: the canopy stands a foot above the garage plane, so neither edge abuts it.
    lifted = dataclasses.replace(canopy, eave_z_m=canopy.eave_z_m + inch(12).meters,
                                 ridge_z_m=canopy.ridge_z_m + inch(12).meters)
    stepped = SimpleNamespace(roofs=(garage, lifted))
    assert abutted_run_keys(stepped, garage) == frozenset()
    assert abutted_run_keys(stepped, lifted) == frozenset()


def test_the_image_ii_gate_is_the_roofing_material_not_the_tag(catlin_model_ro,
                                                               monkeypatch) -> None:
    from typehaus.resolve import roof_image_ii as gate

    house = next(r for r in catlin_model_ro.roofs if r.tag == "RF-HOUSE")
    assert gate.image_ii_members(catlin_model_ro, house)
    assert gate.wrapped_image_ii_edges(catlin_model_ro, house) == frozenset(
        {"west", "east", "north", "south"})

    # The same roof on a covering that names no Image II kit gets no catalog piece at all.
    layers, cladding, material = gate._roofing(catlin_model_ro, house)
    plain = material.model_copy(update={"roof_edge_trim_kit": None})
    monkeypatch.setattr(gate, "_roofing", lambda model, roof: (layers, cladding, plain))
    assert not gate.image_ii_covering(catlin_model_ro, house)
    assert gate.image_ii_members(catlin_model_ro, house) == ()


def test_fascia_edges_keep_the_derived_drip_on_the_garage(catlin_model_ro) -> None:
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-GARAGE")
    # The garage's eaves and north gable carry fascia boards; only the south gable is wrapped.
    assert wrapped_image_ii_edges(catlin_model_ro, roof) == frozenset({"south"})
    drips = {m.child_key for m in roof.members if m.category == "drip_edge"}
    assert "eave-lo-drip-edge-face" in drips and "rake-hi-0-drip-edge-face" in drips
