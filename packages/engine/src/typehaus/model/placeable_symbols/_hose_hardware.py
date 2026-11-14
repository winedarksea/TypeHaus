"""Open hose-thread mouths with annular end faces, shared by the nozzle and breaker."""

import math

from typehaus.model.placeable_symbols._frame import Part
from typehaus.model.placeable_symbols._round_hardware import ROUND_SEGMENTS
from typehaus.quantities import M_PER_IN


def hose_thread(center: tuple[float, float, float], diameter: float, bore: float,
                length: float, *, color: str = "brass") -> Part:
    """Inch inputs; a hollow barrel at the nominal thread OD; the thread helix is omitted."""
    radius, inner_radius = diameter * M_PER_IN / 2, bore * M_PER_IN / 2
    height = length * M_PER_IN
    origin = tuple(v * M_PER_IN for v in center)
    positions, normals, triangles = [], [], []
    # Separate wall and cap vertices retain smooth walls and flat annular end faces.
    for inner in (False, True):
        base = len(positions)
        r = inner_radius if inner else radius
        for sign in (-1, 1):
            for segment in range(ROUND_SEGMENTS):
                angle = math.tau * segment / ROUND_SEGMENTS
                x, y = math.cos(angle), math.sin(angle)
                positions.append((origin[0] + r * x, origin[1] + r * y,
                                  origin[2] + sign * height / 2))
                normals.append(((-x if inner else x), (-y if inner else y), 0.0))
        for i in range(ROUND_SEGMENTS):
            j = (i + 1) % ROUND_SEGMENTS
            a, b, c, d = base + i, base + j, base + i + ROUND_SEGMENTS, base + j + ROUND_SEGMENTS
            triangles.extend(((a, c, b), (b, c, d)) if inner else ((a, b, c), (b, d, c)))
    for sign in (-1, 1):
        base = len(positions)
        for r in (radius, inner_radius):
            for segment in range(ROUND_SEGMENTS):
                angle = math.tau * segment / ROUND_SEGMENTS
                positions.append((origin[0] + r * math.cos(angle),
                                  origin[1] + r * math.sin(angle), origin[2] + sign * height / 2))
                normals.append((0.0, 0.0, float(sign)))
        for i in range(ROUND_SEGMENTS):
            j = (i + 1) % ROUND_SEGMENTS
            a, b, c, d = base + i, base + j, base + i + ROUND_SEGMENTS, base + j + ROUND_SEGMENTS
            triangles.extend(((a, c, b), (b, c, d)) if sign < 0 else ((a, b, c), (b, d, c)))
    return {"center": origin, "size": (radius * 2, radius * 2, height),
            "color": color, "shape": "mesh", "points": (),
            "mesh": {"positions": tuple(positions), "normals": tuple(normals),
                     "triangles": tuple(triangles)}}
