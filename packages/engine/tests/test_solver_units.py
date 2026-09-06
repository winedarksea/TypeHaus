"""WP2/WP4 — solver-level unit tests: configurable corner assemblies + the
``orient`` axis on vertical members.

Builds a minimal wall + assembly double directly (no full house) so these can be
asserted independent of any authored house's geometry.
"""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.model.assembly import FramingSpec, Layer
from typehaus.model.enums import LayerFunction, PartitionLayout
from typehaus.quantities import inch
from typehaus.resolve.framing.openings import WallOpening
from typehaus.resolve.framing.solver import frame_wall
from typehaus.resolve.model import ResolvedWall


def _wall_and_plan(corner_style: str) -> tuple[SimpleNamespace, ResolvedWall]:
    layer = Layer(name="stud", material_ref="spf", thickness=inch(3.5),
                 function=LayerFunction.STRUCTURE,
                 framing=FramingSpec(member="2x4", corner_style=corner_style))
    plan = SimpleNamespace(
        library=SimpleNamespace(resolve_assembly=lambda tag: SimpleNamespace(layers=(layer,)))
    )
    rw = ResolvedWall(
        uid="W1", tag="W-TEST", storey="MAIN", assembly="TEST_ASM",
        axis=((0.0, 0.0), (4.0, 0.0)), layers=(), z0_m=0.0, z1_m=2.5,
    )
    return plan, rw


def test_default_corner_style_emits_one_supplemental_stud():
    plan, rw = _wall_and_plan("3-stud")
    members = frame_wall(plan, rw, openings=[], corner_start=True)
    corners = [m for m in members if m.category == "corner"]
    assert len(corners) == 1


def test_four_stud_corner_style_emits_two_supplemental_studs():
    plan, rw = _wall_and_plan("4-stud")
    members = frame_wall(plan, rw, openings=[], corner_start=True)
    corners = [m for m in members if m.category == "corner"]
    assert len(corners) == 2
    keys = {m.child_key for m in corners}
    assert keys == {"corner-start", "corner-start-2"}


def test_per_end_corner_style_override_beats_the_assembly_style():
    """``Wall.corner_style_start/end`` wins over ``FramingSpec.corner_style`` at its own
    end only — the override belongs to the end that hosts the supplemental studs."""
    plan, rw = _wall_and_plan("3-stud")
    members = frame_wall(plan, rw, openings=[], corner_start=True,
                         corner_style_start="4-stud")
    keys = {m.child_key for m in members if m.category == "corner"}
    assert keys == {"corner-start", "corner-start-2"}

    # The override at one end never leaks to the other: the far corner stays 3-stud.
    members = frame_wall(plan, rw, openings=[], corner_start=True, corner_end=True,
                         corner_style_end="4-stud")
    keys = {m.child_key for m in members if m.category == "corner"}
    assert keys == {"corner-start", "corner-end", "corner-end-2"}


def test_per_end_corner_style_can_relax_a_four_stud_assembly_to_three():
    plan, rw = _wall_and_plan("4-stud")
    members = frame_wall(plan, rw, openings=[], corner_start=True,
                         corner_style_start="3-stud")
    assert len([m for m in members if m.category == "corner"]) == 1


def test_no_corner_studs_when_wall_does_not_own_a_corner():
    plan, rw = _wall_and_plan("4-stud")
    members = frame_wall(plan, rw, openings=[], corner_start=False)
    assert not [m for m in members if m.category == "corner"]


def test_butting_wall_never_frames_studs_off_its_own_authored_override():
    """``butting_start=True`` + an authored ``corner_style_start`` on THIS wall: still zero
    corner studs on this end.

    The supplemental pack lives entirely on the OWNER's side of an L corner; a wall butting
    that corner never gets one of its own, no matter what its own authored override says.
    ``frame_model`` (solver.py) is where that authored value travels to the neighbour that
    DOES own the corner — this is the unit-level half of the contract, pinning that
    ``frame_wall`` itself never honours a style at an end it does not own.
    """
    plan, rw = _wall_and_plan("3-stud")
    members = frame_wall(plan, rw, openings=[], corner_start=False, butting_start=True,
                         corner_style_start="4-stud")
    assert not [m for m in members if m.category == "corner"]


