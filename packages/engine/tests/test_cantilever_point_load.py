"""A post set down on a cantilevered deck (checks/structural/cantilever.py).

Every span table in the model is a uniform-load table, so a pillar standing on the free end
of a joist is a load none of them describe. This check is the rule that says so, and its
whole value is in never going quiet: a post on the overhang is a finding whatever else is
authored — FAIL with nothing carrying it, UNKNOWN once the reinforcement contract is met,
never PASS.

The fixtures are synthetic because catlin has exactly one such post (PT-SG-BR2, on the
porch's 17" north overhang) and it is fully mitigated: it can pin the landed verdict but not
the boundaries, and the boundaries are where a mitigation arm silently stops matching. The
last test pins catlin itself.
"""

from __future__ import annotations

import pytest

from typehaus.checks.registry import CheckContext, Preferences, Tier, registered
from typehaus.checks.structural.cantilever import cantilever_point_load
from typehaus.findings import Result
from typehaus.model import (
    Assembly,
    Building,
    Connector,
    ConnectorKind,
    DeckLayer,
    FloorSystem,
    JoistReinforcement,
    JoistSpec,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    PlanModel,
    Post,
    Project,
    Site,
    Storey,
    StructuralRole,
    Wall,
    degF,
    ft,
    inch,
    pt,
)
from typehaus.resolve import resolve

_MATERIALS = (Material(tag="spf", name="SPF framing", r_per_inch=1.25, perm_rating=2.9),)
_ASSEMBLY = Assembly(tag="EXT", layers=(
    Layer(name="stud", material_ref="spf", thickness=inch(5.5),
          function=LayerFunction.STRUCTURE),
))

# The deck: 16' x 10' between two bearing walls, joists spanning in y at 16" o.c., with a
# 24" overhang past the north wall. So the joist field runs y = 0' .. 12', the back span is
# 0' .. 10', and the band this check is about is 10' .. 12'.
_SPAN_FT = 10.0
_OVERHANG_IN = 24.0
_TIP_FT = _SPAN_FT + _OVERHANG_IN / 12.0
_SPACING_IN = 16.0


def _plan(*, overhang_in: float = _OVERHANG_IN, posts=(), reinforcements=(),
          extras=()) -> PlanModel:
    library = Library(materials=_MATERIALS, assemblies=(_ASSEMBLY,))
    project = Project(name="CANT", project_uuid="00000000-0000-4000-8000-0000000000c1",
                      site=Site(lat=44.9, lon=-93.2, elevation=ft(830),
                                design_temp_heating=degF(-15), design_temp_cooling=degF(90)),
                      building=Building(name="CANT"))
    storey = Storey(uid="ST000000c1", tag="main", elevation=ft(0),
                    default_ceiling_height=ft(9))
    plan = PlanModel(project=project, library=library, storeys=(storey,))
    nodes = (
        Node(uid="N000000c01", tag="N-SW", position=pt(ft(0), ft(0))),
        Node(uid="N000000c02", tag="N-SE", position=pt(ft(16), ft(0))),
        Node(uid="N000000c03", tag="N-NE", position=pt(ft(16), ft(_SPAN_FT))),
        Node(uid="N000000c04", tag="N-NW", position=pt(ft(0), ft(_SPAN_FT))),
    )
    walls = (
        Wall(uid="W000000c01", tag="W-S", start_node="N-SW", end_node="N-SE",
             assembly="EXT", top=ft(9), structural_role=StructuralRole.BEARING),
        Wall(uid="W000000c02", tag="W-E", start_node="N-SE", end_node="N-NE",
             assembly="EXT", top=ft(9)),
        Wall(uid="W000000c03", tag="W-N", start_node="N-NE", end_node="N-NW",
             assembly="EXT", top=ft(9), structural_role=StructuralRole.BEARING),
        Wall(uid="W000000c04", tag="W-W", start_node="N-NW", end_node="N-SW",
             assembly="EXT", top=ft(9)),
    )
    floor = FloorSystem(
        uid="FS000000c1", tag="FS-T",
        joists=JoistSpec(member="2x8", spacing=inch(_SPACING_IN), direction="y",
                         cantilever_end=(inch(overhang_in) if overhang_in else None),
                         bearing_refs=("W-S", "W-N")),
        reinforcements=tuple(reinforcements),
        subfloor=DeckLayer(material_ref="spf", thickness=inch(0.75)),
        service="deck",
    )
    return plan.with_elements("main", (*nodes, *walls, floor, *posts, *extras))


def _context(plan: PlanModel) -> CheckContext:
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], \
        [f.message for f in findings if f.severity.value == "error"]
    return CheckContext(plan=plan, model=model, preferences=Preferences(), profile=None,
                        resolve_findings=list(findings))


def _post(tag: str, x_ft: float, y_ft: float, *, uid: str = "PT000000c1",
          supported_by: str = "FS-T") -> Post:
    return Post(uid=uid, tag=tag, position=pt(ft(x_ft), ft(y_ft)), size="6x6",
                height=ft(8), supported_by=supported_by)


