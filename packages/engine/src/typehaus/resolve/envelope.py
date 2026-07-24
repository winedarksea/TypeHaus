"""Resolve slabs, foundations, footings, and constrained roofs into shared geometry."""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.findings import Finding, Result, Severity
from typehaus.model.floors import FloorOpening, FloorSystem, Slab
from typehaus.model.spatial import Roof, Stair
from typehaus.model.refs import ToRoof
from typehaus.model.enums import ConditionKind
from typehaus.model.structure import Beam, Footing, FootingBedding, Pad, Post
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import polygon_area, rect_between
from typehaus.resolve.model import (
    BoundaryCondition,
    FramedMember,
    ResolvedFootingBedding,
    ResolvedModel,
    ResolvedRoof,
    ResolvedSolid,
    ResolvedStair,
)

_MAX_RISER_M = 7.75 * 0.0254  # IRC R311.7
_MIN_TREAD_M = 10.0 * 0.0254


def resolve_envelope_geometry(model: ResolvedModel) -> list[Finding]:
    """Populate derived non-wall envelope geometry and return precise bad-ref findings."""
    findings: list[Finding] = []
    plan = model.plan
    for wall in model.walls:
        if wall.z1_m <= wall.z0_m:
            findings.append(_error("integrity.wall_elevation", f"wall {wall.tag} has a "
                                   "non-positive resolved height", wall.tag))
    for storey in plan.storeys:
        elevation = storey.elevation.meters
        for element in plan.storey_elements(storey.tag):
            if isinstance(element, Slab):
                outline = [point.xy_m for point in element.outline]
                if len(outline) < 3:
                    findings.append(_error("integrity.slab_outline",
                                           f"slab {element.tag} needs a closed outline",
                                           element.tag))
                    continue
                model.solids.append(ResolvedSolid(
                    element.uid, element.tag, storey.tag, "slab", outline,
                    elevation - element.thickness.meters, elevation, element.assembly,
                    tuple(tuple(point.xy_m for point in model.plan.by_tag(tag).outline)
                          for tag in element.openings
                          if isinstance(model.plan.by_tag(tag), FloorOpening)),
                ))
            elif isinstance(element, Pad):
                outline = [point.xy_m for point in element.outline]
                if len(outline) < 3:
                    findings.append(_error("integrity.pad_outline",
                                           f"pad {element.tag} needs a closed outline",
                                           element.tag))
                    continue
                bottom = (element.bottom_elevation.meters if element.bottom_elevation is not None
                          else elevation - element.thickness.meters)
                model.solids.append(ResolvedSolid(
                    element.uid, element.tag, storey.tag, "pad", outline,
                    bottom, elevation,
                ))
            elif isinstance(element, Footing):
                solid = _resolve_footing(model, element, storey.tag)
                if solid is None:
                    findings.append(_error("integrity.footing_support",
                                           f"footing {element.tag} references missing support "
                                           f"{element.under!r}", element.tag))
                else:
                    model.solids.append(solid)
            elif isinstance(element, Roof):
                roof, roof_findings = _resolve_roof(model, element, storey.tag)
                findings.extend(roof_findings)
                if roof is not None:
                    model.roofs.append(roof)
                    _roof_wall_conditions(model, element, roof)
            elif isinstance(element, Stair):
                stair, stair_findings = _resolve_stair(model, element, storey.tag)
                findings.extend(stair_findings)
                if stair is not None:
                    model.stairs.append(stair)
    # Second pass: FootingBedding resolves against footing solids, so every storey's
    # footings must already be in model.solids regardless of authoring order.
    for storey in plan.storeys:
        for element in plan.storey_elements(storey.tag):
            if isinstance(element, FootingBedding):
                bedding, bedding_findings = _resolve_footing_bedding(model, element, storey.tag)
                findings.extend(bedding_findings)
                if bedding is not None:
                    model.footing_beddings.append(bedding)
    return findings


def _resolve_footing_bedding(
    model: ResolvedModel, bedding: FootingBedding, storey: str
) -> tuple[ResolvedFootingBedding | None, list[Finding]]:
    host = next((s for s in model.solids if s.tag == bedding.host_ref and s.category == "footing"),
                None)
    if host is None:
        return None, [_error("integrity.footing_bedding_host",
                             f"footing bedding {bedding.tag} references missing footing "
                             f"{bedding.host_ref!r}", bedding.tag)]
    perimeter_m = (bedding.perimeter_insulation.meters
                  if bedding.perimeter_insulation is not None else None)
    return ResolvedFootingBedding(
        bedding.uid, bedding.tag, storey, host.tag, host.outline,
        host.z0_m - bedding.undercut.meters, host.z0_m, bedding.aggregate,
        bedding.geotextile, bedding.drain_tile, perimeter_m, bedding.cast_foam_in_aggregate,
    ), []


