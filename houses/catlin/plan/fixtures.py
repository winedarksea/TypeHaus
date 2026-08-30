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
    Fixture(uid="5BBZTZNBWN", tag="FX-B-BATH-LAV", type_ref="FX-LAV-24",
            room="RM-B-BATH", position=pt(ft(16, 8), ft(20)), rotation=deg(-90),
            wall_ref="W-B-BA-N", drain_position=pt(ft(17), ft(20))),
)

# RM-M-BATH1's clear face is 3'-2" x 4'-3-1/4" — too small for the shared FX-TOILET/FX-LAV
# pair without wall-to-wall placement, so this room uses BATH1-only compact types.
# WC is a wall-hung compact on the south wall; rotation 180 turns bowl/front north, back
# toward W-M-HS1 — its carrier/waste stay tied to the W-M-BAE wet-wall stack independent
# of the bowl's own placement.
#
# y nudged +2" (2026-08-15), same reason as the lavatory's +6" nudge (2026-07-29):
# N-M-W2/N-M-C2 pushed north onto the west facade's 16" column module, dragging the
# room's south clear face with it. The 2" preserves the bowl's original 1.985" standoff.
# `drain_position` stays at y=22'-7" (the W-M-BAE stack tie) — moving it would drag
# three pipe runs for nothing.
MAIN_FIXTURES = (
    Fixture(uid="CMQ801AAAA", tag="FX-M-BATH1-WC", type_ref="FX-TOILET-WH", room="RM-M-BATH1",
            position=pt(m(0.670778), m(7.11886)), rotation=deg(180), wall_ref="W-M-BAE",
            drain_position=pt(ft(6), ft(22, 7))),
    # y nudged +6" (2026-07-29, with N-M-W2/N-M-C2's north push for the BATH2 wall move):
    # the room's south face moved with it and the lavatory's old y left it poking through
    # into the hall (test_bath1_fixtures_sit_inside_the_room_and_clear_of_each_other).
    Fixture(uid="CMQ802AAAA", tag="FX-M-BATH1-LAV", type_ref="FX-LAV-COMPACT", room="RM-M-BATH1",
            position=pt(m(1.315138), m(7.00891)), wall_ref="W-M-BAE", rotation=deg(180)),
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
    # `drain_position` stays at (7'-4", 19'-4.8"): the waste is CENTRE on this bath as it
    # was on the allowance, and that point is where PR-B-TUB2-DRAIN turns for the stack, not
    # the outlet itself. The run drops to 1 1/2" with this change (plan/mep_drainage.py) —
    # K-7272's tee, not the 2" the allowance was drawn at.
    Fixture(uid="CMQ806AAAA", tag="FX-M-BATH2-TUB", type_ref="FX-KOHLER-UNDERSCORE-6036",
            room="RM-M-BATH2", position=pt(ft(6, 2.56), ft(19, 4.77)), rotation=deg(90),
            wall_ref="W-M-BA2E", drain_position=pt(ft(7, 4), ft(19, 4.8))),
    # RM-M-BATH2's double-basin sink uses the shared kitchen-sink catalog type rather than
    # a house-local surrogate. Its 27" mount puts the library sink's deck at the intended
    # lavatory height; rotation +90 turns the back of the symbol toward the west wall.
    Fixture(uid="CMQ807AAAA", tag="FX-M-BATH2-SINK", type_ref="FX-KITCHEN-SINK-33",
            room="RM-M-BATH2", position=pt(m(0.434228), m(5.02659)), rotation=deg(90),
            wall_ref="W-M-W3", mount=Mount(kind=MountKind.WALL, elevation=inch(27)),
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
    Fixture(uid="J7VY2GZ062", tag="FX-M-LAUNDRY-SINK", type_ref="FX-LAUNDRY-SINK-24", room="RM-M-LAUNDRY",
            position=pt(m(3.62083), m(5.82791)), rotation=deg(180), wall_ref="W-M-BA2E",
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
    Fixture(uid="CSQ802AAAA", tag="FX-S-BATH1-LAV", type_ref="FX-LAV-24", room="RM-S-BATH1",
            position=pt(ft(9, 0.5), ft(31)), rotation=deg(90), wall_ref="W-S-BA-E1B"),
    Fixture(uid="CSQ803AAAA", tag="FX-S-BATH1-SH", type_ref="FX-TUBSHOWER-60", room="RM-S-BATH1",
            position=pt(m(1.66988), m(10.4013)), wall_ref="W-S-BD-N"),
    # The suite's own bath (source: 46.01sf). Both drain walls are INT_2X6_PLUMBING
    # (W-S-DC2 west, W-S-SBS south) — satisfies advisory.wet_wall_depth's 5.5"
    # requirement. D-S-SUITEBATH's 2'-6" leaf sweeps the room's SW quadrant clear, so WC
    # sits north of the swing on the west wall, lav east of it on the south wall, shower
    # in the NE corner.
    Fixture(uid="CSQ804AAAA", tag="FX-S-SUITEBATH-WC", type_ref="FX-TOILET-STD",
            room="RM-S-SUITEBATH", position=pt(m(3.42422), m(6.34259)), wall_ref="W-S-DC2"),
    Fixture(uid="CSQ805AAAA", tag="FX-S-SUITEBATH-LAV", type_ref="FX-LAV-24",
            room="RM-S-SUITEBATH", position=pt(m(4.21659), m(6.46046)), wall_ref="W-S-SBS"),
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
    Fixture(uid="CSQ807AAAA", tag="FX-S-VANITY-LAV1", type_ref="FX-LAV-24", room="RM-S-VANITY",
            position=pt(ft(1, 9), ft(25, 2)), wall_ref="W-S-BD-N"),
    Fixture(uid="CSQ808AAAA", tag="FX-S-VANITY-LAV2", type_ref="FX-LAV-24", room="RM-S-VANITY",
            position=pt(ft(4), ft(25, 2)), wall_ref="W-S-BD-N"),
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
# ** BOTH THE WATER CLOSET AND THE LAVATORY MOVED EAST ON 2026-08-29, AND THEY CHANGED
# WALLS TO DO IT. ** The bath used to run WC and lav down the wet wall at x 11'-0 7/8" and
# 10'-5 7/8", facing east into the room. With the attic at 6:12 off a 1 1/2" plate the roof
# underside is `1 1/2" + x/2` above the floor, which is 5'-7 1/2" and 5'-4 1/2" over those
# two stations — under a rake you cannot stand up at, let alone use a fixture under.
#
# Minn. R. 1309.0305 Exception 2 asks 6'-8" over the fixture and its front clearance, which
# arrives at x 13'-1". That leaves x 13'-1"..17'-8 5/8" as the bath's usable band, and the
# 36" shower already holds 15'-2 5/8"..17'-2 5/8" of it — so the WC and the lav cannot BOTH
# sit on the west wall's line and still clear the rake. They go on the room's other two
# walls instead, at the tall end of each:
#   * WC on the north wall at x 13'-6" (6'-10 1/2" of ceiling), facing south. Its 15"+15"
#     x 21" clearance zone runs x 12'-3"..14'-9", clear of the shower's 15'-2 5/8" west edge
#     by 5 5/8" and of D-A-STUBATH's 14'-0" jamb.
#   * lav on the south wall at x 13'-2" (6'-8 1/2"), facing north, its east edge 1" short of
#     that same door jamb.
#
# ** `wall_ref` STAYS `W-A-STU-W` ON ALL THREE, AND THAT IS NOT A LEFTOVER. ** In this file
# wall_ref names the WET wall a fixture plumbs into, not the wall it physically hangs on —
# the shower has read that way since the suite was authored ("including the shower that
# backs W-A-C2", above). W-A-STU-W is still the one 5 1/2" staggered cavity in the attic and
# every drop still lands in it; `mep.vent_reachability` and `mep.trap_arm_length` both key
# off that, and PR-A-STUBATH-VENT still has a vertex on its axis.
ATTIC_FIXTURES = (
    # Floor-mount, not FX-TOILET-WH: a wall-hung carrier costs a 6" chase this room need not buy.
    Fixture(uid="WCM0PV9H71", tag="FX-A-STUBATH-WC", type_ref="FX-TOILET-STD", room="RM-A-STUBATH",
            position=pt(ft(13, 6), ft(21, 4)), rotation=deg(180),
            wall_ref="W-A-STU-W"),
    # 18" x 14", the cheapest lavatory in the catalog — not the 24" FX-LAV-24 the second storey
    # uses. This is a guest bath specified as cheaply as the code allows, and the 6" saved is
    # part of what keeps the water closet's clearance zone clear.
    Fixture(uid="N2BDQ3T63Z", tag="FX-A-STUBATH-LAV", type_ref="FX-LAV-COMPACT", room="RM-A-STUBATH",
            position=pt(ft(13, 2), ft(18, 1.375)), rotation=deg(0),
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
    Fixture(uid="11TZJE81BZ", tag="FX-A-STUDIO-BAR-SINK", type_ref="FX-LAV-COMPACT", room="RM-A-STUDIO",
            position=pt(ft(17), ft(16, 8)), rotation=deg(-90), wall_ref="W-A-STU-W",
            mount=Mount(kind=MountKind.WALL, elevation=inch(27)),
            drain_position=pt(ft(17, 6), ft(16, 8))),
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
