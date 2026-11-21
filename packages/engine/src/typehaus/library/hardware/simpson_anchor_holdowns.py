"""A bolted hold-down and the cast-in anchor bolt it bears on (HTT4 on an SSTB16).

The rows are transcribed in ``hardware/anchor_holdowns.py``; these are the BOM records.
"""

from __future__ import annotations

from typehaus.hardware.anchor_holdowns import (
    CITATION_HTT,
    CITATION_SSTB,
    HOLDOWNS,
    SSTB_STEM,
)
from typehaus.hardware.catalog import (
    ROLE_ANCHOR_ROD_HOLDOWN,
    ROLE_HOLDOWN_ANCHOR_BOLT,
    AllowableLoads,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON

HTT4_TENSION_TIE = StructuralHardware(
    tag="simpson-htt4-tension-tie",
    name="HTT4 tension tie (bolted hold-down)",
    role=ROLE_ANCHOR_ROD_HOLDOWN,
    manufacturer=_SIMPSON,
    model="HTT4",
    source="Simpson Strong-Tie HTT4 — nailed to the wide face of a braced panel's end stud, "
           "its seat on a 5/8 in cast-in SSTB (strongtie.com/htt)",
    allowable=AllowableLoads(
        uplift_lb=HOLDOWNS["HTT4"].allowable_spf_lb,
        load_duration_factor=1.6,
        species="SPF/HF column (the lower), which is what the garage frames",
        fasteners="(18) 0.148 x 1-1/2 in nails into a member at least 1-1/2 x 3-1/2 in; "
                  "5/8 in anchor; the anchorage is graded separately on its own row",
        citation=(f"{CITATION_HTT}: (18) 0.148 x 1 1/2, 1 1/2 x 3 1/2 member, DF/SP 3,000 / "
                  'SPF/HF 2,580 lb (160), Code Ref. "—" (no evaluation-report listing for '
                  "this row); general note a: no further increase. Read 2026-11-20"),
    ),
)

SSTB16_ANCHOR_BOLT = StructuralHardware(
    tag="simpson-sstb16-anchor-bolt",
    name="SSTB16 anchor bolt (holdown, cast-in)",
    role=ROLE_HOLDOWN_ANCHOR_BOLT,
    manufacturer=_SIMPSON,
    model="SSTB16",
    source="Simpson Strong-Tie SSTB16, 5/8 x 17-5/8 in, set to its 2x-sill embedment line "
           "with an AnchorMate holder before the pour; HDG nut and washer by others",
    allowable=AllowableLoads(
        uplift_lb=min(SSTB_STEM["SSTB16"].wind),
        load_duration_factor=1.6,
        species="not applicable: a concrete row; the hold-down on it carries the wood row",
        fasteners="cast in a 6 in minimum stem wall, l_e 12-5/8 in, 1-3/4 in minimum edge "
                  "distance, 5 in end distance, one #4 bar 3-5 in from the top (p. 43)",
        citation=(f"{CITATION_SSTB}: SSTB16, 6 in stem wall, 5/8 in, l_e 12 5/8, middle / "
                  f"corner / end 3,465 lb. Read 2026-11-20"),
    ),
)
