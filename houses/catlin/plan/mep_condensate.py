# haus: editable
# Catlin MEP — heat-pump condensate to the nearest utility sink (owner, 2026-11-11).
#
# Every line is 3/4" PVC, `sanitary=False`, falling at least 1/4"/ft (IMC 307.2.1 asks 1/8) to
# an air gap over a receptor that sees water in normal use. The south heads keep the sauna
# floor drain (plan/mep_drainage.py's PR-M-COND-HEADS / PR-B-COND), which their water keeps
# primed. The two north units go to FX-B-UTIL-SINK in the furnace room, beside the ERV and
# water-heater lines: the laundry sink's rim is level with HP3's drain, and one receptor in
# the room where exposed pipe is accepted beats a spout in the laundry. Hoses inside a head's
# own body are drawn as its first leg; the AH's trap (Gree IOM) sits at the second vertex,
# off the front of SL-A-HP1-PLATFORM, and is not drawn. Its emergency pan takes a float switch,
# not a second line. EQ-B-HP2-GYM falls inside the sauna's walls onto PR-B-COND's drop (below).

from typehaus import (
    PipeRun,
    PipeSystem,
    inch,
    pt,
)

# Filed on `main` (datum 0'-0"), like SECOND_DRAINS, so every elevation is absolute.
CONDENSATE_NORTH = [
    # EQ-M-HP3-STAIR: the hose leaves the head's west end into W-M-STRW's 2x6 cavity and
    # falls south inside it to y=29'-3" (RM-B-ESS's rated closet fills the furnace room's NE
    # corner, y >= 31'-2 3/8", and DU-B-ERV-R-PLAY crosses at y=30'-4 5/8"). Down through the
    # plates into FS-M-MECH's y 342-356 bay between the two conduits, west across the x=10'
    # bearing, out under the joists, and south along x=8'-2 1/2", the one free lane west of
    # PR-B-HW-SBATH, under DU-B-ERV-R-BATH and PR-B-HW-SBATH's y=25'-3" leg (6'-10" AFF), to
    # the sink, turning east over its bowl beside the ERV and WH outlets.
    PipeRun(uid="XM4GM4VEZS", tag="PR-M-COND-HP3", system=PipeSystem.DRAIN, sanitary=False,
            path=(pt(inch(126.5), inch(418)), pt(inch(120), inch(418)),
                  pt(inch(120), inch(351)), pt(inch(120), inch(351)),
                  pt(inch(98.5), inch(351)), pt(inch(98.5), inch(351)),
                  pt(inch(98.5), inch(303)), pt(inch(98.5), inch(238)),
                  pt(inch(98.5), inch(238)), pt(inch(103.5), inch(238))),
            diameter=inch(0.75), material="pvc",
            elevations=(inch(37), inch(36.8), inch(35.4), inch(-6), inch(-6.45), inch(-23),
                        inch(-26), inch(-27.4), inch(-62), inch(-62.12))),
    # EQ-S-HP1-AH: from the primary port south off the platform (the trap), east past the
    # cabinet's end clear of the service zone, south on the deck at x=24'-11 1/2" (blocked
    # off the deck at 4' o.c.), down into FS-ATTIC's free y 208-224 bay, west along it over
    # the x=18' bearing, then down W-S-DC2's plumbing cavity beside PR-A-STUBATH-DRAIN and
    # W-M-CLN (the laundry's south wall, 3 1/2" east of the sink's hot stop), west in
    # FS-M-WEST's bay past the laundry sink's drop and PR-B-CW-WASH, out into the furnace
    # room, and over the sink's bowl 13" up.
    PipeRun(uid="31MM8G5WV4", tag="PR-A-COND-HP1", system=PipeSystem.DRAIN, sanitary=False,
            path=(pt(inch(288.25), inch(328.5625)), pt(inch(288.25), inch(324.5)),
                  pt(inch(299.5), inch(324.5)), pt(inch(299.5), inch(216)),
                  pt(inch(299.5), inch(216)), pt(inch(117.5), inch(216)),
                  pt(inch(117.5), inch(218)), pt(inch(117.5), inch(218)),
                  pt(inch(117.5), inch(221.5)), pt(inch(97.5), inch(221.5)),
                  pt(inch(97.5), inch(221.5)), pt(inch(97.5), inch(232)),
                  pt(inch(97.5), inch(232)), pt(inch(103.5), inch(232))),
            diameter=inch(0.75), material="pvc",
            elevations=(inch(246), inch(245.9), inch(245.6), inch(243.32), inch(236),
                        inch(232.2), inch(232.15), inch(-6), inch(-6.08), inch(-6.5),
                        inch(-14), inch(-14.22), inch(-62), inch(-62.13))),
    # EQ-B-HP2-GYM (basement storey, filed here at the main datum so elevations are absolute;
    # rel = abs + 109 7/16"). GRAVITY (owner, 2026-11-14). The sauna's ceiling void is out of
    # reach: its floor (the foil, 87 5/16" rel) stands above any drain a head under the gym's
    # 96 15/16" gypsum can have. So the hose leaves the head's north end at 83 1/4" rel and
    # runs 28" north on the gym face over D-B-SAUNA (clipped 3/4" off the board, bottom at the
    # RO head, 1" over the leaf), into W-B-CS's stud core (x=18'-0") in the bay past the
    # door's king, north through its studs to the sauna's north wall, west in W-B-SA-N2/-N's
    # 2x4 cores (y=10'-1 7/16") and tees onto PR-B-COND's drop at x=13'-6", 79 7/8" rel, 7 7/8"
    # under the drop's head; the drop's 9" air gap over FX-B-SAUNA-FD is its receptor.
    # 135 15/16" (11.3 ft) at 0.3"/ft, no rise. Stud bores 1 1/4": 23% of a 2x6, 36% of a 2x4.
    PipeRun(uid="1TFJSE4NC5", tag="PR-B-COND-HP2-GYM", system=PipeSystem.DRAIN, sanitary=False,
            path=(pt(inch(220.5), inch(44)), pt(inch(220.5), inch(72)), pt(inch(216), inch(72)),
                  pt(inch(216), inch(121.4375)), pt(inch(162), inch(121.4375))),
            diameter=inch(0.75), material="pvc",
            elevations=(inch(-26.1875), inch(-26.8875), inch(-27.0), inch(-28.2359375),
                        inch(-29.5859375)),
            slope_in_per_ft=0.3),
]
