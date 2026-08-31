"""``structural.soffit_rung_span`` — and the property the two-stock ladder actually claims.

Oracled against ``houses/catlin/notes/soffit_rung_deflection.md``, which works the same three
numbers by hand. The synthetic box here is SF-S-HP1's clear span reproduced from first
principles so the arithmetic can be read without the whole house in the way.
"""

from __future__ import annotations

import uuid

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.findings import Result
from typehaus.model import (
    Assembly, Building, FramingSpec, Layer, LayerFunction, Library, Material, Node,
    PlanModel, Project, Site, Soffit, Storey, Wall, degF, ft, inch, pt,
)
from typehaus.quantities import M_PER_IN
from typehaus.resolve import resolve
from typehaus.resolve.framing.soffit import soffit_clear_section

_CHECK_ID = "structural.soffit_rung_span"

# The box: 77" x 80" finished, 21" drop — SF-S-HP1's own dimensions. 77 - 2 x 5/8 lining
# - 2 x 1.5 rail depth is the 72.75" of clear span its rungs really cross. 80" in the other
# direction so the LONG axis is y and the rungs span x, which is the ordering that box is
# authored for and the reason it is 80 over 77 rather than the other way round.
_OUTLINE = (pt(ft(4), ft(1)), pt(inch(48 + 77), ft(1)),
            pt(inch(48 + 77), inch(12 + 80)), pt(ft(4), inch(12 + 80)))


def _plan(framing: FramingSpec) -> PlanModel:
    assembly = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
    ))
    project = Project(
        name="SoffitSpan", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000b2"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="SoffitSpan"),
    )
    main = Storey(uid="STMAIN0001", tag="main", elevation=ft(0), default_ceiling_height=ft(9))
    nodes = tuple(
        Node(uid=f"N{i:09d}", tag=f"N-{i}", position=position)
        for i, position in enumerate((
            pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14)),
        ), 1)
    )
    walls = tuple(
        Wall(uid=f"W{i:09d}", tag=f"W-{i}", start_node=f"N-{start}", end_node=f"N-{end}",
             assembly="EXT", top=ft(9))
        for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1)
    )
    soffit = Soffit(uid="SF00000001", tag="SF-1", outline=_OUTLINE, drop=inch(21),
                    framing=framing)
    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="wood", name="Wood", r_per_inch=1.25),), assemblies=(assembly,)),
                     storeys=(main,))
    return plan.with_elements("main", (*nodes, *walls, soffit))


def _graded(framing: FramingSpec):
    model, _ = resolve(_plan(framing))
    findings = [f for f in run_from_model(model, [], tier=Tier.STRUCTURAL).findings
                if f.check_id == _CHECK_ID]
    assert len(findings) == 1, [f.message for f in findings]
    return model, findings[0]


_ONE_STOCK = FramingSpec(member="2x2", spacing=inch(16))
_TWO_STOCK = FramingSpec(member="2x4", plate_member="2x2", spacing=inch(16))


def test_a_seventy_three_inch_2x2_rung_fails_at_l_over_212() -> None:
    """The condition the check exists for, and the one SF-S-HP1 was built with.

    5 psf of ceiling dead load over a 16" tributary is w = 0.5556 lb/in. A 2x2 laid FLAT —
    which is what the generator lays, and correctly, since the rung is the board's nailer —
    bends about its weak axis: I = 1.5 x 1.5^3 / 12 = 0.4219 in^4. Over 72.75",
    5wL^4/384EI = 0.343", i.e. L/212 against IRC R301.7's L/360 for a brittle-finish ceiling.
    """
    _, finding = _graded(_ONE_STOCK)
    assert finding.result is Result.FAIL
    assert "L/212" in finding.message
    assert "2x2 rungs laid flat" in finding.message
    assert "72.75" in finding.message


