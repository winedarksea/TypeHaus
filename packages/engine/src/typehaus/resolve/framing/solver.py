"""Wall framing solver (#20) — pure deterministic (polygons, spec) -> [FramedMember].

Members are lightweight records (no geometry kernel) until emit (risk 6). M1 handles
level wall tops only; the raked-top/rafter arm activates with M3 roofs (→ 30 WP3.11).
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.model.enums import LayerFunction
from typehaus.model.plan import PlanModel
from typehaus.resolve.framing.tables import (
    DEFAULT_SPACING,
    header_size,
    king_jack_counts,
    member_actual,
)
from typehaus.resolve.geometry import add, length, normal, scale, sub, unit
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

    p0, p1 = _framing_axis(rw)
    axis_len = length(sub(p1, p0))
    d = unit(sub(p1, p0))
    spacing = (spec.spacing or DEFAULT_SPACING).meters
    member = spec.member
    z0, z1 = rw.z0_m, rw.z1_m
    plate_h = 1.5 * 0.0254

    members: list[FramedMember] = []

    # --- plates ---------------------------------------------------------------
    members.append(_plate(rw, p0, p1, "plate-bottom", z0, z0 + plate_h, member))
    top_plates = 2 if spec.double_top_plate and not spec.advanced_framing else 1
    top_start, top_end = _wall_top_elevations(rw)
    for i in range(top_plates):
        start_bottom = top_start - plate_h * (i + 1)
        end_bottom = top_end - plate_h * (i + 1)
        if abs(start_bottom - end_bottom) < 1e-9:
            members.append(_plate(rw, p0, p1, f"plate-top-{i}", start_bottom,
                                  start_bottom + plate_h, member))
        else:
            members.append(FramedMember(
                rw.uid, f"plate-raked-{i}", "raked_plate", member, p0, p1,
                start_bottom, start_bottom + plate_h, axis_len,
                z0_end_m=end_bottom, z1_end_m=end_bottom + plate_h,
            ))

    # --- studs at spacing, skipping those inside an opening's rough width ------
    stud_z0 = z0 + plate_h

    def top_at(s: float) -> float:
        """Framing top (below the top plate(s)) at station ``s`` along the wall axis.

        Interpolates between the wall's raked endpoints so every vertical member —
        regular stud, corner stud, or king stud in an opening — gets the top that
        matches the roof plane at its own plan position, not some other member's.
        """
        fraction = s / axis_len if axis_len else 0.0
        return top_start + (top_end - top_start) * fraction - plate_h * top_plates

    n = int(axis_len // spacing)
    idx = 0
    last_s = None
    for i in range(n + 1):
        s = i * spacing
        if s > axis_len + 1e-6:
            break
        if _inside_opening(s, openings):
            continue
        pt = add(p0, scale(d, s))
        stud_top = top_at(s)
        members.append(
            FramedMember(rw.uid, f"stud-{idx:03d}", "stud", member, pt, pt,
                         stud_z0, stud_top, stud_top - stud_z0, orient=d)
        )
        idx += 1
        last_s = s

    # A stud at the wall's far end regardless of module alignment: standard framing
    # practice puts a stud at both ends of every wall, but the spacing loop above only
    # reaches the end when axis_len happens to be an exact multiple of the module. The
    # off-module remainder was silently leaving one end bare — most visibly at exterior
    # corners, where the *incoming* wall's own end stud is exactly what the neighbor's
    # ``corner_start`` supplemental stud assumes exists (see WP-corner-3-stud).
    if last_s is None or axis_len - last_s > 1e-6:
        if not _inside_opening(axis_len, openings):
            pt = add(p0, scale(d, axis_len))
            stud_top = top_at(axis_len)
            members.append(
                FramedMember(rw.uid, f"stud-{idx:03d}", "stud", member, pt, pt,
                             stud_z0, stud_top, stud_top - stud_z0, orient=d)
            )
            idx += 1

    if corner_start:
        # A third stud at the owned end of each exterior corner favors the requested
        # strength-first 3/4-stud layout.  It is deliberately outside the regular
        # 16" module; the normal endpoint studs retain module continuity for sheathing,
        # standing-seam panels, and floor framing. corner_style="4-stud" adds a second
        # supplemental stud one bay further in, for the box-corner variant.
        corner_offset = min(1.5 * 0.0254, axis_len / 2.0)
        pt = add(p0, scale(d, corner_offset))
        corner_top = top_at(corner_offset)
        members.append(FramedMember(rw.uid, "corner-start", "corner", member, pt, pt,
                                    stud_z0, corner_top, corner_top - stud_z0, orient=d))
        if spec.corner_style == "4-stud":
            corner_offset2 = min(2 * 1.5 * 0.0254, axis_len / 2.0)
            pt2 = add(p0, scale(d, corner_offset2))
            corner_top2 = top_at(corner_offset2)
            members.append(FramedMember(rw.uid, "corner-start-2", "corner", member,
                                        pt2, pt2, stud_z0, corner_top2,
                                        corner_top2 - stud_z0, orient=d))

    # --- opening framing (king/jack/header/cripple/sill) ----------------------
    for oi, (center, width, height, sill, is_door) in enumerate(openings):
        members.extend(
            _frame_opening(rw, d, p0, center, width, height, sill, is_door, member,
                           stud_z0, top_at, oi)
        )
    return tuple(members)


def _framing_axis(rw: ResolvedWall) -> tuple[tuple[float, float], tuple[float, float]]:
    """Translate the wall datum axis to the resolved structure-layer centerline.

    The wall axis may intentionally name an exterior sheathing face.  Framing keeps
    its authored direction and along-wall opening distances, but must sit inside the
    structure layer represented by the resolved polygon.
    """
    structure = next((layer for layer in rw.layers if layer.function == "structure"), None)
    if structure is None or not structure.polygon:
        return rw.axis
    raw_start, raw_end = rw.axis
    perpendicular = normal(unit(sub(raw_end, raw_start)))
    if perpendicular == (0.0, 0.0):
        return rw.axis
    offsets = [
        (point[0] - raw_start[0]) * perpendicular[0]
        + (point[1] - raw_start[1]) * perpendicular[1]
        for point in structure.polygon
    ]
    translation = scale(perpendicular, sum(offsets) / len(offsets))
    return add(raw_start, translation), add(raw_end, translation)


def _wall_top_elevations(rw: ResolvedWall) -> tuple[float, float]:
    """Where the framing tops out — the double top plate, not the wall's overall top.

    A platform-framed wall spans floor-to-floor, but studs stop at the plate; the band
    above is the rim board and joists (``plate_top_z_m``, set by the stacking extension).
    """
    default = rw.plate_top_z_m if rw.plate_top_z_m is not None else rw.z1_m
    return (rw.top_z0_m if rw.top_z0_m is not None else default,
            rw.top_z1_m if rw.top_z1_m is not None else default)


def _plate(rw: ResolvedWall, p0, p1, key: str, z0: float, z1: float,
          profile: str) -> FramedMember:
    return FramedMember(rw.uid, key, "plate", profile, p0, p1, z0, z1, length(sub(p1, p0)))


def _inside_opening(s: float, openings) -> bool:
    for (center, width, _h, _sill, _door) in openings:
        if center - width / 2 - 0.02 <= s <= center + width / 2 + 0.02:
            return True
    return False


def _frame_opening(rw, d, p0, center, width, height, sill, is_door, member,
                   z0, top_at, oi) -> list[FramedMember]:
    from typehaus.quantities import m as _m

    out: list[FramedMember] = []
    plate_h = 1.5 * 0.0254
    kings, jacks = king_jack_counts(_m(width))
    half = width / 2
    header_bottom = (z0 + sill + height) if not is_door else (z0 + height)
    header_depth = 0.14
    # Keep the header directly over the jack studs.  The small extension reaches the
    # jack centreline on each side rather than stopping at the rough-opening edge.
    bearing = 0.01 + max(0, jacks - 1) * 0.04
    header_left_station = center - half - bearing
    header_right_station = center + half + bearing
    for side, sign in (("l", -1), ("r", +1)):
        edge = center + sign * half
        for k in range(kings):
            s = edge + sign * (0.04 + k * 0.04)
            pos = add(p0, scale(d, s))
            king_top = top_at(s)
            out.append(FramedMember(rw.uid, f"king-{oi}-{side}{k}", "king", member,
                                    pos, pos, z0, king_top, king_top - z0, orient=d))
        for j in range(jacks):
            pos = add(p0, scale(d, edge + sign * (0.01 + j * 0.04)))
            out.append(FramedMember(rw.uid, f"jack-{oi}-{side}{j}", "jack", member,
                                    pos, pos, z0, header_bottom, header_bottom - z0, orient=d))
    hl = add(p0, scale(d, header_left_station))
    hr = add(p0, scale(d, header_right_station))
    out.append(FramedMember(rw.uid, f"header-{oi}", "header",
                            header_size(_m(width), rw is not None), hl, hr,
                            header_bottom, header_bottom + header_depth,
                            width + 2 * bearing))

    if not is_door:
        sill_z0 = z0 + sill
        sill_z1 = sill_z0 + plate_h
        out.append(FramedMember(
            rw.uid, f"sill-{oi}", "sill", member, hl, hr, sill_z0, sill_z1,
            width + 2 * bearing,
        ))
        # Cripples under the rough sill and above the header retain the normal stud
        # module without placing framing through the opening itself.
        _append_opening_cripples(out, rw.uid, oi, d, p0, center, half, z0, sill_z0,
                                 header_bottom + header_depth, top_at, member)
    return out


def _append_opening_cripples(out: list[FramedMember], parent_uid: str, opening_index: int,
                             direction, wall_start, center: float, half: float,
                             bottom: float, sill: float, header_top: float, top_at,
                             member: str) -> None:
    """Add deterministic sill and header cripples at a 16 in. maximum spacing."""
    spacing = DEFAULT_SPACING.meters
    start, end = center - half, center + half
    stations = [start + index * spacing for index in range(int((end - start) // spacing) + 1)]
    if not stations or stations[-1] < end - 1e-6:
        stations.append(end)
    # Edge stations coincide with jack framing, so only interior stations are cripples.
    for index, station in enumerate(stations):
        if station <= start + 1e-6 or station >= end - 1e-6:
            continue
        position = add(wall_start, scale(direction, station))
        if sill - bottom > 1e-6:
            out.append(FramedMember(parent_uid, f"cripple-sill-{opening_index}-{index:02d}",
                                    "cripple", member, position, position, bottom, sill,
                                    sill - bottom, orient=direction))
        wall_top = top_at(station)
        if wall_top - header_top > 1e-6:
            out.append(FramedMember(parent_uid, f"cripple-head-{opening_index}-{index:02d}",
                                    "cripple", member, position, position, header_top,
                                    wall_top, wall_top - header_top, orient=direction))


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
        # ``replace`` rather than a field-by-field rebuild: this pass only adds members,
        # and respelling the constructor here silently drops any field added later.
        framed.append(replace(rw, members=members))
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
