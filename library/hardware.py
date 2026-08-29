"""Shared structural connection hardware — the parts the hardware take-off bills.

Each item is the *published product family*, keyed by the condition (role) the resolved
model derives, so a house never names a part number in its plan source. Sources cite the
manufacturer system the record describes; no rating here is estimated.
"""

from __future__ import annotations

from typehaus.takeoff.hardware_catalog import (
    ROLE_BEAM_HOLD_DOWN,
    ROLE_BRACE_THROUGH_BOLT,
    ROLE_COIL_STRAP,
    ROLE_CONCRETE_FACE_MOUNT_HANGER,
    ROLE_EMBEDDED_STRAP_HOLDOWN,
    ROLE_EXPOSED_FASTENER_PANEL_SCREW,
    ROLE_EXTERIOR_INSULATION_SCREW,
    ROLE_FACE_MOUNT_JOIST_HANGER,
    ROLE_GLAZING_PANEL_FASTENER,
    ROLE_HURRICANE_TIE,
    ROLE_KNEE_BRACE,
    ROLE_LATERAL_TIE_PLATE,
    ROLE_MASONRY_GUSSET_ANGLE,
    ROLE_MUDSILL_ANCHOR,
    ROLE_NAIL_STRIP_SEAM_CLAMP,
    ROLE_PIPE_CLAMP,
    ROLE_POCKET_DOOR_FRAME_KIT,
    ROLE_POST_BASE,
    ROLE_POST_BASE_ANCHOR,
    ROLE_POST_CAP,
    ROLE_PV_SEAM_CLAMP,
    ROLE_SILL_ANCHOR_BOLT,
    ROLE_SLOPED_JOIST_HANGER,
    ROLE_SNAP_LOCK_SEAM_CLAMP,
    ROLE_SNOW_RETENTION,
    ROLE_STANDING_SEAM_CLAMP,
    ROLE_STUD_PLATE_TIE,
    ROLE_THROUGH_PANEL_PIPE_STRAP,
    StructuralHardware,
)

_SIMPSON = "Simpson Strong-Tie"

# Structural wood screws through continuous exterior insulation. Two families cover the
# range: the 0.220" SDWS Timber Screw up to 8" (a wall's foam sandwich), and the 0.190"
# SDWH Timber-Hex beyond it (a roof's, which carries far more foam). Only one family may
# serve the role at a given length, so the two ladders must not overlap.
SDWS_TIMBER_SCREW = StructuralHardware(
    tag="simpson-sdws-timber-screw",
    name="SDWS Timber Screw (0.220 in shank)",
    role=ROLE_EXTERIOR_INSULATION_SCREW,
    manufacturer=_SIMPSON,
    model="SDWS22___DB",
    part_number_by_length_in={
        3.0: "SDWS22300DB", 4.0: "SDWS22400DB", 5.0: "SDWS22500DB",
        6.0: "SDWS22600DB", 8.0: "SDWS22800DB",
    },
    source="Simpson Strong-Tie SDWS Timber Screw product family (strongtie.com/sdws) — "
           "0.220 in shank structural wood screw, Double-Barrier coated (DB)",
)

SDWH_TIMBER_HEX_SCREW = StructuralHardware(
    tag="simpson-sdwh-timber-hex-screw",
    name="SDWH Timber-Hex Screw (0.190 in shank)",
    role=ROLE_EXTERIOR_INSULATION_SCREW,
    manufacturer=_SIMPSON,
    model="SDWH19____DB",
    part_number_by_length_in={10.0: "SDWH191000DB", 12.0: "SDWH191200DB"},
    source="Simpson Strong-Tie SDWH Timber-Hex Screw product family "
           "(strongtie.com/sdwh) — long-length structural wood screw for thick "
           "exterior-insulation assemblies",
)

