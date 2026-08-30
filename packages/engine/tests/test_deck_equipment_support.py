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


def _anchor(x_ft: float, tag: str = "CN-T-HP1", y_ft: float = 4.0) -> Connector:
    return Connector(
        uid=f"TSTCN{abs(hash(tag)) % 100000:05d}", tag=tag,
        kind=ConnectorKind.EQUIPMENT_ANCHOR,
        position=Point2D(x=ft(x_ft), y=ft(y_ft)), size="SS316-LAG-38x4-EPDM",
        connects=("PT-T-HP1", "FS-T-DECK"))


def _run(freeze: str | None = "5 W/ft self-regulating, 120 V") -> PipeRun:
    return PipeRun(
        uid="TSTPR01AAA", tag="PR-T-COND", system=PipeSystem.DRAIN,
        path=(Point2D(x=ft(14), y=ft(4)), Point2D(x=ft(14), y=ft(0))),
        diameter=inch(0.75), freeze_protection=freeze)


def _joist(y_ft: float) -> SimpleNamespace:
    """One resolved joist line running in x at this y."""
    return SimpleNamespace(category="joist", parent_uid="TSTFS02AAA",
                           p0=(0.0, y_ft * _M_PER_FT), p1=(21.0 * _M_PER_FT, y_ft * _M_PER_FT))


def _block(x_ft: float) -> SimpleNamespace:
    """One resolved blocking member spanning a joist bay at this x."""
    return SimpleNamespace(category="blocking", parent_uid="TSTFS02AAA",
                           p0=(x_ft * _M_PER_FT, 3.5 * _M_PER_FT),
                           p1=(x_ft * _M_PER_FT, 4.5 * _M_PER_FT))


#: A site with no wind fields at all — what the starter house and every synthetic fixture
#: here carry. ``wind.wind_basis`` reads the three fields with ``getattr``, so this is a
#: faithful stand-in for a ``Site`` that simply never authored them.
_SILENT_SITE = SimpleNamespace(design_wind_speed_mph=None, wind_exposure=None,
                               risk_category=None)
#: Catlin's basis, MN Rules 1309.0301.
_AUTHORED_SITE = SimpleNamespace(design_wind_speed_mph=115.0, wind_exposure="B",
                                 risk_category="II")


def _ctx(elements, blocks=(), storey="second", joists=(),
         site=_SILENT_SITE) -> SimpleNamespace:
    beam_nodes = [Node(uid="TSTN001AAA", tag="N-T-BN", position=Point2D(x=ft(_BEAM_X), y=ft(0))),
                  Node(uid="TSTN002AAA", tag="N-T-BS", position=Point2D(x=ft(_BEAM_X), y=ft(9)))]
    beam = Beam(uid="TSTBM01AAA", tag="BM-T-DECK", start_node="N-T-BN", end_node="N-T-BS",
                size="3-2x12")
    everything = [*elements, *beam_nodes, beam]
    resolved = SimpleNamespace(tag="FS-T-DECK", members=[*blocks, *joists])
    return SimpleNamespace(
        plan=SimpleNamespace(
            project=SimpleNamespace(site=site),
            storeys=[SimpleNamespace(tag=storey)],
            storey_elements=lambda tag: everything if tag == storey else [],
            all_elements=lambda: everything),
        model=SimpleNamespace(floors=[resolved], walls=[], solids=[]))


def _one(findings):
    assert len(findings) == 1, [f.message for f in findings]
    return findings[0]


def test_a_fully_covered_unit_passes_and_names_where_capacity_went():
    """Inverted on 2026-08-30 along with ``structural.uplift_path_coverage``.

    This asserted UNKNOWN so that "the anchors are all in blocking" could not be read as
    "the anchorage is adequate". Right concern, wrong instrument: the rule is now named
    ``mep.deck_equipment_support_coverage``, so a covered unit is an honest PASS of the rule
    that ran, and the capacity question is a named item a seal has to cover rather than a
    disclaimer at the end of a row. See ``test_the_capacity_question_is_a_named_item``.
    """
    ctx = _ctx([_deck(), _unit(), _anchor(_BLOCK_X), _run()], blocks=[_block(_BLOCK_X)])
    finding = _one(deck_equipment_support(ctx))
    assert finding.result is Result.PASS
    assert "CAPACITY is not graded here" in finding.message
    assert "no design wind speed" in finding.message


def test_the_capacity_question_is_a_named_item_not_a_retired_one():
    """The concern the inversion above must not lose: one ENGINEERED item per unit."""
    from typehaus.checks.mep.deck_equipment import deck_equipment_anchorage_capacity
    from typehaus.findings import Authority

    ctx = _ctx([_deck(), _unit(), _anchor(_BLOCK_X), _run()], blocks=[_block(_BLOCK_X)])
    items = deck_equipment_anchorage_capacity(ctx)
    assert [f.engineering_item for f in items] == ["equipment_anchorage/EQ-T-HP-OD"]
    assert all(f.authority is Authority.ENGINEERED for f in items)
    # Still blocking, exactly as the UNKNOWN it replaced was.
    assert all(f.result is Result.UNKNOWN for f in items)


