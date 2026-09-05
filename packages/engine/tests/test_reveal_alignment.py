"""``integrity.reveal_concentric`` — a hole in a wythe must line up with what it reveals.

The bug this check exists for was silent for five days at 0 FAIL: catlin's brick reveal
``AO-B-BRICK-DOOR`` was authored against ``D-B-PATIO``'s position, the door later moved 6"
west off a different node on a different wall, and nothing in the engine compared them.

The fixture is the smallest thing that can go wrong that way: a 20' backer wall with a
door in it, and a 3 5/8" veneer wall standing 1 1/2" off its face with a rough opening
cut through it. Everything the check has to distinguish is a variation on that one plan.
"""

from __future__ import annotations

import uuid

from typehaus.checks import run_from_model
from typehaus.findings import Result
from typehaus.model import (
    Assembly, Building, Door, DoorType, Layer, LayerFunction, Library, Material, Node,
    PlanModel, Project, RoughOpening, Site, Storey, Wall, degF, ft, inch, pt,
)
from typehaus.model.refs import from_node
from typehaus.resolve import resolve

_CHECK_ID = "integrity.reveal_concentric"

#: The veneer's outboard face sits 1 1/2" (cavity) + 3 5/8" (wythe) off the backer's, so its
#: axis is 5 7/16" out — well inside the check's 12" search and far outside its 1" tolerance.
_VENEER_OFFSET = inch(5.4375)

#: The door's own station, so the aligned case is stated once and the misaligned cases are
#: visibly offsets from it rather than two unrelated literals.
_DOOR_AT = ft(10)


def _plan(*, reveal_at=_DOOR_AT, backer_door: bool = True, veneer: bool = True,
          reveal: bool = True) -> PlanModel:
    project = Project(
        name="Reveal", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000c1"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Reveal"))
    main = Storey(uid="STMAIN0001", tag="main", elevation=ft(0), default_ceiling_height=ft(9))
    backer = Assembly(tag="BACKER", layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(8),
              function=LayerFunction.STRUCTURE),))
    wythe = Assembly(tag="WYTHE", layers=(
        Layer(name="air-gap", material_ref="air", thickness=inch(1.5),
              function=LayerFunction.AIRGAP),
        Layer(name="brick", material_ref="brick", thickness=inch(3.625),
              function=LayerFunction.STRUCTURE),))

    nodes = [
        Node(uid="N000000001", tag="N-W", position=pt(ft(0), ft(0))),
        Node(uid="N000000002", tag="N-E", position=pt(ft(20), ft(0))),
        Node(uid="N000000003", tag="N-VW", position=pt(ft(0), -_VENEER_OFFSET)),
        Node(uid="N000000004", tag="N-VE", position=pt(ft(20), -_VENEER_OFFSET)),
    ]
    elements = [*nodes, Wall(uid="W000000001", tag="W-BACK", start_node="N-W",
                             end_node="N-E", assembly="BACKER", top=ft(9))]
    if veneer:
        elements.append(Wall(uid="W000000002", tag="W-VEN", start_node="N-VW",
                             end_node="N-VE", assembly="WYTHE", top=ft(9)))
    if backer_door:
        elements.append(Door(uid="D000000001", tag="D-BACK", host="W-BACK",
                             type_ref="DT-60", position=from_node("N-W", _DOOR_AT)))
    if reveal:
        elements.append(RoughOpening(
            uid="O000000001", tag="AO-REVEAL", host="W-VEN" if veneer else "W-BACK",
            position=from_node("N-VW" if veneer else "N-W", reveal_at),
            width=ft(5), height=inch(78), sill_height=ft(0)))

    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="concrete", name="Concrete", r_per_inch=0.08),
                   Material(tag="brick", name="Brick", r_per_inch=0.2),
                   Material(tag="air", name="Air", r_per_inch=0.0)),
        assemblies=(backer, wythe),
        door_types=(DoorType(tag="DT-60", width=ft(5), height=inch(80)),)),
        storeys=(main,))
    return plan.with_elements("main", tuple(elements))


def _finding(**kwargs):
    model, resolve_findings = resolve(_plan(**kwargs))
    matched = [f for f in run_from_model(model, resolve_findings).findings
               if f.check_id == _CHECK_ID]
    assert len(matched) == 1, [f.message for f in matched]
    return matched[0]


def test_a_reveal_centred_on_its_door_passes() -> None:
    """The fixed catlin condition, and the shape every other case is measured against."""
    finding = _finding()
    assert finding.result is Result.PASS
    assert "1 reveals" in finding.message


def test_a_reveal_six_inches_off_its_door_fails_by_six_inches() -> None:
    """The real defect, at the real magnitude — the reveal's node is 6" east of the door's.

    The number matters as much as the verdict: a check that says "not concentric" without
    saying how far off cannot be told from a rounding artefact by the person reading it.
    """
    finding = _finding(reveal_at=ft(10, 6))
    assert finding.result is Result.FAIL
    assert "6.0\"" in finding.message
    assert set(finding.element_tags) == {"AO-REVEAL", "D-BACK"}


def test_a_reveal_within_the_tolerance_still_passes() -> None:
    """1/2" is a mortar joint's worth of drafting, not a misplaced opening. The tolerance is
    1", chosen to sit far below the smallest error worth a trade's attention and far above
    anything metric conversion introduces."""
    assert _finding(reveal_at=inch(120.5)).result is Result.PASS


def test_a_cased_passthrough_is_not_a_reveal() -> None:
    """A rough opening in a lone wall reveals nothing, and must not be graded as if it did.

    This is the case that decides the check's subject. catlin authors two of them —
    ``D-S-STUDY2`` and ``O-S-VANITY``, plain cased openings framed like a 30" door — and an
    earlier draft of this check paired each with the nearest parallel door two storeys away
    and reported both as FAIL. What makes a reveal a reveal is the wall behind it.
    """
    finding = _finding(veneer=False)
    assert finding.result is Result.NOT_APPLICABLE
    assert "cased passthrough" in finding.message


def test_a_reveal_onto_blind_wall_is_unknown_not_a_pass() -> None:
    """A hole through a wythe onto solid backer is either a mistake or a decoration.

    The model cannot tell which, so it says so. Returning PASS here — "no misalignment
    found" — would be the check reporting success for having nothing to compare.
    """
    finding = _finding(backer_door=False)
    assert finding.result is Result.UNKNOWN
    assert "blind wall" in finding.message
    assert "W-BACK" in finding.element_tags


def test_a_building_with_no_rough_opening_is_not_applicable() -> None:
    """N/A is earned from the absence, never from an empty list (``na-must-be-earned``)."""
    finding = _finding(reveal=False)
    assert finding.result is Result.NOT_APPLICABLE
    assert "no wall in this building carries a rough opening" in finding.message
