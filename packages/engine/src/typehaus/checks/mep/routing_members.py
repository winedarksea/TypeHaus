"""Does the pipe, duct or raceway crossing this floor actually fit between its members.

**Nobody asked.** ``duct_bay_occupancy`` asked whether a duct was *deep enough to be a
problem* and never where it sat; ``mep.run_over_void`` asks whether a run is over nothing
at all; ``mep.run_in_finished_volume`` asks whether it hangs into a room. The 8 7/8" window
that sets every starting invert on catlin's second floor — the number the whole of the
drain note's §3 is about — was prose and a router invariant, and the note's §6 conceded it
outright: *"No structural grading of a penetration."* Three trades thread that field.

It reads ``run_polylines``, so **pipes, ducts and raceways are all graded by one rule**.
That coupling is the actual content of BLD-05: a truss bay is a shared resource and the
plumber, the electrician and the HVAC contractor are all spending it, on drawings none of
them sees together.

**Per-crossing, and that is worth three false FAILs.** Banding a whole leg against the
window reads its high end against the chords even where that end sits in a clear bay with
no truss in it — which is exactly where BLD-05's "half an inch of crown clearance" comes
from. On ``PR-M-S-SUITE-WC-DRAIN``'s south leg the envelope reads +0.250" and the
per-crossing reading +0.944", and the 0.694" between them is the clear bay its high end
sits in. ``PR-M-S-BATH1-TUB-DRAIN`` and ``PR-M-S-SUITE-LAV-DRAIN`` both flip FAIL → PASS
the same way, and a diagonal raceway that "crosses" twelve members on a station-only
reading crosses exactly one when the crossings are interpolated.

**The surfaces are real, not nominal.** ``run_radii`` reads ``resolve/pipe_sections``, so a
3" drain is graded at 3.500" and 3/4" EMT at 0.922". Catlin's two real raceway defects were
invisible at the nominal size and are 0.086" and 1.115" into a chord at the real one.

``Tier.STRUCTURAL`` and **no ``PermitItemSpec``, ever.** The precedent is
``mep.run_over_void``: no IRC section says "do not run conduit across a stairwell", and
none says "put the duct in the middle of the web" either. It is a buildability rule with no
citation to hang a permit item on, and a CODE tier would trip both the coverage test and
the ``code_ref`` requirement dishonestly. ``CheckReport.counts()`` counts any ``Result.FAIL``
regardless of severity, so the weight is the same where it matters.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.routing_geometry import run_polylines, run_radii
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_crossings import CrossingWindow, member_window

_CID = "mep.run_member_crossing"


def _feet_inches(meters: float) -> str:
    """A station a builder can find with a tape, not a float in metres."""
    total_in = meters / M_PER_IN
    sign = "-" if total_in < 0 else ""
    total_in = abs(total_in)
    feet, inches = divmod(total_in, 12.0)
    return f"{sign}{int(feet)}'-{inches:.1f}\""


@check(Tier.STRUCTURAL, _CID)
def run_member_crossing(ctx: CheckContext) -> list[Finding]:
    """A run crossing a floor's members has to fit the window that floor's section gives it.

    One finding per (run, floor), naming the **tightest** crossing — its crown gap, its
    invert gap, the ``FramedMember.child_key`` and the station in feet and inches. A builder
    with a finding needs to know *which* truss, and "the leg is tight somewhere" is not an
    instruction.

    The window itself is ``resolve/mep_crossings.member_window``, which is where the three
    readings live and where the sentence each finding quotes is written. **An I-joist PASS is
    qualified** and says so: clearing both flanges is necessary and not sufficient, because
    the hole's diameter and its allowable zone along the span come off the fabricator's
    chart and this engine does not hold one.

    ``not_applicable()`` is earned — there are resolved floors and routed runs, and no leg
    of any of them meets a member line — rather than assumed. With no floors at all there is
    nothing to have a window, and that is an honest UNKNOWN.
    """
    from typehaus.resolve.mep_crossings import leg_crossings

    floors = list(ctx.model.floors)
    if not floors:
        return [_unknown(_CID, "this model resolves no floors, so no run crosses a framed "
                               "member anywhere in it")]

    runs = run_polylines(ctx)
    radii = run_radii(ctx)
    out: list[Finding] = []
    graded = 0
    for floor in floors:
        window = member_window(floor)
        if window is None:
            continue
        for kind, tag, path, z in runs:
            if len(path) < 2 or len(z) != len(path):
                continue
            radius = radii.get(tag, 0.0)
            tightest: tuple[float, float, float, str, float] | None = None
            for index in range(len(path) - 1):
                for crossing in leg_crossings(floor, path[index], path[index + 1],
                                              z[index], z[index + 1]):
                    crown_gap = window.z1_m - (crossing.z_m + radius)
                    invert_gap = (crossing.z_m - radius) - window.z0_m
                    worst = min(crown_gap, invert_gap)
                    if tightest is None or worst < tightest[0]:
                        tightest = (worst, crown_gap, invert_gap,
                                    crossing.member_key, crossing.station_m)
            if tightest is None:
                continue
            graded += 1
            out.append(_finding(kind, tag, floor.tag, radius, window, tightest))

    if graded == 0:
        return [_na(_CID, f"{len(floors)} resolved floor(s) and {len(runs)} routed run(s), "
                          "and no leg of any run crosses a framed member line in any of "
                          "them — every run travels along its bays or outside the floors")]
    return out


def _finding(kind: str, tag: str, floor_tag: str, radius_m: float,
             window: CrossingWindow,
             tightest: tuple[float, float, float, str, float]) -> Finding:
    worst, crown_gap, invert_gap, member_key, station_m = tightest
    diameter_in = 2 * radius_m / M_PER_IN
    where = (f"{kind} {tag} crosses {floor_tag} at {member_key}, "
             f"{_feet_inches(station_m)} along it")
    sizes = (f"{diameter_in:.3f}\" outside, {window.height_m / M_PER_IN:.3g}\" window")

    if worst < -1e-9:
        face, gap = (("crown", crown_gap) if crown_gap < invert_gap
                     else ("invert", invert_gap))
        return _fail(
            _CID,
            f"{where}: its {face} is {abs(gap) / M_PER_IN:.3f}\" INTO the member "
            f"({sizes}) — {window.basis}",
            (tag, floor_tag),
            fix=("raise or drop the run's elevation at this leg until its whole outside "
                 "clears the window, or take the leg along a bay instead of across the "
                 "members. Check what the move costs downstream before making it — a "
                 "drain's grade and its tie-in are both spent by the same inch"))

    # The I-joist qualification rides on ``window.basis`` rather than being appended here,
    # so a PASS and a FAIL on the same floor say the same thing about the fabricator's
    # chart and cannot drift into saying it twice or not at all.
    return _pass(
        _CID,
        f"{where}: crown {crown_gap / M_PER_IN:+.3f}\", invert "
        f"{invert_gap / M_PER_IN:+.3f}\" ({sizes}) — {window.basis}",
        (tag, floor_tag))
