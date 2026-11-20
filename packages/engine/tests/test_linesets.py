"""Catlin's five linesets against the hand oracle (notes/heat_pump_ground_pad.md, "Line sets").

Developed lengths, kits, field charge and the MUL30 total are the note's hand arithmetic,
worked vertex by vertex off plan/mep_linesets.py.
"""

from __future__ import annotations

import pytest

_FT = 0.3048
_IN = 0.0254

#: tag -> (developed ft, kit ft), the note's table.
ORACLE = {
    "PR-A-RFG-HP1": (39.88, 50),
    "PR-B-RFG-HP2-GYM": (19.27, 25),
    "PR-M-RFG-HP2-BED": (27.00, 35),
    "PR-M-RFG-HP2-LIVING": (24.82, 35),
    "PR-M-RFG-HP3-STAIR": (29.83, 35),
}


def test_catlin_linesets_match_the_hand_oracle(catlin_model_ro) -> None:
    sets = {item.tag: item for item in catlin_model_ro.linesets}
    assert set(sets) == set(ORACLE)
    for tag, (developed_ft, kit_ft) in ORACLE.items():
        item = sets[tag]
        assert item.developed_m / _FT == pytest.approx(developed_ft, abs=0.1), tag
        assert item.kit_m / _FT == pytest.approx(kit_ft), tag
    # FXU24: 31 ft precharged, 0.323 oz/ft beyond it.
    assert sets["PR-A-RFG-HP1"].field_charge_oz == pytest.approx((39.88 - 31) * 0.323, abs=0.05)
    hp2 = [item for item in sets.values() if item.outdoor_tag == "EQ-M-HP2-OD"]
    assert sum(item.developed_m for item in hp2) / _FT == pytest.approx(71.09, abs=0.2)
    assert all(item.field_charge_oz == 0.0 for item in hp2)  # inside the 131 ft precharge
    # The bundle: two lagged tubes side by side, 1.75 + 1.375 in.
    hp1_run = next(run for run in catlin_model_ro.pipe_runs if run.tag == "PR-A-RFG-HP1")
    assert hp1_run.bundle_diameter_m / _IN == pytest.approx(3.125, abs=1e-3)
