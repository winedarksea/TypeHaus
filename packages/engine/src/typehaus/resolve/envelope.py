"""Resolve slabs, foundations, footings, and constrained roofs into shared geometry."""

from __future__ import annotations

import math

from typehaus.findings import Finding, Result, Severity
from typehaus.model.floors import FloorOpening, FloorSystem, Slab
from typehaus.model.spatial import Roof, Stair
from typehaus.model.refs import ToRoof
from typehaus.model.enums import ConditionKind
from typehaus.model.structure import Footing, FootingBedding, Pad, Post
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
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    if max(xs) - min(xs) < 1e-6 or max(ys) - min(ys) < 1e-6:
        return None, [_error("integrity.roof_footprint", f"roof {roof.tag} bearing walls do "
                             "not span a roof footprint", roof.tag)]
    overhangs = {edge.lower(): value.meters for edge, value in roof.edge_overhangs}
    default = roof.overhang.meters if roof.overhang is not None else 0.0
    west, east = overhangs.get("west", default), overhangs.get("east", default)
    south, north = overhangs.get("south", default), overhangs.get("north", default)
    minx, maxx = min(xs) - west, max(xs) + east
    miny, maxy = min(ys) - south, max(ys) + north
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
    """Resolve a straight flight inside the explicitly-owned opening above it."""
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
    if stair.winder_count not in (0, 2):
        return None, [_error("integrity.stair_winders", f"stair {stair.tag} must use zero "
                             "or two winders", stair.tag)]
    risers = math.ceil(rise / _MAX_RISER_M)
    treads = max(0, risers - 1)
    straight_treads = treads - stair.winder_count
    # Two winders consume a square whose side is the stair width. The remaining treads
    # must still meet the 10 in. minimum on their straight walking line.
    straight_run = run - stair.width.meters if stair.winder_count else run
    tread = straight_run / straight_treads if straight_treads else 0.0
    if tread + 1e-9 < _MIN_TREAD_M:
        return None, [_error("integrity.stair_geometry", f"stair {stair.tag} needs {risers} "
                             f"risers but its opening only permits {tread / 0.0254:.1f}\" treads "
                             "(IRC R311.7 requires 10\")", stair.tag)]
    riser = rise / risers
    if not _stair_fits_opening(stair, min(xs), max(xs), min(ys), max(ys), tread, risers):
        return None, [_error("integrity.stair_opening", f"stair {stair.tag} extends outside "
                             f"floor opening {opening.tag!r}", stair.tag)]
    members = _stair_members(stair, min(xs), min(ys), source.elevation.meters, risers, riser,
                             tread)
    return ResolvedStair(stair.uid, stair.tag, storey, stair.to_storey, outline, risers, riser,
                         tread, stair.run_direction, stair.run_reversed, stair.winder_count,
                         members), []


def _element_storey(model: ResolvedModel, tag: str) -> str | None:
    for storey, elements in model.plan.elements.items():
        if any(element.tag == tag for element in elements):
            return storey
    return None


def _stair_members(stair: Stair, minx: float, miny: float, z0: float, risers: int,
                   riser: float, tread: float) -> tuple[FramedMember, ...]:
    if stair.winder_count:
        return _two_winder_stair_members(stair, minx, miny, z0, risers, riser, tread)
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


