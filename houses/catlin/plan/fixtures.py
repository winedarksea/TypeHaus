# haus: editable
# Permit-schedule plumbing fixture/appliance *instances* for Catlin (M3 WP3.4/WP3.10).
# `# haus: editable` so UI drags (moving a toilet, the washer, …) round-trip to source.
# Their FixtureType/ApplianceType catalog lives in the non-editable `library/placeables/`
# at the repo root (it uses `frozenset(...)`, which the editable dialect forbids).

from typehaus import Appliance, Fixture, Mount, MountKind, deg, ft, inch, pt
from typehaus.model import Location, TubEnclosureSpec, WallAttachment, m

# --- basement ----------------------------------------------------------------------------
# Both RM-B-SAUNA fixtures drain under the slab to PR-B-MAIN-DRAIN, not a wall stack
# (see plan/mep.py SLAB_STUBS).
#
# **The sauna rotated onto the garden wall on 2026-09-05** — long axis east-west, clear box
# x 5'-3 13/16"..17'-5 3/4", y 0'-11 1/2"/0'-9 1/2"..9'-8 3/16" between liner faces (the 2"
# jog in the south face is where the buried pour hands over to the framed walkout at
# x=8'-10"). The two fixtures moved with the room and kept their corner: the 36"x36" curbed
# pan is still in the NE corner, still the only corner with both sides finished wall, and
# the floor drain still sits west of it at the 1/8"/ft slope's low point where a boxed
# corner chase can bring PR-B-COND's air-gap down over it. D-B-SAUNA is on W-B-CS now and
# swings OUT into the gym, so no leaf sweeps this floor at all. No slope field exists on
# Slab/FinishZone, so both slopes (and IRC P2708.1's 1/4"-1/2"/ft) live only in comments.
#
# Both fixtures still chase through W-B-CS, not the closer W-B-SA-N partition, to keep
# W-B-SA-N's foil-faced polyiso vapour barrier unbreached; W-B-CS also gives a true vent
# stack path via W-M-C1 above. advisory.wet_wall_depth's 5.5" cavity requirement is a
# house preference, not code — it is not what drives this wall choice.
BASEMENT_FIXTURES = (
    # Pan x 14'-5 3/4"..17'-5 3/4", y 6'-8 3/16"..9'-8 3/16" — snug into the liner faces.
    # It moved 7" north with W-B-SA-N on 2026-09-05 (round three) to stay in the corner, and
    # the floor drain, both sleeves, PR-B-SAUNA-DRAIN's first three vertices, the two
    # condensate air gaps over the grate and PR-B-SAUNA-VENT's riser all moved with it.
    # ** `drain_position` IS THE PAN'S OWN GRATE, AND IT HAS TO BE AUTHORED. ** Without it
    # `_expected_drain_point` reads the "no hot connection = floor-drained" heuristic the
    # wrong way round for a shower — this type DOES need hot water, so the derivation
    # projects the drain onto `wall_ref`'s axis at x=18'-0", 24 1/4" east of the pan and
    # inside W-B-CS's studs. A shower pan drains at its own grate; PR-B-SAUNA-DRAIN's first
    # two vertices are already exactly here, so this authors a fact rather than a route.
    Fixture(uid="CBQ802AAAA", tag="FX-B-SAUNA-SH", type_ref="FX-SHOWER-36-COMBO",
            room="RM-B-SAUNA", position=pt(inch(191.75), inch(98.1875)),
            wall_ref="W-B-CS", drain_position=pt(inch(191.75), inch(98.1875))),
    Fixture(uid="CBQ803AAAA", tag="FX-B-SAUNA-FD", type_ref="FX-FLOOR-DRAIN",
            room="RM-B-SAUNA", position=pt(ft(13, 6), inch(98.1875)),
            wall_ref="W-B-CS"),
    # **RM-B-BATH rotated north-south on 2026-09-05** and is **3'-4 1/16" x 7'-1 1/4"**
    # between finish faces (x 10'-3 1/4"..13'-7 5/16" off W-B-STR2/W-B-STR3B and W-B-BA-E,
    # y 18'-2 3/8"..25'-3 5/8" off W-B-CW2 and W-B-BA-N). It lost 1 5/16" of width later the
    # same day, when W-B-BA-E slid onto the stair well's partition line so the two would be
    # one plane; nothing in the room had to move for it. One fixture at each end again, so
    # each one's depth runs across the room's short dimension and the door lands between
    # them on the long east wall.
    #
    # `wall_ref` on both is **W-B-BA-E**, the room's one wet wall and its only 5 1/2" stud
    # cavity — venting reads `wall_ref`, not geometry, and W-B-BA-N dropped to a dry 2x4
    # when the plumbing moved off it. Their shared 1 1/2" vent rises in it at
    # (13'-10 11/16", 19'-3") — the wall's own x, which moved with it.
    # Trap arms: lav ~2'-1", WC ~5'-9", both inside Table 1002.2's 3'-6"/6'-0" limits.
    #
    # WC at the NORTH end, backing W-B-BA-N, floor-mounted (a wall-hung carrier wants 6 1/2"
    # of furring this room has nowhere to spend). Bowl x 11'-2"..12'-10", y 22'-11 5/8"..
    # 25'-3 5/8"; UPC 402.5's 24" front envelope then reaches y=20'-11 5/8" and its 15"
    # side clearances land 10'-9"..13'-3", inside the room both ways — 5 5/8" of slack at the
    # west face and 4 5/16" at the east, down from 5 5/8" when the east wall moved.
    Fixture(uid="CBQ801AAAA", tag="FX-B-BATH-WC", type_ref="FX-TOTO-DRAKE",
            room="RM-B-BATH", position=pt(ft(12), inch(289.625)),
            wall_ref="W-B-STR2"),
    # Relocated from the mechanical room's utility sink, so the IFC GlobalId follows the
    # fixture rather than being retired with the tag.
    #
    # ÄNGSJÖN 36 / ORRSJÖN 37, centered in the 39.94 in. south-wall run.
    # Cabinet/top clears the WC envelope; its recommended front zone overlaps it.
    # Trap and supplies follow ServicePorts; the slab drop remains at its existing sleeve.
    Fixture(uid="5BBZTZNBWN", tag="FX-B-BATH-LAV", type_ref="FX-ANGSJON-36-SS",
            room="RM-B-BATH", position=pt(ft(12), inch(229.125)), mount=Mount(elevation=inch(8.375)), rotation=deg(180),
            wall_ref="W-B-STR2"),
)

