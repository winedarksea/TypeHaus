"""Solid-colour parity between the glTF palette and the three.js viewer.

``test_palette_parity.py`` covers *member* categories only — the studs, rafters and joists in
``members.ts``. Solid categories (every prism the resolver produces: slabs, footings, posts,
guards, pipes, trim) used to have their own second table, hand-authored in
``ui/src/three/solidMaterials.ts`` as ``SOLID_CATEGORY_COLOR`` and linked to ``_PALETTE``
(``emit/gltf/palette.py``) only by a test reading the TypeScript as text.

That table is gone. ``solidMaterials.ts`` now imports ``ui/src/generated/vocabulary.json`` —
generated from the same ``_PALETTE`` by ``emit/vocabulary_manifest.py`` — directly, so a
TypeScript-only category or a rounding disagreement between the two languages is no longer
possible: there is nothing on the TypeScript side left to disagree. What remains possible is
the checked-in JSON going stale relative to ``_PALETTE``, which
``test_the_checked_in_manifest_matches_a_fresh_build`` catches by rebuilding the manifest in
memory and diffing it against the file on disk.
"""

from __future__ import annotations

import json

import pytest

from typehaus.emit.gltf.palette import _PALETTE
from typehaus.emit.vocabulary_manifest import build_vocabulary_manifest
from _helpers import REPO_ROOT

SOLID_MATERIALS_TS = REPO_ROOT / "ui" / "src" / "three" / "solidMaterials.ts"
VOCABULARY_JSON = REPO_ROOT / "ui" / "src" / "generated" / "vocabulary.json"

# Categories that ride the neutral-grey fallback in BOTH tables on purpose, so "missing an
# entry" stays a meaningful signal. ``emit/finishes.py`` records the same three and the same
# reason: they are named in the geometry IR so it is honest about what they are, and picking
# their tones was deliberately left to a later, reviewable change rather than guessed at
# here. REMOVE an entry the moment its colour is authored, in ``_PALETTE``.
DELIBERATELY_UNPAINTED = {"bug_screen", "glazing", "glazing_trim"}


@pytest.fixture(scope="module")
def catlin_solid_categories(catlin_model) -> set[str]:
    return {solid.category.lower() for solid in catlin_model.solids}


def _metallic_categories() -> set[str]:
    """``METALLIC_SOLID_CATEGORIES`` has no Python mirror — it is a TypeScript-only render
    flag, not one of the five vocabulary tables the manifest generates — so this still reads
    the source file directly."""
    source = SOLID_MATERIALS_TS.read_text()
    import re

    block = re.search(r"const METALLIC_SOLID_CATEGORIES = new Set\(\[(.*?)\]\);",
                      source, re.S)
    assert block is not None, "METALLIC_SOLID_CATEGORIES not found in solidMaterials.ts"
    return set(re.findall(r'"([a-z_]+)"', block.group(1)))


def test_every_emitted_solid_category_has_an_engine_color(catlin_solid_categories) -> None:
    missing = sorted(c for c in catlin_solid_categories
                     if c not in _PALETTE and c not in DELIBERATELY_UNPAINTED)
    assert not missing, f"_PALETTE (emit/gltf/palette.py) has no entry for: {missing}"


def test_the_checked_in_manifest_matches_a_fresh_build() -> None:
    """ui/src/generated/vocabulary.json is checked into git and is what
    ui/src/three/solidMaterials.ts actually imports for ``SOLID_CATEGORY_COLOR`` — there is no
    longer a second, independently authored TypeScript table to compare against. Regenerate
    the manifest in memory and diff it against the file on disk, to catch the checked-in copy
    going stale relative to ``_PALETTE``."""
    fresh = build_vocabulary_manifest()["solidColors"]
    checked_in = json.loads(VOCABULARY_JSON.read_text())["solidColors"]
    assert fresh == checked_in, (
        "ui/src/generated/vocabulary.json is stale — regenerate it "
        "(typehaus.emit.vocabulary_manifest.write_vocabulary_manifest) after this change to "
        "emit/gltf/palette.py")


def test_glass_guard_infill_is_never_metallic() -> None:
    """Metalness is keyed on category alone, so ``railing_glass`` listed among the metals
    renders a glass lite as dark metal however its material is authored. Its opaque sibling
    IS metal — pickets and cable are the same mill aluminium as the frame."""
    metallic = _metallic_categories()
    assert "railing_glass" not in metallic
    assert {"railing", "railing_infill"} <= metallic
