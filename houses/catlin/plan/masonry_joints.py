# haus: editable
# Catlin masonry movement joints — the soft ends of W-B-BRICK (owner, A6, 2026-09-22).
#
# The wythe stands between two rigid concrete returns, W-SG-E1 (x 318") and W-SG-W1
# (x 114"), and brick grows irreversibly while concrete shrinks: restrained, a long wythe
# cracks. Each end gets a seal over compressible filler, graded by
# `structural.masonry_movement_joint` against BIA TN 18A Eq. 1 and billed in [edge_trim].
# notes/sunken_garden_veneer_beam.md §6g/§6k work both by hand.
#
# Each path spans the joint WIDTH across the gap in plan, half the seal depth in from the
# brick's resolved south face (y -9.625"); `depth` is the wythe's full height (-102 7/16" to -13 1/3").
# Move N-B-BRICK-E/-W and these go stale — the check measures the gap and says so.
#
# ** BOTH 1/2" SINCE 2026-11-04 (owner). ** The west end was a 4" Emseal precompressed seal;
# the brick now runs to 1/2" off each wall. Spec'd by class, not brand: Class 50 is the
# compression_pct the check reads; a general-purpose Class 25 silicone halves it (d/c ~0.74,
# ~1.46 if one joint takes the whole run), and acetoxy cure is not for alkaline masonry.
# Tooled 1/4" deep (TN 18A's minimum) over 5/8" closed-cell rod, ~25% over the joint width.

from typehaus import MovementJoint, inch, pt

JOINTS = [
    MovementJoint(uid="8C4QVJG0H7", tag="MJ-B-BRICK-E",
                  path=(pt(inch(317.5), inch(-9.5)),
                        pt(inch(318), inch(-9.5))),
                  top_elevation=inch(-13.333), depth=inch(89.104), thickness=inch(0.25),
                  material="neutral-cure low-modulus silicone, ASTM C920 Type S Grade NS Class 50 or better, brick-matched",
                  host_ref="W-B-BRICK", abuts="W-SG-E1", compression_pct=50.0,
                  backer="5/8\" closed-cell backer rod (ASTM C1330 Type C)",
                  source="ASTM C920 Type S Grade NS Class 50+ (e.g. DOWSIL 790/795, GE SilPruf SCS2000, Pecora 890NST, as equals); backer ASTM C1330 Type C"),
    MovementJoint(uid="H1GWTPAS9B", tag="MJ-B-BRICK-W",
                  path=(pt(inch(114), inch(-9.5)),
                        pt(inch(114.5), inch(-9.5))),
                  top_elevation=inch(-13.333), depth=inch(89.104), thickness=inch(0.25),
                  material="neutral-cure low-modulus silicone, ASTM C920 Type S Grade NS Class 50 or better, brick-matched",
                  host_ref="W-B-BRICK", abuts="W-SG-W1", compression_pct=50.0,
                  backer="5/8\" closed-cell backer rod (ASTM C1330 Type C)",
                  source="ASTM C920 Type S Grade NS Class 50+ (e.g. DOWSIL 790/795, GE SilPruf SCS2000, Pecora 890NST, as equals); backer ASTM C1330 Type C"),
]