# RM-M-BATH1: AP wall-hung bowl and roomier D-Code basin share the south wet wall. The aligned storage walls move 1 1/2" north
# for 45.74" finished depth and 24.49" in front of the verified 21 1/4" bowl.
# `wall_ref` on the WC is the overhead vent target; its carrier backs W-M-HS1.
MAIN_FIXTURES = (
    Fixture(uid="CMQ801AAAA", tag="FX-M-BATH1-WC", type_ref="FX-TOTO-AP-WH", room="RM-M-BATH1",
            wall_ref="W-M-BAE",
            mount=Mount(kind=MountKind.WALL, elevation=inch(3)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-M-HS1", face="left", distance_from_start=inch(24.5),
                normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Basin beside the WC screens it from the entry; 34 in. finished rim.
    # Waste offsets 1 1/8 in. west to a clear wet-wall bay, behind the fixing block.
    Fixture(uid="CMQ802AAAA", tag="FX-M-BATH1-LAV", type_ref="FX-DURAVIT-DCODE-070545",
            room="RM-M-BATH1", wall_ref="W-M-HS1",
            drain_position=pt(inch(53.5), inch(268)),
            mount=Mount(kind=MountKind.WALL, elevation=m(0.7186)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-M-HS1", face="left", distance_from_start=inch(54.625),
                normal_gap=inch(0), rotation_offset=deg(-180)))),
    # Backs W-M-HS1 (retyped to the plumbing assembly for it, see storeys/main.py) at
    # rotation 0, which is the rotation that puts the tank on +y.
    #
    # x=2'-6" is bounded on BOTH sides and there is not much room between them. P2705.1
    # wants 15" clear each side of the centreline: west of 1'-9 5/8" the envelope runs into
    # W-M-W3's face, east of 3'-5.24" it runs into the tub deck's west face at x=4'-8.24".
    # 2'-6" sits in that 1'-7 5/8" band, 11 1/4" clear of the deck (7" before the 2026-10-21
    # deck narrowing).
    # y=20'-10 5/8" is the bowl centre with its tank on the wall's new face (22'-0 5/8"
    # less the type's 14" half-depth). The 21" front clearance then reaches to y=17'-11 5/8"
    # and clears FX-M-BATH2-SINK's south end by 1 1/4" — the tightest dimension in the room
    # and the one to re-check if that sink ever moves north.
    #
    # No `drain_position`: the convention (under the bowl) is correct, and PR-B-WC2-DRAIN
    # follows the bowl to its new flange rather than the reverse.
    Fixture(uid="CMQ803AAAA", tag="FX-M-BATH2-WC", type_ref="FX-TOTO-CARLYLE-II", room="RM-M-BATH2",
            position=pt(ft(2, 6), inch(249.74)), rotation=deg(0), wall_ref="W-M-HS1"),
    # BATH2 has separate bathing fixtures: the 36" shower at the south end of the east
    # plumbing wall, the drop-in bath north of it. Intentionally separate instances/types
    # rather than a tub-shower combination, so the permit schedule and future owner
    # selections can treat them independently.
    #
    # The shower sits hard against W-M-BDN1's face at y=13'-2 1/4", and the shower's north
    # face and the tub deck's south face are on the SAME LINE (y=16'-2 1/4"), so
    # W-M-TUBDK-S is one framed 2x3 run doing both jobs — the deck's south knee wall on its
    # north side, the shower's north wall on its south. The two wet fixtures read as one
    # built element down the east wall instead of two boxes with dead floor between them.
    # The room's depth is spent exactly: 36" of shower + 70.365" of deck = 106.365" clear.
    #
    # `drain_position` is unchanged and is NOT the pan's centre — it never was; it is where
    # PR-B-SH2-DRAIN picks the waste up on its way to the stack. Left alone deliberately.
    #
    # ** -5 3/8" WEST, 2026-09-09, AND THE WALL IS WHY. ** W-M-BA2E2 was flush (0" clearance)
    # against this pan's east edge, so taking that wall off its jog and back onto W-M-BA2E's
    # line — one plane, one plumbing assembly (storeys/main.py) — took the pan with it. The
    # pan's east edge is x=94.615" (7'-10 5/8" nominal). This matched the wall's painted
    # west face at the former 6.77" thickness; the current 6.52" wall face is x=94.74", so
    # the pan and N-M-TUBDK-E now stop 1/8" short. At the old face, striking the pan to the
    # gwb at 94.625" put it 1/100" inside the finish. The owner moved the knee wall and pan
    # 1/8" south (2026-10-23), closing the south jamb gap while keeping the 36" pan and
    # north shared line. The aisle to the vanity is 33 11/16".
    # Centre drain (Swanstone SS-3636) at x of the pan centre, but y 2 3/4" north of it: at
    # y=14'-8 1/4" the riser stands on joist 11's top flange (174 3/4"..177 1/4"). y=14'-11" is
    # the nearest bay point that clears the flange by 1/2" for a 2" pipe. PR-B-SH2-DRAIN.
    Fixture(uid="CMQ805AAAA", tag="FX-M-BATH2-SH", type_ref="FX-SHOWER-36-THERMO-COMBO", room="RM-M-BATH2",
            position=pt(ft(6, 4.615), ft(14, 8.25)), rotation=deg(-90), wall_ref="W-M-BA2E",
            drain_position=pt(ft(6, 4.615), ft(14, 11))),
    # ** THE KOHLER K-1130-W1-0 UNDERSCORE, A DROP-IN (2026-10-22; K-5713-W1 before). ** No
    # skirt: it drops through SL-M-TUBDK onto a 1"-2" mortar bed on the subfloor, and the rim
    # carries no load. So this Fixture is the RIM; the deck box in storeys/main.py is what
    # occupies the room.
    #
    # Rim x 5'-2.49"..7'-10.49", 1/8" off W-M-BA2E; y 16'-10 5/8"..21'-10 5/8", 2" of Corian
    # deck at the head. Rotation 90 puts the drain end SOUTH (foot, with the filler) and the
    # lumbar end and Bask heater pad NORTH. Service: FURN-M-BATH2-TUBDK-AP-N at the heater,
    # FURN-M-BATH2-TUBDK-AP at the drain and filler rough.
    #
    # ** THE FLOOR UNDER IT IS STILL NOT SETTLED HERE. ** Kohler's minimum floor load is
    # 59 lb/ft2. Filled, 81 gal = 676 lb of water on 81 lb of shell; with a 200 lb occupant that
    # is 957 lb over 13.33 ft2, ~72 psf against the 40 psf live load, on FS-M-WEST's I-joists.
    # params/main_deck.py blocks and sisters for it; the engineer of record confirms.
    #
    # `drain_position` is the end drain itself: 12 9/16" in from the shell's south end on its
    # centreline (K-1130-W1 drawing), in the 208"..224" joist bay. PR-B-TUB2-DRAIN drops there.
    Fixture(uid="CMQ806AAAA", tag="FX-M-BATH2-TUB", type_ref="FX-KOHLER-UNDERSCORE-6032",
            room="RM-M-BATH2", position=pt(inch(78.49), inch(232.615)), rotation=deg(90),
            wall_ref="W-M-BA2E", drain_position=pt(inch(78.49), inch(215.1775)),
            tub_enclosure=TubEnclosureSpec(
                knee_wall_refs=("W-M-TUBDK-W", "W-M-TUBDK-S"), batt_thickness=inch(2.5),
                access_panel_refs=("FURN-M-BATH2-TUBDK-AP-N", "FURN-M-BATH2-TUBDK-AP"),
                deck_ref="SL-M-TUBDK", support_width=inch(42), support_depth=inch(23.5))),
    # Hole line y=200.41 in. is unchanged; the trim envelope is centred on the tub.
    # Closed handles point outward. The rough and hoses share the foot bay with the K-7272.
    Fixture(uid="XSAHT3AEKA", tag="FX-M-BATH2-FILLER", type_ref="FX-MOEN-ALIGN-ROMAN", room="RM-M-BATH2",
            host_fixture_ref="FX-M-BATH2-TUB",
            position=pt(inch(78.49), inch(203.800625)), rotation=deg(180),
            mount=Mount(kind=MountKind.FLOOR, elevation=inch(21.25))),
    # Floating 48 in. SEKTION: 12 in. storage + 36 in. sink cabinet, AXSTAD fronts,
    # Corian bonded bowl. Wall ports, dedicated stops and vent: mep_lavatories.py.
    Fixture(uid="CMQ807AAAA", tag="FX-M-BATH2-SINK", type_ref="FX-VANITY-48-SEKTION",
            room="RM-M-BATH2", position=pt(inch(15.51), inch(182.25)), rotation=deg(90),
            wall_ref="W-M-W3"),
    # --- RM-M-LAUNDRY -------------------------------------------------------------------
    # 56 1/4"x47 1/4" clear alcove behind D-M-LAUN's 36" pocket door — a
    # closet, not a room you stand in: both appliances back onto the south wall (rotation
    # 180) and front north through the opening. The 27" tower and 24" tub are wider than
    # the opening together, but their centre lines both fall inside it. The tub has 25"
    # clear in front to the doorway; the tower is used while standing in the hall.
    #
    # `wall_ref` W-M-BA2E is the *service* wall (carries the washer standpipe/supply box),
    # not the back wall — both wastes drop through SL-M-DECK to the basement, so there is
    # no wall stack in this room at all.
    #
    # Stacked pair (uid/tag kept so mep.py's `serves=("FX-M-LAUNDRY",)` refs still resolve).
    # Heat-pump dryer is ventless; its condensate drains via PR-M-DRYER-COND to the tub
    # beside it. It is the LG WashTower (plan/appliance_types.py), 27"x32 3/4"x74 3/8",
    # leaving 12 5/8" of clear floor to the door plane.
    Appliance(uid="CMQ804AAAA", tag="FX-M-LAUNDRY", type_ref="APPL-LG-WASHTOWER",
              room="RM-M-LAUNDRY", position=pt(m(2.9421), m(6.01059)), rotation=deg(180),
              wall_ref="W-M-BA2E"),
    # Utility tub, 4 1/4" east of the stack — also the *receptor*: PR-M-DRYER-COND air-gaps
    # over its 34" rim, why the dryer needs no vent or condensate pump line.
    #
    # `drain_position` at y=18'-9" — offset 3" to clear W-B-CW2 (12" concrete on the y=18'
    # axis) — is what SP-M-LSINK/PR-B-LSINK-DRAIN/the 45" trap arm below are all authored on.
    #
    # SL-M-DECK (9" concrete) means every main-storey fixture drops straight down its own
    # sleeve rather than running a trap arm sideways — same as PR-B-SINK2/WASH-DRAIN. The
    # tub wet-vents off the laundry stack: a 45" 2" branch (MN Plumbing Table 1002.2 caps
    # 1 1/2" at 42") ties into PR-M-BATH2-VENT's x=8'-2 1/2" leg, no new pipe. y = 5.86920 m
    # (was 5.82791) is the basin backed onto W-M-CLN, INT_2X4_STAGGERED_GWB's face;
    # `wall_ref`-relative, so it tracks the wall without a coordinate edit here.
    # ** `wall_ref` STILL SAYS W-M-BA2E AND THAT IS NOT THE WALL IT TOUCHES: **
    # W-M-BA2E is 3'-0" west and is where PR-B-CW-WASH/PR-B-HW-WASH rise; the basin's back
    # is on W-M-CLN. Left as authored because `wall_ref` is what the supply pair names as
    # its riser wall and repointing it would move the risers, not the sink.
    Fixture(uid="J7VY2GZ062", tag="FX-M-LAUNDRY-SINK", type_ref="FX-LAUNDRY-SINK-24", room="RM-M-LAUNDRY",
            position=pt(m(3.69703), m(5.86920)), rotation=deg(180), wall_ref="W-M-BA2E",
            drain_position=pt(ft(12, 0), ft(18, 9))),
    # Window-centred x=352", 5/8" east within the fixed 36" base. The 32x19 flange
    # sits forward of a 3" rear faucet zone in the 32x22 installation envelope.
    # Rim meets the underside of 3 cm quartz: 36 - 1.181 - 10 = 24.819" bowl base.
    # Rear-centre drain is 4 1/2" forward of the flange rear, at y=416.99" (moved 1/8" with the 1/2" board, 2026-10-23).
    Fixture(uid="WZRCBGNDFW", tag="FX-M-KITCH-SINK", type_ref="FX-KITCHEN-SINK-32-SINGLE", room="RM-M-LIVING",
            wall_ref="W-M-N1",
            mount=Mount(kind=MountKind.WALL, elevation=inch(24.819)),
            drain_position=pt(inch(352), inch(416.99)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-M-N1", face="left", distance_from_start=inch(80), normal_gap=inch(1),
                rotation_offset=deg(-180)))),
)


