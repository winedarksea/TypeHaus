"""``concrete_crossings`` walks a solid band by band, not as one prism.

``mep.sleeve_coverage`` is the pour-day check: an unsleeved crossing cures and gets cored.
It read every concrete solid as solid, which is right for a footing and wrong for a
stay-in-place foam deck form. ``SL-M-DECK`` is 14 3/8" tall and 10" of that is
``eps-deck-form`` — a material a plumber routes a channel in with a hot knife, and the whole
reason an EPS deck is specified. A run lying in that foam was reported as embedded in the
pour, which says the opposite of what is true.
"""

from __future__ import annotations

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_queries import concrete_bands, concrete_crossings


def _solid(model, tag):
    return next(s for s in model.solids if s.tag == tag)


def test_the_eps_deck_resolves_one_concrete_band_not_its_whole_depth(
        catlin_model_ro) -> None:
    """``DECK_EPS_INT`` is a 4 3/8" cast cover over a 10" foam beam. Only the cover is
    concrete, and it is the top of the section."""
    deck = _solid(catlin_model_ro, "SL-M-DECK")
    bands = concrete_bands(catlin_model_ro, deck)
    assert len(bands) == 1
    (low, high), = bands
    assert high == pytest.approx(deck.z1_m)
    assert (high - low) / M_PER_IN == pytest.approx(4.375, abs=1e-6)
    # And the foam below it is genuinely most of the section.
    assert (low - deck.z0_m) / M_PER_IN == pytest.approx(10.0, abs=1e-6)


def test_a_plain_slab_falls_back_to_its_whole_prism(catlin_model_ro) -> None:
    """The conservative reading, and the one every ordinary pour keeps. ``SL-B-FLOOR`` is a
    slab on grade with no foam in its section, so nothing about it changes."""
    slab = _solid(catlin_model_ro, "SL-B-FLOOR")
    assert concrete_bands(catlin_model_ro, slab) == [(slab.z0_m, slab.z1_m)]


def test_every_footing_keeps_its_whole_depth(catlin_model_ro) -> None:
    """The trap this function nearly walked into. Catlin's footings resolve about 1/4"
    taller than the assembly that describes them, so a naive top-down walk leaves the
    bottom of every footing outside its own concrete band — and a crossing down there stops
    being reported. The remainder is attributed to concrete, and a section with under
    ``_MIN_NON_CONCRETE_M`` of anything else is not split at all."""
    footings = [s for s in catlin_model_ro.solids if s.category == "footing"]
    assert footings
    for footing in footings:
        assert concrete_bands(catlin_model_ro, footing) == [(footing.z0_m, footing.z1_m)]


def test_the_kitchen_drain_still_crosses_the_cap_through_its_sleeve(
        catlin_model_ro) -> None:
    """The half that must NOT change. ``PR-B-KITCH-DRAIN`` drops from the sink through the
    4 3/8" cast cover, and that is a real crossing with a real cast-in sleeve. Only the
    horizontal leg lying in the foam beyond it stopped being one."""
    crossings = [c for c in concrete_crossings(catlin_model_ro)
                 if c["run"] == "PR-B-KITCH-DRAIN" and c["host"] == "SL-M-DECK"]
    assert len(crossings) == 1, crossings
    assert crossings[0]["sleeve"] == "SP-M-KITCH"


def test_catlin_has_no_unsleeved_concrete_crossing(catlin_model_ro) -> None:
    """The gate this whole pass exists for."""
    findings = [f for f in run_from_model(catlin_model_ro, [], tier=Tier.CODE).findings
                if f.check_id == "mep.sleeve_coverage" and f.result is Result.FAIL]
    assert not findings, [f.message for f in findings]
