"""Shared structural connection hardware — the parts the hardware take-off bills.

Each item is the *published product family*, keyed by the condition (role) the resolved
model derives, so a house never names a part number in its plan source. Sources cite the
manufacturer system the record describes; no rating here is estimated.
"""

from __future__ import annotations

from typehaus.takeoff.hardware_catalog import (
    ROLE_COIL_STRAP,
    ROLE_CONCRETE_FACE_MOUNT_HANGER,
    ROLE_EMBEDDED_STRAP_HOLDOWN,
    ROLE_EXTERIOR_INSULATION_SCREW,
    ROLE_FACE_MOUNT_JOIST_HANGER,
    ROLE_BRACE_THROUGH_BOLT,
    ROLE_HURRICANE_TIE,
    ROLE_KNEE_BRACE,
    ROLE_MUDSILL_ANCHOR,
    ROLE_POST_BASE,
    ROLE_BEAM_HOLD_DOWN,
    ROLE_GLAZING_PANEL_FASTENER,
    ROLE_SLOPED_JOIST_HANGER,
    ROLE_STANDING_SEAM_CLAMP,
    ROLE_STUD_PLATE_TIE,
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

H25A_HURRICANE_TIE = StructuralHardware(
    tag="simpson-h2-5a-hurricane-tie",
    name="H2.5A hurricane/seismic tie",
    role=ROLE_HURRICANE_TIE,
    manufacturer=_SIMPSON,
    model="H2.5A",
    source="Simpson Strong-Tie H2.5A tie (strongtie.com/h25a) — rafter/joist-to-plate "
           "uplift connection",
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
    H25A_HURRICANE_TIE,
    S5_SEAM_CLAMP,
    KBS_BEAM_HOLD_DOWN,
    POLY_PANEL_FASTENER,
)
