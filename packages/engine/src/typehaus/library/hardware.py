"""Shared structural connection hardware — the parts the hardware take-off bills.

Each item is the *published product family*, keyed by the condition (role) the resolved
model derives, so a house never names a part number in its plan source. Sources cite the
manufacturer system the record describes; no rating here is estimated.

**Allowable loads.** Some items carry an ``AllowableLoads`` record
transcribed from a named evaluation report. Three rules govern every one of them, and they
are the reason the field exists at all rather than a "capacity" column somebody fills in:

1. **A number is copied, never derived.** Nothing here is interpolated, converted, scaled
   from a similar part, or reasoned to. If a report does not print it, the field is ``None``.
2. **``None`` is a finding, not a blank.** Four parts below carry an ``AllowableLoads`` whose
   every value is ``None``. Each one names the document that was read and says why it came
   back empty — an unevaluated part number, a scope exclusion, a value that depends on an
   input this model does not carry. That is a materially different statement from "nobody has
   looked", which is what ``allowable=None`` (the default) means.
3. **The species column is load-bearing.** Simpson tabulate against specific gravity. Catlin
   frames in SPF (SG 0.42) and several of these reports publish only DF/SP (SG 0.50) values.
   Where a report gives both, the SPF/HF figure is what is recorded; where it gives only the
   0.50 value, that is recorded *and said so*, because using it for SPF is an unconservative
   error that no amount of care downstream can detect.

Every one of these was pulled from the report itself, not from a retailer listing. That
distinction turned out to matter: several retailers cite ESR-1622 for the ABU66SS, and
ESR-1622 does not cover it. **What covers it is a Simpson engineering letter rather than a
code report** — see ``_L_F_SSNAILS`` below. A stainless connector is rated at its carbon
twin's published loads; the only thing stainless costs is NAIL withdrawal, and a ring-shank
substitution buys that back. Two records in this file said "unrated" for two years on the
strength of having read the code report and stopped there.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    EXPOSURE_DRY,
    EXPOSURE_TREATED,
    ROLE_BEAM_HOLD_DOWN,
    ROLE_BEARING_STANDOFF,
    ROLE_BRACE_THROUGH_BOLT,
    ROLE_COIL_STRAP,
    ROLE_CONCRETE_FACE_MOUNT_HANGER,
    ROLE_DECK_EQUIPMENT_ANCHOR,
    ROLE_EMBEDDED_BEAM_ANCHOR,
    ROLE_EMBEDDED_STRAP_HOLDOWN,
    ROLE_EQUIPMENT_PAD_ANCHOR,
    ROLE_EXPOSED_FASTENER_PANEL_SCREW,
    ROLE_EXTERIOR_INSULATION_SCREW,
    ROLE_FACE_MOUNT_JOIST_HANGER,
    ROLE_FLOOR_TRUSS_HANGER,
    ROLE_GABLE_END_TIE,
    ROLE_GABLE_TRUSS_ANCHOR,
    ROLE_GIRT_STANDOFF_SCREW,
    ROLE_GLAZING_PANEL_FASTENER,
    ROLE_HURRICANE_TIE,
    ROLE_IJOIST_FACE_MOUNT_HANGER,
    ROLE_KNEE_BRACE,
    ROLE_LAPPED_BRACE_BOLT,
    ROLE_LATERAL_TIE_PLATE,
    ROLE_MASONRY_GUSSET_ANGLE,
    ROLE_MUDSILL_ANCHOR,
    ROLE_NAIL_STRIP_SEAM_CLAMP,
    ROLE_PARTITION_DEFLECTION_SCREW,
    ROLE_PIPE_CLAMP,
    ROLE_POCKET_DOOR_FRAME_KIT,
    ROLE_POST_BASE,
    ROLE_POST_BASE_ANCHOR,
    ROLE_POST_CAP,
    ROLE_POST_TENSION_TIE,
    ROLE_PV_SEAM_CLAMP,
    ROLE_RIDGE_TIE_STRAP,
    ROLE_SCL_FACE_MOUNT_HANGER,
    ROLE_SILL_ANCHOR_BOLT,
    ROLE_SLOPED_JOIST_HANGER,
    ROLE_SNAP_LOCK_SEAM_CLAMP,
    ROLE_SNOW_RETENTION,
    ROLE_STANDING_SEAM_CLAMP,
    ROLE_STUD_PLATE_TIE,
    ROLE_THROUGH_PANEL_PIPE_STRAP,
    AllowableLoads,
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
    # IAPMO UES ER-192 Table 7: every SDWS22 threads 3 in, whatever its overall length. That
    # is why this family cannot serve a girt crossing — at 8 in over a 6 in clamped stack,
    # 1 in of that thread stands inside the members it is supposed to be pulling together.
    thread_length_in_by_length_in={
        3.0: 3.0, 4.0: 3.0, 5.0: 3.0, 6.0: 3.0, 8.0: 3.0,
    },
    source="Simpson Strong-Tie SDWS Timber Screw product family (strongtie.com/sdws) — "
           "0.220 in shank structural wood screw, Double-Barrier coated (DB); thread "
           "lengths per IAPMO UES ER-192 Table 7",
)

# The girt crossing screw, and the only member of its role. Chosen on THREAD, not length:
# 2 in of thread on an 8 in screw leaves 6 in of plain shank to span the 6 in clamped stack
# (girt 1-1/2 in + three-ply block 4-1/2 in), so every turn of the thread is pulling the
# stack together rather than standing in it. See ``engineering/girt_screw.py``.
FASTENMASTER_TIMBERLOK = StructuralHardware(
    tag="fastenmaster-timberlok",
    name="TimberLOK heavy-duty wood screw (0.189 in shank)",
    role=ROLE_GIRT_STANDOFF_SCREW,
    manufacturer="FastenMaster",
    model="TLOK",
    part_number_by_length_in={6.0: "TLOK06", 8.0: "TLOK08", 10.0: "TLOK10"},
    thread_length_in_by_length_in={6.0: 2.0, 8.0: 2.0, 10.0: 2.0},
    source="FastenMaster TimberLOK, ICC-ES ESR-1078 (reissued 2026-01) Table 1A — 2 in "
           "thread at every length; coating rated for ACQ-D <= 0.40 pcf per §4.1.7 / "
           "Table 6",
)

# The two SDPW records are ONE role on two shank diameters — the same non-overlapping ladder
# SDWS/SDWH make above. What picks between them here is NOT length, though: it is the
# TOP-PLATE condition each is published for, which is why both carry ``fits_nominal`` and why
# ``takeoff/partition_fasteners.py`` selects with ``hardware_for_role_and_nominal``.
#
# ** THIS IS THE ONE SCREW HERE THAT MUST NOT CLAMP. ** A polymer sleeve on the shank holds a
# non-bearing partition's top plate a set distance below the joist or rafter over it, so the
# deck deflects onto nothing while the wall stays braced against out-of-plane load. The gap is
# "the space between the top surface of the top plate and the lower surface of the supporting
# members", and Simpson warn that a 0" gap "may result in unintended loading of the partition
# wall". The offset driver bit in the carton is what sets it.
#
# Installation facts that are constraints, not trivia (C-F-2025TECHSUP p. 100): the top plate
# is PREDRILLED 3/8"; the supporting member is NOT predrilled; "the polymer sleeve shall not
# penetrate the supporting member"; and the supporting member must be at least as thick as the
# minimum penetration. A wall running parallel to and BETWEEN the framing above must be
# fastened to code-prescribed blocking — which is the third case the take-off counts.
#
# ``thread_length_in_by_length_in`` is populated because ER-192 publishes it, but the
# clamped-stack rule it feeds is inapplicable to this part by design.
_SDPW_ALLOWABLE_NOTE = (
    "Allowable lateral load, ASD, C_D = 1.6 (safety factor 5.0), at the 3/4 in gap this "
    "house builds — IAPMO UES ER-192 Table 37 / C-F-2025TECHSUP pp. 100-101. The table is "
    "indexed by GAP and by OFFSET (head clear of the plate), not by direction, and F1 "
    "(parallel to the top plate) and F2 (perpendicular) read the same cell, which is why "
    "both fields below carry it. Uplift is deliberately absent and must stay absent: this "
    "joint releases vertically, which is the entire point of the sleeve."
)

SDPW_DEFLECTOR_SCREW = StructuralHardware(
    tag="simpson-sdpw-deflector-screw",
    name="Strong-Drive SDPW DEFLECTOR screw (0.140 in shank)",
    role=ROLE_PARTITION_DEFLECTION_SCREW,
    manufacturer=_SIMPSON,
    model="SDPW14___",
    exposure=EXPOSURE_DRY,
    part_number_by_length_in={3.5: "SDPW14312", 5.0: "SDPW14500"},
    thread_length_in_by_length_in={3.5: 2.0, 5.0: 2.0},
    fits_nominal=("single 2x top plate", "built-up top plate to 2-1/4 in"),
    source="Simpson Strong-Tie Strong-Drive SDPW DEFLECTOR screw, IAPMO UES ER-192 "
           "(rev. 2026-09-08) and Fastening Systems Technical Guide C-F-2025TECHSUP "
           "pp. 100-101 — washer-head 6-lobe T-25 screw with a polypropylene sleeve "
           "(1.38 in on the 3-1/2 in, blue; 2.88 in on the 5 in, orange) setting a "
           "deflection gap at a non-bearing partition's top plate. Type 17 point, e-coat, "
           "INTERIOR DRY SERVICE ONLY (dry-service treatment chemicals and FRT wood are "
           "permitted). Cartons of 50 (-R50) include the offset driver bit; PWKIT25T is "
           "the replacement bit kit. Minimum penetration into the supporting member 1/2 in, "
           "point included. Published gap capacity up to 3/4 in on the 3-1/2 in and 1-1/2 "
           "in on the 5 in. **This record's allowables and spacings are published for a "
           "single 2x or a built-up top plate to 2-1/4 in — NOT for a double 2x**, which "
           "is the SDPW19600's row below",
    allowable=AllowableLoads(
        lateral_f1_lb=140.0,
        lateral_f2_lb=140.0,
        load_duration_factor=1.6,
        species="SPF (minimum specific gravity 0.42); ER-192 Table 37 covers SPF/HF/DFL/SP "
                "and the value recorded is the one that applies to what is built here. An "
                "I-joist flange must be at least 1-1/8 in thick",
        fasteners="The screw IS the fastener: one SDPW14500 through a predrilled 3/8 in "
                  "hole in the top plate, the supporting member undrilled, the sleeve "
                  "stopping short of it. 140 lbf is the 2x + 3/4 in WSP top-plate row at "
                  "0 in offset and a 1/2 in, 3/4 in or 1-1/2 in gap; at a 3/4 in offset "
                  "the same row falls to 105 / 80 / 45 lbf",
        citation=_SDPW_ALLOWABLE_NOTE,
    ),
)

#: The 0.195 in rung — a different shank, point, pilot and DRIVER (T-40, bit kit PWKIT40T).
#: **It is this house's screw, and not because of its length.** Simpson publish the
#: SDPW19600's allowables and spacing for the DOUBLE 2x top plate; the 5 in screw's stop at a
#: 2-1/4 in built-up plate. Catlin frames a double 2x on all eleven interior assemblies.
SDPW19_DEFLECTOR_SCREW = StructuralHardware(
    tag="simpson-sdpw19-deflector-screw",
    name="Strong-Drive SDPW DEFLECTOR screw (0.195 in shank)",
    role=ROLE_PARTITION_DEFLECTION_SCREW,
    manufacturer=_SIMPSON,
    model="SDPW19___",
    exposure=EXPOSURE_DRY,
    part_number_by_length_in={6.0: "SDPW19600"},
    thread_length_in_by_length_in={6.0: 3.0},
    fits_nominal=("double 2x top plate",),
    source="Simpson Strong-Tie Strong-Drive SDPW DEFLECTOR screw, IAPMO UES ER-192 "
           "(rev. 2026-09-08) and C-F-2025TECHSUP pp. 100-101 — the 6 in length on the "
           "0.195 in shank, sawtooth point, 6-lobe T-40, 3.10 in gray sleeve, e-coat, "
           "interior dry service, cartons of 50 (-R50) with the offset bit. Minimum "
           "penetration into the supporting member 3/4 in, point included; gap capacity to "
           "1-1/2 in. **The row published for a DOUBLE 2x top plate and thinner**, which "
           "is why this and not the 5 in is the part at a 3 in plate stack",
    allowable=AllowableLoads(
        lateral_f1_lb=165.0,
        lateral_f2_lb=165.0,
        load_duration_factor=1.6,
        species="SPF (minimum specific gravity 0.42); ER-192 Table 37 covers SPF/HF/DFL/SP. "
                "The supporting members here are engineered — 11-7/8 in TJI 230 rafters, "
                "I-joists and open-web floor trusses — which ER-192 permits (dimension "
                "lumber, truss, I-joist, glulam, SCL or CLT) at a flange thickness of at "
                "least 1-1/8 in. **The joist maker's own fastener rules have NOT been read**",
        fasteners="One SDPW19600 through a predrilled 3/8 in hole in the double top plate, "
                  "the supporting member undrilled. 165 lbf is the (2) 2x row at a 3/4 in "
                  "gap, IDENTICAL at 0 in and 3/4 in offset; the same row reads 295 lbf at "
                  "a 0 in gap, 205 at 1/2 in and 75 at 1-1/2 in. The companion MAXIMUM "
                  "SPACING table (8 ft / 10 ft walls at 5 psf, C_D = 1.6) bottoms out at "
                  "42 in / 36 in for this part, which every count this house bills sits "
                  "inside",
        citation=_SDPW_ALLOWABLE_NOTE,
    ),
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

# **Sloped-only and skewed are two different rows, and the house reads the sloped-only
# one.** Every published table splits them (C-C-2026 pp. 178 vs 179; ER-280 Table 11; TJ-4000
# p. 15), because skewing costs fasteners — the header schedule drops 14 -> 13 and the joist
# 12 -> 9, and CSG-TJUS25 p. 10 says why: "All holes must be filled except for the LSSR
# hanger when skewed". catlin's ridge is straight and its rafters land square on it, so the
# skewed row is not this joint's row. The 1,060 lb that circulated in the notes until
# 2026-09-14 was the skewed one.
LSSR_SLOPED_HANGER = StructuralHardware(
    tag="simpson-lssr-adjustable-slope-hanger",
    name="LSSR field-adjustable slope/skew hanger",
    role=ROLE_SLOPED_JOIST_HANGER,
    manufacturer=_SIMPSON,
    model="LSSR",
    source="Simpson Strong-Tie LSSR adjustable slope/skew joist and rafter hanger "
           "(strongtie.com/lssr) — the hanger published for a raked member framing into "
           "the face of a ridge beam",
    allowable=AllowableLoads(
        uplift_lb=510.0,
        download_lb=1090.0,
        load_duration_factor=1.0,
        species="The HEADER is a 2-ply 1.75x16 LVL, which ER-280 §3.2.2 puts in the DF/SP "
                "column (\"minimum equivalent specific gravity of 0.50 for engineered "
                "lumber\") and TJ-4000 p. 15's Support Requirements assume outright. The "
                "carried member is an 11-7/8\" TJI 230, not sawn lumber, and that is why "
                "the download below is TJ-4000's and not the catalog's: on an I-joist the "
                "governing number is the JOIST BEARING capacity, not the hanger's steel",
        fasteners="(14) 10d 0.148\" x 3\" into the header and (12) 10d 0.148\" x 1-1/2\" "
                  "into the joist — TJ-4000 p. 15, the TJI schedule. **The catalog's own "
                  "sloped-only rows are nailed differently** and are read at 2-1/2\": "
                  "(14) 0.148 x 1-1/2 = 1,175 lbf, (14) 0.148 x 2-1/2 = 1,565, (14) SD#9 x "
                  "1-1/2 = 1,870 (C-C-2026 p. 178, DF/SP, roof/snow). Web stiffeners are "
                  "REQUIRED with this hanger — 4\" wide, (4) 0.148\" nails each side — and "
                  "beveled rather than square wherever the joist slope exceeds 1/4:12",
        citation="Weyerhaeuser TJ-4000 Specifier's Guide, Jul 2025, p. 15 \"Variable Slope "
                 "Seat Joist Hanger\" — TJI 230 / LSSR2.37Z, **Sloped Only 1,090 lbf** "
                 "(Sloped and Skewed 1,060). Its general note is the reason this record "
                 "carries that number and not C-C's larger one: \"Hanger capacities shown "
                 "are either joist bearing capacity or hanger capacity — whichever is "
                 "less.\" At 100% duration; p. 16 footnote 1 permits +15% for snow roofs "
                 "(1,254 lbf) and +25% for non-snow. Uplift 510 lbf is C-C-2026 p. 178, "
                 "identical in the skewed row. ER-280 Table 11 note 4 bounds the whole "
                 "table at +/-45 degrees of slope AND skew with **no angle multiplier "
                 "inside that range** — the 0.85 above 45 degrees belongs to the LRUZ, and "
                 "CSG-TJUS25 p. 3's sloped-joist reductions belong to ITS/IUS/MIT/MIU/BA/"
                 "HB/WP/HU, hangers with no sloped seat. 6:12 is 26.57 degrees",
    ),
)

LSTA24_RIDGE_STRAP = StructuralHardware(
    tag="simpson-lsta24-ridge-tie-strap",
    name="LSTA24 twist-free strap tie, rafter to rafter over the ridge",
    role=ROLE_RIDGE_TIE_STRAP,
    manufacturer=_SIMPSON,
    model="LSTA24",
    source="Weyerhaeuser TJI roof detail H5S (sloped hanger at a ridge beam, required for "
           "slopes over 3:12) — \"LSTA24 (Simpson or USP) strap with twelve 10d "
           "(0.148\" x 1-1/2\") nails\", 2-3/8\" minimum end distance; APA EWS D710 detail "
           "10c calls for the same strap from 1/4:12 to 12:12. The sloped hanger carries the "
           "rafter's weight into the beam; this carries its tension across the peak.",
)

LUS_FACE_MOUNT_HANGER = StructuralHardware(
    tag="simpson-lus-face-mount-hanger",
    name="LUS face-mount joist hanger",
    role=ROLE_FACE_MOUNT_JOIST_HANGER,
    manufacturer=_SIMPSON,
    model="LUS",
    exposure=EXPOSURE_DRY,
    source="Simpson Strong-Tie LUS/LUS2 face-mount joist hanger family "
           "(strongtie.com/lus) — level joist into the face of a wood carrier",
)
LUSZ_FACE_MOUNT_HANGER = StructuralHardware(
    tag="simpson-lusz-face-mount-hanger",
    name="LUS ZMAX face-mount joist hanger",
    role=ROLE_FACE_MOUNT_JOIST_HANGER,
    exposure=EXPOSURE_TREATED,
    manufacturer=_SIMPSON,
    model="LUSZ",
    source="Simpson Strong-Tie LUS in ZMAX (G185), e.g. LUS28Z (strongtie.com/lus) — the "
           "LUS above where the carrier is preservative-treated, per IRC R317.3.1 and "
           "Simpson's own treated-wood guidance; same stamping and allowables",
)

#: Level I-joist face-mount. Size reads flange/depth: IUS2.56/11.88 takes a 2-1/2" to 2-9/16"
#: flange at 11-7/8", and IUS2.37 the 2-5/16" (TJI 110/210/230) one step down. Not sloped —
#: the roof's raked rafters take the LSSR. No allowable: no table row has been read yet.
IUS_FACE_MOUNT_HANGER = StructuralHardware(
    tag="simpson-ius-ijoist-face-mount-hanger",
    name="IUS face-mount I-joist hanger",
    role=ROLE_IJOIST_FACE_MOUNT_HANGER,
    manufacturer=_SIMPSON,
    model="IUS",
    source="Simpson Strong-Tie IUS face-mount I-joist hanger (strongtie.com/ius) — "
           "nailless-seat hanger for a level I-joist into the face of a wood carrier; "
           "IUS2.56/11.88 is published for 2-1/2\" to 2-9/16\" joist flanges",
)

#: A 2-ply 1 3/4" x 11 7/8" LVL floor-opening header into its LVL trimmer pack. Identity only,
#: like HU28-2Z below: which row of Simpson's SCL face-mount table, and its allowables, have
#: not been transcribed — confirm the HHUS410 row for a 3-1/2" x 11-7/8" member before ordering.
HHUS410_SCL_FACE_MOUNT_HANGER = StructuralHardware(
    tag="simpson-hhus410-scl-face-mount-hanger",
    name="HHUS410 face-mount hanger, 2-ply 1-3/4\" LVL",
    role=ROLE_SCL_FACE_MOUNT_HANGER,
    manufacturer=_SIMPSON,
    model="HHUS410",
    exposure=EXPOSURE_DRY,
    fits_nominal=("2-1.75x11.875 LVL",),
    source="Simpson Strong-Tie HHUS face-mount hanger (strongtie.com/hhus) — HHUS410 for a "
           "3-1/2\" wide structural-composite-lumber member. DIMENSIONS AND ALLOWABLES NOT "
           "YET TRANSCRIBED: read the SCL face-mount table's row before sizing this joint",
)

#: Level open-web floor truss face-mount. THA422: a 4" wide top-flange hanger seat for a
#: flat 2x4 ("4x2") bottom chord, which is exactly FS-S-WEST's chord (3.5"w x 1.5"t) — not
#: the narrower IUS family, which is cut for an I-joist's thin flange. No allowable: no
#: table row has been read yet.
THA_FLOOR_TRUSS_HANGER = StructuralHardware(
    tag="simpson-tha422-floor-truss-hanger",
    name="THA422 top-flange floor truss hanger",
    role=ROLE_FLOOR_TRUSS_HANGER,
    manufacturer=_SIMPSON,
    model="THA422",
    source="Simpson Strong-Tie THA top-flange truss hanger (strongtie.com/tha) — THA422 is "
           "published for a 4\" wide, 2\" (nominal) thick wood floor-truss chord",
)

#: The Simpson C-C masonry/concrete hanger table, read once and cited by all three records
#: below. Page 280 is the only page in the catalog that publishes a hanger load INTO a pour,
#: and everything about which family may be used there comes from it.
#: ** THE PAGE THAT CLOSED THE HURRICANE TIES' SPECIES GAP (2026-09-14). ** Two records in
#: this file said for weeks that "ESR-2613 publishes no SPF column for the hurricane ties,
#: so there is no honest SPF number to record". The first half is TRUE and still is — the
#: report reissued June 2026 governs species globally in §3.2.2 ("assigned minimum specific
#: gravity of 0.50"), with named exceptions only for the SPH (Table 5) and the SSP/DSP
#: (Table 7), and Table 1 has no species columns at all. The second half was FALSE: Simpson's
#: own CATALOG goes past the report and splits the H/TSP table by species, and the SPF/HF
#: column is right there.
#:
#: So the gap was never in the data, it was in which document had been read. Both records now
#: carry the catalog value for the framing they actually land in, and the ESR value stays
#: named beside it as the DF/SP figure — which is what the parts bedded in southern pine
#: (H2.5AZ, H2.5ASS) correctly use.
_C_C_H_TIES = (
    "Simpson Strong-Tie Wood Construction Connectors catalog C-C-2024, p. 288 "
    "\"H/TSP Seismic and Hurricane Ties\", read 2026-09-14. The table is split into "
    "\"DF/SP Allowable Loads\" and \"SPF/HF Allowable Loads\" halves, each with Uplift "
    "(160) and Lateral F1/F2 (160) columns — the species split ICC-ES ESR-2613 does not "
    "publish. Its DF/SP uplift column reproduces the ESR values exactly, which is what makes "
    "the SPF/HF column trustworthy as the same test programme rather than a second opinion. "
    "General Note e: \"For connections involving members with different specific gravities, "
    "use the allowable load corresponding to the LOWEST specific gravity in the connection, "
    "unless noted otherwise\" — and the catalog's species chart assigns DF 0.50, SP 0.55, "
    "SPF 0.42, HF 0.43, LVL (DF/SP) 0.50"
)

_C_C_MASONRY_HANGERS = (
    "Simpson Strong-Tie Wood Construction Connectors catalog C-C-2017, p. 280 "
    "\"HU/HUC/HSUR/L Hangers (cont.)\" — the masonry/concrete table, updated 04/17/17, "
    "read 2026-09-12. Footnote 1: uplift is already increased for wind/earthquake with no "
    "further increase allowed. Footnote 2: minimum f'c = 2,500 psi, minimum f'm = 1,500 psi. "
    "**Footnote 5: \"Products shall be installed such that Titen screws are not exposed to "
    "weather.\"** The table is headed \"Allowable Loads (DF/SP)\" and publishes NO SPF/HF "
    "column for the concrete case"
)

HUC_CONCRETE_HANGER = StructuralHardware(
    tag="simpson-huc-concealed-flange-hanger",
    name="HUC concealed-flange masonry/concrete hanger",
    role=ROLE_CONCRETE_FACE_MOUNT_HANGER,
    manufacturer=_SIMPSON,
    model="HUC",
    source="Simpson Strong-Tie HUC heavy concealed-flange face-mount hanger family "
           "(strongtie.com/huc) — a wood member hung on concrete or grout-filled masonry, "
           "the round header holes taking 1/4\" Titen concrete screws in place of the "
           "16d commons the wood-header table is measured through. **The FAMILY record, "
           "which is all a derived row can honestly name**: ``takeoff/hangers.py`` knows "
           "only \"this resolver-emitted hanger lands on a foundation wall\" and has no "
           "member depth to pick a model from. A house that knows the member authors the "
           "size (\"HUC212-3\"), and ``hardware_by_model`` prefers the exact record. "
           "This took the role from HUCQ on 2026-09-12: see that record for why",
)

#: **Retired from the concrete role, and kept as a capacity record — the retirement IS the
#: finding.** HUCQ was on ``ROLE_CONCRETE_FACE_MOUNT_HANGER`` for two reasons that both
#: turned out to be wrong, and a later reader reaching for it again should meet them rather
#: than a blank.
#:
#: 1. **HUCQ is not in the masonry/concrete table at all.** ``_C_C_MASONRY_HANGERS`` (p. 280)
#:    lists HU and HUC models only. The concrete capacity on that page comes from substituting
#:    the wood table's FACE NAILS with 1/4" Titen screws — and an HUCQ has no nail holes to
#:    substitute: the catalog's own HUCQ rows are fastened "(12) 1/4" x 2-1/2" SDS" to the
#:    header, a Strong-Drive wood screw that ships with the hanger and bites nothing in a pour.
#:    The product page says as much in one line: "for installation to masonry or concrete,
#:    see p. 279".
#: 2. **The seat was a size too narrow.** The four sunken-garden pockets carry a 3-ply 2x12
#:    at 4-1/2" x 11-1/4". HUCQ410-SDS is W 3-9/16" — a 4x seat, and 4x is 3-1/2" — so the
#:    beam was 15/16" wider than the hanger it was billed into. Nothing validates a
#:    ``Connector.size`` against the member it carries, so the model was silent for three
#:    weeks. ``houses/catlin/prices.toml`` half-noticed it and argued the wrong way round
#:    ("still inside the 4x width the -410 designates").
HUCQ_CONCRETE_HANGER = StructuralHardware(
    tag="simpson-hucq-concealed-flange-hanger",
    name="HUCQ concealed-flange hanger (WOOD HEADERS ONLY)",
    role=ROLE_CONCRETE_FACE_MOUNT_HANGER,
    manufacturer=_SIMPSON,
    model="HUCQ",
    source="Simpson Strong-Tie HUCQ concealed-flange hanger (strongtie.com/hucq) — a "
           "heavy concealed-flange hanger installed with Strong-Drive SDS screws supplied "
           "with the hanger. **It is a WOOD-header part.** " + _C_C_MASONRY_HANGERS
           + " lists HU/HUC only; HUCQ appears nowhere on it, and it carries no nail holes "
           "for the Titen substitution that page's loads are built on",
)

#: The triple-2x12 concealed-flange hanger the sunken garden's four beam pockets take.
#:
#: **HUC rather than HU**: both beam ends land in a 6" pocket cast in a 12" wall, so an
#: exposed face flange has nowhere to go — the same reasoning that rejected LUS210 here.
#: **-212-3 rather than -410**: the member is a 3-ply 2x12, 4-1/2" x 11-1/4", and the seat
#: has to be the member's.
#: **The WOOD twin of the record below, added 2026-09-14.** The two share one row of
#: C-C-2017 p. 136 — "HU212-3 / HUC212-3" — and the same 14 ga, W 4-11/16", H 10-5/16"
#: seat for three plies of 2x12. What separates them is the SUBSTRATE, and it is the whole
#: reason both exist: the HUC is a CONCRETE face-mount part (ROLE_CONCRETE_FACE_MOUNT_HANGER,
#: Titen screws into a pour, p. 280) and the HU is nailed into wood.
#:
#: Catlin needs both because its four porch-beam ends now land two different ways. The two
#: OUTER ends sit in 6" pockets in the 12" cast side walls and take the HUC (CN-SG-HGR-W/E).
#: The four INNER ends stop at PT-SG-BF2 / PT-SG-BR2's east and west faces and hang off a
#: 5 1/2" wood post (CN-SG-HGR-C*2-*), which is this part. **The HUC's one advantage over
#: the HU is a concealed flange, and a 5 1/2" post cannot host one** — there is nothing for
#: it to disappear into — so specifying the HUC at the pillar would buy a concrete-only load
#: table and an uninstallable flange at the same time.
#:
#: The plain model string is deliberate: ``hardware_by_model`` is exact-match, and a stray
#: "Z" would silently yield no allowable at all.
#:
#: **The SPF/HF load columns of that row are NOT transcribed here, and that is recorded
#: rather than guessed.** p. 136 was read for the seat dimensions (2026-09-12); its uplift
#: and download columns have not been. Nothing in the engine grades a ``Connector.size``
#: against an allowable, so this omission costs no check — but it is a real gap for anyone
#: sizing this joint, and the APVKB precedent in this file is that an unread or absent row
#: says so in the citation instead of carrying a number nobody sourced.
#: The north entry's two seat beams hang off the 6x6 KDAT canopy columns on these. Owner's
#: call 2026-09-15: **HU28-2Z, not HUC** — an HUC is the concealed-flange twin for screwing
#: into a POUR, and these land on wood. ZMAX (G185) rather than stainless is accepted
#: because the joint is already effectively bearing on the column below it, so a coating
#: failure here is not catastrophic; it is the same reasoning the ABU66SS did NOT get.
#:
#: ** THE ALLOWABLE IS DELIBERATELY UNREAD, WHICH IS A STATEMENT AND NOT AN OMISSION. **
#: ``allowable=None`` is this schema's "nobody has looked yet", distinct from an
#: ``AllowableLoads`` whose values are all ``None`` ("somebody looked, the report published
#: nothing"). The C-C SPF/HF face-mount row for this model has not been read, and
#: transcribing a DF/SP figure in its place is the one error this file's own rule 3 calls
#: out as "an unconservative error that no amount of care downstream can detect" — SPF runs
#: materially below DF/SP on every hanger row. Read p. 136's HU28 row before this joint is
#: sized or installed.
#:
#: It lives in ``CAPACITY_ONLY_RECORDS``, not ``STRUCTURAL_HARDWARE``: the latter would make
#: ``hardware_for_role`` ambiguous for ROLE_FACE_MOUNT_JOIST_HANGER and raise a LookupError,
#: killing every derived hanger row in the house. What it is here FOR is identity — without
#: a record, ``hardware_by_model``'s prefix matching captions the BOM line with whatever
#: family sorts first under "HU".
HU28_2Z_FACE_MOUNT_HANGER = StructuralHardware(
    tag="simpson-hu28-2z-face-mount-hanger",
    name="HU28-2Z face-mount hanger, double 2x8 (ZMAX)",
    role=ROLE_FACE_MOUNT_JOIST_HANGER,
    manufacturer=_SIMPSON,
    model="HU28-2Z",
    fits_nominal=("2-2x8",),
    source="Simpson Strong-Tie HU28-2 in ZMAX (G185) — the WOOD face-mount hanger, nailed "
           "into the 6x6 KDAT column rather than screwed into a pour. Chosen over the HUC "
           "twin by the owner on 2026-09-15 because the carrying member here is wood. "
           "DIMENSIONS AND ALLOWABLES NOT YET TRANSCRIBED: read the C-C SPF/HF face-mount "
           "table's HU28 row before sizing or installing this joint",
)


HU212_3_FACE_MOUNT_HANGER = StructuralHardware(
    tag="simpson-hu212-3-face-mount-hanger",
    name="HU212-3 face-mount hanger, triple 2x12",
    role=ROLE_FACE_MOUNT_JOIST_HANGER,
    manufacturer=_SIMPSON,
    model="HU212-3",
    source="Simpson Strong-Tie HU212-3 — 14 ga, W 4-11/16\", H 10-5/16\", B 2-1/2\" "
           "(C-C-2017 p. 136, the SPF/HF face-mount table, HU212-3 / HUC212-3 row, read "
           "2026-09-12 for the dimensions). W 4-11/16\" takes the 4-1/2\" three-ply seat "
           "with 3/16\" to spare; H 10-5/16\" is the hanger's own height and is not the "
           "member depth. The WOOD twin of HUC212_3_CONCRETE_HANGER: same seat, nailed into "
           "a post instead of screwed into a pour",
    allowable=AllowableLoads(
        fasteners="NOT TRANSCRIBED. The HU family is nailed — the HUC twin's own concrete "
                  "schedule still puts (10) 10d common into the carried member, and on the "
                  "HU the header leg is nailed too rather than screwed into a pour — but "
                  "p. 136's counts for this model have not been read off the page. The "
                  "hanger ships with no fasteners, so a schedule has to come off that table "
                  "before this joint is installed, let alone sized",
        citation="C-C-2017 p. 136, HU212-3 / HUC212-3 row. **The SPF/HF uplift and download "
                 "columns of that row have not been read**; only the seat dimensions have. "
                 "The concrete numbers on the HUC212_3_CONCRETE_HANGER record below are "
                 "p. 280's and are NOT this part's — they are measured through Titen screws "
                 "into a pour. A load for this joint has to come off p. 136 itself",
    ),
)

HUC212_3_CONCRETE_HANGER = StructuralHardware(
    tag="simpson-huc212-3-concealed-flange-hanger",
    name="HUC212-3 concealed-flange hanger, triple 2x12",
    role=ROLE_CONCRETE_FACE_MOUNT_HANGER,
    manufacturer=_SIMPSON,
    model="HUC212-3",
    source="Simpson Strong-Tie HUC212-3 — 14 ga, W 4-11/16\", H 10-5/16\", B 2-1/2\" "
           "(C-C-2017 p. 136, the SPF/HF face-mount table, HU212-3 / HUC212-3 row, read "
           "2026-09-12). W 4-11/16\" takes the 4-1/2\" three-ply seat with 3/16\" to "
           "spare; H 10-5/16\" is the hanger's own height and is not the member depth. "
           "A SEPARATE record from the HUC family above and not a size within it, for the "
           "reason the H2.5ASS is separate: \"HUC212-3\".startswith(\"HUC\") is true, so "
           "without this row a BOM line reading HUC212-3 would be captioned with the "
           "family's name and carry no allowable at all",
    # p. 280, HUC212-3 (Max.) row, CONCRETE columns. The (Min.) row of the same model is
    # (16) screws for 1,135 lbf uplift / 4,920 lbf download; the Max. schedule is recorded
    # because it is what these four pockets are detailed to and the schedule is stated with
    # the number.
    #
    # ** THE DOWNLOAD IS NOT WHAT CARRIES THIS BEAM, AND THE RECORD SHOULD NOT BE READ AS
    # IF IT WERE. ** Each pocket is 6" deep and the beam is 4-1/2" wide, so 27 sq in of the
    # three-ply bears DIRECTLY on the cast sill of the pocket. The hanger's work here is
    # uplift and lateral restraint. See houses/catlin/notes/balcony_differential_movement.md.
    #
    # ** FOOTNOTE 5 IS A LIVE CONDITION, NOT BOILERPLATE. ** "Titen screws are not exposed to
    # weather" — and a pocket in the wall of an open garden is weather unless it is detailed
    # not to be. The condition is carried on the joint, not waved: the pocket is flashed, back-
    # sloped and sealed so the screws sit dry (notes/beam_water_protection.md). Type 316 Titen
    # Turbo exists, but these published loads are measured through the CARBON screw and
    # Simpson's stainless-parity letter (_L_F_SSNAILS) covers connector NAILS, not Titen
    # anchors — so a stainless substitution here would be an unpublished swap, not a free one.
    allowable=AllowableLoads(
        uplift_lb=1800.0,
        download_lb=5085.0,
        load_duration_factor=1.6,  # uplift only; footnote 1. The download is 100/125.
        species="DF/SP — **the masonry/concrete table publishes no SPF/HF column.** The "
                "member here is a 3-ply KDAT 2x12 (southern pine, SG 0.55), which is inside "
                "the column as published; the porch's SPF framing is not, and a later reader "
                "hanging an SPF member in a pour has no number on this page to use",
        fasteners="(22) 1/4\" x 2-3/4\" Titen 2 (TTN2-25234H) into the concrete and (10) "
                  "10d common into the joist — the (Max.) schedule. Titen TTN25234H may "
                  "also be used at full table loads. The (Min.) schedule is (16) screws and "
                  "(6) 10d for 1,135 lbf uplift / 4,920 lbf download",
        citation=_C_C_MASONRY_HANGERS + ". HUC212-3 (Max.) row, Concrete columns: uplift "
                 "1,800 lbf at 160%, download 5,085 lbf at 100/125%",
    ),
)

# **Retired from the knee-brace role, and kept as a capacity record.** It has no published
# allowable load of any kind (the citation below traces the whole chain). The balcony's
# knee braces are its *entire* lateral system —
# `checks/structural/lateral_racking.py` computes the demand — so an unrated connector there
# is not a documentation gap, it is a hole in the load path.
#
# ``KBS1Z_KNEE_BRACE`` below took the role. The rationale, the arithmetic and what it costs
# are in `houses/catlin/notes/balcony_lateral_bracing_design.md`. This record stays because
# deleting it would delete the finding: a later reader reaching for the Outdoor Accents part
# again should meet the report trail, not a blank.
APVKB_KNEE_BRACE = StructuralHardware(
    tag="simpson-apvkb45-6-knee-brace",
    name="Outdoor Accents Avant 45-degree knee brace, 6 in (NOT LOAD-RATED)",
    role=ROLE_KNEE_BRACE,
    manufacturer=_SIMPSON,
    model="APVKB45-6",
    source="Simpson Strong-Tie Outdoor Accents Avant Collection APVKB knee brace "
           "(strongtie.com/apvkb) — 45-degree brace at a post/beam joint",
    # **No published allowable load, and it is not for want of looking.** Traced
    # through the actual evaluation chain rather than a product page:
    #   * IAPMO UES ER-102 (rev. 08/21/2026) is Simpson's stamped/welded connector
    #     cross-reference index. Its "AP" series row enumerates every Outdoor Accents model
    #     covered — APL/APVL, APT/APVT, APA/APVA, APB/APVB in all sizes, APDJT/APVDJT,
    #     APLH, APHH — and points them at ER-280. **APVKB appears nowhere in that index.**
    #   * ER-280 (rev. 04/28/2026), the report ER-102 points to, has no APVKB section, table
    #     or figure. Its knee-brace product is the KBS1Z (§3.1.7, Table 7).
    #   * Simpson's own Outdoor Accents literature tabulates allowable uplift and download
    #     for the Avant post bases (APVB44 1,035/6,725 lbf, APVB66 1,260/11,450 lbf) and
    #     prints no load row for the knee brace at all.
    # So this connector is orderable, fastener-specified and — as far as any code report
    # goes — unrated. That is a real constraint on the balcony's bracing, not a gap in
    # this catalog, and `houses/catlin/notes/balcony_lateral_bracing_design.md` works it
    # through. The 45-degree brace-angle interpolation Simpson publish belongs to the KBS1Z
    # (ER-280 Table 7 footnote 3), not to this part.
    allowable=AllowableLoads(
        fasteners="(4) SDWS22312DBB structural wood screws through (4) STN22 hex-head "
                  "washers, per Simpson's product literature",
        citation=("IAPMO UES ER-102 rev. 08/21/2026 (AP-series index) and ER-280 rev. "
                  "04/28/2026, both read 2026-08-30 — **neither covers APVKB45-4 or "
                  "APVKB45-6**. Simpson's Outdoor Accents load tables publish uplift and "
                  "download for the Avant POST BASES and no load row for the knee brace. "
                  "No allowable load exists to record"),
    ),
)

APVB_BRACE_BOLT = StructuralHardware(
    tag="simpson-outdoor-accents-hex-bolt-1-2",
    name='Outdoor Accents 1/2 in hex-head through bolt with washer, 6 in',
    role=ROLE_BRACE_THROUGH_BOLT,
    manufacturer=_SIMPSON,
    model="APVB12-6",
    source="Simpson Strong-Tie Outdoor Accents hex-head structural bolt + washer "
           "(strongtie.com/outdooraccents) — through-bolts a 2x knee brace at each end",
    # A 1/2 in bolt in double shear through wood is not a *product* with a published
    # allowable — it is an NDS Chapter 12 calculation, and Simpson publish no connector
    # table for it because there is no connector, only a fastener. That is a different kind
    # of "None" from the APVKB above: the number is computable and this catalog is simply
    # the wrong place for it. It is worked in `notes/balcony_lateral_bracing_design.md`
    # §5 from NDS Table 12F, with the group-action factor of Table 11.3.6A.
    allowable=AllowableLoads(
        fasteners="1/2 in dia. HDG hex bolt, 6 in long, with washer, in double shear",
        citation=("no connector evaluation report applies — a through-bolt's lateral "
                  "capacity is NDS 2018 Ch. 12 yield-limit design (Table 12F reference "
                  "values, Table 11.3.6A group action), not a tabulated product rating. "
                  "Worked in houses/catlin/notes/balcony_lateral_bracing_design.md"),
    ),
)

LAPPED_BRACE_BOLT = StructuralHardware(
    tag="hex-bolt-half-by-eight-hdg",
    name='1/2 in x 8 in HDG hex bolt with nut and two washers',
    role=ROLE_LAPPED_BRACE_BOLT,
    manufacturer="generic",
    model="BOLT-12X8-HDG",
    source="generic hot-dip galvanised structural hex bolt to ASTM A307 with an F436 washer "
           "each side — not a proprietary connector, and no manufacturer publishes a "
           "connector rating for one",
    # Why a separate part from APVB12-6 above, which is also a 1/2 in bolt: LENGTH, and it is
    # a dimension the model states rather than a preference. A face-lapped brace foot
    # (KneeBrace.foot_lap) is bolted through the 1 1/2 in brace AND the 5 1/2 in post behind
    # it — 7 in of wood, plus washers and a nut. The Outdoor Accents bolt is 6 in and does not
    # come out the far side. Substituting it would produce a BOM that orders, and a joint that
    # cannot be built.
    #
    # Galvanised rather than the stainless the ABU66SS bases take: this bolt is 4 ft up a
    # painted pillar under a deck, not standing in run-off at grade, and it is not in contact
    # with a stainless part it could drive the corrosion of. The reasoning is the same one
    # POST_BASE_ANCHOR_BOLT records, reaching the opposite answer for a different exposure.
    allowable=AllowableLoads(
        fasteners="1/2 in dia. HDG hex bolt, 8 in long, nut and two F436 washers, through "
                  "a 1 1/2 in lapped brace into a 5 1/2 in post",
        citation=("no connector evaluation report applies — a bolt through a lapped wood "
                  "joint has no product rating, only NDS 2018 Ch. 12 yield-limit design "
                  "(Table 12E for a 1-1/2 in side member, Table 11.3.6A group action) and "
                  "the end/edge/spacing rules of Table 12.5.1. Worked in "
                  "houses/catlin/notes/balcony_lateral_bracing_design.md"),
    ),
)

MASA_MUDSILL_ANCHOR = StructuralHardware(
    tag="simpson-masa-mudsill-anchor",
    name="MASA mudsill anchor",
    role=ROLE_MUDSILL_ANCHOR,
    manufacturer=_SIMPSON,
    model="MASA",
    source="Simpson Strong-Tie MASA mudsill anchor (strongtie.com/masa) — cast into the "
           "top of a concrete or ICF wall to anchor the sill plate",
    # ESR-2555 Table 1, STANDARD INSTALLATION / 2x4, 2x6 / uncracked concrete / Wind and
    # SDC A&B. Two choices in reading this table are worth stating:
    #   * **Uncracked** is recorded (920 vs 750 lbf uplift cracked). A sill plate at the top
    #     of a wall is in the compression zone and away from flexural cracking; if a reviewer
    #     disagrees the cracked column is one line away in the same table.
    #   * **Wind and SDC A&B**, not SDC C-F: Minnesota is SDC A/B.
    # The species caveat below is the real one. §3.2.3 requires SG >= 0.50 lumber, and this
    # house's sill plates are SPF (SG 0.42). The tabulated values therefore do NOT apply
    # as-is here, which is exactly why `species` records what the report says rather than
    # what the house builds.
    allowable=AllowableLoads(
        uplift_lb=920.0,
        lateral_f1_lb=1475.0,
        lateral_f2_lb=1095.0,
        load_duration_factor=1.6,
        species="DF/SP or better — §3.2.3 requires assigned SG >= 0.50; catlin's SPF "
                "sill plates are SG 0.42 and these values do not apply to them unreduced",
        fasteners="3 - 10d x 1.5 in each side leg + 6 - 10d x 1.5 in top, "
                  "strap cast into the wet concrete",
        citation=("ICC-ES ESR-2555 (MASA/MASAP foundation anchor straps) Table 1, standard "
                  "installation, 2x4/2x6 sill, uncracked concrete, Wind and SDC A&B; §3.2.3 "
                  "for the SG >= 0.50 requirement. Read 2026-08-30"),
    ),
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
    # **A ladder, not a number, and the model does not carry the rung.** ESR-2105 Table 4
    # publishes the CS16 at 1,890 lbf with 20 - 10d x 2-1/2 in common nails, or 1,725 lbf
    # with 22 - 8d common, against a steel strength of 1,705 lbf — and footnote 1 requires
    # half the total in each member. The allowable is therefore a function of how many nails
    # are actually driven, and `takeoff/anchors.py::coil_strap_rows` bills coils by LENGTH.
    # Nothing in this model says how many nails go in a given strap.
    #
    # Recording 1,890 anyway would be the single most tempting error available in this file:
    # it is a real published number, from the right report, for the right part, and it would
    # be wrong for any strap nailed with fewer than 20 nails — which is to say, wrong for
    # every strap in this house, because none of them has a nail count at all. So the load
    # stays None and the citation carries the ladder for whoever adds nail counts later.
    allowable=AllowableLoads(
        fasteners="by nail count — 20 - 10d x 2-1/2 in common or 22 - 8d common, half in "
                  "each connected member (ESR-2105 Table 4 footnote 1); the model carries "
                  "no nail count for a coil strap",
        citation=("ICC-ES ESR-2105 (CS/CMST coil straps) Table 4, read 2026-08-30: CS16 "
                  "1,890 lbf at 20-10d x 2-1/2 common, 1,725 lbf at 22-8d common, steel "
                  "strength 1,705 lbf, all at SG >= 0.50 (footnote 2). No single value is "
                  "recorded because the allowable is selected by a nail count this model "
                  "does not track, and the species basis is SG 0.50 against this house's SPF"),
    ),
)

#: ICC-ES ESR-1622, the ABU family's evaluation report.
_ESR_1622 = "ICC-ES ESR-1622 (Simpson Strong-Tie post base connectors), Table 2, read 2026-08-30"

#: **The letter that rates every stainless connector in this file.** Simpson engineering
#: letter L-F-SSNAILS, read 2026-09-11 from the Simpson technical-notes PDF: a stainless
#: connector carries the CARBON connector's published allowable loads. The one mechanism
#: that reduces them is nail withdrawal — the USDA Forest Products Laboratory found
#: stainless SMOOTH-shank nails withdraw less than carbon smooth-shank ones — and the letter
#: gives a substitution chart that buys the full carbon values back with Strong-Drive SCNR
#: Type 316 ring-shank connector nails. The relevant rows here:
#:
#:     8d common  0.131 x 2-1/2 in  ->  SSA8D  (hand-drive) / T10A250MCN (collated)
#:     16d common 0.162 x 3-1/2 in  ->  SSA16D (hand-drive)
#:
#: This is why two records below stopped saying "unrated". It also explains the lower
#: figures that were in circulation for the H2.5ASS and could not be tied to a report: a
#: 440/75/70 row IS a real Simpson table — the stainless SMOOTH-shank one — and it is the
#: number you get if you nail the part with the wrong stainless nail.
#:
#: ** TWO CONDITIONS RIDE WITH IT, AND NEITHER IS OPTIONAL. **
#:   1. The letter's own first line: "Simpson Strong-Tie stainless-steel connectors are
#:      required to be installed using stainless-steel fasteners." Every bolt, screw and
#:      nail at a stainless connector is stainless, not only the nails in the chart.
#:   2. **The copy read is L-F-SSNAILS23 and it states its own expiry: "valid until
#:      12/31/2024, when it will be re-evaluated by Simpson Strong-Tie."** It is 21 months
#:      past that date. No later revision could be retrieved on 2026-09-11. The parity is
#:      recorded because it is the manufacturer's own statement about its own part and is
#:      the thing the older "unrated" note asked for, but a submittal should pull the
#:      current letter rather than this one.
_L_F_SSNAILS = ("Simpson Strong-Tie engineering letter L-F-SSNAILS23 (1 Jan 2023), read "
                "2026-09-11: a stainless connector carries the carbon connector's published "
                "allowables; only stainless SMOOTH-shank nails reduce them, and the letter's "
                "Nail Substitution Chart restores full values with Strong-Drive SCNR Type "
                "316 ring-shank nails. **The letter states it is valid until 12/31/2024** "
                "and no later revision could be retrieved — re-pull it for a submittal")

ABU_POST_BASE = StructuralHardware(
    tag="simpson-abu66-standoff-post-base",
    name="ABU66 standoff post base (6x6)",
    role=ROLE_POST_BASE,
    manufacturer=_SIMPSON,
    model="ABU66",
    fits_nominal=("6x6",),
    source="Simpson Strong-Tie ABU adjustable standoff post base (strongtie.com/abu) — "
           "1 in standoff keeps the post end off the wet slab",
    #: 1 3/16": Simpson's published 1" of clear standoff plus the 7 ga (0.1793") base plate
    #: it is measured above, which is what actually bears on the pour. See
    #: ``ABU66SS_POST_BASE`` for the full note — the two records are the same stirrup in two
    #: steels and the geometry does not change with the coating.
    bearing_standoff_in=1.0 + 0.1793,
    # ESR-1622 Table 2, ABU66 row, verbatim. Two uplift values are published and footnote 4
    # says they "are not cumulative" — 2,475 lbf through the twelve 16d nails into the post,
    # 2,190 lbf through the two 1/2 in bolts. **The lower one is recorded**: this house bolts
    # its bases (the through-bolt is what a stainless stirrup at grade wants), and a base
    # carrying the nailed number while installed with bolts is over-rated by 13 %.
    #
    # No F1/F2 row exists for the ABU family. ESR-1622 §2.0 says the products "are used to
    # resist lateral and net induced uplift forces", and Table 2 then tabulates uplift and
    # download only — the lateral values in this report belong to the CPTZ (Table 4), a
    # different product. So the lateral fields stay None, and any lateral demand on an ABU is
    # an unanswered question rather than a comparison against 2,190.
    allowable=AllowableLoads(
        uplift_lb=2190.0,
        download_lb=18205.0,
        load_duration_factor=1.6,   # uplift; the download is published at C_D 1.0/1.15/1.25
        species=None,               # the report tabulates by connector, not by lumber species
        fasteners="12-16d into the post, 2 - 1/2 in bolts through the post, "
                  "1 - 5/8 in cast-in anchor bolt (anchor bolt by others)",
        citation=(_ESR_1622 + "; uplift 2,475 lbf by nails / 2,190 lbf by bolts (footnote 4: "
                  "not cumulative — the bolted value is recorded here), download 18,205 lbf. "
                  "§5.6: the anchor bolt and footing design are outside the report's scope"),
    ),
)

#: **The stainless ABU carries the galvanised ABU's numbers, and it took a letter rather
#: than a code report to say so (2026-09-11).** ESR-1622 genuinely does not cover it —
#: §3.2.1 evaluates connectors "fabricated from galvanized steel in accordance with ASTM
#: A653" and Table 2 lists ABU44Z/44RZ/46Z/46RZ/5-5Z/5-6Z/65Z/66Z/66RZ/88Z/88RZ/1010Z/
#: 1010RZ/1212Z/1212RZ, every one of them the Z, none of them stainless. So the retailer
#: listings that cite ESR-1622 for this part are still citing a report that does not cover
#: it, and this record is still separate from ``ABU_POST_BASE`` for that reason.
#:
#: What changed is that the old note asked for exactly one thing — "a stainless allowable
#: has to come from Simpson directly, not from the ABU66 row" — and ``_L_F_SSNAILS`` is
#: Simpson saying it directly. The letter's parity is unconditional on the STEEL; the only
#: reduction it names is stainless smooth-shank nail withdrawal. **These ten bases are
#: BOLTED**, 2 - 1/2" through the post, and the governing uplift value recorded below is the
#: bolted one, so the nail mechanism does not touch it at all. The 16d nails that also go
#: into the post are specified SSA16D anyway, per the letter's chart and its first line.
#:
#: It stays in ``CAPACITY_ONLY_RECORDS`` rather than ``STRUCTURAL_HARDWARE``, so no BOM line,
#: role lookup or ``hardware_by_model`` result moves because of this change either.
#: ``ABU_POST_BASE`` still serves ROLE_POST_BASE at 6x6, exactly as before.
ABU66SS_POST_BASE = StructuralHardware(
    tag="simpson-abu66ss-standoff-post-base",
    name="ABU66SS standoff post base (6x6), 316L stainless",
    role=ROLE_POST_BASE,
    manufacturer=_SIMPSON,
    model="ABU66SS",
    fits_nominal=("6x6",),
    source="Simpson Strong-Tie ABU66SS stainless adjustable post base "
           "(strongtie.com/abu) — the stainless variant of the ABU66, specified here "
           "because these ten bases stand at grade in a wet location",
    # The ABU66's own row, carried across by L-F-SSNAILS. The BOLTED uplift is recorded for
    # the same reason it is on the galvanised record: this house bolts its bases, footnote 4
    # says the nailed and bolted values are not cumulative, and a base carrying the nailed
    # 2,475 while installed with bolts is over-rated by 13%. Lateral stays None — ESR-1622
    # publishes no F1/F2 row for the ABU family in either steel, and parity cannot conjure a
    # number that does not exist on the carbon side.
    #: ** THE STANDOFF IS 1 3/16", NOT 1" (2026-09-14). ** Simpson publish the ABU's
    #: standoff as 1", and that 1" is the clear air between the base plate and the post —
    #: it does not include the plate the whole stirrup sits on. The plate is 7 gauge,
    #: 0.1793", and it bears on the pour, so the wood starts 1.1793" above the concrete.
    #: Both terms are written out because the published number is the 1" and a reader
    #: checking this against the catalog has to see where the rest came from.
    #:
    #: What it buys: this is the R317.1.4 Exception 1/3 standoff itself — the reason an
    #: untreated post end may stand on concrete at all — and it is 1 3/16" of post length
    #: that IRC Table R507.4 does not cap, a mill does not cut and a take-off should not
    #: bill.
    bearing_standoff_in=1.0 + 0.1793,
    allowable=AllowableLoads(
        uplift_lb=2190.0,
        download_lb=18205.0,
        load_duration_factor=1.6,   # uplift; the download is published at C_D 1.0/1.15/1.25
        species=None,               # the report tabulates by connector, not by lumber species
        fasteners="12-SSA16D stainless ring-shank into the post (the letter's substitution "
                  "for the catalog's 16d common), 2 - 1/2 in STAINLESS bolts through the "
                  "post, 1 - 5/8 in stainless cast-in anchor bolt (AB-058-10-SS). Every "
                  "fastener at a stainless connector is stainless — L-F-SSNAILS, line 1",
        citation=(_L_F_SSNAILS + ". The values are the ABU66 row of " + _ESR_1622 +
                  "; ABU66SS is NOT in that table and the parity is the letter's, not the "
                  "report's. §5.8 still puts the anchor bolt and the concrete support "
                  "outside scope, in either steel"),
    ),
)

#: ICC-ES ESR-2330, Table 4, read 2026-09-03. Note the number: the DTT2's report is **2330,
#: not 2320** — ESR-2320 is Simpson's take-up device report (CTUD/TUD/ATUD/RTUD/TUW) and has
#: no DTT in it at all. That was worth checking rather than copying.
#: ICC-ES ESR-2105 (Simpson Strong-Tie straps), Table 3 — the LSTA/MSTA/LSTI/MSTI series —
#: and ICC-ES ESR-3096 (framing connectors), Table 4 — the L reinforcing angles. Both read
#: 2026-09-03 from the ICC-ES PDFs, not from a retail listing.
# THE BASE TIE AT PT-SG-BR2 / PT-SG-BF2 — a strap plus angles, NOT a cap.
#
# ** WHY NOTHING THAT WRAPS THE JOINT WORKS HERE. ** Three parts stood at this joint before
# and all three were wrong; the third was not merely oversized, it could not be installed:
#
#   * **ABU66SS — unrated.** Every published number an ABU has is measured with the stirrup
#     bearing on concrete through a 5/8" cast-in anchor, and ESR-1622 §5.6 puts that anchor
#     and its footing outside its own scope. On a deck there is no pour, no cast-in bolt and
#     no basis for the table; §3.2.1 evaluates galvanised steel and lists no stainless model
#     at all. Its 1" standoff answered IRC R317.1.4 Exception 1/3, which governs a wood
#     column on CONCRETE. Wood on wood is not that condition.
#   * **DTT2Z — right family, wrong shape.** ESR-2330 §3.2.1 does cover the -Z suffix, and
#     Simpson do publish a DTT2 for a post on framing. But it is one-sided: eccentric on a
#     6x6, needing a 1/2" rod driven through the joist pack to a nut in the beam bay, and
#     contributing nothing lateral at a base that is pinned by design. Authored and
#     superseded the same day, unbuilt.
#   * **CCQ4.62-5.50SDS inverted — DOES NOT FIT, at either pillar.** The resolved geometry
#     says so plainly. At PT-SG-BF2 the rim, the joist tips, the beam axis and the post
#     centre are all one line — a T, with no orientation for a channel. At PT-SG-BR2 the
#     squash blocks sit in the bays flanking the 3-ply pack, exactly where an inverted
#     channel's side plates must hang. It also carried 6,785 lbf against a demand around
#     300-600 lbf, and ESR-2604 evaluates no inverted installation. Never buildable here.
#
# ** WHAT THE DEMAND ACTUALLY IS. ** ``structural.uplift_capacity`` is an honest UNKNOWN at
# this joint — no tributary area, no force coefficient, no share of the storey shear. From
# the house's own wind basis (typehaus/wind.py, V_ult 115, Exposure B): q_h ~16.5 psf at
# 15 ft, free-roof C_N ~1.2, 0.6 for ASD -> ~11.9 psf over ~48 ft2 = ~575 lb up, less 0.6D
# ~290 lb -> **~285 lb net**. Call the design demand 300-600 lbf. That is the yardstick the
# two parts below are sized against, and it is why a 6,785 lbf cap was ~20x the joint.
#
# ** MIXED BY WHAT EACH FACE HAS BESIDE IT. ** The strap goes on the one flush vertical pair
# in the joint: the post's west face and the pack's west face are both at x = 213.25" at
# BOTH pillars, so a 12" strap lies flat across the joint with 6" in each member. The east
# face has a 1" step and takes nothing. The angle earns its place only where there is pack
# beside the post to screw into — the north face at both pillars, and the south face at
# PT-SG-BR2 only. The E/W faces offer 1-1/2" of block and would be fiction; **do not author
# angles there.** Totals against a 300-600 lbf demand: BR2 1,408 lbf, BF2 1,033 lbf.
#
# ** REJECTED. ** Four angles (do not fit); L70Z (7" legs overhang the 4-1/2" pack by
# 1-1/4" each side); GA2 (ESR-3096 Table 3 publishes the same 535/820, but there is no ZMAX
# or HDG variant and this pack is copper-treated KDAT); H8 (footnote 7 derates the
# stud-to-bottom-plate case — the one closest to a post on framing — to 380 lbf, with 85 lbf
# F1 and no F2).
#
# ** THE WET SERVICE FACTOR IS APPLIED, NOT DEFERRED. ** ESR-2105 §4.1 and ESR-3096 §4.1 say
# the same thing in the same words: where wet service is expected the allowable loads "must
# be adjusted by the wet service factor, C_M, specified in the NDS" for dowel-type
# fasteners. An open deck frame IS that condition, so C_M 0.70 is taken here and the derated
# number is what these records carry. This is the resolvable half of the moisture question;
# unlike the 19% clause below it does not ride on the seal.
#
# ** THE SPECIES CLAUSE IS FAMILY-WIDE. ** ESR-2105 §3.5.2 and ESR-3096 §3.2.2 are the same
# sentence as ESR-2604/ESR-2330 §3.2.2 — sawn or engineered lumber, SG >= 0.50, MC <= 19%.
# POST_WHITE_PAINT_DF's reason therefore survives the part change intact; only the citation
# widens. The 19% half is still not met by an open deck frame and stays with the record.
MSTA12Z_POST_TENSION_STRAP = StructuralHardware(
    tag="simpson-msta12z-post-base-strap",
    name="MSTA12Z strap, 6x6 post to the joist pack under it (west face)",
    role=ROLE_POST_TENSION_TIE,
    manufacturer=_SIMPSON,
    model="MSTA12Z",
    fits_nominal=("6x6",),
    source="Simpson Strong-Tie MSTA medium strap tie, No. 18 gage, 12 in long, G185 (the Z "
           "suffix). Face-nailed flat across the ONE flush vertical pair at this joint: "
           "the 6x6's west face and the 3-ply 2x8 pack's west face are coplanar at both "
           "centre pillars, 6 in of strap into each member. Chosen over a cap because both "
           "pillars bear on porch deck FRAMING, where nothing that wraps the joint fits",
    allowable=AllowableLoads(
        uplift_lb=658.0,
        load_duration_factor=1.6,
        species="DF-L, SG 0.50 — specified for these two pillars to meet §3.5.2; the "
                "19 percent moisture-content half of that clause is NOT met",
        fasteners="10 - 10d x 2-1/2 in common nails, 5 into each member (ESR-2105 Table 3 "
                  "footnote 1). Hot-dip galvanised nails with the G185 strap. In the pack "
                  "the 2-1/2 in nail crosses the 1-1/2 in outer joist and lands 1 in into "
                  "the first sister, so two of the three plies are engaged",
        citation=("ICC-ES ESR-2105 (Simpson Strong-Tie straps), Table 3, MSTA12 row — read "
                  "2026-09-03. **THE PUBLISHED NUMBER IS 940 lbf** allowable tension at "
                  "C_D 1.6 (the table's only column; footnotes 3-4 say connection strength "
                  "governs and that the C_D is already in it, so no further duration "
                  "increase applies). 940 carries no footnote 5, i.e. the nails govern and "
                  "not the steel, which is exactly the case §4.1's wet service clause bites "
                  "on: 'where wet service is expected, the allowable tension loads based on "
                  "fastener lateral design values ... must be adjusted by the wet service "
                  "factor, C_M, specified in the NDS'. C_M 0.70 for dowel-type fasteners "
                  "gives **940 x 0.70 = 658 lbf**, and 658 is the value recorded above — "
                  "the derate is applied here, not deferred to the seal. NO LATERAL VALUE: "
                  "Table 3 publishes tension only, so lateral_f1/f2 are left None rather "
                  "than invented; the L50Z angles beside this strap are what carry lateral "
                  "at this base. §3.5.2 conditions the value on SG >= 0.50 at MC <= 19 "
                  "percent AND on a main member at least as thick as the fastener is long "
                  "(2-1/2 in; the pack is 4-1/2 in and the post 5-1/2 in, both met). The SG "
                  "half is met only because these two pillars are specified DF-L rather "
                  "than the house's SPF; the moisture half is not met by an open deck frame "
                  "and rides on the seal. §3.5.1: the Z suffix IS the G185 coating, stated "
                  "in the report rather than inferred from a catalog page"),
    ),
)

L50Z_POST_TENSION_ANGLE = StructuralHardware(
    tag="simpson-l50z-post-base-angle",
    name="L50Z reinforcing angle, 6x6 post to the joist pack beside it",
    role=ROLE_POST_TENSION_TIE,
    manufacturer=_SIMPSON,
    model="L50Z",
    fits_nominal=("6x6",),
    source="Simpson Strong-Tie L reinforcing angle, No. 16 gage, 5 in legs, G185 (the Z "
           "suffix). One leg on the 6x6, one on the top of the 3-ply 2x8 pack, only on the "
           "faces where there IS pack beside the post: north at both centre pillars, south "
           "at PT-SG-BR2 alone. The 5 in leg sits inside the pack's 4-1/2 in width with "
           "1/4 in over each edge; an L70Z's 7 in leg would overhang it by 1-1/4 in each "
           "side. It is here for the N-S lateral at a base the notes call pinned, which a "
           "strap in tension does not carry",
    allowable=AllowableLoads(
        lateral_f1_lb=375.0,
        lateral_f2_lb=574.0,
        load_duration_factor=1.6,
        species="DF-L, SG 0.50 — specified for these two pillars to meet §3.2.2; the "
                "19 percent moisture-content half of that clause is NOT met",
        fasteners="6 - SD9112 Strong-Drive SD Connector screws (#9 x 1-1/2 in), 3 per leg "
                  "(ESR-3096 §3.2.3, the screws themselves evaluated in ESR-3046). The "
                  "1-1/2 in screw is inside both members: 5-1/2 in post, 4-1/2 in pack",
        citation=("ICC-ES ESR-3096 (Simpson Strong-Tie framing connectors), Table 4, L50 "
                  "row — read 2026-09-03. **PUBLISHED: F1 535 lbf and F2 820 lbf, both at "
                  "C_D 1.6**, already duration-adjusted, and footnote 1 forbids adjusting "
                  "them for any other duration. §4.1's wet service clause is word for word "
                  "ESR-2105 §4.1's — where wet service is expected the allowables 'must be "
                  "adjusted by the wet service factor, C_M, specified in the NDS' — so "
                  "C_M 0.70 for dowel-type fasteners gives **F1 535 x 0.70 = 375 lbf** and "
                  "**F2 820 x 0.70 = 574 lbf**, which are the values recorded above. NO "
                  "UPLIFT VALUE: Table 4 publishes F1 and F2 only, and footnote 2 forbids "
                  "combining even those two, so uplift_lb is left None — the MSTA12Z beside "
                  "it is the uplift part. TWO CONDITIONS RIDE WITH THESE NUMBERS: footnote "
                  "3 requires the terminating member to be constrained against rotation for "
                  "F1 where the angles are not used in pairs, and footnote 5 requires "
                  "angles on BOTH sides of the terminating member to resist F2 in both "
                  "directions — PT-SG-BF2 carries a north angle only and earns no two-way "
                  "F2 on that account. §3.2.2 conditions the values on SG >= 0.50 at MC <= "
                  "19 percent (SG met by the DF-L specification, moisture not met by an "
                  "open deck frame) and on member thickness >= fastener length. §3.2.1: the "
                  "Z suffix IS the G185 coating, and it also directs that the lumber "
                  "treater's own recommendations govern corrosion resistance with a "
                  "specific proprietary preservative — this pack is copper-treated KDAT"),
    ),
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
    #: The family's 1" standoff over its own 7 ga base plate, as on the ABU66 records. The
    #: standoff is the reason this part is at PT-BW-IC/-IE at all — that corner of the
    #: garage floor is not dry — so it would be odd to carry the part and not its dimension.
    bearing_standoff_in=1.0 + 0.1793,
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
    # **ESR-1622 §5.6, verbatim: "The design of anchor bolts and the concrete footings is
    # outside the scope of this report."** Table 2 footnote 3 says the same thing from the
    # other side — the bolt and footing "must be capable of resisting all loads and forces
    # transferred from the post base connector". So the report that gives the ABU its 2,190
    # lbf explicitly declines to say whether the bolt it is measured through can deliver it.
    #
    # That is not an oversight: a cast-in anchor's capacity is a concrete-breakout and
    # pullout calculation under ACI 318 Ch. 17, and it depends on f'c, embedment, edge
    # distance and whether the concrete is cracked — four facts about the FOOTING, none of
    # them a property of the bolt. It is the one link in the post-base chain that cannot be
    # answered by any product table, and leaving it None is the whole reason this record is
    # here rather than absent.
    allowable=AllowableLoads(
        fasteners="5/8 in dia. x 10 in cast-in bolt with nut and plate washer, 304 stainless",
        citation=("ICC-ES ESR-1622 §5.6 and Table 2 footnote 3, read 2026-08-30: anchor "
                  "bolt and footing design are expressly OUTSIDE the report's scope. The "
                  "capacity of this link is an ACI 318 Ch. 17 concrete-anchorage design "
                  "(breakout and pullout, from f'c, embedment, edge distance and cracked/ "
                  "uncracked state), not a product rating"),
    ),
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

# A 3-1/2" beam landing on a 6x6 post — the catlin balcony's two CENTRE pillars, where the
# other four columns are cast concrete and take an HGAM10 masonry gusset instead. NOT the
# PC6Z above: that cap is published for EQUAL post and beam widths, and a 3-1/2" glulam on a
# 5-1/2" post is not that joint. The CCQ is the column cap made for the unequal case, with
# the beam seat sized to the member rather than to the post.
#
# It is what closes ``checks/structural/uplift_path``'s post-to-beam leg at those two joints:
# both centre pillars bear on the porch FRAMING (since 2026-09-03 — see
# params/sunken_garden.py and engineering/post_bearing.py), so unlike the cast columns there
# is no doweled lap in a pour to hold the beam down, and the cap is the hold-down.
#
# ** READ THE SPECIES CONDITION BELOW BEFORE QUOTING THIS PART'S NUMBER. ** ESR-2604 §3.2.2
# governs every connector in this report, and it is not met by catlin's frame.
CCQ46SDS_POST_CAP = StructuralHardware(
    tag="simpson-ccq46sds25-column-cap",
    name="CCQ46SDS2.5 column cap (4x beam on 6x6 post)",
    role=ROLE_POST_CAP,
    manufacturer=_SIMPSON,
    model="CCQ46SDS2.5",
    fits_nominal=("6x6",),
    source="Simpson Strong-Tie CCQ column cap (strongtie.com/ccq) — the SDS-screw CCQ "
           "seating a nominal 4x (3-1/2 in) beam on a 6x6 post, factory-supplied with "
           "1/4 in x 2-1/2 in SDS Heavy-Duty Connector screws; selected over the PC6Z "
           "because that cap is published for equal post and beam widths",
    #: The cap's SEAT is 7 gauge, 0.1793", and it lies between the post top and the beam
    #: soffit — so the post is that much shorter than the clear distance to the member it
    #: carries. The same 7 ga as the ABU's base plate at the other end of these posts, and
    #: for the same reason it matters: together the two take a 6x6 on a base and a cap
    #: 1 3/8" below the clear height, which is what R507.4 caps and what a mill cuts.
    seat_thickness_in=0.1793,
    # ICC-ES ESR-2604 Table 2, CCQ46SDS2.5 row, re-read 2026-09-03 against the PDF.
    #
    # ** THE NUMBERS HERE WERE WRONG UNTIL THAT RE-READ. ** This record carried 3,285 lbf
    # uplift and 1,670 lbf lateral, attributed to an "SPF/HF column" of the CCQ table.
    # Table 2 HAS NO SPECIES COLUMNS — its four load columns are CCQ/ECCQ uplift and
    # CCQ/ECCQ download — and it publishes NO LATERAL VALUE FOR THE CCQ SERIES AT ALL
    # (lateral is tabulated only for the AC/ACE/ACH, LPC, PC/EPC and BC/BCS caps, Tables
    # 3-6). Neither 3,285 nor 1,670 appears anywhere in the report. ``lateral_f1_lb`` is
    # left None deliberately: absence is the fact, per AllowableLoads' own docstring.
    allowable=AllowableLoads(
        uplift_lb=6_785.0,
        load_duration_factor=1.6,
        species="NOT MET BY THIS HOUSE — see citation; the table is not species-indexed",
        fasteners="factory-supplied 1/4 in x 2-1/2 in SDS Heavy-Duty Connector screws, "
                  "16 into the BEAM and 14 into the POST (Table 2's own two columns; "
                  "this record previously said 16 and 8)",
        citation=("ICC-ES ESR-2604 (Simpson Strong-Tie column caps and post caps), "
                  "Table 2, CCQ46SDS2.5 row — read 2026-09-03. Uplift 6,785 lbf at "
                  "C_D 1.6 (already carries the wind/seismic increase; no further "
                  "duration increase applies), download 24,065 lbf at C_D 1.0. "
                  "THE CONDITION THAT RIDES WITH IT, and it is not met as catlin frames "
                  "today: §3.2.2 requires the wood members to be sawn or engineered "
                  "lumber of specific gravity >= 0.50 at a maximum moisture content of "
                  "19 percent, and these pillars are SPF at 0.42 standing open to the "
                  "weather. The report carries no reduction factor to SPF for this "
                  "series, so there is no published value for the joint as built — the "
                  "same gap ESR-1622 leaves for the ABU66SS above. Note also that "
                  "ESR-2604 says nothing about installing a CCQ inverted, so the "
                  "cap-at-the-top orientation used here is the tabulated one and any "
                  "base-side use of this family would be outside the report's figures."),
    ),
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
    exposure=EXPOSURE_DRY,
    source="Simpson Strong-Tie H2.5A tie (strongtie.com/h25a) — rafter/joist-to-plate "
           "uplift connection. **G90 zinc, so DRY wood contact only.** It took every "
           "derived bearing tie in the house until 2026-09-12, including the twenty-four "
           "on the sunken garden's treated frame, because the role held one product and "
           "``hardware_for_role`` could not ask a second question. H25AZ_HURRICANE_TIE "
           "below is that joint\'s part; this one keeps the ~270 dry ones",
    # ESR-2613 Table 1, H2.5A row. **The lateral values are the ones to notice: 110 lbf,
    # against 700 lbf uplift.** A check that compared a lateral demand against "the H2.5A's
    # 700 lb capacity" would pass a joint six times overloaded, which is precisely why
    # AllowableLoads is a vector. Footnote 2 goes further and requires a unity equation
    # across all three directions when a joint sees more than one at once.
    #
    # ** 700 -> 615 ON 2026-09-14: THE SPF NUMBER EXISTS AND THIS RECORD SAID IT DID NOT. **
    # It read: "Simpson do not print an SPF column for the hurricane ties the way they do for
    # the KBS1Z and the HGAM10, so there is no honest SPF number to record here." Half of that
    # was right. ESR-2613 has no species columns at all and governs species globally in
    # §3.2.2 at SG 0.50 — true, and true again in the June 2026 reissue. But Simpson's own
    # CATALOG splits the H/TSP table by species, and the SPF/HF uplift for this tie is **615
    # lbf at 160%**. The gap was in which document had been read, not in the data.
    #
    # **So this record now carries the SPF value**, which is the convention ``species``
    # already states: where the report gives both, record the column this house is built in.
    # The DF/SP 700 stays named in the species field, because it is the right number for the
    # same stamping bedded in southern pine — which is exactly what the H2.5AZ and H2.5ASS
    # records below are for, and why theirs did NOT move.
    #
    # It is 12% down, and the direction matters: every derived tie in this house was being
    # graded against a capacity 85 lbf higher than the framing can develop.
    #
    # **Do not derive this by factoring.** Simpson's General Note e sends a mixed-species
    # joint to the LOWEST specific gravity in it — here the SPF plate at 0.42, under an I-joist
    # flange at ~0.50 — and the only published multiplier on this page (0.86) belongs to the
    # stud-to-bottom-plate detail alone. NDS Table 12.3.3 governs individual fasteners, not a
    # tested proprietary connector whose capacity is part steel. A species Simpson does not
    # rate at all goes to their letter L-ALTSPECIES, not to arithmetic of ours.
    allowable=AllowableLoads(
        uplift_lb=615.0,
        lateral_f1_lb=110.0,
        lateral_f2_lb=110.0,
        load_duration_factor=1.6,
        species="SPF / HF (assigned SG 0.42 / 0.43) — the column this house is framed in, "
                "and the reason the value is 615 rather than the 700 lbf the same tie "
                "carries in DF-L / SP (SG 0.50 / 0.55). ESR-2613 publishes only the DF/SP "
                "figure; the SPF/HF column is the catalog's",
        fasteners="5 - 0.131 in x 2-1/2 in to the rafter and 5 - 0.131 in x 2-1/2 in to "
                  "the plates (ESR-3096 Table publishes 625/450/110 lbf for the same tie "
                  "with 5-SD9112 screws each side — a different fastener, different values)",
        citation=(_C_C_H_TIES + ". The SPF/HF uplift is 615 lbf; the DF/SP half of the same "
                  "row reads 700 lbf and reproduces ICC-ES ESR-2613 (Simpson hurricane ties) "
                  "Table 1, H2.5A row, read 2026-08-30 — where footnote 2 requires a unity "
                  "check across uplift + both lateral directions for simultaneous loading "
                  "and footnote 5 states the uplift is already increased for wind with no "
                  "further increase allowed. The lateral F1/F2 do not move with species on "
                  "this page: 110 lbf in both halves"),
    ),
)

H25AZ_HURRICANE_TIE = StructuralHardware(
    tag="simpson-h2-5az-hurricane-tie",
    name="H2.5AZ ZMAX hurricane/seismic tie",
    role=ROLE_HURRICANE_TIE,
    exposure=EXPOSURE_TREATED,
    manufacturer=_SIMPSON,
    model="H2.5AZ",
    source="Simpson Strong-Tie H2.5AZ — the H2.5A above in ZMAX, Simpson\'s G185 "
           "hot-dip-galvanized-after-fabrication coating (strongtie.com/h25az). **The "
           "coating is the whole record.** IRC R317.3.1 requires fasteners and connectors "
           "in contact with preservative-treated wood to be hot-dip galvanized, stainless, "
           "silicon bronze or copper; the copper in a modern ACQ/CA preservative corrodes "
           "plain G90 zinc, and Simpson publish the same instruction per part. The twenty-"
           "four ties on the sunken garden\'s treated glulam beams and KDAT porch beams "
           "were billed as G90 H2.5A until 2026-09-12, at 0 FAIL, because "
           "``hardware_for_role`` held one product per role and had no way to ask.",
    # **Same steel, same holes, same report row — only the coating differs.** ESR-2613 is a
    # structural report: it tabulates the H2.5A's allowable loads through a stated fastener
    # schedule and says nothing about zinc thickness, so the Z model is the same row. That is
    # a copy of a published value, not a derivation across a family:
    # `_H25AZ_ESR2613` names the table, the row, and the date it was read, and the ZMAX
    # coverage is the catalog's own — Simpson list the H2.5AZ under the same H2.5A entry.
    #
    # **The species caveat rides across unchanged and is, here, satisfied rather than
    # carried:** every joint this part is selected for lands on KDAT southern pine or treated
    # SYP glulam, both SG 0.55, which is inside the DF/SP column these values come from.
    #
    # ** SO THIS RECORD KEEPS 700 WHERE THE G90 H2.5A WENT TO 615 ON 2026-09-14, AND THAT IS
    # THE POINT OF THE SPLIT. ** Simpson's catalog publishes an SPF/HF column the ESR does
    # not (``_C_C_H_TIES``), and the galvanized record took it because it lands on SPF
    # plates. This one does not, because it does not. Same stamping, same report row, two
    # species columns, two houses' worth of framing — and General Note e is what decides
    # which: the LOWEST specific gravity in the connection.
    allowable=AllowableLoads(
        uplift_lb=700.0,
        lateral_f1_lb=110.0,
        lateral_f2_lb=110.0,
        load_duration_factor=1.6,
        species="DF-L / SP (assigned SG 0.50 / 0.55) — and unlike the galvanized record "
                "above, that is not a caveat in force here: the joints that select this "
                "part are all on SYP (KDAT and treated glulam, SG 0.55), inside the "
                "published column. The catalog's SPF/HF figure for the same tie is 615 lbf "
                "and is the galvanized record's, not this one's",
        fasteners="5 - 0.131 in x 2-1/2 in to the rafter/joist and 5 - 0.131 in x 2-1/2 in "
                  "to the plates — the carbon schedule, unchanged. **Drive it with "
                  "hot-dip-galvanized nails, not electrogalvanized**: R317.3.1 governs the "
                  "nail as much as the connector, and a G90 nail through a ZMAX tie into "
                  "treated wood is the same corrosion cell with a smaller anode",
        citation=("ICC-ES ESR-2613 (Simpson hurricane ties) Table 1, H2.5A row, read "
                  "2026-08-30 — the report tabulates the tie\'s structural capacity through "
                  "a stated nail schedule and does not distinguish the G90 and ZMAX "
                  "coatings, which are the same stamping; footnote 2 requires a unity check "
                  "across uplift + both lateral directions under simultaneous loading, "
                  "footnote 5 states the uplift already carries the wind increase"),
    ),
)
LS30_GABLE_END_TIE = StructuralHardware(
    tag="simpson-ls30-gable-end-tie",
    name="LS30 skewable angle, gable-end stud to rafter",
    role=ROLE_GABLE_END_TIE,
    manufacturer=_SIMPSON,
    model="LS30",
    exposure=EXPOSURE_DRY,
    source="Simpson Strong-Tie LS30 skewable angle, 18 ga, 3-3/8 in long, 2-1/4 in legs, "
           "field-bent 0-135 degrees (once). One leg on the 5-1/2 in face of a gable-end "
           "stud, the other bent to the bottom flange of the TJI 230 rafter above. A trussed "
           "gable takes an LTP4 instead. **The joint is lateral, not "
           "uplift:** no rafter bears on a non-bearing gable wall, and what the tie carries "
           "is the wall's out-of-plane reaction into the roof. Replaced the H10A on "
           "2026-09-16 (owner): that row assumes a sawn 2x rafter (ESR-2613 Table 1 fn.1) "
           "and its rafter-leg nails do not fit a 1-1/2 in I-joist flange; the H6 was "
           "rejected because ESR-2613 publishes it for uplift only (F1/F2 blank).",
    # C-C-2019 p.284 publishes the LS in F1 ONLY — no F2, no uplift — and draws F1 for a
    # member crossing its support, loaded along itself. This joint loads the angle across
    # the wall; the owner's detail, not a table read. Unverified: Weyerhaeuser's rules for
    # nailing up into a TJI flange (1-1/2 in nails, so they stay inside it).
    allowable=AllowableLoads(
        lateral_f1_lb=275.0,
        load_duration_factor=1.6,
        species="SPF / HF — the column this house is framed in (DF/SP reads 320 lbf)",
        fasteners="6 - 0.148 in x 1-1/2 in, three per leg. The 3 in nail row (340 lbf SPF) "
                  "is not used: it would pass through a 1-1/2 in flange",
        citation=("Simpson Strong-Tie Wood Construction Connectors C-C-2019 p.284, "
                  "\"L/LS/GA Reinforcing and Skewable Angles\", LS30 row, SPF/HF "
                  "Wind/Seismic (160) column, read 2026-09-16. Installation note: the joist "
                  "must be constrained against rotation when a single LS is used per "
                  "connection"),
    ),
)

LTP4_GABLE_TRUSS_ANCHOR = StructuralHardware(
    tag="simpson-ltp4-gable-truss-anchor",
    name="LTP4 lateral tie plate, gable-end truss to top plate",
    role=ROLE_GABLE_TRUSS_ANCHOR,
    manufacturer=_SIMPSON,
    model="LTP4",
    exposure=EXPOSURE_DRY,
    source="Simpson Strong-Tie LTP4 lateral tie plate (strongtie.com/ltp), one mid-span "
           "on each gable-end truss, bottom chord to the wall's top plate. Lateral only: "
           "uplift is the H2.5A at each heel, which the bearing rule already derives. "
           "Replaced the HGA10 on 2026-09-16 (owner).",
)

H25ASS_HURRICANE_TIE = StructuralHardware(
    tag="simpson-h2-5ass-hurricane-tie",
    name="H2.5ASS stainless hurricane/seismic tie",
    role=ROLE_HURRICANE_TIE,
    manufacturer=_SIMPSON,
    model="H2.5ASS",
    source="Simpson Strong-Tie H2.5ASS, 18 ga Type 316 stainless — the H2.5A above in "
           "stainless, and the only tie at RF-BW-CANOPY's eight truss bearings. It is a "
           "SEPARATE record and not a size within the H2.5A family on purpose: "
           '"H2.5ASS".startswith("H2.5A") is true, so without this row the canopy\'s '
           "stainless ties would silently take the galvanized tie's price and its 700 lbf. "
           "The house buys stainless at every KDAT joint (owner, 2026-09-10), and this "
           "connector is nailed into treated southern pine headers at an entry that is "
           "salted every winter.",
    # ** RESOLVED 2026-09-11, AND THE OLD NOTE'S PUZZLE IS WHAT RESOLVED IT. ** This record
    # carried no allowable for a day on the grounds that the figures in circulation for the
    # H2.5ASS were materially lower than the galvanized H2.5A's 700 lbf — a 440/75/70
    # uplift-F1-F2 row in secondary listings of the C-C catalog — and could not be tied to a
    # primary table. `_L_F_SSNAILS` explains both halves at once: the 440/75/70 row is a real
    # Simpson table, the STAINLESS SMOOTH-SHANK one, and the letter says the full carbon
    # values are recovered by substituting Strong-Drive SCNR ring-shank nails. The number was
    # not wrong; it was the answer to a different installation.
    #
    # ** WHICH MAKES THE NAIL A SPECIFICATION ITEM, NOT A PURCHASING DETAIL. ** 700 lbf here
    # is conditional on SSA8D. Drive this tie with stainless smooth-shank nails and the joint
    # is worth 440 lbf, at 0 FAIL, with nothing in the model able to tell. The demand is in
    # `notes/north_entry_piers.md` §4a — about 256 lbf per tie under 0.6W with no dead relief
    # — so the canopy survives either nail; the record says SSA8D because the next house may
    # not.
    allowable=AllowableLoads(
        uplift_lb=700.0,
        lateral_f1_lb=110.0,
        lateral_f2_lb=110.0,
        load_duration_factor=1.6,
        species="DF-L / SP (assigned SG 0.50 / 0.55) — in force and satisfied: this tie is "
                "nailed into treated southern pine headers (SG 0.55), inside the published "
                "column. The catalog's SPF/HF figure for the same stamping is 615 lbf "
                "(``_C_C_H_TIES``) and belongs to the G90 record, which lands on SPF "
                "plates; stainless parity is about the steel and the nails and says nothing "
                "about species either way",
        fasteners="5 - SSA8D stainless ring-shank to the rafter and 5 - SSA8D to the plates "
                  "— the letter's substitution for the catalog's 5 - 0.131 in x 2-1/2 in "
                  "(8d common) each side. **With stainless SMOOTH-shank nails instead, this "
                  "tie is a 440/75/70 part, not a 700/110/110 one**",
        citation=(_L_F_SSNAILS + ". The values are the H2.5A row of ICC-ES ESR-2613 "
                  "(Simpson hurricane ties) Table 1, read 2026-08-30; H2.5ASS is not in "
                  "that report and the parity is the letter's. ESR-2613 footnote 2 requires "
                  "a unity check across uplift + both lateral directions under simultaneous "
                  "loading, footnote 5 states the uplift already carries the wind increase"),
    ),
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
    # Florida product approval FL11473 Table 1, HGAM10 row — the SPF/HF column, which is what
    # this house frames in and which is published here (unlike the hurricane ties above,
    # Simpson do print both species for the masonry connectors).
    #
    # F2 is directional and the table says so in footnote 5: 795 lbf for force INTO the
    # connector, 460 lbf away from it. **The lower, away-from figure is recorded**, because
    # nothing in this model orients a gusset against a load direction, and a value that only
    # holds for one sign of the load is not a capacity a check can use. The 795 is in the
    # citation for a reviewer who can establish the sign.
    #
    # **This said "the two HGAM10s at the cast column tops" until 2026-09-14, when there were
    # already twelve.** There are twenty-four now: every one of the twelve joints carries a
    # PAIR, one gusset each side of the beam, because a single angle is an eccentric rotation
    # restraint and NDS 3.3.3 wants beam ends restrained against rotation. Footnote 4 is the
    # condition that permits it — a minimum 2-1/2" member "where anchors are installed on each
    # side" — and every beam at these joints is 3" or wider.
    #
    # A pair does NOT raise the recorded number, and it is worth being explicit about why the
    # temptation exists. With gussets on opposing faces, whichever way the load goes one of
    # them takes it as force INTO the connector, so the 795 is always available to *some*
    # gusset. That is a real observation and it is still not a capacity to record here: which
    # gusset, under which load case, is a question this model cannot answer. The recorded
    # value stays 460.
    #
    # (That sentence used to lean on a second argument — "the three `lateral_uplift` items
    # are UNKNOWN pending a PE seal regardless" — which stopped being true on 2026-09-14
    # when that kind retired. It was never the load-bearing half: an unanswerable question
    # is not recordable whether or not something downstream is blocked, and a capacity that
    # only held while a register entry happened to be open would be the wrong kind of
    # number to carry here.)
    #
    # ** INTERIOR / PROTECTED USE ONLY, AND G90 ONLY. ** Simpson C-C-2021 p.252: "Products
    # shall be installed such that the Titen Turbo screws and Titen HD screw anchors are not
    # exposed to the exterior environment" — a roof or deck overhead does not make a joint
    # interior. No ZMAX/HDG/SS HGAM exists, and G90 against treated wood misses IRC R317.3.1.
    # catlin used sixteen at exterior column heads until 2026-09-21 and retyped them to the
    # cast-in HETA20Z below; the record stays for a protected joint and as a documented
    # backup (`houses/catlin/notes/column_head_connector_options.md`).
    allowable=AllowableLoads(
        uplift_lb=585.0,
        lateral_f1_lb=630.0,
        lateral_f2_lb=460.0,
        load_duration_factor=1.6,
        species="SPF/HF — the column recorded; the DF/SP column is 810 / 875 / 640 lbf",
        fasteners="(4) 1/4 in x 1-1/2 in SDS to the wood leg + (4) 1/4 in x 1-3/4 in "
                  "Titen 2 (or Titen Turbo) into concrete, 1-1/2 in min. edge distance, "
                  "min f'c 2,500 psi",
        citation=("Simpson Strong-Tie Florida product approval FL11473 (masonry products), "
                  "Table 1, HGAM10 row, sealed 2017-10-19, read 2026-08-30. SPF/HF column: "
                  "uplift 585, F1 630, F2 795 lbf INTO the connector / 460 lbf away "
                  "(footnote 5) — the 460 is recorded. Footnote 1: already increased 60 % "
                  "for wind. Footnote 4: a min. 2-1/2 in member thickness is required where "
                  "anchors are installed on each side. Footnote 8: min f'c 2,500 psi"),
    ),
)

HETA20Z_EMBEDDED_BEAM_ANCHOR = StructuralHardware(
    tag="simpson-heta20z-embedded-truss-anchor",
    name="HETA20Z embedded truss anchor (ZMAX), installed in pairs",
    role=ROLE_EMBEDDED_BEAM_ANCHOR,
    manufacturer=_SIMPSON,
    model="HETA20Z",
    source="Simpson Strong-Tie HETA heavy embedded truss anchor, 16 ga, ZMAX (G185) — the "
           "spoon cast 4\" into the pour, the 1-1/8\" strap nailed to the member's face. "
           "Cast in, so there is no post-installed concrete anchor and no anchor-exposure "
           "condition (contrast HGAM10); G185 meets IRC R317.3.1 against treated wood with "
           "HDG 16d nails",
    # ** THE ROW IS THE PAIR'S. ** FL11473 Table 3 rates two HETAs, one each face, as ONE
    # installation; a single HETA20 is Table 2's 1,810 / 340 / 770. `HeadConnector.set_rated`
    # carries that, so the grade credits the pair's value once and never per part.
    #
    # Table 3's "2- or 3-ply" row: 16d nails, 12 total (6 per strap), anchors >= 3" apart
    # (fn 6), spaced <= 1/8" wider than the member (fn 3). A 2-2x8 and a 3-2x12 are that row
    # as printed; a 3-1/2" glulam is it by WIDTH, not by ply count — a reading, flagged. Read
    # as 1-ply instead, the lateral is Table 2's single 340 lb (fn 6).
    #
    # F1 1,350 < F2 1,430: the lower is recorded, as for every tie here. ZMAX carries the
    # G90 part's published values (Simpson corrosion guide); the table prints SP only, which
    # is what every beam at catlin's column heads is.
    allowable=AllowableLoads(
        uplift_lb=2560.0,
        lateral_f1_lb=1350.0,
        lateral_f2_lb=1430.0,
        load_duration_factor=1.6,
        species="SP — Table 3 prints no other column; the PAIR's values (2- or 3-ply, "
                "concrete, 16d). A single HETA20 is 1,810 uplift / 340 F1 / 770 F2 "
                "(Table 2)",
        fasteners="(12) 16d HDG, 6 per strap, into a 2- or 3-ply member; spoons 4\" into "
                  "f'c >= 2,500 psi concrete, >= 6\" wide, 1-1/2\" min. edge distance; the "
                  "lowest four holes of each strap filled (Table 2 fn 2)",
        citation=("Simpson Strong-Tie Florida product approval FL11473 (masonry products), "
                  "Table 3, double HETA, concrete, 2- or 3-ply, sealed 2017-10-19, read "
                  "2026-09-21: uplift 2,560, F1 1,350, F2 1,430 lb. Note 1: already +60 % "
                  "for wind. Note 6: lateral applies only to 2- or 3-ply with anchors >= 3\" "
                  "apart. Note 7: F1 may add 1/16\" deflection when not wrapped over"),
    ),
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

KBS_BEAM_HOLD_DOWN = StructuralHardware(
    tag="simpson-kbs1z-strap",
    name="KBS1Z knee-brace / beam strap (ZMAX)",
    role=ROLE_BEAM_HOLD_DOWN,
    manufacturer=_SIMPSON,
    model="KBS1Z",
    source="Simpson Strong-Tie KBS1Z strap (strongtie.com/kbs) — ZMAX galvanized strap "
           "tying a beam to the post it bears on; published for knee braces and for "
           "beam-to-post uplift, which is the joint it is used for here",
    # IAPMO UES ER-280 Table 7 (rev. 04/28/2026), cross-read against Simpson's C-C-2019
    # catalog page, which prints the same rows split by species where the report prints only
    # the DF/SP figures. **The SPF/HF column is recorded**, because that is what this house
    # frames in and it is 14 % below the DF/SP number the report leads with.
    #
    # The KBS1Z is the reason this record matters beyond its current use. It is the only
    # knee-brace connector in the Simpson line with a code-report allowable at all (§3.1.7,
    # Table 7, Figure 7), and its F1 values are published BY BRACE ANGLE with an explicit
    # interpolation rule (footnote 3) — which is exactly the capacity the balcony's braces
    # need and exactly what the APVKB45-6 above does not have.
    #
    # Which row: **connection type 1, two connectors per joint** — equal-width members, one
    # KBS1Z each side of the brace, 12 - 8d each. That is the configuration a 2x brace into a
    # 6x6 post is not (type 2, single connector, 630/510 DF-SP), so the type is recorded in
    # `fasteners` rather than left to be assumed. The uplift/lateral rows below type 2 are
    # the BEAM-to-post use (types 3 and 4) and are a different joint again; the 1,160/1,725
    # pair is what `takeoff/uplift.py` derives this part for today.
    allowable=AllowableLoads(
        uplift_lb=1000.0,        # connection type 3, 4 connectors per joint, SPF/HF
        lateral_f2_lb=1480.0,    # "Lateral", connection type 3, 4 connectors, SPF/HF
        load_duration_factor=1.6,
        species="SPF/HF — the column recorded; DF/SP is 1,160 uplift / 1,725 lateral "
                "for the same rows",
        fasteners="12 - 8d (0.131 x 2-1/2 in) per connector, connection type 3 "
                  "(continuous beam-to-post, four connectors per joint). SD9x1-1/2 screws "
                  "substitute with no load reduction (ER-280 Table 7 footnote 1)",
        citation=("IAPMO UES ER-280 rev. 04/28/2026 §3.1.7 and Table 7, read 2026-08-30, "
                  "cross-read against Simpson C-C-2019 for the SPF/HF split. This record is "
                  "the BEAM-to-post rows; the knee-brace F1 rows are on "
                  "KBS1Z_KNEE_BRACE. Footnote 2: already increased for wind/earthquake at "
                  "C_D 1.60, no further increase allowed"),
    ),
)

# The same part, serving the knee-brace role, and carrying a DIFFERENT row of the same table.
# Two records rather than one because ``hardware_for_role`` holds exactly one item per role
# and because the load that matters is not the same number: ER-280 Table 7 tabulates the
# KBS1Z by CONNECTION TYPE, and a beam-to-post cap (types 3 and 4) and a knee brace (types 1
# and 2) read different rows. Collapsing them would have handed the balcony's braces the
# 1,010 lbf of the two-connector equal-width row when what they get is 540.
#
# **Connection type 2, and that is the one judgement in this record.** Type 1 is "for
# equal-width members, install (2) KBS1Z on each end of brace"; type 2 is "for 2x knee brace,
# install single KBS1Z on each end". These braces are 2x6 diagonals into 6x6 posts — not
# equal width — so type 2 governs, at 540 lbf SPF/HF against type 1's 1,010. Taking the
# larger number would have been an 87 % overstatement of capacity on the only lateral
# elements this structure has.
KBS1Z_KNEE_BRACE = StructuralHardware(
    tag="simpson-kbs1z-knee-brace",
    name="KBS1Z knee-brace stabilizer (ZMAX), one per brace end",
    role=ROLE_KNEE_BRACE,
    manufacturer=_SIMPSON,
    model="KBS1Z",
    source="Simpson Strong-Tie KBS1Z knee-brace stabilizer (strongtie.com/kbs) — the only "
           "knee-brace connector in this catalog with a code-report allowable load, and the "
           "one Simpson publish by brace angle. Factory-formed at 45 degrees with a "
           "one-time field bend for other angles",
    allowable=AllowableLoads(
        lateral_f1_lb=540.0,     # connection type 2, single connector, 45 deg, SPF/HF
        load_duration_factor=1.6,
        species="SPF/HF — the column recorded; DF/SP is 630 lbf for the same row",
        fasteners="12 - 8d x 1-1/2 in per connector, one connector at each end of the "
                  "brace (connection type 2, a 2x knee brace into a wider member). "
                  "SD9x1-1/2 screws substitute with no load reduction",
        citation=("IAPMO UES ER-280 rev. 04/28/2026 Table 7, connection type 2, read "
                  "2026-08-30; SPF/HF split from Simpson C-C-2019. F1 by brace angle: "
                  "540 lbf at 45 deg, 440 lbf at 30 or 60 deg (SPF/HF, in-service moisture "
                  "<= 19 %; the > 19 % columns are 385 and 330). Footnote 3 permits "
                  "interpolation between the two angles. Footnote 2: values already include "
                  "C_D = 1.60 for wind, no further increase allowed"),
    ),
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

# The balcony heat-pump stands' hold-down. THIS IS THE ONE FASTENER IN THIS
# FILE THAT IS MEANT TO PIERCE A WATERPROOF PLANE, and every part of the spec is about that:
#
# * **3/8" x 4", so it reaches.** Wahoo's own AridDek guardrail detail is a 3/8" lag through
#   the deck board into timber blocking below, which is the precedent this borrows — the
#   plank is 1 1/2", leaving ~2 1/2" of thread in the 2x8 blocking, well past the ~100-150 lb
#   of wind uplift a condenser at +10' develops.
# * **316 stainless, not 304 and not galvanised.** It passes through copper-treated KDAT
#   blocking and lands under an aluminium stand on an aluminium plank. Plain or galvanised
#   steel in MCA-treated wood is the corrosion case AWC DCA6 warns about outright.
# * **Bonded EPDM washer, and butyl under the base plate.** The washer seals the shank at the
#   plank; the butyl seals the plate to the plank. Neither alone is the detail — a sealed
#   surface with an unsealed hole is how this joint fails.
#
# It is NOT a ``post_base``: a post base is selected by the post section, and this is selected
# by the seal and the alloy. Sharing the role would also have made
# ``hardware_for_role(ROLE_POST_BASE)`` ambiguous.
DECK_EQUIPMENT_ANCHOR = StructuralHardware(
    tag="stainless-through-deck-equipment-anchor",
    name="3/8 in x 4 in 316 stainless hex lag, 1 in EPDM-bonded washer, through-deck",
    role=ROLE_DECK_EQUIPMENT_ANCHOR,
    manufacturer="generic",
    model="SS316-LAG-38x4-EPDM",
    source="generic 316 stainless 3/8 in x 4 in hex lag screw with a bonded EPDM sealing "
           "washer; the fastener in Wahoo's own AridDek guardrail-post detail is a 3/8 in "
           "lag through the deck board into added timber blocking, and this is that "
           "connection made stainless for a copper-treated host — no single manufacturer "
           "system is specified, so this record is deliberately generic. INSTALLATION is "
           "most of what this part is: a 1/4 in pilot through the plank and the full depth "
           "of the blocking, the pilot wetted with sealant before the lag is driven, butyl "
           "under the base plate, and the washer seated but not crushed — a flattened EPDM "
           "washer has stopped sealing. 1 1/2 in of plank leaves ~2 1/2 in of thread in the "
           "2x8 blocking",
)

# The shim pack under a wood beam soffit where it lands on a pour. Modelled as a part since
# 2026-09-03; before that it existed only as prose inside SUNKEN_GARDEN_COLUMN_12.source and
# PIER_CONCRETE_12.source — a real purchased item at a real joint, with nothing in the BOM,
# nothing in 3D and nothing a reviewer could click.
#
# * **It holds a GAP, and the gap is the point.** A beam sitting flat on a wash ponds against
#   its own end grain; the gap drains and lets both faces dry. 1/2"-1" is AITC/WoodWorks'
#   range for exposed timber on concrete and the range the column tops are cast to, so the
#   pack is shimmed to suit rather than being one thickness. FPInnovations' durability
#   hierarchy is the reason it is a gap and not a membrane: drain and dry the joint before
#   trying to seal it, and a barrier that can hold water is worse than the air it replaced.
# * **NO CODE SECTION REQUIRES THIS PART, and the record should not pretend one does.** This
#   said "IRC R317.1.4 wants a wood member on concrete held clear of it" until 2026-09-12 and
#   that is not what R317.1.4 says: it governs wood COLUMNS, and its 1"/6"/8" projections are
#   exceptions that RELIEVE the treatment requirement rather than impose a clearance.
#   R317.1 item (2) needs a foundation wall and less than 8" to grade; R317.1.2 is embedment,
#   not bearing. A treated beam on a concrete column top satisfies R317 with no barrier and
#   no standoff. This is a durability choice on top of the code. (The R317.1.4 citation on
#   ABU66SS above is a different joint and is correct — that one IS a wood column on
#   concrete.) FPInnovations bounds the wood-on-concrete wicking concern to ~150 mm above
#   soil, and published equilibrium capillary rise in concrete is 100-480 mm — bounded by
#   evaporation, not by suction, which is why a taller column does not pull further. Nothing
#   this part sits on is within reach of that: catlin's north-entry pier tops stand 18 1/2"
#   above grade, its two full-height canopy columns 9'-2 3/4", and the garden's porch columns
#   rise 10'-0 15/16" out of the court floor. What the gap IS aimed at is rain standing on the
#   pour, and end-grain uptake where a beam END lands there rather than crossing it.
# * **NO GROUT ISLAND under it.** An exposed non-shrink cementitious island is a 10-20 year
#   element carrying a 100-year member, and it re-wets the soffit it was meant to lift. Where
#   a levelling bed is unavoidable it is EPOXY grout confined under the plate — that sentence
#   used to live in an assembly ``source`` and belongs on the part.
# * **316 stainless, or HDG with an isolator.** These sit under copper-treated KDAT and under
#   treated glulam, both of which eat plain steel. Where the pack meets a zinc-coated tie
#   (HETA20Z strap, HGAM10 gusset) an EPDM or HDPE isolator goes between them.
#
# Deliberately NOT a post base and not a bearing plate: it is selected by the gap and the
# alloy, not by a post section, and ``hardware_for_role`` holds one part per role.
BEARING_STANDOFF_SHIM = StructuralHardware(
    tag="stainless-beam-bearing-standoff-shim",
    name="3-1/2 in square 316 stainless beam standoff shim pack, 1/2 in to 1 in",
    role=ROLE_BEARING_STANDOFF,
    manufacturer="generic",
    model="SS316-SHIM-35",
    source="generic 316 stainless plate shims, 3-1/2 in square, stacked to the 1/2 in-1 in "
           "gap a cast column top is finished to — no manufacturer system is specified, so "
           "this record is deliberately generic, as SS316-LAG-38x4-EPDM and SS316-WEDGE-38x3 "
           "are. INSTALLATION is most of what it is: set on the cast wash under the beam "
           "footprint with NO grout island (epoxy grout confined under the plate if a "
           "levelling bed proves unavoidable, never a cementitious one), an EPDM or HDPE "
           "isolator where the pack meets a zinc-coated tie (HETA20Z strap), and the stack "
           "shimmed so the soffit stands clear of the pour rather than bedded on it. **Where the beam is "
           "TILTED, the leaves are LAPPED TO THE DRAINAGE SLOPE** — full leaves at the low "
           "edge, progressively short ones toward the high edge — rather than a custom "
           "tapered shim being fabricated: a tapered stainless shim is a laser-cut/CNC "
           "specialist item, and a pack is already a stack of leaves. At catlin\'s balcony "
           "that taper is 1/8\" over the 6\" bearing (0.0227 in/in), over an EPDM isolator "
           "that conforms the rest under load. SJI requires no sloped seat below 3/8 in per "
           "foot and bridge practice taper-shims sloped girders to the nearest 1/16 in, so "
           "this slope is inside the range a conforming pad handles — "
           "houses/catlin/notes/balcony_differential_movement.md §3",
)

# The ground-pad twin of the part above, and a much simpler joint: an equipment stand
# standing on a 4" concrete pad at grade, wedge-anchored into it.
#
# * **3/8" x 3", so it fits the pour.** A 3/8" wedge anchor wants ~1 1/2"-2" of embedment;
#   3" of length leaves that in a 4" slab with the stand's base plate and a nut on top, and
#   does not reach the capillary break under it.
# * **316 stainless, not 304 and not galvanised.** The stand is aluminium, the pad is at
#   grade in a de-iced climate, and the anchor sits in the splash zone the whole winter.
#   316 in aluminium is the same non-couple 316 in an aluminium plank was.
# * **No sealing washer, and that is the difference.** ``DECK_EQUIPMENT_ANCHOR`` is chosen
#   for its seal because it pierces a roof. Nothing is below this one but stone, so it is
#   selected for embedment and alloy alone.
EQUIPMENT_PAD_ANCHOR = StructuralHardware(
    tag="stainless-equipment-pad-wedge-anchor",
    name="3/8 in x 3 in 316 stainless wedge anchor, into a concrete equipment pad",
    role=ROLE_EQUIPMENT_PAD_ANCHOR,
    manufacturer="generic",
    model="SS316-WEDGE-38x3",
    source="generic 316 stainless 3/8 in x 3 in wedge (expansion) anchor for a mechanical "
           "stand's base plate into a 4 in slab-on-grade; no single manufacturer system is "
           "specified, so this record is deliberately generic. INSTALLATION: drill 3/8 in "
           "to depth in cured concrete, blow the hole clean, drive the anchor to the mark "
           "and torque the nut to the manufacturer's value — an under-torqued wedge has not "
           "set and an over-torqued one has spun its cone",
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
    SDPW_DEFLECTOR_SCREW,
    SDPW19_DEFLECTOR_SCREW,
    FASTENMASTER_TIMBERLOK,
    LSSR_SLOPED_HANGER,
    LSTA24_RIDGE_STRAP,
    LUS_FACE_MOUNT_HANGER,
    LUSZ_FACE_MOUNT_HANGER,
    IUS_FACE_MOUNT_HANGER,
    HHUS410_SCL_FACE_MOUNT_HANGER,
    THA_FLOOR_TRUSS_HANGER,
    HUC_CONCRETE_HANGER,
    APVB_BRACE_BOLT,
    MASA_MUDSILL_ANCHOR,
    STHD_STRAP_HOLDOWN,
    SP4_STUD_PLATE_TIE,
    SP6_STUD_PLATE_TIE,
    CS16_COIL_STRAP,
    ABU_POST_BASE,
    ABU44_POST_BASE,
    MSTA12Z_POST_TENSION_STRAP,
    L50Z_POST_TENSION_ANGLE,
    POST_BASE_ANCHOR_BOLT,
    PC6Z_POST_CAP,
    CCQ46SDS_POST_CAP,
    LTP4_LATERAL_TIE_PLATE,
    SILL_ANCHOR_BOLT,
    H25A_HURRICANE_TIE,
    H25AZ_HURRICANE_TIE,
    LS30_GABLE_END_TIE,
    LTP4_GABLE_TRUSS_ANCHOR,
    HGAM10_MASONRY_GUSSET,
    HETA20Z_EMBEDDED_BEAM_ANCHOR,
    S5_SEAM_CLAMP,
    S5_S_SNAP_LOCK_CLAMP,
    S5_N_NAIL_STRIP_CLAMP,
    S5_CANDUIT_PIPE_CLAMP,
    S5_PV_KIT,
    S5_COLORGARD_SNOW_RETENTION,
    KBS_BEAM_HOLD_DOWN,
    KBS1Z_KNEE_BRACE,
    LAPPED_BRACE_BOLT,
    POLY_PANEL_FASTENER,
    DECK_EQUIPMENT_ANCHOR,
    BEARING_STANDOFF_SHIM,
    EQUIPMENT_PAD_ANCHOR,
    EXPOSED_FASTENER_PANEL_SCREW,
    THROUGH_PANEL_PIPE_STRAP,
    POCKET_FRAME_KIT_1500PF,
    POCKET_FRAME_KIT_HEAVY,
)


#: Parts this catalog holds a **capacity record** for without billing them.
#:
#: ``STRUCTURAL_HARDWARE`` above is the BOM's catalog: every item in it is something the
#: take-off can select and order, and adding to it changes what a house buys. This tuple is
#: for the other case — a part number that appears in a house's plan source or in a
#: published table and whose allowable load somebody needs to be able to look up, without it
#: becoming a purchasable role. ``allowable_for_model`` searches both; nothing else does.
#:
#: The ABU66SS is here because ``hardware_by_model("ABU66SS")`` prefix-matches the galvanised
#: ABU66, and a reader asking "what is this base rated for" must not be handed the wrong
#: report's numbers. Keeping it out of ``STRUCTURAL_HARDWARE`` keeps every BOM line, role
#: lookup and price row exactly where it was.
CAPACITY_ONLY_RECORDS: tuple = (
    ABU66SS_POST_BASE,
    H25ASS_HURRICANE_TIE,
    APVKB_KNEE_BRACE,
    HUCQ_CONCRETE_HANGER,
    HUC212_3_CONCRETE_HANGER,
    HU212_3_FACE_MOUNT_HANGER,
    HU28_2Z_FACE_MOUNT_HANGER,
)
