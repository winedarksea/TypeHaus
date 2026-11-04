"""Shared railing/guard product catalog.

Guards are required by code at every open edge over 30", so "which guard product" is a
question every house asks. Each ``Railing`` instance authors its own run; these are the
product definitions, with no house geometry.

The three guards are one system: the Williams Architectural Products 42" Colonial
aluminium panel, an Ultralox product listed under ICC-ES ESR-3485 (Ultralox holds the
report; Williams and Harmony Railing are additional listees). Reissued October 2025,
subject to renewal October 2027. Sections are the product's, not dressed-lumber nominals:
a true 3" x 3" post (0.065" wall, 6005A-T5) and a 0.50" x 0.75" picket, drawn square at
its 0.50" face along the run, the face R312.1.3's sphere meets.
"""

from __future__ import annotations

from typehaus import RailingType
from typehaus.model.fascia_mount import FasciaMountSpec
from typehaus.model.product import Product
from typehaus.model.surface_mount import SurfaceMountSpec
from typehaus.quantities import inch

_ESR_3485 = "https://icc-es.org/wp-content/uploads/report-directory/ESR-3485.pdf"
_SPACING = ("ESR-3485 Table 1: 91.313\" max post spacing inside face to inside face; 6' "
            "panels 72.43\" c/c; raked bays use the 36\" x 6' stair panel CS252306B "
            "(Menards 1717812), 30-40 deg, 55.68\" max c/c at 37 deg")
#: Ultralox 3" Fascia Mount Post & Bracket (straight / inside / outside corner): four
#: 5/16" x 4" bolts, bracket top 1/2" below the rim, double blocking. Ultralox dealers only.
_FASCIA_BRACKET = ("Ultralox 3\" Fascia Mount Post & Bracket (straight / inside / outside "
                   "corner; Ultralox dealer, not Menards): 4 x 5/16\" x 4\" bolts, top 1/2\" "
                   "below the rim, double blocking behind. ESR-3485's fascia row (Fig. 10) "
                   "covers concrete only; Ultralox's fascia instructions are the wood basis")

WILLIAMS_COLONIAL_42_BLACK = Product(
    tag="PROD-WILLIAMS-CP262406B", brand="Williams Architectural Products",
    model="CP262406B", name="42\" x 6' Colonial baluster panel, Textured Black",
    sku="1717891", url=_ESR_3485,
    source=("Williams catalog p.6 (Menards 1717891; 39\" x 69.43\" actual). Ultralox system, "
            "ICC-ES ESR-3485, reissued 10/2025, current to 10/2027. AkzoNobel Interpon D "
            "powder coat, AAMA 2604."),
)
WILLIAMS_ADA_HANDRAIL_BLACK = Product(
    tag="PROD-WILLIAMS-AD901102B", brand="Williams Architectural Products",
    model="AD901102B", name="Black ADA Pipe Rail and 90 deg Return Kit",
    sku="1717885", url=_ESR_3485, stock_length=inch(94),
    source=("Williams ADA instructions p.5 and planner p.10 (Menards 1717885): 94\" pipe "
            "AD903194, smooth black; returns pivot to the rake and fix to a 3\" post face "
            "with 3 x #10 TEK screws and a backer. ESR-3485 §3.3/§4.1, Table 1: 72\" "
            "max between supports."),
)
RAILING_PRODUCTS = (WILLIAMS_COLONIAL_42_BLACK, WILLIAMS_ADA_HANDRAIL_BLACK)

ULTRALOX_3_INCH_FASCIA_MOUNT = FasciaMountSpec(
    straight_product="FM044300", inside_corner_product="FM144390",
    outside_corner_product="FM244390", pocket_width=inch(3.036),
    overall_height=inch(6), flange_height=inch(5), flange_width=inch(5.64),
    wall_thickness=inch(0.25), corner_wing_length=inch(5.966),
    inside_corner_envelope=inch(4.286), display_corner_hole_inset=inch(0.4375),
    mounting_hole_spacing=(inch(4.63), inch(4)), mounting_hole_top_drop=inch(0.5),
    bolt_diameter=inch(5 / 16), bolt_length=inch(4),
    post_screw_diameter=inch(0.242), post_screw_length=inch(1),
    washer_diameter=inch(0.6875), rear_washer_diameter=inch(0.6875),
    display_washer_thickness=inch(0.0625), display_head_width=inch(0.5),
    display_head_height=inch(0.22), insert_thickness=inch(0.125),
    foot_block_fascia_screw_length=inch(2),
    foot_block_product="FM025900", display_foot_block_width=inch(1),
    display_foot_block_thickness=inch(0.125), bottom_clearance=inch(3),
    source="Ultralox 2025 product guide: FM044300 5.64 x 3.036 x 6; FM244390 "
           "5.966 x 5.966 x 6. ESR-3485 Fig.10: 1/4 wall, 5 inch mounting flange, "
           "4.63 x 4 mounting holes. 06/24 fascia instructions: four 5/16 x 4 bolts; "
           "post screw text says 1 inch, figure says 1.5: use 1 inch per ESR Fig.10. "
           "Head/washer thickness, corner-hole inset, insert and foot-block contours "
           "are illustrative. "
           "Shallow-slope compatibility remains an unverified product assumption.",
)

