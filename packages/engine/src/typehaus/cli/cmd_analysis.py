"""``haus analysis`` — the engineered frame, in the four files an engineer's software opens.

One graph (``typehaus/analytical``), four readers: the IFC4 structural analysis view for
SAP2000 / ETABS / Bonsai, a 3-D centreline DXF for RISA, ``members.csv`` for the
single-member tools, and a self-contained PyNite script. ``--solve`` runs that same graph
through PyNite here and prints every support reaction beside the demand the engineering
record graded, which is the quickest way to see whether the model and the calc sheet are
describing the same building. ``haus handoff`` writes the same files into its bundle.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.table import Table

from typehaus.cli._shared import app, console

_LB = 1 / 4.4482216152605
_LB_FT = _LB / 0.3048


@app.command()
def analysis(
    house: Path | None = typer.Argument(None, help="House directory (default: cwd)"),
    out: Path | None = typer.Option(
        None, "--out", help="Where to write (default: <house>/out/analysis)."),
    profile: str | None = typer.Option(
        None, "--profile", help="Jurisdiction profile (default: preferences.toml)."),
    ifc: bool = typer.Option(
        True, "--ifc/--no-ifc",
        help="Write analysis.ifc — the structural analysis view on its own, without the "
             "physical building. `haus handoff` puts the same view inside model.ifc."),
    solve: bool = typer.Option(
        False, "--solve", help="Solve the graph in PyNite and print reactions beside the "
                               "records' demands (needs `pip install typehaus[fea]`)."),
) -> None:
    """Write the analytical model four ways; --solve checks it against the records."""
    from typehaus.analytical.build import build_analytical_model
    from typehaus.cli.engineering_load import load_engineering
    from typehaus.emit.analytical import (
        write_analysis_readme,
        write_members_csv,
        write_pynite_script,
    )
    from typehaus.emit.draw.dxf_structure import write_structure_dxf

    load = load_engineering(house, profile)
    root = out if out is not None else load.directory / "out" / "analysis"
    root.mkdir(parents=True, exist_ok=True)
    model = build_analytical_model(load.ctx)
    name = load.ctx.model.plan.project.name or load.directory.name

    write_pynite_script(model, root / "model.pynite.py")
    write_members_csv(model, root / "members.csv")
    write_structure_dxf(model, root / "centreline.dxf")
    if ifc:
        from typehaus.emit.ifc.analytical import write_standalone

        write_standalone(model, root / "analysis.ifc",
                         project_uuid=load.ctx.model.plan.project.project_uuid, project_name=name)
    write_analysis_readme(model, root / "README.md", house=name, has_ifc=ifc)
    console.print(f"wrote {root}: {len(model.members)} members, {len(model.nodes)} nodes, "
                  f"{len(model.supports)} supports, {len(model.cases)} load cases, "
                  f"{len(model.scope)} item(s); {len(model.gaps)} gap(s)", soft_wrap=True)
    for gap in model.gaps:
        console.print(f"  [yellow]gap:[/yellow] {gap}", soft_wrap=True)
    if solve:
        _print_solution(model, load)


def _print_solution(model, load) -> None:  # type: ignore[no-untyped-def]
    """Reactions per support and case, beside the record that grades that element."""
    from typehaus.analytical.solve import solve as run_solve

    result = run_solve(model)
    if not result.stable:
        console.print("[red]PyNite reports the model unstable — a support or release is "
                      "wrong; the reactions below are not trustworthy.[/red]")
    for warning in result.warnings:
        console.print(f"[yellow]{warning}[/yellow]", soft_wrap=True)
    table = Table(title="Support reactions (PyNite) vs record demands")
    for column in ("Element", "Case", "Fz lb", "Fx lb", "Fy lb", "M lb-ft", "Record says"):
        table.add_column(column)
    for support in sorted(model.supports, key=lambda s: (s.element_tag, s.node)):
        record = load.results.get(support.item_id) if support.item_id else None
        for case in sorted(model.cases, key=lambda c: c.kind.value):
            reaction = result.reactions.get((support.node, case.name))
            if reaction is None:
                continue
            moment = max(abs(reaction.mx_nm), abs(reaction.my_nm)) * _LB_FT
            table.add_row(
                support.element_tag or support.node, case.name,
                f"{reaction.fz_n * _LB:,.0f}", f"{reaction.fx_n * _LB:,.0f}",
                f"{reaction.fy_n * _LB:,.0f}", f"{moment:,.0f}",
                _record_demand(record, case.name))
    console.print(table)


def _record_demand(record, case: str) -> str:  # type: ignore[no-untyped-def]
    if record is None:
        return "—"
    wanted = {"dead": ("dead_load", "design_dead", "carried_dead"),
              "live": ("live_load",), "snow": ("roof_snow", "design_snow"),
              "wind": ("column_base_moment", "wind_base_moment"),
              "guard": ("guard_base_moment",)}.get(case, ())
    hits = [q for q in record.inputs if q.name in wanted]
    if not hits:
        return "—"
    return "; ".join(f"{q.name} {q.value:,.0f} {q.unit}" for q in hits)
