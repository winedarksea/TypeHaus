# haus: editable
# Catlin MEP: plumbing sleeves/drains (Phase 2) + HVAC trunk ducts + electrical (Phase 3).
#
# Authored routing only — the user places runs/ducts/devices; the resolver validates them
# against the framing (joist bays, bearing lines, slab hosts) and the sheets draw them.
# This file is `# haus: editable` so UI moves (e.g. dragging the water heater) round-trip
# back to source; every element below is an explicit constructor, no generators.
#
# Plumbing: sleeve positions are the exact pre-pour centers the concrete crew works from —
# the resolver validates them against the fixture drain point they serve
# (`mep.sleeve_alignment`); nothing here is derived. Second-floor ensuite drains drop
# through the framed floor into the existing INT_2X6_PLUMBING wet wall (W-S-BD-N) with no
# sleeve needed — only a cast concrete deck needs a pre-positioned penetration.
#
# HVAC: the second-floor trunks run in the FS-SECOND joist bays (11.875" I-joist, 16" o.c.,
# direction "x"). Bay centers are `8" + n*16"` from the joist-line math in
# resolve/floors.py; bay 15 (y=20'-8") and bay 17 (y=23'-4") are both clear of the stair
# FloorOpening (x:11'-18', y:25'-36') and both cross the central bearing wall at x=18'.

from typehaus import (
    Connector,
    ConnectorKind,
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
    Sump,
    VentRun,
    ft,
    inch,
    pt,
)
from typehaus.model import m

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
    # NEMA 3R weatherproof exterior junction box with a gasketed blank cover plate.
    ElectricalDeviceType(tag="ED-T-JBOX", name="NEMA 3R weatherproof junction box",
                          footprint=(inch(6), inch(6)), height=inch(4),
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
             position=pt(m(1.81187), m(10.0473)), footprint=(inch(24), inch(24)), room="RM-B-FURNACE", type_ref="EQ-T-WATER-HEATER"),
]

# --- Electrical: symbols-only (decision 1 — panel/circuit schedule deferred) -------
PANEL = [
    ElectricalDevice(uid="CEP901AAAA", tag="ED-B-PANEL", kind=DeviceKind.PANEL,
                     position=pt(ft(2), ft(29)), mount_height=ft(5), type_ref="ED-T-PANEL"),
]

