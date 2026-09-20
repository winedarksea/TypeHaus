"""The partition top's published SDPW row, and the blocking its screws land in.

Three things are pinned here:

1. **The TJI 230's flange is 1-1/4"**, per Weyerhaeuser TB-808 Table 1. It carried 1.5" —
   a figure nothing published — and the SDPW's 1-1/8" minimum supporting-flange guard is
   answered off exactly this number.
2. **The spacing row is a GROUP item, keyed on the lowest partition tag**, and every guard
   it states is answered from the model. A row citing a Weyerhaeuser table is a drift
   UNKNOWN, never a PASS: TB-206 fn [1] puts a 0.195" shank outside its own nail spacings.
3. **A partition standing in a joist bay gets blocking over it**, at the framing module the
   screw count already uses — and reading that blocking back as "structure over the wall"
   would re-derive the count from its own answer, so it is excluded.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential.profile import MN_2020
from typehaus.checks.registry import CheckContext, Preferences
from typehaus.checks.structural.partition_fasteners import (
    _CHECK_ID,
    partition_deflection_spacing,
)
from typehaus.findings import Result
from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG
from typehaus.model.refs import PublishedSpan
from typehaus.quantities import ft, inch
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.partition_fasteners import (
    BETWEEN_MEMBERS,
    PARTITION_BLOCK_PREFIX,
    partition_top_joints,
)

_IN = 0.0254
_RULES = CONFIG.partition_deflection


def test_the_tji_230_flange_is_an_inch_and_a_quarter() -> None:
    """TB-808 Table 1: 1-1/4" for the 110/210/230, 1-3/8" only for the 360/560."""
    section = cross_section("11.875 TJI 230")
    assert section is not None
    assert round(section.flange_thickness_m / _IN, 6) == 1.25


def test_every_partition_top_joint_answers_its_own_guards(catlin_model_ro) -> None:
    """Flange thickness, edge distance and the plate condition come out of the model."""
    joints, _refusals = partition_top_joints(catlin_model_ro, _RULES)
    assert joints, "catlin frames interior partitions under framed decks"
    for joint in joints:
        assert joint.plate_condition == "double 2x top plate"
        assert -_RULES.gap_search_tolerance_in <= joint.gap_in <= _RULES.maximum_gap_in
        for section in joint.supports:
            assert section.shape is not None, joint.wall_tag
            thickness = section.flange_thickness_in or section.depth_in
            assert thickness is not None and thickness >= 0.75, joint.wall_tag


def test_the_spacing_row_is_read_and_passes(catlin_model_ro) -> None:
    """One group finding, keyed on the lowest partition tag, against the authored row."""
    ctx = CheckContext(plan=catlin_model_ro.plan, model=catlin_model_ro,
                       preferences=Preferences(), profile=MN_2020)
    findings = partition_deflection_spacing(ctx)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.check_id == _CHECK_ID
    assert finding.result is Result.PASS, finding.message
    assert "W-A-BA-E" in finding.element_tags


def test_no_weyerhaeuser_spacing_row_may_be_cited(catlin_model_ro) -> None:
    """Guard 11 — and it is the one that makes the row honest."""
    plan = catlin_model_ro.plan
    wall = plan.by_tag("W-A-BA-E")
    swapped = wall.model_copy(update={"published_span": PublishedSpan(
        source="Weyerhaeuser TB-206 Fastener Spacing in Weyerhaeuser EWP, Table 1",
        table="16d common, wide face of flange, TJI 110/210/230: 6 in o.c.",
        member="11.875 TJI 230", span=inch(6), carried_span=ft(10), load_psf=5.0,
        condition="the nearest published row, quoted as if it covered this fastener")})
    ctx = CheckContext(plan=_with_wall(plan, swapped), model=catlin_model_ro,
                       preferences=Preferences(), profile=MN_2020)
    finding = partition_deflection_spacing(ctx)[0]
    assert finding.result is Result.UNKNOWN
    assert "no Weyerhaeuser spacing row may be quoted" in finding.message


def test_a_partition_in_a_bay_is_blocked_over(catlin_model_ro) -> None:
    """The mirror joint: blocking between the joists above, at the screws' own module."""
    blocks = {member.child_key for floor in catlin_model_ro.floors
              for member in floor.members
              if member.child_key.startswith(PARTITION_BLOCK_PREFIX)}
    assert blocks, "catlin has partitions standing in a joist bay"
    assert any(key.startswith(f"{PARTITION_BLOCK_PREFIX}W-M-HS4-") for key in blocks)


def test_the_blocking_is_not_read_back_as_the_structure_above(catlin_model_ro) -> None:
    """Or the count would be derived from its own answer.

    Every wall this pass blocks must still classify as BETWEEN the members — if the block
    it laid counted as a crossing, the wall would flip to one screw per block and the
    take-off would bill a different number from the one the blocking was laid at.
    """
    joints, _refusals = partition_top_joints(catlin_model_ro, _RULES)
    between = {joint.wall_tag for joint in joints if joint.scope == BETWEEN_MEMBERS}
    blocked = {member.child_key[len(PARTITION_BLOCK_PREFIX):].rsplit("-", 1)[0]
               for floor in catlin_model_ro.floors for member in floor.members
               if member.child_key.startswith(PARTITION_BLOCK_PREFIX)}
    unexplained = {tag for tag in blocked if not any(tag.startswith(w) for w in between)}
    assert not unexplained, unexplained


def _with_wall(plan, wall):
    """``plan`` with one wall replaced — the model elements are pydantic, so copy."""
    elements = dict(plan.elements)
    for storey, members in elements.items():
        if any(getattr(item, "tag", None) == wall.tag for item in members):
            elements[storey] = tuple(
                wall if getattr(item, "tag", None) == wall.tag else item
                for item in members)
            return plan.model_copy(update={"elements": elements})
    raise AssertionError(f"{wall.tag} is not in the plan")
