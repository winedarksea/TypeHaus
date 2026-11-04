"""One station layout for guard posts, mounting faces and backing locations."""

import math
from dataclasses import dataclass

from typehaus.resolve.geometry import Vec
from typehaus.resolve.railings.guard_line import offset_path

LAYOUT_TOLERANCE_M = 1e-8


@dataclass(frozen=True)
class MountingFace:
    origin: Vec
    tangent: Vec
    outward: Vec


@dataclass(frozen=True)
class FasciaStation:
    post: Vec
    edge: Vec
    variant: str
    faces: tuple[MountingFace, ...]


def fascia_stations(path: list[Vec], spacing_m: float, face_offset_m: float,
                    post_offset_m: float) -> list[FasciaStation]:
    """Right-hand outboard, with the same evenly divided offset bays as guard_line."""
    if len(path) < 2:
        return []
    if spacing_m <= 0:
        raise ValueError("fascia post spacing must be positive")
    shifted = offset_path(path, face_offset_m + post_offset_m)
    tangents = []
    for a, b in zip(path[:-1], path[1:], strict=True):
        run = math.dist(a, b)
        if run <= LAYOUT_TOLERANCE_M:
            raise ValueError("fascia path contains a repeated point")
        tangents.append(((b[0] - a[0]) / run, (b[1] - a[1]) / run))

    def station(post, segment, fraction, corner=False):
        indices = [segment]
        variant = "straight"
        if corner and segment:
            incoming, outgoing = tangents[segment - 1], tangents[segment]
            dot = sum(a * b for a, b in zip(incoming, outgoing, strict=True))
            cross = incoming[0] * outgoing[1] - incoming[1] * outgoing[0]
            if abs(cross) > LAYOUT_TOLERANCE_M:
                if abs(dot) > LAYOUT_TOLERANCE_M:
                    raise ValueError("fascia corner brackets require a 90 degree turn")
                indices = [segment - 1, segment]
                variant = "outside_corner" if cross > 0 else "inside_corner"
        edge = tuple(path[segment][i] + fraction * (path[segment + 1][i]
                     - path[segment][i]) for i in range(2))
        faces = []
        for index in indices:
            tangent = tangents[index]
            outward = (tangent[1], -tangent[0])
            origin = tuple(post[i] - outward[i] * post_offset_m for i in range(2))
            faces.append(MountingFace(origin, tangent, outward))
        return FasciaStation(post, edge, variant, tuple(faces))

    result = []
    for index, (a, b) in enumerate(zip(shifted[:-1], shifted[1:], strict=True)):
        bays = max(1, math.ceil(math.dist(a, b) / spacing_m - 1e-9))
        for number in range(bays):
            fraction = number / bays
            post = tuple(a[i] + fraction * (b[i] - a[i]) for i in range(2))
            result.append(station(post, index, fraction, corner=number == 0))
    result.append(station(shifted[-1], len(path) - 2, 1.0))
    return result


def fascia_deck(model, railing):
    """Explicit host association; another nearby deck is never a substitute."""
    fascia = model.plan.by_tag(railing.fascia_ref) if railing.fascia_ref else None
    from typehaus.model.trim import Fascia

    if not isinstance(fascia, Fascia):
        return None
    return next((floor for floor in model.floors if floor.tag == fascia.host_ref), None)
