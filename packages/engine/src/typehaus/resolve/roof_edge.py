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

from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof, ResolvedWall
from typehaus.resolve.roof_edge_geometry import (
    CLOSURE_TOLERANCE_M,
    MatingFaces,
    bbox,
    continuous_skin_cladding,
    footprint_test,
    mating_faces,
    roof_slope,
    skin_layers,
    skin_stand_ins,
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
    """The *exterior* walls this roof closes against, by plan axis inside its footprint.

    Exterior means "has a sheathing layer": an interior partition has no weather skin to
    carry up, and framing a closure band over one would invent construction.

    Normally those are the walls on the roof's own storey. The exception is a bearing wall
    with NO skin — a rafter plate laid flat on a floor deck, which is how a story-and-a-half
    lands its roof with no knee wall at all. That plate closes the storey's room loop and
    carries the roof, but there is no cladding on a 2x on its side, and without a stand-in
    the eave silently loses its whole closure band and drip trim. The skin on that line
    belongs to the wall the plate stands on (:func:`skin_stand_ins`).
    """
    inside = footprint_test(roof)
    walls: list[ResolvedWall] = []
    seen: set[str] = set()
    for wall in model.walls:
        if wall.storey != roof.storey or not inside(wall):
            continue
        if skin_layers(wall):
            candidates: tuple[ResolvedWall, ...] = (wall,)
        elif wall.tag in getattr(model.plan.by_tag(roof.tag), "bearing_refs", ()):
            candidates = skin_stand_ins(model, wall, inside)
        else:
            continue
        for candidate in candidates:
            if candidate.tag not in seen:
                seen.add(candidate.tag)
                walls.append(candidate)
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


def _laps_the_corner(wall: ResolvedWall) -> bool:
    """Which of the two walls meeting at an outside corner carries its band through it.

    A band is a *box*: one plan segment and one width. The layer under it is not — it is
    already mitred, a trapezoid whose outboard edge runs past its inboard one. So a band can
    take the long edge or the short one, and it cannot take both. If both walls at a corner
    take the long edge they double-occupy the mitre square and their faces land coplanar
    (7/8" wide on the garage, the height of the band, z-fighting in every 3D view); if both
    take the short edge the square is left open, which is the gold-square bug
    :func:`_layer_axis_fractions` was written to close. One long and one short tiles it
    exactly — a lapped corner, which is also how the boards themselves go on.

    The pick has to come out *different* for the two walls at a corner, so it is made on the
    wall's own plan direction: the wall running more north-south laps, the one running more
    east-west butts into it. That is exact for every orthogonal corner. At a non-orthogonal
    corner both walls can land on the same side of the test and the overlap comes back — no
    worse than what this replaced, and the case does not arise on this house.

    Only consulted where the neighbour actually caps the same layer; :func:`_lap_flags` is
    where that question is asked, and it laps unconditionally when nobody else will.
    """
    (ax, ay), (bx, by) = wall.axis
    return abs(by - ay) >= abs(bx - ax)


def _layer_axis_fractions(
    wall: ResolvedWall, layer, laps: tuple[bool, bool]
) -> tuple[float, float]:
    """The along-axis fractions the closure band spans over ``layer`` (a mitre passes 0/1).

    A wall's layers are already mitred into the building's outside corners by the time they
    resolve: on the catlin attic's SW corner W-A-S1's cladding polygon runs x -0.128..3.048
    against a 0..3.048 axis, and W-A-W1's runs the matching 0.128 past its own end. The
    closure band above it was the one piece still measured on the raw axis, so at each
    outside corner a (skin depth)² column — 4 3/4" square on this house, the full height of
    the wall→roof stack — was claimed by neither wall's band, and the wall's exterior foam
    showed its end grain there. (Visible as a gold square at both lower gable corners in any
    3D view.) Reading the span off the polygon is what closed that.

    ``lap`` then says which end of the mitre this wall takes (→ :func:`_laps_the_corner`),
    because a rectangular band cannot inherit a trapezoid: the lapping wall runs to the
    polygon's furthest corner and the butting wall stops at its nearest, so the two tile the
    mitre square instead of both claiming it. Taken per END rather than per edge, so a wall
    that turns an outside corner at one end and an inside corner at the other is right at
    both.
    """
    (ax, ay), (bx, by) = wall.axis
    dx, dy = bx - ax, by - ay
    run = math.hypot(dx, dy)
    if run <= 1e-9:
        return (0.0, 1.0)
    along = [((x - ax) * dx + (y - ay) * dy) / (run * run) for x, y in layer.polygon]
    if laps[0] and laps[1]:
        return (min(along), max(along))
    # The two long edges of the layer prism, split on which side of the axis they lie. A
    # butting end stops where the SHORTER of them does; the two ends are independent, so a
    # wall that turns an outside corner at one end and butts at the other is right at both.
    normal = (-dy / run, dx / run)
    across = [(x - ax) * normal[0] + (y - ay) * normal[1] for x, y in layer.polygon]
    mid = (min(across) + max(across)) / 2.0
    near = [along[i] for i in range(len(along)) if across[i] <= mid]
    far = [along[i] for i in range(len(along)) if across[i] > mid]
    if not near or not far:
        return (min(along), max(along))
    return (min(along) if laps[0] else max(min(near), min(far)),
            max(along) if laps[1] else min(max(near), max(far)))


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

def _neighbour_at(
    wall: ResolvedWall, point: tuple[float, float], walls: tuple[ResolvedWall, ...]
) -> ResolvedWall | None:
    """The other wall under this roof that ends where ``wall`` does, if any."""
    for other in walls:
        if other.tag == wall.tag:
            continue
        if any(math.dist(end, point) <= CLOSURE_TOLERANCE_M for end in other.axis):
            return other
    return None


def _lap_flags(
    wall: ResolvedWall, walls: tuple[ResolvedWall, ...], capped: frozenset[tuple[str, str]],
    layer_name: str,
) -> tuple[bool, bool]:
    """Whether this wall's band runs through the mitre at each of its two ends.

    Laps unless the wall on the other side of that corner is going to cap the same layer and
    :func:`_laps_the_corner` gives that one the mitre. "Unless" is the important half: a
    ``ToRoof`` gable already rakes to the deck plane and emits no sheathing band at all, so a
    corner where it meets a flat wall has nobody but the flat wall to close it — butting there
    would reopen the gold square this whole mitre exists to close.
    """
    out: list[bool] = []
    for end in wall.axis:
        other = _neighbour_at(wall, end, walls)
        out.append(True if other is None or (other.tag, layer_name) not in capped
                   else _laps_the_corner(wall))
    return (out[0], out[1])



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

    def pass_over(capped: frozenset[tuple[str, str]]) -> list[FramedMember]:
        out: list[FramedMember] = []
        for wall in walls:
            crossing = _ridge_crossing_fraction(roof, wall)
            spans = ((0.0, 1.0),) if crossing is None else ((0.0, crossing), (crossing, 1.0))
            for index, (t0, t1) in enumerate(spans):
                out.extend(_closure_segment(roof, wall, t0, t1, index, structure_depth,
                                            mating, slope_factor, continuous, walls, capped))
        return out

    # Two passes, because whether a wall laps a corner depends on whether its neighbour caps
    # the same layer there, and that is only known once the bands exist. The probe pass laps
    # everywhere — the old behaviour — and is read only for *which* (wall, layer) pairs
    # produce a band; the mitre it hands them is then corrected in the second.
    probe = pass_over(frozenset())
    capped = frozenset((m.child_key.split("-closure-")[0], m.child_key.rsplit("-", 1)[1])
                       for m in probe)
    return tuple(pass_over(capped))


def _closure_segment(
    roof: ResolvedRoof, wall: ResolvedWall, t0: float, t1: float,
    segment: int, structure_depth: float,
    mating: MatingFaces | None, slope_factor: float, continuous: bool = False,
    walls: tuple[ResolvedWall, ...] = (), capped: frozenset[tuple[str, str]] = frozenset(),
) -> tuple[FramedMember, ...]:
    members: list[FramedMember] = []
    for layer in skin_layers(wall):
        laps = _lap_flags(wall, walls, capped, layer.name)
        offset = _layer_offset_m(wall, layer)
        # Run the band over the layer polygon's own span, so it inherits the outside-corner
        # mitre the prism below it already has. Only the *ends* of the wall stretch: an
        # interior split (the ridge crossing) is a fraction we chose, not a corner.
        mitre0, mitre1 = _layer_axis_fractions(wall, layer, laps)
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
        thickness_in = layer.thickness_m / M_PER_IN
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