def _two_winder_stair_members(stair: Stair, minx: float, miny: float, z0: float,
                               risers: int, riser: float, tread: float) -> tuple[FramedMember, ...]:
    """Generate the Catlin-style lower turn: two winders, then a straight flight.

    ``start`` is the lower outside corner of the winder square.  The straight flight leaves
    that square in ``run_direction``; ``run_reversed`` selects west/south rather than the
    conventional east/north direction. The winder members are diagonal tread edges, which
    lets plan, section, and framed 3D all show the same turn without a second geometry path.
    """
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    straight_treads = risers - 1 - stair.winder_count
    step_z = lambda index: z0 + riser * (index + 1)
    out: list[FramedMember] = []
    if stair.run_direction == "x":
        sign = -1 if stair.run_reversed else 1
        turn_x = start_x + sign * stair.width.meters
        end_x = turn_x + sign * tread * straight_treads
        strings = (((turn_x, start_y), (end_x, start_y)),
                   ((turn_x, start_y + stair.width.meters), (end_x, start_y + stair.width.meters)))
        for index, (a, b) in enumerate(strings):
            out.append(FramedMember(stair.uid, f"stringer-{index}", "stringer", "2x12", a, b,
                                    z0, z0 + riser * risers,
                                    math.hypot(tread * straight_treads, riser * risers)))
        # Ascending north at the east end turns west through these two tapered tread edges.
        winder_edges = (((start_x, start_y),
                         (turn_x, start_y + stair.width.meters / 2)),
                        ((start_x + sign * stair.width.meters / 2, start_y),
                         (turn_x, start_y + stair.width.meters)))
        for index, (a, b) in enumerate(winder_edges):
            out.append(FramedMember(stair.uid, f"winder-{index:03d}", "winder", "tapered tread",
                                    a, b, step_z(index), step_z(index) + 0.0381,
                                    math.hypot(b[0] - a[0], b[1] - a[1])))
        for index in range(straight_treads):
            x = turn_x + sign * tread * index
            out.append(FramedMember(stair.uid, f"tread-{index:03d}", "tread", "2x12",
                                    (x, start_y), (x, start_y + stair.width.meters),
                                    step_z(index + stair.winder_count),
                                    step_z(index + stair.winder_count) + 0.0381,
                                    stair.width.meters))
    else:
        sign = -1 if stair.run_reversed else 1
        turn_y = start_y + sign * stair.width.meters
        end_y = turn_y + sign * tread * straight_treads
        strings = (((start_x, turn_y), (start_x, end_y)),
                   ((start_x + stair.width.meters, turn_y),
                    (start_x + stair.width.meters, end_y)))
        for index, (a, b) in enumerate(strings):
            out.append(FramedMember(stair.uid, f"stringer-{index}", "stringer", "2x12", a, b,
                                    z0, z0 + riser * risers,
                                    math.hypot(tread * straight_treads, riser * risers)))
        winder_edges = (((start_x, start_y),
                         (start_x + stair.width.meters / 2, turn_y)),
                        ((start_x, start_y + sign * stair.width.meters / 2),
                         (start_x + stair.width.meters, turn_y)))
        for index, (a, b) in enumerate(winder_edges):
            out.append(FramedMember(stair.uid, f"winder-{index:03d}", "winder", "tapered tread",
                                    a, b, step_z(index), step_z(index) + 0.0381,
                                    math.hypot(b[0] - a[0], b[1] - a[1])))
        for index in range(straight_treads):
            y = turn_y + sign * tread * index
            out.append(FramedMember(stair.uid, f"tread-{index:03d}", "tread", "2x12",
                                    (start_x, y), (start_x + stair.width.meters, y),
                                    step_z(index + stair.winder_count),
                                    step_z(index + stair.winder_count) + 0.0381,
                                    stair.width.meters))
    return tuple(out)


def _stair_fits_opening(stair: Stair, minx: float, maxx: float, miny: float, maxy: float,
                        tread: float, risers: int) -> bool:
    """Keep the generated flight entirely within its destination deck opening.

    The opening is the structural headroom contract shared by both storeys.  Resolving a
    flight from a shifted start without checking its cross-flight edge could generate treads
    under intact deck, even when its scalar run and width each fit the opening in isolation.
    """
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    if stair.winder_count:
        straight_treads = risers - 1 - stair.winder_count
        if stair.run_direction == "x":
            end_x = start_x + (-1 if stair.run_reversed else 1) * (
                stair.width.meters + tread * straight_treads)
            return (min(start_x, end_x) >= minx - 1e-9 and max(start_x, end_x) <= maxx + 1e-9
                    and miny - 1e-9 <= start_y
                    and start_y + stair.width.meters <= maxy + 1e-9)
        end_y = start_y + (-1 if stair.run_reversed else 1) * (
            stair.width.meters + tread * straight_treads)
        return (min(start_y, end_y) >= miny - 1e-9 and max(start_y, end_y) <= maxy + 1e-9
                and minx - 1e-9 <= start_x
                and start_x + stair.width.meters <= maxx + 1e-9)
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
