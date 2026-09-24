"""Post bases, post-tension ties, anchor bolts and post caps.

Split out of the former ``library/hardware.py``; see the package docstring.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    EXPOSURE_TREATED,
    ROLE_FACE_MOUNT_JOIST_HANGER,
    ROLE_POST_BASE,
    ROLE_POST_BASE_ANCHOR,
    ROLE_POST_CAP,
    ROLE_POST_TENSION_TIE,
    AllowableLoads,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON

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

#: The LUS210 in stainless: catlin's porch ledgers (owner, 2026-09-22). Its own record so the
#: BOM does not caption it as the LUS210Z.
LUS210SS_FACE_MOUNT_HANGER = StructuralHardware(
    tag="simpson-lus210ss-face-mount-hanger",
    name="LUS210SS face-mount hanger, 2x10/2x12 (stainless)",
    role=ROLE_FACE_MOUNT_JOIST_HANGER,
    manufacturer=_SIMPSON,
    model="LUS210SS",
    exposure=EXPOSURE_TREATED,
    fits_nominal=("2x10", "2x12"),
    source="Simpson Strong-Tie LUS210 in stainless steel — 18 ga, W 1-9/16\", "
           "H 7-13/16\", B 1-3/4\"; a treated ledger in a wet, salted court",
    allowable=AllowableLoads(
        uplift_lb=1165.0,
        download_lb=1335.0,
        load_duration_factor=1.0,
        species="DF/SP — the southern pine joists and ledger it is used on",
        fasteners="(8) SCNR Type 316 ring-shank into the header, (4) into the joist, for the "
                  "catalog's 0.148 x 3 (double-shear)",
        citation=("Simpson Strong-Tie C-C-2026 pp. 114-118, \"Face-Mount Hangers - Solid "
                  "Sawn Lumber (DF/SP)\", 2x12, LUS210 row, read 2026-09-22: uplift (160) "
                  "1,165, floor (100) 1,335, snow (115) 1,530, roof (125) 1,640 lb; "
                  + _L_F_SSNAILS),
    ),
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
