"""``[linesets]``: one row per refrigerant set, its kit length the thing ordered (#139).

The tube is bought as a pre-flared, pre-insulated kit, so this table is the order and the
allowance a house prices it under is driven off ``kit_length_ft`` — never also a
``[pipe_runs]`` refrigerant price, which would bill the copper twice.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

_M_TO_FT = 3.280839895
_M_PER_IN = 0.0254


def tube_size_text(od_m: float) -> str:
    """``3/8``, ``3/4``, ``1 1/8``: a tube OD to the nearest sixteenth, as ordered."""
    inches = Fraction(round(od_m / _M_PER_IN * 16), 16)
    whole, rest = divmod(inches, 1)
    if not rest:
        return f"{whole}"
    return f"{whole} {rest}" if whole else f"{rest}"


def _ft(value_m: float | None) -> float | None:
    return None if value_m is None else round(value_m * _M_TO_FT, 1)


def lineset_takeoff(model: Any) -> list[dict[str, Any]]:
    rows = []
    for lineset in sorted(getattr(model, "linesets", ()), key=lambda item: item.tag):
        rows.append({
            "tag": lineset.tag,
            "head": lineset.head_tag,
            "outdoor": lineset.outdoor_tag,
            "port": lineset.port,
            "size": f"{tube_size_text(lineset.liquid_m)} × {tube_size_text(lineset.vapor_m)}",
            "developed_ft": _ft(lineset.developed_m),
            "ordered_ft": _ft(lineset.ordered_m),
            "kit_length_ft": _ft(lineset.kit_m) or 0.0,
            "leftover_ft": _ft(lineset.leftover_m),
            "field_charge_oz": (None if lineset.field_charge_oz is None
                                else round(lineset.field_charge_oz, 1)),
            "cover_ft": _ft(lineset.exterior_m),
        })
    return rows
