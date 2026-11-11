"""ColorGard 2.0 visualization dimensions and purchase units (inches).

Sources: s-5.com/products/colorgard/ and its installation instructions (110426);
S-5-N CCD NG73-A-0-D (2022), ColorGard 2.0 w/S-5-N CCD (2025-02-25).
The minor extrusion lips and clip bends are simplified traces of the CCD, not
fabrication profiles. Clamp envelopes, stock length and installation limits are
published dimensions. No capacity is inferred from this geometry.
"""

from dataclasses import dataclass

INCH_M = 0.0254
STOCK_LENGTH_IN = 92.0
MAX_END_CANTILEVER_IN = 8.0
MAX_SUPPORT_SPACING_IN = 42.0
SPLICE_GAP_IN = 0.125  # diagrammatic expansion gap; not a field setting
CLAMP_LENGTH_IN = 2.0
CLAMP_MINI_LENGTH_IN = 1.18
CLAMP_WIDTH_IN = 1.57
CLAMP_HEIGHT_IN = 1.77
CLAMP_THROAT_WIDTH_IN = 0.84
CLAMP_THROAT_HEIGHT_IN = 1.10
CLAMP_TOE_BELOW_SEAM_TOP_IN = 0.95
RAIL_DOWNSLOPE_IN = 1.25
RAIL_HEIGHT_IN = 2.15
RAIL_FLANGE_HEIGHT_FROM_BOTTOM_IN = 0.75
RAIL_BASE_WIDTH_IN = 1.50
EXTRUSION_WALL_IN = 0.10
COLORSTRIP_WIDTH_IN = 2.0
VERSACLIP_WIDTH_IN = 1.5
VERSACLIP_FOOT_END_IN = -0.5
VERSACLIP_RISE_END_IN = -0.25
SNOCLIP_WIDTH_IN = 3.0
SNOCLIP_FOOT_DEPTH_IN = 0.5
SNOCLIP_SHEET_IN = 0.08
SPLICE_LENGTH_IN = 4.0
BOLT_HEAD_WIDTH_IN = 0.5
BOLT_HEAD_HEIGHT_IN = 0.2
BOLT_CENTRE_DOWNSLOPE_IN = -0.75
GEOMETRY_TOLERANCE_M = 1e-8
PAINTED_SURFACE = (0.45, 0.05)  # roughness, metalness; PVDF is a dielectric coating
ALUMINUM_MATERIAL = "aluminum-6000-series"
STAINLESS_MATERIAL = "stainless-steel-300-series"
COMPONENT_SURFACES = {
    ALUMINUM_MATERIAL: (0.32, 0.75),
    STAINLESS_MATERIAL: (0.32, 0.75),
    "epdm": (0.9, 0.0),
}

SOURCE = "https://www.s-5.com/products/colorgard/ — ColorGard 2.0; installation 110426"


@dataclass(frozen=True)
class SnowRetentionPurchasePart:
    model: str
    name: str
    included: str = ""


CROSSMEMBER = SnowRetentionPurchasePart(
    "ColorGard 2.0 Unpunched", "ColorGard 2.0 unpunched crossmember, 7 ft 8 in",
    "one splice supplied per crossmember")
VERSACLIP = SnowRetentionPurchasePart("VersaClip 2.0", "ColorGard VersaClip 2.0")
SNOCLIP = SnowRetentionPurchasePart(
    "SnoClip 2.0 II", "ColorGard SnoClip 2.0 II with rubber foot", "securing screw included")
COLORSTRIP = SnowRetentionPurchasePart(
    "ColorGard ColorStrip", "2-inch roof-matching ColorStrip, cut to run length")
