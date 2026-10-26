"""Dimensioned metal panel sections and shared sheet-fold construction."""

import math
from dataclasses import dataclass

from typehaus.resolve.surface_clipping import CLIP_TOLERANCE_M


@dataclass(frozen=True)
class MetalSkinProfile:
    key: str
    pitch_m: float
    depth_m: float
    sheet_thickness_m: float
    section_points_m: tuple[tuple[float, float], ...]
    crown_width_m: float | None = None


INCH_M = 0.0254
SHEET_24_GA_M = 0.00060706  # nominal 24 ga base steel, .0239 inch
PROFILE_DEPTH_TOLERANCE_M = 1e-6
SECTION_MITER_TOLERANCE = 1e-8
MAX_SECTION_MITER_RATIO = 4.0
CORRUGATED_SEGMENTS_PER_WAVE = 24


def _board_batten_profile() -> MetalSkinProfile:
    pitch, depth, crown, sheet = 0.3048, 0.01905, 0.0508, SHEET_24_GA_M
    return MetalSkinProfile(
        "board-and-batten",
        pitch,
        depth,
        sheet,
        (
            (-pitch / 2, sheet),
            (-crown / 2, sheet),
            (-crown / 2, depth),
            (crown / 2, depth),
            (crown / 2, sheet),
            (pitch / 2, sheet),
        ),
        crown,
    )


BBD75_PROFILE = _board_batten_profile()


def _pbr_section() -> tuple[tuple[float, float], ...]:
    """Trace the scaled PBR cross-section drawing, including its two minor ribs per pan."""
    pitch, depth, sheet = 12 * INCH_M, 1.25 * INCH_M, SHEET_24_GA_M
    # The current profile sheet dimensions the 12 inch major-rib rhythm and 1-1/4 inch
    # height. Crown/base widths and the minor ribs' roughly 1/4 inch rise are traced
    # proportionally from its section drawing; those smaller features have no callouts.
    features = []
    for center in (-4 * INCH_M, 0.0, 4 * INCH_M):
        major = center == 0.0
        base_half = (1.5 if major else 0.5) * INCH_M
        crown_half = (0.5 if major else 0.1875) * INCH_M
        height = depth if major else sheet + 0.25 * INCH_M
        features.extend(
            (
                (center - base_half, sheet),
                (center - crown_half, height),
                (center + crown_half, height),
                (center + base_half, sheet),
            )
        )
    points = [(-pitch / 2, sheet), *features, (pitch / 2, sheet)]
    return tuple(sorted(points))


PBR_PROFILE = MetalSkinProfile(
    "ribbed-panel",
    12 * INCH_M,
    1.25 * INCH_M,
    SHEET_24_GA_M,
    _pbr_section(),
)


def _corrugated_section() -> tuple[tuple[float, float], ...]:
    """Sample the manufacturer's sinusoidal 7/8 inch wall profile at a named resolution."""
    pitch, depth, sheet = (8 / 3 * INCH_M, 7 / 8 * INCH_M, SHEET_24_GA_M)
    return tuple(
        (
            -pitch / 2 + pitch * index / CORRUGATED_SEGMENTS_PER_WAVE,
            sheet
            + (depth - sheet)
            * (1 + math.cos(2 * math.pi * (index / CORRUGATED_SEGMENTS_PER_WAVE - 0.5)))
            / 2,
        )
        for index in range(CORRUGATED_SEGMENTS_PER_WAVE + 1)
    )


CORRUGATED_PROFILE = MetalSkinProfile(
    "corrugated",
    8 / 3 * INCH_M,
    7 / 8 * INCH_M,
    SHEET_24_GA_M,
    _corrugated_section(),
)


def _image_ii_section():
    # Image II Striated brochure MS/0426: 16 inch coverage, 1 inch rib.
    # Seam width and shallow striations have no callouts; traced proportionally.
    # Slight batter keeps the sheet offset's fold miters bounded.
    sheet = SHEET_24_GA_M
    points = [(0.0, INCH_M), (0.1875 * INCH_M, INCH_M), (0.375 * INCH_M, sheet)]
    for center in (4.0, 8.0, 12.0):
        points.extend(
            (
                ((center - 0.375) * INCH_M, sheet),
                ((center - 0.125) * INCH_M, sheet + INCH_M / 16),
                ((center + 0.125) * INCH_M, sheet + INCH_M / 16),
                ((center + 0.375) * INCH_M, sheet),
            )
        )
    points.extend(((15.625 * INCH_M, sheet), (15.8125 * INCH_M, INCH_M), (16 * INCH_M, INCH_M)))
    return tuple(points)


IMAGE_II_16_PROFILE = MetalSkinProfile(
    "standing-seam",
    16 * INCH_M,
    INCH_M,
    SHEET_24_GA_M,
    _image_ii_section(),
    0.375 * INCH_M,
)


PANEL_PROFILES = {
    profile.key: profile
    for profile in (BBD75_PROFILE, PBR_PROFILE, CORRUGATED_PROFILE, IMAGE_II_16_PROFILE)
}
PROFILE_DEPTH_LABELS = {
    "standing-seam": "1 inch",
    "board-and-batten": "3/4 inch",
    "ribbed-panel": "1-1/4 inch",
    "corrugated": "7/8 inch",
}


def _section_ribbon_faces(a, b, inner_a, inner_b, z0, z1):
    """The two sheet faces for one straight section span.

    Adjacent section spans share their fold edge. Closing a prism around every span
    duplicates those internal edges throughout the export; clipping adds the small cut faces
    where an opening, rake, or footprint actually exposes the sheet thickness.
    """
    ao, bo, ai, bi = a, b, inner_a, inner_b
    a0, a1 = (*ao, z0), (*ao, z1)
    b0, b1 = (*bo, z0), (*bo, z1)
    ia0, ia1 = (*ai, z0), (*ai, z1)
    ib0, ib1 = (*bi, z0), (*bi, z1)
    return [
        [a0, a1, b1, b0],  # exposed face
        [ia0, ib0, ib1, ia1],  # reverse face
    ]


def _inset_section(points, thickness):
    segment_normals = []
    for a, b in zip(points, points[1:], strict=False):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length <= CLIP_TOLERANCE_M:
            raise ValueError("Metal panel profile contains a zero-length section")
        segment_normals.append((-dy / length, dx / length))
    inset = []
    for index, point in enumerate(points):
        if index == 0:
            normal = segment_normals[0]
        elif index == len(points) - 1:
            normal = segment_normals[-1]
        else:
            before, after = segment_normals[index - 1], segment_normals[index]
            total = (before[0] + after[0], before[1] + after[1])
            magnitude = math.hypot(*total)
            if magnitude <= SECTION_MITER_TOLERANCE:
                normal = after
            else:
                bisector = (total[0] / magnitude, total[1] / magnitude)
                projection = bisector[0] * after[0] + bisector[1] * after[1]
                miter_ratio = min(
                    MAX_SECTION_MITER_RATIO, 1 / max(projection, SECTION_MITER_TOLERANCE)
                )
                normal = (bisector[0] * miter_ratio, bisector[1] * miter_ratio)
        inset.append((point[0] - thickness * normal[0], point[1] - thickness * normal[1]))
    return inset
