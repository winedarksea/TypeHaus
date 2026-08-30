# haus: editable
# Permit-schedule plumbing fixture/appliance *instances* for Catlin (M3 WP3.4/WP3.10).
# `# haus: editable` so UI drags (moving a toilet, the washer, …) round-trip to source.
# Their FixtureType/ApplianceType catalog lives in the non-editable `library/placeables/`
# at the repo root (it uses `frozenset(...)`, which the editable dialect forbids). The
# house-local `fixture_types.py` this line used to name went away in the `3d3973a` dedupe.

from typehaus import Appliance, Fixture, Mount, MountKind, deg, ft, inch, pt
from typehaus.model import m

# --- basement (2026-07-30 plumbing pass) -----------------------------------------------
# Both RM-B-SAUNA fixtures drain under the slab to PR-B-MAIN-DRAIN, not a wall stack
# (as the retired FX-1 utility sink did; see plan/mep.py SLAB_STUBS).
#
# 36"x36" curbed pan in the NE corner (only corner with both sides finished wall, at
# y=13'-6 3/16" and x=17'-2 1/2"); curbed rather than curbless because the floor drain at
# (13'-6", 12'-9") covers the rest of the wet floor. That drain sits at the sauna's
# 1/8"/ft slope's low point, positioned so a boxed corner chase can bring PR-B-COND's
# air-gap down over it and stay clear of D-B-SAUNA's leaf sweep. No slope field exists on
# Slab/FinishZone, so both slopes (and IRC P2708.1's 1/4"-1/2"/ft) live only in comments.
#
# Both fixtures chase through W-B-CS, not the closer W-B-SA-N partition, to keep
# W-B-SA-N's foil-faced polyiso vapour barrier unbreached; W-B-CS also gives a true vent
# stack path via W-M-C1 above. advisory.wet_wall_depth's 5.5" cavity requirement is a
# house preference, not code — it is not what drives this wall choice.
BASEMENT_FIXTURES = (
    Fixture(uid="CBQ802AAAA", tag="FX-B-SAUNA-SH", type_ref="FX-SHOWER-36",
            room="RM-B-SAUNA", position=pt(ft(15, 8.5), ft(12, 0.1875)),
            wall_ref="W-B-CS"),
    Fixture(uid="CBQ803AAAA", tag="FX-B-SAUNA-FD", type_ref="FX-FLOOR-DRAIN",
            room="RM-B-SAUNA", position=pt(ft(13, 6), ft(12, 9)), wall_ref="W-B-CS"),
    # RM-B-BATH (stair-foot bath, 3'-0" deep): each fixture backs an end wall so depth runs
    # along the 7'-0" length. WC is floor-mounted (owner's call, 2026-07-30), not wall-hung,
    # since the west end is 12" cast concrete and a wall-hung carrier would cost 6 1/2" of
    # furring. `wall_ref` on both is W-B-BA-N (north partition, not each one's backing
    # wall): it's the room's only stud cavity, carries their shared vent, and is a 5 1/2"
    # wet-wall (not 2x4) because a 3" WC branch needs the depth. Trap arms: 12" (WC), 17"
    # (lav), both well inside Table 1002.2's 6'-0"/3'-6" limits.
    Fixture(uid="CBQ801AAAA", tag="FX-B-BATH-WC", type_ref="FX-TOILET-STD",
            room="RM-B-BATH", position=pt(ft(11, 8), ft(20)), rotation=deg(90),
            wall_ref="W-B-BA-N"),
    # Same uid as the retired FX-1: this is that fixture relocated, not a new one. The
    # mechanical room's utility sink was the basement's only lavatory and the owner's decision
    # of 2026-07-30 moved it here, so the IFC GlobalId follows the fixture rather than being
    # retired with the tag. `drain_position` puts the trap 6" off the east wall face, under the
    # basin's back where the tailpiece actually drops, over SP-B-BATH-LAV.
    # ** A 36" VANITY SINCE 2026-08-30, AND THE DEPTH IS SET BY THE DOOR. ** This was an
    # FX-LAV-24 -- a bare 24" bowl on the east wall with nothing under it. The east wall is
    # 39.61" of clear run (y 218.38"..257.99" between W-B-CW2's and W-B-BA-N's finish
    # faces), which takes a 36" cabinet with 1.8" at each end.
    #
    # ** 18" DEEP, NOT 21", BECAUSE D-B-BATH'S SWING ARC REACHES THIS WALL. ** Tested
    # against the real ``swing_clearance`` polygon rather than its bounding box: a 21"-deep
    # cabinet is caught by the arc at EVERY position along the east wall, and an 18" one
    # clears at every position. That is the whole reason this room gets the shallow type,
    # and it is also the cheaper one -- see fixture_types.py on the big-box combo depth.
    #
    # Position is measured off the wall's own layer polygons, never off `Room.clear_face`.
    # Back at x=210" (W-B-CN2's face), so x 192"..210"; centred on the wall run at
    # y=238.19", so y 220.19"..256.19". The 21" front zone then reaches x=171", clear of
    # FX-B-BATH-WC's 24" front envelope, which ends at x=178".
    #
    # `drain_position` is unchanged and still correct: (17'-0", 20'-0") falls inside the new
    # carcass, 6" off the east wall face under the basin's back, over SP-B-BATH-LAV.
    Fixture(uid="5BBZTZNBWN", tag="FX-B-BATH-LAV", type_ref="FX-VANITY-36-SHALLOW",
            room="RM-B-BATH", position=pt(inch(201), inch(238.19)), rotation=deg(-90),
            wall_ref="W-B-BA-N", drain_position=pt(ft(17), ft(20))),
)

