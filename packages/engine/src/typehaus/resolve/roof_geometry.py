"""Shared roof-plane math for ``ToRoof`` walls and ``FollowRoof`` rooms.

Also owns the *final* elevation of a roof plane. A truss roof's deck is lifted by its
raised heel, and that lift has to happen before anything reads the plane — see
:func:`apply_truss_heel_lift`.
"""

from __future__ import annotations

from dataclasses import replace

from shapely.geometry import Polygon

from typehaus.model.assembly import FramingSpec
from typehaus.model.enums import LayerFunction
from typehaus.model.refs import ToRoof
from typehaus.model.spatial import Roof
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel, ResolvedRoof, ResolvedWall

# A standard raised ("energy") heel when a truss assembly does not declare its own.
DEFAULT_TRUSS_HEEL_M = inch(9.25).meters


def roof_height_at(roof: ResolvedRoof, point: tuple[float, float]) -> float:
    """Return the exterior roof-plane elevation at a plan-frame point."""
    xs = [item[0] for item in roof.footprint]
    ys = [item[1] for item in roof.footprint]
    coordinate = point[1] if roof.ridge_direction == "x" else point[0]
    low, high = (min(ys), max(ys)) if roof.ridge_direction == "x" else (min(xs), max(xs))
    span = high - low
    if span <= 1e-9:
        return roof.eave_z_m
    if roof.form == "shed":
        return roof.eave_z_m + (coordinate - low) / span * (roof.ridge_z_m - roof.eave_z_m)
    midpoint = (low + high) / 2.0
    ratio = max(0.0, 1.0 - abs(coordinate - midpoint) / (span / 2.0))
    return roof.eave_z_m + ratio * (roof.ridge_z_m - roof.eave_z_m)


def roof_structure_framing(model: ResolvedModel, roof: ResolvedRoof) -> FramingSpec | None:
    """The ``FramingSpec`` on the roof assembly's STRUCTURE layer (``None`` if unframed)."""
    assembly = model.plan.library.resolve_assembly(roof.assembly)
    if assembly is None:
        return None
    layer = next((ly for ly in assembly.layers
                  if ly.function is LayerFunction.STRUCTURE and ly.framing is not None), None)
    return layer.framing if layer is not None else None


def truss_heel_height_m(spec: FramingSpec) -> float:
    """Authored raised-heel height, or the standard energy heel."""
    return spec.heel_height.meters if spec.heel_height is not None else DEFAULT_TRUSS_HEEL_M


def truss_chord_depth_m(spec: FramingSpec) -> float:
    return cross_section(spec.chord_member or spec.member).depth_m


def roof_structure_depth_m(model: ResolvedModel, roof: ResolvedRoof) -> float:
    """Depth of the roof's structural plane: chord depth for a truss, member depth else."""
    spec = roof_structure_framing(model, roof)
    if spec is None:
        return 0.0
    if spec.roof_frame == "truss":
        return truss_chord_depth_m(spec)
    return cross_section(spec.member).depth_m


def roof_underside_at(model: ResolvedModel, roof: ResolvedRoof,
                      point: tuple[float, float]) -> float:
    """Underside of the roof structure at a plan point — what a wall below must reach."""
    return roof_height_at(roof, point) - roof_structure_depth_m(model, roof)


def roof_bearing_walls(model: ResolvedModel, roof: ResolvedRoof) -> tuple[ResolvedWall, ...]:
    element = model.plan.by_tag(roof.tag)
    if not isinstance(element, Roof):
        return ()
    return tuple(wall for tag in element.bearing_refs
                 if (wall := model.wall(tag)) is not None)


def truss_heel_lift_m(model: ResolvedModel, roof: ResolvedRoof) -> float:
    """How far a truss roof's deck plane rises so the raised heel fits over the bearings.

    The top-chord *underside* must clear ``plate top + heel`` at every bearing, which lifts
    the whole plane (chords lie on the deck). Zero for a rafter roof or an unresolvable
    bearing line — never a guess.
    """
    spec = roof_structure_framing(model, roof)
    if spec is None or spec.roof_frame != "truss":
        return 0.0
    walls = roof_bearing_walls(model, roof)
    if len(walls) < 2:
        return 0.0
    plate_top = max(wall.z1_m for wall in walls)
    needed = plate_top + truss_heel_height_m(spec) + truss_chord_depth_m(spec)
    return max(0.0, max(needed - roof_height_at(roof, wall.axis[0]) for wall in walls))


