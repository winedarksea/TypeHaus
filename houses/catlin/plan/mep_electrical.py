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
from typehaus.model import Location, ModelRepresentation, WallAttachment, m

ELECTRICAL_DEVICE_TYPES = (
    # RC16's narrow pier takes a standard single-gang plate. Keep its selected product
    # reference here; the shared catalog now uses the same vertical plate envelope.
    ElectricalDeviceType(tag="ED-T-RECEPTACLE-SINGLE-GANG",
                          name="Duplex receptacle, standard 2 3/4 x 4 1/2 in. plate",
                          footprint=(inch(2.75), inch(2)), height=inch(4.5),
                          product_ref="PROD-LEVITON-E5825-W",
                          nema="5-20R",  # E5825-W: Lever Edge duplex, 20 A
                          model_representation=ModelRepresentation(symbol="receptacle-duplex"),
                          source="Standard single-gang wallplate envelope: https://leviton.com/content/dam/leviton/commercial-industrial/product_documents/solution_sheets/Wallplate%20Size%20Guide%20-%20Q-1289.pdf . Ordinary duplex on CKT-RC-MAIN, no special counter hardware.",
                          ports=(ServicePort(tag="power", service=Service.POWER_120,
                                             position=(ft(0), ft(0), ft(0))),)),
    # Backup subpanel on the EG4's dedicated load output: Square D QO112L125PG (2026-11-14),
    # the QO family of ED-B-PANEL, so CKT-SPD-BACKUP takes the same QO2175SB. Main lugs: a
    # main breaker waits on EG4's load-port answer (notes/backup_power.md Q5; QO112M100P is
    # the 22 kA main-breaker sibling). No ``bus_amps``: nothing backfeeds this bus, and a
    # stated rating would be graded by 705.12 against a main it doesn't have.
    ElectricalDeviceType(tag="ED-T-BACKUP-PANEL",
                          name="Square D QO112L125PG, 125A main lugs, 12 spaces (EG4 load output)",
                          # Depth 4 in: the sheet's 3.7 in box plus its surface cover (not
                          # dimensioned on the sheet); the box alone sits behind PANEL-2's front.
                          footprint=(inch(14.3), inch(4)), height=inch(17.9),
                          plan_symbol="panel", spaces=12, sccr_a=65000,
                          product_ref="PROD-SQUARED-QO112L125PG",
                          source="Schneider Electric product data sheet QO112L125PG (se.com, read 2026-11-14): 12 spaces / 24 circuits, 125 A main lugs, Max Short Circuit Current Rating 65 kA, NEMA 1, 17.9 x 14.3 x 3.7 in; cover ordered separately. https://www.se.com/us/en/product/QO112L125PG/",
                          ports=(ServicePort(tag="feed", service=Service.POWER_240,
                                             position=(ft(0), ft(0), ft(0))),)),
    # Every light in the house is a real product from plan/lighting_types.py carrying a
    # schedule mark — a generic fixture with no lamp, no lumens and no listing has no place
    # in a lighting plan; a schedule cannot print a row for it.
    # NEMA 3R weatherproof exterior junction box with a gasketed blank cover plate.
    # Kitchen outlets. ED-T-RECEPTACLE above stays a plain 120V duplex — its port list is
    # pinned by a contract test — so the counter devices name their own types instead.
    # The plant room's outlets. The NEC makes RM-S-PLANT a damp location
    # throughout and a wet one anywhere it is misted or hosed, which changes three things at
    # once about an ordinary duplex: WR listing (the receptacle body itself), a GFCI device
    # (210.8(A) — and at the device, not the breaker, per the circuit convention in
    # plan/circuits.py), and an in-use "bubble" cover rather than a flip lid, because pumps,
    # heat mats and humidifiers stay plugged in permanently and a flip lid is only weather-
    # tight with nothing in it. Non-metallic gasketed box: bare steel and standard EMT rust
    # at 70% RH.
    # Kettle outlet: a 5-20R and a 6-20R in one combination device, so a 120V and a 240V
    # appliance can share the spot. Its neutral and product listing remain to be verified
    # (notes/workshop_receptacles.md). The disposer outlet is a *single* 5-20R, not a duplex —
    # it's the disconnect for one cord-and-plug appliance on its own 20A branch
    # (CKT-DISPOSAL); a duplex would invite a second load onto a motor-inrush-sized circuit.
)