# ** RM-M-BATH1 IS 61.98" x 44.24" BETWEEN FINISH FACES, AND THAT IS WHY THE WALL-HUNG
# BOWL STAYS. ** (x 6.635"..68.615" off W-M-W2/W-M-BAE, y 271.385"..315.625" off
# W-M-HS1/W-M-STOS.) It was 42.24" deep until 2026-08-29, when W-M-STOS moved 2" north —
# see below. The room's resolved `clear_face` reads 70.73" x 46.73" and is NOT the
# number to design against: `resolve/rooms.py` polygonizes wall AXES and insets only the
# lining, so it hands back a room ~2.4"-3.4" oversize on every side. The older comment here
# ("3'-2" x 4'-3-1/4"") matched neither and is gone.
#
# ** FX-TOILET-STD DOES NOT FIT THIS ROOM IN ANY ORIENTATION. ** Asked and answered
# 2026-08-29; the arithmetic is here so it is not asked a third time.
#
# The governing dimension is 24" in front, and it is NOT the IRC's 21": Minn. R. 1309.0010
# subp. 3.D deletes IRC chapters 25-33 outright (only P2904 survives) and 1309.0307 replaces
# R307.1 with "Plumbing fixtures shall be installed in accordance with Minnesota Rules,
# chapter 4714". 4714.0050 adopts the 2018 UPC and ch. 4714 has no amendment to section 402,
# so UPC 402.5 stands unamended: 15" from the centreline to any side wall or obstruction, and
# "the clear space in front of any water closet or bidet shall be not less than twenty-four
# (24) inches." (Anoka's and Farmington's residential bathroom handouts both print 15"/24"
# and cite 402.5. The 21" people quote is IRC's, and the 21" dwelling-unit exception attached
# to it is a Washington amendment.) `_water_closet_required_clearance` encodes 24" as of
# 2026-08-29 and this house now sets `active_code_profile="MN/IRC"`, so the envelope really
# is graded rather than silently dropped — see plan/manifest.py.
#
# ** THE ROOM MISSED THAT BY 1.06" AND THE WALL MOVED, NOT THE TOILET. ** At the old
# 42.24" depth the 19.3" bowl left 22.94". No fixture change could close it: the shortest
# wall-hung bowl obtainable in the US is 18.90" (Duravit D-Code Compact, 480 mm; the TOTO RP
# Compact this type is modelled on is 19.29"), which still leaves 23.34", and every "450 mm"
# short-projection pan on the market turns out to be floor-standing back-to-wall, not
# wall-hung. So W-M-STOS went north 2" to y=26'-6" (plan/storeys/main.py) and the bowl now
# has 24.94". The cost was 2" off RM-M-MUD-CLOSET, 34 3/4" -> 32 3/4", the bottom of the
# 32"-36" reach-in band; the closet has no rod or shelf authored in it.
#
# ** FX-TOILET-STD STILL DOES NOT FIT THIS ROOM IN ANY ORIENTATION, EVEN AT 44.24". **
# Asked and answered 2026-08-29; the arithmetic is here so it is not asked a third time.
# On the south wall a 28"-deep bowl leaves 16.24" against the 24" it needs. Turned 90 degrees
# onto the west wall it DOES clear in front — 33.98" — but its 15"-each-side band is then 30"
# of the room's 44.24" depth and its front envelope reaches x=58.635", and there is no
# 18"x14" strip left anywhere for FX-M-BATH1-LAV: 14.24" north of the band, 14.24" south of
# it, 9.98" east of the envelope. The east wall is spoken for by D-M-BATH1's 24" opening at
# y 280"..304", and the north wall repeats the south wall's 16.24". This is a compact-fixture
# room by geometry, not by preference.
#
# One caveat on the check: `resolve/placeables.py::_clearance_conflicts` compares a required
# zone against PEER PLACEABLE FOOTPRINTS ONLY. It never asks whether the zone fits the room,
# so a water closet whose 24" runs into a wall still reports nothing. Every clearance figure
# above was measured by hand off the wall layer polygons.
#
# WC is a wall-hung compact on the south wall; rotation 180 turns bowl/front north, so the
# china's back lands ON W-M-HS1's finish face at y=271.385" — hence y=281.035" for a bowl
# 19.3" deep. It read 280.27" until 2026-08-29, which buried the back 3/4" in the wall.
#
# ** THE CARRIER IS IN W-M-HS1 AND `wall_ref` STILL SAYS W-M-BAE, ON PURPOSE. ** That is
# this file's documented idiom (see ATTIC_FIXTURES: wall_ref names the WET wall a fixture
# plumbs into, not the wall it hangs on). The bowl bolts to a frame in W-M-HS1 — retyped to
# INT_2X6_STAGGERED_PLUMBING on 2026-08-29 for FX-M-BATH2-WC, which is what makes it a legal
# home for one — and its 3" waste drops through the deck in that wall's own bay. From there
# PR-B-WC1-DRAIN runs to the W-M-BAE stack, which is where the vent takeoff
# (PR-M-WC-VENT, 49.8" away against Table 1002.2's 72" for 3") and the supply riser already
# are. Both walls are 5.5" of structure, so `advisory.wet_wall_depth` is satisfied either way.
#
# ** `drain_position` IS UNDER THE BOWL NOW, NOT 3'-10" AWAY FROM IT. ** It read
# (6'-0", 22'-7") — a point on W-M-BAE's axis, at the far corner of the room, with the china
# 46" west of the waste it was supposedly bolted to. A wall-hung bowl cannot be anywhere but
# on its carrier, so the two are one point: the bowl's own centreline, in W-M-HS1's bay.
# y=22'-4" is that wall's axis, which centres a 3.5"-OD pipe in the 5.5" cavity with 1" of
# cover each side; the manufacturers' nominal is 1 3/4" behind the frame face
# (library/placeables/fixtures.py), and 1" of that is spent on the frame's own set-back.
#
# The override is still required, and the reason is in the type: `_expected_drain_point`
# reads "no WATER_HOT" as "floor-drained, waste under the footprint", which is true of every
# other WC in this house and false of this one — the waste is a foot behind the china,
# inside the wall.
#
# y nudged +2" (2026-08-15), same reason as the lavatory's +6" nudge (2026-07-29):
# N-M-W2/N-M-C2 pushed north onto the west facade's 16" column module, dragging the
# room's south clear face with it.
#
# ** W-M-BAE IS THE WET WALL AND IT IS NOT A TYPO — checked and reverted 2026-08-30. **
# plans/TODO.md carried this as a stale reference on the reasoning that W-M-BAE is a
# *vertical* wall on the x = 6'-0" line while this bowl stands at x 1'-6.9"..2'-9.9" and
# backs onto W-M-HS1. The geometry is right and the conclusion is wrong: `Fixture.wall_ref`
# is the fixture's WET WALL for venting (`checks/mep/plumbing_dwv.vent_reachability` reads
# nothing else), not a backing wall the body touches. W-M-BAE stops at its own ceiling, so
# this WC takes the offset path — `PR-M-WC-VENT`, whose x = 6' leg is W-M-BAE's own stud
# bay (plan/mep_venting.py, and the comment there names both WC wet walls).
#
# Pointing it at W-M-HS1 does not fail: W-S-SN1 stacks over HS1, so the check reports the
# in-wall path and PASSES — silently orphaning PR-M-WC-VENT's bath1 leg. What catches it is
# `test_catlin_fixtures_all_reach_a_vent_chase`, which asserts this fixture is in the
# CHASE-vented set specifically.
MAIN_FIXTURES = (
    Fixture(uid="CMQ801AAAA", tag="FX-M-BATH1-WC", type_ref="FX-TOILET-WH", room="RM-M-BATH1",
            position=pt(m(0.670778), m(7.138289)), rotation=deg(180), wall_ref="W-M-BAE",
            mount=Mount(kind=MountKind.WALL, elevation=inch(1.375)),
            drain_position=pt(m(0.670778), ft(22, 4))),
    # y nudged +6" (2026-07-29, with N-M-W2/N-M-C2's north push for the BATH2 wall move):
    # the room's south face moved with it and the lavatory's old y left it poking through
    # into the hall (test_bath1_fixtures_sit_inside_the_room_and_clear_of_each_other).
    # ** A 24" VANITY SINCE 2026-08-30, AND IT USED TO SIT 2 1/2" INSIDE THE WALL. ** The
    # old FX-LAV-COMPACT (18" x 14", no cabinet) was placed at y=268.94", which is north of
    # W-M-HS1's finish face at y=271.39" -- it was authored off `Room.clear_face`, whose
    # north edge reads 268.64" because rooms.py polygonises wall AXES. Same class of error
    # as the one caught in RM-M-BATH2 on 2026-08-29; nothing checks a Fixture against a wall
    # face, so it built and checked clean for months. Fixed here along with the retype.
    #
    # ** 24" IS EVERYTHING THIS ROOM HAS. ** The wall-hung water closet takes the west half
    # of the north wall: its centreline is x=26.41", so its 15" side band ends at x=41.41",
    # and W-M-BAE's finish face is x=68.62". 27.21" of run, so a 24" cabinet
    # (x 41.5"..65.5") fits and a 30" one does not.
    #
    # ** 18" DEEP, THOUGH 21" WOULD NOW FIT. ** W-M-STOS moved 2" south on 2026-08-30, so
    # the room is 44.23" deep and a 21" carcass would clear its own front zone by 2.2".
    # It stays shallow because of the DOOR, not the clearance: D-M-BATH1's opening runs
    # y 280"..304" in the east wall, so every inch of depth is an inch further across the
    # doorway. At 18" this cabinet's south face is y=289.39" and overlaps the northern 9.4"
    # of that opening at x<65.5"; at 21" it would overlap 12.4". The door swings OUT, so
    # there is no swing conflict either way -- you simply enter through the southern ~15"
    # of the opening. The bowl it replaces had the same geometry 4" less badly. In a
    # 62" x 44" room with a water closet and a door there is no arrangement that avoids it,
    # and the trade is the room's first storage of any kind.
    Fixture(uid="CMQ802AAAA", tag="FX-M-BATH1-LAV", type_ref="FX-VANITY-24-SHALLOW",
            room="RM-M-BATH1", position=pt(inch(53.5), inch(280.39)), wall_ref="W-M-BAE",
            rotation=deg(180)),
    # 2026-08-29, the drop-in bath pass: this bowl finally backs onto a wall. It had stood
    # free in the middle of the floor with its tank 9 3/4" clear of anything since the
    # 2026-07-29 wall move, and `wall_ref` said W-M-BA2E — a wall it was 5'-5" away from.
    # Both are fixed here: it backs W-M-HS1 (retyped to the plumbing assembly for it, see
    # storeys/main.py) at rotation 0, which is the rotation that puts the tank on +y.
    #
    # x=2'-6" is bounded on BOTH sides and there is not much room between them. P2705.1
    # wants 15" clear each side of the centreline: west of 1'-9 5/8" the envelope runs into
    # W-M-W3's face, east of 3'-1" it runs into the tub deck's west face at x=4'-4". 2'-6"
    # sits near the middle of that 1'-3 3/8" band, 7" clear of the deck.
    # y=20'-10 5/8" is the bowl centre with its tank on the wall's new face (22'-0 5/8"
    # less the type's 14" half-depth). The 21" front clearance then reaches to y=17'-11 5/8"
    # and clears FX-M-BATH2-SINK's south end by 1 1/4" — the tightest dimension in the room
    # and the one to re-check if that sink ever moves north.
    #
    # No `drain_position`: the convention (under the bowl) is correct, and PR-B-WC2-DRAIN
    # follows the bowl to its new flange rather than the reverse.
    Fixture(uid="CMQ803AAAA", tag="FX-M-BATH2-WC", type_ref="FX-TOILET-STD", room="RM-M-BATH2",
            position=pt(ft(2, 6), ft(20, 10.615)), rotation=deg(0), wall_ref="W-M-HS1"),
    # BATH2 has separate bathing fixtures: the 36" shower at the south end of the east
    # plumbing wall, the bath north of it. They are intentionally separate instances/types
    # rather than a tub-shower combination, so the permit schedule and future owner
    # selections can treat them independently — and since 2026-08-29 the bath is a drop-in,
    # which a combination unit could not be.
    #
    # The shower moved 4 1/4" SOUTH on 2026-08-29, hard against W-M-BDN1's face at
    # y=13'-2 3/8", and that 4 1/4" is the whole integration: the shower's north face and
    # the tub deck's south face are now the SAME LINE (y=16'-2 3/8"), so W-M-TUBDK-S is one
    # framed 2x4 run doing both jobs — the deck's south knee wall on its north side, the
    # shower's north wall on its south. The two wet fixtures read as one built element
    # down the east wall instead of two boxes with a 4" slot of dead floor between them.
    # The room's depth is spent exactly: 36" of shower + 70 1/4" of deck = 106 1/4" clear.
    #
    # `drain_position` is unchanged and is NOT the pan's centre — it never was; it is where
    # PR-B-SH2-DRAIN picks the waste up on its way to the stack. Left alone deliberately:
    # the pan moved 4 1/4", which does not move a trap that is already offset.
    Fixture(uid="CMQ805AAAA", tag="FX-M-BATH2-SH", type_ref="FX-SHOWER-36", room="RM-M-BATH2",
            position=pt(ft(6, 2.615), ft(14, 8.375)), wall_ref="W-M-BA2E",
            drain_position=pt(ft(1, 9), ft(17, 3))),
    # ** THE KOHLER K-5713-W1-0 UNDERSCORE, AND IT IS A DROP-IN. ** (2026-08-29, replacing
    # the FX-TUB-60 alcove allowance that stood here from the M3 fixture pass.) The bath has
    # no skirt: it drops through SL-M-TUBDK and sits on a 1"-2" mortar bed on the subfloor,
    # and Kohler is explicit that the rim carries no load. So this Fixture is the RIM, and
    # the thing that occupies the room is the framed deck box in storeys/main.py.
    #
    # Position is the centre of the deck's 36 1/8" x 65 3/4" bay with the bath pushed north:
    # 2" of tiled deck at the head (x 4'-8 11/16"..7'-8 7/16", y 16'-10 15/16"..21'-10 5/8"),
    # 4" at the foot, and 3/16" a side — comfortably inside Kohler's 1/8"-gap rule once the
    # tiling-in bead and the silicone joint take up. The 4" at the foot is not slack: it is
    # where the deck receptacle for the Bask heated surface lives, behind the bath and
    # inside the 24" Kohler requires, reachable through FURN-M-BATH2-TUB-AP.
    #
    # ** THE FLOOR UNDER IT IS THE ONE THING THIS PASS COULD NOT SETTLE. ** Kohler states a
    # minimum floor load of 49.3 lb/ft2 and tells the installer to "verify the subfloor is
    # adequately supported for" it "plus water and occupant". Filled, this bath is 72.017 gal
    # = 601 lb of water on 91 lb of shell; with a 200 lb occupant that is 892 lb over its
    # 14.8 ft2 plan area, or 60 psf — against the 40 psf live load an IRC residential floor
    # is designed to, on FS-M-WEST's 11 7/8" I-joists at 16" o.c. spanning 18'-0", which
    # `structural.ijoist_span` passes at 97% of its 18'-6" table limit.
    #
    # That is a LOCAL overload on a joist run already near its limit, and the engine has no
    # check that would ever say so — `structural.ijoist_span` grades the span against a
    # table, not the load standing on it. It is very likely fine (14.8 ft2 of a 18'-0" bay
    # distributes), and it is exactly the kind of "very likely fine" that belongs in front of
    # whoever stamps the drawings. NOT ANSWERED HERE. Recorded in plans/TODO.md.
    #
    # `drain_position` stays at (7'-4", 19'-4.8"): the waste is CENTRE on this bath as it
    # was on the allowance, and that point is where PR-B-TUB2-DRAIN turns for the stack, not
    # the outlet itself. The run drops to 1 1/2" with this change (plan/mep_drainage.py) —
    # K-7272's tee, not the 2" the allowance was drawn at.
    Fixture(uid="CMQ806AAAA", tag="FX-M-BATH2-TUB", type_ref="FX-KOHLER-UNDERSCORE-6036",
            room="RM-M-BATH2", position=pt(ft(6, 2.56), ft(19, 4.77)), rotation=deg(90),
            wall_ref="W-M-BA2E", drain_position=pt(ft(7, 4), ft(19, 4.8))),
    # ** A 54" ONE-BASIN VANITY SINCE 2026-08-29, AND IT USED TO BE A KITCHEN SINK. ** The
    # instance that stood here was ``FX-KITCHEN-SINK-33`` -- the library's DOUBLE-BOWL
    # kitchen sink -- hung on a 27" wall mount to drag its deck down to lavatory height. It
    # drew two bowls on the bathroom plan, billed as a kitchen sink in the fixture schedule,
    # and modelled no cabinet whatsoever. The owner asked for one basin and as much drawer
    # and shelf as the wall will hold, so it is now FX-VANITY-54-SINGLE (plan/fixture_types
    # .py), which carries the cabinet, the single basin and the 36" comfort-height counter.
    #
    # ** NO ``mount``, AND THAT IS THE CHANGE THAT MATTERS. ** A vanity STANDS ON THE FLOOR.
    # The old 27" wall mount was a workaround for a fixture type that models only a deck;
    # leaving it in place would have floated a 54" cabinet 27" up the wall with its toe kick
    # in mid-air. The type's own 41 1/2" height now puts the counter at 36" from the floor.
    #
    # ** POSITION IS STRUCK OFF THE WALLS' OWN FINISH FACES, NOT OFF `Room.clear_face`. **
    # This is the trap that cost a rebuild: `clear_face` is inset from the wall AXIS by the
    # room's lining, NOT from the finished face, so RM-M-BATH2 reports a west edge at
    # x=5/8" where W-M-W3's paint face is actually at x=6 5/8" -- the wall is 13 7/8" thick
    # and its axis is at x=0. A cabinet placed on the reported number stands SIX INCHES
    # inside the studs, and nothing fails: no check grades a fixture against a wall face.
    # The faces here are read off the walls' own layer polygons: W-M-W3 at x=6.635",
    # W-M-BDN1 at y=158.375", W-M-HS1 at y=264.615", W-M-BA2E at x=92.615".
    #
    # So the centre is x=17 1/8" (21" of depth off the west face) and y=15'-5 3/8" (54" of
    # length off the south face), hard into the room's real south-west corner. It runs NORTH
    # and stops at y=17'-8 3/8". ** The run available is 57 1/4", not the 59" a clear_face
    # reading suggests, and 54" leaves 3 1/4" ** to where FX-M-BATH2-WC's 21" P2705.1 front
    # clearance begins at y=17'-11 5/8". That is the one dimension to re-check if the water
    # closet ever moves west or south. rotation +90 turns the 54" length north/south and
    # puts the cabinet front (local -y) facing EAST into the room; the clearance zone
    # projects with it.
    #
    # ** D-M-BATH2 SWINGS OUT BECAUSE OF THIS CABINET, AND THE TWO CANNOT BOTH CHANGE BACK.
    # ** The door's 30" opening runs x 2'-0"..4'-6" and this cabinet's east face is at
    # x=1'-11 5/8", 3 5/8" inside it; swinging IN, the leaf clipped the cabinet by 25 in2
    # (`integrity.door_swing_conflict`, an UNKNOWN — `haus check --only fail` stayed clean
    # through it, so it was found in the takeoff's findings rather than at the gate). The
    # owner chose to turn the door around rather than shorten this to 45 1/2" or thin it to
    # 17", because that was the only one of the three that cost no storage. Re-hang the door
    # inward and the vanity has to give up one of its two dimensions; see storeys/main.py.
    #
    # WIN-M-BATH2 is not in the way and is worth saying so, because it nearly is: the window
    # runs y 18'-6 1/2"..20'-9 1/2" with a 3'-0" sill, which is the SAME plane as this
    # counter. It clears the cabinet's north end by 11 7/8" of bare wall.
    #
    # ** ``drain_position`` IS UNCHANGED, AND THAT IS A RESULT, NOT AN OVERSIGHT. ** The
    # basin sits over the 30" sink base at the NORTH end, centreline y=16'-3 5/8", and the
    # basin is 20" x 15 1/2" about it — so it spans x 3 3/8"..18 7/8", y 15'-5 5/8"..17'-1 5/8".
    # The authored tailpiece at (1'-0", 16'-6") falls inside that rectangle, 2 3/8" north of
    # the basin centreline and effectively on its x centre. Moving the pipe to chase the
    # 5 7/8" the old bowl's centre travelled would have re-pointed PR-B-SINK2-DRAIN into a
    # diagonal trap arm 2 3/8" off PR-B-SH2-DRAIN's line for nothing. Nothing in
    # plan/mep_drainage.py moves for this change.
    Fixture(uid="CMQ807AAAA", tag="FX-M-BATH2-SINK", type_ref="FX-VANITY-54-SINGLE",
            room="RM-M-BATH2", position=pt(inch(17.135), inch(185.375)), rotation=deg(90),
            wall_ref="W-M-W3",
            drain_position=pt(ft(1), ft(16, 6))),
    # --- RM-M-LAUNDRY (2026-07-31) -----------------------------------------------------
    # 62 3/4"x48 3/4" alcove behind D-M-LAUN (56" bifold spanning the north side) — a
    # closet, not a room you stand in: both appliances back onto the south wall (rotation
    # 180) and front north through the opening. 28"+1"+24"=53" fits the stack+tub inside
    # the 56" opening; the stack's west face sits on the door opening (not the wall face)
    # to centre the tower on x=9'-6", the dryer receptacle's existing location.
    #
    # `wall_ref` W-M-BA2E is the *service* wall (carries the washer standpipe/supply box),
    # not the back wall — both wastes drop through SL-M-DECK to the basement, so there is
    # no wall stack in this room at all.
    #
    # Retyped from APPL-WASHER to the stacked pair (uid/tag kept so mep.py's
    # `serves=("FX-M-LAUNDRY",)` refs still resolve). Heat-pump dryer is ventless; its
    # condensate drains via PR-M-DRYER-COND to the tub beside it.
    #
    # Room (and both fixtures) slid north 8" on 2026-08-03 with the W-M-CLN/CLN2 move;
    # this appliance sized that move — 40" deep leaves 8 3/4" to the door plane, the
    # margin the bifold track needs and no more.
    #
    # Retyped again 2026-08-24, allowance -> product: the LG WashTower the owner selected
    # (plan/appliance_types.py). Position is untouched. The tower is 27"x32 3/4"x74 3/8"
    # against the allowance's 28"x40"x80", so the 2026-08-03 move north is now 7 1/4"
    # roomier than the paragraph above describes — 16" to the door plane, not 8 3/4". The
    # margin only ever needed to be positive, so nothing moves to collect the slack.
    Appliance(uid="CMQ804AAAA", tag="FX-M-LAUNDRY", type_ref="APPL-LG-WASHTOWER",
              room="RM-M-LAUNDRY", position=pt(m(2.89712), m(6.06006)), rotation=deg(180),
              wall_ref="W-M-BA2E"),
    # Utility tub, 1" east of the stack — also the *receptor*: PR-M-DRYER-COND air-gaps
    # over its 34" rim, why the dryer needs no vent or condensate pump line.
    #
    # `drain_position` held at y=18'-9" through the 2026-08-03 move north (basin moved,
    # waste didn't) since SP-M-LSINK/PR-B-LSINK-DRAIN/the 45" trap arm below are all
    # authored on this y. Originally offset to clear W-B-CW2 (12" concrete on the y=18'
    # axis) by 3".
    #
    # SL-M-DECK (9" concrete) means every main-storey fixture drops straight down its own
    # sleeve rather than running a trap arm sideways — same as PR-B-SINK2/WASH-DRAIN. The
    # tub wet-vents off the laundry stack: a 45" 2" branch (MN Plumbing Table 1002.2 caps
    # 1 1/2" at 42") ties into PR-M-WC-VENT's existing x=8' leg, no new pipe.
    # 2026-08-29: y +1 5/8" (5.82791 -> 5.86920 m) with W-M-CLN's laundry face, retyped to
    # INT_2X4_STAGGERED_DOUBLE_GWB (storeys/main.py). The basin backed onto that wall with
    # 9/16" to spare and the retype took 1 5/8", so it was 1 1/16" into the studs until it
    # followed. (2026-08-30: W-M-CLN retyped again, to the single-gwb
    # INT_2X4_STAGGERED_GWB — the face gave back 5/8", so the basin followed it south by
    # the same amount. `wall_ref`-relative, so it tracked without a coordinate edit here.)
    # ** `wall_ref` STILL SAYS W-M-BA2E AND THAT IS NOT THE WALL IT TOUCHES: **
    # W-M-BA2E is 3'-0" west and is where PR-B-CW-WASH/PR-B-HW-WASH rise; the basin's back
    # is on W-M-CLN. Left as authored because `wall_ref` is what the supply pair names as
    # its riser wall and repointing it would move the risers, not the sink.
    Fixture(uid="J7VY2GZ062", tag="FX-M-LAUNDRY-SINK", type_ref="FX-LAUNDRY-SINK-24", room="RM-M-LAUNDRY",
            position=pt(m(3.62083), m(5.86920)), rotation=deg(180), wall_ref="W-M-BA2E",
            drain_position=pt(ft(11, 9), ft(18, 9))),
    # Kitchen sink moved to the north wall 2026-07-30 with the range/sink swap, then
    # flipped with the dishwasher to sit mid-run, then moved +9" east (2026-08-26) to
    # x=29'-4" when the base run was re-composed and the window's column moved onto it
    # instead — see storeys/main.py's OPENINGS and plan/placeables.py's kitchen header.
    # Dead-centred under WIN-M-KITCH now, at y=34'-5 3/8" (24" counter depth). W-M-N1 is
    # the wet wall (CATLIN_EXT_2X6, same as the old W-M-E2 — see mep.py's PR-M-KITCH-VENT).
    # The 27" mount is restated here (not just on the type) because the resolver reads the
    # instance Mount; it lands the rim on the 36" counter with 9" of bowl below.
    Fixture(uid="WZRCBGNDFW", tag="FX-M-KITCH-SINK", type_ref="FX-KITCHEN-SINK-33", room="RM-M-LIVING",
            position=pt(ft(29, 4), ft(34, 5.375)), wall_ref="W-M-N1",
            mount=Mount(kind=MountKind.WALL, elevation=inch(27)),
            drain_position=pt(ft(29, 4), ft(35))),
)


