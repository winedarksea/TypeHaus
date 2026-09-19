"""``haus trial`` — score the working tree against a recorded baseline.

The loop's second half. ``haus route --evaluate`` asks "would this proposal help"; this
asks "did the edit help", about the house as it now stands on disk after a person pasted
something and ran ``haus fmt``.

    haus trial houses/catlin --record        # snapshot the tree (out/trials/baseline.json)
    haus trial houses/catlin                 # build + check the tree, diff vs the baseline
    haus trial houses/catlin --checks all --json
    haus trial houses/catlin --no-suppress   # score an open suppressed campaign

``--no-suppress`` is recorded *into* the baseline and a mismatch between the two is
refused rather than scored: catlin blanket-suppresses ``mep.run_interference``, so a
suppressed trial on that house reports a clean card however bad the edit was.

Exit 1 on a new FAIL in the chosen set, 2 on a load or dialect error. **It writes nothing
to the plan**, and its one write — the baseline — is a generated artefact under ``out/``.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from typehaus.cli._shared import _resolve_house, app, console


@app.command()
def trial(
    house: Path | None = typer.Argument(None, help="House directory (default: cwd)"),
    record_baseline: bool = typer.Option(
        False, "--record", help="Snapshot the tree as the baseline and stop."),
    checks: str = typer.Option(
        "mep", "--checks", help='Which findings to diff: "mep" (the set a route can '
                                'break) or "all".'),
    no_suppress: bool = typer.Option(
        False, "--no-suppress",
        help="Lift [checks] suppress, the way `haus check --no-suppress` does. Required "
             "to score an open suppressed campaign; the baseline must match."),
    as_json: bool = typer.Option(False, "--json", help="Print the scorecard as JSON."),
) -> None:
    """Build and check the working tree, and report what moved since the baseline."""
    from typehaus.cli.trial_score import (
        load_baseline,
        record,
        render,
        score,
        write_baseline,
    )

    directory = _resolve_house(house)
    if checks not in ("mep", "all"):
        console.print('[red]--checks wants "mep" or "all"[/red]')
        raise typer.Exit(2)

    try:
        if record_baseline:
            path = write_baseline(
                directory, record(directory, suppress=not no_suppress))
            console.print(f"[green]baseline recorded: {path}"
                          f"{' (suppression lifted)' if no_suppress else ''}[/green]")
            return
        baseline = load_baseline(directory)
        if baseline is None:
            # Recording and saying so, rather than refusing: the first `haus trial` on a
            # branch is always this case, and an error that tells a person to run the same
            # command with one more flag is a step nobody should have to take.
            path = write_baseline(
                directory, record(directory, suppress=not no_suppress))
            console.print(f"[yellow]no baseline existed, so this tree IS the baseline "
                          f"now ({path}). Nothing is scored against it yet — edit, then "
                          "run this again[/yellow]")
            return
        card = score(directory, baseline, checks=checks, suppress=not no_suppress)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc

    if as_json:
        console.print_json(json.dumps(card.as_dict(), default=str))
    else:
        for line in render(card):
            console.print(line)
    if card.exit_code:
        raise typer.Exit(card.exit_code)
