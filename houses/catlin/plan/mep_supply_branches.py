# haus: editable
# Supply branches to the WC stops, the shower and tub-filler valve bodies and the dishwasher
# (2026-10-31): until now each of these fixtures was served only by a trunk that ended feet
# away. BASEMENT_SUPPLY_BRANCHES is basement-relative (main floor = 109 7/16"); the main list
# is filed like mep_lavatories.py, so its elevations are project-absolute.
#
# Sizes: every branch is 1/2" PEX (a WC is 2.5 WSFU cold, a shower 1.5, the tub 3 each side,
# against the 4 WSFU a 1/2" branch carries). Stops follow the lavatories: an angle stop at
# each WC; the valve bodies and the filler rough carry none, as before.
from typehaus import PipeAccessory, PipeAccessoryKind, PipeRun, PipeSystem, inch, pt

_ANGLE_STOP = '1/2 in. quarter-turn fixture angle stop'

BASEMENT_SUPPLY_BRANCHES = [
    # FX-B-BATH-WC. Its back wall W-B-BA-N sits under FS-M-STAIR's partition blocks, and the
    # x=10'-0" bearing line has full-depth blocking, so the branch leaves the cold trunk at
    # y=16'-0", rides 2" over the band (over PR-B-CW-SUITE's diagonal) north through the
    # joist webs at x=11'-7 1/2", and drops in BA-N's front half: PR-B-ERV-COND runs the
    # cavity's centre line at 5'-0" above the slab.
    PipeRun(uid="WV0NXH51VG", tag="PR-B-BATH-WC-CW", system=PipeSystem.WATER_COLD,
            path=(pt(inch(139.5), inch(192)), pt(inch(139.5), inch(192)),
                  pt(inch(139.5), inch(304.875)), pt(inch(139.5), inch(304.875)),
                  pt(inch(139.5), inch(303.8125)),),
            elevations=(inch(100.6375), inch(102.6375), inch(102.6375), inch(8.12),
                        inch(8.12),),
            diameter=inch(0.5), material="pex", serves=("FX-B-BATH-WC",)),
    PipeAccessory(uid="GT1SR1TGKY", tag="PA-B-BATH-WC-STOP", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-BATH-WC-CW", position=pt(inch(139.5), inch(303.8125)),
                  elevation=inch(8.12), accessible=True, room="RM-B-BATH", model=_ANGLE_STOP,
                  serves=("FX-B-BATH-WC",)),
    # FX-M-BATH2-WC. Its stop is in front of FX-M-BATH1-WC's DuoFit carrier bay (W-M-HS1,
    # x 1'-2 5/8"..2'-10 3/8"), which the frame fills, so it is floor-fed: off PR-B-CW-BATH2's
    # x=1'-0" leg, east in FS-M-MECH's bay and up through the floor clear of the base.
    PipeRun(uid="DP63F1BTDQ", tag="PR-B-BATH2-WC-CW", system=PipeSystem.WATER_COLD,
            path=(pt(inch(12), inch(263.6)), pt(inch(24), inch(263.6)), pt(inch(24), inch(263.6)),),
            elevations=(inch(100.6375), inch(100.6375), inch(118.9375),),
            diameter=inch(0.5), material="pex", serves=("FX-M-BATH2-WC",)),
    # FX-M-BATH2-SH's valve in W-M-BA2E2. Cold off the trunk at x=7'-0", 2" over the band to
    # cross PR-B-HW-SAUNA, and up the wall at 8'-1 1/2"; hot off PR-B-HW-TRUNK's low x=7'-6"
    # leg, up into the joist web (over PR-M-S-SUITE-DRAIN) and south to 8'-0 1/2". Both rise
    # in the wall and stub west to the valve body.
    PipeRun(uid="A4PYMFZWY8", tag="PR-B-BATH2-SH-CW", system=PipeSystem.WATER_COLD,
            path=(pt(inch(84), inch(192)), pt(inch(84), inch(192)), pt(inch(84), inch(174.25)),
                  pt(inch(97.5), inch(174.25)), pt(inch(97.5), inch(174.25)),
                  pt(inch(94.615), inch(174.25)),),
            elevations=(inch(100.6375), inch(102.6375), inch(102.6375), inch(102.6375),
                        inch(158.1875), inch(158.1875),),
            diameter=inch(0.5), material="pex", serves=("FX-M-BATH2-SH",)),
    PipeRun(uid="7QKQM2TYZV", tag="PR-B-BATH2-SH-HW", system=PipeSystem.WATER_HOT,
            path=(pt(inch(90), inch(206)), pt(inch(90), inch(206)), pt(inch(96.5), inch(206)),
                  pt(inch(96.5), inch(178.25)), pt(inch(96.5), inch(178.25)),
                  pt(inch(94.615), inch(178.25)),),
            elevations=(inch(84.4375), inch(99.4375), inch(99.4375), inch(99.4375),
                        inch(158.1875), inch(158.1875),),
            diameter=inch(0.5), material="pex", serves=("FX-M-BATH2-SH",)),
    # FX-M-BATH2-FILLER: the 4794 rough's inlets, inside the tub deck's foot bay (reached
    # through FURN-M-BATH2-TUBDK-AP). Both rise inside the trim's footprint, between
    # W-M-TUBDK-S and the shell: cold off the trunk 2" over the band, west of the joist bay's
    # sister block; hot off PR-B-HW-TRUNK's y=17'-0" leg, stepping up between
    # PR-M-S-SUITE-DRAIN and PR-B-HW-SUITE to cross over the drain. They name the tub too, whose fixture-unit row is the demand.
    PipeRun(uid="CN849KDC10", tag="PR-B-FILLER-CW", system=PipeSystem.WATER_COLD,
            path=(pt(inch(71.25), inch(192)), pt(inch(71.25), inch(192)),
                  pt(inch(71.25), inch(200.41)), pt(inch(71.25), inch(200.41)),
                  pt(inch(73.49), inch(200.41)),),
            elevations=(inch(100.6375), inch(102.6375), inch(102.6375), inch(126.9375),
                        inch(126.9375),),
            diameter=inch(0.5), material="pex",
            serves=("FX-M-BATH2-TUB", "FX-M-BATH2-FILLER")),
    PipeRun(uid="TAXS7CPYFM", tag="PR-B-FILLER-HW", system=PipeSystem.WATER_HOT,
            path=(pt(inch(83.49), inch(204)), pt(inch(83.49), inch(204)),
                  pt(inch(83.49), inch(201.5)), pt(inch(83.49), inch(201.5)),
                  pt(inch(83.49), inch(200.41)),),
            elevations=(inch(84.4375), inch(91.4375), inch(91.4375), inch(126.9375),
                        inch(126.9375),),
            diameter=inch(0.5), material="pex",
            serves=("FX-M-BATH2-TUB", "FX-M-BATH2-FILLER")),
]

