"""`haus explain` — why an element, assembly, or transition resolved the way it did.

Registered onto the shared app in :mod:`typehaus.cli._shared`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from rich.table import Table

from typehaus.cli._shared import _detail, _print_findings, _resolve_house, app, console


@app.command()
def explain(
    target: str = typer.Argument(..., help="element tag | assembly tag | 'transitions'"),
    house: Optional[Path] = typer.Argument(None),
    card: bool = typer.Option(False, help="render the assembly section card"),
    detail: bool = typer.Option(False, help="render the transition detail(s) for a TR-* tag"),
    out: Optional[Path] = typer.Option(None, help="write card SVG to this path"),
    transitions: bool = typer.Option(False, help="enumerate derived boundary conditions"),
    bearing: bool = typer.Option(False, help="show authored bearing walls and resolved stack edges"),
) -> None:
    """Explain an element, render an assembly card, or list transitions."""
    from typehaus.source import load_plan

    d = _resolve_house(house)
    result = load_plan(d)
    if result.plan is None:
        _print_findings(result.findings)
        raise typer.Exit(1)
    plan = result.plan

    if target == "transitions" or transitions:
        from typehaus.resolve import resolve

        model, _ = resolve(plan)
        table = Table("kind", "key", "elements")
        for cond in model.conditions:
            table.add_row(cond.kind.value, cond.key, ", ".join(cond.element_tags))
        console.print(table)
        return

    if bearing:
        from typehaus.resolve import resolve

        model, findings = resolve(plan)
        _print_findings(findings)
        table = Table("storey", "bearing wall", "assembly", "supports / stack relation")
        authored = {element.tag: element for element in plan.all_elements()
                    if element.element_kind in ("Wall", "FoundationWall")}
        for wall in sorted(model.walls, key=lambda item: (item.storey, item.tag)):
            source = authored.get(wall.tag)
            role = getattr(getattr(source, "structural_role", None), "value", "unknown")
            lower = [edge.lower_wall for edge in model.stack_edges if edge.upper_wall == wall.tag]
            upper = [edge.upper_wall for edge in model.stack_edges if edge.lower_wall == wall.tag]
            if role != "bearing" and not lower and not upper:
                continue
            relation = ", ".join([*(f"on {tag}" for tag in lower),
                                  *(f"to {tag}" for tag in upper)]) or "bearing role"
            table.add_row(wall.storey, wall.tag, wall.assembly, relation)
        console.print(table)

        # The chain, not the pairs: ``stack_edges`` is pairwise and says nothing about where
        # a wall sits *along* the line it shares, which is the number that decides whether
        # two stud modules agree.
        lines = Table("layout line", "storey", "wall", "station", "runs")
        for line in model.layout_lines:
            if len(line.members) < 2:
                continue
            for index, member in enumerate(line.members):
                lines.add_row(line.tag if index == 0 else "", member.storey,
                              member.wall_tag, f"{member.u_offset_m:+.3f} m",
                              "with" if member.direction_sign > 0 else "reversed")
        console.print(lines)
        return

    if detail:
        from typehaus.emit.draw.details import build_detail, derive_detail_slices
        from typehaus.emit.draw.pdf_writer import write_raster
        from typehaus.resolve import resolve

        model, _ = resolve(plan)
        details = [d for d in derive_detail_slices(model)
                   if d.transition is not None and d.transition.tag == target]
        if not details:
            console.print(f"[red]no derived detail bound to transition {target!r}[/red]")
            raise typer.Exit(1)
        dest_dir = out or (d / "out" / "render")
        dest_dir.mkdir(parents=True, exist_ok=True)
        for derived in details:
            scene, findings = build_detail(model, derived)
            _print_findings(findings)
            slug = derived.view.tag.replace("/", "_")
            path = write_raster(scene, dest_dir / f"detail_{slug}.png",
                                title=f"detail · {derived.key}")
            console.print(f"wrote {path}")
        return

    asm = plan.library.resolve_assembly(target)
    if asm is not None:
        from typehaus.analysis import assembly_r_value
        from typehaus.checks import load_preferences
        from typehaus.checks.building_science.condensation import analyze_assembly
        from typehaus.emit.draw import render_card_svg

        rv = assembly_r_value(asm, plan.library)
        console.print(f"[bold]{asm.tag}[/bold]  R-value: {rv.fmt()}"
                      + (f"  STC {asm.stc}" if asm.stc else ""))
        for layer in list(asm.default_lining) + list(asm.layers):
            console.print(f"  {layer.function.value:9} {layer.name:12} {layer.thickness.fmt()}")
            if layer.cavity is not None:
                fill = layer.cavity
                thk = fill.thickness if fill.thickness is not None else layer.thickness
                console.print(f"  {'  ↳ cavity':9} {fill.material_ref:12} {thk.fmt()}"
                              f"  (ff {fill.framing_factor:.0%}, in bays — adds no depth)")
        if card or out:
            heating = plan.project.site.design_temp_heating
            condensation = analyze_assembly(
                asm, plan.library,
                heating_design_temp_f=heating.fahrenheit if heating else None,
                preferences=load_preferences(d),
            )
            svg = render_card_svg(asm, plan.library, condensation)
            dest = out or (d / "out" / f"card_{asm.tag}.svg")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(svg)
            console.print(f"wrote {dest}")
        return

    el = plan.by_tag(target)
    if el is None:
        console.print(f"[red]no element, assembly, or 'transitions' named {target!r}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]{el.tag}[/bold] ({el.element_kind}) uid={el.uid}")
    loc = result.provenance.location(el.tag)
    if loc:
        console.print(f"  source: {loc}")
    console.print(f"  {_detail(el)}")