def test_a_covered_unit_with_a_wind_basis_still_names_the_ungraded_capacity():
    """Carrying a wind speed is not computing a demand, and the message must say which.

    This is the regression that matters after 2026-08-30: the easy mistake is to read
    "the site now has a wind speed" as "the restraint is now checked". It is not — nothing
    here derives the cabinet's projected area or an ASCE 7 §29.4 force coefficient — so the
    sentence has to name the site's actual basis rather than claim an absence that is no
    longer true, and the capacity itself belongs to the engineering item, not to this PASS.
    """
    ctx = _ctx([_deck(), _unit(), _anchor(_BLOCK_X), _run()], blocks=[_block(_BLOCK_X)],
               site=_AUTHORED_SITE)
    finding = _one(deck_equipment_support(ctx))
    assert finding.result is Result.PASS
    assert "no design wind speed" not in finding.message
    assert "V_ult = 115 mph, Exposure B, Risk Category II" in finding.message
    assert "derives no demand from it" in finding.message


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
    assert finding.result is Result.PASS
    assert "FS-T-DECK" in finding.message
    assert "FS-T-PORCH" not in finding.message


def test_no_deck_is_silence_not_an_unknown():
    ctx = _ctx([_unit()], blocks=[])
    assert deck_equipment_support(ctx) == []


# --- the two holes the check had, and the geometry each one hid ------------------------
def test_flags_an_anchor_sitting_on_a_joist_line():
    """** BLOCKING PRESENT IS NOT THE ANCHOR IN IT. **

    A ``JoistReinforcement`` blocks the bays *either side* of the joist line nearest its load,
    so each block's bounding box runs from one joist line to the next. Testing only that the
    anchor falls inside a block therefore passes an anchor sitting dead on a joist — the
    block is right there, on both sides of it. Every one of catlin's eight real anchors sat
    3" off a joist line, inside the bay but with 2 1/4" of clear to the joist face, and this
    check reported all eight as correctly hosted until the distance to the line was measured
    directly.
    """
    ctx = _ctx([_deck(), _unit(), _anchor(_BLOCK_X, y_ft=3.5), _run()],
               blocks=[_block(_BLOCK_X)], joists=[_joist(3.5)])
    finding = _one(deck_equipment_support(ctx))
    assert finding.result is Result.FAIL
    assert "of a joist line" in finding.message


def test_a_beam_on_another_storey_does_not_reach_this_deck():
    """The wrong-deck bug had a twin: the beams were never storey-scoped either.

    catlin stacks a porch under this balcony, and the porch's back beams run east-west
    directly beneath the balcony's anchors, ten feet down. A whole-plan beam search reported
    four anchors as landing on a beam no lag through this deck could ever reach — the same
    shape of wrong answer, from the same missing filter, one function away.
    """
    other = Beam(uid="TSTBM02AAA", tag="BM-T-BELOW", start_node="N-T-LW", end_node="N-T-LE",
                 size="3-2x12")
    nodes = [Node(uid="TSTN003AAA", tag="N-T-LW", position=Point2D(x=ft(0), y=ft(4))),
             Node(uid="TSTN004AAA", tag="N-T-LE", position=Point2D(x=ft(21), y=ft(4)))]
    here = [_deck(), _unit(), _anchor(_BLOCK_X), _run()]
    below = [*nodes, other]
    resolved = SimpleNamespace(tag="FS-T-DECK", members=[_block(_BLOCK_X)])
    beam_nodes = [Node(uid="TSTN001AAA", tag="N-T-BN",
                       position=Point2D(x=ft(_BEAM_X), y=ft(0))),
                  Node(uid="TSTN002AAA", tag="N-T-BS",
                       position=Point2D(x=ft(_BEAM_X), y=ft(9)))]
    beam = Beam(uid="TSTBM01AAA", tag="BM-T-DECK", start_node="N-T-BN", end_node="N-T-BS",
                size="3-2x12")
    per_storey = {"second": [*here, *beam_nodes, beam], "main": below}
    ctx = SimpleNamespace(
        plan=SimpleNamespace(
            project=SimpleNamespace(site=_SILENT_SITE),
            storeys=[SimpleNamespace(tag="second"), SimpleNamespace(tag="main")],
            storey_elements=lambda tag: per_storey.get(tag, []),
            all_elements=lambda: [*per_storey["second"], *per_storey["main"]]),
        model=SimpleNamespace(floors=[resolved], walls=[], solids=[]))
    finding = _one(deck_equipment_support(ctx))
    assert finding.result is Result.PASS, finding.message
    assert "BM-T-BELOW" not in finding.message
