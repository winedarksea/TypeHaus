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
    # Backs east onto W-M-BA2E (its wet wall); rotation 90 turns its back onto the wall,
    # centred so the tank edge sits on the room's east clear face. The `drain_position`
    # override (removed 2026-07-29) used to hold SP-M-WC2's old corner-fitting position
    # to keep the pre-pour sleeve contract during the WC's move to this wall; the plumbing
    # pass re-pointed the sleeve/PR-B-WC2-DRAIN to the real closet flange, so the convention
    # (under the bowl) is correct on its own now.
    Fixture(uid="CMQ803AAAA", tag="FX-M-BATH2-WC", type_ref="FX-TOILET-STD", room="RM-M-BATH2",
            position=pt(m(0.686504), m(6.14439)), rotation=deg(0), wall_ref="W-M-BA2E"),
    # BATH2 has separate bathing fixtures: the 36" shower sits north of the door swing,
    # while the 60" tub runs north/south along the east plumbing wall. They are intentionally
    # separate instances/types rather than a tub-shower combination, so the permit schedule
    # and future owner selections can treat them independently.
    Fixture(uid="CMQ805AAAA", tag="FX-M-BATH2-SH", type_ref="FX-SHOWER-36", room="RM-M-BATH2",
            position=pt(m(1.88387), m(4.58801)), wall_ref="W-M-BA2E",
            drain_position=pt(ft(1, 9), ft(17, 3))),
    # Shifted 6" north (2026-07-29) with the W-M-HS1..4 wall move that gave BATH2 8" more
    # depth: the old position overlapped FX-M-BATH2-SH by ~1.3" (`advisory.fixture_overlap`);
    # this clears it with a 4.7" gap and still leaves 4" to the room's new north face.
    Fixture(uid="CMQ806AAAA", tag="FX-M-BATH2-TUB", type_ref="FX-TUB-60", room="RM-M-BATH2",
            position=pt(m(1.96436), m(5.91312)), rotation=deg(90), wall_ref="W-M-BA2E",
            drain_position=pt(ft(7, 4), ft(19, 4.8))),
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
    Appliance(uid="CMQ804AAAA", tag="FX-M-LAUNDRY", type_ref="APPL-WASHER-DRYER-STACKED",
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
    # flipped with the dishwasher to sit mid-run. Centred near WIN-M-KITCH (7" off true
    # centre so the RO lands on a stud line) at y=34'-5 3/8" (24" counter depth). W-M-N1 is
    # the wet wall (CATLIN_EXT_2X6, same as the old W-M-E2 — see mep.py's PR-M-KITCH-VENT).
    # The 27" mount is restated here (not just on the type) because the resolver reads the
    # instance Mount; it lands the rim on the 36" counter with 9" of bowl below.
    Fixture(uid="WZRCBGNDFW", tag="FX-M-KITCH-SINK", type_ref="FX-KITCHEN-SINK-33", room="RM-M-LIVING",
            position=pt(ft(28, 7), ft(34, 5.375)), wall_ref="W-M-N1",
            mount=Mount(kind=MountKind.WALL, elevation=inch(27)),
            drain_position=pt(ft(28, 7), ft(35))),
)


# RM-S-BATH1 is the *hall* bath (source's 80.73sf NW "Bathroom"); tag predates the
# suite's own bath (see storeys/second.py).
#
# Tub-shower stays centre-north (crosses x=5', the SL-D-SHOWER detail slice line). WC
# backs west onto exterior 2x6 W-S-W1 (rotation -90), its REQUIRED clearance zone stopping
# 3" south of the tub-shower. Lav backs east onto W-S-BA-E1B (INT_2X6_PLUMBING). All three
# footprints are pairwise disjoint with 9"+ clearance between any two.
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

# --- the two south-face wall hydrants (2026-08-01) -------------------------------------
# Unlike FX-G-HYDRANT (a *yard* hydrant, 6' bury, self-draining below frost), these are
# *wall* hydrants: seat inside the envelope at the inboard end of a ~10" barrel that
# self-drains outward when closed. Not buried, not shut down for winter — the owner's ask.
#
# Both on the south face, serving the porch (0'-0") and balcony (10' up) outdoor rooms:
#   FX-M-PORCH-HYD  x=12'-0" on W-M-S1, the blank stretch between WIN-M-BED-S2 and centre.
#   FX-S-BALC-HYD   x=16'-8" on W-S-S1, a 16" module bay centre behind RM-S-PLANT (which
#                   the balcony irrigation this hydrant feeds actually waters).
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
            room="RM-S-PLANT", position=pt(ft(16, 8), ft(0)), wall_ref="W-S-S1"),
)
