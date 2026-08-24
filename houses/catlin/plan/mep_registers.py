# haus: editable
# Catlin MEP — air terminals — every supply, return, exhaust and transfer opening, storey by storey.
#
# Split out of the old 2,515-line plan/mep.py (AGENTS.md §1.1). Every element below moved
# verbatim; plan/mep.py still re-exports the storey lists, so the manifest is unchanged.
#
# Three families now, and the difference matters on the plan set: REG-T-ERV-* are ventilation
# terminals on EQ-B-ERV's balanced trunks; REG-T-HP-* are System 1's conditioned-air terminals;
# REG-T-TRANSFER-* is the passive one — a louver between two rooms, on no trunk at all, and the
# only register here with no `duct_ref`. Their types and the ducts they sit on are in
# plan/mep_hvac.py.

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
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    Register(uid="CSRH02AAAA", tag="REG-S-HP-BED2", kind=DuctSystem.SUPPLY, room="RM-S-BED2",
             position=pt(ft(22, 6), ft(22, 6)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    Register(uid="CSRH03AAAA", tag="REG-S-HP-BED3", kind=DuctSystem.SUPPLY, room="RM-S-BED3",
             position=pt(ft(22, 6), ft(31, 6)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # "Near the stairs": in the hall band west of the centre line, just south of the stair
    # well's south edge (the well is x 11'..18', y 25'..36').
    Register(uid="CSRH04AAAA", tag="REG-S-HP-STAIR", kind=DuctSystem.SUPPLY, room="RM-S-HALL",
             position=pt(ft(17, 6), ft(24)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # The suite's supply, in SF-S-SUITE's soffit face at the branch's west terminus,
    # throwing west out of the entry arm. 7'-10" because SF-S-SUITE drops 14" off the
    # 9'-0" ceiling.
    Register(uid="CSRH06AAAA", tag="REG-S-HP-SUITE", kind=DuctSystem.SUPPLY, room="RM-S-SUITE",
             position=pt(ft(12, 6), ft(14, 1.875)), duct_ref="DU-S-HP-SUITE",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 10))),
    # The two south rooms (2026-08-16), both on DU-S-HP-SOUTH — the FS-ATTIC joist-bay
    # branch at y=3'-4" that reaches them from above, because the air handler's case fills
    # SF-S-DUCT from y=6'-0" to 9'-7" and leaves no lane south inside the soffit. Ceiling
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
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # RM-S-PLANT at (6'-8", 3'-4"): the branch's west terminus, centred between the room's
    # two south windows (WIN-S-PLANT1/2 at x 4'-0"/9'-4") so the throw washes the glass a
    # humid plant room condenses on first. 1'-4" north of the plant line and 2'-11" south of
    # the two chairs (y 6'-2"/6'-4"), and between — not over — ED-S-PLANT-TUBE1/2, whose
    # suspended tubes hang at x 3'-4"/8'-8". The room's only opening is D-S-PLANT back into
    # the study, at the far east end, so the supply is diagonally opposite it and the room's
    # air crosses the glazing on the way out. (placeables.py still describes the chairs as
    # straddling a floor register at (9', 4') — that was REG-S-SUP1, retired 2026-07-29;
    # this terminal is in the ceiling, so nothing straddles it — and placeables.py says so
    # itself now.)
    # Retyped to REG-T-HP-SUP-DAMPERED 2026-08-18: same grille in the same place doing the
    # same glass wash, with a motorised isolation damper behind it. Two things it now has to
    # be able to do that a plain terminal cannot — shut System 1 out of a 70% RH room so the
    # branch does not carry its moisture to every other room on DU-S-HP-SOUTH, and stop
    # pressurising a room whose vapour barrier has no redundancy. It is interlocked with
    # REG-S-ERV-PLANT-EXH below, which is what makes the pair balanced rather than merely
    # present. (mep.humid_room_pressure is the rule that says so out loud.)
    Register(uid="CXDCYN7YQ2", tag="REG-S-HP-PLANT", kind=DuctSystem.SUPPLY, room="RM-S-PLANT",
             position=pt(ft(6, 8), ft(3, 4)), duct_ref="DU-S-HP-SOUTH",
             type_ref="REG-T-HP-SUP-DAMPERED",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # The plant room's extract (2026-08-18) — the terminal the room did not have, and the
    # single biggest thing wrong with it before. RM-S-PLANT was supply-only, so its own
    # ventilation pushed 70%-RH air into every crack in the envelope it is now lined to
    # protect; slightly negative is the only pressure a continuously humid room may be held
    # at, and that takes an extract, not a better barrier.
    #
    # At (14'-0", 4'-8"): the far east end of the room, 7'-5" from the supply and across
    # the room from it, so conditioned air lands on the south glass, crosses the planting
    # and leaves at the far end rather than short-circuiting. Ceiling at 9'-0" because
    # humid air stratifies — the wettest air in the room is the air at the ceiling, which is
    # also the air directly under FS-ATTIC's I-joists.
    Register(uid="C7LM4KAP2X", tag="REG-S-ERV-PLANT-EXH", kind=DuctSystem.EXHAUST,
             room="RM-S-PLANT", position=pt(ft(14), ft(4, 8)), duct_ref="DU-S-PLANT-EXH",
             type_ref="REG-T-ERV-PLANT-EXH", design_cfm=25,
             mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # The one return, at the hall's south end right AT EQ-S-HP1-AH (2026-07-30), 1" north
    # of the unit's rear face, feeding its bottom-return through DU-S-HP-RET's plenum stub.
    # DU-S-ERV-HP-FEED's wye injects the ERV's fresh air into this return plenum (not a
    # hard-coupled duct) behind the grille, so either machine can run alone.
    Register(uid="CSRH05AAAA", tag="REG-S-HP-RET", kind=DuctSystem.RETURN, room="RM-S-HALL",
             position=pt(ft(20, 8), ft(9, 8)), duct_ref="DU-S-HP-RET",
             type_ref="REG-T-HP-RET",
             mount=Mount(kind=MountKind.CEILING, elevation=ft(7, 10))),
]

REGISTERS_HVAC_ATTIC = [
    Register(uid="CARH01AAAA", tag="REG-A-HP-STUDY", kind=DuctSystem.SUPPLY,
             room="RM-A-STUDY", position=pt(ft(26), ft(3)), duct_ref="DU-A-HP-STUDY",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # Directly above the hall soffit (2026-07-30): the boot rises straight through
    # FS-ATTIC off the x=19'-4" trunk below, no attic duct run needed. y=10' keeps the
    # grille inside RM-A-EAST's south wall and clear of FO-A-STAIR's walkway.
    Register(uid="CARH02AAAA", tag="REG-A-HP-EAST", kind=DuctSystem.SUPPLY,
             room="RM-A-EAST", position=pt(ft(19, 4), ft(10)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # RM-A-WEST's supply (2026-07-30): a floor boot straight up off DU-S-HP-SUITE through
    # FS-ATTIC. Retired REG-A-SUP1/DU-A-ERV-SUP: the room now gets conditioned air off
    # System 1 like RM-A-STUDY/RM-A-EAST, returning stale air at REG-A-RET1, so the ERV's
    # attic side is extract-only — the same pattern as the second storey.
    Register(uid="CARH03AAAA", tag="REG-A-HP-WEST", kind=DuctSystem.SUPPLY,
             room="RM-A-WEST", position=pt(ft(16, 6), ft(14, 1.875)),
             duct_ref="DU-S-HP-SUITE", type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
]

# CONDENSATE — planned plumbing item, no geometry this pass. The four indoor units make
# condensate in cooling and gravity-drain into a collected air-gap line terminating over the
# mechanical-room sink (keeps a trapped condensate line out of the sanitary system), but that
# sink has no drain of its own yet (plans/TODO.md).

# Every register here drops into a boot in the second floor's joist bay (FS-S-EAST's
# I-joists for the three east bedroom boots at x=29'; FS-S-WEST's open-web trusses for the
# suite's REG-S-RET2 at x=9', since 2026-08-21), flush with the finished floor — the
# type's 1" height is the frame below it, not a kerb on top, so it still counts
# against a neighbour's clear floor space.
#
# The second storey went supply-less on the ERV on 2026-07-29: the three bedroom boots kept
# their uids (IFC GlobalId stability) but became stale-air pickups on DU-M-ERV-RET rather
# than the deleted DU-M-ERV-SUP. Fresh air now comes from REG-S-HP-BED1/2/3 and
# REG-S-HP-SUITE (REGISTERS_HVAC_SECOND above), so extracting here is what moves the
# storey's air: in at the hall soffit, out at the far wall of each room.
#
# Dropped for redundancy: REG-S-SUP6 (replaced by REG-S-HP-SUITE) and REG-S-SUP7/REG-S-RET1
# (the hall is the plenum, not a served room).
#
# REG-S-SUP1 (RM-S-PLANT) and REG-S-SUP2 (RM-S-STUDY2) went with the rest of the ERV's
# second-storey supply side on 2026-07-29, and the two rooms then stood unserved for six
# weeks — the plant room "awaiting its own mini-HRV", the study "taking air from the hall it
# opens onto". Both are back on 2026-08-16 as System 1 terminals, REG-S-HP-PLANT and
# REG-S-HP-STUDY2 in REGISTERS_HVAC_SECOND above, on the new DU-S-HP-SOUTH branch. The
# study was always the anomaly: EQ-S-HP1-AH hangs in that room's own ceiling soffit, and a
# room does not breathe by being next to the machine.
REGISTERS = [
    # One per bedroom now that the east bedrooms are equal 9'-0" bays: BED1 y 9'-18',
    # BED2 y 18'-27', BED3 y 27'-36'. RM-S-BED2 had no terminal at all before the
    # re-spacing (plans/TODO.md). All three sit at x=29', against the east wall and
    # diagonally opposite the hall-side supply grille, so the room crossventilates.
    Register(uid="CMR903AAAA", tag="REG-S-RET-BED1", kind=DuctSystem.RETURN, room="RM-S-BED1",
            position=pt(ft(29), ft(13, 6)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CMR907AAAA", tag="REG-S-RET-BED2", kind=DuctSystem.RETURN, room="RM-S-BED2",
            position=pt(ft(29), ft(22, 6)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CMR904AAAA", tag="REG-S-RET-BED3", kind=DuctSystem.RETURN, room="RM-S-BED3",
            position=pt(ft(29), ft(31, 6)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # The suite's extract is back at (9', 20') (2026-07-30, its original spot), after chasing
    # the supply grille's two relocations and briefly short-circuiting it at (9', 12'). (9',
    # 20') sits 7'+ from the current supply, east of FURN-S-SUITE-BED and clear of its foot zone.
    Register(uid="CMR906AAAA", tag="REG-S-RET2", kind=DuctSystem.RETURN, room="RM-S-SUITE",
            position=pt(ft(9), ft(20)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
]

# --- Distribution registers, all four storeys (ASHRAE 62.2 coverage) ----------------
# Stale air out of every wet room, fresh air into the living/sleeping rooms the ERV still
# supplies directly, all matched to rooms explicitly via room= (mep.ventilation_distribution).
# Storage rooms get nothing. On the second storey the ERV is now extract-only (see
# REGISTERS above), leaving just the two wet-room boots here plus the hall bath's grille.
#
# Wet-room pickups are EXHAUST, not RETURN — a bathroom's air is pulled and thrown away,
# never recirculated — and each states its airflow (2026-08-01, code.R303_3_local_exhaust):
# 20 cfm is ASHRAE 62.2's *continuous* local-exhaust rate (this ERV runs all the time, not
# a switched fan, so the 50 cfm intermittent figure doesn't apply). Five wet rooms at 20 cfm
# is 100 cfm of the machine's 210, made up by the balanced supply side.
REGISTERS_SECOND = [
    Register(uid="CSRV03AAAA", tag="REG-S-EXH3", kind=DuctSystem.EXHAUST, room="RM-S-SUITEBATH",
            position=pt(ft(14), ft(19)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-ERV-EXH",
            design_cfm=20,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CSRV04AAAA", tag="REG-S-EXH4", kind=DuctSystem.EXHAUST, room="RM-S-VANITY",
            position=pt(ft(3), ft(24, 4)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-ERV-EXH",
            design_cfm=20,
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    Register(uid="CSRV05AAAA", tag="REG-S-EXH1", kind=DuctSystem.EXHAUST, room="RM-S-BATH1",
            position=pt(ft(5), ft(32, 8)), duct_ref="DU-S-BATH1-EXH", type_ref="REG-T-ERV-EXH",
            design_cfm=20,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
]

# Main-storey terminals are ceiling grilles fed from the DUCTS_MAIN bays overhead. The
# kitchen is open plan inside RM-M-LIVING (no Occupancy.KITCHEN), so its stale pickup is
# placed by position — (33', 33'), over the counter run — and still carries the LIVING room=.
REGISTERS_MAIN = [
    Register(uid="CMRV01AAAA", tag="REG-M-SUP1", kind=DuctSystem.SUPPLY, room="RM-M-LIVING",
            position=pt(ft(27), ft(12)), duct_ref="DU-M1-ERV-SUP", type_ref="REG-T-ERV-SUP",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # REG-M-SUP2, the living room's second outlet at (30', 26'), is gone (2026-07-29): one
    # ERV outlet is right for an open-plan room at the whole-house rate; the pair was sized
    # as if this were a heating trunk.
    Register(uid="CMRV03AAAA", tag="REG-M-SUP3", kind=DuctSystem.SUPPLY, room="RM-M-BED",
            position=pt(ft(9), ft(6)), duct_ref="DU-M1-ERV-SUP", type_ref="REG-T-ERV-SUP",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV04AAAA", tag="REG-M-SUP4", kind=DuctSystem.SUPPLY, room="RM-M-STUDY",
            position=pt(ft(15, 8), ft(20)), duct_ref="DU-M1-ERV-SUP", type_ref="REG-T-ERV-SUP",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # The two baths are EXHAUST at 20 cfm each, like the second storey's — see the note over
    # REGISTERS_SECOND for why the whole wet-room set changed direction on 2026-08-01.
    Register(uid="CMRV05AAAA", tag="REG-M-EXH1", kind=DuctSystem.EXHAUST, room="RM-M-BATH1",
            position=pt(m(0.354668), m(7.86145)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-ERV-EXH",
            design_cfm=20,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV06AAAA", tag="REG-M-EXH2", kind=DuctSystem.EXHAUST, room="RM-M-BATH2",
            position=pt(ft(4), ft(18)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-ERV-EXH",
            design_cfm=20,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV07AAAA", tag="REG-M-RET3", kind=DuctSystem.RETURN, room="RM-M-LAUNDRY",
            position=pt(ft(10, 6), ft(20)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    Register(uid="CMRV08AAAA", tag="REG-M-RET5", kind=DuctSystem.RETURN, room="RM-M-LIVING",
            position=pt(m(6.36709), m(7.76418)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # RM-M-MUDROOM is stale-pickup only, no fresh-air outlet (reversed 2026-07-29 from an
    # earlier fresh-air-intake call). A mudroom is the room that smells; pressurising it pushes
    # that everywhere else. Extracting makes it the main storey's low-pressure end, so boundary
    # air moves toward the boots and the ERV recovers the heat. Same grille/hole/uid, direction
    # only — centred in the hallway strip between the two closets.
    Register(uid="CMRV09AAAA", tag="REG-M-RET-MUD", kind=DuctSystem.RETURN, room="RM-M-MUDROOM",
            position=pt(m(1.23013), m(9.56867)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # The one passive opening in the house (2026-08-15, plans/TODO.md): a louver in W-M-STRW
    # that lets the mudroom share the stair's air after EQ-M-HP3-STAIR moved off this wall.
    # No duct/damper/fan — `duct_ref` is None (the first register with none) and `kind` is
    # TRANSFER, so ventilation checks neither credit a room with fresh air nor double-count
    # a stale pickup beside REG-M-RET-MUD.
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
            position=pt(ft(27), ft(9)), duct_ref="DU-B-ERV-SUP", type_ref="REG-T-ERV-SUP",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # REG-B-SUP2 is back (2026-08-01), same hole and uid as before it was dropped on
    # 2026-07-29 for sharing the basement's open volume with the gym. That argument missed
    # the point: RM-B-PLAY-N is 324 sf of windowless habitable MEDIA space, legal only under
    # R303.1 Exception 1, whose second half requires outdoor air supplied to *the room* — an
    # adjacent room's grille doesn't satisfy it.
    Register(uid="CBRV02AAAA", tag="REG-B-SUP2", kind=DuctSystem.SUPPLY, room="RM-B-PLAY-N",
            position=pt(ft(27), ft(27)), duct_ref="DU-B-ERV-SUP", type_ref="REG-T-ERV-SUP",
            design_cfm=30,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    #
    # REG-B-RET1 is the workshop's light-fume pickup — a bench hood's worth of pull, not a
    # spray booth's, so it stays on the RETURN trunk rather than getting a dedicated exhaust.
    #
    # It moved from mid-floor (5', 8') to (4'-6", 4'-6") in a pass that wanted it over a
    # bench, and had to guess where a bench would go: there was no workbench placeable in the
    # room, so it was parked 18" south of ED-B-WORKSHOP-PANEL1 — a *light* also named "over a
    # bench" — with a note to move it when the bench was placed. That is the whole of
    # plans/TODO.md's workshop-ERV residual, and 2026-08-22 closes it: the benches exist
    # (FURN-B-WORKSHOP-BENCH-N/S), they run the west wall from y=3'-6" to y=13'-6" with their
    # tops at 34", and this now hangs over the middle of that run at x=2'-0", 3" out from the
    # 15"-deep bench line so the grille pulls across the work surface rather than off its back
    # edge.
    Register(uid="CBRV03AAAA", tag="REG-B-RET1", kind=DuctSystem.RETURN, room="RM-B-WORKSHOP",
            position=pt(ft(2), ft(8, 6)), duct_ref="DU-B-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # The sauna's stale pickup moved from ceiling to wall (2026-07-29), 4" above the floor on
    # the south face below FURN-B-SAUNA-BENCH-S: a sauna stratifies hard, so the low pickup
    # pulls the cold spent layer off the floor rather than the löyly at bench height. Paired
    # with REG-B-SUP3 over the heater, both ends dampered (REG-T-ERV-SAUNA-*), it drives the
    # room's convection loop — down the far wall, across the floor, out under the bench.
    # EXHAUST at 20 cfm since 2026-08-01: the room is Occupancy.BATHROOM and its window's
    # openable area (1.2 sf) falls short of R303.3's 1.5 sf, so mechanical exhaust governs.
    Register(uid="CBRV04AAAA", tag="REG-B-EXH2", kind=DuctSystem.EXHAUST, room="RM-B-SAUNA",
            position=pt(ft(11, 5.5), ft(1, 3.5)), duct_ref="DU-B-ERV-RET",
            type_ref="REG-T-ERV-SAUNA-EXH", design_cfm=20,
            mount=Mount(kind=MountKind.WALL, elevation=inch(4))),
    # Fresh air in high, over the stones, directly above EQ-B-SAUNA-HTR (west liner,
    # plan/electrical.py) at 7'-0" — below the 8' ceiling so the DU-B-SAUNA-SUP boot doesn't
    # fight the drop ceiling the condensate line already runs above.
    Register(uid="CBRV06AAAA", tag="REG-B-SUP3", kind=DuctSystem.SUPPLY, room="RM-B-SAUNA",
            position=pt(ft(9, 9.8125), ft(8, 9)), duct_ref="DU-B-SAUNA-SUP",
            type_ref="REG-T-ERV-SAUNA-SUP",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(7))),
    # RM-B-BATH (2026-07-30). Filed as EXHAUST rather than RETURN, like RM-S-BATH1's terminal
    # and unlike the basement's other two stale pickups: a bathroom's air is pulled and not
    # recirculated. It sits over the water closet at the room's west end, the far corner from
    # the door, so the room's makeup air crosses it on the way through.
    Register(uid="CBRV05AAAA", tag="REG-B-EXH1", kind=DuctSystem.EXHAUST, room="RM-B-BATH",
            position=pt(ft(11, 8), ft(20)), duct_ref="DU-B-ERV-BATH",
            type_ref="REG-T-ERV-EXH", design_cfm=20,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
]

# One attic ERV terminal now (2026-07-30): the extract. Four became a balanced pair on
# 2026-07-29 (REG-A-SUP2/SUP3 gone), then the supply half went too when REG-A-SUP1 was
# retired by REG-A-HP-WEST (the floor boot off System 1, REGISTERS_HVAC_ATTIC above), which
# conditions RM-A-WEST instead of just ventilating it. What's left is the stale pickup on a
# 4'-0" branch off the maintenance shaft — fresh in off System 1, stale out here, same
# pattern as every other storey. The attic is one cathedral volume, so one extract suffices.
REGISTERS_ATTIC = [
    Register(uid="CARV04AAAA", tag="REG-A-RET1", kind=DuctSystem.RETURN, room="RM-A-WEST",
            position=pt(ft(6), ft(31, 4)), duct_ref="DU-A-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
]