# RM-S-BATH1 is the *hall* bath (source's 80.73sf NW "Bathroom"); tag predates the
# suite's own bath (see storeys/second.py).
#
# Tub-shower stays centre-north (crosses x=5', the SL-D-SHOWER detail slice line). WC
# backs west onto exterior 2x6 W-S-W1 (rotation 90), its REQUIRED clearance zone stopping
# 3 1/2" south of the tub-shower. Lav backs east onto W-S-BA-E1B
# (INT_2X6_BRG_PLUMBING_HALF). All three
# footprints are pairwise disjoint with 9"+ clearance between any two.
#
# ALCOVE CHECK. FX-TUBSHOWER-60 is a 60"x30" flanged insert, which is exactly the standard
# alcove footprint (the type's 7'-0" height is the modelled surround envelope, matching
# FX-SHOWER-36 — not a product dimension). A flanged insert nails to studs on THREE sides.
# Measured at real finish faces, FX-S-BATH1-SH has two: the chase wall at x 2'-11 3/8"
# against the tub's west end at 2'-11 3/4" (0.36" of scribe), and the north wall at
# y 35'-5 3/8" against the tub's north edge at 35'-4 1/2". Its EAST end at x 7'-11 3/4" is
# open, with 1'-8 7/8" of dead floor out to the east wall at x 9'-8 5/8".
# FURN-S-BATH1-SHELF (plan/placeables.py) closes it: the shelf's west panel is the return,
# with a 2x4 framed behind it for the flange to nail to. The west side is also real: the
# chase's south corners run the tub's full 30" (storeys/second.py, NODES).
SECOND_FIXTURES = (
    # Centred under WIN-S-BATH-W at y=376" (2026-10-02), 12 1/2" north of the former bay.
    # The 3.5" drain envelope clears FS-S-WEST's 369.75"..382.25" bay faces by 4 1/2";
    # the tub is 18 1/2" from the WC centreline, against UPC 402.5's 15" minimum.
    # The drain bend and radiant-floor keepout follow in mep_drainage.py / storeys/second.py.
    Fixture(uid="CSQ801AAAA", tag="FX-S-BATH1-WC", type_ref="FX-TOTO-AQUIA-IV", room="RM-S-BATH1",
            position=pt(m(0.560313), inch(376)), rotation=deg(90), wall_ref="W-S-W1"),
    # ÄNGSJÖN 36 with the 37 in. ORRSJÖN top: y=356..393, half-inch side overhang.
    # Backs the east finish face; retains 1.5 in. to the tub return and the east-hinged entry.
    Fixture(uid="CSQ802AAAA", tag="FX-S-BATH1-LAV", type_ref="FX-ANGSJON-36",
            room="RM-S-BATH1", position=pt(inch(105.87), inch(374.5)), mount=Mount(elevation=inch(8.375)), rotation=deg(-90),
            wall_ref="W-S-BA-E1B"),
    # ** `drain_position` IS THE WASTE-AND-OVERFLOW AT THE WEST END, NOT THE WET WALL. **
    # The derived convention projects a hot-served fixture onto `wall_ref`'s axis, which for
    # this tub is W-S-BD-N at y=26'-6" — 7'-7" from the tub and in another room. A 60"
    # alcove tub's waste sits against its plumbing end wall on the long centreline: the
    # chase wall's finish face is x=2'-11 3/8", the tub's west end 2'-11 3/4", and the
    # w-and-o tee is 3 1/2" in from it at x=39 1/4". y=409.5" is the tub's own centreline
    # (394.5"..424.5"). The drop lands in the 401.75"..414.25" truss bay with 6" to spare.
    # Its back is exterior W-S-N3, ~0 perm on both sides (insert inside, closed-cell
    # outside), so nothing may ever penetrate it: a hole there dries to neither face.
    Fixture(uid="CSQ803AAAA", tag="FX-S-BATH1-SH", type_ref="FX-TUBSHOWER-60-DIVERTED", room="RM-S-BATH1",
            position=pt(m(1.66988), m(10.4013)), wall_ref="W-S-BD-N",
            drain_position=pt(inch(39.25), inch(409.5))),
    # The suite's own bath (source: 46.01sf). D-S-SUITEBATH's 2'-6" leaf sweeps the room's SW
    # quadrant clear, so WC sits north of the swing against the north wall, lav east of it
    # also against the north wall, shower in the NE corner.
    #
    # `wall_ref` is W-S-SN3 — no `rotation` is authored, and this house's own convention is
    # that an un-rotated FX-TOILET-STD backs a HORIZONTAL wall (FX-M-BATH2-WC on W-M-HS1,
    # rotation=0) while a VERTICAL one needs rotation=90 (FX-S-BATH1-WC on W-S-W1,
    # FX-A-STUBATH-WC on W-A-STU-W). W-S-SN3 is horizontal — this WC physically backs it.
    #
    # It is FLUSH to that wall: back = centre + 14" (the bowl's own 28" projection), so
    # y=250.625" puts the tank against SN3's 264.625" gwb face. Nothing grades a WC against
    # a wall face — `test_..._vanities` covers only vanities.
    #
    # **W-S-DC2 still MUST stay a full-depth wet wall**, though not for anything in THIS
    # room: `PR-S-SUITEBATH-VENT` takes off on SN3 now and its riser is entirely north of
    # DC2. What still needs DC2's 5.5" cavity is the ATTIC studio bath one storey up —
    # `PR-A-STUBATH-DRAIN` drops 10'-0" inside it and `PR-A-CW/HW-STUBATH` rise through it
    # into W-A-STU-W. Retyping DC2 to a 2x4 assembly (e.g. for resilient channel) would
    # leave those with nowhere to run.
    Fixture(uid="CSQ804AAAA", tag="FX-S-SUITEBATH-WC", type_ref="FX-TOTO-AQUIA-IV",
            room="RM-S-SUITEBATH", position=pt(inch(134.81), inch(250.625)),
            wall_ref="W-S-SN3"),
    # Chulton 30: maker top measures 30 15/16 x 22 7/16 in.; north face retained.
    # Maker white-model image specifies a single faucet hole; Genta LX 6702 fits.
    # Rough-ins remain approximate until the manufacturer installation drawing is read.
    Fixture(uid="CSQ805AAAA", tag="FX-S-SUITEBATH-LAV", type_ref="FX-CHULTON-30",
            room="RM-S-SUITEBATH", position=pt(inch(165.5), inch(253.53625)),
            wall_ref="W-S-SN3"),
    # Suite bath takes a tub-shower (not the old 36" pan): room's clear face is
    # 9'-8 1/8" x ~6'-4", and the east wall has 5'-0" of run for a 60"x30" alcove. Rotated
    # -90, back turns east onto W-S-C2C; footprint keeps the old pan's north/east edges,
    # extended south, clearing the WC zone, the south lav, and the door swing.
    #
    # ** THE OPEN END IS CLOSED (2026-09-06), THE SAME WAY THE HALL BATH'S WAS: **
    # FURN-S-SUITEBATH-RETURN (plan/placeables.py) is an 11 1/4" x 30" x 84" open shelf in
    # the gap, open to the west since 2026-10-03; its north divider is the tub's south
    # return, with a 2x4 framed behind it for the flange.
    #
    # ** AND THE TUB IS RE-SEATED ON ITS OWN TWO CLOSED WALLS. ** The 10.4" this note used
    # to quote went stale on 2026-08-30 when W-S-SBS was retyped to a 4 3/4"
    # INT_2X4_PARTITION and both its faces moved 1"; the gap was 11.42". Worse, the same
    # 1" shuffle left this FLANGED insert not touching either wall it is supposed to be
    # flanged to: 1.05" off W-S-C2C's face (x=212.615") to the east, and 0.17" THROUGH
    # W-S-SN3's finish face (y=264.625") to the north. x moves +1.047" and y -0.173" so the
    # back and the north end land exactly on those two planes — which is also what makes
    # the south gap exactly 11 1/4" for the carcass to be built to.
    # ** NOTHING GRADED ANY OF THIS: ** no check tests a flanged fixture against the faces
    # it is flanged to, and the 0.17" over-run read as 0 FAIL.
    # ** `drain_position` IS THE WASTE-AND-OVERFLOW AT THE NORTH END. ** Rotated -90, the
    # 60" dimension runs in y (204.625"..264.625") and the long centreline is x=197.615".
    # The plumbing end is the north one, against W-S-SN3 — the wet wall this bath drains
    # into and the wall PR-S-SUITEBATH-VENT takes off from at (196.5", 263"). The tee is
    # 3 1/2" in from that face. Without this the derivation projects onto `wall_ref`
    # W-S-C2C's axis at x=18'-0", which is inside a bearing wall's studs.
    Fixture(uid="CSQ809AAAA", tag="FX-S-SUITEBATH-TUBSH", type_ref="FX-TUBSHOWER-60-DIVERTED",
            room="RM-S-SUITEBATH", position=pt(inch(197.615), inch(234.625)), rotation=deg(-90),
            wall_ref="W-S-C2C", drain_position=pt(inch(197.615), inch(261.125))),
    # The double-vanity alcove off the landing (source: 18.23 sf, two lavatories), backed
    # onto W-S-BD-N — the same 2x6 wet wall the hall bath drains into.
    #
    # y=305.62" backs onto W-S-BD-N: a lavatory that BACKS a wall has to travel with the
    # wall's own station or it stands off the face by the amount the wall moved (see
    # RM-M-BATH1's note in this file for the same rule). Both mirror lights and the switch
    # above them track the same y (plan/lighting.py).
    # Two SEKTION 30 halves under one 61 in. Corian slab; two drains and two lav loads.
    # Keep 30 in. bowl spacing; ED-S-VANITY-RC1 continues to serve both basins.
    Fixture(uid="CSQ807AAAA", tag="FX-S-VANITY-LAV1", type_ref="FX-VANITY-30-SEKTION",
            room="RM-S-VANITY", position=pt(inch(22.375), inch(307.245)),
            wall_ref="W-S-BD-N"),
    Fixture(uid="CSQ808AAAA", tag="FX-S-VANITY-LAV2", type_ref="FX-VANITY-30-SEKTION",
            room="RM-S-VANITY", position=pt(inch(52.375), inch(307.245)),
            wall_ref="W-S-BD-N"),
)


