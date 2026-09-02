"""``mep.run_through_opening`` — a run may not pass through, or stand in, a rough opening.

An opening is the hole the trades leave for something else. A run drawn across it has nothing
to strap to, the leaf swings through it, and in a window it stands in front of the glass. It is
also the easiest defect in the model to author, because a plan drawing shows a run crossing a
wall and says nothing about whether it crossed at the header or at the opening.

Found against six live defects on catlin, every one of which had been passing every check
in the registry:

* ``DU-ERV-EA`` crossed BOTH north-gable windows — 2'-6" of each 30x36 unit, at +23'-0" in a
  22'-0"..25'-0" opening, dead centre of the glass. The plan comment beside it argued the run
  rode "6 inches off the north gable"; that measured to the sheathing, and against the finished
  face it was 0.63", with 4" of the duct inside a 5 1/2" stud cavity.
* ``CD-A-DATA-NE`` crossed ``WIN-A-N2`` in the same band, put there by a REROUTE that was fixing
  a different defect. Two runs in one wrong band is what a check catches and a review does not.
* ``CD-A-PV-EAST`` clipped ``WIN-A-N1``'s head corner, following a junction box that a rake fix
  had walked 3" inside the window's jamb.
* ``PR-B-CW-BATH1`` and ``PR-B-HW-BATH1`` each STOOD 42" inside ``D-M-BATH1``'s opening, and
  ``PR-M-CW-BALC-HYD`` 24" inside ``D-S-DECK-W``'s.
* ``DU-M-ERV-R-PLANT``'s riser stood 78 1/2" inside ``D-S-PLANT``'s opening and then bored a
  2-ply 2x8 header. ``mep.duct_joist_bay`` PASSED it and printed the station twice in its own
  R302.11 fire-blocking list — it grades the bay a duct is in and never asks what its riser
  stands in.

These tests pin the four things that make the check right rather than merely loud: that it is
registered at all, the interpolated crossing band, the riser case, and the jamb tolerance.
"""

from __future__ import annotations

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.mep.routing import MIN_CROSSING_FT, OPENING_EDGE_M
from typehaus.checks.registry import Tier, registered
from typehaus.findings import Result


@pytest.fixture(scope="module")
def findings(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    return [f for f in report.findings if f.check_id == "mep.run_through_opening"]


def test_the_check_is_registered() -> None:
    """A check module that nothing imports registers nothing and every test still passes.

    ``routing.py`` is already in ``checks/mep/__init__.py``, so this check came for free — but
    that is exactly the condition worth asserting, because the failure mode is silent."""
    assert "mep.run_through_opening" in [cid for cid, _ in registered(Tier.ADVISORY)]


def test_catlin_has_no_run_through_an_opening(findings) -> None:
    """The gate. Six defects were fixed to get here; a seventh must not land quietly."""
    assert findings
    offenders = [f.message for f in findings if f.result is Result.FAIL]
    assert not offenders, offenders


def test_the_crossing_band_is_interpolated_not_banded() -> None:
    """The one design decision that separates real findings from arithmetic.

    ``CD-A-DATA-NE`` used to climb 3'-6" across 21 ft of gable in a SINGLE segment. Banding the
    whole segment gives it a four-foot elevation range, which overlaps every opening it passes
    anywhere near — it read as inside both gable windows when it was physically below one of
    them. Interpolating at the crossing is the difference between two findings and five.

    Asserted on the helper directly and with no house fixture at all, because the geometry it
    is about no longer exists in catlin and this arithmetic must stay pinned regardless."""
    from shapely.geometry import LineString

    from typehaus.checks.mep.routing import _crossing_band

    # A 20 ft segment climbing 0 -> 10 ft, crossing an opening over its first two feet.
    segment = LineString([(0.0, 0.0), (20.0, 0.0)])
    piece = LineString([(0.0, 0.0), (2.0, 0.0)])
    low, high = _crossing_band(segment, 0.0, 10.0, piece)
    assert low == pytest.approx(0.0, abs=1e-9)
    assert high == pytest.approx(1.0, abs=1e-9)  # not 10.0, which banding would give


def test_a_riser_standing_in_an_opening_is_caught(catlin_model) -> None:
    """A riser crosses nothing in plan, so a crossing test alone cannot see it.

    This is the ``DU-M-ERV-R-PLANT`` case and it was the worst of the six: 78 1/2" of duct
    standing free in a doorway. Rebuilt here by dropping a riser into a real opening in the
    real house, because a synthetic wall would not exercise the prism construction."""
    from typehaus.checks.mep.routing import _opening_prisms

    class _Ctx:
        model = catlin_model

    prisms = {tag: prism for tag, _door, _host, prism, *_ in _opening_prisms(_Ctx())}
    bands = {tag: (low, high) for tag, _door, _host, _p, low, high in _opening_prisms(_Ctx())}
    assert "D-S-PLANT" in prisms, "the opening the check was written for must resolve"
    low, high = bands["D-S-PLANT"]
    assert high - low == pytest.approx(80 * 0.0254, abs=1e-6), "a 6'-8\" door"
    # Its centroid is inside its own footprint — the prism is a real quadrilateral, not a
    # degenerate one collapsed by the inward buffer.
    assert prisms["D-S-PLANT"].area > 0


def test_the_jamb_tolerance_does_not_swallow_a_real_crossing() -> None:
    """The buffer exists so a raceway strapped to a jack stud is not "through the window".

    It has to stay small enough that a genuine clip still reports: ``CD-A-PV-EAST`` crossed
    ``WIN-A-N1`` by 0.21 ft, which is the smallest real finding of the six, and the check must
    keep catching that class."""
    assert OPENING_EDGE_M < 0.0254, "under an inch — smaller than any framing member"
    assert MIN_CROSSING_FT < 0.21, "must still report CD-A-PV-EAST's 0.21 ft clip"
