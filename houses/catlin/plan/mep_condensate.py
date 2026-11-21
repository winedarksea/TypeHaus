# haus: editable
# Catlin MEP — heat-pump condensate to the nearest utility sink (owner, 2026-11-11).
#
# Every line is 3/4" PVC, `sanitary=False`, falling at least 1/4"/ft (IMC 307.2.1 asks 1/8) to
# an air gap over a receptor that sees water in normal use. The south heads keep the sauna
# floor drain (plan/mep_drainage.py's PR-M-COND-HEADS / PR-B-COND), which their water keeps
# primed. The two north units go to FX-B-UTIL-SINK in the furnace room, beside the ERV and
# water-heater lines: the laundry sink's rim is level with HP3's drain, and one receptor in
# the room where exposed pipe is accepted beats a spout in the laundry. Hoses inside a head's
# own body are drawn as its first leg. The AH's feeder, union, trap, capped cleanout and
# downstream vent are installation parts on its equipment type; PR-A-COND-HP1 starts at the
# outlet tee, east of the service zone. Its emergency pan uses float shutdown, no second line.

from typehaus import (
    PipeRun,
    PipeSystem,
    inch,
    pt,
)

# Filed on `main` (datum 0'-0"), like SECOND_DRAINS, so every elevation is absolute.
CONDENSATE_NORTH = [
    # EQ-M-HP3-STAIR (re-routed 2026-11-18 out of W-M-STRW, whose mudroom bays are open: a
    # bored stud shows; its pan_drain_ref names this run). The hose leaves the head's east end
    # at 37" (inside the body), bores the mounting plate's 2x8 backing into W-M-N2's cavity,
    # drops to 26 1/2" and runs east, then south down W-M-C5B/C5 under
    # PR-M-CW-COLDSTORE-STUB's 30" leg. It drops mid-plate in C5's south bay into FS-M-NE's
    # bearing box, east out of it and south in the truss bay over CD-B-PLAY-SPARE, back west
    # across the box at y=25'-2 3/4", south to y=25'-0" and west along the FS-M-STAIR/MECH
    # bay, boring W-B-BA-N's nailers and 1" under PR-B-BATH-WC-CW. The riser's hole leaves
    # the box a cheek under W-M-C5's end stud (BM-M-HALL's bearing); a run along the box
    # would strip both cheeks. Since the ERV moved to the sink (2026-11-21) it drops into the
    # furnace room at x=9'-3", between DU-B-ERV-R-GYM's and -PLAY's lanes, runs south to
    # y=23'-11 3/8" (north of DU-B-ERV-R-BATH), drops again past the ERV's service gap and
    # runs south to the sink, turning east over its bowl.
    PipeRun(uid="XM4GM4VEZS", tag="PR-M-COND-HP3", system=PipeSystem.DRAIN, sanitary=False,
            path=(pt(inch(158), inch(418)), pt(inch(158), inch(428.75)),
                  pt(inch(158), inch(428.75)), pt(inch(216), inch(428.75)),
                  pt(inch(216), inch(312.9)), pt(inch(216), inch(312.9)),
                  pt(inch(223), inch(312.9)), pt(inch(223), inch(302.75)),
                  pt(inch(214), inch(302.75)), pt(inch(214), inch(300)),
                  pt(inch(111), inch(300)), pt(inch(111), inch(300)),
                  pt(inch(111), inch(287.4)), pt(inch(111), inch(287.4)),
                  pt(inch(111), inch(240)), pt(inch(111), inch(240)),
                  pt(inch(114), inch(240))),
            diameter=inch(0.75), material="pvc",
            elevations=(inch(37.5), inch(37.25), inch(26.5), inch(25.05), inch(22.15), inch(-4.5),
                        inch(-4.7), inch(-5), inch(-5.25), inch(-5.33), inch(-10), inch(-21.5),
                        inch(-21.8), inch(-58), inch(-59.2), inch(-62), inch(-62.1))),
    # EQ-S-HP1-AH: from the modeled trap outlet east of the cabinet and service zone,
    # south on the deck at x=24'-11 1/2" (blocked
    # off the deck at 4' o.c.), down into FS-ATTIC's free y 208-224 bay, west along it over
    # the x=18' bearing, then down W-S-DC2's plumbing cavity beside PR-A-STUBATH-DRAIN and
    # W-M-CLN (the laundry's south wall, 3 1/2" east of the sink's hot stop), west in
    # FS-M-WEST's bay past the laundry sink's drop and PR-B-CW-WASH, out into the furnace
    # room, and over the sink's bowl 13" up.
    PipeRun(uid="31MM8G5WV4", tag="PR-A-COND-HP1", system=PipeSystem.DRAIN, sanitary=False,
            path=(pt(inch(299.5), inch(323.052084)), pt(inch(299.5), inch(216)),
                  pt(inch(299.5), inch(216)), pt(inch(117.5), inch(216)),
                  pt(inch(117.5), inch(218)), pt(inch(117.5), inch(218)),
                  pt(inch(117.5), inch(221.5)), pt(inch(97.5), inch(221.5)),
                  pt(inch(97.5), inch(221.5)), pt(inch(97.5), inch(232)),
                  pt(inch(97.5), inch(232)), pt(inch(103.5), inch(232))),
            diameter=inch(0.75), material="pvc",
            elevations=(inch(246.775987), inch(244.545735), inch(236),
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
