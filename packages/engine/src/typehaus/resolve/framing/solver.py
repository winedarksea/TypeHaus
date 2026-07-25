"""Wall framing solver (#20) — pure deterministic (polygons, spec) -> [FramedMember].

Members are lightweight records (no geometry kernel) until emit (risk 6). M1 handles
level wall tops only; the raked-top/rafter arm activates with M3 roofs (→ 30 WP3.11).
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.findings import Finding, Result, Severity
from typehaus.model.elements import Wall
from typehaus.model.enums import LayerFunction
from typehaus.model.plan import PlanModel
from typehaus.resolve.framing.backing import append_blocking_rows, append_tee_backing
from typehaus.resolve.framing.corners import (
    CORNER_ROLE_BUTTING,
    CORNER_ROLE_OWNER,
    corner_stud_stations,
    invert_corner_role,
    wall_end_framing,
)
from typehaus.resolve.framing.openings import (
    WallOpening,
    frame_opening,
    in_exclusion,
    opening_exclusions,
)
from typehaus.resolve.framing.tables import DEFAULT_SPACING, member_actual
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


def frame_wall(plan: PlanModel, rw: ResolvedWall, openings: list[WallOpening],
               corner_start: bool = False, corner_end: bool = False,
               butting_start: bool = False, butting_end: bool = False,
               tee_stations: tuple[tuple[float, str], ...] = (),
               corner_style_start: str | None = None,
               corner_style_end: str | None = None) \
        -> tuple[FramedMember, ...]:
    """Generate studs, plates, and opening framing for one resolved wall.

    ``corner_*`` marks an end where this wall *owns* the L corner (its framing runs through
    the shared corner square); ``butting_*`` marks an end where the neighbour owns it and
    this wall's framing stops at the neighbour's near face. See ``framing/corners.py``.

    ``corner_style_start``/``corner_style_end`` are the authored per-end overrides
    (``Wall.corner_style_start``/``corner_style_end``): ``"3-stud"``/``"4-stud"`` at the
    end that hosts the supplemental studs, ``None`` to follow the assembly's
    ``FramingSpec.corner_style``. Per-end because a corner belongs to two walls and the
    override lives on the owning end, so two walls never fight over one corner's style.
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
    thickness = member_actual(member)[0] * 0.0254  # stud face dimension along the wall
    z0 = rw.z0_m
    plate_h = 1.5 * 0.0254

    start_role = (CORNER_ROLE_OWNER if corner_start
                  else CORNER_ROLE_BUTTING if butting_start else None)
    end_role = (CORNER_ROLE_OWNER if corner_end
                else CORNER_ROLE_BUTTING if butting_end else None)
    structure_polygon = _structure_polygon(rw)
    start_end = wall_end_framing(structure_polygon, p0, d, axis_len, start_role,
                                 thickness, at_start=True)
    far_end = wall_end_framing(structure_polygon, p0, d, axis_len, end_role,
                               thickness, at_start=False)

    members: list[FramedMember] = []

    # --- plates ---------------------------------------------------------------
    top_start, top_end = _wall_top_elevations(rw)
    top_plates = 2 if spec.double_top_plate and not spec.advanced_framing else 1
    _append_plates(members, rw, member, p0, d, axis_len, z0, plate_h, top_plates,
                   top_start, top_end, structure_polygon, start_role, end_role, thickness)

    # --- studs at spacing, skipping those inside an opening's king/jack pack --
    stud_z0 = z0 + plate_h
    # A regular module stud that would fall inside an opening's trimmer/king pack is
    # redundant (the pack already carries the load there) and would only interpenetrate
    # it. Exclude the full pack width, not just the rough opening.
    stud_zones = opening_exclusions(openings, thickness, spacing)

    def top_at(s: float) -> float:
        """Framing top (below the top plate(s)) at station ``s`` along the wall axis.

        Interpolates between the wall's raked endpoints so every vertical member —
        regular stud, corner stud, or king stud in an opening — gets the top that
        matches the roof plane at its own plan position, not some other member's.
        """
        fraction = s / axis_len if axis_len else 0.0
        return top_start + (top_end - top_start) * fraction - plate_h * top_plates

    # A supplemental stud at each owned corner: with the neighbour's end stud butting the
    # far side of the corner square, this is the third stud of the 3-stud pack. Placed
    # before the module studs because the pack it forms is what they have to clear.
    corner_stations = {
        endpoint: (corner_stud_stations(end, at_start, thickness,
                                        style or spec.corner_style, axis_len)
                   if (corner_start if at_start else corner_end) else ())
        for endpoint, at_start, end, style in (
            ("start", True, start_end, corner_style_start),
            ("end", False, far_end, corner_style_end))
    }
    for endpoint, stations in corner_stations.items():
        for index, station in enumerate(stations):
            suffix = "" if index == 0 else f"-{index + 1}"
            point = add(p0, scale(d, station))
            corner_top = top_at(station)
            members.append(FramedMember(rw.uid, f"corner-{endpoint}{suffix}", "corner",
                                        member, point, point, stud_z0, corner_top,
                                        corner_top - stud_z0, orient=d))

    # Standard framing practice puts a stud at both ends of every wall; the module loop
    # only reaches the far end when axis_len is an exact multiple of the module, and at a
    # corner neither end stud sits on the module at all (it sits where the corner square
    # lets it). Both end studs are therefore explicit, and module stations that would land
    # inside the end/corner pack are dropped rather than allowed to interpenetrate it.
    stud_stations = sorted(
        station for station in _module_stations(
            axis_len, spacing, thickness,
            (start_end.end_stud_station_m, far_end.end_stud_station_m),
            (max((start_end.end_stud_station_m, *corner_stations["start"])),
             min((far_end.end_stud_station_m, *corner_stations["end"]))))
        if not in_exclusion(station, stud_zones)
    )
    for index, station in enumerate(stud_stations):
        point = add(p0, scale(d, station))
        stud_top = top_at(station)
        members.append(FramedMember(rw.uid, f"stud-{index:03d}", "stud", member,
                                    point, point, stud_z0, stud_top, stud_top - stud_z0,
                                    orient=d))

    for station, junction_key in tee_stations:
        append_tee_backing(
            members, rw, spec, member, d, p0, axis_len, station, junction_key,
            stud_z0, top_at,
        )

    # --- opening framing (king/jack/header/cripple/sill) ----------------------
    for opening_index, opening in enumerate(openings):
        members.extend(
            frame_opening(rw, d, p0, opening, member, stud_z0, top_at,
                          opening_index, spacing, tuple(stud_stations))
        )

    # --- in-line blocking courses (fire/backing blocking) ---------------------
    append_blocking_rows(members, rw, spec, member, d, p0, stud_z0, spacing,
                         stud_stations)
    return tuple(members)


