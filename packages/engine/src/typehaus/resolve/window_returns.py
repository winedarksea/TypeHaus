"""Three-sided gypsum reveals fitted to the resolved window product and stool."""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.geometry_millwork import window_stool_prism
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.model import (
    ResolvedLayer,
    ResolvedModel,
    ResolvedOpening,
    ResolvedSolid,
    ResolvedWall,
    ResolvedWindowStool,
)
from typehaus.resolve.model_window_returns import ResolvedWindowReturn, WindowReturnLayer

_GEOMETRY_TOLERANCE_M = 1e-9
FinishStack = list[tuple[ResolvedLayer, bool]]


def _finish_stack(model: ResolvedModel, wall: ResolvedWall) -> FinishStack:
    """Only the exposed coatings and consecutive gypsum boards, never buried linings."""
    layers = []
    has_gypsum = False
    for layer in wall.body_layers():
        material = model.plan.library.material(layer.material_ref)
        gypsum = bool(getattr(material, "gypsum_type", None))
        coating = bool(getattr(material, "coating", False))
        if not gypsum and not (coating and not has_gypsum):
            break
        layers.append((layer, coating))
        has_gypsum |= gypsum
    return layers if has_gypsum else []


def resolve_window_returns(model: ResolvedModel) -> list[Finding]:
    """Emit fitted solids and immutable quantity records; safe to rerun after an edit."""
    model.window_returns.clear()
    model.solids[:] = [solid for solid in model.solids if solid.category != "window_return"]
    from typehaus.resolve.countertop_edges import stool_wrapping_return

    walls = {wall.tag: wall for wall in model.walls}
    stools = {stool.window_ref: stool for stool in model.window_stools}
    findings = []
    for opening in model.openings:
        if opening.kind != "window":
            continue
        authored = model.plan.by_tag(opening.tag)
        if not getattr(authored, "drywall_returns", True):
            continue
        wall = walls.get(opening.host_wall)
        if wall is None:
            continue
        stack = _finish_stack(model, wall)
        if not stack:
            continue
        stool = stools.get(opening.tag)
        if stool is not None and stool.corner_radii_m:
            stool = stool_wrapping_return(
                stool, sum(layer.thickness_m for layer, _ in stack), _bead_radius_m(model))
        try:
            record, solids = _fit_return(wall, opening, stool, stack)
        except ValueError as error:
            findings.append(Finding(
                severity=Severity.WARN, result=Result.UNKNOWN,
                check_id="resolve.window_returns", element_tags=(opening.tag,),
                message=f"Cannot fit drywall returns at {opening.tag}: {error}",
                fix_hint="Review the opening and interior finish, or set drywall_returns=False.",
            ))
            continue
        model.window_returns.append(record)
        model.solids.extend(solids)
        if stool is not None and stool is not stools.get(opening.tag):
            model.window_stools[model.window_stools.index(stools[opening.tag])] = stool
    return findings


def _bead_radius_m(model: ResolvedModel) -> float:
    """The house's window-return bullnose radius; 0 for a square bead or no standard."""
    from typehaus.resolve.drywall_led import drywall_standard

    standard, _findings = drywall_standard(model.plan)  # reported by drywall_trims
    radius = standard.window_corner_radius if standard is not None else None
    return radius.meters if radius is not None else 0.0


