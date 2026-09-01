"""A clearance zone is a volume, not a plan polygon.

Plan overlap alone used to make every peer an obstruction, so a ceiling light at 8', a switch
plate at 4' and a flush floor register all "blocked" the floor beside a bed. The vertical band
(→ resolve/placeable_clear_floor_obstruction) settles that with published ICC A117.1-2017
limits — and must keep reporting the things that genuinely stand in the way.
"""

from __future__ import annotations

import pytest
from library.placeables.fixtures import TOILET, TOILET_WALL_HUNG

from typehaus.model import (
    Building,
    ClearancePolicy,
    ClearanceZone,
    ElectricalDevice,
    ElectricalDeviceType,
    Equipment,
    EquipmentKind,
    EquipmentType,
    Fixture,
    FixtureType,
    Footprint2D,
    Furniture,
    FurnitureType,
    Library,
    Mount,
    MountKind,
    PlanModel,
    Project,
    Register,
    RegisterType,
    Site,
    Storey,
    ft,
    inch,
    m,
    pt,
)
from typehaus.model.enums import DeviceKind, DuctSystem
from typehaus.resolve import resolve
from typehaus.resolve.placeable_clear_floor_obstruction import (
    CLEAR_FLOOR_SPACE_OBSTRUCTION_THRESHOLDS,
    PlaceableBodyProfile,
    clear_floor_space_obstruction,
)

_CONFLICT_CHECK_ID = "integrity.placeable_recommended_clearance_conflict"
_BED_TYPE_TAG = "F-BED"

# The bed is 1.5m x 2m at the origin; its side-access zone is the 0.9m band to its east, so
# anything centred 1.1m east of centre stands squarely in the middle of that zone.
_ZONE_OCCUPANT_X_M = 1.1


def _side_access_bed_type() -> FurnitureType:
    return FurnitureType(
        tag=_BED_TYPE_TAG, name="Bed", footprint=(m(1.5), m(2)), height=m(0.6),
        clearances=(ClearanceZone(footprint=Footprint2D(points=(
            pt(m(0.75), m(-1)), pt(m(1.65), m(-1)), pt(m(1.65), m(1)), pt(m(0.75), m(1)))),
            purpose="side access"),),
    )


def _bedroom_plan(*placed, library_extras: dict | None = None) -> PlanModel:
    extras = library_extras or {}
    return PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000091",
                        building=Building(name="test"),
                        site=Site(lat=0, lon=0, elevation=m(0))),
        # A non-zero storey elevation proves the band is measured against *this* storey's
        # floor rather than the project origin.
        storeys=(Storey(tag="upper", elevation=m(3), default_ceiling_height=m(2.6)),),
        library=Library(furniture_types=(_side_access_bed_type(),), **extras),
        elements={"upper": (
            Furniture(uid="bed-1", tag="BED", type_ref=_BED_TYPE_TAG, position=pt(m(0), m(0))),
            *placed,
        )},
    )


def _conflicts(findings) -> list[tuple[str, ...]]:
    return [finding.element_tags for finding in findings
            if finding.check_id == _CONFLICT_CHECK_ID]


def _messages(findings) -> list[str]:
    return [finding.message for finding in findings if finding.check_id == _CONFLICT_CHECK_ID]


def _device(tag: str, type_tag: str, mount: Mount) -> ElectricalDevice:
    return ElectricalDevice(uid=f"dev-{tag}", tag=tag, kind=DeviceKind.LIGHT,
                            type_ref=type_tag, position=pt(m(_ZONE_OCCUPANT_X_M), m(0)),
                            mount=mount)


def _supply_register_plan(*, recessed: bool) -> PlanModel:
    """The catlin arrangement: a 1"-deep supply grille standing in a bed's side-access zone."""
    register_type = RegisterType(tag="REG-T-SUPPLY", name="Supply register",
                                 footprint=(inch(12), inch(6)), height=inch(1))
    plan = _bedroom_plan(
        Register(uid="reg-1", tag="REGISTER", kind=DuctSystem.SUPPLY, type_ref="REG-T-SUPPLY",
                 position=pt(m(_ZONE_OCCUPANT_X_M), m(0)),
                 mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=recessed)),
    )
    return plan.model_copy(update={"library": Library(
        furniture_types=(_side_access_bed_type(),), register_types=(register_type,))})


# --- the three catlin cases, each cleared by its own cited section ------------------------

def test_a_ceiling_light_above_the_required_headroom_leaves_the_floor_clear() -> None:
    """A117.1 307.4: 80" of headroom is what clear floor space needs, and 8' is above it."""
    light_type = ElectricalDeviceType(tag="ED-T-LIGHT", name="Ceiling light",
                                      footprint=(inch(8), inch(8)), height=inch(2))
    plan = _bedroom_plan(
        _device("LIGHT", "ED-T-LIGHT", Mount(kind=MountKind.CEILING, elevation=ft(8))),
        library_extras={"electrical_device_types": (light_type,)},
    )
    _, findings = resolve(plan)

    assert _conflicts(findings) == []


