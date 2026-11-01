"""Three-sided gypsum reveals fitted to the resolved window product and stool.

On a buck-lined (outie) opening the board runs on the buck's face all the way to the frame.
The buck stands ``lining`` inside the framed jamb, so the stud-zone jamb and head are furred
out by a 3/8" plywood rip to that plane, and the field board laps the step.
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.findings import Finding, Result, Severity
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.geometry_millwork import window_stool_prism
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.model import (
    FramedMember,
    ResolvedLayer,
    ResolvedModel,
    ResolvedOpening,
    ResolvedSolid,
    ResolvedWall,
    ResolvedWindowStool,
)
from typehaus.resolve.model_window_returns import ResolvedWindowReturn, WindowReturnLayer

_GEOMETRY_TOLERANCE_M = 1e-9
_FUR_PREFIX = "buck-fur-"
_FUR_MATERIAL = "struct-1-plywood"  # the buck's own stock
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
    model.walls[:] = [_without_fur(wall) for wall in model.walls]
    from typehaus.resolve.countertop_edges import stool_wrapping_return

    walls = {wall.tag: wall for wall in model.walls}
    stools = {stool.window_ref: stool for stool in model.window_stools}
    furs: dict[str, list[FramedMember]] = {}
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
        lining = buck_lining_m(model, wall)
        stool = stools.get(opening.tag)
        if stool is not None and stool.corner_radii_m:
            stool = stool_wrapping_return(
                stool, sum(layer.thickness_m for layer, _ in stack) + lining,
                _bead_radius_m(model))
        try:
            record, solids, fur = _fit_return(wall, opening, stool, stack, lining)
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
        furs.setdefault(wall.uid, []).extend(fur)
        if stool is not None and stool is not stools.get(opening.tag):
            model.window_stools[model.window_stools.index(stools[opening.tag])] = stool
    # Walls are frozen; swap the furred ones in (as ``opening_flashing`` does).
    model.walls[:] = [replace(wall, members=(*wall.members, *furs[wall.uid]))
                      if wall.uid in furs else wall for wall in model.walls]
    return findings


def buck_lining_m(model: ResolvedModel, wall: ResolvedWall) -> float:
    """How far the buck's membrane face stands inside the framed RO: 0 off a truss wall."""
    from typehaus.resolve.flashing_config import FLASHING
    from typehaus.resolve.opening_flashing import opening_flashing_frame

    frame = opening_flashing_frame(model, wall)
    if frame is None or frame.buck <= _GEOMETRY_TOLERANCE_M:
        return 0.0
    return frame.buck + FLASHING.perimeter_membrane_m


def _without_fur(wall: ResolvedWall) -> ResolvedWall:
    kept = tuple(m for m in wall.members if not m.child_key.startswith(_FUR_PREFIX))
    return wall if len(kept) == len(wall.members) else replace(wall, members=kept)


def _bead_radius_m(model: ResolvedModel) -> float:
    """The house's window-return bullnose radius; 0 for a square bead or no standard."""
    from typehaus.resolve.drywall_led import drywall_standard

    standard, _findings = drywall_standard(model.plan)  # reported by drywall_trims
    radius = standard.window_corner_radius if standard is not None else None
    return radius.meters if radius is not None else 0.0


