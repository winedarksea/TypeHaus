"""Resolve slabs, foundations, footings, and constrained roofs into shared geometry."""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.findings import Finding, element_error
from typehaus.model.floors import FloorOpening, FloorSystem, Slab, Soffit
from typehaus.model.spatial import Roof, Stair
from typehaus.model.refs import ToRoof
from typehaus.model.enums import ConditionKind
from typehaus.model.structure import Beam, Footing, FootingBedding, GlazingPanel, Pad, Post
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.solver import band_axis
from typehaus.resolve.geometry import circle_outline, polygon_area, rect_between
from typehaus.resolve.roof_layer_setbacks import deck_rise_m, layer_edge_setbacks
from typehaus.resolve.drain_tile import drain_tile_solids, resolved_spec
from typehaus.resolve.model import (
    BoundaryCondition,
    Ring,
    ResolvedFootingBedding,
    ResolvedModel,
    ResolvedRoof,
    ResolvedSoffit,
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
                # ``thickness`` is the pour, always. An authored ``bottom_elevation`` sets
                # where the pad *bears* — at frost depth, typically — and the pad is that
                # thick above it; without one the pad hangs its thickness below the storey
                # datum. Reading the bottom as authored but the top as the storey datum
                # (which is what this did) turns a 12" pad on a 42" frost base into a 42"
                # block of concrete, and buries whatever bears on its top.
                if element.bottom_elevation is not None:
                    bottom = element.bottom_elevation.meters
                    top = bottom + element.thickness.meters
                else:
                    top = elevation
                    bottom = top - element.thickness.meters
                model.solids.append(ResolvedSolid(
                    element.uid, element.tag, storey.tag, "pad", outline, bottom, top,
                ))
            elif isinstance(element, Soffit):
                # A dropped ceiling is a framed box hanging under the ceiling plane — a
                # plan polygon between two elevations, which is exactly ``ResolvedSolid``.
                # Its own ``underside_elevation`` (storey-relative) wins; otherwise ``drop``
                # measures down from the storey's default ceiling. Both absent is a
                # modelling gap, not a zero-depth box, so it is named rather than guessed.
                outline = [point.xy_m for point in element.outline]
                if len(outline) < 3:
                    findings.append(element_error("integrity.soffit_outline",
                                           f"soffit {element.tag} needs a closed outline",
                                           element.tag))
                    continue
                ceiling = elevation + storey.default_ceiling_height.meters
                if element.underside_elevation is not None:
                    bottom = elevation + element.underside_elevation.meters
                elif element.drop is not None:
                    bottom = ceiling - element.drop.meters
                else:
                    findings.append(element_error(
                        "integrity.soffit_elevation",
                        f"soffit {element.tag} states neither drop nor "
                        "underside_elevation", element.tag))
                    continue
                if bottom >= ceiling:
                    findings.append(element_error(
                        "integrity.soffit_elevation",
                        f"soffit {element.tag} undersides at or above the ceiling plane "
                        "it hangs from", element.tag))
                    continue
                model.solids.append(ResolvedSolid(
                    element.uid, element.tag, storey.tag, "soffit", outline,
                    bottom, ceiling,
                ))
                # The finished box above is what renders; this record is its framing
                # host, carrying the authored FramingSpec through to the framing stage
                # (typehaus.resolve.framing.soffit). A soffit with no spec still gets a
                # record — it simply frames no members — so the two lists stay 1:1.
                model.soffits.append(ResolvedSoffit(
                    element.uid, element.tag, storey.tag, outline, bottom, ceiling,
                    framing=element.framing,
                ))
            elif isinstance(element, GlazingPanel):
                solid, panel_findings = _resolve_glazing_panel(element, storey.tag)
                findings.extend(panel_findings)
                if solid is not None:
                    model.solids.append(solid)
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


def _resolve_glazing_panel(
    panel: GlazingPanel, storey: str
) -> tuple[ResolvedSolid | None, list[Finding]]:
    """A glazing sheet as a thin solid at its own absolute elevation.

    Both planes are authored the way the sheet is actually described on site: a canopy panel
    by the footprint it covers, a wall panel by the line it stands on. Neither is derived
    from a storey datum — a panel sits where its frame puts it.
    """
    thickness = panel.thickness.meters
    top = panel.top_elevation.meters
    points = [point.xy_m for point in panel.outline]
    if panel.plane == "vertical":
        if len(points) < 2:
            return None, [element_error(
                "integrity.glazing_panel_run",
                f"vertical glazing panel {panel.tag} needs at least 2 plan points to stand on",
                panel.tag)]
        if panel.base_elevation is None:
            return None, [element_error(
                "integrity.glazing_panel_base",
                f"vertical glazing panel {panel.tag} needs a base_elevation", panel.tag)]
        base = panel.base_elevation.meters
        if top <= base:
            return None, [element_error(
                "integrity.glazing_panel_height",
                f"glazing panel {panel.tag} tops out at or below its base", panel.tag)]
        half = thickness / 2.0
        outline = rect_between(points[0], points[-1], -half, half)
        return ResolvedSolid(panel.uid, panel.tag, storey, "glazing", tuple(outline),
                             base, top, panel.assembly), []
    if len(points) < 3:
        return None, [element_error(
            "integrity.glazing_panel_outline",
            f"horizontal glazing panel {panel.tag} needs a closed outline", panel.tag)]
    return ResolvedSolid(panel.uid, panel.tag, storey, "glazing", tuple(points),
                         top - thickness, top, panel.assembly), []


def _slab_elevations(slab: Slab, elevation: float) -> tuple[float, float]:
    """The slab's vertical extent, honouring the one storey datum: top of floor structure.

    A ``datum="structure"`` slab *is* the floor structure, so it hangs its thickness below
    the datum. A ``datum="walking_surface"`` slab is decking over a FloorSystem whose joists
    already top out at the datum, so it rides on top — exactly like that FloorSystem's own
    subfloor sheet. Hanging the latter below the datum buried the boards inside the top inch
    of their own joists.

    An authored ``top_elevation`` overrides the storey datum entirely — the slab tops out
    there and hangs its thickness below, whatever ``datum`` says. Mixing an authored
    elevation with a storey-derived one is the bug ``Pad.bottom_elevation`` records above:
    take one end from the author and the other from the storey and the thickness stops being
    the pour.
    """
    thickness = slab.thickness.meters
    if slab.top_elevation is not None:
        top = slab.top_elevation.meters
        return top - thickness, top
    if slab.datum == "walking_surface":
        return elevation, elevation + thickness
    return elevation - thickness, elevation


def _bedding_host_footprint(
    model: ResolvedModel, bedding: FootingBedding
) -> tuple[Ring | None, float | None, list[Finding]]:
    """The plan ring the bed fills and the elevation it tops out at (the host's underside).

    A footing host beds its own footprint. A wall host has no footing to take a footprint
    from, so the bed is a band on the wall's axis — ``width`` wide, defaulting to the wall's
    own thickness. Like ``_resolve_footing``, the band is not extended past the axis ends:
    two legs of an L therefore butt at the shared node rather than overlapping, which is
    what keeps the corner out of the stone order twice.
    """
    host = next((s for s in model.solids
                 if s.tag == bedding.host_ref and s.category == "footing"), None)
    if host is not None:
        return host.outline, host.z0_m, []
    wall = model.wall(bedding.host_ref)
    if wall is None:
        return None, None, [element_error(
            "integrity.footing_bedding_host",
            f"footing bedding {bedding.tag} references missing footing or wall "
            f"{bedding.host_ref!r}", bedding.tag)]
    # The band the layers actually occupy — a ``face(...)``-aligned wall does not straddle
    # its node line, and a bed centred on that line would be off by half the wall.
    axis = band_axis(wall.axis, [point for layer in wall.layers for point in layer.polygon])
    half = (bedding.width.meters if bedding.width is not None else wall.thickness_m) / 2.0
    return rect_between(axis[0], axis[1], -half, half), wall.z0_m, []


def _resolve_footing_bedding(
    model: ResolvedModel, bedding: FootingBedding, storey: str
) -> tuple[ResolvedFootingBedding | None, list[Finding]]:
    outline, z1, findings = _bedding_host_footprint(model, bedding)
    if outline is None or z1 is None:
        return None, findings
    perimeter_m = (bedding.perimeter_insulation.meters
                  if bedding.perimeter_insulation is not None else None)
    z0 = z1 - bedding.undercut.meters
    spec = resolved_spec(bedding.drain_tile_spec)
    # The tile is derived, not authored: nobody draws a perimeter ring by hand, it follows
    # the excavation. Emitted here so the drainage toggle and the IFC stormwater system see
    # the ring the take-off has always billed by the foot.
    if bedding.drain_tile:
        model.solids.extend(drain_tile_solids(
            bedding.uid, bedding.tag, storey, outline, z0, spec))
    return ResolvedFootingBedding(
        bedding.uid, bedding.tag, storey, bedding.host_ref, outline,
        z0, z1, bedding.aggregate,
        bedding.geotextile, bedding.drain_tile, perimeter_m, bedding.cast_foam_in_aggregate,
        spec,
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
        axis = wall.axis
        if footing.center_on == "wall":
            # The band the resolved layers actually occupy, which is not the node line
            # when the wall carries an ``alignment=face(...)``. Same correction the
            # framing solver makes to put studs inside the structure layer.
            axis = band_axis(axis, [point for layer in wall.layers for point in layer.polygon])
        outline = rect_between(axis[0], axis[1], -footing.width.meters / 2,
                               footing.width.meters / 2)
        z1 = wall.z0_m
        return ResolvedSolid(footing.uid, footing.tag, storey, "footing", outline,
                             z1 - footing.depth.meters, z1, assembly=footing.assembly)
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
                         z1 - footing.depth.meters, z1, assembly=footing.assembly)


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
                # An authored ``top_elevation`` pins the beam absolutely, so there is no
                # derived datum arithmetic for a post to follow — and propagating one would
                # actively break the case it exists for. A breezeway post runs *past* its
                # floor beam (which is bolted to the post face) all the way to the roof;
                # shortening it by that beam's joist depth would take the roof with it.
                if element.top_elevation is not None:
                    continue
                drop = joist_drop.get(element.tag, 0.0)
                for ref in element.bearing_refs:
                    post_drop[ref] = max(post_drop.get(ref, 0.0), drop)
    return joist_drop, post_drop


def resolve_columns_and_beams(model: ResolvedModel) -> list[Finding]:
    findings: list[Finding] = []
    # A post bears on a wall top as readily as on a pad: the balcony pillars stand on the
    # masonry porch railing, whose CMU cores are grouted to receive their bases. Walls are
    # not solids, so merge their tops in first and let a same-tag solid win.
    solid_top = {w.tag: w.z1_m for w in model.walls}
    # A joisted deck is a bearing top too. The storey datum is top-of-joist, so its walking
    # surface is that datum plus whatever sheet is laid on it — which is where a post
    # standing on the deck starts. (The porch's rear-centre balcony pillar is the case: its
    # north edge has no masonry railing to be grouted into, so it stands on the decking.)
    solid_top.update({
        e.tag: (s.elevation.meters
                + (e.subfloor.thickness.meters if e.subfloor is not None else 0.0))
        for s in model.plan.storeys
        for e in model.plan.storey_elements(s.tag)
        if isinstance(e, FloorSystem)
    })
    solid_top.update({s.tag: s.z1_m for s in model.solids})
    ridge_uids = {m.parent_uid for roof in model.roofs for m in roof.members
                  if m.category == "ridge_beam"}
    joist_drop, post_drop = _bearing_stack_drops(model)
    for storey in model.plan.storeys:
        elevation = storey.elevation.meters
        nodes = {e.tag: e.position.xy_m for e in model.plan.storey_elements(storey.tag)
                 if e.element_kind == "Node"}
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, Post):
                solid = _resolve_post(element, storey.tag, elevation, solid_top,
                                      storey, post_drop)
                model.solids.append(solid)
                # A post can bear on another post — a 6x6 standing on the concrete pier that
                # lifts it clear of the ground. Publishing each resolved top as we go is what
                # makes that chain work; ``solid_top`` was snapshotted before this loop, so a
                # support resolved in the same pass was invisible and its post silently fell
                # back to hanging below the storey datum.
                solid_top[solid.tag] = solid.z1_m
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
    # ``bearing_refs`` are untouched — the lowered beam seats into their hanger. An
    # authored ``top_elevation`` wins outright: a beam carrying no joists has no drop to
    # derive, and the girts that hang under an already-dropped beam land below anything
    # this datum arithmetic can reach.
    z1 = (beam.top_elevation.meters if beam.top_elevation is not None
          else elevation - joist_drop.get(beam.tag, 0.0))
    z0 = z1 - cs.depth_m
    # An unset assembly leaves the solid on the "beam" palette entry (wood) rather than the
    # neutral fallback, so an unfinished beam still reads as lumber in every renderer.
    return ResolvedSolid(beam.uid, beam.tag, storey_tag, "beam", tuple(outline), z0, z1,
                         assembly=beam.assembly)
