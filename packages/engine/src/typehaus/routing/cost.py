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
from typing import Any

#: Occupancy-keyed penalty for a foot of run in a room's open air, in inches of equivalent
#: travel per foot. The ordering is the point rather than the magnitudes: a bedroom and a
#: media room are where a bulkhead is least welcome, a hallway is where one is normal, and
#: a garage or a mechanical room is free because pipe hangs there by design — the same set
#: ``EXPOSED_SERVICE_OCCUPANCIES`` names, arrived at from the cost side.
_ROOM_PENALTY_PER_FT: dict[str, float] = {
    "bedroom": 96.0, "media": 96.0, "living": 72.0, "dining": 72.0, "office": 72.0,
    "study_closet": 72.0, "kitchen": 48.0, "bathroom": 48.0, "laundry": 36.0,
    "hallway": 24.0, "stair": 24.0,
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
    #: Per-foot discount for riding beside an accepted parallel run on shared hangers (a
    #: rack, Phase 7). Shares the corridor discount's cap: together they never take an
    #: edge below zero, and ``heuristic_floor`` folds in both.
    rack_discount_per_ft: float = 4.0
    #: A DWV turn that must be a sweep (long-sweep 1/4 bend, combo, wye + 1/8 or a 45 pair):
    #: every drainage transition but horizontal-to-vertical (UPC 706).
    dwv_sweep_in: float = 30.0
    #: A PEX corner made as a field bend at the maker's radius instead of a fitting.
    pex_bend_in: float = 4.0
    #: Per member cut, by kind (``routing/members.py``). A stud bore is a hole and a
    #: plate cut a hole plus a nail plate; a joist bore is a hole in a floor somebody
    #: inspects. An I-joist hole no chart on record publishes is priced high and disclosed.
    bore_stud_in: float = 12.0
    plate_cut_in: float = 24.0
    bore_joist_in: float = 36.0
    bore_engineered_in: float = 36.0
    bore_unpublished_in: float = 96.0
    #: Per foot of supply or drain inside an exterior insulated wall's cavity (vents are
    #: exempt): freeze risk and a hole in the insulation.
    exterior_wall_per_ft: float = 96.0
    #: A cleanout whose access face is concealed needs an access panel (UPC 707.9).
    cleanout_concealed_in: float = 48.0
    #: Room a tool needs round a joint, beyond the fitting's own body, by joining method.
    solvent_weld_tool_in: float = 1.0
    propress_tool_in: float = 2.0
    pex_expansion_tool_in: float = 1.5
    #: A Z-jog whose middle leg is shorter than this is redrawn as a 45 pair.
    offset_jog_max_in: float = 18.0
    #: ``[mep.routing]`` keys this version no longer reads, with what replaced each — read
    #: so a house that pins one is TOLD, never silently ignored.
    superseded: tuple[tuple[str, str], ...] = ()
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
                     corridor: bool = False, rack: bool = False,
                     room_ft: float = 0.0, occupancy: str | None = None) -> float:
        """One edge's travel and open-air cost, in inches of equivalent travel.

        ``room_ft`` is the portion of this edge inside a finished room — a length, not a
        flag, because an edge that clips a room's corner should not pay a whole segment's
        penalty. Member cuts and exterior walls are priced by the caller.
        """
        travel = self.travel(length_ft, vertical=vertical)
        return (travel - self.discount(length_ft, travel, corridor=corridor, rack=rack)
                + room_ft * self.room_penalty(occupancy))

    def travel(self, length_ft: float, *, vertical: bool = False) -> float:
        return length_ft * 12.0 * (self.riser_per_ft if vertical else 1.0)

    def discount(self, length_ft: float, travel: float, *, corridor: bool,
                 rack: bool) -> float:
        """Corridor plus rack discount, capped together at the travel term itself."""
        per_ft = ((self.corridor_discount_per_ft if corridor else 0.0)
                  + (self.rack_discount_per_ft if rack else 0.0))
        return min(length_ft * per_ft, travel)

    def cut_cost(self, kind: str) -> float:
        """What one member cut of this kind costs (``routing/members.py`` kinds)."""
        return {"stud": self.bore_stud_in, "plate": self.plate_cut_in,
                "plate_tie": 2.0 * self.plate_cut_in, "joist": self.bore_joist_in,
                "engineered": self.bore_engineered_in,
                "unpublished": self.bore_unpublished_in}[kind]

    def turn_cost(self, service: str, before: str, after: str) -> float | None:
        """A change of direction's cost, or None where no legal pattern makes it.

        ``before``/``after`` are ``resolve/mep_fitting_direction`` classes in flow order.
        Only drainage cares: horizontal-to-vertical may be a plain 1/4 bend or sanitary
        tee, every other drainage transition a sweep, and nothing may turn upward.
        """
        from typehaus.resolve.mep_fitting_direction import (
            LONG_SWEEP,
            QUARTER_BEND,
            allowed_patterns,
        )

        allowed = allowed_patterns(service, before, after)
        if not allowed:
            return None
        if QUARTER_BEND in allowed:
            return self.bend_in
        return self.dwv_sweep_in if LONG_SWEEP in allowed else self.bend_in

    def table(self) -> list[str]:
        """The weights actually in force, as lines — the whole of ``--explain``'s header.

        Printed rather than assumed, because a house may pin any of them in
        ``[mep.routing]`` and a proposal argued from defaults the house overrode is an
        argument about the wrong building. Only the room penalties that differ from the
        built-in table are listed: the point is what THIS run was priced at, and twenty
        unchanged rows bury it.
        """
        lines = [
            f'weights: bend {self.bend_in:.0f}" each, riser {self.riser_per_ft:.2f}x '
            f"horizontal, corridor -{self.corridor_discount_per_ft:.0f}\"/ft and rack "
            f'-{self.rack_discount_per_ft:.0f}"/ft (capped together)',
            f'  DWV sweep {self.dwv_sweep_in:.0f}", PEX bend {self.pex_bend_in:.0f}"; '
            f'cuts: stud {self.bore_stud_in:.0f}", plate {self.plate_cut_in:.0f}", joist '
            f'{self.bore_joist_in:.0f}", I-joist {self.bore_engineered_in:.0f}" '
            f'({self.bore_unpublished_in:.0f}" with no published hole); exterior wall '
            f'+{self.exterior_wall_per_ft:.0f}"/ft; concealed cleanout '
            f'{self.cleanout_concealed_in:.0f}"',
        ]
        for key, why in self.superseded:
            lines.append(f"  [mep.routing] {key} is SUPERSEDED and ignored: {why}")
        overrides = {k: v for k, v in sorted(self.room_per_ft.items())
                     if abs(v - _ROOM_PENALTY_PER_FT.get(k, -1.0)) > 1e-9}
        if overrides:
            lines.append("  room penalties overridden by the house: "
                         + ", ".join(f'{k} {v:.0f}"/ft' for k, v in overrides.items()))
        lines.append(f"  cheapest possible inch of travel (the heuristic's scale): "
                     f"{self.heuristic_floor():.3f}")
        return lines

    def heuristic_floor(self, *, rack: bool = False) -> float:
        """The cheapest an inch of plan travel can ever be — the heuristic's scale factor.

        A* is optimal only while ``h`` never over-estimates. Every penalty above is
        additive and non-negative, and the one discount is capped at the travel term, so
        the cheapest possible inch is ``1 - corridor_discount_per_ft / 12`` of an inch and
        the honest heuristic is Manhattan distance times exactly that. Where the space
        offers rack lanes (``rack``) that discount shares the cap, so the floor is
        ``1 - (corridor + rack) / 12``, never below zero; a space with none keeps the
        corridor floor rather than degrading every search to Dijkstra.
        """
        per_ft = self.corridor_discount_per_ft + (self.rack_discount_per_ft if rack else 0.0)
        return max(0.0, 1.0 - per_ft / 12.0)


