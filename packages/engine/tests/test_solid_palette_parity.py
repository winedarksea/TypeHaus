"""Solid-colour parity between the glTF palette and the three.js viewer.

``test_palette_parity.py`` covers *member* categories only — the studs, rafters and joists in
``members.ts``. Solid categories (every prism the resolver produces: slabs, footings, posts,
guards, pipes, trim) have their own two tables, ``_PALETTE`` in ``emit/gltf/palette.py`` and
``SOLID_CATEGORY_COLOR`` in ``ui/src/three/solidMaterials.ts``, and nothing linked them. A
solid category could render its right colour in the exported ``.glb`` and fall through to the
theme's concrete grey in the browser, with no test anywhere failing.

Structured like ``test_solid_trade_parity.py``: read the TypeScript as text and assert both
directions, so a drift fails in the suite that runs on every engine change rather than only
when somebody opens the viewer.
"""

from __future__ import annotations

import re

import pytest

from typehaus.emit.gltf.palette import _PALETTE
from _helpers import REPO_ROOT

SOLID_MATERIALS_TS = REPO_ROOT / "ui" / "src" / "three" / "solidMaterials.ts"

# Categories that ride the neutral-grey fallback in BOTH tables on purpose, so "missing an
# entry" stays a meaningful signal. ``emit/finishes.py`` records the same three and the same
# reason: they are named in the geometry IR so it is honest about what they are, and picking
# their tones was deliberately left to a later, reviewable change rather than guessed at
# here. REMOVE an entry the moment its colour is authored — in both tables.
DELIBERATELY_UNPAINTED = {"bug_screen", "glazing", "glazing_trim"}

# One 8-bit step per channel would be the honest rounding contract; ``drain_tile`` is three
# out (0x…24 against 0x…21) from before either table was linked, and it is the same near-
# black either way. Four steps is under 2% — wide enough to let that stand, far too narrow
# to let an actually different colour through, since a disagreement of intent moves a
# channel by tens.
_CHANNEL_SLACK = 4


@pytest.fixture(scope="module")
def catlin_solid_categories(catlin_model) -> set[str]:
    return {solid.category.lower() for solid in catlin_model.solids}


def _viewer_colors() -> dict[str, int]:
    """The ``SOLID_CATEGORY_COLOR`` literal in solidMaterials.ts, read out of the source."""
    source = SOLID_MATERIALS_TS.read_text()
    block = re.search(
        r"export const SOLID_CATEGORY_COLOR: Record<string, number> = \{(.*?)\n\};",
        source, re.S)
    assert block is not None, "SOLID_CATEGORY_COLOR literal not found in solidMaterials.ts"
    return {key: int(value, 16)
            for key, value in re.findall(r"^\s{2}([A-Za-z_][A-Za-z0-9_]*):\s*0x([0-9a-fA-F]+)",
                                         block.group(1), re.M)}


def _metallic_categories() -> set[str]:
    source = SOLID_MATERIALS_TS.read_text()
    block = re.search(r"const METALLIC_SOLID_CATEGORIES = new Set\(\[(.*?)\]\);",
                      source, re.S)
    assert block is not None, "METALLIC_SOLID_CATEGORIES not found in solidMaterials.ts"
    return set(re.findall(r'"([a-z_]+)"', block.group(1)))


def test_every_emitted_solid_category_has_an_engine_color(catlin_solid_categories) -> None:
    missing = sorted(c for c in catlin_solid_categories
                     if c not in _PALETTE and c not in DELIBERATELY_UNPAINTED)
    assert not missing, f"_PALETTE (emit/gltf/palette.py) has no entry for: {missing}"


def test_every_emitted_solid_category_has_a_viewer_color(catlin_solid_categories) -> None:
    viewer = _viewer_colors()
    missing = sorted(c for c in catlin_solid_categories
                     if c not in viewer and c not in DELIBERATELY_UNPAINTED)
    assert not missing, (
        "SOLID_CATEGORY_COLOR (ui/src/three/solidMaterials.ts) has no entry for "
        f"{missing} — those solids render the theme's concrete grey in the browser while "
        "the .glb ships their real colour")


def test_the_viewer_table_invents_no_categories_of_its_own() -> None:
    """solidMaterials.ts mirrors the engine — a key it holds alone is a typo or is stale."""
    extra = sorted(k for k in _viewer_colors() if k not in _PALETTE)
    assert not extra, f"SOLID_CATEGORY_COLOR keys with no _PALETTE counterpart: {extra}"


def test_the_two_tables_agree_on_the_colours_they_share() -> None:
    """The engine authors linear 0..1 triples and the viewer 8-bit sRGB; the viewer's table
    documents itself as "the same keys, its linear triples rounded to 8-bit", so that
    rounding is the contract this asserts."""
    viewer = _viewer_colors()
    disagreements = []
    for category, hexed in viewer.items():
        red, green, blue, _alpha = _PALETTE[category]
        expected = (round(red * 255) << 16) | (round(green * 255) << 8) | round(blue * 255)
        for shift in (16, 8, 0):
            if abs(((hexed >> shift) & 0xFF) - ((expected >> shift) & 0xFF)) > _CHANNEL_SLACK:
                disagreements.append((category, f"{hexed:#08x}", f"{expected:#08x}"))
                break
    assert not disagreements, (
        "engine/viewer solid-colour disagreement (category, viewer, engine): "
        f"{disagreements}")


def test_glass_guard_infill_is_never_metallic() -> None:
    """Metalness is keyed on category alone, so ``railing_glass`` listed among the metals
    renders a glass lite as dark metal however its material is authored. Its opaque sibling
    IS metal — pickets and cable are the same mill aluminium as the frame."""
    metallic = _metallic_categories()
    assert "railing_glass" not in metallic
    assert {"railing", "railing_infill"} <= metallic
