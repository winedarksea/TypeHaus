"""``mep.deck_equipment_support`` — where an equipment anchor is allowed to land.

The rule this pins is a durability decision, not a structural one, and it is the opposite of
the instinct: **an anchor through a deck's waterproof plane must land in sacrificial blocking,
never in a beam.** A beam is stiffer and on the catlin balcony one runs right under each
condenser, which is exactly the trap — a lag there pierces the beam cap and the butyl over a
built-up beam's ply seams, in the one member that cannot be cut out and replaced from below.

Two of these tests exist because the check found real errors in the work that introduced it:

* ``test_matches_the_deck_on_the_units_own_storey`` — the first version searched every deck in
  the plan for one whose outline contains the unit. This house stacks a porch and a balcony on
  one footprint, so both condensers matched the *porch* ten feet below them, and the check then
  read the porch pillars' post bases as the condensers' anchors and graded those. It reported a
  confident, entirely wrong answer.
* ``test_flags_an_anchor_on_a_beam`` — three legs were first authored 4" off a beam axis, which
  is 1 3/4" of clear to the face of a 4 1/2" 3-ply. The check failed them and the legs moved.
"""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.checks.mep.deck_equipment import deck_equipment_support
from typehaus.findings import Result
from typehaus.model.elements import Node
from typehaus.model.enums import ConnectorKind, EquipmentKind, PipeSystem
from typehaus.model.floors import FloorSystem, JoistSpec
from typehaus.model.mep import Equipment, PipeRun
from typehaus.model.structure import Beam, Connector
from typehaus.quantities import Point2D, ft, inch

_M_PER_FT = 0.3048

#: A beam on the x = 10' line, and blocking in the bay at x = 14'. The unit sits between them.
_BEAM_X = 10.0
_BLOCK_X = 14.0


def _deck() -> FloorSystem:
    ring = (Point2D(x=ft(0), y=ft(0)), Point2D(x=ft(21), y=ft(0)),
            Point2D(x=ft(21), y=ft(9)), Point2D(x=ft(0), y=ft(9)))
    return FloorSystem(
        uid="TSTFS02AAA", tag="FS-T-DECK",
        joists=JoistSpec(member="2x8", spacing=inch(16), direction="x"),
        outline=ring, service="deck")


def _unit(**kwargs) -> Equipment:
    kwargs.setdefault("pan_drain_ref", "PR-T-COND")
    return Equipment(
        uid="TSTEQ01AAA", tag="EQ-T-HP-OD", kind=EquipmentKind.HEAT_PUMP,
        position=Point2D(x=ft(14), y=ft(4)), footprint=(inch(38), inch(16)),
        drain_pan=True, **kwargs)


def _anchor(x_ft: float, tag: str = "CN-T-HP1") -> Connector:
    return Connector(
        uid=f"TSTCN{abs(hash(tag)) % 100000:05d}", tag=tag, kind=ConnectorKind.POST_BASE,
        position=Point2D(x=ft(x_ft), y=ft(4)), size="SS316-LAG-38x4-EPDM",
        connects=("PT-T-HP1", "FS-T-DECK"))


def _run(freeze: str | None = "5 W/ft self-regulating, 120 V") -> PipeRun:
    return PipeRun(
        uid="TSTPR01AAA", tag="PR-T-COND", system=PipeSystem.DRAIN,
        path=(Point2D(x=ft(14), y=ft(4)), Point2D(x=ft(14), y=ft(0))),
        diameter=inch(0.75), freeze_protection=freeze)


def _block(x_ft: float) -> SimpleNamespace:
    """One resolved blocking member spanning a joist bay at this x."""
    return SimpleNamespace(category="blocking", parent_uid="TSTFS02AAA",
                           p0=(x_ft * _M_PER_FT, 3.5 * _M_PER_FT),
                           p1=(x_ft * _M_PER_FT, 4.5 * _M_PER_FT))


