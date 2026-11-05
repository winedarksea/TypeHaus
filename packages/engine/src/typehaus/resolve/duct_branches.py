"""Tees, take-offs and reducers where one duct joins another (decision #114, M4-102).

An end landing mid-run on another duct (``mep_soffit.duct_joint_index``, the joint test the
occupancy checks already excuse a tee with) is a take-off, or a tee where the two sections
are equal. An end landing on another run's end with a different section is a reducer; the
same section is a plain joint and takes no part.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from typing import Any

from typehaus.model.ducts import DuctStandard, duct_size_text
from typehaus.resolve.mep_soffit import DUCT_JOINT_TOLERANCE_M, duct_joint_index
from typehaus.resolve.model_ducts import Point3, ResolvedDuctPart


def section(duct: Any) -> str:
    return duct_size_text(duct.diameter_m, duct.width_m, duct.depth_m)


def section_area(duct: Any) -> float:
    if duct.diameter_m is not None:
        return math.pi * duct.diameter_m ** 2 / 4.0
    return duct.width_m * duct.depth_m


def duct_ends(duct: Any) -> Iterator[tuple[int, Point3, Point3]]:
    """(vertex index, end point, unit axis from the end into the run) for both ends."""
    path, z = duct.path, duct.z_m
    if len(path) < 2 or len(z) != len(path):
        return
    points = [(x, y, zz) for (x, y), zz in zip(path, z, strict=True)]
    for index, step in ((0, 1), (len(points) - 1, -1)):
        end = points[index]
        axis = (0.0, 0.0, 1.0)
        k = index + step
        while 0 <= k < len(points):
            d = tuple(b - a for a, b in zip(end, points[k], strict=True))
            norm = math.sqrt(sum(v * v for v in d))
            if norm > 1e-6:
                axis = (d[0] / norm, d[1] / norm, d[2] / norm)
                break
            k += step
        yield index, end, axis


def _at_end(point: Point3, other: Any) -> bool:
    """Whether ``point`` is one of ``other``'s end vertices (within the joint tolerance)."""
    for index in (0, len(other.path) - 1):
        x, y = other.path[index]
        z = other.z_m[index] if other.z_m else point[2]
        if math.dist((x, y, z), point) <= DUCT_JOINT_TOLERANCE_M:
            return True
    return False


def branch_parts(model: Any, standard: DuctStandard) -> list[ResolvedDuctPart]:
    """Every tee, take-off and reducer, once per joint, in run-tag order."""
    out: list[ResolvedDuctPart] = []
    seen: set[tuple[str, str]] = set()
    ducts = sorted(model.ducts, key=lambda d: d.tag)
    for duct in ducts:
        for _, point, axis in duct_ends(duct):
            for main in ducts:
                if main is duct or len(main.path) < 2:
                    continue
                if duct_joint_index(point[:2], point[2], main.path, main.z_m) is None:
                    continue
                pair = tuple(sorted((duct.tag, main.tag)))
                if pair in seen:
                    continue
                part = _joint(standard, duct, main, point, axis)
                if part is not None:
                    seen.add(pair)  # type: ignore[arg-type]
                    out.append(part)
                break
    return out


def _joint(standard: DuctStandard, duct: Any, main: Any, point: Point3,
           axis: Point3) -> ResolvedDuctPart | None:
    branch, trunk = section(duct), section(main)
    if _at_end(point, main):
        if branch == trunk:
            return None
        big, small = ((main, duct) if section_area(main) >= section_area(duct)
                      else (duct, main))
        kind, size, out_size, run, other = ("reducer", section(big), section(small),
                                            big.tag, small.tag)
    else:
        kind = "tee" if branch == trunk else "takeoff"
        size, out_size, run, other = trunk, branch, main.tag, duct.tag
    row = standard.part(kind, size, out_size)
    return ResolvedDuctPart(
        kind=kind, run_tag=run, storey=main.storey, size=size, branch=out_size,
        point=point, axis=axis, other=other,
        product_ref=row.product_ref if row else None,
        fabricated=bool(row and row.fabricated), integral=bool(row and row.integral),
        length_m=row.length.meters if row and row.length else None,
        width_m=row.width.meters if row and row.width else None,
        height_m=row.height.meters if row and row.height else None,
        gap=None if row else f"the duct standard has no {kind} row for {size} x {out_size}")
