"""Duplicate catalog tags must be caught, not silently resolved by tuple order.

Library lookups are `next((x for x in catalog if x.tag == tag), None)`. Nothing validated
against duplicates, so a house entry sharing a library entry's tag produced whichever came
first in the manifest's tuple splat — a spec change with no error, no warning, and no diff.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.checks import run
from typehaus.checks.integrity.catalog_tags import CATALOGS
from typehaus.source import load_plan
from _helpers import HOUSES



def _dupes(report) -> list:
    return [f for f in report.findings if f.check_id == "integrity.duplicate_catalog_tag"]


@pytest.mark.parametrize("house", ["starter", "catlin"])
def test_shipped_houses_have_no_duplicate_catalog_tags(house: str) -> None:
    """The precondition for the library dedupe: both houses are clean *before* any retag."""
    result = load_plan(HOUSES / house)
    assert result.plan is not None
    assert _dupes(run(result.plan, HOUSES / house)) == []


def test_a_shadowed_library_tag_is_a_hard_error(starter_dir: Path) -> None:
    from typehaus.checks import build_context
    from typehaus.checks.integrity.catalog_tags import duplicate_catalog_tag

    result = load_plan(starter_dir)
    assert result.plan is not None
    original = result.plan.library.window_types
    assert original, "starter defines no window types to duplicate"
    shadowed = result.plan.model_copy(update={
        "library": result.plan.library.model_copy(update={
            "window_types": (*original, original[0]),
        }),
    })
    ctx, _ = build_context(shadowed, starter_dir)
    findings = duplicate_catalog_tag(ctx)
    assert len(findings) == 1
    assert original[0].tag in findings[0].message
    assert "window_types" in findings[0].message
    assert findings[0].severity.value == "error"


def test_every_tag_keyed_catalog_is_covered() -> None:
    """A catalog added to Library and not to CATALOGS is an uncovered shadowing hazard."""
    from typehaus.model.plan import Library

    tag_keyed = set()
    for name, field in Library.model_fields.items():
        entries = getattr(Library(), name, ())
        # Model the field's element type rather than an instance (the default is empty):
        # a catalog is tag-keyed if its declared item type carries a `tag` field.
        args = getattr(field.annotation, "__args__", ())
        item = args[0] if args else None
        if item is not None and hasattr(item, "model_fields") and "tag" in item.model_fields:
            tag_keyed.add(name)
        assert isinstance(entries, tuple)
    uncovered = sorted(tag_keyed - set(CATALOGS))
    assert not uncovered, f"tag-keyed catalogs with no duplicate check: {uncovered}"
