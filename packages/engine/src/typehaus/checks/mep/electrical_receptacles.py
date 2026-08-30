"""CODE-tier electrical rule — E3901.6, the receptacle a lavatory basin must have.

Split from ``electrical_code.py`` (E3902 GFCI/AFCI) only to keep both files under the
repo's 500-line ceiling; the four helpers imported from it are shared deliberately rather
than duplicated, because "which room is this device in" and "would a cord pierce a wall"
must answer identically for both rules or the two findings contradict each other.

IRC 2021 E3901.6 / NEC 210.52(D): at least one receptacle outlet within 36" of the outside
edge of each lavatory basin, located on a wall or partition adjacent to the basin, on the
countertop, or on the side or face of the basin cabinet not more than 12" below the
countertop. E3901.1 items (3) and (4) are the counting rules that make the trap citable: a
receptacle "located within cabinets or cupboards", or "more than 5 1/2 ft above the floor",
does not count toward a required outlet.
"""

from __future__ import annotations

from typing import Any

from typehaus.checks.mep.electrical_code import (
    _finding,
    _pierces_a_wall,
    _room_of,
    _wall_barrier,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import Occupancy

# 210.52(D)'s reach, measured to the OUTSIDE EDGE of the basin.
_BASIN_REACH_M = 36 * 0.0254
# E3901.1 item (4): a receptacle more than 5 1/2 ft above the floor is not counted as a
# required outlet. A mirror-height outlet over a vanity is the pattern this guards.
_MAX_COUNTING_HEIGHT_M = 5.5 * 0.3048
# The plan symbols a lavatory basin is drawn with. A kitchen sink or a bar sink is not a
# lavatory and 210.52(D) does not reach it; the bathroom-occupancy gate below is what
# actually excludes them, and this is the second half of the same discrimination.
_BASIN_SYMBOLS = {"lavatory", "vanity"}


@check(Tier.CODE, "code.E3901_6_bathroom_receptacle")
def bathroom_basin_receptacle(ctx: CheckContext) -> list[Finding]:
    """E3901.6 — each lavatory basin has a countable receptacle within 36" of its edge.

    **Basin geometry is the whole vanity carcass, not the bowl.** The model carries no
    basin extent, so ``ResolvedCanvasObject.footprint`` — the case — is what the distance
    is measured to. The carcass is larger than the basin it holds, so a carcass-edge
    distance is a *lower* bound on the real 210.52(D) distance and this rule is permissive
    in exactly the direction E3902's centroid bug used to be. Tightening it means giving
    ``FixtureType`` a ``basin`` extent; until then, a PASS here means "passes at least as
    easily as the code asks", never the reverse.

    Four things disqualify a receptacle that is otherwise close enough, each citable:

    * it is in a different room — a cord does not reach through a wall (210.52(D) says
      "adjacent to", and ``_pierces_a_wall`` is the second, geometric half of that);
    * it is enclosed under a horizontal solid — a tub deck, a countertop overhang, a bench
      — which is E3901.1 item (3), "within cabinets or cupboards";
    * it is mounted more than 5 1/2 ft above the floor — E3901.1 item (4);
    * it is a floor outlet, which 210.52(D) does not list among the three locations.

    The enclosure test is *geometric* on purpose: nobody can forget to author it, and
    nobody can author it away. Its honest limit is that it sees an enclosure modelled as a
    solid over the device. A receptacle sealed inside a wall cavity behind an access panel,
    with nothing above it, is invisible to it; if that case ever appears in a plan, the
    answer is an authored ``ElectricalDevice.enclosed`` flag OR-ed with this one.
    """
    from shapely.geometry import Point, Polygon

    cid, code = "code.E3901_6_bathroom_receptacle", "E3901.6"
    bathrooms = {room.tag: room for room in ctx.model.rooms
                 if room.occupancy == Occupancy.BATHROOM.value}
    basins = _basins(ctx, bathrooms)
    if not basins:
        return [_finding(cid, Result.NOT_APPLICABLE,
                         "no lavatory basin is modeled in any bathroom", (), code)]

    rooms: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(room.clear_face) >= 3:
            rooms.setdefault(room.storey, []).append((room, Polygon(room.clear_face)))
    by_tag = {room.tag: room for room in ctx.model.rooms}
    barriers = _wall_barrier(ctx)
    devices = _receptacles(ctx, rooms, by_tag)
    enclosures = _enclosures(ctx)
    wall_bands = _wall_bands(ctx)
    floors = _floor_datums(ctx)

    out: list[Finding] = []
    for basin, basin_room in basins:
        carcass = Polygon(basin.footprint)
        best: tuple[float, Any, str] | None = None
        rejected: list[tuple[float, str, str]] = []
        for obj, room in devices:
            if obj.storey != basin.storey:
                continue
            distance = carcass.distance(Point(obj.position))
            if distance > _BASIN_REACH_M:
                continue
            why = _disqualified(obj, room, basin_room, carcass, enclosures,
                                floors, barriers.get(obj.storey))
            if why is not None:
                rejected.append((distance, obj.tag, why))
                continue
            where = _location_branch(obj, carcass, wall_bands.get(obj.storey, ()))
            if where is None:
                out.append(_finding(
                    cid, Result.UNKNOWN,
                    f"{obj.tag} is {_inches(distance)} from {basin.tag} and stands over "
                    "neither a wall nor open floor, so 210.52(D)'s cabinet-face branch "
                    "governs — and the basin countertop height it is measured from is not "
                    "modeled", (basin.tag, obj.tag), code,
                    f"state the countertop height of {basin.tag}"))
                best = best or (distance, obj, "")
                break
            if best is None or distance < best[0]:
                best = (distance, obj, where)
        if best is not None and best[2]:
            out.append(_finding(
                cid, Result.PASS,
                f"{basin.tag} is served by {best[1].tag} at {_inches(best[0])} "
                f"({best[2]})", (), code))
        elif best is None:
            out.append(_finding(cid, Result.FAIL, _fail_message(basin, rejected),
                                (basin.tag, basin_room.tag), code,
                                "add a 125V receptacle on the wall beside "
                                f"{basin.tag}, within 36\" of its edge"))
    return out


def _inches(metres: float) -> str:
    return f'{metres / 0.0254:.1f}"'


def _fail_message(basin: Any, rejected: list[tuple[float, str, str]]) -> str:
    head = (f"{basin.tag} has no receptacle within 36\" of its edge that counts toward "
            "210.52(D)")
    if not rejected:
        return f"{head} — no 125V receptacle is within reach at all"
    near = sorted(rejected)
    detail = "; ".join(f"{tag} at {_inches(d)} {why}" for d, tag, why in near[:3])
    return f"{head} — {detail}"


def _basins(ctx: CheckContext, bathrooms: dict[str, Any]) -> list[tuple[Any, Any]]:
    """Every resolved lavatory/vanity fixture that stands in a bathroom, with its room.

    The occupancy gate is what keeps a wet bar's ``vanity``-symbol cabinet out: 210.52(D)
    is a bathroom rule, and a bar sink is served by 210.52(C) instead.
    """
    types = {t.tag for t in ctx.plan.library.fixture_types
             if getattr(t, "plan_symbol", None) in _BASIN_SYMBOLS}
    out = []
    for obj in ctx.model.canvas_objects:
        if obj.kind != "Fixture" or obj.type_ref not in types:
            continue
        if len(obj.footprint) < 3:
            continue
        room = bathrooms.get(obj.room or "")
        if room is not None:
            out.append((obj, room))
    return out


def _receptacles(ctx: CheckContext, rooms: dict[str, list],
                 by_tag: dict[str, Any]) -> list[tuple[Any, Any]]:
    """(resolved object, resolved room) for every 125V receptacle in the plan.

    The AUTHORED element is what ``_counts_as_a_125v_receptacle`` and ``_room_of`` read —
    the first for the device kind and its type's rating, the second for an authored
    ``room=`` — while every distance here is measured against the RESOLVED body. Both are
    needed, and only the resolved one is carried out.
    """
    from shapely.geometry import Point

    from typehaus.checks.mep.electrical import _counts_as_a_125v_receptacle

    resolved = {obj.tag: obj for obj in ctx.model.canvas_objects
                if obj.kind == "ElectricalDevice"}
    out = []
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            if element.element_kind != "ElectricalDevice":
                continue
            if not _counts_as_a_125v_receptacle(ctx, element):
                continue
            obj = resolved.get(element.tag)
            if obj is None:
                continue
            room = _room_of(element, Point(obj.position), rooms.get(obj.storey, ()),
                            by_tag)
            out.append((obj, room))
    return out


def _enclosures(ctx: CheckContext) -> dict[str, list]:
    """Per storey, the horizontal solids a receptacle can be sealed under, as (poly, z)."""
    from shapely.geometry import Polygon

    out: dict[str, list] = {}
    for solid in ctx.model.solids:
        if solid.category not in {"slab", "pad"}:
            continue
        if len(solid.outline) < 3:
            continue
        out.setdefault(solid.storey, []).append((Polygon(solid.outline), solid.z0_m))
    return out


def _floor_datums(ctx: CheckContext) -> dict[str, float]:
    """Per storey, the elevation its rooms' floors sit at."""
    return {storey.tag: storey.elevation.meters for storey in ctx.plan.storeys}


def _wall_bands(ctx: CheckContext) -> dict[str, tuple]:
    """Per storey, (unioned layer footprint, z0, z1) for every resolved wall."""
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all

    out: dict[str, list] = {}
    for wall in ctx.model.walls:
        polys = [Polygon(layer.polygon) for layer in wall.layers
                 if len(layer.polygon) >= 3]
        if not polys:
            continue
        # ``union_all``, never a bare ``unary_union``: the published app runs GEOS 3.12,
        # where an overlay without a grid size is fatal on rings this thin.
        out.setdefault(wall.storey, []).append(
            (union_all(polys), wall.z0_m, wall.z1_m))
    return {storey: tuple(items) for storey, items in out.items()}


def _disqualified(obj: Any, room: Any, basin_room: Any, carcass: Any,
                  enclosures: dict[str, list], floors: dict[str, float],
                  barrier: Any) -> str | None:
    """Why this receptacle does not count toward 210.52(D), or None if it does."""
    from shapely.geometry import Point

    point = Point(obj.position)
    if room is None or room.tag != basin_room.tag:
        where = room.tag if room is not None else "no resolved room"
        return f"(in {where}, not {basin_room.tag})"
    for poly, z0 in enclosures.get(obj.storey, ()):
        if z0 <= obj.z_m:
            continue
        if z0 - floors.get(obj.storey, 0.0) > _MAX_COUNTING_HEIGHT_M:
            continue  # a ceiling or a high soffit is not a cupboard
        if poly.covers(point):
            return "(enclosed under a solid — E3901.1 item 3)"
    elevation = getattr(obj.mount, "elevation", None) if obj.mount else None
    height = elevation.meters if elevation is not None else (
        obj.z_m - floors.get(obj.storey, 0.0))
    if height > _MAX_COUNTING_HEIGHT_M:
        return '(more than 5 1/2 ft above the floor — E3901.1 item 4)'
    if obj.mount is not None and getattr(obj.mount.kind, "value", obj.mount.kind) == "floor":
        return "(a floor outlet — not one of 210.52(D)'s three locations)"
    if _pierces_a_wall(point, carcass, barrier):
        return "(a cord would have to pierce a wall)"
    return None


def _location_branch(obj: Any, carcass: Any, bands: tuple) -> str | None:
    """Which of 210.52(D)'s locations this receptacle occupies, or None for UNKNOWN.

    "On a wall or partition adjacent to the basin" and "on the countertop" both resolve to
    the same observable here — the device body stands against a wall solid at its own
    elevation. The third, "on the side or face of the basin cabinet", is the one the model
    cannot grade: it is bounded at 12" below the countertop, and ``FixtureType.height`` on
    every vanity is the whole assembly (cabinet + top + backsplash + faucet), not the deck.
    So a device standing inside the carcass with no wall behind it reports UNKNOWN rather
    than a guess.
    """
    from shapely.geometry import Point

    point = Point(obj.position)
    for body, z0, z1 in bands:
        if not (z0 - 1e-6 <= obj.z_m <= z1 + 1e-6):
            continue
        if body.distance(point) <= 0.05:
            return "on the wall adjacent to the basin"
    if carcass.covers(point):
        return None
    # Neither against a wall solid nor inside the cabinet: a receptacle standing free in
    # the bathroom, which is adjacent to the basin in every sense 210.52(D) asks about.
    # Say what was actually observed rather than naming a wall no geometry found.
    return "in the basin's own room, clear of its cabinet"
