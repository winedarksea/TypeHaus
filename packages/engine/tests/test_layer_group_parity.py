"""The engine and the viewer must name the same assembly bands.

Per-layer visibility rides plain node visibility in the 3D viewer, keyed by the
``layerGroup`` the engine puts on each part. A group name the UI does not know is a band the
user can never toggle off — and it used to fail silently, in the browser, not here, because
``LAYER_VISIBILITY_GROUPS``/``LAYER_GROUP_ALIASES`` (``emit/finishes.py``) were mirrored by a
second, hand-authored copy in ``ui/src/model/visibility.ts``, linked only by a test reading
the TypeScript as text.

That second copy is gone: ``visibility.ts`` now imports ``ui/src/generated/vocabulary.json``
(generated from the engine tables by ``emit/vocabulary_manifest.py``) directly, so the two
vocabularies can no longer independently drift. What remains possible is the checked-in JSON
going stale relative to the engine tables, which
``test_the_checked_in_manifest_matches_a_fresh_build`` below catches.
"""

from __future__ import annotations

import json

import pytest

from typehaus.emit.finishes import LAYER_VISIBILITY_GROUPS, layer_visibility_group
from typehaus.emit.vocabulary_manifest import build_vocabulary_manifest
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import HOUSES, REPO_ROOT

VOCABULARY_JSON = REPO_ROOT / "ui" / "src" / "generated" / "vocabulary.json"


def test_the_checked_in_manifest_matches_a_fresh_build() -> None:
    """ui/src/generated/vocabulary.json is checked into git and is what
    ui/src/model/visibility.ts actually imports for both ``ALL_LAYER_VISIBILITY_GROUPS`` and
    ``LAYER_FUNCTION_ALIASES`` — there is no longer a second, independently authored
    TypeScript table to compare against. Regenerate the manifest in memory and diff it
    against the file on disk, to catch the checked-in copy going stale relative to
    ``emit/finishes.py``."""
    fresh = build_vocabulary_manifest()
    checked_in = json.loads(VOCABULARY_JSON.read_text())
    assert fresh["layerVisibilityGroups"] == checked_in["layerVisibilityGroups"]
    assert fresh["layerGroupAliases"] == checked_in["layerGroupAliases"]


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
