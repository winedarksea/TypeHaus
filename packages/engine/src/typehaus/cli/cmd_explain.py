"""`haus explain` — why an element, assembly, or transition resolved the way it did.

Registered onto the shared app in :mod:`typehaus.cli._shared`.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.table import Table

from typehaus.cli._shared import _detail, _print_findings, _resolve_house, app, console


@app.command()
def explain(
    target: str = typer.Argument(
        ..., help="element tag | assembly tag | 'transitions' | 'module'"),
    house: Path | None = typer.Argument(None),
    card: bool = typer.Option(False, help="render the assembly section card"),
    detail: bool = typer.Option(False, help="render the transition detail(s) for a TR-* tag"),
    out: Path | None = typer.Option(None, help="write card SVG to this path"),
    transitions: bool = typer.Option(False, help="enumerate derived boundary conditions"),
    bearing: bool = typer.Option(
        False, help="show authored bearing walls and resolved stack edges"),
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

    if target == "module":
        _explain_module(plan)
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
        from typehaus.emit.draw.render import DETAIL_DPI
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
            # DETAIL_DPI, the same as ``haus render --view details`` — a detail carries
            # the finest hatch and lettering in the set, and the two commands drawing the
            # same card at two resolutions made one of them look like a different drawing.
            path = write_raster(scene, dest_dir / f"detail_{slug}.png",
                                title=f"detail · {derived.key}", dpi=DETAIL_DPI)
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


def _explain_module(plan) -> None:
    """``haus explain module`` — the stud grid, as a REPORT and never as a check.

    21 of catlin's 46 second-storey walls start off the 16" module, and a check that said so
    would emit around fifty findings house-wide of which perhaps five are worth acting on. It
    would also break the 0-FAIL gate permanently, which is how a house learns to stop reading
    its own check output. So this prints instead, and three rules keep it honest:

    **Report the residue, never grade it.** A wall whose start node sits at a 12" residue is
    not wrong; it is a wall whose studs are 12" out of phase with the wall below, which may be
    exactly right and may be free to fix. The number is the input to a judgement, not the
    judgement.

    **Sort by consequence, not by residue size.** The wall to look at first is the one with
    the most orphaned studs, and that is a function of how many studs it has and what is under
    it — not of how far off the module its node happens to be. ``W-S-C2C`` at a 4" residue can
    cost more than ``W-A-BA-E`` at 12".

    **Name the remedy per row.** ``reverse``, ``line`` or ``move node``, chosen by what the
    wall's own geometry allows, because "this wall is off the module" is not an instruction.
    ``reverse`` is the cheap one and is offered first wherever it applies: swapping a wall's
    start and end nodes is direction-independent for every ``from_node`` offset on it, so on a
    wall with no openings it is free in every sense. It is what took ``W-A-BA-E`` from 9
    orphaned studs to 3, and it is one line.

    The orphan arithmetic is ``_stud_grid.orphan_studs``, shared with
    ``test_upper_storey_studs_stand_over_studs`` so the pin and this report cannot disagree.
    """
    from typehaus.checks.registry import FramingPreferences
    from typehaus.checks.structural._stud_grid import (
        orphan_studs,
        segment_residue_in,
        structure_framing,
        wall_module,
    )
    from typehaus.resolve import resolve
    from typehaus.resolve.layout_lines import lines_by_wall

    model, findings = resolve(plan)
    _print_findings(findings)
    total, per_wall = orphan_studs(model)
    lines = lines_by_wall(model.layout_lines)
    hosted: dict[str, int] = {}
    for opening in model.openings:
        hosted[opening.host_wall] = hosted.get(opening.host_wall, 0) + 1
    fallback = FramingPreferences().module_in

    console.print(f"[bold]Stud grid[/bold]  {sum(per_wall.values())} of {total} stacked "
                  f"upper-storey studs stand over no stud below, across "
                  f"{len(per_wall)} walls", soft_wrap=True)
    console.print(f"  [dim]{'orph':>4} {'storey':<8}{'wall':<13}{'mod':>4}{'resid':>7}"
                  f"{'ops':>4}  remedy[/dim]", soft_wrap=True)
    for tag, count in sorted(per_wall.items(), key=lambda kv: (-kv[1], kv[0])):
        wall = model.wall(tag)
        if wall is None:
            continue
        framing = structure_framing(plan.library.resolve_assembly(wall.assembly))
        if framing is None:
            continue
        module_in = wall_module(framing, fallback)
        residue = segment_residue_in(wall, module_in)
        on_line = getattr(framing, "layout_origin", "wall-start") == "line"
        openings = hosted.get(tag, 0)
        if on_line:
            # Its grid is the LINE's, shared with every wall on it, so nothing about THIS
            # wall's nodes will move it.
            remedy = "shared line — re-phase the line, or nothing"
        elif residue > 0.01 and not openings:
            remedy = "reverse (free: no openings, direction-independent)"
        elif lines.get(tag) is not None:
            remedy = 'layout_origin="line" on its assembly'
        else:
            remedy = "move the start node — price it first"
        console.print(f"  {count:>4} {wall.storey:<8}{tag:<13}{module_in:>3.0f}\""
                      f"{residue:>6.1f}\"{openings:>4}  {remedy}", soft_wrap=True)
    console.print("[dim]A residue is reported, never graded: a wall out of phase with the "
                  "wall below may be exactly right. Sorted by consequence — orphaned studs — "
                  "not by residue.[/dim]", soft_wrap=True)
