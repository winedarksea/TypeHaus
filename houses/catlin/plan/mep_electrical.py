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
    # Backup subpanel on the EG4's dedicated load output (2026-08-02). 12 spaces for the 7
    # in use — the spare six are room for a second always-on circuit. No ``bus_amps``:
    # nothing backfeeds this bus, and a stated rating would wrongly get graded by the
    # 705.12 check against a service main it doesn't have (see checks/mep/power_sources.py).
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
    # The plant room's outlets (2026-08-18). NEC 2023 makes RM-S-PLANT a damp location
    # throughout and a wet one anywhere it is misted or hosed, which changes three things at
    # once about an ordinary duplex: WR listing (the receptacle body itself), a GFCI device
    # (E3902/210.8 — and at the device, not the breaker, per the circuit convention in
    # plan/circuits.py), and an in-use "bubble" cover rather than a flip lid, because pumps,
    # heat mats and humidifiers stay plugged in permanently and a flip lid is only weather-
    # tight with nothing in it. Non-metallic gasketed box: bare steel and standard EMT rust
    # at 70% RH.
    ElectricalDeviceType(tag="ED-T-RECEPTACLE-WR-GFCI",
                          name="WR GFCI receptacle, in-use cover, non-metallic gasketed box",
                          footprint=(inch(4.5), inch(3)), height=inch(3), nema="5-20R",
                          source="NEC 2023 406.9(B)/210.8 for a damp-to-wet interior location; notes/plant_room.md",
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),)),
    ElectricalDeviceType(tag="ED-T-RECEPTACLE-240", name="240V appliance receptacle, NEMA 14-50",
                          footprint=(inch(4), inch(4)), height=inch(4),
                          ports=(ServicePort(tag="power", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    # Kettle outlet: a 5-20R and a 6-20R in one two-gang box, so a 120V and a 240V
    # appliance can share the spot. The disposer outlet is a *single* 5-20R, not a duplex —
    # it's the disconnect for one cord-and-plug appliance on its own 20A branch
    # (CKT-DISPOSAL); a duplex would invite a second load onto a motor-inrush-sized circuit.
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
                     # x moved 1'-2" -> 0'-10" with the 2026-08-21 12" -> 8" thinning of
                     # W-B-W1/W2: these are face-mounted, and the west wall's inside face
                     # went from x=1'-0" to x=0'-8".
                     position=pt(inch(10), ft(29)), type_ref="ED-T-PANEL",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5)), rotation=deg(90)),
]