def _fit_return(wall: ResolvedWall, opening: ResolvedOpening,
                stool: ResolvedWindowStool | None, stack: FinishStack, lining: float = 0.0,
                ) -> tuple[ResolvedWindowReturn, list[ResolvedSolid], list[FramedMember]]:
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
    shell = [sign * project(point) for layer in layers
             if layer.function in ("structure", "sheathing") for point in layer.polygon]
    shell_face = max(shell) if shell else None
    # Unlined, a frame standing past the sheathing has nothing to carry a board beyond it.
    if lining <= _GEOMETRY_TOLERANCE_M and shell_face is not None:
        frame_face = min(frame_face, shell_face)
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
    ro_head = wall.base_ref_z_m + opening.sill_m + opening.height_m
    top = ro_head - lining if lining > _GEOMETRY_TOLERANCE_M else head.z1_m
    total = sum(layer.thickness_m for layer, _ in stack)
    inset = total + lining
    # The return may cover the frame's perimeter face, but must never cover glazing.
    jamb_width = max((p[0] - q[0]) * tangent[0] + (p[1] - q[1]) * tangent[1]
                     for p in left.ring for q in left.ring)
    glass_edge = max((p[0] - center[0]) * tangent[0] + (p[1] - center[1]) * tangent[1]
                     for p in left.ring)
    if (total <= 0 or total >= min(jamb_width, head.z1_m - head.z0_m)
            or top - total <= head.z0_m or -opening.width_m / 2 + inset >= glass_edge
            or top - bottom <= total or opening.width_m <= 2 * inset):
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
    board_depth = 0.0
    for index, (layer, coating) in enumerate(stack):
        backing = remaining - layer.thickness_m
        head_bottom = top - remaining
        head_top = top - backing
        inner_left, inner_right = -half + lining + backing, half - lining - backing
        near = face + coating_depth
        pieces = [
            ("jamb-left", ring(inner_left, inner_left + layer.thickness_m, near, frame_face),
             bottom, head_bottom),
            ("jamb-right", ring(inner_right - layer.thickness_m, inner_right, near, frame_face),
             bottom, head_bottom),
            ("head", ring(inner_left, inner_right, near, frame_face), head_bottom, head_top),
        ]
        lap_area = 0.0
        if lining > _GEOMETRY_TOLERANCE_M and not coating:
            # The field board runs past the framed RO onto the fur, to meet the return.
            lap = (face + board_depth, face + board_depth + layer.thickness_m)
            pieces.extend((
                ("lap-left", ring(-half, -half + lining, *lap), bottom, top),
                ("lap-right", ring(half - lining, half, *lap), bottom, top),
                ("lap-head", ring(-half, half, *lap), top, top + lining),
            ))
            board_depth += layer.thickness_m
            lap_area = lining * (2 * (top - bottom) + opening.width_m)
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
        area = (depth - coating_depth) * (2 * (head_bottom - bottom) + head_length) + lap_area
        if coating:
            area += (remaining + lining) * (opening.width_m + 2 * (head_bottom - bottom))
            coating_depth += layer.thickness_m
        quantities.append(WindowReturnLayer(layer.name, layer.material_ref,
                                             layer.thickness_m, area, coating))
        remaining = backing
    exposed_area = (depth * (2 * (top - total - bottom) + opening.width_m - 2 * inset)
                    + inset * (opening.width_m + 2 * (top - total - bottom)))
    fur = []
    if lining > _GEOMETRY_TOLERANCE_M and shell_face is not None:
        fur = _stud_zone_fur(wall, opening, point, normal, (face + total, shell_face),
                             bottom, ro_head)
    return ResolvedWindowReturn(
        uid=f"{opening.uid}-RETURN", tag=f"{opening.tag}-return",
        window_ref=opening.tag, wall_tag=wall.tag, storey=wall.storey,
        layers=tuple(quantities), exposed_area_m2=exposed_area,
        bead_length_m=2 * (top - total - bottom) + opening.width_m - 2 * inset,
    ), solids, fur



def _stud_zone_fur(wall: ResolvedWall, opening: ResolvedOpening, point, normal,
                   zone: tuple[float, float], bottom: float, ro_head: float,
                   ) -> list[FramedMember]:
    """3/8" plywood rips on the stud-zone jambs and head, flush with the buck's face."""
    from typehaus.resolve.framing.profiles import panel_profile
    from typehaus.resolve.framing.truss_common import BUCK_CATEGORY, BUCK_THICKNESS_IN

    thickness = BUCK_THICKNESS_IN * 0.0254
    near, far = zone
    if far - near <= _GEOMETRY_TOLERANCE_M:
        return []
    profile = panel_profile(round((far - near) / 0.0254, 4), BUCK_THICKNESS_IN)
    mid, half = (near + far) / 2, opening.width_m / 2
    head_z = ro_head - thickness

    def member(key, p0, p1, z0, z1, length, orient=None):
        return FramedMember(wall.uid, f"{_FUR_PREFIX}{key}-{opening.tag}", BUCK_CATEGORY,
                            profile, p0, p1, z0, z1, length, orient=orient,
                            material=_FUR_MATERIAL)

    out = [member("head", point(-half, mid), point(half, mid), head_z, ro_head, 2 * half)]
    if head_z - bottom > _GEOMETRY_TOLERANCE_M:
        for side, station in (("l", -half + thickness / 2), ("r", half - thickness / 2)):
            at = point(station, mid)
            out.append(member(f"jamb-{side}", at, at, bottom, head_z, head_z - bottom,
                              orient=(normal[0], normal[1])))
    return out
