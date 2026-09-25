"""Placeable bodies join the collision set: what a machine shares volume with, and what it
stands on.

* ``structural.placeable_interference`` — an Equipment body (``resolve/placeable_bodies``)
  entering a hard obstacle (``SolidCategory.collision == "hard"``: walls, decks, pours,
  beams, posts, runs, soffits, other bodies). WARN severity, FAIL result. Touching is not
  entering: the body is shrunk by 1/4" first. The only other pardon is a **relation** — the
  host wall, the ``soffit_ref``, a ``Connector.connects``, or any authored ``*_ref`` between
  the two — never a proximity guess.
* ``structural.equipment_support`` — a FLOOR-mounted body's underside, probed at its four
  plan quadrants against every ``supports_on_top`` top and every room's finished floor at
  the body's base. PASS at 3+ quadrants carried, FAIL at none, UNKNOWN in between.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from shapely.geometry import MultiPoint, Polygon, box

from typehaus.checks._authoring import advisory_fail, failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import AIR_SERVICE_DUCT_SYSTEM
from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedCanvasObject, ResolvedModel
from typehaus.resolve.placeable_bodies import bodied, body_prism
from typehaus.resolve.solid_categories import SOLID_CATEGORIES
from typehaus.resolve.sweep import sweep_legs

_CLASH = "structural.placeable_interference"
_SUPPORT = "structural.equipment_support"
_TOL_M = inch(0.25).meters
_SEAT_TOL_M = inch(0.5).meters
_MIN_AREA_M2 = inch(1).meters ** 2
_SEAT_MIN_M2 = inch(0.25).meters ** 2


@dataclass(frozen=True)
class Obstacle:
    tag: str
    kind: str
    shape: Polygon
    z0_m: float
    z1_m: float

    @property
    def owner(self) -> str:
        """The authored element: a routed run's solid is ``<run tag>-RUN``."""
        return self.tag.removesuffix("-RUN")


def _hard(kind: str) -> bool:
    row = SOLID_CATEGORIES.get(kind)
    return row is not None and row.collision == "hard"


def _carries(kind: str) -> bool:
    row = SOLID_CATEGORIES.get(kind)
    return row is not None and row.supports_on_top


def _poly(ring) -> Polygon | None:
    if len(ring) < 3:
        return None
    shape = Polygon(ring)
    if not shape.is_valid:
        shape = shape.buffer(0)
    return shape if shape.area > 1e-9 else None


def _solid_obstacles(model: ResolvedModel) -> Iterator[Obstacle]:
    for solid in model.solids:
        if solid.sweep is not None:
            for start, end in sweep_legs(solid.sweep):
                points = [*start, *end]
                hull = MultiPoint([(x, y) for x, y, _ in points]).convex_hull
                if hull.area > 1e-9:
                    zs = [z for _, _, z in points]
                    yield Obstacle(solid.tag, solid.category, hull, min(zs), max(zs))
            continue
        shape = _poly(solid.outline)
        if shape is not None:
            yield Obstacle(solid.tag, solid.category, shape, solid.z0_m, solid.z1_m)


def obstacles(model: ResolvedModel) -> list[Obstacle]:
    """Every solid of every kind, filtered by the caller: hard ones or carrying ones."""
    out = list(_solid_obstacles(model))
    for wall in model.walls:
        for layer in wall.body_layers():
            shape = _poly(layer.polygon)
            if shape is not None:
                z0 = layer.z0_m if layer.z0_m is not None else wall.z0_m
                z1 = layer.z1_m if layer.z1_m is not None else wall.z1_m
                out.append(Obstacle(wall.tag, "wall", shape, z0, z1))
    for floor in model.floors:
        shape = _poly(floor.deck_outline)
        if shape is not None and floor.deck_z1_m > floor.deck_z0_m:
            for void in floor.deck_voids:
                hole = _poly(void)
                if hole is not None:
                    shape = shape.difference(hole)
            out.append(Obstacle(floor.tag, "floor", shape, floor.deck_z0_m, floor.deck_z1_m))
    for obj in bodied(model):
        prism = body_prism(obj)
        if prism is not None:
            out.append(Obstacle(obj.tag, "equipment", Polygon(prism.ring),
                                prism.z0_m, prism.z1_m))
    return out


def _ref_values(element) -> Iterator[str]:
    for name in type(element).model_fields:
        if not (name.endswith(("_ref", "_refs")) or name == "connects"):
            continue
        value = getattr(element, name, None)
        if isinstance(value, str):
            yield value
        elif isinstance(value, (tuple, list)):
            yield from (v for v in value if isinstance(v, str))


def relations(ctx: CheckContext, tags: set[str]) -> dict[str, set[str]]:
    """tag -> every tag an authored reference ties it to, in either direction."""
    out: dict[str, set[str]] = {tag: set() for tag in tags}
    for element in ctx.plan.all_elements():
        refs = set(_ref_values(element))
        own = getattr(element, "tag", None)
        if own in out:
            out[own] |= refs
        # A Connector joins everything it names to everything else it names.
        joined = set(getattr(element, "connects", ()) or ())
        for tag in joined & tags:
            out[tag] |= joined
        for tag in refs & tags:
            if own:
                out[tag].add(own)
    return out