LSSR_SLOPED_HANGER = StructuralHardware(
    tag="simpson-lssr-adjustable-slope-hanger",
    name="LSSR field-adjustable slope/skew hanger",
    role=ROLE_SLOPED_JOIST_HANGER,
    manufacturer=_SIMPSON,
    model="LSSR",
    source="Simpson Strong-Tie LSSR adjustable slope/skew joist and rafter hanger "
           "(strongtie.com/lssr) — the hanger published for a raked member framing into "
           "the face of a ridge beam",
)

LUS_FACE_MOUNT_HANGER = StructuralHardware(
    tag="simpson-lus-face-mount-hanger",
    name="LUS face-mount joist hanger",
    role=ROLE_FACE_MOUNT_JOIST_HANGER,
    manufacturer=_SIMPSON,
    model="LUS",
    source="Simpson Strong-Tie LUS/LUS2 face-mount joist hanger family "
           "(strongtie.com/lus) — level joist into the face of a wood carrier",
)

HUCQ_CONCRETE_HANGER = StructuralHardware(
    tag="simpson-hucq-concealed-flange-hanger",
    name="HUCQ concealed-flange masonry/concrete hanger",
    role=ROLE_CONCRETE_FACE_MOUNT_HANGER,
    manufacturer=_SIMPSON,
    model="HUCQ",
    source="Simpson Strong-Tie HUCQ concealed-flange hanger (strongtie.com/hucq) — "
           "published for wood members hung on concrete or masonry",
)

APVKB_KNEE_BRACE = StructuralHardware(
    tag="simpson-apvkb45-6-knee-brace",
    name="Outdoor Accents Avant 45-degree knee brace, 6 in",
    role=ROLE_KNEE_BRACE,
    manufacturer=_SIMPSON,
    model="APVKB45-6",
    source="Simpson Strong-Tie Outdoor Accents Avant Collection APVKB knee brace "
           "(strongtie.com/apvkb) — 45-degree brace at a post/beam joint",
)

APVB_BRACE_BOLT = StructuralHardware(
    tag="simpson-outdoor-accents-hex-bolt-1-2",
    name='Outdoor Accents 1/2 in hex-head through bolt with washer, 6 in',
    role=ROLE_BRACE_THROUGH_BOLT,
    manufacturer=_SIMPSON,
    model="APVB12-6",
    source="Simpson Strong-Tie Outdoor Accents hex-head structural bolt + washer "
           "(strongtie.com/outdooraccents) — through-bolts a 2x knee brace at each end",
)

MASA_MUDSILL_ANCHOR = StructuralHardware(
    tag="simpson-masa-mudsill-anchor",
    name="MASA mudsill anchor",
    role=ROLE_MUDSILL_ANCHOR,
    manufacturer=_SIMPSON,
    model="MASA",
    source="Simpson Strong-Tie MASA mudsill anchor (strongtie.com/masa) — cast into the "
           "top of a concrete or ICF wall to anchor the sill plate",
)

STHD_STRAP_HOLDOWN = StructuralHardware(
    tag="simpson-sthd-embedded-strap-holdown",
    name="STHD embedded strap-tie holdown",
    role=ROLE_EMBEDDED_STRAP_HOLDOWN,
    manufacturer=_SIMPSON,
    model="STHD",
    source="Simpson Strong-Tie STHD embedded strap-tie holdown (strongtie.com/sthd) — "
           "cast into concrete and nailed to the framing at the end of a braced sill run",
)

SP4_STUD_PLATE_TIE = StructuralHardware(
    tag="simpson-sp4-stud-plate-tie",
    name="SP4 stud plate tie (2x4)",
    role=ROLE_STUD_PLATE_TIE,
    manufacturer=_SIMPSON,
    model="SP4",
    fits_nominal=("2x4",),
    source="Simpson Strong-Tie SP stud plate tie family (strongtie.com/sp) — SP4 is the "
           "published size for a 2x4 stud-to-plate connection",
)

