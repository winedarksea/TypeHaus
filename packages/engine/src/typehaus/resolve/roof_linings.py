"""What a rafter roof carries inside and under its joists, drawn: bay fill and sloped ceiling.

A rafter roof's ``Layer.cavity_fills`` share the rafter band's depth and a ``FollowRoof``
room's ceiling has no single plane, so neither had geometry: the takeoff billed both off
the layer stacks while the viewer showed bare joists. This stage draws them.

- **Bay fill**: one ``insulation`` solid per fill, every bay between two adjacent rafters'
  flange faces, inside the eave plate, clear of blocking and gable walls, stacked from the
  soffit in the authored (interior -> exterior) order.
- **Sloped ceiling**: one ``ceiling`` solid per ``FollowRoof`` ceiling and per face no Room
  claims under the roof's ``default_lining`` (what ``takeoff/ceiling_areas.py`` bills), its
  top on the rafter soffit, as deep as its boards plumb, folded at the ridge.

All ``derived``: billed off the stacks already, and the section cuts the roof's own bands.
A truss roof's flat ceiling and attic fill are ``resolve/ceilings.py``'s.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from shapely.geometry import Polygon, box

from typehaus.model.refs import FollowRoof
from typehaus.resolve.ceiling_over import (
    ceiling_decks_over,
    finish_layer,
    polygon_parts,
    split_holes,
)
from typehaus.resolve.coatings import coating_tags, layer_depth_m
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.model import ResolvedModel, ResolvedRoof, ResolvedSolid
from typehaus.resolve.overlay import difference, intersection, union_all
from typehaus.resolve.roof_geometry import (
    roof_height_at,
    roof_is_trussed,
    roof_ridge_coordinate,
    roof_slope_factor,
    roof_structure_depth_m,
    roof_structure_framing,
)
from typehaus.resolve.rooms import room_faces
from typehaus.resolve.sheet_geometry import combine_sheets, polygon_sheet
from typehaus.resolve.wall_faces import storey_wall_mass

_EPS = 1e-6


def resolve_roof_linings(model: ResolvedModel) -> None:
    """Append each rafter roof's bay-fill and sloped-ceiling solids to ``model.solids``."""
    for roof in model.roofs:
        if len(roof.footprint) < 3 or roof_structure_framing(model, roof) is None \
                or roof_is_trussed(model, roof):
            continue
        model.solids.extend(_bay_fill(model, roof))
        model.solids.extend(_sloped_ceilings(model, roof))


def _soffit(model: ResolvedModel, roof: ResolvedRoof) -> Callable[[float, float], float]:
    """The rafter soffit's elevation at a plan point: the deck plane less the plumb depth."""
    plumb = roof_structure_depth_m(model, roof) * roof_slope_factor(roof)
    return lambda x, y: roof_height_at(roof, (x, y)) - plumb


def _bay_fill(model: ResolvedModel, roof: ResolvedRoof) -> list[ResolvedSolid]:
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    band = next((layer for layer in (assembly.layers if assembly else ())
                 if layer.framing is not None and layer.cavity_fills), None)
    if band is None:
        return []
    depth = roof_structure_depth_m(model, roof)
    plumb = roof_slope_factor(roof)
    soffit = _soffit(model, roof)
    cut = _in_the_bays(model, roof, soffit)
    bays = [part for quad in _bays(roof, band.framing.spacing.meters)
            for part in _simple(difference(Polygon(quad), cut))]
    if not bays:
        return []
    solids, offset = [], 0.0
    for index, fill in enumerate(band.cavity_fills, start=1):
        thickness = min((fill.thickness or band.thickness).meters, depth - offset)
        if thickness <= _EPS:
            break
        lift, rise = offset * plumb, thickness * plumb
        mesh = combine_sheets([
            polygon_sheet([list(bay.exterior.coords)[:-1]],
                          lambda x, y, lift=lift: (x, y, soffit(x, y) + lift), (0.0, 0.0, rise))
            for bay in bays])
        solids.append(_solid(f"{roof.uid}-bay-fill-{index}", f"INSUL-{roof.tag}-{index}",
                             roof.storey, "insulation", mesh, fill.material_ref, roof.tag))
        offset += thickness
    return solids


def _in_the_bays(model: ResolvedModel, roof: ResolvedRoof, soffit: Callable):
    """What else stands in the bays, in plan: the roof's blocking (eave, ridge) and every wall
    whose top climbs past the soffit to the deck — a gable end, whose studs fill the end bay."""
    def climbs(wall) -> bool:
        tops = (wall.top_z0_m, wall.top_z1_m)
        return any((wall.z1_m if top is None else top) > soffit(*point) + 0.005
                   for top, point in zip(tops, (wall.axis[0], wall.axis[-1]), strict=True))

    rings = [member_footprint(m)[0] for m in roof.members if m.category == "blocking"]
    rings += [layer.polygon for wall in model.walls if wall.storey == roof.storey and climbs(wall)
              for layer in wall.layers if len(layer.polygon) >= 3]
    return union_all([Polygon(ring) for ring in rings if len(ring) >= 3])


