"""WP2.12/WP3.1 — `haus new` scaffolds a buildable house; catlin is the default (#22)."""

from __future__ import annotations

from pathlib import Path

from typehaus.cli.scaffold import scaffold_house
from typehaus.resolve import resolve
from typehaus.source import load_plan


def test_minimal_scaffold_builds_and_resolves(tmp_path: Path):
    house = tmp_path / "myhouse"
    created = scaffold_house(house, "My House", template="minimal")
    assert (house / "brief.md") in created
    assert (house / "preferences.toml") in created
    result = load_plan(house)
    assert result.ok, [f.message for f in result.findings if f.severity.value == "error"]
    model, _ = resolve(result.plan)
    assert len(model.walls) == 4
    assert len(model.rooms) == 1


def test_minimal_scaffold_has_no_dependency_on_monorepo_library(tmp_path: Path):
    house = tmp_path / "standalone"
    scaffold_house(house, "Standalone", template="minimal")
    # A minimal house defines its own assemblies locally, not `from library import ...`.
    assert "from library" not in (house / "plan" / "assemblies.py").read_text()


def test_minimal_scaffolded_elements_all_have_uids(tmp_path: Path):
    house = tmp_path / "uids"
    scaffold_house(house, "Uids", template="minimal")
    from typehaus.source import lint_only

    missing = [f for f in lint_only(house) if f.check_id == "dialect.missing_uid"]
    assert missing == []


def test_default_template_is_catlin_verbatim(tmp_path: Path):
    """#22: `haus new` defaults to the catlin house; a fresh project uuid is minted."""
    house = tmp_path / "newdefault"
    created = scaffold_house(house, "New Default")
    assert (house / "params" / "sunken_garden.py").is_file()
    manifest = (house / "plan" / "manifest.py").read_text()
    assert 'name="New Default"' in manifest
    assert "c471a000-93b5-4e6e-8f5a-000000000002" not in manifest  # fresh uuid
    result = load_plan(house)
    assert result.ok, [f.message for f in result.findings if f.severity.value == "error"]
    model, _ = resolve(result.plan)
    assert len(model.walls) > 40  # the real house, not the starter box
    assert created