SP6_STUD_PLATE_TIE = StructuralHardware(
    tag="simpson-sp6-stud-plate-tie",
    name="SP6 stud plate tie (2x6)",
    role=ROLE_STUD_PLATE_TIE,
    manufacturer=_SIMPSON,
    model="SP6",
    fits_nominal=("2x6",),
    source="Simpson Strong-Tie SP stud plate tie family (strongtie.com/sp) — SP6 is the "
           "published size for a 2x6 stud-to-plate connection",
)

CS16_COIL_STRAP = StructuralHardware(
    tag="simpson-cs16-coiled-strap",
    name="CS16 coiled strap, 16 ga",
    role=ROLE_COIL_STRAP,
    manufacturer=_SIMPSON,
    model="CS16",
    unit="coil",
    source="Simpson Strong-Tie CS16 coiled strap (strongtie.com/cs) — 16 ga coiled "
           "strapping cut to length for wall-to-wall continuity across a floor band",
)

ABU_POST_BASE = StructuralHardware(
    tag="simpson-abu66-standoff-post-base",
    name="ABU66 standoff post base (6x6)",
    role=ROLE_POST_BASE,
    manufacturer=_SIMPSON,
    model="ABU66",
    fits_nominal=("6x6",),
    source="Simpson Strong-Tie ABU adjustable standoff post base (strongtie.com/abu) — "
           "1 in standoff keeps the post end off the wet slab",
)

ABU44_POST_BASE = StructuralHardware(
    tag="simpson-abu44-standoff-post-base",
    name="ABU44 standoff post base (4x4)",
    role=ROLE_POST_BASE,
    manufacturer=_SIMPSON,
    model="ABU44",
    fits_nominal=("4x4",),
    source="Simpson Strong-Tie ABU adjustable standoff post base (strongtie.com/abu) — "
           "the 4x4 size of the same family as ABU66; a post base is size-selected, so "
           "the role carries a ladder rather than one part",
)

# The bolt every ABU sits on. Simpson publish the ABU's uplift and lateral values against a
# 5/8 in anchor and supply none — "anchor bolt by others" — so a schedule of bases with no
# bolts is short the part the published capacity is measured through.
#
# **304 stainless, and that is not gold-plating.** Ten of the twelve bases this serves are
# ABU66SS, stainless because they stand at grade in a wet location; bolting a stainless
# stirrup down with a hot-dip bolt puts a noble metal in contact with an active one in
# standing water, which corrodes the bolt preferentially — the anchor, not the stirrup. The
# two ZMAX ABU44s on the dry basement slab can take a $3-7 galvanised bolt instead; that is a
# purchasing swap worth about $25 on the job, recorded in the house note beside the MiTek
# ones rather than split into a second catalogue product (``hardware_for_role`` holds exactly
# one item per role).
#
# The model string leads with "AB-" so ``cost_codes.KEY_PATTERNS`` files it under CSI
# 03 15 00 with the concrete sub who sets it, not with the framer who lands on it — the same
# reason SILL_ANCHOR_BOLT above is named the way it is.
POST_BASE_ANCHOR_BOLT = StructuralHardware(
    tag="post-base-anchor-bolt-five-eighths",
    name="5/8 in x 10 in cast-in post-base anchor bolt, 304 stainless, with nut and washer",
    role=ROLE_POST_BASE_ANCHOR,
    manufacturer=_SIMPSON,
    model="AB-058-10-SS",
    source="Simpson Strong-Tie ABU/ABU-Z adjustable post base installation "
           "(strongtie.com/abu) — the published uplift and lateral values are taken through "
           "a 5/8 in anchor bolt, which the base does not include; 304 stainless to match "
           "the ABU66SS stirrups it fastens at grade",
)

PC6Z_POST_CAP = StructuralHardware(
    tag="simpson-pc6z-post-cap",
    name="PC6Z post cap (6x6)",
    role=ROLE_POST_CAP,
    manufacturer=_SIMPSON,
    model="PC6Z",
    fits_nominal=("6x6",),
    source="Simpson Strong-Tie PC post cap (strongtie.com/pc) — ZMAX cap seating a beam on "
           "a 6x6 post and carrying the uplift at that joint; published for equal post and "
           "beam widths, which is the condition it is selected for here",
)

