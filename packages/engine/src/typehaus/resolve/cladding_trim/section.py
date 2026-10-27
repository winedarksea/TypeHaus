"""Extrude a folded sheet section along a straight trim run."""

from __future__ import annotations

import math

from typehaus.resolve.geometry_ir import GMesh, GSweep, Vec2, Vec3
from typehaus.resolve.geometry_slice import sweep_mesh
from typehaus.resolve.metal_skin_profiles import _inset_section


def folded_section_mesh(
    section: tuple[Vec2, ...],
    origin: Vec3,
    first_axis: Vec3,
    second_axis: Vec3,
    run: Vec3,
    thickness_m: float,
) -> GMesh:
    """Sweep a section polyline in an orthonormal frame, including its sheet thickness.

    Coordinates and thickness are in metres. The two axes span the section plane;
    ``run`` must be perpendicular to it. Reversing a run does not change the section.
    """
    if len(section) < 2 or not math.isfinite(thickness_m) or thickness_m <= 0:
        raise ValueError("a folded section needs two points and a positive thickness")
    vectors = (first_axis, second_axis, run)
    if any(not all(math.isfinite(value) for value in vector) for vector in vectors):
        raise ValueError("section frame vectors must be finite")

    def dot(a, b):
        return sum(x * y for x, y in zip(a, b, strict=True))

    run_length = math.sqrt(dot(run, run))
    if (
        abs(dot(first_axis, first_axis) - 1) > 1e-8
        or abs(dot(second_axis, second_axis) - 1) > 1e-8
        or abs(dot(first_axis, second_axis)) > 1e-8
        or run_length <= 1e-10
        or abs(dot(first_axis, run)) > 1e-8 * run_length
        or abs(dot(second_axis, run)) > 1e-8 * run_length
    ):
        raise ValueError("section frame must be orthonormal and perpendicular to the run")
    if any(not all(math.isfinite(value) for value in point) for point in section):
        raise ValueError("section points must be finite")

    inset = _inset_section(section, thickness_m)
    ring = (*section, *reversed(inset))
    points = tuple(
        tuple(origin[i] + first_axis[i] * u + second_axis[i] * v for i in range(3)) for u, v in ring
    )
    # sweep_mesh expects the first cap's winding to face along the extrusion.
    cross = (
        first_axis[1] * second_axis[2] - first_axis[2] * second_axis[1],
        first_axis[2] * second_axis[0] - first_axis[0] * second_axis[2],
        first_axis[0] * second_axis[1] - first_axis[1] * second_axis[0],
    )
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, (*ring[1:], ring[0]), strict=True))
    if area * dot(cross, run) < 0:
        points = tuple(reversed(points))
    return sweep_mesh(GSweep(profile=points, extrude=run))
