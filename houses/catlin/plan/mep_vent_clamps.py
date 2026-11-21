# haus: editable
# Catlin MEP — the straps holding VR-M-STACK's exterior pair on W-A-N2. Split out of
# plan/mep_venting.py (2026-11-19) to keep that file near AGENTS.md's 500 lines.

from typehaus import Connector, ConnectorKind, ft, inch, pt

# Through-panel straps holding the exterior riser pair on W-A-N2, rewritten 2026-11-15
# (DESIGN-LOG). Each fixes INTO WOOD: the 24'-0" girt course (288"-291 1/2") and the rake
# nailer (bottom 252.03" + x/2 on W-A-N2). 316 stainless two-hole strap: radon #11 (3.5" OD),
# vent "4in" (4.5" OD, its 4" head since 2026-11-19).
#
# * WALL: BBD75 board-and-batten (concealed fastener; 2" battens at x = 12n, 10" flats).
#   Strap and block sit on a flat: vent x 97-107, radon x 109-119. The radon block's east
#   edge stays >= 1" off the x=119" batten, so blocks are <= 5" wide. No seam to clamp, so
#   no S-5! CanDuit ring.
# * BLOCK: laminated cellular PVC (PVC-cemented), 5" off the flat. Pipe centre ~6.75" off
#   the flat on the radon (5.95" off the crowns; fan standoff 5.35", subp. 5.D), ~7.25" on
#   the 4" vent (the model keeps both on one line, y=444.7"). Sealant or butyl at
#   the panel holes under the block, as on the gable box blocks.
# * THROUGH-SCREWS: 316 stainless, 6" (5" block + panel + ~1" into the 1 1/2" KDAT). The
#   tip must stay in the girt: 6 1/2" reaches its back face at the vent gap.
# * LOWER STRAPS: a level block on the 24' course, both through-screws at 289.75". The
#   vent's block runs up to ~295" and its strap sits at 292.5", over the 4" elbow's hub.
# * TOP STRAPS: a RAKED-TOP block on the rake nailer, 5" wide, top cut 6:12 and held 1/4"
#   under the trim hem (254.70" + x/2): vent top 303.70"->306.20", radon 310.95"->313.45".
#   Two through-screws on a line parallel to the rake, 1" over the nailer bottom, 3" apart:
#   vent (99.5, 302.78) and (102.5, 304.28); radon (114, 310.03) and (117, 311.53). The
#   strap screws into the block face at 302.5" / 309.5".
# * RESULT: supports 10" apart on the vent, 19.75" on the radon; 17.3" free above the vent's
#   top strap, 17.6" above the radon's.
# * FITTING: 3" elbow hub top ~288"; the 4" vent elbow's ~289.5", under its lifted strap.
#   Confirm both on the elbows delivered; exit stays 23'-8" (option (a), DESIGN-LOG).
# * WALL PENETRATION and BLOCKS are DERIVED (decision #142, PENETRATION-STANDARD): the
#   WP-VR-M-STACK-* records (6" / 4" sleeves, Dektite #4 / #3 boots) and the MB-CN-* strap
#   blocks (level on the course or raked under the hem), billed in [wall_penetrations].
# * PAINT: both exterior PVC legs, exterior water-based latex (Linen White) per IAPMO IS 9 /
#   Charlotte Pipe UV guidance. Never oil-based.
# * FAN, if ever fitted: in-line on rubber couplings just above the elbow, its bracket on
#   the 24' course in CN-M-RADON-CLAMP1's place (the strap comes off).
VENT_CLAMPS = [
    # The vent leg on 8'-5".
    Connector(uid="CMVC01AAAA", tag="CN-M-VENT-CLAMP1", kind=ConnectorKind.PIPE_STRAP,
              position=pt(inch(101), inch(444.7)), elevation=inch(292.5), size="SS316-STANDOFF-STRAP 4in",
              connects=("VR-M-STACK", "W-A-N2")),
    Connector(uid="CMVC02AAAA", tag="CN-M-VENT-CLAMP2", kind=ConnectorKind.PIPE_STRAP,
              position=pt(inch(101), inch(444.7)), elevation=inch(302.5), size="SS316-STANDOFF-STRAP 4in",
              connects=("VR-M-STACK", "W-A-N2")),
    # The radon leg on 9'-7 1/2".
    Connector(uid="97GJ68XRY2", tag="CN-M-RADON-CLAMP1", kind=ConnectorKind.PIPE_STRAP,
              position=pt(ft(9, 7.5), inch(444.7)), elevation=inch(289.75), size="SS316-STANDOFF-STRAP #11",
              connects=("VR-M-STACK", "W-A-N2")),
    Connector(uid="ZRBRXDKJVF", tag="CN-M-RADON-CLAMP2", kind=ConnectorKind.PIPE_STRAP,
              position=pt(ft(9, 7.5), inch(444.7)), elevation=inch(309.5), size="SS316-STANDOFF-STRAP #11",
              connects=("VR-M-STACK", "W-A-N2")),
]
