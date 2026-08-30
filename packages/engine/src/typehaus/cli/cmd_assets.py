"""`haus import | export | import-project` — moving assets and whole houses across machines.

Split out of :mod:`typehaus.cli.app` by command family. The three commands here are the ones
that cross the project boundary: a placeable's visual asset coming in, a house plus its
external references going out as a portable bundle, and that bundle being unpacked and
re-verified on the far side. All three are two-step by design — analyze, then explicitly
commit — because an import that silently mutates the project is how a broken reference gets
in unnoticed.
"""

from __future__ import annotations

from pathlib import Path

import typer

from typehaus.cli._shared import _resolve_house, app, console


@app.command(name="import")
def import_asset(
    kind: str = typer.Argument(
        ..., help="furniture | plumbing | appliance | mechanical | register | electrical"),
    source: Path = typer.Argument(..., help=".glb | .gltf | .dae | .svg | .ifc asset to import"),
    house: Path | None = typer.Argument(None, help="House directory (default: cwd)"),
    tag: str | None = typer.Option(None, help="Type tag suffix (for example lounge-chair)"),
    name: str | None = typer.Option(None, help="Display name"),
    analyze: bool = typer.Option(False, help="Analyze only; do not mutate the project"),
    confirm: bool = typer.Option(False, help="Commit a confirmed project-local catalog type"),
    units: str = typer.Option("m", help="Confirmed source units: m | mm | ft"),
    up_axis: str = typer.Option("y", help="Confirmed up axis: y | z"),
    origin: str = typer.Option("floor_center", help="Confirmed origin: floor_center"),
    ifc_occurrence: str | None = typer.Option(
        None, help="Analyzed IFC occurrence ID or GlobalId to extract"),
) -> None:
    """Analyze, then explicitly commit a house-local placeable visual asset."""
    from typehaus.source.placeable_import import (
        ImportConfirmation,
        analyze_placeable_asset,
        commit_placeable_asset,
    )
    house_dir = _resolve_house(house)
    asset_analysis = analyze_placeable_asset(source)
    if analyze:
        console.print({"format": asset_analysis.format,
                       "content_hash": asset_analysis.content_hash,
                       "total_bytes": asset_analysis.total_bytes,
                       "dependencies": [str(path) for path in asset_analysis.dependencies],
                       "ifc_candidates": [{"id": item.occurrence_id,
                                           "global_id": item.global_id,
                                           "class": item.ifc_class, "name": item.name,
                                           "type_global_id": item.type_global_id,
                                           "bounds_m": item.bounds_m,
                                           "footprint_m": item.footprint_m,
                                           "orientation_degrees": item.orientation_degrees,
                                           "materials": item.materials,
                                           "properties": item.properties,
                                           "ports": item.ports}
                                          for item in asset_analysis.ifc_candidates]})
        return
    if not confirm:
        raise typer.BadParameter("review analysis first, then rerun with --confirm and "
                                 "normalization decisions")
    if tag is None or name is None:
        raise typer.BadParameter("--tag and --name are required for confirmed catalog imports")
    record = commit_placeable_asset(asset_analysis, house_dir, domain=kind, tag=tag, name=name,
                                    confirmation=ImportConfirmation(units=units,
                                                                    up_axis=up_axis,
                                                                    origin=origin),
                                    ifc_occurrence=ifc_occurrence)
    console.print(f"imported {record['tag']} into assets/placeables.json")


@app.command()
def export(
    house: Path | None = typer.Argument(None, help="House directory (default: cwd)"),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Archive path (default: <house>.haus.zip)"),
) -> None:
    """Bundle a house + its external reference assets into a portable .zip for another machine."""
    from typehaus.source.bundle import export_house

    d = _resolve_house(house)
    try:
        result = export_house(d, output)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"wrote {result.archive} ({result.file_count} source file(s))")
    for original, bundled in result.relinked_underlays:
        console.print(f"  bundled underlay {original} -> {bundled}")
    for missing in result.missing_underlays:
        console.print(f"[yellow]  underlay source missing, not bundled: {missing}[/yellow]")
    console.print("[green]export ok[/green]")


@app.command(name="import-project")
def import_project(
    archive: Path = typer.Argument(..., help="house .zip produced by `haus export`"),
    dest: Path = typer.Argument(..., help="destination directory for the imported house"),
    force: bool = typer.Option(False, help="overwrite a non-empty destination"),
) -> None:
    """Unpack a portable house bundle and verify its relinked asset references."""
    from typehaus.source.bundle import import_house

    try:
        result = import_house(archive, dest, force=force)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    console.print(f"imported {result.name} into {result.house_dir}")
    for missing in result.missing_underlays:
        console.print(f"[yellow]  missing underlay: {missing}[/yellow]")
    for missing in result.missing_assets:
        console.print(f"[yellow]  missing asset: {missing}[/yellow]")
    if result.ok:
        console.print(f"[green]import ok[/green] — try: haus build {result.house_dir}")
    else:
        console.print("[red]import completed with missing references[/red]")
        raise typer.Exit(1)
