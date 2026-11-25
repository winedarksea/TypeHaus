"""The court's brick face is a declared variant, and switching back reproduces it exactly.

The default court face is LP panel on ``W-B-S2-FR``/``W-B-S3-FR``; brick (``W-B-BRICK`` on
``W-SG-BRKBM``) is variant ``court-face-brick`` (``variants.toml``). ``FINGERPRINTS`` are
``main``'s fingerprints from before the switch, one per engineering item (``None``: a NO_CALC
record, which has no fingerprint). The proof is that the variant reproduces them all, so
brick is not a second design to re-engineer. The seven in ``_REDERIVED`` were later re-derived
by the structure lane (free body §15n) on BOTH variants; their pins are re-set at the merge.

Slow: one full check run. ``scripts/verify.sh`` runs it; ``--fast`` skips it.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.slow

#: Items the structure lane re-derived on both variants (free body §15n); their pins below
#: are main's pre-switch values and are re-pinned at the merge.
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
    "column_support/W-SG-E1": 'a96ffcb7892f51ff',
    # re-derived by the structure lane (§15n)
    "column_support/W-SG-W1": 'abc8d1796a18c76e',
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
    "retaining_system/W-SG-ARCH": '4961a9629858950f',
    # re-derived by the structure lane (§15n)
    "retaining_wall/W-SG-E2": '0b4843f936bad035',
    # re-derived by the structure lane (§15n)
    "retaining_wall/W-SG-S": '4ded606ddd2ad393',
    # re-derived by the structure lane (§15n)
    "retaining_wall/W-SG-W2": '04e8768786214dfc',
    "roof_beam/BM-BW-RE": '78357259cc953d72',
    "roof_beam/BM-BW-RW": 'c3148e3d5ed7bf06',
    # re-derived by the structure lane (§15n)
    "thermal_break_transfer/W-SG-ARCH": '5ee34ea6333fdbc8',
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
