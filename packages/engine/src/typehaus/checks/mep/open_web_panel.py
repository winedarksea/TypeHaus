"""``mep.open_web_panel`` — how many runs one web opening will actually take.

``mep.run_member_crossing`` asks how TALL the slot is. Nothing asked where along the member
there is a slot at all, and on an open-web deck that is the binding question: the engine
reads a floor truss as a continuous 8 7/8" chase, so **thirteen 4" ducts crossing every
truss inside a 41" band all pass**. A real truss has webs at panel points, and a duct lands
in an opening or it lands on a web.

**Unauthored is UNKNOWN naming the floor, never a pass.** A truss's panel layout is a shop
drawing and this engine has no business inventing a pitch; ``JoistSpec.web_panel_pitch``,
``web_opening_width`` and ``web_panel_offset`` are where a house states the fabricator's,
and ``mep.run_member_crossing`` keeps grading the z window either way.

**A TIER, not a sum** — the same rule ``resolve/mep_packing`` makes about a bay's clear
width, and for the same reason. Two runs that share an elevation have to fit side by side
in one opening; two that stack do not compete at all, and summing them made a 15" opening
full of two 4" ducts that never meet. Runs are clustered by overlapping surface z band and
each cluster is measured on its own.

**Width along the MEMBER, not diameter.** A 4" duct crossing a truss square occupies 4" of
its length; the same duct crossing at 45° occupies 5.66", because a cylinder cut obliquely
is an ellipse. An opening filled by the diameters is not full and an opening filled by the
ellipses is.

``Tier.STRUCTURAL``, no ``PermitItemSpec``: no IRC section publishes a truss's panel layout
— it is the fabricator's geometry, the same footing ``member_window``'s open-web reading
already stands on.
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
    from typehaus.resolve.mep_crossings import member_window, web_panels
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
        panels = web_panels(floor)
        if panels is None:
            out.append(_unknown(
                _CID, f"{floor.tag} is framed in open-web members and states no panel "
                      "layout, so the model reads this truss as a CONTINUOUS slot: every "
                      "crossing of it passes on the chord-to-chord window alone, however "
                      "many of them there are and wherever along the span they land. "
                      "Author the fabricator's web_panel_pitch, web_opening_width and "
                      "web_panel_offset on its JoistSpec",
                (floor.tag,)))
            continue
        out.extend(_graded(floor, panels, runs, sections))

    if not any(f.result.value in ("fail", "pass") for f in out):
        out.append(_pass(_CID, f"{len(decks)} open-web deck(s) and none of them states a "
                               "panel layout to grade against", ()))
    return out


def _graded(floor, panels, runs, sections) -> list[Finding]:
    """One deck whose layout is authored: cluster its crossings per opening, per tier."""
    from typehaus.resolve.mep_crossings import leg_crossings
    from typehaus.resolve.mep_envelopes import insulation_thickness_m

    along_x = floor.direction == "x"
    # (member key, opening index) -> [(tag, width along the member, z low, z high)]
    filled: dict[tuple[str, int], list[tuple[str, float, float, float]]] = {}
    for _kind, tag, path, z in runs:
        if len(path) < 2 or len(z) != len(path):
            continue
        half_w, half_d, insulation = sections.get(tag, (0.0, 0.0, None))
        lagging = insulation_thickness_m(insulation) or 0.0
        width = 2 * (half_w + lagging)
        depth = half_d + lagging
        for leg in range(len(path) - 1):
            a, b = path[leg], path[leg + 1]
            oblique = _obliquity(a, b, along_x)
            if oblique is None:
                continue
            for crossing in leg_crossings(floor, a, b, z[leg], z[leg + 1]):
                key = (crossing.member_key, panels.index_at(crossing.station_m))
                filled.setdefault(key, []).append(
                    (tag, width * oblique, crossing.z_m - depth, crossing.z_m + depth))

    # **One finding per OPENING INDEX, not per member.** Every truss on a deck shares one
    # panel layout, so a lane that over-fills opening 3 over-fills opening 3 of every truss
    # it crosses — thirteen findings saying one thing. The members are counted in the
    # message instead, which is also the number a campaign wants: it is how many trusses
    # have to be re-thought if the lane does not move.
    over: dict[int, tuple[float, set[str], list]] = {}
    for (member_key, index), occupants in sorted(filled.items()):
        for tier in _tiers(occupants):
            used = sum(width for _tag, width, _low, _high in tier)
            if used <= panels.opening_m + 1e-9:
                continue
            worst_used, members, worst_tier = over.get(index, (0.0, set(), []))
            members.add(member_key)
            over[index] = ((used, members, tier) if used > worst_used
                           else (worst_used, members, worst_tier))

    out: list[Finding] = []
    for index, (used, members, tier) in sorted(over.items()):
        low = panels.offset_m + index * panels.pitch_m + panels.web_width_m / 2.0
        high = low + panels.opening_m
        names = sorted(tag for tag, _w, _l, _h in tier)
        out.append(_fail(
            _CID,
            f"{floor.tag}'s web opening between {feet_inches(low)} and {feet_inches(high)} "
            f"is over-subscribed on {len(members)} of its members: {len(tier)} runs share "
            f"one elevation there and want {used / M_PER_IN:.2f}\" of its "
            f"{panels.opening_m / M_PER_IN:.2f}\" clear width — {', '.join(names)}. No "
            "arrangement fixes this; one of them has to take another opening, another tier, "
            "or another lane",
            (floor.tag, *names),
            fix="move one run to the next panel opening, drop it to the other tier of the "
                "web window, or take it along a bay instead of across the members"))

    if not out:
        openings = len({index for _member, index in filled})
        out.append(_pass(
            _CID,
            f"{floor.tag}: {len(runs)} run(s) cross {openings} web opening(s) at "
            f"{panels.pitch_m / M_PER_IN:.3g}\" panel pitch and no opening is over-subscribed "
            f"at any one elevation ({panels.opening_m / M_PER_IN:.3g}\" clear between webs)",
            (floor.tag,)))
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
