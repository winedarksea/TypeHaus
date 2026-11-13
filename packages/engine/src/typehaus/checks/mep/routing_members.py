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

import math

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep._format import feet_inches
from typehaus.checks.mep.routing_geometry import run_polylines, run_radii
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_crossings import CrossingWindow, member_window

_CID = "mep.run_member_crossing"


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
    chart. Where the library holds that chart (``JoistHoleChart``) each hole is graded on it
    by ``_ijoist_finding``.

    ``not_applicable()`` is earned — there are resolved floors and routed runs, and no leg
    of any of them meets a member line — rather than assumed. With no floors at all there is
    nothing to have a window, and that is an honest UNKNOWN.
    """
    from typehaus.resolve.mep_crossings import floor_supports, leg_crossings, web_grade

    floors = list(ctx.model.floors)
    if not floors:
        return [_unknown(_CID, "this model resolves no floors, so no run crosses a framed "
                               "member anywhere in it")]

    from typehaus.resolve.mep_envelopes import insulation_thickness_m, run_sections

    runs = run_polylines(ctx)
    radii = run_radii(ctx)
    # A rectangular duct is its width across the member and its depth in the window.
    sections = run_sections(ctx.model)
    out: list[Finding] = []
    graded = 0
    for floor in floors:
        chart = _ijoist_chart(ctx, floor)
        window = member_window(floor, chart=chart)
        if window is None:
            continue
        supports = (floor_supports(ctx.model, floor)
                    if chart is not None and window.kind == "i_joist" else ())
        # An open-web deck that quotes the maker's openings narrows the window ALONG the
        # member as well as across it: a run lands in an opening it fits, or it lands on a
        # web. Unquoted, no member carries a shape and the reading is unchanged —
        # ``mep.open_web_panel`` is the one that says so, once, naming the floor.
        webbed = {m.child_key: m for m in floor.members if m.web is not None}
        # Every crossing on this floor first, keyed by member, because R502.8.1's spacing
        # rule is a question about the OTHER holes in the same joist and no per-run pass can
        # see them. Two 2" drains 1 1/2" apart each fit the window and each clear D/3; the
        # pair is what the section forbids.
        by_member: dict[str, list[tuple[str, float, float]]] = {}
        per_run: dict[str, list] = {}
        oblique: dict[tuple[str, str, float], float] = {}
        for _kind, tag, path, z in runs:
            if len(path) < 2 or len(z) != len(path):
                continue
            radius = radii.get(tag, 0.0)
            for index in range(len(path) - 1):
                for crossing in leg_crossings(floor, path[index], path[index + 1],
                                              z[index], z[index + 1]):
                    per_run.setdefault(tag, []).append(crossing)
                    oblique[(tag, crossing.member_key, crossing.station_m)] = _stretch(
                        path[index], path[index + 1], floor.direction == "x")
                    by_member.setdefault(crossing.member_key, []).append(
                        (tag, crossing.station_m, radius))

        for kind, tag, _path, _z in runs:
            crossings = per_run.get(tag)
            if not crossings:
                continue
            radius = radii.get(tag, 0.0)
            half_w, half_d, lagging = sections.get(tag, (radius, radius, None))
            # The window must hold the envelope, lagging included, not the bare pipe.
            half_d += insulation_thickness_m(lagging) or 0.0
            tightest: tuple[float, float, float, str, float] | None = None
            on_web: tuple[float, str, float, str] | None = None
            for crossing in crossings:
                crown_gap = window.z1_m - (crossing.z_m + half_d)
                invert_gap = (crossing.z_m - half_d) - window.z0_m
                worst = min(crown_gap, invert_gap)
                if tightest is None or worst < tightest[0]:
                    tightest = (worst, crown_gap, invert_gap,
                                crossing.member_key, crossing.station_m)
                member = webbed.get(crossing.member_key)
                grade = (web_grade(
                    floor, member, crossing.station_m, crossing.z_m,
                    2 * half_w * oblique[(tag, crossing.member_key, crossing.station_m)],
                    2 * half_d, abs(half_w - half_d) < 1e-9) if member is not None else None)
                if grade is not None and not grade.ok:
                    # The first miss is named; later ones add only the count.
                    count = on_web[0] + 1 if on_web is not None else 1.0
                    if on_web is None:
                        on_web = (count, crossing.member_key, crossing.station_m, grade.why)
                    else:
                        on_web = (count, *on_web[1:])
            if tightest is None:
                continue
            graded += 1
            out.append(_finding(kind, tag, floor.tag, half_d, window, tightest))
            if on_web is not None:
                out.append(_web_finding(kind, tag, floor.tag, on_web))
            bore = (_ijoist_finding(floor, chart, tag, radius, crossings, by_member,
                                    supports)
                    if chart is not None and window.kind == "i_joist" else
                    _bore_finding(ctx, floor, window, tag, radius, crossings, by_member))
            if bore is not None:
                out.append(bore)

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
             f"{feet_inches(station_m)} along it")
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


def _stretch(a, b, along_x: bool) -> float:
    """``1 / sin`` of the angle a leg makes with the member lines: a round run crossing
    obliquely occupies that much more of the member's length."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    across = abs(dy) if along_x else abs(dx)
    return math.hypot(dx, dy) / across if across > 1e-9 else 1.0


