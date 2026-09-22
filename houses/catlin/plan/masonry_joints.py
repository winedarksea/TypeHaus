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
    # EAST, 3/8": the mortar-joint width TN 18A calls typical. DOWSIL 790 (ASTM C920 Type S,
    # Grade NS, Class 100/50 — so 50% in compression) tooled 1/4" deep (TN 18A's minimum;
    # half the width would be 3/16") over 1/2" Nomaco HBR closed-cell rod (ASTM C1330
    # Type C, ~25% over the joint width as TN 18A asks).
    MovementJoint(uid="8C4QVJG0H7", tag="MJ-B-BRICK-E",
                  path=(pt(inch(329.625), inch(-13.56)),
                        pt(inch(330), inch(-13.56))),
                  top_elevation=inch(-8), depth=inch(94.4375), thickness=inch(0.25),
                  material="DOWSIL 790 silicone, brick-matched", host_ref="W-B-BRICK",
                  abuts="W-SG-E1", compression_pct=50.0,
                  backer="1/2\" Nomaco HBR closed-cell backer rod",
                  source="Dow DOWSIL 790 TDS form 61-884-01 (C920 Class 100/50, +100/-50); Nomaco HBR (ASTM C1330 Type C)"),
    # WEST, 4": a precompressed foam seal rather than a 4"-wide bead — Sika Emseal Seismic
    # Colorseal, +/-50% of nominal, 4 1/2" deep at 4" (its size table), listed for brick and
    # masonry cavity walls. Deeper than the 3 5/8" wythe: the back 7/8" stands in the cavity.
    MovementJoint(uid="H1GWTPAS9B", tag="MJ-B-BRICK-W",
                  path=(pt(inch(102), inch(-11.435)), pt(inch(106), inch(-11.435))),
                  top_elevation=inch(-8), depth=inch(94.4375), thickness=inch(4.5),
                  material="Sika Emseal Seismic Colorseal 4\" precompressed foam seal, brick-matched",
                  host_ref="W-B-BRICK", abuts="W-SG-W1", compression_pct=50.0,
                  source="Sika Emseal Seismic Colorseal product data sheet (+/-50% of nominal; 4\" size, 4 1/2\" depth of seal)"),
]
