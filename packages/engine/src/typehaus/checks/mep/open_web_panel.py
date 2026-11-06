"""``mep.open_web_panel`` — how many runs one web opening will actually take.

``mep.run_member_crossing`` asks whether a run clears the chords and lands in an opening at
all. This asks the second question of the openings themselves: each open-web truss carries
an ``OpenWebShape`` (``resolve/open_web.py``) derived from the deck's published
``JoistSpec.web_openings``, and a run is graded against the opening it lands in.

* **A D opening takes ONE run** (the maker's round hole, or its R2 rectangle). Two runs
  through one web pocket is the defect, however small each is.
* **The R1 chase takes runs side by side** in one tier up to its published width, and tiers
  stack up to its published height.
* A TrimEnd takes nothing; that and the size/outline limits are ``run_member_crossing``'s.

**Unauthored is UNKNOWN naming the floor, never a pass.** A truss's layout is the maker's
shop drawing; ``JoistSpec.web_openings`` is where a house quotes what is published. A pitch
it could not quote (``panel_pitch_assumed``) places every pocket, so that deck is UNKNOWN too.

**Width along the MEMBER, not diameter.** A 4" duct crossing a truss square occupies 4" of
its length; the same duct crossing at 45 degrees occupies 5.66", because a cylinder cut
obliquely is an ellipse.

``Tier.STRUCTURAL``, no ``PermitItemSpec``: no IRC section publishes a truss's openings; it
is the maker's chart, the same footing ``member_window``'s open-web reading stands on.
"""

from __future__ import annotations

from math import hypot

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep._format import feet_inches
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

_CID = "mep.open_web_panel"


@check(Tier.STRUCTURAL, _CID)
def open_web_panel(ctx: CheckContext) -> list[Finding]:
    """Every web opening of every open-web deck, against what crosses it."""
    from typehaus.resolve.mep_crossings import member_window
    from typehaus.resolve.mep_envelopes import run_polylines, run_sections

    decks = [floor for floor in ctx.model.floors
             if (window := member_window(floor)) is not None and window.kind == "open_web"]
    if not decks:
        return [_na(_CID, "no floor in this model is framed in open-web members, so no run "
                          "crosses a web opening", ())]

    sections = run_sections(ctx.model)
    runs = list(run_polylines(ctx.model))
    out: list[Finding] = []
    for floor in decks:
        if floor.web_openings is None or not any(m.web is not None for m in floor.members):
            out.append(_unknown(
                _CID, f"{floor.tag} is framed in open-web members and quotes no published "
                      "web openings, so the model reads this truss as a CONTINUOUS slot: "
                      "every crossing of it passes on the chord-to-chord window alone, "
                      "however many of them there are and wherever along the span they "
                      "land. Author the maker's PublishedWebOpenings on its "
                      "JoistSpec.web_openings",
                (floor.tag,)))
            continue
        out.extend(_graded(floor, runs, sections))
    return out


