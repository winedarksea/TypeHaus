"""The garage's bolted hold-downs (HTT4 on a cast-in SSTB16), against
``houses/catlin/notes/sthd_esr2920.md``, "The garage, 2026-11-20"."""

from __future__ import annotations

import pytest

from typehaus.checks.structural.anchor_rod_hold_down import anchor_rod_hold_down
from typehaus.quantities import M_PER_IN


def test_both_panel_ends_pass_on_the_hand_worked_rows(catlin_ctx) -> None:
    found = {f.element_tags[0]: f for f in anchor_rod_hold_down(catlin_ctx)}
    assert set(found) == {"CN-G-BWHD-SW", "CN-G-BWHD-S-DR"}
    assert all(f.result.value == "pass" for f in found.values())
    sw = found["CN-G-BWHD-SW"].message
    assert "2.00 / 4.00 in to the faces, corner (6.2 in" in sw
    assert "2,580 lb governs" in sw and "ratio 0.310" in sw
    assert "middle (46.3 in" in found["CN-G-BWHD-S-DR"].message


def test_no_strap_is_cast_in_the_garage_core(catlin_model_ro) -> None:
    """No plumb Figure 1 entry in the 6" core, so the house rule places none there."""
    assert not [s.tag for s in catlin_model_ro.embedded_straps
                if s.core_tag.startswith("W-GF-")]
    assert all(s.jog_in == 0.0 for s in catlin_model_ro.embedded_straps)


def test_the_sstb_bar_is_two_le_and_a_corner_return(catlin_model_ro) -> None:
    bars = {b.key: b for rs in catlin_model_ro.rebar for b in rs.bars if "/sstb/" in b.key}
    lengths = sorted(round(b.placed_length_m / M_PER_IN, 2) for b in bars.values())
    assert lengths == pytest.approx([44.5, 50.5])
