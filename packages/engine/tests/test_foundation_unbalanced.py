"""Unbalanced-backfill screen for plain concrete foundation walls (IRC R404.1.2(1)).

The interesting behaviour is at the edges: what it refuses to answer (no soil class, an
untabulated section), what an authored engineering spec does to it, and that an authored
``unbalanced_fill`` beats the derived proxy. The catlin fixture pins the landed verdicts.
"""

from __future__ import annotations

from typehaus.checks.jurisdiction import JurisdictionProfile
from typehaus.checks.registry import CheckContext, Preferences
from typehaus.checks.structural.foundation import foundation_unbalanced_fill
from typehaus.findings import Result
from typehaus.model import (
    Assembly,
    Building,
    FoundationWall,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    PlanModel,
    Project,
    Site,
    Storey,
    degF,
    face,
    ft,
    inch,
    pt,
)
from typehaus.resolve import resolve

_CONCRETE = Material(tag="concrete", name="Concrete", r_per_inch=0.08, perm_rating=3.2)


def _profile(soil_class: str | None = "GM") -> JurisdictionProfile:
    return JurisdictionProfile(
        name="test", edition="2024", effective_date="2024-01-01", irc_base="IRC 2021",
        coverage_statement="test fixture", soil_class=soil_class)


def _assembly(thickness_in: float) -> Assembly:
    return Assembly(tag=f"CONC{thickness_in:.0f}", layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(thickness_in),
              function=LayerFunction.STRUCTURE),
    ))


def _context(*, thickness_in: float = 12.0, bottom_ft: float = -9.0,
             soil_class: str | None = "GM", **wall_kwargs) -> CheckContext:
    """One 20' foundation wall from grade (0) down to ``bottom_ft``."""
    assembly = _assembly(thickness_in)
    library = Library(materials=(_CONCRETE,), assemblies=(assembly,))
    project = Project(name="FND", project_uuid="00000000-0000-4000-8000-0000000000f5",
                      site=Site(lat=44.9, lon=-93.2, elevation=ft(830), grade=ft(0),
                                design_temp_heating=degF(-15), design_temp_cooling=degF(90)),
                      building=Building(name="FND"))
    storey = Storey(uid="ST000000f1", tag="basement", elevation=ft(-9),
                    default_ceiling_height=ft(9))
    plan = PlanModel(project=project, library=library, storeys=(storey,))
    nodes = (
        Node(uid="N000000f01", tag="N-SW", position=pt(ft(0), ft(0))),
        Node(uid="N000000f02", tag="N-SE", position=pt(ft(20), ft(0))),
        Node(uid="N000000f03", tag="N-NE", position=pt(ft(20), ft(14))),
        Node(uid="N000000f04", tag="N-NW", position=pt(ft(0), ft(14))),
    )
    walls = (
        FoundationWall(uid="F000000f01", tag="W-F-S", start_node="N-SW", end_node="N-SE",
                       assembly=assembly.tag, alignment=face("concrete-ext"),
                       top_elevation=ft(0), bottom_elevation=ft(bottom_ft), **wall_kwargs),
        FoundationWall(uid="F000000f02", tag="W-F-E", start_node="N-SE", end_node="N-NE",
                       assembly=assembly.tag, alignment=face("concrete-ext"),
                       top_elevation=ft(0), bottom_elevation=ft(bottom_ft), **wall_kwargs),
        FoundationWall(uid="F000000f03", tag="W-F-N", start_node="N-NE", end_node="N-NW",
                       assembly=assembly.tag, alignment=face("concrete-ext"),
                       top_elevation=ft(0), bottom_elevation=ft(bottom_ft), **wall_kwargs),
        FoundationWall(uid="F000000f04", tag="W-F-W", start_node="N-NW", end_node="N-SW",
                       assembly=assembly.tag, alignment=face("concrete-ext"),
                       top_elevation=ft(0), bottom_elevation=ft(bottom_ft), **wall_kwargs),
    )
    plan = plan.with_elements("basement", (*nodes, *walls))
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], findings
    return CheckContext(plan=plan, model=model, preferences=Preferences(),
                        profile=_profile(soil_class), resolve_findings=list(findings))


