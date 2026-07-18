"""WP2.12 — `haus new` scaffolds a self-contained, buildable house (→ 20 §brief.md)."""

from __future__ import annotations

from pathlib import Path

from typehaus.cli.scaffold import scaffold_house
from typehaus.resolve import resolve
from typehaus.source import load_plan


def test_scaffold_builds_and_resolves(tmp_path: Path):
    house = tmp_path / "myhouse"
    created = scaffold_house(house, "My House")
    assert (house / "brief.md") in created
    assert (house / "preferences.toml") in created
    result = load_plan(house)
    assert result.ok, [f.message for f in result.findings if f.severity.value == "error"]
    model, _ = resolve(result.plan)
    assert len(model.walls) == 4
    assert len(model.rooms) == 1


def test_scaffold_has_no_dependency_on_monorepo_library(tmp_path: Path):
    house = tmp_path / "standalone"
    scaffold_house(house, "Standalone")
    # A scaffolded house defines its own assemblies locally, not `from library import ...`.
    assert "from library" not in (house / "plan" / "assemblies.py").read_text()


def test_scaffolded_elements_all_have_uids(tmp_path: Path):
    house = tmp_path / "uids"
    scaffold_house(house, "Uids")
    from typehaus.source import lint_only

    missing = [f for f in lint_only(house) if f.check_id == "dialect.missing_uid"]
    assert missing == []
