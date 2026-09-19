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

**What is left is graded in three bands, and the middle one is the finding this was written
for.** A riser landing on a joist, trimmer or rim **FAILs** naming the member and the
station: that member is cut and nothing headed it. A riser clear of every member but wider
than ``max_undrawn_deck_hole_in`` also **FAILs** — "framed, not drilled" — because a 4" duct
and a 3" drain are not hole-sawed through a deck on the day, they are drawn. A riser
narrower than that is **UNKNOWN**, quoting ``member_window.basis``: whether a 1 1/4" raceway
may share an I-joist bay at that station is a fabricator's chart this engine does not hold,
and a confident verdict either way would be inventing one.

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
from typehaus.checks._authoring import unknown as _unknown
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


@check(Tier.STRUCTURAL, _CID)
def riser_through_deck(ctx: CheckContext) -> list[Finding]:
    """Every vertical segment against every deck band it passes through."""
    from shapely.geometry import Point, Polygon

    from typehaus.resolve.mep_crossings import member_window
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
            if path[leg] != path[leg + 1]:
                continue  # not a riser: a sloping or level leg is run_member_crossing's
            low, high = sorted((z[leg], z[leg + 1]))
            for deck in decks:
                if (tag, deck.tag) in seen:
                    continue
                band_low = min(deck.deck_z0_m, _members_low(deck))
                band_high = deck.deck_z1_m
                depth = band_high - band_low
                if depth <= 0:
                    continue
                overlap = min(high, band_high) - max(low, band_low)
                if overlap < depth * MIN_SPAN_FRACTION:
                    continue
                station = Point(path[leg])
                if not Polygon(deck.deck_outline).contains(station):
                    continue
                if _is_authorised(deck, tag, station, Polygon):
                    continue
                seen.add((tag, deck.tag))
                out.append(_verdict(rules, deck, tag, station, radius, limit_m,
                                    member_window))

    if not out:
        out.append(_pass(_CID, f"every riser through the {len(decks)} decks in this model "
                               "stands in a void, a chase or a hole framed for it", ()))
    return out


def _members_low(deck) -> float:
    """The underside of the deck's framing — the bottom of the band a riser goes through."""
    placed = [m.z0_m for m in deck.members if m.z0_m is not None]
    return min(placed) if placed else deck.deck_z0_m


def _is_authorised(deck, tag: str, station, Polygon) -> bool:
    """Whether a hole the model already draws contains this riser — see the module note."""
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


def _verdict(rules, deck, tag: str, station, radius: float, limit_m: float,
             member_window) -> Finding:
    """One riser, one deck: on a member, too big to drill, or a fabricator's question."""
    hole = station.buffer(radius)
    for member in deck.members:
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

    window = member_window(deck)
    basis = window.basis if window is not None else "this deck's section publishes no window"
    return _unknown(
        _CID,
        f"{tag} stands through {deck.tag} at ({feet_inches(station.x)}, "
        f"{feet_inches(station.y)}) clear of every member and is "
        f"{2 * radius / M_PER_IN:.2f}\" across, under the "
        f"{rules.max_undrawn_deck_hole_in:.3g}\" a trade drills. Whether it may go "
        f"there is not this engine's to say: {basis}",
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