def _roof_wall_conditions(model: ResolvedModel, authored_roof: Roof,
                          roof: ResolvedRoof) -> None:
    """Emit one transition-bindable condition for every wall terminating at a roof."""
    wall_tags = set(authored_roof.bearing_refs)
    for element in model.plan.storey_elements(roof.storey):
        if isinstance(getattr(element, "top", None), ToRoof) and element.top.roof_ref == roof.tag:
            wall_tags.add(element.tag)
    for wall_tag in sorted(wall_tags):
        wall = model.wall(wall_tag)
        if wall is None:
            continue
        assemblies = tuple(sorted((wall.assembly, roof.assembly)))
        model.conditions.append(
            BoundaryCondition(
                kind=ConditionKind.WALL_ROOF, assemblies=assemblies, detail="roof-bearing",
                element_tags=(wall.tag, roof.tag), key=f"wall_roof:{'|'.join(assemblies)}",
            )
        )


def _resolve_footing(model: ResolvedModel, footing: Footing, storey: str) -> ResolvedSolid | None:
    wall = model.wall(footing.under)
    if wall is not None:
        outline = rect_between(wall.axis[0], wall.axis[1], -footing.width.meters / 2,
                               footing.width.meters / 2)
        z1 = wall.z0_m
        return ResolvedSolid(footing.uid, footing.tag, storey, "footing", outline,
                             z1 - footing.depth.meters, z1)
    post = model.plan.by_tag(footing.under)
    if not isinstance(post, Post):
        return None
    half = footing.width.meters / 2
    x, y = post.position.xy_m
    outline = [(x - half, y - half), (x + half, y - half),
               (x + half, y + half), (x - half, y + half)]
    storey_def = model.plan.storey(storey)
    assert storey_def is not None
    z1 = storey_def.elevation.meters
    return ResolvedSolid(footing.uid, footing.tag, storey, "footing", outline,
                         z1 - footing.depth.meters, z1)


def _resolve_roof(
    model: ResolvedModel, roof: Roof, storey: str
) -> tuple[ResolvedRoof | None, list[Finding]]:
    walls = [model.wall(tag) for tag in roof.bearing_refs]
    missing = [tag for tag, wall in zip(roof.bearing_refs, walls) if wall is None]
    if missing:
        return None, [_error("integrity.roof_bearing", f"roof {roof.tag} references missing "
                             f"bearing wall(s): {', '.join(missing)}", roof.tag)]
    if len(walls) < 2:
        return None, [_error("integrity.roof_bearing", f"roof {roof.tag} needs at least two "
                             "bearing walls", roof.tag)]
    if roof.ridge_direction not in ("x", "y"):
        return None, [_error("integrity.roof_direction", f"roof {roof.tag} ridge_direction "
                             "must be 'x' or 'y'", roof.tag)]
    if model.plan.library.resolve_assembly(roof.assembly) is None:
        return None, [_error("integrity.roof_assembly", f"roof {roof.tag} references unknown "
                             f"assembly {roof.assembly!r}", roof.tag)]
    directions: list[tuple[float, float]] = []
    for wall in walls:
        assert wall is not None
        dx, dy = wall.axis[1][0] - wall.axis[0][0], wall.axis[1][1] - wall.axis[0][1]
        magnitude = math.hypot(dx, dy)
        if magnitude <= 1e-6:
            return None, [_error("integrity.roof_bearing", f"roof {roof.tag} has a zero-length "
                                 "bearing wall", roof.tag)]
        directions.append((dx / magnitude, dy / magnitude))
    first_x, first_y = directions[0]
    if any(abs(first_x * direction_y - first_y * direction_x) > 1e-6
           for direction_x, direction_y in directions[1:]):
        return None, [_error(
            "integrity.roof_footprint", f"roof {roof.tag} has non-parallel bearing walls; "
            "valleys/intersecting roof masses are unsupported", roof.tag,
        )]
    points = [point for wall in walls if wall is not None for point in wall.axis]
    # The bearing walls' outermost layer, for the cladding lap below.
    clad = [
        point for wall in walls if wall is not None and wall.depth_layers()
        for point in wall.depth_layers()[-1].polygon
    ] or points
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    if max(xs) - min(xs) < 1e-6 or max(ys) - min(ys) < 1e-6:
        return None, [_error("integrity.roof_footprint", f"roof {roof.tag} bearing walls do "
                             "not span a roof footprint", roof.tag)]
    overhangs = {edge.lower(): value.meters for edge, value in roof.edge_overhangs}
    default = roof.overhang.meters if roof.overhang is not None else 0.0
    west, east = overhangs.get("west", default), overhangs.get("east", default)
    south, north = overhangs.get("south", default), overhangs.get("north", default)
    # An authored overhang already clears the cladding; only a roof with (near-)zero
    # overhang needs the lap, so this never silently deepens a designed eave.
    # A roof authored with no overhang would otherwise stop at the wall axis, leaving the
    # cladding standing proud of its own roof edge. Lap it. An authored overhang already
    # clears the cladding, so taking the outer of the two never deepens a designed eave.
    clad_xs, clad_ys = [p[0] for p in clad], [p[1] for p in clad]
    minx, maxx = min(min(xs) - west, min(clad_xs)), max(max(xs) + east, max(clad_xs))
    miny, maxy = min(min(ys) - south, min(clad_ys)), max(max(ys) + north, max(clad_ys))
    footprint = [(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)]
    run = (maxy - miny) if roof.ridge_direction == "x" else (maxx - minx)
    if run <= 1e-6:
        return None, [_error("integrity.roof_footprint", f"roof {roof.tag} has zero run", roof.tag)]
    eave = max(wall.z1_m for wall in walls if wall is not None)
    rise = roof.pitch.rise / roof.pitch.run * (run / 2 if roof.form.value == "gable" else run)
    slope = math.sqrt(1 + (roof.pitch.rise / roof.pitch.run) ** 2)
    return ResolvedRoof(
        roof.uid, roof.tag, storey, roof.form.value, footprint, eave, eave + rise,
        roof.ridge_direction, roof.assembly, abs(polygon_area(footprint)) * slope,
    ), []


