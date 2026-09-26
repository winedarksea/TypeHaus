"""Door products beyond the four-piece frame: the concealed (trimless) frame and lever sets.

Split from ``geometry_openings.py``, which calls in here with its own ``box`` builder so every
solid stays in the same wall frame: ``along`` the axis from the opening centre, ``normal``
offset along the wall's LEFT normal, and an elevation. Mirrored by hand in
``ui/src/three/builders/doorProducts.ts`` — change both.

Handing (``ResolvedOpening.flip_hinge`` / ``flip_swing``): unflipped, the leaf hangs on the
END-node jamb and sweeps toward the left normal, exactly as ``pipeline._door_swing_clearance``.
"""

from __future__ import annotations

from collections.abc import Callable

from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_ir import GPart, GPrism
from typehaus.resolve.model import ResolvedWall

# (width along, height, thickness across, along, elevation, normal offset) -> box
BoxFn = Callable[..., GPrism]

# --- concealed frame (EzyJamb-type: flush on the pull side, rebated on the push side) ------
_CONCEALED_JAMB_M = 0.016        # aluminium liner + plaster return, each jamb and the head
_SHADOW_GAP_M = 0.003            # 1/8" reveal between leaf edge and liner
_CONCEALED_STOP_M = 0.013        # rebate lip projecting past the liner; the leaf closes on it
_SHADOW_STRIP_DEPTH_M = 0.006    # dark face on the stop, seen only through the reveal
_CONCEALED_UNDERCUT_M = 0.019    # leaf bottom above the wall base: finish floor + clearance
_CONCEALED_LEAF_THICKNESS_M = 0.045

# --- lever set (square rose, lever returning toward the hinge) ----------------------------
_LEVER_HEIGHT_M = 0.914          # 36" to the lever centre above the leaf's floor
_LEVER_BACKSET_M = 0.060         # 2 3/8" from the latch edge
_ROSE_SIZE_M = 0.064             # 2 1/2" square rose
_ROSE_PROUD_M = 0.010            # rose thickness off the leaf face
_LEVER_STANDOFF_M = 0.055        # leaf face to the lever's centreline
_LEVER_LENGTH_M = 0.120          # 4 3/4" lever
_LEVER_SECTION_M = 0.016         # 5/8" bar
_LEVER_NECK_M = 0.014            # spindle neck from rose to lever

_CONCEALED_FRAME_KEY = "door_leaf"   # a primed-and-painted liner reads as the wall's white
_SHADOW_GAP_KEY = "shadow_gap"
_HARDWARE_KEY = "door_hardware"


def finish_faces(wall: ResolvedWall) -> tuple[float, float] | None:
    """``(low, high)`` normal offsets of the wall's two outermost faces, or None."""
    (x0, y0), _tangent, (nx, ny), axis_length = wall_frame(wall)
    layers = wall.depth_layers()
    if axis_length <= 1e-9 or not layers:
        return None
    offsets = [(px - x0) * nx + (py - y0) * ny for layer in layers for px, py in layer.polygon]
    return (min(offsets), max(offsets)) if offsets else None


def handing(opening) -> tuple[float, float]:
    """``(hinge_sign, swing_sign)``: hinge on the +along jamb and swing toward +normal at +1."""
    hinge = -1.0 if getattr(opening, "flip_hinge", False) else 1.0
    swing = -1.0 if getattr(opening, "flip_swing", False) else 1.0
    return hinge, swing


def concealed_leaf(faces: tuple[float, float], swing_sign: float, width: float,
                   base_z: float, height: float) -> tuple[float, float, float, float, float]:
    """``(leaf_width, leaf_height, bottom_z, flush_face, back_face)`` of a concealed-frame leaf."""
    flush = faces[1] if swing_sign > 0 else faces[0]
    back = flush - swing_sign * _CONCEALED_LEAF_THICKNESS_M
    leaf_width = width - 2.0 * (_CONCEALED_JAMB_M + _SHADOW_GAP_M)
    bottom = base_z + _CONCEALED_UNDERCUT_M
    top = base_z + height - _CONCEALED_JAMB_M - _SHADOW_GAP_M
    return leaf_width, top - bottom, bottom, flush, back


