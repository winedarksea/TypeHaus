# haus: editable
# Catlin MEP — air terminals — every supply, return, exhaust and transfer opening, storey by storey.
#
# plan/mep.py re-exports the storey lists below (AGENTS.md §1.1), so the manifest is
# unchanged.
#
# Three families, and the difference matters on the plan set: REG-T-ERV-* are ventilation
# terminals on EQ-B-ERV's balanced trunks; REG-T-HP-* are System 1's conditioned-air terminals;
# REG-T-TRANSFER-* is the passive one — a louver between two rooms, on no trunk at all, and the
# only register here with no `duct_ref`. Their types and the ducts they sit on are in
# plan/mep_hvac.py.
#
# EQ-B-ERV is a BALANCED machine authored at 210 cfm, HVI-certified at 206 at 0.4" w.g.
# (plan/mep_erv_types.py::EQ-T-BROAN-B210E75RT explains which number is which). Supply sums
# to 210: 110 cfm across the six REG-*-SUP* terminals plus the 100 cfm DU-S-ERV-HP-FEED puts
# into EQ-S-ERV-MIX. Extract also sums to 210, on the dampers, holding every code minimum:
#
#  * The seven bathroom terminals and the sauna run at 20 cfm each (IRC M1505.4.4's
#    continuous local-exhaust rate) — 160 cfm, untouchable, 76% of the machine.
#  * The remaining 50 cfm is shared by the other ten terminals: RM-S-PLANT 12, the workshop
#    bench hood 12, the study return 5, mudroom 4, kitchen 4, laundry 2, the three bedroom
#    pickups 2 each, and the attic return 5.
#
# RM-S-PLANT's extract and REG-B-RET1's bench hood are token flows at 12 cfm each — sized
# for holding a 70% RH room negative and pulling solder fume off a bench respectively. The
# honest fix is a LARGER ERV, not a redistribution; this arithmetic is true against the
# machine the house actually has.

from typehaus import (
    DuctRun,
    DuctSystem,
    Mount,
    MountKind,
    Register,
    deg,
    ft,
    inch,
    pt,
)
from typehaus.model import m

