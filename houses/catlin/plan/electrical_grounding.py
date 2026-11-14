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
    ServiceEntrance,
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
                      transition_min_height=inch(18), min_rod_spacing=ft(6),
                      # Owner 2026-11-14: no garage SPD (230.67 and 215.18 do not ask for one).
                      outbuilding_spds=False),
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
    # and the copper bath branch. #2 Cu: Table 250.102(C)(1) on the 320 A service (310.12(A):
    # 300 Cu / 400 Al) and on the summed 2 x 4/0 Al feeders alike. Landing on the Ufer stub
    # needs its GEC as large, so BC-M-GEC-UFER is #2 too. A lateral over 500 kcmil Al raises it.
    BondingConductor(uid="BT7H76Q8K7", tag="BC-B-WATER", role="water_bond", from_ref="GE-B-UFER",
                     to_ref="PR-B-CW-WH", size="2"),
    BondingConductor(uid="GKHKD20YQH", tag="BC-B-WATER-WH", role="water_bond", from_ref="PR-B-CW-WH",
                     to_ref="PR-B-HW-TRUNK", size="2"),
    BondingConductor(uid="75ZF8AVPS6", tag="BC-B-WATER-BATH", role="water_bond", from_ref="PR-B-CW-WH",
                     to_ref="PR-B-CW-BATH", size="2"),
    # PV DC SPD at the inverter's DC input (the EG4's own DC surge rating is unpublished).
    ElectricalDevice(uid="EJH2340ANK", tag="ED-B-INV-SPD", kind=DeviceKind.SPD, type_ref="ED-T-SPD-PV",
                     room="RM-B-FURNACE", mount=Mount(kind=MountKind.WALL, elevation=inch(48)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-B-N4", face="left", distance_from_start=inch(44),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]

# --- service: GECs, SPD, IBT and the single-point comms entry, all on W-M-W1 -------------
SERVICE_GROUNDING = [
    # The service's sizing basis and neutral bond (250.24). No conductor_size: the Xcel lateral
    # lands on the meter-main's lugs and its size is not known, so the checks take 310.12(A)
    # on 320 A. The two 200 A mains feed 4/0 Al SER each (250.64(D)(1) summed basis). The
    # main bonding jumper is in the meter-main; every panel past it keeps its neutral isolated.
    ServiceEntrance(uid="9QPW6E02RJ", tag="SE-M-SERVICE", service_ref="ED-M-METER",
                    disconnect_conductors=("4/0", "4/0"), disconnect_material="al",
                    main_bonding_jumper_ref="ED-M-METER",
                    neutral_isolated_refs=("ED-B-PANEL", "ED-B-PANEL-2", "ED-B-BACKUP-PANEL",
                                           "ED-G-PANEL")),
    # Meter-main is the service disconnect: the GECs and the main bonding jumper land here.
    BondingConductor(uid="PM0JNEJBC4", tag="BC-M-GEC-ROD", role="gec", from_ref="ED-M-METER", to_ref="GE-B-ROD-1",
                     size="6", path=(pt(inch(-11.2), inch(357.1)), pt(inch(-11.2), inch(357.1)),
                                     pt(inch(-31), inch(412))),
                     elevations=(inch(0), inch(-58), inch(-58))),
    # Through the rim over the working spaces (their tops are -31 7/16"), down to the stub.
    # #2, over 250.66(B)'s #4 cap: BC-B-WATER lands on this stub (250.104(A)(1)).
    BondingConductor(uid="A81HH8CV8V", tag="BC-M-GEC-UFER", role="gec", from_ref="ED-M-METER",
                     to_ref="GE-B-UFER", size="2", bare=False,
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
    # the box, out from under the radon fan's space (MN 1303.2402 subp. 5.D). On a PVC block
    # like the box (plan/mep_electrical.py, GABLE ENCLOSURE MOUNTING).
    ElectricalDevice(uid="XQ69SAWHP0", tag="ED-A-PV-SPD", kind=DeviceKind.SPD, type_ref="ED-T-SPD-PV",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(22.75)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-A-N2", face="right", distance_from_start=inch(6),
                         normal_gap=inch(0.75), rotation_offset=deg(-180)))),
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

# --- garage: a separate building fed by one feeder (250.32) ------------------------------
# Stone footings, so no Ufer: a rod pair west of W-G-W, its GEC on the ground bar of the
# subpanel ED-G-PANEL, where the feeder's EGC lands (250.32(B)(1); neutral isolated there).
GARAGE_GROUNDING = [
    GroundingElectrode(uid="ZXWN35CW68", tag="GE-G-ROD-1", kind="rod", position=pt(inch(40), inch(600)),
                       top_elevation=inch(-58)),
    GroundingElectrode(uid="809R3NTWXK", tag="GE-G-ROD-2", kind="rod", position=pt(inch(40), inch(792)),
                       top_elevation=inch(-58)),
    BondingConductor(uid="E3V16RT8WC", tag="BC-G-GEC", role="gec", from_ref="ED-G-PANEL", to_ref="GE-G-ROD-1",
                     size="6"),
    BondingConductor(uid="Q1GM2C34KQ", tag="BC-G-ROD-JUMPER", role="gec", from_ref="GE-G-ROD-1",
                     to_ref="GE-G-ROD-2", size="6",
                     path=(pt(inch(40), inch(600)), pt(inch(40), inch(792))),
                     elevations=(inch(-58), inch(-58))),
    # 250.94(A): an IBT at the building, bonded to the subpanel's ground bar.
    ElectricalDevice(uid="592BENDBNY", tag="ED-G-IBT", kind=DeviceKind.JUNCTION_BOX, type_ref="ED-T-IBT",
                     room="RM-GARAGE", mount=Mount(kind=MountKind.WALL, elevation=inch(30)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-G-W", face="left", distance_from_start=inch(206),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
    BondingConductor(uid="F9N78H7JJQ", tag="BC-G-IBT", role="ibt", from_ref="ED-G-IBT", to_ref="ED-G-PANEL",
                     size="6"),
    # ED-G-SPD (Leviton 51120-1) dropped 2026-11-14 (owner): discontinued, 3 kA, and neither
    # 230.67 nor 215.18 asks for one at the garage.
]