# Garage wash-down yard hydrant standing free beside the service stair.
#
# Stands on SL-G-FLOOR (the garage slab at 0'-0"), 1'-10" below the `garage` storey datum
# (the ICF stem top). `resolve/placeables.py` measures mount height off the room's floor
# (resolve/room_floor.py), not the storey datum — off the datum this (and everything else
# in the room) would float 22" in the air.
#
# Handle height (2'-6") is the type's own; everything below the slab (barrel, shutoff,
# supply, sleeve) is authored in params/foundations.py and plan/mep.py, none UI-movable.
# This instance is, which is why it lives here rather than in fixture_types.py.
GARAGE_FIXTURES = (
    # No `wall_ref`, deliberately: a 6'-0"-bury yard hydrant can't stand against a wall here
    # without its shutoff/weep stone entering the perimeter footing's 45° influence line.
    # Stands free at (11'-0", 48'-1 5/16") on the buried service line: the southernmost
    # 1/16" station clearing the drywell's footing influence line (params/foundations.py).
    # Moved 4 11/16" south on 2026-10-13 after the interior landing was retired.
    Fixture(uid="CGQ801AAAA", tag="FX-G-HYDRANT", type_ref="FX-HYDRANT-Y34SS",
            room="RM-GARAGE", position=pt(ft(11), ft(48, 1.3125))),
)