MAIN_SUPPLY_BRANCHES = [
    PipeAccessory(uid="WRA95ZSZCT", tag="PA-M-BATH2-WC-STOP", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-B-BATH2-WC-CW", position=pt(inch(24), inch(263.6)),
                  elevation=inch(9.5), accessible=True, room="RM-M-BATH2",
                  model='1/2 in. quarter-turn angle stop on a floor supply',
                  serves=("FX-M-BATH2-WC",)),
    # FX-M-BATH1-WC: the DuoFit's inlet, lower left of the frame. Tees off the cold riser in
    # W-M-HS1 at the inlet height and runs west in the north half of the staggered cavity,
    # behind PR-B-LAV1-DRAIN's riser, into the carrier bay.
    PipeRun(uid="X0H9SF01VD", tag="PR-M-BATH1-WC-CW", system=PipeSystem.WATER_COLD,
            path=(pt(inch(60), inch(268)), pt(inch(60), inch(270)), pt(inch(33.3), inch(270)),
                  pt(inch(33.3), inch(268)),),
            elevations=(inch(12.7), inch(12.7), inch(12.7), inch(12.7),),
            diameter=inch(0.5), material="pex", serves=("FX-M-BATH1-WC",)),
    PipeAccessory(uid="MV7GG2CP2B", tag="PA-M-BATH1-WC-STOP", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-M-BATH1-WC-CW", position=pt(inch(33.3), inch(268)),
                  elevation=inch(12.7), accessible=True, room="RM-M-BATH1",
                  model="DuoFit cistern's 1/2 in. angle valve, reached through the flush plate",
                  serves=("FX-M-BATH1-WC",)),
    # RM-S-BATH1 (owner, 2026-10-31): the shower pair drops down the chase wall W-S-CH-W, and
    # FX-S-BATH1-WC's stop carries on down the chase from the cold's valve tee and through
    # the floor, so nothing enters exterior W-S-W1. Both leave the PR-B-*-SBATH riser heads
    # and run north in FS-ATTIC's joist webs: DU-M-ERV-EXH-TRUNK fills FS-S-WEST's depth on
    # x=3'-9 3/4", so nothing reaches the chase from the risers through the second floor.
    # Cold at 19'-8", hot 2" over it at 19'-10", both over PR-S-BATH1-VENT and south of
    # VR-M-STACK's +19'-6" jog. 3/4" cold: the
    # tub-shower and the WC are 5.5 WSFU.
    PipeRun(uid="9BDG7R9DHR", tag="PR-S-BATH1-SH-CW", system=PipeSystem.WATER_COLD,
            path=(pt(inch(63), inch(318.75)), pt(inch(63), inch(318.75)),
                  pt(inch(63), inch(410.25)), pt(inch(32.5), inch(410.25)),
                  pt(inch(32.5), inch(410.25)), pt(inch(32.5), inch(411.5)),
                  pt(inch(35.743), inch(411.5)),),
            elevations=(inch(214), inch(236), inch(236), inch(236), inch(150.75),
                        inch(150.75), inch(150.75),),
            diameter=inch(0.75), material="pex",
            serves=("FX-S-BATH1-SH", "FX-S-BATH1-WC")),
    PipeRun(uid="JV56ZZP8TZ", tag="PR-S-BATH1-SH-HW", system=PipeSystem.WATER_HOT,
            path=(pt(inch(76), inch(319.5)), pt(inch(76), inch(319.5)),
                  pt(inch(76), inch(407.5)), pt(inch(32.5), inch(407.5)),
                  pt(inch(32.5), inch(407.5)), pt(inch(35.743), inch(407.5)),),
            elevations=(inch(212), inch(238), inch(238), inch(238), inch(150.75),
                        inch(150.75),),
            diameter=inch(0.5), material="pex", serves=("FX-S-BATH1-SH",)),
    # The floor-fed stop: down the chase past the valve tee into FO-S-ERV-CHASE, east of the
    # ERV riser ducts, south through the trusses' 1'-5 1/2"..2'-6 1/2" web opening, west in
    # the 29'-4"..30'-8" bay under the closet bend, and up clear of W-S-W1's base, 2 1/2"
    # south of the bowl.
    PipeRun(uid="ABVF7VKHZX", tag="PR-S-BATH1-WC-CW", system=PipeSystem.WATER_COLD,
            path=(pt(inch(32.5), inch(410.25)), pt(inch(32.5), inch(410.25)),
                  pt(inch(32.5), inch(401)), pt(inch(26), inch(401)), pt(inch(26), inch(362)),
                  pt(inch(7.75), inch(362)), pt(inch(7.75), inch(365.5)),
                  pt(inch(7.75), inch(365.5)),),
            elevations=(inch(150.75), inch(113.5), inch(113.5), inch(113.5), inch(113.5),
                        inch(113.5), inch(113.5), inch(129.5),),
            diameter=inch(0.5), material="pex", serves=("FX-S-BATH1-WC",)),
    PipeAccessory(uid="A82N47N43Z", tag="PA-S-BATH1-WC-STOP", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-S-BATH1-WC-CW", position=pt(inch(7.75), inch(365.5)),
                  elevation=inch(129.5), accessible=True, room="RM-S-BATH1",
                  model='1/2 in. quarter-turn angle stop on a floor supply',
                  serves=("FX-S-BATH1-WC",)),
    # RM-S-SUITEBATH, all in W-S-SN3's staggered cavity off the suite risers: the WC west on
    # the axis, the tub-shower pair east (hot on the axis, cold in the south half 6" lower,
    # under the lav stops' drops).
    PipeRun(uid="N9GFY7KNY7", tag="PR-S-SUITE-WC-CW", system=PipeSystem.WATER_COLD,
            path=(pt(inch(163.2), inch(268)), pt(inch(128.81), inch(268)),
                  pt(inch(128.81), inch(264.406)),),
            elevations=(inch(129.5), inch(129.5), inch(129.5),),
            diameter=inch(0.5), material="pex", serves=("FX-S-SUITEBATH-WC",)),
    PipeAccessory(uid="D8WJ6Z924S", tag="PA-S-SUITE-WC-STOP", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-S-SUITE-WC-CW", position=pt(inch(128.81), inch(264.406)),
                  elevation=inch(129.5), accessible=True, room="RM-S-SUITEBATH",
                  model=_ANGLE_STOP, serves=("FX-S-SUITEBATH-WC",)),
    PipeRun(uid="KNTMDJRJPN", tag="PR-S-SUITE-TUBSH-HW", system=PipeSystem.WATER_HOT,
            path=(pt(inch(171.6), inch(268)), pt(inch(195.615), inch(268)),
                  pt(inch(195.615), inch(268)), pt(inch(195.615), inch(264.625)),),
            elevations=(inch(150), inch(150), inch(150.75), inch(150.75),),
            diameter=inch(0.5), material="pex", serves=("FX-S-SUITEBATH-TUBSH",)),
    PipeRun(uid="TRYB9RHBHH", tag="PR-S-SUITE-TUBSH-CW", system=PipeSystem.WATER_COLD,
            path=(pt(inch(163.2), inch(268)), pt(inch(163.2), inch(266.25)),
                  pt(inch(199.615), inch(266.25)), pt(inch(199.615), inch(266.25)),
                  pt(inch(199.615), inch(264.625)),),
            elevations=(inch(144), inch(144), inch(144), inch(150.75), inch(150.75),),
            diameter=inch(0.5), material="pex", serves=("FX-S-SUITEBATH-TUBSH",)),
    # RM-A-STUBATH: the WC stop off the cold riser in W-A-STU-W, south in the cavity; the
    # shower pair carries on east from the lavatory branches' corners along the north wall
    # (W-A-HALL-S), the hot in the cavity's front half past the lav revent and shower vent.
    PipeRun(uid="CXYTEY6C5D", tag="PR-A-STUBATH-WC-CW", system=PipeSystem.WATER_COLD,
            path=(pt(inch(113.5), inch(246)), pt(inch(113.5), inch(226)),
                  pt(inch(118.688), inch(226)),),
            elevations=(inch(248.87), inch(248.87), inch(248.87),),
            diameter=inch(0.5), material="pex", serves=("FX-A-STUBATH-WC",)),
    PipeAccessory(uid="0F21Q8EDD6", tag="PA-A-STUBATH-WC-STOP", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-A-STUBATH-WC-CW", position=pt(inch(118.688), inch(226)),
                  elevation=inch(248.87), accessible=True, room="RM-A-STUBATH",
                  model=_ANGLE_STOP, serves=("FX-A-STUBATH-WC",)),
    PipeRun(uid="9DJH46T5SR", tag="PR-A-STUBATH-SH-HW", system=PipeSystem.WATER_HOT,
            path=(pt(inch(161.625), inch(267.5)), pt(inch(162.5), inch(266.6)),
                  pt(inch(192.625), inch(266.6)), pt(inch(192.625), inch(266.6)),
                  pt(inch(192.625), inch(265.625)),),
            elevations=(inch(272), inch(272), inch(272), inch(288.75), inch(288.75),),
            diameter=inch(0.5), material="pex", serves=("FX-A-STUBATH-SH",)),
    PipeRun(uid="S8XSR4YYBZ", tag="PR-A-STUBATH-SH-CW", system=PipeSystem.WATER_COLD,
            path=(pt(inch(167.625), inch(266)), pt(inch(196.625), inch(266)),
                  pt(inch(196.625), inch(266)), pt(inch(196.625), inch(265.625)),),
            elevations=(inch(270), inch(270), inch(288.75), inch(288.75),),
            diameter=inch(0.5), material="pex", serves=("FX-A-STUBATH-SH",)),
    # APPL-M-DW: tees off the kitchen hot riser 5 1/2" over the floor and runs west behind
    # the cold riser, along the cabinet backs, to the machine's inlet. Its stop is in the
    # sink base. Two legs, each ending at a terminal: a third would read as transit.
    PipeRun(uid="0JY6SHV11S", tag="PR-M-DW-HW", system=PipeSystem.WATER_HOT,
            path=(pt(inch(363.6), inch(421.5)), pt(inch(363.6), inch(422.75)),
                  pt(inch(314.175), inch(422.75)),),
            elevations=(inch(5.5), inch(5.5), inch(5.438),),
            diameter=inch(0.5), material="pex", serves=("APPL-M-DW",)),
    PipeAccessory(uid="8C6JYRFZWJ", tag="PA-M-DW-STOP", kind=PipeAccessoryKind.SHUTOFF,
                  pipe_ref="PR-M-DW-HW", position=pt(inch(358), inch(422.75)),
                  elevation=inch(5.5), accessible=True, room="RM-M-LIVING",
                  model='1/2 in. quarter-turn dishwasher stop, in the sink base',
                  serves=("APPL-M-DW",)),
]
