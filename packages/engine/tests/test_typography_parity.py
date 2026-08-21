"""The engine and the viewer must letter a detail the same (→ 30 §Details).

``DetailCanvas`` draws the same ``Scene`` the PDF/DXF writers do, from its own copy of the
text metrics. Nothing made the two agree: ``CHAR_ASPECT`` was written out four times on the
Python side and once more in TypeScript, each with a comment asking the next person to keep
it in sync. This is that comment, enforced.

A *Python* test reading the TypeScript as text, following ``test_palette_parity.py``: it
fails in the engine suite, where an engine change is made, rather than only in a browser.
"""

from __future__ import annotations

import re

import pytest
from _helpers import REPO_ROOT

from typehaus.emit.draw import typography

TS = REPO_ROOT / "ui" / "src" / "components" / "detailTypography.ts"

#: Model-inch fallbacks the TS side needs and the engine expresses elsewhere (``scene.py``'s
#: ``Leader.height`` default, the dimension size that has no IR field yet). Not typography
#: constants, so they are named here rather than silently tolerated.
_TS_ONLY = {"LEADER_TEXT_H", "DIM_TEXT_H"}


def _ts_numbers() -> dict[str, float]:
    source = TS.read_text()
    return {name: float(value) for name, value in
            re.findall(r"^export const ([A-Z][A-Z0-9_]*) = ([0-9.]+);$", source, re.M)}


def _py_numbers() -> dict[str, float]:
    return {name: getattr(typography, name) for name in dir(typography)
            if name.isupper() and isinstance(getattr(typography, name), (int, float))}


def test_every_engine_constant_is_present_and_equal_in_the_viewer():
    ts = _ts_numbers()
    for name, value in _py_numbers().items():
        assert name in ts, f"{name} is missing from detailTypography.ts"
        assert ts[name] == value, f"{name}: engine {value}, viewer {ts[name]}"


def test_the_viewer_invents_no_typography_of_its_own():
    """The direction that actually rots: a constant added on the TS side only.

    Nothing else reads it, so nothing else disagrees with it — until an engine change lands
    beside it and the two renderers quietly draw different drawings.
    """
    extra = set(_ts_numbers()) - set(_py_numbers()) - _TS_ONLY
    assert not extra, f"detailTypography.ts declares {sorted(extra)} with no engine source"


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
