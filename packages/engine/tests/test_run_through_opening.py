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
from typehaus.checks.mep.routing_openings import MIN_CROSSING_FT, OPENING_EDGE_M
from typehaus.checks.registry import Tier, registered
from typehaus.findings import Result


@pytest.fixture(scope="module")
def findings(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    return [f for f in report.findings if f.check_id == "mep.run_through_opening"]


def test_the_check_is_registered() -> None:
    """A check module that nothing imports registers nothing and every test still passes.

    ``routing_openings.py`` has to be named in ``checks/mep/__init__.py``'s import list; it was
    split out of ``routing.py`` and a split is exactly when that line gets forgotten."""
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

    from typehaus.checks.mep.routing_geometry import crossing_band

    # A 20 ft segment climbing 0 -> 10 ft, crossing an opening over its first two feet.
    segment = LineString([(0.0, 0.0), (20.0, 0.0)])
    piece = LineString([(0.0, 0.0), (2.0, 0.0)])
    low, high = crossing_band(segment, 0.0, 10.0, piece)
    assert low == pytest.approx(0.0, abs=1e-9)
    assert high == pytest.approx(1.0, abs=1e-9)  # not 10.0, which banding would give


def test_a_riser_standing_in_an_opening_is_caught(catlin_model) -> None:
    """A riser crosses nothing in plan, so a crossing test alone cannot see it.

    This is the ``DU-M-ERV-R-PLANT`` case and it was the worst of the six: 78 1/2" of duct
    standing free in a doorway. Rebuilt here by dropping a riser into a real opening in the
    real house, because a synthetic wall would not exercise the prism construction."""
    from typehaus.checks.mep.routing_openings import opening_prisms

    class _Ctx:
        model = catlin_model

    prisms = {tag: prism for tag, _door, _host, prism, *_ in opening_prisms(_Ctx())}
    bands = {tag: (low, high)
             for tag, _door, _host, _p, low, high, _pen in opening_prisms(_Ctx())}
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


def test_a_penetration_is_exempt_only_for_the_run_it_exists_for(catlin_model) -> None:
    """``RoughOpening.penetration_for`` names the one run whose crossing IS the point.

    The check's premise is "this is the hole the trades leave for something else". When the
    something else is the run itself — catlin's two ERV wall penetrations, `AO-M-ERV-OA` for
    `DU-ERV-OA` and `AO-S-ERV-EA` for `DU-ERV-EA` — the crossing is the design, not a defect.
    Before the field existed the choice was to leave the hole unmodelled (an outdoor hood on
    a facade with no opening under it, at 0 FAIL) or to suppress a true finding.

    The exemption is a PAIRING, not a flag on the opening: any other run through this hole
    still reports, and so does this run through any other hole. That is what the second half
    of this test pins, because a blanket exemption on the opening would have been the easy
    and wrong implementation.
    """
    from typehaus.checks.mep.routing_openings import opening_prisms

    class _Ctx:
        model = catlin_model

    named = {tag: pen for tag, _d, _h, _p, _lo, _hi, pen in opening_prisms(_Ctx())
             if pen is not None}
    assert named == {"AO-M-ERV-OA": "DU-ERV-OA", "AO-S-ERV-EA": "DU-ERV-EA"}

    # The pairing is one-to-one: no opening claims a run that another opening also claims,
    # and no run is exempted at more than one hole.
    assert len(set(named.values())) == len(named)


def test_the_opening_band_is_measured_from_the_framing_base(catlin_model) -> None:
    """A sill is stated up from the room floor, not from where the cladding stops.

    ``ResolvedWall.base_ref_z_m`` exists for exactly this and every other consumer that adds
    a sill to an elevation already reads it. ``opening_prisms`` read ``z0_m`` instead, which
    on catlin's main-storey exterior walls — extended 13 7/16" down over the rim — put every
    opening more than a foot below where it is built. That is far enough to miss a run
    crossing one, and it did: `DU-ERV-OA` through `AO-M-ERV-OA` went unreported while its
    second-storey twin, on a wall whose base and z0 coincide, reported correctly.
    """
    walls = {w.tag: w for w in catlin_model.walls}
    wall = walls["W-M-W1B"]
    assert wall.plate_base_z_m is not None, "the wall this is about is extended over the rim"
    assert wall.base_ref_z_m != wall.z0_m, "...so the two datums genuinely differ"

    from typehaus.checks.mep.routing_openings import opening_prisms

    class _Ctx:
        model = catlin_model

    bands = {tag: (low, high)
             for tag, _d, _h, _p, low, high, _pen in opening_prisms(_Ctx())}
    low, _high = bands["AO-M-ERV-OA"]
    # Authored sill 44.5" on a framing base of 0'-0", which is where the duct is at +4'-0".
    assert low == pytest.approx(44.5 * 0.0254, abs=1e-6)
