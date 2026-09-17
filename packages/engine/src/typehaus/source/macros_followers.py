"""What follows a moved placeable, and what an edit leaves behind (→ Stage 1 WP6).

A drag reports every relationship it touches as an :class:`Impact`: the drain sleeve and
run it carried, a ``wall_ref`` it walked away from, a wall attachment a free move dropped.
Electrical refs (``circuit``, ``kind``, ``mount``, ``wall_ref``, lighting ``controlled_by``)
are element fields or tag refs, so they survive a move untouched; no shared collector is
ever translated.
"""

from __future__ import annotations

from typehaus.model.enums import Service
from typehaus.model.plan import PlanModel
from typehaus.model.remap import Impact
from typehaus.model.spatial import Appliance, Fixture
from typehaus.quantities.length import m
from typehaus.resolve.mep import _PIPE_SLEEVE_SNAP_M
from typehaus.source.macros_common import _nodes, _point_expr_m, _walls
from typehaus.source.macros_geometry import _dist, _project_param
from typehaus.source.ops import PatchOp, RawExpr

# A move that takes an item this much farther from its ``wall_ref`` axis has left that wall.
# Measured as a change, not a distance: a wall_ref is the wet wall, and a shower or floor
# drain legitimately sits a metre or two off it (catlin: up to 2.3 m).
WALL_REF_REACH_M = 0.6


def _follower_ops(plan: PlanModel, storey: str, item: object,
                  new_xy: tuple[float, float]) -> tuple[list[PatchOp], list[Impact]]:
    """Ops that carry ``item``'s followers to ``new_xy``, and every impact of the free move."""
    ops, impacts = _drain_follower_ops(plan, storey, item, new_xy)
    wall_ref = getattr(item, "wall_ref", None)
    if wall_ref:
        axis = _wall_axis(plan, storey, wall_ref)
        before = _segment_distance(*axis, item.position.xy_m) if axis is not None else 0.0
        after = _segment_distance(*axis, new_xy) if axis is not None else 0.0
        if after - before > WALL_REF_REACH_M:
            impacts.append(Impact(
                item.tag, "left_behind",
                f"{item.tag} now sits {m(after).fmt()} off its wall_ref {wall_ref} — "
                "re-point wall_ref or reattach"))
    location = getattr(item, "location", None)
    attachment = getattr(location, "attachment", None)
    if attachment is not None:
        impacts.append(Impact(item.tag, "left_behind",
                              f"{item.tag} attachment to {attachment.wall_ref} dropped by a "
                              "free move"))
    return ops, impacts


def _wall_axis(plan: PlanModel, storey: str, wall_tag: str):
    wall = next((w for w in _walls(plan, storey) if w.tag == wall_tag), None)
    if wall is None:
        return None
    by_tag = {node.tag: node for node in _nodes(plan, storey)}
    start, end = by_tag.get(wall.start_node), by_tag.get(wall.end_node)
    if start is None or end is None:
        return None
    return start.position.xy_m, end.position.xy_m


def _segment_distance(p0, p1, q) -> float:
    t = max(0.0, min(1.0, _project_param(p0, p1, q)))
    return _dist(q, (p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1])))


# --- coupled drain followers -------------------------------------------------
#
# Dragging a floor-drained fixture moves a closet flange, and a closet flange is the top of
# a pipe that is already through the concrete: a pre-pour SleevePenetration at that point
# and a PipeRun dropping through it.  Neither is resolver-derived — both are authored plan
# geometry with their own coordinates — so a bare `position` patch silently decouples them.
# That is the 76c1871 defect: FX-M-BATH2-WC was nudged 6.46" in a drive-by edit, SP-M-WC2
# and PR-B-WC2-DRAIN stayed put, the plan still loaded and built, and only
# `mep.sleeve_alignment` (and one plumbing test) ever said so.  So the move carries them.
#
# A fixture with an authored ``drain_position`` is excluded on purpose: that field *is* the
# author saying where the waste leaves, independently of where the bowl sits, so moving the
# bowl is not a statement about the drain at all (it is how FX-M-BATH1-WC's wall-hung
# carrier stays put while its bowl slides along W-M-BAE).
#
# Followers are searched across the WHOLE plan, not the moved item's storey: the drain of a
# main-floor WC is hung from the basement ceiling, one storey down from the thing that moved.


def _placeable_type(plan: PlanModel, item: object) -> object | None:
    """The fixture/appliance catalog entry behind ``item``, for its service list."""
    return next((entry for entry in (*plan.library.fixture_types, *plan.library.appliance_types)
                 if entry.tag == getattr(item, "type_ref", None)), None)


def _convention_drain_point(plan: PlanModel, storey: str, item: object,
                            at_m: tuple[float, float]) -> tuple[float, float] | None:
    """Where ``item``'s waste would leave the floor if the unit stood at ``at_m``.

    The plan-side mirror of ``resolve/mep_sleeves.py::_expected_drain_point``'s convention branch,
    and it reads the same signal for the same reason: a water closet is the only common
    fixture with no hot-water connection, which makes "no WATER_HOT" the one reliable mark
    of a floor-drained unit (drain under its own footprint) as against a wall-drained one
    (trap arm back to the wet wall it names, so the drain rides that wall's axis).

    It is stated twice rather than imported because the resolver can only answer for the
    position a fixture *has*; a move macro has to answer for the position it is about to
    have, which no resolved model holds.  The authored-``drain_position`` branch is the
    caller's (a fixture that has one never gets here).
    """
    fixture_type = _placeable_type(plan, item)
    if fixture_type is None:
        return None
    if Service.WATER_HOT not in fixture_type.needs:
        return at_m
    wall_ref = getattr(item, "wall_ref", None)
    if wall_ref is None:
        return None
    wall = next((candidate for candidate in _walls(plan, storey)
                 if candidate.tag == wall_ref), None)
    if wall is None:
        return None
    by_tag = {node.tag: node for node in _nodes(plan, storey)}
    start, end = by_tag.get(wall.start_node), by_tag.get(wall.end_node)
    if start is None or end is None:
        return None
    p0, p1 = start.position.xy_m, end.position.xy_m
    t = _project_param(p0, p1, at_m)
    return (p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1]))


