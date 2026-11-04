"""The porch guard: the four cast corner columns are its posts (owner, 2026-11-04).

A base sits wholly on one substrate, and a concrete anchor row stays >= 3" from a face. So
the west and east legs run on W-SG-W1/E1's tops and end into PT-SG-BR1/BF1 and BR3/BF3,
which are their posts: `start_post_ref`/`end_post_ref` name the column and the path ends on
its drawn face. A path cannot carry a hole, so the guard is one element per span between
columns. The south leg stands on the plank (params/sunken_garden.py, beside its blocks).

West, the leg is on the wall's centreline: anchor rows 4 1/8" off both faces. East, it is
on the stair guards' head-post line, 5" back from the wall's east face, and draws those two
head posts at the porch's 42"; RL-SG-PSTAIR-S/N end on them. At the house each side leg
ends on its own post: anchors 3" off the wall's north end, the post 3 3/8" off the cladding.

Uids are minted by hand (`haus fmt` does not visit params/).
"""

from __future__ import annotations

import math

from params.sunken_garden import (
    PILLARS,
    PORCH_GUARD_HEAD_X_FT,
    PORCH_GUARD_S_X,
    PORCH_GUARD_S_Y,
    PORCH_WALKING_SURFACE,
    RETAINING_TOP,
    SPEC,
    STAIR_GUARD_Y_FT,
    WALL_E_AXIS_X_FT,
    WALL_N_END_Y_FT,
    WALL_S_AXIS_Y_FT,
    WALL_W_AXIS_X_FT,
)
from params.sunken_garden_options import OPTION
from typehaus import Railing, RailingKind, ft, inch, pt
from typehaus.library.railings import RAILING_EXT_ALUMINUM_SURFACE
from typehaus.model.surface_mount import SurfacePostMount
from typehaus.resolve.framing.profiles import cross_section, post_outline

_FT = 0.3048
_SPACING_FT = 5.0
_COLUMNS = {post.tag: post for post in PILLARS}
_HOLE_HALF_IN = RAILING_EXT_ALUMINUM_SURFACE.surface_mount.display_hole_spacing.meters / 0.0254 / 2
#: The house-end post, on the 1/8" south of where its anchor row is 3" off the wall's end.
_HOUSE_POST_Y_FT = math.floor((WALL_N_END_Y_FT * 12.0 - 3.0 - _HOLE_HALF_IN) * 8.0) / 8.0 / 12.0
_EAST_X_FT = PORCH_GUARD_HEAD_X_FT
_WALL_TOP = ft(0)


def _face_y(column: str, x_ft: float, north: bool) -> float:
    """Where the plan line x = ``x_ft`` meets ``column``'s drawn face, north or south side."""
    post = _COLUMNS[column]
    ring = post_outline(post.position.xy_m, cross_section(post.size))
    x = x_ft * _FT
    ys = [ay + (x - ax) / (bx - ax) * (by - ay)
          for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1], strict=True)
          if ax != bx and min(ax, bx) <= x <= max(ax, bx)]
    return (max(ys) if north else min(ys)) / _FT


def _stations(points) -> int:
    """How many posts the resolver frames on ``points`` at 60" (railing_post_stations)."""
    return 1 + sum(max(math.ceil(math.dist(a, b) / _SPACING_FT - 1e-9), 1)
                   for a, b in zip(points[:-1], points[1:], strict=True))


def _guard(uid, tag, points, substrate, *, start=None, end=None, base=PORCH_WALKING_SURFACE,
           bearing=_WALL_TOP):
    mounts = tuple(SurfacePostMount(elevation=bearing, substrate=substrate)
                   for _ in range(_stations(points)))
    return Railing(uid=uid, tag=tag, type_ref="RAILING-EXT-ALUMINUM-SURFACE",
                   path=tuple(pt(ft(x), ft(y)) for x, y in points),
                   kind=RailingKind.METAL_SURFACE_MOUNT, height=ft(SPEC.railing_height_ft),
                   base_elevation=base, post_spacing=inch(_SPACING_FT * 12.0),
                   post_size="3x3", rail_count=2, mount="surface",
                   assembly="RAILING_DARK_METAL", start_post_ref=start, end_post_ref=end,
                   surface_post_mounts=mounts, infill="balusters", baluster_spacing=inch(4))


_W, _E = WALL_W_AXIS_X_FT, _EAST_X_FT
PORCH_GUARDS = [
    _guard("NHGMTJ4GDY", "RL-SG-PORCH-W-HOUSE",
           [(_W, _HOUSE_POST_Y_FT), (_W, _face_y("PT-SG-BR1", _W, north=True))],
           "concrete", end="PT-SG-BR1"),
    _guard("6563PJPRHE", "RL-SG-PORCH-W",
           [(_W, _face_y("PT-SG-BR1", _W, north=False)),
            (_W, _face_y("PT-SG-BF1", _W, north=True))],
           "concrete", start="PT-SG-BR1", end="PT-SG-BF1"),
    # The south leg, on the plank: posts 2 3/4" clear of BF1/BF3, under R312.1.3's 4".
    _guard("SGRA02AAAA", "RL-SG-PORCH",
           [(PORCH_GUARD_S_X[0], PORCH_GUARD_S_Y), (PORCH_GUARD_S_X[1], PORCH_GUARD_S_Y)],
           "wood", bearing=PORCH_WALKING_SURFACE),
    _guard("CGG2R40NMP", "RL-SG-PORCH-SE",
           [(_E, STAIR_GUARD_Y_FT[0]), (_E, _face_y("PT-SG-BF3", _E, north=True))],
           "concrete", end="PT-SG-BF3"),
    _guard("SGRA07AAAA", "RL-SG-PORCH-NE",
           [(_E, STAIR_GUARD_Y_FT[1]), (_E, _face_y("PT-SG-BR3", _E, north=False))],
           "concrete", end="PT-SG-BR3"),
    _guard("1NH4W6DT1C", "RL-SG-PORCH-E-HOUSE",
           [(_E, _face_y("PT-SG-BR3", _E, north=True)), (_E, _HOUSE_POST_Y_FT)],
           "concrete", start="PT-SG-BR3"),
]

# A planter placed directly against the retaining wall leaves only 10 inches of concrete
# above its 30-inch soil surface, so the porch's guard continues round the court on the
# retaining walls' centrelines, out of BF1 and BF3's south faces.
if OPTION.needs_court_guard:
    PORCH_GUARDS.append(_guard(
        "SGRA08AAAA", "RL-SG-COURT",
        [(WALL_W_AXIS_X_FT, _face_y("PT-SG-BF1", WALL_W_AXIS_X_FT, north=False)),
         (WALL_W_AXIS_X_FT, WALL_S_AXIS_Y_FT), (WALL_E_AXIS_X_FT, WALL_S_AXIS_Y_FT),
         (WALL_E_AXIS_X_FT, _face_y("PT-SG-BF3", WALL_E_AXIS_X_FT, north=False))],
        "concrete", start="PT-SG-BF1", end="PT-SG-BF3", base=RETAINING_TOP,
        bearing=RETAINING_TOP))

MAIN_ELEMENTS = PORCH_GUARDS
