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
# soffit — the boot is a detail, not a run, so it carries no DuctRun of its own; the
# grille's `duct_ref` names the trunk it comes off. All of them are ceiling grilles in the
# soffit face at 8'-0" (9'-0" ceiling less the 12" drop).
#
# RM-S-SUITE is in EQ-S-HP1-AH's zone_rooms and has its terminal: REG-S-HP-SUITE, off the
# DU-S-HP-SUITE branch above. Since the 2026-07-30 reroute the branch enters over D-S-SUITE
# and runs down the suite's entry arm to about the bathroom door, and the grille sits at
# the branch's west terminus (12'-6", 14'-1 7/8") in SF-S-SUITE's west end face, throwing
# the rest of the way down the arm and into the suite's main volume where the arm opens
# out at x=9'-7 1/2".
#
# The suite's ERV supply (REG-S-SUP6) is gone rather than kept alongside: this branch is
# what makes it redundant.
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
    # The one return, at the hall's south end right AT EQ-S-HP1-AH (2026-07-30): the
    # unit's rear face is y=9'-7" and the grille centres 1" north of it in the soffit
    # face, feeding the unit's bottom-return through DU-S-HP-RET's 6" plenum stub. Behind
    # this grille is where DU-S-ERV-HP-FEED's wye injects the ERV's fresh air (see
    # DUCTS_HVAC_SECOND): fresh mixes into the return plenum, not into a hard-coupled duct,
    # so either machine runs alone. 7'-10" — the soffit face, same plane as the hall cans.
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
    # Directly above the hall soffit (2026-07-30): the trunk runs at x=19'-4" below, so
    # the boot rises straight through FS-ATTIC into the floor grille — no attic duct run
    # at all. y=10' keeps the grille a foot inside RM-A-EAST's south wall (y=9') and
    # clear of FO-A-STAIR's walkway (the opening ends at y=8'-9 5/8").
    Register(uid="CARH02AAAA", tag="REG-A-HP-EAST", kind=DuctSystem.SUPPLY,
             room="RM-A-EAST", position=pt(ft(19, 4), ft(10)), duct_ref="DU-S-HP-SUP",
             type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
    # RM-A-WEST's supply (2026-07-30): a floor boot straight up off DU-S-HP-SUITE through
    # FS-ATTIC — the branch runs at y=14'-1 7/8" directly below, so the boot is one bay's
    # rise, landing just west of the centre bearing wall roughly over D-S-SUITE. This is
    # what retired REG-A-SUP1 and its DU-A-ERV-SUP trunk: the west attic room now gets
    # conditioned air off System 1 like RM-A-STUDY/RM-A-EAST do, and gives stale air back
    # at REG-A-RET1 (REGISTERS_ATTIC), so the ERV's attic side is extract-only, the same
    # pattern as the second storey.
    Register(uid="CARH03AAAA", tag="REG-A-HP-WEST", kind=DuctSystem.SUPPLY,
             room="RM-A-WEST", position=pt(ft(16, 6), ft(14, 1.875)),
             duct_ref="DU-S-HP-SUITE", type_ref="REG-T-HP-SUP",
             mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
]

# CONDENSATE — planned plumbing item, no geometry this pass. Each of the four indoor units
# (EQ-S-HP1-AH and the three heads) makes condensate in cooling; the two wall heads on
# interior walls and the ducted unit gravity-drain into a collected air-gap drain line that
# terminates over the mechanical-room sink, which is what keeps a trapped condensate line
# out of the sanitary system. Nothing is modeled here yet: the line needs the plumbing pass
# that gives the mechanical-room sink its own drain (plans/TODO.md).

# Every register here drops into a boot in the FS-SECOND joist bay, so the grille face lands
# flush with the finished floor and the type's 1" height is the frame below it, not a kerb
# standing on it. Saying so keeps a register out of a neighbour's clear floor space without
# exempting registers as a class — a surface-mounted one would still report.
#
# The second storey went supply-less on the ERV on 2026-07-29. The three bedrooms' boots
# are still here and still in the same holes — same uids, so the IFC GlobalIds survive a
# rename that would otherwise churn every downstream reference — but they are stale-air
# pickups now, on DU-M-ERV-RET rather than the deleted DU-M-ERV-SUP. The bedrooms' fresh
# air comes from REG-S-HP-BED1/2/3 off DU-S-HP-SUP (REGISTERS_HVAC_SECOND above), and the
# suite's from REG-S-HP-SUITE off DU-S-HP-SUITE, so extracting here rather than supplying
# is what makes the storey's air actually move: in at the hall soffit, out at the far wall
# of each room.
#
# Two terminals were dropped outright rather than converted:
#   REG-S-SUP1 (RM-S-PLANT) — the plant room is getting its own dedicated mini-HRV, whose
#     humidity load has nothing to do with the whole-house rate; it is not drawn yet, so
#     mep.ventilation_distribution honestly reports RM-S-PLANT as unserved until it is.
#   REG-S-SUP2 (RM-S-STUDY2) — dropped by the user's 2026-07-29 call; the study takes its
#     air from the hall it opens onto. Also honestly reported.
# And two more for redundancy: REG-S-SUP6 (RM-S-SUITE, replaced by REG-S-HP-SUITE) and
# REG-S-SUP7/REG-S-RET1 (the hall, which is the plenum between them, not a served room).
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
    # The suite's extract is back at (9', 20') (2026-07-30, its original spot). It chased
    # the supply grille twice: when REG-S-HP-SUITE first landed at (8'-6", 20'-4") this
    # moved south to (9', 12') to break the ceiling-supply-over-floor-extract short
    # circuit; then the branch reroute put the supply at (12'-6", 14'-1 7/8") and (9', 12')
    # became the short circuit — ~4' away in plan. (9', 20') is 7'+ from the new supply,
    # on the same trunk, east of FURN-S-SUITE-BED (x 2'-6"..7'-6") and clear of its foot
    # zone.
    Register(uid="CMR906AAAA", tag="REG-S-RET2", kind=DuctSystem.RETURN, room="RM-S-SUITE",
            position=pt(ft(9), ft(20)), duct_ref="DU-M-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
]

# --- Distribution registers, all four storeys (ASHRAE 62.2 coverage) ----------------
# Stale air out of every wet room, fresh air into the living/sleeping rooms the ERV still
# supplies directly, all matched to rooms explicitly via room= (mep.ventilation_distribution).
# RM-S-NCLOSET and the other storage rooms get nothing. On the second storey the ERV is now
# extract-only (see REGISTERS above): what is left here is the two wet-room boots off the
# FS-SECOND return trunk plus the hall bath's ceiling grille on the EXHAUST run in the
# FS-ATTIC bay over the shower.
#
# The wet-room pickups are EXHAUST, not RETURN, and each states the airflow it is balanced
# to (2026-08-01, code.R303_3_local_exhaust). Two things were wrong before: a bathroom's air
# is pulled and thrown away, never recirculated — which is what DuctSystem.EXHAUST means and
# what RM-B-BATH and RM-S-BATH1 already said — and no terminal in the house stated a cfm, so
# R303.3 could not tell a 20 cfm grille from a decorative one. 20 cfm each is ASHRAE 62.2's
# *continuous* local-exhaust rate, which is the rate that applies here: this is an ERV that
# runs all the time, not a fan on a timer, and the 50 cfm figure is the intermittent
# alternative for a fan someone has to remember to switch on.
#
# Five wet rooms at 20 cfm is 100 cfm of the machine's 210, which is what the balanced supply
# side has to make up and does.
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
    # REG-M-SUP2, the living room's second outlet at (30', 26'), is gone (2026-07-29). One
    # ERV outlet is what an open-plan room at the whole-house rate wants; the pair was
    # sized as if this were a heating trunk.
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
            position=pt(ft(33), ft(33)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # RM-M-MUDROOM is stale-pickup only, no fresh-air outlet — the user reversed the earlier
    # call on 2026-07-29, and this comment used to argue the opposite ("fresh-air intake
    # only... positive pressure against the door"). A mudroom is the room that smells: wet
    # coats, boots, the dog, and whatever comes in off the drive through the door beside it.
    # Pressurising it pushes that everywhere else in the house. Extracting from it makes the
    # mudroom the low-pressure end of the main storey, so the boundary air moves toward the
    # boots instead of away from them, and the ERV recovers the heat on the way out.
    #
    # Same grille, same hole, same uid — only the direction changed. Centred in the hallway
    # strip between the two closets, clear of both, in line with the window/bench.
    Register(uid="CMRV09AAAA", tag="REG-M-RET-MUD", kind=DuctSystem.RETURN, room="RM-M-MUDROOM",
            position=pt(m(1.23013), m(9.56867)), duct_ref="DU-M1-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(9))),
    # The one passive opening in the house (2026-08-15, plans/TODO.md). EQ-M-HP3-STAIR used
    # to be recessed *into* W-M-STRW so a single head reached both the stair and the mudroom
    # through the cutout; it has moved to the north wall at the NW corner, so this louver is
    # now how the mudroom gets its share. No duct, no damper, no fan: `duct_ref` is None —
    # the first register in the house with none — and `kind` is TRANSFER so the ventilation
    # checks neither credit a room with fresh air it is not getting nor count it as a second
    # stale pickup beside REG-M-RET-MUD.
    #
    # *** THE ROOM THIS SERVES IS RM-M-MUDROOM. `room` says RM-M-LIVING. ***
    # Both are true and the field only holds one. A transfer opening is the one placeable
    # that belongs to two rooms at once, and the resolver reads `room` as containment — it
    # compares the footprint centre against the room polygon and files an
    # integrity.placeable_room_mismatch when they disagree. The 1" plate is on the *stair*
    # face of W-M-STRW, and the stair well is RM-M-LIVING, so RM-M-LIVING is what keeps the
    # build log honest. The mudroom side of the relationship lives in this comment and in
    # the tag, which is why the tag is XFER-MUD and not XFER-STAIR.
    #
    # It is REG-M-RET-MUD that makes the thing work at all. A hole between two rooms moves
    # nothing without a pressure difference, and the mudroom is the low-pressure end of the
    # main storey by design (see the note on that register): the ERV pulls out of it
    # continuously, so what comes back in is the stair air this louver hands over, warmed by
    # the head 2'-6" away round the corner.
    #
    # Geometry, all of it constrained:
    #   x  10'-3 7/8" — a 1" body with its back on W-M-STRW's ply-stair face at 10'-3 3/8",
    #      facing east into the well (rotation 90 backs it west, the same sense the head used
    #      on this wall). The mudroom side needs no opening at all: that face is bare 2x6
    #      bays (the coat nooks), so the bay behind this louver is already the room.
    #   y  34'-0" — dead centre of the 14 1/2" clear bay between the studs at 33'-4" and
    #      34'-8". W-M-STRW is BEARING; the bay north of it is only 7 1/8" clear (the corner
    #      end stud sits at 35'-4 5/8"), and the 12" face will not fit there without cutting
    #      a stud and heading it. This is the bay, not a preference.
    #   z  7'-6" — top at 8'-4", 8" under the 9' ceiling, in the same high band as the head's
    #      7'-0"..8'-0" body, and well over D-M-ENTRY's head just west of it.
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
    # REG-B-SUP2 is back (2026-08-01), in its old hole at (27', 27') and on its old uid so
    # the IFC GlobalId is the one it had. It was dropped on 2026-07-29 on the argument that
    # the media room shares the basement's open volume with the gym and takes its air through
    # the opening between them — true as far as air goes, and beside the point for this room:
    # RM-B-PLAY-N is 324 sf of habitable MEDIA space with no glazing at all, so it is legal
    # only under R303.1 Exception 1, and the exception's second half is outdoor air supplied
    # to *the room*. An adjacent room's grille does not satisfy it, and neither does an
    # opening between them.
    Register(uid="CBRV02AAAA", tag="REG-B-SUP2", kind=DuctSystem.SUPPLY, room="RM-B-PLAY-N",
            position=pt(ft(27), ft(27)), duct_ref="DU-B-ERV-SUP", type_ref="REG-T-ERV-SUP",
            design_cfm=30,
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    #
    # REG-B-RET1 moved off the middle of the floor (it was at (5', 8')) and onto the
    # workbench line at (4'-6", 4'-6") — the pickup is there for light fume handling
    # (plans/TODO.md: "an ERV intake in the workshop (this one over a bench for light fume
    # handling)"), which only works if it is over the bench and not over the aisle. Solder,
    # a can of finish, a bit of glue: this is a bench hood's worth of pull, not a spray
    # booth's, and it is deliberately on the RETURN trunk rather than a dedicated exhaust.
    # NOTE the bench itself is not modeled yet — no Furniture in RM-B-WORKSHOP — so the
    # position is taken from ED-B-WORKSHOP-PANEL1 (plan/lighting.py), the flat panel
    # authored explicitly as the light "over a bench" in the west bay — offset 18" south of
    # the panel so the two are not the same ceiling point. When the workbench is placed,
    # this register moves with it.
    Register(uid="CBRV03AAAA", tag="REG-B-RET1", kind=DuctSystem.RETURN, room="RM-B-WORKSHOP",
            position=pt(ft(4, 6), ft(4, 6)), duct_ref="DU-B-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.CEILING, elevation=ft(8))),
    # The sauna's stale pickup came off the ceiling on 2026-07-29 and went to the wall, 4"
    # above the finished floor on the south concrete face (y=1'-0") directly below
    # FURN-B-SAUNA-BENCH-S, whose 18" top clears it completely. This is the whole point of a
    # sauna's extract: the room stratifies hard, the löyly you want to keep is at bench
    # height and above, and the air you want gone is the cold, stale, spent layer sitting on
    # the floor. A ceiling grille at 8' pulls the good air straight out. Paired with
    # REG-B-SUP3 over the heater, it makes the convection loop the room needs — down the
    # far wall, across the floor, out under the bench — and both ends are dampered
    # (REG-T-ERV-SAUNA-*) so the loop can be shut during a session and opened after one.
    # EXHAUST at 20 cfm since 2026-08-01 (code.R303_3_local_exhaust). The room is
    # Occupancy.BATHROOM and R303.3 reaches it: it has a 14x24 window whose openable half is
    # 1.2 sf, short of the section's 1.5 sf, so the mechanical path is the one that carries
    # it. The direction was always what this grille did — spent air out of a sealed hot room
    # is not air to recirculate — and the loop the comment above describes is unchanged.
    Register(uid="CBRV04AAAA", tag="REG-B-EXH2", kind=DuctSystem.EXHAUST, room="RM-B-SAUNA",
            position=pt(ft(11, 5.5), ft(1)), duct_ref="DU-B-ERV-RET",
            type_ref="REG-T-ERV-SAUNA-EXH", design_cfm=20,
            mount=Mount(kind=MountKind.WALL, elevation=inch(4))),
    # Fresh air in high, over the stones. EQ-B-SAUNA-HTR is at (9'-9 13/16", 8'-9") on the
    # west liner (plan/electrical.py); this sits directly above it at 7'-0", below the 8'
    # ceiling so the boot can turn out of DU-B-SAUNA-SUP without fighting the drop ceiling
    # the condensate line already runs above.
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
# 2026-07-29 (REG-A-SUP2/SUP3 gone, the pair moved to the NW corner beside the maintenance
# shaft at (1', 34'-6") where the radon/plumbing riser rises through every storey), and then
# the supply half went too — REG-A-SUP1 was retired by REG-A-HP-WEST, the floor boot off
# System 1's DU-S-HP-SUITE branch (REGISTERS_HVAC_ATTIC above), which conditions RM-A-WEST
# instead of just ventilating it. What is left is the stale pickup on a 4'-0" branch off the
# shaft: fresh in off System 1, stale out here, the same in-at-the-supply / out-at-the-ERV
# pattern as every other storey. The attic is one cathedral volume across the knee walls, so
# one extract still turns the floor over.
REGISTERS_ATTIC = [
    Register(uid="CARV04AAAA", tag="REG-A-RET1", kind=DuctSystem.RETURN, room="RM-A-WEST",
            position=pt(ft(6), ft(31, 4)), duct_ref="DU-A-ERV-RET", type_ref="REG-T-ERV-EXH",
            mount=Mount(kind=MountKind.FLOOR, recessed_into_host_surface=True)),
]
