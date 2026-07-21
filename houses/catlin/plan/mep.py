"""Catlin MEP: plumbing sleeves/drains (Phase 2) + HVAC trunk ducts + electrical (Phase 3).

Authored routing only — the user places runs/ducts/devices; the resolver validates them
against the framing (joist bays, bearing lines, slab hosts) and the sheets draw them.

Plumbing: sleeve positions are the exact pre-pour centers the concrete crew works from —
the resolver validates them against the fixture drain point they serve
(``mep.sleeve_alignment``); nothing here is derived. Second-floor ensuite drains drop
through the framed floor into the existing INT_2X6_PLUMBING wet wall (W-S-BD-N) with no
sleeve needed — only a cast concrete deck needs a pre-positioned penetration.

HVAC: the second-floor trunks run in the FS-SECOND joist bays (11.875" I-joist, 16" o.c.,
direction "x"). Bay centers are ``8" + n*16"`` from the joist-line math in
resolve/floors.py; bay 15 (y=20'-8") and bay 17 (y=23'-4") are both clear of the stair
FloorOpening (x:11'-18', y:25'-36') and both cross the central bearing wall at x=18'.
"""

from typehaus import (
    DeviceKind,
    DuctRouting,
    DuctRun,
    DuctSystem,
    ElectricalDevice,
    ElectricalDeviceType,
    Equipment,
    EquipmentKind,
    EquipmentType,
    PipeRun,
    PipeSystem,
    Register,
    RegisterType,
    Service,
    ServicePort,
    SleevePenetration,
    ft,
    inch,
    pt,
)

