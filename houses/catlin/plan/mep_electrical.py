# haus: editable
# Catlin MEP — electrical symbols — the panel, per-storey devices, exterior boxes and clamps.
#
# Split out of the old 2,515-line plan/mep.py (AGENTS.md §1.1). Every element below moved
# verbatim; plan/mep.py still re-exports the storey lists, so the manifest is unchanged.
#
# The symbols-only half (decision 1): the panel/circuit schedule is plan/circuits.py and the
# service upgrade is plan/electrical.py. Devices point at circuits via `circuit=`, which
# `electrical.circuit_refs` reconciles.

from typehaus import (
    Connector,
    ConnectorKind,
    DeviceKind,
    ElectricalDevice,
    ElectricalDeviceType,
    Mount,
    MountKind,
    Service,
    ServicePort,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import m

ELECTRICAL_DEVICE_TYPES = (
    # ``bus_amps=225`` is what `code.NEC_705_12_interconnection` computes the 120% rule
    # against (2026-08-02). It is the busbar rating, deliberately not the 200A service:
    # NEC 705.12(B)(3)(2) sizes the allowable backfeed on the bus, and this panel is a 225A
    # bus on a 200A main precisely so there is 70A of source headroom.
    ElectricalDeviceType(tag="ED-T-PANEL", name="225A electrical panel (200A service)", footprint=(inch(20), inch(4)), height=ft(3),
                          plan_symbol="panel", spaces=54, bus_amps=225,
                          ports=(ServicePort(tag="service", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    # The backup subpanel on the EG4's dedicated load output (2026-08-02). 12 spaces for the
    # 7 the two tiers use — the spare six are the room a second always-on circuit needs, and
    # a 12-space enclosure costs nothing over an 8. No ``bus_amps``: nothing backfeeds this
    # bus today, and stating a rating the 705.12 check would then grade against a service
    # main it does not have would be worse than saying nothing (see the note in
    # checks/mep/power_sources.py about the missing feeder element).
    ElectricalDeviceType(tag="ED-T-BACKUP-PANEL",
                          name="12-space backup subpanel (EG4 load output)",
                          footprint=(inch(14), inch(4)), height=ft(1, 8),
                          plan_symbol="panel", spaces=12,
                          ports=(ServicePort(tag="feed", service=Service.POWER_240,
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
    # The disposer outlet. A *single* 5-20R, not a duplex: the receptacle is the disconnect
    # for one cord-and-plug appliance on its own 20A branch (CKT-DISPOSAL), and a duplex
    # would invite a second load onto a circuit sized for a motor's inrush. 20A because the
    # branch is 20A — a 15A receptacle is only permitted where two or more share the branch.
    ElectricalDeviceType(tag="ED-T-RECEPTACLE-520S",
                          name="NEMA 5-20R single receptacle, 20A",
                          footprint=(inch(4), inch(2)), height=inch(2),
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-RECEPTACLE-620",
                          name="NEMA 5-20R/6-20R duplex kettle outlet",
                          footprint=(inch(4), inch(4)), height=inch(4),
                          ports=(ServicePort(tag="power-120", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),
                                 ServicePort(tag="power-240", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))))),
)

# --- Electrical: symbols-only (decision 1 — panel/circuit schedule deferred) -------
PANEL = [
    ElectricalDevice(uid="CEP901AAAA", tag="ED-B-PANEL", kind=DeviceKind.PANEL,
                     position=pt(ft(1, 2), ft(29)), type_ref="ED-T-PANEL",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5)), rotation=deg(90)),
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
                     position=pt(ft(23, 6.5), ft(17, 5)), type_ref="ED-T-SWITCH", circuit="CKT-LT-BACKUP",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

MAIN_DEVICES = [
    ElectricalDevice(uid="CED001K1AA", tag="ED-M-LIVING-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(4)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-MAIN",
                     room="RM-M-LIVING", controlled_by=("ED-M-LIVING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED001K2AA", tag="ED-M-LIVING-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(18, 4.375), ft(12)), type_ref="ED-T-SWITCH", circuit="CKT-LT-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    ElectricalDevice(uid="CED002K1AA", tag="ED-M-BED-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(5), ft(4)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-MAIN",
                     room="RM-M-BED", controlled_by=("ED-M-BED-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED002K2AA", tag="ED-M-BED-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(12, 6), ft(12, 8.625)), type_ref="ED-T-SWITCH", circuit="CKT-LT-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED002K3AA", tag="ED-M-BED-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(10), ft(0, 7.625)), type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="CED003K1AA", tag="ED-M-STUDY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(15, 8), ft(19, 6)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-MAIN",
                     room="RM-M-STUDY", controlled_by=("ED-M-STUDY-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED003K2AA", tag="ED-M-STUDY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(17, 7.625), ft(21, 5)), type_ref="ED-T-SWITCH", circuit="CKT-LT-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(270)),
    # --- kitchen outlets (RM-M-LIVING is open plan, so these keep the LIVING suffix) ---
    # Circuits are still deferred (decision 1): these are symbols and mounting heights, not
    # a panel schedule. Counter outlets sit at 42" — 6" of backsplash over the 36" counter,
    # under the 54" wall cabinets. The refrigerator's future battery-backup circuit is not
    # modeled; KRF1 is an ordinary duplex until that circuit is designed.
    #
    # Repositioned 2026-07-30 with the range/sink wall swap, then again the same day with the
    # sink/dishwasher flip and the range/N3 flip. KET1 stayed on FURN-M-KIT-E1's open counter;
    # KGF1 moved off the sink (now under it) onto the dishwasher's new spot instead. KGF2
    # stayed put — it was never over an appliance. KGF3 followed the range's cooking zone
    # north with N3.
    ElectricalDevice(uid="VDGMBY3YW7", tag="ED-M-LIVING-KET1", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(25, 6), ft(35, 3.375)), type_ref="ED-T-RECEPTACLE-620", circuit="CKT-KETTLE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
    ElectricalDevice(uid="N9317V3K8Y", tag="ED-M-LIVING-KGF1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(31, 1), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-KITCH-SA1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
    ElectricalDevice(uid="J34E2ZM4GG", tag="ED-M-LIVING-KGF2", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(32), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-KITCH-SA1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42))),
    ElectricalDevice(uid="EJYZJRDFG0", tag="ED-M-LIVING-KGF3", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(35, 4.375), ft(28, 11.375)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-KITCH-SA2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)), rotation=deg(270)),
    # The island receptacle (2026-08-02). FURN-M-KIT-ISLAND (CASE-ISLAND-60, 5'x3',
    # x 25'-0"..30'-0", y 26'-5 3/8"..29'-5 3/8", 36" counter) had none. 2023 NEC
    # 210.52(C)(2) no longer *requires* an island countertop receptacle — but where none
    # serves the countertop it requires provisions for adding one, and 210.52(C)(3) now
    # confines a receptacle that SERVES the countertop to on/above/in the counter surface
    # (the old below-counter side-mount allowance is gone, precisely because of cords
    # draped over an edge people sit at). So this one goes on the island's EAST END face —
    # never the south face, where the seating overhang is and the stools tuck under — at
    # 32", just below the 36" top with no overhang above it on that end, wired as the
    # 210.52(C)(2) provision and a usable point for stand-mixer-class appliances. GFCI at
    # the device per 210.8(A)(6) (all kitchen 125V receptacles), on CKT-KITCH-SA2, the
    # counter-east small-appliance circuit the east end of the kitchen already runs on
    # (20A, dual-function GFCI+AFCI breaker). rotation 90 backs it west into the carcass.
    ElectricalDevice(uid="CEDKGF4AAA", tag="ED-M-LIVING-KGF4", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(30, 1), ft(27, 11.375)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-KITCH-SA2",
                     rotation=deg(90),
                     mount=Mount(kind=MountKind.WALL, elevation=inch(32))),
    # Behind the range at 6": the whip drops to the floor box, not to a counter height. Moved
    # north with APPL-M-RANGE when it swapped with N3; x is still the wall-face constant
    # (35'-4") and y is the range's new along-wall position.
    ElectricalDevice(uid="S8DH5FRQQA", tag="ED-M-LIVING-KRG1", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(35, 3.375), ft(31, 8.375)), type_ref="ED-T-RECEPTACLE-240", circuit="CKT-RANGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(6)), rotation=deg(270)),
    # On the centre bearing wall's east face, behind APPL-M-FRIDGE, at 48" — above the
    # coil deck, so the plug is reachable without pulling the whole cabinet out.
    ElectricalDevice(uid="D9EBW2FJTX", tag="ED-M-LIVING-KRF1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(31, 5.375)), type_ref="ED-T-RECEPTACLE", circuit="CKT-FRIDGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    # Inside the sink base, 18" up: the dishwasher's cord. It used to share this box with
    # the disposer; the disposer moved to its own circuit and its own single receptacle
    # 9" west (2026-08-07), so this one now serves APPL-M-DW alone.
    # Followed APPL-M-DW to its new spot when it flipped with the sink; x is the dishwasher's
    # along-wall position and y is the wall-face constant (35'-4").
    ElectricalDevice(uid="WK41TSMA97", tag="ED-M-LIVING-KDW1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(31, 1), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE", circuit="CKT-DISHWASHER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18))),
    # The disposer outlet, 9" west of KDW1 at the sink base's east end and the same 18" up
    # on the same wall face — a second box in the same cabinet run, reachable by the cord
    # from APPL-M-DISP hanging under the bowl at 28'-7". Single 5-20R on CKT-DISPOSAL; the
    # wall control is the 24V loop billed with the appliance, not a switch on this branch.
    ElectricalDevice(uid="N4A3YD3680", tag="ED-M-LIVING-KDS1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(30, 4), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE-520S",
                     circuit="CKT-DISPOSAL",
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
                     position=pt(ft(17, 7.625), ft(6, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(270)),
    ElectricalDevice(uid="CED005K1AA", tag="ED-S-STUDY2-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(24), ft(3)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-STUDY2", controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED005K2AA", tag="ED-S-STUDY2-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(19), ft(8, 8.625)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED006K1AA", tag="ED-S-BED1-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(11, 6)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-BED1", controlled_by=("ED-S-BED1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED006K2AA", tag="ED-S-BED1-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(22, 2.375), ft(13, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    ElectricalDevice(uid="CED006K3AA", tag="ED-S-BED1-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(25, 11), ft(17, 4.625)), type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="CED007K1AA", tag="ED-S-BED2-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(20, 6)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-BED2", controlled_by=("ED-S-BED2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED007K2AA", tag="ED-S-BED2-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(22, 2.375), ft(22, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    ElectricalDevice(uid="CED007K3AA", tag="ED-S-BED2-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(25, 10), ft(26, 4.625)), type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16))),
    ElectricalDevice(uid="CED008K1AA", tag="ED-S-BED3-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(25), ft(29, 6)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-BED3", controlled_by=("ED-S-BED3-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED008K2AA", tag="ED-S-BED3-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(22, 2.375), ft(30, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    ElectricalDevice(uid="CED008K3AA", tag="ED-S-BED3-RC1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(22, 4.375), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)), rotation=deg(0)),
    ElectricalDevice(uid="CED009K1AA", tag="ED-S-SUITE-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(4), ft(11)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-SUITE", controlled_by=("ED-S-SUITE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # In the suite's east arm, beside D-S-SUITE (the hall door through the bearing wall).
    ElectricalDevice(uid="CED009K2AA", tag="ED-S-SUITE-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(16, 7), ft(12, 8.375)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED009K3AA", tag="ED-S-SUITE-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(15, 3), ft(15, 6.625)), type_ref="ED-T-RECEPTACLE-GFCI", circuit="CKT-RC-SECOND",
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
                     position=pt(ft(12, 9), ft(16, 3.375)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED014K1AA", tag="ED-S-VANITY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(3), ft(23, 6)), type_ref="ED-T-LT-CAN4-WET", circuit="CKT-LT-UPPER",
                     room="RM-S-VANITY", controlled_by=("ED-S-VANITY-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED014K2AA", tag="ED-S-VANITY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(5), ft(25, 11.625)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED015K1AA", tag="ED-S-LANDING-LT", kind=DeviceKind.LIGHT,
                     position=pt(m(2.44371), m(7.41198)), type_ref="ED-T-LT-CAN3", circuit="CKT-LT-UPPER",
                     room="RM-S-HALL", controlled_by=("ED-S-LANDING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # On W-S-SN3's north face beside ED-S-STAIR-SW (plan/lighting.py): W-S-BD-N2, which
    # used to carry this switch, came out with O-S-STAIRTOP on 2026-07-28.
    ElectricalDevice(uid="CED015K2AA", tag="ED-S-LANDING-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(11, 6), ft(22, 7.375)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
    ElectricalDevice(uid="CED016K1AA", tag="ED-S-NCLOSET-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(20), ft(33)), type_ref="ED-T-LT-CAN3", circuit="CKT-LT-UPPER",
                     room="RM-S-NCLOSET", controlled_by=("ED-S-NCLOSET-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED016K2AA", tag="ED-S-NCLOSET-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(21, 5.5), ft(30, 6.625)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
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
                     position=pt(ft(18, 4.375), ft(32, 5.5)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    # RM-A-STUDY (x 18'-36', y 0-8'-8"): switch inside D-A-STUDY, the door at (19', 8'-8").
    ElectricalDevice(uid="CED012K1AA", tag="ED-A-STUDY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(3)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-A-STUDY", controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(9, 8),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED012K2AA", tag="ED-A-STUDY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(21, 8.375), ft(8, 8.625)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
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
                     position=pt(ft(4), ft(36, 8)), type_ref="ED-T-JBOX",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5, 6))),
]
NEMA_CLAMP = [
    # The clamp is the box's own fastener, so it shares the box's point exactly — it followed
    # ED-A-NEMA-JB from y=37'-0" to the cladding face on 2026-08-03 (the box had been hanging
    # 4" clear of the siding it is supposed to be clamped to).
    Connector(uid="CMNC01AAAA", tag="CN-A-NEMA-CLAMP", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(ft(4), ft(36, 8)), elevation=ft(25, 6), size="S-5!",
              connects=("ED-A-NEMA-JB", "W-A-N2")),
]

# --- Downspout securement: S-5! CanDuit clamps on the standing-seam siding ------------
# The two roof leaders (params/roof_trim.py, TR-RF-LEADER-W/E) run ~24' from the gutter
# outlet down the north end of the west and east faces. They are steadied — NOT supported —
# by the same hardware the radon riser uses: an S-5! non-penetrating standing-seam clamp
# with an S-5! CanDuit pipe clamp on its M8 shaft, exactly as CN-M-VENT-CLAMP1..3 above.
# https://3482954.fs1.hubspotusercontent-na1.net/hubfs/3482954/Resources/Product%20Documents/Utility/CanDuit%20Pipe%20Clamp/WEB-Hybrid-Sales-Tech-CanDuit-Pipe-Clamp-Cut-Sheet.pdf
# CanDuit comes in 14 sizes; a 4" round leader (4.0" OD) takes the **#13** ring, whose
# 4.00-4.37" adjustability range is the only one that closes on it. The reference note is
# explicit that these keep the leader against the wall and are not its primary support.
#
# The ring number is the part number: it is what `size` bills through `library/hardware.py`
# (S5_CANDUIT_PIPE_CLAMP), which in turn declares `requires_role`, so the seam clamp each
# ring mounts on is billed with it. Authoring a bare "S-5!" here would order the brackets
# and none of the rings.
#
# Four per leader at roughly 6' o.c. (5' / 11' / 17' / 23'), each on the wall that actually
# has cladding at that elevation: main to 10', second to 20', the attic knee wall above. In
# plan they sit on the leader's own centre line — 8.77" outboard of the sheathing datum,
# which is the trough's mid-width (params/roof_trim.py::_TROUGH_MID_IN) and also just about
# where a strapped 4" round leader's centre lands off 5.02" of wall stack.
# (Literal offsets, not arithmetic: the editable-plan dialect forbids binary operators.)
_LEADER_X_W = inch(-8.77)
_LEADER_X_E = ft(36, 8.77)
_LEADER_Y = ft(35, 6)

LEADER_CLAMPS = [
    Connector(uid="CMLC01AAAA", tag="CN-A-LEADER-W1", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_W, _LEADER_Y), elevation=ft(5), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-W", "W-M-W1B")),
    Connector(uid="CMLC02AAAA", tag="CN-A-LEADER-W2", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_W, _LEADER_Y), elevation=ft(11), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-W", "W-S-W1B")),
    Connector(uid="CMLC03AAAA", tag="CN-A-LEADER-W3", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_W, _LEADER_Y), elevation=ft(17), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-W", "W-S-W1B")),
    Connector(uid="CMLC04AAAA", tag="CN-A-LEADER-W4", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_W, _LEADER_Y), elevation=ft(23), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-W", "W-A-W1")),
    Connector(uid="CMLC05AAAA", tag="CN-A-LEADER-E1", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_E, _LEADER_Y), elevation=ft(5), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-E", "W-M-E2")),
    Connector(uid="CMLC06AAAA", tag="CN-A-LEADER-E2", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_E, _LEADER_Y), elevation=ft(11), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-E", "W-S-E4")),
    Connector(uid="CMLC07AAAA", tag="CN-A-LEADER-E3", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_E, _LEADER_Y), elevation=ft(17), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-E", "W-S-E4")),
    Connector(uid="CMLC08AAAA", tag="CN-A-LEADER-E4", kind=ConnectorKind.STANDING_SEAM_CLAMP,
              position=pt(_LEADER_X_E, _LEADER_Y), elevation=ft(23), size="S-5! CanDuit #13",
              connects=("TR-RF-LEADER-E", "W-A-E2")),
]
