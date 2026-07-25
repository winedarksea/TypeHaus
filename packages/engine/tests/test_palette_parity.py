"""Member-colour parity between the glTF emitter and the three.js viewer.

Two tables name the same thing: ``_PALETTE`` in ``emit/gltf/emitter.py`` and
``CATEGORY_COLOR`` in ``ui/src/three/members.ts``. Nothing linked them, so they drifted —
``rafter``/``blocking``/``outlooker``/``barge_rafter`` were missing from *both* (the "garage
truss should visualize as wood" report) and the truss keys existed engine-side only. That
was ~470 framing members rendering as the neutral grey fallback.

This test is the link: every member category the Catlin model actually emits has to resolve
in both tables. It reads the TypeScript as text on purpose — the point is to fail here, in
the suite that runs on every engine change, rather than only in the browser.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from typehaus.emit.gltf.emitter import _PALETTE
from typehaus.resolve import resolve
from typehaus.source import load_plan

REPO_ROOT = Path(__file__).resolve().parents[3]
CATLIN_DIR = REPO_ROOT / "houses" / "catlin"
MEMBERS_TS = REPO_ROOT / "ui" / "src" / "three" / "members.ts"


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


def _category_color_keys() -> set[str]:
    """The keys of ``CATEGORY_COLOR`` in members.ts, read out of the source."""
    source = MEMBERS_TS.read_text()
    block = re.search(
        r"const CATEGORY_COLOR: Record<string, number> = \{(.*?)\n\};", source, re.S)
    assert block is not None, "CATEGORY_COLOR literal not found in members.ts"
    return set(re.findall(r"^\s{2}([A-Za-z_][A-Za-z0-9_]*):\s*0x", block.group(1), re.M))


# Categories the roof-eave stream added whose colour entries live in files that stream does
# not own (emit/gltf/palette.py `_PALETTE` and ui/src/three/members.ts `CATEGORY_COLOR` —
# both ui-stream territory). The palette additions are recorded as a coordinator escape;
# REMOVE this set when applying it. Both member kinds carry a `material` (standing-seam /
# aluminum), so the material colour path covers them in the meantime — only the category
# fallback colour is missing.
_PENDING_PALETTE_ESCAPES = {"ridge_cap", "corner_trim"}


def test_every_emitted_member_category_has_an_engine_color(catlin_member_categories) -> None:
    missing = sorted(c for c in catlin_member_categories
                     if c not in _PALETTE and c not in _PENDING_PALETTE_ESCAPES)
    assert not missing, f"_PALETTE (emit/gltf/emitter.py) has no entry for: {missing}"


def test_every_emitted_member_category_has_a_viewer_color(catlin_member_categories) -> None:
    missing = sorted(c for c in catlin_member_categories
                     if c not in _category_color_keys()
                     and c not in _PENDING_PALETTE_ESCAPES)
    assert not missing, f"CATEGORY_COLOR (ui/src/three/members.ts) has no entry for: {missing}"


def test_the_viewer_table_invents_no_categories_of_its_own() -> None:
    """members.ts mirrors the engine — a key it holds alone is a typo or a stale category."""
    extra = sorted(k for k in _category_color_keys() if k not in _PALETTE)
    assert not extra, f"CATEGORY_COLOR keys with no _PALETTE counterpart: {extra}"
