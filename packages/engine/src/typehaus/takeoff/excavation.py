"""The over-dig, billed: cut, haul-off, backfill, cap and the wall drain columns.

Everything placed at the backfill stage bills here, off the resolved records
(``model.excavations``, ``model.wall_columns``). The footing beds keep their own
``footing_bedding`` rows, so a join already written against those keys still holds.

``backfill`` is a PLACEMENT quantity — native lifts plus the column stone the same crew
places — while ``drain-column-stone`` is the stone as delivered; price them that way.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel

_M3_TO_CY = 1.30795062
_M2_TO_FT2 = 10.7639104


def _row(item: str, quantity: float, unit: str, basis: str, **extra: object) -> dict[str, object]:
    return {"item": item, "quantity": round(quantity, 2), "unit": unit, "basis": basis, **extra}


def excavation_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for exc in sorted(model.excavations, key=lambda e: e.uid):
        rows += [
            _row("cut", exc.cut_bank_m3 * _M3_TO_CY, "cy", "bank", excavation=exc.tag),
            _row("haul-off", exc.haul_off_loose_m3 * _M3_TO_CY, "cy",
                 f"loose (swell {exc.swell:.0%})", excavation=exc.tag),
            _row("backfill", (exc.native_m3 + exc.column_m3) * _M3_TO_CY, "cy",
                 f"compacted, native in {exc.lift_m / 0.0254:.0f}\" lifts + column stone placed",
                 excavation=exc.tag),
            _row("cap", exc.cap_m3 * _M3_TO_CY, "cy", exc.cap_material, excavation=exc.tag),
        ]
    stone: dict[str, list[float]] = {}
    for column in model.wall_columns:
        entry = stone.setdefault(column.aggregate, [0.0, 0.0, 0])
        entry[0] += column.volume_m3
        entry[1] += column.geotextile_m2
        entry[2] += 1
    for aggregate, (volume, fabric, count) in sorted(stone.items()):
        rows.append(_row("drain-column-stone", volume * _M3_TO_CY, "cy", "placed in the wall",
                         aggregate=aggregate, columns=count))
        if fabric > 0.0:
            rows.append(_row("drain-column-geotextile", fabric * _M2_TO_FT2, "SF",
                             "soil face and top", aggregate=aggregate, columns=count))
    return rows
