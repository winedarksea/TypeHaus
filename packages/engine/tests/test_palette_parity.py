"""Member-colour parity between the glTF emitter and the three.js viewer.

``_PALETTE`` (``emit/gltf/palette.py``) used to be mirrored by a second, hand-authored table
in TypeScript — ``CATEGORY_COLOR`` in ``ui/src/three/members.ts`` — linked only by a test that
read the TypeScript as text. That drifted: ``rafter``/``blocking``/``outlooker``/
``barge_rafter`` were missing from *both* (the "garage truss should visualize as wood" report)
and the truss keys existed engine-side only. That was ~470 framing members rendering as the
neutral grey fallback.

The second table is gone. ``members.ts`` now imports ``ui/src/generated/vocabulary.json`` —
generated from ``_PALETTE`` by ``emit/vocabulary_manifest.py`` — directly, so a TypeScript
table with its own typo or its own stale entry is no longer a thing that can exist. What is
still possible is the checked-in JSON going stale relative to ``_PALETTE`` because nobody
regenerated it; that is what ``test_the_checked_in_manifest_matches_a_fresh_build`` below
catches, by rebuilding the manifest in memory and diffing it against the file on disk, rather
than trusting either language's copy.
"""

from __future__ import annotations

import json

import pytest

from typehaus.emit.gltf.emitter import _PALETTE
from typehaus.emit.vocabulary_manifest import build_vocabulary_manifest
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR, REPO_ROOT

VOCABULARY_JSON = REPO_ROOT / "ui" / "src" / "generated" / "vocabulary.json"


@pytest.fixture(scope="module")
def catlin_member_categories() -> set[str]:
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    assert not [f for f in findings if f.severity.value == "error"]
    categories: set[str] = set()
    for host in (*model.walls, *model.floors, *model.roofs, *model.stairs):
        for member in host.members:
            categories.add(member.category.lower())
    return categories


def test_every_emitted_member_category_has_an_engine_color(catlin_member_categories) -> None:
    missing = sorted(c for c in catlin_member_categories
                     if c not in _PALETTE)
    assert not missing, f"_PALETTE (emit/gltf/palette.py) has no entry for: {missing}"


def test_the_checked_in_manifest_matches_a_fresh_build() -> None:
    """ui/src/generated/vocabulary.json is checked into git and is what
    ui/src/three/members.ts actually imports — there is no longer a second, independently
    authored TypeScript table to compare against. The only remaining drift is the checked-in
    copy going stale relative to ``_PALETTE``, so regenerate the manifest in memory and diff
    it against the file on disk rather than trusting either side."""
    fresh = build_vocabulary_manifest()["memberColors"]
    checked_in = json.loads(VOCABULARY_JSON.read_text())["memberColors"]
    assert fresh == checked_in, (
        "ui/src/generated/vocabulary.json is stale — regenerate it "
        "(typehaus.emit.vocabulary_manifest.write_vocabulary_manifest) after this change to "
        "emit/gltf/palette.py")