def test_under_the_cap_passes() -> None:
    """12" at 45 psf/ft is good for 7'; 5' of fill is comfortably inside it."""
    findings = foundation_unbalanced_fill(_context(bottom_ft=-5.0))
    assert [f.result for f in findings] == [Result.PASS]
    assert "within the 7' plain-concrete limit" in findings[0].message


def test_past_the_cap_fails_and_asks_for_an_engineered_design() -> None:
    findings = foundation_unbalanced_fill(_context(bottom_ft=-9.0))
    assert [f.result for f in findings] == [Result.FAIL]
    assert "9.0' of unbalanced fill" in findings[0].message
    assert "engineered design" in findings[0].message
    assert findings[0].message.startswith("[advisory, not engineering]")


def test_an_authored_engineering_spec_is_the_design() -> None:
    """Same wall, same fill — but the engineer already answered, so the table stops applying.

    This is Door.header_spec's contract: an authored spec IS the design, and a check that
    kept demanding one would be asking for what is already in hand.
    """
    spec = "#5 @ 16\" o.c. vertical, EF, per S-2.1 rev. B"
    findings = foundation_unbalanced_fill(_context(bottom_ft=-9.0, engineering_spec=spec))
    assert [f.result for f in findings] == [Result.PASS]
    assert f"engineered design authored: {spec}" in findings[0].message


def test_an_authored_unbalanced_fill_beats_the_derived_proxy() -> None:
    """The derivation is a documented proxy, not a measurement: the author can correct it.

    A 9'-deep wall backfilled only 4' up — a walkout, or a wall braced by a slab — is not the
    condition grade-to-footing describes, and the authored number is the one that governs.
    """
    findings = foundation_unbalanced_fill(_context(bottom_ft=-9.0, unbalanced_fill=ft(4)))
    assert [f.result for f in findings] == [Result.PASS]
    assert "4.0' of unbalanced fill" in findings[0].message


def test_zero_unbalanced_fill_is_not_a_retaining_condition_at_all() -> None:
    """An interior cross wall retains nothing, so it is not screened rather than passed."""
    findings = foundation_unbalanced_fill(_context(bottom_ft=-9.0, unbalanced_fill=ft(0)))
    assert findings == []


def test_unknown_without_a_soil_class() -> None:
    """The 30/45/60 psf columns are two wall thicknesses apart — guessing is not defaulting."""
    findings = foundation_unbalanced_fill(_context(soil_class=None))
    assert [f.result for f in findings] == [Result.UNKNOWN]
    assert "soil_class" in findings[0].message


def test_unknown_off_the_published_thickness() -> None:
    findings = foundation_unbalanced_fill(_context(thickness_in=16.0))
    assert [f.result for f in findings] == [Result.UNKNOWN]
    assert "thicker than the table's 12\" maximum" in findings[0].message


def test_identical_walls_aggregate_into_one_finding() -> None:
    """Four identical walls are one condition and one decision, not four copies of it."""
    findings = foundation_unbalanced_fill(_context(bottom_ft=-9.0))
    assert len(findings) == 1
    assert len(findings[0].element_tags) == 4
    assert "4 CONC12 wall(s)" in findings[0].message


def test_catlin_basement_and_garden_fail_and_the_garage_stem_passes(catlin_model) -> None:
    """The landed house — accepted by decision, see plans/TODO.md."""
    from typehaus.checks.code.mn_residential.profile import MN_2024

    ctx = CheckContext(plan=catlin_model.plan, model=catlin_model,
                       preferences=Preferences(), profile=MN_2024)
    findings = foundation_unbalanced_fill(ctx)
    by_result = {}
    for f in findings:
        by_result.setdefault(f.result, []).append(f.message)
    fails = " | ".join(by_result.get(Result.FAIL, []))
    passes = " | ".join(by_result.get(Result.PASS, []))
    assert "CATLIN_BASEMENT_12" in fails
    assert "SUNKEN_GARDEN_WALL" in fails
    assert "GARAGE_ICF_8" in passes
    # The interior cross walls author unbalanced_fill=0, so they are not screened at all.
    assert "CATLIN_CONC_12_INT" not in fails + passes
