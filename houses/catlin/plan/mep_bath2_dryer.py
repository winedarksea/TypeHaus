# haus: editable
# RM-M-BATH2's stall-drying fan (2026-10-12, notes/bath2_shower.md §7).
#
# A breeze, not a blower: EQ-M-BATH2-STALL-FAN draws filtered bedroom air through
# REG-M-BATH2-DRY-IN, pushes it down DU-M-BATH2-DRY and out of REG-M-BATH2-DRY-OUT into the
# stall, on a 30-60 min countdown (ED-M-BATH2-SW-DRY). The air leaves over the front glass's
# open top, past REG-M-EXH2, and back to the bedroom under the door. It is a TRANSFER loop:
# no outdoor air, no ventilation credit, and `joinable` makes any contact with an ERV run a
# clash.
#
# The type catalog (fan, both terminals) is plan/equipment_types.py; plan/mep_hvac.py is at
# its 500-line limit. An editable file cannot `from plan import ...`, so plan/mep.py composes.
#
# Load: ~30 VA on CKT-LT-MAIN. An Equipment adds 0 VA to the derived panel schedule, so it
# is stated on the circuit's description, not as `load_va` (which would freeze the sum).

from typehaus import (
    DeviceKind,
    DuctRouting,
    DuctRun,
    DuctSystem,
    ElectricalDevice,
    Equipment,
    EquipmentKind,
    Mount,
    MountKind,
    Register,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import Location, WallAttachment

MAIN_STALL_FAN = [
    # In RM-M-BED's ceiling, in the FS-S-WEST bay y 128"-144", 6" east of the east nightstand,
    # under RM-S-CLOSET. The case stands on the bottom chord (109 5/8") and tops out at
    # 117 5/8", under the 118 1/2" top chord. Serviced by dropping the grille below it.
    Equipment(uid="BFWXCA2JDD", tag="EQ-M-BATH2-STALL-FAN", kind=EquipmentKind.FAN,
              position=pt(ft(15), ft(11, 4)), footprint=(inch(12), inch(9)),
              room="RM-M-BED", type_ref="EQ-T-INLINE-FAN-4", circuit="CKT-LT-MAIN",
              mount=Mount(kind=MountKind.CEILING, elevation=inch(108.125))),
    Register(uid="VR9BYEJNG8", tag="REG-M-BATH2-DRY-IN", kind=DuctSystem.TRANSFER, room="RM-M-BED",
             position=pt(ft(15), ft(11, 4)), duct_ref="DU-M-BATH2-DRY",
             type_ref="REG-T-FILTER-GRILLE-10", design_cfm=95,
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # Inside the glass, between ED-M-BATH2-CAN-SH and -CAN-SH-EVE: 3.4" clear of each.
    Register(uid="J58Z78JMHC", tag="REG-M-BATH2-DRY-OUT", kind=DuctSystem.TRANSFER, room="RM-M-BATH2",
             position=pt(ft(6, 4), ft(15, 4)), duct_ref="DU-M-BATH2-DRY",
             type_ref="REG-T-NOZZLE-DAMPER-4", design_cfm=95,
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # The third control: a countdown timer on W-M-W3 over the counter, 5" north of
    # ED-M-BATH2-RC1 and clear of the 42" halo glass and its cleat. It did not fit as a third
    # gang on W-M-BDN1 (plan/lighting.py).
    ElectricalDevice(uid="T3ZXRZ1CN3", tag="ED-M-BATH2-SW-DRY", kind=DeviceKind.SWITCH,
                     type_ref="ED-T-SWITCH-TIMER",
                     circuit="CKT-LT-MAIN", room="RM-M-BATH2",
                     mount=Mount(kind=MountKind.WALL, elevation=inch(46)),
                     location=Location(attachment=WallAttachment(
                         wall_ref="W-M-W3", face="left", distance_from_start=inch(51),
                         normal_gap=inch(0), rotation_offset=deg(-180)))),
]

# 4" galvanized, second-storey-relative z, FS-S-WEST's two tiers (plan/mep_erv_l2.py): a
# bay leg rides the LOWER tier (-8 3/8"), a leg crossing trusses the UPPER (-3 1/2").
# West along the 11'-4" bay, south through web opening 3 (x 7'-4 1/2"..8'-7 1/2") across
# the 12', 13'-4" and 14'-8" trusses, over DU-M-ERV-R-LIVING and -BED2, then west along the
# 15'-4" bay to the nozzle. Moves no existing run; 5" and 6" do not fit the crossing.
# ACCEPTED ROUTE: `haus route --run DU-M-BATH2-DRY --alternatives 6 --evaluate --via
# "8,11.3333" --via "8,15.3333"` proposal A (13.07 ft, 4 bends), with two corrections. Its
# crossing tier was -2", which puts the crown 1 1/2" into the top chord
# (`mep.run_member_crossing` FAIL), so the crossing is set to the house's -3 1/2" upper tier.
# Its x=7'-10 13/16" became 8'-0", the centre of web opening 3. B-F were longer and each
# added FAILs.
DUCTS_STALL_FAN = [
    DuctRun(uid="YGK2JPV5AN", tag="DU-M-BATH2-DRY", system=DuctSystem.TRANSFER,
            path=(pt(ft(14, 6), ft(11, 4)), pt(ft(8), ft(11, 4)), pt(ft(8), ft(11, 4)),
                  pt(ft(8), ft(15, 4)), pt(ft(8), ft(15, 4)), pt(ft(6, 4), ft(15, 4))),
            elevations=(inch(-8.375), inch(-8.375), inch(-3.5), inch(-3.5), inch(-8.375),
                        inch(-8.375)),
            diameter=inch(4), routing=DuctRouting.JOIST_BAY, floor_ref="FS-S-WEST",
            material="galvanized", design_cfm=95),
]