def test_vertical_members_carry_orient_but_plates_do_not():
    plan, rw = _wall_and_plan("3-stud")
    members = frame_wall(plan, rw, openings=[], corner_start=True)
    vertical = [m for m in members if m.p0 == m.p1]
    assert vertical and all(m.orient == (1.0, 0.0) for m in vertical)
    plates = [m for m in members if m.category == "plate"]
    assert plates and all(m.orient is None for m in plates)


def test_end_owned_corner_offsets_inward_from_far_endpoint():
    plan, rw = _wall_and_plan("3-stud")
    members = frame_wall(plan, rw, openings=[], corner_end=True)
    corner = next(member for member in members if member.category == "corner")
    assert corner.child_key == "corner-end"
    assert 0.0 < corner.p0[0] < rw.axis[1][0]


def test_ladder_and_stud_pack_tee_backing_are_configurable():
    plan, rw = _wall_and_plan("3-stud")
    ladder = frame_wall(plan, rw, openings=[], tee_stations=((2.0, "N-T"),))
    assert any(member.category == "blocking" for member in ladder)

    structure = plan.library.resolve_assembly("TEST_ASM").layers[0]
    packed = structure.model_copy(update={
        "framing": structure.framing.model_copy(update={"tee_backing_style": "stud-pack"})
    })
    plan.library.resolve_assembly = lambda _tag: SimpleNamespace(layers=(packed,))
    stud_pack = frame_wall(plan, rw, openings=[], tee_stations=((2.0, "N-T"),))
    assert len([member for member in stud_pack
                if member.child_key.startswith("tee-N-T-stud-")]) == 2


def test_ladder_tee_backing_omits_only_the_rung_intersecting_opening_framing():
    plan, rw = _wall_and_plan("3-stud")
    tee_station = 2.0
    baseline = frame_wall(plan, rw, openings=[], tee_stations=((tee_station, "N-T"),))
    baseline_rungs = {
        member.child_key for member in baseline
        if member.child_key.startswith("tee-N-T-block-")
    }
    opening = WallOpening(
        center_m=tee_station,
        width_m=inch(27).meters,
        height_m=inch(36).meters,
        sill_m=inch(36).meters,
        is_door=False,
    )

    framed = frame_wall(plan, rw, openings=[opening], tee_stations=((tee_station, "N-T"),))
    retained_rungs = {
        member.child_key for member in framed
        if member.child_key.startswith("tee-N-T-block-")
    }

    assert baseline_rungs - retained_rungs == {"tee-N-T-block-02"}
    assert retained_rungs == baseline_rungs - {"tee-N-T-block-02"}
    assert any(member.category == "header" for member in framed)


def _wall_and_plan_with_blocking(heights) -> tuple[SimpleNamespace, ResolvedWall]:
    layer = Layer(name="stud", material_ref="spf", thickness=inch(3.5),
                 function=LayerFunction.STRUCTURE,
                 framing=FramingSpec(member="2x4", blocking_heights=heights))
    plan = SimpleNamespace(
        library=SimpleNamespace(resolve_assembly=lambda tag: SimpleNamespace(layers=(layer,)))
    )
    rw = ResolvedWall(
        uid="W1", tag="W-TEST", storey="MAIN", assembly="TEST_ASM",
        axis=((0.0, 0.0), (4.0, 0.0)), layers=(), z0_m=0.0, z1_m=2.5,
    )
    return plan, rw


