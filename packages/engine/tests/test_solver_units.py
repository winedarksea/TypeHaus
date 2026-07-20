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
