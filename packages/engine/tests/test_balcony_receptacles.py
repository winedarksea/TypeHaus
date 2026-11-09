"""NEC 210.52(E)(3): the porch and the balcony each have a receptacle on the deck."""

from __future__ import annotations

from _helpers import check_context

from typehaus.checks.mep.electrical_outdoor import balcony_deck_porch_receptacles
from typehaus.findings import Result


def test_catlin_porch_and_balcony_are_each_served(catlin_model):
    findings = balcony_deck_porch_receptacles(check_context(model=catlin_model))
    assert [f.result for f in findings] == [Result.PASS, Result.PASS]
    text = " ".join(f.message for f in findings)
    assert "FS-SG-BALCONY" in text and "ED-S-BALCONY-RC1" in text
    assert "FS-SG-PORCH" in text and "ED-M-REAR-RC1" in text
