"""Knee braces and lapped brace bolts.

Split out of the former ``library/hardware.py``; see the package docstring.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    ROLE_BRACE_THROUGH_BOLT,
    ROLE_KNEE_BRACE,
    ROLE_LAPPED_BRACE_BOLT,
    AllowableLoads,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON

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