RAILING_EXT_ALUMINUM_FASCIA = RailingType(
    tag="RAILING-EXT-ALUMINUM-FASCIA",
    name="Exterior aluminum fascia-mounted guard",
    product_ref=WILLIAMS_COLONIAL_42_BLACK.tag,
    post_width=inch(3), baluster_width=inch(0.5),
    source=f"Williams Colonial 42\" black on 3\" fascia posts. {_FASCIA_BRACKET}. "
           f"Fascia runs use 6' panels only. {_SPACING}.",
    # The bracket's 5" flange on the mounting face (it wraps 6" at a corner). Width and
    # projection are read off ESR-3485 Fig. 10: a 1/4" hat over a 3.036" square pocket, the
    # post's fascia face on the mounting face, so its centre stands 3.036/2 outboard.
    fascia_bracket_height=inch(5),
    fascia_bracket_width=inch(5.64),
    fascia_bracket_projection=inch(3.29),
    fascia_post_offset=inch(1.518),
    fascia_mount=ULTRALOX_3_INCH_FASCIA_MOUNT,
)

RAILING_INT_STAIR_GUARD = RailingType(
    tag="RAILING-INT-STAIR-GUARD",
    name="Interior stair guard rail",
    product_ref=WILLIAMS_COLONIAL_42_BLACK.tag,
    post_width=inch(3), baluster_width=inch(0.5),
    source=f"Williams Colonial 42\" black; ESR-3485 §2.0/§5.1 list it for interior use. "
           f"Posts on the 42\" surface kit (Menards 1717824) or {_FASCIA_BRACKET}. {_SPACING}.",
    fascia_bracket_height=inch(5),
    fascia_bracket_width=inch(5.64),
    fascia_bracket_projection=inch(3.29),
    fascia_post_offset=inch(1.518),
)

RAILING_EXT_ALUMINUM_SURFACE = RailingType(
    tag="RAILING-EXT-ALUMINUM-SURFACE",
    surface_mount=SurfaceMountSpec(
        product="BP04450", bottom_clearance=inch(3), stair_bottom_clearance=inch(1),
        base_width=inch(4.99),
        display_base_thickness=inch(0.5), display_hole_spacing=inch(3.75),
        wood_screw_diameter=inch(5/16), wood_screw_length=inch(6),
        concrete_anchor_diameter=inch(0.25), concrete_anchor_length=inch(3),
        display_head_width=inch(0.5), display_head_height=inch(0.22),
        source="Ultralox BP04450: 4.99 inch cast base; ESR-3485 Table 1 / Fig.9 "
               "wood and concrete fasteners. Thickness, hole centres and head contours "
               "are display approximations; verify actual base before drilling.",
    ),
    name="Exterior aluminum surface-mounted guard",
    product_ref=WILLIAMS_COLONIAL_42_BLACK.tag,
    post_width=inch(3), baluster_width=inch(0.5),
    source=("Williams Colonial 42\" black on the 42\" surface post kit (Menards 1717824): a "
            "cast 4.99\" square base (BP04450) screwed to the post. ESR-3485 §3.1.1, §4.2, "
            "Table 1 fn 2: on concrete 4 x 1/4\" x 3\" anchors; on wood 4 GRK RSS 5/16\" x 6\" "
            f"into SG >= 0.50. {_SPACING}."),
)

RAILING_EXT_ALUMINUM_ADA_HANDRAIL = RailingType(
    tag="RAILING-EXT-ALUMINUM-ADA-HANDRAIL",
    name="Exterior aluminum ADA pipe handrail",
    product_ref=WILLIAMS_ADA_HANDRAIL_BLACK.tag,
    # ~1.5" OD from the part names; the comparable Aria Railing 94" ADA pipe kit
    # (Home Depot AADAPRBK) reads "94 in. x 1.5 in.". Measure on delivery.
    rail_diameter=inch(1.5),
    stock_length=inch(94),
    bracket_spacing_max=inch(72),
    source=("Williams ADA pipe rail AD901102B: ESR-3485 §3.3 ADA handrail system (the "
            "Colonial top rail is no handrail, §5.7); Table 1 row for 90 deg returns to a 3\" "
            "post, 72\" max between supports. Return standoff unpublished: confirm on "
            "delivery."),
)

ALL_RAILING_TYPES = (
    RAILING_EXT_ALUMINUM_FASCIA,
    RAILING_INT_STAIR_GUARD,
    RAILING_EXT_ALUMINUM_SURFACE,
    RAILING_EXT_ALUMINUM_ADA_HANDRAIL,
)
