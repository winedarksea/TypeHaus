"""Per-zone heat-load sizing check (mep.heating_capacity) — tri-state + catlin fixture.

The check reuses ``estimate_block_load`` with a storey filter; capacities come from the
authored ``EquipmentType.heating_capacity_at_design_btuh`` and are never invented.
"""

from __future__ import annotations

import pytest

from typehaus.checks.mep.hvac import heating_capacity
from typehaus.checks.registry import CheckContext, Preferences
from typehaus.energy import estimate_block_load
from typehaus.findings import Result
from typehaus.model import (
    Assembly,
    Building,
    CavityFill,
    EquipmentType,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    Occupancy,
    PlanModel,
    Project,
    Room,
    Site,
    Storey,
    Wall,
    degF,
    ft,
    inch,
    pt,
)
from typehaus.resolve import resolve

_MATERIALS = (
    Material(tag="gwb", name="Gypsum board", r_per_inch=0.9, perm_rating=18.8),
    Material(tag="spf", name="SPF framing", r_per_inch=1.25, perm_rating=2.9),
    Material(tag="wool", name="Mineral wool", r_per_inch=4.2, perm_rating=116.0),
    Material(tag="ply", name="Structural plywood", r_per_inch=1.25, perm_rating=0.30),
)

_ASSEMBLY = Assembly(tag="EXT", layers=(
    Layer(name="gwb", material_ref="gwb", thickness=inch(0.625),
          function=LayerFunction.FINISH),
    Layer(name="stud", material_ref="spf", thickness=inch(5.5),
          function=LayerFunction.STRUCTURE, cavity=CavityFill(material_ref="wool")),
    Layer(name="sheathing", material_ref="ply", thickness=inch(0.5),
          function=LayerFunction.SHEATHING),
    Layer(name="siding", material_ref="ply", thickness=inch(0.5),
          function=LayerFunction.CLADDING),
))


def _plan(equipment_types: tuple[EquipmentType, ...]) -> PlanModel:
    """Two conditioned storeys of the same clad shell, side by side."""
    library = Library(materials=_MATERIALS, assemblies=(_ASSEMBLY,),
                      equipment_types=equipment_types)
    project = Project(name="HC", project_uuid="00000000-0000-4000-8000-0000000000c4",
                      site=Site(lat=44.9, lon=-93.2, elevation=ft(830),
                                design_temp_heating=degF(-15),
                                design_temp_cooling=degF(90)),
                      building=Building(name="HC"))
    storeys = (Storey(uid="ST00000h01", tag="lower", elevation=ft(0),
                      default_ceiling_height=ft(9)),
               Storey(uid="ST00000h02", tag="upper", elevation=ft(0),
                      default_ceiling_height=ft(9)))
    plan = PlanModel(project=project, library=library, storeys=storeys)
    for index, (tag, origin) in enumerate((("lower", 0.0), ("upper", 40.0)), 1):
        nodes = tuple(
            Node(uid=f"N{index}{i:08d}", tag=f"N-{tag}-{i}", position=position)
            for i, position in enumerate((
                pt(ft(origin), ft(0)), pt(ft(origin + 20), ft(0)),
                pt(ft(origin + 20), ft(14)), pt(ft(origin), ft(14)),
            ), 1))
        walls = tuple(
            Wall(uid=f"W{index}{i:08d}", tag=f"W-{tag}-{i}",
                 start_node=f"N-{tag}-{start}", end_node=f"N-{tag}-{end}",
                 assembly="EXT", top=ft(9))
            for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1))
        room = Room(uid=f"RM00000h{index:02d}", tag=f"RM-{tag}",
                    seed=pt(ft(origin + 10), ft(7)), occupancy=Occupancy.LIVING)
        plan = plan.with_elements(tag, (*nodes, *walls, room))
    return plan


def _context(plan: PlanModel) -> CheckContext:
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], findings
    return CheckContext(plan=plan, model=model, preferences=Preferences(), profile=None,
                        resolve_findings=list(findings))


def _heater(tag: str, name: str, **kwargs) -> EquipmentType:
    return EquipmentType(tag=tag, name=name, footprint=(inch(30), inch(12)),
                         height=inch(22), **kwargs)


# --- tri-state -----------------------------------------------------------------------

def test_pass_when_capacity_covers_the_zone_load() -> None:
    ctx = _context(_plan((_heater(
        "EQ-T-BIG", "Whole-house heat pump", heating_capacity_btuh=60000,
        heating_capacity_at_design_btuh=48000),)))
    findings = heating_capacity(ctx)
    assert [f.result for f in findings] == [Result.PASS]
    assert "margin +" in findings[0].message


def test_fail_when_capacity_falls_short_at_design() -> None:
    ctx = _context(_plan((_heater(
        "EQ-T-TINY", "Undersized heat pump", heating_capacity_btuh=6000,
        heating_capacity_at_design_btuh=1000),)))
    findings = heating_capacity(ctx)
    assert [f.result for f in findings] == [Result.FAIL]
    assert "undersized at design temp" in findings[0].message
    assert "margin -" in findings[0].message


