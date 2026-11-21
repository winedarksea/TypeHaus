# haus: editable
# EQ-B-WH's air (2026-11-09; notes/basement_winter_heat.md "Air connections").
#
# Both connections are ducted to the stair hall, so the workshop keeps its heat and the
# evaporator never draws shop dust. AP22654 p.9: ducted both ways is "any size room", no
# added ventilation; p.15: any split of length up to Table 1 (8" flex 125'); never tied to
# another duct. DuctSystem.TRANSFER: no fan curve or credit.
#
# One bay takes both. W-B-HALL-W's only 12"-clear bay north of D-B-SHOP is 170 5/8"..183 1/4"
# (king to stud); the next is 9.8" (stud to D-B-BATH's pocket king) and the pocket itself is
# north of that. So the two boots stack in one bay, exhaust low and intake 10" above it:
# cold exhaust falls away from the intake (p.15 asks only that recirculation be reduced).
# The tank's rotation puts its side port and the top elbow's outlet on one plan line, so
# each run is a straight leg and one 60 deg bend square into its boot (a boot's collar
# takes the duct square). Each boot fits the bay and cuts nothing.
#
# Exhaust: SP17829 side adapter, about 16" of R-6 8" flex, the bend (centreline radius
# 12": the 8" inner radius p.16 asks), 13" into the boot: 2.4 ft.
# Intake: Rheem's inlet adapter and SP20890 elbow (H 91" to its top), then about 28" of the
# same flex and the same bend (4.5 ft): the p.15 12" isolation section. Both together are
# under 10 ft of flex against Table 1's 125 ft. The filter lifts out of the top (p.26): the
# kit's rigid spacer between flange and elbow (AP21628 step 1) keeps the flex 2 13/16" over
# AP22654's 6" line (notes/basement_winter_heat.md "Filter").
#
# Elevations off the slab. Duct ends are the boots' collar tips, 6 3/4" behind the hall face.

from typehaus import DuctRun, DuctSystem, Mount, MountKind, Register, deg, inch, pt
from typehaus.model import Location, WallAttachment

from .ducts import INSULATION_HPWH_FLEX


DUCTS_HPWH_AIR = [
    DuctRun(uid="2XHERX8QJG", tag="DU-B-WH-OUT", system=DuctSystem.TRANSFER,
            path=(pt(inch(143.57), inch(190.87)), pt(inch(151.43), inch(177.25)),
                  pt(inch(163.5), inch(177.25))),
            diameter=inch(8), material="flex", insulation=INSULATION_HPWH_FLEX,
            end_terminal_ref="REG-B-WH-OUT",
            elevations=(inch(65.5), inch(65.5), inch(65.5))),
    DuctRun(uid="NC6N6JJRAZ", tag="DU-B-WH-IN", system=DuctSystem.TRANSFER,
            path=(pt(inch(137.5), inch(201.375)), pt(inch(137.5), inch(201.375)),
                  pt(inch(151.43), inch(177.25)), pt(inch(163.5), inch(177.25))),
            diameter=inch(8), material="flex", insulation=INSULATION_HPWH_FLEX,
            end_terminal_ref="REG-B-WH-IN",
            elevations=(inch(74.1875), inch(87), inch(87), inch(87))),
]

REGISTERS_HPWH_AIR = [
    # Wall elevation is the face BOTTOM: both 12x10 faces are centred on their duct.
    Register(uid="1MZ9EB5VTZ", tag="REG-B-WH-IN", kind=DuctSystem.TRANSFER, room="RM-B-STAIR",
             type_ref="REG-T-HPWH-STAIR-1210", duct_ref="DU-B-WH-IN",
             mount=Mount(kind=MountKind.WALL, elevation=inch(81.125)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-B-HALL-W", face="left", distance_from_start=inch(38.75),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    Register(uid="V4Q2XAQCNS", tag="REG-B-WH-OUT", kind=DuctSystem.TRANSFER, room="RM-B-STAIR",
             type_ref="REG-T-HPWH-STAIR-1210", duct_ref="DU-B-WH-OUT",
             mount=Mount(kind=MountKind.WALL, elevation=inch(59.625)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-B-HALL-W", face="left", distance_from_start=inch(38.75),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
]
