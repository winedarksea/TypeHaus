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
                  position=pt(ft(9, 4), ft(18, 10.625)), fitting_elevation=inch(91.25),
                  cap_position=pt(ft(9, 4), ft(18, 2)), cap_elevation=inch(95.25),
                  access="wall", wall_ref="W-B-CW3",
                  clear_width=inch(18), clear_depth=inch(18)),
    # FX-B-UTIL-SINK's line is a sink line (707.4): a cleanout tee on the trap arm at the
    # W-B-STR2 face, reached through the tub's cabinet. The cap is 2 1/2" off the fitting so
    # the 2" body (2026-11-10) does not swallow it.
    DrainCleanout(uid="NY556FY4H7", tag="CO-B-USINK", pipe_ref="PR-B-USINK-DRAIN",
                  position=pt(inch(117.5), inch(229.5)), fitting_elevation=inch(15.9375),
                  cap_position=pt(inch(115), inch(229.5)), cap_elevation=inch(18),
                  access="cabinet", clear_width=inch(18), clear_depth=inch(18)),
    # The slab branches' upper terminals are wall panels: the fitting on the buried pipe, its
    # extension up a stud bay, the cap behind a panel. No slab branch turns past 707.4's
    # 135° (mep_drainage.py), so none needs a turn cleanout.
    # The WC branch: a wye 6 1/2" down it, west of W-B-STR2; the extension runs under the
    # slab into the wall's 232"-248" bay, 6" south of the WC vent's riser, cap in the bath face.
    DrainCleanout(uid="COB0000006", tag="CO-B-BATH", pipe_ref="PR-B-BATH-DRAIN",
                  position=pt(inch(116), inch(242)), fitting_elevation=inch(-10.06),
                  cap_position=pt(inch(122), inch(236)), cap_elevation=inch(12),
                  access="wall", wall_ref="W-B-STR2",
                  clear_width=inch(24), clear_depth=inch(24)),
    # The sauna branch: a wye on its 1/8 bend 22" from the drop, under the shower pan; the
    # extension runs under the slab into W-B-SA-N2's cavity, cap in the hall face (never the
    # sauna's).
    DrainCleanout(uid="COB0000007", tag="CO-B-SAUNA-HEAD", pipe_ref="PR-B-SAUNA-DRAIN",
                  position=pt(inch(176.5), inch(113.4375)), fitting_elevation=inch(-9.13),
                  cap_position=pt(inch(176.5), inch(122.5)), cap_elevation=inch(12),
                  access="wall", wall_ref="W-B-SA-N2",
                  clear_width=inch(18), clear_depth=inch(18)),
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
    # PR-B-SH2-DRAIN's upper terminal: its 21.8" trap arm makes the branch >81" of horizontal,
    # past 707.4's 5' exemption. A cleanout tee on the arm 2" short of the vent tee, its
    # extension up W-M-BA2E2's west bay clear of the hot riser and stud-004, capped 12" up
    # behind a panel in RM-M-CLOSET's face (never the shower's).
    DrainCleanout(uid="05QYQYFP72", tag="CO-M-SH2-HEAD", pipe_ref="PR-B-SH2-DRAIN",
                  # On the straight recentered arm; cap remains at the existing service panel.
                  position=pt(inch(96), inch(180.102525)), fitting_elevation=inch(-3.453238),
                  cap_position=pt(inch(96), inch(182.4)), cap_elevation=inch(12),
                  access="wall", wall_ref="W-M-BA2E2",
                  clear_width=inch(18), clear_depth=inch(18)),
]
