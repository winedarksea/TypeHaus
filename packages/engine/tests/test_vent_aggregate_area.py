"""UPC 904.1 aggregate vent area and the VentRun increaser it led to.

Oracle: houses/catlin/notes/vent_aggregate_area.md (50 DFU -> 4" sewer, 12.57 in²).
"""

from __future__ import annotations

import pytest

from typehaus.findings import Result


def _vent(**increaser):
    from typehaus.model.enums import PipeSystem
    from typehaus.model.mep import VentRun
    from typehaus.model.vent_increaser import VentIncreaser
    from typehaus.quantities import ft, inch, pt

    return VentRun(uid="V1", tag="VR-T", systems=(PipeSystem.VENT, PipeSystem.RADON),
                   diameter=inch(3), chase_position=pt(ft(1), ft(1)),
                   start_elevation=ft(0), exit_elevation=ft(20),
                   exit_offset=pt(ft(0), ft(2)),
                   vent_increaser=VentIncreaser(**increaser))


def test_increaser_sizes_only_the_vent_leg_above_its_station():
    from typehaus.model.enums import PipeSystem
    from typehaus.quantities import ft, inch

    vent = _vent(diameter=inch(4), elevation=ft(15))
    assert vent.diameter_of(PipeSystem.VENT, ft(10).meters).inches == pytest.approx(3)
    assert vent.diameter_of(PipeSystem.VENT).inches == pytest.approx(4)
    assert vent.diameter_of(PipeSystem.RADON).inches == pytest.approx(3)
    with pytest.raises(ValueError, match="interior riser"):
        _vent(diameter=inch(4), elevation=ft(21))   # above the exit: outside, subp. 3


def test_catlin_vents_total_the_required_sewer(catlin_ctx, monkeypatch):
    from typehaus.checks.mep import vent_area

    (finding,) = vent_area.vent_aggregate_area(catlin_ctx)
    assert finding.result is Result.PASS and "12.57 in²" in finding.message
    assert "PR-B-MAIN-DRAIN, 50 DFU" in finding.message
    # The 3" stack it replaced: 7.07 in² against 12.57.
    monkeypatch.setattr(vent_area, "terminal_vents", lambda ctx: [("VR-M-STACK", 3.0)])
    (finding,) = vent_area.vent_aggregate_area(catlin_ctx)
    assert finding.result is Result.FAIL and "7.07 in²" in finding.message
