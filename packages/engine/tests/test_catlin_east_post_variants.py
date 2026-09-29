"""The canopy's east supports are a SWITCH, and every position of it is a graded 0-FAIL house.

``params/north_entry_frame.py`` carries ``EAST_POST_SYSTEM = "steel" | "kdat" | "cast"``
(owner, 2026-09-29), and the promise the switch makes is that changing the word lands on a
known state rather than a design pass. This module keeps the promise: each variant is
copied to a sandbox, the one line is rewritten, the house is loaded and checked, and the
report must carry **0 FAIL** and the north entry's engineering items must be exactly the set
``notes/canopy_garage_diaphragm.md`` works for that variant.

Slow: three full check runs. ``scripts/verify.sh`` runs it; ``--fast`` skips it.
"""

from __future__ import annotations

import pytest
from _helpers import east_variant_house

pytestmark = pytest.mark.slow

_COMMON = {
    "deck_post/PT-BW-E", "deck_post/PT-BW-GE", "deck_post/PT-BW-GW", "deck_post/PT-BW-W",
    "deck_tie/FS-BW-FLOOR", "lateral_system/RF-BW-CANOPY", "rafter/RF-BW-CANOPY",
    "roof_beam/BM-BW-RE", "roof_beam/BM-BW-RW",
}
_PINNED_PIERS = {"column_base/PT-BW-PE", "column_base/PT-BW-PNE",
                 "deck_post/PT-BW-PE", "deck_post/PT-BW-PNE"}

#: ``variant -> the north entry's engineering items``, per the note's §5-§7.
EXPECTED = {
    "steel": _COMMON | _PINNED_PIERS | {"steel_post/PT-BW-RE", "steel_post/PT-BW-RNE"},
    "kdat": _COMMON | _PINNED_PIERS | {"wood_roof_post/PT-BW-RE", "wood_roof_post/PT-BW-RNE"},
    "cast": _COMMON | {
        "base_rotation/PT-BW-RE", "base_rotation/PT-BW-RNE",
        "column_base/PT-BW-RE", "column_base/PT-BW-RNE",
        "column_head_joint/PT-BW-RE", "column_head_joint/PT-BW-RNE",
        "deck_post/PT-BW-RE", "deck_post/PT-BW-RNE"},
}


def _north_entry(items) -> set[str]:
    return {item for item in items if "-BW-" in item or item.startswith("steel_post/")}


@pytest.fixture(scope="module", params=sorted(EXPECTED))
def variant(request, tmp_path_factory):
    from typehaus.checks.run import build_context, run_checks
    from typehaus.source import load_plan

    name = request.param
    house = east_variant_house(tmp_path_factory.mktemp(f"east-{name}") / "house", name)
    loaded = load_plan(house)
    assert loaded.plan is not None, [f.message for f in loaded.findings]
    ctx, _ = build_context(loaded.plan, house)
    return name, ctx, run_checks(ctx)


def test_the_variant_checks_at_zero_fail(variant) -> None:
    from typehaus.findings import Result

    name, _ctx, report = variant
    failed = [f"{f.check_id}: {f.message[:160]}" for f in report.findings
              if f.result is Result.FAIL]
    assert not failed, f"EAST_POST_SYSTEM = {name!r}:\n" + "\n".join(failed)


def test_the_variant_has_exactly_its_items(variant) -> None:
    name, ctx, _report = variant
    assert _north_entry(ctx.engineering) == EXPECTED[name]


def test_every_north_entry_item_is_graded(variant) -> None:
    from typehaus.engineering.item import Status

    name, ctx, _report = variant
    for item in sorted(EXPECTED[name] - {"rafter/RF-BW-CANOPY"}):
        record = ctx.engineering[item]
        assert record.status is Status.OK, f"{name}: {item} is {record.status}: {record.summary}"


def test_the_canopy_delivers_to_the_garage_in_every_variant(variant) -> None:
    name, ctx, _report = variant
    record = ctx.engineering["lateral_system/RF-BW-CANOPY"]
    names = {s.name for s in record.limit_states}
    assert {"joint boundary nailing, along", "W-G-S delivered shear on the surplus",
            "RF-GARAGE unit-shear increment"} <= names, name
