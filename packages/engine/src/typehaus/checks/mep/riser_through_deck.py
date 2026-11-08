"""``mep.riser_through_deck`` — a vertical through a floor needs a hole somebody drew.

``plans/TODO.md`` has carried it since 2026-09-15: "``FS-M-MECH`` still carries the vents,
the radon riser and nine conduits through its joist field **undrawn**." ``FO-M-ERV-OA`` and
``FO-M-ERV-EA`` were added for the two ERV risers that day; the rest of the chase cluster
has no floor opening at all, and nothing in the engine grades a riser against a floor
member. A deck is the one place where a run's own geometry says "there is a hole here" and
the model can be silent about it — a horizontal run at least has
``mep.run_member_crossing`` to answer to.

**Three ways a riser is already answered for, and all three are read off the model:**

* a ``deck_void`` contains it — a stair well, or the cut a through-wall made. There is no
  deck there to go through;
* a ``chase`` contains it (``FloorOpening(purpose=CHASE)``): a shaft a trade is meant to
  use, recognised by what it is rather than by what it names;
* a ``FloorOpening`` whose ``penetration_for`` names the run. The hole that exists only
  because this pipe goes through it, and the strongest statement the model has.

**A sloped leg is graded too** (``_sloped_footprint``): clipped to the deck sheet, it cuts a
hole ``D/sin(theta) + t/tan(theta)`` long by ``D`` wide, which the same three answers and the
same bands read. A leg that starts at the sheet's underside has no member below it to cut.

**What is left is graded in three bands.** A riser landing on a joist, trimmer or rim
**FAILs** naming the member and the station: that member is cut and nothing headed it. A
riser clear of every member but wider than ``max_undrawn_deck_hole_in`` also **FAILs** —
"framed, not drilled" — because a 4" duct is not hole-sawed through a deck on the day, it is
drawn. A riser clear of every member and narrower than that **PASSes**, printing its
clearance: the hole cuts the subfloor sheet only, and the allowance is the house's own trade
argument for that sheet.

**A stub is graded when it crosses the whole sheet.** A vertical spanning less than
``MIN_SPAN_FRACTION`` of the band is skipped unless it runs from below the sheet's underside
to above its top (a tub's drop) — it still cuts the sheet, and may land on a member.

**``Severity.WARN``, not ERROR, and the distinction is deliberate.** Every other reading in
this family is of something DRAWN wrong; this one is mostly of something **not drawn yet**,
and a missing floor opening over an otherwise sound riser should not carry a pipe-through-a-
beam's weight. ``permit.py``'s gate keys off ERROR severity alone, so this does not shut
``haus print`` — but ``CheckReport.counts()`` counts any ``Result.FAIL`` regardless of
severity, and ``haus check`` exits 1 on one, so it is still red and still in the score.

``Tier.STRUCTURAL`` and no ``PermitItemSpec``: IRC R502.8 governs what may be cut out of a
joist and ``mep.run_member_crossing`` cites it, but "draw the hole" is a drawing-set rule,
not a code section.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory as _advisory
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.mep._format import feet_inches
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_IN

_CID = "mep.riser_through_deck"

#: A riser has to span at least this much of a deck's band before it is going through it. A
#: run whose top stops an inch into the sheet is a stub, and a stub is a different question.
MIN_SPAN_FRACTION = 0.5

#: Breadth for a member whose profile the section reader cannot parse — solid-sawn 2x, the
#: narrowest a floor is ever framed in, so an unparsed profile errs toward a QUIETER check
#: rather than a confident false hit. Same number and same direction as
#: ``mep_queries._JOIST_BREADTH_FALLBACK_M``.
_FALLBACK_BREADTH_M = 0.0381

#: A leg rising less than this is level for this check (a drain's fall, a duct's pitch).
_MIN_SLOPE_DZ_M = 0.5 * M_PER_IN


@check(Tier.STRUCTURAL, _CID)
def riser_through_deck(ctx: CheckContext) -> list[Finding]:
    """Every vertical segment against every deck band it passes through."""
    from shapely.geometry import Point, Polygon

    from typehaus.resolve.mep_envelopes import (
        insulation_thickness_m,
        run_polylines,
        run_sections,
    )

    decks = [floor for floor in ctx.model.floors if floor.deck_outline]
    if not decks:
        return [_na(_CID, "no floor in this model resolves a deck, so no riser can pass "
                          "through one", ())]

    sections = run_sections(ctx.model)
    rules = ctx.preferences.mep
    limit_m = rules.max_undrawn_deck_hole_in * M_PER_IN
    out: list[Finding] = []
    seen: set[tuple[str, str]] = set()

    for _kind, tag, path, z in run_polylines(ctx.model):
        if len(path) < 2 or len(z) != len(path):
            continue
        half_w, _half_d, insulation = sections.get(tag, (0.0, 0.0, None))
        radius = half_w + (insulation_thickness_m(insulation) or 0.0)
        for leg in range(len(path) - 1):
            low, high = sorted((z[leg], z[leg + 1]))
            vertical = path[leg] == path[leg + 1]
            if not vertical and high - low < _MIN_SLOPE_DZ_M:
                continue  # level: run_member_crossing's
            for deck in decks:
                if (tag, deck.tag) in seen:
                    continue
                if vertical:
                    station = Point(path[leg])
                    band_low = min(deck.deck_bottom_at(*path[leg][:2]), _members_low(deck))
                    band_high = deck.deck_top_at(*path[leg][:2])  # on a tilted deck
                    depth = band_high - band_low
                    if depth <= 0:
                        continue
                    overlap = min(high, band_high) - max(low, band_low)
                    through_sheet = (low <= deck.deck_bottom_at(*path[leg][:2])
                                     and high >= band_high)
                    if overlap < depth * MIN_SPAN_FRACTION and not through_sheet:
                        continue
                    footprint = station
                    in_cavity = high < deck.deck_bottom_at(*path[leg][:2]) - 1e-6
                else:
                    footprint = _sloped_footprint(deck, path[leg], path[leg + 1],
                                                  z[leg], z[leg + 1], 2 * radius)
                    if footprint is None:
                        continue
                    station = footprint.centroid
                    in_cavity = False
                if not Polygon(deck.deck_outline).contains(station):
                    continue
                if _is_authorised(deck, tag, footprint, Polygon):
                    continue
                seen.add((tag, deck.tag))
                # A leg that starts at the sheet's underside has nothing below it to cut.
                below = vertical or min(z[leg], z[leg + 1]) < deck.deck_bottom_at(
                    *station.coords[0])
                out.append(_verdict(rules, deck, tag, station, footprint, below, radius,
                                    limit_m, in_cavity))

    if not out:
        out.append(_pass(_CID, f"every riser through the {len(decks)} decks in this model "
                               "stands in a void, a chase or a hole framed for it", ()))
    return out


def _members_low(deck) -> float:
    """The underside of the deck's framing — the bottom of the band a riser goes through."""
    placed = [m.z0_m for m in deck.members if m.z0_m is not None]
    return min(placed) if placed else deck.deck_z0_m


