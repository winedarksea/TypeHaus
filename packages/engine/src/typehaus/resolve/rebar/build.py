"""``resolve_rebar``: every authored ``ReinforcementSpec`` laid out as pieces (decision #75).

Runs as the ``"rebar"`` pipeline stage, after every host it reads has resolved and before
``"geometry"``. Bars land in ``ResolvedModel.rebar`` and nowhere else — not in any member
list — so framing takeoff, member checks, sections and the geometry IR never see them.

Defaults, where a pour states nothing: cover 1 1/2", f'c 3,000 psi, 20'-0" stock, class B
laps. ``integrity.reinforcement_layout`` is where an unplaceable role is reported.
"""

from __future__ import annotations

import math

from typehaus.model.enums import LayerFunction
from typehaus.resolve.assembly_material import is_cast_beam
from typehaus.resolve.concrete import concrete_spec_for
from typehaus.resolve.rebar import detailing as det
from typehaus.resolve.rebar.beams import frame_of_ring, lay_beam
from typehaus.resolve.rebar.cages import lay_column, lay_dowels
from typehaus.resolve.rebar.mats import lay_mat
from typehaus.resolve.rebar.records import ResolvedRebarSet
from typehaus.resolve.rebar.stock import Sink
from typehaus.resolve.rebar.walls import lay_wall, structure_layer, wall_frame

_IN = 0.0254
DEFAULT_COVER_IN = 1.5
DEFAULT_FC_PSI = 3000.0
_SOLID_SCOPES = {"footing", "pad", "slab", "column", "beam"}


def cover_m(plan, element, spec=None) -> float:
    """The element's cover: its spec's, else its pour's mix, else 1 1/2"."""
    mix = concrete_spec_for(plan, element)
    own = getattr(spec, "cover", None)
    cover_in = (own.inches if own is not None
                else mix.cover.inches if mix is not None and mix.cover is not None
                else DEFAULT_COVER_IN)
    return cover_in * _IN


def _sink(plan, element, spec) -> tuple[Sink, float]:
    mix = concrete_spec_for(plan, element)
    stock = spec.stock_length.meters if spec.stock_length else det.DEFAULT_STOCK_IN * _IN
    sink = Sink(element.tag, (mix.bar_coating if mix is not None else None) or "",
                mix.fc_psi if mix is not None else DEFAULT_FC_PSI, spec.lap_class, stock)
    return sink, cover_m(plan, element, spec)


def resolve_rebar(model) -> list[ResolvedRebarSet]:
    plan = model.plan
    out: list[ResolvedRebarSet] = []
    reinforced = {el.tag for el in plan.all_elements()
                  if getattr(el, "reinforcement", None) is not None}
    junctions = {(j.storey, j.node_tag): j for j in model.junctions}
    openings: dict[str, list] = {}
    for o in model.openings:
        openings.setdefault(o.host_wall, []).append(o)

    for wall in model.walls:
        element = plan.by_tag(wall.tag)
        spec = getattr(element, "reinforcement", None)
        if spec is None or structure_layer(wall) is None:
            continue
        sink, cover = _sink(plan, element, spec)
        hooks = (_hook_dir(junctions, wall, element.start_node, reinforced),
                 _hook_dir(junctions, wall, element.end_node, reinforced))
        lay_wall(sink, spec, wall, cover, openings.get(wall.tag, ()), hooks)
        _wall_dowels(model, sink, spec, wall, cover)
        out.append(ResolvedRebarSet(wall.uid, wall.tag, element.element_kind, wall.storey,
                                    "foundation wall" if wall.is_foundation else "wall",
                                    tuple(sink.bars)))

    for solid in model.solids:
        if solid.derived or solid.category not in _SOLID_SCOPES:
            continue
        element = plan.by_tag(solid.tag)
        spec = getattr(element, "reinforcement", None) if element is not None else None
        if spec is None:
            continue
        if solid.category == "beam" and not is_cast_beam(plan, element):
            continue
        sink, cover = _sink(plan, element, spec)
        if solid.category == "column":
            feet = lay_column(sink, spec, solid, cover)
            _post_dowels(model, sink, spec, element, feet, cover)
        elif solid.category == "beam":
            lay_beam(sink, spec.bars, frame_of_ring(solid.outline, solid.z0_m, solid.z1_m), cover)
        else:
            lay_mat(sink, spec, solid, cover, ey=_strip_axis(model, element),
                    cap_thickness=_cap_thickness(plan, element))
        out.append(ResolvedRebarSet(solid.uid, solid.tag, element.element_kind, solid.storey,
                                    solid.category, tuple(sink.bars)))
    return out


