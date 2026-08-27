"""Per-zone heat-load sizing check (mep.heating_capacity) — tri-state + catlin fixture.

A zone is the authored ``Equipment.zone_rooms`` of a rated unit, unioned with the rooms of
every indoor head naming it through ``outdoor_ref``. The check reuses ``estimate_block_load``
with a *room* filter; capacities come from the authored
``EquipmentType.heating_capacity_at_design_btuh`` and are never invented, and a conditioned
room no unit claims is reported as unclaimed rather than folded into a neighbour.
"""

from __future__ import annotations

import pytest

from typehaus.checks.mep.hvac import cooling_capacity, heating_capacity
from typehaus.checks.registry import CheckContext, Preferences
from typehaus.energy import estimate_block_load
from typehaus.findings import Result
from typehaus.model import (
    Assembly,
    Building,
    CavityFill,
    Equipment,
    EquipmentKind,
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

# Every fixture authors a blower-door result: without one the block load names
# ach50/cfm50 in `unknown_inputs` and the check is honestly UNKNOWN, which would make every
# capacity assertion below untestable for the wrong reason.
_PREFERENCES = Preferences(cfm50=900.0, infiltration_n_factor=18.0)

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

_LOWER_ROOM = "RM-lower"
_UPPER_ROOM = "RM-upper"


def _plan(equipment_types: tuple[EquipmentType, ...],
          equipment: tuple[Equipment, ...] = ()) -> PlanModel:
    """Two conditioned storeys of the same clad shell, side by side, one room each."""
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
        # The equipment for a storey is whatever names one of its rooms; the fixtures below
        # keep it simple by putting every unit on "lower".
        extra = equipment if tag == "lower" else ()
        plan = plan.with_elements(tag, (*nodes, *walls, room, *extra))
    return plan


def _context(plan: PlanModel) -> CheckContext:
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], findings
    return CheckContext(plan=plan, model=model, preferences=_PREFERENCES, profile=None,
                        resolve_findings=list(findings))


def _heater(tag: str, name: str, **kwargs) -> EquipmentType:
    return EquipmentType(tag=tag, name=name, footprint=(inch(30), inch(12)),
                         height=inch(22), **kwargs)


def _outdoor(tag: str, type_ref: str, uid: str, zone_rooms=(),) -> Equipment:
    return Equipment(uid=uid, tag=tag, kind=EquipmentKind.HEAT_PUMP,
                     position=pt(ft(10), ft(7)), footprint=(inch(30), inch(12)),
                     type_ref=type_ref, zone_rooms=tuple(zone_rooms))


def _head(tag: str, type_ref: str, uid: str, outdoor_ref: str, zone_rooms) -> Equipment:
    return Equipment(uid=uid, tag=tag, kind=EquipmentKind.INDOOR_HEAD,
                     position=pt(ft(10), ft(7)), footprint=(inch(30), inch(12)),
                     type_ref=type_ref, outdoor_ref=outdoor_ref,
                     zone_rooms=tuple(zone_rooms))


_BOTH_ROOMS = (_LOWER_ROOM, _UPPER_ROOM)


# --- tri-state -----------------------------------------------------------------------

def test_pass_when_capacity_covers_the_zone_load() -> None:
    ctx = _context(_plan(
        (_heater("EQ-T-BIG", "Whole-house heat pump", heating_capacity_btuh=60000,
                 heating_capacity_at_design_btuh=48000),),
        (_outdoor("EQ-BIG", "EQ-T-BIG", "EQ00000h01", _BOTH_ROOMS),)))
    findings = heating_capacity(ctx)
    assert [f.result for f in findings] == [Result.PASS]
    assert "margin +" in findings[0].message
    # The rooms it claims are named in the message — a zone the reader can check by eye.
    assert _LOWER_ROOM in findings[0].message and _UPPER_ROOM in findings[0].message