# One light + switch per habitable room, one code-minimum receptacle per bedroom (bare
# minimum, not NEC 210.52 spacing). Switch sits 1' toward -x of the light; receptacle 1'
# toward +x. Uids avoid the letters I/L/O/U (Crockford base32, → model/ids.py). These were
# formerly generated from a `_HABITABLE_ROOMS` table; expanded to explicit constructors so
# the file is `# haus: editable` and UI edits round-trip.
MAIN_DEVICES = [
    ElectricalDevice(uid="CED001K1AA", tag="ED-M-LIVING-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(12)), mount_height=ft(8), type_ref="ED-T-LIGHT"),
    ElectricalDevice(uid="CED001K2AA", tag="ED-M-LIVING-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(26), ft(12)), mount_height=inch(48), type_ref="ED-T-SWITCH"),
    ElectricalDevice(uid="CED002K1AA", tag="ED-M-BED-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(9), ft(6)), mount_height=ft(8), type_ref="ED-T-LIGHT"),
    ElectricalDevice(uid="CED002K2AA", tag="ED-M-BED-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(8), ft(6)), mount_height=inch(48), type_ref="ED-T-SWITCH"),
    ElectricalDevice(uid="CED002K3AA", tag="ED-M-BED-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(10), ft(6)), mount_height=inch(16), type_ref="ED-T-RECEPTACLE"),
    ElectricalDevice(uid="CED003K1AA", tag="ED-M-STUDY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(15.667), ft(20)), mount_height=ft(8), type_ref="ED-T-LIGHT"),
    ElectricalDevice(uid="CED003K2AA", tag="ED-M-STUDY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(14.667), ft(20)), mount_height=inch(48), type_ref="ED-T-SWITCH"),
]

SECOND_DEVICES = [
    ElectricalDevice(uid="CED004K1AA", tag="ED-S-PLANT-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(9), ft(4)), mount_height=ft(8), type_ref="ED-T-LIGHT"),
    ElectricalDevice(uid="CED004K2AA", tag="ED-S-PLANT-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(8), ft(4)), mount_height=inch(48), type_ref="ED-T-SWITCH"),
    ElectricalDevice(uid="CED005K1AA", tag="ED-S-STUDY2-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(4)), mount_height=ft(8), type_ref="ED-T-LIGHT"),
    ElectricalDevice(uid="CED005K2AA", tag="ED-S-STUDY2-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(26), ft(4)), mount_height=inch(48), type_ref="ED-T-SWITCH"),
    ElectricalDevice(uid="CED006K1AA", tag="ED-S-BED1-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(29), ft(16)), mount_height=ft(8), type_ref="ED-T-LIGHT"),
    ElectricalDevice(uid="CED006K2AA", tag="ED-S-BED1-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(28), ft(16)), mount_height=inch(48), type_ref="ED-T-SWITCH"),
    ElectricalDevice(uid="CED006K3AA", tag="ED-S-BED1-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(30), ft(16)), mount_height=inch(16), type_ref="ED-T-RECEPTACLE"),
    ElectricalDevice(uid="CED007K1AA", tag="ED-S-BED2-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(29), ft(24)), mount_height=ft(8), type_ref="ED-T-LIGHT"),
    ElectricalDevice(uid="CED007K2AA", tag="ED-S-BED2-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(28), ft(24)), mount_height=inch(48), type_ref="ED-T-SWITCH"),
    ElectricalDevice(uid="CED007K3AA", tag="ED-S-BED2-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(30), ft(24)), mount_height=inch(16), type_ref="ED-T-RECEPTACLE"),
    ElectricalDevice(uid="CED008K1AA", tag="ED-S-BED3-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(29), ft(32)), mount_height=ft(8), type_ref="ED-T-LIGHT"),
    ElectricalDevice(uid="CED008K2AA", tag="ED-S-BED3-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(28), ft(32)), mount_height=inch(48), type_ref="ED-T-SWITCH"),
    ElectricalDevice(uid="CED008K3AA", tag="ED-S-BED3-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(30), ft(32)), mount_height=inch(16), type_ref="ED-T-RECEPTACLE"),
    ElectricalDevice(uid="CED009K1AA", tag="ED-S-SUITE-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(9), ft(20)), mount_height=ft(8), type_ref="ED-T-LIGHT"),
    ElectricalDevice(uid="CED009K2AA", tag="ED-S-SUITE-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(8), ft(20)), mount_height=inch(48), type_ref="ED-T-SWITCH"),
    ElectricalDevice(uid="CED009K3AA", tag="ED-S-SUITE-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(10), ft(20)), mount_height=inch(16), type_ref="ED-T-RECEPTACLE"),
]

# --- Radon sump + shared radon/plumbing vent riser ---------------------------------
# A sealed radon sump in the NW basement furnace room. Its passive radon vent and the
# plumbing vent share one mechanical chase up to near the attic ceiling (29'), turn 90°
# out through the north gable siding, then 90° back up — clamped to the standing seam with
# S-5!-style clamps — terminating 12" above the roof (33'). Elevations are project-frame.
RADON_SUMP = [
    Sump(uid="CMSP01AAAA", tag="SM-B-RADON", position=pt(ft(3), ft(33)),
         diameter=inch(18), depth=inch(24), host_ref="SL-B-FLOOR",
         sealed_cover=True, radon_vent=True, vent_ref="VR-M-RADON-VENT"),
]

VENT_RISERS = [
    VentRun(uid="CMVR01AAAA", tag="VR-M-RADON-VENT",
            systems=(PipeSystem.RADON, PipeSystem.VENT), diameter=inch(3),
            chase_position=pt(ft(3), ft(33)), start_elevation=ft(-8.5),
            exit_elevation=ft(29), exit_offset=pt(ft(0), ft(4)),
            roof_termination_elevation=ft(33), wall_ref="W-A-N1",
            attachment="standing_seam_clamp"),
]

# S-5! standing-seam clamps fixing the exterior riser to the north gable siding.
VENT_CLAMPS = [
    Connector(uid="CMVC01AAAA", tag="CN-M-VENT-CLAMP1", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(3), ft(37)), elevation=ft(30), size="S-5!",
              connects=("VR-M-RADON-VENT", "W-A-N1")),
    Connector(uid="CMVC02AAAA", tag="CN-M-VENT-CLAMP2", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(3), ft(37)), elevation=ft(31, 6), size="S-5!",
              connects=("VR-M-RADON-VENT", "W-A-N1")),
    Connector(uid="CMVC03AAAA", tag="CN-M-VENT-CLAMP3", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(3), ft(37)), elevation=ft(33), size="S-5!",
              connects=("VR-M-RADON-VENT", "W-A-N1")),
]

# --- Outdoor NEMA 3R weatherproof junction box on the north siding ------------------
# Gasketed blank cover plate; mounted to the standing seam with an S-5!-style clamp.
NEMA_BOX = [
    ElectricalDevice(uid="CEJ901AAAA", tag="ED-M-NEMA-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(6), ft(37)), mount_height=ft(6), type_ref="ED-T-JBOX"),
]
NEMA_CLAMP = [
    Connector(uid="CMNC01AAAA", tag="CN-M-NEMA-CLAMP", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(6), ft(37)), elevation=ft(6), size="S-5!",
              connects=("ED-M-NEMA-JB", "W-M-N")),
]

MAIN_ELEMENTS = [*SLEEVES, *MAIN_DEVICES, *NEMA_BOX, *NEMA_CLAMP]
BASEMENT_ELEMENTS = [*DRAINS, *EQUIPMENT, *PANEL, *RADON_SUMP, *VENT_RISERS, *VENT_CLAMPS]
SECOND_ELEMENTS = [*DUCTS, *REGISTERS, *SECOND_DEVICES]
