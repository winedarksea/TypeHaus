"""Validated perpendicular wall supports for nonbearing pocket frames.

Resolve before framing so every consumer uses the same permission to omit a jamb
pack. Complete the connection after framing by reusing a full-height stud or adding
one inside the support wall; a ladder rung alone cannot support the frame head.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from shapely.geometry import LineString, Polygon

from typehaus.findings import Finding, Result, Severity
from typehaus.model.elements import Door, Wall
from typehaus.model.enums import StructuralRole
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.tables import member_actual
from typehaus.resolve.geometry import add, normal, pocket_centerline_offset, scale, sub, unit
from typehaus.resolve.model import FramedMember
from typehaus.resolve.overlay import union_all

_GEOMETRY_TOLERANCE_M = 1e-5
_PERPENDICULAR_TOLERANCE = 1e-5
_FULL_HEIGHT_CATEGORIES = {"stud", "king", "corner"}


@dataclass(frozen=True)
class FrameEndConnection:
    wall_tag: str
    point: tuple[float, float]
    direction: tuple[float, float]
    member: str
    stud_bottom_m: float
    stud_top_m: float
    contact_line: tuple[tuple[float, float], tuple[float, float]]


def framed_extent(opening) -> tuple[float, float]:
    low = opening.center_along_m - opening.width_m / 2
    high = opening.center_along_m + opening.width_m / 2
    if opening.pocket_sign < 0:
        low -= opening.pocket_run_m
    elif opening.pocket_sign > 0:
        high += opening.pocket_run_m
    return low, high


def _structure(plan, wall):
    return next(
        (
            layer
            for layer in plan.library.resolve_assembly(wall.assembly).layers
            if layer.function.value == "structure"
        ),
        None,
    )


def _connection(plan, model, opening, reference: str, at_start: bool):
    authored = {wall.tag: wall for wall in plan.all_elements() if isinstance(wall, Wall)}
    host, support = model.wall(opening.host_wall), model.wall(reference)
    if support is None:
        raise ValueError(f"support wall {reference} does not exist")
    host_source, support_source = authored[host.tag], authored[support.tag]
    if not (
        {host_source.start_node, host_source.end_node}
        & {support_source.start_node, support_source.end_node}
    ):
        raise ValueError(f"support wall {reference} is disconnected from the host")
    direction = unit(sub(host.axis[1], host.axis[0]))
    support_direction = unit(sub(support.axis[1], support.axis[0]))
    if (
        abs(sum(a * b for a, b in zip(direction, support_direction, strict=True)))
        > _PERPENDICULAR_TOLERANCE
    ):
        raise ValueError(f"support wall {reference} must be perpendicular to the frame")
    layer, host_layer = _structure(plan, support), _structure(plan, host)
    if layer is None or layer.framing is None or layer.framing.wall_frame != "studs":
        raise ValueError(f"support wall {reference} must have stud framing")
    if host_layer is None or host_layer.framing is None:
        raise ValueError("the host must have stud framing")
    thickness, depth = (value * M_PER_IN for value in member_actual(layer.framing.member))
    if depth + _GEOMETRY_TOLERANCE_M < host_layer.thickness.meters:
        raise ValueError(f"support wall {reference} has insufficient framing depth")
    structure = next(layer for layer in support.layers if layer.function == "structure")
    projections = [
        sum(a * b for a, b in zip(sub(point, host.axis[0]), direction, strict=True))
        for point in structure.polygon
    ]
    face = max(projections) if at_start else min(projections)
    station = framed_extent(opening)[0 if at_start else 1]
    if abs(face - station) > _GEOMETRY_TOLERANCE_M:
        raise ValueError(f"frame end does not meet the structure face of {reference}")
    end = add(
        add(host.axis[0], scale(direction, station)),
        scale(normal(direction), pocket_centerline_offset(host)),
    )
    contact_line = tuple(
        add(end, scale(normal(direction), sign * host_layer.thickness.meters / 2))
        for sign in (-1, 1)
    )
    point = add(end, scale(direction, -depth / 2 if at_start else depth / 2))
    bottom = support.base_ref_z_m + thickness
    plate_top = support.plate_top_z_m if support.plate_top_z_m is not None else support.z1_m
    top = min(
        value if value is not None else plate_top for value in (support.top_z0_m, support.top_z1_m)
    )
    top -= thickness * (
        2 if layer.framing.double_top_plate and not layer.framing.advanced_framing else 1
    )
    if (
        bottom > host.base_ref_z_m + thickness + _GEOMETRY_TOLERANCE_M
        or top < host.base_ref_z_m + opening.sill_m + opening.height_m + thickness
    ):
        raise ValueError(f"support wall {reference} cannot support the frame head vertically")
    candidate = FramedMember(
        support.uid,
        "candidate",
        "stud",
        layer.framing.member,
        point,
        point,
        bottom,
        top,
        top - bottom,
        orient=support_direction,
    )
    footprint = Polygon(member_footprint(candidate)[0])
    # A support stud can straddle an authored seam, but only through matching continuous
    # framing. It must never extend into an unrelated corner or an opening.
    # Mitred corner polygons divide ownership, not the rectangular wood section.
    # The host may own the other half of that corner, outside the framed extent.
    compatible = [Polygon(layer.polygon) for layer in host.layers if layer.function == "structure"]
    for wall in model.walls:
        if (
            wall.assembly != support.assembly
            or abs(wall.base_ref_z_m - support.base_ref_z_m) > _GEOMETRY_TOLERANCE_M
        ):
            continue
        wall_direction = unit(sub(wall.axis[1], wall.axis[0]))
        if (
            abs(sum(a * b for a, b in zip(direction, wall_direction, strict=True)))
            > _PERPENDICULAR_TOLERANCE
        ):
            continue
        compatible.extend(
            Polygon(layer.polygon) for layer in wall.layers if layer.function == "structure"
        )
    if not union_all(compatible).buffer(_GEOMETRY_TOLERANCE_M).covers(footprint):
        raise ValueError(f"support stud for {reference} does not fit inside continuous framing")
    for other in model.openings:
        wall = model.wall(other.host_wall)
        if wall is None or wall.assembly != support.assembly:
            continue
        axis = unit(sub(wall.axis[1], wall.axis[0]))
        perpendicular = (-axis[1], axis[0])
        low, high = framed_extent(other)
        mid = add(wall.axis[0], scale(axis, (low + high) / 2))
        void = Polygon(
            [
                add(
                    add(mid, scale(axis, sign * (high - low) / 2)),
                    scale(perpendicular, side * depth / 2),
                )
                for sign, side in ((-1, -1), (1, -1), (1, 1), (-1, 1))
            ]
        )
        if (
            wall.base_ref_z_m + other.sill_m < top
            and wall.base_ref_z_m + other.sill_m + other.height_m > bottom
            and void.intersection(footprint).area > _GEOMETRY_TOLERANCE_M**2
        ):
            raise ValueError(f"support stud for {reference} conflicts with opening {other.tag}")
    return FrameEndConnection(
        reference, point, support_direction, layer.framing.member, bottom, top, contact_line
    )


def resolve_frame_end_supports(plan, model) -> tuple[dict, list[Finding]]:
    connections, findings = {}, []
    for index, original in enumerate(model.openings):
        opening = replace(original, frame_start_support_wall=None, frame_end_support_wall=None)
        model.openings[index] = opening
        source = plan.by_tag(opening.tag)
        supports = getattr(source, "frame_end_supports", None)
        if supports is None:
            continue
        try:
            if not isinstance(source, Door) or not opening.pocket_run_m:
                raise ValueError("frame_end_supports is supported only on pocket doors")
            if plan.by_tag(opening.host_wall).structural_role != StructuralRole.NONBEARING:
                raise ValueError("frame_end_supports requires an explicitly nonbearing host")
            resolved = {}
            for at_start, reference in (
                (True, supports.start_wall_ref),
                (False, supports.end_wall_ref),
            ):
                if reference is not None:
                    resolved[at_start] = _connection(plan, model, opening, reference, at_start)
        except ValueError as error:
            findings.append(
                Finding(
                    severity=Severity.ERROR,
                    check_id="integrity.frame_end_support",
                    message=f"{opening.tag}: {error}",
                    element_tags=(opening.tag,),
                    result=Result.FAIL,
                )
            )
            continue  # Fail closed: neither jamb may disappear on an invalid declaration.
        model.openings[index] = replace(
            opening,
            frame_start_support_wall=resolved[True].wall_tag if True in resolved else None,
            frame_end_support_wall=resolved[False].wall_tag if False in resolved else None,
        )
        for at_start, connection in resolved.items():
            connections[(opening.tag, at_start)] = connection
    return connections, findings


def complete_frame_end_supports(model, connections) -> None:
    members_by_wall = {wall.tag: list(wall.members) for wall in model.walls}
    for (opening_tag, at_start), connection in connections.items():
        wall = model.wall(connection.wall_tag)
        candidate = FramedMember(
            wall.uid,
            f"frame-support-{opening_tag}-{'start' if at_start else 'end'}",
            "stud",
            connection.member,
            connection.point,
            connection.point,
            connection.stud_bottom_m,
            connection.stud_top_m,
            connection.stud_top_m - connection.stud_bottom_m,
            orient=connection.direction,
            opening_tag=opening_tag,
            material=next(
                (member.material for member in wall.members if member.category == "stud"), None
            ),
        )
        footprint = Polygon(member_footprint(candidate)[0])
        contact = LineString(connection.contact_line)
        minimum_contact = member_actual(connection.member)[0] * M_PER_IN
        for support_wall in model.walls:
            for member in members_by_wall[support_wall.tag]:
                ring, bottom, top = member_footprint(member)
                if (
                    member.category in _FULL_HEIGHT_CATEGORIES
                    and bottom <= candidate.z0_m + _GEOMETRY_TOLERANCE_M
                    and top >= candidate.z1_m - _GEOMETRY_TOLERANCE_M
                    and Polygon(ring).buffer(_GEOMETRY_TOLERANCE_M).intersection(contact).length
                    + _GEOMETRY_TOLERANCE_M
                    >= minimum_contact
                ):
                    break
            else:
                continue
            break
        else:
            # Full-height backing replaces the intersecting finish ladder rungs. Other
            # framing is retained for the model-wide member interference check.
            for support_wall in model.walls:
                retained = []
                for member in members_by_wall[support_wall.tag]:
                    ring, bottom, top = member_footprint(member)
                    overlaps = (
                        min(top, candidate.z1_m) > max(bottom, candidate.z0_m)
                        and Polygon(ring).intersection(footprint).area > _GEOMETRY_TOLERANCE_M**2
                    )
                    if (
                        overlaps
                        and member.child_key.startswith("tee-")
                        and member.category == "blocking"
                    ):
                        continue
                    retained.append(member)
                members_by_wall[support_wall.tag] = retained
            members_by_wall[wall.tag].append(candidate)
    model.walls = [replace(wall, members=tuple(members_by_wall[wall.tag])) for wall in model.walls]