def test_fail_when_capacity_falls_short_at_design() -> None:
    ctx = _context(_plan(
        (_heater("EQ-T-TINY", "Undersized heat pump", heating_capacity_btuh=6000,
                 heating_capacity_at_design_btuh=1000),),
        (_outdoor("EQ-TINY", "EQ-T-TINY", "EQ00000h02", _BOTH_ROOMS),)))
    findings = heating_capacity(ctx)
    assert [f.result for f in findings] == [Result.FAIL]
    assert "undersized at design temp" in findings[0].message
    assert "margin -" in findings[0].message


def test_unknown_when_no_equipment_carries_a_rating() -> None:
    ctx = _context(_plan(
        (_heater("EQ-T-ERV", "ERV, no heating rating"),),
        (_outdoor("EQ-ERV", "EQ-T-ERV", "EQ00000h03", _BOTH_ROOMS),)))
    findings = heating_capacity(ctx)
    assert [f.result for f in findings] == [Result.UNKNOWN, Result.UNKNOWN]
    assert "heating_capacity" in findings[0].message
    # An unrated unit claims nothing, so both rooms are reported unclaimed.
    assert "in no equipment zone_rooms" in findings[1].message


def test_unknown_when_only_the_rated_point_is_authored() -> None:
    """A 47F rating without an at-design figure must stay UNKNOWN — the check never
    invents a derate — while still reporting the computed zone load."""
    ctx = _context(_plan(
        (_heater("EQ-T-47ONLY", "Heat pump, rated point only",
                 heating_capacity_btuh=36000),),
        (_outdoor("EQ-47", "EQ-T-47ONLY", "EQ00000h04", _BOTH_ROOMS),)))
    findings = heating_capacity(ctx)
    assert [f.result for f in findings] == [Result.UNKNOWN]
    assert "no heating_capacity_at_design_btuh" in findings[0].message
    assert "Btu/h at design" in findings[0].message  # the load is still reported


def test_zone_rooms_partition_and_nearly_sum_to_the_whole_house_load() -> None:
    """Two units, one room each. Room-scoped loads are approximate by design (envelope area
    is attributed by plan overlap), so the two zones sum to the whole-house block load to
    within a few percent rather than exactly — which is what the docstring promises."""
    ctx = _context(_plan(
        (_heater("EQ-T-LOW", "Heat pump (lower)", heating_capacity_at_design_btuh=90000),
         _heater("EQ-T-UP", "Heat pump (upper)", heating_capacity_at_design_btuh=90000)),
        (_outdoor("EQ-LOW", "EQ-T-LOW", "EQ00000h05", (_LOWER_ROOM,)),
         _outdoor("EQ-UP", "EQ-T-UP", "EQ00000h06", (_UPPER_ROOM,)))))
    findings = heating_capacity(ctx)
    assert [f.result for f in findings] == [Result.PASS, Result.PASS]
    by_tag = {f.element_tags[0]: f for f in findings}
    assert _LOWER_ROOM in by_tag["EQ-LOW"].message
    assert _UPPER_ROOM in by_tag["EQ-UP"].message
    whole = estimate_block_load(ctx.model, ctx.preferences).heating_load_btu_per_hour
    parts = sum(
        estimate_block_load(ctx.model, ctx.preferences,
                            rooms=frozenset({room})).heating_load_btu_per_hour
        for room in _BOTH_ROOMS)
    assert parts == pytest.approx(whole, rel=0.05)


def test_a_condensers_zone_is_the_union_of_its_heads_rooms() -> None:
    """One multi-zone condenser, two heads: the capacity is compared against the load of
    both rooms together, because one compressor has to make it all."""
    ctx = _context(_plan(
        (_heater("EQ-T-MULTI", "Multi condenser", heating_capacity_at_design_btuh=90000),
         _heater("EQ-T-HEAD", "Wall head")),
        (_outdoor("EQ-MULTI", "EQ-T-MULTI", "EQ00000h07"),
         _head("EQ-H1", "EQ-T-HEAD", "EQ00000h08", "EQ-MULTI", (_LOWER_ROOM,)),
         _head("EQ-H2", "EQ-T-HEAD", "EQ00000h09", "EQ-MULTI", (_UPPER_ROOM,)))))
    findings = heating_capacity(ctx)
    # One finding: the heads carry no rating of their own and never claim a zone.
    assert [f.result for f in findings] == [Result.PASS]
    assert findings[0].element_tags == ("EQ-MULTI",)
    assert _LOWER_ROOM in findings[0].message and _UPPER_ROOM in findings[0].message


