"""How a drain run joins the pipe it discharges into, and what happens when it does not.

Split out of :mod:`typehaus.resolve.mep_queries`, which was past the AGENTS.md budget before
this record existed. It is the right seam anyway: everything here answers one question —
which pipe does this branch land on, and how — and nothing else in that module asks it.

**The rejection is the whole reason this is a record and not a dict.** ``drain_tie_ins``
used to ``continue`` silently past a branch arriving below its collector, so the run simply
dropped out of the load graph: ``accumulated_serves`` under-counted, ``branch_load``
under-reported, and ``mep.pipe_sizing`` under-sized the pipe downstream — **with no finding
anywhere in the report.** ``mep.drain_tie_in`` is the check that grades what these records
now carry.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.resolve.geometry import length, sub

# Arrival may read slightly below the receiving invert at the matched vertex: authored
# inverts interpolate along whole segments, while the physical wye sits a little way
# downstream of a corner (catlin's kitchen branch arrives 0.43" under the main's invert
# at the (6', 16'-6") turn). One inch of slack keeps the *load* graph connected — grading
# slope/backflow is drain_slope's job, not the rollup's; a missed tie-in here silently
# under-sizes the pipe downstream, which is the worse failure.
_TIE_IN_INVERT_TOL_M = 0.0254


@dataclass(frozen=True)
class TieIn:
    """One drain run's arrival at the pipe it discharges into — accepted or not.

    **The rejection is the point.** ``drain_tie_ins`` used to ``continue`` silently past a
    branch arriving below its collector, so the run simply dropped out of the load graph:
    ``accumulated_serves`` under-counted, ``branch_load`` under-reported and
    ``mep.pipe_sizing`` under-sized downstream pipe — **with no finding anywhere.** That is
    the silent-failure pattern this repo exists to eliminate, and it needed a record with
    the fact on it before a check could grade it.
    """

    child: str
    #: The receiving run, or ``None`` when no run passes under the arrival point at all.
    parent: str | None
    accepted: bool
    #: How far the child's centreline arrives ABOVE the parent's at that station. Negative
    #: is below. ``None`` when there was no candidate to measure against.
    drop_m: float | None
    #: The arrival point, in the plan frame.
    station: tuple[float, float] | None


def drain_tie_in_records(pipe_runs) -> list[TieIn]:
    """Every drain run's arrival, whether or not the geometry accepts it.

    The connection is the geometry itself — ``PipeRun`` carries no upstream/downstream refs.
    A run ties into another when its *last* path vertex lies on a segment of the other's path
    and arrives at or above the other's centreline there within
    :data:`_TIE_IN_INVERT_TOL_M`. Runs without elevation data can't be judged and never tie
    in.

    A run never receives at its own terminal vertex: that point is where *it* discharges, so
    several branches all ending on one junction are siblings meeting at a wye on whatever
    continues downstream, not each other's parents — which is also what keeps the derivation
    acyclic on real junctions.

    **A run with no candidate at all is not a rejection.** On catlin the four drains that
    tie into nothing terminate at a sleeve, a receptor or an air gap; they get a record with
    ``parent=None`` so a check can tell "nothing to join" from "joined below the thing it
    joins", which are a non-event and a defect.
    """
    from typehaus.resolve.mep_queries import pipe_invert_at

    drains = [r for r in pipe_runs if r.system == "drain"]
    out: list[TieIn] = []
    for child in drains:
        if child.z_m is None or not child.path:
            continue
        end_point, end_invert = child.path[-1], child.z_m[-1]
        best: tuple[float, str] | None = None
        highest: tuple[float, str] | None = None
        for parent in drains:
            if parent.tag == child.tag or not parent.path:
                continue
            if length(sub(end_point, parent.path[-1])) <= 1e-6:
                continue  # the parent terminates here too — a sibling, not a receiver
            invert = pipe_invert_at(parent, end_point)
            if invert is None:
                continue
            # Every candidate, for the rejection record; the ACCEPTED one has to clear the
            # arrival tolerance as well.
            if highest is None or invert > highest[0]:
                highest = (invert, parent.tag)
            if end_invert < invert - _TIE_IN_INVERT_TOL_M:
                continue
            # Of several runs passing under the arrival point, the receiving pipe is
            # the one whose invert sits closest beneath the arrival.
            if best is None or invert > best[0]:
                best = (invert, parent.tag)
        if best is not None:
            out.append(TieIn(child.tag, best[1], True, end_invert - best[0], end_point))
        elif highest is not None:
            out.append(TieIn(child.tag, highest[1], False, end_invert - highest[0],
                             end_point))
        else:
            out.append(TieIn(child.tag, None, False, None, end_point))
    return out


def drain_tie_ins(pipe_runs) -> dict[str, str]:
    """Child drain run tag → the drain run it discharges into, derived geometrically.

    A projection of :func:`drain_tie_in_records` — the accepted ties only, which is what
    every existing caller wants and what the load rollup is built on. Signature and
    behaviour are unchanged; the rejections that used to vanish here are now on the records,
    where ``mep.drain_tie_in`` grades them.
    """
    return {tie.child: tie.parent for tie in drain_tie_in_records(pipe_runs)
            if tie.accepted and tie.parent is not None}