def _sloped_footprint(deck, p0, p1, z0: float, z1: float, diameter: float):
    """The plan hole a sloped leg cuts in the deck sheet, or ``None`` if it misses it.

    The leg is clipped to ``[deck_bottom_at, deck_top_at]``; the cut is ``D / sin(theta) +
    t / tan(theta)`` long (along the leg) by ``D`` wide, centred on the crossing's midpoint
    and trimmed to the leg's own extent.
    """
    import math

    from shapely.geometry import LineString, Polygon

    dz = z1 - z0
    run = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    xy = p0
    for _ in range(2):  # the plane may tilt: re-read the sheet where the leg meets it
        bottom, top = deck.deck_bottom_at(*xy[:2]), deck.deck_top_at(*xy[:2])
        t_enter, t_exit = sorted(((bottom - z0) / dz, (top - z0) / dz))
        t_lo, t_hi = max(t_enter, 0.0), min(t_exit, 1.0)
        if t_hi <= t_lo:
            return None
        mid = (t_lo + t_hi) / 2
        xy = (p0[0] + (p1[0] - p0[0]) * mid, p0[1] + (p1[1] - p0[1]) * mid)
    if top - bottom <= 0:
        return None
    theta = math.atan2(abs(dz), run)
    length = diameter / math.sin(theta) + (top - bottom) / math.tan(theta)
    ux, uy = ((p1[0] - p0[0]) / run, (p1[1] - p0[1]) / run) if run else (1.0, 0.0)
    hl, hw = length / 2, diameter / 2
    cut = Polygon([(xy[0] + ux * a - uy * b, xy[1] + uy * a + ux * b)
                   for a, b in ((-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw))])
    # The leg exists only between its own joints: past them the neighbouring leg is graded.
    cut = cut.intersection(LineString((p0, p1)).buffer(hw, cap_style=2))
    return cut if cut.geom_type == "Polygon" and not cut.is_empty else None


