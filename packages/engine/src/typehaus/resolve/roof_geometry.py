"""Shared roof-plane math for ``ToRoof`` walls and ``FollowRoof`` rooms.

Also owns the *final* elevation of a roof plane. A truss roof's deck is lifted by its
raised heel, and that lift has to happen before anything reads the plane — see
:func:`apply_truss_heel_lift`.
"""

from __future__ import annotations

import math
from dataclasses import replace

from shapely.geometry import Polygon

from typehaus.model.assembly import FramingSpec
from typehaus.model.enums import LayerFunction
from typehaus.model.refs import ToRoof
from typehaus.model.spatial import Roof
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import cross_section, truss_chord_depth_m
from typehaus.resolve.geometry import polygon_area
from typehaus.resolve.model import ResolvedModel, ResolvedRoof, ResolvedWall

# A standard raised ("energy") heel when a truss assembly does not declare its own.
DEFAULT_TRUSS_HEEL_M = inch(9.25).meters


def roof_slope_coordinate(roof: ResolvedRoof, point: tuple[float, float]) -> float:
    """The plan coordinate the roof's slope runs along — perpendicular to the ridge."""
    return point[1] if roof.ridge_direction == "x" else point[0]


def roof_slope_extent(roof: ResolvedRoof) -> tuple[float, float]:
    """The footprint's ``(low, high)`` along the slope axis — the plane's own domain."""
    axis = 1 if roof.ridge_direction == "x" else 0
    values = [item[axis] for item in roof.footprint]
    return (min(values), max(values))


def roof_slope_factor(roof: ResolvedRoof) -> float:
    """``hypot(1, pitch)`` — what turns a *perpendicular* offset into a *vertical* one.

    An assembly's layers are stacked perpendicular to the plane they clad; an elevation is
    measured straight up. On a 4:12 the two differ by 5.4%, which is nothing on a wall and
    most of a layer on a roof: the whole stack over catlin's deck is 7.9" deep, so drawing
    its bands at their perpendicular offsets lands the vent-mat intake a third of an inch
    low — on the underlayment below it. ``houses/catlin/params/roof_trim.py`` has carried a
    hand-written copy of this number since the eave water chain was authored; this is the
    one the drawing side reads.
    """
    low, high = roof_slope_extent(roof)
    span = high - low
    if span <= 1e-9:
        return 1.0
    run = span if roof.form == "shed" else span / 2.0
    if run <= 1e-9:
        return 1.0
    return math.hypot(1.0, (roof.ridge_z_m - roof.eave_z_m) / run)


def roof_ridge_coordinate(roof: ResolvedRoof) -> float | None:
    """Where the ridge falls on the slope axis, or ``None`` for a shed (it has no fold).

    A section that crosses the ridge has to break its band lines there or the polygon
    short-cuts the peak.
    """
    if roof.form == "shed":
        return None
    low, high = roof_slope_extent(roof)
    return (low + high) / 2.0


def roof_plane_z(roof: ResolvedRoof, coordinate: float, *, clamp: bool = False) -> float:
    """Roof-plane elevation at a slope-axis ``coordinate`` (see :func:`roof_slope_coordinate`).

    The single copy of the roof plane's equation. ``clamp`` decides what happens *outside*
    the footprint on a gable: clamped, the plane flattens at the eave elevation (what a
    headroom or vent-termination query wants — there is no roof out there); unclamped, it
    keeps falling, which is what a layer band offset proud of the eave needs so its drip
    edge stays on the slope instead of kinking flat. A shed extrapolates either way; it has
    only one plane, so there is no ridge to fold about.

    Three modules had their own transcription of this: ``geometry_roofs._plane_z`` (the
    unclamped one), ``section._emit_roof_cut``'s ``z_at`` closure and
    ``joints._roof_underside_line``'s ``z_top``. They agreed by luck, not by construction.
    """
    low, high = roof_slope_extent(roof)
    span = high - low
    if span <= 1e-9:
        return roof.eave_z_m
    if roof.form == "shed":
        return roof.eave_z_m + (coordinate - low) / span * (roof.ridge_z_m - roof.eave_z_m)
    midpoint = (low + high) / 2.0
    ratio = 1.0 - abs(coordinate - midpoint) / (span / 2.0)
    if clamp:
        ratio = max(0.0, ratio)
    return roof.eave_z_m + ratio * (roof.ridge_z_m - roof.eave_z_m)