# One light + switch per habitable room, one code-minimum receptacle per bedroom (bare
# minimum, not NEC 210.52 spacing). Switch sits 1' toward -x of the light, or beside the
# door on the latch side where the door is known; receptacle 1' toward +x. Uids avoid
# I/L/O/U (Crockford base32, model/ids.py). Explicit constructors (not a generated table)
# so the file stays `# haus: editable` and UI edits round-trip.
#
# `electrical.room_lighting` matches devices to rooms by tag suffix (ED-<x>-* -> RM-<x>).
#
# Each `-LT` fixture was re-typed in place from a generic ED-T-LIGHT when the lighting plan
# went in, preserving uid/IFC GlobalId. Each now names a real product and one corner of the
# grid completed in plan/lighting.py; switches were left where they were.
BASEMENT_DEVICES = [
    # RM-B-GYM (x 18'-36', y 0-18'): switch just inside D-B-PLAY, the door at (24', 18').
    ElectricalDevice(uid="CED010K1AA", tag="ED-B-GYM-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(9)), type_ref="ED-T-LT-FAN52", circuit="CKT-LT-BACKUP",
                     room="RM-B-GYM", controlled_by=("ED-B-GYM-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(1, 6))),
    ElectricalDevice(uid="CED010K2AA", tag="ED-B-GYM-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(23, 6.5), ft(17, 7.615)), type_ref="ED-T-SWITCH", circuit="CKT-LT-BACKUP",
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
    # Circuits still deferred (decision 1): symbols and mounting heights, not a panel
    # schedule. Counter outlets at 42" (6" backsplash over the 36" counter, under 54"
    # cabinets). KRF1 is an ordinary duplex — the fridge's future battery-backup circuit
    # isn't modeled. Positions reflect the 2026-07-30 range/sink/dishwasher wall swaps
    # (KGF3 followed the range north with N3). KGF1 and KGF2 both still fall inside the
    # 2026-08-26 base run's B30 bay (30'-10".."33'-4") after the sink/dishwasher
    # re-composition, so neither moved — KGF1 is no longer "on the dishwasher's spot"
    # (the dishwasher moved to the sink base's west side).
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
    # ** N4's COUNTER HAS HAD NO RECEPTACLE SINCE IT WAS BUILT (found 2026-08-24). ** It is
    # 5'-11" of L-shaped top from KGF2 round the inside corner to the end of the run,
    # against 210.52(C)(1)'s 24". Nothing in the engine checks 210.52(C) — the counter rule
    # reports UNKNOWN by design, because counter casework is not resolved geometry — which
    # is exactly why it went unnoticed through three kitchen passes. y=34'-8" clears
    # WIN-M-KIT-E's north jamb at 34'-7".
    ElectricalDevice(uid="DCP5ZCJVTK", tag="ED-M-LIVING-KGF7", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(35, 4.375), ft(34, 8)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-KITCH-SA2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)), rotation=deg(270)),
    # --- FURN-M-KIT-MIXER-GARAGE's outlets (2026-08-24) ------------------------------
    # ** BOTH OF THESE LIVE INSIDE THE CABINET, AND THAT IS THE POINT. ** The owner asked
    # for the stand mixer to slide straight out onto the peninsula with "outlet in the
    # cabinet". That was first built as three flush ED-T-RECEPTACLE-POPUP units cut into the
    # countertop plus one inside a base bay under a spring lift — a misreading on both
    # counts. The pop-ups (KGF5/KGF6) and their type are deleted with this correction; KGF4
    # keeps its uid, which is a shipped IFC GlobalId, and moves into the garage where the
    # brief actually put it.
    #
    # 42": 6" above the peninsula's 36" top, so a cord reaches an appliance standing on the
    # pull-out shelf and coils clear of it when the shelf travels. x=35'-4 3/8" is the east
    # wall's finish face plus 1" — the garage's back IS that wall, so these are ordinary
    # wall-hosted boxes, not floating in-cabinet ones. y=25'-9" and 26'-8" are inside the
    # garage's y 25'-2 3/8"..27'-2 3/8" after it was bumped south against the tall bank.
    #
    # ** GFCI, and it is not merely belt-and-braces here. ** These sit ~10'-7" from
    # FX-M-KITCH-SINK (2026-08-26: ~11'-0" before the sink moved +9" east), outside
    # E3902.10's 6' reach, and CKT-KITCH-SA1 is a GFCI breaker
    # anyway — but a receptacle serving a countertop appliance a step from a sink is exactly
    # where an inspector will want the device, and a GFCI device costs less than an argument.
    #
    # ** NEC note, and it is a real one. ** 2023 NEC 210.52(C)(2) no longer REQUIRES a
    # receptacle at an island or peninsular countertop, but where none is installed it wants
    # provisions for adding one; 210.52(C)(3) confines any receptacle that does serve the
    # top to on/above/IN the surface. These are ABOVE it, inside a cabinet whose bottom is
    # the counter plane, which satisfies (C)(3) — and they are the peninsula's only
    # countertop-serving outlets now that the pop-ups are gone. A cord from here reaches the
    # east end of the counter and not the west; if the owner wants power at the seating end
    # later, that is a second device on this circuit, not a redesign.
    #
    # ** WIRE THEM BEFORE THE BOX GOES IN. ** Retrofitting behind an installed
    # counter-to-ceiling cabinet is miserable, and that sequencing belongs in the source.
    ElectricalDevice(uid="CEDKGF4AAA", tag="ED-M-LIVING-KGF4", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(35, 4.375), ft(25, 9)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-KITCH-SA2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)), rotation=deg(270)),
    # The mixer's own outlet, on the SMALL-APPLIANCE partner circuit so a 1,000 W machine
    # and whatever else is plugged in up here are not on one 20 A branch.
    ElectricalDevice(uid="NXKCFS9YGV", tag="ED-M-LIVING-KMX1", kind=DeviceKind.RECEPTACLE_GFCI,
                     position=pt(ft(35, 4.375), ft(26, 8)), type_ref="ED-T-RECEPTACLE-GFCI",
                     circuit="CKT-KITCH-SA1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)), rotation=deg(270)),
    # Behind the range at 6": the whip drops to the floor box, not to a counter height. Moved
    # north with APPL-M-RANGE when it swapped with N3; x is still the wall-face constant
    # (35'-4") and y is the range's new along-wall position.
    ElectricalDevice(uid="S8DH5FRQQA", tag="ED-M-LIVING-KRG1", kind=DeviceKind.RECEPTACLE_240,
                     position=pt(ft(35, 3.375), ft(31, 8.375)), type_ref="ED-T-RECEPTACLE-240", circuit="CKT-RANGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(6)), rotation=deg(270)),
    # On the centre bearing wall's east face, behind APPL-M-FRIDGE, at 48" — above the
    # coil deck, so the plug is reachable without pulling the whole cabinet out.
    # y 31'-5 3/8" -> 31'-0 5/8" -> 31'-4 5/8" (both 2026-08-24): south with the pantry
    # room's partition, then back north with the cold run when W-M-PAN-S moved 4"
    # (storeys/main.py). Fridge now y 30'-1 3/4"..32'-10 5/8".
    ElectricalDevice(uid="D9EBW2FJTX", tag="ED-M-LIVING-KRF1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(18, 4.375), ft(31, 4.625)), type_ref="ED-T-RECEPTACLE", circuit="CKT-FRIDGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    # Inside the sink base, 18" up: the dishwasher's cord. Follows APPL-M-DW, which moved
    # to the sink base's west side (2026-08-26) when the base run was re-composed to centre
    # the sink under WIN-M-KITCH — see storeys/main.py's OPENINGS and plan/placeables.py's
    # kitchen header.
    ElectricalDevice(uid="WK41TSMA97", tag="ED-M-LIVING-KDW1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(28, 6), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE", circuit="CKT-DISHWASHER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18))),
    # The disposer outlet, in the sink base, the same 18" up on the same wall face —
    # reachable by the cord from APPL-M-DISP hanging under the bowl at 29'-4" (2026-08-26,
    # moved with the sink). Single 5-20R on CKT-DISPOSAL; the wall control is the 24V loop
    # billed with the appliance, not a switch on this branch.
    ElectricalDevice(uid="N4A3YD3680", tag="ED-M-LIVING-KDS1", kind=DeviceKind.RECEPTACLE,
                     position=pt(ft(29, 9), ft(35, 4.375)), type_ref="ED-T-RECEPTACLE-520S",
                     circuit="CKT-DISPOSAL",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(18))),
]

# Re-snapped to the survey-aligned partitions (storeys/second.py): each light in its room's
# new centre, each switch beside that room's door, each -RC1 on the first wall position
# `electrical.receptacle_spacing` measures (rest of the 210.52 fill is in plan/electrical.py).
# None carry `room=`, so a stale-coordinate device still matches by tag suffix and passes —
# that's how these got stranded inside partitions in the first place.
SECOND_DEVICES = [
    # Retyped to the wet-location fan 2026-08-18: a standard "damp-rated" bath-and-porch
    # fixture is inadequate in a room that condenses on purpose, and this one hangs at the
    # ceiling where the wettest air in the room collects.
    ElectricalDevice(uid="CED004K1AA", tag="ED-S-PLANT-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(9), ft(6)), type_ref="ED-T-LT-FAN52-WET", circuit="CKT-LT-UPPER",
                     room="RM-S-PLANT", controlled_by=("ED-S-PLANT-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(1, 6))),
    # Beside D-S-PLANT, the door through the centre bearing wall at y=4'-5 1/2".
    ElectricalDevice(uid="CED004K2AA", tag="ED-S-PLANT-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(17, 7), ft(6, 6)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
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

# Attic habitable rooms, both east of the ridge. ** THE CATHEDRAL PLANE CHANGED ON 2026-08-29
# AND BOTH CEILING BOXES CAME DOWN WITH IT. ** It used to follow a 4:12 roof off a 5'-0" knee
# wall, so at x=27' the plane was 5' + 9'/3 = 8' — "the same 8' the rest of the house's
# ceiling boxes sit at, which is why these lights need no special elevation". At 6:12 off a
# 1 1/2" rafter plate the underside is `1 1/2" + x/2` mirrored about x=18', which at these
# two fittings' x=22'-0" is 7'-1 1/2". A recessed can sits IN that plane, so that is the
# elevation; the 9'-8" they carried was 2'-6 1/2" of fresh air. The stations do not move —
# x=22'-0" is inside the 13'-9"..22'-3" band where the ceiling clears 7'-0" (see
# plan/lighting_attic.py, which relocated the rest of the storey's fittings).
ATTIC_DEVICES = [
    # RM-A-EAST-UNFIN (x 18'-36', y 8'-8"-36'): switch inside D-A-HALVES, the door at (18', 32').
    ElectricalDevice(uid="CED011K1AA", tag="ED-A-EAST-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(15)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-A-EAST-UNFIN", controlled_by=("ED-A-EAST-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 1.5),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED011K2AA", tag="ED-A-EAST-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(18, 4.375), ft(32, 5.5)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)), rotation=deg(90)),
    # RM-A-STUDY (x 18'-36', y 0-8'-8"): switch inside D-A-STUDY, the door at (19', 8'-8").
    ElectricalDevice(uid="CED012K1AA", tag="ED-A-STUDY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(22), ft(3)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-A-STUDY", controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 1.5),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED012K2AA", tag="ED-A-STUDY-SW", kind=DeviceKind.SWITCH,
                     position=pt(ft(21, 8.375), ft(8, 8.625)), type_ref="ED-T-SWITCH", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48))),
]

# --- Outdoor NEMA 3R weatherproof junction box on the north gable siding -------------
# Gasketed blank cover plate, beside the CN-M-VENT-CLAMP riser cluster (24'-4"/24'-10"/
# 25'-4") it serves — filed on the attic storey because the gable carries siding well above
# it there, giving a 25'-6" box cladding to grip. 3' east of the riser (2026-07-28: riser
# moved x=3'->1', box followed to stay clear).
#
# ** MOVED x 4'-0" -> 16'-4" ON 2026-08-29, AND IT IS STILL 3'-0" EAST OF THE RISER. **
# Both numbers changed for one reason: the riser jogged east inside the attic to x 13'-4"
# (mep_venting.py) and the gable's rake dropped to `20'-11 3/8" + x/2`. At the old x=4'-0"
# the plane now stands at 22'-11 3/8" — three feet BELOW this box — so the enclosure had
# nothing to hang on. At 16'-4" the plane is 29'-1 3/8" and the box hangs with 3'-7" of
# cladding over it, beside the clamps exactly as it was drawn to be. MN 1303.2402 subp. 6
# wants the fan's box within reach of the riser and `code.MN_1303_2402_radon` grades that
# at 8'-0"; 3'-0" holds it.
#
# Both heights below are the same 25'-6": Mount elevation is storey-relative (attic datum
# 20'), Connector elevation is project-frame absolute.
NEMA_BOX = [
    ElectricalDevice(uid="CEJ901AAAA", tag="ED-A-NEMA-JB", kind=DeviceKind.JUNCTION_BOX,
                     position=pt(ft(16, 4), ft(36, 10.25)), type_ref="ED-T-JBOX",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(5, 6))),
]
# ** CN-A-NEMA-CLAMP is GONE (2026-08-26), and this list is empty on purpose. **
# It was a plain S-5! seam clamp: the box's own fastener, sharing ED-A-NEMA-JB's point
# exactly, and it had followed that box out to the cladding face on 2026-08-03 (the box had
# been hanging 4" clear of the siding it is supposed to be clamped to), out 1/2" more on
# 2026-08-23 with the Swinburne truss, and 1" more on 2026-08-26 with the catlin truss.
#
# The gable wall it sits on is `pbr-panel-26` now. **This is WALL and not roof**, which is
# the fact that decides it: at x=4' the rake stands near 26'-6" and the box hangs at 25'-6",
# so it is a foot below the roof line on an exposed-fastener panel with no seam anywhere in
# it. An S-5! clamp has nothing to close on.
#
# Nothing replaces it, and that is the honest answer rather than a gap: a surface enclosure
# on a face-fastened panel is screwed to the wall the way the panel itself is, with the same
# gasketed T09150HWAM through the flat into the girt behind. Those screws are inside the
# field-grid count (``takeoff.fasteners``), which deducts nothing for openings or
# penetrations precisely so that fixings like this one are covered by it.
#
# Restoring the seam cladding means restoring this connector — see git, and see
# CATLIN_EXT_2X6_SWINBURNE in plan/assemblies.py, which is the rest of that revert.
NEMA_CLAMP = []

# --- Downspout securement: through-panel straps on the PBR siding ---------------------
# The two roof leaders (params/roof_trim.py, TR-RF-LEADER-W/E) run ~24' down the north end
# of the west/east faces, steadied — NOT supported — by a two-hole 316 stainless pipe strap
# on a standoff block, screwed through the panel into the girt behind with two of the same
# gasketed T09150HWAM screws the panel itself is hung on (library/hardware.py,
# THROUGH_PANEL_PIPE_STRAP; same hardware as CN-M-VENT-CLAMP1..3).
#
# ** This was an S-5! CanDuit #13 ring on an S-5! seam clamp until 2026-08-26, and it is
# not a downgrade — it is the only thing that can work. ** The CanDuit's entire value is
# non-penetration, and S5_CANDUIT_PIPE_CLAMP declares `requires_role=ROLE_STANDING_SEAM_CLAMP`,
# so every ring ordered brings a seam clamp with it. `pbr-panel-26` has no seam to clamp:
# the ring would arrive with a bracket that has nothing to grip. On a wall already screwed
# through 3,098 times, a non-penetrating fixing also buys nothing it did not already spend.
# It is cheaper by roughly $15-22/point against ~$3, but that is the consequence, not the
# reason.
#
# The ring is still catalogued and still priced, untouched, so reverting the cladding is a
# `size=` change here and nothing more. The strap is sized on pipe OUTER diameter exactly
# the way the ring was: a 4" round leader is 4.0" OD, hence **#13**, and `size` bills it
# through `hardware_by_model`'s family-prefix match. ** THREE per leader at ~6' o.c.
# (5'/11'/17') SINCE 2026-08-29 — it was four, and the fourth is gone with the knee wall. **
# CN-A-LEADER-W4/E4 stood at 23'-0" on W-A-W1/W-A-E2, which were 5'-0" walls carrying the
# eave to 25'-0". The eave is 20'-11 3/8" now (6:12 off a 1 1/2" rafter plate), so there is
# no leader at 23'-0" to strap and no wall behind it either — those two walls are plates.
# Each leader is ~4'-11" shorter and the 17'-0" strap is 3'-11" below its new head, which is
# inside the same ~6' spacing the other three keep. 6' apart is three 24" girt courses, so
# every strap lands on a course and none of them needs its own blocking. Each on the wall
# with cladding at that elevation. Plan position is the leader's own centreline, 8.77" outboard
# of the sheathing datum (trough mid-width, params/roof_trim.py::_TROUGH_MID_IN) — literal
# offsets below, not arithmetic, since the editable-plan dialect forbids binary operators.
_LEADER_X_W = inch(-8.77)
_LEADER_X_E = ft(36, 8.77)
_LEADER_Y = ft(35, 6)

LEADER_CLAMPS = [
    Connector(uid="CMLC01AAAA", tag="CN-A-LEADER-W1", kind=ConnectorKind.PIPE_STRAP,
              position=pt(_LEADER_X_W, _LEADER_Y), elevation=ft(5), size="SS316-STANDOFF-STRAP #13",
              connects=("TR-RF-LEADER-W", "W-M-W1B")),
    Connector(uid="CMLC02AAAA", tag="CN-A-LEADER-W2", kind=ConnectorKind.PIPE_STRAP,
              position=pt(_LEADER_X_W, _LEADER_Y), elevation=ft(11), size="SS316-STANDOFF-STRAP #13",
              connects=("TR-RF-LEADER-W", "W-S-W1B")),
    Connector(uid="CMLC03AAAA", tag="CN-A-LEADER-W3", kind=ConnectorKind.PIPE_STRAP,
              position=pt(_LEADER_X_W, _LEADER_Y), elevation=ft(17), size="SS316-STANDOFF-STRAP #13",
              connects=("TR-RF-LEADER-W", "W-S-W1B")),
    Connector(uid="CMLC05AAAA", tag="CN-A-LEADER-E1", kind=ConnectorKind.PIPE_STRAP,
              position=pt(_LEADER_X_E, _LEADER_Y), elevation=ft(5), size="SS316-STANDOFF-STRAP #13",
              connects=("TR-RF-LEADER-E", "W-M-E1")),
    Connector(uid="CMLC06AAAA", tag="CN-A-LEADER-E2", kind=ConnectorKind.PIPE_STRAP,
              position=pt(_LEADER_X_E, _LEADER_Y), elevation=ft(11), size="SS316-STANDOFF-STRAP #13",
              connects=("TR-RF-LEADER-E", "W-S-E4")),
    Connector(uid="CMLC07AAAA", tag="CN-A-LEADER-E3", kind=ConnectorKind.PIPE_STRAP,
              position=pt(_LEADER_X_E, _LEADER_Y), elevation=ft(17), size="SS316-STANDOFF-STRAP #13",
              connects=("TR-RF-LEADER-E", "W-S-E4")),
]
