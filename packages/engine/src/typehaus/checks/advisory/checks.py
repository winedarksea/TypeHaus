"""Advisory checks — design intelligence, warn-only, reasoning shown (→ 12 §checks/advisory).

Opinions with arithmetic behind them, never authority. Each finding states *why* and is
individually suppressible in preferences.toml.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity


def _warn(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.FAIL)


@check(Tier.ADVISORY, "advisory.habitable_window")
def habitable_room_window(ctx: CheckContext) -> list[Finding]:
    """Habitable rooms should have an exterior window (natural light, R303)."""
    from typehaus.model.enums import Occupancy

    habitable = {Occupancy.BEDROOM, Occupancy.LIVING, Occupancy.KITCHEN,
                 Occupancy.DINING, Occupancy.OFFICE}
    out: list[Finding] = []
    has_window = any(not op.is_door for op in ctx.model.openings)
    for room in (e for e in ctx.plan.all_elements() if e.element_kind == "Room"):
        if room.occupancy in habitable and not has_window:
            out.append(_warn("advisory.habitable_window",
                             f"habitable room {room.tag} appears to have no window — "
                             "consider natural light/ventilation", (room.tag,)))
    return out


@check(Tier.ADVISORY, "advisory.window_size_variety")
def window_size_variety(ctx: CheckContext) -> list[Finding]:
    """Fewer unique window sizes = cheaper ordering (reported as a fact with a histogram)."""
    sizes: dict[tuple[float, float], int] = {}
    for op in ctx.model.openings:
        if not op.is_door:
            key = (round(op.width_m, 3), round(op.height_m, 3))
            sizes[key] = sizes.get(key, 0) + 1
    if len(sizes) <= 1:
        return []
    hist = ", ".join(f"{w*39.37:.0f}x{h*39.37:.0f}\"×{n}" for (w, h), n in sizes.items())
    return [_warn("advisory.window_size_variety",
                  f"{len(sizes)} unique window sizes — fewer eases ordering ({hist})")]


@check(Tier.ADVISORY, "advisory.control_continuity")
def control_layer_continuity(ctx: CheckContext) -> list[Finding]:
    """Warn where a tagged control layer dead-ends at a condition whose transition does
    not declare continuity (walks junctions and stack edges, → 11b)."""
    out: list[Finding] = []
    transitions = ctx.plan.library.transitions
    for cond in ctx.model.conditions:
        if cond.kind.value not in ("storey_stack", "assembly_change"):
            continue
        declared = any(
            _matches(t.condition_pattern, cond.key) and t.continuity for t in transitions
        )
        if not declared:
            out.append(_warn("advisory.control_continuity",
                             f"control-layer continuity not declared across {cond.key}",
                             cond.element_tags))
    return out


@check(Tier.ADVISORY, "advisory.wet_wall_depth")
def wet_wall_depth(ctx: CheckContext) -> list[Finding]:
    """Drain fixtures need a real service chase, not an assumed 2x4-wall stack."""
    from typehaus.model.enums import Service

    types = {item.tag: item for item in ctx.plan.library.fixture_types}
    required = ctx.preferences.plumbing.drain_stack_required_structure_in * 0.0254
    out: list[Finding] = []
    for fixture in (element for element in ctx.plan.all_elements()
                    if element.element_kind == "Fixture"):
        fixture_type = types.get(fixture.type_ref)
        if fixture_type is None or Service.DRAIN not in fixture_type.needs:
            continue
        if fixture.wall_ref is None:
            out.append(_warn("advisory.wet_wall_depth",
                             f"drain fixture {fixture.tag} has no wall_ref for a service chase",
                             (fixture.tag,)))
            continue
        wall = ctx.model.wall(fixture.wall_ref)
        if wall is None:
            out.append(_warn("advisory.wet_wall_depth",
                             f"drain fixture {fixture.tag} references missing wall {fixture.wall_ref}",
                             (fixture.tag, fixture.wall_ref)))
            continue
        structure = next((layer for layer in wall.layers if layer.function == "structure"), None)
        if structure is None or structure.thickness_m + 1e-9 < required:
            actual = structure.thickness_m / 0.0254 if structure is not None else 0.0
            out.append(_warn(
                "advisory.wet_wall_depth",
                f"drain fixture {fixture.tag} uses {fixture.wall_ref} with {actual:.1f}\" structure; "
                f"planning allowance requires {required / 0.0254:.1f}\" for its drain stack",
                (fixture.tag, fixture.wall_ref),
            ))
    return out


@check(Tier.ADVISORY, "advisory.fixture_room_unassigned")
def fixture_room_unassigned(ctx: CheckContext) -> list[Finding]:
    """A permit fixture schedule lists a room per fixture, so an unassignable one is worth
    saying out loud.  This is the finding that replaced ``Fixture.room`` being a required
    string: a drag that lands a fixture outside every resolvable room stays loadable and
    keeps its authored position, and the gap is reported here instead of at import time."""
    return [_warn("advisory.fixture_room_unassigned",
                  f"fixture {obj.tag} is in no room — the fixture schedule needs one; move it "
                  "inside a room or extend the room boundary", (obj.tag,))
            for obj in ctx.model.canvas_objects
            if obj.kind == "Fixture" and obj.room is None]


@check(Tier.ADVISORY, "advisory.floor_heat_fixture_keepout")
def floor_heat_fixture_keepout(ctx: CheckContext) -> list[Finding]:
    """Radiant wire zones must not run beneath a fixture's authored footprint."""
    from shapely.geometry import Polygon, box

    types = {item.tag: item for item in ctx.plan.library.fixture_types}
    fixtures = [
        (storey.tag, element)
        for storey in ctx.plan.storeys
        for element in ctx.plan.storey_elements(storey.tag)
        if element.element_kind == "Fixture"
    ]
    out: list[Finding] = []
    for zone in ctx.model.floor_heat:
        zone_polygon = Polygon(zone.zone)
        for storey, fixture in fixtures:
            if storey != zone.storey or fixture.type_ref not in types:
                continue
            width, depth = (value.meters for value in types[fixture.type_ref].footprint)
            x, y = fixture.position.xy_m
            footprint = box(x - width / 2, y - depth / 2, x + width / 2, y + depth / 2)
            if zone_polygon.intersects(footprint):
                out.append(_warn(
                    "advisory.floor_heat_fixture_keepout",
                    f"floor-heat zone {zone.tag} overlaps fixture {fixture.tag}; "
                    "exclude the fixture footprint from the heating loop",
                    (zone.tag, fixture.tag),
                ))
    return out