_TIP_POST = _post("PT-TIP", 8.0, _TIP_FT)                      # dead on the joist tips
_INBOARD_POST = _post("PT-IN", 8.0, _SPAN_FT + 0.5)            # 6" out on the overhang
_BACK_SPAN_POST = _post("PT-BACK", 8.0, 5.0)                   # mid back-span


def _findings(**kwargs):
    return cantilever_point_load(_context(_plan(**kwargs)))


def _one(**kwargs):
    findings = _findings(**kwargs)
    assert len(findings) == 1, [f.message for f in findings]
    return findings[0]


# --- the band -------------------------------------------------------------------------
def test_a_post_on_the_overhang_with_nothing_carrying_it_fails() -> None:
    finding = _one(posts=(_TIP_POST,))
    assert finding.result is Result.FAIL
    assert finding.element_tags == ("FS-T", "PT-TIP")
    # Advisory, never presented as engineering — the sibling structural convention.
    assert finding.message.startswith("[advisory, not engineering]")
    assert "nothing in the model carrying the point load" in finding.message
    assert "uniform-load tables" in finding.message
    assert finding.fix_hint


def test_the_finding_measures_the_overhang_and_how_far_out_the_post_is() -> None:
    finding = _one(posts=(_INBOARD_POST,))
    assert '24" cantilever at its high-y edge' in finding.message
    assert '6.0" past the bearing line' in finding.message
    assert '2x8 joists at 16" o.c.' in finding.message


def test_a_post_over_the_back_span_is_not_this_rule() -> None:
    """The uniform span tables already grade it; a second opinion here would be noise."""
    assert _findings(posts=(_BACK_SPAN_POST,)) == []


def test_a_deck_that_does_not_cantilever_is_out_of_scope_entirely() -> None:
    assert _findings(overhang_in=0.0, posts=(_TIP_POST, _BACK_SPAN_POST)) == []


def test_a_post_bearing_on_something_else_is_not_carried_by_this_deck() -> None:
    stray = _post("PT-ELSEWHERE", 8.0, _TIP_FT, supported_by="W-N")
    assert _findings(posts=(stray,)) == []


def test_two_posts_on_the_overhang_are_two_findings() -> None:
    second = _post("PT-TIP2", 12.0, _TIP_FT, uid="PT000000c2")
    findings = _findings(posts=(_TIP_POST, second))
    assert sorted(f.element_tags[1] for f in findings) == ["PT-TIP", "PT-TIP2"]
    assert all(f.result is Result.FAIL for f in findings)


# --- arm (a): sistered plies ----------------------------------------------------------
def _reinforcement(x_ft: float = 8.0, y_ft: float = _TIP_FT, **kwargs) -> JoistReinforcement:
    return JoistReinforcement(at=pt(ft(x_ft), ft(y_ft)), **kwargs)


def test_a_three_ply_reinforcement_under_the_post_downgrades_to_unknown() -> None:
    finding = _one(posts=(_TIP_POST,),
                   reinforcements=(_reinforcement(plies=3, blocking=False),))
    assert finding.result is Result.UNKNOWN
    assert "an authored 3-ply JoistReinforcement" in finding.message
    assert "2 sistered 2x8 plies" in finding.message


def test_mitigated_is_never_a_pass_because_the_tables_have_no_row_for_it() -> None:
    """The reinforcement is right and it still is not a verdict: 'reinforced' is a
    judgement the uniform tables cannot make, so the finding stays in the not-evaluable
    column rather than retiring the question."""
    finding = _one(posts=(_TIP_POST,), reinforcements=(_reinforcement(plies=3),))
    assert finding.result is Result.UNKNOWN
    assert finding.message.startswith("[advisory, not engineering]")
    assert "assume no cantilever point load" in finding.message
    assert "reinforced, not verified" in finding.message


def test_a_reinforcement_two_bays_over_reinforces_a_different_joist() -> None:
    """``at`` is the load, not a hint: the resolver sisters the line nearest it, and a line
    two bays away carries none of this post."""
    away = _reinforcement(x_ft=8.0 + 3 * _SPACING_IN / 12.0, plies=3)
    finding = _one(posts=(_TIP_POST,), reinforcements=(away,))
    assert finding.result is Result.FAIL


def test_a_resolved_sister_counts_even_when_the_authored_ply_count_is_two() -> None:
    """The ``plies >= 3`` gate is on the *authored* arm. A ply that actually resolved on the
    post's own line is doubling the joist under it whatever the entry claimed, so the
    geometric arm reads it — conservatively, as UNKNOWN, not as a pass."""
    finding = _one(posts=(_TIP_POST,),
                   reinforcements=(_reinforcement(plies=2, blocking=False),))
    assert finding.result is Result.UNKNOWN
    assert "1 sistered 2x8 plies" in finding.message
    assert "JoistReinforcement" not in finding.message


# --- arm (b): blocking ----------------------------------------------------------------
def test_blocking_alone_downgrades_to_unknown() -> None:
    """``plies=1`` sisters nothing but still blocks, which isolates arm (b)."""
    finding = _one(posts=(_TIP_POST,), reinforcements=(_reinforcement(plies=1),))
    assert finding.result is Result.UNKNOWN
    assert "2 solid blocks" in finding.message
    assert "sistered" not in finding.message


