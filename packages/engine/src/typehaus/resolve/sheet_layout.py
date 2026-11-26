"""Structural sheathing laid sheet by sheet off its wall's framing (decision #146).

For every SHEATHING layer with a stated ``Layer.sheet_length`` (each ``-tee-i`` piece
apart): columns are walked from the corner where this wall's sheathing runs through
(``ResolvedJunction.sheathing_through``), each vertical break snapped back to the last
member face within ``member_face / 2 - min_edge_bearing``; a band taller than a sheet is
coursed, columns alternating bottom/top anchored so neighbouring horizontal joints stagger
(an all-backed anchoring wins). Openings cut pieces; a raked head trims them. The breaks
carry their backing for ``structural.sheathing_edge_support`` and the pieces feed the sheet
count in ``takeoff/sheet_goods.py``.

A CLADDING layer stating ``sheet_length`` is a panel siding and is laid the same way on the
framed layer it hangs on (its furring). Over horizontal furring with joint nailers a joint
anywhere a nailer fits counts as backed, so the columns keep the bare module from the start
end, and the nailers are derived at the joints (``resolve/sheet_layout_nailers.py``).
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from shapely.geometry import Polygon

from typehaus.findings import Finding, element_error
from typehaus.model.sheet_layout import SheetLayoutStandard
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_walls import body_top_at
from typehaus.resolve.model_sheet_layout import ResolvedSheetLayout, SheetBreak, SheetPiece
from typehaus.resolve.rainscreen_closures import panel_bottom_z
from typehaus.resolve.sheet_layout_backing import (
    backing_rects,
    face_frame,
    nearest,
    opening_rects,
    unbacked_length,
    unbacked_spans,
)
from typehaus.resolve.sheet_layout_nailers import (
    cladding_backing,
    end_stations,
    nailer_spans,
    nailer_spec,
    nailers_at,
    with_nailers,
)
from typehaus.resolve.sheet_layout_runs import Face, Run, build_runs, direction
from typehaus.resolve.sheet_layout_walk import pieces, walk, walk_centred
from typehaus.resolve.sheet_stock import SHEET_WIDTH_IN, layer_sheet_length_in, wall_layer

_GAP_TOL_M = 0.125 * M_PER_IN  # unbacked joint length under a panel gap's width is none
_PIECE_TOL_M = 0.125 * M_PER_IN
_PARALLEL = 0.99
_TOP_STEP_M = 1.0 * M_PER_IN  # a column's top is sampled this finely (a gable apex inside it)


def sheet_layout_standard(plan: Any) -> tuple[SheetLayoutStandard | None, list[Finding]]:
    """The house's one ``SheetLayoutStandard`` (or None), with its integrity finding."""
    found = [el for el in plan.all_elements() if isinstance(el, SheetLayoutStandard)]
    if len(found) > 1:
        tags = ", ".join(sorted(el.tag for el in found))
        return None, [element_error("integrity.sheet_layout_standard",
                                    f"a house declares at most one SheetLayoutStandard; "
                                    f"found {len(found)}: {tags}", found[0].tag)]
    return (found[0] if found else None), []


def layout_params(standard: SheetLayoutStandard | None) -> SimpleNamespace:
    std = standard or SheetLayoutStandard(tag="default")
    return SimpleNamespace(vertical=std.orientation == "vertical",
                           min_rip=std.min_rip_width.meters,
                           bearing=std.min_edge_bearing.meters,
                           stagger=std.stagger_min.meters,
                           start_at_through=std.start_at_through_end,
                           centre_cladding=std.centre_cladding,
                           tail=std.max_course_shortfall.meters)


def resolve_sheet_layouts(plan: Any, model: Any) -> list[Finding]:
    standard, findings = sheet_layout_standard(plan)
    params = layout_params(standard)
    faces = []
    for function in ("sheathing", "cladding"):
        laid = [(w, layer) for w in model.walls for layer in w.layers
                if layer.function == function and len(layer.polygon) >= 3]
        shapes = {id(layer): Polygon(layer.polygon).buffer(0.002) for _w, layer in laid}
        for wall, layer in laid:
            length_in = layer_sheet_length_in(
                wall_layer(plan, wall, layer.source_layer_name or layer.name))
            if length_in is None:
                continue
            z0, nailer = layer.band(wall)[0], None
            if function == "sheathing":
                structure = next((ly for ly in wall.layers
                                  if ly.function == "structure" and not ly.is_cavity), None)
            else:  # a panel stands on its base strip, over a screened rainscreen foot
                structure = cladding_backing(wall, layer)
                nailer = nailer_spec(plan, wall, structure)
                z0 = panel_bottom_z(model, wall, layer)
            faces.append(Face(wall, layer, structure, length_in * M_PER_IN, z0,
                              _clip_above(wall, layer, laid, shapes), nailer=nailer))
    nailers: dict[str, list] = {}
    model.sheet_layouts[:] = [lay_run(model, run, params, nailers) for run in build_runs(faces)]
    with_nailers(model, nailers)
    return findings


