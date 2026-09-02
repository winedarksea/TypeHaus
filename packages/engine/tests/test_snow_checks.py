"""Sliding-snow exposure and rafter-span screens (checks/structural/snow.py).

Both checks are advisory table/geometry screens, and their edges matter more than their
centres: what they report UNKNOWN on is the promise that they never bluff. These fixtures are
synthetic on purpose — the catlin house has exactly one sliding-snow pair and one rafter
profile, so it can pin the landed behaviour but not the boundaries.
"""

from __future__ import annotations

import pytest

from _helpers import check_context

from typehaus.checks.registry import CheckContext, Preferences
from typehaus.checks.structural.snow import rafter_span, sliding_snow
from typehaus.findings import Authority, Result
from typehaus.model import (
    Assembly,
    Building,
    Connector,
    ConnectorKind,
    GlazingPanel,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    Pitch,
    PlanModel,
    Project,
    Roof,
    RoofForm,
    Site,
    Storey,
    StructuralRole,
    Wall,
    degF,
    face,
    ft,
    inch,
    pt,
)

_MATERIALS = (
    Material(tag="spf", name="SPF framing", r_per_inch=1.25, perm_rating=2.9),
    Material(tag="ply", name="Structural plywood", r_per_inch=1.25, perm_rating=0.30),
)
_ASSEMBLY = Assembly(tag="EXT", layers=(
    Layer(name="stud", material_ref="spf", thickness=inch(5.5),
          function=LayerFunction.STRUCTURE),
    Layer(name="sheathing", material_ref="ply", thickness=inch(0.5),
          function=LayerFunction.SHEATHING),
))
_ROOF_ASSEMBLY = Assembly(tag="ROOF", layers=(
    Layer(name="deck", material_ref="ply", thickness=inch(0.625),
          function=LayerFunction.SHEATHING),
))


def _plan(*, ground_snow_psf: float | None = 50.0, canopy_top_ft: float | None = 6.0,
          extras=()) -> PlanModel:
    """A 20' x 14' gabled box, optionally with a flat canopy off its south eave.

    The ridge runs in x, so the roof sheds north and south; the canopy sits just south of the
    footprint, which is the geometry the check is looking for.
    """
    library = Library(materials=_MATERIALS, assemblies=(_ASSEMBLY, _ROOF_ASSEMBLY))
    project = Project(name="SNOW", project_uuid="00000000-0000-4000-8000-0000000000f1",
                      site=Site(lat=44.9, lon=-93.2, elevation=ft(830),
                                design_temp_heating=degF(-15), design_temp_cooling=degF(90),
                                ground_snow_load_psf=ground_snow_psf),
                      building=Building(name="SNOW"))
    storey = Storey(uid="ST000000s1", tag="main", elevation=ft(0),
                    default_ceiling_height=ft(9))
    plan = PlanModel(project=project, library=library, storeys=(storey,))
    nodes = (
        Node(uid="N000000s01", tag="N-SW", position=pt(ft(0), ft(0))),
        Node(uid="N000000s02", tag="N-SE", position=pt(ft(20), ft(0))),
        Node(uid="N000000s03", tag="N-NE", position=pt(ft(20), ft(14))),
        Node(uid="N000000s04", tag="N-NW", position=pt(ft(0), ft(14))),
    )
    walls = (
        Wall(uid="W000000s01", tag="W-S", start_node="N-SW", end_node="N-SE",
             assembly="EXT", alignment=face("sheathing-ext"), top=ft(9),
             structural_role=StructuralRole.BEARING),
        Wall(uid="W000000s02", tag="W-E", start_node="N-SE", end_node="N-NE",
             assembly="EXT", alignment=face("sheathing-ext"), top=ft(9)),
        Wall(uid="W000000s03", tag="W-N", start_node="N-NE", end_node="N-NW",
             assembly="EXT", alignment=face("sheathing-ext"), top=ft(9),
             structural_role=StructuralRole.BEARING),
        Wall(uid="W000000s04", tag="W-W", start_node="N-NW", end_node="N-SW",
             assembly="EXT", alignment=face("sheathing-ext"), top=ft(9)),
    )
    roof = Roof(uid="R000000s01", tag="RF-TEST", form=RoofForm.GABLE, pitch=Pitch(4, 12),
                bearing_refs=("W-S", "W-N"), assembly="ROOF", overhang=ft(1),
                ridge_direction="x")
    canopy = ()
    if canopy_top_ft is not None:
        canopy = (GlazingPanel(
            uid="G000000s01", tag="GL-CANOPY",
            outline=(pt(ft(4), ft(-4)), pt(ft(12), ft(-4)),
                     pt(ft(12), ft(-1)), pt(ft(4), ft(-1))),
            thickness=inch(0.625), top_elevation=ft(canopy_top_ft), plane="horizontal"),)
    return plan.with_elements("main", (*nodes, *walls, roof, *canopy, *extras))


def _context(plan: PlanModel) -> CheckContext:
    return check_context(plan, profile=None)


def _guards(count: int = 3) -> tuple:
    return tuple(
        Connector(uid=f"C000000s{i:02d}", tag=f"CN-SNOW-{i}",
                  kind=ConnectorKind.SNOW_GUARD, position=pt(ft(4 + 4 * i), ft(0.5)),
                  elevation=ft(9), size="S-5! ColorGard", connects=("RF-TEST",))
        for i in range(1, count + 1))


# --- sliding snow --------------------------------------------------------------------