def test_a_switch_plate_within_the_protrusion_limit_leaves_the_floor_clear() -> None:
    """A117.1 307.2: above 27", 4" of projection into a circulation path is allowed."""
    switch_type = ElectricalDeviceType(tag="ED-T-SWITCH", name="Wall switch",
                                       footprint=(inch(4), inch(2)), height=inch(2))
    plan = _bedroom_plan(
        _device("SWITCH", "ED-T-SWITCH", Mount(kind=MountKind.WALL, elevation=inch(48))),
        library_extras={"electrical_device_types": (switch_type,)},
    )
    _, findings = resolve(plan)

    assert _conflicts(findings) == []


def test_a_register_recessed_into_the_floor_leaves_the_floor_clear() -> None:
    """A117.1 303.2/305.2: a flush face is a permitted (in fact zero) change in level."""
    _, findings = resolve(_supply_register_plan(recessed=True))

    assert _conflicts(findings) == []


# --- what must keep reporting -------------------------------------------------------------

def test_the_same_register_sitting_proud_of_the_floor_still_reports() -> None:
    """The exemption is the recess, not the product class: drop it and the grille is a kerb."""
    _, findings = resolve(_supply_register_plan(recessed=False))

    assert _conflicts(findings) == [("BED", "REGISTER")]


def test_a_floor_standing_radiator_in_the_zone_still_reports() -> None:
    radiator = FurnitureType(tag="F-RADIATOR", name="Radiator", footprint=(m(1), m(0.2)),
                             height=inch(24))
    plan = _bedroom_plan(
        Furniture(uid="rad-1", tag="RADIATOR", type_ref="F-RADIATOR",
                  position=pt(m(_ZONE_OCCUPANT_X_M), m(0))),
    )
    plan = plan.model_copy(update={"library": Library(
        furniture_types=(_side_access_bed_type(), radiator))})
    _, findings = resolve(plan)

    assert _conflicts(findings) == [("BED", "RADIATOR")]


def test_a_low_console_table_in_the_zone_still_reports() -> None:
    """Under 27" the standard stops limiting projection — it does not stop the body existing."""
    console = FurnitureType(tag="F-CONSOLE", name="Console", footprint=(m(1), m(0.35)),
                            height=inch(26))
    plan = _bedroom_plan(
        Furniture(uid="console-1", tag="CONSOLE", type_ref="F-CONSOLE",
                  position=pt(m(_ZONE_OCCUPANT_X_M), m(0))),
    )
    plan = plan.model_copy(update={"library": Library(
        furniture_types=(_side_access_bed_type(), console))})
    _, findings = resolve(plan)

    assert _conflicts(findings) == [("BED", "CONSOLE")]


def test_a_wall_cabinet_projecting_past_the_protrusion_limit_still_reports() -> None:
    """12" off the wall at 40" AFF is three times what A117.1 307.2 allows.

    This is also the guard that the over-the-fixture exemption below never leaks onto a
    furniture zone: a bed's side-access zone is floor you stand on, and hanging the cabinet
    above the mattress does not give it back.
    """
    cabinet = FurnitureType(tag="F-CABINET", name="Wall cabinet",
                            footprint=(inch(24), inch(12)), height=inch(30))
    plan = _bedroom_plan(
        Furniture(uid="cab-1", tag="CABINET", type_ref="F-CABINET",
                  position=pt(m(_ZONE_OCCUPANT_X_M), m(0)),
                  mount=Mount(kind=MountKind.WALL, elevation=inch(40))),
    )
    plan = plan.model_copy(update={"library": Library(
        furniture_types=(_side_access_bed_type(), cabinet))})
    _, findings = resolve(plan)

    assert _conflicts(findings) == [("BED", "CABINET")]


