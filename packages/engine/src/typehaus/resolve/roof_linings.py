"""What a rafter roof carries inside and under its joists, drawn: bay fill and sloped ceiling.

A rafter roof's ``Layer.cavity_fills`` share the rafter band's depth and a ``FollowRoof``
room's ceiling has no single plane, so neither had geometry: the takeoff billed both off
the layer stacks while the viewer showed bare joists. This stage draws them.

- **Bay fill**: one ``insulation`` solid per fill, every bay between two adjacent rafters'
  flange faces, run to the heel, stacked from the soffit in the authored (interior ->
  exterior) order. Each bay is a section extruded across it: blocking and the plate cut it at
  their own height (the foam fills over an eave block), a gable wall to the deck in plan, and
  the heel, out to the plate's inside face, is the air-control fill solid.
- **Sloped ceiling**: one ``ceiling`` solid per ``FollowRoof`` ceiling and per face no Room
  claims under the roof's ``default_lining`` (what ``takeoff/ceiling_areas.py`` bills), its
  top on the rafter soffit, as deep as its boards plumb, folded at the ridge.

All ``derived``: billed off the stacks already, and the section cuts the roof's own bands.
A truss roof's flat ceiling and attic fill are ``resolve/ceilings.py``'s.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, replace

from shapely.geometry import Polygon, box

from typehaus.model.enums import ControlLayer
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
_IN_BAY = ("blocking", "ridge_beam")  # framing that stands in a rafter bay at part height


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
    fills, offset = [], 0.0  # (index, fill, offset, thickness), soffit -> deck
    for index, fill in enumerate(band.cavity_fills, start=1):
        thickness = min((fill.thickness or band.thickness).meters, depth - offset)
        if thickness <= _EPS:
            break
        fills.append((index, fill, offset, thickness))
        offset += thickness
    if not fills:
        return []
    air = next((f for f in fills if ControlLayer.AIR in f[1].control), fills[-1])
    soffit = _soffit(model, roof)
    walls = _climbing_walls(model, roof, soffit, depth * plumb)
    blocks = [(Polygon(ring), z0, z1) for m in roof.members if m.category in _IN_BAY
              for ring, z0, z1 in (member_footprint(m),) if len(ring) >= 3]
    sheets: dict[int, list] = {f[0]: [] for f in fills}
    for bay in _bays(roof, band.framing.spacing.meters):
        for piece in _pieces(bay, walls, blocks):
            if isinstance(piece, Polygon):  # not a frame rectangle: the old plan extrusion
                _plan_sheets(piece, fills, soffit, plumb, sheets)
                continue
            for index, region in _sections(piece, fills, air, soffit, depth * plumb, plumb):
                sheets[index].extend(_extrude(piece, part) for part in _parts(region))
    return [_solid(f"{roof.uid}-bay-fill-{index}", f"INSUL-{roof.tag}-{index}", roof.storey,
                   "insulation", combine_sheets(sheets[index]), fill.material_ref, roof.tag)
            for index, fill, _o, _t in fills if sheets[index]]


@dataclass(frozen=True)
class _Bay:
    """One bay in its own frame: run ``u``, across ``n`` (left of ``u``), flange faces ``lo/hi``
    across, ``s0/s1`` along; ``seats`` are (heel s, plate inside-face s, plate top z)."""

    u: tuple[float, float]
    lo: float
    hi: float
    s0: float
    s1: float
    seats: tuple[tuple[float, float, float], ...] = ()
    obstacles: tuple = ()  # partial-height framing as (s0, s1, z0, z1) section boxes

    @property
    def n(self) -> tuple[float, float]:
        return (-self.u[1], self.u[0])

    def xy(self, s: float, c: float) -> tuple[float, float]:
        (ux, uy), (nx, ny) = self.u, self.n
        return (s * ux + c * nx, s * uy + c * ny)

    def sc(self, x: float, y: float) -> tuple[float, float]:
        (ux, uy), (nx, ny) = self.u, self.n
        return (x * ux + y * uy, x * nx + y * ny)

    def plan(self) -> Polygon:
        return Polygon([self.xy(s, c) for s, c in ((self.s0, self.lo), (self.s1, self.lo),
                                                   (self.s1, self.hi), (self.s0, self.hi))])


def _pieces(bay: _Bay, walls, blocks) -> list:
    """The bay less what stands in it. Framing spanning the bay at part height becomes a section
    box; a wall to the deck, or a block that stops short across it, cuts the plan. What is left
    is banded across at its corners: a frame rectangle stays a ``_Bay``, any other band is a
    plan ``Polygon`` clear of the plate (as the bays were before the heel was filled)."""
    rect = bay.plan()
    cut, boxes, spanning = [walls], [], []
    for footprint, z0, z1 in blocks:
        if not footprint.intersects(rect):
            continue
        hit = intersection(footprint, rect)
        if hit.area <= _EPS * _EPS:
            continue
        sc = [bay.sc(x, y) for x, y in hit.convex_hull.exterior.coords]
        ss, cs = [p[0] for p in sc], [p[1] for p in sc]
        if min(cs) <= bay.lo + 0.003 and max(cs) >= bay.hi - 0.003:
            boxes.append((min(ss), max(ss), z0, z1))
            spanning.append(footprint)
        else:
            cut.append(footprint)
    cut = [g for g in cut if not g.is_empty]
    rest = _simple(difference(rect, union_all(cut))) if cut else [rect]
    out = []
    for part in (band for whole in rest for band in _banded(bay, whole)):
        frame = Polygon([bay.sc(x, y) for x, y in part.exterior.coords])
        s0, c0, s1, c1 = frame.bounds
        if abs(frame.area - (s1 - s0) * (c1 - c0)) <= 1e-7:
            out.append(replace(bay, lo=c0, hi=c1, s0=s0, s1=s1, obstacles=tuple(boxes)))
            continue
        inside = [bay.s0, bay.s1]
        for heel, face, _z in bay.seats:
            inside = [max(inside[0], face), inside[1]] if heel < face \
                else [inside[0], min(inside[1], face)]
        strip = Polygon([bay.xy(s, c) for s, c in ((inside[0], c0 - 1), (inside[1], c0 - 1),
                                                   (inside[1], c1 + 1), (inside[0], c1 + 1))])
        if inside[1] > inside[0]:
            part = intersection(part, strip)
            out.extend(_simple(difference(part, union_all(spanning)) if spanning else part))
    return out


def _banded(bay: _Bay, part: Polygon) -> list[Polygon]:
    """``part`` cut along the run at each of its corners' across offsets."""
    cs = sorted({round(bay.sc(x, y)[1], 6) for x, y in part.exterior.coords})
    if len(cs) <= 2:
        return [part]
    reach = (bay.s0 - 1.0, bay.s1 + 1.0)
    return [piece for c0, c1 in zip(cs, cs[1:], strict=False) if c1 - c0 > 0.001
            for piece in _simple(intersection(part, Polygon(
                [bay.xy(s, c) for s, c in ((reach[0], c0), (reach[1], c0),
                                           (reach[1], c1), (reach[0], c1))])))]


