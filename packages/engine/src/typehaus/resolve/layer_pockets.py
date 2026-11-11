"""Cut a rectangular service region from a layer, retaining its quantity extents."""

from dataclasses import replace

from shapely import get_coordinates
from shapely.geometry import Polygon

from typehaus.resolve.geometry import wall_frame


def subtract_layer_region(wall, layer, cutter, bottom, top, name):
    shape = Polygon(layer.polygon)
    overlap = shape.intersection(cutter)
    z0, z1 = layer.band(wall)
    if overlap.area < 1e-10 or top <= z0 or bottom >= z1:
        return (layer,)
    origin, tangent, normal, _ = wall_frame(wall)
    def region_layer(region, index, lower=z0, upper=z1):
        coordinates = []
        for x, y in list(region.exterior.coords)[:-1]:  # drop clip slivers (zero-length edges)
            if not coordinates or abs(x - coordinates[-1][0]) + abs(y - coordinates[-1][1]) > 1e-9:
                coordinates.append((x, y))
        if len(coordinates) > 1 and abs(coordinates[0][0] - coordinates[-1][0]) \
                + abs(coordinates[0][1] - coordinates[-1][1]) <= 1e-9:
            coordinates.pop()
        stations = [(x - origin[0]) * tangent[0] + (y - origin[1]) * tangent[1]
                    for x, y in coordinates]
        offsets = [(x - origin[0]) * normal[0] + (y - origin[1]) * normal[1]
                   for x, y in coordinates]
        return replace(layer, thickness_m=max(offsets) - min(offsets),
                       name=f"{layer.name}-{name}-{index}", polygon=coordinates,
                       z0_m=None if abs(lower-wall.z0_m) < 1e-9 else lower,
                       z1_m=None if abs(upper-wall.z1_m) < 1e-9 else upper,
                       source_layer_name=layer.source_layer_name or layer.name,
                       band_spec=None, slot=layer.slot or f"service-region:{layer.name}",
                       run_span_m=(min(stations), max(stations)))
    remainder = shape.difference(cutter)
    def station(point):
        return sum((a-b)*c for a, b, c in zip(point, origin, tangent, strict=True))
    lo, hi = min(map(station, shape.exterior.coords)), max(map(station, shape.exterior.coords))
    # ``cutter`` may be multi-part (several tees on one wall): split at every vertex.
    cuts = sorted({lo, hi, *(max(lo, min(hi, station(p)))
                             for p in get_coordinates(cutter).tolist())})
    offsets = [(x-origin[0])*normal[0] + (y-origin[1])*normal[1]
               for x, y in shape.exterior.coords]
    regions = []
    for start, end in zip(cuts, cuts[1:], strict=False):
        def point(u, v):
            return origin[0]+tangent[0]*u+normal[0]*v, origin[1]+tangent[1]*u+normal[1]*v
        cell = Polygon([point(start, min(offsets)), point(end, min(offsets)),
                        point(end, max(offsets)), point(start, max(offsets))])
        region = remainder.intersection(cell)
        if not region.is_empty and region.area > 1e-10:
            regions.extend(piece for piece in (region.geoms if hasattr(region, "geoms")
                                              else (region,))
                           if piece.geom_type == "Polygon" and piece.area > 1e-10)
    layers = [region_layer(region, index) for index, region in enumerate(regions)]
    for suffix, lower, upper in (("below", z0, max(z0, bottom)),
                                 ("above", min(z1, top), z1)):
        if upper - lower > 1e-8:
            parts = [g for g in getattr(overlap, "geoms", (overlap,))
                     if g.geom_type == "Polygon" and g.area > 1e-10]
            layers.extend(region_layer(part, suffix if len(parts) == 1 else f"{suffix}-{i}",
                                       lower, upper) for i, part in enumerate(parts))
    return tuple(layers)
