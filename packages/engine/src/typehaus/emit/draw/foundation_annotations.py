"""Compact foundation keys with complete callout text in an adjacent register."""

from __future__ import annotations

from typehaus.emit.draw.annotation_requests import add_point_label
from typehaus.emit.draw.scene import Leader, NamedPoint, Scene, SceneBuilder, Text
from typehaus.emit.draw.typography import TEXT_PT


def foundation_annotations(scene: Scene) -> tuple[SceneBuilder, tuple[str, ...]]:
    builder = SceneBuilder(name=scene.name, units=scene.units)
    callouts: dict[str, str] = {}
    for index, node in enumerate(scene.nodes):
        if isinstance(node, Leader):
            text = " ".join(node.text.split())
            key = callouts.setdefault(text, f"K{len(callouts) + 1}")
            target = node.anchor.xy if isinstance(node.anchor, NamedPoint) else node.to
            add_point_label(builder, key=f"foundation:{index}", text=key,
                            target=target, layer=node.layer, height_pt=TEXT_PT, priority=60)
        elif isinstance(node, Text) and node.layer == "A-SLAB":
            # Thickness, tag, elevation, and assembly already live in the slab schedule.
            mark = node.content.split(" · ", 1)[0]
            add_point_label(builder, key=f"foundation-slab:{index}", text=mark,
                            target=node.anchor, layer=node.layer, height_pt=TEXT_PT, priority=70)
        else:
            builder.add(node)
    return builder, tuple(f"{key}: {text}" for text, key in callouts.items())
