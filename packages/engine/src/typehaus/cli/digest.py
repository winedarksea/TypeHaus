"""`haus ls --summary` — a compact, context-window-sized plan digest for agents (#52)."""

from __future__ import annotations

from rich.console import Console

from typehaus.model.plan import PlanModel


def print_summary(plan: PlanModel, console: Console) -> None:
    from typehaus.analysis import assembly_r_value
    from typehaus.resolve import resolve

    model, findings = resolve(plan)
    console.print(f"[bold]{plan.project.name}[/bold] — {len(plan.storeys)} storeys")
    for storey in sorted(plan.storeys, key=lambda s: s.elevation.meters):
        walls = [e for e in plan.storey_elements(storey.tag)
                 if e.element_kind in ("Wall", "FoundationWall")]
        rooms = [r for r in model.rooms if r.storey == storey.tag]
        console.print(f"  storey {storey.tag} @ {storey.elevation.fmt()}: "
                      f"{len(walls)} walls, {len(rooms)} rooms")
        for r in rooms:
            # The floor area, and — where a roof rakes into the room — how much of it has
            # 5'-0" of head. An attic room's first number alone is misleading.
            head = ""
            if r.head_limited_area_m2 is not None and \
                    r.area_m2 - r.head_limited_area_m2 > 0.5:
                head = f" ({r.head_limited_area_m2 * 10.7639:.0f} sf over 5'-0\" head)"
            console.print(f"    {r.tag} ({r.occupancy}) {r.area_m2 * 10.7639:.0f} sf{head}")
    console.print("  assemblies:")
    for asm in plan.library.assemblies:
        ra = plan.library.resolve_assembly(asm.tag)
        rv = assembly_r_value(ra, plan.library) if ra else None
        console.print(f"    {asm.tag}: {rv.fmt() if rv else '?'}")
    console.print(f"  derived conditions: {len(model.conditions)}; "
                  f"stack edges: {len(model.stack_edges)}; "
                  f"framed members: {len(model.all_members())}")
    open_findings = [f for f in findings]
    console.print(f"  open resolve findings: {len(open_findings)}")
