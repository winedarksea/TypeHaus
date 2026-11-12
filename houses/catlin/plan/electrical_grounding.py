# haus: editable
# Grounding electrode system, bonding, surge and lightning hooks (decision #123).
# Basis, oracle sums and the rejected ideas: notes/grounding_bonding.md.
#
# Elevations here are ABSOLUTE (project frame). Grade is -2'-10" (-34"); every rod top and
# the counterpoise are 24" below it (-58"), clear over the 3 ft-deep power lateral at y=18'.
# Rods stand 2 ft outside the west cladding (x=-31"), inside the x=-7' lot line.
# A bond with no path is the electrician's route: billed and graded on the straight line.

from typehaus import (
    BondingConductor,
    ConduitRun,
    DeviceKind,
    ElectricalDevice,
    GroundingElectrode,
    GroundingStandard,
    Mount,
    MountKind,
    RacewayMaterial,
    Service,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import Location, WallAttachment

GROUNDING_STANDARD = [
    GroundingStandard(uid="74RT1X67ZB", tag="GND-STANDARD", rod_product_ref="GND-ROD-58X8",
                      rod_diameter=inch(0.625), rod_length=ft(8),
                      rod_clamp_product_ref="GND-ACORN-58",
                      encased_clamp_product_ref="GND-UFER-CLAMP", ibt_product_ref="GND-IBT",
                      transition_product_ref="GND-AL-CU-TRANS",
                      conductor_fastener_product_ref="GND-CLIP-S5",
                      conductor_fastener_spacing=inch(36), counterpoise_size="2",
                      counterpoise_material="copper", counterpoise_depth=inch(24),
                      down_lead_size="1/0", down_lead_material="aluminum",
                      transition_min_height=inch(18), min_rod_spacing=ft(6)),
]

# --- house electrode system: the Ufer, two rods, the counterpoise and its terminals ------
HOUSE_GROUNDING = [
    # #4 HDG in FT-B-W1 tied through into FT-B-W2 (params/foundations.py), stubbed up at
    # the panel bay inboard of W-B-W1, in the 4" between CZ-B-WS-BACKUP-PANEL and
    # CZ-B-WS-PANEL (110.26). ** TIE AND STUB BEFORE THE FOOTING POUR. **
    GroundingElectrode(uid="FVBPJHVC3F", tag="GE-B-UFER", kind="concrete_encased", position=pt(inch(13), inch(336)),
                       top_elevation=inch(-96), host_ref="FT-B-W1",
                       description="Concrete-encased electrode stub, inside face of W-B-W1"),
    # 14'-4" apart, south of the leader extension (y>=424") and 2 ft north of the lateral.
    GroundingElectrode(uid="95PJSE8XKG", tag="GE-B-ROD-1", kind="rod", position=pt(inch(-31), inch(412)),
                       top_elevation=inch(-58)),
    GroundingElectrode(uid="CS16YCN7KK", tag="GE-B-ROD-2", kind="rod", position=pt(inch(-31), inch(240)),
                       top_elevation=inch(-58)),
    # Lightning-ready corner terminals, diagonally opposite (NFPA 780 hooks only).
    GroundingElectrode(uid="3SEJP8W2AV", tag="GE-B-LPS-SW", kind="rod", use="lps_terminal",
                       position=pt(inch(-31), inch(-31)), top_elevation=inch(-58)),
    GroundingElectrode(uid="JG1FXZ7WM4", tag="GE-B-LPS-NE", kind="rod", use="lps_terminal",
                       position=pt(inch(463), inch(478)), top_elevation=inch(-58)),
    # Counterpoise: bare #2 Cu, SW terminal north along the west wall through both rods,
    # round the NW corner, and east at y=39'-10" (clear of the entry piers <=459", the
    # garage pads >=497", and both HP pads <=471.5") to the NE terminal.
    BondingConductor(uid="CCEVM9H2Y7", tag="BC-B-CP-W1", role="counterpoise", from_ref="GE-B-LPS-SW",
                     to_ref="GE-B-ROD-2", size="2",
                     path=(pt(inch(-31), inch(-31)), pt(inch(-31), inch(240))),
                     elevations=(inch(-58), inch(-58))),
    BondingConductor(uid="CP5Y556KHK", tag="BC-B-CP-W2", role="counterpoise", from_ref="GE-B-ROD-2",
                     to_ref="GE-B-ROD-1", size="2",
                     path=(pt(inch(-31), inch(240)), pt(inch(-31), inch(412))),
                     elevations=(inch(-58), inch(-58))),
    BondingConductor(uid="X3XQ155X90", tag="BC-B-CP-N", role="counterpoise", from_ref="GE-B-ROD-1",
                     to_ref="GE-B-LPS-NE", size="2",
                     path=(pt(inch(-31), inch(412)), pt(inch(-31), inch(478)),
                           pt(inch(463), inch(478))),
                     elevations=(inch(-58), inch(-58), inch(-58))),
    # Water bonds (250.104(A)): the copper cold at the heater, a jumper across the heater,
    # and the copper bath branch.
    BondingConductor(uid="BT7H76Q8K7", tag="BC-B-WATER", role="water_bond", from_ref="GE-B-UFER",
                     to_ref="PR-B-CW-WH", size="4"),
    BondingConductor(uid="GKHKD20YQH", tag="BC-B-WATER-WH", role="water_bond", from_ref="PR-B-CW-WH",
                     to_ref="PR-B-HW-TRUNK", size="4"),
    BondingConductor(uid="75ZF8AVPS6", tag="BC-B-WATER-BATH", role="water_bond", from_ref="PR-B-CW-WH",
                     to_ref="PR-B-CW-BATH", size="4"),
    # PV DC SPD at the inverter's DC input (the EG4's own DC surge rating is unpublished).
    ElectricalDevice(uid="EJH2340ANK", tag="ED-B-INV-SPD", kind=DeviceKind.SPD, type_ref="ED-T-SPD-PV",
                     room="RM-B-FURNACE", mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-N4", face="left", distance_from_start=inch(44),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]

# --- service: GECs, SPD, IBT and the single-point comms entry, all on W-M-W1 -------------
SERVICE_GROUNDING = [
    # Meter-main is the service disconnect: the GECs and the main bonding jumper land here.
    BondingConductor(uid="PM0JNEJBC4", tag="BC-M-GEC-ROD", role="gec", from_ref="ED-M-METER", to_ref="GE-B-ROD-1",
                     size="6", path=(pt(inch(-11.2), inch(357.1)), pt(inch(-11.2), inch(357.1)),
                                     pt(inch(-31), inch(412))),
                     elevations=(inch(0), inch(-58), inch(-58))),
    # Through the rim over the working spaces (their tops are -31 7/16"), down to the stub.
    BondingConductor(uid="A81HH8CV8V", tag="BC-M-GEC-UFER", role="gec", from_ref="ED-M-METER",
                     to_ref="GE-B-UFER", size="4", bare=False,
                     path=(pt(inch(-11.2), inch(357.1)), pt(inch(-11.2), inch(357.1)),
                           pt(inch(13), inch(357.1)), pt(inch(13), inch(336)),
                           pt(inch(13), inch(336))),
                     elevations=(inch(0), inch(-6), inch(-6), inch(-6), inch(-96))),
    BondingConductor(uid="F15125QS01", tag="BC-M-IBT", role="ibt", from_ref="ED-M-IBT", to_ref="ED-M-METER",
                     size="6"),
    ElectricalDevice(uid="FWX17NKXGJ", tag="ED-M-SPD", kind=DeviceKind.SPD, type_ref="ED-T-SPD-T1",
                     mount=Mount(kind=MountKind.WALL, elevation=ft(0)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-W1", face="right", distance_from_start=inch(29),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="22CJG651XR", tag="ED-M-IBT", kind=DeviceKind.JUNCTION_BOX, type_ref="ED-T-IBT",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(-12)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-W1", face="right", distance_from_start=inch(12),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ElectricalDevice(uid="12C93JY6Y5", tag="ED-M-DATA-ENTRY", kind=DeviceKind.DATA_OUTLET,
                     type_ref="ED-T-DATA-ENTRY",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(-12)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-W1", face="right", distance_from_start=inch(24),
                         normal_gap=inch(0), rotation_offset=deg(0)))),
    ConduitRun(uid="BDXPZAZE29", tag="CD-M-DATA-ENTRY", trade_size=inch(1), material=RacewayMaterial.EMT,
               service=Service.DATA, from_ref="ED-M-DATA-ENTRY", to_ref="ED-B-NET-PATCH",
               path=(pt(inch(-11), inch(376)), pt(inch(12), inch(376))),  # one joist bay
               start_elevation=inch(-6), end_elevation=inch(-45)),  # through the rim
]

# --- PV: DC SPD at the array box and the down-lead ---------------------------------------
PV_GROUNDING = [
    # Beside ED-A-PV-JB on the 22'-0" girt course (2026-11-12): x 9'-3"..9'-9", 2" west of
    # the box, out from under the radon fan's space (MN 1303.2402 subp. 5.D).
    ElectricalDevice(uid="XQ69SAWHP0", tag="ED-A-PV-SPD", kind=DeviceKind.SPD, type_ref="ED-T-SPD-PV",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(22.75)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-N2", face="right", distance_from_start=inch(6),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Aluminium (never copper on the Galvalume skin) on seam clips from SP-A-PV-W9 north to
    # the rake, down the rake and the NW corner trim to 18" above grade. Confirm the PVKIT's
    # UL 2703 module-to-rail bonding before relying on the array as one conductor.
    BondingConductor(uid="BA06162ZG0", tag="BC-A-PV-DOWN", role="down_lead", from_ref="SP-A-PV-W9",
                     to_ref="BC-B-PV-TAIL", size="1/0", material="aluminum",
                     path=(pt(inch(168), inch(401)), pt(inch(168), inch(438)),
                           pt(inch(-6), inch(438)), pt(inch(-6), inch(438))),
                     elevations=(inch(338), inch(338), inch(251), inch(-16))),
    # Bimetallic transition at -16" (18" above grade), then bare Cu to GE-B-ROD-1.
    BondingConductor(uid="4W5T38PB50", tag="BC-B-PV-TAIL", role="down_lead", from_ref="BC-A-PV-DOWN",
                     to_ref="GE-B-ROD-1", size="2",
                     path=(pt(inch(-6), inch(438)), pt(inch(-6), inch(438)),
                           pt(inch(-31), inch(412))),
                     elevations=(inch(-16), inch(-58), inch(-58))),
]

# --- garage: a separate building fed by seven branch circuits (250.32) ------------------
# Stone footings, so no Ufer: a rod pair west of W-G-W, bonded to the EGC bar in ED-G-GND-JB
# where the circuits' EGCs are joined.
GARAGE_GROUNDING = [
    GroundingElectrode(uid="ZXWN35CW68", tag="GE-G-ROD-1", kind="rod", position=pt(inch(40), inch(600)),
                       top_elevation=inch(-58)),
    GroundingElectrode(uid="809R3NTWXK", tag="GE-G-ROD-2", kind="rod", position=pt(inch(40), inch(792)),
                       top_elevation=inch(-58)),
    BondingConductor(uid="E3V16RT8WC", tag="BC-G-GEC", role="gec", from_ref="ED-G-GND-JB", to_ref="GE-G-ROD-1",
                     size="6"),
    BondingConductor(uid="Q1GM2C34KQ", tag="BC-G-ROD-JUMPER", role="gec", from_ref="GE-G-ROD-1",
                     to_ref="GE-G-ROD-2", size="6",
                     path=(pt(inch(40), inch(600)), pt(inch(40), inch(792))),
                     elevations=(inch(-58), inch(-58))),
    ElectricalDevice(uid="RMVDMF1Q8Y", tag="ED-G-GND-JB", kind=DeviceKind.JUNCTION_BOX,
                     type_ref="ED-T-GND-JB", room="RM-GARAGE",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(30)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-W", face="left", distance_from_start=inch(196),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Type 2 SPD beside the EV outlet, landed on its CKT-EV-1450 junction.
    ElectricalDevice(uid="GH0TMES07M", tag="ED-G-SPD", kind=DeviceKind.SPD, type_ref="ED-T-SPD-T2",
                     room="RM-GARAGE", mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-S", face="left", distance_from_start=inch(180),
                         normal_gap=inch(0), rotation_offset=deg(180)))),
]
