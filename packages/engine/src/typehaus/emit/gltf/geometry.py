"""glTF's own geometry concern: the axis swizzle.

The plan-frame math lives in ``resolve/geometry_prims.py``, shared with the IR producer. The
names are re-exported here because the emitter modules import them from this path.
"""

from __future__ import annotations

from typehaus.resolve.geometry_prims import (  # noqa: F401 - re-exported for the emitters
    _ARCH_SOFFIT_CHORD_TOLERANCE_M,
    _ARCH_SOFFIT_MAX_SEGMENTS,
    _ARCH_SOFFIT_MIN_SEGMENTS,
    _COLLINEAR_VERTEX_TOLERANCE_M,
    Vec3,
    _arch_soffit_sample,
    _arch_soffit_segment_count,
    _dedupe_ring,
    _lerp,
    _ring_signed_area,
    _slice,
    _thin_rect_edges,
    _without_collinear_vertices,
    arch_soffit_circle,
)


def _to_gltf(x: float, y: float, z: float) -> Vec3:
    """Plan frame (x, y plan / z up) → glTF's y-up, right-handed frame."""
    return (x, z, -y)
