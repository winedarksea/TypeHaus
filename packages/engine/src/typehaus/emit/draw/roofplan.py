"""Roof-plan drawing from resolved roof planes (M3 A-106)."""

from __future__ import annotations

from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Text
from typehaus.resolve.model import ResolvedModel

_M_TO_IN = 39.37007874015748


def build_roof_plan(model: ResolvedModel) -> Scene:
    """Draw gable/shed plane outlines, ridges, and pitch labels from resolved roofs."""
    b = SceneBuilder(name="roof-plan", units="in")
    for roof in model.roofs:
        footprint = tuple((x * _M_TO_IN, y * _M_TO_IN) for x, y in roof.footprint)
        b.add(Polyline(points=footprint, layer="A-ROOF", closed=True, lineweight=0.45,
                       uid=roof.uid, tag=roof.tag))
        xs, ys = [point[0] for point in roof.footprint], [point[1] for point in roof.footprint]
        if roof.ridge_direction == "x":
            ridge = ((min(xs), (min(ys) + max(ys)) / 2), (max(xs), (min(ys) + max(ys)) / 2))
        else:
            ridge = (((min(xs) + max(xs)) / 2, min(ys)), ((min(xs) + max(xs)) / 2, max(ys)))
        b.add(Polyline(points=tuple((x * _M_TO_IN, y * _M_TO_IN) for x, y in ridge),
                       layer="A-ROOF", lineweight=0.8, uid=roof.uid, tag=f"{roof.tag}-ridge"))
        authored = model.plan.by_tag(roof.tag)
        pitch = getattr(authored, "pitch", None)
        pitch_label = f"{pitch.rise}:{pitch.run}" if pitch is not None else "resolved"
        b.add(Text(anchor=((min(xs) + max(xs)) / 2 * _M_TO_IN,
                           (min(ys) + max(ys)) / 2 * _M_TO_IN),
                   content=f"{roof.tag}  {pitch_label}", height=3.5, align="center"))
    return b.build()
