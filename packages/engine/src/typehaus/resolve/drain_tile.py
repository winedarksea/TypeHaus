"""Derived geometry for perforated drain tile.

A ``FootingBedding`` says it runs a tile; a ``FrenchDrain`` says where one runs. Neither
authors the pipe itself, because nobody draws a perimeter ring by hand — it follows the
excavation it sits in. So the tile is *derived*, the way ``EaveGutter`` members are derived
from the eave they hang on, and this module is the one place that derives it: both callers
would otherwise reinvent the same band-per-edge extrusion and disagree about the invert.

Bands rather than a round pipe because ``ResolvedSolid`` extrudes a plan outline vertically
— a run along the plan is a rectangular band of the pipe's own diameter, which is what the
take-off measures and what the 3D drainage toggle needs to show a continuous ring.
"""

from __future__ import annotations

from typehaus.resolve.geometry import rect_between
from typehaus.resolve.model import ResolvedDrainTile, ResolvedSolid

#: Stock perimeter tile where a bedding carries the bare ``drain_tile: bool`` and no spec.
#: The same 4" the perimeter-drain detail falls back to (``detail_components/config.py``).
DEFAULT_DIAMETER_M = 4.0 * 0.0254

#: The pipe floats in stone rather than sitting on the excavation floor, so the invert lifts
#: by one course of bedding. Mirrors ``PerimeterDrainConfig.pipe_bedding_in``.
PIPE_BEDDING_M = 1.0 * 0.0254

SOLID_CATEGORY = "drain_tile"


def tile_diameter_m(spec: ResolvedDrainTile | None) -> float:
    return spec.diameter_m if spec is not None else DEFAULT_DIAMETER_M


def resolved_spec(spec) -> ResolvedDrainTile | None:
    """An authored :class:`~typehaus.model.structure.DrainTile` flattened to SI, or None."""
    if spec is None:
        return None
    return ResolvedDrainTile(
        diameter_m=spec.diameter.meters, material=spec.material, sock=spec.sock,
        discharge=spec.discharge,
        rock_width_m=spec.rock_width.meters if spec.rock_width is not None else None,
        rock_depth_m=spec.rock_depth.meters if spec.rock_depth is not None else None,
    )


def drain_tile_solids(uid: str, tag: str, storey: str, path, floor_z_m: float,
                      spec: ResolvedDrainTile | None,
                      closed: bool = True) -> list[ResolvedSolid]:
    """One band per run segment, from ``floor_z_m`` up one pipe diameter.

    ``path`` is a plan polyline; ``closed`` runs the segment back to the start, which is what
    a footing-bedding perimeter does and an open french-drain run does not. ``floor_z_m`` is
    the excavation floor — the invert lifts off it by :data:`PIPE_BEDDING_M`.
    """
    points = [tuple(point) for point in path]
    if len(points) < 2:
        return []
    if closed and points[0] != points[-1]:
        points.append(points[0])
    diameter = tile_diameter_m(spec)
    half = diameter / 2.0
    z0 = floor_z_m + PIPE_BEDDING_M
    solids: list[ResolvedSolid] = []
    # strict=True: two slices of the same list, both length len(points) - 1.
    for index, (start, end) in enumerate(zip(points[:-1], points[1:], strict=True)):
        if start == end:
            continue
        solids.append(ResolvedSolid(
            uid=f"{uid}-DT-{index:02d}", tag=f"{tag}-DT-{index + 1}", storey=storey,
            category=SOLID_CATEGORY, outline=rect_between(start, end, -half, half),
            z0_m=z0, z1_m=z0 + diameter,
        ))
    return solids