def _is_authorised(deck, tag: str, station, Polygon) -> bool:
    """Whether a hole the model already draws contains this riser (a point) or sloped
    footprint (a polygon) — see the module note."""
    for ring in deck.deck_voids:
        if len(ring) >= 3 and Polygon(ring).contains(station):
            return True
    for _chase_tag, ring in deck.chases:
        if len(ring) >= 3 and Polygon(ring).contains(station):
            return True
    for _opening_tag, ring, names in getattr(deck, "penetrations", ()):
        if tag in names and len(ring) >= 3 and Polygon(ring).contains(station):
            return True
    return False


def _verdict(rules, deck, tag: str, station, footprint, below: bool, radius: float,
             limit_m: float, in_cavity: bool = False) -> Finding:
    """One riser, one deck: on a member, too big to drill, or a hole saw through the sheet.

    ``in_cavity``: the riser rises from below and stops under the sheet, so clear of the
    members it cuts the ceiling, not the deck."""
    hole = station.buffer(radius) if footprint.geom_type == "Point" else footprint
    for member in deck.members if below else ():
        rect = _member_rect(member)
        if rect is None or not rect.intersects(hole):
            continue
        return _advisory(
            _CID,
            f"{tag} stands through {deck.tag} on {member.category} {member.child_key} at "
            f"({feet_inches(station.x)}, {feet_inches(station.y)}): a "
            f"{2 * radius / M_PER_IN:.2f}\" riser lands on the member, and no floor opening, "
            "chase or deck void contains it — so the member is cut and nothing headed it",
            (tag, deck.tag), Result.FAIL,
            fix=f"author a FloorOpening on {deck.tag} whose penetration_for names {tag} "
                "(the trimmers and header then resolve with it), or move the riser into a "
                "clear bay")

    if in_cavity:
        return _pass(
            _CID,
            f"{tag} rises into {deck.tag}'s framing at ({feet_inches(station.x)}, "
            f"{feet_inches(station.y)}) clear of every member and stops under the sheet: it "
            "cuts the ceiling below, not the deck", (tag, deck.tag))
    if 2 * radius >= limit_m:
        return _advisory(
            _CID,
            f"{tag} stands through {deck.tag} at ({feet_inches(station.x)}, "
            f"{feet_inches(station.y)}) clear of every member, but it is "
            f"{2 * radius / M_PER_IN:.2f}\" across and this house's undrawn hole allowance "
            f"is {rules.max_undrawn_deck_hole_in:.3g}\". A hole that size is FRAMED, "
            "NOT DRILLED: it wants a drawing, not an installer's decision on the day",
            (tag, deck.tag), Result.FAIL,
            fix=f"author a FloorOpening on {deck.tag} whose penetration_for names {tag}, or "
                "raise [mep] max_undrawn_deck_hole_in with the trade argument beside it")

    rects = [r for m in (deck.members if below else ()) if (r := _member_rect(m)) is not None]
    clear = (f"{min(r.distance(hole) for r in rects) / M_PER_IN:.2f}\" clear of the nearest "
             "member" if rects else "clear of every member")
    return _pass(
        _CID,
        f"{tag} stands through {deck.tag} at ({feet_inches(station.x)}, "
        f"{feet_inches(station.y)}) {clear}, {2 * radius / M_PER_IN:.2f}\" across, under "
        f"the {rules.max_undrawn_deck_hole_in:.3g}\" a trade hole-saws through the sheet",
        (tag, deck.tag))


def _member_rect(member):
    """A member's plan footprint: its ``p0 -> p1`` axis buffered by half its breadth.

    A ``FramedMember`` is a segment and a profile, not a rectangle — the same reading
    ``resolve/mep_queries.clear_bay_width_m`` takes, and for the same reason: two readers
    of one member's width that disagree are two answers to "is this hole on the joist".
    """
    from shapely.geometry import LineString

    from typehaus.resolve.framing.profiles import cross_section

    if member.p0 == member.p1:
        return None  # a stud is not something a deck riser lands ON
    section = cross_section(member.profile)
    breadth = getattr(section, "width_m", None) or _FALLBACK_BREADTH_M
    return LineString((member.p0, member.p1)).buffer(breadth / 2.0, cap_style=2)
