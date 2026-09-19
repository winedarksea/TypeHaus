"""A second lane in an occupied bay — where the free width actually is.

``corridors.floor_corridors`` offers one corridor per bay, on the bay's CENTRELINE, with
whatever a run already in it has taken subtracted from the width. That is the right answer
to "is there room" and the wrong answer to "where". A 12 1/2" truss bay holding one 4" duct
has 8 1/2" left, and none of it is on the centreline: the occupant is sitting there. A
router offered only the centreline either refuses a bay it could use or proposes a lane
drawn on top of something.

So this derives the lane. In an occupied bay the occupant's lateral station is the **median
of its path points inside that bay** — a median rather than a mean because a run that jogs
into the bay and back has two stations and the mean is the one place it is not — and what is
left is the intervals between the occupants and the bay's two edges. The widest one that
admits the target becomes a second ``Corridor``, at its own centre and **with its own
width**, which is the whole point: the free interval is not the bay's width and pricing it
as the bay's would propose two ducts in one lane.

The tag keeps the ``<floor>:bay@<station>`` shape ``floor_corridors`` mints, so
``proposal.concealment`` reads ``floor_ref=`` off it unchanged — a lane is a station in a
bay, not a new kind of thing.

**What this does not do.** It does not re-tier: two runs that STACK do not compete for
lateral width at all, and the occupant band this reads is ``mep_packing``'s governing tier,
so a lane derived here is a lane beside the pinch. And it does not move the occupant: a
``movable`` blocker is ``--counterfactual``'s subject and lifting one here would be pricing
a route nobody has searched.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.routing.corridors import Corridor

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel

#: Two stations closer than this are one lane. A sixteenth of an inch, the grid a proposal
#: is snapped to and the same tolerance ``graph`` calls two coordinates one line at.
_LANE_TOL_M = 0.0015875


def lane_corridors(model: ResolvedModel, corridors: list[Corridor],
                   radius_m: float) -> list[Corridor]:
    """The free lanes of every occupied bay in ``corridors`` that admit ``radius_m``.

    Returned as extra corridors to append; the centreline ones are left alone, because a
    bay whose occupant sits off-centre still has its centreline free and the search should
    be offered both.
    """
    from typehaus.resolve.mep_envelopes import run_polylines
    from typehaus.resolve.mep_packing import run_occupants
    from typehaus.resolve.mep_queries import clear_bay_width_m

    occupied = [c for c in corridors if c.kind == "bay" and c.occupants]
    if not occupied:
        return []

    lines_by_tag = {tag: path for _kind, tag, path, _z in run_polylines(model)}
    floors = {floor.tag: floor for floor in model.floors}
    occupants_by_floor: dict[str, list] = {}

    out: list[Corridor] = []
    for corridor in occupied:
        floor_tag = corridor.tag.split(":bay@")[0]
        floor = floors.get(floor_tag)
        if floor is None:
            continue
        clear = clear_bay_width_m(floor)
        if clear is None or clear <= 0:
            continue
        if floor_tag not in occupants_by_floor:
            occupants_by_floor[floor_tag] = run_occupants(
                model, channel_ref=floor_tag, attr="floor_ref")
        widths = {o.tag: o.width_m for o in occupants_by_floor[floor_tag]}
        cross = 1 if corridor.axis == "x" else 0

        taken: list[tuple[float, float]] = []
        for tag in corridor.occupants:
            station = _median_station(lines_by_tag.get(tag, ()), cross,
                                      corridor.station, clear)
            width = widths.get(tag)
            if station is None or not width:
                continue
            taken.append((station - width / 2.0, station + width / 2.0))

        lane = _widest_free(corridor.station - clear / 2.0,
                            corridor.station + clear / 2.0, taken, 2.0 * radius_m)
        if lane is None:
            continue
        low, high = lane
        centre = (low + high) / 2.0
        if abs(centre - corridor.station) <= _LANE_TOL_M:
            continue  # the free lane IS the centreline; the corridor already offers it
        out.append(Corridor(
            tag=f"{floor_tag}:bay@{centre:.4f}", kind="bay", axis=corridor.axis,
            station=centre, z0_m=corridor.z0_m, z1_m=corridor.z1_m,
            clear_width_m=high - low, lo_m=corridor.lo_m, hi_m=corridor.hi_m,
            occupied_z=corridor.occupied_z, occupants=corridor.occupants,
            gaps=(*corridor.gaps,
                  f"{floor_tag} lane @{centre:.4f}: derived by SUBTRACTION from the bay's "
                  f"structural clear width, off each occupant's MEDIAN station in this bay. "
                  "A run that jogs into the bay and back is read at its median, not its "
                  "mean, and a run banded at a different tier is not competing for this "
                  "width at all.",)))
    return out


def _median_station(path, cross: int, bay_station: float,
                    clear_m: float) -> float | None:
    """The occupant's lateral station in this bay — the median of its points inside it."""
    inside = sorted(point[cross] for point in path
                    if abs(point[cross] - bay_station) <= clear_m / 2.0)
    if not inside:
        return None
    middle = len(inside) // 2
    if len(inside) % 2:
        return inside[middle]
    return (inside[middle - 1] + inside[middle]) / 2.0


def _widest_free(low: float, high: float, taken: list[tuple[float, float]],
                 width_m: float) -> tuple[float, float] | None:
    """The widest gap in ``[low, high]`` clear of ``taken`` that is at least ``width_m``.

    **A tie goes to the LOWER station**, and it is a tie often: an occupant on the bay's
    centreline leaves two equal lanes. Deterministic beats arbitrary — a router whose
    answer flips between two equally good lanes when an unrelated run moves is one nobody
    can diff a campaign against.
    """
    best: tuple[float, float] | None = None
    edge = low
    for start, end in sorted(taken):
        if start > edge:
            span = (edge, min(start, high))
            if span[1] - span[0] >= width_m - 1e-9 and (
                    best is None or span[1] - span[0] > best[1] - best[0]):
                best = span
        edge = max(edge, end)
    if edge < high:
        span = (edge, high)
        if span[1] - span[0] >= width_m - 1e-9 and (
                best is None or span[1] - span[0] > best[1] - best[0]):
            best = span
    return best
