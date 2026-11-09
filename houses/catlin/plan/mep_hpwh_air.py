# haus: editable
# EQ-B-WH's two air connections, ducted into the stair (2026-11-09; notes/basement_winter_heat.md).
#
# The tank stands in the closet so its chill leaves the furnace room. Both ducts go through
# W-B-WELL's stud bays into the open stair, 8" insulated flex off Rheem's adapters: AP22654
# p.9, "ducted with inlet and outlet duct: any size room, no additional ventilation". Table 1
# allows 125' of 8" flex; this pair is about 33' equivalent with both grilles (p.16, 5' each).
# Never tied to another duct (p.15). DuctSystem.TRANSFER: no fan curve, no ventilation credit.
#
# Elevations are off the slab. The inlet elbow's crown is H, 91" (RH-PIHP-SC-SO p.2, ±1.5"
# scaled): it clears the stair soffit by about 1 3/4" here, and only with the inlet on the
# tank's south side. The flex falls north under the rake to 81" at the bay; the model draws
# that as level at 81" (the rigid kit elbow above it is Rheem's, 91" to its crown).
# W-B-WELL's studs are 16" o.c. off y=320 1/4"; each duct takes one 14 1/2" bay and cuts none.
# Each run stops short of the wall so its jacket stays out of the flight's headroom: the
# grille's 8" boot carries it through.

from typehaus import DuctRun, DuctSystem, Mount, MountKind, Register, deg, inch, pt
from typehaus.model import Location, WallAttachment

_INSULATION = '1 1/2" fibreglass flex jacket, R-6, vapour-sealed (Rheem AP22654 p.15)'

DUCTS_HPWH_AIR = [
    # Top inlet: warm air off the stair, high. From the adapter up into the kit elbow, then
    # north under the rake and east through the 321"..335 1/2" bay.
    DuctRun(uid="T2SF2058ME", tag="DU-B-WH-IN", system=DuctSystem.TRANSFER,
            path=(pt(inch(159.1), inch(317.9)), pt(inch(159.1), inch(317.9)),
                  pt(inch(159.1), inch(326.25)), pt(inch(164.5), inch(326.25))),
            diameter=inch(8), material="flex", insulation=_INSULATION,
            elevations=(inch(74.1875), inch(81), inch(81), inch(81))),
    # Side exhaust: faces west at about 63" (scaled), so it wraps the tank's north side at
    # that height and goes through the 337 3/4"..351 1/4" bay, 18" from the inlet.
    DuctRun(uid="2XHERX8QJG", tag="DU-B-WH-OUT", system=DuctSystem.TRANSFER,
            path=(pt(inch(141.5), inch(320.375)), pt(inch(136), inch(320.375)),
                  pt(inch(136), inch(344.5)), pt(inch(164.5), inch(344.5))),
            diameter=inch(8), material="flex", insulation=_INSULATION,
            elevations=(inch(63), inch(63), inch(63), inch(63))),
]

REGISTERS_HPWH_AIR = [
    # Warm air high, cold exhaust below it and above the handrail: the exhaust falls away
    # from the intake down the stair (Rheem p.15, reduce recirculation).
    Register(uid="1MZ9EB5VTZ", tag="REG-B-WH-IN", kind=DuctSystem.TRANSFER, room="RM-B-STAIR",
             type_ref="REG-T-HPWH-STAIR-1210", duct_ref="DU-B-WH-IN",
             mount=Mount(kind=MountKind.WALL, elevation=inch(85)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-B-WELL", face="right", distance_from_start=inch(22.25),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    Register(uid="V4Q2XAQCNS", tag="REG-B-WH-OUT", kind=DuctSystem.TRANSFER, room="RM-B-STAIR",
             type_ref="REG-T-HPWH-STAIR-1210", duct_ref="DU-B-WH-OUT",
             mount=Mount(kind=MountKind.WALL, elevation=inch(69)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-B-WELL", face="right", distance_from_start=inch(38.5),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
]
