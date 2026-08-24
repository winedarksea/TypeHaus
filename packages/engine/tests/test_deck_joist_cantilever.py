"""A cantilever is not span — ``structural.deck_joist_span`` / ``deck_joist_cantilever``.

Both deck tables this module reads are SPAN tables. DCA6 Table 3A gives the joist's
allowable back span and IRC R507.6.1 bounds the overhang separately, at a quarter of it;
IRC Table R507.5(1) is then indexed by the joist span a beam carries. The check used to
measure the whole resolved member instead, which folded the overhang into the span and
rounded the beam table up to a stiffer row than the code asks for.

On catlin that cost three FAILs: the balcony joists span 10'-0" beam to beam and overhang
the outer beams 6", the check read 10'-6", and 10'-6" rounds to the 12' row, where nothing
built-up out of sawn lumber reaches the beams' 8'-8" span. At the real 10' row a 3-2x12
reaches 9'-2" and the beams pass on their merits.

These tests pin both halves: the span excludes the overhang, and the overhang is still
bounded — because subtracting it from one check without bounding it in another would be a
loosening, not a fix.
"""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.checks.structural.deck import deck_joist_cantilever, deck_joist_span
from typehaus.findings import Result
from typehaus.model.floors import FloorSystem, JoistSpec
from typehaus.quantities import Point2D, ft, inch

_M_PER_FT = 0.3048


def _deck(**joist_kwargs) -> FloorSystem:
    ring = (Point2D(x=ft(0), y=ft(0)), Point2D(x=ft(21), y=ft(0)),
            Point2D(x=ft(21), y=ft(9)), Point2D(x=ft(0), y=ft(9)))
    return FloorSystem(
        uid="TSTFS02AAA", tag="FS-T-DECK",
        joists=JoistSpec(member="2x8", spacing=inch(16), direction="x", **joist_kwargs),
        outline=ring, service="deck",
    )


def _joist(x0_ft: float, x1_ft: float) -> SimpleNamespace:
    """One resolved member running along x, the way ``resolve/floors.py`` emits them."""
    return SimpleNamespace(category="joist", p0=(x0_ft * _M_PER_FT, 0.0),
                           p1=(x1_ft * _M_PER_FT, 0.0),
                           length_m=abs(x1_ft - x0_ft) * _M_PER_FT)


def _ctx(deck: FloorSystem, members: list[SimpleNamespace]) -> SimpleNamespace:
    resolved = SimpleNamespace(tag=deck.tag, members=members)
    return SimpleNamespace(
        plan=SimpleNamespace(all_elements=lambda: [deck], by_tag=lambda tag: None),
        model=SimpleNamespace(walls=[], floors=[resolved], solids=[]),
    )


def _one(findings) -> object:
    assert len(findings) == 1, findings
    return findings[0]


# The catlin balcony, to scale: bearing lines at 0.5/10.5/20.5, joists overhanging each
# outer line by 6" out to the deck edges at 0 and 21.
_BALCONY = [_joist(0.0, 10.5), _joist(10.5, 21.0)]


def test_the_overhang_does_not_count_as_span():
    deck = _deck(cantilever=inch(6), bearing_refs=("BM-A", "BM-B", "BM-C"))
    finding = _one(deck_joist_span(_ctx(deck, _BALCONY)))
    assert finding.result is Result.PASS
    # 10.00', not the 10.50' member. The distinction is the whole point: 10.50' rounds the
    # beam table up to its 12' row and 10.00' lands on the 10' row.
    assert "span 10.00'" in finding.message


def test_a_flush_deck_is_measured_exactly_as_before():
    """No authored cantilever, no subtraction — the fix must not move a flush deck."""
    deck = _deck(bearing_refs=("BM-A", "BM-B"))
    finding = _one(deck_joist_span(_ctx(deck, [_joist(0.0, 10.5)])))
    assert "span 10.50'" in finding.message


def test_a_per_end_override_is_read_at_the_end_it_belongs_to():
    """The porch's shape: flush in the front beams, overhanging at the back. Only the
    high-end member loses its overhang, and the low-end one keeps its full length."""
    deck = _deck(cantilever=inch(0), cantilever_end=inch(24),
                 bearing_refs=("BM-A", "BM-B", "BM-C"))
    finding = _one(deck_joist_span(_ctx(deck, [_joist(0.0, 10.0), _joist(10.0, 22.0)])))
    # The high member is 12.0' with a 2' overhang -> 10.0'; the low one is a flush 10.0'.
    assert "span 10.00'" in finding.message


def test_an_interior_bay_never_loses_a_cantilever():
    """Three bays: only the outer two touch the field's extent, so the middle member is
    reported at its full length even though the deck authors an overhang."""
    deck = _deck(cantilever=inch(6), bearing_refs=("BM-A", "BM-B", "BM-C", "BM-D"))
    members = [_joist(0.0, 8.5), _joist(8.5, 20.5), _joist(20.5, 29.0)]
    finding = _one(deck_joist_span(_ctx(deck, members)))
    assert "span 12.00'" in finding.message  # the interior bay, untouched


def test_the_overhang_is_still_bounded_somewhere():
    """R507.6.1: a quarter of the back span. Without this the subtraction above would let
    an arbitrarily long overhang vanish out of every deck check in the tier."""
    deck = _deck(cantilever=inch(6), bearing_refs=("BM-A", "BM-B", "BM-C"))
    finding = _one(deck_joist_cantilever(_ctx(deck, _BALCONY)))
    assert finding.result is Result.PASS
    assert "cantilever 0.50'" in finding.message and "2.50' IRC R507.6.1" in finding.message


def test_an_overlong_overhang_fails_r507_6_1():
    """Also the single-bay case, where one member carries BOTH overhangs: the symmetric
    4' scalar comes off each end of the 14' member, leaving a 6' back span."""
    deck = _deck(cantilever=ft(4), bearing_refs=("BM-A", "BM-B"))
    finding = _one(deck_joist_cantilever(_ctx(deck, [_joist(0.0, 14.0)])))
    assert finding.result is Result.FAIL
    assert "cantilever 4.00'" in finding.message
    assert "1.50' IRC R507.6.1" in finding.message and "6.00' back span" in finding.message


def test_a_flush_deck_raises_no_cantilever_finding_at_all():
    """Nothing to bound is not an UNKNOWN — most decks have no overhang and should not
    each contribute a finding to the report."""
    deck = _deck(bearing_refs=("BM-A", "BM-B"))
    assert deck_joist_cantilever(_ctx(deck, [_joist(0.0, 10.0)])) == []