def _bays(roof: ResolvedRoof, spacing_m: float) -> list[tuple[tuple[float, float], ...]]:
    """Each bay's plan quad: flange face to flange face, over the run both rafters share."""
    planes: dict[tuple[float, float], list] = {}
    for member in (m for m in roof.members if m.category == "rafter"):
        dx, dy = member.p1[0] - member.p0[0], member.p1[1] - member.p0[1]
        run = math.hypot(dx, dy)
        if run > _EPS:
            planes.setdefault((round(dx / run, 3), round(dy / run, 3)), []).append(member)
    quads = []
    for (ux, uy), rafters in planes.items():
        nx, ny = -uy, ux

        def across(m, nx=nx, ny=ny):
            return m.p0[0] * nx + m.p0[1] * ny

        def along(m, ux=ux, uy=uy):
            """The run, less the plate a seated end bears on: the fill stops at its inside face."""
            lo, hi = sorted((m.p0[0] * ux + m.p0[1] * uy, m.p1[0] * ux + m.p1[1] * uy))
            if m.seat is not None:
                heel = m.seat.heel[0] * ux + m.seat.heel[1] * uy
                plate = m.seat.bearing_run_m or m.seat.seat_run_m
                if heel - lo < hi - heel:
                    lo = max(lo, heel + plate)
                else:
                    hi = min(hi, heel - plate)
            return lo, hi

        rafters.sort(key=across)
        for a, b in zip(rafters, rafters[1:], strict=False):
            lo = across(a) + _flange(a) / 2
            hi = across(b) - _flange(b) / 2
            s0, s1 = max(along(a)[0], along(b)[0]), min(along(a)[1], along(b)[1])
            if hi - lo <= 0.005 or across(b) - across(a) > 1.5 * spacing_m or s1 - s0 <= _EPS:
                continue
            quads.append(tuple((s * ux + c * nx, s * uy + c * ny)
                               for s, c in ((s0, lo), (s1, lo), (s1, hi), (s0, hi))))
    return quads


def _flange(member) -> float:
    section = cross_section(member.profile)
    return section.flange_width_m or section.width_m


def _sloped_ceilings(model: ResolvedModel, roof: ResolvedRoof) -> list[ResolvedSolid]:
    plan = model.plan
    coatings = coating_tags(plan.library)
    pieces = []  # (uid, tag, storey, polygon, layers)
    for ceiling in model.ceilings:
        room = plan.by_tag(ceiling.room_ref)
        if ceiling.z0_m is None and isinstance(getattr(room, "ceiling", None), FollowRoof) \
                and room.ceiling.roof_ref == roof.tag and len(ceiling.outline) >= 3:
            pieces.append((ceiling.uid, ceiling.tag, ceiling.storey, Polygon(ceiling.outline),
                           ceiling.layers))
    pieces += _unroomed(model, roof)
    soffit = _soffit(model, roof)
    plumb = roof_slope_factor(roof)
    solids = []
    for uid, tag, storey, polygon, layers in pieces:
        boards = tuple(layer for layer in layers if layer.material_ref not in coatings)
        deep = sum(layer_depth_m(plan.library, layer) for layer in boards) * plumb
        finish = finish_layer(boards)
        if deep <= _EPS or finish is None:
            continue
        sheets = [polygon_sheet([list(part.exterior.coords)[:-1]],
                                lambda x, y: (x, y, soffit(x, y)), (0.0, 0.0, -deep))
                  for half in _halves(roof, polygon) for part in _simple(half)]
        if sheets:
            solids.append(_solid(uid, tag, storey, "ceiling", combine_sheets(sheets),
                                 finish.material_ref, roof.tag))
    return solids


def _unroomed(model: ResolvedModel, roof: ResolvedRoof) -> list:
    """The roof's lining over each face no Room claims, net of the walls — as billed."""
    plan = model.plan
    assembly = plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    if assembly is None or not assembly.default_lining:
        return []
    claimed, open_faces = room_faces(plan, roof.storey)
    footprint = Polygon(roof.footprint)
    faces = [face for face in open_faces if footprint.contains(face.representative_point())
             and not ceiling_decks_over(plan, roof.storey, face)]
    if not faces:
        return []
    mass = storey_wall_mass(model, roof.storey, [face for _r, face in claimed] + open_faces)
    out = []
    for index, face in enumerate(faces, start=1):
        for nth, part in enumerate(_simple(difference(face, mass)), start=1):
            out.append((f"{roof.uid}-ceiling-{index}-{nth}", f"CEIL-{roof.tag}-{index}-{nth}",
                        roof.storey, part, tuple(assembly.default_lining)))
    return out


def _halves(roof: ResolvedRoof, polygon: Polygon) -> list:
    """``polygon`` cut at the ridge, so each piece lies on one plane."""
    ridge = roof_ridge_coordinate(roof)
    if ridge is None:
        return [polygon]
    minx, miny, maxx, maxy = polygon.bounds
    if roof.ridge_direction == "x":
        sides = (box(minx, miny, maxx, ridge), box(minx, ridge, maxx, maxy))
    else:
        sides = (box(minx, miny, ridge, maxy), box(ridge, miny, maxx, maxy))
    return [intersection(polygon, side) for side in sides]


def _simple(geometry) -> list[Polygon]:
    return [simple for part in polygon_parts(geometry) for simple in split_holes(part)
            if simple.area > _EPS]


def _solid(uid: str, tag: str, storey: str, category: str, mesh: GMesh,
           material: str, host: str) -> ResolvedSolid:
    xs = [p[0] for p in mesh.positions]
    ys = [p[1] for p in mesh.positions]
    zs = [p[2] for p in mesh.positions]
    outline = [(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))]
    return ResolvedSolid(uid, tag, storey, category, outline, min(zs), max(zs),
                         material=material, body_mesh=mesh, derived=True, host_ref=host)