def _clip_above(wall, layer, sheathing, shapes) -> float:
    """The band top, held under a parallel wall's sheathing that starts inside it above:
    the upper storey's sheet owns their overlap (a subfloor edge both bands claim)."""
    z0, z1 = layer.band(wall)
    d = direction(wall)
    for other, other_layer in sheathing:
        start = other_layer.band(other)[0]
        if other is wall or not z0 + 0.01 < start < z1:
            continue
        od = direction(other)
        if abs(d[0] * od[0] + d[1] * od[1]) < _PARALLEL:
            continue
        if shapes[id(layer)].intersection(shapes[id(other_layer)]).area > 1e-5:
            z1 = start
    return z1


def _start_end(model, run: Run, params) -> str:
    """The run end where a wall's sheathing runs through an L, else its start."""
    if not params.start_at_through:
        return "start"
    ends = set()
    for face in run.faces:
        for j in model.junctions:
            if j.kind != "l" or j.sheathing_through != face.wall.tag:
                continue
            for inc in j.incidents:
                if inc.wall_tag == face.wall.tag:
                    point = face.wall.axis[0] if inc.endpoint == "start" else face.wall.axis[-1]
                    s = ((point[0] - run.origin[0]) * run.d[0]
                         + (point[1] - run.origin[1]) * run.d[1])
                    ends.add("start" if abs(s - run.lo) <= abs(s - run.hi) else "end")
    return "end" if ends == {"end"} else "start"


def lay_run(model, run: Run, params, nailers: dict[str, list] | None = None
            ) -> ResolvedSheetLayout:
    """One run's layout: columns along it, courses up each column. A cladding run's derived
    joint nailers are added to ``nailers`` by wall tag."""
    first = run.faces[0]
    lo, hi, z0 = run.lo, run.hi, first.z0
    sheet_w, sheet_l = SHEET_WIDTH_IN * M_PER_IN, first.sheet_l
    size_s, size_z = (sheet_w, sheet_l) if params.vertical else (sheet_l, sheet_w)
    rects, holes, frames = [], [], {}
    for face in run.faces:
        frame = (face_frame(face.layer, face.structure, run.origin, run.d)
                 if face.structure is not None else None)
        frames[id(face)] = frame
        if frame is not None:
            rects.extend(backing_rects(model, face.wall, frame, z0, face.top, face.lo, face.hi))
        holes.extend(opening_rects(model, face))

    def top(s: float) -> float:
        face = run.face_at(s)
        x, y = run.origin[0] + run.d[0] * s, run.origin[1] + run.d[1] * s
        return min(face.top, body_top_at(face.wall, x, y))

    ctx = SimpleNamespace(rects=rects, holes=holes, top=top, z0=z0, params=params,
                          size_s=size_s, size_z=size_z, framed=bool(rects),
                          nailer=first.nailer, run=run)
    centred = params.centre_cladding and first.layer.function == "cladding"
    start_end = "centre" if centred else _start_end(model, run, params)
    from_hi = start_end == "end"
    s_faces = [(r.s0, r.s1) for r in rects]
    if centred:
        s_breaks = walk_centred(lo, hi, size_s, s_faces, params.bearing,
                                lambda x: _vertical_cost(ctx, x), params.min_rip, _GAP_TOL_M)
    else:
        s_breaks = walk(lo, hi, size_s, s_faces, params.bearing,
                        lambda x: _vertical_cost(ctx, x), params.min_rip, _GAP_TOL_M,
                        from_hi=from_hi)
    derived = []
    if first.nailer is not None and ctx.framed:
        derived = (nailers_at(run, lambda f: frames[id(f)], first.nailer, ctx, s_breaks)
                   + nailers_at(run, lambda f: frames[id(f)], first.nailer, ctx,
                                end_stations(run, first.nailer), "end-"))
    for tag, member, rect in derived:
        rects.append(rect)
        if nailers is not None:
            nailers.setdefault(tag, []).append(member)
    columns = pieces(lo, hi, s_breaks, size_s)
    order = list(reversed(columns)) if from_hi else columns
    out_pieces, h_breaks, shortfall, previous = [], [], 0.0, []
    for k, (c0, c1) in enumerate(order):
        courses, joints, short = _column(ctx, c0, c1, prefer_top=k % 2 == 1, previous=previous)
        previous = [j.at for j in joints]
        shortfall = max(shortfall, short)
        h_breaks.extend(joints)
        coursed = len(courses) > 1
        out_pieces.extend(p for za, zb in courses
                          if (p := _piece(ctx, c0, c1, za, zb, coursed)))
    v_breaks = [_vertical_break(ctx, x) for x in s_breaks]
    return ResolvedSheetLayout(
        wall_tag=first.wall.tag, layer_name=first.layer.name,
        material_ref=first.layer.material_ref, thickness_m=first.layer.thickness_m,
        lo=lo, hi=hi, z0=z0, z1=max(f.top for f in run.faces), sheet_w_m=sheet_w,
        sheet_l_m=sheet_l, start_end=start_end,
        pieces=tuple(sorted(out_pieces, key=lambda p: (p.s0, p.z0))),
        vertical_breaks=tuple(v_breaks), horizontal_breaks=tuple(h_breaks),
        framed=ctx.framed, shortfall_m=shortfall, vertical=params.vertical,
        faces=tuple((f.wall.tag, f.layer.name, f.lo, f.hi) for f in run.faces),
        function=first.layer.function, nailers=tuple(m for _t, m, _r in derived))