def apply_truss_heel_lift(model: ResolvedModel) -> None:
    """Raise every truss roof plane by its heel lift, during the *envelope* stage.

    Framing used to do this, two stages after ``apply_to_roof_wall_tops`` — so a ``ToRoof``
    wall raked to the pre-lift plane and stopped a heel-plus-chord short of the roof it was
    supposed to meet. Establishing the final plane here keeps one source of truth for every
    downstream consumer (raked wall tops, ``FollowRoof`` ceilings, headroom, framing).
    """
    model.roofs = [
        roof if (lift := truss_heel_lift_m(model, roof)) <= 0.0
        else replace(roof, eave_z_m=roof.eave_z_m + lift, ridge_z_m=roof.ridge_z_m + lift)
        for roof in model.roofs
    ]


def apply_to_roof_wall_tops(model: ResolvedModel) -> None:
    """Resolve raked wall endpoints after roof envelopes have been established."""
    roofs = {roof.tag: roof for roof in model.roofs}
    resolved: list[ResolvedWall] = []
    for wall in model.walls:
        authored = model.plan.by_tag(wall.tag)
        top = getattr(authored, "top", None)
        if not isinstance(top, ToRoof) or top.roof_ref not in roofs:
            resolved.append(wall)
            continue
        roof = roofs[top.roof_ref]
        start_top = roof_height_at(roof, wall.axis[0])
        end_top = roof_height_at(roof, wall.axis[1])
        resolved.append(ResolvedWall(
            uid=wall.uid, tag=wall.tag, storey=wall.storey, assembly=wall.assembly,
            axis=wall.axis, layers=wall.layers, z0_m=wall.z0_m,
            z1_m=max(start_top, end_top), is_foundation=wall.is_foundation,
            members=wall.members, top_z0_m=start_top, top_z1_m=end_top,
        ))
    model.walls = resolved


def roof_headroom_areas(room_ring: list[tuple[float, float]], roof: ResolvedRoof,
                        elevation_m: float, threshold_m: float) -> tuple[float, float]:
    """Return room area and area at/above a headroom threshold.

    Gable roof halves are linear planes.  Clipping each half against the corresponding
    threshold strip keeps the code result exact for arbitrary room polygons rather than
    relying on a display-resolution sample grid.
    """
    room = Polygon(room_ring).intersection(Polygon(roof.footprint))
    if room.is_empty:
        return (0.0, 0.0)
    total = room.area
    required_z = elevation_m + threshold_m
    xs = [item[0] for item in roof.footprint]
    ys = [item[1] for item in roof.footprint]
    low, high = (min(ys), max(ys)) if roof.ridge_direction == "x" else (min(xs), max(xs))
    rise = roof.ridge_z_m - roof.eave_z_m
    if rise <= 1e-9:
        return total, total if roof.eave_z_m >= required_z else 0.0
    ratio = (required_z - roof.eave_z_m) / rise
    if ratio <= 0:
        return total, total
    if ratio > 1:
        return total, 0.0
    midpoint = (low + high) / 2.0
    extent = max(max(xs) - min(xs), max(ys) - min(ys)) + 1.0
    if roof.ridge_direction == "x":
        if roof.form == "shed":
            qualifying = Polygon([(min(xs) - extent, low + ratio * (high - low)),
                                  (max(xs) + extent, low + ratio * (high - low)),
                                  (max(xs) + extent, max(ys) + extent),
                                  (min(xs) - extent, max(ys) + extent)])
        else:
            lo = low + ratio * (midpoint - low)
            hi = high - ratio * (high - midpoint)
            qualifying = Polygon([(min(xs) - extent, lo), (max(xs) + extent, lo),
                                  (max(xs) + extent, hi), (min(xs) - extent, hi)])
    else:
        if roof.form == "shed":
            qualifying = Polygon([(low + ratio * (high - low), min(ys) - extent),
                                  (max(xs) + extent, min(ys) - extent),
                                  (max(xs) + extent, max(ys) + extent),
                                  (low + ratio * (high - low), max(ys) + extent)])
        else:
            lo = low + ratio * (midpoint - low)
            hi = high - ratio * (high - midpoint)
            qualifying = Polygon([(lo, min(ys) - extent), (hi, min(ys) - extent),
                                  (hi, max(ys) + extent), (lo, max(ys) + extent)])
    return total, room.intersection(qualifying).area
