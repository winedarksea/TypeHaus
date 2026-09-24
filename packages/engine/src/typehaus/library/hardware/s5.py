"""S-5! seam clamps and snow retention.

Split out of the former ``library/hardware.py``; see the package docstring.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    ROLE_NAIL_STRIP_SEAM_CLAMP,
    ROLE_PIPE_CLAMP,
    ROLE_SNAP_LOCK_SEAM_CLAMP,
    ROLE_SNOW_RETENTION,
    ROLE_STANDING_SEAM_CLAMP,
    StructuralHardware,
)

S5_SEAM_CLAMP = StructuralHardware(
    tag="s5-standing-seam-clamp",
    name="S-5! standing-seam clamp",
    role=ROLE_STANDING_SEAM_CLAMP,
    manufacturer="S-5!",
    model="S-5!",
    source="S-5! non-penetrating standing-seam clamp (s-5.com) — attaches accessories to "
           "a standing-seam panel rib without piercing the panel",
)

# --- wind mitigation -----------------------------------------------------------------------
# A seam clamp set on the seam purely to resist UPLIFT, rather than to carry an accessory.
# S-5! is explicit that "any of our seam clamps will improve wind resistance of the roof and
# can be used for that purpose"; the dedicated WindClamp line (DL/UD/2X) fits commercial
# trapezoidal profiles only, so on residential snap-lock and nail-strip the wind clamp IS the
# ordinary catalog clamp matched to the profile. These are separate records from
# ``S5_SEAM_CLAMP`` because the profile decides the part and the parts are not interchangeable
# — an S-5-S will not close on a nail-strip bulb, and an S-5-N will not close on a snap-lock
# leg. Both are non-penetrating: stainless setscrews (Torx T-30) dimple the seam without
# piercing it, so no sealant, no flashing and no effect on the panel warranty.
#
# S-5! publishes NO prescriptive layout — the install sheet puts spacing and configuration on
# "the user and/or installer". The one prescriptive standard is FM Global DS 1-31 Table 2,
# which places clamps at CORNER zone clip positions above 90 psf and adds the perimeter above
# 135 psf. The governing rule of thumb, from S-5!'s own PV guidance, is that clamp spacing
# must never EXCEED the panel's own clip spacing.
S5_S_SNAP_LOCK_CLAMP = StructuralHardware(
    tag="s5-s-snap-lock-clamp",
    role=ROLE_SNAP_LOCK_SEAM_CLAMP,
    name="S-5-S snap-lock seam clamp",
    manufacturer="S-5!",
    model="S-5-S",
    source="S-5! S-5-S clamp (s-5.com/s-5-s-clamps) — two-setscrew non-penetrating clamp "
           "for 1.5\"-1.75\" snap-lock/snap-together vertical seams",
)

S5_N_NAIL_STRIP_CLAMP = StructuralHardware(
    tag="s5-n-nail-strip-clamp",
    role=ROLE_NAIL_STRIP_SEAM_CLAMP,
    name="S-5-N nail-strip seam clamp",
    manufacturer="S-5!",
    model="S-5-N",
    source="S-5! S-5-N clamp (s-5.com/s-5-n-clamps) — two-setscrew non-penetrating clamp "
           "for nail-strip / bulb-and-lip seam profiles",
)

# The ring that actually holds a round pipe — a downspout leader, a vent riser, conduit —
# against the standing seam. It is *not* the same part as the clamp above: the CanDuit is an
# electro-zinc strap with an EPDM liner pad, and its M8 threaded shaft mounts to any S-5!
# clamp or bracket, so every ring ordered needs a clamp under it (``requires_role``).
#
# Fourteen diameters, selected on the pipe's *outer* diameter, not its trade size — which is
# why the plan authors the ring number: a 4" round leader (4.0" OD) takes #13 (4.00-4.37"),
# while 3" PVC DWV (3.5" OD) takes #11 (3.4-3.7"). Billing these as plain seam clamps, which
# is what a family-prefix match on "S-5!" used to do, ships brackets and no rings.
S5_CANDUIT_PIPE_CLAMP = StructuralHardware(
    tag="s5-canduit-pipe-clamp",
    name="S-5! CanDuit pipe clamp",
    role=ROLE_PIPE_CLAMP,
    manufacturer="S-5!",
    model="S-5! CanDuit",
    source="S-5! CanDuit pipe clamp (s-5.com) — electro-zinc coated steel strap with an "
           "EPDM liner pad, 14 sizes for 0.79\"-4.6\" pipe OD; mounts on an S-5! clamp or "
           "bracket by its M8 threaded shaft",
    requires_role=ROLE_STANDING_SEAM_CLAMP,
)

# Snow retention for a standing-seam slope that sheds onto something. ColorGard is a rail
# system, not a discrete "guard": a continuous 1"x1" aluminum bar runs the width of the slope
# through the seam clamps, with a colour-matched strip clipped into it. It reaches the panel
# only through those clamps, so like the CanDuit ring above it declares ``requires_role`` and
# every foot of rail ordered brings its clamps with it.
S5_COLORGARD_SNOW_RETENTION = StructuralHardware(
    tag="s5-colorgard-snow-retention",
    name="S-5! ColorGard snow-retention rail",
    role=ROLE_SNOW_RETENTION,
    manufacturer="S-5!",
    model="S-5! ColorGard",
    source="S-5! ColorGard snow retention system (s-5.com) — 1\" x 1\" aluminum crossbar "
           "with a colour-matched panel strip, carried on S-5! seam clamps; spacing and row "
           "count are the manufacturer's calculation at the site ground snow load",
    requires_role=ROLE_STANDING_SEAM_CLAMP,
)