def _joint_top(ctx, s: float) -> float:
    return ctx.top(s)


def _tops(ctx, c0: float, c1: float) -> list[tuple[float, float]]:
    """``(s, top)`` across a column, ends included: a gable's apex can fall inside it."""
    n = max(1, int((c1 - c0) / _TOP_STEP_M))
    return [(s, ctx.top(s)) for s in (c0 + (c1 - c0) * i / n for i in range(n + 1))]


def _peak(ctx, c0: float, c1: float) -> float:
    return max(t for _s, t in _tops(ctx, c0, c1))


def _vertical_cost(ctx, x: float) -> float:
    """Unbacked length of a vertical joint at ``x`` (the whole joint where unframed); none
    where a joint nailer fits."""
    if not ctx.framed:
        return _joint_top(ctx, x) - ctx.z0
    if ctx.nailer is not None and nailer_spans(ctx, ctx.nailer, x) is not None:
        return 0.0
    holes = [(h[1], h[2], h[3], h[4]) for h in ctx.holes]
    return unbacked_length(ctx.rects, True, x, ctx.z0, _joint_top(ctx, x),
                           ctx.params.bearing, holes)


def _horizontal_span(ctx, c0: float, c1: float, z: float) -> tuple[float, float] | None:
    """Where a course joint at ``z`` has panel above it across a column (a rake clips it)."""
    tops = _tops(ctx, c0, c1)
    above = [i for i, (_s, t) in enumerate(tops) if t > z]
    if not above:
        return None
    if len(above) == len(tops):
        return c0, c1

    def cross(i: int, j: int) -> float:  # where the top passes z between samples i and j
        (sa, ta), (sb, tb) = tops[i], tops[j]
        return sa + (sb - sa) * (z - ta) / (tb - ta) if tb != ta else sa

    lo, hi = above[0], above[-1]
    return (c0 if lo == 0 else cross(lo - 1, lo),
            c1 if hi == len(tops) - 1 else cross(hi, hi + 1))


def _horizontal_cost(ctx, c0: float, c1: float, z: float) -> float:
    span = _horizontal_span(ctx, c0, c1, z)
    if span is None:
        return 0.0
    if not ctx.framed:
        return span[1] - span[0]
    holes = [(h[3], h[4], h[1], h[2]) for h in ctx.holes]
    return unbacked_length(ctx.rects, False, z, span[0], span[1], ctx.params.bearing, holes)


