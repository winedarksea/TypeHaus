"""Wall framing solver (#20) — pure deterministic (polygons, spec) -> [FramedMember].

Members are lightweight records (no geometry kernel) until emit (risk 6). M1 handles
level wall tops only; the raked-top/rafter arm activates with M3 roofs (→ 30 WP3.11).
"""

from __future__ import annotations

import math

from typehaus.model.enums import LayerFunction
from typehaus.model.plan import PlanModel
from typehaus.resolve.framing.tables import (
    DEFAULT_SPACING,
    header_size,
    king_jack_counts,
    member_actual,
)
from typehaus.resolve.geometry import add, length, scale, sub, unit
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedWall


def _structure_layer(plan: PlanModel, assembly_tag: str):
    asm = plan.library.resolve_assembly(assembly_tag)
    if asm is None:
        return None
    for layer in asm.layers:
        if layer.function is LayerFunction.STRUCTURE:
            return layer
    return None


def frame_wall(plan: PlanModel, rw: ResolvedWall, openings: list,
               corner_start: bool = False) -> tuple[FramedMember, ...]:
    """Generate studs, plates, and opening framing for one resolved wall.

    ``openings`` is a list of (center_m, width_m, height_m, sill_m, is_door) tuples.
    """
    layer = _structure_layer(plan, rw.assembly)
    if layer is None or layer.masonry is not None:
        return ()  # masonry walls take the arithmetic-takeoff path, no members (#23)
    spec = layer.framing
    if spec is None:
        return ()

    p0, p1 = rw.axis
    axis_len = length(sub(p1, p0))
    d = unit(sub(p1, p0))
    spacing = (spec.spacing or DEFAULT_SPACING).meters
    member = spec.member
    z0, z1 = rw.z0_m, rw.z1_m
    plate_h = 1.5 * 0.0254

    members: list[FramedMember] = []

    # --- plates ---------------------------------------------------------------
    members.append(_plate(rw, p0, p1, "plate-bottom", z0, z0 + plate_h))
    top_plates = 2 if spec.double_top_plate and not spec.advanced_framing else 1
    top_start, top_end = _wall_top_elevations(rw)
    for i in range(top_plates):
        start_bottom = top_start - plate_h * (i + 1)
        end_bottom = top_end - plate_h * (i + 1)
        if abs(start_bottom - end_bottom) < 1e-9:
            members.append(_plate(rw, p0, p1, f"plate-top-{i}", start_bottom,
                                  start_bottom + plate_h))
        else:
            members.append(FramedMember(
                rw.uid, f"plate-raked-{i}", "raked_plate", "plate", p0, p1,
                start_bottom, start_bottom + plate_h, axis_len,
                z0_end_m=end_bottom, z1_end_m=end_bottom + plate_h,
            ))

    # --- studs at spacing, skipping those inside an opening's rough width ------
    stud_z0 = z0 + plate_h
    stud_z1 = z1 - plate_h * top_plates
    n = int(axis_len // spacing)
    idx = 0
    for i in range(n + 1):
        s = i * spacing
        if s > axis_len + 1e-6:
            break
        if _inside_opening(s, openings):
            continue
        pt = add(p0, scale(d, s))
        fraction = s / axis_len if axis_len else 0.0
        stud_z1 = top_start + (top_end - top_start) * fraction - plate_h * top_plates
        members.append(
            FramedMember(rw.uid, f"stud-{idx:03d}", "stud", member, pt, pt,
                         stud_z0, stud_z1, stud_z1 - stud_z0)
        )
        idx += 1

    if corner_start:
        # A third stud at the owned end of each exterior corner favors the requested
        # strength-first 3/4-stud layout.  It is deliberately outside the regular
        # 16" module; the normal endpoint studs retain module continuity for sheathing,
        # standing-seam panels, and floor framing.
        corner_offset = min(1.5 * 0.0254, axis_len / 2.0)
        pt = add(p0, scale(d, corner_offset))
        fraction = corner_offset / axis_len if axis_len else 0.0
        corner_top = top_start + (top_end - top_start) * fraction - plate_h * top_plates
        members.append(FramedMember(rw.uid, "corner-start", "corner", member, pt, pt,
                                    stud_z0, corner_top, corner_top - stud_z0))

    # --- opening framing (king/jack/header/cripple/sill) ----------------------
    for oi, (center, width, height, sill, is_door) in enumerate(openings):
        members.extend(
            _frame_opening(rw, d, p0, center, width, height, sill, is_door, member,
                           stud_z0, stud_z1, oi)
        )
    return tuple(members)


def _wall_top_elevations(rw: ResolvedWall) -> tuple[float, float]:
    return (rw.top_z0_m if rw.top_z0_m is not None else rw.z1_m,
            rw.top_z1_m if rw.top_z1_m is not None else rw.z1_m)


def _plate(rw: ResolvedWall, p0, p1, key: str, z0: float, z1: float) -> FramedMember:
    return FramedMember(rw.uid, key, "plate", "plate", p0, p1, z0, z1, length(sub(p1, p0)))


def _inside_opening(s: float, openings) -> bool:
    for (center, width, _h, _sill, _door) in openings:
        if center - width / 2 - 0.02 <= s <= center + width / 2 + 0.02:
            return True
    return False


def _frame_opening(rw, d, p0, center, width, height, sill, is_door, member,
                   z0, z1, oi) -> list[FramedMember]:
    from typehaus.quantities import m as _m

    out: list[FramedMember] = []
    kings, jacks = king_jack_counts(_m(width))
    half = width / 2
    header_bottom = (z0 + sill + height) if not is_door else (z0 + height)
    for side, sign in (("l", -1), ("r", +1)):
        edge = center + sign * half
        for k in range(kings):
            pos = add(p0, scale(d, edge + sign * (0.04 + k * 0.04)))
            out.append(FramedMember(rw.uid, f"king-{oi}-{side}{k}", "king", member,
                                    pos, pos, z0, z1, z1 - z0))
        for j in range(jacks):
            pos = add(p0, scale(d, edge + sign * (0.01 + j * 0.04)))
            out.append(FramedMember(rw.uid, f"jack-{oi}-{side}{j}", "jack", member,
                                    pos, pos, z0, header_bottom, header_bottom - z0))
    hl = add(p0, scale(d, center - half))
    hr = add(p0, scale(d, center + half))
    out.append(FramedMember(rw.uid, f"header-{oi}", "header",
                            header_size(_m(width), rw is not None), hl, hr,
                            header_bottom, header_bottom + 0.14, width))
    return out


def frame_model(plan: PlanModel, model: ResolvedModel) -> None:
    """Attach framed members to every resolved wall (mutates the model in place)."""
    by_host: dict[str, list] = {}
    for op in model.openings:
        by_host.setdefault(op.host_wall, []).append(
            (op.center_along_m, op.width_m, op.height_m, op.sill_m, op.is_door)
        )
    framed: list[ResolvedWall] = []
    for rw in model.walls:
        members = frame_wall(plan, rw, by_host.get(rw.tag, []),
                             corner_start=_owns_exterior_corner(plan, rw))
        framed.append(
            ResolvedWall(
                uid=rw.uid, tag=rw.tag, storey=rw.storey, assembly=rw.assembly,
                axis=rw.axis, layers=rw.layers, z0_m=rw.z0_m, z1_m=rw.z1_m,
                is_foundation=rw.is_foundation, members=members,
                top_z0_m=rw.top_z0_m, top_z1_m=rw.top_z1_m,
            )
        )
    model.walls = framed


def _owns_exterior_corner(plan: PlanModel, rw: ResolvedWall) -> bool:
    """Assign one supplemental corner stud to the wall starting at each true corner."""
    authored = plan.by_tag(rw.tag)
    if authored is None or not _is_exterior_wall(rw):
        return False
    siblings = [element for element in plan.storey_elements(rw.storey)
                if element.element_kind == "Wall" and element.tag != rw.tag
                and getattr(element, "end_node", None) == authored.start_node]
    if not siblings:
        return False
    nodes = {element.tag: element.position.xy_m for element in plan.storey_elements(rw.storey)
             if element.element_kind == "Node"}
    start, end = nodes.get(authored.start_node), nodes.get(authored.end_node)
    if start is None or end is None:
        return False
    direction = (end[0] - start[0], end[1] - start[1])
    for sibling in siblings:
        sibling_start = nodes.get(sibling.start_node)
        if sibling_start is None:
            continue
        incoming = (start[0] - sibling_start[0], start[1] - sibling_start[1])
        if math.hypot(*incoming) > 1e-9 and math.hypot(*direction) > 1e-9:
            cross = incoming[0] * direction[1] - incoming[1] * direction[0]
            if abs(cross) > 1e-9:
                return True
    return False


def _is_exterior_wall(wall: ResolvedWall) -> bool:
    return any(layer.function == "cladding" for layer in wall.layers)
