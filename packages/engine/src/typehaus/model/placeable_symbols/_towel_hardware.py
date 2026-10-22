"""Simplified Align hardware: round bar posts and a hook with a recessed neck and lip."""

import math

from typehaus.model.placeable_symbols._align_hardware import align_bar
from typehaus.model.placeable_symbols._frame import Part, Stroke, rect
from typehaus.model.placeable_symbols._mesh import mesh_part
from typehaus.model.placeable_symbols._round_hardware import ROUND_SEGMENTS, round_cylinder

_HOOK_REAR_LENGTH_SHARE = 0.32
_HOOK_LIP_LENGTH_SHARE = 0.18
_HOOK_SCOOP_DEPTH_SHARE = 0.45
_HOOK_SCOOP_SEGMENTS = 12


def towel_bar(width: float, depth: float, height: float, *, color: str = "brushed-nickel"
              ) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    return align_bar(width, depth, height, width_post_ratio=1.34 / 9.17,
                     depth_post_ratio=1.34 / 3.33, color=color)



def _scooped_seat(radius: float, length: float, center_y: float, color: str) -> Part:
    """Keep the barrel's underside while scooping the upper surface between its ends."""
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for course in range(_HOOK_SCOOP_SEGMENTS + 1):
        fraction = course / _HOOK_SCOOP_SEGMENTS
        y = center_y + (fraction - 0.5) * length
        top = 2 * radius * (1 - _HOOK_SCOOP_DEPTH_SHARE * math.sin(math.pi * fraction) ** 2)
        for segment in range(ROUND_SEGMENTS):
            angle = math.tau * segment / ROUND_SEGMENTS
            vertices.append((radius * math.sin(angle), y,
                             min(radius + radius * math.cos(angle), top)))
    for course in range(_HOOK_SCOOP_SEGMENTS):
        for segment in range(ROUND_SEGMENTS):
            following = (segment + 1) % ROUND_SEGMENTS
            a, b = course * ROUND_SEGMENTS + segment, course * ROUND_SEGMENTS + following
            c, d = a + ROUND_SEGMENTS, b + ROUND_SEGMENTS
            triangles.extend(((a, b, c), (b, d, c)))
    for course, sign in ((0, -1), (_HOOK_SCOOP_SEGMENTS, 1)):
        center = len(vertices)
        vertices.append((0, center_y + sign * length / 2, radius))
        for segment in range(ROUND_SEGMENTS):
            a = course * ROUND_SEGMENTS + segment
            b = course * ROUND_SEGMENTS + (segment + 1) % ROUND_SEGMENTS
            triangles.append((center, b, a) if sign < 0 else (center, a, b))
    return mesh_part(vertices, triangles, color)


def towel_hook(width: float, depth: float, height: float, *, color: str = "brushed-nickel"
               ) -> tuple[tuple[Stroke, ...], tuple[Part, ...]]:
    radius = min(width, height) / 2
    rear = depth * _HOOK_REAR_LENGTH_SHARE
    lip = depth * _HOOK_LIP_LENGTH_SHARE
    neck = depth - rear - lip
    # The concave seat represents the product's notch, with a raised round
    # nose to retain fabric. All three solids stay inside the manufacturer's envelope.
    parts = (
        round_cylinder((0, depth / 2 - rear / 2, radius), radius, rear, axis=1, color=color),
        _scooped_seat(radius, neck, -depth / 2 + lip + neck / 2, color),
        round_cylinder((0, -depth / 2 + lip / 2, radius), radius, lip, axis=1, color=color),
    )
    return (rect(0, 0, width, depth, fill="metal"),), parts