def test_discharge_onto_a_lower_glazed_canopy_fails() -> None:
    findings = sliding_snow(_context(_plan()))
    hits = [f for f in findings if f.result is Result.FAIL]
    assert hits, [f.message for f in findings]
    assert "GL-CANOPY" in hits[0].message
    assert "snow retention or an engineered impact load is required" in hits[0].message
    # Advisory, never presented as engineering.
    assert hits[0].message.startswith("[advisory, not engineering]")


def test_authored_snow_guards_turn_the_same_geometry_into_a_pass() -> None:
    """Only the retention changes — the exposure is identical, and still described."""
    findings = sliding_snow(_context(_plan(extras=_guards())))
    assert not [f for f in findings if f.result is Result.FAIL]
    hit = next(f for f in findings if "GL-CANOPY" in f.message)
    assert hit.result is Result.PASS
    assert "snow retention authored on RF-TEST" in hit.message
    # PASS means authored, not adequate — the message has to keep saying so.
    assert "manufacturer's calculation" in hit.message


def test_a_guard_on_a_different_roof_does_not_mitigate_this_one() -> None:
    stray = (Connector(uid="C000000s99", tag="CN-SNOW-X",
                       kind=ConnectorKind.SNOW_GUARD, position=pt(ft(8), ft(0.5)),
                       elevation=ft(9), size="S-5! ColorGard",
                       connects=("RF-SOMEWHERE-ELSE",)),)
    findings = sliding_snow(_context(_plan(extras=stray)))
    assert [f.result for f in findings if "GL-CANOPY" in f.message] == [Result.FAIL]


def test_no_lower_surface_in_the_discharge_band_passes() -> None:
    findings = sliding_snow(_context(_plan(canopy_top_ft=None)))
    assert [f.result for f in findings] == [Result.PASS]
    assert "no pitched roof discharges" in findings[0].message


def test_a_canopy_above_the_eave_is_not_a_target() -> None:
    """Sliding snow goes down. A surface at or above the eave cannot be landed on."""
    findings = sliding_snow(_context(_plan(canopy_top_ft=30.0)))
    assert [f.result for f in findings] == [Result.PASS]


def test_unknown_without_a_ground_snow_load() -> None:
    findings = sliding_snow(_context(_plan(ground_snow_psf=None)))
    assert [f.result for f in findings] == [Result.UNKNOWN]
    assert "ground_snow_load_psf" in findings[0].message


# --- rafter spans --------------------------------------------------------------------


def test_rafter_span_unknown_without_a_ground_snow_load() -> None:
    findings = rafter_span(_context(_plan(ground_snow_psf=None)))
    assert [f.result for f in findings] == [Result.UNKNOWN]


def test_rafter_span_unknown_off_the_published_snow_load() -> None:
    """The table is a 50 psf table. At another Pg it is not conservative, it is wrong."""
    findings = rafter_span(_context(_plan(ground_snow_psf=30.0)))
    assert [f.result for f in findings] == [Result.UNKNOWN]
    assert "published at 50 psf" in findings[0].message


def test_rafter_span_reports_unknown_rather_than_borrowing_a_row(catlin_model) -> None:
    """Catlin's roof is framed in 11.875" I-joists — an engineered product sized by its
    manufacturer's software, not by the sawn-lumber table. UNKNOWN, never a sawn-lumber row.
    """
    ctx = CheckContext(plan=catlin_model.plan, model=catlin_model,
                       preferences=Preferences(), profile=None)
    findings = rafter_span(ctx)
    assert findings
    assert all(f.result is Result.UNKNOWN for f in findings), \
        [f.message for f in findings]
    # The message names which engineering item governs, and the finding carries the
    # authority beside its verdict — still UNKNOWN, still blocking, but with an id a
    # professional seal can cover.
    assert all(f.authority is Authority.ENGINEERED for f in findings)
    assert {f.engineering_item for f in findings} == {"rafter/RF-HOUSE", "rafter/RF-GARAGE"}
    # The roof names its series ("11.875 TJI 230") so the price row and the PE scope both
    # key off something orderable. Either spelling is an engineered profile the sawn table
    # does not publish, which is the point being asserted.
    assert any("TJI" in f.message or "I-joist" in f.message for f in findings)
    # The trussed garage roof is the case the two-gate split exists for: this engine will
    # never compute it, so the item can never reach draft and correctly blocks a *sealed*
    # submittal without pretending anything was computed.
    garage = next(f for f in findings if f.engineering_item == "rafter/RF-GARAGE")
    assert "this engine computes none" in garage.message


def test_catlin_sliding_snow_is_screened_and_retained(catlin_model) -> None:
    """The landed house: the garage sheds onto the breezeway canopy, and it is guarded."""
    ctx = CheckContext(plan=catlin_model.plan, model=catlin_model,
                       preferences=Preferences(), profile=None)
    findings = sliding_snow(ctx)
    assert not [f for f in findings if f.result is Result.FAIL], \
        [f.message for f in findings]
    hit = next(f for f in findings if "GL-BW-ROOF" in f.message)
    assert hit.result is Result.PASS
    assert "RF-GARAGE" in hit.message


@pytest.mark.parametrize("profile,spacing,expected", [
    ("2x6", 16.0, 9.1),
    ("2x12", 24.0, 13.4),
])
def test_the_span_table_is_keyed_by_profile_and_spacing(profile, spacing, expected) -> None:
    """A rafter table is published per spacing; interpolating between rows is a design."""
    from typehaus.checks.structural.snow import _RAFTER_SPAN_FT

    assert _RAFTER_SPAN_FT[(profile, spacing)] == expected
    assert ("11.875 I-joist", 16.0) not in _RAFTER_SPAN_FT
