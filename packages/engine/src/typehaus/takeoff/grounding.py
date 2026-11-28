"""Grounding and bonding parts by the piece and the foot (decision #123, → resolve/grounding.py).

``[grounding]`` (ea) bills the hardware keyed on the Product tag; ``[grounding_conductors]``
(LF) the bonds by ``"<size> <material>"``. Not here: the galvanized electrode bar (bills in
``reinforcement``), SPDs and the IBT (devices, billed by their ED-T-* type in ``[placeables]``).
"""

from __future__ import annotations

import math
from collections import defaultdict

from typehaus.resolve.model import ResolvedModel

_FT = 0.3048


def _row(model: ResolvedModel, rows: dict[str, dict[str, object]], ref: str, role: str,
         tag: str, count: int = 1) -> None:
    product = model.plan.library.product(ref)
    row = rows.setdefault(ref, {
        "product": ref, "role": role, "count": 0, "tags": [],
        "name": (product.name or product.model) if product is not None else ref})
    row["count"] = int(row["count"]) + count  # type: ignore[call-overload]
    row["tags"].append(tag)  # type: ignore[union-attr]


def grounding_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per hardware Product: a rod and its acorn clamp each per rod electrode, the
    encased clamp per concrete-encased electrode, one Al-Cu transition and ``ceil(L/spacing)``
    screw-mounted conductor holders per aluminium down-lead."""
    grounding = model.grounding
    std = getattr(grounding, "standard", None)
    if std is None:
        return []
    rows: dict[str, dict[str, object]] = {}
    for el in grounding.electrodes:
        if el.kind == "rod":
            _row(model, rows, std.rod_product_ref, "rod", el.tag)
            _row(model, rows, std.rod_clamp_product_ref, "rod clamp", el.tag)
        elif el.kind == "concrete_encased" and std.encased_clamp_product_ref:
            _row(model, rows, std.encased_clamp_product_ref, "encased-electrode clamp", el.tag)
    spacing = std.conductor_fastener_spacing.meters if std.conductor_fastener_spacing else 0.0
    for bond in grounding.bonds:
        if bond.role != "down_lead":
            continue
        if std.transition_product_ref and bond.material == "aluminum":
            _row(model, rows, std.transition_product_ref, "Al-Cu transition", bond.tag)
        # Clips hold the above-grade run only: the part of the path at or above grade.
        exposed = _above_grade_m(model, bond)
        if std.conductor_fastener_product_ref and spacing > 0 and exposed > 0:
            n = max(1, math.ceil(exposed / spacing - 1e-9))
            _row(model, rows, std.conductor_fastener_product_ref, "conductor fastener",
                 bond.tag, n)
    return [{**row, "tags": sorted(row["tags"])}  # type: ignore[arg-type]
            for row in (rows[key] for key in sorted(rows))]


def grounding_conductor_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per (size, material): net LF off ``ResolvedBond.length_m``, no slack. A bond
    with no path is a straight 3D distance (``straight_line``), so those lengths are minimums;
    ``unlocated`` bonds bill nothing and are counted in ``unlocated``."""
    grounding = model.grounding
    if grounding is None:
        return []
    length: dict[tuple[str, str], float] = defaultdict(float)
    tags: dict[tuple[str, str], list[str]] = defaultdict(list)
    straight: dict[tuple[str, str], int] = defaultdict(int)
    unlocated: dict[tuple[str, str], int] = defaultdict(int)
    for bond in grounding.bonds:
        key = (bond.size, bond.material)
        length[key] += bond.length_m
        tags[key].append(bond.tag)
        if bond.length_basis == "straight_line":
            straight[key] += 1
        elif bond.length_basis == "unlocated":
            unlocated[key] += 1
    return [{"size": size, "material": material, "conductor": f"{size} {material}",
             "name": f"#{size} {material} bonding conductor",
             "length_ft": round(length[key] / _FT, 1), "count": len(tags[key]),
             "straight_line": straight[key], "unlocated": unlocated[key],
             "basis": "authored path length, else the straight 3D distance; no slack",
             "tags": sorted(tags[key])}
            for key in sorted(length) for size, material in (key,)]


def _above_grade_m(model, bond) -> float:
    """Length of a bond's path above the site grade."""
    from typehaus.resolve.site_earth import site_grade_elevation_m

    grade_m = site_grade_elevation_m(model)
    pts = bond.path
    if len(pts) < 2:
        return bond.length_m
    total = 0.0
    for a, b in zip(pts, pts[1:], strict=False):
        seg = math.dist(a, b)
        lo, hi = sorted((a[2] - grade_m, b[2] - grade_m))
        if hi <= 0:
            continue
        total += seg if lo >= 0 else seg * hi / (hi - lo)
    return total

