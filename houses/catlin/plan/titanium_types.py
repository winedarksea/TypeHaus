"""The owner-furnished titanium: the basement handrail's type and the two Waltly products.

House-local because the stock is already bought — 5 tubes and 5 sheets — and the type is
sized to it. The cut plan, fitting fit and the R301.5 hand-calc are in
notes/titanium_handrail_backsplash.md. Placements: plan/storeys/main.py (rails) and
plan/kitchen_casework.py (backsplash).
"""

from __future__ import annotations

from typehaus import RailingType
from typehaus.model import Product, WallMountSpec, mm

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

# Stock 316 fittings for 42.4 mm (1.66") tube, one US seller. Stair Warehouse publishes no
# dimensions or tube wall for these; the per-part fit on the 42.0 x 37.0 Ti tube is note §2.
_SW = "Stair Warehouse listing, read 2026-11-15"
TI_WALL_BRACKET = Product(
    tag="PROD-SW-ADJ-WALL-RAIL-BRACKET", brand="Stair Warehouse",
    model="Adjustable Wall Rail Bracket",
    name="Stainless adjustable wall rail bracket, cupped saddle for 1.66 in. tube",
    url="https://www.stairwarehouse.com/adjustable-wall-rail-bracket/",
    source=f"{_SW}, $52. Grade and wall-to-centre not stated on the page.",
)
TI_RETURN_ELBOW = Product(
    tag="PROD-SW-90-ANGLE-ELBOW-1.66", brand="Stair Warehouse",
    model="90 Degree Angle Elbow - 1.66in, 316",
    name="Grade 316 stainless 90-degree angle elbow for 1.66 in. tube",
    url="https://www.stairwarehouse.com/90-degree-angle-elbow-1-66/",
    source=f"{_SW}, $34.96-42.80 (304/316). Spigot size not stated.",
)
TI_WALL_FLANGE = Product(
    tag="PROD-SW-WALL-TERMINATION-1.66", brand="Stair Warehouse",
    model="Stainless Steel Wall Termination - 1.66in",
    name="Grade 316 stainless wall flange for 42.4 mm (1.66 in.) tube",
    url="https://www.stairwarehouse.com/stainless-steel-wall-termination-1-66/",
    source=f"{_SW}, $24. Flange diameter not stated.",
)
TI_SPLICE = Product(
    tag="PROD-SW-HANDRAIL-CONNECTOR-1.66", brand="Stair Warehouse",
    model="Handrail Connector - 1.66in, 316",
    name="Grade 316 stainless internal tube connector for 1.66 in. tube",
    url="https://www.stairwarehouse.com/handrail-connector-1-66/",
    source=f"{_SW}, $14.63-17.07 (304/316); bonded with their E4584 adhesive. Size not stated.",
)

RAILING_INT_TI_HANDRAIL_42 = RailingType(
    tag="RAILING-INT-TI-HANDRAIL-42",
    name="Titanium tube handrail, 42 mm, on 316 stainless 42.4 mm fittings",
    rail_material="titanium-alloy-tube",
    post_material="stainless-316-brushed",
    rail_diameter=mm(42),
    stock_length=mm(1200),
    # The R301.5 hand-calc span (note §4).
    bracket_spacing_max=mm(1000),
    product_ref=TI_TUBE.tag,
    wall_mount=WallMountSpec(
        bracket_product=TI_WALL_BRACKET.tag,
        return_product=TI_RETURN_ELBOW.tag,
        end_plate_product=TI_WALL_FLANGE.tag,
        splice_product=TI_SPLICE.tag,
        fit_note="42.4 fitting on 42.0 Ti: shim/set screw/expander, note §2",
        source="Stair Warehouse 316 line for 1.66 in. tube (read 2026-11-15). No projection "
               "or flange size published, so neither is graded or drawn from the spec.",
    ),
    source="Owner-furnished Ti tube, spliced over a bracket on an internal connector. "
           "Fittings and their field fit: wall_mount and note §2. Accepted at the maker's "
           "spacing (owner rule).",
)

RAILING_TYPES = (RAILING_INT_TI_HANDRAIL_42,)
TITANIUM_PRODUCTS = (TI_TUBE, TI_SHEET, TI_WALL_BRACKET, TI_RETURN_ELBOW, TI_WALL_FLANGE,
                     TI_SPLICE)