#: Retired keys and what replaced each — printed by ``table()``, never silently dropped.
_SUPERSEDED = {
    "in_wall_travel_per_ft": "a wall is priced per member cut now (bore_stud_in, "
                             "plate_cut_in), and vertical travel in a cavity that fits pays "
                             "travel only",
}

_FLOAT_KEYS = (
    "bend_in", "riser_per_ft", "corridor_discount_per_ft", "rack_discount_per_ft",
    "dwv_sweep_in", "pex_bend_in", "bore_stud_in", "plate_cut_in", "bore_joist_in",
    "bore_engineered_in", "bore_unpublished_in", "exterior_wall_per_ft",
    "cleanout_concealed_in", "solvent_weld_tool_in", "propress_tool_in",
    "pex_expansion_tool_in", "offset_jog_max_in",
)


def cost_from_preferences(table: dict[str, Any]) -> RouteCost:
    """Build a :class:`RouteCost` from ``preferences.toml``'s ``[mep.routing]`` table.

    Unknown keys are ignored rather than raising: a house that pins a weight this version
    does not have should still route, and ``haus route --explain`` prints the weights it
    actually used, which is where a typo shows up.
    """
    rooms = dict(_ROOM_PENALTY_PER_FT)
    rooms.update({str(k): float(v)
                  for k, v in dict(table.get("room_per_ft") or {}).items()})
    defaults = RouteCost()
    values = {key: float(table.get(key, getattr(defaults, key))) for key in _FLOAT_KEYS}
    superseded = tuple((key, why) for key, why in _SUPERSEDED.items() if key in table)
    return RouteCost(room_per_ft=rooms, superseded=superseded, **values)
