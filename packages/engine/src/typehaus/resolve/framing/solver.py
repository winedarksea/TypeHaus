"""Wall framing solver (#20) — pure deterministic (polygons, spec) -> [FramedMember].

Members are lightweight records (no geometry kernel) until emit (risk 6). M1 handles
level wall tops only; the raked-top/rafter arm activates with M3 roofs (→ 30 WP3.11).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from typehaus.findings import Finding, Result, Severity
from typehaus.model.elements import Door, Wall
from typehaus.model.enums import LayerFunction, PartitionLayout
from typehaus.model.plan import PlanModel
from typehaus.resolve.framing.backing import append_blocking_rows, append_tee_backing
from typehaus.resolve.framing.corners import (
    CORNER_ROLE_BUTTING,
    CORNER_ROLE_OWNER,
    corner_stud_stations,
    invert_corner_role,
    neighbour_band_insets,
    wall_end_framing,
)
from typehaus.resolve.framing.openings import (
    WallOpening,
    frame_opening,
    in_exclusion,
    opening_exclusions,
)
from typehaus.resolve.framing.pockets import pocket_keepouts
from typehaus.resolve.framing.tables import DEFAULT_SPACING, member_actual
from typehaus.resolve.geometry import add, length, normal, scale, sub, unit
from typehaus.resolve.layout_lines import layout_phase, lines_by_wall
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedWall


def structure_layer(plan: PlanModel, assembly_tag: str):
    """The assembly's STRUCTURE layer, or ``None`` if it has none."""
    asm = plan.library.resolve_assembly(assembly_tag)
    if asm is None:
        return None
    for layer in asm.layers:
        if layer.function is LayerFunction.STRUCTURE:
            return layer
    return None


def frames_as_members(layer) -> bool:
    """Does this STRUCTURE layer become sticks of lumber, or is it a monolithic pour/course?

    The one place the framed/monolithic split is decided. ``frame_wall`` returns no members
    when this is false, and ``takeoff/wall_structure.py`` bills exactly that complement by
    area and volume — so the predicate lives here, once, rather than being re-derived by
    each consumer and drifting.

    All three arms matter: a masonry course is arithmetic, not members (#23), and a
    structure layer with no ``FramingSpec`` (a pour) has nothing to lay out.
    """
    return layer is not None and layer.masonry is None and layer.framing is not None


