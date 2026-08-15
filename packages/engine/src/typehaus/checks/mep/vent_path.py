"""Where a fixture's vent goes when its own wet wall stops at the ceiling (→ MEP Phase 2).

A vent only rises inside the fixture's wet wall when that wall continues to the storey
above.  Where it does not — catlin's powder-bath and ensuite wet walls all die at their own
top plate — the plumber takes the vent above the fixtures' flood-level rim and runs it
horizontally to a chase that does reach the roof.  That is a routing decision, and this
engine never invents routing, so the alternate path has to be *authored*: a ``PipeRun`` with
``system=VENT`` that ``serves`` the fixture, touches the fixture's wet wall, and lands on a
``VentRun`` chase.

This module answers only the geometry question ("is that path present and connected at both
ends?").  ``checks/mep/plumbing_dwv.py`` turns the answer into a finding.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.enums import PipeSystem
from typehaus.model.mep import VentRun
from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedModel, ResolvedWall

# A vent run is drawn to the centerline of the wall it rises in and of the chase it lands
# in, but an author may just as reasonably snap it to a wall face or a chase corner.  One
# framing bay of slack absorbs that without letting a run that misses entirely read as
# connected: the widest wet wall here is 5.5" and a framed vent chase is ~12" square.
VENT_CONNECTION_TOLERANCE_M = inch(12).meters


@dataclass(frozen=True)
class VentPath:
    """How far an authored vent path for one fixture actually got.

    ``run_tag`` is None when nothing carries the fixture at all; the two booleans separate
    "the run does not start at the wet wall" from "the run ends nowhere" so the finding can
    say which end is wrong instead of a blanket "no vent".
    """

    run_tag: str | None
    chase_tag: str | None
    touches_wet_wall: bool

    @property
    def is_connected(self) -> bool:
        return self.run_tag is not None and self.chase_tag is not None and self.touches_wet_wall


def evaluate_vent_path(model: ResolvedModel, fixture_tag: str, wall: ResolvedWall) -> VentPath:
    """Best authored vent path from ``fixture_tag``'s wet wall to a through-roof chase."""
    runs = [run for run in model.pipe_runs
            if run.system == PipeSystem.VENT.value and fixture_tag in run.serves]
    if not runs:
        return VentPath(None, None, False)
    best = VentPath(runs[0].tag, None, False)
    for run in runs:
        candidate = VentPath(run.tag, _chase_at_either_end(model, run.path),
                             _touches_wall_axis(run.path, wall.axis))
        if candidate.is_connected:
            return candidate
        # Prefer the most-connected partial result so the finding names the nearest miss.
        if _connectedness(candidate) > _connectedness(best):
            best = candidate
    return best


def _connectedness(path: VentPath) -> int:
    return int(path.chase_tag is not None) + int(path.touches_wet_wall)


def _chase_at_either_end(model: ResolvedModel, path) -> str | None:
    """Tag of the vent riser a run lands on, at whichever end it was authored from.

    Polyline direction is an authoring detail, not a plumbing fact, so both endpoints count.
    Only a riser that actually carries the vent system qualifies — a radon-only riser is a
    soil-gas stack a plumbing vent may not be tied into.
    """
    ends = (path[0], path[-1])
    for element in model.plan.all_elements():
        if not isinstance(element, VentRun) or PipeSystem.VENT not in element.systems:
            continue
        chase = element.chase_position.xy_m
        if any(_distance(end, chase) <= VENT_CONNECTION_TOLERANCE_M for end in ends):
            return element.tag
    return None


def _touches_wall_axis(path, axis) -> bool:
    """Whether any vertex of the run sits on the wet wall — i.e. the vent really starts
    inside the wall the fixture is plumbed into rather than crossing the room to it."""
    return any(_distance_to_segment(point, axis[0], axis[1]) <= VENT_CONNECTION_TOLERANCE_M
               for point in path)


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _distance_to_segment(point: tuple[float, float], start: tuple[float, float],
                         end: tuple[float, float]) -> float:
    dx, dy = end[0] - start[0], end[1] - start[1]
    denominator = dx * dx + dy * dy
    if denominator < 1e-12:  # degenerate wall axis — fall back to the endpoint
        return _distance(point, start)
    t = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / denominator
    t = max(0.0, min(1.0, t))
    return _distance(point, (start[0] + t * dx, start[1] + t * dy))
