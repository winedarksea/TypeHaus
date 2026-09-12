# haus: editable
# Catlin wall backing — the WET-WALL COURSES, split out of plan/backing.py on 2026-09-12.
#
# plan/backing.py ran past AGENTS.md's 500 lines when the one 3/4" plywood band per wet wall
# became three 2x courses: 17 elements went to 50. Split by SUBJECT rather than by storey,
# because these 50 are one decision with one set of constants and the rest of backing.py is
# a dozen unrelated ones. The constants live HERE and only here, so a course height is
# changed in one place.
#
# ** AN EDITABLE FILE CANNOT `from plan import ...` ** — the dialect forbids it — so this
# module imports only from `typehaus` and plan/manifest.py composes, exactly as
# plan/lighting_attic.py does.
#
# `# haus: editable` is REQUIRED: a band is UI-movable, and a WallBacking edited in the
# editor against a file without this marker is silently dropped on write-back.
#
# Elevations are above the storey datum — the same datum `Mount.elevation` and an opening's
# sill use — and the dialect forbids arithmetic, so every one is a literal.
#
# The policy these bands carry, the IRC/CRC reading behind them and why backing is an element
# rather than a `FramingSpec` field are all set out in plan/backing.py's header. Read that
# first.

from typehaus import WallBacking, inch


# --- the wet walls ---------------------------------------------------------------------
#
# THREE 2x COURSES PER WET WALL, not one continuous sheet. Until 2026-09-12 this was a
# single 3/4" Structural 1 plywood band, 48" tall, 32"-80" AFF, on all 17 walls — 86 LF of
# band and ~13 sheets. Every one of those walls puts 5/8" gypsum straight on the studs, so a
# 3/4" sheet either stands proud of the finish plane or is let into the studs; `notes/
# wall_backing.md` claimed the second, which for a 48"-tall band means routing a 3/4" x 48"
# dado across ~65 studs. Nothing draws that and nothing prices it. See DESIGN-LOG.md.
#
# A 2x laid flat and FITTED BETWEEN the studs is what the kitchen bands have always meant by
# "2x8 flat": nothing stands proud, nothing is dadoed, and the framer cuts to the bay.
#
#   course   profile   bottom   top        what it answers
#   -GRAB    2x8       32"      39 1/4"    CRC R328.1.1 verbatim — 2x8 nominal minimum,
#                                          32" to 39 1/4", flush with the framing
#   -MID     2x10      44"      53 1/4"    towel bar (48"), robe hook, slide-bar lower
#                                          bracket, FURN-M-BATH2-CAB's 48" rail
#   -HIGH    2x8       72"      79 1/4"    shower arm (78"), slide-bar upper bracket,
#                                          high hook
#
# ** WHAT THIS GIVES UP, AND IT IS REAL. ** The retired band was continuous 32"-80". The
# courses leave 39 1/4"-44", 53 1/4"-72" and everything above 80 1/4" unbacked. A screw in
# one of those gaps has nothing behind it. The policy has not changed — these are three
# standard anchor heights authored where a screw MIGHT land, not a fit to today's fixtures;
# only one modelled body in the house sits inside the old 48" band at all.
#
# ** WHAT IT GAINS BEYOND THE FLAT WALL. ** A per-bay block can be omitted or shifted at the
# bay a shower valve and its risers occupy. A continuous sheet cannot, and
# `notes/wall_backing.md` flags that overlap as ungraded.
#
# Of the four anchors the old prose named, three — valve body, tub spout, shower arm — are
# the plumber's rough-in blocking, set with the rough-in and not finish backing at all. Only
# the grab bar is this file's business.
#
# `material_ref="spf"` is written on every course on purpose: the field defaults to
# "struct-1-plywood", which is what these used to be.

_GRAB_ELEVATION = inch(32)
_GRAB_HEIGHT = inch(7.25)
_GRAB_PROFILE = "2x8"

_MID_ELEVATION = inch(44)
_MID_HEIGHT = inch(9.25)
_MID_PROFILE = "2x10"

_HIGH_ELEVATION = inch(72)
_HIGH_HEIGHT = inch(7.25)
_HIGH_PROFILE = "2x8"


