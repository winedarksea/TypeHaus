"""Where the roof meets the walls it lands on (→ B2).

A wall prism stops at its top plate. Over a raised-heel truss the deck plane sits a heel
above that plate, and at a gable end the plane climbs to the ridge, so the sheathing/
rainscreen/cladding band between the wall top and the roof is simply missing — daylight at
the heel and an exposed truss at the gable. Every exterior wall under a roof gets that band
carried up here, and *where* it stops depends on the eave type:

* **overhung** (the garage's 16" eave): the roof runs past the wall and its soffit closes
  the underside, so the skin dies at the structure's underside as one band per layer.
* **flush** (the golden detail's condition, and RF-HOUSE's): there is no soffit, so each
  wall layer runs up to *its own* counterpart face in the roof stack — see
  :class:`MatingFaces`. A ``ToRoof`` wall already rakes to the deck plane, so only the
  layers with somewhere left to go (foam, furring, cladding) produce anything.

The trim hung off the plane on the other side of that joint — fascia, soffit, gutter, and
the roof-edge cladding band — is derived in :mod:`typehaus.resolve.roof_trim`, which this
module drives so a roof picks up both halves of its edge in one pass.

Both are emitted as ``FramedMember`` records on the roof: unlike ``ResolvedSolid`` (a plan
prism), a member carries different elevations at each end, which is what a raked gable
closure and a sloped rake fascia need.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof, ResolvedWall
from typehaus.resolve.roof_edge_geometry import (
    CLOSURE_TOLERANCE_M,
    FOOTPRINT_TOLERANCE_M,
    METERS_PER_INCH,
    MatingFaces,
    bbox,
    continuous_skin_cladding,
    mating_faces,
    roof_slope,
    skin_layers,
)
from typehaus.resolve.roof_geometry import roof_height_at, roof_structure_depth_m
from typehaus.resolve.roof_layer_setbacks import above_structure_layers
from typehaus.resolve.roof_trim import roof_trim_members


def resolve_roof_edges(model: ResolvedModel) -> None:
    """Attach the wall→roof closure band and the derived eave/rake trim to every roof."""
    resolved: list[ResolvedRoof] = []
    for roof in model.roofs:
        walls = _walls_under_roof(model, roof)
        extra = (_closure_members(model, roof, walls)
                 + roof_trim_members(model, roof, walls))
        resolved.append(replace(roof, members=roof.members + extra) if extra else roof)
    model.roofs = resolved


# --- shared geometry ---------------------------------------------------------------------

def _walls_under_roof(model: ResolvedModel, roof: ResolvedRoof) -> tuple[ResolvedWall, ...]:
    """The roof's storey's *exterior* walls whose plan axis lies inside its footprint.

    Exterior means "has a sheathing layer": an interior partition has no weather skin to
    carry up, and framing a closure band over one would invent construction.
    """
    minx, miny, maxx, maxy = bbox(roof.footprint)
    tol = FOOTPRINT_TOLERANCE_M
    walls: list[ResolvedWall] = []
    for wall in model.walls:
        if wall.storey != roof.storey or not skin_layers(wall):
            continue
        if all(minx - tol <= x <= maxx + tol and miny - tol <= y <= maxy + tol
               for x, y in wall.axis):
            walls.append(wall)
    return tuple(walls)


def _wall_top_at(wall: ResolvedWall, fraction: float) -> float:
    """The wall's top elevation at a fraction along its axis (a rake interpolates)."""
    start = wall.z1_m if wall.top_z0_m is None else wall.top_z0_m
    end = wall.z1_m if wall.top_z1_m is None else wall.top_z1_m
    return start + (end - start) * fraction


def _layer_offset_m(wall: ResolvedWall, layer) -> float:
    """Signed perpendicular offset of a layer's centerline from the wall axis."""
    (ax, ay), (bx, by) = wall.axis
    run = math.hypot(bx - ax, by - ay) or 1.0
    normal = (-(by - ay) / run, (bx - ax) / run)
    ring = layer.polygon
    cx = sum(point[0] for point in ring) / len(ring)
    cy = sum(point[1] for point in ring) / len(ring)
    return (cx - ax) * normal[0] + (cy - ay) * normal[1]


def _layer_axis_fractions(wall: ResolvedWall, layer) -> tuple[float, float]:
    """The along-axis fractions the layer's own plan polygon spans (a mitre reaches past 0/1).

    A wall's layers are already mitred into the building's outside corners by the time they
    resolve: on the catlin attic's SW corner W-A-S1's cladding polygon runs x -0.128..3.048
    against a 0..3.048 axis, and W-A-W1's runs the matching 0.128 past its own end. The
    closure band above it was the one piece still measured on the raw axis, so at each
    outside corner a (skin depth)² column — 4 3/4" square on this house, the full height of
    the wall→roof stack — was claimed by neither wall's band, and the wall's exterior foam
    showed its end grain there. (Visible as a gold square at both lower gable corners in any
    3D view.) Taking the span from the polygon makes the band inherit whatever mitre the
    layer beneath it already has, including its convention at every other junction kind, so
    this cannot drift from the prism it caps.
    """
    (ax, ay), (bx, by) = wall.axis
    dx, dy = bx - ax, by - ay
    run = math.hypot(dx, dy)
    if run <= 1e-9:
        return (0.0, 1.0)
    along = [((x - ax) * dx + (y - ay) * dy) / (run * run) for x, y in layer.polygon]
    return (min(along), max(along))


