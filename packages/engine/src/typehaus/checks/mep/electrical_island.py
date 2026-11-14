"""NEC 210.52(C)(2)-(C)(4): receptacles at a freestanding island."""

from __future__ import annotations

from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.electrical import _counts_toward_210_52, _warn_fail
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.nec import NEC, mark
from typehaus.resolve import room_perimeter
from typehaus.resolve.placeables import placed_xy

_NEAR_WALL_M = room_perimeter.NEAR_WALL_M
_FIXED_CABINET_FLOOR_CONTACT_M = room_perimeter.FLOOR_CONTACT_M

# How far past an island's carcass a receptacle may sit and still be serving it: an end-
# or side-mounted device projects an inch or two off the face, and anything much farther
# out is a wall receptacle that happens to be nearby. Kept well under _NEAR_WALL_M so a
# freestanding island (> _NEAR_WALL_M from every boundary) can never borrow one.
_ISLAND_RECEPTACLE_MARGIN_M = 12 * 0.0254


@check(Tier.ADVISORY, "electrical.island_receptacle")
def island_receptacle(ctx: CheckContext) -> list[Finding]:
    """Every freestanding work-surface island has a receptacle at its footprint.

    NEC 210.52(C)(2) stopped *requiring* an island or peninsular countertop receptacle in
    2023, but where none is installed it requires provisions for adding one, and
    210.52(C)(3) confines any receptacle that serves the countertop to on/above/in the
    counter surface. An island with nothing at all — no receptacle, no provision — is the
    thing worth flagging: the appliance ends up on an extension cord across the aisle.
    2026 210.52(C)(4) forbids a receptacle less than 24" below the countertop, so an end-
    panel device that high is refused, not counted.

    Population: ``FurnitureType.work_surface is True`` (the same type attribute
    ``_fixed_cabinet_intervals`` reads for the opposite purpose), sitting on the floor,
    standing free of every room boundary by more than ``_NEAR_WALL_M`` — a base run
    against a wall is the wall receptacles' problem and ``receptacle_spacing``'s beat. A
    peninsula (attached to a wall at one end) reads as near-wall here and is not graded.
    The unit graded is the RUN — carcasses chained within the filler tolerance — so a
    peninsula of several boxes is attached when any box of it is.
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
    receptacles_by_storey: dict[str, list] = {}
    for storey in ctx.plan.storeys:
        receptacles_by_storey[storey.tag] = [
            element for element in ctx.plan.storey_elements(storey.tag)
            if element.element_kind == "ElectricalDevice"
            and _counts_toward_210_52(ctx, element)]

    floor_z = {s.tag: s.elevation.meters for s in ctx.plan.storeys}
    # Absolute body tops: a carcass's is the counter, a device's is its box.
    tops = {obj.tag: obj.body_z1_m for obj in ctx.model.canvas_objects}
    out: list[Finding] = []
    islands = 0
    work_surfaces = 0
    carcasses: dict[str, list[tuple[str, Polygon]]] = {}
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
            if any(run.distance(boundary) <= _NEAR_WALL_M
                   for boundary in boundaries_by_storey.get(storey, [])):
                continue
            islands += 1
            label = " + ".join(tags)
            reach = run.buffer(_ISLAND_RECEPTACLE_MARGIN_M)
            near = [device for device in receptacles_by_storey.get(storey, [])
                    if reach.contains(Point(placed_xy(ctx.model, device)))]
            top = max((tops.get(tag) or 0.0 for tag in tags), default=0.0)
            face = run.buffer(_ON_CARCASS_M)  # (C)(4) bans a box on the island, not near it
            banned = [d.tag for d in near if _below_counter_band(tops.get(d.tag), top)
                      and face.contains(Point(placed_xy(ctx.model, d)))]
            if banned:
                out.append(_warn_fail(
                    cid, f"island {label}: {', '.join(banned)} sits less than 24\" below "
                         f"the countertop, which NEC {NEC.BELOW_COUNTERTOP} forbids",
                    (*tags, *banned)))
            if [d for d in near if d.tag not in banned]:
                out.append(_pass(cid, f"island {label} has a receptacle at its footprint",
                                 tags))
            elif not banned:
                out.append(_warn_fail(
                    cid, f"island {label} has no receptacle within its footprint — "
                         f"NEC {mark(NEC.ISLAND_PROVISION)} wants one (or provisions for one), and "
                         f"{mark(NEC.COUNTERTOP_RECEPTACLE_LOCATION)} wants any that serves the "
                         f"countertop on/above/in the counter surface", tags))
    if not islands:
        if work_surfaces:
            # Positive absence, not a missing input: the house's work-surface casework was
            # read and every piece of it stands against a room boundary. There is no island
            # here, so there is no 210.52(C)(2) island receptacle to want.
            return [_na(cid, f"{work_surfaces} work-surface unit(s) modeled and every one "
                             f"stands against a room boundary — this house has no "
                             f"freestanding island for {mark(NEC.ISLAND_PROVISION)} to govern")]
        # No work surfaces at all is a *gap*: a dwelling has counters, so their absence
        # means the casework is unmodeled rather than absent from the design.
        return [_unknown(cid, "no work-surface casework is modeled at all, so whether this "
                              "house has an island cannot be answered")]
    return out


_BELOW_COUNTER_M = 24 * 0.0254  # NEC 210.52(C)(4)
_ON_CARCASS_M = 2 * 0.0254  # a box on an end panel projects about this far


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
