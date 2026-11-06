"""The P/M/E plan sheets framed on their trade content, not on every wall of the level.

A level plan draws every structure on its datum, so catlin's basement and main trade plans
carried the garage and the sunken court as ghost walls, and those walls set the scale: E-101
printed at 1/16" and E-102 at 3/32" with a 36' house in a corner and its device tags stacked
(M3-102, M2-106). The frame is chosen here from the trade's own content plus the primary
storey's own walls; another structure's ghost walls stay in the scene and are clipped at the
viewport. Nothing a trade drew is ever cropped: it is in the box the scale is chosen for.
"""

from __future__ import annotations

from typing import Any

from typehaus.emit.draw.datum import model_at_level
from typehaus.emit.draw.scene import Scene
from typehaus.resolve.model import ResolvedModel

#: ``_shared.emit_ghost_walls``'s layer: context, not content.
GHOST_LAYER = "A-WALL-BELW"


def content_framed(scene: Scene, own_walls: set[str], paper: tuple[float, float]) -> Scene:
    """``scene`` with a frame fitted to everything but other structures' ghost walls."""
    from typehaus.emit.draw.sheet_writer import frame_for_scene

    focus = tuple(node for node in scene.nodes if getattr(node, "layer", "") != GHOST_LAYER
                  or getattr(node, "uid", None) in own_walls)
    frame = frame_for_scene(scene.model_copy(update={"nodes": focus}), paper)
    return scene if frame is None else scene.model_copy(update={"frame": frame})


def trade_plan_sheet(build: Any, primary: str) -> Any:
    """The ``SceneFn`` for one trade plan of ``primary``'s level, content-framed.

    Carries ``func``/``keywords`` like ``datum.at_level`` so ``test_sheet_index`` can still
    ask which builder a sheet uses.
    """

    def scene(model: ResolvedModel) -> Scene:
        from typehaus.emit.draw.sheet_writer import current_paper

        own = {wall.uid for wall in model.walls if wall.storey == primary}
        built = build(model_at_level(model, primary), storey=primary)
        return content_framed(built, own, current_paper())

    scene.func = build          # type: ignore[attr-defined]
    scene.keywords = {"storey": primary}  # type: ignore[attr-defined]
    return scene
