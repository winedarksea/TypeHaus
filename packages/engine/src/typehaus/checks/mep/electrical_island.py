"""NEC 210.52(C)(2)-(C)(4): receptacles at islands and peninsulas."""

from __future__ import annotations

import math
import warnings

from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.electrical import _counts_toward_210_52, _warn_fail
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.nec import NEC, mark
from typehaus.resolve import room_perimeter
from typehaus.resolve.placeables import placed_xy

_IN = 0.0254
_NEAR_WALL_M = room_perimeter.NEAR_WALL_M
_FIXED_CABINET_FLOOR_CONTACT_M = room_perimeter.FLOOR_CONTACT_M

# How far past a run's carcass a receptacle may sit and still be serving it: an end- or
# side-mounted device projects an inch or two off the face, and anything much farther out
# is a wall receptacle that happens to be nearby. Kept well under _NEAR_WALL_M so a
# freestanding island (> _NEAR_WALL_M from every boundary) can never borrow one.
_ISLAND_RECEPTACLE_MARGIN_M = 12 * _IN
# A peninsula touches a boundary within this, and only with an end panel (contact parallel to
# its carcasses' depth axis); a wall run touches with its back (parallel to their width).
_ATTACHED_M = 2 * _IN
_MIN_CONTACT_M = 2 * _ATTACHED_M  # an edge meeting the wall picks up the buffer's width
_BELOW_COUNTER_M = 24 * _IN  # NEC 210.52(C)(4)
_ABOVE_COUNTER_M = 20 * _IN  # NEC 210.52(C)(3)
_ON_CARCASS_M = 2 * _IN  # a box on an end panel projects about this far
_PROVISION_KINDS = frozenset({"junction_box"})


@check(Tier.ADVISORY, "electrical.island_receptacle")
def island_receptacle(ctx: CheckContext) -> list[Finding]:
    """Every island and peninsula has a countertop receptacle, or provisions for one.

    NEC 210.52(C)(2): islands and peninsulas need no receptacle, but any installed follows
    (C)(3) and (C)(4), and without one provisions for adding one are required. A receptacle
    counts only inside (C)(3)'s window (on or above the counter, box top at most 20" above
    it); a box less than 24" below the counter is refused under (C)(4). With none, a junction
    box at the run is read as the provision; with neither, the provision is not modelled,
    so UNKNOWN.

    Population: floor-standing runs of ``FurnitureType.work_surface is True`` carcasses
    (chained within the filler tolerance). An island stands more than ``_NEAR_WALL_M`` from
    every room boundary; a peninsula touches one only along its end (``_ATTACHED_M``). A
    peninsula leg joined to a wall run reads as part of the wall run and is not graded here.
    """
    from shapely.geometry import LineString, Point, Polygon

    cid = "electrical.island_receptacle"
    furniture_types = {t.tag: t for t in ctx.plan.library.furniture_types}
    if not furniture_types:
        return [_unknown(cid, "no furniture types in the library")]

    boundaries_by_storey: dict[str, list] = {}
    for room in ctx.model.rooms:
        ring = [tuple(point) for point in room.clear_face]
        if len(ring) >= 3:
            boundaries_by_storey.setdefault(room.storey, []).append(
                LineString(ring + [ring[0]]))
    devices_by_storey: dict[str, list] = {}
    for storey in ctx.plan.storeys:
        devices_by_storey[storey.tag] = [
            element for element in ctx.plan.storey_elements(storey.tag)
            if element.element_kind == "ElectricalDevice"]

    floor_z = {s.tag: s.elevation.meters for s in ctx.plan.storeys}
    # Absolute body bottoms and tops: a carcass's top is the counter, a device's its box.
    objects = {obj.tag: obj for obj in ctx.model.canvas_objects}
    out: list[Finding] = []
    graded = 0
    work_surfaces = 0
    carcasses: dict[str, list[tuple[str, Polygon]]] = {}
    rotations = {obj.tag: obj.rotation_degrees for obj in ctx.model.canvas_objects}
    for item in ctx.model.canvas_objects:
        item_type = furniture_types.get(item.type_ref or "")
        if item_type is None or item_type.work_surface is not True:
            continue
        work_surfaces += 1
        if item.z_m - floor_z.get(item.storey, 0.0) > _FIXED_CABINET_FLOOR_CONTACT_M:
            continue
        carcass = Polygon(item.footprint)
        if carcass.is_valid and not carcass.is_empty:
            carcasses.setdefault(item.storey, []).append((item.tag, carcass))
    for storey, items in carcasses.items():
        for tags, run in _work_surface_runs(items):
            members = [(tag, polygon, rotations[tag]) for tag, polygon in items if tag in tags]
            shape = _shape(run, boundaries_by_storey.get(storey, []), members)
            if shape is None:
                continue
            graded += 1
            label = f"{shape} {' + '.join(tags)}"
            top = max((_top(objects, tag) or 0.0 for tag in tags), default=0.0)
            reach = run.buffer(_ISLAND_RECEPTACLE_MARGIN_M)
            face = run.buffer(_ON_CARCASS_M)  # (C)(4) bans a box on the run, not near it
            near = [d for d in devices_by_storey.get(storey, [])
                    if reach.contains(Point(placed_xy(ctx.model, d)))]
            counting = [d for d in near if _counts_toward_210_52(ctx, d)]
            banned = [d.tag for d in counting
                      if _below_counter_band(_top(objects, d.tag), top)
                      and face.contains(Point(placed_xy(ctx.model, d)))]
            serving = [d.tag for d in counting if d.tag not in banned
                       and _in_window(objects.get(d.tag), top)]
            # A provision is at the run: a ceiling box overhead in plan is not one.
            provisions = [d.tag for d in near if d.kind.value in _PROVISION_KINDS
                          and (_top(objects, d.tag) or math.inf) <= top + _ABOVE_COUNTER_M]
            if banned:
                out.append(_warn_fail(
                    cid, f"{label}: {', '.join(banned)} sits less than 24\" below the "
                         f"countertop, which NEC {NEC.BELOW_COUNTERTOP} forbids",
                    (*tags, *banned)))
            if serving:
                out.append(_pass(cid, f"{label} has a countertop receptacle "
                                      f"({', '.join(sorted(serving))})", tags))
            elif provisions:
                out.append(_pass(cid, f"{label} has no countertop receptacle; "
                                      f"{', '.join(sorted(provisions))} is the provision "
                                      f"{mark(NEC.ISLAND_PROVISION)} asks for", tags))
            elif not banned:
                window = mark(NEC.COUNTERTOP_RECEPTACLE_LOCATION)
                out.append(_unknown(
                    cid, f"{label} has no receptacle within {window}'s window (on or above "
                         f"the counter, at most 20\" above); {mark(NEC.ISLAND_PROVISION)} "
                         "then wants provisions for one, and none (a junction box at the "
                         "run) is modelled", tags,
                    fix="add a countertop receptacle, or a capped box at the run as the "
                        "provision"))
    if not graded:
        if work_surfaces:
            # Positive absence: every piece of work-surface casework stands along a wall.
            return [_na(cid, f"{work_surfaces} work-surface unit(s) modeled and every one "
                             f"stands along a room boundary — this house has no island or "
                             f"peninsula for {mark(NEC.ISLAND_PROVISION)} to govern")]
        # No work surfaces at all is a *gap*: a dwelling has counters.
        return [_unknown(cid, "no work-surface casework is modeled at all, so whether this "
                              "house has an island cannot be answered")]
    return out