def _fit_return(wall: ResolvedWall, opening: ResolvedOpening,
                stool: ResolvedWindowStool | None,
                stack: FinishStack) -> tuple[ResolvedWindowReturn, list[ResolvedSolid]]:
    if opening.arch_rise_m > _GEOMETRY_TOLERANCE_M:
        raise ValueError("arched window heads are not supported")
    origin, tangent, normal, run = wall_frame(wall)
    center = opening_center(wall, opening)
    if run <= _GEOMETRY_TOLERANCE_M or center is None:
        raise ValueError("wall axis has no length")

    def project(point):
        return (point[0] - origin[0]) * normal[0] + (point[1] - origin[1]) * normal[1]

    layers = wall.depth_layers()
    first = [project(point) for point in layers[0].polygon]
    last = [project(point) for point in layers[-1].polygon]
    if not first or not last:
        raise ValueError("wall finish has no face")
    delta = sum(last) / len(last) - sum(first) / len(first)
    if abs(delta) <= _GEOMETRY_TOLERANCE_M:
        raise ValueError("interior and exterior wall faces are ambiguous")
    sign = 1.0 if delta > 0 else -1.0
    face = min(sign * value for value in first)
    frame = next((part for part in opening_parts(wall, opening, None)
                  if part.key == "frame"), None)
    if frame is None or len(frame.solids) != 4:
        raise ValueError("window product has no rectangular frame")
    left, _right, head, sill = frame.solids
    frame_face = min(sign * project(point) for solid in frame.solids for point in solid.ring)
    depth = frame_face - face
    if depth <= _GEOMETRY_TOLERANCE_M:
        raise ValueError("window frame leaves no interior reveal depth")
    bottom = sill.z1_m
    if stool is not None:
        prism = window_stool_prism(wall, opening, stool)
        if prism is None:
            raise ValueError("the authored stool has no fitted geometry")
        # A stool notched round the finished return leaves the board to run past it.
        bottom = prism.z0_m if stool.notch_inset_m > 0 else prism.z1_m
    top = head.z1_m
    total = sum(layer.thickness_m for layer, _ in stack)
    # The return may cover the frame's perimeter face, but must never cover glazing.
    jamb_width = max((p[0] - q[0]) * tangent[0] + (p[1] - q[1]) * tangent[1]
                     for p in left.ring for q in left.ring)
    if (total <= 0 or total >= min(jamb_width, head.z1_m - head.z0_m)
            or top - bottom <= total or opening.width_m <= 2 * total):
        raise ValueError("finish stack does not fit the frame's perimeter face")
    for layer, _ in stack:
        if layer.thickness_m < 0:
            raise ValueError(f"finish layer {layer.name} has negative thickness")
        low, high = layer.band(wall)
        if low > bottom + _GEOMETRY_TOLERANCE_M or high < top - _GEOMETRY_TOLERANCE_M:
            raise ValueError(f"finish layer {layer.name} does not cover the whole reveal")

    def point(along, offset):
        normal_offset = sign * offset
        return (center[0] + tangent[0] * along + normal[0] * normal_offset,
                center[1] + tangent[1] * along + normal[1] * normal_offset)

    def ring(x0, x1, near, far):
        return [point(x0, near), point(x1, near), point(x1, far), point(x0, far)]

    solids, quantities = [], []
    remaining = total
    coating_depth = 0.0
    half = opening.width_m / 2
    for index, (layer, coating) in enumerate(stack):
        backing = remaining - layer.thickness_m
        head_bottom = top - remaining
        head_top = top - backing
        inner_left, inner_right = -half + backing, half - backing
        near = face + coating_depth
        pieces = [
            ("jamb-left", ring(inner_left, inner_left + layer.thickness_m, near, frame_face),
             bottom, head_bottom),
            ("jamb-right", ring(inner_right - layer.thickness_m, inner_right, near, frame_face),
             bottom, head_bottom),
            ("head", ring(inner_left, inner_right, near, frame_face), head_bottom, head_top),
        ]
        if coating and backing > 0:
            # Wrap the room-facing cut ends too: a reveal-only film would leave a white
            # gypsum border around an accent wall. Deeper layers start behind these caps.
            far = near + layer.thickness_m
            pieces.extend((
                ("jamb-left-front", ring(-half, inner_left, near, far), bottom, head_top),
                ("jamb-right-front", ring(inner_right, half, near, far), bottom, head_top),
                ("head-front", ring(-half, half, near, far), head_top, top),
            ))
        for edge, outline, z0, z1 in pieces:
            if layer.thickness_m == 0:
                continue
            solids.append(ResolvedSolid(
                uid=f"{opening.uid}-RETURN-{index}-{edge}",
                tag=f"{opening.tag}-return-{index}-{edge}", storey=wall.storey,
                category="window_return", outline=outline, z0_m=z0, z1_m=z1,
                material=layer.material_ref, host_ref=opening.tag))
        # Board orders include the head's lap. Paint covers the clear reveal plus the
        # narrow front border; hidden contacts between the coating prisms add no area.
        head_length = inner_right - inner_left - (2 * layer.thickness_m if coating else 0)
        area = (depth - coating_depth) * (2 * (head_bottom - bottom) + head_length)
        if coating:
            area += remaining * (opening.width_m + 2 * (head_bottom - bottom))
            coating_depth += layer.thickness_m
        quantities.append(WindowReturnLayer(layer.name, layer.material_ref,
                                             layer.thickness_m, area, coating))
        remaining = backing
    exposed_area = (depth * (2 * (top - total - bottom) + opening.width_m - 2 * total)
                    + total * (opening.width_m + 2 * (top - total - bottom)))
    return ResolvedWindowReturn(
        uid=f"{opening.uid}-RETURN", tag=f"{opening.tag}-return",
        window_ref=opening.tag, wall_tag=wall.tag, storey=wall.storey,
        layers=tuple(quantities), exposed_area_m2=exposed_area,
        bead_length_m=2 * (top - total - bottom) + opening.width_m - 2 * total,
    ), solids
