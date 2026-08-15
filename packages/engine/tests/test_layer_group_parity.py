"""The engine and the viewer must name the same assembly bands.

Per-layer visibility rides plain node visibility in the 3D viewer, keyed by the
``layerGroup`` the engine puts on each part. A group name the UI does not know is a band the
user can never toggle off — and it fails silently, in the browser, not here.

Same grep-the-TypeScript technique as `test_palette_parity.py`: the point is to fail in the
suite that runs on every engine change.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from typehaus.emit.finishes import LAYER_VISIBILITY_GROUPS, layer_visibility_group
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import HOUSES, REPO_ROOT

VISIBILITY_TS = REPO_ROOT / "ui" / "src" / "model" / "visibility.ts"


def _ts_groups() -> list[str]:
    text = VISIBILITY_TS.read_text()
    block = re.search(
        r"ALL_LAYER_VISIBILITY_GROUPS:\s*LayerVisibilityGroup\[\]\s*=\s*\[(.*?)\]",
        text, re.S,
    )
    assert block, "could not find ALL_LAYER_VISIBILITY_GROUPS in visibility.ts"
    return re.findall(r'"([^"]+)"', block.group(1))


def _ts_aliases() -> dict[str, str]:
    text = VISIBILITY_TS.read_text()
    block = re.search(
        r"LAYER_FUNCTION_ALIASES:\s*Record<string,\s*LayerVisibilityGroup>\s*=\s*\{(.*?)\}",
        text, re.S,
    )
    assert block, "could not find LAYER_FUNCTION_ALIASES in visibility.ts"
    return dict(re.findall(r"(\w+):\s*\"([^\"]+)\"", block.group(1)))


def test_the_group_vocabularies_are_identical() -> None:
    assert list(LAYER_VISIBILITY_GROUPS) == _ts_groups()


def test_the_alias_tables_agree() -> None:
    """An alias only one side knows sends a band to `other` in one renderer and to its real
    group in the other, so the same toggle hides different things."""
    for key, group in _ts_aliases().items():
        assert layer_visibility_group(key) == group, key


def test_an_unknown_function_buckets_to_other_on_both_sides() -> None:
    assert layer_visibility_group("no-such-function") == "other"
    assert layer_visibility_group("") == "other"
    assert layer_visibility_group(None) == "other"


@pytest.mark.parametrize("house", ["starter", "catlin"])
def test_every_emitted_layer_group_is_in_the_vocabulary(house: str) -> None:
    result = load_plan(HOUSES / house)
    assert result.plan is not None
    model, _findings = resolve(result.plan)
    assert model.geometry is not None
    groups = {part.layer_group for element in model.geometry.elements
              for part in element.parts if part.layer_group is not None}
    assert groups, "no part declared a layer group at all"
    assert groups <= set(LAYER_VISIBILITY_GROUPS), sorted(
        groups - set(LAYER_VISIBILITY_GROUPS))
