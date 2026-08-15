"""WP2.12/WP3.1 — `haus new` scaffolds a buildable house by copying a shipped one (#22).

The scaffolder used to write an inline "minimal" plan out of string constants, a third copy
of the starter house that drifted from it. It now copies ``houses/starter`` (default) or
``houses/catlin``, so a scaffolded house is by construction one the test suite already builds.
"""

from __future__ import annotations

import filecmp
from pathlib import Path

import pytest

from typehaus.cli.scaffold import scaffold_house
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import STARTER



def test_default_scaffold_builds_and_resolves(tmp_path: Path):
    house = tmp_path / "myhouse"
    created = scaffold_house(house, "My House")
    assert (house / "brief.md") in created
    assert (house / "preferences.toml") in created
    result = load_plan(house)
    assert result.ok, [f.message for f in result.findings if f.severity.value == "error"]
    model, _ = resolve(result.plan)
    assert model.walls and model.rooms


def test_default_scaffold_is_the_starter_house_verbatim(tmp_path: Path):
    """The one property the deleted inline template could not hold: no drift is possible,
    because the scaffold *is* the starter source (bar the minted project identity)."""
    house = tmp_path / "copy"
    scaffold_house(house, "My House")
    for source in sorted(STARTER.joinpath("plan").rglob("*.py")):
        if "__pycache__" in source.parts:
            continue
        rel = source.relative_to(STARTER)
        copied = house / rel
        assert copied.is_file(), rel
        if rel.name == "manifest.py":
            continue  # the project uuid is deliberately re-minted
        assert filecmp.cmp(source, copied, shallow=False), rel


def test_scaffolded_elements_all_have_uids(tmp_path: Path):
    house = tmp_path / "uids"
    scaffold_house(house, "Uids")
    from typehaus.source import lint_only

    missing = [f for f in lint_only(house) if f.check_id == "dialect.missing_uid"]
    assert missing == []


def test_catlin_template_copies_the_real_house(tmp_path: Path):
    """#22: `--template catlin` still yields the reference house, with a fresh uuid."""
    house = tmp_path / "newdefault"
    created = scaffold_house(house, "New Default", template="catlin")
    assert (house / "params" / "sunken_garden.py").is_file()
    manifest = (house / "plan" / "manifest.py").read_text()
    assert 'name="New Default"' in manifest
    assert "c471a000-93b5-4e6e-8f5a-000000000002" not in manifest  # fresh uuid
    result = load_plan(house)
    assert result.ok, [f.message for f in result.findings if f.severity.value == "error"]
    model, _ = resolve(result.plan)
    assert len(model.walls) > 40  # the real house, not the starter box
    assert created


def test_a_fresh_project_uuid_is_minted_per_scaffold(tmp_path: Path):
    def uuid_of(house: Path) -> str:
        scaffold_house(house, "Same Name")
        return (house / "plan" / "manifest.py").read_text()

    assert uuid_of(tmp_path / "a") != uuid_of(tmp_path / "b")


def test_an_unknown_template_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError):
        scaffold_house(tmp_path / "nope", "Nope", template="minimal")
