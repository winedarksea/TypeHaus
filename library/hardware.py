"""Shared structural connection hardware — the parts the hardware take-off bills.

Each item is the *published product family*, keyed by the condition (role) the resolved
model derives, so a house never names a part number in its plan source. Sources cite the
manufacturer system the record describes; no rating here is estimated.

**Allowable loads, from 2026-08-30.** Some items now carry an ``AllowableLoads`` record
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
ESR-1622 does not cover it.
"""

from __future__ import annotations

from typehaus.takeoff.hardware_catalog import (
    ROLE_BEAM_HOLD_DOWN,
    ROLE_BRACE_THROUGH_BOLT,
    ROLE_COIL_STRAP,
    ROLE_CONCRETE_FACE_MOUNT_HANGER,
    ROLE_DECK_EQUIPMENT_ANCHOR,
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
    ROLE_RIDGE_TIE_STRAP,
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

# **Retired from the knee-brace role on 2026-08-30, and kept as a capacity record.** It
# served ROLE_KNEE_BRACE from the day the balcony was framed, and the 2026-08-30 research
# pass established that it has no published allowable load of any kind (the citation below
# traces the whole chain). The balcony's knee braces are its *entire* lateral system —
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
    # **No published allowable load, and it is not for want of looking.** Traced 2026-08-30
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

#: ICC-ES ESR-1622, the ABU family's evaluation report. Pulled and read 2026-08-30.
_ESR_1622 = "ICC-ES ESR-1622 (Simpson Strong-Tie post base connectors), Table 2, read 2026-08-30"

ABU_POST_BASE = StructuralHardware(
    tag="simpson-abu66-standoff-post-base",
    name="ABU66 standoff post base (6x6)",
    role=ROLE_POST_BASE,
    manufacturer=_SIMPSON,
    model="ABU66",
    fits_nominal=("6x6",),
    source="Simpson Strong-Tie ABU adjustable standoff post base (strongtie.com/abu) — "
           "1 in standoff keeps the post end off the wet slab",
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

#: **The stainless ABU is not the galvanised ABU with a different finish, as far as any
#: published number is concerned.** Retailers list the ABU66SS under "ICC Certification ABU -
#: ESR 1622" and that citation does not survive reading the report: ESR-1622 §3.2.1 evaluates
#: connectors "fabricated from galvanized steel in accordance with ASTM A653", and its Table 2
#: lists ABU44/44R/46/46R/5-5/5-6/66/66R/88/88R/1010/1010R/1212/1212R — no SS model anywhere.
#: 316L stainless has a lower yield than the A653 SS Grade 33/40 the tables are built on, so
#: this is not a case where the galvanised number is obviously conservative either.
#:
#: This record exists so that ``allowable_for_model("ABU66SS")`` returns an explicit "read the
#: report, it does not cover this part" rather than falling through to the ABU66's numbers by
#: prefix match — which is precisely what ``hardware_by_model`` would do and why
#: ``allowable_for_model`` is exact-match only. It is not in ``STRUCTURAL_HARDWARE``'s role
#: dispatch at all — it lives in ``CAPACITY_ONLY_RECORDS`` at the foot of this file, not in
#: ``STRUCTURAL_HARDWARE``, so no BOM line, role lookup or ``hardware_by_model`` result moves
#: because of it. ``ABU_POST_BASE`` still serves ROLE_POST_BASE at 6x6, exactly as before.
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
    allowable=AllowableLoads(
        fasteners="12-16d into the post, 2 - 1/2 in bolts through the post, "
                  "1 - 5/8 in cast-in anchor bolt (as for the galvanised ABU66)",
        citation=(_ESR_1622 + " — **ABU66SS IS NOT IN IT**. §3.2.1 evaluates ASTM A653 "
                  "galvanised steel and Table 2 lists no stainless model. Retailer listings "
                  "citing ESR-1622 for this part are citing a report that does not cover it. "
                  "No allowable load is recorded because none is published; a stainless "
                  "allowable has to come from Simpson directly, not from the ABU66 row"),
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
    # ESR-2613 Table 1, H2.5A row. **The lateral values are the ones to notice: 110 lbf,
    # against 700 lbf uplift.** A check that compared a lateral demand against "the H2.5A's
    # 700 lb capacity" would pass a joint six times overloaded, which is precisely why
    # AllowableLoads is a vector. Footnote 2 goes further and requires a unity equation
    # across all three directions when a joint sees more than one at once.
    #
    # **These values are published for SG 0.50 lumber (DF-L, and 0.55 for southern pine) —
    # footnote to Table 1 / §3 of the report — and this house frames in SPF at SG 0.42.**
    # Simpson do not print an SPF column for the hurricane ties the way they do for the
    # KBS1Z and the HGAM10, so there is no honest SPF number to record here and the species
    # field says which lumber the numbers belong to instead. Using 700 lbf against an SPF
    # plate is unconservative and nothing downstream can detect it, so it is stated here.
    allowable=AllowableLoads(
        uplift_lb=700.0,
        lateral_f1_lb=110.0,
        lateral_f2_lb=110.0,
        load_duration_factor=1.6,
        species="DF-L / SP (assigned SG 0.50 / 0.55) — **NOT SPF**; catlin frames SPF at "
                "SG 0.42 and ESR-2613 publishes no SPF column for the hurricane ties",
        fasteners="5 - 0.131 in x 2-1/2 in to the rafter and 5 - 0.131 in x 2-1/2 in to "
                  "the plates (ESR-3096 Table publishes 625/450/110 lbf for the same tie "
                  "with 5-SD9112 screws each side — a different fastener, different values)",
        citation=("ICC-ES ESR-2613 (Simpson hurricane ties) Table 1, H2.5A row, read "
                  "2026-08-30; footnote 2 requires a unity check across uplift + both "
                  "lateral directions for simultaneous loading, footnote 5 states the uplift "
                  "is already increased for wind with no further increase allowed"),
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
    # nothing in this model orients the two HGAM10s at the cast column tops against a load
    # direction, and a value that only holds for one sign of the load is not a capacity a
    # check can use. The 795 is in the citation for a reviewer who can establish the sign.
    #
    # This part is used here as a masonry gusset angle at a beam-on-cast-column joint — its
    # actual published application ("anchor wood trusses, rafters, joists, or beams to
    # masonry or concrete") — and NOT as a hurricane tie. See the 2026-08-28 rationale in
    # `houses/catlin/params/sunken_garden.py`; it is deliberate and should not be "fixed".
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

# The balcony heat-pump stands' hold-down (2026-08-28). THIS IS THE ONE FASTENER IN THIS
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
    LSTA24_RIDGE_STRAP,
    LUS_FACE_MOUNT_HANGER,
    HUCQ_CONCRETE_HANGER,
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
    KBS1Z_KNEE_BRACE,
    POLY_PANEL_FASTENER,
    DECK_EQUIPMENT_ANCHOR,
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
    APVKB_KNEE_BRACE,
)
