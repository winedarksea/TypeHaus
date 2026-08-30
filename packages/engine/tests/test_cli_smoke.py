"""Every `haus` command is reachable and its --help renders.

The CLI was one 960-line module; splitting it into `cli/_shared.py` + per-topic `cmd_*`
modules is only safe if something proves the full command list still registers. A command
that fails to register, or whose options collide (`fmt` is both a command name and a
parameter name elsewhere), disappears silently — `haus` just stops offering it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from typehaus.cli.app import app, main  # `main` is the packaging entry point — keep it here
from _helpers import CATLIN, copy_house

EXPECTED_COMMANDS = {
    "build", "check", "compare", "diff", "doctor", "energy",
    "engineering", "explain", "export", "fmt",
    "import", "import-project", "ls", "millwork", "new", "permit-check", "print", "render",
    "serve", "takeoff", "tasks", "version",
}

runner = CliRunner()


def _names() -> set[str]:
    return {command.name or command.callback.__name__.replace("_", "-")
            for command in app.registered_commands}


def test_every_command_is_registered() -> None:
    assert _names() == EXPECTED_COMMANDS


def test_the_subapps_are_still_mounted() -> None:
    assert {"variants", "costs"} <= {group.name for group in app.registered_groups}


def test_main_is_importable_from_the_entry_point_module() -> None:
    """`typehaus.cli.app:main` is the console_scripts target — the split must not move it."""
    assert callable(main)


@pytest.mark.parametrize("command", sorted(EXPECTED_COMMANDS))
def test_command_help_renders(command: str) -> None:
    result = runner.invoke(app, [command, "--help"])
    assert result.exit_code == 0, result.output


def test_version_prints_the_engine_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "engine" in result.output


def test_check_reports_loader_findings_on_a_successful_import(tmp_path: Path) -> None:
    """A movable element in a non-editable file imports fine, so `check` used to print
    nothing about it — the error only reached the console when the import itself failed."""
    catlin = Path(__file__).resolve().parents[3] / "houses" / "catlin"
    dst = tmp_path / "catlin"
    copy_house(catlin, dst)
    # An MEP module that actually authors movable elements (Registers). plan/mep.py is now
    # only the aggregator lists and carries no editable header to strip.
    mep = dst / "plan" / "mep_registers.py"
    mep.write_text(mep.read_text().replace("# haus: editable\n", "", 1))

    # Loader errors are never filtered by --only, so the default output must carry it.
    result = runner.invoke(app, ["check", str(dst)])
    assert "uneditable_movable_element" in result.output
    assert result.exit_code == 1


def test_ls_runs_over_the_starter_house(starter_dir: Path) -> None:
    result = runner.invoke(app, ["ls", str(starter_dir)])
    assert result.exit_code == 0, result.output


def test_takeoff_runs_over_the_starter_house(starter_dir: Path) -> None:
    result = runner.invoke(app, ["takeoff", str(starter_dir), "--json"])
    assert result.exit_code == 0, result.output


def test_takeoff_summary_runs_over_the_starter_house(starter_dir: Path) -> None:
    """`haus takeoff --summary` (#52): a per-section rollup, not the full per-row dump."""
    result = runner.invoke(app, ["takeoff", str(starter_dir), "--summary"])
    assert result.exit_code == 0, result.output
    assert "Bill of materials summary" in result.output
    assert "sections," in result.output


def test_takeoff_summary_is_an_order_of_magnitude_smaller_than_json() -> None:
    """catlin's full ``--json`` is the ~860KB / ~1,363-line per-row dump; ``--summary``
    replaces it with a rows/keys-per-section rollup for the same house."""
    full = runner.invoke(app, ["takeoff", str(CATLIN), "--json"])
    summary = runner.invoke(app, ["takeoff", str(CATLIN), "--summary"])
    assert full.exit_code == 0 and summary.exit_code == 0
    assert len(summary.output) < len(full.output) / 10
    assert "cost_estimate" not in summary.output
    # The escape hatch is unaffected: --json still carries every row.
    assert '"cost_estimate"' in full.output
