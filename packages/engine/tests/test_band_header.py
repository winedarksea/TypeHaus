"""``band_header/D-B-SUNKEN`` against ``houses/catlin/notes/sunken_door_band_header.md`` (§2-§3)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from typehaus.engineering.item import Status
from typehaus.resolve.band_headers import band_header_findings

_IN = 0.0254
#: §3: name -> (demand, capacity).
_ROWS = {"bending": (189.9, 17849.0), "shear": (131.5, 7897.0),
         "deflection": (0.00099, 0.1925)}


def test_the_record_reproduces_the_note(catlin_ctx) -> None:
    record = catlin_ctx.engineering["band_header/D-B-SUNKEN"]
    assert record.status is Status.OK, record.summary
    states = {s.name: s for s in record.limit_states}
    for name, (demand, capacity) in _ROWS.items():
        assert states[name].demand == pytest.approx(demand, rel=5e-3), name
        assert states[name].capacity == pytest.approx(capacity, rel=1e-3), name
    values = {q.name: q.value for q in record.inputs}
    assert values["tributary"] == pytest.approx(8 / 12, abs=1e-6)
    assert (values["seat_lo"], values["seat_hi"]) == pytest.approx((6.0, 6.0))
    # §2: D-M-PORCH's packs stand on the seats, so nothing lands in the span.
    assert values["loads_inside_span"] == 0
    assert "W-M-S2:king-0-l1" in record.notes[0]


def test_the_wall_frames_no_header_and_an_empty_band_is_an_error(catlin_model) -> None:
    wall = catlin_model.wall("W-B-S3-FR")
    assert not [m for m in wall.members if m.category == "header"]
    [nailer] = [m for m in wall.members if m.child_key.startswith("headnailer")]
    assert nailer.z1_m - nailer.z0_m == pytest.approx(1.5 * _IN)
    plate = min(m.z0_m for m in wall.members if m.child_key.startswith("plate-top"))
    assert all(m.z1_m == pytest.approx(plate) for m in wall.members if m.category == "jack")
    assert band_header_findings(catlin_model) == []
    index, floor = next((i, f) for i, f in enumerate(catlin_model.floors)
                        if f.tag == "FS-M-EAST")
    catlin_model.floors[index] = replace(floor, members=tuple(
        m for m in floor.members if m.category != "sister_joist"))
    [finding] = band_header_findings(catlin_model)
    assert finding.check_id == "integrity.header_in_band"
