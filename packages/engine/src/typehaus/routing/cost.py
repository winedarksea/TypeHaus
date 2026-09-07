"""What a foot of pipe costs the router, and why every term has a unit.

Everything here is **inches of equivalent travel**. A bend priced at 24 means "turning
costs as much as two feet of straight run"; a room penalty of 60 means "a foot through a
living room costs as much as six feet through a joist bay". One unit throughout is what
lets the A* heuristic stay admissible — see :meth:`RouteCost.heuristic_floor`.

The numbers are house preferences, not code, and they are read from ``preferences.toml``'s
``[mep.routing]`` table exactly as ``MepPreferences`` reads ``[mep]``. Defaults below are
catlin's, and each states its basis the way ``max_run_developed_over_straight`` does.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Occupancy-keyed penalty for a foot of run in a room's open air, in inches of equivalent
#: travel per foot. The ordering is the point rather than the magnitudes: a bedroom and a
#: media room are where a bulkhead is least welcome, a hallway is where one is normal, and
#: a garage or a mechanical room is free because pipe hangs there by design — the same set
#: ``EXPOSED_SERVICE_OCCUPANCIES`` names, arrived at from the cost side.
_ROOM_PENALTY_PER_FT: dict[str, float] = {
    "bedroom": 96.0, "media": 96.0, "living": 72.0, "dining": 72.0, "office": 72.0,
    "kitchen": 48.0, "bathroom": 48.0, "laundry": 36.0, "hallway": 24.0, "stair": 24.0,
    "utility": 0.0, "mechanical": 0.0, "garage": 0.0, "storage": 0.0,
    "unconditioned": 0.0,
}


@dataclass(frozen=True)
class RouteCost:
    """The weights a search adds up. Immutable, so one is safe to share across a tree.

    **Every term is inches of equivalent travel.** A route's cost is therefore comparable
    to its own length, which is what makes ``--explain``'s breakdown readable: "42 ft of
    pipe, 3 bends, 6 ft of it through the study" comes out as three numbers in one unit.
    """

    #: What one change of axis costs. Two feet is roughly what a plumber's fitting, its
    #: labour and its head loss are worth against straight pipe on this house; it is high
    #: enough that the search prefers one L to a staircase and low enough that it will
    #: still turn twice to get out of a bedroom.
    bend_in: float = 24.0
    #: What a foot of VERTICAL travel costs against a foot of horizontal. Under 1.0 because
    #: a drop is cheap pipe in a wall or a bay; it is not free, because it still has to
    #: land somewhere and be reachable.
    riser_per_ft: float = 0.5
    #: Per-foot discount for riding a corridor — a joist bay centreline, a soffit with
    #: section left, a wall cavity. **Capped at the travel term** by
    #: :meth:`segment_cost`, never applied to a bend, and never allowed to make a segment
    #: cost less than zero: an edge cheaper than its own Manhattan length would break the
    #: heuristic's admissibility and A* would stop being optimal without saying so.
    corridor_discount_per_ft: float = 8.0
    #: Per-foot penalty for travelling in a wall beyond one stud bay, because every stud
    #: on the way gets bored. Mirrors ``mep_queries._STUD_BAY_TRAVEL_M``'s reading in
    #: ``mep.wet_wall_occupancy``, which reports the same thing after the fact.
    in_wall_travel_per_ft: float = 18.0
    #: Room penalties by occupancy value, per foot. Defaults to :data:`_ROOM_PENALTY_PER_FT`.
    room_per_ft: dict[str, float] = field(
        default_factory=lambda: dict(_ROOM_PENALTY_PER_FT))

    def room_penalty(self, occupancy: str | None) -> float:
        """Per-foot cost of open air in a room of this occupancy.

        An occupancy the table does not name is priced as a living room rather than as
        free: a new ``Occupancy`` member should cost something until somebody decides what,
        and a router that silently treats an unknown room as a plenum is the failure mode
        that produces confident nonsense.
        """
        if occupancy is None:
            return 0.0
        return self.room_per_ft.get(occupancy, self.room_per_ft.get("living", 72.0))

    def segment_cost(self, length_ft: float, *, vertical: bool = False,
                     corridor: bool = False, in_wall_ft: float = 0.0,
                     room_ft: float = 0.0, occupancy: str | None = None) -> float:
        """One edge's cost, in inches of equivalent travel.

        ``room_ft`` and ``in_wall_ft`` are the portions of this edge inside a finished room
        and inside a wall — they are lengths, not flags, because an edge that clips a
        room's corner should not pay a whole segment's penalty.
        """
        travel = length_ft * 12.0 * (self.riser_per_ft if vertical else 1.0)
        if corridor:
            travel = max(travel - length_ft * self.corridor_discount_per_ft,
                         travel * 0.0)
            travel = max(travel, 0.0)
        return (travel
                + in_wall_ft * self.in_wall_travel_per_ft
                + room_ft * self.room_penalty(occupancy))

    def heuristic_floor(self) -> float:
        """The cheapest an inch of plan travel can ever be — the heuristic's scale factor.

        A* is optimal only while ``h`` never over-estimates. Every penalty above is
        additive and non-negative, and the one discount is capped at the travel term, so
        the cheapest possible inch is ``1 - corridor_discount_per_ft / 12`` of an inch and
        the honest heuristic is Manhattan distance times exactly that. Returning 1.0 with a
        discount configured would be an inadmissible heuristic and a silently suboptimal
        router; this is why the discount has a cap at all.
        """
        return max(0.0, 1.0 - self.corridor_discount_per_ft / 12.0)


def cost_from_preferences(table: dict) -> RouteCost:
    """Build a :class:`RouteCost` from ``preferences.toml``'s ``[mep.routing]`` table.

    Unknown keys are ignored rather than raising: a house that pins a weight this version
    does not have should still route, and ``haus route --explain`` prints the weights it
    actually used, which is where a typo shows up.
    """
    rooms = dict(_ROOM_PENALTY_PER_FT)
    rooms.update({str(k): float(v)
                  for k, v in dict(table.get("room_per_ft") or {}).items()})
    return RouteCost(
        bend_in=float(table.get("bend_in", 24.0)),
        riser_per_ft=float(table.get("riser_per_ft", 0.5)),
        corridor_discount_per_ft=float(table.get("corridor_discount_per_ft", 8.0)),
        in_wall_travel_per_ft=float(table.get("in_wall_travel_per_ft", 18.0)),
        room_per_ft=rooms,
    )