def _resolve_stair(
    model: ResolvedModel, stair: Stair, storey: str
) -> tuple[ResolvedStair | None, list[Finding]]:
    """Resolve an authored stair layout inside its explicitly-owned opening."""
    source = model.plan.storey(stair.from_storey)
    target = model.plan.storey(stair.to_storey)
    opening = model.plan.by_tag(stair.floor_opening)
    if source is None or target is None:
        return None, [_error("integrity.stair_storey", f"stair {stair.tag} references an "
                             "unknown storey", stair.tag)]
    if not isinstance(opening, FloorOpening):
        return None, [_error("integrity.stair_opening", f"stair {stair.tag} references "
                             f"missing FloorOpening {stair.floor_opening!r}", stair.tag)]
    if stair.to_storey != _element_storey(model, opening.tag):
        return None, [_error("integrity.stair_opening", f"stair {stair.tag} must use an "
                             "opening on its destination storey", stair.tag)]
    # The destination deck (wood FloorSystem or concrete Slab) must own the opening.
    destination_floor = next(
        (element for element in model.plan.storey_elements(stair.to_storey)
         if isinstance(element, (FloorSystem, Slab))), None)
    if destination_floor is None or opening.tag not in destination_floor.openings:
        return None, [_error("integrity.stair_opening", f"stair {stair.tag} opening must be "
                             "owned by the destination FloorSystem/Slab", stair.tag)]
    rise = target.elevation.meters - source.elevation.meters
    if rise <= 0:
        return None, [_error("integrity.stair_rise", f"stair {stair.tag} does not rise to "
                             "its destination storey", stair.tag)]
    outline = [point.xy_m for point in opening.outline]
    if len(outline) < 3:
        return None, [_error("integrity.stair_opening", f"stair {stair.tag} opening has no "
                             "usable outline", stair.tag)]
    xs, ys = [point[0] for point in outline], [point[1] for point in outline]
    along_x = stair.run_direction == "x"
    run = (max(xs) - min(xs)) if along_x else (max(ys) - min(ys))
    width = (max(ys) - min(ys)) if along_x else (max(xs) - min(xs))
    if width + 1e-9 < stair.width.meters:
        return None, [_error("integrity.stair_width", f"stair {stair.tag} is wider than its "
                             "floor opening", stair.tag)]
    if stair.layout not in {"straight", "u_split_landing", "right_angle_winder"}:
        return None, [_error("integrity.stair_layout", f"stair {stair.tag} has unknown layout "
                             f"{stair.layout!r}", stair.tag)]
    if stair.layout == "right_angle_winder":
        if stair.turn_direction not in {"left", "right"}:
            return None, [_error("integrity.stair_turn", f"stair {stair.tag} needs a left or "
                                 "right turn direction", stair.tag)]
        if stair.winder_count < 3:
            return None, [_error("integrity.stair_winders", f"stair {stair.tag} needs at least "
                                 "three winders for a quarter turn", stair.tag)]
    elif stair.winder_count:
        return None, [_error("integrity.stair_winders", f"stair {stair.tag} only accepts "
                             "winders in right_angle_winder layout", stair.tag)]
    risers = math.ceil(rise / _MAX_RISER_M)
    treads = max(0, risers - 1)
    straight_treads = treads - stair.winder_count
    # Turn-landing depth (in the run direction) for the U-stair. Unset reproduces the
    # historical "reserve one stair width" behaviour; an authored value renders a deeper
    # walk-off platform. IRC R311.7.6 floors the landing at the stair width.
    landing_depth_m = (max(stair.landing_depth.meters, stair.width.meters)
                       if stair.landing_depth is not None else stair.width.meters)
    # A winder turn consumes a square whose side is the stair width. The remaining treads
    # must still meet the 10 in. minimum on their straight walking line.
    if stair.layout == "u_split_landing":
        # The parallel flights each use the opening length less the landing depth;
        # the one intervening step consumes the remaining tread in the riser count.
        flight_treads = (treads - 1) // 2
        straight_run = run - landing_depth_m
        tread = straight_run / flight_treads if flight_treads else 0.0
    else:
        straight_run = run - stair.width.meters if stair.layout == "right_angle_winder" else run
        tread = straight_run / straight_treads if straight_treads else 0.0
    if tread + 1e-9 < _MIN_TREAD_M:
        return None, [_error("integrity.stair_geometry", f"stair {stair.tag} needs {risers} "
                             f"risers but its opening only permits {tread / 0.0254:.1f}\" treads "
                             "(IRC R311.7 requires 10\")", stair.tag)]
    riser = rise / risers
    if not _stair_fits_opening(stair, min(xs), max(xs), min(ys), max(ys), tread, risers,
                               landing_depth_m):
        return None, [_error("integrity.stair_opening", f"stair {stair.tag} extends outside "
                             f"floor opening {opening.tag!r}", stair.tag)]
    members = _stair_members(stair, min(xs), min(ys), source.elevation.meters, risers, riser,
                             tread, landing_depth_m)
    # Structural guards: the flight never drops below the subfloor it springs from (so a
    # U-stair well partition cannot poke through the foundation), and a stair rising off a
    # concrete foundation is hung on that concrete rather than floating on stud framing.
    members = _clip_stair_to_subfloor(members, source.elevation.meters)
    members = _anchor_stair_on_concrete(model, stair, members, source.elevation.meters)
    # A stair declaration lives with its destination deck so it can own the opening, but
    # its resolved plan-storey identity is the floor it rises *from*.
    return ResolvedStair(stair.uid, stair.tag, stair.from_storey, stair.to_storey, outline, risers, riser,
                         tread, stair.run_direction, stair.run_reversed, stair.layout,
                         stair.turn_direction, stair.winder_count, members), []


