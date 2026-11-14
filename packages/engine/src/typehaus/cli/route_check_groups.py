"""Check-id groups shared by the scorecard, the decision view and campaign selection."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel
    from typehaus.routing.proposal import RouteProposal

#: ``--evaluate`` check ids each metric reads, by what they grade.
BORE_CHECKS = frozenset({
    "mep.run_through_stud", "mep.run_through_plate", "mep.run_through_header",
    "mep.run_member_crossing", "mep.run_through_floor_member", "mep.run_in_joist_flange",
    "mep.run_in_joist_web",
    "mep.run_through_blocking", "mep.run_through_beam"})
TRAP_ARM_CHECKS = frozenset({"mep.trap_arm_length"})
VENT_CHECKS = frozenset({"mep.vent_reachability", "mep.vent_grade",
                         "mep.vent_termination_height"})
CLEANOUT_CHECKS = frozenset({"mep.drain_cleanouts"})
FITTING_PATTERN_CHECKS = frozenset({"mep.fitting_pattern"})
#: What grades a duct's ROUTE, not its sizing or parts: the bay or soffit it rides, the truss
#: panel it crosses, its hangers and penetrations, whether it lands, and the ERV static
#: budget its length and elbows spend.
DUCT_CHECKS = frozenset({
    "mep.duct_joist_bay", "mep.duct_joist_bay_occupancy", "mep.duct_soffit_occupancy",
    "mep.open_web_panel", "mep.duct_supports", "mep.duct_penetration_fit",
    "mep.duct_connectivity", "mep.erv_static_budget"})

INTERFERENCE_CHECKS = frozenset({"mep.run_interference"})
FINISHED_VOLUME_CHECKS = frozenset({"mep.run_in_finished_volume"})
FREEZE_CHECKS = frozenset({"mep.supply_freeze_exposure"})
#: A FAIL in any of these makes a network not constructible (campaign eligibility). Forbidden
#: fittings are counted off geometry (``forbidden_turns``), not a check id.
CONSTRUCTION_CHECKS = (BORE_CHECKS | INTERFERENCE_CHECKS | FINISHED_VOLUME_CHECKS
                       | FREEZE_CHECKS)

#: Named groups in report order; a check in none of them reports as "other".
GROUPS: tuple[tuple[str, frozenset[str]], ...] = (
    ("bores", BORE_CHECKS), ("interference", INTERFERENCE_CHECKS),
    ("finished_volume", FINISHED_VOLUME_CHECKS), ("freeze", FREEZE_CHECKS),
    ("fitting_pattern", FITTING_PATTERN_CHECKS), ("trap_arm", TRAP_ARM_CHECKS),
    ("vent", VENT_CHECKS), ("cleanout", CLEANOUT_CHECKS), ("duct", DUCT_CHECKS))


def group_of(check_id: str) -> str:
    """The named group a check id belongs to, else ``"other"``."""
    return next((name for name, ids in GROUPS if check_id in ids), "other")


def segments(proposal: RouteProposal):
    for a, b in zip(proposal.points, proposal.points[1:], strict=False):
        yield (a[0], a[1]), (b[0], b[1]), a[2], b[2]


def bores(model: ResolvedModel, proposals: list[RouteProposal]) -> Counter[str]:
    """Members each proposal passes through, by kind: stud/plate/header, joist, truss pass."""
    from shapely.geometry import LineString, box

    from typehaus.resolve.mep_bore_geometry import leg_crossings as wall_crossings
    from typehaus.resolve.mep_crossings import leg_crossings as floor_crossings
    from typehaus.resolve.mep_crossings import member_window
    from typehaus.resolve.pipe_sections import pipe_outside_diameter_m

    out: Counter[str] = Counter()
    kinds = {f.tag: getattr(member_window(f), "kind", None) for f in model.floors}
    for proposal in proposals:
        radius = pipe_outside_diameter_m(proposal.diameter_m,
                                         proposal.echo.get("material")) / 2.0
        for a, b, za, zb in segments(proposal):
            reach = (LineString([a, b]) if a != b else LineString([a, (a[0] + 1e-6, a[1])])
                     ).buffer(radius + 0.01)
            for wall in model.walls:
                if not wall.members or not reach.intersects(box(*_wall_bounds(wall))):
                    continue
                for cut in wall_crossings(wall, a, b, za, zb, radius):
                    out[cut.category] += 1
            for floor in model.floors:
                kind = {"open_web": "truss_pass", "i_joist": "i_joist"}.get(
                    kinds[floor.tag], "joist")
                out[kind] += len(floor_crossings(floor, a, b, za, zb))
    return out


def _wall_bounds(wall: Any) -> tuple[float, float, float, float]:
    xs = [p[0] for layer in wall.layers for p in layer.polygon] or [wall.axis[0][0]]
    ys = [p[1] for layer in wall.layers for p in layer.polygon] or [wall.axis[0][1]]
    return (min(xs), min(ys), max(xs), max(ys))