def _web_finding(kind: str, tag: str, floor_tag: str,
                 on_web: tuple[float, str, float, str]) -> Finding:
    """A crossing that does not fit the opening it lands in (or lands in none).

    The other half of an open-web reading: ``open_web_opening_m`` says how tall the slot is,
    and each truss's ``OpenWebShape`` says where along it there is an opening and what that
    opening takes (D a round, R1 the chase rectangle, a TrimEnd nothing).
    """
    count, member_key, station_m, why = on_web
    more = f" (and {int(count) - 1} more crossing(s))" if count > 1 else ""
    return _fail(
        _CID,
        f"{kind} {tag} crosses {floor_tag} at {member_key}, {feet_inches(station_m)} along "
        f"it{more}: not in an opening it fits, ON A WEB — {why}. A truss web is not bored or "
        "notched by anyone, ever",
        (tag, floor_tag),
        fix="move the leg along the member into an opening it fits, or take it along a bay "
            "instead of across the members")


def _bore_finding(ctx, floor, window: CrossingWindow, tag: str, radius_m: float,
                  crossings: list, by_member: dict) -> Finding | None:
    """R502.8.1's other two limits: the hole's DIAMETER, and its distance to the next cut.

    The z window says a run fits between the chords. It does not say the hole is legal, and
    on a solid-sawn joist those are different questions: a 3" hole in a 2x8 sits comfortably
    inside a 3 1/4" window and is still half an inch over D/3. Nothing asked until now, which
    is what "notching and boring limits (R502.8/R602.6)" on the profile's not-covered list
    meant in practice.

    **Only where a code table reaches.** An open-web truss hands a service its web space and
    cuts nothing; an I-joist and an LVL are the fabricator's chart. This returns ``None`` for
    both rather than applying a solid-sawn rule to a product it has never governed.
    """
    from typehaus.resolve.mep_bores import JOIST_HOLE_SPACING_IN, joist_bore

    if window.kind != "solid_sawn":
        return None
    member = next((m for m in floor.members if m.category == "joist"), None)
    if member is None:
        return None
    diameter_in = 2 * radius_m / M_PER_IN

    # The nearest OTHER cut in any member this run crosses — clear distance between the two
    # holes' edges, not between their centres.
    nearest_in: float | None = None
    for crossing in crossings:
        for other_tag, station_m, other_radius in by_member.get(crossing.member_key, ()):
            if other_tag == tag:
                continue
            clear = (abs(station_m - crossing.station_m) - radius_m - other_radius)
            clear_in = clear / M_PER_IN
            if nearest_in is None or clear_in < nearest_in:
                nearest_in = clear_in

    verdict = joist_bore(member.profile, diameter_in, nearest_cut_in=nearest_in)
    if verdict.ok is not False:
        return None
    spacing = (f' and its nearest neighbour is {nearest_in:.2f}" away (2" minimum)'
               if nearest_in is not None and nearest_in < JOIST_HOLE_SPACING_IN else "")
    return _fail(
        _CID, f"{tag} bores {floor.tag}: {verdict.basis}{spacing}", (tag, floor.tag),
        fix="take the leg along a bay instead of across the members, or split the run "
            "into two smaller ones if its load allows. Never a notch, and never a "
            "reinforcement this engine added on its own")