def _element_storey(model: ResolvedModel, tag: str) -> str | None:
    for storey, elements in model.plan.elements.items():
        if any(element.tag == tag for element in elements):
            return storey
    return None


def _stair_members(stair: Stair, minx: float, miny: float, z0: float, risers: int,
                   riser: float, tread: float,
                   landing_depth_m: float) -> tuple[FramedMember, ...]:
    if stair.layout == "right_angle_winder":
        return _winder_stair_members(stair, minx, miny, z0, risers, riser, tread)
    if stair.layout == "u_split_landing":
        return _u_split_landing_members(stair, minx, miny, z0, risers, riser, tread,
                                        landing_depth_m)
    along_x = stair.run_direction == "x"
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    width = stair.width.meters
    sign = -1 if stair.run_reversed else 1
    if along_x:
        end_x, end_y = start_x + sign * tread * (risers - 1), start_y
        strings = (((start_x, start_y), (end_x, end_y)),
                   ((start_x, start_y + width), (end_x, end_y + width)))
    else:
        end_x, end_y = start_x, start_y + sign * tread * (risers - 1)
        strings = (((start_x, start_y), (end_x, end_y)),
                   ((start_x + width, start_y), (end_x + width, end_y)))
    out = [
        FramedMember(stair.uid, f"stringer-{index}", "stringer", "2x12", a, b, z0,
                     z0 + riser * risers, math.hypot(tread * (risers - 1), riser * risers))
        for index, (a, b) in enumerate(strings)
    ]
    for index in range(risers - 1):
        if along_x:
            a = (start_x + sign * tread * index, start_y)
            b = (start_x + sign * tread * index, start_y + width)
        else:
            a = (start_x, start_y + sign * tread * index)
            b = (start_x + width, start_y + sign * tread * index)
        z = z0 + riser * (index + 1)
        out.append(FramedMember(stair.uid, f"tread-{index:03d}", "tread", "2x12", a, b,
                                 z, z + 0.0381, stair.width.meters))
    return tuple(out)


