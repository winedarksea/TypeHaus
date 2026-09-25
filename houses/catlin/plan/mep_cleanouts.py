# haus: editable
# Catlin sanitary cleanouts, paired with their physical access caps.

from typehaus import DrainCleanout, ft, inch, pt

BASEMENT_CLEANOUTS = [
    # Building drain / sewer connection. Local south grade is -2'-10" project datum.
    DrainCleanout(uid="COB0000001", tag="CO-B-SEWER", pipe_ref="PR-B-MAIN-DRAIN",
                  position=pt(ft(3), ft(-1)), fitting_elevation=inch(-18.6),
                  cap_position=pt(ft(3), ft(-1)), cap_elevation=inch(75.4375),
                  direction="two_way", access="grade",
                  clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000002", tag="CO-B-MAIN-TURN", pipe_ref="PR-B-MAIN-DRAIN",
                  position=pt(ft(3), ft(16, 6)), fitting_elevation=inch(80.6375),
                  cap_position=pt(ft(3), ft(17, 9)), cap_elevation=inch(84.6375),
                  access="wall", wall_ref="W-B-CW",
                  clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000009", tag="CO-B-COLLECTOR", pipe_ref="PR-B-MAIN-DRAIN",
                  position=pt(ft(5, 3), ft(16, 6)), fitting_elevation=inch(81.2375),
                  cap_position=pt(ft(5, 3), ft(17, 9)), cap_elevation=inch(85.2375),
                  direction="two_way", access="wall", wall_ref="W-B-CW",
                  clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000010", tag="CO-B-SLAB-TURN", pipe_ref="PR-B-MAIN-DRAIN",
                  position=pt(ft(3), ft(15, 6)), fitting_elevation=inch(-13.2),
                  cap_position=pt(ft(3), ft(15, 6)), cap_elevation=inch(0),
                  access="floor", clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000003", tag="CO-B-KITCH-HEAD", pipe_ref="PR-B-KITCH-DRAIN",
                  position=pt(ft(29, 4), ft(35)), fitting_elevation=inch(101.9375),
                  cap_position=pt(ft(29, 4), ft(35)), cap_elevation=inch(121.4375),
                  access="cabinet", clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000004", tag="CO-B-KITCH-TURN", pipe_ref="PR-B-KITCH-DRAIN",
                  position=pt(ft(9, 8), ft(35)), fitting_elevation=inch(96.21875),
                  cap_position=pt(ft(9, 10.2), ft(35)), cap_elevation=inch(100.21875),
                  access="wall", wall_ref="W-B-STR",
                  clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000005", tag="CO-B-LSINK", pipe_ref="PR-B-LSINK-DRAIN",
                  position=pt(ft(11, 9), ft(18, 10.625)), fitting_elevation=inch(94.04),
                  cap_position=pt(ft(11, 9), ft(18, 2)), cap_elevation=inch(98.04),
                  access="wall", wall_ref="W-B-CW2",
                  clear_width=inch(18), clear_depth=inch(18)),
    # Buried branches use flush caps in the basement slab, away from their fixture drops.
    DrainCleanout(uid="COB0000006", tag="CO-B-BATH", pipe_ref="PR-B-BATH-DRAIN",
                  position=pt(ft(12), ft(21, 6)), fitting_elevation=inch(-9.258854),
                  cap_position=pt(ft(12), ft(21, 6)), cap_elevation=inch(0),
                  access="floor", clear_width=inch(24), clear_depth=inch(24)),
    DrainCleanout(uid="COB0000007", tag="CO-B-SAUNA-HEAD", pipe_ref="PR-B-SAUNA-DRAIN",
                  position=pt(ft(13, 6), ft(5, 6)), fitting_elevation=inch(-10.1284375),
                  cap_position=pt(ft(13, 6), ft(5, 6)), cap_elevation=inch(0),
                  access="floor", clear_width=inch(18), clear_depth=inch(18)),
    DrainCleanout(uid="COB0000008", tag="CO-B-SAUNA-TURN", pipe_ref="PR-B-SAUNA-DRAIN",
                  position=pt(ft(13, 6), ft(4)), fitting_elevation=inch(-10.58),
                  cap_position=pt(ft(13, 6), ft(4)), cap_elevation=inch(0),
                  access="floor", clear_width=inch(18), clear_depth=inch(18)),
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