def _graded(floor, runs, sections) -> list[Finding]:
    """One deck with published openings: who shares which opening of which truss."""
    from typehaus.resolve.mep_crossings import leg_crossings
    from typehaus.resolve.mep_envelopes import insulation_thickness_m
    from typehaus.resolve.open_web import RunSize, grade_crossing, run_of

    along_x = floor.direction == "x"
    members = {m.child_key: m for m in floor.members if m.web is not None}
    # (member key, opening key) -> {run tag: (width along member, z low, z high)}
    filled: dict[tuple[str, str], dict[str, tuple[float, float, float]]] = {}
    for _kind, tag, path, z in runs:
        if len(path) < 2 or len(z) != len(path):
            continue
        half_w, half_d, insulation = sections.get(tag, (0.0, 0.0, None))
        lagging = insulation_thickness_m(insulation) or 0.0
        width, depth = 2 * (half_w + lagging), half_d + lagging
        round_ = abs(half_w - half_d) < 1e-9
        for leg in range(len(path) - 1):
            a, b = path[leg], path[leg + 1]
            oblique = _obliquity(a, b, along_x)
            if oblique is None:
                continue
            for crossing in leg_crossings(floor, a, b, z[leg], z[leg + 1]):
                member = members.get(crossing.member_key)
                if member is None:
                    continue
                run = run_of(member, crossing.station_m, along_x)
                grade = grade_crossing(member.web, run, crossing.z_m - member.z0_m,
                                       RunSize(width * oblique, 2 * depth, round_))
                if grade.opening is None or grade.opening.kind == "trim_end":
                    continue  # run_member_crossing names the web or TrimEnd hit
                filled.setdefault((crossing.member_key, grade.opening.key), {})[tag] = (
                    width * oblique, crossing.z_m - depth, crossing.z_m + depth)

    # **One finding per set of runs and opening kind, not per truss.** Trusses repeat one
    # layout, so a lane that over-fills a pocket over-fills it on every truss it crosses;
    # the members are counted in the message, which is how many trusses need re-thinking.
    over: dict[tuple[str, tuple[str, ...]], list[tuple[str, str, float, float]]] = {}
    row = floor.web_openings
    for (member_key, opening_key), occupants in sorted(filled.items()):
        opening = next(o for o in members[member_key].web.openings if o.key == opening_key)
        entries = [(tag, w, low, high) for tag, (w, low, high) in occupants.items()]
        if opening.kind == "D":
            if len(entries) > 1:
                names = tuple(sorted(tag for tag, *_ in entries))
                over.setdefault(("D", names), []).append(
                    (member_key, opening_key, 0.0, opening.round_m))
            continue
        tiers = _tiers(entries)
        width_cap, height_cap = opening.rect_m
        worst = max((sum(w for _t, w, _l, _h in tier) for tier in tiers), default=0.0)
        stacked = sum(max(h - lo for _t, _w, lo, h in tier) for tier in tiers)
        if worst > width_cap + 1e-9 or stacked > height_cap + 1e-9:
            names = tuple(sorted(tag for tag, *_ in entries))
            over.setdefault((opening.kind, names), []).append(
                (member_key, opening_key, max(worst, 0.0), max(stacked, 0.0)))

    out: list[Finding] = []
    for (kind, names), hits in sorted(over.items()):
        member_key, opening_key, used, extra = hits[0]
        shape = members[member_key].web
        opening = next(o for o in shape.openings if o.key == opening_key)
        where = feet_inches((opening.run0_m + opening.run1_m) / 2.0)
        if kind == "D":
            detail = (f"{len(names)} runs share one web pocket (a {extra / M_PER_IN:.3g}\" "
                      "round, or R2 where the row has it) and a pocket takes one")
        else:
            detail = (f"{len(names)} runs want {used / M_PER_IN:.2f}\" across by "
                      f"{extra / M_PER_IN:.2f}\" of height in the "
                      f"{opening.rect_m[0] / M_PER_IN:g}\" x {opening.rect_m[1] / M_PER_IN:g}\" "
                      "chase")
        out.append(_fail(
            _CID,
            f"{floor.tag}'s {kind} opening {opening_key} (about {where} from the truss "
            f"start, first on {member_key}, {len(hits)} of its members) is over-subscribed: "
            f"{detail} — {', '.join(names)}. No arrangement fixes this; one of them has to "
            "take another opening or another lane",
            (floor.tag, *names),
            fix="move one run to its own web pocket, into the chase, or take it along a bay "
                "instead of across the members"))

    if not out:
        openings = len({key for key in filled})
        shape = next(iter(members.values())).web
        crossing = len({tag for occupants in filled.values() for tag in occupants})
        said = (f"{floor.tag}: {crossing} run(s) land in {openings} web opening(s) and none "
                f"is over-subscribed ({shape.pitch_m / M_PER_IN:.3g}\" panels, one run per D "
                "pocket)")
        # Where the pockets stand rests on the pitch: unpublished, it is no PASS.
        out.append(_unknown(
            _CID, f"{said}, but the panel pitch is assumed, not published, so where each "
                  f"pocket stands is this house's working figure [{row.source}]",
            (floor.tag,), fix="replace the assumed pitch with the maker's shop layout")
                   if row.panel_pitch_assumed else _pass(_CID, said, (floor.tag,)))
    return out


def _obliquity(a, b, along_x: bool) -> float | None:
    """``1 / sin`` of the angle this leg makes with the member lines, or None if parallel.

    A cylinder cut obliquely is an ellipse: a 4" duct crossing a truss square occupies 4" of
    its length and the same duct at 45° occupies 5.66". Grading the diameter would call a
    full opening empty.
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    across = abs(dy) if along_x else abs(dx)
    if across < 1e-9:
        return None  # a leg running ALONG a bay crosses no member
    return hypot(dx, dy) / across


def _tiers(occupants) -> list[list]:
    """Cluster occupants of one opening by overlapping surface z band.

    Runs that share an elevation share the opening's clear width; runs that stack do not.
    Greedy over the band's low edge, which is exact for a one-dimensional overlap graph.
    """
    out: list[list] = []
    for entry in sorted(occupants, key=lambda row: row[2]):
        _tag, _width, low, high = entry
        for tier in out:
            if any(low < other_high - 1e-9 and other_low < high - 1e-9
                   for _t, _w, other_low, other_high in tier):
                tier.append(entry)
                break
        else:
            out.append([entry])
    return out
