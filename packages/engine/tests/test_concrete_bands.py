"""``concrete_crossings`` walks a solid band by band, not as one prism.

``mep.sleeve_coverage`` is the pour-day check: an unsleeved crossing cures and gets cored.
It read every concrete solid as solid, which is right for a footing and wrong for a
stay-in-place foam deck form. Catlin's retired ``SL-M-DECK`` was 14 3/16" tall and 10" of that is
``eps-deck-form`` — a material a plumber routes a channel in with a hot knife, and the whole
reason an EPS deck is specified. A run lying in that foam was reported as embedded in the
pour, which says the opposite of what is true.
"""

from __future__ import annotations

import pytest
from _helpers import check_context
from _mixed_deck_plan import DECK, mixed_deck_model

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_queries import concrete_bands, concrete_crossings


def _solid(model, tag):
    return next(s for s in model.solids if s.tag == tag)


def test_the_eps_deck_resolves_one_concrete_band_not_its_whole_depth() -> None:
    """A 4 3/16" cast cover over a 10" foam form (``_mixed_deck_plan``, catlin's retired
    ``DECK_EPS_INT``). Only the cover is concrete, and it is the top of the section."""
    model = mixed_deck_model()
    deck = _solid(model, DECK)
    bands = concrete_bands(model, deck)
    assert len(bands) == 1
    (low, high), = bands
    assert high == pytest.approx(deck.z1_m)
    assert (high - low) / M_PER_IN == pytest.approx(4.1875, abs=1e-6)
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


def _drained_deck_model():
    """Catlin's retired kitchen drain in miniature: a drop through the cap at its cast
    sleeve, 5' lying in the foam, and out through the soffit."""
    from _mixed_deck_plan import drain, resolved_with

    from typehaus.model import SleevePenetration, ft, inch, pt

    run = drain("PRDRAIN0e1", "PR-DRAIN", ((9, 20), (9, 20), (9, 25), (9, 25), (9, 27)),
                (113, 100, 99.5, 90, 89.5))
    sleeve = SleevePenetration(uid="SPDRAIN0e1", tag="SP-DRAIN", host_ref=DECK,
                               position=pt(ft(9), ft(20)), pipe_diameter=inch(2),
                               sleeve_diameter=inch(3))
    return resolved_with(basement=(run,), main=(sleeve,))


def test_a_drop_through_the_cap_is_a_crossing_and_the_leg_in_the_foam_is_not() -> None:
    """The half that must NOT change: the drop through the cast cap is a real crossing with
    a real cast-in sleeve. Only the leg lying in the foam beyond it stopped being one, and
    leaving through the foam's soffit crosses no concrete at all."""
    from typehaus.checks.mep.run_in_slab import run_in_slab

    model = _drained_deck_model()
    crossings = [c for c in concrete_crossings(model) if c["run"] == "PR-DRAIN"]
    assert [(c["host"], c["sleeve"]) for c in crossings] == [(DECK, "SP-DRAIN")]
    assert crossings[0]["point"] == pytest.approx((9 * 0.3048, 20 * 0.3048))
    fails = [f for f in run_in_slab(check_context(model=model))
             if f.result is Result.FAIL and "PR-DRAIN" in f.element_tags]
    assert not fails, [f.message for f in fails]


def test_catlin_has_no_unsleeved_concrete_crossing(catlin_model_ro) -> None:
    """The gate this whole pass exists for."""
    findings = [f for f in run_from_model(catlin_model_ro, [], tier=Tier.CODE,
                                          only="mep.sleeve_coverage").findings
                if f.check_id == "mep.sleeve_coverage" and f.result is Result.FAIL]
    assert not findings, [f.message for f in findings]
