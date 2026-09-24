"""Joist, stringer and concrete face-mount hangers, and the ridge strap.

Split out of the former ``library/hardware.py``; see the package docstring.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    EXPOSURE_DRY,
    EXPOSURE_TREATED,
    ROLE_CONCRETE_FACE_MOUNT_HANGER,
    ROLE_FACE_MOUNT_JOIST_HANGER,
    ROLE_FLOOR_TRUSS_HANGER,
    ROLE_IJOIST_FACE_MOUNT_HANGER,
    ROLE_RIDGE_TIE_STRAP,
    ROLE_SCL_FACE_MOUNT_HANGER,
    ROLE_SLOPED_JOIST_HANGER,
    ROLE_STAIR_STRINGER_CONNECTOR,
    AllowableLoads,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON

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

LSCZ_STRINGER_CONNECTOR = StructuralHardware(
    tag="simpson-lscz-adjustable-stringer-connector",
    name="LSCZ adjustable stair-stringer connector (ZMAX)",
    role=ROLE_STAIR_STRINGER_CONNECTOR,
    manufacturer=_SIMPSON,
    model="LSCZ",
    source="Simpson Strong-Tie LSC adjustable stringer connector, 18 ga, field-slopeable to "
           "any common stringer pitch; LSCZ is the ZMAX finish (strongtie.com/lsc)",
    # The STANDARD row: footnote 4 puts an LSC at the end of a rim over support framing
    # there, and a stringer head at a header's end over its post is that case.
    allowable=AllowableLoads(
        download_lb=755.0,
        load_duration_factor=1.0,
        species="DF/SP (KDAT southern pine); SPF/HF is 650 lbf on the same row",
        fasteners="(8) 0.148\" x 1-1/2\" into the rim board, (8) 0.148\" x 1-1/2\" into the "
                  "stringer wide face, (1) 0.148\" x 1-1/2\" into the stringer narrow face "
                  "(second-to-last hole)",
        citation="Simpson Strong-Tie C-C-2024 p. 308, LSCZ/LSCSS, Standard installation, "
                 "DF/SP Floor (100) 755 lbf, Snow (115) 755 lbf. No uplift or lateral is "
                 "published for the part",
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
    # ** THE FULL 18 NAILS, OR THIS NUMBER IS NOT THE PART'S. ** Table 3's row is tabulated
    # through 18-10d, nine into each member (footnote 1), and the detail that specifies this
    # strap over a ridge names only twelve. Twelve nails is a DIFFERENT connection; the
    # tabulated 1,235 lbf is the STEEL value (footnote 5) and the nail group behind it is
    # what has to be installed for the steel to be what governs.
    allowable=AllowableLoads(
        uplift_lb=1235.0,
        load_duration_factor=1.6,
        species="wood of assigned or equivalent SG >= 0.50 (Table 3 footnote 2) — southern "
                "pine and DF-L qualify; SPF (0.42) does not, and nothing here lands in it",
        fasteners="18 - 10d x 2-1/2 in common nails, 9 into each member (Table 3 footnote 1)",
        citation=("ICC-ES ESR-2105 (Simpson Strong-Tie straps), reissued January 2026, "
                  "Table 3, LSTA24 row — read 2026-09-22: 20 ga, 24 in, allowable TENSION "
                  "1,235 lbf. Footnote 5: the value is governed by STEEL strength and "
                  "carries neither the one-third stress increase nor C_D, so the C_D 1.6 "
                  "recorded here is the table's column heading and not an increase applied "
                  "to this row. Footnote 4's connection strength (18 nails x the NDS yield "
                  "mode value) is higher, which is why the steel governs — and is why a "
                  "demand ALONG the joint rather than across it is no weaker: NDS dowel "
                  "bearing is independent of the angle to grain for a fastener under 1/4 in"),
    ),
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


#: The single-2x12 face-mount on a treated ledger. Simpson publishes no LUS212: the 2x12
#: rows of the DF/SP face-mount table list LUS210, whose 7-13/16" is 70% of an 11-1/4" joist.
#: Its own record so ``hardware_by_model`` does not caption it as the LUS family.
LUS210Z_FACE_MOUNT_HANGER = StructuralHardware(
    tag="simpson-lus210z-face-mount-hanger",
    name="LUS210Z face-mount hanger, 2x10/2x12 (ZMAX)",
    role=ROLE_FACE_MOUNT_JOIST_HANGER,
    manufacturer=_SIMPSON,
    model="LUS210Z",
    exposure=EXPOSURE_TREATED,
    fits_nominal=("2x10", "2x12"),
    source="Simpson Strong-Tie LUS210 in ZMAX (G185) — 18 ga, W 1-9/16\", H 7-13/16\", "
           "B 1-3/4\"; ZMAX per IRC R317.3.1 on a preservative-treated carrier",
    allowable=AllowableLoads(
        uplift_lb=1165.0,
        download_lb=1340.0,
        load_duration_factor=1.0,
        species="DF/SP — the southern pine joists and ledger it is used on",
        fasteners="(8) 10d into the header, (4) 10d into the joist (double-shear)",
        citation=("Simpson Strong-Tie Wood Construction Connectors C-C-2017 p. 127, "
                  "\"Face-Mount Hangers - Solid Sawn Lumber (DF/SP)\", 2x12 joist size, "
                  "LUS210 row, read 2026-09-22: uplift (160) 1,165, floor (100) 1,340, "
                  "snow (115) 1,525, roof (125) 1,650 lb. download_lb is the floor column"),
    ),
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
