"""Counted nails and connector screws (decision #105); billed by the piece, not the package.

The first three are the diaphragm's HDG nails. The rest are the "upgrade" fasteners the
connector schedules, the treated-framing allowance and the sheathing schedules name: a
contractor quotes exactly these, not "nails". Stainless at a stainless connector, zinc at
a zinc one (Simpson L-F-SSNAILS line 1; IRC R317.3.1 for treated wood).
"""

from typehaus.hardware.catalog import (
    EXPOSURE_TREATED,
    ROLE_CONNECTOR_NAIL,
    ROLE_SHEATHING_NAIL,
    ROLE_STAINLESS_FRAMING_NAIL,
    ROLE_TREATED_FRAMING_NAIL,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON

_C_C_2026 = "Simpson Strong-Tie C-C-2026 p.25 (Strong-Drive SCN / SCNR connector nails)"

DIAPHRAGM_NAILS = (
    StructuralHardware(
        tag="connector-nail-0148-15",
        name="HDG smooth-shank connector nail, 0.148in x 1.5in",
        role=ROLE_CONNECTOR_NAIL, manufacturer="generic",
        model="0.148x1.5 connector nail", exposure=EXPOSURE_TREATED, finish="hdg",
        source="Simpson Strong-Tie C-C-2026 p.313, LS30: six 0.148in x 1.5in nails, "
               "three per leg; ASTM F1667 connector nails (N10D5HDG equivalent).",
    ),
    StructuralHardware(
        tag="common-nail-8d-25",
        name="HDG 8d common smooth-shank nail, 0.131in x 2.5in",
        role="diaphragm_deck_nail", manufacturer="generic",
        model="8d common 0.131x2.5", exposure=EXPOSURE_TREATED, finish="hdg",
        source="AWC NDS 2018 Table L4, 8d common; Simpson Strong-Tie Fastener Overview "
               "— Nails, common dimensions per AWC/NDS Table L4; ASTM F1667.",
    ),
    StructuralHardware(
        tag="connector-nail-0148-25",
        name="HDG smooth-shank strap nail, 0.148in x 2.5in",
        role="diaphragm_strap_nail", manufacturer="generic",
        model="10d short common 0.148x2.5", exposure=EXPOSURE_TREATED, finish="hdg",
        source="Simpson Strong-Tie C-C-2026 p.291 and LSTA installation guide: "
               "0.148in x 2.5in nails; ASTM F1667 smooth-shank full-head connector "
               "nails (N10DHDGPT500 equivalent).",
    ),
)

CONNECTOR_NAILS = (
    StructuralHardware(
        tag="connector-nail-0131-15",
        name="HDG smooth-shank connector nail, 0.131in x 1.5in",
        role=ROLE_CONNECTOR_NAIL, manufacturer="generic",
        model="0.131x1.5 connector nail", exposure=EXPOSURE_TREATED, finish="hdg",
        source=f"{_C_C_2026}: N8DHDG, 0.131 x 1-1/2 HDG; ASTM F1667.",
    ),
    StructuralHardware(
        tag="common-nail-16d-35",
        name="HDG 16d common nail, 0.162in x 3.5in",
        role=ROLE_CONNECTOR_NAIL, manufacturer="generic",
        model="16d common 0.162x3.5", exposure=EXPOSURE_TREATED, finish="hdg",
        source=f"{_C_C_2026}: 16DHDG-R, 0.162 x 3-1/2 HDG; ASTM F1667.",
    ),
    StructuralHardware(
        tag="simpson-ssa8d", name="SCNR ring-shank connector nail, 0.131in x 2.5in, Type 316",
        role=ROLE_CONNECTOR_NAIL, manufacturer=_SIMPSON, model="SSA8D",
        exposure=EXPOSURE_TREATED, finish="ss316",
        source=f"{_C_C_2026}; L-F-SSNAILS substitution for 8d common at a stainless connector.",
    ),
    StructuralHardware(
        tag="simpson-ssna10d", name="SCNR ring-shank connector nail, 0.148in x 1.5in, Type 316",
        role=ROLE_CONNECTOR_NAIL, manufacturer=_SIMPSON, model="SSNA10D",
        exposure=EXPOSURE_TREATED, finish="ss316",
        source=f"{_C_C_2026}; L-F-SSNAILS substitution for 0.148 x 1-1/2.",
    ),
    StructuralHardware(
        tag="simpson-ssa10d", name="SCNR ring-shank connector nail, 0.148in x 3in, Type 316",
        role=ROLE_CONNECTOR_NAIL, manufacturer=_SIMPSON, model="SSA10D",
        exposure=EXPOSURE_TREATED, finish="ss316",
        source=f"{_C_C_2026}; L-F-SSNAILS substitution for 10d common (0.148 x 3).",
    ),
    StructuralHardware(
        tag="simpson-sd9112", name="Strong-Drive SD connector screw, #9 x 1-1/2in",
        role=ROLE_CONNECTOR_NAIL, manufacturer=_SIMPSON, model="SD9112",
        exposure=EXPOSURE_TREATED, finish="mech_galv",
        source="Simpson Strong-Tie C-C-2026 pp.378-379: mechanically galvanized, ASTM B695 "
               "Class 55, an alternate to hot-dip galvanized (ESR-3046); \"to be used with "
               "galvanized connectors\" (note 1).",
    ),
)

#: The treated-framing allowance's nails. The HDG record is the library DEFAULT for any
#: ``preservative_treated`` member (its role holds one product); a house names stainless
#: per material through ``Project.treated_framing_fasteners``.
TREATED_FRAMING_NAILS = (
    StructuralHardware(
        tag="common-nail-10d-3-hdg",
        name="HDG 10d common nail, 0.148in x 3in, ASTM A153",
        role=ROLE_TREATED_FRAMING_NAIL, manufacturer="generic",
        model="10d common 0.148x3", exposure=EXPOSURE_TREATED, finish="hdg",
        source="IRC R317.3.1 (hot-dip galvanized to ASTM A153 in treated wood); "
               f"{_C_C_2026}: 10DHDG-R, 0.148 x 3 HDG.",
    ),
    StructuralHardware(
        tag="simpson-s10acn", name="10d common ring-shank nail, 0.148in x 3in, Type 304",
        role=ROLE_STAINLESS_FRAMING_NAIL, manufacturer=_SIMPSON, model="S10ACN",
        exposure=EXPOSURE_TREATED, finish="ss304",
        source="Simpson Strong-Tie S10ACN: common nail, annular ring shank, 3in x 0.148in, "
               "Type 304 stainless (toolnut S10ACN1 / S10ACN5 listings, 2026-10-31).",
    ),
)

SHEATHING_NAILS = (
    StructuralHardware(
        tag="rsrs-01-ring-shank-0113",
        name="RSRS-01 roof sheathing ring-shank nail, 0.113in x 2-3/8in, full round head",
        role=ROLE_SHEATHING_NAIL, manufacturer="generic",
        model="RSRS-01 0.113x2.375", finish=None,
        source="2025 FORTIFIED Home Standard §4.2.2: \"minimum RSRS-01; 0.113 in. dia. x 2 3/8 "
               "in. Roof Sheathing Ring Shank Nail at 4 in. o.c. spacing maximum in all areas "
               "of the roof\"; §2.8: ASTM F1667, full round head only (clipped head is not "
               "acceptable). No finish is required; e.g. Paslode RounDrive 0.113 x 2-3/8 bright.",
    ),
    StructuralHardware(
        tag="simpson-s8acn", name="8d common ring-shank nail, 0.131in x 2.5in, Type 304",
        role=ROLE_SHEATHING_NAIL, manufacturer=_SIMPSON, model="S8ACN",
        exposure=EXPOSURE_TREATED, finish="ss304",
        source="Simpson Strong-Tie S8ACN: common nail, annular ring shank, 2-1/2in x 0.131in, "
               "Type 304 stainless (toolnut S8ACN1 / S8ACN5 listings, 2026-10-31).",
    ),
)