# --- the guest studio: bath + wet bar ---------------------------------------------------
# The bath box is x 9'-10 7/8"..17'-8 5/8", y 17'-6 3/8"..22'-1 5/8" — ENTIRELY INSIDE
# RM-S-SUITEBATH's footprint one storey down, which is the whole point of where it is.
#
# ** `wall_ref="W-A-STU-W"` ON ALL THREE FIXTURES, INCLUDING THE SHOWER THAT BACKS W-A-C2. **
# That is FX-B-BATH-WC/FX-B-BATH-LAV's exact idiom above ("it's the room's only stud cavity,
# carries their shared vent"), and it is load-bearing for both `mep.vent_reachability` and
# `mep.trap_arm_length`: W-A-STU-W is the 5 1/2" 2x6 wet wall stacked on W-S-DC2, and
# every drop in this suite lands in it.
#
# ** advisory.fixture_overlap PASSES, AND THE TIGHT DIMENSION IS 2". ** FX-TOILET-STD's one
# REQUIRED ClearanceZone (library/placeables/fixtures.py) is 15" each side of centreline and
# depth/2 + 21" in front; at rotation=deg(90) that projects east to x 9'-10 7/8"..13'-11 7/8",
# y 19'-5"..21'-11". The lavatory clears its south edge by 2", the shower clears its east edge
# by 8 3/4", and all three footprints are pairwise disjoint. The finding trigger is ~1.55 in2,
# so 2" over an 18" face is not much slack — ** IF THE LAV MOVES, MOVE IT SOUTH AND RE-CHECK. **
# ** THE WC BELONGS ON THE WET WALL, NOT THE NORTH WALL — A MISREADING OF EXCEPTION 2. **
# Putting the WC on the north wall and the lavatory on the south, both crammed into the
# same 20 inches of x, rests on the claim "Minn. R. 1309.0305 Exception 2 asks 6'-8" over
# the fixture and its front clearance". It does not. The exception reads:
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
# ** THE CLEARANCE ENVELOPE IS 15" + 24", NOT 15" + 21", AND IT IS CHECKED. ** The front
# dimension is UPC 402.5's 24" (derivation at the head of library/placeables/fixtures.py:
# Minn. R. 1309.0307 -> ch. 4714 -> the 2018 UPC, unamended; IRC's 21" is not Minnesota's
# number). `active_code_profile="MN/IRC"` in plan/manifest.py is what makes
# `_resolved_clearance_zones` keep the zone instead of dropping it, so
# `integrity.placeable_required_clearance_conflict` is live here. Do not trust any comment
# in this repo that says these envelopes are inert; check the manifest.
#
# What is still ungraded is whether the envelope FITS THE ROOM: `_clearance_conflicts`
# compares a zone against peer placeable FOOTPRINTS only, never against a wall. Every
# distance-to-a-wall figure below was measured by hand off the resolved layer polygons.
# `code.R305_ceiling_height` grades the ROOM, not a fixture against the rake. On the finished
# ceiling face (rafter underside less paint and 5/8" GWB), the attic bath has 17.97 of its
# 35.30 sf (50.9%) at or above 7'-0", and all 35.30 sf is at or above 5'-0". That R305.1
# Exception 1 pass is only 0.32 sf over the 50% line. The fixture measurements below are
# therefore checked separately against R305.1 Exception 2.
#
# ** THE WATER CLOSET GOES BACK ON THE WET WALL, WHICH IS THE ONLY WALL IT CAN PLUMB INTO. **
# Back to W-A-STU-W's east face at x 9'-10 7/8", facing east, c/l at y 20'-8" -> 19'-4". The
# finished ceiling face is about 5'-8" over the seat — you SIT there, and Exception 2's usability
# test is satisfied by a fixture you use seated. What the exception actually measures is the
# centre of the 24" front clearance, at x 13'-3 1/16", where the resolved finish-face height is
# ** about 6'-9 1/16" **. That clears 6'-8" by about 1 1/16", and it is the whole reason this
# fixture can be on this wall at all. These heights include the sloped paint/GWB lining.
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
# x >= 13'-1", D-A-STUBATH's west jamb at 13'-11 1/2" wants x <= 13'-1", and the old 13'-2"
# station missed on BOTH sides — 1" of its bowl stood inside the door's rough opening. The
# north wall has neither stop.
#
#   LAV c/l (13'-8 5/8", 21'-4 5/8"), no rotation.  footprint x 12'-8 5/8"..14'-8 5/8",
#       y 20'-7 5/8"..22'-1 5/8". ** THIS IS A 24" VANITY AS OF 2026-09-09, NOT A BARE
#       BOWL ** — see the note on the fixture itself. The underside rises 1/2" per inch of
#       x here, so the 2 5/8" it moved east buys 1 5/16" of headroom on top of the three
#       inches the north wall already had over the south. It is boxed on three sides and
#       every gap is deliberate: 5/8" west to ED-A-STUBATH-GFCI's plate, 5/8" south to the
#       WC's clearance zone, and its east end dies flat into the shower's west panel at
#       14'-8 5/8" and is scribed to it. There is no slack left on this wall.
#
# The trap arms all improved on the move, which is the tell that the fixtures went where the
# plumbing already was rather than the other way round: WC 8" -> 16", lav 31" -> 0", shower
# 0", bar 50" -> ~0 on its own revent, against limits of 72"/72"/72"/60". The lavatory's drop
# followed its basin 2" north to y 21'-4 5/8" (plan/mep_drainage.py) and its arm is unchanged.
#
# The shower's bounding box did not move: 14'-8 5/8"..17'-8 5/8" x 19'-1 5/8"..22'-1 5/8",
# flush into the NE corner, under 7'-6 11/16" and up. ** ITS SW CORNER IS CUT BACK 16" ON
# EACH LEG AS OF 2026-09-09 ** (FX-SHOWER-36-NEO-COMBO), which is the corner a person walks
# into coming through the door — the whole derivation is on the type in
# plan/fixture_types_wc.py. One fixture per wall, and the floor you enter onto is clear.
#
# ** `wall_ref` STAYS `W-A-STU-W` ON ALL THREE, AND THAT IS NOT A LEFTOVER. ** In this file
# wall_ref names the WET wall a fixture plumbs into, not the wall it physically hangs on —
# the shower has read that way since the suite was authored ("including the shower that
# backs W-A-C2", above). W-A-STU-W is still the one 5 1/2" 2x6 cavity in the attic and
# every drop still lands in it; `mep.vent_reachability` and `mep.trap_arm_length` both key
# off that, and PR-A-STUBATH-VENT still has a vertex on its axis. It is now literally true
# of the water closet as well, which is new.
ATTIC_FIXTURES = (
    # Floor-mount, not FX-TOILET-WH: a wall-hung carrier costs a 6" chase this room need not buy.
    Fixture(uid="WCM0PV9H71", tag="FX-A-STUBATH-WC", type_ref="FX-TOTO-DRAKE", room="RM-A-STUBATH",
            position=pt(ft(11, 0.875), ft(19, 4)), rotation=deg(90),
            wall_ref="W-A-STU-W"),
    # SEKTION 24 / AXSTAD with an 18 in. deep Corian bonded-bowl top.
    # The north-wall port and local revent replace the old 49 in. undrawn trap arm.
    # The existing under-floor drop avoids the hall trimmer and beam.
    Fixture(uid="N2BDQ3T63Z", tag="FX-A-STUBATH-LAV", type_ref="FX-VANITY-24-SEKTION-SS", room="RM-A-STUBATH",
            position=pt(inch(164.625), inch(256.625)),
            wall_ref="W-A-STU-W"),
    # A 36" NEO-ANGLE pan in the NE corner — retyped from the 36" square 2026-09-09 to open
    # the diagonal a person walks on coming through D-A-STUBATH; the geometry, the P2708.1
    # arithmetic and the 22 5/8" door-opening limit are all on the type. The bounding box,
    # this position and the drain are unchanged by that retype, so nothing downstream moved.
    # ** NOT FX-TUBSHOWER-60 ** — a 60" insert costs more, needs
    # three nailable walls (the 2026-08-21 alcove audit above), and a guest suite does not want
    # a tub. R305 is not the constraint here either: the roof underside over this corner is
    # 10'-6" and up.
    # ** `drain_position` IS THE PAN'S GRATE, WHICH IS ALSO ITS CENTRE. ** `wall_ref` here
    # names the WET wall, not the wall the pan touches (see the note above this tuple), so
    # the derived convention put this shower's drain 6'-7" west, on W-A-STU-W's axis. A 36"
    # pan drains at its centre, and PR-A-STUBATH-VENT already takes off there.
    Fixture(uid="P63E8HB7WZ", tag="FX-A-STUBATH-SH", type_ref="FX-SHOWER-36-NEO-COMBO", room="RM-A-STUBATH",
            position=pt(ft(16, 2.625), ft(20, 7.625)), wall_ref="W-A-STU-W",
            drain_position=pt(ft(16, 2.625), ft(20, 7.625))),
    # SUNNERSTA's own integral sink, with fixed-stainless Indy and a tubular trap.
    # Bowl station is unpublished: APPROXIMATE ports remain explicit in the catalog.
    Fixture(uid="11TZJE81BZ", tag="FX-A-STUDIO-BAR-SINK", type_ref="FX-SUNNERSTA-BAR-SINK", room="RM-A-STUDIO",
            wall_ref="W-A-STU-W",
            mount=Mount(kind=MountKind.WALL, elevation=inch(27)),
            location=Location(attachment=WallAttachment(
                wall_ref="W-A-BATH-S", face="right", distance_from_start=inch(37),
                normal_gap=inch(3), rotation_offset=deg(0)))),
)