# RM-S-BATH1 is the *hall* bath (source's 80.73sf NW "Bathroom"); tag predates the
# suite's own bath (see storeys/second.py).
#
# Tub-shower stays centre-north (crosses x=5', the SL-D-SHOWER detail slice line). WC
# backs west onto exterior 2x6 W-S-W1 (rotation -90), its REQUIRED clearance zone stopping
# 3" south of the tub-shower. Lav backs east onto W-S-BA-E1B (INT_2X6_PLUMBING). All three
# footprints are pairwise disjoint with 9"+ clearance between any two.
#
# ALCOVE CHECK, 2026-08-21. FX-TUBSHOWER-60 is a 60"x30" flanged insert, which is exactly
# the standard alcove footprint (the type's 7'-0" height is the modelled surround envelope,
# matching FX-SHOWER-36 — not a product dimension). A flanged insert nails to studs on
# THREE sides. Measured at real finish faces, FX-S-BATH1-SH had two: the chase wall at
# x 2'-11 3/8" against the tub's west end at 2'-11 3/4" (0.36" of scribe), and the north
# wall at y 35'-5 3/8" against the tub's north edge at 35'-4 1/2". Its EAST end at
# x 7'-11 3/4" stood open, with 1'-8 7/8" of dead floor out to the east wall at x 9'-8 5/8".
# FURN-S-BATH1-SHELF (plan/placeables.py) closes it: the shelf's west panel is the return,
# with a 2x4 framed behind it for the flange to nail to.
#
# The west side was not quite two walls either, and is now. W-S-CH-W used to stop at
# y 33'-1 5/8", 3 1/8" short of the tub's front, so the southernmost 3 1/8" of the west
# flange had nothing to nail to. The chase's south corners moved 3 1/8" south on 2026-08-21
# (storeys/second.py, NODES) and that wall now runs the tub's full 30". All three sides are
# real.
SECOND_FIXTURES = (
    Fixture(uid="CSQ801AAAA", tag="FX-S-BATH1-WC", type_ref="FX-TOILET-STD", room="RM-S-BATH1",
            position=pt(m(0.560313), m(9.2783)), rotation=deg(90), wall_ref="W-S-W1"),
    # ** A 48" VANITY SINCE 2026-08-30 -- THE BIGGEST IN THE HOUSE AFTER RM-M-BATH2'S. **
    # It replaces a bare FX-LAV-24 that had also been 1.9" inside W-S-BA-E1B's finish face
    # (x=116.62") and carried `rotation=deg(90)`, which points a fixture's back at -x. The
    # bowl backs the EAST wall, so the correct rotation is -90; the old value was invisible
    # only because FX-LAV-24 has no clearance zone to point the wrong way.
    #
    # ** 48" FITS ONLY AS A REAL ARC. ** The usable run is bounded north by D-S-BATH1's
    # swing and south by FURN-S-BATH1-SHELF (the shower's return panel) at y=394.5". The
    # swing's BOUNDING BOX reaches y=348", which would leave 46.5" and force a 42"
    # special-order cabinet -- but the swing is a quarter-disc, and tested against the real
    # polygon a 21"-deep carcass clears from y=345.88" on. So the cabinet runs
    # y 345.88"..393.88": 48" of stock width, scribing to the shelf with 0.62" to spare,
    # and the two read as one continuous run of millwork along the wall. ** Re-run that
    # test if this door, this shelf or W-S-BD-N1B ever moves ** -- 0.62" is the whole
    # margin, and the north wall already moved 2" south once, on 2026-08-30.
    #
    # 30" sink base at the SOUTH end (bowl centred on the vanity at y=369.88"), 18"
    # three-drawer bank at the north. ED-S-BATH1-RC-MIRROR sits at y 370"..374" on this
    # wall, so it is within inches of the basin's edge -- NEC 210.52(D) wants 36" to the
    # sink's OUTSIDE EDGE and this is nowhere near the limit.
    Fixture(uid="CSQ802AAAA", tag="FX-S-BATH1-LAV", type_ref="FX-VANITY-48-SINGLE",
            room="RM-S-BATH1", position=pt(inch(106.12), inch(369.88)), rotation=deg(-90),
            wall_ref="W-S-BA-E1B"),
    Fixture(uid="CSQ803AAAA", tag="FX-S-BATH1-SH", type_ref="FX-TUBSHOWER-60", room="RM-S-BATH1",
            position=pt(m(1.66988), m(10.4013)), wall_ref="W-S-BD-N"),
    # The suite's own bath (source: 46.01sf). D-S-SUITEBATH's 2'-6" leaf sweeps the room's SW
    # quadrant clear, so WC sits north of the swing against the north wall, lav east of it
    # also against the north wall, shower in the NE corner.
    #
    # `wall_ref` is W-S-SN3 (2026-08-30, was W-S-DC2) — no `rotation` is authored, and this
    # house's own convention is that an un-rotated FX-TOILET-STD backs a HORIZONTAL wall
    # (FX-M-BATH2-WC on W-M-HS1, rotation=0) while a VERTICAL one needs rotation=90
    # (FX-S-BATH1-WC on W-S-W1, FX-A-STUBATH-WC on W-A-STU-W). W-S-DC2 is vertical; W-S-SN3
    # is horizontal — this WC physically backs SN3, same split the lav's `wall_ref` used to
    # carry (`FX-S-SUITEBATH-LAV`, above).
    #
    # It is also FLUSH to that wall now, which it never was: authored at y=249.71" it stood
    # 1.92" off the old 4 3/4" partition's face and would still have stood 0.92" off the
    # 6.77" wet wall that replaced it. Back = centre + 14" (the bowl's own 28" projection),
    # so y=250.625" puts the tank against SN3's 264.625" gwb face. Nothing grades a WC
    # against a wall face — `test_..._vanities` covers only vanities — so this was invisible.
    #
    # **W-S-DC2 still MUST stay a full-depth wet wall**, and after the 2026-08-30 vent
    # reroute the reason is no longer anything in THIS room: `PR-S-SUITEBATH-VENT` takes off
    # on SN3 now and its riser is entirely north of DC2. What still needs DC2's 5.5" cavity
    # is the ATTIC studio bath one storey up — `PR-A-STUBATH-DRAIN` drops 10'-0" inside it
    # and `PR-A-CW/HW-STUBATH` rise through it into W-A-STU-W. Retyping DC2 to a 2x4
    # assembly (e.g. for resilient channel) would leave those with nowhere to run.
    Fixture(uid="CSQ804AAAA", tag="FX-S-SUITEBATH-WC", type_ref="FX-TOILET-STD",
            room="RM-S-SUITEBATH", position=pt(inch(134.81), inch(250.625)),
            wall_ref="W-S-SN3"),
    # ** A 30" VANITY SINCE 2026-08-30. ** The NORTH wall (W-S-SN3 — this bullet said "south"
    # while the cabinet's `wall_ref` still pointed at W-S-SBS across the room) gives 31.76"
    # between the water closet's 15" side band (its centreline is x=134.81", so the band ends
    # at x=149.81") and the tub-shower's west face at x=181.57". 30" is the largest stock
    # width that fits; this cabinet runs x 150.5"..180.5", clearing the WC band by 0.69" and
    # scribing to the tub with 1.07". The room is 71" deep so this one keeps the standard 21"
    # carcass, and the 21" front zone stops at y=222.63", with W-S-SBS's face 29 1/4" further
    # on. None of those x dimensions moved when the wall was retyped; only y did.
    #
    # `wall_ref` is W-S-SN3 (2026-08-30, was W-S-SBS) — the wall this vanity actually backs
    # onto is now also the WET wall it drains into, so the split convention the attic suite
    # still uses (`wall_ref` names the drain wall, not the physical back) no longer applies
    # here: W-S-SN3 is INT_2X6_STAGGERED_PLUMBING for exactly this fixture
    # (`plan/storeys/second.py`), so the two now agree.
    #
    # ** THE BACK IS AT y=264.63", NOT 265.63". ** The retype took SN3 from a 4 3/4"
    # partition to a 6.77" wet wall, which moved its south face 1.000" INTO this room, so
    # every fixture and device on that face followed it by exactly 1.000" — this cabinet,
    # ED-S-SUITEBATH-RC1 and ED-S-SUITEBATH-MIRROR. `test_each_vanity_backs_its_walls_finish_
    # face_not_the_rooms_clear_face` is what catches this one; nothing catches the other two.
    #
    # NEC 210.52(D)'s receptacle is `ED-S-SUITEBATH-RC1` (plan/electrical.py) at x=148",
    # 2 1/2" west of the cabinet's outside edge and far inside the 36" limit.
    Fixture(uid="CSQ805AAAA", tag="FX-S-SUITEBATH-LAV", type_ref="FX-VANITY-30-SINGLE",
            room="RM-S-SUITEBATH", position=pt(inch(165.5), inch(254.13)),
            wall_ref="W-S-SN3"),
    # Suite bath takes a tub-shower (not the old 36" pan): room's clear face is
    # 9'-8 1/8" x ~6'-4", and the east wall has 5'-0" of run for a 60"x30" alcove. Rotated
    # -90, back turns east onto W-S-C2C; footprint keeps the old pan's north/east edges,
    # extended south, clearing the WC zone, the south lav, and the door swing.
    #
    # SAME DEFECT, LEFT OPEN (2026-08-21). This insert also stands in two walls, not three:
    # the east wall and W-S-SN3 to the north are closed, and its SOUTH end is open with only
    # 10.4" to W-S-SBS. That is why the hall bath's fix does not transfer — a return
    # partition here leaves 5 5/8" of filler beside a 4 3/4" wall, which is a framing
    # decision (furr the whole 10.4" out, move W-S-SBS, or accept a two-wall install and
    # detail the open end) and not a modelling one. Left for the owner rather than decided
    # here; a shelf like FURN-S-BATH1-SHELF will not fit the leftover.
    Fixture(uid="CSQ809AAAA", tag="FX-S-SUITEBATH-TUBSH", type_ref="FX-TUBSHOWER-60",
            room="RM-S-SUITEBATH", position=pt(m(4.99282), m(5.96387)), rotation=deg(-90),
            wall_ref="W-S-C2C"),
    # The double-vanity alcove off the landing (source: 18.23 sf, two lavatories), backed
    # onto W-S-BD-N — the same 2x6 wet wall the hall bath drains into.
    #
    # y 25'-2" -> 25'-4" on 2026-08-29: W-S-BD-N moved 2" north with the whole y=26'-6" line
    # (see RM-M-BATH1's note in this file), and a lavatory that BACKS a wall has to travel
    # with it or it stands off the wall by the amount the wall moved. Both mirror lights and
    # the switch above them moved the same 2" (plan/lighting.py).
    # ** A 60" DOUBLE VANITY SINCE 2026-08-30, BUILT AS TWO 30" CABINETS. ** Both bowls
    # stay: this alcove exists so two people can use it at once, and it keeps both mirrors.
    # It is authored as two FX-VANITY-30-SHALLOW instances rather than one 60" type because
    # that is how a 60" double is actually bought and built -- two stock 30" bases under one
    # 61" double top -- and because one 60" fixture would collapse two lavatories into one
    # in the fixture schedule, halving the DFU this alcove contributes to the drain.
    #
    # ** 18" DEEP. ** W-S-BD-N moved 2" south on 2026-08-30, so the alcove is 42.62" deep
    # (y 272.0"..314.62" between W-S-SN1's and W-S-BD-N's finish faces) and an 18" carcass
    # clears its own 21" front zone by 3.62". A 21" one would now clear by 0.62", which is
    # not enough margin to spend on a wall that has already moved once this week.
    #
    # ** THE BOWL SPACING IS THE CODE MINIMUM, EXACTLY. ** Centrelines at x=22.375" and
    # x=52.375": 30.0" centre-to-centre (IRC P2705.1 / IPC 405.3.1 want 30" between adjacent
    # fixtures) and 15.75" from each centreline to its side wall (they want 15"). NKBA
    # Guideline 5 would rather have 20" to the wall and 36" between bowls -- i.e. a 72"-76"
    # vanity -- and this alcove is 61.49" wide, so the recommendation cannot be met here.
    # 60" is the smallest code-legal true double and this is it, with nothing to spare.
    #
    # ** THIS ROOM HAS NO RECEPTACLE, AND IT NEEDS ONE. ** NEC 210.52(D) wants an outlet
    # within 36" of each sink's outside edge and there is not one anywhere in RM-S-VANITY.
    # That predates this change -- the bare bowls had the same problem -- and the fix lands
    # in plan/electrical.py. See plans/TODO.md.
    Fixture(uid="CSQ807AAAA", tag="FX-S-VANITY-LAV1", type_ref="FX-VANITY-30-SHALLOW",
            room="RM-S-VANITY", position=pt(inch(22.375), inch(305.62)),
            wall_ref="W-S-BD-N"),
    Fixture(uid="CSQ808AAAA", tag="FX-S-VANITY-LAV2", type_ref="FX-VANITY-30-SHALLOW",
            room="RM-S-VANITY", position=pt(inch(52.375), inch(305.62)),
            wall_ref="W-S-BD-N"),
)


