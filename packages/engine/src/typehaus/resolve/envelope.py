"""Resolve slabs, foundations, footings, and constrained roofs into shared geometry."""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.findings import Finding, element_error
from typehaus.model.floors import FloorOpening, FloorSystem, Slab
from typehaus.model.spatial import Roof, Stair
from typehaus.model.refs import ToRoof
from typehaus.model.enums import ConditionKind
from typehaus.model.structure import Beam, Footing, FootingBedding, Pad, Post
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import circle_outline, polygon_area, rect_between
from typehaus.resolve.roof_layer_setbacks import deck_rise_m, layer_edge_setbacks
from typehaus.resolve.model import (
    BoundaryCondition,
    ResolvedFootingBedding,
    ResolvedModel,
    ResolvedRoof,
    ResolvedSolid,
)
from typehaus.resolve.stairs import _resolve_stair


def resolve_envelope_geometry(model: ResolvedModel) -> list[Finding]:
    """Populate derived non-wall envelope geometry and return precise bad-ref findings."""
    findings: list[Finding] = []
    plan = model.plan
    for wall in model.walls:
        if wall.z1_m <= wall.z0_m:
            findings.append(element_error("integrity.wall_elevation", f"wall {wall.tag} has a "
                                   "non-positive resolved height", wall.tag))
    for storey in plan.storeys:
        elevation = storey.elevation.meters
        for element in plan.storey_elements(storey.tag):
            if isinstance(element, Slab):
                outline = [point.xy_m for point in element.outline]
                if len(outline) < 3:
                    findings.append(element_error("integrity.slab_outline",
                                           f"slab {element.tag} needs a closed outline",
                                           element.tag))
                    continue
                z0, z1 = _slab_elevations(element, elevation)
                model.solids.append(ResolvedSolid(
                    element.uid, element.tag, storey.tag, "slab", outline, z0, z1,
                    element.assembly,
                    tuple(tuple(point.xy_m for point in model.plan.by_tag(tag).outline)
                          for tag in element.openings
                          if isinstance(model.plan.by_tag(tag), FloorOpening)),
                ))
            elif isinstance(element, Pad):
                outline = [point.xy_m for point in element.outline]
                if len(outline) < 3:
                    findings.append(element_error("integrity.pad_outline",
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
                    findings.append(element_error("integrity.footing_support",
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


def _slab_elevations(slab: Slab, elevation: float) -> tuple[float, float]:
    """The slab's vertical extent, honouring the one storey datum: top of floor structure.

    A ``datum="structure"`` slab *is* the floor structure, so it hangs its thickness below
    the datum. A ``datum="walking_surface"`` slab is decking over a FloorSystem whose joists
    already top out at the datum, so it rides on top — exactly like that FloorSystem's own
    subfloor sheet. Hanging the latter below the datum buried the boards inside the top inch
    of their own joists.
    """
    thickness = slab.thickness.meters
    if slab.datum == "walking_surface":
        return elevation, elevation + thickness
    return elevation - thickness, elevation


def _resolve_footing_bedding(
    model: ResolvedModel, bedding: FootingBedding, storey: str
) -> tuple[ResolvedFootingBedding | None, list[Finding]]:
    host = next((s for s in model.solids if s.tag == bedding.host_ref and s.category == "footing"),
                None)
    if host is None:
        return None, [element_error("integrity.footing_bedding_host",
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
        return None, [element_error("integrity.roof_bearing", f"roof {roof.tag} references missing "
                             f"bearing wall(s): {', '.join(missing)}", roof.tag)]
    if len(walls) < 2:
        return None, [element_error("integrity.roof_bearing", f"roof {roof.tag} needs at least two "
                             "bearing walls", roof.tag)]
    if roof.ridge_direction not in ("x", "y"):
        return None, [element_error("integrity.roof_direction", f"roof {roof.tag} ridge_direction "
                             "must be 'x' or 'y'", roof.tag)]
    if model.plan.library.resolve_assembly(roof.assembly) is None:
        return None, [element_error("integrity.roof_assembly", f"roof {roof.tag} references unknown "
                             f"assembly {roof.assembly!r}", roof.tag)]
    directions: list[tuple[float, float]] = []
    for wall in walls:
        assert wall is not None
        dx, dy = wall.axis[1][0] - wall.axis[0][0], wall.axis[1][1] - wall.axis[0][1]
        magnitude = math.hypot(dx, dy)
        if magnitude <= 1e-6:
            return None, [element_error("integrity.roof_bearing", f"roof {roof.tag} has a zero-length "
                                 "bearing wall", roof.tag)]
        directions.append((dx / magnitude, dy / magnitude))
    first_x, first_y = directions[0]
    if any(abs(first_x * direction_y - first_y * direction_x) > 1e-6
           for direction_x, direction_y in directions[1:]):
        return None, [element_error(
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
        return None, [element_error("integrity.roof_footprint", f"roof {roof.tag} bearing walls do "
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
        return None, [element_error("integrity.roof_footprint", f"roof {roof.tag} has zero run", roof.tag)]
    plate_top = max(wall.z1_m for wall in walls if wall is not None)
    # ``eave_z_m`` is the rafter-top (deck) plane: a rafter-framed roof rises
    # ``deck_rise_m`` above the plate (only the birdsmouth sinks below it, per the
    # golden eave detail). Truss roofs keep eave == plate top here — ``_frame_trusses``
    # self-corrects via its raised-heel delta.
    roof_assembly = model.plan.library.resolve_assembly(roof.assembly)
    bearing_assembly = model.plan.library.resolve_assembly(walls[0].assembly)
    rise_to_deck = deck_rise_m(roof_assembly, bearing_assembly, roof.pitch)
    eave = plate_top + (rise_to_deck or 0.0)
    rise = roof.pitch.rise / roof.pitch.run * (run / 2 if roof.form.value == "gable" else run)
    slope = math.sqrt(1 + (roof.pitch.rise / roof.pitch.run) ** 2)
    resolved = ResolvedRoof(
        roof.uid, roof.tag, storey, roof.form.value, footprint, eave, eave + rise,
        roof.ridge_direction, roof.assembly, abs(polygon_area(footprint)) * slope,
        bearing_z_m=plate_top,
    )
    if rise_to_deck is not None:
        # Only rafter-framed roofs get the reference clip setbacks (garage/truss deferred).
        resolved = replace(resolved, layer_edge_setbacks=layer_edge_setbacks(model, resolved))
    return resolved, []


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
                    findings.append(element_error("integrity.beam_nodes",
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
        return circle_outline(center, cs.width_m / 2.0, _COLUMN_FACETS)
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
    # An unset assembly leaves the solid on the "beam" palette entry (wood) rather than the
    # neutral fallback, so an unfinished beam still reads as lumber in every renderer.
    return ResolvedSolid(beam.uid, beam.tag, storey_tag, "beam", tuple(outline), z0, z1,
                         assembly=beam.assembly)