def test_blocking_heights_emit_one_course_per_bay_between_studs():
    plan, rw = _wall_and_plan_with_blocking((inch(48),))
    members = frame_wall(plan, rw, openings=[])
    studs = [m for m in members if m.category == "stud"]
    blocks = [m for m in members if m.child_key.startswith("blocking-")]
    # One block fills each bay between consecutive studs.
    assert len(blocks) == len(studs) - 1
    plate_h = inch(1.5).meters
    expected_base = rw.z0_m + plate_h + inch(48).meters
    assert all(m.category == "blocking" for m in blocks)
    assert all(abs(m.z0_m - expected_base) < 1e-9 for m in blocks)
    # Each block is horizontal (p0 != p1) and butts inside its bay.
    assert all(m.p0 != m.p1 and m.length_m > 0 for m in blocks)


def test_no_blocking_by_default():
    plan, rw = _wall_and_plan_with_blocking(())
    members = frame_wall(plan, rw, openings=[])
    assert not [m for m in members if m.child_key.startswith("blocking-")]


def test_window_that_fits_in_a_bay_gets_no_structural_header():
    plan, rw = _wall_and_plan("3-stud")
    # A 14" window (< 16" module) centered on a bay center (4.5 modules) breaks no stud.
    center = 4.5 * inch(16).meters
    openings = [WallOpening(center, inch(14).meters, inch(36).meters, inch(24).meters, False)]
    members = frame_wall(plan, rw, openings=openings)
    assert not [m for m in members if m.category == "header"]
    assert not [m for m in members if m.category in ("king", "jack")]
    assert any(m.child_key.startswith("roughhead-") for m in members)
    assert any(m.category == "sill" for m in members)


def test_window_that_breaks_a_stud_line_gets_a_header():
    plan, rw = _wall_and_plan("3-stud")
    # A 30" window centered on a stud line breaks the run and needs a header.
    openings = [WallOpening(2.0, inch(30).meters, inch(36).meters, inch(24).meters, False)]
    members = frame_wall(plan, rw, openings=openings)
    assert [m for m in members if m.category == "header"]
    assert [m for m in members if m.category == "jack"]


def _stations_by_category(members) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for m in members:
        if m.p0 == m.p1:  # vertical members carry their station in x (wall runs along +x)
            out.setdefault(m.category, []).append(m.p0[0])
    return out


def test_module_stud_a_half_thickness_past_the_pack_face_is_excluded():
    """Regression: the exclusion band used to end at the pack's outer *face*, but module
    studs are tested by *centreline* — a station in the half-thickness sliver beyond the
    face body-overlapped the outer king (catlin W-M-C3 stud-001 vs king-0-r0)."""
    plan, rw = _wall_and_plan("3-stud")
    # 30" opening centered at 0.75 m: the 48" module station (1.2192 m) lands 2.9 mm past
    # the old band end (1.2122 m) and half-overlaps the king at 1.188 m.
    openings = [WallOpening(0.75, inch(30).meters, inch(80).meters, 0.0, True)]
    members = frame_wall(plan, rw, openings=openings)
    stations = _stations_by_category(members)
    thickness = inch(1.5).meters
    for stud in stations.get("stud", []):
        for pack in stations.get("king", []) + stations.get("jack", []):
            assert abs(stud - pack) >= thickness - 1e-9, (stud, pack)


def test_staggered_wall_module_studs_clear_the_jamb_pack():
    """Same property on a staggered partition (catlin W-S-SBS stud-000 vs king-0-r0):
    module studs ride the half-spacing combined rhythm, and the exclusion band must be
    judged against that same rhythm."""
    layer = Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                  function=LayerFunction.STRUCTURE,
                  framing=FramingSpec(member="2x4", plate_member="2x6",
                                      layout=PartitionLayout.STAGGERED))
    plan = SimpleNamespace(
        library=SimpleNamespace(resolve_assembly=lambda tag: SimpleNamespace(layers=(layer,)))
    )
    rw = ResolvedWall(
        uid="W1", tag="W-TEST", storey="MAIN", assembly="TEST_ASM",
        axis=((0.0, 0.0), (4.0, 0.0)), layers=(), z0_m=0.0, z1_m=2.5,
    )
    openings = [WallOpening(0.75, inch(30).meters, inch(80).meters, 0.0, True)]
    members = frame_wall(plan, rw, openings=openings)
    stations = _stations_by_category(members)
    thickness = inch(1.5).meters
    assert stations.get("king"), "the 30\" door must still get its pack"
    for stud in stations.get("stud", []):
        for pack in stations.get("king", []) + stations.get("jack", []):
            assert abs(stud - pack) >= thickness - 1e-9, (stud, pack)


