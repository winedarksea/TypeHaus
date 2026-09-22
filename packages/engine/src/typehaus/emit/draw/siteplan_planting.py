"""C-101 planting: specimen spreads, grid dots and accents, trellises, rain gardens.

Plan drawings skip derived solids, so this reads ``model.plants`` and the authored
elements instead. Layers: ``L-PLNT`` (spreads, trellis lines), ``L-PLNT-SYMB`` (grid dots
and accent glyphs), ``C-STRM-BIOR`` (the basin rim, its floor, and its ponding note).
"""

from __future__ import annotations

from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.annotation_requests import add_point_label
from typehaus.emit.draw.lineweights import LIGHT, PROFILE, REFERENCE
from typehaus.emit.draw.scene import Polyline, SceneBuilder
from typehaus.emit.draw.typography import DIM_TEXT_PT
from typehaus.model.landscape import Plant, RainGarden, Trellis
from typehaus.resolve.geometry import circle_outline
from typehaus.resolve.landscape import trellis_post_stations
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.rain_garden import floor_ring

_DOT_M = 2.0 * 0.0254      # a field plant's symbol radius
_ACCENT_M = 3.5 * 0.0254   # half-size of an accent's cross
_TICK_M = 4.0 * 0.0254     # half-length of a post tick


def emit_site_planting(builder: SceneBuilder, model: ResolvedModel) -> None:
    specimens = {e.tag for e in model.plan.all_elements() if isinstance(e, Plant)}
    for plant in sorted(model.plants, key=lambda p: p.tag):
        x, y = plant.position
        if plant.source_ref in specimens:
            builder.add(Polyline(
                points=tuple(_in(p) for p in circle_outline((x, y), plant.spread_m / 2, 24)),
                closed=True, layer="L-PLNT", lineweight=PROFILE, tag=plant.tag))
            add_point_label(builder, key=f"plant-{plant.tag}", text=plant.tag,
                            target=_in((x, y)), layer="L-PLNT", height_pt=DIM_TEXT_PT,
                            priority=30)
        elif plant.accent:
            a = _ACCENT_M
            for dx, dy in ((a, a), (a, -a)):
                builder.add(Polyline(points=(_in((x - dx, y - dy)), _in((x + dx, y + dy))),
                                     layer="L-PLNT-SYMB", lineweight=LIGHT))
        else:
            builder.add(Polyline(
                points=tuple(_in(p) for p in circle_outline((x, y), _DOT_M, 8)),
                closed=True, layer="L-PLNT-SYMB", lineweight=REFERENCE))
    for element in model.plan.all_elements():
        if isinstance(element, Trellis):
            _trellis(builder, element)
        elif isinstance(element, RainGarden):
            _rain_garden(builder, element)


def _trellis(builder: SceneBuilder, el: Trellis) -> None:
    builder.add(Polyline(points=tuple(_in(p.xy_m) for p in el.path), layer="L-PLNT",
                         lineweight=PROFILE, uid=el.uid, tag=el.tag))
    path = [p.xy_m for p in el.path]
    dx, dy = path[-1][0] - path[0][0], path[-1][1] - path[0][1]
    norm = (dx * dx + dy * dy) ** 0.5 or 1.0
    nx, ny = -dy / norm * _TICK_M, dx / norm * _TICK_M
    for x, y in trellis_post_stations(el):
        builder.add(Polyline(points=(_in((x - nx, y - ny)), _in((x + nx, y + ny))),
                             layer="L-PLNT", lineweight=PROFILE))
    add_point_label(builder, key=f"trellis-{el.tag}", text=el.tag, target=_in(path[0]),
                    layer="L-PLNT", height_pt=DIM_TEXT_PT, priority=30)


def _rain_garden(builder: SceneBuilder, el: RainGarden) -> None:
    rim = [p.xy_m for p in el.outline]
    builder.add(Polyline(points=tuple(_in(p) for p in rim), closed=True, layer="C-STRM-BIOR",
                         lineweight=PROFILE, uid=el.uid, tag=el.tag))
    floor = floor_ring(el)
    if floor:
        builder.add(Polyline(points=tuple(_in(p) for p in floor), closed=True,
                             layer="C-STRM-BIOR", lineweight=LIGHT, linetype="DASHED"))
    x = sum(p[0] for p in rim) / len(rim)
    y = sum(p[1] for p in rim) / len(rim)
    depth_in = el.ponding_depth.meters / 0.0254
    add_point_label(builder, key=f"rain-garden-{el.tag}",
                    text=f"{el.tag} RAIN GARDEN, {depth_in:.0f}\" PONDING", target=_in((x, y)),
                    layer="C-STRM-BIOR", height_pt=DIM_TEXT_PT, priority=45)
