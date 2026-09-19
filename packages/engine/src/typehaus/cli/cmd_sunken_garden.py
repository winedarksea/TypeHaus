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

    from typehaus.analytical.sunken_garden_coupled import analyse_coupled
    from typehaus.cli._shared import _resolve_house
    from typehaus.cli.sunken_garden_costs import price_variants
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.engineering.sunken_garden.comparison import REFERENCE_LAYOUT
    from typehaus.engineering.sunken_garden.model_inputs import design_input_from_model
    from typehaus.engineering.sunken_garden.report import write_study
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    root = _resolve_house(house)
    output = out.resolve() if out is not None else root / "out" / "sunken-garden-study"

    # ** THIS COMMAND RESOLVED THE HOUSE AND THEN NEVER OPENED IT, UNTIL 2026-09-14. **
    # ``write_study`` ran off ``default_design_input()``'s literals, which disagreed with the
    # authored court — so the report described a wall nine inches shorter than the one being
    # built, and said nothing about it. The study is now driven from the same resolved model
    # the engineering register reads; what cannot be derived is printed as a gap.
    result = load_plan(root)
    if result.plan is None:
        console.print("[red]the house does not load; the study needs the resolved model[/]")
        for finding in result.findings[:10]:
            console.print(f"  {finding.message}")
        raise typer.Exit(1)
    model, _ = resolve(result.plan)
    design, fell_back = design_input_from_model(
        EngineeringContext(plan=result.plan, model=model))
    priced = price_variants(root)
    report = write_study(output, design, fell_back,
                         costs=priced.lines if priced else None,
                         cost_source=priced.source if priced else None,
                         allowances=priced.allowances if priced else ())
    console.print(f"wrote {report} and five coordinated SVG sections")
    if priced is None:
        console.print("[yellow]no prices.toml: every layout is reported unpriced[/]")
    if fell_back:
        console.print(f"[yellow]{len(fell_back)} input(s) kept a literal basis:[/]")
        for item in fell_back:
            console.print(f"  {item}")
    else:
        console.print("every geometric input was read from the resolved model")

    # ** THE COUPLED FIVE-WALL SHELL MODEL HAD NO CALLER UNTIL 2026-09-18. **
    # ``analyse_coupled`` builds all five walls, their footings, the soil springs and the
    # balcony column loads as one shell model and solves it — or refuses, naming what it
    # wants. Both are reviewable; neither was reachable from any command, so the study
    # said nothing at all about the walls acting together. It is printed, never written:
    # a refusal is the honest answer here and it is not a deliverable.
    coupled = analyse_coupled(design, REFERENCE_LAYOUT)
    if coupled.successful:
        console.print(
            f"coupled five-wall solve: vertical equilibrium error "
            f"{coupled.equilibrium_error:.2%}, maximum translation "
            f"{coupled.maximum_translation_in:.3f} in")
    else:
        console.print("[yellow]the coupled five-wall solve is refused:[/]")
        for item in coupled.unresolved:
            console.print(f"  {item}")