# --- california corners ------------------------------------------------------------
#
# The third corner style: the same stick count as "3-stud", but the supplemental stud is
# laid FLAT so the corner cavity stays open to insulation. Two things follow, and both are
# pinned here because neither shows up in a member count: the backer is turned across the
# wall axis, and it eats its DEPTH (3-1/2") of that axis rather than its thickness.

_INCH_M = 0.0254
_STUD_THICKNESS_M = 1.5 * _INCH_M
_STUD_DEPTH_M = 3.5 * _INCH_M


def test_california_corner_style_validates_on_the_schema():
    """The literal is spelled the same way in all three places that speak it."""
    from typehaus.model.elements import Wall

    spec = FramingSpec(member="2x4", corner_style="california")
    assert spec.corner_style == "california"
    wall = Wall(tag="W-X", start_node="N1", end_node="N2", assembly="EXT",
                corner_style_start="california", corner_style_end="california")
    assert (wall.corner_style_start, wall.corner_style_end) == ("california", "california")


def test_california_corner_emits_one_flat_supplemental_stud():
    plan, rw = _wall_and_plan("california")
    corners = [m for m in frame_wall(plan, rw, openings=[], corner_start=True)
               if m.category == "corner"]
    assert [m.child_key for m in corners] == ["corner-start"]
    # Laid flat: turned across the wall axis, which runs +x here.
    assert corners[0].orient == (0.0, 1.0)


def test_on_edge_corner_styles_keep_the_wall_axis_orientation():
    for style in ("3-stud", "4-stud"):
        plan, rw = _wall_and_plan(style)
        corners = [m for m in frame_wall(plan, rw, openings=[], corner_start=True)
                   if m.category == "corner"]
        assert corners and all(m.orient == (1.0, 0.0) for m in corners), style


def test_california_backer_consumes_its_depth_of_the_wall_axis():
    """3-1/2" of axis, not 1-1/2": the backer's centre sits half a thickness plus half a
    depth inboard of the end stud, so the two faces touch."""
    from typehaus.resolve.framing.corners import WallEndFraming, corner_stud_stations

    end = WallEndFraming(plate_station_m=0.0, end_stud_station_m=_STUD_THICKNESS_M / 2.0)
    (backer,) = corner_stud_stations(end, True, _STUD_THICKNESS_M, "california",
                                     axis_len_m=4.0, stud_depth_m=_STUD_DEPTH_M)
    assert backer.laid_flat is True
    assert backer.along_axis_m == _STUD_DEPTH_M
    expected = end.end_stud_station_m + (_STUD_THICKNESS_M + _STUD_DEPTH_M) / 2.0
    assert backer.station_m == expected
    # Faces touch: the end stud's inboard face and the backer's outboard face coincide.
    assert abs((backer.station_m - _STUD_DEPTH_M / 2.0)
               - (end.end_stud_station_m + _STUD_THICKNESS_M / 2.0)) < 1e-12


