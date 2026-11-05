"""``structural.footing_size``: IRC Table R403.1(1) read with footnotes a and b.

Oracle: the 2026-11-04 geometry review's hand read (plans/geometry-review/2026-11-04/
adjudicated/C2.md E1) — 50 psf band, 3 story plus basement, 36' house: 32x11 at 1,500 psf,
25x8 at 2,000.
"""

from __future__ import annotations

import pytest

from typehaus.checks.structural.footing_size import footing_size
from typehaus.checks.structural.footing_tables import required_footing_in
from typehaus.findings import Result


@pytest.mark.parametrize(("stories", "soil", "width_ft", "expected"), [
    (3, 1500.0, 36.0, (32.0, 11.0)),
    (3, 2000.0, 36.0, (25.0, 8.0)),
    (2, 1500.0, 36.0, (29.0, 9.0)),
    (2, 2000.0, 36.0, (23.0, 8.0)),
    (3, 1750.0, 32.0, (24.5, 7.5)),   # footnote a: between columns
    (1, 2000.0, 24.0, (12.0, 6.0)),   # footnote b floors: 16 - 8 -> 12, T never under 6
])
def test_the_table_reads_like_the_hand_note(stories, soil, width_ft, expected):
    assert required_footing_in(stories, "basement", 50.0, soil, width_ft) == \
        pytest.approx(expected)


def test_every_catlin_house_strip_meets_the_table(catlin_ctx):
    findings = [f for f in footing_size(catlin_ctx) if f.element_tags[0].startswith("FT-B-")]
    assert len(findings) == 21
    assert all(f.result == Result.PASS for f in findings), \
        [f.message for f in findings if f.result != Result.PASS]