def frame_wall(plan: PlanModel, rw: ResolvedWall, openings: list[WallOpening],
               corner_start: bool = False, corner_end: bool = False,
               butting_start: bool = False, butting_end: bool = False,
               tee_stations: tuple[tuple[float, str], ...] = (),
               corner_style_start: str | None = None,
               corner_style_end: str | None = None,
               neighbour_insets_start: tuple[float, float] | None = None,
               neighbour_insets_end: tuple[float, float] | None = None,
               stud_keepouts: tuple[tuple[float, float], ...] = (),
               continuation_start: str | None = None,
               continuation_end: str | None = None,
               line: object | None = None) \
        -> tuple[FramedMember, ...]:
    """Generate studs, plates, and opening framing for one resolved wall.

    ``corner_*`` marks an end where this wall *owns* the L corner (its framing runs through
    the shared corner square); ``butting_*`` marks an end where the neighbour owns it and
    this wall's framing stops at the neighbour's near face. See ``framing/corners.py``.

    ``stud_keepouts`` are extra (centre, half-width) bands to keep module studs out of,
    on top of this wall's own openings' packs. They exist for one case: a pocket door on a
    *colinear neighbour* whose cavity runs across the shared node into this wall. Wall
    segmentation at a tee is an authoring convention — the two walls are one plane, one
    assembly and one set of plates — so the leaf really does travel through here, and a
    module stud in its path is a door that will not open. See ``_pocket_keepouts``.

    ``continuation_start``/``continuation_end`` mark an end where this wall simply *carries
    on* into a collinear neighbour that shares its grid — the two halves of one real wall,
    split at a tee because the rooms behind them are two rooms. ``"owner"`` on one side and
    ``"follower"`` on the other; ``None`` (the default) is an end that really ends. See
    ``_continuation_roles``.

    ``corner_style_start``/``corner_style_end`` are the authored per-end overrides
    (``Wall.corner_style_start``/``corner_style_end``): ``"3-stud"``/``"4-stud"`` at the
    end that hosts the supplemental studs, ``None`` to follow the assembly's
    ``FramingSpec.corner_style``. Per-end because a corner belongs to two walls and the
    override lives on the owning end, so two walls never fight over one corner's style.
    """
    layer = structure_layer(plan, rw.assembly)
    if not frames_as_members(layer):
        # Masonry and monolithic walls take the arithmetic-takeoff path, no members (#23);
        # `takeoff/wall_structure.py` bills them by area and cubic yards.
        return ()
    spec = layer.framing
    assert spec is not None  # frames_as_members

    p0, p1 = _framing_axis(rw)
    axis_len = length(sub(p1, p0))
    d = unit(sub(p1, p0))
    spacing = (spec.spacing or DEFAULT_SPACING).meters
    member = spec.member
    # STAGGERED layout (#50 acoustic partitions): narrow studs alternate between the two
    # faces of a wider plate (2x4s on 2x6 plates), 16" o.c. per face — 8" combined rhythm —
    # leaving a continuous cavity. Plates, end/corner studs, tee backing, and opening
    # packs stay full plate depth so drywall backing and load paths are conventional; only
    # the module studs stagger.
    staggered = spec.layout is PartitionLayout.STAGGERED
    plate_member = spec.plate_member or member
    frame_member = plate_member if staggered else member
    thickness = member_actual(member)[0] * 0.0254  # stud face dimension along the wall
    stagger_offset = 0.0
    if staggered:
        plate_depth = member_actual(plate_member)[1] * 0.0254
        stud_depth = member_actual(member)[1] * 0.0254
        stagger_offset = max((plate_depth - stud_depth) / 2.0, 0.0)
    # The framing base, which a wall extended down over the rim does NOT move: the
    # bottom plate, the studs and every opening sill stay on the storey datum while
    # only the wall's skin laps the foundation below (→ ``ResolvedWall.plate_base_z_m``).
    z0 = rw.base_ref_z_m
    plate_h = 1.5 * 0.0254

    start_role = (CORNER_ROLE_OWNER if corner_start
                  else CORNER_ROLE_BUTTING if butting_start else None)
    end_role = (CORNER_ROLE_OWNER if corner_end
                else CORNER_ROLE_BUTTING if butting_end else None)
    structure_polygon = _structure_polygon(rw)
    start_end = wall_end_framing(structure_polygon, p0, d, axis_len, start_role,
                                 thickness, at_start=True,
                                 neighbour_insets=neighbour_insets_start)
    far_end = wall_end_framing(structure_polygon, p0, d, axis_len, end_role,
                               thickness, at_start=False,
                               neighbour_insets=neighbour_insets_end)

    members: list[FramedMember] = []

    # --- plates ---------------------------------------------------------------
    top_start, top_end = _wall_top_elevations(rw)
    top_plates = 2 if spec.double_top_plate and not spec.advanced_framing else 1
    _append_plates(members, rw, plate_member, p0, d, axis_len, z0, plate_h, top_plates,
                   top_start, top_end, structure_polygon, start_role, end_role, thickness,
                   neighbour_insets_start, neighbour_insets_end)

    # --- studs at spacing, skipping those inside an opening's king/jack pack --
    stud_z0 = z0 + plate_h
    # A regular module stud that would fall inside an opening's trimmer/king pack is
    # redundant (the pack already carries the load there) and would only interpenetrate
    # it. Exclude the full pack width, not just the rough opening. Staggered walls place
    # module studs on the combined half-spacing rhythm, so the jamb-pack verdict (and
    # every other consumer of the module) must see that same rhythm.
    module_spacing = spacing / 2.0 if staggered else spacing
    module_phase = layout_phase(spec, line, rw.tag, module_spacing)
    stud_zones = opening_exclusions(openings, thickness, module_spacing, module_phase)
    stud_zones.extend(stud_keepouts)

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
                                        frame_member, point, point, stud_z0, corner_top,
                                        corner_top - stud_z0, orient=d))

    # Standard framing practice puts a stud at both ends of every wall; the module loop
    # only reaches the far end when axis_len is an exact multiple of the module, and at a
    # corner neither end stud sits on the module at all (it sits where the corner square
    # lets it). Both end studs are therefore explicit, and module stations that would land
    # inside the end/corner pack are dropped rather than allowed to interpenetrate it.
    #
    # Except where the end is not an end: at a continuation the wall runs on into a collinear
    # neighbour on the same grid, so the module carries through and neither half plants a
    # stud at the seam.
    stud_stations = sorted(
        station for station in _module_stations(
            axis_len, module_spacing, thickness,
            (start_end.end_stud_station_m, far_end.end_stud_station_m),
            (max((start_end.end_stud_station_m, *corner_stations["start"])),
             min((far_end.end_stud_station_m, *corner_stations["end"]))),
            phase=module_phase,
            continuations=(continuation_start, continuation_end))
        if not in_exclusion(station, stud_zones)
    )
    perpendicular = normal(d)
    end_stations = {start_end.end_stud_station_m, far_end.end_stud_station_m}
    for index, station in enumerate(stud_stations):
        point = add(p0, scale(d, station))
        stud_top = top_at(station)
        profile = member
        if staggered:
            if station in end_stations:
                # End studs stay full plate depth on the centerline — both faces of
                # drywall need backing where the wall meets its neighbours.
                profile = frame_member
            else:
                # Face parity from the station itself (not the loop index) so a dropped
                # station under an opening never flips the rest of the wall's rhythm.
                side = 1.0 if round(station / module_spacing) % 2 == 0 else -1.0
                point = add(point, scale(perpendicular, side * stagger_offset))
        members.append(FramedMember(rw.uid, f"stud-{index:03d}", "stud", profile,
                                    point, point, stud_z0, stud_top, stud_top - stud_z0,
                                    orient=d))

    # --- opening framing (king/jack/header/cripple/sill) ----------------------
    # Staggered walls frame their openings full plate depth: a king/jack pack split
    # across two faces has no continuous bearing surface for the header.
    opening_framing_members: list[FramedMember] = []
    for opening_index, opening in enumerate(openings):
        opening_framing_members.extend(
            frame_opening(rw, d, p0, opening, frame_member, stud_z0, top_at,
                          opening_index, module_spacing, tuple(stud_stations),
                          module_phase)
        )

    # Opening framing is computed first because it is structural and takes precedence over
    # finish-backing ladder rungs. Keep the historical member order by appending the backing
    # before the already-computed opening members.
    opening_framing = tuple(opening_framing_members)
    for station, junction_key in tee_stations:
        append_tee_backing(
            members, rw, spec, frame_member, d, p0, axis_len, station, junction_key,
            stud_z0, top_at, opening_framing,
        )
    members.extend(opening_framing)

    # --- in-line blocking courses (fire/backing blocking) ---------------------
    append_blocking_rows(members, rw, spec, member, d, p0, stud_z0, module_spacing,
                         stud_stations)
    return tuple(members)


