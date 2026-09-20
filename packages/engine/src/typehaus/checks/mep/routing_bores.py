"""``mep.run_through_stud``/``_plate``/``_header`` — what the trades cut out of a wall.

IRC R602.6 and R602.6.1 have been on ``mn_residential``'s **not-covered** list since the
profile was written, which was honest and is no longer necessary. A run drawn through a wall
is a bore somebody drills, and until now nothing said whether the hole was legal — while
``mep.wet_wall_occupancy`` cheerfully priced a run's travel *along* a wall by the number of
studs it would go through.

The rules themselves are :mod:`typehaus.resolve.mep_bores`, stated once where the router can
reach them too: a check that graded a different limit from the one the search aims at would
make the loop impossible to close.

**The actual stud positions, never "the wall is empty".** ``ResolvedWall.members`` carries
each stud's own plan point and its orientation, so a staggered wall — whose studs alternate
between two rows — is graded against the studs that resolved rather than against a spacing.
That is the case the reviewer's framing policy calls out by name.

**One finding per (run, wall), naming the worst cut.** A 2" branch travelling twelve feet
down a wet wall bores nine studs; nine findings would bury the one that matters, and the
count is in the message.

**A header is collected and honestly ungraded.** ``mep.run_through_header`` exists because
the member list left headers out, so a run over a door met nothing at all and the report was
silent about the one member carrying an opening's whole load. No IRC table publishes a bore
limit for a header, so the verdict is UNKNOWN with the numbers — except a penetration as deep
as the member, which is the header's removal and needs no table to fail.

``Tier.STRUCTURAL`` and no ``PermitItemSpec``: the same footing as
``mep.run_member_crossing``. ``CheckReport.counts()`` counts any ``Result.FAIL`` regardless
of severity.

``houses/catlin/notes/framing_bore_limits.md`` is the hand-worked oracle.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding

_STUD = "mep.run_through_stud"
_PLATE = "mep.run_through_plate"
_HEADER = "mep.run_through_header"

#: Categories that are a stud for R602.6's purposes. A king, a jack and a cripple are all
#: studs; the section does not distinguish them and neither does the drill.
STUD_CATEGORIES = frozenset({"stud", "king", "jack", "cripple"})


def bearing_wall_tags(ctx: CheckContext) -> frozenset[str]:
    """Every wall some floor's joists actually bear on, plus every foundation wall.

    Read from ``JoistSpec.bearing_refs`` — the model's own statement of what carries what —
    rather than guessed from "exterior". The difference is 25% against 40% of a stud's
    depth, which for a 2x6 is nearly an inch of pipe and is the whole question for a 2"
    branch.
    """
    tags = {wall.tag for wall in ctx.model.walls if wall.is_foundation}
    for floor in ctx.model.floors:
        system = ctx.model.plan.by_tag(floor.tag)
        tags.update(getattr(getattr(system, "joists", None), "bearing_refs", ()) or ())
    return frozenset(tags)


def _crossings(ctx: CheckContext):
    """``(run tag, wall, [MemberCut])`` for every run that meets a wall's framing.

    Indexed by the walls' own plan footprints, because the naive loop is 108 runs against
    99 walls against every member of each and is the kind of thing that turns a check run
    from ten seconds into a minute.
    """
    from shapely import STRtree
    from shapely.geometry import LineString, Point

    from typehaus.resolve.mep_bores import leg_crossings
    from typehaus.resolve.mep_envelopes import run_polylines, run_radii

    walls = [wall for wall in ctx.model.walls if wall.members]
    if not walls:
        return
    hulls = [LineString(wall.axis).buffer(wall.thickness_m) for wall in walls]
    index = STRtree(hulls)
    radii = run_radii(ctx.model)

    for _kind, tag, path, z in run_polylines(ctx.model):
        if len(path) < 2 or len(z) != len(path):
            continue
        radius = radii.get(tag, 0.0)
        found: dict[str, list] = {}
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            probe = (Point(a) if a == b else LineString([a, b])).buffer(radius)
            for position in index.query(probe):
                wall = walls[int(position)]
                cuts = leg_crossings(wall, a, b, z[i], z[i + 1], radius)
                if cuts:
                    found.setdefault(wall.tag, []).extend(cuts)
        for wall in walls:
            if wall.tag in found:
                yield (tag, wall, found[wall.tag])


@check(Tier.STRUCTURAL, _STUD)
def run_through_stud(ctx: CheckContext) -> list[Finding]:
    """Every stud a run would have to bore, against IRC R602.6.

    A bore over the limit is a FAIL with the number; an **engineered** stud — an LVL post, a
    built-up column — is UNKNOWN, because it is cut to the fabricator's chart and no IRC
    table describes it. Reporting a confident PASS about one of those would be the worst of
    the three answers.

    **A notch is not proposed and an existing one is still graded.** This check reads the
    run's outside diameter and asks for a bore, which is what a trade drills; where the
    model authors a notch, ``mep_bores.stud_notch`` is the predicate and it is reached the
    same way.
    """
    from typehaus.resolve.mep_bores import stud_bore

    bearing = bearing_wall_tags(ctx)
    out: list[Finding] = []
    seen = 0
    for tag, wall, cuts in _crossings(ctx):
        studs = [cut for cut in cuts if cut.category in STUD_CATEGORIES]
        if not studs:
            continue
        seen += 1
        verdicts = [(cut, stud_bore(cut.profile, cut.diameter_in,
                                    bearing=wall.tag in bearing)) for cut in studs]
        bad = [(cut, v) for cut, v in verdicts if v.ok is False]
        unsure = [(cut, v) for cut, v in verdicts if v.ok is None]
        where = (f"{tag} would bore {len(studs)} member(s) of {wall.tag} "
                 f"({'bearing' if wall.tag in bearing else 'non-bearing'})")
        if bad:
            cut, verdict = max(bad, key=lambda item: item[1].actual_in
                               - (item[1].limit_in or 0.0))
            out.append(_fail(
                _STUD, f"{where}: the worst is {cut.member_key} — {verdict.basis}",
                (tag, wall.tag),
                fix=(verdict.remedy or "take the run to a clear bay, or drop to a smaller "
                     "branch if its fixture-unit load allows one. Never a notch, and never "
                     "a reinforcement this engine added on its own")))
        elif unsure:
            cut, verdict = unsure[0]
            out.append(_unknown(
                _STUD, f"{where}: {cut.member_key} is not graded — {verdict.basis}",
                (tag, wall.tag)))
        else:
            worst = min(verdicts, key=lambda item: (item[1].limit_in or 0.0)
                        - item[1].actual_in)
            out.append(_pass(_STUD, f"{where}: the tightest is {worst[0].member_key} — "
                                    f"{worst[1].basis}", (tag, wall.tag)))
    if not seen:
        return [_na(_STUD, "no run's leg meets a stud of any resolved wall, so nothing in "
                           "this model is bored through framing", ())]
    return out


def plate_ties(ctx: CheckContext) -> dict[str, frozenset[str]]:
    """``{wall tag: run tags the ties on it cover}``, ``"*"`` meaning every cut in it.

    A ``PlateTie`` is a spec and resolves to nothing, so it is read off the authored plan
    rather than off the resolved model — the same way ``bearing_wall_tags`` reads
    ``JoistSpec.bearing_refs``.
    """
    from typehaus.model.structure import PlateTie

    out: dict[str, set[str]] = {}
    for element in ctx.model.plan.all_elements():
        if isinstance(element, PlateTie):
            out.setdefault(element.wall, set()).update(element.covers or ("*",))
    return {wall: frozenset(covers) for wall, covers in out.items()}


@check(Tier.STRUCTURAL, _PLATE)
def run_through_plate(ctx: CheckContext) -> list[Finding]:
    """A top plate cut for a run, against IRC R602.6.1.

    **Over 50% is conditional, not illegal**, and saying so is the whole value of this
    check: a cut plate with a 16 ga tie across it is built every day. Since 2026-09-19 the
    model can say the tie is there — ``PlateTie`` — so the absence of one IS evidence of
    absence and the verdict is an honest FAIL naming what to author, rather than the
    permanent UNKNOWN that stood while the model had no vocabulary for a strap. The engine
    still never adds the strap itself: that is a structural detail a person draws.

    A penetration **as wide as the plate** is not a plate cut at all — it interrupts the
    plate, which is a framed opening with a header over it. Those are UNKNOWN here and are
    graded, as far as anything grades them, by ``mep.run_through_header``.
    """
    from typehaus.resolve.mep_bores import top_plate_cut

    ties = plate_ties(ctx)
    out: list[Finding] = []
    seen = 0
    for tag, wall, cuts in _crossings(ctx):
        # TOP plates only. R602.6.1 is about the plate that ties the wall together at its
        # head; a bottom plate bored for a riser is a hole in a board on a deck and the
        # section has nothing to say about it.
        plates = [cut for cut in cuts
                  if cut.category == "plate" and "top" in cut.member_key]
        if not plates:
            continue
        seen += 1
        covered = ties.get(wall.tag, frozenset())
        tied = "*" in covered or tag in covered
        verdicts = [(cut, top_plate_cut(cut.profile, cut.diameter_in, tie=tied))
                    for cut in plates]
        bad = [(cut, v) for cut, v in verdicts if v.ok is False]
        unsure = [(cut, v) for cut, v in verdicts if v.ok is None]
        where = f"{tag} passes through {len(plates)} top plate(s) of {wall.tag}"
        if bad:
            cut, verdict = bad[0]
            out.append(_fail(
                _PLATE, f"{where}: {cut.member_key} — {verdict.basis}", (tag, wall.tag),
                fix=(f"{verdict.remedy}: PlateTie(uid=\"\", tag=\"PTIE-{wall.tag}\", "
                     f"wall=\"{wall.tag}\", product=\"Simpson PSPN58\") — or take the run "
                     "to a bay where the plate is not cut past half its width")))
        elif unsure:
            cut, verdict = unsure[0]
            out.append(_unknown(_PLATE, f"{where}: {cut.member_key} is not graded — "
                                        f"{verdict.basis}", (tag, wall.tag)))
        else:
            cut, verdict = verdicts[0]
            out.append(_pass(_PLATE, f"{where}: {verdict.basis}", (tag, wall.tag)))
    if not seen:
        return [_na(_PLATE, "no run passes through a top plate of any resolved wall", ())]
    return out


@check(Tier.STRUCTURAL, _HEADER)
def run_through_header(ctx: CheckContext) -> list[Finding]:
    """Every header a run would have to bore — and the admission that nothing grades it.

    Until 2026-09-19 ``leg_crossings`` did not collect headers at all, so a run over a door
    met nothing and the report was silent about the one member in a wall that carries an
    opening's whole tributary load. Silence is not a verdict.

    **No prescriptive table reaches a header** (see ``mep_bores.header_bore``): R502.8.1 is
    floor joists and R602.6 is studs, so an ordinary hole is UNKNOWN with its numbers and
    the remedy is the header designer's allowable, not a fraction this engine picked. The
    determinate case is a penetration as deep as the member — a severed header — and that
    is a FAIL that needs no table.
    """
    from typehaus.resolve.mep_bores import header_bore

    out: list[Finding] = []
    seen = 0
    for tag, wall, cuts in _crossings(ctx):
        headers = [cut for cut in cuts if cut.category == "header"]
        if not headers:
            continue
        seen += 1
        verdicts = [(cut, header_bore(cut.profile, cut.diameter_in)) for cut in headers]
        bad = [(cut, v) for cut, v in verdicts if v.ok is False]
        unsure = [(cut, v) for cut, v in verdicts if v.ok is None]
        where = f"{tag} would bore {len(headers)} header(s) of {wall.tag}"
        if bad:
            cut, verdict = bad[0]
            out.append(_fail(_HEADER, f"{where}: {cut.member_key} — {verdict.basis}",
                             (tag, wall.tag), fix=verdict.remedy or ""))
        elif unsure:
            cut, verdict = unsure[0]
            out.append(_unknown(_HEADER, f"{where}: {cut.member_key} is not graded — "
                                         f"{verdict.basis}", (tag, wall.tag)))
        else:  # pragma: no cover - header_bore publishes no PASS today
            cut, verdict = verdicts[0]
            out.append(_pass(_HEADER, f"{where}: {verdict.basis}", (tag, wall.tag)))
    if not seen:
        return [_na(_HEADER, "no run's leg meets a header of any resolved wall", ())]
    return out
