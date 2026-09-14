"""The shape of one hardware BOM line.

A row is a *take-off* artefact, not a catalog one: the catalog says what a part is and
where the number came from, and a row says how many of it this building needs. It lives
in its own module rather than in :mod:`typehaus.takeoff.hardware` because every
derivation below that entry point builds rows, and the entry point imports them all.
"""

from __future__ import annotations

from typehaus.hardware.catalog import StructuralHardware


def hardware_row(item: StructuralHardware | None, *, scope: str, count: int, basis: str,
                 part_number: str | None = None, size: str | None = None,
                 length_ft: float | None = None, coils: int | None = None,
                 by_storey: dict | None = None) -> dict:
    """One BOM line: what it is, how many, and the rule that produced the number.

    ``basis`` is not decoration — a hardware count is only auditable if the line carries
    the spacing/condition it came from, so every row states it.
    """
    return {
        "scope": scope,
        "role": item.role if item else None,
        "hardware_tag": item.tag if item else None,
        "description": item.name if item else scope,
        "manufacturer": item.manufacturer if item else None,
        "part_number": part_number if part_number is not None else (item.model if item else None),
        "size": size,
        "unit": item.unit if item else "each",
        "count": count,
        "length_ft": round(length_ft, 1) if length_ft is not None else None,
        "coils": coils,
        "basis": basis,
        "source": item.source if item else None,
        "by_storey": by_storey,
    }
