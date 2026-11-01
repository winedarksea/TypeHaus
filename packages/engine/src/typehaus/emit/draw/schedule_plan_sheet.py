"""A plan with keyed schedules beside it, on a real sheet (S-100, S-101.n, S-102.n, C-101).

The schedule blocks are lettering, and lettering has a printed size, but a builder lays
them out before the sheet's scale exists. ``metrics_for`` guesses in model inches, and where
the sheet lands small the writer rounds the guess up to ``MIN_PT``: every row then prints
up to 3x wider than the column it reserved and the next block starts on top of it (C7-E1).

So the scale and the lettering are chosen together, the way ``floorplan_sheet`` chooses a
scale with its dimension tiers: walk the ladder from the top, build at each rung with the
blocks sized for that rung at ``MIN_PT``, and stop at the first rung the whole scene fits.
At that rung the schedule takes the largest of ``SCHEDULE_PTS`` that still fits — the plan
is what the sheet is for, so the tables never cost it a rung. Builds are cheap (well under
0.1 s), and rungs the bare drawing cannot fit are skipped without a build.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

from typehaus.emit.draw.datum import model_at_level
from typehaus.emit.draw.dimension_rows import dimension_reserve
from typehaus.emit.draw.paper import ARCH_SCALES, ENG_SCALES
from typehaus.emit.draw.scene import ArchDimension, Scene, Text
from typehaus.emit.draw.schedule_block import (
    SCHEDULE_GRID_LAYER,
    BlockMetrics,
    metrics_at_scale,
)
from typehaus.emit.draw.typography import MIN_PT, TEXT_PT
from typehaus.resolve.model import ResolvedModel

#: Schedule body sizes tried at the chosen rung, largest first; the last is the floor.
SCHEDULE_PTS = (TEXT_PT, 6.0, 5.0, MIN_PT)

Build = Callable[[BlockMetrics | None, float | None], Scene]


def framed_schedule_plan(build: Build, paper: tuple[float, float]) -> Scene:
    """``build(metrics, scale)`` framed on ``paper``, schedules at a printed size.

    ``scale`` is the rung being tried, so dimension tiers are laid out for it; ``None`` is
    the builder's own nominal guess. The tiers stand outside the scene bounds the frame is
    fitted to, so each fit reserves their paper (``dimension_rows.dimension_reserve``).
    """
    from typehaus.emit.draw.sheet_writer import frame_for_scene

    nominal = build(None, None)
    floor = _drawing_floor(nominal)
    if frame_for_scene(nominal, paper) is None:
        return nominal
    for scale, label in (*ARCH_SCALES, *ENG_SCALES):
        if floor is not None and not _fits(floor, paper, scale):
            continue
        scene = build(metrics_at_scale(scale, SCHEDULE_PTS[-1]), scale)
        if not _fits(scene, paper, scale):
            continue
        for larger in SCHEDULE_PTS[:-1]:
            bigger = build(metrics_at_scale(scale, larger), scale)
            if _fits(bigger, paper, scale):
                scene = bigger
                break
        frame = frame_for_scene(scene, paper, scale_label=label,
                                reserve=dimension_reserve(scene, scale))
        return scene.model_copy(update={"frame": frame})
    return nominal  # nothing fits even at the floor: the writer's N.T.S. fit, as before


def _fits(scene: Scene, paper: tuple[float, float], scale: float) -> bool:
    from typehaus.emit.draw.sheet_writer import frame_for_scene

    frame = frame_for_scene(scene, paper, reserve=dimension_reserve(scene, scale))
    return frame is not None and frame.scale >= scale


def _drawing_floor(scene: Scene) -> Scene | None:
    """The scene without its lettering or dimensions — a lower bound used only to skip rungs.

    Dropping text can only shrink the bounds, so a rung this cannot fit, the full scene
    cannot fit either; it never makes the search skip a rung that would have worked.
    """
    kept = tuple(node for node in scene.nodes
                 if not isinstance(node, (Text, ArchDimension)) and getattr(node, "layer", "")
                 != SCHEDULE_GRID_LAYER)
    return scene.model_copy(update={"nodes": kept}) if kept else None


def schedule_plan_sheet(build: Any, level: str | None = None, **kwargs: Any) -> Any:
    """The ``SceneFn`` for a schedule-bearing plan, framed on the set's paper.

    ``level`` draws that level's whole datum (``datum.at_level``); ``kwargs`` go to the
    builder. Carries ``func``/``keywords`` so ``test_sheet_index`` can still ask which
    builder a sheet uses.
    """

    def scene(model: ResolvedModel) -> Scene:
        from typehaus.emit.draw.sheet_writer import current_paper

        here = model if level is None else model_at_level(model, level)
        dimensioned = "dimension_scale" in inspect.signature(build).parameters
        extra = {} if level is None else {"storey": level}
        def built(metrics: BlockMetrics | None, scale: float | None) -> Scene:
            tiers = {} if scale is None or not dimensioned else {"dimension_scale": scale}
            return build(here, metrics=metrics, **extra, **tiers, **kwargs)

        return framed_schedule_plan(built, current_paper())

    scene.func = build  # type: ignore[attr-defined]
    scene.keywords = {**({} if level is None else {"storey": level}), **kwargs}  # type: ignore[attr-defined]
    return scene