def test_an_object_with_no_stated_height_still_reports_and_says_why() -> None:
    """An unknown body is never assumed clear — the finding names the missing dimension."""
    plan = _bedroom_plan(
        # ElectricalDevice tolerates a missing type by design, so this is the real-world
        # shape of "the height is not in the model".
        ElectricalDevice(uid="dev-x", tag="MYSTERY", kind=DeviceKind.LIGHT,
                         position=pt(m(_ZONE_OCCUPANT_X_M), m(0)),
                         mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    )
    _, findings = resolve(plan)

    assert _conflicts(findings) == [("BED", "MYSTERY")]
    assert "states no height" in _messages(findings)[0]


# --- the band itself, exercised without a whole plan --------------------------------------

@pytest.mark.parametrize(
    "profile, obstructs",
    [
        # Exactly at 80" of headroom clears; a hair under it does not.
        (PlaceableBodyProfile(2.032, 0.05), False),
        (PlaceableBodyProfile(2.031, 0.05), True),
        # Exactly at the 1/4" untreated level change clears; a hair over it does not.
        (PlaceableBodyProfile(0.0, 0.00635), False),
        (PlaceableBodyProfile(0.0, 0.0064), True),
        # A projection inside the 4" limit clears at any mounting height. §307.2 states the
        # limit for leading edges above 27"; below that it sets none at all, so a body that
        # would satisfy the stated limit up where you can walk into it satisfies it down
        # where a cane finds it. (This is what stops every 16"-AFF receptacle reading as an
        # obstruction of the floor beside a bed.)
        (PlaceableBodyProfile(0.6858, 0.05, 0.05), False),
        (PlaceableBodyProfile(0.6859, 0.05, 0.05), False),
        (PlaceableBodyProfile(0.4064, 0.0508, 0.0508), False),
        # 4" of projection is the limit, not a hair more.
        (PlaceableBodyProfile(1.2, 0.05, 0.1016), False),
        (PlaceableBodyProfile(1.2, 0.05, 0.102), True),
        # The protrusion allowance is only for wall-mounted bodies.
        (PlaceableBodyProfile(1.2, 0.05, None), True),
    ],
)
def test_each_threshold_is_the_published_limit(profile, obstructs) -> None:
    assert clear_floor_space_obstruction(profile).obstructs is obstructs


def test_thresholds_carry_the_sections_they_come_from() -> None:
    thresholds = CLEAR_FLOOR_SPACE_OBSTRUCTION_THRESHOLDS
    assert thresholds.minimum_headroom_over_clear_floor_space.inches == pytest.approx(80)
    assert thresholds.lowest_leading_edge_of_a_protruding_object.inches == pytest.approx(27)
    assert thresholds.maximum_protrusion_into_a_circulation_path.inches == pytest.approx(4)
    assert thresholds.maximum_untreated_change_in_level.inches == pytest.approx(0.25)
    assert thresholds.source == "ICC A117.1-2017 §303.2, §305.2, §307.2, §307.4"


def test_a_receptacle_at_outlet_height_leaves_the_floor_clear() -> None:
    """The same 4" allowance, 32" lower. A 2"-deep cover plate at 16" AFF is the single most
    common thing standing in a bedroom clearance zone, and it costs the floor nothing."""
    receptacle_type = ElectricalDeviceType(tag="ED-T-RECEPTACLE", name="Duplex receptacle",
                                           footprint=(inch(4), inch(2)), height=inch(2))
    plan = _bedroom_plan(
        _device("RECEPTACLE", "ED-T-RECEPTACLE",
                Mount(kind=MountKind.WALL, elevation=inch(16))),
        library_extras={"electrical_device_types": (receptacle_type,)},
    )
    _, findings = resolve(plan)

    assert _conflicts(findings) == []


# --- a zone is not a column of air: storage hung above a fixture ---------------------------
#
# UPC 402.5's 15" is elbow room for someone *seated* on the bowl and its 24" is standing room
# in front of it; neither is measured up to the ceiling. Stock over-toilet storage is 24-30"
# wide and 8-12" deep and is built and inspected routinely, and A117.1 §604.3.2 permits grab
# bars, dispensers, hooks and *shelves* to overlap a water closet's clearance outright.

_REQUIRED_CONFLICT_CHECK_ID = "integrity.placeable_required_clearance_conflict"

_CABINET_TYPE_TAG = "F-OT-CABINET"


def _required_conflicts(findings) -> list[tuple[str, ...]]:
    return [finding.element_tags for finding in findings
            if finding.check_id == _REQUIRED_CONFLICT_CHECK_ID]


def _over_toilet_cabinet_type() -> FurnitureType:
    """The catlin box: 45" wide, 6" deep, hung on the wall the bowl backs onto."""
    return FurnitureType(tag=_CABINET_TYPE_TAG, name="Over-toilet cabinet",
                         footprint=(inch(45), inch(6)), height=inch(60), storage=True)


def _water_closet_plan(fixture_type: FixtureType, cabinet_y_in: float,
                       cabinet_elevation_in: float) -> PlanModel:
    """One bowl at the origin facing local -y, with a wall cabinet ``cabinet_y_in`` behind it.

    ``active_code_profile`` is not decoration: the water-closet envelope is authored with
    ``code_profile="MN/IRC"``, so without it ``_resolved_clearance_zones`` drops the zone and
    every assertion below passes vacuously.
    """
    return PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000092",
                        building=Building(name="test"),
                        site=Site(lat=0, lon=0, elevation=m(0)),
                        active_code_profile="MN/IRC"),
        storeys=(Storey(tag="upper", elevation=m(3), default_ceiling_height=m(2.6)),),
        library=Library(fixture_types=(fixture_type,),
                        furniture_types=(_over_toilet_cabinet_type(),)),
        elements={"upper": (
            # The element's own ``Mount`` is the height contract — ``resolved_mount_elevation``
            # never reads the type's — so the wall-hung bowl's 1 3/8" lift has to be authored
            # here, exactly as the catlin plan authors it.
            Fixture(uid="wc-1", tag="WC", type_ref=fixture_type.tag, position=pt(m(0), m(0)),
                    mount=fixture_type.mount),
            Furniture(uid="cab-1", tag="CABINET", type_ref=_CABINET_TYPE_TAG,
                      position=pt(inch(0), inch(cabinet_y_in)),
                      mount=Mount(kind=MountKind.WALL, elevation=inch(cabinet_elevation_in))),
        )},
    )