def _ctx(elements, blocks=(), storey="second") -> SimpleNamespace:
    beam_nodes = [Node(uid="TSTN001AAA", tag="N-T-BN", position=Point2D(x=ft(_BEAM_X), y=ft(0))),
                  Node(uid="TSTN002AAA", tag="N-T-BS", position=Point2D(x=ft(_BEAM_X), y=ft(9)))]
    beam = Beam(uid="TSTBM01AAA", tag="BM-T-DECK", start_node="N-T-BN", end_node="N-T-BS",
                size="3-2x12")
    everything = [*elements, *beam_nodes, beam]
    resolved = SimpleNamespace(tag="FS-T-DECK", members=list(blocks))
    return SimpleNamespace(
        plan=SimpleNamespace(
            storeys=[SimpleNamespace(tag=storey)],
            storey_elements=lambda tag: everything if tag == storey else [],
            all_elements=lambda: everything),
        model=SimpleNamespace(floors=[resolved], walls=[], solids=[]))


def _one(findings):
    assert len(findings) == 1, [f.message for f in findings]
    return findings[0]


def test_a_fully_covered_unit_is_unknown_not_pass():
    """Coverage is not capacity. Nothing here carries a design wind speed."""
    ctx = _ctx([_deck(), _unit(), _anchor(_BLOCK_X), _run()], blocks=[_block(_BLOCK_X)])
    finding = _one(deck_equipment_support(ctx))
    assert finding.result is Result.UNKNOWN
    assert "no design wind speed" in finding.message


def test_an_unanchored_unit_fails():
    ctx = _ctx([_deck(), _unit(), _run()], blocks=[_block(_BLOCK_X)])
    finding = _one(deck_equipment_support(ctx))
    assert finding.result is Result.FAIL
    assert "no anchor" in finding.message


def test_flags_an_anchor_on_a_beam():
    """The whole point: stiffer is not the same as replaceable."""
    ctx = _ctx([_deck(), _unit(), _anchor(_BEAM_X), _run()], blocks=[_block(_BEAM_X)])
    finding = _one(deck_equipment_support(ctx))
    assert finding.result is Result.FAIL
    assert "lands on beam BM-T-DECK" in finding.message


def test_flags_an_anchor_with_no_blocking_under_it():
    ctx = _ctx([_deck(), _unit(), _anchor(_BLOCK_X), _run()], blocks=[])
    finding = _one(deck_equipment_support(ctx))
    assert finding.result is Result.FAIL
    assert "no modeled blocking" in finding.message


def test_flags_an_untraced_condensate_line():
    ctx = _ctx([_deck(), _unit(), _anchor(_BLOCK_X), _run(freeze=None)],
               blocks=[_block(_BLOCK_X)])
    finding = _one(deck_equipment_support(ctx))
    assert finding.result is Result.FAIL
    assert "freeze_protection" in finding.message


def test_flags_a_heat_pump_with_no_condensate_path():
    ctx = _ctx([_deck(), _unit(pan_drain_ref=None), _anchor(_BLOCK_X)],
               blocks=[_block(_BLOCK_X)])
    finding = _one(deck_equipment_support(ctx))
    assert finding.result is Result.FAIL
    assert "pan_drain_ref" in finding.message


def test_matches_the_deck_on_the_units_own_storey():
    """A unit on the balcony must not be graded against the porch ten feet below it.

    Both decks share this plan footprint, so a whole-plan outline search matches both. The
    porch's own anchors are in the element list here and must NOT be read as this unit's.
    """
    porch_anchor = Connector(
        uid="TSTCN99999", tag="CN-T-PORCH-BASE", kind=ConnectorKind.POST_BASE,
        position=Point2D(x=ft(14), y=ft(4)), size="ABU66",
        connects=("PT-T-PILLAR", "FS-T-PORCH"))
    ctx = _ctx([_deck(), _unit(), _anchor(_BLOCK_X), _run(), porch_anchor],
               blocks=[_block(_BLOCK_X)])
    finding = _one(deck_equipment_support(ctx))
    assert finding.result is Result.UNKNOWN
    assert "FS-T-DECK" in finding.message
    assert "FS-T-PORCH" not in finding.message


def test_no_deck_is_silence_not_an_unknown():
    ctx = _ctx([_unit()], blocks=[])
    assert deck_equipment_support(ctx) == []
