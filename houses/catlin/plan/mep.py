# haus: editable
# Catlin MEP: plumbing sleeves/drains (Phase 2) + ERV trunk ducts + electrical (Phase 3).
#
# Authored routing only — the user places runs/ducts/devices; the resolver validates them
# against the framing (joist bays, bearing lines, slab hosts) and the sheets draw them.
# This file is `# haus: editable` so UI moves (e.g. dragging the water heater) round-trip
# back to source; every element below is an explicit constructor, no generators.
#
# Plumbing: sleeve positions are the exact pre-pour centers the concrete crew works from —
# the resolver validates them against the fixture drain point they serve
# (`mep.sleeve_alignment`); nothing here is derived. Second-floor hall-bath drains drop
# through the framed floor into the existing INT_2X6_PLUMBING wet wall (W-S-BD-N) with no
# sleeve needed — only a cast concrete deck needs a pre-positioned penetration.
#
# Ventilation: the second-floor ERV trunks run in the FS-SECOND joist bays (11.875" I-joist, 16" o.c.,
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
    Mount,
    MountKind,
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

# The house has no forced-air heat: heating and cooling are the two minisplits
# (EQ-M-MINI1/2, plan/electrical.py) plus the electric radiant floor zones, so nothing here
# moves *conditioned* air. These two terminals are the ERV's — fresh air to the rooms, stale
# air back to EQ-B-ERV — which is why they are sized for ventilation flow, not a heating CFM.
REGISTER_TYPES = (
    RegisterType(tag="REG-T-SUPPLY", name="ERV fresh-air supply register",
                 footprint=(inch(12), inch(6)), height=inch(1),
                 plan_symbol="register",
                 ports=(ServicePort(tag="supply", service=Service.SUPPLY_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
    RegisterType(tag="REG-T-RETURN", name="ERV stale-air return grille",
                 footprint=(inch(14), inch(8)), height=inch(1),
                 plan_symbol="register",
                 ports=(ServicePort(tag="return", service=Service.RETURN_AIR,
                                    position=(ft(0), ft(0), ft(0))),)),
)

# No gas appliance in the house: the gas furnace that used to stand at (4', 29'-4") is gone
# (all-electric — minisplits + radiant floor), and `plan/site.py` never authored a GAS
# UtilityLine to feed one. The air-side ports that were on it now live on EQ-T-ERV
# (plan/electrical.py), which is the only thing left that pushes air.
EQUIPMENT_TYPES = (
    # The 120V Rheem heat-pump water heater (plans/electrical_notes.md lines 25-26): stays
    # on the backup subsystem, so no gas and no 240V boost — the 240V tank is EQ-B-WH2
    # (plan/electrical.py). Compressor ~500W; the type is electric-only.
    EquipmentType(tag="EQ-T-WATER-HEATER", name="Heat pump water heater, Rheem 120V", footprint=(inch(24), inch(24)), height=ft(5),
                  plan_symbol="water-heater",
                  ports=(ServicePort(tag="cold", service=Service.WATER_COLD, position=(ft(0), ft(0), ft(4))),
                         ServicePort(tag="hot", service=Service.WATER_HOT, position=(ft(0), ft(0), ft(4))),
                         ServicePort(tag="power", service=Service.POWER_120, position=(ft(0), ft(0), ft(0))))),
)

ELECTRICAL_DEVICE_TYPES = (
    ElectricalDeviceType(tag="ED-T-PANEL", name="225A electrical panel (200A service)", footprint=(inch(20), inch(4)), height=ft(3),
                          plan_symbol="panel", spaces=42,
                          ports=(ServicePort(tag="service", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    # ED-T-LIGHT is gone. It was a generic "Ceiling light" with no lamp, no lumens and no
    # listing, standing one per room; every light in the house is now a real product from
    # plan/lighting_types.py carrying a schedule mark, and a fixture a schedule cannot
    # print a row for has no place in a lighting plan.
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
    # Kitchen outlets. ED-T-RECEPTACLE above stays a plain 120V duplex — its port list is
    # pinned by a contract test — so the counter devices name their own types instead.
    ElectricalDeviceType(tag="ED-T-RECEPTACLE-GFCI", name="GFCI receptacle",
                          footprint=(inch(4), inch(2)), height=inch(2),
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-RECEPTACLE-240", name="240V appliance receptacle, NEMA 14-50",
                          footprint=(inch(4), inch(4)), height=inch(4),
                          ports=(ServicePort(tag="power", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    # The kettle outlet the brief asks for: a 5-20R and a 6-20R in one two-gang box, so a
    # 120V and a 240V appliance can share the spot. Two ports, one device.
    ElectricalDeviceType(tag="ED-T-RECEPTACLE-620",
                          name="NEMA 5-20R/6-20R duplex kettle outlet",
                          footprint=(inch(4), inch(4)), height=inch(4),
                          ports=(ServicePort(tag="power-120", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),
                                 ServicePort(tag="power-240", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))))),
)

SLEEVES = [
    # BATH1's WC is wall-hung on an in-wall carrier (FX-TOILET-WH): the bowl bolts to a
    # steel carrier frame inside W-M-BAE's 2x6 stud bay and the 3" waste drops *inside the
    # wall*, so the pre-pour sleeve sits on the wall centerline (x=6') at the fixture's
    # authored drain_position — under the carrier, not under the bowl.
    SleevePenetration(uid="CMP901AAAA", tag="SP-M-WC1", host_ref="SL-M-DECK",
                      position=pt(ft(6), ft(22, 7)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-M-BATH1-WC"),
    SleevePenetration(uid="CMP902AAAA", tag="SP-M-WC2", host_ref="SL-M-DECK",
                      position=pt(ft(3), ft(18)), pipe_diameter=inch(3),
                      sleeve_diameter=inch(4), serves_fixture="FX-M-BATH2-WC"),
    SleevePenetration(uid="CMP907AAAA", tag="SP-M-BATH2-SH", host_ref="SL-M-DECK",
                      position=pt(ft(1, 9), ft(17, 3)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-BATH2-SH"),
    SleevePenetration(uid="CMP908AAAA", tag="SP-M-BATH2-TUB", host_ref="SL-M-DECK",
                      position=pt(ft(7, 4), ft(18, 10.8)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-BATH2-TUB"),
    # Projection of FX-M-BATH1-LAV onto the W-M-BAE structure-layer centerline (x=6, from
    # storeys/main.py node coordinates N-M-BA1/N-M-BA2), at the lavatory's own y.
    SleevePenetration(uid="CMP903AAAA", tag="SP-M-LAV1", host_ref="SL-M-DECK",
                      position=pt(ft(6), m(6.85651)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), serves_fixture="FX-M-BATH1-LAV"),
    # Projection of FX-M-LAUNDRY (10'-6", 20') onto the W-M-BA2E2 centerline (x=8).
    SleevePenetration(uid="CMP904AAAA", tag="SP-M-WASH", host_ref="SL-M-DECK",
                      position=pt(ft(8), ft(20)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-LAUNDRY"),
    # The kitchen sink's waste through the 9" deck. Authored at exactly FX-M-KITCH-SINK's
    # `drain_position`, which is what makes `mep.sleeve_alignment` read 0.00".
    SleevePenetration(uid="BFQH6F04VQ", tag="SP-M-KITCH", host_ref="SL-M-DECK",
                      position=pt(ft(35), ft(32, 8)), pipe_diameter=inch(2),
                      sleeve_diameter=inch(3), serves_fixture="FX-M-KITCH-SINK"),
]

# Slab-on-grade stub-ups. A fixture standing on grade has no wall drain stack — its trap
# arm runs *under* the slab — so the penetration is set before the pour exactly like the
# deck sleeves above. FX-1 (the furnace-room utility sink, plan/placeables.py) authors this
# same point as its `drain_position`, which is what makes the alignment check exact.
SLAB_STUBS = [
    SleevePenetration(uid="CBP901AAAA", tag="SP-B-UTILITY", host_ref="SL-B-FLOOR",
                      position=pt(ft(7), ft(19)), pipe_diameter=inch(1.5),
                      sleeve_diameter=inch(2), serves_fixture="FX-1"),
]

# Basement-ceiling collector: picks up both WC sleeves, heads to the south-wall sewer
# exit. Starts at SP-M-WC1's new carrier-outlet point on the x=4' wall line (the wall-hung
# WC drops its waste inside W-M-BAE, → SLEEVES). Axis-aligned so the authored length is
# exact (4'-7" + 1' + 18' = 23'-7"); inverts give a comfortable 8"/23'-7" ≈ 0.34"/ft
# slope, well above the 1/4"/ft minimum for a 3" line, and SP-M-WC2 still ties in at the
# (3', 18') corner fitting.
DRAINS = [
    PipeRun(uid="CMP905AAAA", tag="PR-B-MAIN-DRAIN", system=PipeSystem.DRAIN,
           path=(pt(ft(6), ft(22, 7)), pt(ft(6), ft(18)), pt(ft(3), ft(18)),
                 pt(ft(3), ft(0))),
           diameter=inch(3), start_elevation=ft(8), end_elevation=ft(7, 4),
           serves=("FX-M-BATH1-WC", "FX-M-BATH2-WC", "FX-M-KITCH-SINK")),
    # Kitchen branch: down SP-M-KITCH, then the long haul across the basement ceiling to the
    # main drain's own corner fitting at (3', 18'). 46'-8" of 2" pipe needs 11 3/4" of fall
    # to hold 1/4"/ft, so it starts tight under the deck at 8'-10" and lands at 7'-10" — a
    # hair above the main's interpolated 7.84' invert there, which is the direction a wye
    # has to be tied. Tying in anywhere further downstream only makes the run longer and
    # the start higher, so this corner is the best point on the line.
    PipeRun(uid="S0Y00EZNNG", tag="PR-B-KITCH-DRAIN", system=PipeSystem.DRAIN,
            path=(pt(ft(35), ft(32, 8)), pt(ft(35), ft(18)), pt(ft(3), ft(18))),
            diameter=inch(2), start_elevation=ft(8, 10), end_elevation=ft(7, 10),
            serves=("FX-M-KITCH-SINK",)),
]

# --- Vent branches: wet wall -> shared chase ----------------------------------------
# None of the water-closet wet walls continues to the storey above (W-M-BAE and W-M-BA2E
# die at the main-floor top plate; W-S-BD-N dies under the cathedral attic), so no vent can
# simply rise inside them. They don't have to: VR-M-RADON-VENT below is already a shared
# radon/plumbing chase running the full height of the house at (1', 34'-6") — moved to the
# NW corner 2026-07-28, inside RM-M-MECH's framed closet and RM-S-BATH1's NW notch (was
# (3', 33'), floating in open mudroom floor space) — and a vent may run horizontally once
# it is above every served fixture's flood-level rim. These are the runs that get it
# there — authored, because the engine never routes pipe on its own, and validated by
# `mep.vent_reachability` (must touch the wet wall, must land on the chase).
#
# Both runs sit inside the floor system over their storey's 9' top plate, drilled through
# the I-joist webs, and fall ~1/8"/ft back toward the fixtures so condensate returns to the
# drainage system rather than pooling in the horizontal leg.
VENT_BRANCHES_MAIN = [
    # Bath2 takeoff on W-M-BA2E (x=8') -> across the hall -> bath1 takeoff on W-M-BAE
    # (x=6') -> north through the storage-room ceiling -> chase. 2" for two water closets.
    PipeRun(uid="CMP906AAAA", tag="PR-M-WC-VENT", system=PipeSystem.VENT,
            path=(pt(ft(8), ft(18)), pt(ft(8), ft(24)), pt(ft(6), ft(24)),
                  pt(ft(6), ft(34, 6)), pt(ft(1), ft(34, 6))),
            diameter=inch(2), start_elevation=ft(9, 3), end_elevation=ft(9, 5.5),
            serves=("FX-M-BATH2-WC", "FX-M-BATH1-WC")),
    # Kitchen sink. W-M-E2 *does* continue to the storey above (W-S-E3/E4/E5 stack on it), so
    # `mep.vent_reachability` is already satisfied by the wet-wall path — this run is the
    # drawn route, not a check-driven workaround. It rises in the E2 stud bay at x=35'-9",
    # turns west in the FS-SECOND joist bay whose centre is y=24'-8" (bays are 8"+n*16"; this
    # one passes south of FO-S-STAIR, which starts at y=25'-2 3/8", and north of both trunk
    # ducts at 20'-8" and 23'-4"), then north to the shared radon/vent chase at (1', 34'-6").
    # It rises 6" over its length so condensate drains back to the fixture.
    PipeRun(uid="ZTQRPPRATP", tag="PR-M-KITCH-VENT", system=PipeSystem.VENT,
            path=(pt(ft(35, 9), ft(32, 8)), pt(ft(35, 9), ft(24, 8)),
                  pt(ft(1), ft(24, 8)), pt(ft(1), ft(34, 6))),
            diameter=inch(1.5), start_elevation=ft(9, 3), end_elevation=ft(9, 9),
            serves=("FX-M-KITCH-SINK",)),
]

VENT_BRANCHES_SECOND = [
    # Hall-bath takeoff on W-S-BD-N (y=26'-4") -> west to the chase line -> north to the
    # chase.
    PipeRun(uid="CSP901AAAA", tag="PR-S-BATH1-VENT", system=PipeSystem.VENT,
            path=(pt(ft(5), ft(26, 4)), pt(ft(1), ft(26, 4)), pt(ft(1), ft(34, 6))),
            diameter=inch(2), start_elevation=ft(9, 3), end_elevation=ft(9, 4),
            serves=("FX-S-BATH1-WC",)),
    # The suite bath's own vent: takeoff on its west wet wall W-S-DC2 (x=9'-7 1/2"), north
    # through the landing and the hall bath, then west along y=34'-6" to the shared
    # radon/plumbing chase. It runs up the x=9'-7 1/2" line rather than joining the hall
    # bath's run at x=1' so the two branches never share a leg.
    #
    # The chase here is VR-M-RADON-VENT's, at (1', 34'-6") — now the *same* shaft as the
    # 2'x2' mechanical chase in the hall bath's NW corner (W-S-CH-W/CH-S, moved there
    # 2026-07-28 from the NE corner specifically so it could carry this riser; storeys/
    # second.py).
    PipeRun(uid="CSP902AAAA", tag="PR-S-SUITEBATH-VENT", system=PipeSystem.VENT,
            path=(pt(ft(9, 7.5), ft(20)), pt(ft(9, 7.5), ft(34, 6)), pt(ft(1), ft(34, 6))),
            diameter=inch(2), start_elevation=ft(9, 3), end_elevation=ft(9, 5),
            serves=("FX-S-SUITEBATH-WC",)),
]

# --- Ventilation: ERV fresh-air / stale-air trunks in the FS-SECOND joist bays -------
# These are ventilation trunks, not heating ducts — EQ-B-ERV (plan/electrical.py) is what
# they connect to, and nothing on the air side carries heat. Sized for the ASHRAE 62.2 whole-
# house rate rather than a furnace CFM: 0.03 x 5,078 ft2 conditioned + 7.5 x (5 bedrooms + 1)
# = ~197 cfm, which at 10"x6" (0.42 ft2) is ~475 fpm — quiet enough to run continuously,
# where the 12"x8"/14"x8" furnace trunks they replace were roughly four times oversized.
#
# The balanced pair is modeled as the ERV's SUPPLY and RETURN trunks; dedicated stale
# pulls (the hall bath's shower takeoff) use DuctSystem.EXHAUST. Distribution now reaches all
# four storeys: trunks ride joist bays where a floor system exists (FS-SECOND under the
# second storey, FS-SECOND over the main storey's ceiling, FS-ATTIC under the attic) and
# drop to CHASE routing in the basement, whose ceiling is the SL-M-DECK concrete.
DUCTS = [
    DuctRun(uid="CMD901AAAA", tag="DU-M-ERV-SUP", system=DuctSystem.SUPPLY,
           path=(pt(ft(4), ft(20, 8)), pt(ft(32), ft(20, 8))), width=inch(10), depth=inch(6),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-SECOND"),
    DuctRun(uid="CMD902AAAA", tag="DU-M-ERV-RET", system=DuctSystem.RETURN,
           path=(pt(ft(4), ft(23, 4)), pt(ft(32), ft(23, 4))), width=inch(10), depth=inch(6),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-SECOND"),
    # Hall bath shower exhaust: a dedicated stale pull in the FS-ATTIC joist bay centred at
    # y=32'-8" (8" + 24*16"), right over FX-S-BATH1-SH at (5', 33'). It crosses the
    # SL-D-SHOWER cut plane (x=5', plan/views.py) inside the shower's reach, which is what
    # makes the detail's `shower_hrv_duct` component draw the takeoff.
    DuctRun(uid="CSDV01AAAA", tag="DU-S-BATH1-EXH", system=DuctSystem.EXHAUST,
           path=(pt(ft(3), ft(32, 8)), pt(ft(17), ft(32, 8))), width=inch(6), depth=inch(4),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-ATTIC"),
]

# Main-storey distribution rides the FS-SECOND joist bays overhead (the main ceiling is
# that floor's underside) in its own pair of bays — 12'-8" (8"+9*16") and 15'-4"
# (8"+11*16") — south of both second-storey trunks and clear of FO-S-STAIR.
DUCTS_MAIN = [
    DuctRun(uid="CMDV01AAAA", tag="DU-M1-ERV-SUP", system=DuctSystem.SUPPLY,
           path=(pt(ft(4), ft(12, 8)), pt(ft(32), ft(12, 8))), width=inch(8), depth=inch(6),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-SECOND"),
    DuctRun(uid="CMDV02AAAA", tag="DU-M1-ERV-RET", system=DuctSystem.RETURN,
           path=(pt(ft(4), ft(15, 4)), pt(ft(32), ft(15, 4))), width=inch(8), depth=inch(6),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-SECOND"),
]

# Basement trunks leave EQ-B-ERV in the furnace room and run exposed-in-chase under the
# SL-M-DECK concrete — no joist bays to ride, so CHASE routing and no floor_ref.
DUCTS_BASEMENT = [
    DuctRun(uid="CBDV01AAAA", tag="DU-B-ERV-SUP", system=DuctSystem.SUPPLY,
           path=(pt(ft(5), ft(29)), pt(ft(5), ft(18)), pt(ft(27), ft(18)), pt(ft(27), ft(9))),
           width=inch(8), depth=inch(6), routing=DuctRouting.CHASE),
    DuctRun(uid="CBDV02AAAA", tag="DU-B-ERV-RET", system=DuctSystem.RETURN,
           path=(pt(ft(5), ft(29)), pt(ft(5), ft(8)), pt(ft(16), ft(8))),
           width=inch(8), depth=inch(6), routing=DuctRouting.CHASE),
]

# Attic distribution rides the FS-ATTIC joist bays: supply at 18'-0" (8"+13*16"), return
# at 4'-8" (8"+3*16"), both clear of FO-A-STAIR (y 5'-9 5/8"..8'-9 5/8", x 21'-2" east).
DUCTS_ATTIC = [
    DuctRun(uid="CADV01AAAA", tag="DU-A-ERV-SUP", system=DuctSystem.SUPPLY,
           path=(pt(ft(4), ft(18)), pt(ft(32), ft(18))), width=inch(8), depth=inch(6),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-ATTIC"),
    DuctRun(uid="CADV02AAAA", tag="DU-A-ERV-RET", system=DuctSystem.RETURN,
           path=(pt(ft(4), ft(4, 8)), pt(ft(32), ft(4, 8))), width=inch(8), depth=inch(6),
           routing=DuctRouting.JOIST_BAY, floor_ref="FS-ATTIC"),
]

# Every register here drops into a boot in the FS-SECOND joist bay, so the grille face lands
# flush with the finished floor and the type's 1" height is the frame below it, not a kerb
# standing on it. Saying so keeps a register out of a neighbour's clear floor space without
# exempting registers as a class — a surface-mounted one would still report.
REGISTERS = [
    Register(uid="CMR901AAAA", tag="REG-S-SUP1", kind=DuctSystem.SUPPLY, room="RM-S-PLANT",
            position=pt(ft(9), ft(4)), duct_ref="DU-M-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CMR902AAAA", tag="REG-S-SUP2", kind=DuctSystem.SUPPLY, room="RM-S-STUDY2",
            position=pt(ft(27), ft(4)), duct_ref="DU-M-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # One per bedroom now that the east bedrooms are equal 9'-0" bays: SUP3 y 9'-18',
    # SUP5 y 18'-27', SUP4 y 27'-36'. RM-S-BED2 had no terminal at all before the
    # re-spacing (plans/TODO.md).
    Register(uid="CMR903AAAA", tag="REG-S-SUP3", kind=DuctSystem.SUPPLY, room="RM-S-BED1",
            position=pt(ft(29), ft(13, 6)), duct_ref="DU-M-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CMR907AAAA", tag="REG-S-SUP5", kind=DuctSystem.SUPPLY, room="RM-S-BED2",
            position=pt(ft(29), ft(22, 6)), duct_ref="DU-M-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CMR904AAAA", tag="REG-S-SUP4", kind=DuctSystem.SUPPLY, room="RM-S-BED3",
            position=pt(ft(29), ft(31, 6)), duct_ref="DU-M-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CMR905AAAA", tag="REG-S-RET1", kind=DuctSystem.RETURN, room="RM-S-HALL",
            position=pt(ft(20), ft(20)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-RETURN",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CMR906AAAA", tag="REG-S-RET2", kind=DuctSystem.RETURN, room="RM-S-SUITE",
            position=pt(ft(9), ft(20)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-RETURN",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
]

# --- Distribution registers, all four storeys (ASHRAE 62.2 coverage) ----------------
# Fresh air to every sleeping/living/office room, stale air out of every wet room, all
# matched to rooms explicitly via room= (mep.ventilation_distribution). RM-S-NCLOSET and
# the other storage rooms get nothing. Second-storey terminals are floor boots off the
# FS-SECOND trunks like the seven above; the hall bath's stale terminal is a ceiling grille
# on the EXHAUST run in the FS-ATTIC bay over the shower.
REGISTERS_SECOND = [
    Register(uid="CSRV01AAAA", tag="REG-S-SUP6", kind=DuctSystem.SUPPLY, room="RM-S-SUITE",
            position=pt(ft(5), ft(18)), duct_ref="DU-M-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CSRV02AAAA", tag="REG-S-SUP7", kind=DuctSystem.SUPPLY, room="RM-S-HALL",
            position=pt(ft(13), ft(23, 6)), duct_ref="DU-M-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CSRV03AAAA", tag="REG-S-RET3", kind=DuctSystem.RETURN, room="RM-S-SUITEBATH",
            position=pt(ft(14), ft(19)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-RETURN",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CSRV04AAAA", tag="REG-S-RET4", kind=DuctSystem.RETURN, room="RM-S-VANITY",
            position=pt(ft(3), ft(24, 4)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-RETURN",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CSRV05AAAA", tag="REG-S-EXH1", kind=DuctSystem.EXHAUST, room="RM-S-BATH1",
            position=pt(ft(5), ft(32, 8)), duct_ref="DU-S-BATH1-EXH", type_ref="REG-T-RETURN",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
]

# Main-storey terminals are ceiling grilles fed from the DUCTS_MAIN bays overhead. The
# kitchen is open plan inside RM-M-LIVING (no Occupancy.KITCHEN), so its stale pickup is
# placed by position — (33', 33'), over the counter run — and still carries the LIVING room=.
REGISTERS_MAIN = [
    Register(uid="CMRV01AAAA", tag="REG-M-SUP1", kind=DuctSystem.SUPPLY, room="RM-M-LIVING",
            position=pt(ft(27), ft(12)), duct_ref="DU-M1-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV02AAAA", tag="REG-M-SUP2", kind=DuctSystem.SUPPLY, room="RM-M-LIVING",
            position=pt(ft(30), ft(26)), duct_ref="DU-M1-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV03AAAA", tag="REG-M-SUP3", kind=DuctSystem.SUPPLY, room="RM-M-BED",
            position=pt(ft(9), ft(6)), duct_ref="DU-M1-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV04AAAA", tag="REG-M-SUP4", kind=DuctSystem.SUPPLY, room="RM-M-STUDY",
            position=pt(ft(15, 8), ft(20)), duct_ref="DU-M1-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV05AAAA", tag="REG-M-RET1", kind=DuctSystem.RETURN, room="RM-M-BATH1",
            position=pt(m(0.354668), m(7.86145)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-RETURN",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV06AAAA", tag="REG-M-RET2", kind=DuctSystem.RETURN, room="RM-M-BATH2",
            position=pt(ft(4), ft(18)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-RETURN",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV07AAAA", tag="REG-M-RET3", kind=DuctSystem.RETURN, room="RM-M-LAUNDRY",
            position=pt(ft(10, 6), ft(20)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-RETURN",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV08AAAA", tag="REG-M-RET5", kind=DuctSystem.RETURN, room="RM-M-LIVING",
            position=pt(ft(33), ft(33)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-RETURN",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # RM-M-MUDROOM gets fresh-air intake only, no stale pickup (plans/TODO.md) — an entry
    # vestibule wants positive pressure against the door, not a return pulling outdoor air
    # straight back out before it mixes. Centred in the hallway strip between the two
    # closets, clear of both, in line with the window/bench.
    Register(uid="CMRV09AAAA", tag="REG-M-SUP5", kind=DuctSystem.SUPPLY, room="RM-M-MUDROOM",
            position=pt(m(1.23013), m(9.56867)), duct_ref="DU-M1-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
]

# Basement terminals hang from the SL-M-DECK underside off the CHASE trunks. The sauna's
# stale pickup sits inside the room low on the trunk side — a sauna needs its exhaust to
# turn the room over after a session.
REGISTERS_BASEMENT = [
    Register(uid="CBRV01AAAA", tag="REG-B-SUP1", kind=DuctSystem.SUPPLY, room="RM-B-GYM",
            position=pt(ft(27), ft(9)), duct_ref="DU-B-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    Register(uid="CBRV02AAAA", tag="REG-B-SUP2", kind=DuctSystem.SUPPLY, room="RM-B-PLAY-N",
            position=pt(ft(27), ft(27)), duct_ref="DU-B-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    Register(uid="CBRV03AAAA", tag="REG-B-RET1", kind=DuctSystem.RETURN, room="RM-B-WORKSHOP",
            position=pt(ft(5), ft(8)), duct_ref="DU-B-ERV-RET", type_ref="REG-T-RETURN",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    Register(uid="CBRV04AAAA", tag="REG-B-RET2", kind=DuctSystem.RETURN, room="RM-B-SAUNA",
            position=pt(ft(16), ft(6)), duct_ref="DU-B-ERV-RET", type_ref="REG-T-RETURN",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(7))),
]

# Attic terminals are floor boots in the FS-ATTIC bays, like the second storey's. The
# stale pickup serves the den side of the floor.
REGISTERS_ATTIC = [
    Register(uid="CARV01AAAA", tag="REG-A-SUP1", kind=DuctSystem.SUPPLY, room="RM-A-WEST",
            position=pt(ft(9), ft(20)), duct_ref="DU-A-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CARV02AAAA", tag="REG-A-SUP2", kind=DuctSystem.SUPPLY, room="RM-A-EAST",
            position=pt(ft(27), ft(20)), duct_ref="DU-A-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CARV03AAAA", tag="REG-A-SUP3", kind=DuctSystem.SUPPLY, room="RM-A-STUDY",
            position=pt(ft(27), ft(4)), duct_ref="DU-A-ERV-SUP", type_ref="REG-T-SUPPLY",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CARV04AAAA", tag="REG-A-RET1", kind=DuctSystem.RETURN, room="RM-A-DEN",
            position=pt(ft(14), ft(4)), duct_ref="DU-A-ERV-RET", type_ref="REG-T-RETURN",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
]

EQUIPMENT = [
    Equipment(uid="CME902AAAA", tag="EQ-B-WH", kind=EquipmentKind.WATER_HEATER,
             position=pt(m(1.88684), m(10.0015)), footprint=(inch(24), inch(24)), room="RM-B-FURNACE", type_ref="EQ-T-WATER-HEATER", circuit="CKT-WH-HP"),
]

# --- Electrical: symbols-only (decision 1 — panel/circuit schedule deferred) -------
PANEL = [
    ElectricalDevice(uid="CEP901AAAA", tag="ED-B-PANEL", kind=DeviceKind.PANEL,
                     position=pt(ft(2), ft(29)), type_ref="ED-T-PANEL",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5))),
]

# One light + switch per habitable room, one code-minimum receptacle per bedroom (bare
# minimum, not NEC 210.52 spacing). Switch sits 1' toward -x of the light, except where the
# room's door is known, in which case the switch sits beside the door on the latch side —
# which is where a switch actually goes. Receptacle 1' toward +x. Uids avoid the letters
# I/L/O/U (Crockford base32, → model/ids.py). These were formerly generated from a
# `_HABITABLE_ROOMS` table; expanded to explicit constructors so the file is
# `# haus: editable` and UI edits round-trip.
#
# `electrical.room_lighting` matches devices to rooms by tag suffix, so a device serving
# RM-<x> must be tagged ED-<x>-*.
#
# Each `-LT` fixture below was one generic ED-T-LIGHT until the lighting plan went in. They
# were re-typed in place rather than deleted and re-added, so every uid — and therefore
# every derived IFC GlobalId — survived. Each now names a real product, states the switch
# that controls it, and is positioned as one corner of the grid the rest of which lives in
# plan/lighting.py. The switches were left where they were.
BASEMENT_DEVICES = [
    # RM-B-GYM (x 18'-36', y 0-18'): switch just inside D-B-PLAY, the door at (24', 18').
    ElectricalDevice(uid="CED010K1AA", tag="ED-B-GYM-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(9)), type_ref="ED-T-LT-FAN52", circuit="CKT-LT-BACKUP",
                     room="RM-B-GYM", controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(1, 6))),
    ElectricalDevice(uid="CED010K2AA", tag="ED-B-GYM-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(25), ft(17)), type_ref="ED-T-SWITCH", circuit="CKT-LT-BACKUP",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

MAIN_DEVICES = [
    ElectricalDevice(uid="CED001K1AA", tag="ED-M-LIVING-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(4)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-MAIN",
                     room="RM-M-LIVING", controlled_by=("ED-M-LIVING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED001K2AA", tag="ED-M-LIVING-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(26), ft(12)), type_ref="ED-T-SWITCH", circuit="CKT-LT-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED002K1AA", tag="ED-M-BED-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(5), ft(4)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-MAIN",
                     room="RM-M-BED", controlled_by=("ED-M-BED-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED002K2AA", tag="ED-M-BED-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(8), ft(6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED002K3AA", tag="ED-M-BED-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(10), ft(6)), type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="CED003K1AA", tag="ED-M-STUDY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(15, 8), ft(19, 6)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-MAIN",
                     room="RM-M-STUDY", controlled_by=("ED-M-STUDY-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED003K2AA", tag="ED-M-STUDY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(14.667), ft(20)), type_ref="ED-T-SWITCH", circuit="CKT-LT-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # --- kitchen outlets (RM-M-LIVING is open plan, so these keep the LIVING suffix) ---
    # Circuits are still deferred (decision 1): these are symbols and mounting heights, not
    # a panel schedule. Counter outlets sit at 42" — 6" of backsplash over the 36" counter,
    # under the 54" wall cabinets. The refrigerator's future battery-backup circuit is not
    # modeled; KRF1 is an ordinary duplex until that circuit is designed.
    ElectricalDevice(uid="N9317V3K8Y", tag="ED-M-LIVING-KGF1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(22, 6), ft(35, 4)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-KITCH-SA1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
    ElectricalDevice(uid="J34E2ZM4GG", tag="ED-M-LIVING-KGF2", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(28, 6), ft(35, 4)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-KITCH-SA1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
    ElectricalDevice(uid="EJYZJRDFG0", tag="ED-M-LIVING-KGF3", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(35, 4), ft(30, 6)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-KITCH-SA2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
    ElectricalDevice(uid="VDGMBY3YW7", tag="ED-M-LIVING-KET1", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(21, 6), ft(35, 4)), type_ref="ED-T-RECEPTACLE-620", circuit="CKT-KETTLE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
    # Behind the range at 6": the whip drops to the floor box, not to a counter height.
    ElectricalDevice(uid="S8DH5FRQQA", tag="ED-M-LIVING-KRG1", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(26, 7), ft(35, 4)), type_ref="ED-T-RECEPTACLE-240", circuit="CKT-RANGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(6))),
    # On the centre bearing wall's east face, behind APPL-M-FRIDGE, at 48" — above the
    # coil deck, so the plug is reachable without pulling the whole cabinet out.
    ElectricalDevice(uid="D9EBW2FJTX", tag="ED-M-LIVING-KRF1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4), ft(31, 5.375)), type_ref="ED-T-RECEPTACLE", circuit="CKT-FRIDGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # Inside the sink base, 18" up: the dishwasher's cord and the disposer share the box.
    ElectricalDevice(uid="WK41TSMA97", tag="ED-M-LIVING-KDW1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(35, 4), ft(32)), type_ref="ED-T-RECEPTACLE", circuit="CKT-DISHWASHER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18))),
]

# Re-snapped to the survey-aligned partitions (storeys/second.py): each light sits in its
# room's new centre, each switch beside that room's door on the room side, and each -RC1 on
# the first of the wall positions `electrical.receptacle_spacing` measures (the rest of the
# 210.52 fill is in plan/electrical.py). None of these carry `room=`, so a device left on a
# stale coordinate is matched to its room by tag suffix and still reports PASS — which is
# exactly how they came to be stranded inside partitions.
SECOND_DEVICES = [
    ElectricalDevice(uid="CED004K1AA", tag="ED-S-PLANT-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(9), ft(6)), type_ref="ED-T-LT-FAN52", circuit="CKT-LT-UPPER",
                     room="RM-S-PLANT", controlled_by=("ED-S-PLANT-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(1, 6))),
    # Beside D-S-PLANT, the door through the centre bearing wall at y=4'-5 1/2".
    ElectricalDevice(uid="CED004K2AA", tag="ED-S-PLANT-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(17, 3), ft(6, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED005K1AA", tag="ED-S-STUDY2-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(24), ft(3)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-STUDY2", controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED005K2AA", tag="ED-S-STUDY2-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(19), ft(8, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED006K1AA", tag="ED-S-BED1-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(11, 6)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-BED1", controlled_by=("ED-S-BED1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED006K2AA", tag="ED-S-BED1-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(22, 6), ft(13, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED006K3AA", tag="ED-S-BED1-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(25.92), ft(17.85)), type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="CED007K1AA", tag="ED-S-BED2-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(20, 6)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-BED2", controlled_by=("ED-S-BED2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED007K2AA", tag="ED-S-BED2-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(22, 6), ft(22, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED007K3AA", tag="ED-S-BED2-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(25.83), ft(26.85)), type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="CED008K1AA", tag="ED-S-BED3-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(29, 6)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-BED3", controlled_by=("ED-S-BED3-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED008K2AA", tag="ED-S-BED3-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(22, 6), ft(30, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED008K3AA", tag="ED-S-BED3-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(22.08), ft(35.51)), type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="CED009K1AA", tag="ED-S-SUITE-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(4), ft(11)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-SUITE", controlled_by=("ED-S-SUITE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # In the suite's east arm, beside D-S-SUITE (the hall door through the bearing wall).
    ElectricalDevice(uid="CED009K2AA", tag="ED-S-SUITE-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(15), ft(13)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED009K3AA", tag="ED-S-SUITE-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(15.25), ft(15.83)), type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    # --- rooms the survey added: suite bath, vanity alcove, landing, north closet -------
    # None is a habitable occupancy, so `electrical.room_lighting` does not require these;
    # they are here because a windowless bath, an interior alcove, the stair arrival and a
    # closet all need a switched light to be usable.
    ElectricalDevice(uid="CED013K1AA", tag="ED-S-SUITEBATH-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(11, 6), ft(18)), type_ref="ED-T-LT-CAN4-WET", circuit="CKT-LT-UPPER",
                     room="RM-S-SUITEBATH", controlled_by=("ED-S-SUITEBATH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED013K2AA", tag="ED-S-SUITEBATH-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(12, 9), ft(16, 8)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED014K1AA", tag="ED-S-VANITY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(3), ft(23, 6)), type_ref="ED-T-LT-CAN4-WET", circuit="CKT-LT-UPPER",
                     room="RM-S-VANITY", controlled_by=("ED-S-VANITY-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED014K2AA", tag="ED-S-VANITY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(5), ft(25, 8)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED015K1AA", tag="ED-S-LANDING-LT", kind=DeviceKind.LIGHT,
                     position=pt(m(2.44371), m(7.41198)), type_ref="ED-T-LT-CAN3", circuit="CKT-LT-UPPER",
                     room="RM-S-HALL", controlled_by=("ED-S-LANDING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # On W-S-SN3's north face beside ED-S-STAIR-SW (plan/lighting.py): W-S-BD-N2, which
    # used to carry this switch, came out with O-S-STAIRTOP on 2026-07-28.
    ElectricalDevice(uid="CED015K2AA", tag="ED-S-LANDING-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(11, 6), ft(22, 7)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED016K1AA", tag="ED-S-NCLOSET-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(20), ft(33)), type_ref="ED-T-LT-CAN3", circuit="CKT-LT-UPPER",
                     room="RM-S-NCLOSET", controlled_by=("ED-S-NCLOSET-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED016K2AA", tag="ED-S-NCLOSET-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(21), ft(30, 4)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

# Attic habitable rooms, both east of the ridge. The cathedral ceiling follows the 4:12 roof
# off a 5' knee wall, so at x=27' the roof plane is 5' + 9'/3 = 8' — the same 8' the rest of
# the house's ceiling boxes sit at, which is why these lights need no special elevation.
ATTIC_DEVICES = [
    # RM-A-EAST (x 18'-36', y 8'-8"-36'): switch inside D-A-HALVES, the door at (18', 32').
    ElectricalDevice(uid="CED011K1AA", tag="ED-A-EAST-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(15)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-A-EAST", controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED011K2AA", tag="ED-A-EAST-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(19), ft(31)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    # RM-A-STUDY (x 18'-36', y 0-8'-8"): switch inside D-A-STUDY, the door at (19', 8'-8").
    ElectricalDevice(uid="CED012K1AA", tag="ED-A-STUDY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(3)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-A-STUDY", controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED012K2AA", tag="ED-A-STUDY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(20), ft(8)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

# --- Radon sump + shared radon/plumbing vent riser ---------------------------------
# A sealed radon sump in the NW basement furnace room, riding RM-M-MECH's framed shaft
# closet up through the NW notch moved into RM-S-BATH1 (2026-07-28 — was at (3',33'),
# floating in open mudroom floor space with no enclosure; storeys/main.py, storeys/
# second.py). Its passive radon vent and the plumbing vent share one mechanical chase up
# to 23'-10" — under the 4:12 rake, which is at 25'-5.7" over the chase's x=1' — turn 90°
# out through the north gable siding, then 90° back up, clamped to the standing seam with
# S-5!-style clamps. The termination is derived (12" above the true roof surface at the
# riser — the deck plane plus CATLIN_ROOF's above-structure skin, resolve/
# vent_termination.py), not authored: an authored absolute cannot follow a rake, which is
# how it drifted to 33', 2' above its own ridge. Elevations are project-frame.
RADON_SUMP = [
    Sump(uid="CMSP01AAAA", tag="SM-B-RADON", position=pt(ft(1), ft(34, 6)),
         diameter=inch(18), depth=inch(24), host_ref="SL-B-FLOOR",
         sealed_cover=True, radon_vent=True, vent_ref="VR-M-RADON-VENT"),
]

VENT_RISERS = [
    VentRun(uid="CMVR01AAAA", tag="VR-M-RADON-VENT",
            systems=(PipeSystem.RADON, PipeSystem.VENT), diameter=inch(3),
            chase_position=pt(ft(1), ft(34, 6)), start_elevation=ft(-8.5),
            exit_elevation=ft(23, 10), exit_offset=pt(ft(0), ft(2, 6)),
            wall_ref="W-A-N2", attachment="standing_seam_clamp"),
]

# S-5! standing-seam clamps fixing the exterior riser to the north gable siding. The riser
# spans 23'-10" to its derived termination, and the gable siding at x=1' stops at the
# 25'-5.7" rake, so all three clamps sit on the pipe *and* on cladding they can actually
# grip. The riser rides W-A-N2, the west half of the north gable wall (x=0..18); W-A-N1
# is the east half.
VENT_CLAMPS = [
    Connector(uid="CMVC01AAAA", tag="CN-M-VENT-CLAMP1", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(1), ft(37)), elevation=ft(24, 4), size="S-5!",
              connects=("VR-M-RADON-VENT", "W-A-N2")),
    Connector(uid="CMVC02AAAA", tag="CN-M-VENT-CLAMP2", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(1), ft(37)), elevation=ft(24, 10), size="S-5!",
              connects=("VR-M-RADON-VENT", "W-A-N2")),
    Connector(uid="CMVC03AAAA", tag="CN-M-VENT-CLAMP3", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(1), ft(37)), elevation=ft(25, 4), size="S-5!",
              connects=("VR-M-RADON-VENT", "W-A-N2")),
]

# --- Outdoor NEMA 3R weatherproof junction box on the north gable siding -------------
# Gasketed blank cover plate; mounted to the standing seam with an S-5!-style clamp. It
# serves the exterior vent riser's work zone, so it belongs beside the CN-M-VENT-CLAMP
# cluster (24'-4" / 24'-10" / 25'-4" at x=1') — not 19' below it at eye level on the main
# storey. Filed on the attic storey with the gable wall it now rides: at x=4' the 4:12
# rake carries the siding to ~26'-5.7", so a box at 25'-6" has cladding to grip. It stands
# 3' east of the riser bundle (2026-07-28: riser moved from x=3' to x=1', box follows to
# stay 3' clear of the pipes and their clamps).
# Both heights below are the same 25'-6": a Mount elevation is storey-relative (attic datum
# 20') while a Connector elevation is project-frame absolute.
NEMA_BOX = [
    ElectricalDevice(uid="CEJ901AAAA", tag="ED-A-NEMA-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(4), ft(37)), type_ref="ED-T-JBOX",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5, 6))),
]
NEMA_CLAMP = [
    Connector(uid="CMNC01AAAA", tag="CN-A-NEMA-CLAMP", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(4), ft(37)), elevation=ft(25, 6), size="S-5!",
              connects=("ED-A-NEMA-JB", "W-A-N2")),
]

# --- Water supply: the house entry out to the garage hydrant ------------------------
#
# The project's first PipeSystem.WATER_COLD run — everything authored before this is DRAIN
# or VENT. It starts at the house's water entry (5', 0'), where site.py's WATER UtilityLine
# terminates, and runs north under the basement slab and then out under grade to the garage,
# surfacing through SP-G-HYDRANT (params/foundations.py) at the hydrant.
#
# Elevations are the burial depth, not a ceiling height: the run leaves the entry at the
# service's own 6' depth and stays there. That is what keeps the hydrant's shutoff — which
# sits at the *end* of this run — at the 72" bury the code wants, well below the 42" frost
# depth the footings are set to. It is deliberately NOT routed up into the garage and back
# down: a supply line that rises above frost anywhere along its length freezes there.
#
# Filed on ``main`` rather than ``basement`` even though it runs under both: PipeRun
# elevations resolve as ``storey datum + authored``, and main's datum is 0'-0" = grade. On
# the basement's -9' datum the same authored -6' would resolve to -15' absolute, and the
# authored number would stop meaning "six feet down".
#
# The interior shutoff is ED/EQ-free by design: it is the hydrant's own valve at the
# buried end plus the isolation valve immediately downstream of the slab penetration, both
# of which mep.hydrant_freeze_depth asserts against this run's geometry.
WATER_SUPPLY = [
    PipeRun(uid="CMP920AAAA", tag="PR-G-HYDRANT-CW", system=PipeSystem.WATER_COLD,
            path=(pt(ft(5), ft(0)), pt(ft(5), ft(38)), pt(ft(1, 6), ft(38)),
                  pt(ft(1, 6), ft(62))),
            diameter=inch(0.75), start_elevation=ft(-6), end_elevation=ft(-6),
            serves=("FX-G-HYDRANT",)),
]

MAIN_ELEMENTS = [*SLEEVES, *VENT_BRANCHES_MAIN, *MAIN_DEVICES, *WATER_SUPPLY,
                 *DUCTS_MAIN, *REGISTERS_MAIN]
BASEMENT_ELEMENTS = [*DRAINS, *SLAB_STUBS, *EQUIPMENT, *PANEL, *BASEMENT_DEVICES,
                     *RADON_SUMP, *VENT_RISERS, *VENT_CLAMPS, *DUCTS_BASEMENT,
                     *REGISTERS_BASEMENT]
SECOND_ELEMENTS = [*DUCTS, *REGISTERS, *REGISTERS_SECOND, *VENT_BRANCHES_SECOND,
                   *SECOND_DEVICES]
ATTIC_ELEMENTS = [*NEMA_BOX, *NEMA_CLAMP, *ATTIC_DEVICES, *DUCTS_ATTIC, *REGISTERS_ATTIC]
