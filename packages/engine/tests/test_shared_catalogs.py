"""Intrinsic contracts for shared declarative catalogs."""

from __future__ import annotations

import pytest

from typehaus import Service
from typehaus.library import (
    ALL_DOOR_TYPES,
    ALL_DUCT_PRODUCT_TYPES,
    ALL_ELECTRICAL_DEVICE_TYPES,
    ALL_MATERIALS,
    ALL_RAILING_TYPES,
    ALL_REGISTER_TYPES,
    ALL_VENTILATION_EQUIPMENT_TYPES,
    WINDOW_TYPES_16_INCH_MODULE,
)
from typehaus.model.enums import DoorOperation, WindowOperation


def test_shared_catalog_tags_are_unique_and_provenanced():
    catalogs = (
        ALL_MATERIALS,
        ALL_DOOR_TYPES,
        ALL_RAILING_TYPES,
        WINDOW_TYPES_16_INCH_MODULE,
        ALL_ELECTRICAL_DEVICE_TYPES,
        ALL_REGISTER_TYPES,
        ALL_DUCT_PRODUCT_TYPES,
        ALL_VENTILATION_EQUIPMENT_TYPES,
    )
    tags = [item.tag for catalog in catalogs for item in catalog]
    assert len(tags) == len(set(tags))
    assert all(item.source for catalog in catalogs for item in catalog)


def test_16_inch_module_window_ladder_preserves_dimensions_and_variants():
    types = {item.tag: item for item in WINDOW_TYPES_16_INCH_MODULE}
    assert len(types) == 21
    assert types["WT-1424"].width.inches == pytest.approx(14)
    assert types["WT-2764"].height.inches == pytest.approx(64)
    assert types["WT-3660-FIX"].operation is WindowOperation.FIXED
    assert types["WT-1424-T"].tempered
    assert types["WT-3048-T"].tempered
    assert types["WT-2736-HP"].u_factor.u_us == pytest.approx(0.14)
    assert types["WT-3048-HP"].frame_depth.inches == pytest.approx(4)


def test_standard_door_operations_are_explicit():
    types = {item.tag: item for item in ALL_DOOR_TYPES}
    assert types["DT-EXT-FRENCH60"].operation is DoorOperation.DOUBLE_SWING
    assert types["DT-INT-BIFOLD56"].operation is DoorOperation.BIFOLD
    assert types["DT-INT-BYPASS48"].operation is DoorOperation.SLIDE
    assert types["DT-EXT-OVERHEAD192"].operation is DoorOperation.OVERHEAD
    assert types["DT-INT-SWING36-TRIMLESS"].trimless


def test_shared_electrical_devices_keep_declared_services_and_loads():
    types = {item.tag: item for item in ALL_ELECTRICAL_DEVICE_TYPES}
    assert {port.service for port in types["ED-T-RECEPTACLE-620"].ports} == {
        Service.POWER_120,
        Service.POWER_240,
    }
    assert types["ED-T-EV-620"].load_va == pytest.approx(3840)
    assert types["ED-T-EV-1450"].load_va == pytest.approx(9600)
    assert {port.service for port in types["ED-T-NET-ENCLOSURE"].ports} == {
        Service.POWER_120,
        Service.DATA,
    }


def test_shared_register_direction_and_duct_physics_are_preserved():
    registers = {item.tag: item for item in ALL_REGISTER_TYPES}
    assert registers["REG-T-ERV-SUP"].ports[0].service is Service.SUPPLY_AIR
    assert registers["REG-T-ERV-EXH"].ports[0].service is Service.RETURN_AIR
    assert registers["REG-T-TRANSFER-1210"].ports == ()

    ducts = {item.tag: item for item in ALL_DUCT_PRODUCT_TYPES}
    assert ducts["DUCT-T-GALV-4"].bore_diameter.inches == pytest.approx(4)
    assert ducts["DUCT-T-SEMIRIGID-4"].bore_diameter.inches == pytest.approx(3.8)
    assert ducts["DUCT-T-GALV-6"].roughness_m == pytest.approx(0.0000914)
    assert ducts["DUCT-T-FLEX-6"].bend_equivalent_length.inches == pytest.approx(84)
