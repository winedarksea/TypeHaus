"""A guard end that dies into a structural column: the column is that end's post.

``Railing.start_post_ref``/``end_post_ref`` may name a ``Post`` as well as another guard. The
path ends on the column's drawn face (:func:`post_outline`, the ring the column solid is
extruded from), so rails and infill already stop there; the guard draws no post of its own
at that end, only a bracket plate per rail against the face, ``{tag}-COLBRK{n}``, which
the take-off counts.
"""

from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.model.structure import Post, Railing
from typehaus.resolve.framing.profiles import cross_section, post_outline
from typehaus.resolve.geometry import Vec
from typehaus.resolve.model import ResolvedModel, ResolvedSolid, SolidSweep
from typehaus.resolve.railings.parts import RAILING_CATEGORY, RailingParts
from typehaus.resolve.railings.spans import RailingSurface
from typehaus.resolve.sweep import rect_profile, sweep_plan_silhouette, sweep_z_extent

#: The rail-end bracket as drawn: a 2" x 3" plate, 3/16" thick. A drawing size only.
_PLATE_W_M, _PLATE_H_M, _PLATE_T_M = 0.0508, 0.0762, 0.0048


def column_face_distance(post: Post, point: Vec) -> float:
    """How far ``point`` stands off ``post``'s drawn face, in plan."""
    ring = Polygon(post_outline(post.position.xy_m, cross_section(post.size)))
    return ring.exterior.distance(Point(point))


def column_end_indices(plan, el: Railing, path: list[Vec]) -> list[int]:
    """Path end indices (0 / -1) whose ref names a ``Post`` — whatever the station check says."""
    if plan is None or len(path) < 2:
        return []
    return [index for index, ref in ((0, el.start_post_ref), (-1, el.end_post_ref))
            if ref is not None and isinstance(plan.by_tag(ref), Post)]


def emit_column_brackets(model: ResolvedModel, el: Railing, storey: str, path: list[Vec],
                         surface: RailingSurface, parts: RailingParts,
                         rises: list[float], ends: list[int]) -> None:
    """One plate per rail at each column end, on the face and reaching into the bay."""
    count = 0
    for index in ends:
        end, inward = (path[0], path[1]) if index == 0 else (path[-1], path[-2])
        dx, dy = inward[0] - end[0], inward[1] - end[1]
        run = (dx * dx + dy * dy) ** 0.5
        if run < 1e-9:
            continue
        ux, uy = dx / run, dy / run
        for rise in rises:
            z = surface.height_at(end) + rise
            sweep = SolidSweep(
                path=((end[0], end[1], z),
                      (end[0] + ux * _PLATE_T_M, end[1] + uy * _PLATE_T_M, z)),
                profile=rect_profile(_PLATE_W_M, _PLATE_H_M))
            count += 1
            z0, z1 = sweep_z_extent(sweep)
            model.solids.append(ResolvedSolid(
                uid=f"{el.uid}-cb{count:02d}", tag=f"{el.tag}-COLBRK{count}",
                storey=storey, category=RAILING_CATEGORY,
                outline=sweep_plan_silhouette(sweep), z0_m=z0, z1_m=z1,
                assembly=el.assembly, material=parts.post_material, sweep=sweep))
