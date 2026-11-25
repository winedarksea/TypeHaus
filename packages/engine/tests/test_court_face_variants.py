"""The court's brick face is a declared variant, and switching back reproduces it exactly.

The default court face is LP panel on ``W-B-S2-FR``/``W-B-S3-FR``; brick (``W-B-BRICK`` on
``W-SG-BRKBM``) is variant ``court-face-brick`` (``variants.toml``). ``FINGERPRINTS`` are
``main``'s fingerprints from before the switch, one per engineering item (``None``: a NO_CALC
record, which has no fingerprint). Brick reproduces them exactly, so it is not a second design
to re-engineer, except the seven in ``_REDERIVED``: re-derived on BOTH variants by the court
structure change (W1/E1 stem steel, the 3'-0" backfill rule, FT-SG-S's heel), worked in
``notes/sunken_garden_court_free_body.md`` §15n, and pinned here at their new values.

Slow: one full check run. ``scripts/verify.sh`` runs it; ``--fast`` skips it.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.slow

#: Items the court structure change re-derived on both variants (free body §15n); their pins
#: below are the re-derived values, every other pin is main's pre-switch value.
_REDERIVED = {
    "retaining_system/W-SG-ARCH",
    "column_support/W-SG-W1",
    "column_support/W-SG-E1",
    "retaining_wall/W-SG-S",
    "retaining_wall/W-SG-W2",
    "retaining_wall/W-SG-E2",
    "thermal_break_transfer/W-SG-ARCH",
}

FINGERPRINTS = {
    "base_rotation/PT-SG-BF1": '504fb789417cb1b4',
    "base_rotation/PT-SG-BF3": '9d79ac4ce308d1f6',
    "base_rotation/PT-SG-BR1": 'ecbb9867ffdb1999',
    "base_rotation/PT-SG-BR3": '1cc218f5c2c08560',
    "column_head_joint/PT-SG-BF1": '061406486e8154d5',
    "column_head_joint/PT-SG-BF3": '2bfd06b9ba160283',
    "column_head_joint/PT-SG-BR1": '95cb5fe026d2805f',
    "column_head_joint/PT-SG-BR3": 'f7ded399caeb3338',
    # re-derived by the structure lane (§15n)
    "column_support/W-SG-E1": 'a32add969c8b8d0f',
    # re-derived by the structure lane (§15n)
    "column_support/W-SG-W1": '7a23d8233f213c1b',
    "deck_post/PT-SG-BF1": 'ceeb7ebb6c351b71',
    "deck_post/PT-SG-BF3": 'be66d44cf62c74e9',
    "deck_post/PT-SG-BR1": '37c3198868f3b275',
    "deck_post/PT-SG-BR3": '3fbdee23626ccf92',
    "deck_tie/FS-BW-FLOOR": '57b32bc2cdf9bcb8',
    "glulam_beam/BM-SG-BLE": '2efbf1aac75fd818',
    "glulam_beam/BM-SG-BLW": '4f944054628be019',
    "lateral_system/RF-BW-CANOPY": '1ddd91e69ab938c9',
    "rafter/RF-BW-CANOPY": None,
    "rafter/RF-GARAGE": None,
    # re-derived by the structure lane (§15n)
    "retaining_system/W-SG-ARCH": '984583ec50c3db47',
    # re-derived by the structure lane (§15n)
    "retaining_wall/W-SG-E2": 'e60c4a1104818100',
    # re-derived by the structure lane (§15n)
    "retaining_wall/W-SG-S": 'c3b08ccf282470f4',
    # re-derived by the structure lane (§15n)
    "retaining_wall/W-SG-W2": 'e24a67b7b2704f21',
    "roof_beam/BM-BW-RE": '78357259cc953d72',
    "roof_beam/BM-BW-RW": 'c3148e3d5ed7bf06',
    # re-derived by the structure lane (§15n)
    "thermal_break_transfer/W-SG-ARCH": '27fb313ee3a76025',
    "veneer_anchor/W-B-BRICK": None,
    "wood_roof_post/PT-BW-CNW": 'ae46fb9a6cd1311d',
    "wood_roof_post/PT-BW-CW": 'c4d9585b4f1fc6a1',
    "wood_roof_post/PT-BW-RE": 'e2c509c73642ba93',
    "wood_roof_post/PT-BW-RNE": '5df8d5ff5802138a',
}


@pytest.fixture(scope="module")
def brick(catlin_brick_ctx):
    from typehaus.checks.run import run_checks

    return catlin_brick_ctx, run_checks(catlin_brick_ctx)


def test_the_brick_variant_has_no_check_failures(brick) -> None:
    from typehaus.findings import Result

    _ctx, report = brick
    failures = {(f.check_id, tuple(sorted(f.element_tags or ())))
                for f in report.findings if f.result is Result.FAIL}
    assert not failures, sorted(failures)


def test_the_brick_variant_has_exactly_the_pre_switch_register(brick) -> None:
    from typehaus.engineering.discovery import engineering_item_ids

    ctx, report = brick
    items = set(engineering_item_ids(ctx.engineering, report.findings))
    assert items == set(FINGERPRINTS)
    assert "veneer_anchor/W-B-BRICK" in items


def test_the_brick_variant_reproduces_the_pre_switch_fingerprints(brick) -> None:
    from typehaus.engineering import Status, fingerprint

    ctx, _report = brick
    got = {item: None if ctx.engineering[item].status is Status.NO_CALC
           else fingerprint(ctx.engineering[item]) for item in FINGERPRINTS}
    assert got == FINGERPRINTS
