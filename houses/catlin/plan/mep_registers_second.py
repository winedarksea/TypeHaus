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
# ================== SYSTEM 1 HAS ONE RETURN, AND SIX DOORS ARE IT ==================
#
# REG-S-HP-RET is the only return, it is in RM-S-HALL, every other System 1 terminal below is
# a supply, and the ERV's bedroom pickups are stale-air tokens, not a return path. So a
# room's air gets back to the machine UNDER ITS DOOR. Since 2026-11-06 an undercut stays in
# 1/2"-3/4" (owner: stock prehungs cut on site), so the relief doors hang at 3/4" and still
# fall short: a bedroom's 75 cfm net through 22.5 in2 is 9.7 Pa against Manual D's 3 Pa.
# mep.door_transfer_air grades it; the 1 1/4"-1 3/4" undercuts once named here are withdrawn
# and the fix (transfer grilles, jump ducts or a return) is open. D-S-PLANT keeps 1/2": its
# room's pressure is a design output held by an interlocked damper.
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
    REG_S_RET_BED3,
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
# carpet: 2 1/2" under the grille face. The throw clears it; nothing grades it.
#
# BED3 is a ceiling boot at its bay leg's end, at the room's resolved ceiling, 8'-10 1/4".
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
             mount=Mount(kind=MountKind.WALL, elevation=inch(95)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-S-BW2", face="right", distance_from_start=inch(24),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    # Above D-S-BED3's header, with the collar north of its south king; the straight
    # branch passes south of the return plenum (see mep_hvac_branches.py).
    Register(uid="CSRH03AAAA", tag="REG-S-HP-BED3", kind=DuctSystem.SUPPLY, room="RM-S-BED3",
             duct_ref="DU-S-HP-BED3", type_ref="REG-T-HP-SIDE-1206", design_cfm=80,
             mount=Mount(kind=MountKind.WALL, elevation=inch(95)),
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
    # East-window supply, 75 cfm with RH-interlocked isolation. The complete rectangular
    # assembly and raised feed are dimensioned in notes/plant_supply_connection.md.
    # Westward vane setting distributes air across the planting; window wash is unverified.
    Register(uid="CXDCYN7YQ2", tag="REG-S-HP-PLANT", kind=DuctSystem.SUPPLY, room="RM-S-PLANT",
             position=pt(ft(14, 8), ft(3, 3)), duct_ref="DU-S-HP-SOUTH",
             type_ref="REG-T-HP-CEIL-DAMPERED", design_cfm=75,
             mount=Mount(kind=MountKind.CEILING)),
    # The plant room's extract. RM-S-PLANT was supply-only, so its own ventilation pushed
    # 70%-RH air into every crack in the envelope it is now lined to protect; slightly
    # negative is the only pressure a continuously humid room may be held at, which takes an
    # extract, not a better barrier.
    #
    # At (14'-0", 4'-8"): the far east end of the room, 7'-5" from the supply and across
    # the room from it, so conditioned air lands on the south glass, crosses the planting
    # and leaves at the far end rather than short-circuiting. Ceiling at 9'-0" because
    # humid air stratifies — the wettest air in the room is the air at the ceiling, which is
    # also the air directly under FS-ATTIC's I-joists. Repointed onto the ERV: the plant
    # extract is not System 1's, it is the ERV's stale pull.
    #
    # HIGH SIDEWALL, not ceiling: its radial runs off the attic manifold down into
    # FS-S-WEST's open-web trusses (DU-M-ERV-R-PLANT), putting the duct BELOW this room
    # instead of above it — but the stratification argument does not care whether the boot
    # comes from above or from the side, only that the terminal is in the warm wet air at
    # the top of the room. 8'-6" is six inches under the 9'-0" ceiling.
    #
    # In W-S-C1 because that wall is PLANT_INT_2X6_BRG_HUMID — 5 1/2" of cavity, which takes a
    # 75 mm riser and a vapour-tight boot through the Class I liner. The room's north wall
    # W-S-PS1 is 2x4 and would take the duct but not the boot.
    #
    # x=17'-7" is that wall's room-side pvc-panel face (17'-7.96") plus the same ~1" inboard
    # offset the electrical devices carry, NOT the wall axis at 18'-0". Authored on the axis it
    # resolves with its footprint centre outside the room and
    # `integrity.placeable_room_mismatch` says so. (REG-A-STUBATH-EXH and ED-A-POCKET-SW still
    # carry that UNKNOWN and want the same treatment.) The duct's riser is still on the axis,
    # inside the stud cavity; the boot is the 5" of horizontal that crosses the liner.
    #
    # Approximately 5' from the supply at (14'-8", 3'-3"). Supply blades aim west;
    # whole-room throw and short-circuit performance remain commissioning checks.
    Register(uid="C7LM4KAP2X", tag="REG-S-ERV-PLANT-EXH", kind=DuctSystem.EXHAUST,
             # y=7'-4" is a truss bay centre and a stud bay centre at once; y=4'-8" would
             # put the riser inside D-S-PLANT's rough opening — 78 1/2" of bare duct standing
             # in the doorway and a bore through the 2-ply 2x8 header (see mep_erv_l2.py) — with
             # no legal riser station in that opening.
             room="RM-S-PLANT", duct_ref="DU-M-ERV-R-PLANT",
             type_ref="REG-T-ERV-PLANT-EXH", design_cfm=REG_S_ERV_PLANT_EXH,
             # A surface disc valve on the liner since 2026-10-31: the collar crosses the
             # liner, the face does not (it was a ceiling-style face let 2" into the wall).
             mount=Mount(kind=MountKind.WALL, elevation=inch(98.75)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-S-C1", face="left", distance_from_start=inch(88),
                 normal_gap=inch(0), rotation_offset=deg(0)))),
    # THE ONE RETURN, and since 2026-09-04 it opens into a BOX rather than into three
    # things at once. It is a filter-back grille in SF-S-HP1's underside at (20'-11 1/2",
    # 29'-1 1/4"), wholly inside EQ-S-ERV-MIX — the return plenum that fills the box's east
    # lane south of the cabinet — where the ERV's 100 cfm of fresh air enters through its own
    # 6" drop and damper. Room air and outdoor air mix across 29" of plenum, then leave
    # north up DU-S-HP-RET to the coil. Upstream of the coil and of EQ-S-HP1-STRIP, which
    # sits south of the cabinet in the discharge.
    #
    # ** WHAT IT WAS, AND WHY IT MOVED. ** A 30 x 16 face at (20'-9", 29'-0"): 240 in2 of it
    # opened into DU-S-HP-RET, 120 in2 into the old 10 x 12 mixing box, and 120 in2 into bare
    # soffit cavity. A return drawing a quarter of its face out of a framed ceiling cavity is
    # IMC 601.5's building-cavity-as-plenum, and no check in this engine looks for it.
    #
    # ** `rotation=deg(90)` IS STILL REQUIRED. ** REG-T-HP-RET is catalogued 28 x 12; turned,
    # it is 12 (x) x 28 (y), which is the plenum's own 12" east lane. Unrotated it would run
    # 28" straight through the box lining.
    #
    # ** IT IS IN THE HALL, AND THAT IS ** IMC 601.5(7) **, NOT A PREFERENCE. ** MN adopts the
    # IMC (Minn. R. 1309.0010 deletes IRC ch. 12-24), and 601.5(7) forbids taking return air
    # from a closet. The face runs y 27'-11 1/4"..30'-3 1/4", clear of W-S-CLN-S's hall face
    # at 30'-7 5/8" by 4 3/8". The same rule is why the closet's ceiling access panel is
    # gasketed: an open lid over this cavity would be a closet return by another name.
    #
    # ** design_cfm IS 650, NOT 750, AND THE 100 IS NOT LOST. ** The air handler moves 750;
    # the ERV puts 100 of that into the plenum through DU-S-ERV-HP-FEED, so the ROOM air
    # this grille draws is 650. Authoring 750 here double-counted the ERV's share. 336 in2
    # at 650 cfm is 279 fpm, inside Manual D SS4-10's 300 for a grille carrying the filter.
    #
    # ** THE ELEVATION IS HAND-COUPLED AND UNCHECKED. ** 7'-1" is SF-S-HP1's finished
    # underside (23" drop, storeys/second.py), not SF-S-DUCT's 7'-10". Change the drop and
    # this number must be changed with it, or the grille sits inside the box and nothing
    # says so. It has happened once: the drop went 21" -> 23" on 2026-09-18 to find room
    # for the air handler's emergency drain pan, and this line followed it by hand.
    Register(uid="CSRH05AAAA", tag="REG-S-HP-RET", kind=DuctSystem.RETURN,
             room="RM-S-HALL", rotation=deg(90),
             position=pt(inch(251.5), inch(350.25)), duct_ref="DU-S-HP-RET",
             type_ref="REG-T-HP-RET-FILTER", design_cfm=650,
             mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 1))),
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
# The second storey has no supply on the ERV: the three bedroom boots kept their uids (IFC
# GlobalId stability) but are stale-air pickups on DU-M-ERV-RET. Fresh air comes from
# REG-S-HP-BED1/2/3 and REG-S-HP-SUITE (REGISTERS_HVAC_SECOND above), so extracting here is
# what moves the storey's air: in at the hall soffit, out at the far wall of each room.
#
# RM-S-PLANT and RM-S-STUDY2 are served as System 1 terminals — REG-S-HP-PLANT and
# REG-S-HP-STUDY2 in REGISTERS_HVAC_SECOND above. The plant takes a ceiling boot
# from DU-S-HP-SOUTH; the study takes a sidewall boot off DU-S-HP-SOUTH-RISE.
REGISTERS = [
    # One per bedroom: BED1 y 9'-18', BED2 y 18'-27', BED3 y 27'-36'.
    #
    # BED1/BED2 ARE FLOOR BOOTS AGAINST THE SOUTH WALL (2026-10-02), not mid-floor at x=29'.
    # x=28'-1" leaves 5 1/8" from the east PAX frame to the grille's west edge (2026-10-03).
    # It is the open floor between the expanded SW PAX run (to 27'-4 3/8") and the bed's west
    # side (~29'-11"); y is the FS-S-EAST bay beside the south wall (I-joists span x, so the
    # boot cannot leave its bay). A low sidewall grille was rejected: the south walls are
    # INT_2X4_RC, whose 3 1/2" cavity takes no 4" riser without a shop-made stack.
    Register(uid="CMR903AAAA", tag="REG-S-RET-BED1", kind=DuctSystem.RETURN, room="RM-S-BED1",
            position=pt(ft(28, 1), ft(9, 9)), duct_ref="DU-M-ERV-R-BED1",
            type_ref="REG-T-ERV-EXH-FLOOR", design_cfm=REG_S_RET_BED1,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CMR907AAAA", tag="REG-S-RET-BED2", kind=DuctSystem.RETURN, room="RM-S-BED2",
            position=pt(ft(28, 1), ft(18, 4)), duct_ref="DU-M-ERV-R-BED2",
            type_ref="REG-T-ERV-EXH-FLOOR", design_cfm=REG_S_RET_BED2,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # BED3 IS A CEILING GRILLE, AND ITS TWO NEIGHBOURS ARE NOT: FO-S-STAIR blocks every
    # FS-S bay between y=26'-0 3/8" and y=35'-5 3/8" across x 10'-3 1/8"..17'-8 5/8", BED3
    # spans y 27'-36', and FS-S-EAST is I-joist so nothing travels north-south on the far
    # side of the well. So this one is fed from the ATTIC sub-manifold instead of the
    # RM-M-MECH one (DU-A-ERV-R-BED3), which makes it a grille in the ceiling rather than a
    # boot in the floor. For stale air that is the better end of the room anyway; the
    # asymmetry with BED1/BED2 is real and is the price of the stair well being where it is.
    Register(uid="CMR904AAAA", tag="REG-S-RET-BED3", kind=DuctSystem.RETURN, room="RM-S-BED3",
            position=pt(ft(29), ft(31, 4)), duct_ref="DU-A-ERV-R-BED3",
            type_ref="REG-T-ERV-VALVE-EXH", design_cfm=REG_S_RET_BED3,
            mount=Mount(kind=MountKind.CEILING)),
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
            position=pt(ft(5), ft(32, 8)), duct_ref="DU-A-ERV-R-BATH1",
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