# Garage wash-down hydrant on the west wall near the NW corner — clear of EQ-G-HEATER,
# both north windows, and the EV receptacles; 1'-6" off the wall for hose swing.
#
# Stands on SL-G-FLOOR (the garage slab at 0'-0"), 1'-10" below the `garage` storey datum
# (the ICF stem top). `resolve/placeables.py` measures mount height off the room's floor
# (resolve/room_floor.py), not the storey datum — before 2026-08-03 it measured off the
# datum and this (and everything else in the room) floated 22" in the air.
#
# Handle height (2'-6") is the type's own; everything below the slab (barrel, shutoff,
# supply, sleeve) is authored in params/foundations.py and plan/mep.py, none UI-movable.
# This instance is, which is why it lives here rather than in fixture_types.py.
GARAGE_FIXTURES = (
    # No `wall_ref` since 2026-08-15, deliberately: a 6'-0"-bury yard hydrant can't stand
    # against a wall here without its shutoff/weep stone entering the perimeter footing's
    # 45° influence line. Stands free at (5'-0", 59'-6") on the existing buried service
    # line (see params/foundations.py); the 6" of y came off when FT-GF-N's footing was
    # re-centred under the aligned garage stem.
    Fixture(uid="CGQ801AAAA", tag="FX-G-HYDRANT", type_ref="FX-HYDRANT-Y34SS",
            room="RM-GARAGE", position=pt(ft(5), ft(59, 6))),
)