# Floor finishes that constrain a radiant zone under them, and why. Tile and sealed concrete
# are what radiant wants — dense, thin, thermally transparent — so they are deliberately not
# here. Everything else either caps the surface temperature the loop may run at or throttles
# how much of its output reaches the room.
_RADIANT_LIMITED_FINISHES: dict[str, str] = {
    "lvp": "vinyl plank is surface-temperature limited (manufacturers cap the floor around "
           "80-85 F); set the thermostat's floor-sensor limit accordingly or the plank can "
           "cup and the seams can open",
    "vinyl": "sheet vinyl is surface-temperature limited (manufacturers cap the floor around "
             "80-85 F); set the thermostat's floor-sensor limit accordingly",
    "oak": "solid wood over radiant is both temperature and moisture limited — it wants a "
           "capped surface temperature and a controlled shrinkage regime, or the strips gap "
           "in the heating season",
    "carpet": "carpet and pad insulate the loop from the room; the zone has to be sized for "
              "the covering's R-value or it will not deliver its rated output",
}


@check(Tier.ADVISORY, "advisory.floor_finish_over_radiant")
def floor_finish_over_radiant(ctx: CheckContext) -> list[Finding]:
    """Radiant zones under a temperature- or output-limited floor finish.

    Not a defect — every combination here is a legal one people build — but each carries a
    commissioning constraint that has to be decided before the floor goes down, which is
    exactly what an advisory is for.

    Matched by polygon rather than by ``FloorHeat.room_ref``: the ref is optional and
    ``ResolvedFloorHeat`` does not carry it at all, so a free-standing zone (the catlin
    house's FH-M-DINING, a loop in the middle of the living room with no room ref on it)
    would silently escape a ref lookup. One zone can also cross a doorway into a second
    finish, and the polygon test reports both.
    """
    from shapely.geometry import Polygon

    out: list[Finding] = []
    rooms = [(room, Polygon(room.clear_face))
             for room in ctx.model.rooms if len(room.clear_face) >= 3]
    for zone in ctx.model.floor_heat:
        if len(zone.zone) < 3:
            continue
        zone_polygon = Polygon(zone.zone)
        for room, face in rooms:
            if room.storey != zone.storey or not zone_polygon.intersects(face):
                continue
            reason = _RADIANT_LIMITED_FINISHES.get(room.floor_finish or "")
            if reason is None:
                continue
            out.append(_warn(
                "advisory.floor_finish_over_radiant",
                f"floor-heat zone {zone.tag} runs under {room.tag}'s "
                f"{room.floor_finish} floor: {reason}",
                (zone.tag, room.tag),
            ))
    return out