BASEMENT_WET_BACKING = [
    WallBacking(uid="MCEY2KK7X7", tag="BK-B-BA-E-GRAB", wall_ref="W-B-BA-E",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="E0RDYHMTV9", tag="BK-B-BA-E-MID", wall_ref="W-B-BA-E",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="4N884BQZGN", tag="BK-B-BA-E-HIGH", wall_ref="W-B-BA-E",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
    WallBacking(uid="F2VB4ZSJM3", tag="BK-B-CE-GRAB", wall_ref="W-B-CE",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="5J6MHCSY4H", tag="BK-B-CE-MID", wall_ref="W-B-CE",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="43C3RSDCJ4", tag="BK-B-CE-HIGH", wall_ref="W-B-CE",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
    WallBacking(uid="MVECH5GPSX", tag="BK-B-CW-GRAB", wall_ref="W-B-CW",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="YZSVNJAR9W", tag="BK-B-CW-MID", wall_ref="W-B-CW",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="EGDJSBN6MM", tag="BK-B-CW-HIGH", wall_ref="W-B-CW",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
    WallBacking(uid="RVQ4CEHMJ6", tag="BK-B-CW3-GRAB", wall_ref="W-B-CW3",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="CZY4YFAVJM", tag="BK-B-CW3-MID", wall_ref="W-B-CW3",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="GY22PQ90JJ", tag="BK-B-CW3-HIGH", wall_ref="W-B-CW3",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
    WallBacking(uid="DQFXW82JCN", tag="BK-B-HALL-W-GRAB", wall_ref="W-B-HALL-W",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="JE8PNZ9WWZ", tag="BK-B-HALL-W-MID", wall_ref="W-B-HALL-W",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="02MYNPVVSX", tag="BK-B-HALL-W-HIGH", wall_ref="W-B-HALL-W",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
]


MAIN_WET_BACKING = [
    WallBacking(uid="63Q2NFMTRY", tag="BK-M-BA2E-GRAB", wall_ref="W-M-BA2E",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="SWV98C74SJ", tag="BK-M-BA2E-MID", wall_ref="W-M-BA2E",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="A3GNDJP246", tag="BK-M-BA2E-HIGH", wall_ref="W-M-BA2E",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
    WallBacking(uid="NGSM5DJCT1", tag="BK-M-BA2E2-GRAB", wall_ref="W-M-BA2E2",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="HXM80EJD0W", tag="BK-M-BA2E2-MID", wall_ref="W-M-BA2E2",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="QMZNJ07GJR", tag="BK-M-BA2E2-HIGH", wall_ref="W-M-BA2E2",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
    WallBacking(uid="9123HCR34E", tag="BK-M-BAE-GRAB", wall_ref="W-M-BAE",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="G1A06PS22V", tag="BK-M-BAE-MID", wall_ref="W-M-BAE",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="T53RCH1XMR", tag="BK-M-BAE-HIGH", wall_ref="W-M-BAE",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
    WallBacking(uid="QN93C99PCJ", tag="BK-M-HS1-GRAB", wall_ref="W-M-HS1",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="RNKWND9P9B", tag="BK-M-HS1-MID", wall_ref="W-M-HS1",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, over-toilet cabinet rail"),
    WallBacking(uid="82SRRT7F5Z", tag="BK-M-HS1-HIGH", wall_ref="W-M-HS1",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
    WallBacking(uid="548DDSJFJ4", tag="BK-M-HS2-GRAB", wall_ref="W-M-HS2",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="A4N3R0722B", tag="BK-M-HS2-MID", wall_ref="W-M-HS2",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="8PSM00TZN8", tag="BK-M-HS2-HIGH", wall_ref="W-M-HS2",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
]


SECOND_WET_BACKING = [
    WallBacking(uid="DA0BDATHZ7", tag="BK-S-BA-E-GRAB", wall_ref="W-S-BA-E",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="PXYFEKYE5P", tag="BK-S-BA-E-MID", wall_ref="W-S-BA-E",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="XNX4ZNASE0", tag="BK-S-BA-E-HIGH", wall_ref="W-S-BA-E",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
    WallBacking(uid="7114P8MNBY", tag="BK-S-BA-E1B-GRAB", wall_ref="W-S-BA-E1B",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="V4E88WNW8H", tag="BK-S-BA-E1B-MID", wall_ref="W-S-BA-E1B",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="AMXZGKHZZB", tag="BK-S-BA-E1B-HIGH", wall_ref="W-S-BA-E1B",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
    WallBacking(uid="NJJYT7QAMA", tag="BK-S-BD-N-GRAB", wall_ref="W-S-BD-N",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="0BHT64WFKQ", tag="BK-S-BD-N-MID", wall_ref="W-S-BD-N",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="HZ7NZAV31W", tag="BK-S-BD-N-HIGH", wall_ref="W-S-BD-N",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
    WallBacking(uid="KFWVA9EPGE", tag="BK-S-BD-N1B-GRAB", wall_ref="W-S-BD-N1B",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="3B0HK4NCQ4", tag="BK-S-BD-N1B-MID", wall_ref="W-S-BD-N1B",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="4XAJW4Q841", tag="BK-S-BD-N1B-HIGH", wall_ref="W-S-BD-N1B",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
    WallBacking(uid="D9754TGGC7", tag="BK-S-DC2-GRAB", wall_ref="W-S-DC2",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="P6AZAAYF1S", tag="BK-S-DC2-MID", wall_ref="W-S-DC2",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="22EBX0QVT1", tag="BK-S-DC2-HIGH", wall_ref="W-S-DC2",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
    WallBacking(uid="YQESA1JG5K", tag="BK-S-SN3-GRAB", wall_ref="W-S-SN3",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="KHQD8PAMQT", tag="BK-S-SN3-MID", wall_ref="W-S-SN3",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall mid course: towel bar, robe hook, slide-bar lower bracket"),
    WallBacking(uid="8Y7R1WNS1Q", tag="BK-S-SN3-HIGH", wall_ref="W-S-SN3",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="wet wall high course: shower arm, slide-bar upper bracket, high hook"),
]


ATTIC_WET_BACKING = [
    # W-A-STU-W is the one short wet wall, and it is short twice over, so it gets the GRAB
    # and MID courses and NOT the HIGH one. Its plate is at 72 3/4", so a course at 72"
    # has no stud left to land on and `backing_panels.py` would drop it in silence. The
    # binding limit is lower still: `CARF01AAAA:rafter-020` rakes down across this knee wall
    # and passes 60 7/8" above its floor, which nothing in the framing solver knows about —
    # `top_at` reads the wall's own plate, not the roof over it, so a 64" band resolved
    # happily and `structural.member_interference` caught it. -MID tops at 53 1/4" and
    # clears that rafter by 7 5/8"; between them the two courses are the whole range a
    # knee-wall bar sink's valve and towel ring can physically use. (This replaces the
    # 0.75x24.0 plywood band that stood here until 2026-09-12.)
    WallBacking(uid="GCV1Y8MJ5J", tag="BK-A-STU-W-GRAB", wall_ref="W-A-STU-W",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="wet wall (short) grab-bar course (CRC R328.1.1)"),
    WallBacking(uid="JPJMNET0MD", tag="BK-A-STU-W-MID", wall_ref="W-A-STU-W",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="wet wall (short) mid course: bar sink valve and towel ring"),
]