def test_the_same_box_passes_once_the_rail_and_the_rung_are_different_stock() -> None:
    """2x4 rungs on 2x2 rails: I = 3.5 x 1.5^3 / 12 = 0.9844 in^4, delta 0.147", L/495."""
    _, finding = _graded(_TWO_STOCK)
    assert finding.result is Result.PASS
    assert "L/495" in finding.message
    assert "2x4 rungs laid flat" in finding.message


def test_the_cavity_is_byte_identical_before_and_after() -> None:
    """** THE PROPERTY THE DESIGN ACTUALLY CLAIMS, ASSERTED DIRECTLY. **

    Upsizing a single shared profile fixes deflection by taking one stock DEPTH off each long
    side — on catlin that evicted EQ-S-ERV-MIX from the box and produced
    ``FAIL (error) mep.duct_soffit_occupancy``. Holding the rails at ``plate_member`` is what
    makes the rungs free to grow, and the claim is that NOTHING about the cavity moves:
    ``across`` (the rails are still 2x2), ``along`` (end blocking is still 1.5" thick) and
    ``z`` — including ``z[0]``, because the rung is still laid flat at one stock thickness.

    ``z[0]`` is the one that would have hurt. DU-S-HP-RET is a 14" duct in a 14.25" cavity;
    an on-edge rung, a deeper rung or a mid-height bearer all raise the cavity floor and force
    the return plenum and the ERV feed to be re-authored.
    """
    thin, _ = _graded(_ONE_STOCK)
    thick, _ = _graded(_TWO_STOCK)
    before = soffit_clear_section(thin.soffits[0])
    after = soffit_clear_section(thick.soffits[0])
    assert before is not None and after is not None
    assert after.across == pytest.approx(before.across)
    assert after.along == pytest.approx(before.along)
    assert after.z == pytest.approx(before.z)
    assert after.width_m / M_PER_IN == pytest.approx(72.75, abs=1e-6)


def test_the_rails_take_the_plate_stock_and_the_rungs_take_the_member() -> None:
    """Which stick got which profile, read off what was built rather than off the spec."""
    model, _ = _graded(_TWO_STOCK)
    soffit = model.soffits[0]
    by_category: dict[str, set[str]] = {}
    for member in soffit.members:
        by_category.setdefault(member.category, set()).add(member.profile)
    assert by_category["plate"] == {"2x2"}   # the rails
    assert by_category["stud"] == {"2x2"}    # the ladder studs between them
    rungs = {m.profile for m in soffit.members if m.child_key.startswith("soffit-rung-")}
    ends = {m.profile for m in soffit.members if m.child_key.startswith("soffit-end-")}
    assert rungs == {"2x4"}
    # End blocking closes the box against the rails, so it is rail stock, not rung stock.
    assert ends == {"2x2"}


def test_defaulting_plate_member_frames_byte_identically() -> None:
    """The migration guarantee: a soffit that does not set ``plate_member`` is unchanged."""
    explicit, _ = resolve(_plan(FramingSpec(member="2x2", plate_member="2x2", spacing=inch(16))))
    implicit, _ = resolve(_plan(_ONE_STOCK))
    def shape(model):
        return [(m.child_key, m.category, m.profile, m.p0, m.p1, m.z0_m, m.z1_m, m.length_m)
                for m in model.soffits[0].members]
    assert shape(explicit) == shape(implicit)


def test_an_unframed_soffit_gets_no_finding_at_all() -> None:
    """Not UNKNOWN. A soffit drawn without a FramingSpec has no lumber to grade, and catlin
    is held to zero UNKNOWNs; ``mep.duct_soffit_occupancy`` already reports the missing spec
    once, and reporting it twice would be a second finding about one omission.

    The check still has to say something when NO soffit in the model frames anything, and it
    says N/A — earned from positive evidence of absence, not assumed."""
    model, _ = resolve(_plan(None))
    findings = [f for f in run_from_model(model, [], tier=Tier.STRUCTURAL).findings
                if f.check_id == _CHECK_ID]
    assert [f.result for f in findings] == [Result.NOT_APPLICABLE]