def _u_split_landing_members(stair: Stair, minx: float, miny: float, z0: float,
                             risers: int, riser: float, tread: float,
                             landing_depth_m: float) -> tuple[FramedMember, ...]:
    """Generate two parallel flights with distinct landings and one connecting step."""
    width = stair.width.meters
    # One tread is the step between landings; distribute every remaining tread across the
    # two flights, putting an odd extra tread in the lower flight.
    lower_treads = (risers - 2 + 1) // 2
    upper_treads = risers - 2 - lower_treads
    sign = -1 if stair.run_reversed else 1
    along_x = stair.run_direction == "x"
    if along_x:
        lane0, lane1 = miny, miny + width
        lower_start, upper_start = minx, minx + sign * (tread * upper_treads)
        lower_strings = (((lower_start, lane0), (lower_start + sign * tread * lower_treads, lane0)),
                         ((lower_start, lane0 + width), (lower_start + sign * tread * lower_treads, lane0 + width)))
        upper_strings = (((upper_start, lane1), (upper_start - sign * tread * upper_treads, lane1)),
                         ((upper_start, lane1 + width), (upper_start - sign * tread * upper_treads, lane1 + width)))
    else:
        lane0, lane1 = minx, minx + width
        lower_start, upper_start = miny, miny + sign * (tread * upper_treads)
        lower_strings = (((lane0, lower_start), (lane0, lower_start + sign * tread * lower_treads)),
                         ((lane0 + width, lower_start), (lane0 + width, lower_start + sign * tread * lower_treads)))
        upper_strings = (((lane1, upper_start), (lane1, upper_start - sign * tread * upper_treads)),
                         ((lane1 + width, upper_start), (lane1 + width, upper_start - sign * tread * upper_treads)))
    out: list[FramedMember] = []
    for prefix, strings, count in (("lower", lower_strings, lower_treads), ("upper", upper_strings, upper_treads)):
        for index, (a, b) in enumerate(strings):
            out.append(FramedMember(stair.uid, f"stringer-{prefix}-{index}", "stringer", "2x12", a, b,
                                    z0, z0 + riser * risers,
                                    math.hypot(tread * count, riser * (count + 1))))
    for index in range(lower_treads):
        z = z0 + riser * (index + 1)
        if along_x:
            x = lower_start + sign * tread * index
            a, b = (x, lane0), (x, lane0 + width)
        else:
            y = lower_start + sign * tread * index
            a, b = (lane0, y), (lane0 + width, y)
        out.append(FramedMember(stair.uid, f"tread-lower-{index:03d}", "tread", "2x12", a, b, z, z + 0.0381, width))
    lower_landing_z = z0 + riser * (lower_treads + 1)
    upper_landing_z = lower_landing_z + riser
    if along_x:
        lower_end = lower_start + sign * tread * lower_treads
        upper_end = upper_start - sign * tread * upper_treads
        lower_edge, upper_edge = ((lower_end, lane0), (lower_end, lane0 + width)), ((upper_end, lane1), (upper_end, lane1 + width))
    else:
        lower_end = lower_start + sign * tread * lower_treads
        upper_end = upper_start - sign * tread * upper_treads
        lower_edge, upper_edge = ((lane0, lower_end), (lane0 + width, lower_end)), ((lane1, upper_end), (lane1 + width, upper_end))
    out.append(FramedMember(stair.uid, "landing-lower", "landing", "2x12", *lower_edge,
                            lower_landing_z, lower_landing_z + 0.0381, width))
    out.append(FramedMember(stair.uid, "step-between-landings", "tread", "2x12", *upper_edge,
                            upper_landing_z, upper_landing_z + 0.0381, width))
    out.append(FramedMember(stair.uid, "landing-upper", "landing", "2x12", *upper_edge,
                            upper_landing_z, upper_landing_z + 0.0381, width))
    for index in range(upper_treads):
        z = upper_landing_z + riser * (index + 1)
        if along_x:
            x = upper_start - sign * tread * index
            a, b = (x, lane1), (x, lane1 + width)
        else:
            y = upper_start - sign * tread * index
            a, b = (lane1, y), (lane1 + width, y)
        out.append(FramedMember(stair.uid, f"tread-upper-{index:03d}", "tread", "2x12", a, b, z, z + 0.0381, width))
    # The 180° turn platform: a real walk-off deck spanning both flights (2× width) and
    # ``landing_depth`` deep, filling the reserved zone beyond the flight tops. Framed as
    # joists across the well so a deeper authored landing renders as a deeper platform.
    well = 2.0 * width
    joist_spacing = 0.4064  # 16" o.c.
    joists = max(1, math.ceil(abs(landing_depth_m) / joist_spacing))
    for index in range(joists + 1):
        offset = sign * min(landing_depth_m, joist_spacing * index)
        if along_x:
            x = lower_end + offset
            a, b = (x, lane0), (x, lane0 + well)
        else:
            y = lower_end + offset
            a, b = (lane0, y), (lane0 + well, y)
        out.append(FramedMember(stair.uid, f"landing-joist-{index:03d}", "landing", "2x12",
                                a, b, lower_landing_z, lower_landing_z + 0.0381, well))
    # Well partition between the up and down flights. It bears on the subfloor the stair
    # springs from and rises to the arrival deck — it must NOT run past the subfloor into
    # the foundation below, so its base is clamped there (the flight-clip guard is the
    # backstop). Authored as generated framing (no constructor), exempt from the editable
    # rule like the rest of the stair carriage.
    partition_top = z0 + riser * risers
    lane_boundary = lane0 + width  # the plane dividing the up run from the down run
    # Hold the partition off the opening perimeter so its ends do not foul the surrounding
    # trimmed-deck framing / stair-block walls where the flights meet the arrival deck.
    inset = 0.20
    run_start, run_end = (minx, lower_end) if along_x else (miny, lower_end)
    lo, hi = sorted((run_start, run_end))
    lo, hi = lo + inset, hi - inset
    if hi > lo:
        if along_x:
            pa, pb = (lo, lane_boundary), (hi, lane_boundary)
        else:
            pa, pb = (lane_boundary, lo), (lane_boundary, hi)
        out.append(FramedMember(stair.uid, "well-partition", "partition", "2x4", pa, pb,
                                z0, partition_top, hi - lo))
    return tuple(out)


