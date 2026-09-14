"""Generate the coordinated Catlin sunken-courtyard engineering study."""

from __future__ import annotations

from pathlib import Path

import typer

from typehaus.cli._shared import app, console


@app.command("sunken-garden-study")
def sunken_garden_study(
    house: Path | None = typer.Argument(None, help="House directory (default: cwd)"),
    out: Path | None = typer.Option(
        None, "--out", help="Output directory (default: <house>/out/sunken-garden-study)."),
) -> None:
    """Write the layout, engineering, sizing and cost comparison."""

    from typehaus.cli._shared import _resolve_house
    from typehaus.engineering.sunken_garden.report import write_study

    root = _resolve_house(house)
    output = out.resolve() if out is not None else root / "out" / "sunken-garden-study"
    report = write_study(output)
    console.print(f"wrote {report} and five coordinated SVG sections")
