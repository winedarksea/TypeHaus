"""Fit catalog bodies to the member faces already located by the joint resolvers."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import cast

from shapely.geometry import Point, Polygon

from typehaus.hardware.plan_geometry import centerline_endpoints
from typehaus.joints.model import Joint
from typehaus.model import Connector, Element, KneeBrace
from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.catalog import connector_mesh
from typehaus.resolve.connector_geometry.mesh import transform_mesh
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry_ir import GMesh, Vec2, Vec3
from typehaus.resolve.kbs_geometry import kbs_mesh
from typehaus.resolve.model import (
    FramedMember,
    ResolvedBrace,
    ResolvedConstructionReturn,
    ResolvedFloor,
    ResolvedModel,
    ResolvedRoof,
    ResolvedSolid,
    ResolvedWall,
)

HANGER_PREFIXES = ("LUS", "LSSR", "LSC", "IUS", "HHUS", "THA", "HUC", "HU")
BASE_PREFIXES = ("ABU", "CBSQ")
CAP_PREFIXES = ("PC", "CCQ", "AC", "ACE")
BEAM_CATEGORIES = frozenset({"beam", "ridge_beam", "header", "trimmer", "rim", "joist"})
FACE_PLATE_PARTS = frozenset({"LTP4", "LTP4Z"})


def _direction(start: Vec2, end: Vec2) -> Vec2:
    dx, dy = end[0] - start[0], end[1] - start[1]
    run = math.hypot(dx, dy)
    if run <= 0.0:
        raise ValueError("a connector support needs a nonzero member axis")
    direction = (dx / run, dy / run)
    # A support has an unoriented axis. Pick a stable half-plane for symmetric bodies.
    return direction if direction[0] > 0 or (direction[0] == 0 and direction[1] > 0) \
        else (-direction[0], -direction[1])


def _centroid(outline: Sequence[Vec2]) -> Vec2:
    return cast(Vec2, tuple(sum(point[i] for point in outline) / len(outline) for i in range(2)))


def _width(outline: Sequence[Vec2], across: Vec2) -> float:
    offsets = [point[0] * across[0] + point[1] * across[1] for point in outline]
    return max(offsets) - min(offsets)


@dataclass
class ConnectorPlacementIndex:
    """One index per resolve; hundreds of ties must not rescan all framing each time."""

    model: ResolvedModel

    def __post_init__(self) -> None:
        self.solids: dict[str, ResolvedSolid] = {
            solid.tag: solid for solid in self.model.solids
            if not solid.category.startswith("connector")}
        self.members: dict[str, FramedMember] = {
            f"{member.parent_uid}:{member.child_key}": member
            for member in self.model.all_members()}
        self.returns_by_tag: dict[str, list[tuple[ResolvedConstructionReturn, Polygon]]] = {}
        for ret in self.model.construction_returns:
            self.returns_by_tag.setdefault(ret.tag, []).append((ret, Polygon(ret.outline)))
        self.elements: dict[str, Element] = {
            element.tag: element for element in self.model.plan.all_elements()}
        self.hosts: dict[str, ResolvedRoof | ResolvedFloor | ResolvedWall | ResolvedBrace] = {
            host.tag: host for collection in (self.model.roofs, self.model.floors,
                                              self.model.walls, self.model.braces)
            for host in collection}
        self.knee_bands: dict[str, tuple[FramedMember, bool]] = {}
        for brace in self.model.braces:
            element = self.elements.get(brace.tag)
            if isinstance(element, KneeBrace):
                for end in ("top", "bot"):
                    self.knee_bands[f"{element.uid or element.tag}-band-{end}"] = (
                        brace.members[0], end == "top")

    def direction(self, tag: str) -> Vec2 | None:
        member = self.members.get(tag)
        if member is not None:
            return _direction(member.p0, member.p1)
        wall = self.model.wall(tag)
        if wall is not None:
            return _direction(*wall.axis)
        solid = self.solids.get(tag)
        if solid is not None and len(solid.outline) >= 3:
            return _direction(*centerline_endpoints(list(solid.outline)))
        return None

    def return_at(self, tag: str, point: Vec2, z_m: float) -> ResolvedConstructionReturn | None:
        """Return tags name a construction detail, so location disambiguates its runs."""
        candidates = self.returns_by_tag.get(tag, ())
        if not candidates:
            return None
        location = Point(point)
        return min(candidates, key=lambda pair: pair[1].distance(location)
                   + abs(pair[0].z0_m - z_m))[0]

    def support_width(self, tag: str | None, tangent: Vec2, *, point: Vec2 | None = None,
                      z_m: float | None = None) -> float | None:
        tag = cast(str, tag)
        member = self.members.get(tag)
        if member is not None:
            return member.plan_width_m or cross_section(member.profile).width_m
        solid: ResolvedSolid | ResolvedConstructionReturn | None = self.solids.get(tag)
        if solid is None and point is not None and z_m is not None:
            solid = self.return_at(tag, point, z_m)
        if solid is not None:
            return _width(solid.outline, (-tangent[1], tangent[0]))
        wall = self.model.wall(tag)
        if wall is not None:
            plates = [member for member in wall.members
                      if member.category in ("plate", "top_plate", "bottom_plate")]
            if plates:
                return cross_section(plates[0].profile).depth_m
            return wall.thickness_m
        return None


def solid_with_body(solid: ResolvedSolid, mesh: GMesh) -> ResolvedSolid:
    """Keep the picking envelope synchronized with the body every renderer exports."""
    xs, ys, zs = zip(*mesh.positions, strict=True)
    return replace(solid, body_mesh=mesh,
                   outline=[(min(xs), min(ys)), (max(xs), min(ys)),
                            (max(xs), max(ys)), (min(xs), max(ys))],
                   z0_m=min(zs), z1_m=max(zs))


def _connected_beam(index: ConnectorPlacementIndex,
                    references: Sequence[str]) -> ResolvedSolid | None:
    return next((index.solids[tag] for tag in references
                 if tag in index.solids and index.solids[tag].category in BEAM_CATEGORIES), None)


def _authored_hanger_frame(index: ConnectorPlacementIndex, element: Element | None,
                          point: Vec2, z_m: float
                          ) -> tuple[Vec2, float, Vec2 | None, float | None, float | None]:
    """An authored hanger names a carried beam; its real end and soffit define the seat."""
    beam = _connected_beam(index, cast(Connector, element).connects)
    if beam is None:
        return point, z_m, None, None, None
    ends = centerline_endpoints(list(beam.outline))
    near_index = min(range(2), key=lambda i: math.dist(point, ends[i]))
    near, far = ends[near_index], ends[1 - near_index]
    run = math.dist(near, far)
    outward = ((far[0] - near[0]) / run, (far[1] - near[1]) / run)
    across = (outward[1], -outward[0])
    return near, beam.z0_m, outward, _width(beam.outline, across), beam.z1_m - beam.z0_m


def _roof_slope(index: ConnectorPlacementIndex, references: Sequence[str]) -> float:
    for tag in references:
        roof = index.hosts.get(tag)
        if roof is None:
            roof = next((host for host in index.model.roofs
                         if any(f"{member.parent_uid}:{member.child_key}" == tag
                                for member in host.members)), None)
        if roof is not None:
            slopes = []
            for member in roof.members:
                run = math.dist(member.p0, member.p1)
                if run > 0.0 and member.z1_end_m is not None:
                    slopes.append(abs(math.atan2(member.z1_end_m - member.z1_m, run)))
            if slopes:
                return max(slopes)
    return 0.0


def _member_at_joint(index: ConnectorPlacementIndex, references: Sequence[str],
                     point: Vec2) -> FramedMember | None:
    members = [member for tag in references if tag in index.hosts
               for member in index.hosts[tag].members
               if member.category in ("rafter", "joist", "truss", "roof_truss", "ridge_beam")]
    members.extend(index.members[tag] for tag in references if tag in index.members)
    if not members:
        return None
    # Endpoint distance also works for bearing intersections: use the segment projection.
    from typehaus.hardware.plan_geometry import distance_point_to_segment

    return min(members, key=lambda member: distance_point_to_segment(point, member.p0, member.p1))


def _knee_body(member: FramedMember, top: bool) -> GMesh:
    """Fold the existing KBS stamping around the actual post/soffit and brace faces."""
    run = math.dist(member.p0, member.p1)
    ux, uy = (member.p1[0] - member.p0[0]) / run, (member.p1[1] - member.p0[1]) / run
    inward = (-uy, ux, 0.0)
    width = cross_section(member.profile).width_m
    point = member.p1 if top else member.p0
    z_m = cast(float, member.z1_end_m) if top else member.z1_m
    heel = (point[0] - inward[0] * width / 2, point[1] - inward[1] * width / 2, z_m)
    root = math.sqrt(2.0)
    sign = -1.0 if top else 1.0
    support_axis = (-ux, -uy, 0.0) if top else (0.0, 0.0, -1.0)
    support_face = (0.0, 0.0, 1.0) if top else (-ux, -uy, 0.0)
    return kbs_mesh(heel, support_axis, support_face,
                    (sign * ux / root, sign * uy / root, sign / root),
                    (ux / root, uy / root, -1.0 / root), inward)


def _body_at_joint(index: ConnectorPlacementIndex, solid: ResolvedSolid,
                   joint: Joint | None) -> GMesh | None:
    part = (solid.product or "").upper().strip()
    if part == "KBS1Z" and solid.uid in index.knee_bands:
        return _knee_body(*index.knee_bands[solid.uid])
    element = index.elements.get(solid.tag)
    references = joint.members if joint is not None else getattr(element, "connects", ())
    point = joint.point if joint is not None else _centroid(solid.outline)
    z_m = joint.z_m if joint is not None else (solid.z0_m + solid.z1_m) / 2
    axis = joint.axis if joint is not None else getattr(element, "axis", None)
    tangent = ((0.0, 1.0) if axis == "y" else (1.0, 0.0))
    if axis is None:
        beam = _connected_beam(index, references)
        tangent = cast(Vec2, index.direction(beam.tag) if beam is not None \
            else next((index.direction(tag) for tag in references
                       if index.direction(tag) is not None), tangent))
    x_axis: Vec3 = (*tangent, 0.0)
    y_axis: Vec3 = (-tangent[1], tangent[0], 0.0)
    z_axis: Vec3 = (0.0, 0.0, 1.0)
    member_width_m = joint.member_width_m if joint else None
    member_depth_m = joint.height_m if joint else None
    slope = joint.slope_radians if joint else 0.0
    support_width_m = None

    if part.startswith(HANGER_PREFIXES):
        if joint is not None:
            outward = joint.outward_xy
            z_m = joint.seat_z_m if joint.seat_z_m is not None else z_m
        else:
            point, z_m, outward, member_width_m, member_depth_m = _authored_hanger_frame(
                index, element, point, z_m)
        if outward is not None:
            tangent = (outward[1], -outward[0])
            x_axis, y_axis = (*tangent, 0.0), (*outward, 0.0)
        if references:
            # Authored refs name the carried beam first; a derived joint names its carrier.
            support_ref = references[0] if joint else next(
                (tag for tag in references if index.solids.get(tag) is not
                 _connected_beam(index, references)), references[0])
            support_width_m = index.support_width(support_ref, tangent)
            if joint is not None and outward is not None and support_width_m is not None:
                # Hung connections are detected on the carrier centreline, but face-mount
                # catalog geometry uses y=0 as the carrier face. Move the datum to the
                # face on the carried member's side before fitting the hanger body.
                point = (point[0] + outward[0] * support_width_m / 2,
                         point[1] + outward[1] * support_width_m / 2)
    elif part.startswith(BASE_PREFIXES):
        if joint is not None and len(references) > 1:
            support = index.solids.get(references[1])
            wall = index.model.wall(references[1])
            if support is not None:
                z_m = support.z1_m
            elif wall is not None:
                z_m = wall.z1_m
    elif part.startswith(CAP_PREFIXES):
        beam = _connected_beam(index, references)
        if beam is not None:
            member_width_m = _width(beam.outline, (-tangent[1], tangent[0]))
            member_depth_m = beam.z1_m - beam.z0_m
    elif part.startswith("LSTA"):
        slope = _roof_slope(index, references)
    elif part.startswith("THD"):
        beam = _connected_beam(index, references)
        wall = next((index.model.wall(tag) for tag in references
                     if index.model.wall(tag) is not None), None)
        if beam is not None and wall is not None:
            wall_centre = _centroid(wall.axis)
            outward = (-tangent[1], tangent[0])
            if ((point[0] - wall_centre[0]) * outward[0]
                    + (point[1] - wall_centre[1]) * outward[1]) < 0:
                outward = (-outward[0], -outward[1])
            projection = max(x * outward[0] + y * outward[1] for x, y in beam.outline)
            offset = projection - point[0] * outward[0] - point[1] * outward[1]
            point = (point[0] + outward[0] * offset, point[1] + outward[1] * offset)
            x_axis, y_axis = (outward[1], -outward[0], 0.0), (*outward, 0.0)
    elif part.startswith(("H2.5", "H10")):
        member = _member_at_joint(index, references, point)
        if member is not None:
            centre = ((member.p0[0] + member.p1[0]) / 2,
                      (member.p0[1] + member.p1[1]) / 2)
            normal = (-tangent[1], tangent[0])
            if ((centre[0] - point[0]) * normal[0]
                    + (centre[1] - point[1]) * normal[1]) < 0:
                x_axis = (-tangent[0], -tangent[1], 0.0)
                y_axis = (tangent[1], -tangent[0], 0.0)
            member_width_m = member.plan_width_m or cross_section(member.profile).width_m
        support = _connected_beam(index, references)
        support_reference = support.tag if support is not None else (
            references[0] if references else None)
        support_width_m = index.support_width(support_reference, tangent)
        if support_width_m:
            point = (point[0] - y_axis[0] * support_width_m / 2,
                     point[1] - y_axis[1] * support_width_m / 2)
        if part.startswith("H2.5") and member_width_m:
            point = (point[0] + x_axis[0] * member_width_m / 2,
                     point[1] + x_axis[1] * member_width_m / 2)
    elif part == "LS30" and joint is not None:
        # The gable tie reaches the bottom flange, and its long heel runs with the rafter.
        member = _member_at_joint(index, references, point)
        if member is None:
            return None
        z_m -= cross_section(member.profile).depth_m
        x_axis, z_axis = z_axis, x_axis
    elif part.startswith(("MASA", "STHD")) and joint is not None and references:
        run = index.return_at(references[0], point, z_m)
        if run is not None:
            member_width_m = _width(run.outline, y_axis[:2])
            member_depth_m = run.z1_m - run.z0_m
            # Embedded straps lie on the sill face; the embed bends back into its pour.
            point = (point[0] - y_axis[0] * member_width_m / 2,
                     point[1] - y_axis[1] * member_width_m / 2)
    elif part in FACE_PLATE_PARTS and references:
        widths = [(tag, index.support_width(tag, tangent, point=point, z_m=z_m))
                  for tag in references]
        support_reference, width = next(((tag, width) for tag, width in widths
                                         if width is not None), (None, None))
        if width is not None:
            wall = index.model.wall(cast(str, support_reference))
            if wall is not None:
                centre = _centroid(wall.axis)
                offset = sum((centre[i] - point[i]) * y_axis[i] for i in range(2))
                point = (point[0] + y_axis[0] * offset, point[1] + y_axis[1] * offset)
            point = (point[0] - y_axis[0] * width / 2,
                     point[1] - y_axis[1] * width / 2)
    elif part.startswith("HL"):
        beam = _connected_beam(index, references)
        if beam is not None:
            centre = _centroid(beam.outline)
            # Paired angles on opposite block faces have their concrete legs outside.
            if sum((point[i] - centre[i]) * y_axis[i] for i in range(2)) < 0:
                y_axis = cast(Vec3, tuple(-value for value in y_axis))
            from typehaus.resolve.connector_geometry.bases_caps import (
                ANGLE_DIMENSIONS,
                STEEL_GAUGE_THICKNESS_IN,
            )

            dimensions = ANGLE_DIMENSIONS.get(part.removesuffix("HDG"))
            if dimensions is not None:
                thickness_m = STEEL_GAUGE_THICKNESS_IN[dimensions.gauge] * M_PER_IN
                point = (point[0] + y_axis[0] * thickness_m,
                         point[1] + y_axis[1] * thickness_m)
                # These authored angle elevations name the centre of the upright leg.
                z_m += thickness_m - dimensions.vertical_leg_in * M_PER_IN / 2
        elif axis is None and len(references) == 2 and all(
                index.model.wall(tag) is not None for tag in references):
            # A wall face meeting another wall's end has a vertical heel, even when
            # their centreline axes are parallel (the screen/garage corner).
            wall_axis = cast(Vec2, index.direction(references[0]))
            x_axis = z_axis
            centre = _centroid(cast(ResolvedWall, index.model.wall(references[0])).axis)
            sign = 1.0 if sum((centre[i] - point[i]) * wall_axis[i] for i in range(2)) > 0 else -1.0
            y_axis = (sign * wall_axis[0], sign * wall_axis[1], 0.0)
            z_axis = (wall_axis[1], -wall_axis[0], 0.0)

    body = connector_mesh(part, member_width_in=member_width_m / M_PER_IN
                          if member_width_m is not None else None,
                          member_depth_in=member_depth_m / M_PER_IN
                          if member_depth_m is not None else None,
                          support_width_in=support_width_m / M_PER_IN
                          if support_width_m is not None else None, slope_radians=slope)
    return transform_mesh(body, origin_m=(*point, z_m), x_axis=x_axis, y_axis=y_axis,
                          z_axis=z_axis) if body is not None else None


def resolve_connector_bodies(model: ResolvedModel, joints_by_uid: dict[str, Joint]) -> None:
    """Replace known marker envelopes once, after authored and derived joints both exist."""
    index = ConnectorPlacementIndex(model)
    for i, solid in enumerate(model.solids):
        if solid.body_mesh is not None or not solid.category.startswith("connector"):
            continue
        mesh = _body_at_joint(index, solid, joints_by_uid.get(solid.uid))
        if mesh is not None:
            model.solids[i] = solid_with_body(solid, mesh)