def test_an_unclaimed_conditioned_room_is_named_not_absorbed() -> None:
    ctx = _context(_plan(
        (_heater("EQ-T-ONE", "Heat pump", heating_capacity_at_design_btuh=90000),),
        (_outdoor("EQ-ONE", "EQ-T-ONE", "EQ00000h10", (_LOWER_ROOM,)),)))
    findings = heating_capacity(ctx)
    unclaimed = [f for f in findings if f.result is Result.UNKNOWN]
    assert len(unclaimed) == 1
    assert _UPPER_ROOM in unclaimed[0].message
    assert _UPPER_ROOM in unclaimed[0].element_tags


def test_a_rated_unit_with_no_zone_rooms_is_unknown_not_whole_house() -> None:
    ctx = _context(_plan(
        (_heater("EQ-T-ORPHAN", "Heat pump", heating_capacity_at_design_btuh=90000),),
        (_outdoor("EQ-ORPHAN", "EQ-T-ORPHAN", "EQ00000h11"),)))
    findings = heating_capacity(ctx)
    assert all(f.result is Result.UNKNOWN for f in findings)
    assert any("no zone_rooms authored" in f.message for f in findings)


# --- the cooling advisory beside it ----------------------------------------------------

def test_cooling_is_unknown_without_an_authored_cooling_rating() -> None:
    ctx = _context(_plan(
        (_heater("EQ-T-HEATONLY", "Heat pump", heating_capacity_at_design_btuh=90000),),
        (_outdoor("EQ-HEATONLY", "EQ-T-HEATONLY", "EQ00000h12", _BOTH_ROOMS),)))
    findings = cooling_capacity(ctx)
    assert [f.result for f in findings] == [Result.UNKNOWN]
    assert "no cooling_capacity_btuh" in findings[0].message


def test_cooling_passes_when_the_rating_covers_the_sensible_load() -> None:
    ctx = _context(_plan(
        (_heater("EQ-T-COOL", "Heat pump", heating_capacity_at_design_btuh=90000,
                 cooling_capacity_btuh=60000),),
        (_outdoor("EQ-COOL", "EQ-T-COOL", "EQ00000h13", _BOTH_ROOMS),)))
    findings = cooling_capacity(ctx)
    assert [f.result for f in findings] == [Result.PASS]
    assert "no latent or internal gains" in findings[0].message


# --- catlin fixture -------------------------------------------------------------------

def test_catlin_zones_follow_the_authored_pairings(catlin_model) -> None:
    """Three Gree systems: one condenser per system, each zone the union of its indoor
    units' rooms. The unconditioned garage belongs to no zone."""
    from typehaus.takeoff.hvac import heating_zones

    zones, unclaimed = heating_zones(catlin_model, Preferences())
    by_tag = {zone.equipment_tag: zone for zone in zones}
    assert set(by_tag) == {"EQ-M-HP1-OD", "EQ-M-HP2-OD", "EQ-M-HP3-OD"}
    assert by_tag["EQ-M-HP1-OD"].indoor_tags == ("EQ-S-HP1-AH",)
    assert set(by_tag["EQ-M-HP2-OD"].indoor_tags) == {
        "EQ-B-HP2-GYM", "EQ-M-HP2-BED", "EQ-M-HP2-LIVING"}
    assert by_tag["EQ-M-HP3-OD"].indoor_tags == ("EQ-M-HP3-STAIR",)
    assert "RM-GARAGE" not in {room for zone in zones for room in zone.rooms}
    assert "RM-GARAGE" not in unclaimed
    # No zone claims a room another zone already claims.
    claimed = [room for zone in zones for room in zone.rooms]
    assert len(claimed) == len(set(claimed))


