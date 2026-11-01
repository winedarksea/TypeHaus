"""The dimension pass for an authored detail (C7-E4).

Two sources, both read off the cut already drawn: the strings a derived detail would get
for the pours in frame (XPS run, footing width/depth/toes), and the slice's own
``SliceDimension``\\ s, whose anchors resolve at the cut station
(``detail_anchors.cut_anchor``). An anchor that does not resolve drops its string and logs
it rather than printing a number measured off nothing.
"""

from __future__ import annotations

import logging

from typehaus.emit.draw.detail_anchors import cut_anchor, cut_frame
from typehaus.emit.draw.detail_components.stack_dimensions import (
    dim,
    dim_text,
    wall_stack_strings,
)
from typehaus.emit.draw.dimension_rows import dimension_offsets
from typehaus.emit.draw.scene import IRNode, Scene
from typehaus.model.views import Slice, SliceDimension
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

_LOG = logging.getLogger(__name__)

#: Smallest sheet scale (paper inches per foot) the derived wall strings print at.
_AUTO_MIN_SCALE = 0.5


def authored_dimension_nodes(model: ResolvedModel, view: Slice, scene: Scene) -> list[IRNode]:
    """Derived pour/footing strings plus every authored ``SliceDimension`` on ``view``."""
    if view.crop is None or view.cut_origin is None:
        return []
    direction, station = cut_frame(view)
    crop = (view.crop[0].xy_m, view.crop[1].xy_m)
    scale = _scale(scene)
    # The derived pour/footing strings only where a 4" toe can hold its label (>= 1/2").
    nodes: list[IRNode] = (list(wall_stack_strings(model, view, crop, direction, station))
                           if scale >= _AUTO_MIN_SCALE else [])
    resolved = []
    for spec in view.dimensions:
        node = _authored(model, view, scene, spec)
        if node is None:
            _LOG.warning("%s: dimension %s -> %s does not resolve at the cut",
                         view.tag, spec.start, spec.end)
            continue
        resolved.append(node)
    return nodes + _staggered(resolved, scale)


def _scale(scene: Scene) -> float:
    """The scale the sheet will print this cut at: its own frame, else the sheet's choice."""
    if scene.frame is not None:
        return scene.frame.scale
    from typehaus.emit.draw.sheet_writer import current_paper, frame_for_scene

    frame = frame_for_scene(scene, current_paper())
    return frame.scale if frame is not None else 0.25


def _staggered(nodes: list, scale: float) -> list:
    """Consecutive strings on one line form a chain; its labels stagger off each other."""
    out: list = []
    i = 0
    while i < len(nodes):
        vertical = abs(nodes[i].p1[1] - nodes[i].p0[1]) > abs(nodes[i].p1[0] - nodes[i].p0[0])
        axis = 0 if vertical else 1
        j = i + 1
        while (j < len(nodes) and abs(nodes[j].p0[axis] - nodes[i].p0[axis]) < 1e-6
               and abs(nodes[j].p0[1 - axis] - nodes[j - 1].p1[1 - axis]) < 1e-6):
            j += 1
        chain = nodes[i:j]
        if len(chain) > 1:
            spans = [abs(n.p1[1 - axis] - n.p0[1 - axis]) for n in chain]
            # Rows step away from the drawing: left of a vertical line, up off a horizontal.
            base = -1e-6 if vertical else 1e-6
            placed = dimension_offsets(spans, [n.text for n in chain], base, scale)
            chain = [n.model_copy(update={"offset": off, "text_along": along})
                     for n, (off, along) in zip(chain, placed, strict=True)]
        out.extend(chain)
        i = j
    return out


def _authored(model, view, scene, spec: SliceDimension):
    a = cut_anchor(model, scene, view, spec.start)
    b = cut_anchor(model, scene, view, spec.end)
    vertical = spec.axis == "z"
    if isinstance(spec.at, str):
        line = cut_anchor(model, scene, view, spec.at)
        at = None if line is None else (line[0] if vertical else line[1])
    else:
        at = spec.at.meters / M_PER_IN
    if a is None or b is None or at is None:
        return None
    if spec.offset is not None:
        at += spec.offset.meters / M_PER_IN
    if vertical:
        p0, p1 = (at, a[1]), (at, b[1])
    else:
        p0, p1 = (a[0], at), (b[0], at)
    if abs(p1[0] - p0[0]) + abs(p1[1] - p0[1]) < 1e-6:
        return None
    text = spec.text
    if text is not None and "{}" in text:  # "{} band": the measured 1/8" string, labelled
        text = text.replace("{}", dim_text(abs(p1[0] - p0[0]) + abs(p1[1] - p0[1])))
    return dim(p0, p1, 0.0, text)