def _air_systems(ctx: CheckContext, obj: ResolvedCanvasObject) -> set[str]:
    """Duct systems a machine's declared air ports connect: a port is a relation to every run
    of its service (``mep.equipment_port_service`` grades which). Return and exhaust are one
    family, as ``resolve/mep_envelopes.joinable`` has them."""
    machine = next((t for t in ctx.plan.library.equipment_types if t.tag == obj.type_ref),
                   None)
    systems = {AIR_SERVICE_DUCT_SYSTEM[port.service].value for port in
               (machine.ports if machine is not None else ())
               if port.service in AIR_SERVICE_DUCT_SYSTEM}
    if systems & {"return", "exhaust"}:
        systems |= {"return", "exhaust"}
    return systems


def _hosts(obj: ResolvedCanvasObject) -> set[str]:
    return {obj.attachment_wall} if obj.attachment_wall else set()


@check(Tier.STRUCTURAL, _CLASH)
def placeable_interference(ctx: CheckContext) -> list[Finding]:
    bodies = bodied(ctx.model)
    if not bodies:
        return [not_applicable(_CLASH, "the plan has no Equipment")]
    hard = [o for o in obstacles(ctx.model) if _hard(o.kind)]
    related = relations(ctx, {obj.tag for obj in bodies})
    out: list[Finding] = []
    graded = 0
    for obj in bodies:
        prism = body_prism(obj)
        if prism is None:
            out.append(unknown(_CLASH, f"{obj.tag}'s type states no height, so its body "
                                       "cannot be graded", tags=(obj.tag,),
                               fix="author a height on its EquipmentType"))
            continue
        graded += 1
        core = Polygon(prism.ring).buffer(-_TOL_M, join_style="mitre")
        z0, z1 = prism.z0_m + _TOL_M, prism.z1_m - _TOL_M
        pardoned = related[obj.tag] | _hosts(obj) | {obj.tag}
        air = _air_systems(ctx, obj)
        hits: dict[str, float] = {}
        for other in hard:
            if (other.owner in pardoned or other.z1_m <= z0 or other.z0_m >= z1
                    or (other.kind.startswith("duct_") and other.kind[5:] in air)):
                continue
            if not core.intersects(other.shape):
                continue
            area = core.intersection(other.shape).area
            if area > _MIN_AREA_M2:
                hits[other.tag] = max(hits.get(other.tag, 0.0), area)
        for tag, area in sorted(hits.items()):
            out.append(advisory_fail(
                _CLASH, f"{obj.tag}'s body shares {area / _MIN_AREA_M2:.0f} sq in of plan "
                        f"with {tag} over their common height", tags=(obj.tag, tag),
                fix="move the unit, or author the relation that makes the contact intended"))
    if not any(f.result.value == "fail" for f in out):
        out.append(passed(_CLASH, f"{graded} Equipment bodies clear every hard solid"))
    return out


def _quadrants(shape: Polygon) -> list[Polygon]:
    x0, y0, x1, y1 = shape.bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    boxes = (box(x0, y0, cx, cy), box(cx, y0, x1, cy), box(x0, cy, cx, y1), box(cx, cy, x1, y1))
    return [shape.intersection(b) for b in boxes]


def _seats(ctx: CheckContext, carriers: list[Obstacle], z0: float) -> list[Polygon]:
    """Every carrying top and room floor within reach of the body's underside."""
    from typehaus.resolve.room_floor import room_finished_floor_elevation

    seats = [o.shape for o in carriers if abs(o.z1_m - z0) <= _SEAT_TOL_M]
    for room in ctx.model.rooms:
        shape = _poly(room.clear_face or room.axis_face)
        if shape is not None and abs(room_finished_floor_elevation(ctx.model, room) - z0) \
                <= _SEAT_TOL_M:
            seats.append(shape)
    return seats


@check(Tier.STRUCTURAL, _SUPPORT)
def equipment_support(ctx: CheckContext) -> list[Finding]:
    standing = [obj for obj in bodied(ctx.model)
                if obj.mount is None or obj.mount.kind.value == "floor"]
    if not standing:
        return [not_applicable(_SUPPORT, "no Equipment is floor-mounted")]
    carriers = [o for o in obstacles(ctx.model) if _carries(o.kind)]
    out: list[Finding] = []
    for obj in standing:
        z0 = obj.body_z0_m if obj.body_z0_m is not None else obj.z_m
        seats = _seats(ctx, carriers, z0)
        body = Polygon(obj.footprint)
        centre = body.centroid
        carried = sum(1 for q in _quadrants(body)
                      if any(q.intersection(s).area > _SEAT_MIN_M2 for s in seats))
        centred = any(s.covers(centre) for s in seats)
        if carried >= 3:
            continue
        if carried == 0 and not centred:
            out.append(failed(
                _SUPPORT, f"{obj.tag} is floor-mounted at {z0 / inch(1).meters:.1f}\" with "
                          "nothing under its body at that height", tags=(obj.tag,),
                fix="model what it stands on (a pad, a stand's rails), or correct "
                    "Mount.elevation to the top of it"))
        else:
            out.append(unknown(
                _SUPPORT, f"{obj.tag} is carried under {carried} of its 4 quadrants",
                tags=(obj.tag,)))
    if not out:
        out.append(passed(_SUPPORT, f"all {len(standing)} floor-mounted Equipment bodies "
                                    "bear on a surface under 3+ quadrants"))
    return out