def _drain_follower_ops(plan: PlanModel, storey: str, item: object,
                        new_xy: tuple[float, float]) -> tuple[list[PatchOp], list[Impact]]:
    """Patches that keep a moved fixture's sleeve and drain run under its flange.

    Followers are claimed by proximity to the fixture's OLD drain point, within the same
    ``_PIPE_SLEEVE_SNAP_M`` the resolver uses to decide a routed vertex belongs to a sleeve
    — so the two agree on what "at the flange" means, and a collector that merely *serves*
    the fixture from twenty feet away (PR-B-MAIN-DRAIN serves seventeen of them) is not
    dragged along with it.  Everything found is reported either way: what followed, because
    a cast-in sleeve moving is a fact the author must see, and what did not, because a
    served run left behind is exactly the tie-in that now needs re-cutting by hand.
    """
    if not isinstance(item, (Fixture, Appliance)):
        return [], []
    sleeves = [element for element in plan.elements_of_kind("SleevePenetration")
               if element.serves_fixture == item.tag]
    runs = [element for element in plan.elements_of_kind("PipeRun")
            if item.tag in element.serves]
    if not sleeves and not runs:
        return [], []
    if item.drain_position is not None:
        return [], [Impact(item.tag, "carried",
                           f"{item.tag} authors its drain_position, so its drain stays put")]

    old_xy = _convention_drain_point(plan, storey, item, item.position.xy_m)
    target_xy = _convention_drain_point(plan, storey, item, new_xy)
    if old_xy is None or target_xy is None:
        # No convention applies (unknown type, or a wall-drained unit naming no wall), so
        # there is no defensible delta.  Say so rather than guess: the drain is now stale.
        return [], [Impact(item.tag, "needs_review",
                           f"{item.tag} moved but its drain point cannot be derived — "
                           f"{', '.join(sorted(element.tag for element in (*sleeves, *runs)))} "
                           "left in place; re-point by hand")]
    dx, dy = target_xy[0] - old_xy[0], target_xy[1] - old_xy[1]
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return [], []  # a wall-drained unit slid off its wall: the drain point is unchanged

    ops: list[PatchOp] = []
    impacts: list[Impact] = []
    for sleeve in sleeves:
        gap = _dist(sleeve.position.xy_m, old_xy)
        if gap > _PIPE_SLEEVE_SNAP_M:
            impacts.append(Impact(
                sleeve.tag, "needs_review",
                f"sleeve {sleeve.tag} serves {item.tag} but sat {m(gap).fmt()} from its old "
                "drain point — left where it was; re-point it by hand"))
            continue
        sx, sy = sleeve.position.xy_m
        ops.append(PatchOp("update", "SleevePenetration", sleeve.tag,
                           {"position": _point_expr_m(sx + dx, sy + dy)}))
        impacts.append(Impact(
            sleeve.tag, "carried",
            f"sleeve {sleeve.tag} moved {m(_dist((0, 0), (dx, dy))).fmt()} with {item.tag} — "
            "it is cast in place, so confirm the pour has not happened"))
    stayed: list[str] = []
    for run in runs:
        # EVERY vertex at the old point moves, not just the first: a vertical drop is
        # authored as the same plan point repeated with two inverts (path[0] == path[1] on
        # every riser here), so rewriting one of the pair would fold the riser into a slope.
        moved = {index for index, vertex in enumerate(run.path)
                 if _dist(vertex.xy_m, old_xy) <= _PIPE_SLEEVE_SNAP_M}
        if not moved:
            # Normal and expected for most of them — a WC's supply, its vent and the house
            # collector all serve it without ever touching the flange — so these are one
            # line, not one toast each, and they name a distance so a near miss stands out.
            nearest = min((_dist(vertex.xy_m, old_xy) for vertex in run.path), default=None)
            stayed.append(run.tag + (f" ({m(nearest).fmt()} away)" if nearest is not None else ""))
            continue
        vertices: list[str] = []
        for index, vertex in enumerate(run.path):
            if index in moved:
                vx, vy = vertex.xy_m
                vertices.append(_point_expr_m(vx + dx, vy + dy).expr)
            else:
                # Untouched vertices are re-emitted in their authored units, not round-tripped
                # through meters, so a path rewrite never smears the rest of the route.
                vertices.append(f"pt({vertex.x.to_source()}, {vertex.y.to_source()})")
        ops.append(PatchOp("update", "PipeRun", run.tag,
                           {"path": RawExpr("(" + ", ".join(vertices) + ",)")}))
        impacts.append(Impact(
            run.tag, "carried",
            f"run {run.tag} followed {item.tag} ({len(moved)} of {len(run.path)} vertices "
            "re-pointed); its inverts and slope were not re-solved"))
    if stayed:
        impacts.append(Impact(
            item.tag, "needs_review",
            f"{len(stayed)} run(s) serving {item.tag} had no vertex at its old drain point "
            f"and were left as routed — check the tie-ins: {', '.join(stayed)}"))
    return ops, impacts