def _strip_axis(model, element) -> tuple[float, float]:
    """A strip footing's ``y``: its wall's axis. Anything else is plan Y."""
    if element.element_kind != "Footing":
        return (0.0, 1.0)
    wall = model.wall(getattr(element, "under", ""))
    if wall is None:
        return (0.0, 1.0)
    (ax, ay), (bx, by) = wall.axis
    d = math.hypot(bx - ax, by - ay) or 1.0
    return ((bx - ax) / d, (by - ay) / d)


def _cap_thickness(plan, element) -> float | None:
    assembly = plan.library.resolve_assembly(getattr(element, "assembly", None) or "")
    if assembly is None:
        return None
    layer = next((ly for ly in assembly.layers if ly.function == LayerFunction.STRUCTURE), None)
    return layer.thickness.meters if layer is not None else None


def _hook_dir(junctions, wall, node_tag, reinforced) -> tuple[float, float] | None:
    """Hook into the first other reinforced, non-collinear wall at this node (D5)."""
    junction = junctions.get((wall.storey, node_tag))
    if junction is None or junction.kind in ("open_end", "collinear"):
        return None
    if wall.tag in junction.through_walls:
        return None
    mine = next((i for i in junction.incidents if i.wall_tag == wall.tag), None)
    for inc in junction.incidents:
        if inc.wall_tag == wall.tag or inc.wall_tag not in reinforced:
            continue
        if mine is not None and abs(mine.direction[0] * inc.direction[0]
                                    + mine.direction[1] * inc.direction[1]) > 0.95:
            continue
        return inc.direction
    return None


def _verticals_xy(sink: Sink) -> list[tuple[float, float]]:
    seen: dict[tuple[int, int], tuple[float, float]] = {}
    for bar in sink.bars:
        if bar.role == "vertical" and bar.piece == 1:
            x, y, _ = min(bar.path, key=lambda p: p[2])
            seen.setdefault((round(x * 1e4), round(y * 1e4)), (x, y))
    return list(seen.values())


def _wall_dowels(model, sink: Sink, spec, wall, cover: float) -> None:
    entries = [e for e in spec.bars if e.role == "dowels"]
    if not entries:
        return
    footing = next((s for s in model.solids if s.category == "footing"
                    and getattr(model.plan.by_tag(s.tag), "under", None) == wall.tag), None)
    if footing is None:
        return
    frame, ext = wall_frame(wall, structure_layer(wall))
    foot = (frame.n[0] * ext, frame.n[1] * ext)
    points = _verticals_xy(sink)
    base_cover = cover_m(model.plan, model.plan.by_tag(footing.tag),
                         getattr(model.plan.by_tag(footing.tag), "reinforcement", None))
    for entry in entries:
        lay_dowels(sink, entry, points, footing.z0_m, footing.z1_m, base_cover, foot)


def _post_dowels(model, sink: Sink, spec, element, feet, cover: float) -> None:
    entries = [e for e in spec.bars if e.role == "dowels"]
    base_tag = getattr(element, "supported_by", None)
    if not entries or not base_tag:
        return
    points = [(x, y) for x, y, _ in feet]
    base = next((s for s in model.solids if s.tag == base_tag and not s.derived), None)
    foot = (1.0, 0.0)
    if base is not None:
        bottom, top = base.z0_m, base.z1_m
        base_el = model.plan.by_tag(base_tag)
        cover = cover_m(model.plan, base_el, getattr(base_el, "reinforcement", None))
    else:
        wall = model.wall(base_tag)
        if wall is None:
            return
        # A column on a wall: the dowel develops straight down from the wall top, then turns.
        top = wall.z1_m
        ld = max(det.development_length_in(e.bar, sink.fc_psi) for e in entries) * _IN
        bottom = max(wall.z0_m, top - ld - cover)
        # The foot turns along the wall, the only way a 90° leg stays inside its thickness.
        (ax, ay), (bx, by) = wall.axis
        d = math.hypot(bx - ax, by - ay) or 1.0
        foot = ((bx - ax) / d, (by - ay) / d)
    for entry in entries:
        lay_dowels(sink, entry, points, bottom, top, cover, foot)
