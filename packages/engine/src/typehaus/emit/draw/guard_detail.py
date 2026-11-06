"""A-606: one typical bay per guard type and mount, and a section per handrail type (S3-107).

Each bay is drawn at its type's widest support pitch with the resolver's own numbers: rail
centrelines from ``rail_rises``, the baluster count from ``derived_infill_count`` (the
R312.1.3 algebra the guard is drawn with), posts from the drawn post solids, and the base or
fascia bracket from the type's mount spec. A raked guard is shown level.
"""

from __future__ import annotations

import math
from collections import defaultdict

from typehaus.emit.draw.scene import ArchDimension, NamedPoint, Polyline, Scene, SceneBuilder, Text
from typehaus.emit.draw.schedules.stairs import _rail_faces
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.railing_hardware import inch_text, railing_hardware_rows

_RAIL = "A-RAIL"
_STRUCT = "S-FRAM"
_TEXT_PT = 6.0
_LINE_IN = 7.0   #: note line pitch under a panel, model inches
_COL_IN = 150.0  #: panel pitch: room for its notes at 1/4" = 1'-0"
_ROW_IN = 150.0  #: row pitch
_WRAP = 50       #: note characters per line


def _in(m: float) -> str:
    return inch_text(round(m / M_PER_IN * 16) / 16)


class _Row:
    """A builder that drops every node ``dy`` model inches: one row of panels."""

    def __init__(self, builder: SceneBuilder, dy: float) -> None:
        self._builder, self._dy = builder, dy

    def add(self, node):
        dy = self._dy
        if isinstance(node, Polyline):
            node = node.model_copy(update={"points": tuple((x, y + dy) for x, y in node.points)})
        elif isinstance(node, Text):
            node = node.model_copy(update={"anchor": (node.anchor[0], node.anchor[1] + dy)})
        elif isinstance(node, ArchDimension):
            p0, p1 = ((p[0], p[1] + dy) for p in (node.p0, node.p1))
            node = node.model_copy(update={"p0": p0, "p1": p1, "ends": (
                NamedPoint(xy=p0), NamedPoint(xy=p1))})
        return self._builder.add(node)


def _box(b: SceneBuilder, x0, y0, x1, y1, layer=_RAIL, weight=0.25, dashed=False, tag=None):
    b.add(Polyline(points=((x0, y0), (x1, y0), (x1, y1), (x0, y1)), closed=True, layer=layer,
                   lineweight=weight, linetype="DASHED" if dashed else "CONTINUOUS", tag=tag))


def _dim(b: SceneBuilder, p0, p1, offset, text):
    b.add(ArchDimension(ends=(NamedPoint(xy=p0), NamedPoint(xy=p1)), p0=p0, p1=p1,
                        offset=offset, text=text))


def _text(b: SceneBuilder, x, y, content, pt=_TEXT_PT):
    b.add(Text(anchor=(x, y), content=content, height_pt=pt))


def _groups(model: ResolvedModel):
    """``{(type or tag, mount): [railings]}`` — guards with posts, then handrails by type."""
    posts: dict[str, list] = defaultdict(list)
    for solid in model.solids:
        if solid.category == "railing" and solid.host_ref and "-POST" in solid.tag:
            posts[solid.host_ref].append(solid)
    guards: dict[tuple, list] = defaultdict(list)
    rails: dict[tuple, list] = defaultdict(list)
    for railing in sorted(model.plan.elements_of_kind("Railing"), key=lambda r: r.tag):
        key = (railing.type_ref or railing.tag, railing.mount)
        (guards if posts.get(railing.tag) else rails)[key].append(railing)
    return guards, rails, posts


def _pitch(model, railing) -> float:
    from typehaus.resolve.railings import guard_post_stations

    stations = guard_post_stations(model.plan.library, railing)
    return max((math.dist(a, b) for a, b in zip(stations, stations[1:], strict=False)),
               default=0.0)


def _hardware(model, type_ref: str, railings) -> list[str]:
    tags = {r.tag for r in railings}
    return [f"{row['count']} {row['part']}" + (f" {row['product']}" if row["product"] != "—"
                                               else "")
            + (f" {row['size']}" if row["size"] != "—" else "")
            for row in railing_hardware_rows(model)
            if row["type"] == type_ref and tags & set(row["railings"])]