def _winder_stair_members(stair: Stair, minx: float, miny: float, z0: float,
                          risers: int, riser: float, tread: float) -> tuple[FramedMember, ...]:
    """Generate a lower quarter-turn with consistently fanned winder treads.

    ``start`` is the lower outside corner of the winder square.  The straight flight leaves
    that square in ``run_direction``; ``run_reversed`` selects west/south rather than the
    conventional east/north direction. Each tread edge shares the inside corner and fans
    across the outside of the turn, preventing the opposed-diagonal geometry two winders
    produced.
    """
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    straight_treads = risers - 1 - stair.winder_count
    step_z = lambda index: z0 + riser * (index + 1)
    out: list[FramedMember] = []
    turn_sign = 1 if stair.turn_direction != "right" else -1
    if stair.run_direction == "x":
        sign = -1 if stair.run_reversed else 1
        turn_x = start_x + sign * stair.width.meters
        end_x = turn_x + sign * tread * straight_treads
        strings = (((turn_x, start_y), (end_x, start_y)),
                   ((turn_x, start_y + turn_sign * stair.width.meters),
                    (end_x, start_y + turn_sign * stair.width.meters)))
        for index, (a, b) in enumerate(strings):
            out.append(FramedMember(stair.uid, f"stringer-{index}", "stringer", "2x12", a, b,
                                    z0, z0 + riser * risers,
                                    math.hypot(tread * straight_treads, riser * risers)))
        inside = (turn_x, start_y)
        for index in range(stair.winder_count):
            fraction = (index + 1) / stair.winder_count
            # First half follows the entering outside edge, second half the departing edge.
            if fraction <= 0.5:
                outer = (start_x, start_y + turn_sign * stair.width.meters * fraction * 2)
            else:
                outer = (start_x + sign * stair.width.meters * (fraction * 2 - 1),
                         start_y + turn_sign * stair.width.meters)
            a, b = inside, outer
            out.append(FramedMember(stair.uid, f"winder-{index:03d}", "winder", "tapered tread",
                                    a, b, step_z(index), step_z(index) + 0.0381,
                                    math.hypot(b[0] - a[0], b[1] - a[1])))
        for index in range(straight_treads):
            x = turn_x + sign * tread * index
            out.append(FramedMember(stair.uid, f"tread-{index:03d}", "tread", "2x12",
                                    (x, start_y), (x, start_y + turn_sign * stair.width.meters),
                                    step_z(index + stair.winder_count),
                                    step_z(index + stair.winder_count) + 0.0381,
                                    stair.width.meters))
    else:
        sign = -1 if stair.run_reversed else 1
        turn_y = start_y + sign * stair.width.meters
        end_y = turn_y + sign * tread * straight_treads
        strings = (((start_x, turn_y), (start_x, end_y)),
                   ((start_x + turn_sign * stair.width.meters, turn_y),
                    (start_x + turn_sign * stair.width.meters, end_y)))
        for index, (a, b) in enumerate(strings):
            out.append(FramedMember(stair.uid, f"stringer-{index}", "stringer", "2x12", a, b,
                                    z0, z0 + riser * risers,
                                    math.hypot(tread * straight_treads, riser * risers)))
        inside = (start_x, turn_y)
        for index in range(stair.winder_count):
            fraction = (index + 1) / stair.winder_count
            if fraction <= 0.5:
                outer = (start_x + turn_sign * stair.width.meters * fraction * 2, start_y)
            else:
                outer = (start_x + turn_sign * stair.width.meters, start_y + sign * stair.width.meters *
                         (fraction * 2 - 1))
            a, b = inside, outer
            out.append(FramedMember(stair.uid, f"winder-{index:03d}", "winder", "tapered tread",
                                    a, b, step_z(index), step_z(index) + 0.0381,
                                    math.hypot(b[0] - a[0], b[1] - a[1])))
        for index in range(straight_treads):
            y = turn_y + sign * tread * index
            out.append(FramedMember(stair.uid, f"tread-{index:03d}", "tread", "2x12",
                                    (start_x, y), (start_x + turn_sign * stair.width.meters, y),
                                    step_z(index + stair.winder_count),
                                    step_z(index + stair.winder_count) + 0.0381,
                                    stair.width.meters))
    return tuple(out)


def _clip_stair_to_subfloor(members: tuple[FramedMember, ...],
                            subfloor: float) -> tuple[FramedMember, ...]:
    """Clamp generated stair framing to the subfloor the flight springs from.

    The U-stair well partition (and any carriage member) bears on the first framed deck
    and must never drop into the foundation below it. This is the clip guard the audit
    called for; for a flight already sized off that deck it is a no-op backstop.
    """
    out: list[FramedMember] = []
    for member in members:
        z0 = max(member.z0_m, subfloor)
        z1 = max(member.z1_m, subfloor)
        z0e = None if member.z0_end_m is None else max(member.z0_end_m, subfloor)
        z1e = None if member.z1_end_m is None else max(member.z1_end_m, subfloor)
        if (z0, z1, z0e, z1e) == (member.z0_m, member.z1_m, member.z0_end_m, member.z1_end_m):
            out.append(member)
        else:
            out.append(replace(member, z0_m=z0, z1_m=z1, z0_end_m=z0e, z1_end_m=z1e))
    return tuple(out)


def _wall_carries_run(wall, p0: tuple[float, float], p1: tuple[float, float]) -> bool:
    """True when an axis-aligned stringer p0->p1 runs against a wall's axis (a bearing)."""
    (wx0, wy0), (wx1, wy1) = wall.axis
    if abs(wx1 - wx0) < 1e-6 and abs(p1[0] - p0[0]) < 1e-6:  # both run in y
        if abs(p0[0] - wx0) > 0.20:
            return False
        lo, hi = sorted((p0[1], p1[1]))
        wlo, whi = sorted((wy0, wy1))
        return min(hi, whi) - max(lo, wlo) > 0.10
    if abs(wy1 - wy0) < 1e-6 and abs(p1[1] - p0[1]) < 1e-6:  # both run in x
        if abs(p0[1] - wy0) > 0.20:
            return False
        lo, hi = sorted((p0[0], p1[0]))
        wlo, whi = sorted((wx0, wx1))
        return min(hi, whi) - max(lo, wlo) > 0.10
    return False


