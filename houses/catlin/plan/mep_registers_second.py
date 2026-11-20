# haus: editable
# Catlin MEP — air terminals on the second storey. plan/mep.py re-exports the lists below
# (AGENTS.md §1.1); the ERV terminals' flows are named in plan/erv_balance.py.
#
# Three families, and the difference matters on the plan set: REG-T-ERV-* are ventilation
# terminals on EQ-B-ERV's balanced trunks; REG-T-HP-* are System 1's conditioned-air terminals;
# REG-T-TRANSFER-* is the passive one — a louver between two rooms, on no trunk at all, and the
# only register here with no `duct_ref`. Their types and the ducts they sit on are in
# plan/mep_hvac.py.
#
# ================ SYSTEM 1 HAS THREE RETURNS; THE REST GO UNDER DOORS ================
#
# REG-S-HP-RET is the hall return; RM-S-SUITE has its own ducted REG-S-HP-SUITE-RET behind a
# sealed door (2026-11-09) and RM-S-BED3 its REG-S-HP-BED3-RET (2026-11-11). Every other
# System 1 terminal below is a supply, and the ERV takes no air from the bedrooms (the
# BED1/BED2 5 cfm tokens were deleted 2026-11-20). So a room's air gets back to the
# machine UNDER ITS DOOR. Since 2026-11-06 an undercut stays in 1/2"-3/4" (owner: stock
# prehungs cut on site), so the relief doors hang at 3/4" and still fall short: a bedroom's
# 80 cfm net through 22.5 in2 is 9.7 Pa against Manual D's 3 Pa. mep.door_transfer_air grades
# it; relief for the bedrooms is open. D-S-PLANT is a sealed steel door since 2026-11-12:
# RM-S-PLANT takes no System 1 air and vents to Study 2 through its own transfer pair.
# Arithmetic and history: notes/system1_return_path.md.

