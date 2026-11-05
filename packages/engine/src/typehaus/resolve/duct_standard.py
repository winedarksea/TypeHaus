"""The house's one ``DuctStandard`` and ``integrity.duct_standard`` (decision #114)."""

from __future__ import annotations

from typing import Any

from typehaus.findings import Finding, Result, Severity
from typehaus.model.ducts import DuctElbowRow, DuctStandard

CHECK_ID = "integrity.duct_standard"

_CACHE: dict[int, tuple[Any, DuctStandard | None, tuple[Finding, ...]]] = {}


def duct_standard(plan: Any) -> tuple[DuctStandard | None, list[Finding]]:
    """The standard (or None), with the integrity findings that refuse it. Memoised per plan."""
    if not hasattr(plan, "all_elements"):  # no plan, or a test's stub
        return None, []
    cached = _CACHE.get(id(plan))
    if cached is not None and cached[0] is plan:
        return cached[1], list(cached[2])
    standard, findings = _read(plan)
    if len(_CACHE) > 8:
        _CACHE.clear()
    _CACHE[id(plan)] = (plan, standard, tuple(findings))
    return standard, findings


def _read(plan: Any) -> tuple[DuctStandard | None, list[Finding]]:
    found = [el for el in plan.all_elements() if isinstance(el, DuctStandard)]
    if not found:
        return None, []
    if len(found) > 1:
        tags = tuple(sorted(el.tag for el in found))
        return None, [_error(tags, f"a house declares at most one DuctStandard; found "
                                   f"{len(found)}: {', '.join(tags)}")]
    standard = found[0]
    out = [_error((standard.tag,), f"duct standard {standard.tag} names no product {ref!r}")
           for ref in standard.product_refs() if plan.library.product(ref) is None]
    for row in standard.elbows:
        if not row.angles:
            out.append(_error((standard.tag,), f"duct standard {standard.tag}: the "
                                               f"{row.diameter} elbow is bought at no angle"))
    types = {t.tag for t in plan.library.equipment_types}
    out.extend(_error((standard.tag,), f"duct standard {standard.tag}: port kit names no "
                                       f"equipment type {kit.type_ref!r}")
               for kit in standard.port_kits if kit.type_ref not in types)
    return (None if out else standard), out


def _error(tags: tuple[str, ...], message: str) -> Finding:
    return Finding(severity=Severity.ERROR, check_id=CHECK_ID, result=Result.FAIL,
                   message=message, element_tags=tags)


#: A turn within this of a bought angle is made with that elbow.
ELBOW_SNAP_DEG = 10.0


def elbow_for_turn(standard: DuctStandard, diameter_m: float,
                   angle_deg: float) -> tuple[DuctElbowRow, float] | None:
    """(row, stock angle) for a round turn: a fixed (stamped) elbow within the snap of one
    of its angles first, else an adjustable one set down from the smallest angle at or
    above the turn. None where neither makes it (a reversal, or no row at the size)."""
    rows = [r for r in standard.elbows if abs(r.diameter.meters - diameter_m) < 1e-4]
    for row in rows:
        if row.kind != "adjustable" and row.angles:
            stock = min(row.angles, key=lambda a: abs(a - angle_deg))
            if abs(stock - angle_deg) <= ELBOW_SNAP_DEG:
                return row, stock
    for row in rows:
        if row.kind == "adjustable":
            for stock in sorted(row.angles):
                if angle_deg <= stock + ELBOW_SNAP_DEG:
                    return row, stock
    return None


def duct_elbow_key(standard: DuctStandard | None, angle_deg: float, size: str,
                   diameter_m: float | None = None) -> str | None:
    """The elbow row a duct turn is billed on, off the elbows the standard buys (M4-108).

    A round turn takes ``elbow_for_turn``'s row (``elbow-adj-`` for an adjustable one); a
    rectangular turn, or a size with no row, snaps to the standard's angles, and past the
    largest is a ``bend``. None without a standard: the caller keeps its stock list.
    """
    if standard is None:
        return None
    hit = elbow_for_turn(standard, diameter_m, angle_deg) if diameter_m else None
    if hit is not None:
        row, stock = hit
        return f"elbow-{'adj-' if row.kind == 'adjustable' else ''}{stock:g}-{size}"
    angles = sorted({a for row in standard.elbows for a in row.angles}) or [90.0]
    for stock in angles:
        if angle_deg <= stock + ELBOW_SNAP_DEG:
            return f"elbow-{stock:g}-{size}"
    return f"bend-{round(angle_deg / 5.0) * 5:g}-{size}"
