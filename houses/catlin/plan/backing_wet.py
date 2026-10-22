# haus: editable
# Catlin wall backing — the BATH courses: a grab-bar course where a tub, shower or WC stands,
# plus the bath mirrors, cabinets and vanities that hang on the same walls. Split out of
# plan/backing.py on 2026-09-12; trimmed to designated bodies on 2026-10-10 (DESIGN-LOG.md).
#
# ** AN EDITABLE FILE CANNOT `from plan import ...` ** — the dialect forbids it — so this
# module imports only from `typehaus` and plan/manifest.py composes, exactly as
# plan/lighting_attic.py does.
#
# `# haus: editable` is REQUIRED: a band is UI-movable, and a WallBacking edited in the
# editor against a file without this marker is silently dropped on write-back.
#
# Elevations are above the storey datum — the same datum `Mount.elevation` and an opening's
# sill use — and the dialect forbids arithmetic, so every one is a literal. The policy is in
# plan/backing.py's header.
#
# A 2x laid flat and FITTED BETWEEN the studs: nothing stands proud, nothing is dadoed, and
# the framer cuts to the bay. Three standard heights, kept as constants:
#
#   course   profile   bottom   top        what it backs
#   -GRAB    2x8       32"      39 1/4"    CRC R328.1.1 verbatim — 2x8 nominal minimum,
#                                          32" to 39 1/4", flush with the framing
#   -MID     2x10      44"      53 1/4"    mirror bottom cleats, FURN-M-BATH2-CAB's 48" rail
#   -HIGH    2x8       72"      79 1/4"    mirror top cleats, closet wire clips at 80"
#
# ** A GRAB COURSE STANDS ONLY WHERE A TUB, SHOWER OR WC DOES, read off geometry** (the wall
# the body's footprint is against), never off `Fixture.wall_ref`, which names the wet wall a
# fixture plumbs into. Three walls that carried one never had a fixture in front:
# W-M-BAE (both main-floor WCs back onto W-M-HS1), W-S-BA-E1B (a vanity), and W-S-BD-N, whose
# GRAB course now backs the two vanity top rails — FX-S-BATH1-SH stands on W-S-N3 instead.
# Fixtures with NO grab course today, for the record: FX-S-BATH1-SH (W-S-N3/W-S-CH-W),
# FX-S-SUITEBATH-TUBSH's back wall (W-S-C2C), FX-S-BATH1-WC (W-S-W1), FX-B-BATH-WC
# (W-B-BA-N), FX-B-SAUNA-SH and FX-A-STUBATH-SH.
#
# A per-bay block can be omitted or shifted at the bay a shower valve and its risers occupy;
# valve body, tub spout and shower arm are the plumber's rough-in blocking, not this file's.
#
# `material_ref="spf"` is written on every course on purpose: the field defaults to
# "struct-1-plywood", which is what these used to be.

from typehaus import WallBacking, inch


_GRAB_ELEVATION = inch(32)
_GRAB_HEIGHT = inch(7.25)
_GRAB_PROFILE = "2x8"

_MID_ELEVATION = inch(44)
_MID_HEIGHT = inch(9.25)
_MID_PROFILE = "2x10"

_HIGH_ELEVATION = inch(72)
_HIGH_HEIGHT = inch(7.25)
_HIGH_PROFILE = "2x8"


