"""Installation footprints that cut floor coverings, shared by finish geometry and quantities.

Bathing fixtures cut every covering. Fixed casework on a toe kick stands on the subfloor
and cuts only a floating covering, its footprint less the kick strip (decision #112).
"""

from __future__ import annotations

from dataclasses import replace

from shapely.affinity import rotate, translate
from shapely.geometry import LineString, Polygon

from typehaus.findings import Finding, Result, Severity
from typehaus.model.placeables import MountKind
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


# A footprint edge within this of the bounding box is an outer face, not an L's notch face.
_OUTER_FACE_TOLERANCE_M = 1e-6


def _front_faces(local: Polygon) -> list[LineString]:
    """The faces a toe kick runs along: an L's notch faces, else the local -y face."""
    min_x, min_y, max_x, max_y = local.bounds
    coords = list(local.exterior.coords)
    edges = list(zip(coords, coords[1:], strict=False))

    def outer(a, b) -> bool:
        return any(abs(a[i] - edge) < _OUTER_FACE_TOLERANCE_M
                   and abs(b[i] - edge) < _OUTER_FACE_TOLERANCE_M
                   for i, edge in ((0, min_x), (0, max_x), (1, min_y), (1, max_y)))

    notch = [LineString(edge) for edge in edges if not outer(*edge)]
    return notch or [LineString(edge) for edge in edges
                     if abs(edge[0][1] - min_y) < _OUTER_FACE_TOLERANCE_M
                     and abs(edge[1][1] - min_y) < _OUTER_FACE_TOLERANCE_M]


def _casework_footprint(placed, setback_m: float):
    """The box behind the kick, in plan: the placed footprint less ``setback_m`` at its fronts."""
    if len(placed.footprint) < 3:
        raise ValueError("Casework exclusion footprint is unresolved")
    cx, cy = placed.position
    local = rotate(translate(Polygon(placed.footprint), -cx, -cy),
                   -placed.rotation_degrees, origin=(0, 0))
    kick = union_all([face.buffer(setback_m, cap_style="square")
                      for face in _front_faces(local)]) if setback_m > 0 else Polygon()
    bearing = difference(local, kick)
    if bearing.area == 0:
        raise ValueError("Toe kick is as deep as the casework footprint")
    return translate(rotate(bearing, placed.rotation_degrees, origin=(0, 0)), cx, cy)


def _stands_on_floor(item) -> bool:
    mount = getattr(item, "mount", None)
    return mount is None or (mount.kind is MountKind.FLOOR
                             and (mount.elevation is None or mount.elevation.meters == 0))


def _exclusion_footprints(model: ResolvedModel):
    """Per storey: bathing-fixture footprints (every covering) and casework (floating only)."""
    findings: list[Finding] = []
    library = model.plan.library
    types = {"Fixture": {t.tag: t for t in library.fixture_types},
             "Furniture": {t.tag: t for t in getattr(library, "furniture_types", ())},
             "Appliance": {t.tag: t for t in getattr(library, "appliance_types", ())}}
    canvas = {item.tag: item for item in model.canvas_objects}
    fixtures: dict[str, list] = {}
    casework: dict[str, list] = {}
    for storey in model.plan.storeys:
        for item in model.plan.storey_elements(storey.tag):
            item_type = types.get(item.element_kind, {}).get(getattr(item, "type_ref", None))
            if item_type is None:
                continue
            toe_kick = getattr(item_type, "toe_kick_depth", None)
            bathing = item.element_kind == "Fixture" and item_type.excludes_floor_finish
            if not bathing and (toe_kick is None or not _stands_on_floor(item)):
                continue
            try:
                placed = canvas.get(item.tag)
                if placed is None:
                    raise ValueError("Floor-finish exclusion has no resolved placement")
                footprint = (_installation_footprint(model, item, placed) if bathing
                             else _casework_footprint(placed, toe_kick.meters))
                if footprint.is_empty or not footprint.is_valid:
                    raise ValueError("Floor-finish exclusion footprint is empty or invalid")
                (fixtures if bathing else casework).setdefault(storey.tag, []).append(footprint)
            except ValueError as exc:
                findings.append(Finding(
                    severity=Severity.ERROR, check_id="integrity.fixture_floor_finish",
                    message=str(exc), element_tags=(item.tag,), result=Result.FAIL))
    return ({storey: union_all(parts) for storey, parts in fixtures.items()},
            {storey: union_all(parts) for storey, parts in casework.items()}, findings)


def _floating_region(room, extent, floating):
    """Where the room's covering floats: its field unless a zone says otherwise.

    Read off zone outlines, not cut parts, so a second pass finds the same region.
    """
    region = extent if floating(room.floor_finish) else Polygon()
    for zone in room.finish_zones:
        if len(zone.outline) < 3:
            continue
        outline = Polygon(zone.outline)
        region = (union_all([region, intersection(outline, extent)])
                  if floating(zone.material_ref) else difference(region, outline))
    return region


def resolve_fixture_floor_finishes(model: ResolvedModel) -> list[Finding]:
    """Cut installed coverings after placement and doorway extensions, before takeoff.

    Work from existing finish parts so stair holes, split zones and reveal patches survive.
    Coatings have no installation buildup and retain their continuous substrate allowance.
    """
    fixture_cuts, casework_cuts, findings = _exclusion_footprints(model)
    materials = {material.tag: material for material in model.plan.library.materials}

    def coating(ref):
        material = materials.get(ref)
        return material is not None and material.coating

    def floating(ref):
        material = materials.get(ref)
        return material is not None and getattr(material, "floating", False)

    rooms = []
    for room in model.rooms:
        fixture_cut, casework_cut = fixture_cuts.get(room.storey), casework_cuts.get(room.storey)
        if fixture_cut is None and casework_cut is None:
            rooms.append(room)
            continue
        field = _geometry(room.field_finish)
        # Axis ownership includes enclosure knee walls; reveal patches can extend beyond it.
        extent = union_all([axis_polygon(room), field,
                            *(_geometry(zone.parts) for zone in room.finish_zones)])
        fixture_excluded = (intersection(fixture_cut, extent) if fixture_cut is not None
                            else Polygon())
        casework_excluded = (intersection(casework_cut, _floating_region(room, extent, floating))
                             if casework_cut is not None else Polygon())
        excluded = union_all([fixture_excluded, casework_excluded])
        if excluded.area == 0:
            rooms.append(room)
            continue

        def cut(parts, ref, all_cuts=excluded, fixture_only=fixture_excluded):
            if coating(ref):
                return parts
            return _cut_covering(parts, all_cuts if floating(ref) else fixture_only)

        parts = cut(room.field_finish, room.floor_finish)
        zones = []
        for zone in room.finish_zones:
            zone_parts = cut(zone.parts, zone.material_ref)
            zones.append(replace(zone, parts=zone_parts, area_m2=_area(zone_parts)))
        rooms.append(replace(room, field_finish=parts, field_area_m2=_area(parts),
                             finish_zones=tuple(zones),
                             floor_finish_exclusions=finish_parts(excluded.normalize())))
    model.rooms = rooms
    return findings
