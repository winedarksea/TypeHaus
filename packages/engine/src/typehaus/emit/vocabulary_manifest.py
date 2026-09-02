"""One generated JSON manifest for the vocabulary tables the engine and the ``ui/`` viewer
must agree on, replacing five "author twice, test-scrape the TypeScript to catch drift"
pairs with one authored (Python) source and one generated (JSON) artifact.

The five tables:

* ``emit/gltf/palette.py`` ``_PALETTE`` (member-category colours) <-> ``ui/src/three/members.ts``
  ``CATEGORY_COLOR``.
* the same ``_PALETTE`` (solid-category colours) <-> ``ui/src/three/solidMaterials.ts``
  ``SOLID_CATEGORY_COLOR``. These are the *same* Python dict serving two TypeScript tables —
  the two already agreed on every key they shared (``fascia``/``gutter``/``soffit``), because
  both were transcriptions of the one table below. The manifest makes that explicit instead
  of implicit: both ``memberColors`` and ``solidColors`` are the whole palette.
* ``emit/trades.py`` ``SOLID_CATEGORY_TRADE`` <-> the mirror inlined in
  ``ui/src/three/solidMaterials.ts``.
* ``emit/finishes.py`` ``LAYER_VISIBILITY_GROUPS`` + ``LAYER_GROUP_ALIASES`` <->
  ``ui/src/model/visibility.ts`` ``ALL_LAYER_VISIBILITY_GROUPS`` + ``LAYER_FUNCTION_ALIASES``.
* ``emit/draw/typography.py``'s sizing constants <-> ``ui/src/components/detailTypography.ts``
  (the constants only — ``modelInPerPt``/``paperInPerModelIn``/``wrapColumnsFor`` are logic,
  authored once per language on purpose, and stay hand-written in both).

This module imports each of those from its *owning* module — nothing here is restated data —
and assembles them into one JSON-serializable dict. Colours: the Python side stores linear
0..1 RGBA tuples (comments in ``palette.py`` say so); the manifest converts to TypeScript's
representation — ``0xRRGGBB`` packed into a JSON int, alpha dropped (opacity is a separate,
per-material path on the ``ui/`` side) — rounding each channel to the nearest 8-bit step
exactly once, here, rather than leaving each language to round independently.

Checked in vs. regenerated: ``ui/src/generated/vocabulary.json`` is checked into git. There is
no existing "generated-and-gitignored" convention for source the ``ui/`` build itself needs to
exist (the only generated-artifact entries in ``.gitignore`` are asset-bundler outputs staged by
``ui/scripts/build-*.mjs`` at dev-server start, and this is Vite/tsc source, imported at build
time, needed by a bare ``npm run build``/``npm run typecheck``/CI with no Python build step ever
having run). So the JSON file is authored-by-generation and versioned like any other source
file — which means it can go stale relative to ``_PALETTE`` et al. the same way a hand-copied
table could. ``write_vocabulary_manifest`` is how a maintainer refreshes it after touching one
of the five Python tables; the guard tests under ``packages/engine/tests`` regenerate the
manifest fresh from source and diff it against the checked-in copy, so a forgotten refresh
fails in the suite instead of silently drifting.
"""

from __future__ import annotations

import json
from pathlib import Path

from typehaus.emit.draw.typography import (
    CHAR_ASPECT,
    DIM_TEXT_PT,
    LEADER_TEXT_PT,
    LEADER_WRAP_COLUMNS,
    LINE_SPACING,
    MIN_PT,
    NOTES_PT,
    TEXT_PT,
)
from typehaus.emit.finishes import LAYER_GROUP_ALIASES, LAYER_VISIBILITY_GROUPS
from typehaus.emit.gltf.palette import _PALETTE
from typehaus.emit.trades import SOLID_CATEGORY_TRADE


def _to_hex(rgba: tuple[float, float, float, float]) -> int:
    """Linear 0..1 RGBA -> packed ``0xRRGGBB`` int, alpha dropped.

    Each channel rounds to the nearest 8-bit step.
    """
    red, green, blue, _alpha = rgba
    return (round(red * 255) << 16) | (round(green * 255) << 8) | round(blue * 255)


def _palette_hex() -> dict[str, int]:
    return {category: _to_hex(rgba) for category, rgba in _PALETTE.items()}


def build_vocabulary_manifest() -> dict[str, object]:
    """Assemble the manifest in memory — what :func:`write_vocabulary_manifest` serializes,
    and what a guard test diffs against the checked-in copy without touching disk."""
    palette_hex = _palette_hex()
    return {
        # The same table, twice: `_PALETTE` is the one Python source for both the member-
        # category colours the framing/roof members read and the solid-category colours the
        # slabs/posts/pipes/trim read. Splitting it into two curated subsets here would be a
        # second place that decides which keys belong to which viewer table — exactly the
        # kind of restatement this manifest exists to remove.
        "memberColors": palette_hex,
        "solidColors": palette_hex,
        "solidTrades": dict(SOLID_CATEGORY_TRADE),
        "layerVisibilityGroups": list(LAYER_VISIBILITY_GROUPS),
        "layerGroupAliases": dict(LAYER_GROUP_ALIASES),
        "typography": {
            "CHAR_ASPECT": CHAR_ASPECT,
            "LINE_SPACING": LINE_SPACING,
            "MIN_PT": MIN_PT,
            "TEXT_PT": TEXT_PT,
            "LEADER_TEXT_PT": LEADER_TEXT_PT,
            "DIM_TEXT_PT": DIM_TEXT_PT,
            "NOTES_PT": NOTES_PT,
            "LEADER_WRAP_COLUMNS": LEADER_WRAP_COLUMNS,
        },
    }


def write_vocabulary_manifest(path: Path) -> None:
    """Write the manifest as JSON to ``path``, creating parent directories as needed.

    Used both by ``haus build`` (-> ``out/vocabulary.json``, a per-build artifact that never
    depends on which house was built) and, pointed at ``ui/src/generated/vocabulary.json``,
    to refresh the checked-in copy the ``ui/`` build imports directly.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_vocabulary_manifest()
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