def _anchor_stair_on_concrete(model: ResolvedModel, stair: Stair,
                              members: tuple[FramedMember, ...],
                              subfloor: float) -> tuple[FramedMember, ...]:
    """Hang a stair that springs off a concrete foundation on that concrete.

    A basement stair does not float on stud framing: its outer stringers run against the
    poured foundation walls and are carried on wall-mounted (joist-hanger-style) ledgers
    let into the concrete. Annotate every stringer that lands on such a wall with the
    connection the 2D detail pipeline binds, and emit a ledger/hanger band as connector
    geometry so the bearing reads structurally. Stairs that spring off a framed deck (no
    foundation walls on the storey they rise from) are left untouched.
    """
    conc_walls = [w for w in model.walls
                  if w.storey == stair.from_storey and getattr(w, "is_foundation", False)]
    if not conc_walls:
        return members
    out: list[FramedMember] = []
    for member in members:
        if member.category == "stringer":
            host = next((w for w in conc_walls
                         if _wall_carries_run(w, member.p0, member.p1)), None)
            if host is not None:
                tag = f"concrete-wall-hanger:{host.tag}"
                out.append(replace(member, connection=tag))
                top = max(member.z0_m, member.z1_m)
                out.append(FramedMember(
                    stair.uid, f"hanger-{host.tag}-{member.child_key}", "hanger", "hanger",
                    member.p0, member.p1, max(subfloor, top - 0.2032), top,
                    member.length_m, connection=tag))
                continue
        out.append(member)
    return tuple(out)


def _stair_fits_opening(stair: Stair, minx: float, maxx: float, miny: float, maxy: float,
                        tread: float, risers: int, landing_depth_m: float) -> bool:
    """Keep the generated flight entirely within its destination deck opening.

    The opening is the structural headroom contract shared by both storeys.  Resolving a
    flight from a shifted start without checking its cross-flight edge could generate treads
    under intact deck, even when its scalar run and width each fit the opening in isolation.
    """
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    if stair.layout == "u_split_landing":
        flight_treads = max((risers - 2 + 1) // 2, risers - 2 - ((risers - 2 + 1) // 2))
        required_run = landing_depth_m + tread * flight_treads
        if stair.run_direction == "x":
            return (2 * stair.width.meters <= maxy - miny + 1e-9
                    and required_run <= maxx - minx + 1e-9)
        return (2 * stair.width.meters <= maxx - minx + 1e-9
                and required_run <= maxy - miny + 1e-9)
    if stair.layout == "right_angle_winder":
        straight_treads = risers - 1 - stair.winder_count
        cross_end = (start_y + (1 if stair.turn_direction != "right" else -1) * stair.width.meters
                     if stair.run_direction == "x" else
                     start_x + (1 if stair.turn_direction != "right" else -1) * stair.width.meters)
        if stair.run_direction == "x":
            end_x = start_x + (-1 if stair.run_reversed else 1) * (
                stair.width.meters + tread * straight_treads)
            return (min(start_x, end_x) >= minx - 1e-9 and max(start_x, end_x) <= maxx + 1e-9
                    and min(start_y, cross_end) >= miny - 1e-9
                    and max(start_y, cross_end) <= maxy + 1e-9)
        end_y = start_y + (-1 if stair.run_reversed else 1) * (
            stair.width.meters + tread * straight_treads)
        return (min(start_y, end_y) >= miny - 1e-9 and max(start_y, end_y) <= maxy + 1e-9
                and min(start_x, cross_end) >= minx - 1e-9
                and max(start_x, cross_end) <= maxx + 1e-9)
    run = (-1 if stair.run_reversed else 1) * tread * max(0, risers - 1)
    if stair.run_direction == "x":
        return (min(start_x, start_x + run) >= minx - 1e-9
                and max(start_x, start_x + run) <= maxx + 1e-9
                and miny - 1e-9 <= start_y
                and start_y + stair.width.meters <= maxy + 1e-9)
    return (min(start_y, start_y + run) >= miny - 1e-9
            and max(start_y, start_y + run) <= maxy + 1e-9
            and minx - 1e-9 <= start_x
            and start_x + stair.width.meters <= maxx + 1e-9)


def _error(check_id: str, message: str, tag: str) -> Finding:
    return Finding(severity=Severity.ERROR, check_id=check_id, message=message,
                   element_tags=(tag,), result=Result.FAIL)


# --- point + linear structural members (columns / beams) --------------------------
# Posts (→ IfcColumn) and standalone Beams (→ IfcBeam) become ResolvedSolids so the same
# glTF/IFC/model.json consumers that draw slabs also draw the framing. Run this AFTER roof
# framing so authored ridge Beams (already emitted as roof members) are excluded.
_COLUMN_FACETS = 16


def _bearing_stack_drops(model: ResolvedModel) -> tuple[dict[str, float], dict[str, float]]:
    """Derive the post → beam → joist bearing stack from the authored bearing graph.

    The storey datum stays top-of-joist, so a beam carrying joists must drop its whole
    depth *below* the deepest joist bearing on it, and a post carrying that beam must
    shorten to land at the beam soffit. Returns:

    - ``joist_drop``: beam tag → deepest joist depth (m) bearing on that beam.
    - ``post_drop``: post tag → joist drop (m) of the deepest-joist beam it carries, so
      the post can shorten by exactly that amount and preserve any authored base offset
      (e.g. the intentional 2" rear-row drainage rise).
    """
    joist_drop: dict[str, float] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, FloorSystem):
                depth = cross_section(element.joists.member).depth_m
                for ref in element.joists.bearing_refs:
                    joist_drop[ref] = max(joist_drop.get(ref, 0.0), depth)
    post_drop: dict[str, float] = {}
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, Beam):
                drop = joist_drop.get(element.tag, 0.0)
                for ref in element.bearing_refs:
                    post_drop[ref] = max(post_drop.get(ref, 0.0), drop)
    return joist_drop, post_drop


