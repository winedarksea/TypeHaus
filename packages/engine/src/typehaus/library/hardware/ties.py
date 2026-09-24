"""Tie hardware for a deck held to another structure — split out of the hardware catalog (size).

The north-entry landing's two tie lines (catlin ``params/landing_tie.py``, owner
2026-09-21): HL33HDG wood to wood into the garage's west wall, and HL35HDG on the garage
stem's core where the anchor side is an ACI 318 Ch. 17 design
(``engineering/deck_tie_anchor.py``). Numbers copied from the catalog, never derived.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    ROLE_HEAVY_ANGLE,
    ROLE_TIE_BLOCK,
    AllowableLoads,
    StructuralHardware,
)

#: Simpson C-C-2024 p. 303, the HL page (excerpt as distributed by a Simpson dealer).
HL_CATALOG_URL = ("https://cdn.shopify.com/s/files/1/0398/5188/4705/files/"
                  "HL_Heavy_Angle_and_Gusset.pdf?v=1733415950")

HL33HDG_HEAVY_ANGLE = StructuralHardware(
    tag="simpson-hl33hdg-heavy-angle",
    name="HL33HDG heavy angle, 7 ga, hot-dip galvanized",
    role=ROLE_HEAVY_ANGLE,
    manufacturer="Simpson Strong-Tie",
    model="HL33HDG",
    source="Simpson Strong-Tie HL heavy angle, 7 ga, legs 3-1/4\" x 3-1/4\", 2-1/2\" long, one "
           "1/2\" hole per leg 2\" off the heel (D3); HDG to order (C-C-2024 p. 303: 'May be "
           "ordered HDG'). ~$14 ea retail (fastenersplus, HL33HDG, 2026-09-21)",
    # ** TWO PUBLISHED DIRECTIONS, AND THE THIRD IS A READING. ** Uplift (740) is the force
    # perpendicular to the heel in one leg's plane, prying the other leg; F1 (1,040) is along
    # the heel, every bolt in shear. The legs are equal and identically bolted, so the force
    # perpendicular to the heel in the OTHER leg's plane is the same case mirrored — deck_tie
    # reads the uplift value for it and says so. Nothing else is inferred.
    #
    # DF/SP, published at C_D 1.6 for a DRY member: deck_tie applies NDS C_M 0.70 (Table
    # 11.3.3) to an exterior tie unless its parts author `service=InServiceMoisture("dry")`.
    allowable=AllowableLoads(
        uplift_lb=740.0,
        lateral_f1_lb=1040.0,
        lateral_f2_lb=None,
        load_duration_factor=1.6,
        species="DF/SP (SPF/HF 0.85x, fn 2) — every member it bolts to here is KDAT SP",
        fasteners="(2) 1/2\" through bolts, ASTM A307 Gr A or better (fn 8), one per leg; "
                  "lag screws of equal diameter >= 5\" long may replace the bolt in the "
                  "carried member (fn 7); wood members >= 3-1/2\" thick (fn 4), face at least "
                  "as wide as the angle (fn 3). On concrete: (1) 1/2\" x 4\" Titen HD, "
                  "mechanically galvanized (THD50400HMG), ESR-2713 — outside this row",
        citation=("Simpson Strong-Tie Wood Construction Connectors C-C-2024 p. 303, HL "
                  "table, HL33 row, read 2026-09-21: DF/SP uplift 740, F1 1,040 lb at "
                  "C_D 1.6. Fn 6: allowable loads are for a single connector; uplift may be "
                  "doubled for two, connectors on both sides for lateral both ways, lateral "
                  "may NOT be doubled. The table is wood-to-wood; Simpson publishes no HL "
                  "value on concrete. (C-C-2019 p. 287 printed 910 / 1,580 for the same row; "
                  "the 2024 values govern.) " + HL_CATALOG_URL),
    ),
)

HL35HDG_HEAVY_ANGLE = StructuralHardware(
    tag="simpson-hl35hdg-heavy-angle",
    name="HL35HDG heavy angle, 7 ga, hot-dip galvanized",
    role=ROLE_HEAVY_ANGLE,
    manufacturer="Simpson Strong-Tie",
    model="HL35HDG",
    source="Simpson Strong-Tie HL heavy angle, 7 ga, legs 3-1/4\" x 3-1/4\", 5\" long, two "
           "1/2\" holes per leg 1-1/4\" from each end (D1), 2-1/2\" apart (D2), 2\" off the "
           "heel (D3); HDG to order. Same reading as HL33HDG; only F1 differs",
    allowable=AllowableLoads(
        uplift_lb=740.0,
        lateral_f1_lb=1310.0,
        lateral_f2_lb=None,
        load_duration_factor=1.6,
        species="DF/SP (SPF/HF 0.85x, fn 2) — every member it bolts to here is KDAT SP",
        fasteners="(4) 1/2\" through bolts, ASTM A307 Gr A or better (fn 8), two per leg at "
                  "2-1/2\"; wood members >= 3-1/2\" thick (fn 4), face at least as wide as "
                  "the angle (fn 3). On concrete: ONE 1/2\" x 4\" Titen HD per leg — the "
                  "holes' 2-1/2\" is under ESR-2713's 3\" s_min, so the other stays empty",
        citation=("Simpson Strong-Tie Wood Construction Connectors C-C-2024 p. 303, HL "
                  "table, HL35 row, read 2026-09-21: 7 ga, W1/W2 3-1/4, L 5, D1 1-1/4, "
                  "D2 2-1/2, D3 2, (4) 1/2\" bolts; DF/SP uplift 740, F1 1,310 lb at "
                  "C_D 1.6. Fn 6: allowable loads are for a single connector; uplift may be "
                  "doubled for two, lateral may NOT be doubled. Wood-to-wood only. "
                  + HL_CATALOG_URL),
    ),
)

TIE_BLOCK_KDAT = StructuralHardware(
    tag="kdat-4x4-tie-block",
    name="KDAT 4x4 tie block, 3-1/2\" long, screwed to the tied member",
    role=ROLE_TIE_BLOCK,
    manufacturer="(lumber)",
    model="TIE-BLOCK-4X4-KDAT",
    source="A 3-1/2\" x 3-1/2\" x 3-1/2\" KDAT SP block: the member an HL angle's wood leg "
           "bolts through where the tied member cannot meet the angle (a carrier soffit held "
           "1/4\" off a stem; a filler flush with the cladding at a corner). Cut ends field "
           "treated per AWPA M4. Its screws into the member are a seal item, not graded",
)

TIE_BLOCK_KDAT_5 = StructuralHardware(
    tag="kdat-4x4-tie-block-5",
    name="KDAT 4x4 tie block, 5\" long, screwed to the tied member",
    role=ROLE_TIE_BLOCK,
    manufacturer="(lumber)",
    model="TIE-BLOCK-4X4X5-KDAT",
    source="A 3-1/2\" x 3-1/2\" x 5\" KDAT SP block, 5\" along the HL35's length: the member "
           "a pair of HL35HDG bolts through under a carrier soffit (HL fn 3: face at least as "
           "wide as the angle; fn 4: 3-1/2\" thick). Cut ends field treated per AWPA M4",
)

FILLER_4X_KDAT = StructuralHardware(
    tag="kdat-4x4-filler",
    name="KDAT 4x4 filler, 26-1/2\" long, nailed into a stud pack",
    role=ROLE_TIE_BLOCK,
    manufacturer="(lumber)",
    model="FILLER-4X4-KDAT",
    source="A 3-1/2\" x 3-1/2\" KDAT SP filler in a wall's end stud pack, long enough to take "
           "two HL33HDG 2'-0\" apart (2'-0\" + 2-1/2\"): gives the angle's 3-1/4\" leg a "
           "3-1/2\" face where two 2x plies give 3\" (HL fn 3). Its nailing is not graded",
)

TIE_HARDWARE: tuple = (HL33HDG_HEAVY_ANGLE, HL35HDG_HEAVY_ANGLE, TIE_BLOCK_KDAT,
                       TIE_BLOCK_KDAT_5, FILLER_4X_KDAT)
