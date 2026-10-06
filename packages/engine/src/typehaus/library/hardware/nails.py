"""Dimensioned common/connector nails; counted by nail rather than retail package."""

from typehaus.hardware.catalog import EXPOSURE_DRY, StructuralHardware

DIAPHRAGM_NAILS = (
    StructuralHardware(
        tag="connector-nail-0148-15",
        name="Smooth-shank connector nail, 0.148in x 1.5in",
        role="blocking_angle_nail", manufacturer="generic",
        model="0.148x1.5 connector nail", exposure=EXPOSURE_DRY,
        source="Simpson Strong-Tie C-C-2026 p.313, LS30: six 0.148in x 1.5in nails, "
               "three per leg; ASTM F1667 connector nails (N10D5HDG equivalent).",
    ),
    StructuralHardware(
        tag="common-nail-8d-25",
        name="8d common smooth-shank nail, 0.131in x 2.5in",
        role="diaphragm_deck_nail", manufacturer="generic",
        model="8d common 0.131x2.5", exposure=EXPOSURE_DRY,
        source="AWC NDS 2018 Table L4, 8d common; Simpson Strong-Tie Fastener Overview "
               "— Nails, common dimensions per AWC/NDS Table L4; ASTM F1667.",
    ),
    StructuralHardware(
        tag="connector-nail-0148-25",
        name="Smooth-shank strap nail, 0.148in x 2.5in",
        role="diaphragm_strap_nail", manufacturer="generic",
        model="10d short common 0.148x2.5", exposure=EXPOSURE_DRY,
        source="Simpson Strong-Tie C-C-2026 p.291 and LSTA installation guide: "
               "0.148in x 2.5in nails; ASTM F1667 smooth-shank full-head connector "
               "nails (N10DHDGPT500 equivalent).",
    ),
)