def _column(ctx, c0: float, c1: float, prefer_top: bool, previous: list[float]):
    """``(courses, joints, shortfall)`` for one column, choosing its anchoring."""
    hi = _peak(ctx, c0, c1)
    faces = [(r.z0, r.z1) for r in ctx.rects if r.s0 < c1 and r.s1 > c0]
    options = []
    for from_top in (prefer_top, not prefer_top):
        breaks = walk(ctx.z0, hi, ctx.size_z, faces, ctx.params.bearing,
                      lambda z, a=c0, b=c1: _horizontal_cost(ctx, a, b, z), ctx.params.min_rip,
                      _GAP_TOL_M, from_hi=from_top, tail=ctx.params.tail)
        courses = pieces(ctx.z0, hi, breaks, ctx.size_z, from_hi=from_top and bool(breaks))
        joints = [_horizontal_break(ctx, c0, c1, z) for z in breaks]
        staggered = all(abs(z - p) >= ctx.params.stagger - 1e-6
                        for z in breaks for p in previous)
        backed = all(j.backed for j in joints)
        options.append(((backed, staggered), courses, joints))
        if not breaks:
            break
    best = max(options, key=lambda o: o[0])  # ties keep the preferred (first) anchoring
    covered = sum(b - a for a, b in best[1])
    return best[1], best[2], max(0.0, (hi - ctx.z0) - covered)


def _corner(edges, at: float) -> float | None:
    return min((abs(at - e) for e in edges), default=None)


def _vertical_break(ctx, x: float) -> SheetBreak:
    z1 = _joint_top(ctx, x)
    holes = [(h[1], h[2], h[3], h[4]) for h in ctx.holes]
    spans = (unbacked_spans(ctx.rects, True, x, ctx.z0, z1, ctx.params.bearing, holes)
             if ctx.framed else [(ctx.z0, z1)])
    missing = sum(b - a for a, b in spans)
    key, offset = nearest(ctx.rects, True, x, ctx.z0, z1)
    edges = [e for h in ctx.holes if h[4] > ctx.z0 and h[3] < z1 for e in (h[1], h[2])]
    return SheetBreak(x, ctx.z0, z1, "vertical", key, offset,
                      ctx.framed and missing <= _GAP_TOL_M, missing, _corner(edges, x),
                      tuple(spans))


def _horizontal_break(ctx, c0: float, c1: float, z: float) -> SheetBreak:
    span = _horizontal_span(ctx, c0, c1, z) or (c0, c0)
    holes = [(h[3], h[4], h[1], h[2]) for h in ctx.holes]
    spans = (unbacked_spans(ctx.rects, False, z, span[0], span[1], ctx.params.bearing, holes)
             if ctx.framed else [span])
    missing = sum(b - a for a, b in spans)
    key, offset = nearest(ctx.rects, False, z, span[0], span[1])
    edges = [e for h in ctx.holes if h[2] > span[0] and h[1] < span[1] for e in (h[3], h[4])]
    return SheetBreak(z, span[0], span[1], "horizontal", key, offset,
                      ctx.framed and missing <= _GAP_TOL_M, missing, _corner(edges, z),
                      tuple(spans))


def _piece(ctx, c0: float, c1: float, za: float, zb: float, coursed: bool
           ) -> SheetPiece | None:
    """A course remainder is ``short`` only in a coursed column: a lone course cut to a
    band shorter than the sheet still takes a whole sheet."""
    t0, t1 = min(zb, ctx.top(c0)), min(zb, ctx.top(c1))
    peak = min(zb, _peak(ctx, c0, c1))
    if peak <= za + _PIECE_TOL_M:
        return None
    t0, t1 = max(t0, za), max(t1, za)
    apex = peak if peak > max(t0, t1) + _PIECE_TOL_M else None  # a gable peak inside it
    cuts = tuple(h[0] for h in ctx.holes if h[1] < c1 and h[2] > c0 and h[3] < zb and h[4] > za)
    raked = apex is not None or abs(t0 - t1) > _PIECE_TOL_M or peak < zb - _PIECE_TOL_M
    if cuts or raked:
        kind = "cut"
    elif coursed and zb - za < ctx.size_z - _PIECE_TOL_M:
        kind = "short"
    elif c1 - c0 < ctx.size_s - _PIECE_TOL_M:
        kind = "rip"
    else:
        kind = "full"
    return SheetPiece(c0, c1, za, t0, t1, kind, cuts, apex)