def _shape(run, boundaries: list, members: list) -> str | None:
    """"island", "peninsula", or None for a run along a wall.

    Reads which face meets the boundary, not the run's aspect: a lone B18's back is its
    short side too. The width axis is the run's rectangular carcasses' (an L corner unit has
    none); any contact along it is a back, so a wall run.
    """
    from shapely.geometry import LineString

    from typehaus.resolve.overlay import union_all

    if all(run.distance(boundary) > _NEAR_WALL_M for boundary in boundaries):
        return "island"
    touching = [boundary.buffer(_ATTACHED_M) for boundary in boundaries
                if run.distance(boundary) <= _ATTACHED_M]
    axis = _width_axis(members)
    if not touching or axis is None:
        return None
    zone = union_all(touching)
    coords = list(run.exterior.coords)
    end_contact = False
    for a, b in zip(coords, coords[1:], strict=False):
        dx, dy = b[0] - a[0], b[1] - a[1]
        edge = math.hypot(dx, dy)
        if edge < _MIN_CONTACT_M or zone.intersection(LineString([a, b])).length < _MIN_CONTACT_M:
            continue
        if abs(dx * axis[0] + dy * axis[1]) / edge > math.cos(math.radians(45)):
            return None  # a back on the boundary: a wall run
        end_contact = True
    return "peninsula" if end_contact else None


def _width_axis(members: list) -> tuple[float, float] | None:
    """The width direction most of the run's rectangular carcass area shares."""
    weight: dict[int, float] = {}
    for _, polygon, rotation in members:
        with warnings.catch_warnings():  # GEOS divides by zero on a collinear hull edge
            warnings.simplefilter("ignore", RuntimeWarning)
            hull = polygon.minimum_rotated_rectangle.area
        if polygon.area < 0.99 * hull:
            continue  # an L corner unit: no single width axis
        key = round(rotation) % 180
        weight[key] = weight.get(key, 0.0) + polygon.area
    if not weight:
        return None
    angle = math.radians(max(weight, key=weight.__getitem__))
    return math.cos(angle), math.sin(angle)


def _top(objects: dict, tag: str) -> float | None:
    obj = objects.get(tag)
    return None if obj is None else (obj.body_z1_m or obj.z_m)


def _in_window(obj, counter_top: float) -> bool:
    """(C)(3): on or above the counter and the box top at most 20" over it."""
    if obj is None or counter_top <= 0.0:
        return False
    return obj.z_m >= counter_top - 1e-3 and (obj.body_z1_m or obj.z_m) <= (
        counter_top + _ABOVE_COUNTER_M + 1e-6)


def _below_counter_band(device_top: float | None, counter_top: float) -> bool:
    """A box whose top is under the counter by less than 24"."""
    if device_top is None or counter_top <= 0.0:
        return False
    return counter_top - _BELOW_COUNTER_M < device_top < counter_top


def _work_surface_runs(items: list[tuple[str, object]]) -> list[tuple[tuple[str, ...], object]]:
    """Chain carcasses that abut within the filler tolerance into runs: (tags, union)."""
    from typehaus.resolve.overlay import union_all
    from typehaus.resolve.placeable_groups import RUN_GAP_TOLERANCE_M

    pad = RUN_GAP_TOLERANCE_M / 2.0
    merged = union_all([polygon.buffer(pad, join_style=2) for _, polygon in items])
    parts = list(getattr(merged, "geoms", [merged]))
    runs: list[tuple[tuple[str, ...], object]] = []
    for part in parts:
        members = [(tag, polygon) for tag, polygon in items if part.intersects(polygon)]
        runs.append((tuple(tag for tag, _ in members),
                     union_all([polygon for _, polygon in members])))
    return runs