REGISTER_TYPES = (
    RegisterType(tag="REG-T-SUPPLY", name="Supply register", footprint=(inch(12), inch(6)), height=inch(1),
                 ports=(ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
    RegisterType(tag="REG-T-RETURN", name="Return grille", footprint=(inch(14), inch(8)), height=inch(1),
                 ports=(ServicePort(tag="return", service=Service.RETURN_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
)

EQUIPMENT_TYPES = (
    EquipmentType(tag="EQ-T-FURNACE", name="Gas furnace", footprint=(inch(24), inch(28)), height=ft(5),
                  ports=(ServicePort(tag="gas", service=Service.GAS, position=(ft(0), ft(0), ft(0))),
                         ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))),
                         ServicePort(tag="supply", service=Service.SUPPLY_AIR, position=(ft(0), ft(0), ft(4))),
                         ServicePort(tag="return", service=Service.RETURN_AIR, position=(ft(0), ft(0), ft(4))))),
    EquipmentType(tag="EQ-T-WATER-HEATER", name="Water heater", footprint=(inch(24), inch(24)), height=ft(5),
                  ports=(ServicePort(tag="cold", service=Service.WATER_COLD, position=(ft(0), ft(0), ft(4))),
                         ServicePort(tag="hot", service=Service.WATER_HOT, position=(ft(0), ft(0), ft(4))),
                         ServicePort(tag="gas", service=Service.GAS, position=(ft(0), ft(0), ft(0))))),
)

ELECTRICAL_DEVICE_TYPES = (
    ElectricalDeviceType(tag="ED-T-PANEL", name="Electrical panel", footprint=(inch(20), inch(4)), height=ft(3),
                          ports=(ServicePort(tag="service", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-LIGHT", name="Ceiling light", footprint=(inch(8), inch(8)), height=inch(2),
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-SWITCH", name="Wall switch", footprint=(inch(4), inch(2)), height=inch(2),
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-RECEPTACLE", name="Receptacle", footprint=(inch(4), inch(2)), height=inch(2),
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),)),
)

SLEEVES = [
    SleevePenetration(uid="CMP901AAAA", tag="SP-M-WC1", host_ref="SL-M-DECK",
                      position=pt(ft(2), ft(24)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-M-BATH1-WC"),
    SleevePenetration(uid="CMP902AAAA", tag="SP-M-WC2", host_ref="SL-M-DECK",
                      position=pt(ft(3), ft(18)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-M-BATH2-WC"),
    # Projection of FX-M-BATH1-LAV (3'-6", 24') onto the W-M-BAE structure-layer
    # centerline (x=4, from storeys/main.py node coordinates N-M-BA1/N-M-BA2).
    SleevePenetration(uid="CMP903AAAA", tag="SP-M-LAV1", host_ref="SL-M-DECK",
                      position=pt(ft(4), ft(24)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), serves_fixture="FX-M-BATH1-LAV"),
    # Projection of FX-M-LAUNDRY (10'-6", 20') onto the W-M-BA2E2 centerline (x=8).
    SleevePenetration(uid="CMP904AAAA", tag="SP-M-WASH", host_ref="SL-M-DECK",
                      position=pt(ft(8), ft(20)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-LAUNDRY"),
]

# Basement-ceiling collector: picks up both WC sleeves, heads to the south-wall sewer
# exit. Axis-aligned so the authored length is exact (6' + 1' + 18' = 25'); inverts give
# a comfortable 8"/25' ≈ 0.32"/ft slope, well above the 1/4"/ft minimum for a 3" line.
DRAINS = [
    PipeRun(uid="CMP905AAAA", tag="PR-B-MAIN-DRAIN", system=PipeSystem.DRAIN,
           path=(pt(ft(2), ft(24)), pt(ft(2), ft(18)), pt(ft(3), ft(18)), pt(ft(3), ft(0))),
           diameter=inch(3), start_elevation=ft(8), end_elevation=ft(7, 4),
           serves=("FX-M-BATH1-WC", "FX-M-BATH2-WC")),
]

# --- HVAC: second-floor supply/return trunks in the FS-SECOND joist bays ------------
DUCTS = [
    DuctRun(uid="CMD901AAAA", tag="DU-M-SUP-TRUNK", system=DuctSystem.SUPPLY,
           path=(pt(ft(4), ft(20, 8)), pt(ft(32), ft(20, 8))), width=inch(12), depth=inch(8),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-SECOND"),
    DuctRun(uid="CMD902AAAA", tag="DU-M-RET-TRUNK", system=DuctSystem.RETURN,
           path=(pt(ft(4), ft(23, 4)), pt(ft(32), ft(23, 4))), width=inch(14), depth=inch(8),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-SECOND"),
]

REGISTERS = [
    Register(uid="CMR901AAAA", tag="REG-S-SUP1", kind=DuctSystem.SUPPLY,
            position=pt(ft(9), ft(4)), duct_ref="DU-M-SUP-TRUNK", type_ref="REG-T-SUPPLY"),
    Register(uid="CMR902AAAA", tag="REG-S-SUP2", kind=DuctSystem.SUPPLY,
            position=pt(ft(27), ft(4)), duct_ref="DU-M-SUP-TRUNK", type_ref="REG-T-SUPPLY"),
    Register(uid="CMR903AAAA", tag="REG-S-SUP3", kind=DuctSystem.SUPPLY,
            position=pt(ft(29), ft(16)), duct_ref="DU-M-SUP-TRUNK", type_ref="REG-T-SUPPLY"),
    Register(uid="CMR904AAAA", tag="REG-S-SUP4", kind=DuctSystem.SUPPLY,
            position=pt(ft(29), ft(32)), duct_ref="DU-M-SUP-TRUNK", type_ref="REG-T-SUPPLY"),
    Register(uid="CMR905AAAA", tag="REG-S-RET1", kind=DuctSystem.RETURN,
            position=pt(ft(20), ft(20)), duct_ref="DU-M-RET-TRUNK", type_ref="REG-T-RETURN"),
    Register(uid="CMR906AAAA", tag="REG-S-RET2", kind=DuctSystem.RETURN,
            position=pt(ft(9), ft(20)), duct_ref="DU-M-RET-TRUNK", type_ref="REG-T-RETURN"),
]

EQUIPMENT = [
    Equipment(uid="CME901AAAA", tag="EQ-B-FURNACE", kind=EquipmentKind.FURNACE,
             position=pt(ft(4), ft(29)), footprint=(inch(24), inch(28)), room="RM-B-FURNACE", type_ref="EQ-T-FURNACE"),
    Equipment(uid="CME902AAAA", tag="EQ-B-WH", kind=EquipmentKind.WATER_HEATER,
             position=pt(ft(7), ft(29)), footprint=(inch(24), inch(24)), room="RM-B-FURNACE", type_ref="EQ-T-WATER-HEATER"),
]

# --- Electrical: symbols-only (decision 1 — panel/circuit schedule deferred) -------
PANEL = [
    ElectricalDevice(uid="CEP901AAAA", tag="ED-B-PANEL", kind=DeviceKind.PANEL,
                     position=pt(ft(2), ft(29)), mount_height=ft(5), type_ref="ED-T-PANEL"),
]

# (room tag, storey, x, y, is_bedroom) — one light + switch per habitable room, one
# code-minimum receptacle per bedroom (bare minimum, not NEC 210.52 spacing).
_HABITABLE_ROOMS = (
    ("RM-M-LIVING", "main", 27, 12, False),
    ("RM-M-BED", "main", 9, 6, True),
    ("RM-M-STUDY", "main", 15.667, 20, False),
    ("RM-S-PLANT", "second", 9, 4, False),
    ("RM-S-STUDY2", "second", 27, 4, False),
    ("RM-S-BED1", "second", 29, 16, True),
    ("RM-S-BED2", "second", 29, 24, True),
    ("RM-S-BED3", "second", 29, 32, True),
    ("RM-S-SUITE", "second", 9, 20, True),
)


def _room_devices():
    main_devices, second_devices = [], []
    for index, (room, storey, x, y, is_bedroom) in enumerate(_HABITABLE_ROOMS, start=1):
        # Uids avoid the letters I/L/O/U (Crockford base32, → model/ids.py) even though
        # non-editable plan files aren't dialect-linted — keeps the scheme consistent.
        uid_light = f"CED{index:03d}K1AA"
        uid_switch = f"CED{index:03d}K2AA"
        light = ElectricalDevice(uid=uid_light, tag=f"ED-{room[3:]}-LT", kind=DeviceKind.LIGHT,
                                 position=pt(ft(x), ft(y)), mount_height=ft(8), type_ref="ED-T-LIGHT")
        switch = ElectricalDevice(uid=uid_switch, tag=f"ED-{room[3:]}-SW", kind=DeviceKind.SWITCH,
                                  position=pt(ft(x - 1), ft(y)), mount_height=inch(48), type_ref="ED-T-SWITCH")
        devices = [light, switch]
        if is_bedroom:
            uid_recep = f"CED{index:03d}K3AA"
            devices.append(ElectricalDevice(
                uid=uid_recep, tag=f"ED-{room[3:]}-RC1", kind=DeviceKind.RECEPTACLE,
                position=pt(ft(x + 1), ft(y)), mount_height=inch(16), type_ref="ED-T-RECEPTACLE",
            ))
        (main_devices if storey == "main" else second_devices).extend(devices)
    return main_devices, second_devices


_MAIN_DEVICES, _SECOND_DEVICES = _room_devices()

MAIN_ELEMENTS = [*SLEEVES, *_MAIN_DEVICES]
BASEMENT_ELEMENTS = [*DRAINS, *EQUIPMENT, *PANEL]
SECOND_ELEMENTS = [*DUCTS, *REGISTERS, *_SECOND_DEVICES]