LTP4_LATERAL_TIE_PLATE = StructuralHardware(
    tag="simpson-ltp4-lateral-tie-plate",
    name="LTP4 lateral tie plate",
    role=ROLE_LATERAL_TIE_PLATE,
    manufacturer=_SIMPSON,
    model="LTP4",
    source="Simpson Strong-Tie LTP4 lateral tie plate (strongtie.com/ltp) — transfers "
           "lateral load between a plate and the framing or rim under it",
)

# A threaded rod set in wet concrete, plus the square plate washer that IRC R602.11.1 makes
# mandatory. Two parts, one joint: they are catalogued as one item because neither is
# ordered without the other and a bolt counted without its washer is not a buildable line.
# The model string leads with "AB-" so ``cost_codes.KEY_PATTERNS`` can file it with the
# concrete sub who sets it, not with the framer who lands on it.
SILL_ANCHOR_BOLT = StructuralHardware(
    tag="sill-anchor-bolt-half-inch",
    name="1/2 in x 10 in sill anchor bolt with BP1/2 plate washer",
    role=ROLE_SILL_ANCHOR_BOLT,
    manufacturer=_SIMPSON,
    model="AB-050-10-BP",
    source="IRC R403.1.6 anchor bolt (1/2 in diameter, 7 in embedment) with the "
           "Simpson Strong-Tie BP 1/2 plate washer R602.11.1 requires "
           "(strongtie.com/bp) — set in wet concrete between the mudsill anchors",
)

H25A_HURRICANE_TIE = StructuralHardware(
    tag="simpson-h2-5a-hurricane-tie",
    name="H2.5A hurricane/seismic tie",
    role=ROLE_HURRICANE_TIE,
    manufacturer=_SIMPSON,
    model="H2.5A",
    source="Simpson Strong-Tie H2.5A tie (strongtie.com/h25a) — rafter/joist-to-plate "
           "uplift connection",
)