@check(Tier.ADVISORY, "advisory.clearance_overlap")
def clearance_overlap(ctx: CheckContext) -> list[Finding]:
    """Surface authored fixture/furniture use-zone conflicts in both CLI and canvas.

    Clearances are intentionally a planning envelope, not a code-compliance calculation:
    rotations and wall-side semantics remain authored decisions.  A bounding envelope catches
    the high-value case—another placed object occupies a declared use zone—without quietly
    asserting that every item has a universal code clearance.
    """
    from shapely.geometry import box

    fixtures = {item.tag: item for item in ctx.plan.library.fixture_types}
    furniture = {item.tag: item for item in ctx.plan.library.furniture_types}
    placed: list[tuple[str, object, tuple[float, float], tuple[float, float, float, float] | None]] = []
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            if element.element_kind == "Fixture":
                item = fixtures.get(element.type_ref)
            elif element.element_kind == "Furniture":
                item = furniture.get(element.type_ref)
            else:
                continue
            if item is None:
                continue
            footprint = tuple(value.meters for value in item.footprint)
            clearance = (tuple(value.meters for value in item.clearance)
                         if item.clearance is not None else None)
            placed.append((storey.tag, element, footprint, clearance))

    out: list[Finding] = []
    reported: set[tuple[str, str]] = set()
    for storey, source, footprint, clearance in placed:
        if clearance is None:
            continue
        front, back, left, right = clearance
        x, y = source.position.xy_m
        zone = box(x - footprint[0] / 2 - left, y - footprint[1] / 2 - back,
                   x + footprint[0] / 2 + right, y + footprint[1] / 2 + front)
        for other_storey, other, other_footprint, _ in placed:
            if other_storey != storey or other.uid == source.uid:
                continue
            ox, oy = other.position.xy_m
            other_box = box(ox - other_footprint[0] / 2, oy - other_footprint[1] / 2,
                            ox + other_footprint[0] / 2, oy + other_footprint[1] / 2)
            key = tuple(sorted((source.tag, other.tag)))
            if zone.intersects(other_box) and key not in reported:
                reported.add(key)
                out.append(_warn(
                    "advisory.clearance_overlap",
                    f"declared clearance for {source.tag} overlaps {other.tag}; review the use zone",
                    key,
                ))
    return out


def _polygon_centroid(polygon) -> tuple[float, float] | None:
    """Vertex mean — enough to locate a layer's thin rectangle relative to its neighbours."""
    if not polygon:
        return None
    return (sum(p[0] for p in polygon) / len(polygon),
            sum(p[1] for p in polygon) / len(polygon))


