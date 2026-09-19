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



# A tee has a BODY, and a branch is authored at ITS OWN running elevation rather than at the
# fitting: PR-B-HW-SAUNA tees off the hot trunk and is drawn 3.2" up on the cold band,
# because that is the lane it rides. So the tolerance has to cover a tee plus a short riser
# stub, not a tee alone.
#
# ** FOUR INCHES IS NOT A TUNED NUMBER, AND THE REASON IS THAT THE GAPS ARE BIMODAL. **
# Measured across catlin's 29 supply runs, every candidate is either within 3.2" of its
# child or beyond 33"; there is nothing between. The threshold is insensitive anywhere in
# that gulf, which is what makes it a reading rather than a knob — 3", 4" or 8" all derive
# the same 22 parents. Re-measure the distribution before moving it; do not move it to make
# a particular run pass.
_SUPPLY_TEE_TOL_M = 0.1016

#: The pressurised systems. A drain is gravity and has ``drain_tie_ins``; a vent has a
#: chase rather than a parent run; a supply tree is neither.
_SUPPLY_SYSTEMS = ("water_cold", "water_hot")


@dataclass(frozen=True)
class SupplyTieIn:
    """One supply run's tee onto the run that feeds it — accepted or not, with the cause.

    **Supply is the mirror image of a vent and the opposite of a drain.** A drain branch
    discharges at its LAST vertex into whatever passes beneath; a supply branch is authored
    tie-first, so its FIRST vertex is the tee and its last is the riser at the fixture. And
    a tee sits on a SEGMENT, never at an endpoint, so no endpoint-to-endpoint tolerance can
    find one — which is why ``_vent_siblings`` never matched a single supply run.

    ``reason`` is what makes this a record. The three ways a supply run has no parent are
    three different facts about the model and want three different sentences from the
    router, not one about a vent chase:

    ``accepted``      it tees onto ``parent`` at ``station``.
    ``no_candidate``  no run of any system passes under the first vertex. The source is not
                      a run in this model — a service lateral, or a riser nobody drew.
    ``elevation``     a same-system run passes under the first vertex, but none within
                      :data:`_SUPPLY_TEE_TOL_M` of its elevation. ``z_gap_m`` says how far.
    ``cross_system``  no same-system candidate, but another system's run is there. A water
                      heater's hot outlet fed from a cold run is exactly this, and it is not
                      a defect — it is a parent this derivation cannot name.
    """

    child: str
    parent: str | None
    accepted: bool
    reason: str
    #: The tee point in the plan frame — the child's first vertex.
    station: tuple[float, float] | None
    #: Signed distance from the child's elevation to the nearest candidate's at that
    #: station. ``None`` when there was no candidate of any kind to measure against.
    z_gap_m: float | None
    #: The nearest candidate's tag when the tie was refused on elevation, so a refusal can
    #: name the run it would have joined.
    nearest: str | None = None


def _best_by_load(child_serves: frozenset, candidates: list[tuple[str, frozenset]]) -> str:
    """Of several runs on whose polyline the tee stands, the one that FEEDS the child.

    Branches overlap in plan — ``PR-B-CW-BATH1``'s first vertex sits on four candidates'
    lines — so geometry alone does not answer it and the load does. A run whose ``serves``
    is a proper superset of the child's carries the child's fixtures and therefore feeds
    them; failing that, the largest overlap; failing that, the largest tree, which is the
    trunk. Tag order breaks a remaining tie so the derivation is deterministic.
    """
    supersets = [(tag, serves) for tag, serves in candidates
                 if serves > child_serves]
    if supersets:
        # The SMALLEST superset, which is the nearest ancestor. Largest would walk past
        # every intermediate branch to the trunk: PR-B-CW-HYD-RISER's fixtures are carried
        # by PR-B-CW-HYD (2 fixtures) and by PR-B-CW-TRUNK (21), and the riser tees off the
        # branch standing at its foot, not off the trunk twenty feet away.
        return min(supersets, key=lambda item: (len(item[1]), item[0]))[0]
    return min(candidates, key=lambda item: (-len(item[1] & child_serves),
                                             -len(item[1]), item[0]))[0]


