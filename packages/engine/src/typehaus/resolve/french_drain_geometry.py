"""Continuous French-drain geometry, separate from level footing-bedding tile rings."""

from __future__ import annotations

from typehaus.model.structure import FrenchDrain
from typehaus.resolve.drain_tile import PIPE_BEDDING_M
from typehaus.resolve.geometry import rect_between
from typehaus.resolve.geometry_ir import GBox
from typehaus.resolve.geometry_slice_box import outward_box_mesh
from typehaus.resolve.model import ResolvedSolid, SolidSweep
from typehaus.resolve.round_solids import PIPE_FACETS
from typehaus.resolve.sweep import round_profile, sweep_plan_silhouette, sweep_z_extent


def french_drain_solids(element: FrenchDrain, storey: str, path, inverts) -> list[ResolvedSolid]:
    """One stone envelope and round pipe per authored leg, without level stair steps.

    Trench depth is vertical, rather than normal to the slope: a sheared box preserves
    the authored excavation width, depth and plan length even on steep connecting leads.
    Pipe centres sit one radius above the invert on the shared stone bedding allowance.
    """
    solids: list[ResolvedSolid] = []
    trench_half_width = element.trench_width.meters / 2.0
    trench_depth = element.trench_depth.meters
    for index, (start, end) in enumerate(zip(path[:-1], path[1:], strict=True)):
        if start == end:
            continue
        start_floor, end_floor = inverts[index:index + 2]
        outline = rect_between(start, end, -trench_half_width, trench_half_width)
        dx, dy = end[0] - start[0], end[1] - start[1]
        length_squared = dx * dx + dy * dy
        bottom = tuple(
            (x, y, start_floor + (end_floor - start_floor)
             * ((x - start[0]) * dx + (y - start[1]) * dy) / length_squared)
            for x, y in outline)
        top = tuple((x, y, z + trench_depth) for x, y, z in bottom)
        solids.append(ResolvedSolid(
            uid=f"{element.uid}-{index:02d}", tag=f"{element.tag}-{index + 1}",
            storey=storey, category="french_drain", outline=outline,
            z0_m=min(start_floor, end_floor),
            z1_m=max(start_floor, end_floor) + trench_depth, material="aggregate",
            body_mesh=outward_box_mesh(GBox(bottom, top)),
        ))
        if element.tile is None:
            continue
        radius = element.tile.diameter.meters / 2.0
        sweep = SolidSweep(
            path=((start[0], start[1], start_floor + PIPE_BEDDING_M + radius),
                  (end[0], end[1], end_floor + PIPE_BEDDING_M + radius)),
            profile=round_profile(radius, PIPE_FACETS))
        z0, z1 = sweep_z_extent(sweep)
        solids.append(ResolvedSolid(
            uid=f"{element.uid}-DT-{index:02d}", tag=f"{element.tag}-DT-{index + 1}",
            storey=storey, category="drain_tile", outline=sweep_plan_silhouette(sweep),
            z0_m=z0, z1_m=z1, material=element.tile.material, sweep=sweep,
        ))
    return solids