def _cladding_offset(wall) -> tuple[float, float] | None:
    """Innermost layer → cladding layer, i.e. the direction this wall calls "outdoors".

    ``None`` for walls with nothing to orient: a single-layer or uncladded assembly is
    symmetric, so no winding can put it on backwards.
    """
    layers = wall.depth_layers()
    cladding = next((layer for layer in reversed(layers) if layer.function == "cladding"), None)
    if cladding is None or len(layers) < 2 or cladding is layers[0]:
        return None
    inner = _polygon_centroid(layers[0].polygon)
    outer = _polygon_centroid(cladding.polygon)
    if inner is None or outer is None:
        return None
    return (outer[0] - inner[0], outer[1] - inner[1])


@check(Tier.ADVISORY, "advisory.cladding_side_mismatch")
def cladding_side_mismatch(ctx: CheckContext) -> list[Finding]:
    """Adjacent clad walls must put their cladding on the same side of the run they form.

    A wall's layers are laid out interior→exterior along its authored start→end direction
    (times the storey's outward sign, → resolve/orientation), so authoring one wall of a run
    backwards silently turns its stack inside out — face brick pointing at the porch, stucco
    at the weather. Nothing downstream notices, because each wall is individually well-formed
    and the storey still has a single outward sign. Comparing neighbours across a shared node
    catches it without having to decide which side of the run is outdoors: walk node ``a→n``
    then ``n→b`` and the cladding must sit on the same hand of both legs.
    """
    import math

    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        elements = ctx.plan.storey_elements(storey.tag)
        positions = {e.tag: e.position.xy_m for e in elements if e.element_kind == "Node"}
        # node tag -> [(wall tag, far-end node tag, cladding offset)]
        incident: dict[str, list[tuple[str, str, tuple[float, float]]]] = {}
        for element in elements:
            if element.element_kind not in ("Wall", "FoundationWall"):
                continue
            resolved = ctx.model.wall(element.tag)
            if resolved is None:
                continue
            offset = _cladding_offset(resolved)
            if offset is None:
                continue
            a, b = element.start_node, element.end_node
            if a not in positions or b not in positions or a == b:
                continue
            incident.setdefault(a, []).append((element.tag, b, offset))
            incident.setdefault(b, []).append((element.tag, a, offset))

        for node, legs in sorted(incident.items()):
            # Only an unambiguous two-wall corner/joint has one traversal; at a branch the
            # "same side" question has no single answer, so say nothing rather than guess.
            if len(legs) != 2:
                continue
            (tag_a, far_a, offset_a), (tag_b, far_b, offset_b) = legs
            here = positions[node]
            # Traverse the run far_a -> node -> far_b, then take each leg's cladding hand.
            hands = []
            for (far, offset, incoming) in ((far_a, offset_a, True), (far_b, offset_b, False)):
                direction = ((here[0] - positions[far][0], here[1] - positions[far][1])
                             if incoming
                             else (positions[far][0] - here[0], positions[far][1] - here[1]))
                length = math.hypot(*direction)
                if length < 1e-9:
                    break
                hands.append((direction[0] * offset[1] - direction[1] * offset[0]) / length)
            if len(hands) != 2 or min(abs(h) for h in hands) < 1e-9:
                continue
            if hands[0] * hands[1] < 0.0:
                out.append(_warn(
                    "advisory.cladding_side_mismatch",
                    f"{tag_a} and {tag_b} meet at {node} but their cladding faces opposite "
                    "sides of the run — one of them is authored end-to-start, so its layer "
                    "stack is inside out; swap that wall's start_node/end_node",
                    (tag_a, tag_b, node),
                ))
    return out


def _matches(pattern: str, key: str) -> bool:
    import fnmatch

    return fnmatch.fnmatch(key, pattern)
