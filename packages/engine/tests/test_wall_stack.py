"""``integrity.wall_stack_continuous`` — a stacked wall must land on the one below it.

The failure mode is arithmetic, and it is silent. A tall panel is authored as a chain of
walls whose every ``base_elevation`` is the previous base plus the previous ``top``, worked
out by hand. One stale term and the wall above starts where its neighbour does not end —
a horizontal slot straight through the panel — while every other consumer stays happy,
because each wall on its own is still a perfectly good wall.

The fixture is catlin's ``W-M-FIRE`` in miniature: a plinth, two jambs either side of a
firebox, and a head across the top. That one plan carries both verdicts the check has to
tell apart — the gap between plinth and head is *earned* by the jambs beside it, and the
same gap with the jambs taken away is the defect.
"""

from __future__ import annotations

import uuid

import pytest

from typehaus.checks import run_from_model
from typehaus.findings import Result
from typehaus.model import (
    Assembly, Building, Layer, LayerFunction, Library, Material, Node, PlanModel, Project,
    Site, Storey, StructuralRole, Wall, degF, ft, inch, pt,
)
from typehaus.resolve import resolve

_CHECK_ID = "integrity.wall_stack_continuous"

# The real panel's elevations, rounded to whole inches: the stack is what is under test,
# not catlin's 1/16ths.
_PLINTH_BASE, _PLINTH_TOP = inch(0), inch(24)
_JAMB_BASE, _JAMB_TOP = inch(24), inch(21)     # 24" -> 45"
_HEAD_BASE, _HEAD_TOP = inch(45), inch(19)     # 45" -> 64"

_PANEL_W = ft(4)
_JAMB_W = inch(8)


def _plan(*, jambs: bool = True, plinth_top=_PLINTH_TOP, head_base=_HEAD_BASE,
          second_storey: bool = False) -> PlanModel:
    project = Project(
        name="Stack", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000d1"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Stack"))
    storeys = [Storey(uid="STMAIN0001", tag="main", elevation=ft(0),
                      default_ceiling_height=ft(9))]
    if second_storey:
        storeys.append(Storey(uid="STUPPR0001", tag="upper", elevation=ft(10),
                              default_ceiling_height=ft(9)))
    wythe = Assembly(tag="WYTHE", layers=(
        Layer(name="brick", material_ref="brick", thickness=inch(3.625),
              function=LayerFunction.STRUCTURE),))

    # Every wall in the stack gets its OWN node pair, at the same coordinates. Sharing one
    # pair between two stacked walls collapses their junction polygons and the resolver
    # runs the lower wall up to meet the upper one — which would hide the very gap this
    # fixture exists to open. catlin authors N-M-FIRE-S/N, -HD-S/N, -JS-*, -JN-* for
    # exactly this reason.
    nodes = [
        Node(uid="N000000001", tag="N-P-S", position=pt(ft(0), ft(0))),
        Node(uid="N000000002", tag="N-P-N", position=pt(_PANEL_W, ft(0))),
        Node(uid="N000000009", tag="N-H-S", position=pt(ft(0), ft(0))),
        Node(uid="N000000010", tag="N-H-N", position=pt(_PANEL_W, ft(0))),
        # The two jambs, each 8" in from its end of the panel.
        Node(uid="N000000003", tag="N-JS-S", position=pt(ft(0), ft(0))),
        Node(uid="N000000004", tag="N-JS-N", position=pt(_JAMB_W, ft(0))),
        Node(uid="N000000005", tag="N-JN-S", position=pt(_PANEL_W - _JAMB_W, ft(0))),
        Node(uid="N000000006", tag="N-JN-N", position=pt(_PANEL_W, ft(0))),
    ]

    def wall(uid, tag, start, end, base, top):
        return Wall(uid=uid, tag=tag, start_node=start, end_node=end, assembly="WYTHE",
                    base_elevation=base, top=top,
                    structural_role=StructuralRole.NONBEARING)

    elements = [*nodes,
                wall("W000000001", "W-PLINTH", "N-P-S", "N-P-N", _PLINTH_BASE, plinth_top),
                wall("W000000004", "W-HEAD", "N-H-S", "N-H-N", head_base, _HEAD_TOP)]
    if jambs:
        elements.append(wall("W000000002", "W-JAMB-S", "N-JS-S", "N-JS-N",
                             _JAMB_BASE, _JAMB_TOP))
        elements.append(wall("W000000003", "W-JAMB-N", "N-JN-S", "N-JN-N",
                             _JAMB_BASE, _JAMB_TOP))

    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="brick", name="Brick", r_per_inch=0.2),),
        assemblies=(wythe,)), storeys=tuple(storeys))
    plan = plan.with_elements("main", tuple(elements))
    if second_storey:
        # Directly over the panel, on the same plane — the pairing a cross-storey sweep
        # makes and this check must not.
        plan = plan.with_elements("upper", (
            Node(uid="N000000007", tag="N-US", position=pt(ft(0), ft(0))),
            Node(uid="N000000008", tag="N-UN", position=pt(_PANEL_W, ft(0))),
            wall("W000000005", "W-UPPER", "N-US", "N-UN", inch(0), ft(9)),
        ))
    return plan


