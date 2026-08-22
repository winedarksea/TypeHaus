"""The engine and the viewer must letter a detail the same (→ 30 §Details).

``DetailCanvas`` draws the same ``Scene`` the PDF/DXF writers do. Its sizing constants
(``CHAR_ASPECT``, ``TEXT_PT``, and friends) used to be a second, hand-authored copy in
``ui/src/components/detailTypography.ts`` — ``CHAR_ASPECT`` alone was written out four times
on the Python side before this module existed, each copy asking the next person to keep it in
sync by comment.

The TypeScript copy is gone: ``detailTypography.ts`` now imports
``ui/src/generated/vocabulary.json`` (generated from ``emit/draw/typography.py`` by
``emit/vocabulary_manifest.py``) for its eight sizing constants, so a value can no longer
drift or be invented independently on the TypeScript side. What remains possible is the
checked-in JSON going stale relative to ``typography.py``, which
``test_the_checked_in_manifest_matches_a_fresh_build`` below catches.

The two tests below that are about *logic*, not data — ``modelInPerPt``/
``paperInPerModelIn``/``wrapColumnsFor`` are hand-written once per language on purpose — are
untouched.
"""

from __future__ import annotations

import json

import pytest
from _helpers import REPO_ROOT

from typehaus.emit.draw import typography
from typehaus.emit.vocabulary_manifest import build_vocabulary_manifest

TS = REPO_ROOT / "ui" / "src" / "components" / "detailTypography.ts"
VOCABULARY_JSON = REPO_ROOT / "ui" / "src" / "generated" / "vocabulary.json"


def test_the_checked_in_manifest_matches_a_fresh_build():
    """ui/src/generated/vocabulary.json is checked into git and is what
    ui/src/components/detailTypography.ts actually imports for its eight sizing constants —
    there is no longer a second, independently authored TypeScript copy to compare against.
    Regenerate the manifest in memory and diff it against the file on disk, to catch the
    checked-in copy going stale relative to ``emit/draw/typography.py``."""
    fresh = build_vocabulary_manifest()["typography"]
    checked_in = json.loads(VOCABULARY_JSON.read_text())["typography"]
    assert fresh == checked_in, (
        "ui/src/generated/vocabulary.json is stale — regenerate it "
        "(typehaus.emit.vocabulary_manifest.write_vocabulary_manifest) after this change to "
        "emit/draw/typography.py")


def test_the_conversions_agree_line_for_line():
    """``modelInPerPt``/``paperInPerModelIn``/``wrapColumnsFor``, read as source.

    Comparing the arithmetic rather than sampled outputs: a wrong constant inside one of
    them produces the right answer at the one scale anybody happens to test.
    """
    source = TS.read_text()
    assert "return 12.0 / scale / 72.0;" in source
    assert "return scale / 12.0;" in source
    assert "Math.floor((bandIn * 72.0) / (sizePt * CHAR_ASPECT))" in source
    # And the Python side still says the same thing. ``scale`` is ARCH_SCALES' number —
    # paper inches per model foot — so 1-1/2" = 1'-0" is 1.5, not 8.
    assert typography.model_in_per_pt(1.5) == 12.0 / 1.5 / 72.0
    assert typography.model_in_per_pt(1.5) * typography.TEXT_PT == pytest.approx(0.7778, abs=1e-4)
    assert typography.paper_in_per_model_in(0.25) == 0.25 / 12.0
    assert typography.wrap_columns_for(3.4, typography.NOTES_PT) == \
        int(3.4 * 72.0 / (typography.NOTES_PT * typography.CHAR_ASPECT))


def test_a_zero_size_cannot_wrap_to_zero_columns():
    """``textwrap`` raises on width 0, so the floor is a real guard, not a nicety."""
    assert typography.wrap_columns_for(3.4, 0.0) == 1
    assert typography.wrap_columns_for(0.0, 9.0) == 1
    assert "if (sizePt <= 0.0) return 1;" in TS.read_text()