def roof_height_at(roof: ResolvedRoof, point: tuple[float, float]) -> float:
    """Return the exterior roof-plane elevation at a plan-frame point."""
    return roof_plane_z(roof, roof_slope_coordinate(roof, point), clamp=True)


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


def roof_is_trussed(model: ResolvedModel, roof: ResolvedRoof) -> bool:
    """True when the roof's STRUCTURE layer is framed as a truss rather than as rafters.

    The one fact that decides whether a roof has a *ceiling plane* distinct from its deck:
    a truss's bottom chord is flat, so the finish and the insulation below it lie in a
    horizontal plane, while a rafter roof's lining follows the slope. Do not substitute
    ``deck_rise_m() is None`` for this — that returns None for an unframed roof too.
    """
    spec = roof_structure_framing(model, roof)
    return spec is not None and spec.roof_frame == "truss"


def roof_bearing_footprint(model: ResolvedModel,
                           roof: ResolvedRoof) -> tuple[tuple[float, float], ...] | None:
    """The roof's plan rectangle at the BEARING WALLS — the overhangs taken back off.

    ``ResolvedRoof.footprint`` is deliberately the *overhang-expanded* rectangle: it is the
    edge the deck, the roofing and the fascia run to, and it is also lapped out to clear the
    bearing wall's cladding (resolve/envelope.py). That is the right extent for everything
    bought by the roof surface — and the wrong one for anything that stops at the wall.
    A ceiling and its insulation stop at the wall. On catlin's garage the difference is not
    a rounding error: 26'-8" square with the 1'-4" eaves against 24'-0" square without, so
    billing a ceiling off the footprint orders 30% too much of it.

    Rebuilt from the bearing walls' axes rather than by subtracting the authored overhangs
    from ``footprint``, because the footprint also carries the cladding lap, and undoing two
    adjustments to recover a number the resolver already had is how the two drift apart.
    Returns None when the roof does not resolve two bearing walls — never a guess.
    """
    walls = roof_bearing_walls(model, roof)
    if len(walls) < 2:
        return None
    points = [point for wall in walls for point in wall.axis]
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    if maxx - minx < 1e-6 or maxy - miny < 1e-6:
        return None
    return ((minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy))


def roof_ceiling_area_m2(model: ResolvedModel, roof: ResolvedRoof) -> float | None:
    """Area of the plane a roof's ceiling finish and cavity insulation actually cover.

    Two different planes, decided by :func:`roof_is_trussed`:

    - a TRUSS roof ceilings out flat on the bottom chord, so the area is the bearing
      footprint as-is and the pitch never enters it;
    - a RAFTER roof carries its lining and its cavity up the slope, so the same footprint
      is multiplied by the slope factor — the identical ``sqrt(1 + (rise/run)^2)`` the
      resolver applies to the deck (resolve/envelope.py), just over the smaller rectangle.

    Neither is ``ResolvedRoof.surface_area_m2``, which is sloped *and* overhung and belongs
    to the deck. Returns None when the bearing footprint or the authored pitch is unknown.
    """
    footprint = roof_bearing_footprint(model, roof)
    if footprint is None:
        return None
    area = abs(polygon_area(list(footprint)))
    if roof_is_trussed(model, roof):
        return area
    element = model.plan.by_tag(roof.tag)
    if not isinstance(element, Roof):
        return None
    return area * math.sqrt(1.0 + (element.pitch.rise / element.pitch.run) ** 2)


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
        # ``replace``, not a fresh ``ResolvedWall``: an explicit constructor silently
        # reverts every field it does not list to its default, and by this stage
        # ``extend_walls_to_foundation`` has already written ``plate_base_z_m`` on any
        # clad gable that got the rim drop. Framing, anchors and uplift all read it.
        resolved.append(replace(
            wall, z1_m=max(start_top, end_top),
            top_z0_m=start_top, top_z1_m=end_top,
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