def _sections(bay: _Bay, fills, air, soffit, deep: float, plumb: float):
    """Each fill's region in the bay's (s, z) section: the stacked band, less the framing at its
    height. In the heel zone, heel to plate inside face, the air-control fill takes the whole
    height — where the air barrier turns from the roof onto the wall's sheathing."""
    mid = (bay.lo + bay.hi) / 2
    z0, z1 = soffit(*bay.xy(bay.s0, mid)), soffit(*bay.xy(bay.s1, mid))

    def strip(a: float, b: float) -> Polygon:
        return Polygon([(bay.s0, z0 + a), (bay.s1, z1 + a), (bay.s1, z1 + b), (bay.s0, z0 + b)])

    low = min(z0, z1) - 10.0
    solid = [box(s0, za, s1, zb) for s0, s1, za, zb in bay.obstacles]
    solid += [box(min(heel, face), low, max(heel, face), top) for heel, face, top in bay.seats]
    region = difference(strip(0.0, deep), union_all(solid)) if solid else strip(0.0, deep)
    heel = union_all([box(min(h, f), low, max(h, f), max(z0, z1) + deep + 1.0)
                      for h, f, _t in bay.seats]) if bay.seats else None
    # down to the plate and blocks, below the soffit line where the seat lifts off the plate
    foamed = difference(intersection(strip(-5.0, deep), heel), union_all(solid)) \
        if heel is not None else None
    for index, _fill, offset, thickness in fills:
        piece = intersection(region, strip(offset * plumb, (offset + thickness) * plumb))
        if heel is not None:
            piece = union_all([difference(piece, heel), foamed]) \
                if index == air[0] else difference(piece, heel)
        yield index, piece