def resolve_columns_and_beams(model: ResolvedModel) -> list[Finding]:
    findings: list[Finding] = []
    solid_top = {s.tag: s.z1_m for s in model.solids}
    ridge_uids = {m.parent_uid for roof in model.roofs for m in roof.members
                  if m.category == "ridge_beam"}
    joist_drop, post_drop = _bearing_stack_drops(model)
    for storey in model.plan.storeys:
        elevation = storey.elevation.meters
        nodes = {e.tag: e.position.xy_m for e in model.plan.storey_elements(storey.tag)
                 if e.element_kind == "Node"}
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, Post):
                model.solids.append(_resolve_post(element, storey.tag, elevation, solid_top,
                                                   storey, post_drop))
            elif isinstance(element, Beam) and element.uid not in ridge_uids:
                solid = _resolve_beam(element, storey.tag, elevation, nodes, joist_drop)
                if solid is None:
                    findings.append(_error("integrity.beam_nodes",
                                           f"beam {element.tag} references missing node(s) "
                                           f"{element.start_node!r}/{element.end_node!r}",
                                           element.tag))
                else:
                    model.solids.append(solid)
    return findings


def _resolve_post(post: Post, storey_tag: str, elevation: float,
                  solid_top: dict[str, float], storey,
                  post_drop: dict[str, float]) -> ResolvedSolid:
    """A post supported by a footing/pad stands up from that support; otherwise its top
    sits at its storey's deck elevation (it carries that level) and it hangs down by its
    height.

    A post carrying joist-loaded beams shortens by that beam's joist drop so its top
    lands at the (lowered) beam soffit. Shortening the authored height rather than
    overriding the top preserves any intentional base offset (the 2" rear-row drainage
    rise), and leaves breezeway/other non-carrying posts untouched."""
    cs = cross_section(post.size)
    height = (post.height.meters if post.height is not None
              else storey.default_ceiling_height.meters)
    base = solid_top.get(post.supported_by) if post.supported_by else None
    drop = post_drop.get(post.tag, 0.0)
    if base is not None:
        z0, z1 = base, base + height - drop
    else:
        z0, z1 = elevation - height, elevation - drop
    return ResolvedSolid(post.uid, post.tag, storey_tag, "column",
                         tuple(_post_outline(post.position.xy_m, cs)), z0, z1,
                         assembly=post.assembly)


def _post_outline(center: tuple[float, float], cs) -> list[tuple[float, float]]:
    cx, cy = center
    if cs.shape == "round":
        r = cs.width_m / 2.0
        return [(cx + r * math.cos(2 * math.pi * k / _COLUMN_FACETS),
                 cy + r * math.sin(2 * math.pi * k / _COLUMN_FACETS))
                for k in range(_COLUMN_FACETS)]
    hw, hd = cs.width_m / 2.0, cs.depth_m / 2.0
    return [(cx - hw, cy - hd), (cx + hw, cy - hd), (cx + hw, cy + hd), (cx - hw, cy + hd)]


def _resolve_beam(beam: Beam, storey_tag: str, elevation: float,
                  nodes: dict[str, tuple[float, float]],
                  joist_drop: dict[str, float]) -> ResolvedSolid | None:
    p0, p1 = nodes.get(beam.start_node), nodes.get(beam.end_node)
    if p0 is None or p1 is None:
        return None
    cs = cross_section(beam.size)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return None
    hw = cs.width_m / 2.0
    nx, ny = -dy / length * hw, dx / length * hw  # perpendicular half-width offset
    outline = [(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny),
               (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)]
    # The beam carries the joists that top out at the storey datum, so its own top sits
    # a joist depth below that datum; hang the beam's depth below that. Walls in
    # ``bearing_refs`` are untouched — the lowered beam seats into their hanger.
    z1 = elevation - joist_drop.get(beam.tag, 0.0)
    z0 = z1 - cs.depth_m
    return ResolvedSolid(beam.uid, beam.tag, storey_tag, "beam", tuple(outline), z0, z1)
