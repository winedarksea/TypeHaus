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
# System 1 terminal below is a supply, and the ERV's BED1/BED2 pickups are stale-air tokens,
# not a return path. So a room's air gets back to the
# machine UNDER ITS DOOR. Since 2026-11-06 an undercut stays in 1/2"-3/4" (owner: stock
# prehungs cut on site), so the relief doors hang at 3/4" and still fall short: a bedroom's
# 75 cfm net through 22.5 in2 is 9.7 Pa against Manual D's 3 Pa. mep.door_transfer_air grades
# it; relief for the bedrooms is open. D-S-PLANT keeps 1/2": its room's pressure is a design
# output held by an interlocked damper.
# Arithmetic and history: notes/system1_return_path.md.

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
    REG_S_ERV_PLANT_EXH,
    REG_S_EXH1,
    REG_S_EXH3,
    REG_S_EXH4,
    REG_S_RET_BED1,
    REG_S_RET_BED2,
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
# a wall attachment and the same 12x6 double-deflection type and mount elevation.
# The 75 cfm attic boot is at the shortened DU-S-HP-SUITE's west end, 28" from its takeoff.
# Total branch airflow and the suite's old ERV supply (REG-S-SUP6) are unchanged.
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
    # The suite's high sidewall supply over D-S-SUITE, throwing west into RM-S-SUITE. Its
    # mount elevation matches the bedroom side collars. The W-S-C2B station is y=14'-8 7/8",
    # 7" north of the door centre, in the clear cripple bay its branch crosses (2026-10-31).
    # `face="left"` is the suite side of this north-running wall.
    Register(uid="CSRH06AAAA", tag="REG-S-HP-SUITE", kind=DuctSystem.SUPPLY, room="RM-S-SUITE",
             duct_ref="DU-S-HP-SUITE", type_ref="REG-T-HP-SIDE-1206", design_cfm=100,
             mount=Mount(kind=MountKind.WALL, elevation=inch(95)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-S-C2B", face="left", distance_from_start=inch(27.875),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    # East face of the wall-width SF-S-DUCT (260 3/4"), throwing across the study.
    # The 8x6 grille and its 6" boot clear the ladder rails at a 99 1/8" centreline;
    # y=3'-7 1/2" puts the full face between the end blocking and first side stud.
    # The boot tees off the soffit leg before it rises, so this room no longer
    # needs a joist-bay terminal.
    # Centre the 1" body 1/2" east of the lining so its back bears on the face.
    # Mount height is above the finished floor: 99 1/8 - 3 - 1 1/2 = 94 5/8".
    # See notes/system1_study_supply.md for grille selection and vane setting.
    Register(uid="DMVENAN0DW", tag="REG-S-HP-STUDY2", kind=DuctSystem.SUPPLY, room="RM-S-STUDY2",
             position=pt(inch(261.25), inch(43.5)), rotation=deg(90),
             duct_ref="DU-S-HP-STUDY2", type_ref="REG-T-HP-STUDY-SIDE", design_cfm=75,
             mount=Mount(kind=MountKind.WALL, elevation=inch(93.75))),
    # RM-S-PLANT's 75 cfm supply (2026-11-12): a HIGH SIDEWALL grille on W-S-C1's plant face,
    # in the clear cripple bay above D-S-PLANT's header (cripples at y=33" and 49", 14 1/2"
    # between), throwing west down the room's 17' length. It was a ceiling boot at x=14'-8"
    # with a service hatch in the humid liner. The RH-interlocked 6" 24 VAC damper rides in the
    # type's collar behind the grille, reached by pulling it; nothing is opened in the liner.
    # DU-S-HP-PLANT feeds it off DU-S-HP-SOUTH-RISE inside SF-S-DUCT; the wall's Class I
    # membrane is taped to the box flange as at REG-S-ERV-PLANT-EXH. notes/plant_supply_connection.md.
    Register(uid="CXDCYN7YQ2", tag="REG-S-HP-PLANT", kind=DuctSystem.SUPPLY, room="RM-S-PLANT",
             duct_ref="DU-S-HP-PLANT", type_ref="REG-T-HP-PLANT-SIDE", design_cfm=75,
             mount=Mount(kind=MountKind.WALL, elevation=inch(94.125)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-S-C1", face="left", distance_from_start=inch(41),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    # The plant room's extract. RM-S-PLANT was supply-only, so its own ventilation pushed
    # 70%-RH air into every crack in the envelope it is now lined to protect; slightly
    # negative is the only pressure a continuously humid room may be held at, which takes an
    # extract, not a better barrier. The ERV's stale pull, not System 1's.
    #
    # HIGH SIDEWALL, 8'-3" to its centre (face bottom 96 1/2" over the carpet), because humid air
    # stratifies: the wettest air is the air at the ceiling. 3" under the 8'-6" of the W-S-C1
    # version so the stack boot clears PS1's top plates (underside 104 3/8"). In W-S-PS1's plant
    # face at x=3'-6 1/2" (2026-11-11; it was W-S-C1 at x=18'-0", 25 ft of duct away), at the
    # end of DU-M-ERV-R-PLANT's 3 1/4 x 8 stack in the stud bay x 32 3/4".."47 1/4" (studs at 32"
    # and 48"). It is across the room from REG-S-HP-PLANT at (14'-8", 3'-3"), and its face stands 6"
    # east of FURN-S-PLANT-HANG-NW (edge x 33.8"), so the hung pot is not in the throw.
    #
    # PS1 is the 2x4 PLANT_INT_2X4_HUMID wall, 3 1/2" cavity: the stack fits (3 1/4"), a round
    # riser plus boot did not, which is why the first design used W-S-C1's 5 1/2". The boot is
    # a flanged rectangular stack boot with a 4" collar, its flange sealed to the Class I
    # membrane (butyl tape) and mastic round the stack: the vapour-tight detail is in
    # plan/mep_erv_l2.py above DU-M-ERV-R-PLANT, and the opening cut through the furring and
    # panel is the boot's own size. The valve sits on the liner, as before, 2026-10-31: the
    # collar crosses the liner, the face does not.
    Register(uid="C7LM4KAP2X", tag="REG-S-ERV-PLANT-EXH", kind=DuctSystem.EXHAUST,
             room="RM-S-PLANT", duct_ref="DU-M-ERV-R-PLANT",
             type_ref="REG-T-ERV-PLANT-EXH", design_cfm=REG_S_ERV_PLANT_EXH,
             mount=Mount(kind=MountKind.WALL, elevation=inch(96.5)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-S-PS1", face="right", distance_from_start=inch(42.5),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    # THE HALL RETURN: a 24 x 12 filter-back grille (stock 12x24x1) in SF-S-DUCT's underside at
    # the hall's north end (AO-S-DUCT-RET), its boot rising through the soffit's open top into
    # DU-S-HP-RET in FS-ATTIC's y 352-368 bay (2026-11-11; it was in SF-S-HP1's underside,
    # opening into EQ-S-ERV-MIX). In the hall, not the closet: IMC 601.5(7) forbids return
    # air from a closet (MN adopts the IMC). 288 in2 at 455 cfm is 228 fpm, inside Manual D
    # SS4-10's 300 for a grille carrying the filter. The air handler moves 750: the ERV's 100,
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
# The second storey has no supply on the ERV: the BED1/BED2 boots kept their uids (IFC
# GlobalId stability) but are stale-air pickups on DU-M-ERV-RET. Fresh air comes from
# REG-S-HP-BED1/2/3 and REG-S-HP-SUITE (REGISTERS_HVAC_SECOND above), so extracting here is
# what moves the storey's air: in at the hall soffit, out at the far wall of each room.
#
# RM-S-PLANT and RM-S-STUDY2 are served as System 1 terminals — REG-S-HP-PLANT and
# REG-S-HP-STUDY2 in REGISTERS_HVAC_SECOND above. Both take sidewall boots straight off
# DU-S-HP-SOUTH-RISE: the plant's through W-S-C1 above its door, the study's through SF-S-DUCT's east lining.
REGISTERS = [
    # BED1 y 9'-18', BED2 y 18'-27'. BED3 has no ERV pickup since 2026-11-11: it returns
    # to System 1 through REG-S-HP-BED3-RET instead, and its old 5 cfm went to the kitchen.
    #
    # BED1/BED2 ARE FLOOR BOOTS (2026-10-02), not mid-floor at x=29'. BED2's is against the south
    # wall of its room; BED1's moved from y=9'-9" to y=16'-8", the north side of RM-S-BED1
    # (2026-11-11), when its radial became a branch off BED2's x=16'-1 3/4" crossing: clear of the
    # y=17'-4" joist line, inside the room (y<17'-5"), ~4'-11" west of FURN-S-DESK-CHAIR1.
    # x=28'-1" leaves 5 1/8" from the east PAX frame to the grille's west edge (2026-10-03).
    # It is the open floor between the expanded SW PAX run (to 27'-4 3/8") and the bed's west
    # side (~29'-11"); y is the FS-S-EAST bay beside the wall (I-joists span x, so the
    # boot cannot leave its bay). A low sidewall grille was rejected: the south walls are
    # INT_2X4_RC, whose 3 1/2" cavity takes no 4" riser without a shop-made stack.
    Register(uid="CMR903AAAA", tag="REG-S-RET-BED1", kind=DuctSystem.RETURN, room="RM-S-BED1",
            position=pt(ft(28, 1), ft(16, 8)), duct_ref="DU-M-ERV-R-BED1",
            type_ref="REG-T-ERV-EXH-FLOOR", design_cfm=REG_S_RET_BED1,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CMR907AAAA", tag="REG-S-RET-BED2", kind=DuctSystem.RETURN, room="RM-S-BED2",
            position=pt(ft(28, 1), ft(18, 4)), duct_ref="DU-M-ERV-R-BED2",
            type_ref="REG-T-ERV-EXH-FLOOR", design_cfm=REG_S_RET_BED2,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # No REG-S-RET2 (the suite's own extract) — the owner's call, and defensible on the
    # model too: no check fires for its absence (BEDROOM is not in
    # checks/mep/hvac.py's _STALE_OCCUPANCIES), and RM-S-SUITEBATH's REG-S-EXH3 carries the
    # suite through the door undercut. The suite KEEPS its System 1 supply REG-S-HP-SUITE.
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
    Register(uid="CSRV04AAAA", tag="REG-S-EXH4", kind=DuctSystem.EXHAUST, room="RM-S-VANITY",
            # Turned 90 (2026-11-08): long axis north-south, clear of the flat trunk (x<=31")
            # and DU-M-ERV-R-LIVING's x=40 1/2" lane.
            position=pt(ft(3), ft(24, 8)), rotation=deg(90), duct_ref="DU-M-ERV-R-VANITY",
            type_ref="REG-T-ERV-EXH-FLOOR", design_cfm=REG_S_EXH4,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
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
