"""`haus print3d` — the house as a 3MF file set for a desktop printer (``docs/print3d.md``).

Outside ``haus check`` and the standard gate entirely, and the one command that needs the
``print3d`` extra (manifold3d).
"""

from __future__ import annotations

from pathlib import Path

import typer

from typehaus.cli._shared import _print_findings, _resolve_house, app, console
from typehaus.findings import Severity


def _kinds(value: str | None) -> frozenset[str]:
    from typehaus.print3d.policy import KIND_POLICY

    kinds = frozenset(part.strip() for part in (value or "").split(",") if part.strip())
    unknown = sorted(kinds - set(KIND_POLICY))
    if unknown:
        raise typer.BadParameter(f"no print3d policy row for {', '.join(unknown)}")
    return kinds


def _bed(value: str) -> tuple[float, float, float]:
    parts = [float(part) for part in value.lower().split("x")]
    if len(parts) != 3:
        raise typer.BadParameter("--bed is WxDxH in mm, e.g. 256x256x256")
    return (parts[0], parts[1], parts[2])


@app.command()
def print3d(
    house: Path | None = typer.Argument(None),
    out: Path = typer.Option(Path("out/print3d"), "--out", help="Output directory."),
    bed: str = typer.Option("256x256x256", "--bed", help="Build volume WxDxH, mm."),
    margin_mm: float = typer.Option(4.0, "--margin-mm", help="Kept clear at the bed edge."),
    nozzle: float = typer.Option(0.4, "--nozzle", help="Nozzle mm; sets the two minimums."),
    min_feature_mm: float | None = typer.Option(
        None, "--min-feature-mm", help="Smallest printed feature (default: the nozzle)."),
    min_wall_mm: float | None = typer.Option(
        None, "--min-wall-mm", help="Thinnest wall or slab (default: two nozzle widths)."),
    max_thicken: float = typer.Option(3.0, "--max-thicken", help="Drop past this growth."),
    min_piece_m: float = typer.Option(0.6, "--min-piece-m", help="Merge cuts closer than this."),
    min_island_mm3: float = typer.Option(2.0, "--min-island-mm3",
                                         help="Drop loose bits smaller than this."),
    plate_margin_mm: float = typer.Option(3.0, "--plate-margin-mm"),
    scale: int | None = typer.Option(None, "--scale", help="Print at 1:N, or refuse."),
    include: str | None = typer.Option(None, "--include",
                                       help="Kinds to print that are dropped by default: "
                                            "railing,solar_panel,site."),
    exclude: str | None = typer.Option(None, "--exclude", help="Kinds to leave out."),
    no_furniture: bool = typer.Option(False, "--no-furniture", help="Skip furniture.3mf."),
    stl: bool = typer.Option(False, "--stl", help="Also write one STL per piece."),
    timing: bool = typer.Option(False, "--timing", help="Print stage timings."),
) -> None:
    """Export the house as lift-off storeys on a plate, plus movable furniture, as 3MF."""
    import time

    from typehaus.print3d.policy import PrintSettings
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    try:
        from typehaus.solids3d import require_manifold3d

        require_manifold3d()
    except ImportError as error:
        console.print(str(error), markup=False)
        raise typer.Exit(1) from error
    from typehaus.print3d.build import build_print
    from typehaus.print3d.report import report_lines
    from typehaus.print3d.threemf import write_3mf, write_stl

    started = time.perf_counter()
    directory = _resolve_house(house)
    loaded = load_plan(directory)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    model, findings = resolve(loaded.plan)
    if any(finding.severity is Severity.ERROR for finding in findings):
        _print_findings(findings)
        raise typer.Exit(1)
    resolved = time.perf_counter() - started
    settings = PrintSettings(
        bed_mm=_bed(bed), margin_mm=margin_mm, nozzle_mm=nozzle, min_feature_mm=min_feature_mm,
        min_wall_mm=min_wall_mm, max_thicken=max_thicken, min_piece_m=min_piece_m,
        min_island_mm3=min_island_mm3, plate_margin_mm=plate_margin_mm, scale=scale,
        include=_kinds(include), exclude=_kinds(exclude), furniture=not no_furniture)
    try:
        run = build_print(model, settings)
    except ValueError as error:
        console.print(f"print3d: {error}", soft_wrap=True)
        raise typer.Exit(1) from error
    run.timings = {"resolve": resolved, **run.timings}
    files = [write_3mf(out / "house.3mf", run.pieces, directory.name)]
    if run.furniture:
        files.append(write_3mf(out / "furniture.3mf", run.furniture,
                               f"{directory.name} furniture"))
    if stl:
        files += [write_stl(out / "stl" / f"{piece.name}.stl", piece) for piece in run.pieces]
    run.timings["write"] = time.perf_counter() - started - sum(run.timings.values())
    names = [str(path) for path in files]
    lines = report_lines(run, settings, names)
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    shown = lines if timing else lines[:lines.index("## Timings")]
    console.print("\n".join(shown), soft_wrap=True, markup=False)
    console.print(f"wrote {out / 'report.md'}", soft_wrap=True)
