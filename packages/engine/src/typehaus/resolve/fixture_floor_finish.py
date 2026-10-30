"""Bathing-fixture installation footprints shared by finish geometry and quantities."""

from __future__ import annotations

from dataclasses import replace

from shapely.geometry import Polygon

from typehaus.findings import Finding, Result, Severity
from typehaus.resolve.model import FinishPart, ResolvedModel
from typehaus.resolve.overlay import difference, intersection, union_all
from typehaus.resolve.room_finish import finish_parts
from typehaus.resolve.room_floor import SLAB_MATCH_TOLERANCE_M
from typehaus.resolve.room_lookup import axis_polygon
from typehaus.resolve.walking_surface import surfaces_at


def fixture_support_elevation(model: ResolvedModel, point: tuple[float, float],
                              structural_anchor_m: float) -> float:
    """Top of the supporting slab/subfloor, rather than the storey's joist datum."""
    surfaces = [surface for surface in surfaces_at(model, point)
                if abs(surface.deck_top_m - structural_anchor_m) < SLAB_MATCH_TOLERANCE_M]
    if not surfaces:
        raise ValueError("Fixture has no supporting slab or subfloor at its location")
    return min(surfaces, key=lambda surface: abs(
        surface.deck_top_m - structural_anchor_m)).deck_top_m


def _geometry(parts: tuple[FinishPart, ...]):
    return union_all([Polygon(outline, holes=list(holes)) for outline, holes in parts])


def _cut_covering(parts, excluded):
    geometry = _geometry(parts)
    # Avoid GEOS cycling a ring's first vertex when a repeated pass removes no material.
    if intersection(geometry, excluded).area == 0:
        return parts
    return finish_parts(difference(geometry, excluded))


def _area(parts):
    return sum(Polygon(outline, holes=list(holes)).area for outline, holes in parts)


def _installation_footprint(model, fixture, placed):
    enclosure = fixture.tub_enclosure
    if enclosure is None:
        if len(placed.footprint) < 3:
            raise ValueError("Fixture exclusion footprint is unresolved")
        return Polygon(placed.footprint)
    deck = next((solid for solid in model.solids if solid.tag == enclosure.deck_ref), None)
    walls = [model.wall(ref) for ref in enclosure.knee_wall_refs]
    if deck is None or len(deck.outline) < 3 or any(wall is None for wall in walls):
        raise ValueError("Tub enclosure exclusion requires its deck and knee walls")
    if deck.storey != placed.storey or any(wall.storey != placed.storey for wall in walls):
        raise ValueError("Tub enclosure exclusion parts must share the fixture's storey")
    # The cap's cutout is the bath bay, not a patch of room flooring. Access-panel holes
    # likewise do not put tile beneath the box, so use complete exterior outlines.
    footprints = [Polygon(deck.outline)]
    footprints.extend(Polygon(layer.polygon) for wall in walls
                      for layer in wall.depth_layers() if len(layer.polygon) >= 3)
    footprints.extend(Polygon(panel.outline) for panel in model.panelings
                      if panel.wall_tag in enclosure.knee_wall_refs
                      and len(panel.outline) >= 3)
    return union_all(footprints)


def resolve_fixture_floor_finishes(model: ResolvedModel) -> list[Finding]:
    """Cut installed coverings after placement and doorway extensions, before takeoff.

    Work from existing finish parts so stair holes, split zones and reveal patches survive.
    Coatings have no installation buildup and retain their continuous substrate allowance.
    """
    findings: list[Finding] = []
    types = {kind.tag: kind for kind in model.plan.library.fixture_types}
    canvas = {item.tag: item for item in model.canvas_objects}
    by_storey: dict[str, list] = {}
    for storey in model.plan.storeys:
        for fixture in model.plan.storey_elements(storey.tag):
            if fixture.element_kind != "Fixture":
                continue
            fixture_type = types.get(fixture.type_ref)
            if fixture_type is None or not fixture_type.excludes_floor_finish:
                continue
            try:
                placed = canvas.get(fixture.tag)
                if placed is None:
                    raise ValueError("Fixture exclusion has no resolved placement")
                footprint = _installation_footprint(model, fixture, placed)
                if footprint.is_empty or not footprint.is_valid:
                    raise ValueError("Fixture exclusion footprint is empty or invalid")
                by_storey.setdefault(storey.tag, []).append(footprint)
            except ValueError as exc:
                findings.append(Finding(
                    severity=Severity.ERROR, check_id="integrity.fixture_floor_finish",
                    message=str(exc), element_tags=(fixture.tag,), result=Result.FAIL))
    materials = {material.tag: material for material in model.plan.library.materials}

    def coating(ref):
        material = materials.get(ref)
        return material is not None and material.coating

    cuts = {storey: union_all(parts) for storey, parts in by_storey.items()}
    rooms = []
    for room in model.rooms:
        cut = cuts.get(room.storey)
        if cut is None:
            rooms.append(room)
            continue
        field = _geometry(room.field_finish)
        # Axis ownership includes enclosure knee walls; reveal patches can extend beyond it.
        extent = union_all([axis_polygon(room), field,
                            *(_geometry(zone.parts) for zone in room.finish_zones)])
        excluded = intersection(cut, extent)
        if excluded.area == 0:
            rooms.append(room)
            continue
        parts = (room.field_finish if coating(room.floor_finish)
                 else _cut_covering(room.field_finish, excluded))
        zones = []
        for zone in room.finish_zones:
            zone_parts = (zone.parts if coating(zone.material_ref)
                          else _cut_covering(zone.parts, excluded))
            zones.append(replace(zone, parts=zone_parts, area_m2=_area(zone_parts)))
        rooms.append(replace(room, field_finish=parts, field_area_m2=_area(parts),
                             finish_zones=tuple(zones),
                             floor_finish_exclusions=finish_parts(excluded.normalize())))
    model.rooms = rooms
    return findings
