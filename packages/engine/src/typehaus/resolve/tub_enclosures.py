"""Fit tub batts and lower returns once, for the viewer and both exchange formats.

Wall batts are display geometry of already billed cavity fill. Lower returns are new
construction and bill by their net horizontal area. No insulation carries the bath.
"""

from math import cos, sin

from shapely.geometry import Point, Polygon, box

from typehaus.findings import Finding, Result, Severity
from typehaus.model.placeable_symbols import place_local
from typehaus.model.placeable_symbols._kohler_underscore import (
    SEGMENTS,
    shell_half_axes_at,
)
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_members import member_box
from typehaus.resolve.model import ResolvedSolid
from typehaus.resolve.overlay import union_all

GEOMETRY_TOLERANCE_M = 1e-7
ENCLOSURE_CATEGORIES = frozenset({"tub_batt", "tub_insulation_return", "tub_mortar_bed"})


def _polygons(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == "Polygon":
        return [geometry]
    if geometry.geom_type in {"MultiPolygon", "GeometryCollection"}:
        return [part for item in geometry.geoms for part in _polygons(item)]
    return []


def _ellipse(rx, ry, center, rotation):
    from math import pi

    return Polygon(place_local([(rx*cos(2*pi*i/SEGMENTS), ry*sin(2*pi*i/SEGMENTS))
                                for i in range(SEGMENTS)], center, rotation))


def _emit(model, fixture, category, key, polygon, z0, z1, material, derived):
    for index, piece in enumerate(sorted(_polygons(polygon), key=lambda p: p.bounds)):
        if piece.area <= GEOMETRY_TOLERANCE_M**2 or z1-z0 <= GEOMETRY_TOLERANCE_M:
            continue
        model.solids.append(ResolvedSolid(
            uid=f"{fixture.uid}-{key}-{index}", tag=f"{fixture.tag}:{key}-{index}",
            storey=fixture.storey, category=category,
            outline=list(piece.exterior.coords)[:-1],
            voids=tuple(list(ring.coords)[:-1] for ring in piece.interiors),
            z0_m=z0, z1_m=z1, material=material, derived=derived,
            host_ref=fixture.tag))


def _frame(wall):
    origin, tangent, normal, run = wall_frame(wall)

    def local(point):
        delta = (point[0]-origin[0], point[1]-origin[1])
        return (sum(delta[i]*tangent[i] for i in range(2)),
                sum(delta[i]*normal[i] for i in range(2)))

    def world(station, offset):
        return tuple(origin[i]+station*tangent[i]+offset*normal[i] for i in range(2))

    return local, world, run


def _wall_batts(model, fixture, wall, panel, spec, enclosure_walls):
    local, world, _run = _frame(wall)
    cavity = [layer for layer in wall.layers if layer.is_cavity
              and layer.material_ref == spec.insulation_material_ref]
    if len(cavity) != 1:
        raise ValueError(f"{wall.tag} must have one {spec.insulation_material_ref} cavity")
    layer = cavity[0]
    coordinates = [local(point) for point in layer.polygon]
    s0, s1 = min(p[0] for p in coordinates), max(p[0] for p in coordinates)
    d0, d1 = min(p[1] for p in coordinates), max(p[1] for p in coordinates)
    if abs(d1-d0-spec.batt_thickness.meters) > GEOMETRY_TOLERANCE_M:
        raise ValueError(f"{wall.tag} cavity depth differs from the enclosure batt thickness")
    z0, z1 = layer.band(wall)
    cuts = []
    # A mitred cavity can enter the adjoining wall's plates at the corner. Subtract
    # both walls' physical framing, not just members owned by this wall.
    for member in (m for other in enclosure_walls for m in other.members):
        solid = member_box(member)
        if solid is None:
            raise ValueError(f"Unsupported enclosure framing member {member.child_key}")
        corners = solid.corners_bottom + solid.corners_top
        depths = [local(point)[1] for point in corners]
        if min(depths) >= d1-GEOMETRY_TOLERANCE_M or max(depths) <= d0+GEOMETRY_TOLERANCE_M:
            continue
        stations = [local(point)[0] for point in corners]
        elevations = [point[2] for point in corners]
        cuts.append((min(stations), min(elevations), max(stations), max(elevations)))
    # The access panel is a placed product rather than a RoughOpening. Its opening must
    # nevertheless remove the batts; clearing a whole wall-depth prism also preserves access.
    panel_points = [local(point) for point in panel.footprint]
    if panel.attachment_wall == wall.tag:
        cuts.append((min(p[0] for p in panel_points), panel.body_z0_m,
                     max(p[0] for p in panel_points), panel.body_z1_m))
    available = box(s0, z0, s1, z1).difference(union_all([box(*cut) for cut in cuts]))
    stations = sorted({s0, s1, *(max(s0, min(s1, x)) for cut in cuts for x in (cut[0], cut[2]))})
    heights = sorted({z0, z1, *(max(z0, min(z1, z)) for cut in cuts for z in (cut[1], cut[3]))})
    # Sweep exact framing boundaries, merging equal spans vertically. This produces bay
    # pieces rather than triangles and leaves plates and partial-depth blocking unobscured.
    rectangles = {}
    for bottom, top in zip(heights[:-1], heights[1:], strict=True):
        spans = []
        for left, right in zip(stations[:-1], stations[1:], strict=True):
            if right-left <= GEOMETRY_TOLERANCE_M or top-bottom <= GEOMETRY_TOLERANCE_M:
                continue
            if available.covers(Point((left+right)/2, (bottom+top)/2)):
                if spans and abs(spans[-1][1]-left) < GEOMETRY_TOLERANCE_M:
                    spans[-1] = (spans[-1][0], right)
                else:
                    spans.append((left, right))
        for left, right in spans:
            key = (left, right)
            if key in rectangles and abs(rectangles[key][-1][1]-bottom) < GEOMETRY_TOLERANCE_M:
                rectangles[key][-1][1] = top
            else:
                rectangles.setdefault(key, []).append([bottom, top])
    for index, ((left, right), bands) in enumerate(sorted(rectangles.items())):
        footprint = Polygon([world(left, d0), world(right, d0), world(right, d1), world(left, d1)])
        footprint = footprint.intersection(Polygon(layer.polygon))
        for band, (bottom, top) in enumerate(bands):
            _emit(model, fixture, "tub_batt", f"{wall.tag}-batt-{index}-{band}",
                  footprint, bottom, top, spec.insulation_material_ref, True)


def _fit_enclosure(model, fixture, spec):
    canvas = {item.tag: item for item in model.canvas_objects}
    tub, panel = canvas[fixture.tag], canvas[spec.access_panel_ref]
    walls = [model.wall(ref) for ref in spec.knee_wall_refs]
    if any(wall is None for wall in walls):
        raise ValueError("Enclosure knee wall reference is unresolved")
    deck = next((solid for solid in model.solids if solid.tag == spec.deck_ref), None)
    if deck is None:
        raise ValueError("Enclosure deck reference is unresolved")
    fixture_type = next((item for item in model.plan.library.fixture_types
                         if item.tag == fixture.type_ref), None)
    if fixture_type is None:
        raise ValueError("Tub fixture type is unresolved")
    if fixture_type.plan_symbol != "kohler-underscore-6036":
        raise ValueError("Tub enclosure shell clearance requires the Kohler Underscore symbol")
    width, depth = (dimension.meters for dimension in fixture_type.footprint)
    height = fixture_type.height.meters
    if spec.insulation_material_ref not in {m.tag for m in model.plan.library.materials}:
        raise ValueError("Enclosure insulation material reference is unresolved")
    if (any(wall.storey != tub.storey for wall in walls) or panel.storey != tub.storey
            or deck.storey != tub.storey):
        raise ValueError("Enclosure parts must share the tub's storey")
    floor_z = min(wall.z0_m for wall in walls)
    seat_z = tub.z_m
    if abs(seat_z-floor_z-spec.mortar_bed_thickness.meters) > GEOMETRY_TOLERANCE_M:
        raise ValueError("Tub support seat must meet the mortar bed on the subfloor")
    support = _ellipse(spec.support_width.meters/2, spec.support_depth.meters/2,
                       tub.position, tub.rotation_degrees)
    # This bottom-basin envelope is an explicit visualization assumption, not bearing design.
    _emit(model, tub, "tub_mortar_bed", "mortar-bed", support, floor_z,
          floor_z+spec.mortar_bed_thickness.meters,
          "mortar", True)
    strips = []
    panel_wall = None
    for wall in walls:
        _wall_batts(model, tub, wall, panel, spec, walls)
        local, world, _run = _frame(wall)
        points = [local(point) for layer in wall.depth_layers() for point in layer.polygon]
        side = 1 if local(tub.position)[1] > sum(p[1] for p in points)/len(points) else -1
        face = (max if side > 0 else min)(p[1] for p in points)
        lo, hi = min(p[0] for p in points), max(p[0] for p in points)
        far = face+side*spec.lower_return_projection.meters
        strips.append(Polygon([world(lo, face), world(hi, face), world(hi, far), world(lo, far)]))
        authored_panel = model.plan.by_tag(spec.access_panel_ref)
        attachment = getattr(getattr(authored_panel, "location", None), "attachment", None)
        if getattr(attachment, "wall_ref", None) == wall.tag:
            panel_wall = wall
    if panel_wall is None:
        raise ValueError("Access panel must be attached to one of the enclosure knee walls")
    local, world, _run = _frame(panel_wall)
    stations = [local(point)[0] for point in panel.footprint]
    offsets = [local(point)[1] for point in deck.outline]
    margin = spec.service_side_clearance.meters
    corridor = Polygon([world(s, d) for s, d in (
        (min(stations)-margin, min(offsets)), (max(stations)+margin, min(offsets)),
        (max(stations)+margin, max(offsets)), (min(stations)-margin, max(offsets)))])
    top_z = floor_z+spec.lower_return_thickness.meters
    # Subtract the largest shell section within the entire return height. This conservative
    # trim avoids hidden shell penetration without approximating a taper as many thin slices.
    fraction = (top_z-tub.z_m)/height
    rx, ry = shell_half_axes_at(fraction, width, depth)
    shell = _ellipse(rx, ry, tub.position, tub.rotation_degrees)
    clearance = spec.shell_clearance.meters
    returns = union_all(strips).intersection(Polygon(deck.outline)).difference(
        union_all([support.buffer(clearance), shell.buffer(clearance)])).difference(corridor)
    _emit(model, tub, "tub_insulation_return", "lower-return", returns, floor_z, top_z,
          spec.insulation_material_ref, False)


def resolve_tub_enclosures(model):
    """Invalid referenced construction produces a finding and no partial enclosure."""
    findings = []
    for storey in model.plan.storeys:
        for fixture in model.plan.storey_elements(storey.tag):
            spec = getattr(fixture, "tub_enclosure", None)
            if spec is None:
                continue
            start = len(model.solids)
            try:
                _fit_enclosure(model, fixture, spec)
            except (KeyError, ValueError) as error:
                del model.solids[start:]
                findings.append(Finding(check_id="integrity.tub_enclosure", severity=Severity.ERROR,
                                        result=Result.FAIL, message=str(error),
                                        element_tags=(fixture.tag,)))
    return findings