def concealed_frame_parts(box: BoxFn, faces: tuple[float, float], swing_sign: float,
                          width: float, base_z: float, height: float) -> list[GPart]:
    """Liner, leaf, stop and shadow strips of a flush concealed-frame door.

    The liner lines the whole jamb depth and stops flush with both finish faces; the leaf is
    coplanar with the face it swings toward. Behind it the stop steps into the opening, so
    the push side shows the frame depth and the pull side only the reveal.
    """
    lo, hi = faces
    depth, mid = hi - lo, (hi + lo) / 2.0
    j, g, p = _CONCEALED_JAMB_M, _SHADOW_GAP_M, _CONCEALED_STOP_M
    leaf_w, leaf_h, leaf_z0, flush, back = concealed_leaf(faces, swing_sign, width, base_z,
                                                          height)
    push = lo if swing_sign > 0 else hi
    head_z = base_z + height
    liner = (
        box(j, height, depth, -width / 2.0 + j / 2.0, base_z + height / 2.0, mid),
        box(j, height, depth, width / 2.0 - j / 2.0, base_z + height / 2.0, mid),
        box(width - 2.0 * j, j, depth, 0.0, head_z - j / 2.0, mid),
    )
    strip_far = back - swing_sign * _SHADOW_STRIP_DEPTH_M
    strip_t, strip_n = abs(strip_far - back), (strip_far + back) / 2.0
    stop_t, stop_n = abs(push - strip_far), (push + strip_far) / 2.0
    stop_h = head_z - j - leaf_z0
    inner = width / 2.0 - j            # liner face, along
    shadow, stop = [], []
    for side in (-1.0, 1.0):
        shadow.append(box(g, stop_h - g, strip_t, side * (inner - g / 2.0),
                          leaf_z0 + (stop_h - g) / 2.0, strip_n))
        stop.append(box(p, stop_h, stop_t, side * (inner - p / 2.0),
                        leaf_z0 + stop_h / 2.0, stop_n))
    shadow.append(box(2.0 * inner, g, strip_t, 0.0, head_z - j - g / 2.0, strip_n))
    stop.append(box(2.0 * (inner - p), p, stop_t, 0.0, head_z - j - p / 2.0, stop_n))
    return [
        GPart(key="jamb_liner", material_key=_CONCEALED_FRAME_KEY, solids=liner),
        GPart(key="leaf", material_key="door_leaf", solids=(
            box(leaf_w, leaf_h, _CONCEALED_LEAF_THICKNESS_M, 0.0, leaf_z0 + leaf_h / 2.0,
                (flush + back) / 2.0),)),
        GPart(key="stop", material_key=_CONCEALED_FRAME_KEY, solids=tuple(stop)),
        GPart(key="shadow_gap", material_key=_SHADOW_GAP_KEY, solids=tuple(shadow)),
    ]


def lever_solids(box: BoxFn, latch_along: float, toward_hinge: float,
                 leaf_faces: tuple[float, float], floor_z: float) -> list[GPrism]:
    """A rose, neck and lever on each face of one leaf, the lever pointing at the hinge.

    ``leaf_faces`` are the leaf's two face offsets; ``latch_along`` its latch edge.
    """
    rose_along = latch_along + toward_hinge * _LEVER_BACKSET_M
    z = floor_z + _LEVER_HEIGHT_M
    solids: list[GPrism] = []
    lo, hi = sorted(leaf_faces)
    for face, out in ((hi, 1.0), (lo, -1.0)):
        solids.append(box(_ROSE_SIZE_M, _ROSE_SIZE_M, _ROSE_PROUD_M, rose_along, z,
                          face + out * _ROSE_PROUD_M / 2.0))
        neck_len = _LEVER_STANDOFF_M - _ROSE_PROUD_M - _LEVER_SECTION_M / 2.0
        solids.append(box(_LEVER_NECK_M, _LEVER_NECK_M, neck_len, rose_along, z,
                          face + out * (_ROSE_PROUD_M + neck_len / 2.0)))
        solids.append(box(_LEVER_LENGTH_M, _LEVER_SECTION_M, _LEVER_SECTION_M,
                          rose_along + toward_hinge * (_LEVER_LENGTH_M / 2.0 - _LEVER_NECK_M / 2.0),
                          z, face + out * _LEVER_STANDOFF_M))
    return solids


def hardware_part(solids: list[GPrism]) -> GPart | None:
    return GPart(key="hardware", material_key=_HARDWARE_KEY, solids=tuple(solids)) \
        if solids else None
