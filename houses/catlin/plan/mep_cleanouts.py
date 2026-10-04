# haus: editable
# Catlin sanitary cleanouts, paired with their physical access caps.

from typehaus import DrainCleanout, ft, inch, pt

BASEMENT_CLEANOUTS = [
    # The building drain's cleanout at the sewer connection (UPC 719.1), INSIDE the wall:
    # a two-way fitting 3'-0" short of FT-B-N4, capped flush in RM-B-FURNACE's floor beside
    # SM-B-RADON. Two-way inside the wall is also 707.4 exception 4, so it stands in for an
    # upper-terminal cleanout at the collector's head. It was a 94" riser to grade in the
    # rear yard while the sewer left south.
    DrainCleanout(uid="COB0000001", tag="CO-B-SEWER", pipe_ref="PR-B-MAIN-DRAIN",
                  position=pt(ft(3), ft(34)), fitting_elevation=inch(-19.375),
                  cap_position=pt(ft(3), ft(34)), cap_elevation=inch(0),
                  direction="two_way", access="floor",
                  clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000009", tag="CO-B-COLLECTOR", pipe_ref="PR-B-MAIN-DRAIN",
                  position=pt(ft(5, 3), ft(16, 6)), fitting_elevation=inch(81.2375),
                  cap_position=pt(ft(5, 3), ft(17, 9)), cap_elevation=inch(85.2375),
                  direction="two_way", access="wall", wall_ref="W-B-CW",
                  clear_width=inch(24), clear_depth=inch(24)),
    # PR-B-BATH-DRAIN turns south, then west, and the main carries it north: 180° in
    # aggregate at its tie, 4 3/4" downstream. Two-way, between the stack's base and that tie,
    # capped flush in the workshop floor.
    DrainCleanout(uid="COB0000010", tag="CO-B-STACK-BASE", pipe_ref="PR-B-MAIN-DRAIN",
                  position=pt(ft(3), ft(17)), fitting_elevation=inch(-15.125),
                  cap_position=pt(ft(3), ft(17)), cap_elevation=inch(0),
                  direction="two_way", access="floor",
                  clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000003", tag="CO-B-KITCH-HEAD", pipe_ref="PR-B-KITCH-DRAIN",
                  position=pt(inch(352), inch(416.875)), fitting_elevation=inch(101.9375),
                  cap_position=pt(inch(352), inch(416.875)), cap_elevation=inch(121.4375),
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
    # Buried branches use flush caps in the basement slab, away from their fixture drops.
    DrainCleanout(uid="COB0000006", tag="CO-B-BATH", pipe_ref="PR-B-BATH-DRAIN",
                  position=pt(ft(12), ft(21, 6)), fitting_elevation=inch(-9.258854),
                  cap_position=pt(ft(12), ft(21, 6)), cap_elevation=inch(0),
                  access="floor", clear_width=inch(24), clear_depth=inch(24)),
    # On the sauna branch's west leg, 4" south of FURN-B-SAUNA-BENCH-E's front.
    DrainCleanout(uid="COB0000007", tag="CO-B-SAUNA-HEAD", pipe_ref="PR-B-SAUNA-DRAIN",
                  position=pt(ft(13), ft(5, 10.2)), fitting_elevation=inch(-9.58),
                  cap_position=pt(ft(13), ft(5, 10.2)), cap_elevation=inch(0),
                  access="floor", clear_width=inch(18), clear_depth=inch(18)),
    # WC2's branch runs in the basement ceiling. Its upper terminal is below the fixture;
    # the cap needs an access panel. Its turn east into the stack is only 90° now that the
    # collector drops at that corner, so it carries no turn cleanout.
    DrainCleanout(uid="COB0000011", tag="CO-B-WC2-HEAD", pipe_ref="PR-B-WC2-DRAIN",
                  position=pt(ft(2, 6), ft(20, 10.615)),
                  fitting_elevation=ft(7, 4.4375),
                  cap_position=pt(ft(2, 6), ft(20, 10.615)),
                  cap_elevation=ft(8, 0.9375),
                  access="ceiling", clear_width=inch(24), clear_depth=inch(24)),
]


MAIN_CLEANOUTS = [
    DrainCleanout(uid="COM0000001", tag="CO-M-BATH1", pipe_ref="PR-M-S-BATH1-DRAIN",
                  position=pt(ft(5), ft(26, 6)), fitting_elevation=inch(-22),
                  cap_position=pt(ft(5), ft(26, 7.75)), cap_elevation=ft(2),
                  access="wall", wall_ref="W-M-STOS",
                  clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COM0000002", tag="CO-M-SUITE", pipe_ref="PR-M-S-SUITE-DRAIN",
                  position=pt(ft(12, 6), ft(18)), fitting_elevation=inch(-5),
                  cap_position=pt(ft(12, 6), ft(18, 1.75)), cap_elevation=ft(2),
                  access="wall", wall_ref="W-M-CLN",
                  clear_width=inch(24), clear_depth=inch(24)),
]