def test_corner_stud_stations_reports_stations_and_orientation_for_every_style():
    from typehaus.resolve.framing.corners import WallEndFraming, corner_stud_stations

    end = WallEndFraming(plate_station_m=0.0, end_stud_station_m=_STUD_THICKNESS_M / 2.0)
    kwargs = dict(axis_len_m=4.0, stud_depth_m=_STUD_DEPTH_M)

    three = corner_stud_stations(end, True, _STUD_THICKNESS_M, "3-stud", **kwargs)
    assert [(s.station_m, s.along_axis_m, s.laid_flat) for s in three] == [
        (end.end_stud_station_m + _STUD_THICKNESS_M, _STUD_THICKNESS_M, False)]

    four = corner_stud_stations(end, True, _STUD_THICKNESS_M, "4-stud", **kwargs)
    assert [(s.station_m, s.along_axis_m, s.laid_flat) for s in four] == [
        (end.end_stud_station_m + _STUD_THICKNESS_M, _STUD_THICKNESS_M, False),
        (end.end_stud_station_m + 2 * _STUD_THICKNESS_M, _STUD_THICKNESS_M, False)]

    cal = corner_stud_stations(end, True, _STUD_THICKNESS_M, "california", **kwargs)
    assert [(s.along_axis_m, s.laid_flat) for s in cal] == [(_STUD_DEPTH_M, True)]


def test_corner_stud_stations_runs_inboard_from_the_far_end():
    """``at_start=False`` packs toward decreasing station — same arithmetic, mirrored."""
    from typehaus.resolve.framing.corners import WallEndFraming, corner_stud_stations

    axis_len = 4.0
    end = WallEndFraming(plate_station_m=axis_len,
                         end_stud_station_m=axis_len - _STUD_THICKNESS_M / 2.0)
    (backer,) = corner_stud_stations(end, False, _STUD_THICKNESS_M, "california",
                                     axis_len_m=axis_len, stud_depth_m=_STUD_DEPTH_M)
    assert backer.station_m == end.end_stud_station_m - (_STUD_THICKNESS_M
                                                         + _STUD_DEPTH_M) / 2.0


def test_midpoint_guard_drops_a_backer_that_would_reach_past_the_wall_centre():
    """The guard grades the stud's INBOARD FACE, so it measures the flat backer's 3-1/2"
    and not some single constant — a stub wall that comfortably holds an on-edge stud can
    still be too short for a california backer."""
    from typehaus.resolve.framing.corners import WallEndFraming, corner_stud_stations

    # 7" stub: midpoint at 3.5". The on-edge stud's inboard face lands at 3" (kept); the
    # flat backer's at 5" (dropped), as does the 4-stud pack's second stud at 4.5".
    axis_len = 7.0 * _INCH_M
    end = WallEndFraming(plate_station_m=0.0, end_stud_station_m=_STUD_THICKNESS_M / 2.0)
    kwargs = dict(axis_len_m=axis_len, stud_depth_m=_STUD_DEPTH_M)
    assert len(corner_stud_stations(end, True, _STUD_THICKNESS_M, "3-stud", **kwargs)) == 1
    assert corner_stud_stations(end, True, _STUD_THICKNESS_M, "california", **kwargs) == ()
    # ...and the second stud of a 4-stud pack goes the same way, at 3.75".
    assert len(corner_stud_stations(end, True, _STUD_THICKNESS_M, "4-stud", **kwargs)) == 1


def test_california_corner_needs_a_stud_depth():
    """The flat backer has no station without one; a silent fallback to the thickness
    would place it 1" out and nothing downstream would notice."""
    import pytest

    from typehaus.resolve.framing.corners import WallEndFraming, corner_stud_stations

    end = WallEndFraming(plate_station_m=0.0, end_stud_station_m=_STUD_THICKNESS_M / 2.0)
    with pytest.raises(ValueError):
        corner_stud_stations(end, True, _STUD_THICKNESS_M, "california", axis_len_m=4.0)


def test_module_studs_clear_the_flat_backers_face_not_its_centre():
    """A module stud is kept one stud thickness off the pack. Measured from the backer's
    CENTRE that clearance would cut 1" into its face, so the california wall's first
    module stud stands further in than the 3-stud wall's."""
    plan, rw = _wall_and_plan("california")
    california = frame_wall(plan, rw, openings=[], corner_start=True)
    plan, rw = _wall_and_plan("3-stud")
    three = frame_wall(plan, rw, openings=[], corner_start=True)

    def first_module(members):
        return min(m.p0[0] for m in members
                   if m.category == "stud" and m.p0[0] > inch(1).meters)

    assert first_module(california) >= first_module(three)