from typehaus import (
    DuctSystem,
    Mount,
    MountKind,
    Register,
    RoughOpening,
    from_node,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import Location, WallAttachment

from .erv_balance import (
    REG_S_EXH1,
    REG_S_EXH3,
)

# Terminals off the chase name their drawn branch in `duct_ref`. Until 2026-09-23 the bedroom
# grilles named the trunk through an unmodelled boot that could not have been built: ceiling
# grilles on or beside a joist, 1 3/8" into the hall wall.
#
# BED1 and BED2 are HIGH SIDEWALL grilles on W-S-BW1/2's bedroom face (22'-1 3/8"), at the end
# of a side collar straight off the trunk — REG-S-HP-STAIR's type, rotation and derivation:
# x is the face plus half the 1" body. The face's bottom is 97 1/8" storey, a 6" face centred
# on the trunk's 100 1/8"; a WALL mount is measured off the finished floor, so it is authored
# 95 7/8" over the carpet's 1 1/4". They throw east across the room, over the desk below.
# Both are now over the PAX frame (plan/bedroom_wardrobes.py), whose top is 93 3/8" over the
# carpet: 2 1/2" under the grille face. The throw clears it; nothing grades it. BED2/BED3 sit
# 3/4" lower with their collars (2026-11-09, the suite return's lane): 1 3/4" over BED2's PAX.
#
# NOTHING GRADES A REGISTER AGAINST ITS HOST SURFACE — a Register resolves no solid, so
# `Mount.elevation` is a number the schedule and the sections print and no check reads.
#
# RM-S-SUITE's 100 cfm terminal is a high sidewall grille on W-S-C2B, directly above
# D-S-SUITE and aimed west into the sleeping room. It matches the bedroom side-collar pattern:
# a wall attachment, the same 12x6 double-deflection type and mount elevation, and since
# 2026-11-16 the same 6" round ending on a straight 12x6x6 register box behind the grille. The loft's 75
# cfm boot has its own run off the trunk's crown (DU-S-HP-WEST-BOOT).
REGISTERS_HVAC_SECOND = [
    Register(uid="CSRH01AAAA", tag="REG-S-HP-BED1", kind=DuctSystem.SUPPLY, room="RM-S-BED1",
             duct_ref="DU-S-HP-BED1", type_ref="REG-T-HP-SIDE-1206", design_cfm=80,
             mount=Mount(kind=MountKind.WALL, elevation=inch(95)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-S-BW1", face="right", distance_from_start=inch(40),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    Register(uid="CSRH02AAAA", tag="REG-S-HP-BED2", kind=DuctSystem.SUPPLY, room="RM-S-BED2",
             duct_ref="DU-S-HP-BED2", type_ref="REG-T-HP-SIDE-1206", design_cfm=80,
             mount=Mount(kind=MountKind.WALL, elevation=inch(94.25)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-S-BW2", face="right", distance_from_start=inch(24),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    # Above D-S-BED3's header, with the collar north of its south king; the straight
    # branch passes south of the return plenum (see mep_hvac_branches.py).
    Register(uid="CSRH03AAAA", tag="REG-S-HP-BED3", kind=DuctSystem.SUPPLY, room="RM-S-BED3",
             duct_ref="DU-S-HP-BED3", type_ref="REG-T-HP-SIDE-1206", design_cfm=80,
             mount=Mount(kind=MountKind.WALL, elevation=inch(94.25)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-S-BW3", face="right", distance_from_start=inch(12.75),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    # West-facing 50 cfm stair/landing supply. The separate 4in branch ends at the
    # dimensioned inlet of TH-HP-STAIR-BOX-01, rather than an implicit gap to the trunk.
    # The collar sits 1.5in above the trunk centre and fits fully within its 8in height.
    # Box, framing clearance and seals: notes/stair_supply_connection.md.
    Register(uid="CSRH04AAAA", tag="REG-S-HP-STAIR", kind=DuctSystem.SUPPLY, room="RM-S-HALL",
             position=pt(inch(218.76), inch(282.625)), duct_ref="DU-S-HP-STAIR", rotation=deg(90),
             type_ref="REG-T-HP-STAIR-SIDE", design_cfm=50,
             mount=Mount(kind=MountKind.WALL, elevation=inch(96.25))),
    # The suite's high sidewall supply over D-S-SUITE, throwing west into RM-S-SUITE: a Sun Gold
    # Reggio Chevron since 2026-11-19. Its mount elevation matches the bedroom side collars.
    # The W-S-C2B station is y=14'-8 7/8", 7" north of the door centre, in the clear cripple bay its branch ends in (2026-10-31).
    # `face="left"` is the suite side of this north-running wall.
    Register(uid="CSRH06AAAA", tag="REG-S-HP-SUITE", kind=DuctSystem.SUPPLY, room="RM-S-SUITE",
             duct_ref="DU-S-HP-SUITE", type_ref="REG-T-HP-SUITE-CHEVRON", design_cfm=100,
             mount=Mount(kind=MountKind.WALL, elevation=inch(95)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-S-C2B", face="left", distance_from_start=inch(27.875),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    # East face of the wall-width SF-S-DUCT (260 3/4"), throwing across the study.
    # The 8x6 grille and its 6" boot clear the ladder rails at a 99 1/8" centreline;
    # y=4'-10 5/8" is the centre of the ladder bay between the 50 5/8" and 66 5/8" studs,
    # 19" clear of the south grille's collar (2026-11-15).
    # Centre the 1" body 1/2" east of the lining so its back bears on the face.
    # Mount height is above the finished floor: 99 1/8 - 3 - 1 1/2 = 94 5/8".
    # See notes/system1_study_supply.md for grille selection and vane setting.
    Register(uid="DMVENAN0DW", tag="REG-S-HP-STUDY2", kind=DuctSystem.SUPPLY, room="RM-S-STUDY2",
             position=pt(inch(261.25), inch(58.625)), rotation=deg(90),
             duct_ref="DU-S-HP-STUDY2", type_ref="REG-T-HP-STUDY-SIDE", design_cfm=75,
             mount=Mount(kind=MountKind.WALL, elevation=inch(93.75))),
    # Study 2's second 75 cfm grille (2026-11-12, replacing the plant room's supply): the
    # SOUTH end face of SF-S-DUCT (y=2'-10"), same 8x6 double-deflection type as the east
    # one, ~34" off the south wall. A glass wash: vanes spread east-west and aimed up, never
    # straight at D-S-BALCONY's glass; its jet runs parallel to W-S-C1 past D-S-PLANT, which
    # is what makes the plant room's open-door fallback work. Body centred 1/2" off the
    # lining as at REG-S-HP-STUDY2. notes/system1_study_supply.md.
    Register(uid="QWCKXAS4SM", tag="REG-S-HP-STUDY2-S", kind=DuctSystem.SUPPLY, room="RM-S-STUDY2",
             position=pt(inch(249), inch(33.5)), rotation=deg(0),
             duct_ref="DU-S-HP-STUDY2-S", type_ref="REG-T-HP-STUDY-SIDE", design_cfm=75,
             mount=Mount(kind=MountKind.WALL, elevation=inch(93.75))),
    # THE HALL RETURN: a 24 x 12 filter-back grille (stock 12x24x1) in SF-S-DUCT's underside at
    # the hall's north end (AO-S-DUCT-RET), its boot rising through the soffit's open top into
    # DU-S-HP-RET in FS-ATTIC's y 352-368 bay (2026-11-11; it was in SF-S-HP1's underside,
    # opening into EQ-S-ERV-MIX). In the hall, not the closet: IMC 601.5(7) forbids return
    # air from a closet (MN adopts the IMC). 288 in2 at 455 cfm is 228 fpm, inside Manual D
    # SS4-10's 300 for a grille carrying the filter. The air handler moves 750: the ERV's 92,
    # RM-S-SUITE's 80, RM-S-BED3's 80 and RM-A-EAST-UNFIN's 35 join in EQ-S-ERV-MIX.
    #
    # 92 1/2" is SF-S-DUCT's 94" underside off the hall's 1 1/2" oak floor, hand-coupled.
    Register(uid="CSRH05AAAA", tag="REG-S-HP-RET", kind=DuctSystem.RETURN,
             room="RM-S-HALL",
             position=pt(inch(239), inch(359.5)), duct_ref="DU-S-HP-RET",
             type_ref="REG-T-HP-RET-FILTER", design_cfm=455,
             mount=Mount(kind=MountKind.CEILING, elevation=inch(92.5))),
    # RM-S-SUITE's ducted return (2026-11-09): a 12x12 filter-back ceiling grille between two
    # FS-ATTIC joists, clear of the W-S-SBS/W-S-DC2 corner, the bed and CAN3. Its own MERV 13
    # filter, because it enters the plenum behind REG-S-HP-RET's; a locked balancing damper
    # at the boot, set to 80 cfm through the hinged face. With D-S-SUITE sealed the suite's
    # pressure follows that damper and the hall filter's loading: re-check at filter changes.
    Register(uid="1G7M6SM0ND", tag="REG-S-HP-SUITE-RET", kind=DuctSystem.RETURN, room="RM-S-SUITE",
             position=pt(inch(104), inch(184)), duct_ref="DU-S-HP-SUITE-RET",
             type_ref="REG-T-HP-RET-FILTER-1212", design_cfm=80,
             mount=Mount(kind=MountKind.CEILING)),
    # RM-S-BED3's return (2026-11-11): the suite's 12x12 filter-back ceiling grille, 6'-7" from
    # REG-S-HP-BED3, clear of the bed and desk, rising to EQ-S-ERV-MIX on the attic deck.
    # Damper locked at 80 cfm; re-check at filter changes. D-S-BED3: stock 1/2".
    Register(uid="M9R1FECSXZ", tag="REG-S-HP-BED3-RET", kind=DuctSystem.RETURN, room="RM-S-BED3",
             position=pt(inch(317.5), inch(392)), duct_ref="DU-S-HP-BED3-RET",
             type_ref="REG-T-HP-RET-FILTER-1212", design_cfm=80,
             mount=Mount(kind=MountKind.CEILING)),
]

# CONDENSATE — the indoor heads gravity-drain through PR-M-COND-HEADS / PR-B-COND to an air
# gap over FX-B-SAUNA-FD; the ERV and water heater drain to FX-B-UTIL-SINK
# (plan/mep_drainage.py).

# Every register here drops into a boot in the second floor's joist bay (FS-S-EAST's
# I-joists for the three east bedroom boots at x=29'; FS-S-WEST's open-web trusses for the
# suite's REG-S-RET2 at x=9'), flush with the finished floor — the type's 1" height is the
# frame below it, not a kerb on top, so it still counts against a neighbour's clear floor
# space.
#
# The second storey has no ERV supply: fresh air reaches the bedrooms through System 1
# (REG-S-HP-BED1/2/3, REG-S-HP-SUITE; REGISTERS_HVAC_SECOND above), interlocked to the ERV.
# The bedroom extract pickups were deleted 2026-11-20 (5 cfm tokens): the rooms return under
# their doors, and the stair-top pickup REG-A-RET-STAIR takes the hall's stale air.
#
# RM-S-STUDY2 is served by two System 1 grilles on SF-S-DUCT (east and south faces), both
# off DU-S-HP-SOUTH. RM-S-PLANT is sealed: no supply, no extract (notes/plant_room.md).
REGISTERS = [
    # No REG-S-RET2 (the suite's own extract): RM-S-SUITEBATH's REG-S-EXH3 carries the suite
    # through the door undercut. The suite keeps its System 1 supply REG-S-HP-SUITE.
]

REGISTERS_SECOND = [
    # High on the west wall: the former floor boot was in the lavatory's splash area.
    # The 16'-4" station is south of the robe-peg backing, between the corner and
    # first staggered stud. The taller boot stays below the double top plate.
    Register(uid="CSRV03AAAA", tag="REG-S-EXH3", kind=DuctSystem.EXHAUST, room="RM-S-SUITEBATH",
            duct_ref="DU-M-ERV-R-SUITEBATH",
            type_ref="REG-T-ERV-SUITEBATH-WALL", design_cfm=REG_S_EXH3,
            mount=Mount(kind=MountKind.WALL, elevation=inch(95.75)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-S-DC2", face="right", distance_from_start=inch(5),
                normal_gap=inch(0), rotation_offset=deg(0)))),
    Register(uid="CSRV05AAAA", tag="REG-S-EXH1", kind=DuctSystem.EXHAUST, room="RM-S-BATH1",
            # Under its deck leg's end (2026-11-10): one stock 90 down onto the collar.
            position=pt(ft(5, 7.5), ft(32, 8)), duct_ref="DU-A-ERV-R-BATH1",
            type_ref="REG-T-ERV-VALVE-EXH", design_cfm=REG_S_EXH1,
            mount=Mount(kind=MountKind.CEILING), rotation=deg(90)),
    # D-S-BATH1 is sealed (2026-11-03), so REG-S-EXH1's 20 cfm makes up through an offset
    # pair in W-S-BD-N's west bay (x 8"..15 1/4"), lined, insulation out: high on the bath
    # face above the SEKTION rail backing, lower on the vanity face over the mirror arches.
    # notes/system1_return_path.md, "Sealed doors".
    Register(uid="WRHS831M9S", tag="REG-S-XFER-BATH1", kind=DuctSystem.TRANSFER, room="RM-S-BATH1",
            type_ref="REG-T-TRANSFER-0606",
            mount=Mount(kind=MountKind.WALL, elevation=inch(95.375)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-S-BD-N", face="left", distance_from_start=inch(11.625),
                normal_gap=inch(0), rotation_offset=deg(-180)))),
    Register(uid="XX9YQFJ8PT", tag="REG-S-XFER-VANITY", kind=DuctSystem.TRANSFER, room="RM-S-VANITY",
            type_ref="REG-T-TRANSFER-0606",
            mount=Mount(kind=MountKind.WALL, elevation=inch(82)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-S-BD-N", face="right", distance_from_start=inch(11.625),
                normal_gap=inch(0), rotation_offset=deg(0)))),
]


# RM-S-PLANT's only ventilation (2026-11-12): a manually set high/low transfer pair into
# Study 2 through W-S-C1, both in the clear bay y 64 3/4".."79 1/4" (studs at 64"/80", no
# stud cut). The study face is under SF-S-DUCT from y=2'-10" (94" underside), so the high
# sleeve tops out at 90 1/2"; the low one's grille bottom is 8 1/4" over the plant floor,
# above the base and any spill. The plant face's OBD is the humidity control: open on RH
# over 75%, close under 60% (notes/plant_room_moisture_budget.md §4, notes/plant_room.md).
# Mount is the face bottom above each room's finished floor (plant +1 1/8", study +1 1/2").
PLANT_TRANSFER_SECOND = [
    Register(uid="1GPW7J2XP7", tag="REG-S-XFER-PLANT-HI", kind=DuctSystem.TRANSFER, room="RM-S-PLANT",
             type_ref="REG-T-XFER-PLANT-1006",
             mount=Mount(kind=MountKind.WALL, elevation=inch(82.255)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-S-C1", face="left", distance_from_start=inch(72),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    Register(uid="QCWNT36HQ0", tag="REG-S-XFER-PLANT-LO", kind=DuctSystem.TRANSFER, room="RM-S-PLANT",
             type_ref="REG-T-XFER-PLANT-1006",
             mount=Mount(kind=MountKind.WALL, elevation=inch(8.255)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-S-C1", face="left", distance_from_start=inch(72),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    Register(uid="KTJPQ98QXP", tag="REG-S-XFER-STUDY2-HI", kind=DuctSystem.TRANSFER, room="RM-S-STUDY2",
             type_ref="REG-T-XFER-STUDY-1006",
             mount=Mount(kind=MountKind.WALL, elevation=inch(81.875)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-S-C1", face="right", distance_from_start=inch(72),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    Register(uid="DWMQCYY0SS", tag="REG-S-XFER-STUDY2-LO", kind=DuctSystem.TRANSFER, room="RM-S-STUDY2",
             type_ref="REG-T-XFER-STUDY-1006",
             mount=Mount(kind=MountKind.WALL, elevation=inch(7.875)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-S-C1", face="right", distance_from_start=inch(72),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    # The sleeves' holes: 10 1/2 x 6 1/2 through the whole wall, sills off the storey datum.
    RoughOpening(uid="Q99PR2TFVP", tag="AO-S-XFER-PLANT-HI", host="W-S-C1",
                 position=from_node("N-S-S1", inch(66.75)),
                 width=inch(10.5), height=inch(6.5), sill_height=inch(84),
                 penetration_for=("REG-S-XFER-PLANT-HI", "REG-S-XFER-STUDY2-HI")),
    RoughOpening(uid="JC23SF4360", tag="AO-S-XFER-PLANT-LO", host="W-S-C1",
                 position=from_node("N-S-S1", inch(66.75)),
                 width=inch(10.5), height=inch(6.5), sill_height=inch(10),
                 penetration_for=("REG-S-XFER-PLANT-LO", "REG-S-XFER-STUDY2-LO")),
]
