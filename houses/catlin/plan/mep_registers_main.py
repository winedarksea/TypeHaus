# haus: editable
# Catlin MEP — air terminals on the main storey. plan/mep.py re-exports the lists below
# (AGENTS.md §1.1); the ERV terminals' flows are named in plan/erv_balance.py.

from typehaus import (
    DuctSystem,
    Mount,
    MountKind,
    Register,
    RoughOpening,
    deg,
    from_node,
    ft,
    inch,
    pt,
)
from typehaus.model import Location, WallAttachment

from .erv_balance import (
    REG_M_EXH1,
    REG_M_EXH2,
    REG_M_RET3,
    REG_M_RET5,
    REG_M_RET_MUD,
    REG_M_RET_STUDY,
    REG_M_SUP1,
    REG_M_SUP3,
    REG_M_SUP4,
)

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
            type_ref="REG-T-ERV-VALVE-SUP", design_cfm=REG_M_SUP1,
            mount=Mount(kind=MountKind.CEILING)),
    # No second living-room outlet: one ERV outlet is right for an open-plan room at the
    # whole-house rate; a pair would be sized as if this were a heating trunk.
    # ** MOVED 2'-0" WEST, 2026-09-20, TO CLEAR ED-M-BED-FAN. ** This sat at (9'-0", 6'-0"),
    # which is RM-M-BED's `Room.seed` and not a chosen station — and the room centre is now
    # the fan's. 6" apart, a 52" fan canopy and a 6" register physically overlap, and the
    # engine grades no device-vs-device collision. 7'-0" keeps it on DU-M-ERV-R-BED's own
    # east leg along y=6'-0" (that run's last point shortens; no new turn, no re-route) and
    # leaves 2'-2" to the fan hub, so the 15 cfm supply is not blowing into the motor.
    # D-M-BED2 is sealed (auto bottom), so these 15 cfm leave under D-M-BATH2 to REG-M-EXH2:
    # D-M-BATH2 keeps its 3/4" undercut (notes/interior_door_schedule.md).
    Register(uid="CMRV03AAAA", tag="REG-M-SUP3", kind=DuctSystem.SUPPLY, room="RM-M-BED",
            position=pt(inch(83.75), inch(71.25)), duct_ref="DU-M-ERV-R-BED",
            type_ref="REG-T-ERV-VALVE-SUP", design_cfm=REG_M_SUP3,
            mount=Mount(kind=MountKind.CEILING)),
    # ================== RM-M-STUDY-CLOSET: THE CALL BOOTH'S TWO TERMINALS ==================
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
    # ** (14'-8", 20'-8") SINCE 2026-11-10. ** The duct drops onto the valve's collar on a stock
    # 90 now, and east of PR-B-CW-SUITE (x=183") the suite's pipes leave no room over the
    # low tier to drop from; the history below is the old (17'-2") position.
    # (17'-2", 20'-8") on the ceiling. ED-M-STUDY-SPOT is at (17'-6 5/8", 21'-9 1/2"), so this is
    # 4 5/8" west and 13 1/2" south of directly above the sconce, three feet over it.
    # FS-S-WEST's bays centre on 8" + n*16", so 20'-8" is a bay; the sconce's 21'-9 1/2"
    # is 5 1/2" past the joist at 21'-4". Reaching its line would jog across that joist
    # directly over W-M-C3, which
    # is the bearing end of the truss — the one place the hole chart forbids outright, and
    # the same objection that kept the terminal off the east WALL yesterday. The x is as far
    # east as a 7" grille goes: the face reaches 17'-5 1/2", 3 1/8" clear of W-M-C3's study
    # face and 3 3/4" clear of its top plate.
    Register(uid="CMRV04AAAA", tag="REG-M-SUP4", kind=DuctSystem.SUPPLY, room="RM-M-STUDY-CLOSET",
            position=pt(ft(14, 8), inch(248.6)), duct_ref="DU-M-ERV-R-STUDY",
            type_ref="REG-T-ERV-VALVE-SUP", design_cfm=REG_M_SUP4,
            mount=Mount(kind=MountKind.CEILING)),
    # -- the extract, low, and NOT on the east wall -----------------------------------
    #
    # ** THE OWNER ASKED FOR THE EAST WALL AND THE EAST WALL DOES NOT EXIST. ** Measured off
    # the resolved layer polygons rather than off the plan's look:
    #   * W-M-C3's study face runs y 18'-0"..22'-1 5/8" — 4'-1 5/8" of wall;
    #   * D-M-STUDY's RO takes y 18'-2 3/8"..21'-0 11/16" of it, leaving one 12 15/16"
    #     sliver at the north end (the sliver ED-M-STUDY-SPOT and ED-M-STUDY-SW share);
    #   * The refitted bench is 48 5/8" wide, y ~245.743"..266.563"; north remains bench.
    # The bench covers the sliver to within 3/4". There is no low east wall to cut a grille
    # into, and freeing one means shortening the bench by 7" and opening a dead pocket in
    # the corner — a worse trade than moving the grille one wall.
    #
    # So it is the SOUTH wall's east end, which is the only low wall this room has left:
    # FURN-M-STUDY-DESK holds x 165 3/16"..194 3/16", the east wall is door, the north
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
    # hanging down the wall it is hinged to — now 12 1/2" to 28 1/2" across the pocket, straight
    # over a grille whose face is 8 1/2"..15 1/2". Folding it up instead would have buried
    # ED-M-STUDY-RC1 at 32" and cut 12" above the wainscot cap; the grille was the cheaper
    # thing to move. **THE GENERAL LESSON: a placeable's STOWED envelope is load-bearing on
    # the MEP, and the model holds no geometry for it at all.** FT-STUDY-DESK-LEAF is drawn
    # deployed (18" x 20" on the floor); the 18" x 20" of SOUTH WALL it covers when folded
    # is specified in notes/study_booth.md. Re-read it before putting anything back on
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
    # Hosted on W-M-CLN2's study face, back to the wall (it sits in the corner with W-M-LS,
    # which the host codemod could not choose between).
    Register(uid="H6C6RD9NED", tag="REG-M-RET-STUDY", kind=DuctSystem.RETURN, room="RM-M-STUDY-CLOSET",
            duct_ref="DU-M-ERV-R-LAUNDRY",
            type_ref="REG-T-ERV-VALVE-EXH-WALL", design_cfm=REG_M_RET_STUDY,
            mount=Mount(kind=MountKind.WALL, elevation=inch(12)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-M-CLN2", face="left", distance_from_start=inch(11.5),
                normal_gap=inch(0), rotation_offset=deg(180)))),
    # The two baths are EXHAUST at 20 cfm each, like the second storey's — see the note over
    # REGISTERS_SECOND for why the whole wet-room set changed direction on 2026-08-01.
    # On its run's line (24'-6") and 2" west (2026-11-10): the run climbs 4 3/8" off the trunk
    # tap and drops onto the collar.
    Register(uid="CMRV05AAAA", tag="REG-M-EXH1", kind=DuctSystem.EXHAUST, room="RM-M-BATH1",
            position=pt(ft(1), ft(24, 6)), duct_ref="DU-M-ERV-R-BATH1",
            type_ref="REG-T-ERV-VALVE-EXH", design_cfm=REG_M_EXH1,
            mount=Mount(kind=MountKind.CEILING)),
    # BATH2's moved 2026-10-12 from (4'-0", 18'-0") by the tub to the 15'-4" bay, ~8" west of
    # the shower's front glass (x 4'-10 5/8"). That glass stops at 90" under a 106" ceiling,
    # so steam spilling over its open top is caught here at the source. Kept OUTSIDE the
    # enclosure on purpose, at 20 cfm: the ERV has no headroom to boost
    # (notes/bath2_shower.md). Clear of ED-M-BATH2-CAN1 at (2'-10", 15'-0 1/2"), and 2 1/4"
    # north of the bay centre so its branch passes the can (2026-11-08).
    Register(uid="CMRV06AAAA", tag="REG-M-EXH2", kind=DuctSystem.EXHAUST, room="RM-M-BATH2",
            position=pt(ft(4, 4), inch(186.25)), duct_ref="DU-M-ERV-R-BATH2",
            type_ref="REG-T-ERV-VALVE-EXH", design_cfm=REG_M_EXH2,
            mount=Mount(kind=MountKind.CEILING)),
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
    # and passing. At the 19'-4" bay centre on its own branch, DU-M-ERV-R-RET3, off
    # LAUNDRY's crown (2026-11-10): a ceiling collar takes a run end, not a pass-by.
    Register(uid="CMRV07AAAA", tag="REG-M-RET3", kind=DuctSystem.RETURN, room="RM-M-LAUNDRY",
            position=pt(inch(106.875), ft(19, 4)), duct_ref="DU-M-ERV-R-RET3",
            type_ref="REG-T-ERV-VALVE-EXH", design_cfm=REG_M_RET3,
            mount=Mount(kind=MountKind.CEILING)),
    Register(uid="CMRV08AAAA", tag="REG-M-RET5", kind=DuctSystem.RETURN, room="RM-M-LIVING",
            position=pt(ft(20, 10.7), ft(21, 9.75)), duct_ref="DU-M-ERV-R-KITCH",
            type_ref="REG-T-ERV-VALVE-EXH", design_cfm=REG_M_RET5,
            mount=Mount(kind=MountKind.CEILING)),
    # RM-M-MUDROOM is stale-pickup only, no fresh-air outlet (reversed 2026-07-29 from an
    # earlier fresh-air-intake call). A mudroom is the room that smells; pressurising it pushes
    # that everywhere else. Extracting makes it the main storey's low-pressure end, so boundary
    # air moves toward the boots and the ERV recovers the heat. Same grille/hole/uid, direction
    # only — centred in the hallway strip between the two closets.
    Register(uid="CMRV09AAAA", tag="REG-M-RET-MUD", kind=DuctSystem.RETURN, room="RM-M-MUDROOM",
            position=pt(ft(4, 4), ft(31, 4)), duct_ref="DU-M-ERV-R-MUD",
            type_ref="REG-T-ERV-VALVE-EXH", design_cfm=REG_M_RET_MUD,
            mount=Mount(kind=MountKind.CEILING)),
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
    # One stair-side plate covers a cut in the painted MDO; the coat nook behind is open.
    # Keep the hosted station in its existing clear bearing-wall bay. The 42in mount is
    # the face bottom above finished LVP, not the centre of the nominal 12x10 opening.
    Register(uid="MW7W7SBZ65", tag="REG-M-XFER-MUD", kind=DuctSystem.TRANSFER, room="RM-M-LIVING",
            type_ref="REG-T-TRANSFER-MUD-1210",
            mount=Mount(kind=MountKind.WALL, elevation=ft(3, 6)),
             location=Location(attachment=WallAttachment(
                 wall_ref="W-M-STRW", face="left", distance_from_start=inch(17.125),
                 normal_gap=inch(0), rotation_offset=deg(-180)))),
]


# Cut only the painted 1/2in MDO on the stair side (left/exterior). The sill is off
# W-M-STRW's wall datum, while the register's 42in mount is its FACE BOTTOM above LVP.
# Face centre: 42 + 1.02559055 + 11.75/2 = 48.90059055in; nominal hole bottom is 5in lower.
TRANSFER_PANEL_OPENINGS_MAIN = [
    RoughOpening(uid="MUDXFER001", tag="AO-M-XFER-MUD", host="W-M-STRW",
                 position=from_node("N-M-N2", inch(11.125)),
                 width=inch(12), height=inch(10), sill_height=inch(43.90059055),
                 depth=inch(0.5), depth_from="exterior", framing_required=False),
]