# --- the guest studio: bath + wet bar (2026-08-29) -------------------------------------
# The bath box is x 9'-10 7/8"..17'-8 5/8", y 17'-6 3/8"..22'-1 5/8" — ENTIRELY INSIDE
# RM-S-SUITEBATH's footprint one storey down, which is the whole point of where it is.
#
# ** `wall_ref="W-A-STU-W"` ON ALL THREE FIXTURES, INCLUDING THE SHOWER THAT BACKS W-A-C2. **
# That is FX-B-BATH-WC/FX-B-BATH-LAV's exact idiom above ("it's the room's only stud cavity,
# carries their shared vent"), and it is load-bearing for both `mep.vent_reachability` and
# `mep.trap_arm_length`: W-A-STU-W is the 5 1/2" staggered wet wall stacked on W-S-DC2, and
# every drop in this suite lands in it.
#
# ** advisory.fixture_overlap PASSES, AND THE TIGHT DIMENSION IS 2". ** FX-TOILET-STD's one
# REQUIRED ClearanceZone (library/placeables/fixtures.py) is 15" each side of centreline and
# depth/2 + 21" in front; at rotation=deg(90) that projects east to x 9'-10 7/8"..13'-11 7/8",
# y 19'-5"..21'-11". The lavatory clears its south edge by 2", the shower clears its east edge
# by 8 3/4", and all three footprints are pairwise disjoint. The finding trigger is ~1.55 in2,
# so 2" over an 18" face is not much slack — ** IF THE LAV MOVES, MOVE IT SOUTH AND RE-CHECK. **
# ** THE 2026-08-29 ARRANGEMENT IS REVERSED HERE (2026-08-30), AND THE REASON IS THAT IT
# MISREAD EXCEPTION 2. ** That pass moved the WC onto the NORTH wall and the lavatory onto
# the SOUTH wall, both crammed into the same 20 inches of x, on this sentence: "Minn. R.
# 1309.0305 Exception 2 asks 6'-8" over the fixture and its front clearance". It does not.
# The exception reads:
#
#     "Bathrooms shall have a minimum ceiling height of 6 feet 8 inches AT THE CENTER OF THE
#      FRONT CLEARANCE AREA for fixtures as shown in Figure R307.1. The ceiling height above
#      fixtures shall be such that the fixture is capable of being used for its intended
#      purpose."
#
# One point, not an area — and above the fixture itself the test is usability, not a number.
# That is the difference between a bathroom and the mess this room had become, and it is the
# same lesson `haus check` teaches everywhere else: read the cited section before moving the
# house to satisfy it.
#
# ** THE CLEARANCE ENVELOPE IS 15" + 24", NOT 15" + 21", AND IT IS CHECKED. ** Two things
# that were true when the older comments in this file were written are not true now. The
# front dimension went to UPC 402.5's 24" on 2026-08-29 (the derivation is at the head of
# library/placeables/fixtures.py: Minn. R. 1309.0307 -> ch. 4714 -> the 2018 UPC, unamended;
# IRC's 21" is not Minnesota's number). And `active_code_profile="MN/IRC"` is now set in
# plan/manifest.py, which is what makes `_resolved_clearance_zones` keep the zone instead of
# dropping it — so `integrity.placeable_required_clearance_conflict` is live here and FAILED
# on the first draft of this arrangement. Do not trust any comment in this repo that says
# these envelopes are inert; check the manifest.
#
# What is still ungraded is whether the envelope FITS THE ROOM: `_clearance_conflicts`
# compares a zone against peer placeable FOOTPRINTS only, never against a wall. Every
# distance-to-a-wall figure below was measured by hand off the resolved layer polygons.
# `code.R305_ceiling_height` grades the ROOM (78% of required floor area at 7'-0") and
# nothing grades a fixture against the rake, so the headroom figures are hand-measured too.
#
# ** THE WATER CLOSET GOES BACK ON THE WET WALL, WHICH IS THE ONLY WALL IT CAN PLUMB INTO. **
# Back to W-A-STU-W's east face at x 9'-10 7/8", facing east, c/l at y 20'-8" -> 19'-4". The
# roof underside (measured off the resolved model, which runs ~7/8" more generous than the
# `1 1/2" + x/2` rule of thumb) is 5'-1 13/16" at its back and 5'-8 3/8" over the seat — you
# SIT there, and Exception 2's usability test is satisfied by a fixture you use seated. What
# the exception actually measures is the centre of the 24" front clearance, at x 13'-2 7/8",
# where the model reads ** 6'-9 13/16" **. An inch and thirteen sixteenths of margin, and it
# is the whole reason this fixture can be on this wall at all.
#
#   WC  c/l (11'-0 7/8", 19'-4"), rot -90.  footprint x 9'-10 7/8"..12'-2 7/8",
#       y 18'-6"..20'-2".  UPC 402.5 zone (15" each side, 24" in front)
#       x 9'-10 7/8"..14'-2 7/8", y 18'-1"..20'-7" — 6 5/8" off the south wall face and
#       5 3/4" off the shower's west edge, both hand-measured.
#       ** y 19'-4" IS AN FS-ATTIC BAY CENTRE ** (232" = 8 + 14 x 16), so the flange drops
#       between joists and PR-A-STUBATH-DRAIN loses its dog-leg entirely (plan/mep_drainage.py).
#       It is also what dragged REG-A-STUBATH-EXH's type into the open: a 7x7 CEILING grille
#       authored on this wall stood 4" into the zone and failed A117.1 307.2 the moment the
#       zone existed. See plan/mep_hvac.py — the grille did not move, the type was wrong.
#
# ** THE LAVATORY GOES ON THE NORTH WALL, IN THE TALL HALF, AND THAT IS WHERE THE ROOM WINS. **
# You STAND at a lavatory, so this is the fixture Exception 2's usability sentence actually
# bites on. On the south wall it is trapped between two hard stops: 6'-8" of headroom wants
# x >= 13'-1", D-A-STUBATH's west jamb at 13'-10" wants x <= 13'-1", and the old 13'-2"
# station missed on BOTH sides — 1" of its bowl stood inside the door's rough opening. The
# north wall has neither stop.
#
#   LAV c/l (13'-6", 21'-6 5/8"), rot 180.  footprint x 12'-9"..14'-3",
#       y 20'-11 5/8"..22'-1 5/8".  ** 6'-11 3/8" of ceiling, measured ** — three inches
#       better than the south wall, and 5 5/8" of counter-end clearance to the shower's
#       14'-8 5/8" west edge. Its south edge is 4 5/8" clear of the WC's zone, which is why
#       the WC came one bay south of the 20'-8" it would otherwise have taken.
#
# The trap arms all improved on the move, which is the tell that the fixtures went where the
# plumbing already was rather than the other way round: WC 8" -> 16", lav 31" -> 0", shower
# 0", bar 50" -> 53", against limits of 72"/72"/72"/60".
#
# The shower did not move: 14'-8 5/8"..17'-8 5/8" x 19'-1 5/8"..22'-1 5/8", flush into the NE
# corner, under 7'-6 11/16" and up. One fixture per wall, and the floor you enter onto is
# clear.
#
# ** `wall_ref` STAYS `W-A-STU-W` ON ALL THREE, AND THAT IS NOT A LEFTOVER. ** In this file
# wall_ref names the WET wall a fixture plumbs into, not the wall it physically hangs on —
# the shower has read that way since the suite was authored ("including the shower that
# backs W-A-C2", above). W-A-STU-W is still the one 5 1/2" staggered cavity in the attic and
# every drop still lands in it; `mep.vent_reachability` and `mep.trap_arm_length` both key
# off that, and PR-A-STUBATH-VENT still has a vertex on its axis. It is now literally true
# of the water closet as well, which is new.
ATTIC_FIXTURES = (
    # Floor-mount, not FX-TOILET-WH: a wall-hung carrier costs a 6" chase this room need not buy.
    Fixture(uid="WCM0PV9H71", tag="FX-A-STUBATH-WC", type_ref="FX-TOILET-STD", room="RM-A-STUBATH",
            position=pt(ft(11, 0.875), ft(19, 4)), rotation=deg(90),
            wall_ref="W-A-STU-W"),
    # 18" x 14", the cheapest lavatory in the catalog — not the 24" FX-LAV-24 the second storey
    # uses. This is a guest bath specified as cheaply as the code allows, and the 6" saved is
    # part of what keeps the water closet's clearance zone clear.
    Fixture(uid="N2BDQ3T63Z", tag="FX-A-STUBATH-LAV", type_ref="FX-LAV-COMPACT", room="RM-A-STUBATH",
            position=pt(ft(13, 6), ft(21, 6.625)), rotation=deg(180),
            wall_ref="W-A-STU-W"),
    # A 36" pan in the NE corner. ** NOT FX-TUBSHOWER-60 ** — a 60" insert costs more, needs
    # three nailable walls (the 2026-08-21 alcove audit above), and a guest suite does not want
    # a tub. R305 is not the constraint here either: the roof underside over this corner is
    # 10'-6" and up.
    Fixture(uid="P63E8HB7WZ", tag="FX-A-STUBATH-SH", type_ref="FX-SHOWER-36", room="RM-A-STUBATH",
            position=pt(ft(16, 2.625), ft(20, 7.625)), wall_ref="W-A-STU-W"),
    # ** THE WET BAR'S SINK, BACK-TO-BACK WITH THE BATH THROUGH THE SAME WET WALL. ** It is on
    # W-A-STU-W's WEST face, so the bar and the bathroom share one stack, one vent and one
    # 5 1/2" cavity instead of running a second branch across the studio floor.
    #
    # It is an FX-LAV-COMPACT used as a bar sink, and that is deliberate rather than lazy: 18" x
    # 14" is dimensionally exact for a bar bowl, it is the cheapest wet fixture in the catalog,
    # and the house already runs the trade in the other direction (FX-M-BATH2-SINK is an
    # FX-KITCHEN-SINK-33). Adding a dedicated FX-BAR-SINK-15 to the shared catalog is the
    # cleaner alternative and costs one entry; either is defensible, and this one costs nothing.
    #
    # ** SINK AND UNDERCOUNTER FRIDGE, AND NOTHING THAT COOKS. ** That is what keeps this a wet
    # bar rather than a kitchen, and it is the entire IRC R302.3 argument: with no cooking
    # appliance this is not a second dwelling unit, so R302.3's two-family separation does not
    # land on D-A-HALVES or on FS-ATTIC. **The engine has no R302.3 rule at all**, so that
    # argument exists only here and in the permit narrative. The alcove is also deliberately NOT
    # `Occupancy.KITCHEN` — that would put a 25 sf nook in `_HABITABLE` (graded for 8% glazing on
    # its own), in `_GFCI_OCCUPANCIES` and in `_STALE_OCCUPANCIES` (demanding its own exhaust
    # terminal). It is part of RM-A-STUDIO and it stays that way.
    # ** THE BAR MOVED TO THE CENTRE WALL ON 2026-08-29 (x 8'-6" -> 17'-0"). ** It stood on
    # W-A-STU-W's WEST face, which put the person using it at x ~7'-6" under 4'-3" of roof.
    # There is no station near that wall the 6:12 rake makes usable, and the wall itself only
    # runs y 17'-4"..22'-4" — inside the bath's own band — so the bar could not simply slide
    # north or south. It goes to W-A-C2's west face at y 16'-8", SOUTH of the bath box, where
    # the ceiling is 8'-7 1/2" and the counter is against the one full-height wall the studio
    # has. `wall_ref` still names the wet wall (see the block above): the drain crosses the
    # joist field west to the same stack and the bar is still on one branch, one vent.
    #
    # ** THAT MOVE WAS THEN DRAGGED OUT OF TRUE IN THE EDITOR, AND 2026-08-30 PUTS IT BACK. **
    # The position came back from the UI as raw metres, `pt(m(5.18719), m(4.85213))` — which
    # is (17'-0 7/32", 15'-11"), not the (17'-0", 16'-8") the comment above still described.
    # Three things were wrong with it and none of them draws a finding:
    #   * `rotation=deg(-90)` put the BACK of the bowl at -x. The sink faced INTO W-A-C2 and
    #     its rim stood out into the room. deg(90) is what backs a fixture onto an east wall
    #     (deg(0) backs south, deg(180) north, deg(-90) west) — compare FX-A-STUBATH-WC above.
    #   * the bowl floated 1 3/8" clear of W-A-C2's 17'-8 5/8" west face instead of touching it.
    #   * `drain_position` stayed at the authored (17'-6", 16'-8"), 9" north of where the bowl
    #     had drifted to, so PR-A-BAR-DRAIN started at a point under no fixture.
    # Now: back on the finish face at c/l x 17'-1 5/8" (17'-8 5/8" less half the 14" depth),
    # c/l y 16'-4", drain under the bowl. Footprint x 16'-6 5/8"..17'-8 5/8", y 15'-7"..17'-1".
    #
    # ** y 16'-4" IS NOT A BAY CENTRE, AND THAT COSTS PR-A-BAR-DRAIN A 4" LEG, DELIBERATELY. **
    # 16'-8" is the bay centre and it is where the note above says this sink is — but the wall
    # it dies into is W-A-BATH-S, whose SOUTH face is 17'-1 5/8", not the 17'-6 3/8" north
    # face the bath is measured from. At 16'-8" the bowl stood 3 3/8" inside that wall, which
    # is to say the position the comment claimed was never buildable either. 16'-4" leaves
    # 5/8". Going the other way to 15'-4", the next bay centre south — which would have made
    # one continuous 3'-7" counter with APPL-A-STUDIO-FRIDGE, the "4'-0" bank" the note above
    # wishes for, and D-A-STUBATH's arc stops at x 16'-4" so the swing does not reach it —
    # puts the trap arm at 65" against Table 1002.2's 60" for a 2" arm. `mep.trap_arm_length`
    # FAILed it outright. 16'-4" measures 53". The bank stays a sink, a gap and a fridge.
    Fixture(uid="11TZJE81BZ", tag="FX-A-STUDIO-BAR-SINK", type_ref="FX-LAV-COMPACT", room="RM-A-STUDIO",
            position=pt(ft(17, 1.625), ft(16, 4)), rotation=deg(90), wall_ref="W-A-STU-W",
            mount=Mount(kind=MountKind.WALL, elevation=inch(27)),
            drain_position=pt(ft(17, 1.625), ft(16, 4))),
)