def test_catlin_margins_read_off_the_resolved_model(catlin_model) -> None:
    from typehaus.takeoff.hvac import heating_zones

    preferences = Preferences()
    ctx = CheckContext(plan=catlin_model.plan, model=catlin_model,
                       preferences=preferences, profile=None)
    findings = {f.element_tags[0]: f for f in heating_capacity(ctx)
                if f.element_tags and f.element_tags[0].startswith("EQ-")}
    zones, _ = heating_zones(catlin_model, preferences)
    for zone in zones:
        finding = findings[zone.equipment_tag]
        capacity = zone.heating_capacity_at_design_btuh
        assert capacity is not None  # authored datasheet rating is present
        load = zone.heating_load_btu_per_hour
        # Supplemental resistance heat in the zone's rooms counts toward the margin, and is
        # named in the message so a margin that only clears because of it says so.
        available = capacity + zone.supplemental_btuh
        # The message reports exactly the resolved load, capacity, and margin.
        assert f"block load {load:,.0f} Btu/h" in finding.message
        assert f"{capacity:,.0f} Btu/h at-design capacity" in finding.message
        assert f"margin {available - load:+,.0f} Btu/h" in finding.message
        if zone.supplemental_tags:
            assert f"{zone.supplemental_btuh:,.0f} Btu/h supplemental" in finding.message
            for tag in zone.supplemental_tags:
                assert tag in finding.message
        if finding.result is not Result.UNKNOWN:
            expected = Result.PASS if available >= load else Result.FAIL
            assert finding.result is expected
        else:
            assert "missing" in finding.message  # unknown_inputs are named, not hidden


def test_catlin_zone_loads_do_not_exceed_the_whole_house_load(catlin_model) -> None:
    """Room-scoped loads are approximate, but they are a *partition*: no room is in two
    zones, so their sum cannot exceed the whole-house block load by more than the
    attribution slop, and it is short by whatever the unclaimed rooms carry."""
    from typehaus.takeoff.hvac import heating_zones

    preferences = Preferences()
    zones, unclaimed = heating_zones(catlin_model, preferences)
    whole = estimate_block_load(
        catlin_model, preferences).heating_load_btu_per_hour
    parts = sum(zone.heating_load_btu_per_hour for zone in zones)
    assert 0 < parts <= whole * 1.05
    # Catlin's attic den is deliberately served by nothing yet. RM-A-WEST-UNFIN left this set
    # on 2026-07-30: REG-A-HP-WEST (a floor boot off DU-S-HP-SUITE) put it in System 1's
    # zone.
    #
    # RM-B-ESS joined it 2026-08-02 and stays: the battery closet is a 12 sf cabinet carved
    # out of RM-B-FURNACE, and it gets no terminal of its own on purpose. It is enclosed on
    # every side by conditioned space, its own occupant is a heat *source*, and a supply
    # boot into a sealed Type X box is the last thing that enclosure wants. Unclaimed here
    # means "served by no zone", which is the true statement, not a gap to fill.
    #
    # RM-M-MUD-CLOSET joined the same day, for the mundane version of the same reason:
    # it replaced the furniture closet FURN-M-MUD-CLOSET-S sat in (never a room, never
    # zoned), and its 48" bypass slider onto the conditioned mudroom is wide open air
    # transfer, not a sealed enclosure — a dedicated supply register would be serving a
    # storage closet through its own open door.
    # RM-M-PANTRY joined them 2026-08-24 for exactly RM-M-MUD-CLOSET's reason: a framed
    # reach-in off a conditioned room, with no register and no need of one — it borrows the
    # kitchen's air through a 60" bypass that is open whenever anyone is in there.
    assert set(unclaimed) == {"RM-A-DEN", "RM-B-ESS", "RM-M-MUD-CLOSET", "RM-M-PANTRY"}


