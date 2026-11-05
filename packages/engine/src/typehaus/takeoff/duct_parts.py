"""Duct parts, hangers and sealing, off ``ResolvedModel.duct_parts`` / ``duct_supports`` (#114).

Elbows stay in ``[duct_fittings]`` (``takeoff/mep.duct_fitting_takeoff``); these are every
other part on a run. An integral part (the terminal's own collar) is not billed; a part the
standard has no row for is billed with no product, so the estimator sees the hole.
"""

from __future__ import annotations

import math

from typehaus.resolve.model import ResolvedModel

_FT = 0.3048


def duct_part_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per (kind, size, branch, product): count, the runs it is on."""
    rows: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for part in model.duct_parts:
        if part.integral:
            continue
        product = part.product_ref or ""
        key = (part.kind, part.size, part.branch or "", product)
        row = rows.setdefault(key, {
            "kind": part.kind, "size": part.size, "branch": part.branch,
            "product": part.product_ref, "fabricated": part.fabricated and not product,
            "source": ("shop-fabricated" if part.fabricated else "not specified")
            if not product else "", "count": 0, "length_ft": 0.0, "tags": set()})
        row["count"] = int(row["count"]) + 1  # type: ignore[call-overload]
        if part.kind == "flex" and part.length_m:
            row["length_ft"] = round(float(row["length_ft"]) + part.length_m / _FT, 2)  # type: ignore[arg-type]
        row["tags"].add(part.run_tag)  # type: ignore[union-attr]
    return [{**row, "tags": sorted(row["tags"])}  # type: ignore[call-overload]
            for _, row in sorted(rows.items())]


def duct_support_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per (product, hanger, size): count and the runs it hangs."""
    rows: dict[tuple[str, str, str], dict[str, object]] = {}
    for support in model.duct_supports:
        key = (support.product_ref or "", support.hanger, support.size)
        row = rows.setdefault(key, {"product": support.product_ref, "hanger": support.hanger,
                                    "size": support.size, "count": 0, "drop_ft": 0.0,
                                    "unhung": 0, "tags": set()})
        row["count"] = int(row["count"]) + 1  # type: ignore[call-overload]
        row["drop_ft"] = round(float(row["drop_ft"]) + support.drop_m / _FT, 1)  # type: ignore[arg-type]
        if support.hangs_from is None:
            row["unhung"] = int(row["unhung"]) + 1  # type: ignore[call-overload]
        row["tags"].add(support.run_tag)  # type: ignore[union-attr]
    return [{**row, "tags": sorted(row["tags"])}  # type: ignore[call-overload]
            for _, row in sorted(rows.items())]


def seam_lengths_m(model: ResolvedModel) -> tuple[float, float]:
    """(longitudinal seam, transverse joint) metres over every rigid run.

    Longitudinal: one snap-lock seam per round run, four corner seams per rectangular run,
    over the developed length. Transverse: one joint per ``joint_length`` of stock, plus two
    ends per elbow and per billed part, each one girth (pi D, or the perimeter). Flex is
    jointed at its kit's ends, which the part count already carries.
    """
    from typehaus.resolve.duct_standard import duct_standard
    from typehaus.resolve.mep_fittings import FAMILY_DUCT, fitting_records

    standard, _ = duct_standard(model.plan)
    stick = standard.joint_length.meters if standard is not None else 5 * _FT
    girth = {}
    longitudinal = transverse = 0.0
    for duct in model.ducts:
        if duct.material == "flex":
            continue
        round_ = duct.diameter_m is not None
        girth[duct.tag] = (math.pi * duct.diameter_m if round_
                           else 2.0 * (duct.width_m + duct.depth_m))
        longitudinal += duct.length_m * (1 if round_ else 4)
        transverse += math.ceil(duct.length_m / stick) * girth[duct.tag]
    elbows = [r for r in fitting_records(model) if r.family == FAMILY_DUCT]
    transverse += sum(2 * girth.get(r.run_tag, 0.0) for r in elbows)
    transverse += sum(2 * girth.get(p.run_tag, 0.0) for p in model.duct_parts if p.billed)
    return longitudinal, transverse


def duct_sealing_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Tape on the longitudinal seams, mastic on every transverse joint and fitting.

    ``count`` is containers or rolls, None where the standard reads no coverage.
    """
    from typehaus.resolve.duct_standard import duct_standard

    standard, _ = duct_standard(model.plan)
    if standard is None or not model.ducts:
        return []
    longitudinal, transverse = seam_lengths_m(model)
    rows = []
    if standard.sealant_product_ref:
        lf = transverse / _FT
        cover = standard.sealant_coverage_lf
        rows.append({"product": standard.sealant_product_ref, "use": "transverse joints",
                     "seam_ft": round(lf, 1), "unit": "container",
                     "count": math.ceil(lf / cover) if cover else None})
    if standard.tape_product_ref:
        lf = longitudinal / _FT
        roll = standard.tape_roll_length
        rows.append({"product": standard.tape_product_ref, "use": "longitudinal seams",
                     "seam_ft": round(lf, 1), "unit": "roll",
                     "count": math.ceil(lf / (roll.meters / _FT)) if roll else None})
    return rows