def _behind_the_bowl_in(fixture_type: FixtureType) -> float:
    """Cabinet centre such that its 6" body straddles the back face of the bowl's footprint."""
    return fixture_type.footprint[1].inches / 2


# ``base + height``, not height alone: TOILET stands on the floor and tops out at 30", while
# TOILET_WALL_HUNG hangs 1 3/8" clear with a 13 5/8" body and tops out at 15". The catalogue
# already contains the case that distinguishes the two.
_ABOVE_THE_BOWL = [(TOILET, 48.0), (TOILET_WALL_HUNG, 15.0)]
_BESIDE_THE_BOWL = [(TOILET, 24.0), (TOILET_WALL_HUNG, 14.0)]


@pytest.mark.parametrize("fixture_type, elevation_in", _ABOVE_THE_BOWL)
def test_a_cabinet_hung_above_the_bowl_takes_none_of_its_use_space(
        fixture_type, elevation_in) -> None:
    _, findings = resolve(_water_closet_plan(
        fixture_type, _behind_the_bowl_in(fixture_type), elevation_in))

    assert _required_conflicts(findings) == []


@pytest.mark.parametrize("fixture_type, elevation_in", _BESIDE_THE_BOWL)
def test_a_cabinet_hung_below_the_bowls_own_top_still_reports(
        fixture_type, elevation_in) -> None:
    """Down at tank level the box is beside the person, not above them — real elbow room."""
    _, findings = resolve(_water_closet_plan(
        fixture_type, _behind_the_bowl_in(fixture_type), elevation_in))

    assert _required_conflicts(findings) == [("WC", "CABINET")]


def test_a_cabinet_on_the_wall_the_bowl_faces_still_reports() -> None:
    """The condition that keeps the exemption honest: in front of you is walked into."""
    _, findings = resolve(_water_closet_plan(
        TOILET, -_behind_the_bowl_in(TOILET) - 3, 48.0))

    assert _required_conflicts(findings) == [("WC", "CABINET")]


def test_a_cabinet_above_an_equipment_separation_band_still_reports() -> None:
    """The exemption is scoped to ``kind == "Fixture"`` for a reason.

    The catalogue's other REQUIRED zone is ``EQ-T-ESS-BATT``'s 3'-0" band, whose own comment
    insists it is not a working space — it is a separation rule about heat and fire spread
    between devices. A body hung above a battery still has to keep away from it.
    """
    battery_type = EquipmentType(
        tag="EQ-T-BATT", name="Battery", footprint=(inch(30), inch(12)), height=inch(48),
        clearances=(ClearanceZone(footprint=Footprint2D(points=(
            pt(inch(-33), inch(-6)), pt(inch(33), inch(-6)),
            pt(inch(33), inch(6)), pt(inch(-33), inch(6)))),
            purpose="equipment separation", policy=ClearancePolicy.REQUIRED),),
    )
    plan = PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000093",
                        building=Building(name="test"),
                        site=Site(lat=0, lon=0, elevation=m(0)),
                        active_code_profile="MN/IRC"),
        storeys=(Storey(tag="upper", elevation=m(3), default_ceiling_height=m(2.6)),),
        library=Library(equipment_types=(battery_type,),
                        furniture_types=(_over_toilet_cabinet_type(),)),
        elements={"upper": (
            Equipment(uid="batt-1", tag="BATTERY", kind=EquipmentKind.BATTERY,
                      type_ref="EQ-T-BATT", footprint=(inch(30), inch(12)),
                      position=pt(m(0), m(0))),
            Furniture(uid="cab-1", tag="CABINET", type_ref=_CABINET_TYPE_TAG,
                      position=pt(inch(0), inch(3)),
                      mount=Mount(kind=MountKind.WALL, elevation=inch(60))),
        )},
    )
    _, findings = resolve(plan)

    assert _required_conflicts(findings) == [("BATTERY", "CABINET")]