# Terminals off the chase. Each bedroom grille sits just inside the bedroom at the hallway
# wall (interior face x=22'-2 3/4"), fed by a short boot through that wall out of the
# soffit — the boot carries no DuctRun of its own; `duct_ref` names the trunk it comes off.
# All are ceiling grilles in the soffit face at 8'-0" (9'-0" ceiling less the 12" drop).
#
# RM-S-SUITE's terminal (REG-S-HP-SUITE) sits at DU-S-HP-SUITE's west terminus (12'-6",
# 14'-1 7/8") in SF-S-SUITE's end face, throwing down the entry arm into the suite's main
# volume. This branch is what made the suite's old ERV supply (REG-S-SUP6) redundant.
REGISTERS_HVAC_SECOND = [
    Register(uid="CSRH01AAAA", tag="REG-S-HP-BED1", kind=DuctSystem.SUPPLY, room="RM-S-BED1",
             position=pt(ft(22, 6), ft(13, 6)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP", design_cfm=80,
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    Register(uid="CSRH02AAAA", tag="REG-S-HP-BED2", kind=DuctSystem.SUPPLY, room="RM-S-BED2",
             position=pt(ft(22, 6), ft(22, 6)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP", design_cfm=80,
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    Register(uid="CSRH03AAAA", tag="REG-S-HP-BED3", kind=DuctSystem.SUPPLY, room="RM-S-BED3",
             position=pt(ft(22, 6), ft(31, 6)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP", design_cfm=80,
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # "Near the stairs": in the hall band west of the centre line, just south of the stair
    # well's south edge (the well is x 11'..18', y 25'..36').
    Register(uid="CSRH04AAAA", tag="REG-S-HP-STAIR", kind=DuctSystem.SUPPLY, room="RM-S-HALL",
             position=pt(ft(17, 6), ft(24)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP", design_cfm=50,
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # The suite's supply, in SF-S-SUITE's soffit face at the branch's west terminus,
    # throwing west out of the entry arm. 7'-10" because SF-S-SUITE drops 14" off the
    # 9'-0" ceiling.
    Register(uid="CSRH06AAAA", tag="REG-S-HP-SUITE", kind=DuctSystem.SUPPLY, room="RM-S-SUITE",
             position=pt(ft(12, 6), ft(14, 1.875)), duct_ref="DU-S-HP-SUITE",
             type_ref="REG-T-HP-SUP", design_cfm=100,
             mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 10))),
    # The two south rooms, both on DU-S-HP-SOUTH — the FS-ATTIC joist-bay branch at
    # y=3'-4" that reaches them from above, because the air handler's case fills SF-S-DUCT
    # from y=6'-0" to 9'-7" and leaves no lane south inside the soffit. Ceiling
    # grilles at 9'-0" (the storey's flat ceiling, not the 7'-10" soffit face), each a short
    # boot down out of the bay.
    #
    # RM-S-STUDY2 at (22'-8", 3'-4"): the room's west end, 4'-8" east of W-S-C1 and clear of
    # FURN-S-STUDY-TABLE's west chair (24'-0 5/8"). Both of the room's ways out are behind
    # the grille — D-S-STUDY2 north at x=20'-3 5/8", D-S-PLANT west at y=4'-5 1/2" — so the
    # 12x6 throws east down the room and past WIN-S-STUDY1/2 before the air turns back to
    # the hall. Nothing short-circuits: the study has no extract of its own, it hands its
    # air on through the two openings.
    Register(uid="DMVENAN0DW", tag="REG-S-HP-STUDY2", kind=DuctSystem.SUPPLY, room="RM-S-STUDY2",
             position=pt(ft(22, 8), ft(3, 4)), duct_ref="DU-S-HP-SOUTH",
             type_ref="REG-T-HP-SUP", design_cfm=75,
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # RM-S-PLANT at (6'-8", 3'-4"): the branch's west terminus, centred between the room's
    # two south windows (WIN-S-PLANT1/2 at x 4'-0"/9'-4") so the throw washes the glass a
    # humid plant room condenses on first. 1'-4" north of the plant line and 2'-11" south of
    # the two chairs (y 6'-2"/6'-4"), and between — not over — ED-S-PLANT-TUBE1/2, whose
    # suspended tubes hang at x 3'-4"/8'-8". The room's only opening is D-S-PLANT back into
    # the study, at the far east end, so the supply is diagonally opposite it and the room's
    # air crosses the glazing on the way out. (placeables.py still describes the chairs as
    # straddling a floor register at (9', 4') — that was REG-S-SUP1, since retired; this
    # terminal is in the ceiling, so nothing straddles it, and placeables.py says so itself.)
    # REG-T-HP-SUP-DAMPERED: same grille doing the same glass wash, with a motorised
    # isolation damper behind it. Two things it has to do that a plain terminal cannot — shut
    # System 1 out of a 70% RH room so the branch does not carry its moisture to every other
    # room on DU-S-HP-SOUTH, and stop pressurising a room whose vapour barrier has no
    # redundancy. It is interlocked with REG-S-ERV-PLANT-EXH below, which is what makes the
    # pair balanced rather than merely present (mep.humid_room_pressure is the rule that
    # says so out loud).
    Register(uid="CXDCYN7YQ2", tag="REG-S-HP-PLANT", kind=DuctSystem.SUPPLY, room="RM-S-PLANT",
             position=pt(ft(6, 8), ft(3, 4)), duct_ref="DU-S-HP-SOUTH",
             type_ref="REG-T-HP-SUP-DAMPERED", design_cfm=75,
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
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
    # y=4'-8" is the radial's own bay centre. It leaves 6'-9" between this grille and
    # REG-S-HP-PLANT at (6'-8", 3'-4"), so conditioned air still lands on the south glass and
    # crosses the planting before it is pulled out, rather than short-circuiting.
    Register(uid="C7LM4KAP2X", tag="REG-S-ERV-PLANT-EXH", kind=DuctSystem.EXHAUST,
             # y=7'-4" is a truss bay centre and a stud bay centre at once; y=4'-8" would
             # put the riser inside D-S-PLANT's rough opening — 78 1/2" of bare duct standing
             # in the doorway and a bore through the 2-ply 2x8 header (see mep_erv.py) — with
             # no legal riser station in that opening.
             room="RM-S-PLANT", position=pt(ft(17, 7), ft(7, 4)),
             duct_ref="DU-M-ERV-R-PLANT",
             type_ref="REG-T-ERV-PLANT-EXH", design_cfm=12,
             mount=Mount(kind=MountKind.WALL, elevation=ft(8, 6))),
    # The one return: a filter-back grille in SF-S-HP1's underside at (20'-7", 1'-9"), in
    # the return chamber at the box's south end, upstream of the coil, the strip heater and
    # the machine's own filter — with EQ-S-ERV-MIX at the far side of the same chamber,
    # which is what puts 100 cfm of -15 F design outdoor air UPSTREAM of the heat rather
    # than downstream of it. DU-S-HP-RET is 25x14 from here to the case's collar.
    #
    # `room` is RM-S-STUDY2 rather than RM-S-HALL because that is the room the chamber is
    # in. The AH draws through the study: hall -> D-S-STUDY2 (a 2'-6" cased opening, no
    # leaf) -> return, a deliberate loose coupling.
    #
    # Elevation 7'-3" is SF-S-HP1's finished underside (21" drop for the FLEXX Ultra
    # cabinet, storeys/second.py), not SF-S-DUCT's 7'-10".
    Register(uid="CSRH05AAAA", tag="REG-S-HP-RET", kind=DuctSystem.RETURN,
             room="RM-S-STUDY2",
             position=pt(ft(20, 7), ft(1, 9)), duct_ref="DU-S-HP-RET",
             type_ref="REG-T-HP-RET", design_cfm=750,
             mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 3))),
]

REGISTERS_HVAC_ATTIC = [
    # y=3'-4" is the FS-ATTIC bay's own centreline (8" + 2 x 16"), so the boot drops
    # straight down out of DU-S-HP-SOUTH, which passes directly under this point — the same
    # straight-boot pattern as REG-A-HP-EAST and REG-A-HP-WEST. 100 cfm is the east arm's
    # larger share; see DU-S-HP-SOUTH for why that branch is 10x6.
    Register(uid="CARH01AAAA", tag="REG-A-HP-STUDY", kind=DuctSystem.SUPPLY,
             room="RM-A-STUDY", position=pt(ft(26), ft(3, 4)), duct_ref="DU-S-HP-SOUTH",
             type_ref="REG-T-HP-SUP", design_cfm=100,
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # Directly above the hall soffit: the boot rises straight through FS-ATTIC off the
    # x=19'-4" trunk below, no attic duct run needed. y=11'-4" is the next FS-ATTIC bay
    # centre north of W-A-SN's north face (9'-10 3/8", thickened to 12 3/4" for the study's
    # bookcase wall) and is still over DU-S-HP-SUP, so the boot rises straight; the grille
    # stays inside RM-A-EAST-UNFIN and clear of FO-A-STAIR's walkway.
    Register(uid="CARH02AAAA", tag="REG-A-HP-EAST", kind=DuctSystem.SUPPLY,
             room="RM-A-EAST-UNFIN", position=pt(ft(19, 4), ft(11, 4)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP", design_cfm=35,
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # The west loft's supply: a floor boot straight up off DU-S-HP-SUITE through FS-ATTIC.
    # The room gets conditioned air off System 1 like RM-A-STUDY/RM-A-EAST-UNFIN, returning
    # stale air at REG-A-RET1, so the ERV's attic side is extract-only.
    #
    # `room=RM-A-STUDIO` is LOAD-BEARING TWICE OVER: the room is a BEDROOM, and this one
    # register answers two different checks for it — `mep.ventilation_distribution` wants a
    # fresh-air supply in a conditioned bedroom, and R303.1 Exception 1 (which is how this
    # room gets out of its 8% glazing shortfall — see plan/lighting.py) requires a
    # mechanical fresh-air SUPPLY Register in the room as one of its four conditions. NO
    # MINI-SPLIT IS WANTED: reusing this boot is the whole reason the studio costs what it
    # costs.
    Register(uid="CARH03AAAA", tag="REG-A-HP-WEST", kind=DuctSystem.SUPPLY,
             room="RM-A-STUDIO", position=pt(ft(16, 6), ft(14, 1.875)),
             duct_ref="DU-S-HP-SUITE", type_ref="REG-T-HP-SUP", design_cfm=75,
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
]

# CONDENSATE — planned plumbing item, no geometry this pass. The four indoor units make
# condensate in cooling and gravity-drain into a collected air-gap line terminating over the
# mechanical-room sink (keeps a trapped condensate line out of the sanitary system), but that
# sink has no drain of its own yet (plans/TODO.md).

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
# REG-S-HP-STUDY2 in REGISTERS_HVAC_SECOND above, on the DU-S-HP-SOUTH branch. The study
# was always the anomaly: EQ-S-HP1-AH hangs in that room's own ceiling soffit, and a room
# does not breathe by being next to the machine.
REGISTERS = [
    # One per bedroom now that the east bedrooms are equal 9'-0" bays: BED1 y 9'-18',
    # BED2 y 18'-27', BED3 y 27'-36'. RM-S-BED2 had no terminal at all before the
    # re-spacing (plans/TODO.md). All three sit at x=29', against the east wall and
    # diagonally opposite the hall-side supply grille, so the room crossventilates.
    Register(uid="CMR903AAAA", tag="REG-S-RET-BED1", kind=DuctSystem.RETURN, room="RM-S-BED1",
            position=pt(ft(29), ft(14)), duct_ref="DU-M-ERV-R-BED1",
            type_ref="REG-T-ERV-EXH", design_cfm=2,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CMR907AAAA", tag="REG-S-RET-BED2", kind=DuctSystem.RETURN, room="RM-S-BED2",
            position=pt(ft(29), ft(22)), duct_ref="DU-M-ERV-R-BED2",
            type_ref="REG-T-ERV-EXH", design_cfm=2,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # BED3 IS A CEILING GRILLE, AND ITS TWO NEIGHBOURS ARE NOT: FO-S-STAIR blocks every
    # FS-S bay between y=26'-0 3/8" and y=35'-5 3/8" across x 10'-3 3/8"..17'-8 5/8", BED3
    # spans y 27'-36', and FS-S-EAST is I-joist so nothing travels north-south on the far
    # side of the well. So this one is fed from the ATTIC sub-manifold instead of the
    # RM-M-MECH one (DU-A-ERV-R-BED3), which makes it a grille in the ceiling rather than a
    # boot in the floor. For stale air that is the better end of the room anyway; the
    # asymmetry with BED1/BED2 is real and is the price of the stair well being where it is.
    Register(uid="CMR904AAAA", tag="REG-S-RET-BED3", kind=DuctSystem.RETURN, room="RM-S-BED3",
            position=pt(ft(29), ft(31, 4)), duct_ref="DU-A-ERV-R-BED3",
            type_ref="REG-T-ERV-EXH", design_cfm=2,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # No REG-S-RET2 (the suite's own extract) — the owner's call, and defensible on the
    # model too: no check fires for its absence (BEDROOM is not in
    # checks/mep/hvac.py's _STALE_OCCUPANCIES), and RM-S-SUITEBATH's REG-S-EXH3 carries the
    # suite through the door undercut. The suite KEEPS its System 1 supply REG-S-HP-SUITE.
]

REGISTERS_SECOND = [
    Register(uid="CSRV03AAAA", tag="REG-S-EXH3", kind=DuctSystem.EXHAUST, room="RM-S-SUITEBATH",
            position=pt(ft(14), ft(19, 4)), duct_ref="DU-M-ERV-R-SUITEBATH",
            type_ref="REG-T-ERV-EXH", design_cfm=20,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CSRV04AAAA", tag="REG-S-EXH4", kind=DuctSystem.EXHAUST, room="RM-S-VANITY",
            position=pt(ft(3), ft(24, 8)), duct_ref="DU-M-ERV-R-VANITY",
            type_ref="REG-T-ERV-EXH", design_cfm=20,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CSRV05AAAA", tag="REG-S-EXH1", kind=DuctSystem.EXHAUST, room="RM-S-BATH1",
            position=pt(ft(5), ft(32, 8)), duct_ref="DU-A-ERV-R-BATH1",
            type_ref="REG-T-ERV-EXH", design_cfm=20,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
]

# Main-storey terminals are ceiling grilles fed from the FS-S-WEST bays overhead, each with
# its own 75 mm radial back to EQ-M-ERV-MAN-SUP/EXH in RM-M-MECH. Every position below sits
# on the bay centre its radial rides (8" + n*16"), which is what lets `mep.duct_joist_bay`
# grade the run end to end rather than stopping at a trunk and leaving the last few feet
# undrawn.
#
# The kitchen is open plan inside RM-M-LIVING (no Occupancy.KITCHEN), so its stale pickup is
# placed by position and still carries the LIVING room=.
REGISTERS_MAIN = [
    Register(uid="CMRV01AAAA", tag="REG-M-SUP1", kind=DuctSystem.SUPPLY, room="RM-M-LIVING",
            position=pt(ft(27), ft(12, 8)), duct_ref="DU-M-ERV-R-LIVING",
            type_ref="REG-T-ERV-SUP", design_cfm=20,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # No second living-room outlet: one ERV outlet is right for an open-plan room at the
    # whole-house rate; a pair would be sized as if this were a heating trunk.
    Register(uid="CMRV03AAAA", tag="REG-M-SUP3", kind=DuctSystem.SUPPLY, room="RM-M-BED",
            position=pt(ft(9), ft(6)), duct_ref="DU-M-ERV-R-BED",
            type_ref="REG-T-ERV-SUP", design_cfm=15,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # ================== RM-M-STUDY: THE CALL BOOTH'S TWO TERMINALS ==================
    #
    # THE ROOM HAS AN EXTRACT, AND THAT IS WHAT PUTS THE SUPPLY BACK IN THE CEILING. A lone
    # ceiling supply strands its air at the ceiling because the only way out is D-M-STUDY's
    # undercut, four feet below it and across the room. Give the room a LOW extract and the
    # ceiling supply has to cross the whole occupied zone to reach it: the air is pulled
    # down past a seated head rather than left to find its own way. So the pair below is
    # strictly better than either terminal alone, and the supply is overhead where the
    # owner asked for it, over ED-M-STUDY-SPOT.
    #
    # D-M-STUDY'S UNDERCUT IS THE RELIEF PATH AND MAY NOT BE CLOSED. 15 cfm in, 10 cfm out:
    # the booth runs +5 cfm POSITIVE, which is what a call booth wants — nothing is drawn in
    # under the door from the hall, so the staggered studs and the felt stay the whole
    # acoustic boundary. The 5 cfm leaves under the door. A gasket, a sweep or a drop seal
    # added later for the last few STC points needs a transfer grille or a jump duct to come
    # with it — or the extract raised to 15 cfm, the cheap version of that fix. (Not free:
    # see the 3" radial's ~17 cfm ceiling on DU-M-ERV-R-LAUNDRY, which this shares.)
    #
    # -- the supply, back in the ceiling ---------------------------------------------
    #
    # (17'-2", 20'-8") at 9'-0". ED-M-STUDY-SPOT is at (17'-6 5/8", 21'-5"), so this is
    # 4 5/8" west and 9" south of directly-above-the-sconce, three feet over it. **The 9"
    # is a joist line, not a preference:** FS-S-WEST's bays centre on 8" + n*16", so 20'-8"
    # is a bay and the sconce's 21'-5" is 1" past the joist at 21'-4". Reaching the sconce's
    # own line would mean jogging the radial across that joist directly over W-M-C3, which
    # is the bearing end of the truss — the one place the hole chart forbids outright, and
    # the same objection that kept the terminal off the east WALL yesterday. The x is as far
    # east as a 7" grille goes: the face reaches 17'-5 1/2", 3 1/8" clear of W-M-C3's study
    # face and 3 3/4" clear of its top plate.
    Register(uid="CMRV04AAAA", tag="REG-M-SUP4", kind=DuctSystem.SUPPLY, room="RM-M-STUDY",
            position=pt(ft(17, 2), ft(20, 8)), duct_ref="DU-M-ERV-R-STUDY",
            type_ref="REG-T-ERV-SUP", design_cfm=15,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # -- the extract, low, and NOT on the east wall -----------------------------------
    #
    # ** THE OWNER ASKED FOR THE EAST WALL AND THE EAST WALL DOES NOT EXIST. ** Measured off
    # the resolved layer polygons rather than off the plan's look:
    #   * W-M-C3's study face runs y 18'-0"..22'-1 5/8" — 4'-1 5/8" of wall;
    #   * D-M-STUDY's RO takes y 18'-2 3/8"..21'-0 11/16" of it, leaving one 12 15/16"
    #     sliver at the north end (the sliver ED-M-STUDY-SPOT and ED-M-STUDY-SW share);
    #   * FURN-M-STUDY-BENCH is 47" wide and runs wall to wall, y 20'-7 7/8"..22'-0 7/8".
    # The bench covers the sliver to within 3/4". There is no low east wall to cut a grille
    # into, and freeing one means shortening the bench by 7" and opening a dead pocket in
    # the corner — a worse trade than moving the grille one wall.
    #
    # So it is the SOUTH wall's east end, which is the only low wall this room has left:
    # FURN-M-STUDY-DESK holds x 13'-8 3/4"..16'-1 3/4", the east wall is door, the north
    # wall is bench, and the west wall's one gap between desk and bench is 7 1/8" wide. That
    # leaves x 16'-1 3/4"..17'-8 5/8" — the 18 7/8" pocket you step into — and this sits in
    # it at 16'-6", 3/4" east of the desk's end.
    #
    # ** IT IS BETTER THERE THAN IT WOULD HAVE BEEN ON THE EAST WALL, WHICH IS LUCK. ** The
    # pocket is the one piece of this room's floor nobody sits at: the occupant sits on the
    # bench facing south with their feet under the cantilevered desk top, so a floor-level
    # grille here is not behind a bag, a chair or a foot the way one under the desk would be.
    #
    # y = 18'-4 1/2" is W-M-CLN2's resolved study face at 18'-0" plus half this type's 1"
    # depth (the face-position convention in plan/electrical.py). No rotation: the type's
    # footprint is already (7" of face, 1" of depth) in x/y, which is a south wall's
    # orientation — REG-M-SUP4 needed deg(90) yesterday only because W-M-LS runs the other
    # way. 12" of elevation puts the face 8 1/2"..15 1/2", above a base and below a knee,
    # inside the last courses of WP-M-STUDY-WAINSCOT: a grille cut into walnut is ordinary
    # joinery, and the same plate ED-M-STUDY-DATA1 already asks that wainscot for.
    #
    # It sits at 14'-6", not the entry pocket at 16'-6": FURN-M-STUDY-DESK-LEAF STOWS by
    # hanging down the wall it is hinged to — 8" to 28" across the whole pocket, straight
    # over a grille whose face is 8 1/2"..15 1/2". Folding it up instead would have buried
    # ED-M-STUDY-RC1 at 32" and cut 12" above the wainscot cap; the grille was the cheaper
    # thing to move. **THE GENERAL LESSON: a placeable's STOWED envelope is load-bearing on
    # the MEP, and the model holds no geometry for it at all.** FT-STUDY-DESK-LEAF is drawn
    # deployed (18" x 20" on the floor); the 18" x 20" of SOUTH WALL it covers when folded
    # exists only in prose. Re-read plan/furniture_types.py before putting anything back on
    # that wall below 28".
    #
    # 14'-6" is not a retreat to a worse spot, and the reason is the diagonal. The supply is
    # in the ceiling at (17'-2", 20'-8"); at 16'-6" the extract sat 2'-4" from directly under
    # it, the short-circuit corner of the room. At 14'-6" the pair is corner to corner — nine
    # feet of plan separation over eight feet of fall, so the sweep crosses the occupied zone
    # instead of dropping down one end of it.
    #
    # WHAT IT COSTS: the grille is in the knee space, under the fixed desk's west half, so a
    # shoe or a bag can sit in front of it. At 10 cfm through a 7" face that is a throttle,
    # not a blockage, and it is the price of the leaf. If it ever reads as a problem the fix
    # is the west wall (W-M-LS, out of the foot zone entirely) — but that wall is the centre
    # bearing line and a riser in it wants checking against the trusses before anyone tries.
    #
    # RISER CLEARANCES. W-M-CLN2 is INT_2X4_STAGGERED_GWB: 5 1/2" of cavity, but a 2 1/8"
    # device box and a 3" duct still do not share one 3 1/2" leaf. At 14'-6" the drop is
    # 1'-6" from ED-M-STUDY-DATA1 (16'-0") and 2'-6" from ED-M-STUDY-RC1 (17'-0"), and
    # CD-B-DATA-STUDY rises at 16'-0" on this same wall, now 1'-6" clear.
    Register(uid="H6C6RD9NED", tag="REG-M-RET-STUDY", kind=DuctSystem.RETURN, room="RM-M-STUDY",
            position=pt(m(4.27777), m(5.60336)), duct_ref="DU-M-ERV-R-LAUNDRY",
            type_ref="REG-T-ERV-EXH-WALL", design_cfm=5,
            mount=Mount(kind=MountKind.WALL, elevation=inch(12))),
    # The two baths are EXHAUST at 20 cfm each, like the second storey's — see the note over
    # REGISTERS_SECOND for why the whole wet-room set changed direction on 2026-08-01.
    Register(uid="CMRV05AAAA", tag="REG-M-EXH1", kind=DuctSystem.EXHAUST, room="RM-M-BATH1",
            position=pt(ft(1, 2), ft(24, 8)), duct_ref="DU-M-ERV-R-BATH1",
            type_ref="REG-T-ERV-EXH", design_cfm=20,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV06AAAA", tag="REG-M-EXH2", kind=DuctSystem.EXHAUST, room="RM-M-BATH2",
            position=pt(ft(4), ft(18)), duct_ref="DU-M-ERV-R-BATH2",
            type_ref="REG-T-ERV-EXH", design_cfm=20,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # THE OWNER ASKED FOR THIS ONE TO GO, AND IT COULD NOT. RM-M-LAUNDRY is a 4'-3" x 4'-3"
    # closet with a CONDENSING dryer (APPL-LG-WASHTOWER, so M1502 does not reach it and
    # there is no lint-laden air to pull), and the hall it opens onto is extracted six feet
    # away at REG-M-RET5 — but `mep.ventilation_distribution` disagrees, and is right to:
    # "laundry" is in that check's stale-occupancy set (checks/mep/hvac.py::
    # _STALE_OCCUPANCIES) because ASHRAE 62.2 lists a laundry room as a local-exhaust space,
    # washer or dryer notwithstanding, and this house is held to a clean report. (REG-S-RET2's
    # deletion stands: BEDROOM is NOT in that set.)
    #
    # So it stays, at 5 cfm rather than a full pickup — the smallest rate that is both true
    # and passing, on its own radial at the 20'-8" bay centre that radial rides.
    Register(uid="CMRV07AAAA", tag="REG-M-RET3", kind=DuctSystem.RETURN, room="RM-M-LAUNDRY",
            position=pt(ft(10, 6), ft(20, 8)), duct_ref="DU-M-ERV-R-LAUNDRY",
            type_ref="REG-T-ERV-EXH", design_cfm=2,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV08AAAA", tag="REG-M-RET5", kind=DuctSystem.RETURN, room="RM-M-LIVING",
            position=pt(ft(20, 10.7), ft(24, 8)), duct_ref="DU-M-ERV-R-KITCH",
            type_ref="REG-T-ERV-EXH", design_cfm=4,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # RM-M-MUDROOM is stale-pickup only, no fresh-air outlet (reversed 2026-07-29 from an
    # earlier fresh-air-intake call). A mudroom is the room that smells; pressurising it pushes
    # that everywhere else. Extracting makes it the main storey's low-pressure end, so boundary
    # air moves toward the boots and the ERV recovers the heat. Same grille/hole/uid, direction
    # only — centred in the hallway strip between the two closets.
    Register(uid="CMRV09AAAA", tag="REG-M-RET-MUD", kind=DuctSystem.RETURN, room="RM-M-MUDROOM",
            position=pt(ft(4, 0.4), ft(31, 4)), duct_ref="DU-M-ERV-R-MUD",
            type_ref="REG-T-ERV-EXH", design_cfm=4,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # The one passive opening in the house (plans/TODO.md): a louver in W-M-STRW that lets
    # the mudroom share the stair's air. No duct/damper/fan — `duct_ref` is None (the first
    # register with none) and `kind` is TRANSFER, so ventilation checks neither credit a
    # room with fresh air nor double-count a stale pickup beside REG-M-RET-MUD.
    #
    # *** THE ROOM THIS SERVES IS RM-M-MUDROOM. `room` says RM-M-LIVING. *** A transfer
    # opening belongs to two rooms, but `room` can only hold one and the resolver reads it as
    # containment (footprint centre vs. room polygon, flagged as
    # integrity.placeable_room_mismatch if they disagree). The plate is on the *stair* face
    # of W-M-STRW (stair well = RM-M-LIVING), so that's what keeps the build log honest; the
    # mudroom side lives in this comment and in the tag (XFER-MUD, not XFER-STAIR).
    #
    # REG-M-RET-MUD is what actually drives airflow through it: the mudroom is the main
    # storey's low-pressure end by design, so the ERV pulls stair air through this louver.
    #
    # Geometry: x=10'-3 7/8" backs onto W-M-STRW's stair face (10'-3 3/8"), facing east —
    # the mudroom side is bare 2x6 bay, no opening needed there. y=34'-0" is the only bay
    # wide enough (14 1/2" clear) on this BEARING wall; the bay north is 7 1/8", too narrow
    # for the 12" face without cutting and heading a stud. z=7'-6" (top 8'-4") matches the
    # head's 7'-0"..8'-0" band, clear of D-M-ENTRY's head.
    Register(uid="MW7W7SBZ65", tag="REG-M-XFER-MUD", kind=DuctSystem.TRANSFER, room="RM-M-LIVING",
            position=pt(ft(10, 3.875), ft(34)), type_ref="REG-T-TRANSFER-1210",
            rotation=deg(90),
            mount=Mount(kind=MountKind.WALL, elevation=ft(7, 6))),
]

# Basement terminals hang from the SL-M-DECK underside off the CHASE trunks — except the
# sauna's stale pickup, which is the one wall-mounted terminal in the house (see below).
REGISTERS_BASEMENT = [
    Register(uid="CBRV01AAAA", tag="REG-B-SUP1", kind=DuctSystem.SUPPLY, room="RM-B-GYM",
            position=pt(m(5.75157), m(3.2161)), duct_ref="DU-B-ERV-R-GYM",
            type_ref="REG-T-ERV-SUP", design_cfm=18,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # RM-B-PLAY-N is 324 sf of windowless habitable MEDIA space, legal only under R303.1
    # Exception 1, whose second half requires outdoor air supplied to *the room* — an
    # adjacent room's grille doesn't satisfy it. **Deleting this terminal is a hard
    # code.R303_1_light_and_ventilation FAIL.**
    #
    # (19', 26'): the entire play-room ceiling is SL-M-DECK's 14 3/8" solid concrete with NO
    # cavity at all, so every foot of that run is surface-mounted; entering at the room's
    # west edge and stopping just inside cuts about eight feet of exposed duct. It still
    # throws away from FURN-B-PLAY-TV on the east wall.
    Register(uid="CBRV02AAAA", tag="REG-B-SUP2", kind=DuctSystem.SUPPLY, room="RM-B-PLAY-N",
            position=pt(ft(19), ft(26)), duct_ref="DU-B-ERV-R-PLAY",
            type_ref="REG-T-ERV-SUP", design_cfm=30,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # THE WORKSHOP TERMINAL IS A BENCH HOOD, NOT A CEILING DIFFUSER: a diffuser eight feet
    # up does not capture solder fume, it dilutes it into the room and then extracts the
    # dilution. REG-T-ERV-BENCH-HOOD is a 30" x 12" capture face hung at 5'-6", i.e. 24"
    # above FURN-B-WORKSHOP-BENCH-N/S's 34" tops, and it captures at the source.
    #
    # It stays `kind=RETURN` rather than becoming a dedicated EXHAUST: the fumes are light,
    # the heat is worth recovering, and this is not a spray booth.
    #
    # HONEST LIMIT: the two benches run ten feet along the west wall (y 3'-6"..13'-6") and
    # one 30" hood captures a fraction of that. It is a bench hood, not bench-run coverage.
    Register(uid="CBRV03AAAA", tag="REG-B-RET1", kind=DuctSystem.RETURN, room="RM-B-WORKSHOP",
            position=pt(ft(2), ft(8, 6)), duct_ref="DU-B-ERV-R-BENCH",
            type_ref="REG-T-ERV-BENCH-HOOD", design_cfm=12,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(5, 6))),
    # The sauna's stale pickup is on the wall, 4" above the floor on the south face below
    # FURN-B-SAUNA-BENCH-S: a sauna stratifies hard, so the low pickup pulls the cold spent
    # layer off the floor rather than the löyly at bench height. Paired with REG-B-SUP3 over
    # the heater, both ends dampered (REG-T-ERV-SAUNA-*), it drives the room's convection
    # loop — down the far wall, across the floor, out under the bench. EXHAUST at 20 cfm:
    # the room is Occupancy.BATHROOM and its window's openable area (1.2 sf) falls short of
    # R303.3's 1.5 sf, so mechanical exhaust governs.
    Register(uid="CBRV04AAAA", tag="REG-B-EXH2", kind=DuctSystem.EXHAUST, room="RM-B-SAUNA",
            position=pt(m(2.85824), m(0.407047)), duct_ref="DU-B-ERV-R-SAUNA-EXH",
            type_ref="REG-T-ERV-SAUNA-EXH", design_cfm=20,
            mount=Mount(kind=MountKind.WALL, elevation=inch(4))),
    # Fresh air in high, over the stones, directly above EQ-B-SAUNA-HTR (west liner,
    # plan/electrical.py) at 7'-0" — below the 8' ceiling so the boot doesn't fight the drop
    # ceiling the condensate line already runs above.
    Register(uid="CBRV06AAAA", tag="REG-B-SUP3", kind=DuctSystem.SUPPLY, room="RM-B-SAUNA",
            position=pt(ft(9, 9.8125), ft(8, 9)), duct_ref="DU-B-ERV-R-SAUNA-SUP",
            type_ref="REG-T-ERV-SAUNA-SUP", design_cfm=12,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(7))),
    # RM-B-BATH. Filed as EXHAUST rather than RETURN, like RM-S-BATH1's terminal and unlike
    # the basement's other two stale pickups: a bathroom's air is pulled and not
    # recirculated. It sits over the water closet at the room's west end, the far corner from
    # the door, so the room's makeup air crosses it on the way through.
    Register(uid="CBRV05AAAA", tag="REG-B-EXH1", kind=DuctSystem.EXHAUST, room="RM-B-BATH",
            position=pt(ft(11, 8), ft(20)), duct_ref="DU-B-ERV-R-BATH",
            type_ref="REG-T-ERV-EXH", design_cfm=20,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
]

# The attic ERV terminals: extract only. Fresh air is off System 1 (REG-A-HP-WEST, the
# floor boot in REGISTERS_HVAC_ATTIC above); this is the stale pickup — the same pattern as
# every other storey. The attic is not one cathedral volume: it is a guest bedroom, a closed
# bathroom and a walled storage pocket with three doors between them, so REG-A-RET1 sits in
# the studio and the bath gets its own terminal, because R303.3 requires local exhaust from
# a bathroom and a grille in the next room is not it.
REGISTERS_ATTIC = [
    # x=1'-0": the 6:12 roof underside there is 7 1/2" above the deck — a wedge nothing else
    # can use, no furniture can stand in and nobody walks through — which is exactly what
    # makes it the right home for a boxed-in 3" surface duct and a floor grille at its end.
    # Moving it inboard would put a duct across a finished bedroom to buy headroom a floor
    # boot has no use for.
    # (1'-0", 20'-8") is a floor boot in the studio's NW corner, on the existing x=1'-0" chase,
    # at a bay centre (248" = 8 + 15 x 16), diagonally opposite REG-A-HP-WEST's supply at
    # (16'-6", 14'-1 7/8"). Fresh in at one corner, stale out at the other, which is the
    # arrangement every other storey already has.
    Register(uid="CARV04AAAA", tag="REG-A-RET1", kind=DuctSystem.RETURN, room="RM-A-STUDIO",
            position=pt(ft(1), ft(20, 8)), duct_ref="DU-A-ERV-R-ATTIC",
            type_ref="REG-T-ERV-EXH", design_cfm=5,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # ** THE BATH'S EXHAUST, AND ITS design_cfm IS NOT OPTIONAL. ** R303.3 accepts an operable
    # window OR a local exhaust; this room has no exterior wall, so it is the exhaust — and
    # `checks/.../ventilation.py` reads the AUTHORED number on the GRILLE (the run's is only a
    # fallback for a single-terminal branch, and None on both is UNKNOWN, never a pass).
    #
    # 20 cfm lands in R303.3's CONTINUOUS band, which is what every other bath terminal in this
    # house runs at — 50 cfm intermittent would pass the same check and would be the odd one
    # out on a balanced machine whose whole attic side is continuous extract.
    #
    # A WALL MOUNT IS WHAT MAKES A HIGH PICKUP POSSIBLE HERE, AND 4'-4" IS AS HIGH AS THE
    # WALL GOES. There is no ceiling plenum under a cathedral: the room follows the roof.
    # W-A-STU-W's 5 1/2" staggered cavity is the only place a duct can drop from a high
    # grille into the FS-ATTIC bay, which is exactly why the wet wall carries this as well
    # as every drain in the suite. That wall is `ToRoof`, so its own top is the rake: at
    # x=9'-7 1/2" the 6:12 underside is 4'-11 1/4" above the deck. 4'-4" leaves 7 1/4" of
    # wall over the boot — the highest pickup this room can have.
    Register(uid="N989VQP3T8", tag="REG-A-STUBATH-EXH", kind=DuctSystem.EXHAUST, room="RM-A-STUBATH",
            # y=19'-4" follows DU-A-ERV-R-STUBATH onto the 232" bay centre so its east leg
            # could leave the studio floor for the joist bay. x=9'-11 7/8" is W-A-STU-W's
            # bath-side paint face (9'-10 7/8") plus the ~1" inboard offset every wall device
            # here carries, NOT the wall AXIS — on the axis the footprint centre sits inside
            # the wall and outside the room, and `integrity.placeable_room_mismatch` says so.
            # The riser stays on the axis in the staggered cavity; the offset is the boot
            # crossing the finish.
            position=pt(ft(9, 11.875), ft(19, 4)), duct_ref="DU-A-ERV-R-STUBATH",
            # REG-T-ERV-EXH-WALL, not the ceiling REG-T-ERV-EXH: this is the house's only
            # WALL-mounted extract, and on the ceiling type the resolver read its 7" face as
            # 7" of projection into the room. See plan/mep_hvac.py.
            type_ref="REG-T-ERV-EXH-WALL", design_cfm=20,
            mount=Mount(kind=MountKind.WALL, elevation=ft(4, 4))),
]
