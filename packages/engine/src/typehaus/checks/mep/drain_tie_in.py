"""A branch has to land on the pipe it joins, not under it.

**Nothing graded this, and the failure was silent in the worst way.**
``resolve/mep_tie_ins.drain_tie_ins`` derives the DWV topology from the geometry, and a
branch arriving below its collector simply fell out of the result. The run then vanished
from the load graph: ``accumulated_serves`` stopped counting its fixtures,
``branch_load`` reported less than the house produces, and ``mep.pipe_sizing`` sized the
pipe downstream for a load that was missing rooms — **with no finding anywhere in the
report.** A rule that under-sizes a drain and says nothing is worse than no rule.

``Tier.CODE``, where ``mep.run_member_crossing`` is deliberately not. A branch discharging
below the drain it joins does not flow, and MN ch. 4714 § 706.3 governs the fitting that
makes the junction — so there is a citation, and a reviewer asks this question.

**Two verdicts under one id, mixed severity** — the ``mep.wet_wall_occupancy`` precedent:

* a **rejected** tie is an ERROR-severity FAIL, and the message names the fixture load that
  fell off the rollup and the run that is therefore being sized short. That is the fact the
  builder needs, and it is not derivable from "this pipe is 0.3" low";
* an **accepted** tie that still enters below the collector's centreline is a WARN-severity
  advisory FAIL. It flows, it is inside the tolerance the load rollup runs on, and it is
  worth a look before it is built.

**The epsilon is -1/32", not ``< 0``.** Catlin's minimum arrival delta is **-0.00025"**, on
``PR-B-SAUNA-FD-DROP`` — that is floating point in the interpolation, not geometry, and
grading it at zero would invent a finding out of the last bit of a double.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_IN

_CID = "mep.drain_tie_in"

#: The section that governs a change in direction and the fitting that makes a junction.
#: ch. 4714, not IRC P3005.3 — Minn. R. 1309.0010 subp. 3.D deletes IRC chapters 25-33.
_CODE = "MN Plumbing Code (ch. 4714) 706.3"

#: How far below a collector's centreline an arrival may read before it is a finding rather
#: than arithmetic. Catlin's tightest honest arrival is -0.00025", which is the interpolation
#: rounding and nothing else; a thirty-second of an inch is two orders above that and two
#: orders below anything a person could build wrong.
_ARRIVAL_EPSILON_IN = -1.0 / 32.0


@check(Tier.CODE, _CID)
def drain_tie_in(ctx: CheckContext) -> list[Finding]:
    """Every drain run's arrival at the pipe it discharges into.

    A run with **no candidate collector at all** is not graded here: on catlin the four that
    tie into nothing terminate at a sleeve, a receptor or an air gap, which is a
    termination rather than a rejected junction. ``mep.sewer_exit_invert`` and
    ``mep.fixture_drain_reach`` own those ends. Reporting them here would be reporting the
    building for being a building.

    ``not_applicable()`` is earned from positive evidence: this model has drain runs and not
    one of them arrives on another, so there is no junction in it for 706.3 to govern.
    """
    from typehaus.resolve.mep_queries import accumulated_serves
    from typehaus.resolve.mep_tie_ins import drain_tie_in_records

    drains = [r for r in ctx.model.pipe_runs if r.system == "drain"]
    if not drains:
        return [_na(_CID, "this model routes no drain piping, so no branch joins another",
                    code=_CODE)]

    records = drain_tie_in_records(drains)
    junctions = [tie for tie in records if tie.parent is not None]
    if not junctions:
        return [_na(_CID, f"{len(drains)} drain run(s) and no junction between any two of "
                          "them — every run terminates at a sleeve, a receptor or an air "
                          "gap", code=_CODE)]

    serves = accumulated_serves(drains)
    by_tag = {r.tag: r for r in drains}
    out: list[Finding] = []
    for tie in junctions:
        assert tie.parent is not None and tie.drop_m is not None
        drop_in = tie.drop_m / M_PER_IN
        where = f"{tie.child} arrives on {tie.parent}"
        if not tie.accepted:
            out.append(_fail(
                _CID,
                f"{where} {abs(drop_in):.3f}\" BELOW its centreline — it does not flow, and "
                f"the load rollup drops it: {_lost_load(tie, serves, by_tag)}",
                (tie.child, tie.parent), code=_CODE,
                fix=("raise this run's end, or lower the collector, until the branch "
                     "arrives at or above the collector's centreline. Check the branch's "
                     "own grade after the move — a drain spends the same inch on its slope "
                     "and on its tie-in, and `mep.drain_slope_margin` says how much is left")))
        elif drop_in < _ARRIVAL_EPSILON_IN:
            out.append(advisory(
                _CID,
                f"{where} {abs(drop_in):.3f}\" below its centreline. It is inside the 1\" "
                "the load rollup tolerates, so the pipe downstream is still sized for it — "
                "but a branch entering a collector's lower half is a wye rolled past the "
                "horizontal, and it is cheaper to look now than after the slab",
                (tie.child, tie.parent), Result.FAIL, code=_CODE,
                fix="raise the branch's last invert so it enters in the collector's upper "
                    "half, which is where a side entry belongs"))
        elif drop_in < -_ARRIVAL_EPSILON_IN:
            # Inside a thirty-second either way. Printing "-0.000" above" reads as a defect
            # and is not one: it is the interpolation's last bit, and saying so is more
            # useful than a signed zero.
            out.append(_pass(
                _CID, f"{where} on its centreline (within 1/32\") — a level side entry",
                (tie.child, tie.parent), code=_CODE))
        else:
            out.append(_pass(
                _CID, f"{where} {drop_in:+.3f}\" above its centreline — an upper-half side "
                      "entry", (tie.child, tie.parent), code=_CODE))
    return out


def _lost_load(tie, serves: dict[str, tuple[str, ...]], by_tag) -> str:
    """What the rejection actually costs, named — the half of the finding that is the point.

    "This pipe is 0.3" low" is a dimension. "``mep.pipe_sizing`` is sizing the main for a
    house with two fewer bathrooms in it" is the defect, and it is what makes this a FAIL
    rather than a note.
    """
    fixtures = serves.get(tie.child, ())
    subtree = ", ".join(fixtures) if fixtures else "no tabulated fixture"
    return (f"{len(fixtures)} fixture(s) upstream of it ({subtree}) stop counting toward "
            f"{tie.parent}'s load, so mep.pipe_sizing is sizing {tie.parent} and everything "
            "below it short")
