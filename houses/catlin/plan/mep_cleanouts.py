# haus: editable
# Catlin sanitary cleanouts, paired with their physical access caps.

from typehaus import DrainCleanout, ft, inch, pt

BASEMENT_CLEANOUTS = [
    # The building drain's cleanout at the sewer connection (UPC 719.1), INSIDE the wall:
    # a two-way fitting 2'-0" short of FT-B-N4 at x=3'-6", capped flush in RM-B-FURNACE's floor beside
    # SM-B-RADON. Two-way inside the wall is also 707.4 exception 4, so it stands in for an
    # upper-terminal cleanout at the collector's head. It was a 94" riser to grade in the
    # rear yard while the sewer left south.
    DrainCleanout(uid="COB0000001", tag="CO-B-SEWER", pipe_ref="PR-B-MAIN-DRAIN",
                  position=pt(inch(42), ft(34)), fitting_elevation=inch(-19.46875),
                  cap_position=pt(inch(42), ft(34)), cap_elevation=inch(0),
                  direction="two_way", access="floor",
                  clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000009", tag="CO-B-COLLECTOR", pipe_ref="PR-B-MAIN-DRAIN",
                  position=pt(ft(5, 3), ft(16, 6)), fitting_elevation=inch(83.7375),
                  cap_position=pt(ft(5, 3), ft(17, 9)), cap_elevation=inch(87.7375),
                  direction="two_way", access="wall", wall_ref="W-B-CW",
                  clear_width=inch(24), clear_depth=inch(24)),
    # The stack's base turns the main north, and PR-B-BATH-DRAIN's tie (y=17'-4 3/4") turns
    # the bath branch north into it before the main's two 1/8 bends at y=17'-10". Two-way,
    # between that tie and the bends (since the 2026-11-05 905 reroute, which put the bath
    # branch's own turn cleanout upstream), capped flush in the workshop floor.
    DrainCleanout(uid="COB0000010", tag="CO-B-STACK-BASE", pipe_ref="PR-B-MAIN-DRAIN",
                  position=pt(ft(3), inch(211.25)), fitting_elevation=inch(-15.28),
                  cap_position=pt(ft(3), inch(211.25)), cap_elevation=inch(0),
                  direction="two_way", access="floor",
                  clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000003", tag="CO-B-KITCH-HEAD", pipe_ref="PR-B-KITCH-DRAIN",
                  position=pt(inch(352), inch(416.99)), fitting_elevation=inch(106.25),
                  cap_position=pt(inch(352), inch(416.99)), cap_elevation=inch(121.4375),
                  access="cabinet", clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000004", tag="CO-B-KITCH-TURN", pipe_ref="PR-B-KITCH-DRAIN",
                  position=pt(ft(9, 8), ft(35)), fitting_elevation=inch(96.21875),
                  cap_position=pt(ft(9, 10.2), ft(35)), cap_elevation=inch(100.21875),
                  access="wall", wall_ref="W-B-STR",
                  clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000005", tag="CO-B-LSINK", pipe_ref="PR-B-LSINK-DRAIN",
                  position=pt(ft(12, 0), ft(18, 10.625)), fitting_elevation=inch(94.04),
                  cap_position=pt(ft(12, 0), ft(18, 2)), cap_elevation=inch(98.04),
                  access="wall", wall_ref="W-B-CW2",
                  clear_width=inch(18), clear_depth=inch(18)),
    # FX-B-UTIL-SINK's line is a sink line (707.4): a cleanout tee on the trap arm at the
    # W-B-STR2 face, reached through the tub's cabinet.
    DrainCleanout(uid="NY556FY4H7", tag="CO-B-USINK", pipe_ref="PR-B-USINK-DRAIN",
                  position=pt(inch(117.5), inch(229.5)), fitting_elevation=inch(15.9375),
                  cap_position=pt(inch(115.5), inch(229.5)), cap_elevation=inch(18),
                  access="cabinet", clear_width=inch(18), clear_depth=inch(18)),
    # Buried branches use flush caps in the basement slab, away from their fixture drops.
    # The branch turns 180° at (10'-0", 17'-4 3/4") (S, SW, S, then W), so 707.4 wants a turn
    # cleanout there too; capped flush in the workshop floor 8" west of the corner.
    DrainCleanout(uid="GBM1ZV4EJV", tag="CO-B-BATH-TURN", pipe_ref="PR-B-BATH-DRAIN",
                  position=pt(inch(112), inch(208.75)), fitting_elevation=inch(-10.83),
                  cap_position=pt(inch(112), inch(208.75)), cap_elevation=inch(0),
                  access="floor", clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000006", tag="CO-B-BATH", pipe_ref="PR-B-BATH-DRAIN",
                  position=pt(inch(134), inch(254)), fitting_elevation=inch(-9.5),
                  cap_position=pt(inch(134), inch(254)), cap_elevation=inch(0),
                  access="floor", clear_width=inch(24), clear_depth=inch(24)),
    # Keep the fitting on the branch; its rising access extension now terminates in the
    # open aisle at (181", 60"). An 18" square clears the foot platform and access step.
    DrainCleanout(uid="COB0000007", tag="CO-B-SAUNA-HEAD", pipe_ref="PR-B-SAUNA-DRAIN",
                  position=pt(inch(191.75), inch(108)), fitting_elevation=inch(-8.82),
                  cap_position=pt(inch(181), inch(60)), cap_elevation=inch(0),
                  access="floor", clear_width=inch(18), clear_depth=inch(18)),
    # The shower branch turns north-to-west at the wall and west-to-north at x=3'-4" (180°
    # in aggregate), so 707.4 wants a turn cleanout; capped flush in the workshop floor.
    DrainCleanout(uid="PK92YRMM4A", tag="CO-B-SAUNA-TURN", pipe_ref="PR-B-SAUNA-DRAIN",
                  position=pt(inch(40), inch(121.375)), fitting_elevation=inch(-12.8),
                  cap_position=pt(inch(40), inch(121.375)), cap_elevation=inch(0),
                  access="floor", clear_width=inch(18), clear_depth=inch(18)),
    # WC2's branch runs in the basement ceiling. Its upper terminal is the closet bend's heel;
    # the cleanout is a 45 wye there, its cap 3 1/2" SW and up, off the drop's axis and away
    # from PR-M-BATH2-WC-VENT, just under the furnace-room ceiling. Its turn east into the
    # stack is only 90°, so it carries no turn cleanout.
    DrainCleanout(uid="COB0000011", tag="CO-B-WC2-HEAD", pipe_ref="PR-B-WC2-DRAIN",
                  position=pt(ft(2, 6), inch(252.74)),
                  fitting_elevation=ft(7, 4.4375),
                  cap_position=pt(inch(26.5), inch(249.24)),
                  cap_elevation=inch(95.9375),
                  access="ceiling", clear_width=inch(24), clear_depth=inch(24)),
]