# --- supplemental resistance heat ------------------------------------------------------
#
# A radiant mat or an electric fireplace is real heat at the design temperature: excluding it
# reports a shortfall the house does not have. But it is never a zone of its own — nothing is
# sized around a fireplace — so it is credited to the zone containing its room and nowhere
# else. These four tests pin both halves of that rule.


def _supplemental(tag: str, type_ref: str, uid: str, room: str) -> Equipment:
    return Equipment(uid=uid, tag=tag, kind=EquipmentKind.SPACE_HEATER,
                     position=pt(ft(10), ft(7)), footprint=(inch(30), inch(12)),
                     type_ref=type_ref, room=room)


def _undersized_plus_supplemental(capacity: float, supplemental: float) -> CheckContext:
    return _context(_plan(
        (_heater("EQ-T-HP", "Heat pump", heating_capacity_at_design_btuh=capacity),
         _heater("EQ-T-FP", "Electric fireplace",
                 heating_capacity_btuh=supplemental,
                 heating_capacity_at_design_btuh=supplemental,
                 supplemental_heat=True)),
        (_outdoor("EQ-HP", "EQ-T-HP", "EQ00000h20", _BOTH_ROOMS),
         _supplemental("EQ-FP", "EQ-T-FP", "EQ00000h21", _LOWER_ROOM))))


def _load(ctx: CheckContext) -> float:
    return estimate_block_load(ctx.model, ctx.preferences).heating_load_btu_per_hour


def test_supplemental_heat_joins_the_zone_containing_its_room() -> None:
    """Capacity alone is short; capacity + the fireplace clears the load."""
    probe = _undersized_plus_supplemental(1000.0, 0.0)
    load = _load(probe)
    ctx = _undersized_plus_supplemental(load - 2000.0, 5000.0)
    findings = heating_capacity(ctx)
    assert [f.result for f in findings] == [Result.PASS]
    assert "5,000 Btu/h supplemental (EQ-FP)" in findings[0].message


def test_supplemental_heat_never_opens_a_zone_of_its_own() -> None:
    """It is rated, so a naive `_rated()` would give it a zone — and double-count it."""
    ctx = _undersized_plus_supplemental(90000.0, 5000.0)
    findings = heating_capacity(ctx)
    assert [f.element_tags[0] for f in findings] == ["EQ-HP"]
    assert "EQ-FP zone" not in findings[0].message


def test_supplemental_heat_in_an_unclaimed_room_is_not_counted() -> None:
    """The fireplace heats the *upper* room, which the heat pump's zone does not include, so
    it must not pad the lower zone's margin — and the upper room stays honestly unclaimed."""
    ctx = _context(_plan(
        (_heater("EQ-T-HP", "Heat pump", heating_capacity_at_design_btuh=90000),
         _heater("EQ-T-FP", "Electric fireplace", heating_capacity_at_design_btuh=5000,
                 supplemental_heat=True)),
        (_outdoor("EQ-HP", "EQ-T-HP", "EQ00000h22", (_LOWER_ROOM,)),
         _supplemental("EQ-FP", "EQ-T-FP", "EQ00000h23", _UPPER_ROOM))))
    findings = heating_capacity(ctx)
    zone = next(f for f in findings if f.element_tags[0] == "EQ-HP")
    assert "supplemental" not in zone.message
    assert any("in no equipment zone_rooms" in f.message and _UPPER_ROOM in f.message
               for f in findings)


def test_a_zone_without_supplemental_heat_says_nothing_about_it() -> None:
    """No supplemental heat authored → the message stays the plain capacity-vs-load line."""
    ctx = _context(_plan(
        (_heater("EQ-T-HP", "Heat pump", heating_capacity_at_design_btuh=90000),),
        (_outdoor("EQ-HP", "EQ-T-HP", "EQ00000h24", _BOTH_ROOMS),)))
    findings = heating_capacity(ctx)
    assert [f.result for f in findings] == [Result.PASS]
    assert "supplemental" not in findings[0].message
