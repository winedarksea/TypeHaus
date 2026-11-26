# haus: editable
# Catlin MEP — air terminals on the basement. plan/mep.py re-exports the lists below
# (AGENTS.md §1.1); the ERV terminals' flows are named in plan/erv_balance.py.

from typehaus import (
    DuctSystem,
    Mount,
    MountKind,
    Register,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import Location, WallAttachment

from .erv_balance import (
    REG_B_EXH1,
    REG_B_EXH2,
    REG_B_RET1,
    REG_B_SUP1,
    REG_B_SUP2,
    REG_B_SUP3,
)

# Basement ERV terminals are sidewall valves (both supplies and the bath extract), the sauna's
# two wood vents and the workshop's bench valve.
REGISTERS_BASEMENT = [
    # ** BOTH BASEMENT SUPPLIES ARE SIDEWALL VALVES ON THE x=18' LINE (2026-11-10). ** A ceiling
    # collar takes its run from above on a stock 90, and under FS-M-EAST/-NE that meant an
    # exposed gym leg and a climb over W-B-CN2's plate. Each run now ends in a stud bay of the
    # wall it crossed, the valve on the room face, centred on the duct.
    #
    # REG-B-SUP1: W-B-CS3's gym face at y=11'-3 1/2", in the 128"..144" stud bay under the
    # plates, where DU-B-ERV-R-GYM comes through over the bath ceiling (2026-11-25; it sat on
    # D-B-GYM's king before). 10 cfm since 2026-11-03: 8 went to the sauna's supply (REG-B-SUP3).
    Register(uid="CBRV01AAAA", tag="REG-B-SUP1", kind=DuctSystem.SUPPLY, room="RM-B-GYM",
            duct_ref="DU-B-ERV-R-GYM",
            type_ref="REG-T-ERV-VALVE-SUP-WALL", design_cfm=REG_B_SUP1,
            mount=Mount(kind=MountKind.WALL, elevation=inch(86.84375)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-B-CS3", face="left", distance_from_start=inch(20.5),
                normal_gap=inch(0), rotation_offset=deg(-180)))),
    # RM-B-PLAY-N is 324 sf of windowless habitable MEDIA space, legal only under R303.1
    # Exception 1, whose second half requires outdoor air supplied to *the room* — an
    # adjacent room's grille doesn't satisfy it. **Deleting this terminal is a hard
    # code.R303_1_light_and_ventilation FAIL.**
    #
    # W-B-CN2's theater face at y=20'-6", in the 240"..256" stud bay. The face centre sits
    # 5/16" under DU-B-ERV-R-PLAY's 90 3/4" (the 4" duct stays inside the 5" increaser) so
    # the increaser clears the plates (93"). It
    # throws east across the room, away from nothing: FURN-B-PLAY-TV is on the east wall.
    # Mount elevations here are off the finished floor, 3/4" over the slab datum.
    Register(uid="CBRV02AAAA", tag="REG-B-SUP2", kind=DuctSystem.SUPPLY, room="RM-B-PLAY-N",
            duct_ref="DU-B-ERV-R-PLAY",
            type_ref="REG-T-ERV-VALVE-SUP-125-WALL", design_cfm=REG_B_SUP2,
            mount=Mount(kind=MountKind.WALL, elevation=inch(86.5)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-B-CN2", face="right", distance_from_start=inch(30),
                normal_gap=inch(0), rotation_offset=deg(0)))),
    # The workshop's bench pickup (2026-11-15): a stock 100 mm extract valve, face down at
    # 46" AFF (12" over the 34" bench tops), 3" off W-B-W2's concrete, 9" south of the bench
    # seam where ED-B-WORKSHOP-DATA1 and CD-B-DATA-SHOP come down. It is
    # a near-source extract, not a fume hood: at 6 cfm it captures nothing beyond a few
    # inches. Solder fume is APPL-B-WORKSHOP-FUME (benchtop carbon extractor). RETURN, so the
    # heat is recovered.
    Register(uid="CBRV03AAAA", tag="REG-B-RET1", kind=DuctSystem.RETURN, room="RM-B-WORKSHOP",
            position=pt(inch(11), ft(7, 9)), duct_ref="DU-B-ERV-R-BENCH",
            type_ref="REG-T-ERV-VALVE-EXH", design_cfm=REG_B_RET1,
            mount=Mount(kind=MountKind.CEILING, elevation=inch(46))),
    # The sauna's stale pickup is on the wall, 4" above the floor on the WEST liner below
    # FURN-B-SAUNA-UPPER; its inset posts keep the register face clear. The former south
    # face rotated on 2026-09-05 and
    # EQ-B-SAUNA-HTR took that wall: a sauna stratifies hard, so the low pickup pulls
    # the cold spent
    # layer off the floor rather than the löyly at bench height. Paired with REG-B-SUP3 over
    # the heater, both ends closeable wood vents (REG-T-SAUNA-VENT-*), it drives the room's convection
    # loop — down the far wall, across the floor, out under the bench. EXHAUST at 20 cfm:
    # the room is Occupancy.BATHROOM and its window's openable area (1.2 sf) falls short of
    # R303.3's 1.5 sf, so mechanical exhaust governs.
    Register(uid="CBRV04AAAA", tag="REG-B-EXH2", kind=DuctSystem.EXHAUST, room="RM-B-SAUNA",
            duct_ref="DU-B-ERV-R-SAUNA-EXH",
            type_ref="REG-T-SAUNA-VENT-EXH", design_cfm=REG_B_EXH2,
            mount=Mount(kind=MountKind.WALL, elevation=inch(4), recessed_into_host_surface=True),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-B-SA-W", face="right", distance_from_start=inch(38),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    # Fresh air in high, over the stones: a ceiling hatch on EQ-B-SAUNA-HTR's centre (the
    # east liner), Harvia's inlet-near-heater layout restored with the bath replan
    # (2026-11-25). DU-B-ERV-R-SAUNA-SUP drops 10 3/4" to it through the service cavity.
    # 38 cfm, balancing REG-B-EXH2 behind the sealed sauna door (notes/erv_static_budget.md
    # §10.30).
    Register(uid="CBRV06AAAA", tag="REG-B-SUP3", kind=DuctSystem.SUPPLY, room="RM-B-SAUNA",
            position=pt(inch(199.75), inch(20.5)), duct_ref="DU-B-ERV-R-SAUNA-SUP",
            type_ref="REG-T-SAUNA-VENT-SUP", design_cfm=REG_B_SUP3,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(7))),
    # RM-B-BATH. Filed as EXHAUST rather than RETURN, like RM-S-BATH1's terminal and unlike
    # the basement's other two stale pickups: a bathroom's air is pulled and not
    # recirculated. A ceiling disc valve 9" outside FX-B-BATH-SH's front, at the source
    # (2026-11-25, the bath north of the sauna); DU-B-ERV-R-BATH drops to it from above.
    Register(uid="CBRV05AAAA", tag="REG-B-EXH1", kind=DuctSystem.EXHAUST, room="RM-B-BATH",
            position=pt(inch(128), inch(145)), duct_ref="DU-B-ERV-R-BATH",
            type_ref="REG-T-ERV-VALVE-EXH", design_cfm=REG_B_EXH1,
            mount=Mount(kind=MountKind.CEILING)),
]