def test_blocking_left_down_at_the_bearing_line_does_not_reach_the_post() -> None:
    """The resolver puts the blocks at the load's own axis coordinate; blocking authored at
    a bearing line is 2' away from this post and carries none of it."""
    finding = _one(posts=(_TIP_POST,),
                   reinforcements=(_reinforcement(y_ft=1.0, plies=1),))
    assert finding.result is Result.FAIL


# --- arm (c): uplift hardware ---------------------------------------------------------
def _tie(*, x_ft: float = 8.0, y_ft: float = 0.0, connects=("FS-T",),
         kind: ConnectorKind = ConnectorKind.HURRICANE_TIE) -> Connector:
    return Connector(uid="CN000000c1", tag="CN-TIE", kind=kind,
                     position=pt(ft(x_ft), ft(y_ft)), elevation=ft(0), size="H2.5A",
                     connects=connects)


def test_a_tie_on_the_deck_at_the_post_line_downgrades_to_unknown() -> None:
    finding = _one(posts=(_TIP_POST,), extras=(_tie(),))
    assert finding.result is Result.UNKNOWN
    assert "uplift hardware CN-TIE (H2.5A)" in finding.message
    assert finding.element_tags == ("FS-T", "PT-TIP", "CN-TIE")


def test_a_hold_down_counts_the_same_as_a_hurricane_tie() -> None:
    finding = _one(posts=(_TIP_POST,), extras=(_tie(kind=ConnectorKind.HOLD_DOWN),))
    assert finding.result is Result.UNKNOWN


def test_a_tie_naming_the_back_span_bearing_wall_counts() -> None:
    finding = _one(posts=(_TIP_POST,), extras=(_tie(connects=("PT-TIP", "W-S")),))
    assert finding.result is Result.UNKNOWN


def test_a_tie_on_the_cantilevered_bearing_line_answers_a_different_load() -> None:
    """W-N is the bearing the joists oversail. Hardware there holds that joint together; it
    is not the back-span hold-down the overhang's prying calls for. (catlin authors exactly
    this shape — CN-SG-TIE-COL on the back beams — so the distinction is not academic.)"""
    finding = _one(posts=(_TIP_POST,),
                   extras=(_tie(y_ft=_SPAN_FT, connects=("PT-TIP", "W-N")),))
    assert finding.result is Result.FAIL


def test_a_tie_on_another_joist_line_carries_another_joist() -> None:
    finding = _one(posts=(_TIP_POST,), extras=(_tie(x_ft=8.0 + 2 * _SPACING_IN / 12.0),))
    assert finding.result is Result.FAIL


def test_a_post_base_is_not_uplift_hardware() -> None:
    """A standoff base ties the post to the deck; it does nothing for the joist under it.
    catlin has one at exactly this location (CN-SG-BASE-R2), so the kind filter has work."""
    finding = _one(posts=(_TIP_POST,), extras=(_tie(kind=ConnectorKind.POST_BASE),))
    assert finding.result is Result.FAIL


# --- catlin ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def catlin_findings() -> list:
    from pathlib import Path

    from typehaus.source import load_plan

    catlin = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    result = load_plan(catlin)
    model, resolve_findings = resolve(result.plan)
    errors = [f for f in resolve_findings if f.severity.value == "error"]
    assert not errors, [f.message for f in errors]
    ctx = CheckContext(plan=result.plan, model=model, preferences=Preferences(),
                       profile=None, resolve_findings=list(resolve_findings))
    return cantilever_point_load(ctx)


def test_the_check_is_registered_in_the_structural_tier() -> None:
    """It has to actually run under ``haus check``, not merely be importable."""
    assert "structural.cantilever_point_load" in {
        check_id for check_id, _fn in registered(Tier.STRUCTURAL)}


def test_the_catlin_porch_pillar_is_the_one_finding_and_it_is_reinforced(catlin_findings):
    """PT-SG-BR2 stands on the porch's 17" north overhang and is the only post in the house
    that does. WP1 answered it — 3-ply PT 2x8, solid blocking, and CN-SG-TIE-BR2 at the
    arch-wall back span — so all three arms match and the verdict is UNKNOWN, not FAIL."""
    assert len(catlin_findings) == 1, [f.message for f in catlin_findings]
    finding = catlin_findings[0]
    assert finding.result is Result.UNKNOWN, finding.message
    assert finding.element_tags == ("FS-SG-PORCH", "PT-SG-BR2", "CN-SG-TIE-BR2")
    assert '17" cantilever at its high-y edge' in finding.message
    # Each arm of the contract, named — a silently-unmatched arm is how this check rots.
    assert "an authored 3-ply JoistReinforcement" in finding.message
    assert "2 sistered 2x8 plies" in finding.message
    assert "2 solid blocks" in finding.message
    assert "uplift hardware CN-SG-TIE-BR2 (H2.5A)" in finding.message
