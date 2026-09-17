"""Reflow authored section ladders at their final printed scale."""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.emit.draw.annotate import model_in_per_pt, text_extent
from typehaus.emit.draw.annotation_layout import LayoutDiagnostic, Viewport
from typehaus.emit.draw.annotation_layout_config import COLUMN_MARGIN_PT, LABEL_CLEARANCE_PT
from typehaus.emit.draw.scene import Leader, Scene
from typehaus.emit.draw.typography import TEXT_PT


@dataclass(frozen=True)
class LadderRequest:
    key: str
    seed: Leader


def resolve_ladders(scene: Scene, viewport: Viewport, scale: float) -> Scene:
    """Keep each column's top-to-bottom order and all original arrow targets.

    The seeds retain model-space layouts for unframed exports. Paper composition expands
    rung spacing to the actual lettering height; a reverse sweep keeps the last rung
    inside the viewport without compressing any lettering.
    """
    requests = [item for item in scene.annotation_requests if isinstance(item, LadderRequest)]
    if not requests:
        return scene
    per_pt = model_in_per_pt(scale)
    clearance = LABEL_CLEARANCE_PT * per_pt
    margin = COLUMN_MARGIN_PT * per_pt
    x0, y0, x1, y1 = viewport.bounds
    columns: dict[tuple[float, bool], list[LadderRequest]] = {}
    for request in requests:
        node = request.seed
        columns.setdefault((node.at[0], node.at[0] < node.to[0]), []).append(request)
    replacements = {}
    diagnostics = list(scene.annotation_diagnostics)
    for (column_x, right_aligned), column in sorted(columns.items()):
        column.sort(key=lambda item: (-item.seed.at[1], item.key))
        sizes = [text_extent(item.seed.text, item.seed.height_pt or TEXT_PT) for item in column]
        half_heights = [height * per_pt / 2 for _, height in sizes]
        max_width = max(width for width, _ in sizes) * per_pt
        x = (max(column_x, x0 + margin + max_width) if right_aligned
             else min(column_x, x1 - margin - max_width))
        positions = []
        ceiling = y1 - margin
        for request, half_height in zip(column, half_heights, strict=True):
            y = min(request.seed.at[1], ceiling - half_height)
            positions.append(y)
            ceiling = y - half_height - clearance
        floor = y0 + margin
        for index in range(len(column) - 1, -1, -1):
            positions[index] = max(positions[index], floor + half_heights[index])
            floor = positions[index] + half_heights[index] + clearance
        for request, y, half_height in zip(column, positions, half_heights, strict=True):
            replacements[id(request.seed)] = request.seed.model_copy(update={"at": (x, y)})
            if y + half_height > y1 - margin or max_width > x1 - x0 - 2 * margin:
                diagnostics.append(LayoutDiagnostic(request.key, "ladder exceeds viewport"))
    return scene.model_copy(update={
        "nodes": tuple(replacements.get(id(node), node) for node in scene.nodes),
        "annotation_diagnostics": tuple(diagnostics),
    })
