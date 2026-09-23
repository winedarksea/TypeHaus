"""A floor plan on a real sheet: the scale chosen with room for its dimension tiers.

``build_floorplan`` spaces its tiers for whatever ``dimension_scale`` it is given, and a
sheet does not know its scale until the drawing exists. Dimensions never enter the scene
bounds a scale is chosen from, so this is one decision and at most one rebuild — no loop:
build, choose the scale with the tiers' paper band reserved, rebuild the tiers at it, pin
the frame.

The band is struck off the wall FACES, and a porch or a stair pad that already reaches
past a face has paid for that much of it: at 1/4" the porch below catlin's south face is
2" of paper, nearly the whole south band. Reserving the full band past the drawing's edge
cost A-102 its 1/4" on 24x36.
"""

from __future__ import annotations

from typing import Any

from typehaus.emit.draw._shared import PLAN_RESERVATION_SCALE, wall_face_bounds
from typehaus.emit.draw.datum import model_at_level
from typehaus.emit.draw.dimension_rows import dimension_band_in
from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.scene import Scene
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel


def _band_past_drawing(scene: Scene, faces_in: tuple[float, float, float, float] | None):
    """``scale -> (w, e, s, n)`` paper inches of dimension band beyond the drawing's edge."""
    from typehaus.emit.draw.pdf_writer import _scene_bounds

    band = dimension_band_in()
    bounds = _scene_bounds(scene)
    if faces_in is None or bounds is None:
        return band
    minx, maxx, miny, maxy = faces_in
    u0, z0, u1, z1 = bounds
    overhang = (minx - u0, u1 - maxx, miny - z0, z1 - maxy)  # model inches past each face

    def at(scale: float) -> tuple[float, float, float, float]:
        paper_per_model = scale / 12.0
        return tuple(max(0.0, need - max(0.0, past) * paper_per_model)  # type: ignore[return-value]
                     for need, past in zip(band, overhang, strict=True))

    return at


def framed_floorplan(model: ResolvedModel, storey: str, paper: tuple[float, float],
                     scale_label: str | None = None) -> Scene:
    """``storey``'s level plan with a pinned :class:`Frame` on ``paper``."""
    from typehaus.emit.draw.sheet_writer import frame_for_scene

    level = model_at_level(model, storey)
    scene = build_floorplan(level, storey)
    faces = wall_face_bounds([w for w in level.walls if w.storey == storey])
    faces_in = None if faces is None else tuple(v / M_PER_IN for v in faces)
    frame = frame_for_scene(scene, paper, scale_label=scale_label,
                            reserve=_band_past_drawing(scene, faces_in))
    if frame is None:
        return scene
    if frame.scale != PLAN_RESERVATION_SCALE:
        scene = build_floorplan(level, storey, dimension_scale=frame.scale)
    return scene.model_copy(update={"frame": frame})


def floorplan_sheet(storey: str) -> Any:
    """The A-1xx ``SceneFn``: the plan framed on the paper the set is printing on."""

    def scene(model: ResolvedModel) -> Scene:
        from typehaus.emit.draw.sheet_writer import current_paper

        return framed_floorplan(model, storey, current_paper())

    # ``test_sheet_index`` asks which builder a sheet uses, as ``datum.at_level`` answers.
    scene.func = build_floorplan          # type: ignore[attr-defined]
    scene.keywords = {"storey": storey}   # type: ignore[attr-defined]
    return scene