HGAM10_MASONRY_GUSSET = StructuralHardware(
    tag="simpson-hgam10-masonry-gusset-angle",
    name="HGAM10 masonry gusset angle",
    role=ROLE_MASONRY_GUSSET_ANGLE,
    manufacturer=_SIMPSON,
    model="HGAM10",
    source="Simpson Strong-Tie HGAM masonry/concrete gusset angle (strongtie.com/hgam) — "
           "#14 screws into the wood leg, Titen Turbo concrete screws into the masonry leg; "
           "1-1/2 in minimum edge distance to the anchors",
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

# --- wind mitigation (2026-08-20) --------------------------------------------------------
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

KBS_BEAM_HOLD_DOWN = StructuralHardware(
    tag="simpson-kbs1z-strap",
    name="KBS1Z knee-brace / beam strap (ZMAX)",
    role=ROLE_BEAM_HOLD_DOWN,
    manufacturer=_SIMPSON,
    model="KBS1Z",
    source="Simpson Strong-Tie KBS1Z strap (strongtie.com/kbs) — ZMAX galvanized strap "
           "tying a beam to the post it bears on; published for knee braces and for "
           "beam-to-post uplift, which is the joint it is used for here",
)

# The screw an exposed-fastener wall panel is hung on. Driven through the panel flat (not
# the rib) into the support behind, it is the ONLY penetration in the water plane, so the
# gasket — not the steel — sets the service life of the wall.
#
# 316, not 304: this is a lakeside/road-salt exposure, and a stainless screw head that
# streaks or pits is both the leak path and the thing you look at from the driveway.
#
# Length arithmetic, so the choice is auditable: 1-1/2" through a ~0.02" 26 ga panel into
# the flat 1.5" KDAT outer girt leaves ~1.4" of embedment — the full thickness of the
# nailer, with the tip breaking through into the blind 0.5" vent gap behind it rather than
# stopping in the sheathing. Longer is not better here: a screw that reaches the WRB adds a
# second penetration in a plane that is meant to stay unbroken.
EXPOSED_FASTENER_PANEL_SCREW = StructuralHardware(
    tag="simpson-t09150hwam-panel-screw",
    name="#9 x 1-1/2\" 316 stainless metal-panel screw, EPDM washer",
    role=ROLE_EXPOSED_FASTENER_PANEL_SCREW,
    manufacturer=_SIMPSON,
    model="T09150HWAM",
    part_number_by_length_in={1.5: "T09150HWAM"},
    source="Simpson Strong-Tie T09150HWAM (strongtie.com) — #9 x 1-1/2\" Type 316 stainless "
           "metal-panel screw, hex washer head with a bonded EPDM sealing washer, for "
           "through-fastening metal panel to a wood support",
)

# The strap that carries a round pipe on an exposed-fastener panel. The CanDuit ring above
# cannot serve here: it mounts on a seam clamp by its M8 shaft (``requires_role``), and a
# PBR wall has no seam to clamp. This one reaches the building the other way — two panel
# screws straight through the panel flat into the girt — so it declares no ``requires_role``
# and brings its own fixings instead of a bracket.
#
# The standoff block is what makes it legal on a ribbed panel: without it the strap would
# bear on the rib crowns and either crush them or hold the pipe off the wall unevenly.
THROUGH_PANEL_PIPE_STRAP = StructuralHardware(
    tag="through-panel-standoff-pipe-strap",
    name="316 stainless two-hole pipe strap on standoff block",
    role=ROLE_THROUGH_PANEL_PIPE_STRAP,
    manufacturer="generic",
    model="SS316-STANDOFF-STRAP",
    source="generic Type 316 stainless two-hole pipe strap on a moulded standoff block, "
           "sized on pipe OUTER diameter the way the CanDuit ring is; fixed with two "
           "T09150HWAM gasketed panel screws per point. No single manufacturer system is "
           "specified, so this record is deliberately generic",
)

# Multiwall polycarbonate is fastened through oversize holes so the sheet can move: the
# washer seals, the screw does not clamp. Stainless because the fastener sits in the wet
# zone of an exterior roof for the life of the sheet.
POLY_PANEL_FASTENER = StructuralHardware(
    tag="stainless-gasketed-panel-screw",
    name="#12 stainless gasketed panel screw with EPDM-bonded washer",
    role=ROLE_GLAZING_PANEL_FASTENER,
    manufacturer="generic",
    model="SS-GASKET-12",
    source="generic 304 stainless #12 hex-head panel screw with a bonded EPDM sealing "
           "washer, the standard multiwall-polycarbonate fixing; no single manufacturer "
           "system is specified, so this record is deliberately generic",
)

# PV module mounting on the standing seam: the S-5! PVKIT clamp+bracket assembly grips a
# panel rib without penetration and takes the module frame directly (no rails). Distinct
# model string so ``Connector(size="S-5-PVKIT")`` bills this kit, not the plain clamp.
S5_PV_KIT = StructuralHardware(
    tag="s5-pvkit-clamp",
    name="S-5! PVKIT standing-seam PV mounting kit",
    role=ROLE_PV_SEAM_CLAMP,
    manufacturer="S-5!",
    model="S-5-PVKIT",
    source="S-5! PVKIT 2.0 (s-5.com/pvkit) — non-penetrating standing-seam clamp with "
           "integrated module clamp; one kit per module corner support point",
)

# --- door hardware ------------------------------------------------------------------
# The first non-structural family in this catalog, and it earns its place: a pocket door's
# frame kit is the whole reason a pocket is a *product* decision and not a framing one. The
# kit brings the split studs, the head track, the hangers and the leaf guides, and it is
# what caps the leaf width — which is why the two records below are two products, not two
# rows of one ladder. A takeoff that orders the commodity kit for a 4'-0" solid-core leaf
# gets a frame the door will pull off the wall.
#
# Selected by door width through ``fits_nominal`` (inches, as authored on the DoorType).
POCKET_FRAME_KIT_1500PF = StructuralHardware(
    tag="johnson-1500pf-pocket-frame-kit",
    name="Pocket door frame kit, 2x4 wall (commodity, to 36\"/125 lb)",
    role=ROLE_POCKET_DOOR_FRAME_KIT,
    manufacturer="Johnson Hardware",
    # Named for its trade, not its brand: ``cost_codes`` routes ``pocket-frame-*`` to
    # CSI 08 71 00 Door Hardware rather than to the hardware section's rough-carpentry
    # default, and this string is the BOM key that rule matches.
    model="POCKET-FRAME-1500PF",
    fits_nominal=("24", "28", "30", "32", "36"),
    part_number_by_length_in={24: "152068PF", 28: "152468PF", 30: "152668PF",
                              32: "152868PF", 36: "153068PF"},
    source="Johnson Hardware 1500PF series pocket door frame kit "
           "(johnsonhardware.com/1500-series-pocket-door-frame-kits) — all-steel split "
           "studs, 6063T6 extruded aluminium track, 125 lb max per door, 3-1/2\" minimum "
           "wall structure. Door, jambs, drywall and locks not included.",
)

# Past the commodity ladder the frame, the track and the hangers all change. No published
# SKU ladder is recorded here on purpose: the width families are published, the part
# numbers are configured per order, and inventing one would be an estimate wearing a part
# number's clothes.
POCKET_FRAME_KIT_HEAVY = StructuralHardware(
    tag="cavity-sliders-cs-for-wood-pocket-frame",
    name="Pocket door frame, 2x4 wall (heavy duty, to 4'-0\")",
    role=ROLE_POCKET_DOOR_FRAME_KIT,
    manufacturer="Cavity Sliders",
    model="POCKET-FRAME-CS-WOOD",
    fits_nominal=("48",),
    source="Cavity Sliders CS For Wood cavity slider pocket frame, 2x4 stud "
           "(cavitysliders.com/cavislider/cavity-slider-pocket-door-frame/2x4-stud/) — "
           "published to 4'0\" x 8'0\", above the 36\"/125 lb ceiling of the commodity "
           "series.",
)

STRUCTURAL_HARDWARE: tuple = (
    SDWS_TIMBER_SCREW,
    SDWH_TIMBER_HEX_SCREW,
    LSSR_SLOPED_HANGER,
    LUS_FACE_MOUNT_HANGER,
    HUCQ_CONCRETE_HANGER,
    APVKB_KNEE_BRACE,
    APVB_BRACE_BOLT,
    MASA_MUDSILL_ANCHOR,
    STHD_STRAP_HOLDOWN,
    SP4_STUD_PLATE_TIE,
    SP6_STUD_PLATE_TIE,
    CS16_COIL_STRAP,
    ABU_POST_BASE,
    ABU44_POST_BASE,
    POST_BASE_ANCHOR_BOLT,
    PC6Z_POST_CAP,
    LTP4_LATERAL_TIE_PLATE,
    SILL_ANCHOR_BOLT,
    H25A_HURRICANE_TIE,
    HGAM10_MASONRY_GUSSET,
    S5_SEAM_CLAMP,
    S5_S_SNAP_LOCK_CLAMP,
    S5_N_NAIL_STRIP_CLAMP,
    S5_CANDUIT_PIPE_CLAMP,
    S5_PV_KIT,
    S5_COLORGARD_SNOW_RETENTION,
    KBS_BEAM_HOLD_DOWN,
    POLY_PANEL_FASTENER,
    EXPOSED_FASTENER_PANEL_SCREW,
    THROUGH_PANEL_PIPE_STRAP,
    POCKET_FRAME_KIT_1500PF,
    POCKET_FRAME_KIT_HEAVY,
)