MAIN_CLEANOUTS = [
    DrainCleanout(uid="COM0000001", tag="CO-M-BATH1", pipe_ref="PR-M-S-BATH1-DRAIN",
                  position=pt(ft(5), ft(26, 8)), fitting_elevation=inch(-22),
                  cap_position=pt(ft(5), inch(323.75)), cap_elevation=ft(2),
                  access="wall", wall_ref="W-M-STOS",
                  clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COM0000002", tag="CO-M-SUITE", pipe_ref="PR-M-S-SUITE-DRAIN",
                  position=pt(ft(12, 6), ft(18)), fitting_elevation=inch(-5),
                  cap_position=pt(ft(12, 6), ft(18, 1.75)), cap_elevation=ft(2),
                  access="wall", wall_ref="W-M-CLN",
                  clear_width=inch(24), clear_depth=inch(24)),
    # PR-B-SH2-DRAIN's upper terminal: its 21 1/2" trap arm made the branch 81" of horizontal,
    # past 707.4's 5' exemption. A cleanout tee on the arm 2" short of the vent tee, its
    # extension up W-M-BA2E2's west bay clear of the hot riser and stud-004, capped 12" up
    # behind a panel in RM-M-CLOSET's face (never the shower's).
    DrainCleanout(uid="05QYQYFP72", tag="CO-M-SH2-HEAD", pipe_ref="PR-B-SH2-DRAIN",
                  position=pt(inch(96), inch(180.36)), fitting_elevation=inch(-3.456),
                  cap_position=pt(inch(96), inch(182.4)), cap_elevation=inch(12),
                  access="wall", wall_ref="W-M-BA2E2",
                  clear_width=inch(18), clear_depth=inch(18)),
]