def test_unknown_when_no_equipment_carries_a_rating() -> None:
    ctx = _context(_plan((_heater("EQ-T-ERV", "ERV, no heating rating"),)))
    findings = heating_capacity(ctx)
    assert [f.result for f in findings] == [Result.UNKNOWN]
    assert "heating_capacity" in findings[0].message


def test_unknown_when_only_the_rated_point_is_authored() -> None:
    """A 47F rating without an at-design figure must stay UNKNOWN — the check never
    invents a derate — while still reporting the computed zone load."""
    ctx = _context(_plan((_heater(
        "EQ-T-47ONLY", "Heat pump, rated point only", heating_capacity_btuh=36000),)))
    findings = heating_capacity(ctx)
    assert [f.result for f in findings] == [Result.UNKNOWN]
    assert "no heating_capacity_at_design_btuh" in findings[0].message
    assert "Btu/h at design" in findings[0].message  # the load is still reported


def test_named_zones_partition_and_sum_to_the_whole_house_load() -> None:
    ctx = _context(_plan((
        _heater("EQ-T-LOW", "Heat pump (lower zone)", heating_capacity_at_design_btuh=90000),
        _heater("EQ-T-UP", "Heat pump, everything else", heating_capacity_at_design_btuh=90000),
    )))
    findings = heating_capacity(ctx)
    assert [f.result for f in findings] == [Result.PASS, Result.PASS]
    by_tag = {f.element_tags[0]: f for f in findings}
    assert "lower zone" in by_tag["EQ-T-LOW"].message
    assert "upper zone" in by_tag["EQ-T-UP"].message
    whole = estimate_block_load(ctx.model, ctx.preferences).heating_load_btu_per_hour
    parts = sum(
        estimate_block_load(ctx.model, ctx.preferences, storeys=z).heating_load_btu_per_hour
        for z in (frozenset({"lower"}), frozenset({"upper"})))
    assert parts == pytest.approx(whole)


def test_two_unnamed_heaters_are_ambiguous_not_guessed() -> None:
    ctx = _context(_plan((
        _heater("EQ-T-A", "Heat pump A", heating_capacity_at_design_btuh=50000),
        _heater("EQ-T-B", "Heat pump B", heating_capacity_at_design_btuh=50000),
    )))
    findings = heating_capacity(ctx)
    assert all(f.result is Result.UNKNOWN for f in findings)
    assert any("ambiguous" in f.message for f in findings)


# --- catlin fixture -------------------------------------------------------------------

def test_catlin_zones_partition_the_conditioned_storeys(catlin_model) -> None:
    ctx = CheckContext(plan=catlin_model.plan, model=catlin_model,
                       preferences=Preferences(), profile=None)
    findings = heating_capacity(ctx)
    assert len(findings) == 2
    by_tag = {f.element_tags[0]: f for f in findings}
    assert set(by_tag) == {"EQ-T-MINISPLIT-LG", "EQ-T-MINISPLIT-SM"}
    # The small deep-cold unit names the basement; the large unit takes the rest of the
    # conditioned storeys. The unconditioned garage belongs to neither zone.
    assert "basement zone" in by_tag["EQ-T-MINISPLIT-SM"].message
    assert "attic+main+second zone" in by_tag["EQ-T-MINISPLIT-LG"].message
    assert "garage zone" not in by_tag["EQ-T-MINISPLIT-LG"].message
    assert "garage+" not in by_tag["EQ-T-MINISPLIT-LG"].message


def test_catlin_margins_read_off_the_resolved_model(catlin_model) -> None:
    ctx = CheckContext(plan=catlin_model.plan, model=catlin_model,
                       preferences=Preferences(), profile=None)
    findings = {f.element_tags[0]: f for f in heating_capacity(ctx)}
    types = {eq.tag: eq for eq in catlin_model.plan.library.equipment_types}
    zones = {"EQ-T-MINISPLIT-SM": frozenset({"basement"}),
             "EQ-T-MINISPLIT-LG": frozenset({"main", "second", "attic"})}
    for tag, storeys in zones.items():
        finding = findings[tag]
        load = estimate_block_load(
            catlin_model, Preferences(), storeys=storeys).heating_load_btu_per_hour
        capacity = types[tag].heating_capacity_at_design_btuh
        assert capacity is not None  # authored (placeholder) rating is present
        # The message reports exactly the resolved load, capacity, and margin.
        assert f"block load {load:,.0f} Btu/h" in finding.message
        assert f"{capacity:,.0f} Btu/h at-design capacity" in finding.message
        assert f"margin {capacity - load:+,.0f} Btu/h" in finding.message
        if finding.result is not Result.UNKNOWN:
            expected = Result.PASS if capacity >= load else Result.FAIL
            assert finding.result is expected
        else:
            assert "missing" in finding.message  # unknown_inputs are named, not hidden
    # Per-zone loads sum to the whole-house block load (zones share no components).
    whole = estimate_block_load(catlin_model, Preferences()).heating_load_btu_per_hour
    parts = sum(
        estimate_block_load(catlin_model, Preferences(), storeys=z).heating_load_btu_per_hour
        for z in zones.values())
    assert parts == pytest.approx(whole)
