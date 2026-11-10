"""Local sauna valve recesses; surrounding service runs remain behind the finish."""

from dataclasses import replace

from shapely.geometry import Polygon

from typehaus.model.placeable_symbols import place_local
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.layer_pockets import subtract_layer_region


def resolve_shower_pockets(plan, model):
    types = {product.tag: product for product in plan.library.fixture_types}
    for fixture in model.canvas_objects:
        product = types.get(fixture.type_ref)
        spec = product.shower_assembly if product else None
        pocket = spec.valve_pocket if spec else None
        if pocket is None:
            continue
        wall = next(w for w in model.walls if w.tag == pocket.wall_ref)
        half = pocket.width.meters / 2
        # The recess reaches from the substrate back through the foil to the stringer.
        points = [spec.point(lateral=lateral, depth=depth)[:2]
                  for lateral, depth in ((-half, 0), (half, 0),
                                         (half, spec.valve_dimensions.stringer_setback.meters),
                                         (-half, spec.valve_dimensions.stringer_setback.meters))]
        cutter = Polygon(place_local(points, fixture.position, fixture.rotation_degrees))
        z = fixture.z_m + spec.valve_face[2].meters
        bottom, top = z - pocket.height.meters / 2, z + pocket.height.meters / 2
        layers = tuple(region for layer in wall.layers for region in (
            subtract_layer_region(wall, layer, cutter, bottom, top, "valve-pocket")
            if layer.name in pocket.layer_names else (layer,)))
        # Horizontal liner strapping is cut back to the pocket's side supports.
        origin, tangent, _, _ = wall_frame(wall)
        def station(point, origin=origin, tangent=tangent):
            return sum((a - b) * c for a, b, c in zip(point, origin, tangent, strict=True))
        limits = [station(point) for point in cutter.exterior.coords]
        low, high = min(limits), max(limits)
        members = []
        for member in wall.members:
            if (not member.child_key.startswith("strapping-liner-furring")
                    or member.z1_m <= bottom or member.z0_m >= top):
                members.append(member)
                continue
            start, end = station(member.p0), station(member.p1)
            if start > end:
                start, end = end, start
                member = replace(member, p0=member.p1, p1=member.p0)
            for index, (a, b) in enumerate(((start, min(end, low)), (max(start, high), end))):
                if b - a <= 1e-8:
                    continue
                def at(value, start=start, end=end, member=member):
                    t = (value - start) / (end - start)
                    return tuple(x + (y - x) * t for x, y in zip(member.p0, member.p1, strict=True))
                members.append(replace(member, child_key=f"{member.child_key}-pocket-{index}",
                                       p0=at(a), p1=at(b), length_m=b - a))
        model.walls[model.walls.index(wall)] = replace(wall, layers=layers, members=members)