def _module_stations(axis_len: float, spacing: float, thickness: float,
                     end_studs: tuple[float, float],
                     pack_limits: tuple[float, float]) -> list[float]:
    """Both end-stud stations plus every module station that clears the end packs.

    A module station closer than one stud thickness to an end stud (or to the corner studs
    packed against it) *is* that member: two there would interpenetrate rather than double,
    which is why the module loop cannot simply run from 0 once the corner rule places the
    ends. ``pack_limits`` is the innermost occupied station at each end.
    """
    start_station, end_station = end_studs
    start_limit, end_limit = pack_limits
    stations = [start_station]
    if end_station - start_station > thickness - 1e-9:
        stations.append(end_station)
    for index in range(int(axis_len // spacing) + 1):
        station = index * spacing
        if station > axis_len + 1e-6:
            break
        if (station - start_limit < thickness - 1e-9
                or end_limit - station < thickness - 1e-9):
            continue
        stations.append(station)
    return stations


def _append_plates(members: list[FramedMember], rw: ResolvedWall, member: str, p0, d,
                   axis_len: float, z0: float, plate_h: float, top_plates: int,
                   top_start: float, top_end: float, structure_polygon,
                   start_role: str | None, end_role: str | None,
                   thickness: float) -> None:
    """Bottom + top plate course(s), each cut to the corner square that course owns.

    The cap plate of a double top plate laps the *opposite* way from the courses below it:
    at a corner the wall that runs through at the bottom stops short at the cap, and the
    neighbour's cap runs over it. That reversal is the tie between the two walls, and
    modelling it is what stops two plates from doubling in the same corner square.
    """
    def plate_run(course_start_role: str | None, course_end_role: str | None):
        start = wall_end_framing(structure_polygon, p0, d, axis_len, course_start_role,
                                 thickness, at_start=True).plate_station_m
        end = wall_end_framing(structure_polygon, p0, d, axis_len, course_end_role,
                               thickness, at_start=False).plate_station_m
        return start, end

    def point_at(station: float):
        return add(p0, scale(d, station))

    def top_at_station(station: float) -> float:
        fraction = station / axis_len if axis_len else 0.0
        return top_start + (top_end - top_start) * fraction

    start_station, end_station = plate_run(start_role, end_role)
    members.append(_plate(rw, point_at(start_station), point_at(end_station),
                          "plate-bottom", z0, z0 + plate_h, member))
    for i in range(top_plates):
        laps_back = top_plates > 1 and i == top_plates - 1
        roles = ((invert_corner_role(start_role), invert_corner_role(end_role))
                 if laps_back else (start_role, end_role))
        course_start, course_end = plate_run(*roles)
        start_bottom = top_at_station(course_start) - plate_h * (i + 1)
        end_bottom = top_at_station(course_end) - plate_h * (i + 1)
        a, b = point_at(course_start), point_at(course_end)
        if abs(start_bottom - end_bottom) < 1e-9:
            members.append(_plate(rw, a, b, f"plate-top-{i}", start_bottom,
                                  start_bottom + plate_h, member))
        else:
            members.append(FramedMember(
                rw.uid, f"plate-raked-{i}", "raked_plate", member, a, b,
                start_bottom, start_bottom + plate_h, length(sub(b, a)),
                z0_end_m=end_bottom, z1_end_m=end_bottom + plate_h,
            ))


def _structure_polygon(rw: ResolvedWall):
    """The resolved structure-layer plan polygon — mitred at every resolved junction."""
    structure = next((layer for layer in rw.layers if layer.function == "structure"), None)
    return structure.polygon if structure is not None and structure.polygon else ()


def _framing_axis(rw: ResolvedWall) -> tuple[tuple[float, float], tuple[float, float]]:
    """Translate the wall datum axis to the resolved structure-layer centerline.

    The wall axis may intentionally name an exterior sheathing face.  Framing keeps
    its authored direction and along-wall opening distances, but must sit inside the
    structure layer represented by the resolved polygon.
    """
    polygon = _structure_polygon(rw)
    if not polygon:
        return rw.axis
    raw_start, raw_end = rw.axis
    perpendicular = normal(unit(sub(raw_end, raw_start)))
    if perpendicular == (0.0, 0.0):
        return rw.axis
    offsets = [
        (point[0] - raw_start[0]) * perpendicular[0]
        + (point[1] - raw_start[1]) * perpendicular[1]
        for point in polygon
    ]
    # Mid-band, not the vertex average: a resolved polygon is mitred at its corners and may
    # carry a jog, so its vertices are not evenly distributed across the band. Averaging
    # them pulls the framing centreline off centre — by 0.7" on the catlin sauna walls,
    # enough to push their corner studs into the neighbouring wall's band.
    translation = scale(perpendicular, (min(offsets) + max(offsets)) / 2.0)
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


def frame_model(plan: PlanModel, model: ResolvedModel) -> list[Finding]:
    """Attach members using the shared junction decisions; return configuration findings."""
    # The framing pattern is a property of the *product type*, not of the resolved
    # opening, so it is looked up once here rather than per wall.
    door_operations = {door_type.tag: door_type.operation
                       for door_type in plan.library.door_types}
    by_host: dict[str, list[WallOpening]] = {}
    for op in model.openings:
        by_host.setdefault(op.host_wall, []).append(WallOpening(
            center_m=op.center_along_m, width_m=op.width_m, height_m=op.height_m,
            sill_m=op.sill_m, is_door=op.is_door,
            operation=door_operations.get(op.type_ref) if op.is_door else None,
        ))
    corner_endpoints: dict[str, set[str]] = {}
    butting_endpoints: dict[str, set[str]] = {}
    tee_points: dict[str, list[tuple[tuple[float, float], str]]] = {}
    findings: list[Finding] = []
    for junction in model.junctions:
        if junction.kind == "l" and junction.framing_owner:
            # Both walls at the corner are recorded: the owner runs its framing through the
            # shared corner square, and the other has to know to stop at the owner's near
            # face instead of pinwheeling its end stud through the owner's.
            for item in junction.incidents:
                owned = item.wall_tag == junction.framing_owner
                target = corner_endpoints if owned else butting_endpoints
                target.setdefault(item.wall_tag, set()).add(item.endpoint)
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
        elif junction.kind in ("t", "x") and junction.framing_owner:
            # A branch dies into the through wall: its framing stops at the through wall's
            # face, exactly like the butting side of an L. Without this the branch's end
            # stud sits on the through wall's centreline, inside its studs.
            for item in junction.incidents:
                if item.wall_tag not in junction.through_walls:
                    butting_endpoints.setdefault(item.wall_tag, set()).add(item.endpoint)
            if junction.kind != "t":
                continue
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
    authored_walls = {element.tag: element for element in plan.all_elements()
                      if isinstance(element, Wall)}
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
        butting = butting_endpoints.get(rw.tag, set())
        # The authored per-end corner-style overrides (Wall.corner_style_start/end).
        # ``ResolvedWall`` does not carry them, so read them off the authored element.
        authored = authored_walls.get(rw.tag)
        members = frame_wall(plan, rw, by_host.get(rw.tag, []),
                             corner_start="start" in endpoints,
                             corner_end="end" in endpoints,
                             butting_start="start" in butting,
                             butting_end="end" in butting,
                             tee_stations=tee_stations,
                             corner_style_start=getattr(authored, "corner_style_start",
                                                        None),
                             corner_style_end=getattr(authored, "corner_style_end", None))
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