def _module_stations(axis_len: float, spacing: float, thickness: float,
                     end_studs: tuple[float, float],
                     pack_limits: tuple[float, float],
                     phase: float = 0.0,
                     continuations: tuple[str | None, str | None] = (None, None)
                     ) -> list[float]:
    """Both end-stud stations plus every module station that clears the end packs.

    A module station closer than one stud thickness to an end stud (or to the corner studs
    packed against it) *is* that member: two there would interpenetrate rather than double,
    which is why the module loop cannot simply run from 0 once the corner rule places the
    ends. ``pack_limits`` is the innermost occupied station at each end.

    ``phase`` shifts the module's first station off the wall's own station 0, and is how a
    wall lays out from its *layout line* instead of from itself (``FramingSpec
    .layout_origin``). 0.0 — the default and every wall before the field existed — is the
    old behaviour exactly. End studs, corner packs and opening king/jack packs are not
    phased: they are already deliberately off-module, sitting where the corner square and
    the rough opening put them.

    ``continuations`` (``frame_wall``'s ``continuation_*``) marks an end that is not an end:
    the wall runs on into a collinear neighbour on the same grid. Three things follow, and
    all three are needed — the first cut of this had only the first two and left a 32" bay on
    the north wall, where the seam fell 1" off a grid station and *both* halves declined it.
      * no end stud there, because the module carries through instead;
      * no pack limit either — the limit exists to keep a module stud out of an end stud or
        corner pack, and at a continuation there is neither, so a station 1" from the seam is
        perfectly placed rather than a collision;
      * exactly one station is genuinely contested — the seam itself, when the seam happens
        to land *on* the grid. Both halves hold it as an endpoint, so the ``"follower"``
        yields it and the ``"owner"`` frames it, and it carries one stud rather than two in
        the same place.

    The fallback at the bottom is what makes dropping end studs safe: a jog short enough to
    hold no module station at all still gets its ends, so no wall is left with nothing
    standing in it.
    """
    start_station, end_station = end_studs
    start_limit, end_limit = pack_limits
    start_cont, end_cont = continuations
    stations = [] if start_cont else [start_station]
    if not end_cont and (start_cont or end_station - start_station > thickness - 1e-9):
        stations.append(end_station)
    for index in range(int(max(0.0, axis_len - phase) // spacing) + 1):
        station = phase + index * spacing
        if station > axis_len + 1e-6:
            break
        if start_cont is None and station - start_limit < thickness - 1e-9:
            continue
        if end_cont is None and end_limit - station < thickness - 1e-9:
            continue
        if start_cont == "follower" and abs(station) < 1e-6:
            continue
        if end_cont == "follower" and abs(station - axis_len) < 1e-6:
            continue
        stations.append(station)
    if not stations:
        stations = [start_station]
        if end_station - start_station > thickness - 1e-9:
            stations.append(end_station)
    return stations


def _append_plates(members: list[FramedMember], rw: ResolvedWall, member: str, p0, d,
                   axis_len: float, z0: float, plate_h: float, top_plates: int,
                   top_start: float, top_end: float, structure_polygon,
                   start_role: str | None, end_role: str | None,
                   thickness: float,
                   neighbour_insets_start: tuple[float, float] | None = None,
                   neighbour_insets_end: tuple[float, float] | None = None) -> None:
    """Bottom + top plate course(s), each cut to the corner square that course owns.

    The cap plate of a double top plate laps the *opposite* way from the courses below it:
    at a corner the wall that runs through at the bottom stops short at the cap, and the
    neighbour's cap runs over it. That reversal is the tie between the two walls, and
    modelling it is what stops two plates from doubling in the same corner square.
    """
    def plate_run(course_start_role: str | None, course_end_role: str | None):
        start = wall_end_framing(structure_polygon, p0, d, axis_len, course_start_role,
                                 thickness, at_start=True,
                                 neighbour_insets=neighbour_insets_start).plate_station_m
        end = wall_end_framing(structure_polygon, p0, d, axis_len, course_end_role,
                               thickness, at_start=False,
                               neighbour_insets=neighbour_insets_end).plate_station_m
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
    return band_axis(rw.axis, _structure_polygon(rw))


def band_axis(axis: tuple[tuple[float, float], tuple[float, float]],
              polygon) -> tuple[tuple[float, float], tuple[float, float]]:
    """``axis`` translated sideways onto the centreline of the band ``polygon`` occupies.

    Shared with ``framing/furring.py``, which lays strapping in a FURRING layer's band
    rather than the structure layer's: same arithmetic, different polygon, and a copy of
    it would be a copy of the mid-band subtlety below.
    """
    if not polygon:
        return axis
    raw_start, raw_end = axis
    perpendicular = normal(unit(sub(raw_end, raw_start)))
    if perpendicular == (0.0, 0.0):
        return axis
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
    # Engineered-header overrides: the Door instance's header_spec wins, then its
    # DoorType's. Neither survives onto ResolvedOpening, so both are read off the plan.
    type_header_specs = {door_type.tag: door_type.header_spec
                         for door_type in plan.library.door_types}
    door_header_specs = {element.tag: element.header_spec
                         for element in plan.all_elements()
                         if isinstance(element, Door)}
    # A wall's layout line, so ``FramingSpec.layout_origin="line"`` can phase its module.
    lines_for_wall = lines_by_wall(model.layout_lines)
    by_host: dict[str, list[WallOpening]] = {}
    for op in model.openings:
        by_host.setdefault(op.host_wall, []).append(WallOpening(
            center_m=op.center_along_m, width_m=op.width_m, height_m=op.height_m,
            sill_m=op.sill_m, is_door=op.is_door,
            operation=door_operations.get(op.type_ref) if op.is_door else None,
            header_spec=(door_header_specs.get(op.tag)
                         or type_header_specs.get(op.type_ref))
            if op.is_door else None,
            pocket_run_m=op.pocket_run_m,
            pocket_sign=op.pocket_sign,
        ))
    keepouts = pocket_keepouts(plan, model)
    corner_endpoints: dict[str, set[str]] = {}
    butting_endpoints: dict[str, set[str]] = {}
    # (wall tag, endpoint) -> the tag of the other wall in that L corner, so the framing
    # rule can read the neighbour's own band instead of inferring it from the mitre.
    corner_neighbours: dict[tuple[str, str], str] = {}
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
                other = next(o for o in junction.incidents if o is not item)
                corner_neighbours[(item.wall_tag, item.endpoint)] = other.wall_tag
            corner_styles = {
                layer.framing.corner_style
                for item in junction.incidents
                if (layer := structure_layer(plan, item.assembly)) is not None
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
                and (layer := structure_layer(plan, item.assembly)) is not None
                and layer.framing is not None
            }
            if len(tee_styles) > 1:
                findings.append(_framing_junction_finding(
                    junction, "incompatible tee_backing_style values"
                ))

    framed: list[ResolvedWall] = []
    authored_walls = {element.tag: element for element in plan.all_elements()
                      if isinstance(element, Wall)}
    resolved_by_tag = {wall.tag: wall for wall in model.walls}
    continuations = continuation_roles(model, lambda tag: _structure_module_signature(
        plan, resolved_by_tag.get(tag), lines_for_wall.get(tag)))

    def _neighbour_insets(rw: ResolvedWall, endpoint: str, p0, direction,
                          axis_len: float) -> tuple[float, float] | None:
        """The corner neighbour's band, projected onto ``rw``'s framing axis.

        Only for a square corner: the projection of a whole wall polygon is its band width
        only while the neighbour runs perpendicular, and a skew L keeps the mitre reading.
        """
        neighbour = resolved_by_tag.get(corner_neighbours.get((rw.tag, endpoint), ""))
        if neighbour is None:
            return None
        n0, n1 = _framing_axis(neighbour)
        n_direction = unit(sub(n1, n0))
        if abs(n_direction[0] * direction[0] + n_direction[1] * direction[1]) > 1e-3:
            return None
        polygon = _structure_polygon(neighbour)
        return neighbour_band_insets(polygon, p0, direction, axis_len,
                                     at_start=endpoint == "start")

    for rw in model.walls:
        framing_start, framing_end = _framing_axis(rw)
        framing_direction = unit(sub(framing_end, framing_start))
        framing_len = length(sub(framing_end, framing_start))
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
                             corner_style_end=getattr(authored, "corner_style_end", None),
                             neighbour_insets_start=_neighbour_insets(
                                 rw, "start", framing_start, framing_direction,
                                 framing_len),
                             neighbour_insets_end=_neighbour_insets(
                                 rw, "end", framing_start, framing_direction,
                                 framing_len),
                             stud_keepouts=tuple(keepouts.get(rw.tag, ())),
                             continuation_start=continuations.get((rw.tag, "start")),
                             continuation_end=continuations.get((rw.tag, "end")),
                             line=lines_for_wall.get(rw.tag))
        # ``replace`` rather than a field-by-field rebuild: this pass only adds members,
        # and respelling the constructor here silently drops any field added later.
        framed.append(replace(rw, members=members))
    model.walls = framed
    return findings


def _structure_module_signature(plan: PlanModel, rw: ResolvedWall | None,
                               line: object | None) -> tuple[Any, ...] | None:
    """What has to match for two walls' *stud* modules to be provably one grid."""
    if rw is None or line is None:
        return None
    layer = structure_layer(plan, rw.assembly)
    if not frames_as_members(layer):
        return None
    spec = layer.framing
    if getattr(spec, "layout_origin", "wall-start") != "line":
        return None
    return (getattr(line, "tag", None), (spec.spacing or DEFAULT_SPACING).meters,
            spec.layout, spec.member, spec.plate_member)


def continuation_roles(model: ResolvedModel,
                       signature: Callable[[str], tuple[Any, ...] | None],
                       ) -> dict[tuple[str, str], str]:
    """Wall ends that are not ends: (wall, endpoint) -> ``"owner"`` | ``"follower"``.

    A facade is authored as a chain of wall segments because the *rooms* behind it are a
    chain of rooms — the exterior wall is split wherever a partition tees in. Each half then
    framed its own end stud at that node, so the seam carried two studs in the same 1.5" of
    wall, off the module, at a station the storey above split somewhere else entirely. That
    is what stopped studs stacking up a facade even after #43 phase-locked the module itself
    to the layout line: the module lined up, and the seam studs it ran between did not.

    Where the two halves provably lay out on **one grid** — same layout line, both taking
    their origin from it, same member and same module — the seam is a modelling artifact and
    the module simply runs through it. Elsewhere (two different lines, a wall laying out from
    its own start, a change of stud size) the modules are genuinely independent and dropping
    the seam stud would leave a hole, so the historical end studs stay.

    The ``"owner"``/``"follower"`` split settles the one station the two halves share: a seam
    that happens to land *on* the grid is claimed by the owner, so it carries one stud rather
    than two stacked in the same place or — worse — none at all.

    The branch wall at a tee is untouched: it still butts, and its backing is
    ``append_tee_backing``'s job either way.

    ``signature`` is what "one grid" means for the caller's layer — ``wall_tag`` in, an
    opaque comparable out, or ``None`` for "this wall has no such grid". The stud module and
    a furring band ask the same question of the same junctions about different layers, so the
    junction reading lives here once and the layer reading stays with each caller.
    """
    roles: dict[tuple[str, str], str] = {}
    for junction in model.junctions:
        if junction.kind not in ("collinear", "t", "x"):
            continue
        through = [item for item in junction.incidents
                   if item.wall_tag in junction.through_walls]
        if len(through) != 2:
            continue
        first, second = (signature(item.wall_tag) for item in through)
        if first is None or first != second:
            continue
        tags = {item.wall_tag for item in through}
        # ``framing_owner`` is a through wall at every junction kind reaching here, but it is
        # not part of that contract; falling back on the sorted tag keeps the choice
        # deterministic rather than letting both halves think they are the follower.
        owner = junction.framing_owner if junction.framing_owner in tags else min(tags)
        for item in through:
            roles[(item.wall_tag, item.endpoint)] = (
                "owner" if item.wall_tag == owner else "follower")
    return roles


def _framing_junction_finding(junction, problem: str) -> Finding:
    return Finding(
        severity=Severity.WARN,
        check_id="structural.junction_framing_conflict",
        message=f"node {junction.node_tag}: {problem}",
        element_tags=tuple(item.wall_tag for item in junction.incidents),
        fix_hint="make incident FramingSpec junction settings agree",
        result=Result.UNKNOWN,
    )
