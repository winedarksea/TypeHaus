"""What a wall header carries: roof, floors and point loads, walked down the bearing graph.

``stacking`` runs after ``framing``, so this cannot read ``model.stack_edges``. It reads what
exists at framing time — the resolved wall axes, the resolved roofs and stairs, and the
plan's ``bearing_refs`` — and the checks call the same walk on the finished model.

* A ``Roof`` or ``FloorSystem`` naming a wall or beam is a uniform load on it.
* A ``Beam`` running along the wall's line is uniform and carries what bears on it (the
  roof whose ridge it is included); a beam ending on the wall, a ``FloorOpening`` and a
  ``Stair`` are point loads, counted where their bearing falls inside the span.
* Then the walls above: on the next storey up of the same building that carries a wall on
  this line, every wall whose collinear run covers the span, recursively. Read off the
  line, not one stack edge, so an upper wall spanning two lower segments is found.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from typehaus.model.floors import FloorOpening, FloorSystem
from typehaus.model.spatial import Roof, Stair
from typehaus.model.structure import Beam
from typehaus.resolve.layout_lines import collinear_overlap
from typehaus.resolve.mep_bore_scope import outdoor_wall_tags

_AXIS_TOL_M = 0.5 * 0.0254  # stacking's raw-axis tolerance
_OVERLAP_M = 0.0254  # a run shorter than this touches, it does not carry
_END_M = 1.5 * 0.0254  # a point within a stud of a wall's end stands in its corner


@dataclass(frozen=True)
class HeaderCondition:
    """The derived load on one span of one wall."""

    exterior: bool
    roofs: tuple[str, ...] = ()
    #: (floor tag, "center" | "clear") per floor carried.
    floors: tuple[tuple[str, str], ...] = ()
    point_loads: tuple[str, ...] = ()
    building_width_m: float | None = None
    #: The walls above the load came down through.
    via: tuple[str, ...] = ()

    @property
    def carries(self) -> bool:
        return bool(self.roofs or self.floors or self.point_loads)

    def describe(self) -> str:
        parts = ([f"roof {', '.join(self.roofs)}"] if self.roofs else []) + [
            f"{tag} ({kind})" for tag, kind in self.floors]
        if self.point_loads:
            parts.append(f"point loads {', '.join(self.point_loads)}")
        text = "; ".join(parts) or "nothing"
        return text + (f", via {', '.join(self.via)}" if self.via else "")


@dataclass
class _Load:
    source: str
    point: bool
    roofs: tuple[str, ...] = ()
    floors: tuple[str, ...] = ()
    #: Plan points whose projection on the wall is the load's extent; empty = the whole wall.
    footprint: tuple[tuple[float, float], ...] = ()


@dataclass
class LoadIndex:
    """Every bearer's loads, indexed once per model."""

    plan: object
    model: object
    outdoor: frozenset[str] = frozenset()
    on: dict[str, list[_Load]] = field(default_factory=dict)
    floor_kind: dict[str, str] = field(default_factory=dict)
    widths: dict[str, float | None] = field(default_factory=dict)

    @classmethod
    def of(cls, plan, model) -> LoadIndex:
        index = cls(plan, model, outdoor_wall_tags(model))
        index._build()
        return index

    # --- index -----------------------------------------------------------------------
    def _build(self) -> None:
        plan, model = self.plan, self.model
        self.walls = {wall.tag: wall for wall in model.walls}
        self.nodes = {node.tag: node.position.xy_m for node in plan.elements_of_kind("Node")}
        self.storey_of = {el.tag: storey.tag for storey in plan.storeys
                          for el in plan.storey_elements(storey.tag)}
        self.beams = {el.tag: el for el in plan.all_elements() if isinstance(el, Beam)}
        resolved_roofs = {roof.tag: roof for roof in model.roofs}
        stairs = {stair.tag: stair for stair in model.stairs}
        beam_loads: dict[str, list[_Load]] = {}
        for el in plan.all_elements():
            if isinstance(el, Roof):
                roof = resolved_roofs.get(el.tag)
                load = _Load(el.tag, False, roofs=(el.tag,),
                             footprint=tuple(roof.footprint) if roof else ())
                self._add(el.bearing_refs, load, beam_loads)
                self.widths[el.tag] = self._roof_width(el)
                ridge = self._ridge_beam(roof) if roof else None
                if ridge is not None:
                    beam_loads.setdefault(ridge, []).append(_Load(el.tag, False, (el.tag,)))
            elif isinstance(el, FloorSystem) and el.joists is not None:
                refs = el.joists.bearing_refs
                self.floor_kind[el.tag] = ("center" if any(
                    ref in self.beams or (ref in self.walls and ref not in self.outdoor)
                    for ref in refs) else "clear")
                self.widths[el.tag] = self._floor_width(el)
                self._add(refs, _Load(el.tag, False, floors=(el.tag,),
                                      footprint=tuple(p.xy_m for p in el.outline)),
                          beam_loads)
            elif isinstance(el, FloorOpening):
                self._add(el.bearing_refs, _Load(el.tag, True, footprint=tuple(
                    p.xy_m for p in el.outline)), beam_loads)
            elif isinstance(el, Stair):
                stair = stairs.get(el.tag)
                self._add(el.bearing_refs, _Load(el.tag, True, footprint=tuple(
                    stair.outline) if stair else ()), beam_loads)
        for tag, beam in self.beams.items():
            roofs, floors = self._beam_carries(tag, beam_loads, set())
            ends = (self.nodes.get(beam.start_node), self.nodes.get(beam.end_node))
            if None in ends:
                continue
            for ref in beam.bearing_refs:
                wall = self.walls.get(ref)
                along = (wall is not None
                         and collinear_overlap(wall.axis, ends, _AXIS_TOL_M) is not None)
                load = _Load(tag, not along, roofs, floors, footprint=ends)
                if wall is not None and not along:
                    load.footprint = (min(ends, key=lambda p: _line_distance(wall.axis, p)),)
                self.on.setdefault(ref, []).append(load)

    def _add(self, refs, load: _Load, beam_loads: dict[str, list[_Load]]) -> None:
        for ref in refs:
            target = beam_loads if ref in self.beams else self.on
            target.setdefault(ref, []).append(load)

    def _beam_carries(self, tag: str, beam_loads, seen: set[str]):
        roofs: dict[str, None] = {}
        floors: dict[str, None] = {}
        seen.add(tag)
        for load in beam_loads.get(tag, ()):
            roofs.update(dict.fromkeys(load.roofs))
            floors.update(dict.fromkeys(load.floors))
        for other, beam in self.beams.items():
            if other in seen or tag not in beam.bearing_refs:
                continue
            more_roofs, more_floors = self._beam_carries(other, beam_loads, seen)
            roofs.update(dict.fromkeys(more_roofs))
            floors.update(dict.fromkeys(more_floors))
        return tuple(roofs), tuple(floors)

    def _ridge_beam(self, roof) -> str | None:
        from typehaus.resolve.framing.roof import _find_ridge_beam

        found = _find_ridge_beam(self.model, roof)
        return found[0].tag if found else None

    def _line_coordinate(self, ref: str, axis: int) -> float | None:
        wall = self.walls.get(ref)
        if wall is not None:
            return (wall.axis[0][axis] + wall.axis[1][axis]) / 2
        beam = self.beams.get(ref)
        ends = (self.nodes.get(beam.start_node), self.nodes.get(beam.end_node)) if beam else ()
        return (ends[0][axis] + ends[1][axis]) / 2 if ends and None not in ends else None

    def _roof_width(self, roof: Roof) -> float | None:
        """Bearing line to bearing line, perpendicular to the ridge (note c)."""
        axis = 1 if roof.ridge_direction == "x" else 0
        lines = [c for ref in roof.bearing_refs
                 if (c := self._line_coordinate(ref, axis)) is not None]
        return max(lines) - min(lines) if len(lines) > 1 else None

    def _floor_width(self, floor: FloorSystem) -> float | None:
        """The storey's whole deck across its joists: a half-house floor framing to a centre
        bearing still sits in a building as wide as both halves."""
        axis = 0 if floor.joists.direction == "x" else 1
        storey = self.storey_of.get(floor.tag)
        coords: list[float] = []
        for el in self.plan.storey_elements(storey) if storey else ():
            if (isinstance(el, FloorSystem) and el.joists is not None
                    and el.joists.direction == floor.joists.direction):
                coords += [p.xy_m[axis] for p in el.outline]
        if not coords:
            coords = [p[axis] for wall in self.walls.values() if wall.storey == storey
                      for p in wall.axis]
        return max(coords) - min(coords) if coords else None

    # --- walk ------------------------------------------------------------------------
    def walls_above(self, wall) -> list[tuple[object, tuple[float, float]]]:
        """(upper wall, run on ``wall``) on the next storey up that carries this line."""
        plan = self.plan
        building = plan.building_of(wall.storey)
        here = plan.storey(wall.storey).elevation.meters
        above = sorted((s for s in plan.storeys_of(building) if s.elevation.meters > here),
                       key=lambda s: s.elevation.meters)
        for storey in above:
            runs = [(upper, run) for upper in self.walls.values() if upper.storey == storey.tag
                    and (run := collinear_overlap(wall.axis, upper.axis, _AXIS_TOL_M))
                    and run[1] - run[0] > _OVERLAP_M]
            if runs:
                return runs
        return []

    def condition(self, wall, lo_m: float, hi_m: float) -> HeaderCondition:
        roofs, floors, points, via = self._walk(wall, lo_m, hi_m, set())
        widths = [w for tag in (*roofs, *floors) if (w := self.widths.get(tag)) is not None]
        # A floor is a LEVEL: two half-decks framing to one centre bearing are one floor.
        levels: dict[str, list[str]] = {}
        for tag in floors:
            levels.setdefault(self.storey_of.get(tag, tag), []).append(tag)
        return HeaderCondition(
            exterior=wall.tag in self.outdoor, roofs=tuple(roofs),
            floors=tuple(("+".join(tags), "center" if any(
                self.floor_kind.get(tag) == "center" for tag in tags) else "clear")
                for tags in levels.values()),
            point_loads=tuple(points), building_width_m=max(widths) if widths else None,
            via=tuple(via))

    def _walk(self, wall, lo: float, hi: float, seen: set[str]):
        roofs: dict[str, None] = {}
        floors: dict[str, None] = {}
        points: dict[str, None] = {}
        via: dict[str, None] = {}
        seen.add(wall.tag)
        for load in self.on.get(wall.tag, ()):
            a, b = _extent(wall.axis, load.footprint, lo, hi)
            if load.point:
                if (a <= hi + 1e-6 and b >= lo - 1e-6
                        and not self._on_a_bearing_corner(wall, a, b)):
                    points[load.source] = None
                continue
            if min(b, hi) - max(a, lo) > _OVERLAP_M:
                roofs.update(dict.fromkeys(load.roofs))
                floors.update(dict.fromkeys(load.floors))
        for upper, (a, b) in self.walls_above(wall):
            run_lo, run_hi = max(a, lo), min(b, hi)
            if run_hi - run_lo <= _OVERLAP_M or upper.tag in seen:
                continue
            ends = sorted(_station(upper.axis, _point(wall.axis, s)) for s in (run_lo, run_hi))
            sub = self._walk(upper, ends[0], ends[1], seen)
            for target, found in zip((roofs, floors, points, via), sub, strict=True):
                target.update(dict.fromkeys(found))
            via[upper.tag] = None
        return roofs, floors, points, via


    def _on_a_bearing_corner(self, wall, a: float, b: float) -> bool:
        """A point landing on the wall's end where a BEARING wall meets it is that wall's:
        the corner post carries it, not the run behind it (BM-S-BATH-E at N-S-BA1)."""
        from typehaus.model.enums import StructuralRole

        length = math.dist(*wall.axis)
        end = (0.0 if b <= _END_M else length if a >= length - _END_M else None)
        if end is None:
            return False
        corner = _point(wall.axis, end)
        return any(
            other.tag != wall.tag and other.storey == wall.storey
            and _line_distance(other.axis, corner) <= _AXIS_TOL_M
            and -_AXIS_TOL_M <= _station(other.axis, corner)
            <= math.dist(*other.axis) + _AXIS_TOL_M
            and getattr(self.plan.by_tag(other.tag), "structural_role", None)
            is StructuralRole.BEARING
            for other in self.walls.values())


def _point(axis, station: float) -> tuple[float, float]:
    (x0, y0), (x1, y1) = axis
    run = math.dist(axis[0], axis[1]) or 1.0
    return x0 + (x1 - x0) * station / run, y0 + (y1 - y0) * station / run


def _station(axis, point) -> float:
    (x0, y0), (x1, y1) = axis
    run = math.dist(axis[0], axis[1]) or 1.0
    return ((point[0] - x0) * (x1 - x0) + (point[1] - y0) * (y1 - y0)) / run


def _line_distance(axis, point) -> float:
    (x0, y0), (x1, y1) = axis
    run = math.dist(axis[0], axis[1]) or 1.0
    return abs((point[0] - x0) * (y1 - y0) - (point[1] - y0) * (x1 - x0)) / run


def _extent(axis, footprint, lo: float, hi: float) -> tuple[float, float]:
    if not footprint:
        return lo, hi
    stations = [_station(axis, p) for p in footprint]
    return min(stations), max(stations)