def _ijoist_chart(ctx, floor):
    """The library's hole ladder for this floor's I-joist, or ``None``."""
    from typehaus.resolve.mep_hole_chart import joist_hole_chart

    joist = next((m for m in floor.members if m.category == "joist"), None)
    library = getattr(getattr(ctx, "plan", None), "library", None)
    return None if joist is None or library is None else joist_hole_chart(library,
                                                                           joist.profile)


def _ijoist_finding(floor, chart, tag: str, radius_m: float, crossings: list,
                    by_member: dict, supports: tuple = ()) -> Finding | None:
    """Every hole this run drills in an I-joist, against the maker's published ladder.

    One finding per (run, floor): the first hole out of zone or too close to a neighbour
    FAILs naming the joist and station; otherwise the tightest PASS cites its row. The rule
    is ``resolve/mep_hole_chart.ijoist_hole_verdict``, which the router reads too.
    """
    from typehaus.resolve.mep_bores import joist_bore
    from typehaus.resolve.mep_crossings import support_faces
    from typehaus.resolve.mep_hole_chart import DRILLED_HOLE_CLEARANCE_IN

    members = {m.child_key: m for m in floor.members}
    half = DRILLED_HOLE_CLEARANCE_IN * M_PER_IN / 2.0
    graded: list[tuple[int, float, object, str, float]] = []
    for crossing in crossings:
        member = members.get(crossing.member_key)
        if member is None or member.category != "joist":
            continue
        lo, hi = support_faces(floor, member, supports)
        s = crossing.station_m
        centre = (None if lo is None or hi is None
                  else min(s - lo, hi - s) / M_PER_IN)
        nearest = nearest_d = None
        for other_tag, station_m, other_r in by_member.get(crossing.member_key, ()):
            if other_tag == tag and abs(station_m - s) < 1e-9:
                continue
            clear = (abs(station_m - s) - radius_m - other_r - 2 * half) / M_PER_IN
            if nearest is None or clear < nearest:
                nearest, nearest_d = clear, 2 * (other_r + half) / M_PER_IN
        verdict = joist_bore(member.profile, 2 * radius_m / M_PER_IN, chart=chart,
                             edge_to_support_in=centre, nearest_cut_in=nearest,
                             nearest_diameter_in=nearest_d)
        rank = {False: 0, None: 1, True: 2}[verdict.ok]
        graded.append((rank, centre if centre is not None else 0.0, verdict,
                       crossing.member_key, s))
    if not graded:
        return None
    graded.sort(key=lambda g: (g[0], g[1]))
    rank, _c, verdict, key, station = graded[0]
    more = sum(1 for g in graded if g[0] == rank) - 1
    where = (f"{tag} bores {floor.tag} at {key}, {feet_inches(station)} along it"
             + (f" (and {more} more like it)" if more and rank != 2 else "")
             + (f", {len(graded)} hole(s) in all" if rank == 2 else ""))
    if rank == 2:
        return _pass(_CID, f"{where}: {verdict.basis}", (tag, floor.tag))
    if rank == 1:
        return _unknown(_CID, f"{where}: {verdict.basis}", (tag, floor.tag))
    return _fail(_CID, f"{where}: {verdict.basis}", (tag, floor.tag),
                 fix=verdict.remedy or "move the crossing into the chart's zone")
