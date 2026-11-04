"""The roof plan on a real sheet: a scale chosen with room for its locating tiers.

``build_roof_plan`` spaces its tiers for the ``dimension_scale`` it is given, and the tiers
stand outside the scene bounds a frame is fitted to. So, as ``floorplan_sheet`` does for the
floor plans, the scale and the tiers are decided together: walk down from the scale the bare
drawing would take, build the tiers at each rung, and keep the first the frame still lands on.
"""

from __future__ import annotations

from typing import Any

from typehaus.emit.draw.dimension_rows import dimension_reserve
from typehaus.emit.draw.roofplan import build_roof_plan
from typehaus.emit.draw.scene import Scene
from typehaus.resolve.model import ResolvedModel


def framed_roof_plan(model: ResolvedModel, paper: tuple[float, float]) -> Scene:
    """The roof plan with a pinned :class:`Frame` on ``paper``."""
    from typehaus.emit.draw.paper import ARCH_SCALES, ENG_SCALES
    from typehaus.emit.draw.sheet_writer import frame_for_scene

    scene = build_roof_plan(model)
    bare = frame_for_scene(scene, paper)
    if bare is None:
        return scene
    frame = None
    for rung, _label in (*ARCH_SCALES, *ENG_SCALES):
        if rung > bare.scale:
            continue  # tiers only add paper, so a rung the bare drawing misses cannot fit
        scene = build_roof_plan(model, dimension_scale=rung)
        frame = frame_for_scene(scene, paper, reserve=dimension_reserve(scene, rung))
        if frame is not None and frame.scale >= rung:
            return scene.model_copy(update={"frame": frame})
    return scene.model_copy(update={"frame": frame}) if frame is not None else scene


def roof_plan_sheet() -> Any:
    """The A-1xx roof ``SceneFn``: the plan framed on the paper the set is printing on."""

    def scene(model: ResolvedModel) -> Scene:
        from typehaus.emit.draw.sheet_writer import current_paper

        return framed_roof_plan(model, current_paper())

    scene.func = build_roof_plan  # type: ignore[attr-defined]
    scene.keywords = {}           # type: ignore[attr-defined]
    return scene