# --- Electrical: symbols-only (decision 1 — panel/circuit schedule deferred) -------
# ** ALL FOUR PANEL TOPS ON ONE LINE, 6'-6" AFF (2026-10-31). ** NEC 240.24(A)/404.10(A)(2) cap
# the top handle at 6'-7"; `electrical.panel_handle_height` grades the body top. Bottoms:
# ED-B-PANEL 38.63" (QO154M200P, 39.37" can), PANEL-2 48.16" (HOM2040M200PC, 29.84" can),
# BACKUP-PANEL 60.1" (QO112L125PG, 17.9" can), -ENCL 58" (plan/electrical.py). Both panels are 14.25" wide (Square D sheets).
# Each panel's 110.26(A) working space is a ClearZone in plan/panel_working_space.py.
PANEL = [
    ElectricalDevice(uid="CEP901AAAA", tag="ED-B-PANEL", kind=DeviceKind.PANEL,
                     # x=0'-10": face-mounted on W-B-W1/W2, whose inside face is x=0'-8".
                     type_ref="ED-T-PANEL",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(38.63)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-W1", face="left", distance_from_start=inch(84),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Feeder 2's panel, on the same W-B-W1/W2 face, SOUTH of ED-B-BACKUP-PANEL. The bays
    # north of ED-B-PANEL are full and nothing grades a device-on-device overlap: the wall
    # runs ED-B-BACKUP-PANEL 26'-5"..27'-7", ED-B-UTIL-RC1 27'-10"..28'-2", ED-B-PANEL
    # 28'-2"..29'-10", ED-B-NET-PATCH 30'-4 1/2"..31'-7 1/2", the ERV duct crossing at
    # 31'-4" and ED-B-BACKUP-ENCL 31'-10"..33'-2" — the one gap between them is 6 1/2" wide.
    # 25'-0" centres this 14.25" enclosure at 24'-4 7/8"..25'-7 1/8", 9 7/8" clear of the backup panel,
    # with the whole 23'..26' band empty. NEC 110.26 working space (36" deep, 30" wide) runs
    # east into open basement floor (CZ-B-WS-PANEL-2 grades it); device overlap is held
    # by the measurements above.
    ElectricalDevice(uid="F7T26XHBCR", tag="ED-B-PANEL-2", kind=DeviceKind.PANEL,
                     type_ref="ED-T-PANEL-2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48.16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-W1", face="left", distance_from_start=inch(132),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
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
# grid completed in a plan/lighting_<zone>.py file; switches were left where they were.
BASEMENT_DEVICES = [
    # RM-B-GYM (x 18'-36', y 0-18'): switch just inside D-B-PLAY, the door at (24', 18').
    #
    # ** RETYPED N -> N3 (FLUSH) AND drop 18" -> 11", 2026-09-06, uid PRESERVED. ** An 18"
    # fan left the blades near 6'-5" in a room people exercise in. Restated 2026-10-30 over
    # the 3/4" stall mats: the fan hangs under the gym's one flat gypsum ceiling, 96 3/16"
    # above the mats.
    # The Gallegos is modelled at 10 9/16" overall, so its body bottoms at 7'-1 5/8"; Hunter's
    # sheet puts the blade bottom 7.97" below the ceiling flush-mounted, ~7'-4 1/4" AFF.
    # ** NOTHING GRADES THIS: ** there is no blade-to-floor check in the engine, so this
    # comment and the height on ED-T-LT-FAN52-FLUSH are the only guard.
    # ** OFF THE BACKUP TIER SINCE 2026-10-28: ** the product upgrade of the day (14.5 W cans,
    # 60 W panels, both since replaced) took CKT-LT-BACKUP 0.18 kWh short of `cycle_48h.sustains_always_on`. A lightless fan is
    # the least essential load on the always-on lighting tier, so it moved off it, and since
    # 2026-10-31 it is on CKT-LT-BSMT, the basement's non-backup lighting circuit. It is an AC
    # fan (Hunter's sheet; not DC) with no lamp, on constant hot with its included wall
    # control, so ED-B-GYM-SW (the cans') does not switch it.
    ElectricalDevice(uid="CED010K1AA", tag="ED-B-GYM-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(27), ft(9)), type_ref="ED-T-LT-FAN52-FLUSH", circuit="CKT-LT-BSMT",
                     room="RM-B-GYM",
                     mount=Mount(kind=MountKind.CEILING, drop=inch(10.5625))),
    # A D315S relay (2026-11-03), as is -SW2: HA runs the gym's workout routines.
    ElectricalDevice(uid="CED010K2AA", tag="ED-B-GYM-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER", circuit="CKT-LT-BSMT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-CE", face="right", distance_from_start=inch(66.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]

MAIN_DEVICES = [
    ElectricalDevice(uid="CED001K1AA", tag="ED-M-LIVING-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(27, 4), ft(7, 4)), type_ref="ED-T-LT-CAN4-PREM", circuit="CKT-LT-MAIN",
                     room="RM-M-LIVING", controlled_by=("ED-M-LIVING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # Group B, the lounge downlights (LT, CAN5, CAN6), one gang of the 4-gang station whose
    # other three are in plan/lighting_living.py.
    ElectricalDevice(uid="CED001K2AA", tag="ED-M-LIVING-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-MATTER", circuit="CKT-LT-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C1", face="right", distance_from_start=inch(142.125),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="CED002K1AA", tag="ED-M-BED-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(4), ft(3, 4)), type_ref="ED-T-LT-CAN4-PREM", circuit="CKT-LT-MAIN",
                     room="RM-M-BED", controlled_by=("ED-M-BED-SW", "ED-M-BED-SW2"),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # The closet door's switch, and it follows D-M-BED. The door moved 16" east on
    # 2026-09-15 (storeys/main.py) and this box, 4" west of the OLD jamb at 12'-10", would
    # have been left orphaned mid-wall in the new bedside-table zone. 13'-8" keeps the same
    # 4" of clear wall to the strike side of the new RO at 14'-2". After the 2026-10-03 bed
    # move, this switch sits 2 1/8" east of the bed's east face in the 8 1/8" strip before
    # the RO; at 48" AFF it clears the furniture. Half the 3-way with ED-M-BED-SW2 at
    # D-M-BED2 (plan/lighting_main.py), both on CKT-LT-MAIN: a switch on another circuit than
    # its load FAILs electrical.lighting_controls (NEC 210.7). A plain 3-way since 2026-10-31;
    # ED-M-BED-SCONCE-E's body ends 1/2" west of this box.
    ElectricalDevice(uid="CED002K2AA", tag="ED-M-BED-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3", circuit="CKT-LT-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-BDN2", face="right", distance_from_start=inch(66),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="CED002K3AA", tag="ED-M-BED-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-20", circuit="CKT-RC-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-S1", face="left", distance_from_start=inch(120),
                         normal_gap=inch(0), rotation_offset=deg(180)))),
    ElectricalDevice(uid="CED003K1AA", tag="ED-M-STUDY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(14, 11.5), ft(19, 4)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-MAIN",
                     room="RM-M-STUDY-CLOSET", controlled_by=("ED-M-STUDY-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED003K2AA", tag="ED-M-STUDY-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-MAIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C3", face="left", distance_from_start=inch(45.375),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # --- kitchen outlets (RM-M-LIVING is open plan, so these keep the LIVING suffix) ---
    # Counter outlets at 42" (6" backsplash over the 36" counter, under 54" cabinets);
    # `electrical.receptacle_spacing` grades them against the resolved countertops (NEC
    # 210.52(C): <= 24" of wall line from one, 20" above the top, none within 24" below).
    # KRF1 is a recessed DVFR1W on its own always-on CKT-FRIDGE (the freezer is on CKT-FREEZER). KGF1 and KGF2 both fall over FURN-M-KIT-E2 (a B15
    # since 2026-10-02) and its filler, 30'-10".."32'-3 3/8".
    ElectricalDevice(uid="VDGMBY3YW7", tag="ED-M-LIVING-KET1", kind=DeviceKind.RECEPTACLE_240,
                     type_ref="ED-T-LEV-620-FLUSH", circuit="CKT-KETTLE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N1", face="left", distance_from_start=inch(119),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="N9317V3K8Y", tag="ED-M-LIVING-KGF1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-20", circuit="CKT-KITCH-SA1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N1", face="left", distance_from_start=inch(59),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="J34E2ZM4GG", tag="ED-M-LIVING-KGF2", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-20", circuit="CKT-KITCH-SA1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N1", face="left", distance_from_start=inch(46.125),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="EJYZJRDFG0", tag="ED-M-LIVING-KGF3", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-20", circuit="CKT-KITCH-SA2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-E1", face="left", distance_from_start=inch(349.25),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # The NE carousel's east leg (y 32'-3 3/8"..35'-5 3/8"); KGF2 serves its north leg.
    # KGF3 at 29'-1 1/4" serves the 14" landing between the hung upper and the range,
    # its box on the south side of the 29'-4" stud.
    # y=35'-0" clears WIN-M-KIT-E's north jamb at 34'-7".
    ElectricalDevice(uid="DCP5ZCJVTK", tag="ED-M-LIVING-KGF7", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-20",
                     circuit="CKT-KITCH-SA2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-E1", face="left", distance_from_start=inch(420),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # The last stretch of the NE carousel's east leg, between the hood's north end (y 387 1/8")
    # and WIN-M-KIT-E's RO (y 401"): KGF7 at y=35'-0" is 32 5/8" from the range-side end of
    # the stone, past 210.52(C)(1)'s 24". 393 1/2" is mid-bay, 6 1/2" off each.
    ElectricalDevice(uid="1F178X082B", tag="ED-M-LIVING-KGF8", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-20",
                     circuit="CKT-KITCH-SA2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-E1", face="left", distance_from_start=inch(393.5),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # --- Under FURN-M-KIT-E-HUNG: the 20" countertop-appliance cave (36-56") -------------
    # Ordinary countertop receptacles since the mixer box was retired (2026-10-25). KGF4 (SA2)
    # is the MICROWAVE trial outlet; KMX1 (SA1) is the stand mixer's. 42" sits behind a
    # 12-13" tall unit and within a 30-36" cord. KGF4 keeps its uid, a shipped IFC GlobalId.
    #
    # GFCI: ~10'-7" from FX-M-KITCH-SINK, outside 210.8(A)(9)'s 6' reach, but a countertop
    # appliance a step from a sink is where an inspector wants the device.
    #
    # NEC 210.52(C)(3) confines a receptacle serving the counter to on/above/in the surface:
    # these are on the wall above it.
    ElectricalDevice(uid="CEDKGF4AAA", tag="ED-M-LIVING-KGF4", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-20",
                     circuit="CKT-KITCH-SA2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-E1", face="left", distance_from_start=inch(326.0),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # The stand mixer's outlet, on SA1 so it never shares a branch with the microwave.
    ElectricalDevice(uid="NXKCFS9YGV", tag="ED-M-LIVING-KMX1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-20",
                     circuit="CKT-KITCH-SA1",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(42)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-E1", face="left", distance_from_start=inch(338.75),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Behind the range at 6": the whip drops to the floor box, not to a counter height. x is
    # the wall-face constant (35'-4"); y is the range's centre, 31'-0 3/8" since 2026-10-03.
    ElectricalDevice(uid="S8DH5FRQQA", tag="ED-M-LIVING-KRG1", kind=DeviceKind.RECEPTACLE_240,
                     type_ref="ED-T-LEV-RANGE-1450", circuit="CKT-RANGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-E1", face="left", distance_from_start=inch(372.375),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # On the centre bearing wall's east face, behind APPL-M-FRIDGE, at 48" — above the
    # coil deck, so the plug is reachable without pulling the whole cabinet out. Fridge is
    # y 30'-1 9/16"..32'-10 7/16". Recessed like KFZ1: 1" behind the unit takes no plug.
    ElectricalDevice(uid="D9EBW2FJTX", tag="ED-M-LIVING-KRF1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-20-REC", circuit="CKT-FRIDGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-C5", face="right", distance_from_start=inch(66.625),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Inside the sink base, 9" up (210.52(C)(4): 24" or more below the counter): the dishwasher's
    # cord. Follows APPL-M-DW on the sink base's west side — see storeys/main.py's OPENINGS
    # and plan/placeables.py's kitchen header.
    ElectricalDevice(uid="WK41TSMA97", tag="ED-M-LIVING-KDW1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-20", circuit="CKT-DISHWASHER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(9)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N1", face="left", distance_from_start=inch(90),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # The disposer outlet, in the sink base, the same 9" up on the same wall face —
    # reachable by the cord from APPL-M-DISP hanging under the bowl at 29'-4". Single 5-20R
    # on CKT-DISPOSAL; the wall control is the 24V loop billed with the appliance, not a
    # switch on this branch.
    ElectricalDevice(uid="N4A3YD3680", tag="ED-M-LIVING-KDS1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-SINGLE-520",
                     circuit="CKT-DISPOSAL",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(9)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-N1", face="left", distance_from_start=inch(75),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]

# Re-snapped to the survey-aligned partitions (storeys/second.py): each light in its room's
# new centre, each switch beside that room's door, each -RC1 on the first wall position
# `electrical.receptacle_spacing` measures (rest of the 210.52 fill is in plan/electrical.py).
# None carry `room=`, so a stale-coordinate device still matches by tag suffix and passes —
# that's how these got stranded inside partitions in the first place.
SECOND_DEVICES = [
    # The wet-location fan: a standard "damp-rated" bath-and-porch fixture is inadequate in
    # a room that condenses on purpose, and this one hangs at the ceiling where the wettest
    # air in the room collects.
    ElectricalDevice(uid="CED004K1AA", tag="ED-S-PLANT-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(9), ft(6)), type_ref="ED-T-LT-FAN52", circuit="CKT-LT-UPPER",
                     room="RM-S-PLANT", controlled_by=("ED-S-PLANT-SW",),
                     mount=Mount(kind=MountKind.CEILING, drop=ft(1, 6))),
    # North of D-S-PLANT's y=47" jamb pack, in the clear bay before the y=64" stud.
    ElectricalDevice(uid="CED004K2AA", tag="ED-S-PLANT-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-C1", face="left", distance_from_start=inch(56),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Reservoir service rack: only its cord plug occupies RC6, so the in-use cover closes.
    # Local timers, power supplies and wired pump-permit relay mount in the dry enclosure;
    # safety controls stay powered independently of the timer-switched pump supplies.
    ElectricalDevice(uid="PEHTPE0R62", tag="ED-S-PLANT-RC6", kind=DeviceKind.RECEPTACLE_GFCI,
                     type_ref="ED-T-LEV-GFCI-WR", circuit="CKT-RC-SECOND", room="RM-S-PLANT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-S1", face="left", distance_from_start=inch(184),
                         normal_gap=inch(0), rotation_offset=deg(180)))),
    ElectricalDevice(uid="CED005K1AA", tag="ED-S-STUDY2-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(24), ft(3)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-STUDY2", controlled_by=("ED-S-STUDY2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # West of D-S-STUDY2: the 2 1/4" box butts its west king/jack pack;
    # the midway plate clears the opening, on the study (south) face.
    ElectricalDevice(uid="CED005K2AA", tag="ED-S-STUDY2-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-SS1", face="right", distance_from_start=inch(8.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="CED006K1AA", tag="ED-S-BED1-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(26, 4), ft(14)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-BED1", controlled_by=("ED-S-BED1-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # On the north wall since 2026-10-02: the latch jamb is now the PAX side panel. x 24'-8 7/8",
    # east of the open leaf (its ring ends at 24'-5"), west of the desk.
    ElectricalDevice(uid="CED006K2AA", tag="ED-S-BED1-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BD1", face="right", distance_from_start=inch(33.875),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # The reading can's own switch is at the bed (2026-11-08; ED-S-SUITE-LAMP-SW's idiom): 46"
    # AFF on W-S-SS2, x=33'-8", over the twin's head third, 16"+ from ED-S-STUDY2-RC4 behind.
    ElectricalDevice(uid="3RQFN92MPQ", tag="ED-S-BED1-SW-READ", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-SS2", face="left", distance_from_start=inch(141),
                         normal_gap=inch(0), rotation_offset=deg(180)))),
    # y follows W-S-BD1's south face: the wall is INT_2X4_RC (plan/storeys/second.py) with
    # the resilient channel on the BED1 side. The box's back sits ON the face and the box is
    # 2" deep, so the authored y is the face LESS 1": 17'-5 1/8" - 1" = 17'-4 1/8".
    ElectricalDevice(uid="CED006K3AA", tag="ED-S-BED1-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-20", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BD1", face="right", distance_from_start=inch(46.125),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="CED007K1AA", tag="ED-S-BED2-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(26, 6), ft(22)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-BED2", controlled_by=("ED-S-BED2-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # As ED-S-BED1-SW, one bedroom north.
    ElectricalDevice(uid="CED007K2AA", tag="ED-S-BED2-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BD2", face="right", distance_from_start=inch(33.875),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # The reading cans' switch is at the bed (2026-11-08): 46" AFF on W-S-BD2 over the queen's
    # east head corner, x=34'-7" (the bed stands 1" off W-S-E3).
    ElectricalDevice(uid="5DG7KH9CA2", tag="ED-S-BED2-SW-READ", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BD2", face="right", distance_from_start=inch(155),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # Same 1/2" as ED-S-BED1-RC1, on W-S-BD2's south face, for the same reason.
    ElectricalDevice(uid="CED007K3AA", tag="ED-S-BED2-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-20", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BD2", face="right", distance_from_start=inch(46.125),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="CED008K1AA", tag="ED-S-BED3-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(31, 3.5), ft(30)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-BED3", controlled_by=("ED-S-BED3-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED008K2AA", tag="ED-S-BED3-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BW3", face="right", distance_from_start=inch(46),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # The reading can's switch is at the bed (2026-11-08): 46" AFF on W-S-E4 at y=30'-4", just
    # south of the full bed's head, on the open side.
    ElectricalDevice(uid="6RW73D2Q06", tag="ED-S-BED3-SW-READ", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-E4", face="left", distance_from_start=inch(44),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="CED008K3AA", tag="ED-S-BED3-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-20", circuit="CKT-RC-SECOND",
                     # x=35'-0", 12" off the NE corner; 48" keeps the box above the bed's
                     # corner (WIN-S-BED3-N, whose sill it matched, is gone since 2026-11-16).
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-N1", face="left", distance_from_start=inch(12),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    ElectricalDevice(uid="CED009K1AA", tag="ED-S-SUITE-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(2, 4.5), ft(9, 10.25)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-SUITE", controlled_by=("ED-S-SUITE-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # In the suite's east arm, beside D-S-SUITE (the hall door through the bearing wall).
    ElectricalDevice(uid="CED009K2AA", tag="ED-S-SUITE-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-CLN", face="left", distance_from_start=inch(83.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="CED009K3AA", tag="ED-S-SUITE-RC1", kind=DeviceKind.RECEPTACLE_GFCI,
                     type_ref="ED-T-LEV-GFCI-20", circuit="CKT-RC-SECOND",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-SBS", face="right", distance_from_start=inch(67.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # --- rooms the survey added: suite bath, vanity alcove, landing, north closet -------
    # None is a habitable occupancy, so `electrical.room_lighting` does not require these;
    # they are here because a windowless bath, an interior alcove, the stair arrival and a
    # closet all need a switched light to be usable.
    # ED-S-SUITEBATH-LT is the dry zone's can (2026-10-03): x 12'-6 3/4" is mid-way across
    # it, 11" in front of the vanity. Both suite-bath cans sit on y 19'-4", the middle of the
    # clear FS-ATTIC bay between the I-joists at 18'-8"/20'-0"; it was under DU-A-ERV-R-BED3
    # at 18'-0". ~15" clear of PR-A-STUBATH-DRAIN. Nothing grades this; re-measure after
    # a move. (2 x 500 + 2,400 Karlie bulb source) lm x CU 0.6 x LLF 0.8 / 46 sf = ~35 fc
    # (the Karlie's delivered lumens are unpublished).
    ElectricalDevice(uid="CED013K1AA", tag="ED-S-SUITEBATH-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(12, 6.75), ft(19, 4)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-SUITEBATH", controlled_by=("ED-S-SUITEBATH-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # On the bath face east of D-S-SUITEBATH, 55 1/2" from the wall start; clear of its casing.
    ElectricalDevice(uid="CED013K2AA", tag="ED-S-SUITEBATH-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-SBS", face="left", distance_from_start=inch(55.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # One can over each lavatory, 20" off the mirror wall, ahead of whoever stands there.
    ElectricalDevice(uid="CED014K1AA", tag="ED-S-VANITY-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(1, 10.25), ft(24, 8)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-VANITY", controlled_by=("ED-S-VANITY-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    ElectricalDevice(uid="EGJBXN0J2K", tag="ED-S-VANITY-CAN2", kind=DeviceKind.LIGHT,
                     position=pt(ft(4, 4.25), ft(24, 8)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-VANITY", controlled_by=("ED-S-VANITY-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # On W-S-BD-N's vanity face between the two mirrors, under P6 sconce C (plan/mirrors.py).
    ElectricalDevice(uid="CED014K2AA", tag="ED-S-VANITY-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-BD-N", face="right", distance_from_start=inch(37.375),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="CED015K1AA", tag="ED-S-LANDING-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(7, 9), ft(24, 8)), type_ref="ED-T-LT-CAN4", circuit="CKT-LT-UPPER",
                     room="RM-S-HALL", controlled_by=("ED-S-LANDING-SW",),
                     mount=Mount(kind=MountKind.CEILING, recessed_into_host_surface=True)),
    # On W-S-SN3's north face beside ED-S-STAIR-SW (plan/lighting_second.py).
    ElectricalDevice(uid="CED015K2AA", tag="ED-S-LANDING-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-SN3", face="left", distance_from_start=inch(22.125),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # ** IT MOVED, AND IT HAD TO. ** (20'-0", 33'-0") is inside EQ-S-HP1-AH's footprint
    # since the 2026-09-04 HP1 move, and having no authored elevation it resolved against a
    # 9'-0" ceiling that no longer exists in this room at all — SF-S-HP1 is the closet's
    # ceiling now, at 7'-3". (18'-9", 33'-6") is west of the cabinet, in the closet's own
    # west lane, with the elevation and the recess authored so it sets into the box face
    # rather than hanging above it.
    # It is 12 3/8" east of FO-S-STAIR's east edge — CLOSER to the stair than the old
    # station, so `code.R303_7_stairway_illumination` still counts it for ST-M2S.
    ElectricalDevice(uid="CED016K1AA", tag="ED-S-NCLOSET-LT", kind=DeviceKind.LIGHT,
                     position=pt(ft(18, 9), ft(33, 6)), type_ref="ED-T-LT-WAFER4",
                     circuit="CKT-LT-UPPER",
                     room="RM-S-NCLOSET", controlled_by=("ED-S-NCLOSET-SW",),
                     mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 3),
                                 recessed_into_host_surface=True)),
    ElectricalDevice(uid="CED016K2AA", tag="ED-S-NCLOSET-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-S-CLN-S", face="right", distance_from_start=inch(41.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]

# Attic habitable rooms, both east of the ridge. ** THE CATHEDRAL PLANE SETS BOTH CEILING
# BOX ELEVATIONS. ** At 6:12 off a 1 1/2" rafter plate the underside is `1 1/2" + x/2`
# mirrored about x=18'. These two fittings USED to be recessed cans in that plane at
# x=22'-0"; on 2026-09-06 the whole storey came off its recessed cans (plan/lighting_attic.py
# carries the reasoning and the corrected 2" product data) and they became up/down sconces
# on the centre wall's east face at x=18'-5 3/8" — that face's finish plane plus a 4"-deep
# body's own half, the offset ED-A-STUDY-SPOT already uses on the same wall. (2026-10-14: the
# RM-A-EAST-UNFIN fittings are now gothic iron sconces, ED-T-LT-SCONCE-GOTHIC.)
ATTIC_DEVICES = [
    # RM-A-EAST-UNFIN (x 18'-36', y 8'-8"-36'): switch inside D-A-HALVES, the door at (18', 32').
    # ** y MOVED 15'-0" -> 31'-6", AND THAT IS A BUG FIX, NOT A STYLE CHANGE: ** this fitting
    # stood at exactly (22'-0", 15'-0"), the same point as the old ED-A-EAST-CAN3, so the
    # loft has been lit by two coincident fixtures and billed for both. 31'-6" is the fourth
    # station in that room's run, 11 1/2" clear of ED-A-EAST-SW's plate below.
    ElectricalDevice(uid="CED011K1AA", tag="ED-A-EAST-LT", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-CANDLE",
                     circuit="CKT-LT-UPPER", room="RM-A-EAST-UNFIN",
                     controlled_by=("ED-A-EAST-SW", "ED-A-EAST-SW2"),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-C2B", face="right", distance_from_start=inch(110),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="CED011K2AA", tag="ED-A-EAST-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW3", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-C2B", face="right", distance_from_start=inch(121.5),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # The air handler's service receptacle (NEC 210.63; IMC 306.3 / IRC M1305.1.3 "at or near
    # the appliance"): on the centre wall's east face 34" west of EQ-S-HP1-AH's platform,
    # level with its front panel, 10" off ED-A-EAST-SCONCE2. Plain duplex on the attic
    # circuit, not the unit's own CKT-HP1-AH. Its light and switch are ED-A-EAST-LT3 / -SW2.
    ElectricalDevice(uid="QPHY6A75YB", tag="ED-A-HP1-RC1", kind=DeviceKind.RECEPTACLE,
                     type_ref="ED-T-LEV-DUPLEX-15", circuit="CKT-RC-ATTIC",
                     room="RM-A-EAST-UNFIN",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(16)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-C2B", face="right", distance_from_start=inch(54),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    # RM-A-STUDY (x 18'-36', y 0-8'-8"): wall light and switch on W-A-C1's east face.
    ElectricalDevice(uid="CED012K1AA", tag="ED-A-STUDY-LT", kind=DeviceKind.LIGHT,
                     type_ref="ED-T-LT-SCONCE-UD",
                     circuit="CKT-LT-UPPER", room="RM-A-STUDY", controlled_by=("ED-A-STUDY-SW",),
                     mount=Mount(kind=MountKind.WALL, elevation=ft(6, 6)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-C1", face="right", distance_from_start=inch(40),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="CED012K2AA", tag="ED-A-STUDY-SW", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-LEV-SW1", circuit="CKT-LT-UPPER",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-C1", face="right", distance_from_start=inch(60),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
]

# --- The radon fan's outlet on the north gable siding ----------------------------------
# ** MN 1303.2402 subp. 6, 2026-11-12. ** Was ED-A-NEMA-JB, an unfed blank box at x=13'-10".
# VR-M-STACK names it (fan_power_ref).
#   * A WR GFCI receptacle under an in-use cover, not a blank box. A radon fan comes with a
#     cord; the outlet is its GFCI (NEC 210.8(F), outdoors) and its disconnect in one, on a
#     15 A device to match the 15 A breaker (210.21(B)(3)).
#   * W-A-N2, centre x=8'-10", below the radon leg's 23'-8" elbow and so below the fan's
#     24" x 3' space (graded, subp. 5.D). East along the same course: ED-A-PV-JB, with
#     ED-A-PV-SPD hung from its bottom knockout (the MNSPD mounts only by its nipple).
#   * GABLE ENCLOSURE MOUNTING (both boxes): a 3/4" cellular-PVC block, 1" larger than the
#     box all round, centred on the 22'-0" girt course (264"-267 1/2") and screwed through a
#     panel flat into the KDAT with two gasketed screws in one row. The box screws to the
#     block, so its own hole pattern never has to fit a 3 1/2" course (normal_gap 3/4").
#   * Fed on CKT-RC-ATTIC (15 A AFCI, slot 47) by NM off ED-A-POCKET-RC1's run in RM-A-POCKET,
#     through a short sealed nipple behind the box: ccSPF and sheathing foamed, the panel
#     hole under the block. Not modelled, like every NM branch.
# Mount elevation is storey-relative (attic datum 20'): 24 1/4" is the 3" box's bottom.
NEMA_BOX = [
    ElectricalDevice(uid="CEJ901AAAA", tag="ED-A-RADON-RC", kind=DeviceKind.RECEPTACLE_GFCI,
                     type_ref="ED-T-LEV-GFCI-WR-15", circuit="CKT-RC-ATTIC",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(24.25)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-N2", face="right", distance_from_start=inch(14),
                         normal_gap=inch(0.75), rotation_offset=deg(0)))),
]
# No clamp: the block's two gasketed screws per enclosure are inside the field-grid count
# (``takeoff.fasteners``). An S-5! seam clamp has no seam to close on here.
NEMA_CLAMP = []

# --- Downspout securement: through-panel straps on the PBR siding ---------------------
# The two roof leaders (params/roof_trim.py, TR-RF-LEADER-W/E) run ~24' down the north end
# of the west/east faces, steadied — NOT supported — by a two-hole 316 stainless pipe strap
# on a standoff block, screwed through the panel into the girt behind with 316 screws sized
# through the block into the girt (library/hardware/, THROUGH_PANEL_PIPE_STRAP; same strap
# as CN-M-VENT-CLAMP1/2 and CN-M-RADON-CLAMP1/2).
#
# ** This is not a downgrade from an S-5! CanDuit #13 ring on a seam clamp — it is the only
# thing that can work. ** The CanDuit's entire value is
# non-penetration, and S5_CANDUIT_PIPE_CLAMP declares `requires_role=ROLE_STANDING_SEAM_CLAMP`,
# so every ring ordered brings a seam clamp with it. `pbr-panel-24` has no seam to clamp:
# the ring would arrive with a bracket that has nothing to grip. On a wall already screwed
# through 3,098 times, a non-penetrating fixing also buys nothing it did not already spend.
# It is cheaper by roughly $15-22/point against ~$3, but that is the consequence, not the
# reason.
#
# The ring is still catalogued and still priced, untouched, so reverting the cladding is a
# `size=` change here and nothing more. The strap is sized on pipe OUTER diameter exactly
# the way the ring was: a 4" round leader is 4.0" OD, hence **#13**, and `size` bills it
# through `hardware_by_model`'s family-prefix match. ** THREE per leader at ~6' o.c.
# (5'/11'/17'). ** The eave is 20'-10 3/8" (6:12 off a 1 1/2" rafter plate); the top strap
# at 17'-0" sits 3'-11" below the head, inside the same ~6' spacing the other three keep.
# 6' apart is three 24" girt courses, so
# every strap lands on a course and none of them needs its own blocking. Each on the wall
# with cladding at that elevation. Plan position is the leader's own centreline, 9.805" outboard
# of the sheathing datum (trough mid-width, params/roof_trim.py::_TROUGH_MID_IN) — literal
# offsets below, not arithmetic, since the editable-plan dialect forbids binary operators.
_LEADER_X_W = inch(-9.805)
_LEADER_X_E = ft(36, 9.805)
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