def _extrude(bay: _Bay, part: Polygon):
    (nx, ny), width = bay.n, bay.hi - bay.lo
    rings = [list(part.exterior.coords)[:-1], *(list(r.coords)[:-1] for r in part.interiors)]
    return polygon_sheet(rings, lambda s, z: (*bay.xy(s, bay.lo), z),
                         (width * nx, width * ny, 0.0))


def _plan_sheets(part: Polygon, fills, soffit, plumb: float, sheets: dict) -> None:
    for index, _fill, offset, thickness in fills:
        lift = offset * plumb
        sheets[index].append(polygon_sheet(
            [list(part.exterior.coords)[:-1]],
            lambda x, y, lift=lift: (x, y, soffit(x, y) + lift), (0.0, 0.0, thickness * plumb)))


def _parts(geometry) -> list[Polygon]:
    if isinstance(geometry, Polygon):
        geoms = [geometry]
    else:
        geoms = [g for g in getattr(geometry, "geoms", ()) if isinstance(g, Polygon)]
    return [g for g in geoms if g.area > 1e-7]


def _climbing_walls(model: ResolvedModel, roof: ResolvedRoof, soffit: Callable, deep: float):
    """Every wall whose top climbs past mid-bay toward the deck — a gable end, whose studs fill
    the end bay — cut in plan. An eave wall stops at its plate: that is the seat's section box."""
    def climbs(wall) -> bool:
        tops = (wall.top_z0_m, wall.top_z1_m)
        return any((wall.z1_m if top is None else top) > soffit(*point) + deep / 2
                   for top, point in zip(tops, (wall.axis[0], wall.axis[-1]), strict=True))

    rings = [layer.polygon for wall in model.walls if wall.storey == roof.storey and climbs(wall)
             for layer in wall.layers if len(layer.polygon) >= 3]
    return union_all([Polygon(ring) for ring in rings])


def _bays(roof: ResolvedRoof, spacing_m: float) -> list[_Bay]:
    """Each bay: flange face to flange face, over the run both rafters share, to the heel."""
    planes: dict[tuple[float, float], list] = {}
    for member in (m for m in roof.members if m.category == "rafter"):
        dx, dy = member.p1[0] - member.p0[0], member.p1[1] - member.p0[1]
        run = math.hypot(dx, dy)
        if run > _EPS:
            planes.setdefault((round(dx / run, 3), round(dy / run, 3)), []).append(member)
    bays = []
    for (ux, uy), rafters in planes.items():
        nx, ny = -uy, ux

        def across(m, nx=nx, ny=ny):
            return m.p0[0] * nx + m.p0[1] * ny

        def along(m, ux=ux, uy=uy):
            """The run, to the heel at a seated end; the seat as (heel, plate inside face, top)."""
            lo, hi = sorted((m.p0[0] * ux + m.p0[1] * uy, m.p1[0] * ux + m.p1[1] * uy))
            if m.seat is None:
                return lo, hi, ()
            heel = m.seat.heel[0] * ux + m.seat.heel[1] * uy
            plate = m.seat.bearing_run_m or m.seat.seat_run_m
            if heel - lo < hi - heel:
                return max(lo, heel), hi, ((heel, heel + plate, m.seat.plate_top_z_m),)
            return lo, min(hi, heel), ((heel, heel - plate, m.seat.plate_top_z_m),)

        rafters.sort(key=across)
        for a, b in zip(rafters, rafters[1:], strict=False):
            lo = across(a) + _flange(a) / 2
            hi = across(b) - _flange(b) / 2
            (a0, a1, sa), (b0, b1, sb) = along(a), along(b)
            s0, s1 = max(a0, b0), min(a1, b1)
            if hi - lo <= 0.005 or across(b) - across(a) > 1.5 * spacing_m or s1 - s0 <= _EPS:
                continue
            bays.append(_Bay((ux, uy), lo, hi, s0, s1, (*sa, *sb)))
    return bays


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

