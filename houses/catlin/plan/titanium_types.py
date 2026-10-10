"""The owner-furnished titanium: the basement handrail's type and the two Waltly products.

House-local because the stock is already bought — 5 tubes and 5 sheets — and the type is
sized to it. The cut plan, fitting fit and the R301.5 hand-calc are in
notes/titanium_handrail_backsplash.md. Placements: plan/storeys/main.py (rails) and
plan/kitchen_casework.py (backsplash).
"""

from __future__ import annotations

from typehaus import RailingType
from typehaus.model import Product, mm

TI_TUBE = Product(
    tag="PROD-WALTLY-TI-TUBE-42X2.5", brand="Waltly Titanium",
    model="Ti alloy tube 42 x 2.5 x 1200",
    name="Titanium alloy tube, 42 mm OD x 2.5 mm wall, ~1200 mm",
    source="Owner order, 5 pieces (2026-10). Grade not stated; ask Waltly for the mill cert.",
)
TI_SHEET = Product(
    tag="PROD-WALTLY-TI-SHEET-GR2-0.8", brand="Waltly Titanium",
    model="Gr 2 sheet 500 x 1000 x 0.8, teardrop hem",
    name="Grade 2 titanium sheet, 500 x 1000 x 0.8 mm, hemmed, brushed",
    source="Owner order, 5 sheets (2026-10): open teardrop/rolled hem, 12 mm finished depth, "
           "2.0 mm inside bend radius, brushed.",
)

RAILING_INT_TI_HANDRAIL_42 = RailingType(
    tag="RAILING-INT-TI-HANDRAIL-42",
    name="Titanium tube handrail, 42 mm, on 316 stainless 42.4 mm fittings",
    rail_material="titanium-alloy-tube",
    post_material="stainless-316-brushed",
    rail_diameter=mm(42),
    stock_length=mm(1200),
    # The R301.5 hand-calc span (note §4); the bracket bought must publish at least this.
    bracket_spacing_max=mm(1000),
    product_ref=TI_TUBE.tag,
    source="Owner-furnished Ti tube, spliced over a bracket on an internal sleeve. Fittings "
           "are stock 316 stainless for 42.4 mm tube: saddle wall brackets at 60-93 mm "
           "wall-to-centre rated >= 0.9 kN, 90-degree wall-return elbows and wall end "
           "plates, bonded with structural epoxy. Measure fit first: the tube is 42.0 OD / "
           "37.0 ID (note §2).",
)

RAILING_TYPES = (RAILING_INT_TI_HANDRAIL_42,)
TITANIUM_PRODUCTS = (TI_TUBE, TI_SHEET)
