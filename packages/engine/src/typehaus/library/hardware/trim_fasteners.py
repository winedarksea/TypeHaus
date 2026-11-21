"""Trim-to-wood fasteners (decision #147): what ``Material.trim_fastening`` names.

Window-install fasteners would live here too; none is catalogued until a house's maker
publishes its anchorage.
"""

from typehaus.hardware.catalog import (
    EXPOSURE_TREATED,
    ROLE_TRIM_FASTENER,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON

TRIM_FASTENERS = (
    StructuralHardware(
        tag="simpson-t15n250sfn", name="15-gauge DA finishing nail, 2-1/2in, Type 316",
        role=ROLE_TRIM_FASTENER, manufacturer=_SIMPSON, model="T15N250SFN",
        exposure=EXPOSURE_TREATED, finish="ss316",
        source="Simpson Strong-Tie tape collation DA-style angle 15-gauge finishing nail, "
               "2-1/2 in., Type 316 (T15N250SFN, 4,000-qty). AZEK Trim install guide: "
               "stainless or HDG, 1-1/4 in. into solid wood, no staples, brads or wire nails.",
    ),
    StructuralHardware(
        tag="simpson-t08175fs75", name="Fascia-Fastening Solution screw, #8 x 1-3/4in, Type 316",
        role=ROLE_TRIM_FASTENER, manufacturer=_SIMPSON, model="T08175FS75",
        exposure=EXPOSURE_TREATED, finish="ss316",
        source="Simpson Strong-Tie Fascia-Fastening Solution, #8 x 1-3/4 in. pancake head, "
               "Type 17 point, T20, Type 316; colour suffix per board (T08175FS75xx); "
               "counterbore bit FSBIT. A Trex TF-0823 recommended fascia fastener.",
    ),
)
