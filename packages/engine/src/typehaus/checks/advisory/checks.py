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


def _matches(pattern: str, key: str) -> bool:
    import fnmatch

    return fnmatch.fnmatch(key, pattern)