MAIN_WET_BACKING = [
    # The drop-in bath's long side is on W-M-BA2E; the shower's back is on W-M-BA2E2, which
    # also carries the closet's SuperSlide west leg on its other face.
    WallBacking(uid="63Q2NFMTRY", tag="BK-M-BA2E-GRAB", wall_ref="W-M-BA2E",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="FX-M-BATH2-TUB grab bar (CRC R328.1.1)"),
    WallBacking(uid="NGSM5DJCT1", tag="BK-M-BA2E2-GRAB", wall_ref="W-M-BA2E2",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="FX-M-BATH2-SH grab bar (CRC R328.1.1); closet wire west-leg lower clips (40 in.)"),
    WallBacking(uid="QMZNJ07GJR", tag="BK-M-BA2E2-HIGH", wall_ref="W-M-BA2E2",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="closet wire west-leg upper clips (80 in.)"),
    # Both WCs back onto W-M-HS1, one per face; the bath's tub end and FX-M-BATH1-LAV are on it
    # too, so the course runs the wall.
    WallBacking(uid="QN93C99PCJ", tag="BK-M-HS1-GRAB", wall_ref="W-M-HS1",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="FX-M-BATH1-WC and FX-M-BATH2-WC grab bars (CRC R328.1.1), FX-M-BATH2-TUB end"),
    WallBacking(uid="RNKWND9P9B", tag="BK-M-HS1-MID", wall_ref="W-M-HS1",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="FURN-M-BATH2-CAB bottom rail (48 in.)"),
    WallBacking(uid="82SRRT7F5Z", tag="BK-M-HS1-HIGH", wall_ref="W-M-HS1",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="FURN-M-BATH2-CAB upper fastening"),
    WallBacking(uid="XVMRGW2TW9", tag="BK-M-STOS-BASIN", wall_ref="W-M-STOS", face="right",
                elevation=inch(29.5), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="Vero wall-basin mounting bolts, 36 in. rim"),
    WallBacking(uid="V6XB1CWBFD", tag="BK-M-STOS-MIRROR", wall_ref="W-M-STOS", face="right",
                elevation=inch(72), height=inch(7.25), profile="2x8",
                material_ref="spf", purpose="ED-M-BATH1-MIRROR fastening"),
    # The halo mirror on W-M-W3 (2026-10-12): 24" wide, centred y=14'-5 3/8", 42"-78", so
    # the two stud bays between the 76" and 108" studs (W-M-W3 runs south from y=22'-4").
    WallBacking(uid="WKTYSGFTJZ", tag="BK-M-W3-MID", wall_ref="W-M-W3",
                start=inch(76.75), length=inch(30.5),
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="ED-M-BATH2-MIRROR-HALO bottom cleats"),
    WallBacking(uid="QCFR9MSFJR", tag="BK-M-W3-HIGH", wall_ref="W-M-W3",
                start=inch(76.75), length=inch(30.5),
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="ED-M-BATH2-MIRROR-HALO top cleats; ED-M-BATH2-MIRROR"),
]


SECOND_WET_BACKING = [
    WallBacking(uid="V4E88WNW8H", tag="BK-S-BA-E1B-MID", wall_ref="W-S-BA-E1B",
                start=inch(0), length=inch(47.25),
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="ED-S-BATH1-MIRROR, the 30 in. Robern round (42-72 in.)"),
    WallBacking(uid="NJJYT7QAMA", tag="BK-S-BD-N-GRAB", wall_ref="W-S-BD-N",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="FX-S-VANITY-LAV1/LAV2 cabinet top rails"),
    WallBacking(uid="0BHT64WFKQ", tag="BK-S-BD-N-MID", wall_ref="W-S-BD-N",
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="ED-S-VANITY-MIRROR1/2 bottom cleats"),
    WallBacking(uid="HZ7NZAV31W", tag="BK-S-BD-N-HIGH", wall_ref="W-S-BD-N",
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="ED-S-VANITY-MIRROR1/2 top cleats"),
    # The WC's back and the tub-shower's end are 40" apart on W-S-SN3; one run takes both.
    WallBacking(uid="YQESA1JG5K", tag="BK-S-SN3-GRAB", wall_ref="W-S-SN3",
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="FX-S-SUITEBATH-WC grab bar (CRC R328.1.1), FX-S-SUITEBATH-TUBSH end"),
    WallBacking(uid="KHQD8PAMQT", tag="BK-S-SN3-MID", wall_ref="W-S-SN3",
                start=inch(40.75), length=inch(22.5),
                elevation=_MID_ELEVATION, height=_MID_HEIGHT,
                profile=_MID_PROFILE, material_ref="spf",
                purpose="FURN-S-SUITEBATH-MIRROR bottom (46 in.)"),
    WallBacking(uid="8Y7R1WNS1Q", tag="BK-S-SN3-HIGH", wall_ref="W-S-SN3",
                start=inch(40.75), length=inch(22.5),
                elevation=_HIGH_ELEVATION, height=_HIGH_HEIGHT,
                profile=_HIGH_PROFILE, material_ref="spf",
                purpose="FURN-S-SUITEBATH-MIRROR top hang (74 in.)"),
]


ATTIC_WET_BACKING = [
    # W-A-STU-W's plate is at 72 3/4" and `CARF01AAAA:rafter-020` rakes across it 60 7/8"
    # above its floor, so a course here stays low; the WC's own bay is all it needs.
    WallBacking(uid="GCV1Y8MJ5J", tag="BK-A-STU-W-GRAB", wall_ref="W-A-STU-W",
                start=inch(16.75), length=inch(14.5),
                elevation=_GRAB_ELEVATION, height=_GRAB_HEIGHT,
                profile=_GRAB_PROFILE, material_ref="spf",
                purpose="FX-A-STUBATH-WC grab bar (CRC R328.1.1)"),
]