def supply_tie_in_records(pipe_runs) -> list[SupplyTieIn]:
    """Every supply run's tee onto its feeder, whether or not the geometry accepts it.

    Beside :func:`drain_tie_in_records` because it is the same question for a pressurised
    tree, and in ``resolve/`` rather than ``routing/`` because a check and a router may both
    reach it — and because ``routing/`` owes every module a hand-worked oracle note, and
    there is nothing to work by hand here: this is a point-on-segment predicate plus a
    load-superset tie-break, argued in prose.

    **A run with no candidate gets ``parent=None`` and a reason, never a silent
    ``continue``** — that is this module's own stated lesson.
    """
    from typehaus.resolve.mep_queries import pipe_elevations_at

    supply = [r for r in pipe_runs if r.system in _SUPPLY_SYSTEMS]
    out: list[SupplyTieIn] = []
    for child in supply:
        if child.z_m is None or not child.path:
            continue
        tee, tee_z = child.path[0], child.z_m[0]
        same: list[tuple[str, frozenset]] = []
        nearest: tuple[float, str] | None = None
        cross: tuple[float, str] | None = None
        for parent in pipe_runs:
            if parent.tag == child.tag or not parent.path or parent.z_m is None:
                continue
            if (length(sub(tee, parent.path[0])) <= 1e-6
                    and not frozenset(parent.serves or ()) > frozenset(child.serves or ())):
                # ** TWO RUNS THAT BEGIN AT THE SAME POINT AND DO NOT CARRY EACH OTHER'S
                # LOAD ARE SIBLINGS, AND THIS IS WHAT KEEPS THE DERIVATION ACYCLIC. ** The
                # mirror of the drain rule ("a run never receives at its own terminal
                # vertex"). PR-B-CW-TRUNK and PR-G-HYDRANT-CW both leave the service entry
                # at (11'-0", 35'-6") and neither serves the other's fixtures; without this
                # each derives the other as its parent, and the street main that actually
                # feeds them both is not a run in this model.
                #
                # The load half is not decoration. Four hot branches tee off
                # PR-B-HW-TRUNK's FIRST vertex at the water heater — a manifold, which a
                # drain never has — and the trunk carries every one of their fixtures. A
                # bare same-origin test would call the trunk their sibling and leave the
                # whole hot tree parentless.
                continue
            elevations = pipe_elevations_at(parent, tee)
            if not elevations:
                continue
            if parent.system not in _SUPPLY_SYSTEMS or parent.system != child.system:
                # A candidate in plan but on another system. Recorded, never chosen: the
                # water heater between PR-B-CW-WH and PR-B-HW-TRUNK is a real source and
                # not a pipe, and naming a cold run as a hot run's parent would be worse
                # than saying nothing.
                gap = min((z - tee_z for z in elevations), key=abs)
                if cross is None or abs(gap) < abs(cross[0]):
                    cross = (gap, parent.tag)
                continue
            gap = min((z - tee_z for z in elevations), key=abs)
            if nearest is None or abs(gap) < abs(nearest[0]):
                nearest = (gap, parent.tag)
            if abs(gap) <= _SUPPLY_TEE_TOL_M:
                same.append((parent.tag, frozenset(parent.serves or ())))
        if same:
            parent_tag = _best_by_load(frozenset(child.serves or ()), same)
            out.append(SupplyTieIn(child.tag, parent_tag, True, "accepted", tee,
                                   0.0 if nearest is None else nearest[0], parent_tag))
        elif cross is not None and abs(cross[0]) <= _SUPPLY_TEE_TOL_M:
            # A source that really is there and really is not a run of this system. It
            # outranks a same-system sibling further away: PR-B-HW-TRUNK leaves EQ-B-WH,
            # where PR-B-CW-WH ends at the same point and the same height, and the nearest
            # hot run is its own branch 52" up. "Fed across the water heater" is the true
            # sentence; "52" from PR-B-HW-BATH1" is a coincidence.
            out.append(SupplyTieIn(child.tag, None, False, "cross_system", tee,
                                   cross[0], cross[1]))
        elif nearest is not None:
            out.append(SupplyTieIn(child.tag, None, False, "elevation", tee,
                                   nearest[0], nearest[1]))
        elif cross is not None:
            out.append(SupplyTieIn(child.tag, None, False, "cross_system", tee,
                                   cross[0], cross[1]))
        else:
            out.append(SupplyTieIn(child.tag, None, False, "no_candidate", tee, None))
    return out


def supply_tie_ins(pipe_runs) -> dict[str, str]:
    """Child supply run tag → the run it tees off, derived geometrically.

    The accepted ties alone, the projection :func:`drain_tie_ins` is of its own records.
    """
    return {tie.child: tie.parent for tie in supply_tie_in_records(pipe_runs)
            if tie.accepted and tie.parent is not None}
