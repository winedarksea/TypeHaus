"""``structural.wall_post_opening_clearance`` / ``structural.wall_post_bearing``, and the
stud-height plate cut in ``resolve/framing/posts.py``.

A synthetic two-storey fixture: one 16' framed wall per storey on the same line, a 3'
window centred in the upper one, and 6x6 posts standing in the upper wall's stud line.
Studs are 16" o.c. from the start node on both storeys.
"""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.checks.structural.wall_posts import wall_post_bearing, wall_post_opening_clearance
from typehaus.findings import Result
from typehaus.model import (
    Library,
    Node,
    PlanModel,
    Post,
    Storey,
    Wall,
    Window,
    WindowType,
    ft,
    inch,
    pt,
)
from typehaus.model.refs import centered

_IN = 0.0254


def _plan(project, wall_assembly, posts: dict[str, float], height=None) -> PlanModel:
    """``posts`` maps a tag to its station in inches along the upper wall."""
    materials, asm = wall_assembly
    library = Library(materials=materials, assemblies=(asm,),
                      window_types=(WindowType(tag="WT-3", width=ft(3), height=ft(4),
                                               u_factor=None, shgc=0.4),))
    storeys = (Storey(uid="ST00000WP1", tag="main", elevation=ft(0),
                      default_ceiling_height=ft(9)),
               Storey(uid="ST00000WP2", tag="second", elevation=ft(10),
                      default_ceiling_height=ft(9)))
    plan = PlanModel(project=project, library=library, storeys=storeys)
    for storey, s in (("main", "M"), ("second", "S")):
        nodes = (Node(uid=f"N0000WP{s}1", tag=f"N-{s}-A", position=pt(ft(0), ft(0)),
                      open_end=True),
                 Node(uid=f"N0000WP{s}2", tag=f"N-{s}-B", position=pt(ft(16), ft(0)),
                      open_end=True))
        wall = Wall(uid=f"W0000WP{s}1", tag=f"W-{s}", start_node=f"N-{s}-A",
                    end_node=f"N-{s}-B", assembly="EXT", top=ft(9))
        elements = [*nodes, wall]
        if storey == "second":
            elements.append(Window(uid="WN0000WPS1", tag="WIN-S", host="W-S",
                                   type_ref="WT-3", position=centered(), sill_height=ft(3)))
            elements.extend(
                Post(uid=f"P0000WP{i}", tag=tag, position=pt(inch(station), inch(0)),
                     size="6x6", height=height, within_wall="W-S")
                for i, (tag, station) in enumerate(posts.items()))
        plan = plan.with_elements(storey, tuple(elements))
    return plan


def _by_post(findings):
    return {f.element_tags[0]: f for f in findings}


def test_a_post_in_the_window_fails_and_one_clear_of_it_passes(project, wall_assembly):
    ctx = check_context(_plan(project, wall_assembly, {"P-IN": 96.0, "P-CLEAR": 32.0}))
    found = _by_post(wall_post_opening_clearance(ctx))
    assert found["P-IN"].result is Result.FAIL
    assert "WIN-S" in found["P-IN"].message
    assert found["P-CLEAR"].result is Result.PASS


def test_a_post_on_the_jamb_pack_fails(project, wall_assembly):
    # RO 78..114"; the king's outer face is 3" past it. A post centred 4" past the RO
    # overlaps the pack, not the RO.
    ctx = check_context(_plan(project, wall_assembly, {"P-PACK": 118.0}))
    finding = _by_post(wall_post_opening_clearance(ctx))["P-PACK"]
    assert finding.result is Result.FAIL, finding.message


def test_a_post_over_a_stud_passes_and_one_mid_bay_fails(project, wall_assembly):
    ctx = check_context(_plan(project, wall_assembly, {"P-STUD": 32.0, "P-BAY": 40.0}))
    found = _by_post(wall_post_bearing(ctx))
    assert found["P-STUD"].result is Result.PASS
    assert "W-M:" in found["P-STUD"].message
    assert found["P-BAY"].result is Result.FAIL
    assert "nearest is W-M:" in found["P-BAY"].message


def test_no_wall_post_is_not_applicable(project, wall_assembly):
    ctx = check_context(_plan(project, wall_assembly, {}))
    assert [f.result for f in wall_post_opening_clearance(ctx)] == [Result.NOT_APPLICABLE]
    assert [f.result for f in wall_post_bearing(ctx)] == [Result.NOT_APPLICABLE]


def _plates(ctx, wall_tag):
    wall = next(w for w in ctx.model.walls if w.tag == wall_tag)
    return sorted(m.child_key for m in wall.members if m.category == "plate")


def test_a_stud_height_post_cuts_the_sole_plate_only(project, wall_assembly):
    # 9' of framing less the 3" double top plate, seated on the deck.
    ctx = check_context(_plan(project, wall_assembly, {"P-STUD": 32.0},
                              height=inch(104.25)))
    assert _plates(ctx, "W-S") == ["plate-bottom-0", "plate-bottom-1",
                                   "plate-top-0", "plate-top-1"]
    assert not [f for f in ctx.resolve_findings
                if f.check_id == "integrity.post_within_wall_short"]


@pytest.mark.parametrize("height", [None, ft(9)])
def test_a_full_height_post_cuts_every_course(project, wall_assembly, height):
    ctx = check_context(_plan(project, wall_assembly, {"P-FULL": 32.0}, height=height))
    assert _plates(ctx, "W-S") == ["plate-bottom-0", "plate-bottom-1",
                                   "plate-top-0-0", "plate-top-0-1",
                                   "plate-top-1-0", "plate-top-1-1"]


def test_a_pedestal_still_warns(project, wall_assembly):
    ctx = check_context(_plan(project, wall_assembly, {"P-PED": 32.0}, height=ft(4)))
    assert [f.element_tags[0] for f in ctx.resolve_findings
            if f.check_id == "integrity.post_within_wall_short"] == ["P-PED"]
