"""Tie hardware for a deck held to another structure — split out of ``hardware.py`` (size).

The north-entry landing's two tie lines (catlin ``params/landing_tie.py``, owner
2026-09-21): HDG heavy angles wood to wood into the garage's west wall, and the same angle
on the garage stem's core where the anchor side is an ACI 318 Ch. 17 design
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
    # 11.3.3) for an exterior tie, as the house already does for the L50Z.
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

TIE_HARDWARE: tuple = (HL33HDG_HEAVY_ANGLE, TIE_BLOCK_KDAT)
