"""210.52(I): a foyer over 60 sq ft has a receptacle on each wall space of 3 ft or more."""

from __future__ import annotations

import dataclasses

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier

_CID = "electrical.foyer_receptacle"


def _graded(model, tag: str):
    report = run_from_model(model, [], tier=Tier.CODE, only=_CID)
    return next(f for f in report.findings if f.check_id == _CID and tag in f.message)


def test_small_foyer_is_out_of_scope_and_bare_wall_space_fails(catlin_model):
    # RM-S-HALL read as a foyer: 190 sq ft, and its long east wall carries no receptacle.
    catlin_model.rooms = [dataclasses.replace(r, occupancy="foyer") if r.tag == "RM-S-HALL"
                          else r for r in catlin_model.rooms]
    assert _graded(catlin_model, "RM-M-MUDROOM").result.value == "not_applicable"
    hall = _graded(catlin_model, "RM-S-HALL")
    assert hall.result.value == "fail" and "wall space with no receptacle" in hall.message