def _guard_panel(b: SceneBuilder, model, key, railings, posts, ox: float) -> None:
    """Draw one bay at ``ox``, walking surface at y = 0."""
    from typehaus.resolve.railings.frame import rail_rises
    from typehaus.resolve.railings.infill import derived_infill_count
    from typehaus.resolve.railings.parts import railing_type, resolve_parts

    rep = max(railings, key=lambda r: (len(posts[r.tag]), r.tag))
    parts = resolve_parts(model, rep)
    product = railing_type(model.plan.library, rep)
    pitch = max(_pitch(model, r) for r in railings) / M_PER_IN
    pw = parts.post_section_m / M_PER_IN
    rs = parts.rail_section_m / M_PER_IN
    top, bottom, rail_h = (v / M_PER_IN if v is not None else None
                           for v in _rail_faces(model, rep))
    fascia = product.fascia_mount if product and rep.mount == "fascia" else None
    surface = product.surface_mount if product and rep.surface_post_mounts else None
    clearance = (surface.stair_bottom_clearance if surface and rep.serves_stair
                 else (fascia or surface).bottom_clearance if (fascia or surface) else None)
    rises = [r / M_PER_IN for r in rail_rises(
        rep, parts, rail_h * M_PER_IN, clearance.meters if clearance else 0.0,
        clearance is not None)]
    post = posts[rep.tag][0]
    post_bottom = rail_h - (post.z1_m - post.z0_m) / M_PER_IN
    b.add(Polyline(points=((ox - 12, 0), (ox + pitch + 12, 0)), layer=_STRUCT,
                   lineweight=0.5))
    for x in (ox, ox + pitch):
        _box(b, x - pw / 2, post_bottom, x + pw / 2, rail_h, weight=0.35)
    for rise in rises:
        _box(b, ox + pw / 2, rise - rs / 2, ox + pitch - pw / 2, rise + rs / 2)
    y0 = rises[-1] + rs / 2 if len(rises) > 1 else (clearance.inches if clearance else 0) + rs / 2
    y1 = rises[0] - rs / 2
    if rep.infill == "balusters" and rep.baluster_spacing is not None:
        width = parts.baluster_width_m / M_PER_IN
        clear = pitch - pw
        count = derived_infill_count(clear, width, rep.baluster_spacing.inches)
        gap = (clear - count * width) / (count + 1)
        for index in range(count):
            x = ox + pw / 2 + gap * (index + 1) + width * index
            _box(b, x, y0, x + width, y1, weight=0.18)
        if count:  # the gap left of the middle picket
            g0 = ox + pw / 2 + (gap + width) * (count // 2)
            _dim(b, (g0, y0 + 6), (g0 + gap, y0 + 6), 0, inch_text(round(gap * 16) / 16))
    elif rep.infill in ("panel", "mesh"):
        _box(b, ox + pw / 2, y0, ox + pitch - pw / 2, y1, weight=0.18, dashed=True)
    _dim(b, (ox - pw / 2, 0), (ox - pw / 2, top), -8, inch_text(round(top * 16) / 16))
    if bottom is not None and bottom > 0.05:
        _dim(b, (ox + pitch + pw / 2, 0), (ox + pitch + pw / 2, bottom), 12,
             inch_text(round(bottom * 16) / 16))
    _dim(b, (ox, top), (ox + pitch, top), 6, f"{_in(pitch * M_PER_IN)} C/C")
    if surface is not None:
        t = surface.display_base_thickness.inches
        for x in (ox, ox + pitch):
            _box(b, x - surface.base_width.inches / 2, 0, x + surface.base_width.inches / 2,
                 t, weight=0.35)
            for side in (-1, 1):
                sx = x + side * surface.display_hole_spacing.inches / 2
                length = (surface.wood_screw_length if rep.surface_post_mounts[0].substrate
                          == "wood" else surface.concrete_anchor_length).inches
                b.add(Polyline(points=((sx, t), (sx, t - length)), layer=_RAIL,
                               lineweight=0.18, linetype="DASHED"))
    elif fascia is not None:
        drop = rep.fascia_bracket_drop.inches if rep.fascia_bracket_drop else 0.0
        _box(b, ox - 12, -drop - fascia.overall_height.inches - 3, ox + pitch + 12, 0,
             layer=_STRUCT, dashed=True)
        for x in (ox, ox + pitch):
            w = fascia.flange_width.inches
            _box(b, x - w / 2, -drop - fascia.overall_height.inches, x + w / 2, -drop,
                 weight=0.35)
        _dim(b, (ox - pw / 2, 0), (ox - pw / 2, -drop), -8, inch_text(drop))
    else:
        _text(b, ox - 6, post_bottom - 4, "POST MOUNT NOT MODELLED")
    lines = [f"{key[0].removeprefix('RAILING-')} / {rep.mount.upper()} MOUNT",
             ", ".join(r.tag for r in railings),
             f"GUARD {inch_text(rail_h)} ABOVE "
             + ("NOSINGS" if rep.serves_stair else "WALKING SURFACE")
             + (f"; {rep.infill.upper()} <= {inch_text(rep.baluster_spacing.inches)} CLEAR"
                if rep.baluster_spacing else ""),
             *_hardware(model, key[0], railings)[:4]]
    if any(r.serves_stair for r in railings):
        lines.append("RAKED RUNS SHOWN LEVEL; RAILS FOLLOW THE NOSING LINE")
    low = min(post_bottom, -(rep.fascia_bracket_drop.inches if fascia and
                             rep.fascia_bracket_drop else 0) - 12)
    _notes(b, ox - 12, low - 8, lines)


def _handrail_panel(b: SceneBuilder, model, key, railings, ox: float) -> None:
    from typehaus.resolve.railings.parts import railing_type, resolve_parts

    rep = railings[0]
    parts = resolve_parts(model, rep)
    product = railing_type(model.plan.library, rep)
    top, _bottom, rail_h = (v / M_PER_IN if v is not None else None
                            for v in _rail_faces(model, rep))
    radius = parts.rail_section_m / M_PER_IN / 2
    b.add(Polyline(points=((ox - 10, 0), (ox + 14, 0)), layer=_STRUCT, lineweight=0.5))
    circle = tuple((ox + radius * math.cos(a / 16 * math.pi),
                    top - radius + radius * math.sin(a / 16 * math.pi)) for a in range(32))
    b.add(Polyline(points=circle, closed=True, layer=_RAIL, lineweight=0.35))
    _dim(b, (ox, 0), (ox, top), -6, inch_text(round(top * 16) / 16))
    pitch = max(_pitch(model, r) for r in railings)
    lines = [f"{key[0].removeprefix('RAILING-')} / {rep.mount.upper()}",
             ", ".join(r.tag for r in railings),
             f"DIA {_in(parts.rail_section_m)}; {inch_text(rail_h)} ABOVE NOSINGS",
             f"SUPPORTS {_in(pitch)} MAX C/C"
             + (f" (TYPE MAX {_in(product.bracket_spacing_max.meters)})"
                if product and product.bracket_spacing_max else ""),
             "ENDS: " + (" / ".join(sorted({str(getattr(t, "value", t)).replace("_", " ")
                                            for t in (rep.start_termination,
                                                      rep.end_termination) if t})) or "—"),
             *_hardware(model, key[0], railings)[:3]]
    _notes(b, ox - 10, -12, lines)


def _notes(b, x: float, y: float, lines: list[str]) -> None:
    """The panel's title (larger) and its notes, each wrapped to ``_WRAP``."""
    from textwrap import wrap

    row = 0
    for index, line in enumerate(lines):
        for part in wrap(line, _WRAP, subsequent_indent="  ") or [""]:
            _text(b, x, y - row * _LINE_IN, part, pt=_TEXT_PT + (1.5 if index == 0 else 0))
            row += 1


def has_guard_detail(model: ResolvedModel) -> bool:
    return any(True for _ in model.plan.elements_of_kind("Railing"))


def build_guard_detail(model: ResolvedModel) -> Scene:
    b = SceneBuilder(name="guard-detail", units="in")
    guards, rails, posts = _groups(model)
    for index, (key, railings) in enumerate(guards.items()):
        _guard_panel(_Row(b, -(index // 3) * _ROW_IN), model, key, railings, posts,
                     (index % 3) * _COL_IN)
    y = -((len(guards) + 2) // 3) * _ROW_IN
    for index, (key, railings) in enumerate(rails.items()):
        _handrail_panel(_Row(b, y), model, key, railings, index * _COL_IN)
    scene = b.build()
    return scene.model_copy(update={"notes": (
        "Heights: guards above the walking surface they stand on (R312.1.2); handrails "
        "above the nosing line (R311.7.8.1).",
        "Each bay is drawn at the widest support pitch its type has in the model.",
        "Baluster count and gap: the R312.1.3 algebra the guard is drawn with (4\" sphere).",
        "Counts per type for the railings listed; every mount and fastener: S-602.",
        "Schedule of every guard and handrail: A-605.",
    )})