def _finding(**kwargs):
    model, resolve_findings = resolve(_plan(**kwargs))
    matched = [f for f in run_from_model(model, resolve_findings, only=_CHECK_ID).findings
               if f.check_id == _CHECK_ID]
    assert len(matched) == 1, [f.message for f in matched]
    return matched[0]


def test_the_firebox_is_an_earned_opening_not_a_slot() -> None:
    """The verdict that decides the check's worth: a 21" hole that must NOT be a defect.

    Plinth tops at 24" and head starts at 45", so at the firebox station there is 21" of
    nothing. The jambs stand beside it and run exactly that band. A check that cannot see
    that reports catlin's fireplace as a hole in the wall.
    """
    finding = _finding()
    assert finding.result is Result.PASS
    assert "1 earned opening(s)" in finding.message


def test_a_small_mistyped_top_is_healed_by_the_platform_lifter_not_by_this_check() -> None:
    """The negative result that sets this check's scope, and it is worth stating outright.

    ``resolve/platform.extend_walls_to_platform`` grows a lower wall to meet the wall above
    it whenever the band is at most 24". So typing ``W-PLINTH.top`` as 18" instead of 24"
    does not open anything: the plinth is lifted back to the jambs' base and the model
    resolves identically to the correct one. Asserted against the resolved elevations
    rather than against the verdict, because "this check passes" would be equally true of a
    check that graded nothing.
    """
    good, _ = resolve(_plan())
    typo, _ = resolve(_plan(plinth_top=inch(18)))
    assert ({w.tag: (w.z0_m, w.z1_m) for w in good.walls}
            == {w.tag: (w.z0_m, w.z1_m) for w in typo.walls})
    assert _finding(plinth_top=inch(18)).result is Result.PASS


def test_a_gap_past_the_platform_band_is_a_slot_and_is_found() -> None:
    """The defect that does reach the resolved model: a band the lifter refuses to close.

    Past 24" ``extend_walls_to_platform`` stops, because anything deeper may be a real void
    — a stairwell, a double-height space — and must not be absorbed into the wall below.
    That is right for a void and wrong for a typo, and it cannot tell them apart. Here the
    head's base is typed 30" too high: the jambs top out at 45" and it starts at 75", so
    30" of nothing runs the full width of the panel with nothing spanning it anywhere.

    The message has to carry the number, or a reader cannot tell a slot from a rounding
    artefact.
    """
    finding = _finding(head_base=inch(75))
    assert finding.result is Result.FAIL
    assert "30.00\"" in finding.message
    assert "W-HEAD" in finding.element_tags


def test_the_jambs_are_what_earn_it_so_without_them_it_fails() -> None:
    """The control on the earning rule, at a gap the lifter will not close either.

    Same head at 75", jambs deleted: now the plinth tops at 24" and the head starts at 75",
    a 51" slot. If this passed, the earning rule would be excusing every gap rather than
    the spanned ones, and the check would grade nothing.
    """
    finding = _finding(jambs=False, head_base=inch(75))
    assert finding.result is Result.FAIL
    assert "51.00\"" in finding.message


def test_a_storey_is_not_a_gap() -> None:
    """The restriction that is not optional: never pair across storeys.

    A wall on the storey above stands in the same plane over the same stations, and the
    storey between them is not a slot — it is a storey. On catlin a sweep without this rule
    reports four such pairs, at 120" to 253" apart, none of them defects.
    """
    finding = _finding(second_storey=True)
    assert finding.result is Result.PASS
    assert "W-UPPER" not in finding.message


def test_nothing_stacked_is_not_applicable_not_silence() -> None:
    """Per CLAUDE.md: a check with nothing to grade earns N/A rather than returning []."""
    model, resolve_findings = resolve(_plan(jambs=False, plinth_top=_PLINTH_TOP))
    # One wall alone on its plane: strip the head so nothing is over anything.
    model.walls = [w for w in model.walls if w.tag != "W-HEAD"]
    matched = [f for f in run_from_model(model, resolve_findings, only=_CHECK_ID).findings
               if f.check_id == _CHECK_ID]
    assert [f.result for f in matched] == [Result.NOT_APPLICABLE]


def test_catlin_fireplace_stack_closes(catlin_model_ro) -> None:
    """The reference house, which is the panel this check was written from.

    ``W-M-FIRE-*`` is SEVEN walls since 2026-09-19 — the buried stub became three piers with
    two 4" joist pockets between them — and the earned openings are FIVE: the firebox, and
    each pocket counted twice, once at the pier/pier plane below and once at the plinth
    course spanning it. That is the verdict this check exists for: three piers side by side
    in one z band, with the plinth's base exactly on their top, is not a hole in a wall. A
    new FAIL here means someone's arithmetic went stale, which is the whole point — but a
    new *stack* appearing is worth reading too, so the count is pinned.
    """
    matched = [f for f in run_from_model(catlin_model_ro, [], only=_CHECK_ID).findings
               if f.check_id == _CHECK_ID]
    assert len(matched) == 1
    assert matched[0].result is Result.PASS
    assert "5 earned opening(s)" in matched[0].message