# --- the two south-face wall hydrants (2026-08-01) -------------------------------------
# Unlike FX-G-HYDRANT (a *yard* hydrant, 6' bury, self-draining below frost), these are
# *wall* hydrants: seat inside the envelope at the inboard end of a ~10" barrel that
# self-drains outward when closed. Not buried, not shut down for winter — the owner's ask.
#
# Both on the south face, serving the porch (0'-0") and balcony (10' up) outdoor rooms:
#   FX-M-PORCH-HYD  x=12'-0" on W-M-S1, the blank stretch between WIN-M-BED-S1 and
#                   WIN-M-BED-S2 (which moved east to centre 14'-8" on 2026-08-24 — its
#                   RO now runs 13'-5"..15'-11", leaving 1'-5" of clear wall to that jamb).
#   FX-S-BALC-HYD   x=7'-4" on W-S-S1, a 16" module bay centre behind RM-S-PLANT (which
#                   the balcony irrigation this hydrant feeds actually waters). Moved west
#                   off 16'-8" on 2026-08-24: D-S-DECK-W slid 1'-0" inward and its rough
#                   opening (12'-2"..17'-2") swallowed the old station. It lands in the
#                   2'-10" of blank wall between WIN-S-PLANT1 and WIN-S-PLANT2 — the only
#                   bay left on this wall that is not spoken for, since the 1'-7" west of
#                   the door took ED-S-PLANT-RC1 (plan/electrical.py).
#
# Each names the room *behind* it, which draws an `integrity.placeable_room_mismatch`
# (footprint centre outside its assigned room) — correct for an exterior hose bib whose
# escutcheon is outdoors; leaving `room` unset would trade that for a worse
# `advisory.fixture_room_unassigned` FAIL with a blank permit-schedule cell.
#
# Mount is WALL/24" from the type. The pierced wall is CATLIN_EXT_2X6 with 4" continuous
# exterior insulation, so the hydrant's seat and feed stay on the warm side of the thermal
# break — a cavity-only wall would freeze this detail.
PORCH_HYDRANT = (
    Fixture(uid="7QK2M4XR0B", tag="FX-M-PORCH-HYD", type_ref="FX-HYDRANT-SD34",
            room="RM-M-BED", position=pt(ft(12), ft(0)), wall_ref="W-M-S1"),
)
BALCONY_HYDRANT = (
    Fixture(uid="D3NLW8VC5T", tag="FX-S-BALC-HYD", type_ref="FX-HYDRANT-SD34",
            room="RM-S-PLANT", position=pt(ft(7, 4), ft(0)), wall_ref="W-S-S1"),
)
