"""Turn radial profiles about local +Z with smooth or crisp shading."""

import math

from typehaus.model.placeable_symbols._frame import Part


def turned_profile(profile: tuple[tuple[float, float], ...], radius: float,
                   thickness: float, color: str, *, segments: int,
                   closed: bool = False, smooth: bool = False) -> Part:
    """Turn a meridian; smooth the housing while keeping hardware edges crisp."""
    positions, normals, triangles = [], [], []
    edges = tuple(zip(profile if closed else profile[:-1],
                      (*profile[1:], profile[0]) if closed else profile[1:], strict=True))
    edge_normals = []
    for (r0, a0), (r1, a1) in edges:
        radial_delta, axial_delta = (r1 - r0) * radius, (a1 - a0) * thickness
        length = math.hypot(radial_delta, axial_delta)
        edge_normals.append((axial_delta / length, -radial_delta / length))
    for edge_index, ((radius0, axial0), (radius1, axial1)) in enumerate(edges):
        radius0, radius1 = radius0 * radius, radius1 * radius
        axial0, axial1 = axial0 * thickness, axial1 * thickness
        base = len(positions)
        for endpoint, (ring_radius, axial) in enumerate(((radius0, axial0), (radius1, axial1))):
            radial_normal, axial_normal = edge_normals[edge_index]
            neighbor = edge_index + (1 if endpoint else -1)
            if smooth and 0 <= neighbor < len(edge_normals):
                radial_normal += edge_normals[neighbor][0]
                axial_normal += edge_normals[neighbor][1]
                length = math.hypot(radial_normal, axial_normal)
                radial_normal, axial_normal = radial_normal / length, axial_normal / length
            for segment in range(segments):
                angle = math.tau * segment / segments
                cosine, sine = math.cos(angle), math.sin(angle)
                positions.append((ring_radius * cosine, ring_radius * sine, axial))
                normals.append((radial_normal * cosine, radial_normal * sine, axial_normal))
        for segment in range(segments):
            following = (segment + 1) % segments
            a, b = base + segment, base + following
            c, d = a + segments, b + segments
            if radius0 > 0:
                triangles.append((a, b, c))
            if radius1 > 0:
                triangles.append((b, d, c))
    low = tuple(min(point[axis] for point in positions) for axis in range(3))
    high = tuple(max(point[axis] for point in positions) for axis in range(3))
    return {"center": tuple((a + b) / 2 for a, b in zip(low, high, strict=True)),
            "size": tuple(b - a for a, b in zip(low, high, strict=True)),
            "color": color, "points": (), "shape": "mesh",
            "mesh": {"positions": tuple(positions), "normals": tuple(normals),
                     "triangles": tuple(triangles)}}
