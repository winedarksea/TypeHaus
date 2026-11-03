# haus: editable
# Catlin masonry movement joints — the soft ends of W-B-BRICK (owner, A6, 2026-09-22).
#
# The wythe stands between two rigid concrete returns, W-SG-E1 (x 330") and W-SG-W1
# (x 102"), and brick grows irreversibly while concrete shrinks: restrained, a long wythe
# cracks. Each end gets a seal over compressible filler, graded by
# `structural.masonry_movement_joint` against BIA TN 18A Eq. 1 and billed in [edge_trim].
# notes/sunken_garden_veneer_beam.md §6g works both by hand.
#
# Each path spans the joint WIDTH across the gap in plan, half the seal depth in from the
# brick's resolved south face (y -13.685"); `depth` is the wythe's full height (-102 7/16" to -8").
# Move N-B-BRICK-E/-W and these go stale — the check measures the gap and says so.

from typehaus import MovementJoint, inch, pt

JOINTS = [
    # EAST, 3/8": the mortar-joint width TN 18A calls typical. Spec'd by class, not brand:
    # Class 50 is the compression_pct the check reads; a general-purpose Class 25 silicone
    # halves it, and acetoxy cure is not for alkaline masonry. Tooled 1/4" deep (TN 18A's
    # minimum) over 1/2" closed-cell rod, ~25% over the joint width as TN 18A asks.
    MovementJoint(uid="8C4QVJG0H7", tag="MJ-B-BRICK-E",
                  path=(pt(inch(317.625), inch(-13.56)),
                        pt(inch(318), inch(-13.56))),
                  top_elevation=inch(-13.333), depth=inch(89.104), thickness=inch(0.25),
                  material="neutral-cure low-modulus silicone, ASTM C920 Type S Grade NS Class 50 or better, brick-matched",
                  host_ref="W-B-BRICK", abuts="W-SG-E1", compression_pct=50.0,
                  backer="1/2\" closed-cell backer rod (ASTM C1330 Type C)",
                  source="ASTM C920 Type S Grade NS Class 50+ (e.g. DOWSIL 790/795, GE SilPruf SCS2000, Pecora 890NST); backer ASTM C1330 Type C"),
    # WEST, 4": a precompressed foam seal rather than a 4"-wide bead — Sika Emseal Seismic
    # Colorseal, +/-50% of nominal, 4 1/2" deep at 4" (its size table), listed for brick and
    # masonry cavity walls. Deeper than the 3 5/8" wythe: the back 7/8" stands in the cavity.
    MovementJoint(uid="H1GWTPAS9B", tag="MJ-B-BRICK-W",
                  path=(pt(inch(114), inch(-11.435)), pt(inch(118), inch(-11.435))),
                  top_elevation=inch(-13.333), depth=inch(89.104), thickness=inch(4.5),
                  material="Sika Emseal Seismic Colorseal 4\" precompressed foam seal, brick-matched",
                  host_ref="W-B-BRICK", abuts="W-SG-W1", compression_pct=50.0,
                  source="Sika Emseal Seismic Colorseal product data sheet (+/-50% of nominal; 4\" size, 4 1/2\" depth of seal)"),
]
