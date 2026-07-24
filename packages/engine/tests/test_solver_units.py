"""WP2/WP4 — solver-level unit tests: configurable corner assemblies + the
``orient`` axis on vertical members.

Builds a minimal wall + assembly double directly (no full house) so these can be
asserted independent of any authored house's geometry.
"""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.model.assembly import FramingSpec, Layer
from typehaus.model.enums import LayerFunction
from typehaus.quantities import inch
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


def test_no_corner_studs_when_wall_does_not_own_a_corner():
    plan, rw = _wall_and_plan("4-stud")
    members = frame_wall(plan, rw, openings=[], corner_start=False)
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
    openings = [(center, inch(14).meters, inch(36).meters, inch(24).meters, False)]
    members = frame_wall(plan, rw, openings=openings)
    assert not [m for m in members if m.category == "header"]
    assert not [m for m in members if m.category in ("king", "jack")]
    assert any(m.child_key.startswith("roughhead-") for m in members)
    assert any(m.category == "sill" for m in members)


def test_window_that_breaks_a_stud_line_gets_a_header():
    plan, rw = _wall_and_plan("3-stud")
    # A 30" window centered on a stud line breaks the run and needs a header.
    openings = [(2.0, inch(30).meters, inch(36).meters, inch(24).meters, False)]
    members = frame_wall(plan, rw, openings=openings)
    assert [m for m in members if m.category == "header"]
    assert [m for m in members if m.category == "jack"]
