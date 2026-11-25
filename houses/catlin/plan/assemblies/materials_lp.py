"""LP SmartSide panel siding on the sunken court's house face (notes/court_face_lp_panel.md).

House-local; promoting it to the shared library is a CONTRIBUTING step. Tags name the product,
not the colour. Every value is read from LP's own documents (out/lp_reads, cited per row):
AI = LP Application Instructions LPZB0512, 38/76/190 Series panel siding, 2024-04-26;
ESR = ICC-ES/APA ESR-1301, reissued 2026-02; CAT = LP SmartSide Product Catalog 2025.
"""

from typehaus import Material
from typehaus.model.cladding_trim import TrimCondition

#: Benjamin Moore Potters Clay, 1221 (CC-360): hex B98766, LRV 28.25 (benjaminmoore.com, read
#: 2026-11-24). The panel and its trim are field-painted in it.
POTTERS_CLAY = "#b98766"

#: The panel's own trim kit; the court's two walls have no outside corner, eave or rake. Heads
#: take the house's dark drips: D-B-SUNKEN the custom door head (D-M-PORCH's), WIN-B-SAUNA the
#: Z drip flashing. Each vertical joint takes a 440 3.50" batten over its 2x4 nailer.
LP_PANEL_KIT = {
    TrimCondition.DOOR_HEAD: "DOOR_HEAD_CUSTOM",
    TrimCondition.OPENING_HEAD: "OPENING_HEAD_DRIP_FLASHING",
    TrimCondition.VERTICAL_JOINT: "LP_440_BATTEN_3_5",
}

MATERIALS_LP = [
    Material(tag="lp-smartside-smooth-panel",
             name='LP SmartSide 38 Series 3/8" Brushed Smooth primed panel siding, 4x8, vertical',
             r_per_inch=0.0, hatch="siding", color=POTTERS_CLAY, finish="paint",
             trim_kit=LP_PANEL_KIT,
             source="CAT 2025: 38 Series Brushed Smooth panel, 3/8 nominal (0.354 in actual), 47.81 in "
                    "wide, square edge, primed 4x8/4x10 special order. AI 2024 p.4: 6 in o.c. edges, "
                    "12 in field, 3/8 in from a square edge, 1/8 in joint gap; seal every cut edge; "
                    "paint within 180 days, 100% acrylic. No panel weight read, so no density; no LP "
                    "R-value read, so r_per_inch 0: outboard of the vented cavity it is credited nothing."),
    Material(tag="lp-smartside-trim-smooth",
             name='LP SmartSide 440 Series 3/4" Brushed Smooth primed trim',
             density=570.0, hatch="wood", color=POTTERS_CLAY, finish="paint",
             source="CAT 2025 p.43: 440 Series Brushed Smooth trim, 3/4 nominal, 0.675 in actual, "
                    "primed widths 1.50/2.50/3.50/5.50/7.21/9.21/11.21 in, 16 ft; AI 2024 p.2: 440 or "
                    "540 trim so the panel does not stand past the trim face; 3/16 in gap and sealant "
                    "at the panel (p.11). Painted with the panel. Density = CAT's 2 psf / 0.675 in."),
    Material(tag="lp-panel-paint-exterior",
             name="100% acrylic exterior paint, Benjamin Moore Potters Clay 1221, 2 coats",
             r_per_inch=0.0, coating=True, color=POTTERS_CLAY, finish="paint",
             source="AI 2024: LP SmartSide is painted within 180 days of installation with a 100% "
                    "acrylic exterior paint (flat, satin or semi-gloss on smooth); colour Benjamin "
                    "Moore Potters Clay 1221 / CC-360 (owner, 2026-11-24)."),
]
