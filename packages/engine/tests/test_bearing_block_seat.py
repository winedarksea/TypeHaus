"""``structural.bearing_block_seat``: a point-load stud over a 2x6 box stands on a cheek."""

from __future__ import annotations

import copy
import dataclasses
from types import SimpleNamespace

from typehaus.checks.structural.bearing_block_seat import bearing_block_seat
from typehaus.findings import Result


def _findings(model, drop_cheeks_of: str | None = None):
    live = copy.copy(model)  # shallow: only this copy's floors list is replaced
    live.floors = [dataclasses.replace(f, members=tuple(
        m for m in f.members if "-cheek-" not in m.child_key)) if f.tag == drop_cheeks_of else f
        for f in model.floors]
    return bearing_block_seat(SimpleNamespace(plan=model.plan, model=live))


def test_w_m_c5s_end_stud_stands_on_the_cheek_under_bm_m_hall(catlin_model_ro) -> None:
    passes = {f.element_tags: f for f in _findings(catlin_model_ro) if f.result is Result.PASS}
    assert "W-M-C5 stud-000" in passes[("FS-M-NE",)].message


def test_the_same_stud_fails_once_the_box_has_no_cheek(catlin_model_ro) -> None:
    fails = [f for f in _findings(catlin_model_ro, "FS-M-NE") if f.result is Result.FAIL]
    assert ("FS-M-NE", "W-M-C5", "BM-M-HALL") in [f.element_tags for f in fails]


def test_a_bearing_walls_header_jack_over_a_box_stands_on_a_cheek(catlin_model_ro) -> None:
    # W-S-C2B (BEARING) carries RF-HOUSE and FS-ATTIC on header-0; DU-M-ERV-R-LIVING runs
    # clear of the jack so FS-S-WEST's and FS-S-EAST's boxes keep a cheek under it.
    findings = _findings(catlin_model_ro)
    assert not [f for f in findings if f.result is Result.FAIL]
    passes = {f.element_tags[0]: f.message for f in findings if f.result is Result.PASS}
    assert "W-S-C2B jack-0-l0" in passes["FS-S-WEST"] and "W-S-C2B jack-0-l0" in passes["FS-S-EAST"]
