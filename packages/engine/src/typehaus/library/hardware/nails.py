"""Dimensioned common/connector nails, hot-dip galvanized; counted by nail, not package.

HDG to match the ZMAX connectors of the open canopy and for contact with treated wood
(IRC R317.3.1).
"""

from typehaus.hardware.catalog import EXPOSURE_TREATED, StructuralHardware

DIAPHRAGM_NAILS = (
    StructuralHardware(
        tag="connector-nail-0148-15",
        name="HDG smooth-shank connector nail, 0.148in x 1.5in",
        role="blocking_angle_nail", manufacturer="generic",
        model="0.148x1.5 connector nail", exposure=EXPOSURE_TREATED,
        source="Simpson Strong-Tie C-C-2026 p.313, LS30: six 0.148in x 1.5in nails, "
               "three per leg; ASTM F1667 connector nails (N10D5HDG equivalent).",
    ),
    StructuralHardware(
        tag="common-nail-8d-25",
        name="HDG 8d common smooth-shank nail, 0.131in x 2.5in",
        role="diaphragm_deck_nail", manufacturer="generic",
        model="8d common 0.131x2.5", exposure=EXPOSURE_TREATED,
        source="AWC NDS 2018 Table L4, 8d common; Simpson Strong-Tie Fastener Overview "
               "— Nails, common dimensions per AWC/NDS Table L4; ASTM F1667.",
    ),
    StructuralHardware(
        tag="connector-nail-0148-25",
        name="HDG smooth-shank strap nail, 0.148in x 2.5in",
        role="diaphragm_strap_nail", manufacturer="generic",
        model="10d short common 0.148x2.5", exposure=EXPOSURE_TREATED,
        source="Simpson Strong-Tie C-C-2026 p.291 and LSTA installation guide: "
               "0.148in x 2.5in nails; ASTM F1667 smooth-shank full-head connector "
               "nails (N10DHDGPT500 equivalent).",
    ),
)
