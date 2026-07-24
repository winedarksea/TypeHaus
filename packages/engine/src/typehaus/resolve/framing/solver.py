"""Wall framing solver (#20) — pure deterministic (polygons, spec) -> [FramedMember].

Members are lightweight records (no geometry kernel) until emit (risk 6). M1 handles
level wall tops only; the raked-top/rafter arm activates with M3 roofs (→ 30 WP3.11).
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import LayerFunction
from typehaus.model.plan import PlanModel
from typehaus.resolve.framing.tables import (
    DEFAULT_SPACING,
    DEFAULT_TEE_BLOCKING_SPACING,
    header_size,
    king_jack_counts,
    member_actual,
)
from typehaus.resolve.geometry import add, length, normal, scale, sub, unit
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedWall

_EPSILON = 1e-9


def _structure_layer(plan: PlanModel, assembly_tag: str):
    asm = plan.library.resolve_assembly(assembly_tag)
    if asm is None:
        return None
    for layer in asm.layers:
        if layer.function is LayerFunction.STRUCTURE:
            return layer
    return None


def frame_wall(plan: PlanModel, rw: ResolvedWall, openings: list,
               corner_start: bool = False, corner_end: bool = False,
               tee_stations: tuple[tuple[float, str], ...] = ()) \
        -> tuple[FramedMember, ...]:
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
    z0 = rw.z0_m
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

    # --- studs at spacing, skipping those inside an opening's king/jack pack --
    stud_z0 = z0 + plate_h
    # A regular module stud that would fall inside an opening's trimmer/king pack is
    # redundant (the pack already carries the load there) and would only interpenetrate
    # it. Exclude the full pack width, not just the rough opening.
    stud_zones = _opening_exclusions(openings, member_actual(member)[0] * 0.0254)

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
    stud_stations: list[float] = []  # placed regular-stud stations, for in-line blocking
    for i in range(n + 1):
        s = i * spacing
        if s > axis_len + 1e-6:
            break
        if _in_exclusion(s, stud_zones):
            continue
        pt = add(p0, scale(d, s))
        stud_top = top_at(s)
        members.append(
            FramedMember(rw.uid, f"stud-{idx:03d}", "stud", member, pt, pt,
                         stud_z0, stud_top, stud_top - stud_z0, orient=d)
        )
        idx += 1
        last_s = s
        stud_stations.append(s)

    # A stud at the wall's far end regardless of module alignment: standard framing
    # practice puts a stud at both ends of every wall, but the spacing loop above only
    # reaches the end when axis_len happens to be an exact multiple of the module. The
    # off-module remainder was silently leaving one end bare — most visibly at exterior
    # corners, where the *incoming* wall's own end stud is exactly what the neighbor's
    # ``corner_start`` supplemental stud assumes exists (see WP-corner-3-stud).
    if (last_s is None or axis_len - last_s > 1e-6) \
            and not _in_exclusion(axis_len, stud_zones):
        pt = add(p0, scale(d, axis_len))
        stud_top = top_at(axis_len)
        members.append(
            FramedMember(rw.uid, f"stud-{idx:03d}", "stud", member, pt, pt,
                         stud_z0, stud_top, stud_top - stud_z0, orient=d)
        )
        idx += 1
        stud_stations.append(axis_len)

    def append_corner(endpoint: str) -> None:
        # A third stud at the owned end of each exterior corner favors the requested
        # strength-first 3/4-stud layout.  It is deliberately outside the regular
        # 16" module; the normal endpoint studs retain module continuity for sheathing,
        # standing-seam panels, and floor framing. corner_style="4-stud" adds a second
        # supplemental stud one bay further in, for the box-corner variant.
        direction_sign = 1.0 if endpoint == "start" else -1.0
        endpoint_station = 0.0 if endpoint == "start" else axis_len
        corner_offset = min(1.5 * 0.0254, axis_len / 2.0)
        station = endpoint_station + direction_sign * corner_offset
        pt = add(p0, scale(d, station))
        corner_top = top_at(station)
        members.append(FramedMember(rw.uid, f"corner-{endpoint}", "corner", member, pt, pt,
                                    stud_z0, corner_top, corner_top - stud_z0, orient=d))
        if spec.corner_style == "4-stud":
            corner_offset2 = min(2 * 1.5 * 0.0254, axis_len / 2.0)
            station2 = endpoint_station + direction_sign * corner_offset2
            pt2 = add(p0, scale(d, station2))
            corner_top2 = top_at(station2)
            members.append(FramedMember(rw.uid, f"corner-{endpoint}-2", "corner", member,
                                        pt2, pt2, stud_z0, corner_top2,
                                        corner_top2 - stud_z0, orient=d))

    if corner_start:
        append_corner("start")
    if corner_end:
        append_corner("end")

    for station, junction_key in tee_stations:
        _append_tee_backing(
            members, rw, spec, member, d, p0, axis_len, station, junction_key,
            stud_z0, top_at,
        )

    # --- opening framing (king/jack/header/cripple/sill) ----------------------
    for oi, (center, width, height, sill, is_door) in enumerate(openings):
        members.extend(
            _frame_opening(rw, d, p0, center, width, height, sill, is_door, member,
                           stud_z0, top_at, oi, spacing)
        )

    # --- in-line blocking courses (fire/backing blocking) ---------------------
    _append_blocking_rows(members, rw, spec, member, d, p0, stud_z0, spacing,
                          stud_stations)
    return tuple(members)


def _append_blocking_rows(members: list[FramedMember], rw: ResolvedWall, spec, member: str,
                          direction, wall_start, stud_bottom: float, spacing: float,
                          stud_stations: list[float]) -> None:
    """Emit a horizontal blocking course fitted between studs at each configured height.

    One block per stud bay, butting the flanking studs (the same-wall blocking/stud
    contact the interference check treats as intended nailing). Bays wider than ~1.5
    modules — an opening — are skipped so a block never spans an opening.
    """
    heights = getattr(spec, "blocking_heights", ()) or ()
    if not heights or len(stud_stations) < 2:
        return
    thickness = member_actual(member)[0] * 0.0254
    block_height = thickness  # a flat 2x course
    max_bay = spacing * 1.5
    stations = sorted(stud_stations)
    for hi, height in enumerate(heights):
        base = stud_bottom + height.meters
        for bi in range(len(stations) - 1):
            s0, s1 = stations[bi], stations[bi + 1]
            if s1 - s0 > max_bay or s1 - s0 <= thickness:
                continue  # opening bay, or studs too close to fit a block
            a = add(wall_start, scale(direction, s0 + thickness / 2))
            b = add(wall_start, scale(direction, s1 - thickness / 2))
            members.append(FramedMember(
                rw.uid, f"blocking-{hi}-{bi:03d}", "blocking", member, a, b,
                base, base + block_height, s1 - s0 - thickness,
            ))


def _append_tee_backing(members: list[FramedMember], rw: ResolvedWall, spec,
                        member: str, direction, wall_start, axis_len: float,
                        station: float, junction_key: str, stud_bottom: float,
                        top_at) -> None:
    """Emit the through-wall backing selected by ``FramingSpec`` at one T branch."""
    station = min(max(station, 0.0), axis_len)
    if spec.tee_backing_style == "none":
        return
    center = add(wall_start, scale(direction, station))
    if spec.tee_backing_style == "stud-pack":
        thickness_m = member_actual(member)[0] * 0.0254
        for index, offset in enumerate((-thickness_m, thickness_m)):
            stud_station = min(max(station + offset, 0.0), axis_len)
            point = add(wall_start, scale(direction, stud_station))
            stud_top = top_at(stud_station)
            members.append(FramedMember(
                rw.uid, f"tee-{junction_key}-stud-{index}", "corner", member,
                point, point, stud_bottom, stud_top, stud_top - stud_bottom,
                orient=direction,
            ))
        return

    depth_m = member_actual(member)[1] * 0.0254
    perpendicular = (-direction[1], direction[0])
    half_depth = depth_m / 2.0
    block_start = add(center, scale(perpendicular, -half_depth))
    block_end = add(center, scale(perpendicular, half_depth))
    block_height = member_actual(member)[0] * 0.0254
    spacing = (spec.tee_blocking_spacing or DEFAULT_TEE_BLOCKING_SPACING).meters
    top = top_at(station)
    elevation = stud_bottom + spacing
    index = 0
    while elevation + block_height < top - _EPSILON:
        members.append(FramedMember(
            rw.uid, f"tee-{junction_key}-block-{index:02d}", "blocking", member,
            block_start, block_end, elevation, elevation + block_height, depth_m,
        ))
        elevation += spacing
        index += 1


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


def _opening_exclusions(openings, thickness: float) -> list[tuple[float, float]]:
    """(center, half-width) bands to keep regular module studs clear of each opening.

    The band covers the rough opening *and* the full trimmer+king pack on each side, so a
    module stud never lands inside the pack (redundant load path, guaranteed clash).
    """
    from typehaus.quantities import m as _m

    zones: list[tuple[float, float]] = []
    for (center, width, _h, _sill, _door) in openings:
        kings, jacks = king_jack_counts(_m(width))
        zones.append((center, width / 2 + (kings + jacks) * thickness + 0.005))
    return zones


def _in_exclusion(s: float, zones: list[tuple[float, float]]) -> bool:
    return any(abs(s - center) <= half for center, half in zones)


def _studs_broken(center: float, half: float, spacing: float) -> int:
    """How many on-module stud lines an opening interrupts (0 => it fits inside a bay)."""
    import math

    lo = math.ceil((center - half) / spacing - 1e-9)
    hi = math.floor((center + half) / spacing + 1e-9)
    return max(0, hi - lo + 1)


def _frame_opening(rw, d, p0, center, width, height, sill, is_door, member,
                   z0, top_at, oi, spacing) -> list[FramedMember]:
    from typehaus.quantities import m as _m

    out: list[FramedMember] = []
    plate_h = 1.5 * 0.0254
    thickness = member_actual(member)[0] * 0.0254  # stud face dimension along the wall
    kings, jacks = king_jack_counts(_m(width))
    half = width / 2
    header_bottom = (z0 + sill + height) if not is_door else (z0 + height)
    header_depth = 0.14

    # A window narrower than the stud module that lands wholly inside one bay breaks no
    # stud line: the load path over it is uninterrupted, so it needs no structural header
    # (and no king/jack trimmers). It gets a flat rough sill + rough head nailer between
    # the intact bounding studs. Doors always reach the floor and break the run, so they
    # always frame fully.
    if not is_door and _studs_broken(center, half, spacing) == 0:
        sl = add(p0, scale(d, center - half))
        sr = add(p0, scale(d, center + half))
        sill_z0 = z0 + sill
        out.append(FramedMember(rw.uid, f"sill-{oi}", "sill", member, sl, sr,
                                sill_z0, sill_z0 + plate_h, width))
        out.append(FramedMember(rw.uid, f"roughhead-{oi}", "blocking", member, sl, sr,
                                header_bottom, header_bottom + plate_h, width))
        return out
    # Trimmers (jacks) and kings pack face-to-face outward from each rough-opening edge:
    # the innermost jack's inner face sits on the RO edge (centreline at half a thickness
    # in), each following member is one full thickness further out. Spacing members by
    # their real thickness makes the stud pack *touch* rather than interpenetrate — the
    # box IR then shows a face-nailed pack as adjacency, not a clash.
    for side, sign in (("l", -1), ("r", +1)):
        edge = center + sign * half
        for j in range(jacks):
            s = edge + sign * (thickness / 2 + j * thickness)
            pos = add(p0, scale(d, s))
            out.append(FramedMember(rw.uid, f"jack-{oi}-{side}{j}", "jack", member,
                                    pos, pos, z0, header_bottom, header_bottom - z0, orient=d))
        for k in range(kings):
            s = edge + sign * (thickness / 2 + (jacks + k) * thickness)
            pos = add(p0, scale(d, s))
            king_top = top_at(s)
            out.append(FramedMember(rw.uid, f"king-{oi}-{side}{k}", "king", member,
                                    pos, pos, z0, king_top, king_top - z0, orient=d))
    # The header bears on both trimmer stacks; its ends land on the king inner faces
    # (RO half-width + the full trimmer stack), so it butts the kings without crossing them.
    header_half = half + jacks * thickness
    hl = add(p0, scale(d, center - header_half))
    hr = add(p0, scale(d, center + header_half))
    out.append(FramedMember(rw.uid, f"header-{oi}", "header",
                            header_size(_m(width), rw is not None), hl, hr,
                            header_bottom, header_bottom + header_depth,
                            2 * header_half))

    if not is_door:
        sill_z0 = z0 + sill
        sill_z1 = sill_z0 + plate_h
        # The rough sill fits *between* the trimmers, spanning the rough opening only, so
        # its ends butt the jack inner faces instead of running through them.
        sl = add(p0, scale(d, center - half))
        sr = add(p0, scale(d, center + half))
        out.append(FramedMember(
            rw.uid, f"sill-{oi}", "sill", member, sl, sr, sill_z0, sill_z1, width,
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


def frame_model(plan: PlanModel, model: ResolvedModel) -> list[Finding]:
    """Attach members using the shared junction decisions; return configuration findings."""
    by_host: dict[str, list] = {}
    for op in model.openings:
        by_host.setdefault(op.host_wall, []).append(
            (op.center_along_m, op.width_m, op.height_m, op.sill_m, op.is_door)
        )
    corner_endpoints: dict[str, set[str]] = {}
    tee_points: dict[str, list[tuple[tuple[float, float], str]]] = {}
    findings: list[Finding] = []
    for junction in model.junctions:
        if junction.kind == "l" and junction.framing_owner:
            owner_incident = next((
                item for item in junction.incidents
                if item.wall_tag == junction.framing_owner
            ), None)
            if owner_incident is not None:
                corner_endpoints.setdefault(owner_incident.wall_tag, set()).add(
                    owner_incident.endpoint
                )
            corner_styles = {
                layer.framing.corner_style
                for item in junction.incidents
                if (layer := _structure_layer(plan, item.assembly)) is not None
                and layer.framing is not None
            }
            if len(corner_styles) > 1:
                findings.append(_framing_junction_finding(
                    junction, "incompatible corner_style values"
                ))
        elif junction.kind == "t" and junction.framing_owner:
            tee_points.setdefault(junction.framing_owner, []).append(
                (junction.point, junction.node_tag)
            )
            tee_styles = {
                layer.framing.tee_backing_style
                for item in junction.incidents
                if item.wall_tag in junction.through_walls
                and (layer := _structure_layer(plan, item.assembly)) is not None
                and layer.framing is not None
            }
            if len(tee_styles) > 1:
                findings.append(_framing_junction_finding(
                    junction, "incompatible tee_backing_style values"
                ))

    framed: list[ResolvedWall] = []
    for rw in model.walls:
        framing_start, framing_end = _framing_axis(rw)
        framing_direction = unit(sub(framing_end, framing_start))
        tee_stations = tuple(
            (
                sub(point, framing_start)[0] * framing_direction[0]
                + sub(point, framing_start)[1] * framing_direction[1],
                node_tag,
            )
            for point, node_tag in sorted(tee_points.get(rw.tag, []))
        )
        endpoints = corner_endpoints.get(rw.tag, set())
        members = frame_wall(plan, rw, by_host.get(rw.tag, []),
                             corner_start="start" in endpoints,
                             corner_end="end" in endpoints,
                             tee_stations=tee_stations)
        # ``replace`` rather than a field-by-field rebuild: this pass only adds members,
        # and respelling the constructor here silently drops any field added later.
        framed.append(replace(rw, members=members))
    model.walls = framed
    return findings


def _framing_junction_finding(junction, problem: str) -> Finding:
    return Finding(
        severity=Severity.WARN,
        check_id="structural.junction_framing_conflict",
        message=f"node {junction.node_tag}: {problem}",
        element_tags=tuple(item.wall_tag for item in junction.incidents),
        fix_hint="make incident FramingSpec junction settings agree",
        result=Result.UNKNOWN,
    )
