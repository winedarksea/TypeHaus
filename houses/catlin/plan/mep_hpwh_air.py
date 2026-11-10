# haus: editable
# EQ-B-WH's air (2026-11-09; notes/basement_winter_heat.md "Air connection review").
#
# Exhaust is ducted to the stair; the inlet is NOT ducted (owner). Rheem's top inlet cannot
# be built here: its elbow takes 8-10" of the 11 1/4" to W-B-WELL, leaving 1-3" against the
# 12" of flex AP22654 p.15 demands. AP22654 p.9 lists one duct for "any size room" with 18 in2
# under the door (D-B-CLOSET's 3/4" undercut). The heater draws off the closet, fed from the
# stair through REG-B-WH-IN, so the door gap is a code minimum and not the air path.
#
# Exhaust parts: SP17829 adapter, one 8" adjustable 90 set full (SP20890 or equal, bare, on
# the unit), then about 32" of R-6 8" flex, R12 centreline at the bend, to the boot. Flex
# between heater and boot is the p.15 isolation section. The model's mitres are a routing
# envelope. Never tied to another duct (p.15). DuctSystem.TRANSFER: no fan curve or credit.
#
# Elevations off the slab. W-B-WELL's studs are 16" o.c. off y=320 1/4"; each opening takes
# one 14 1/2" bay and cuts none.

from typehaus import DuctRun, DuctSystem, Mount, MountKind, Register, deg, inch, pt
from typehaus.model import Location, WallAttachment

_INSULATION = '1 1/2" fibreglass flex jacket, R-6, vapour-sealed (Rheem AP22654 p.15)'

DUCTS_HPWH_AIR = [
    DuctRun(uid="2XHERX8QJG", tag="DU-B-WH-OUT", system=DuctSystem.TRANSFER,
            path=(pt(inch(142.225), inch(324.525)), pt(inch(136), inch(326.79)),
                  pt(inch(136), inch(344.5)), pt(inch(163.5), inch(344.5))),
            diameter=inch(8), material="flex", insulation=_INSULATION,
            end_terminal_ref="REG-B-WH-OUT",
            elevations=(inch(65.5), inch(65.5), inch(63), inch(63))),
]

REGISTERS_HPWH_AIR = [
    # Wall elevation is the face BOTTOM. The intake sleeve's top (80 1/2") stays under the
    # lined stringer at the opening's north edge (81.8"), where W-B-WELL's closet face has
    # the stringer standing on it. No closet-side grille: its flange would hit that stringer
    # and the tank.
    Register(uid="1MZ9EB5VTZ", tag="REG-B-WH-IN", kind=DuctSystem.TRANSFER, room="RM-B-STAIR",
             type_ref="REG-T-HPWH-INTAKE-1210",
             mount=Mount(kind=MountKind.WALL, elevation=inch(69.625)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-B-WELL", face="right", distance_from_start=inch(22.25),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    Register(uid="V4Q2XAQCNS", tag="REG-B-WH-OUT", kind=DuctSystem.TRANSFER, room="RM-B-STAIR",
             type_ref="REG-T-HPWH-STAIR-1210", duct_ref="DU-B-WH-OUT",
             mount=Mount(kind=MountKind.WALL, elevation=inch(57.125)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-B-WELL", face="right", distance_from_start=inch(38.5),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
]