def _offset_point(wall: ResolvedWall, fraction: float, offset: float) -> tuple[float, float]:
    (ax, ay), (bx, by) = wall.axis
    dx, dy = bx - ax, by - ay
    run = math.hypot(dx, dy) or 1.0
    normal = (-dy / run, dx / run)
    return (ax + dx * fraction + normal[0] * offset, ay + dy * fraction + normal[1] * offset)


def _ridge_crossing_fraction(roof: ResolvedRoof, wall: ResolvedWall) -> float | None:
    """Where along the wall the ridge passes over it, if it does.

    A gable wall runs from eave to eave over the ridge, so a single straight rake between its
    endpoints would cut the peak off. Splitting the closure there follows the real two-plane
    roof instead.
    """
    if roof.form != "gable":
        return None
    minx, miny, maxx, maxy = bbox(roof.footprint)
    axis = 1 if roof.ridge_direction == "x" else 0
    low, high = (miny, maxy) if axis == 1 else (minx, maxx)
    mid = (low + high) / 2.0
    start, end = wall.axis[0][axis], wall.axis[1][axis]
    if abs(end - start) < CLOSURE_TOLERANCE_M:
        return None
    fraction = (mid - start) / (end - start)
    return fraction if 1e-6 < fraction < 1.0 - 1e-6 else None


# --- wall → roof closure -----------------------------------------------------------------

def _closure_members(
    model: ResolvedModel, roof: ResolvedRoof, walls: tuple[ResolvedWall, ...]
) -> tuple[FramedMember, ...]:
    """Carry each exterior wall's weather skin up to the roof faces it mates with."""
    structure_depth = roof_structure_depth_m(model, roof)
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    element = model.plan.by_tag(roof.tag)
    overhang = getattr(element, "overhang", None)
    # Where the roof runs past the wall, its soffit closes the gap and the skin stops at the
    # structure's underside. Where it is flush — the golden detail's condition, and RF-HOUSE's
    # — there is no soffit and the skin continues up into the layer stack itself.
    layers = above_structure_layers(assembly)
    mating = (mating_faces(layers)
              if layers and (overhang is None or overhang.meters <= CLOSURE_TOLERANCE_M)
              else None)
    # One continuous cladding skin wall→roof (the wrapped standing-seam edge): the wall's
    # metal keeps climbing past the foam underside to the roofing's own underside, because
    # there is no drip-edge band left for it to die under (roof_trim emits a corner trim
    # piece over the joint instead).
    continuous = mating is not None and continuous_skin_cladding(model, roof, walls)
    slope_factor = math.hypot(1.0, roof_slope(roof))
    members: list[FramedMember] = []
    for wall in walls:
        crossing = _ridge_crossing_fraction(roof, wall)
        spans = ((0.0, 1.0),) if crossing is None else ((0.0, crossing), (crossing, 1.0))
        for index, (t0, t1) in enumerate(spans):
            members.extend(_closure_segment(roof, wall, t0, t1, index, structure_depth,
                                            mating, slope_factor, continuous))
    return tuple(members)


def _closure_segment(
    roof: ResolvedRoof, wall: ResolvedWall, t0: float, t1: float,
    segment: int, structure_depth: float,
    mating: MatingFaces | None, slope_factor: float, continuous: bool = False,
) -> tuple[FramedMember, ...]:
    members: list[FramedMember] = []
    for layer in skin_layers(wall):
        offset = _layer_offset_m(wall, layer)
        # Run the band over the layer polygon's own span, so it inherits the outside-corner
        # mitre the prism below it already has. Only the *ends* of the wall stretch: an
        # interior split (the ridge crossing) is a fraction we chose, not a corner.
        mitre0, mitre1 = _layer_axis_fractions(wall, layer)
        f0 = min(t0, mitre0) if t0 <= 1e-9 else t0
        f1 = max(t1, mitre1) if t1 >= 1.0 - 1e-9 else t1
        tops = (_wall_top_at(wall, f0), _wall_top_at(wall, f1))
        p0 = _offset_point(wall, f0, offset)
        p1 = _offset_point(wall, f1, offset)
        if mating is None:
            # Overhung edge: one band per layer, up to the structure's underside, measured on
            # the wall's own axis (the soffit closes everything outboard of that).
            targets = tuple(roof_height_at(roof, _offset_point(wall, fraction, 0.0))
                            - structure_depth for fraction in (f0, f1))
        else:
            # Flush edge: each layer rises to its own face in the roof stack, measured at that
            # layer's own plan position — the layers are parallel to the slope, so a layer
            # further out mates a little lower.
            perpendicular = mating.for_layer(layer.function, continuous_cladding=continuous)
            targets = tuple(roof_height_at(roof, point) + perpendicular * slope_factor
                            for point in (p0, p1))
        if max(targets[0] - tops[0], targets[1] - tops[1]) < CLOSURE_TOLERANCE_M:
            continue  # this layer already reaches its face (a ToRoof rake, or a flush eave)
        thickness_in = layer.thickness_m / METERS_PER_INCH
        members.append(FramedMember(
            parent_uid=wall.uid,
            child_key=f"{wall.tag}-closure-{segment}-{layer.name}",
            category=layer.function, profile=panel_profile(thickness_in, thickness_in),
            p0=p0, p1=p1,
            z0_m=tops[0], z1_m=max(tops[0], targets[0]),
            length_m=math.hypot(p1[0] - p0[0], p1[1] - p0[1]),
            z0_end_m=tops[1], z1_end_m=max(tops[1], targets[1]),
            connection="roof:wall-top-closure",
            material=layer.material_ref,
        ))
    return tuple(members)
