"""``structural.bearing_block_seat``: a beam's bearing stud over a 2x6 box stands on a cheek."""

from __future__ import annotations

import dataclasses
from types import SimpleNamespace

from typehaus.checks.structural.bearing_block_seat import bearing_block_seat
from typehaus.findings import Result


def _ctx(model, floors):
    return SimpleNamespace(model=SimpleNamespace(floors=floors, walls=model.walls,
                                                 solids=model.solids))


def test_w_m_c5s_end_stud_stands_on_the_cheek_under_bm_m_hall(catlin_model_ro) -> None:
    findings = bearing_block_seat(_ctx(catlin_model_ro, catlin_model_ro.floors))
    assert [f.result for f in findings] == [Result.PASS]
    assert "W-M-C5 stud-000" in findings[0].message


def test_the_same_stud_fails_once_the_box_has_no_cheek(catlin_model_ro) -> None:
    floors = [dataclasses.replace(f, members=tuple(
        m for m in f.members if "-cheek-" not in m.child_key)) if f.tag == "FS-M-NE" else f
        for f in catlin_model_ro.floors]
    fails = [f for f in bearing_block_seat(_ctx(catlin_model_ro, floors))
             if f.result is Result.FAIL]
    assert [f.element_tags for f in fails] == [("FS-M-NE", "W-M-C5", "BM-M-HALL")]
