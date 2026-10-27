"""Ventilated beam-tail covers and separate, canopy-supported roof aprons."""

import math

from typehaus.model.enums import LayerFunction
from typehaus.resolve.flashing_solids import flashing_solid
from typehaus.resolve.geometry_ir import GBox
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.roof_geometry import roof_height_at, roof_slope_factor
from typehaus.resolve.roof_layer_setbacks import above_structure_layers
from typehaus.resolve.sheet_geometry import combine_sheets, polygon_sheet, sheet_between


def resolve_beam_hood(model, element, storey):
    """Keep the hood outside the truss bearing; lap a separate apron over its upstand.

    Coordinates are local to the straight run: s points towards shelter, d across
    the beam. No cutouts or automatic obstacle removal can conceal a bad fit.
    """
    section = element.section
    if element.vertical or len(element.path) != 2 or not element.host_ref:
        raise ValueError(f"{element.tag}: hood requires a straight plan run and beam host")
    beam = next((s for s in model.solids
                 if s.tag == element.host_ref and s.category == "beam"), None)
    roof = next((r for r in model.roofs if r.tag == section.roof_ref), None)
    if beam is None or roof is None:
        raise ValueError(f"{element.tag}: hood beam or roof host is missing")
    if element.host_ref not in model.plan.by_tag(roof.tag).bearing_refs:
        raise ValueError(f"{element.tag}: apron roof must bear on the hood's beam")
    a, b = (p.xy_m for p in element.path)
    length = math.dist(a, b)
    if length <= 0:
        raise ValueError(f"{element.tag}: hood run must have positive length")
    along = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
    across = (-along[1], along[0])
    half = element.thickness.meters / 2
    crown = element.top_elevation.meters
    edge = crown - half * section.slope
    gap, gauge = section.air_gap.meters, section.sheet_thickness.meters

    def project(p, axis):
        return sum((p[i] - a[i]) * axis[i] for i in range(2))

    def point(s, d, z):
        return (a[0] + along[0] * s + across[0] * d,
                a[1] + along[1] * s + across[1] * d, z)

    wood_start = min(project(p, along) for p in beam.outline)
    wood_half = max(abs(project(p, across)) for p in beam.outline)
    if min(edge - beam.z1_m, half - wood_half, wood_start) < gap - 1e-8:
        raise ValueError(f"{element.tag}: hood does not maintain its wood ventilation gap")
    roof_edge = min(project(p, along) for p in roof.footprint)
    if roof_edge <= length or section.apron_gap.meters >= length:
        raise ValueError(f"{element.tag}: hood must stop before its roof bearing")
    for member in roof.members:
        if member.category != "roof_truss":
            continue
        bounds = member_solid(member)
        if not isinstance(bounds, GBox):
            raise ValueError(f"{element.tag}: unsupported truss envelope for hood clearance")
        face = min(project(p, along) for p in bounds.corners_bottom)
        if face - length - gauge < gap - 1e-8:
            raise ValueError(f"{element.tag}: hood upstand is too close to a roof truss")

    run = (*[value * length for value in along], 0.0)
    hood = []
    for sign in (-1, 1):
        rim = sign * half
        hood.append(sheet_between(point(0, 0, crown), point(0, rim, edge), run, gauge,
                                  normal_hint=(0, 0, 1)))
        hood.append(sheet_between(point(0, rim, edge),
                                  point(0, rim, edge - section.drip.meters), run, gauge,
                                  normal_hint=(*[sign * v for v in across], 0)))
        hood.append(sheet_between(point(0, rim, edge - section.drip.meters),
                                  point(0, rim + sign * section.hem.meters,
                                        edge - section.drip.meters), run, gauge,
                                  normal_hint=(0, 0, 1)))
        # A ventilated south return, with a projecting drip instead of a closed bottom.
        hood.append(polygon_sheet([[(0, crown), (rim, edge),
                                    (rim, edge - section.end_drop.meters),
                                    (0, crown - section.end_drop.meters)]],
                                  lambda d, z: point(0, d, z),
                                  (*[-value * gauge for value in along], 0)))
        hood.append(sheet_between(point(0, 0, crown - section.end_drop.meters),
                                  point(0, rim, edge - section.end_drop.meters),
                                  (*[-v * section.end_hem.meters for v in along], 0),
                                  gauge, normal_hint=(0, 0, 1)))
        hood.append(sheet_between(point(length, 0, crown), point(length, rim, edge),
                                  (0, 0, section.upstand.meters), gauge,
                                  normal_hint=(*along, 0)))

    hood_solid = flashing_solid(
        uid=f"{element.uid}-hood", tag=element.tag, storey=storey,
        category="beam_cap", mesh=combine_sheets(hood), material=element.material,
        host_ref=element.host_ref)

    # The lap lies on the roof deck beneath its water-control layer. It remains
    # attached to this roof only; no part is resolved relative to the house wall.
    layers = above_structure_layers(model.plan.library.resolve_assembly(roof.assembly))
    deck = next((layer for layer in layers if layer.function is LayerFunction.SHEATHING), None)
    if deck is None:
        raise ValueError(f"{element.tag}: roof apron requires a sheathed roof")
    deck_offset = deck.thickness.meters * roof_slope_factor(roof)
    front = length - section.apron_gap.meters
    back = roof_edge + section.apron_lap.meters

    def roof_top(d):
        return roof_height_at(roof, point(roof_edge, d, 0)[:2]) + deck_offset

    if min(roof_top(-half), roof_top(half)) <= crown + section.upstand.meters:
        raise ValueError(f"{element.tag}: apron has no clearance above the hood upstand")
    apron = []
    for left, right in ((-half, 0), (0, half)):
        def bottom(d):
            return crown - abs(d) * section.slope + section.apron_drip_clearance.meters

        apron.append(polygon_sheet([[(left, bottom(left)), (right, bottom(right)),
                                     (right, roof_top(right)), (left, roof_top(left))]],
                                   lambda d, z: point(front, d, z),
                                   (*[-v * gauge for v in along], 0)))
        apron.append(sheet_between(point(front, left, roof_top(left)),
                                   point(front, right, roof_top(right)),
                                   (*[v * (back - front) for v in along], 0),
                                   gauge, normal_hint=(0, 0, 1)))
    apron_solid = flashing_solid(
        uid=f"{element.uid}-apron", tag=f"{element.tag}-APRON", storey=storey,
        category="beam_cap", mesh=combine_sheets(apron), material=element.material,
        host_ref=section.roof_ref)
    model.solids.extend((hood_solid, apron_solid))