# --- the two south-face wall hydrants ---------------------------------------------------
# Unlike FX-G-HYDRANT (a *yard* hydrant, 6' bury, self-draining below frost), these are
# *wall* hydrants: seat inside the envelope at the inboard end of a ~10" barrel that
# self-drains outward when closed. Not buried, not shut down for winter — the owner's ask.
#
# Both on the south face, serving the porch (0'-0") and balcony (10' up) outdoor rooms:
#   FX-M-PORCH-HYD  x=12'-8" on W-M-S1, the blank stretch between WIN-M-BED-S1 and
#                   WIN-M-BED-S2 (RO 13'-5"..15'-11"), leaving 9" of clear wall to that
#                   jamb. **12'-0" until 2026-09-15, which was dead on stud-006**: the
#                   barrel was bored straight through a stud and nothing in the model
#                   graded it. W-M-S1 resolves stud-006 at 144"..145 1/2" and king-1-l0 at
#                   158 3/4", so the clear bay is 145 1/2"..158 3/4" and its centre is
#                   152 1/8". 12'-8" is that centre to the nearest inch — the same rounding
#                   FX-S-BALC-HYD already carries (authored 88", clear centre 88 1/8").
#                   BK-M-S1-HYD spans 128 3/4"..158" and covers the new station unchanged.
#   FX-S-BALC-HYD   x=7'-4" on W-S-S1, a 16" module bay centre behind RM-S-PLANT (which
#                   the balcony irrigation this hydrant feeds actually waters). It lands in
#                   the 2'-10" of blank wall between WIN-S-PLANT1 and WIN-S-PLANT2 — the
#                   only bay left on this wall not spoken for, since the 1'-7" west of the
#                   door took ED-S-PLANT-RC1 (plan/electrical.py).
#
# Each names the room *behind* it, which draws an `integrity.placeable_room_mismatch`
# (footprint centre outside its assigned room) — correct for an exterior hose bib whose
# escutcheon is outdoors; leaving `room` unset would trade that for a worse
# `advisory.fixture_room_unassigned` FAIL with a blank permit-schedule cell.
#
# The pierced wall is EXT_2X6 with 4" continuous exterior insulation, so the hydrant's seat
# and feed stay on the warm side of the thermal break — a cavity-only wall would freeze this
# detail.
#
# ** THE MOUNT IS RE-STATED ON THE ELEMENT, AND IT HAS TO BE (2026-09-15). ** This block
# used to say "Mount is WALL/24" from the type" and that was simply not true of the model.
# `Placeable.mount` is NON-OPTIONAL (`model/spatial.py`), so an element that says nothing
# still carries a default `Mount()` — FLOOR, no elevation — and a default beats a type. Both
# hydrants were therefore resolving at their storey's floor: FX-M-PORCH-HYD at 1 1/4", and
# FX-S-BALC-HYD a full 24" BELOW the ft(2) supply barrel that feeds it (plan/mep_supply.py).
#
# The fix is not a resolver-wide "fall back to the type when the element is silent", because
# a non-optional field cannot tell "the author said FLOOR" from "the author said nothing" —
# such a fallback would silently overrule every deliberate floor mount in every house. The
# convention is to re-state it on the element, as FURN-M-LAUNDRY-RACK already does. Written
# out at each element rather than shared through a module constant: this file is
# `# haus: editable` and a UI drag rewrites these calls, so every argument stays a literal
# the writer can round-trip.
PORCH_HYDRANT = (
    Fixture(uid="7QK2M4XR0B", tag="FX-M-PORCH-HYD", type_ref="FX-HYDRANT-SD34",
            room="RM-M-BED", wall_ref="W-M-S1",
            mount=Mount(kind=MountKind.WALL, elevation=inch(24), recessed_into_host_surface=True),
            location=Location(attachment=WallAttachment(
                wall_ref="W-M-S1", face="right", distance_from_start=inch(152),
                normal_gap=inch(-10.25), rotation_offset=deg(0)))),
)
BALCONY_HYDRANT = (
    Fixture(uid="D3NLW8VC5T", tag="FX-S-BALC-HYD", type_ref="FX-HYDRANT-SD34",
            room="RM-S-PLANT", wall_ref="W-S-S1",
            mount=Mount(kind=MountKind.WALL, elevation=inch(24), recessed_into_host_surface=True),
            location=Location(attachment=WallAttachment(
                wall_ref="W-S-S1", face="right", distance_from_start=inch(88),
                normal_gap=inch(-10.25), rotation_offset=deg(0)))),
)
